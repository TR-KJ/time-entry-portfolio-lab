"""A2 Phase 1 fixed-state overlap diagnosis; no trade deletion or portfolio replay."""
import argparse,csv,hashlib,json,sys
from collections import Counter,defaultdict
from datetime import datetime,date,timedelta
from pathlib import Path
import numpy as np

BASELINE_SHA='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PLAN_SHA='5c38edbd64df7901d3716f2a0817ca6a81e82d50'
BRANCH='research/overlap-incremental-edge-phase1'
SEED=20260913; B=5000
PAIRS={'EJ':'EURJPY','GJ':'GBPJPY','AJ':'AUDJPY','UJ':'USDJPY','EA':'EURAUD','GA':'GBPAUD','AU':'AUDUSD'}
STATES=('NO_SAME_SYMBOL_OPEN','SAME_SYMBOL_SAME_DIR_OPEN','SAME_SYMBOL_OPPOSITE_DIR_OPEN','SIMULTANEOUS_BATCH','BOUNDARY_AMBIGUOUS')
CROSS=('CROSS_SYMBOL_ALIGNED_EXPOSURE','CROSS_SYMBOL_OPPOSED_EXPOSURE','NO_SHARED_CURRENCY_EXPOSURE','MIXED_CROSS_SYMBOL_EXPOSURE')
PERIODS={'Historical':('2015-01-01','2022-01-01'),'Recent A':('2022-01-01','2024-01-01'),'Recent B':('2024-01-01','2026-01-01'),'2026 Monitor':('2026-01-01','2026-09-10'),'Recent Combined':('2022-01-01','2026-09-10'),'ALL':('2015-01-01','2026-09-10')}

def period(day,p):
 a,z=PERIODS[p];return a<=day.isoformat()<z

def week(day):return (day-timedelta(days=day.weekday())).isoformat()

def vector(symbol,direction):
 if len(symbol)!=6 or direction not in ('Long','Short'):raise ValueError('symbol/direction')
 sign=1 if direction=='Long' else -1
 return {symbol[:3]:sign,symbol[3:]:-sign}

def load_baseline(path):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=BASELINE_SHA:raise ValueError('baseline hash mismatch')
 rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
 if len(rows)!=16298:raise ValueError('baseline count mismatch')
 ids={(int(r['StrategyNo']),r['Strategy']) for r in rows}
 if len(ids)!=28 or {n for n,_ in ids}!=set(range(1,29)):raise ValueError('identities mismatch')
 if len({(r['StrategyNo'],r['EntryTime']) for r in rows})!=len(rows):raise ValueError('duplicate identity')
 for r in rows:
  if r['Pair'] not in PAIRS:raise ValueError('unknown pair alias')
  e=datetime.fromisoformat(r['EntryTime']);x=datetime.fromisoformat(r['CloseTime'])
  if e.tzinfo is not None or x.tzinfo is not None or x<=e:raise ValueError('invalid JST ordering')
  r['No']=int(r['StrategyNo']);r['Entry']=e;r['Exit']=x;r['Day']=e.date();r['Week']=week(e.date());r['Symbol']=PAIRS[r['Pair']];r['Rfloat']=float(r['R'])
  if not np.isfinite(r['Rfloat']) or abs(r['Rfloat']-float(r['Pips'])/float(r['SL']))>1e-8:raise ValueError('R integrity')
  if not period(r['Day'],'ALL'):raise ValueError('outside period')
 return rows

def state_for(candidate,prior,batch_size):
 same=[r for r in prior if r['Symbol']==candidate['Symbol']]
 boundary=[r for r in same if r['Exit']==candidate['Entry']]
 strict=[r for r in same if r['Entry']<candidate['Entry']<r['Exit']]
 same_dir=sum(r['Direction']==candidate['Direction'] for r in strict)
 opposite=len(strict)-same_dir
 if batch_size>1:state='SIMULTANEOUS_BATCH';reason=''
 elif boundary:state='BOUNDARY_AMBIGUOUS';reason='EXIT_EQUALS_ENTRY'
 elif same_dir and opposite:state='BOUNDARY_AMBIGUOUS';reason='MIXED_DIRECTIONS'
 elif same_dir:state='SAME_SYMBOL_SAME_DIR_OPEN';reason=''
 elif opposite:state='SAME_SYMBOL_OPPOSITE_DIR_OPEN';reason=''
 else:state='NO_SAME_SYMBOL_OPEN';reason=''
 cv=vector(candidate['Symbol'],candidate['Direction']);aligned=opposed=False
 for r in prior:
  if r['Symbol']==candidate['Symbol'] or not (r['Entry']<candidate['Entry']<r['Exit']):continue
  ov=vector(r['Symbol'],r['Direction'])
  for c in set(cv)&set(ov):
   aligned|=cv[c]==ov[c];opposed|=cv[c]!=ov[c]
 cross='MIXED_CROSS_SYMBOL_EXPOSURE' if aligned and opposed else ('CROSS_SYMBOL_ALIGNED_EXPOSURE' if aligned else ('CROSS_SYMBOL_OPPOSED_EXPOSURE' if opposed else 'NO_SHARED_CURRENCY_EXPOSURE'))
 return state,reason,cross,same_dir,opposite

def classify(rows,portfolio):
 own=[r.copy() for r in rows if portfolio=='Old28' or r['No']!=22]
 if len(own)!=(15837 if portfolio=='Primary27' else 16298):raise ValueError('portfolio count')
 own.sort(key=lambda r:(r['Entry'],r['No']))
 active=[];batches=[];i=0
 while i<len(own):
  j=i+1
  while j<len(own) and own[j]['Entry']==own[i]['Entry']:j+=1
  batch=own[i:j];t=batch[0]['Entry'];active=[r for r in active if r['Exit']>=t]
  if len(batch)>1:
   batches.append(dict(Portfolio=portfolio,EntryTime=t.isoformat(sep=' '),Trades=len(batch),Strategies='|'.join(str(r['No']) for r in batch),Symbols='|'.join(r['Symbol'] for r in batch),Directions='|'.join(r['Direction'] for r in batch),AvgR=float(np.mean([r['Rfloat'] for r in batch]))))
  for r in batch:
   r['State'],r['BoundaryReason'],r['CrossExposure'],r['SameOpenCount'],r['OppositeOpenCount']=state_for(r,active,len(batch))
  active.extend(batch);i=j
 if len(own)!=sum(Counter(r['State'] for r in own).values()):raise ValueError('state uniqueness')
 return own,batches

def metrics(rows):
 a=np.array([r['Rfloat'] for r in rows]);n=len(a);gain=float(a[a>0].sum());loss=float(-a[a<0].sum())
 return dict(Trades=n,Weeks=len({r['Week'] for r in rows}),TotalR=float(a.sum()),AvgR=float(a.mean()) if n else None,PF=gain/loss if loss else (float('inf') if gain else None),WinRate=float(np.count_nonzero(a>0)/n) if n else None,AvgWinR=float(a[a>0].mean()) if gain else None,AvgLossR=float(a[a<0].mean()) if loss else None)

def bootstrap(rows,levels,period_name='Recent Combined'):
 subset=[r for r in rows if period(r['Day'],period_name)]
 clusters=defaultdict(list)
 for r in subset:clusters[r['Week']].append(r)
 keys=sorted(clusters)
 sums=np.zeros((len(keys),len(levels)));counts=np.zeros_like(sums)
 for i,k in enumerate(keys):
  for r in clusters[k]:
   if r['State'] in levels:
    j=levels.index(r['State']);sums[i,j]+=r['Rfloat'];counts[i,j]+=1
 rng=np.random.Generator(np.random.PCG64(SEED));draws=rng.integers(0,len(keys),size=(B,len(keys)))
 with np.errstate(divide='ignore',invalid='ignore'):
  s=sums[draws].sum(axis=1);n=counts[draws].sum(axis=1);means=s/n
 return means,draws,keys

def ci(values):return tuple(np.quantile(values,[.025,.975],method='linear')) if np.isfinite(values).all() else (None,None)
def holm(pvalues):
 order=sorted(range(len(pvalues)),key=lambda i:(pvalues[i],i));out=[None]*len(order);running=0
 for rank,i in enumerate(order):running=max(running,min(1.0,(len(order)-rank)*pvalues[i]));out[i]=running
 return out

def analyze(rows):
 tables={k:[] for k in ('strategy_state_summary','period_summary','contrasts','multiple_comparison','global_summary','simultaneous_summary','cross_symbol_exposure_diagnostic','coverage','yearly_summary')}
 local=[];portfolio_cache={}
 for portfolio in ('Primary27','Old28'):
  own,batches=classify(rows,portfolio);portfolio_cache[portfolio]=own
  for r in own:local.append(dict(Portfolio=portfolio,StrategyNo=r['No'],Strategy=r['Strategy'],EntryTime=r['EntryTime'],CloseTime=r['CloseTime'],Symbol=r['Symbol'],Direction=r['Direction'],R=r['R'],State=r['State'],BoundaryReason=r['BoundaryReason'],CrossExposure=r['CrossExposure'],SameOpenCount=r['SameOpenCount'],OppositeOpenCount=r['OppositeOpenCount']))
  nos=sorted({r['No'] for r in own})
  for n in nos:
   sr=[r for r in own if r['No']==n]
   tables['coverage'].append(dict(Portfolio=portfolio,StrategyNo=n,Strategy=sr[0]['Strategy'],Trades=len(sr),StateCounts=json.dumps(dict(Counter(r['State'] for r in sr)),sort_keys=True),CrossCounts=json.dumps(dict(Counter(r['CrossExposure'] for r in sr)),sort_keys=True)))
   for state in STATES:
    ss=[r for r in sr if r['State']==state]
    tables['strategy_state_summary'].append(dict(Portfolio=portfolio,StrategyNo=n,Strategy=sr[0]['Strategy'],State=state,**metrics(ss)))
    for pname in PERIODS:
     pp=[r for r in ss if period(r['Day'],pname)]
     tables['period_summary'].append(dict(Portfolio=portfolio,StrategyNo=n,Strategy=sr[0]['Strategy'],State=state,Period=pname,**metrics(pp)))
    for year in range(2015,2027):
     yy=[r for r in ss if r['Day'].year==year]
     tables['yearly_summary'].append(dict(Portfolio=portfolio,StrategyNo=n,State=state,Year=year,**metrics(yy)))
   m={state:metrics([r for r in sr if r['State']==state and period(r['Day'],'Recent Combined')]) for state in STATES}
   ov=m['SAME_SYMBOL_SAME_DIR_OPEN'];no=m['NO_SAME_SYMBOL_OPEN'];diff=ov['AvgR']-no['AvgR'] if ov['Trades'] and no['Trades'] else None
   samples,_,_=bootstrap(sr,['SAME_SYMBOL_SAME_DIR_OPEN','NO_SAME_SYMBOL_OPEN'])
   valid=bool(np.isfinite(samples).all());sufficient=all(v['Trades']>=30 and v['Weeks']>=20 for v in (ov,no))
   oci=ci(samples[:,0]) if sufficient and valid else (None,None);nci=ci(samples[:,1]) if sufficient and valid else (None,None);dci=ci(samples[:,0]-samples[:,1]) if sufficient and valid else (None,None)
   p=(1+int(np.count_nonzero(samples[:,0]-samples[:,1]>=0)))/(B+1) if sufficient and valid else 1.0
   stability={pname:metrics([r for r in sr if r['State']=='SAME_SYMBOL_SAME_DIR_OPEN' and period(r['Day'],pname)]) for pname in ('Historical','Recent A','Recent B','2026 Monitor')}
   a,b=stability['Recent A'],stability['Recent B'];stable=all(x['Trades']>=15 and x['Weeks']>=10 and x['AvgR'] is not None and x['AvgR']<0 for x in (a,b))
   tables['contrasts'].append(dict(Portfolio=portfolio,StrategyNo=n,Strategy=sr[0]['Strategy'],OverlapTrades=ov['Trades'],OverlapWeeks=ov['Weeks'],OverlapAvgR=ov['AvgR'],OverlapCI_L=oci[0],OverlapCI_U=oci[1],NoOverlapTrades=no['Trades'],NoOverlapWeeks=no['Weeks'],NoOverlapAvgR=no['AvgR'],NoOverlapCI_L=nci[0],NoOverlapCI_U=nci[1],OverlapDiff=diff,DiffCI_L=dci[0],DiffCI_U=dci[1],RawP=p,SampleSufficient=sufficient,BootstrapValid=valid,RecentAOverlapAvgR=a['AvgR'],RecentAOverlapTrades=a['Trades'],RecentAOverlapWeeks=a['Weeks'],RecentBOverlapAvgR=b['AvgR'],RecentBOverlapTrades=b['Trades'],RecentBOverlapWeeks=b['Weeks'],MonitorOverlapAvgR=stability['2026 Monitor']['AvgR'],HistoricalOverlapAvgR=stability['Historical']['AvgR'],StabilityPass=stable))
  for pname in PERIODS:
   group=[r for r in own if period(r['Day'],pname)]
   for state in STATES:
    tables['global_summary'].append(dict(Portfolio=portfolio,Period=pname,State=state,**metrics([r for r in group if r['State']==state])))
   for cross in CROSS:
    tables['cross_symbol_exposure_diagnostic'].append(dict(Portfolio=portfolio,Period=pname,CrossExposure=cross,**metrics([r for r in group if r['CrossExposure']==cross])))
  bgroup=defaultdict(list)
  for b in batches:
   key=(b['Strategies'],b['Symbols'],b['Directions']);bgroup[key].append(b)
  for key,bs in bgroup.items():
   tables['simultaneous_summary'].append(dict(Portfolio=portfolio,Strategies=key[0],Symbols=key[1],Directions=key[2],Batches=len(bs),Trades=sum(b['Trades'] for b in bs),MeanBatchR=float(np.mean([b['AvgR'] for b in bs]))))
 primary=[x for x in tables['contrasts'] if x['Portfolio']=='Primary27'];adjusted=holm([x['RawP'] for x in primary])
 for x,padj in zip(primary,adjusted):
  x['AdjustedP']=padj
  flags={'A':x['OverlapAvgR'] is not None and x['OverlapAvgR']<0,'B':x['OverlapCI_U'] is not None and x['OverlapCI_U']<0,'C':x['NoOverlapAvgR'] is not None and x['NoOverlapAvgR']>=0,'D':x['OverlapDiff'] is not None and x['OverlapDiff']<0,'E':padj<.05,'F':x['SampleSufficient'] and x['BootstrapValid'],'G':x['StabilityPass']}
  for k,v in flags.items():x[k]='PASS' if v else 'FAIL'
  if all(flags.values()):label='OVERLAP_SUPPRESSION_CANDIDATE'
  elif not flags['F']:label='INSUFFICIENT_SAMPLE'
  elif x['OverlapAvgR'] is not None and x['OverlapAvgR']>0:label='OVERLAP_STILL_POSITIVE'
  elif flags['A'] and flags['C'] and flags['D']:label='WEAK_OVERLAP_SIGNAL'
  else:label='NOT_SUPPORTED'
  x['Verdict']=label
  tables['multiple_comparison'].append(dict(StrategyNo=x['StrategyNo'],RawP=x['RawP'],AdjustedP=padj,FamilySize=27,Pass=flags['E']))
 for x in tables['contrasts']:
  if x['Portfolio']=='Old28':x['AdjustedP']='';x['Verdict']='ROBUSTNESS_ONLY'
 if len(primary)!=27:raise ValueError('Holm family size')
 # Global pooled and strategy-adjusted recent comparison, fixed original states.
 for portfolio,own in portfolio_cache.items():
  g=[r for r in own if period(r['Day'],'Recent Combined')]
  ov=metrics([r for r in g if r['State']=='SAME_SYMBOL_SAME_DIR_OPEN']);no=metrics([r for r in g if r['State']=='NO_SAME_SYMBOL_OPEN'])
  eligible=[x['StrategyNo'] for x in tables['contrasts'] if x['Portfolio']==portfolio and x['SampleSufficient'] and x['BootstrapValid']]
  diffs=[x['OverlapDiff'] for x in tables['contrasts'] if x['Portfolio']==portfolio and x['StrategyNo'] in eligible]
  pooled=ov['AvgR']-no['AvgR'] if ov['Trades'] and no['Trades'] else None
  adjusted_point=float(np.mean(diffs)) if diffs else None
  byweek=defaultdict(list)
  for r in g:byweek[r['Week']].append(r)
  keys=sorted(byweek);rng=np.random.Generator(np.random.PCG64(SEED));draws=rng.integers(0,len(keys),size=(B,len(keys)))
  # Aggregate weekly sums/counts for the two states and every eligible strategy.
  levels=[None]+eligible;arr=np.zeros((len(keys),len(levels),2,2))
  for i,k in enumerate(keys):
   for r in byweek[k]:
    if r['State'] not in ('SAME_SYMBOL_SAME_DIR_OPEN','NO_SAME_SYMBOL_OPEN'):continue
    q=0 if r['State']=='SAME_SYMBOL_SAME_DIR_OPEN' else 1
    for j,n in enumerate(levels):
     if n is None or r['No']==n:arr[i,j,q,0]+=r['Rfloat'];arr[i,j,q,1]+=1
  sampled=arr[draws].sum(axis=1)
  with np.errstate(divide='ignore',invalid='ignore'):
   means=sampled[:,:,:,0]/sampled[:,:,:,1]
   pooldiff=means[:,0,0]-means[:,0,1]
   eqdiff=np.mean(means[:,1:,0]-means[:,1:,1],axis=1) if eligible else np.full(B,np.nan)
  valid=bool(np.isfinite(means[:,0,:]).all());pooled_ci=ci(pooldiff) if valid else (None,None);overlap_ci=ci(means[:,0,0]) if valid else (None,None);equal_ci=ci(eqdiff) if eligible and np.isfinite(eqdiff).all() else (None,None)
  advance=(portfolio=='Primary27' and ov['Trades']>=30 and ov['Weeks']>=20 and no['Trades']>=30 and no['Weeks']>=20 and len(eligible)>=5 and ov['AvgR'] is not None and ov['AvgR']<0 and overlap_ci[1] is not None and overlap_ci[1]<0 and adjusted_point is not None and adjusted_point<0 and equal_ci[1] is not None and equal_ci[1]<0)
  tables['global_summary'].append(dict(Portfolio=portfolio,Period='Recent Combined',State='GLOBAL_CONTRAST',Trades=ov['Trades'],Weeks=ov['Weeks'],TotalR=ov['TotalR'],AvgR=ov['AvgR'],PF=ov['PF'],WinRate=ov['WinRate'],AvgWinR=ov['AvgWinR'],AvgLossR=ov['AvgLossR'],NoOverlapTrades=no['Trades'],NoOverlapAvgR=no['AvgR'],PooledDiff=pooled,PooledDiffCI_L=pooled_ci[0],PooledDiffCI_U=pooled_ci[1],OverlapCI_L=overlap_ci[0],OverlapCI_U=overlap_ci[1],EligibleStrategies=len(eligible),StrategyEqualDiff=adjusted_point,StrategyEqualCI_L=equal_ci[0],StrategyEqualCI_U=equal_ci[1],GlobalRuleAdvance=advance))
 return tables,local

def write(path,records):
 if not records:return
 keys=list(dict.fromkeys(k for r in records for k in r))
 with open(path,'w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(records)

def run(baseline,out,implementation_sha='UNCOMMITTED'):
 rows=load_baseline(baseline);tables,local=analyze(rows);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 for name,records in tables.items():write(out/f'overlap_phase1_{name}.csv',records)
 write(out/'overlap_phase1_trade_assignment_local.csv',local)
 run_record=[dict(Branch=BRANCH,PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,BaselineSHA256=BASELINE_SHA,BaselineTrades=16298,Primary27Trades=15837,Robustness28Trades=16298,BootstrapReplicates=B,Seed=SEED,Python=sys.version.split()[0],Numpy=np.__version__,FreshHoldout=False,BaselineRecalculated=False,PortfolioReplay=False,ResultsPublic=False)]
 write(out/'overlap_phase1_run_record.csv',run_record)
 print(json.dumps({'primary_states':dict(Counter(x['State'] for x in local if x['Portfolio']=='Primary27')),'old28_states':dict(Counter(x['State'] for x in local if x['Portfolio']=='Old28')),'candidates':[x['StrategyNo'] for x in tables['contrasts'] if x.get('Verdict')=='OVERLAP_SUPPRESSION_CANDIDATE'],'global':[x['GlobalRuleAdvance'] for x in tables['global_summary'] if x['State']=='GLOBAL_CONTRAST']},indent=2))
 return tables
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',default='/content');p.add_argument('--implementation-sha',default='UNCOMMITTED');a=p.parse_args();run(a.baseline,a.out,a.implementation_sha)
