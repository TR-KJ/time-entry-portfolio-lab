"""A3 fixed-anchor exit-efficiency replay; E100 hard gate before variant outcomes."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,sys,gc
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from daily_stop_baseline_revalidation import STRATEGIES,MANIFEST_NAMES,PIP_SIZE,SPREAD_PIPS,load_pair,is_forward_gotobi

BASELINE_SHA='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PLAN_SHA='5d6cf4f784562ed8cee2f9c0a353527917b22388'
SEED=20260913;B=5000
LABELS={'E25':.25,'E50':.5,'E75':.75,'E100':1.0}
PERIODS={'Historical':('2015-01-01','2022-01-01'),'Recent A':('2022-01-01','2024-01-01'),'Recent B':('2024-01-01','2026-01-01'),'2026 Monitor':('2026-01-01','2026-09-10'),'Recent Combined':('2022-01-01','2026-09-10'),'ALL':('2015-01-01','2026-09-10')}
STRATEGY={s.no:s for s in STRATEGIES}

def week(t):
 d=t.date();return (d-timedelta(days=d.weekday())).isoformat()
def in_period(t,p):
 a,z=PERIODS[p];return a<=t.date().isoformat()<z

def load_baseline(path):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=BASELINE_SHA:raise ValueError('baseline SHA mismatch')
 rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
 if len(rows)!=16298 or len({(r['StrategyNo'],r['Strategy']) for r in rows})!=28:raise ValueError('baseline identity/count')
 if len({(r['StrategyNo'],r['EntryTime']) for r in rows})!=len(rows):raise ValueError('duplicate identity')
 for r in rows:
  n=int(r['StrategyNo']);s=STRATEGY[n]
  if r['Strategy']!=s.name or r['Pair']!=s.pair:raise ValueError('strategy metadata identity')
  e=datetime.fromisoformat(r['EntryTime']);x=datetime.fromisoformat(r['ScheduledExitTime'])
  if e.tzinfo or x.tzinfo or x<=e or e.second or x.second:raise ValueError('bad JST schedule')
  if (x.date()-e.date()).days!=s.exit_day_offset or (x.hour,x.minute)!=s.exit:raise ValueError('planned exit metadata')
  expected_entry=s.entry;mode='STANDARD';sl=s.sl;tp=s.tp
  if n==12:
   goto=e.day in (20,25,30) or is_forward_gotobi(pd.Timestamp(e))
   mode='GOTO' if goto else 'NORMAL';expected_entry=(9,55) if goto else (8,4);sl=20 if goto else 50;tp=50 if goto else None
  if (e.hour,e.minute)!=expected_entry or r['Mode']!=mode or abs(float(r['SL'])-sl)>1e-9:raise ValueError('planned entry/mode/SL metadata')
  if (tp is None and r['TP'] not in ('','nan','NaN')) or (tp is not None and abs(float(r['TP'])-tp)>1e-9):raise ValueError('TP metadata')
  if abs(float(r['R'])-float(r['Pips'])/sl)>1e-8:raise ValueError('baseline R')
  r['_n']=n;r['_entry']=e;r['_scheduled']=x;r['_week']=week(e)
 return rows

def checkpoint(entry,scheduled,fraction):
 duration=(scheduled-entry).total_seconds()
 if duration<=0 or duration%60:raise ValueError('invalid planned duration')
 minutes=int(np.floor(duration*fraction/60))
 if minutes<=0:raise ValueError('checkpoint before entry')
 return entry+timedelta(minutes=minutes)

def resolve_and_audit(manifest_path,root):
 manifest=list(csv.DictReader(open(manifest_path,newline='',encoding='utf-8')))
 if len(manifest)!=56 or Counter(x['Symbol'] for x in manifest)!={s:8 for s in MANIFEST_NAMES}:raise ValueError('expected 56 manifest rows')
 for s,names in MANIFEST_NAMES.items():
  if [x['Filename'] for x in manifest if x['Symbol']==s]!=names:raise ValueError('manifest names/order mismatch')
 want={x['Filename'] for x in manifest};hits=defaultdict(list)
 for base,dirs,files in os.walk(root):
  for name in files:
   if name in want:hits[name].append(Path(base)/name)
 if set(hits)!=want or any(len(v)!=1 for v in hits.values()):raise ValueError('missing/duplicate M1 files')
 audit=[];paths=defaultdict(list)
 for x in manifest:
  p=hits[x['Filename']][0];h=hashlib.sha256();lines=0;first=None;last=None;tail=b''
  with p.open('rb') as f:
   header=f.readline();h.update(header);lines+=1
   for line in f:
    h.update(line);lines+=1
    if first is None:first=line
    last=line
  if h.hexdigest()!=x['SHA256'] or lines-1!=int(x['Rows']):raise ValueError('M1 hash/row mismatch '+x['Filename'])
  def rawdt(line):
   parts=line.decode('utf-8-sig').strip().split('\t');return parts[0].replace('.','-')+' '+parts[1]
  if rawdt(first)!=x['FirstRaw'] or rawdt(last)!=x['LastRaw']:raise ValueError('M1 first/last mismatch '+x['Filename'])
  paths[x['Symbol']].append(p);audit.append(dict(Symbol=x['Symbol'],Filename=x['Filename'],SHA256=h.hexdigest(),Rows=lines-1,Bytes=p.stat().st_size,FirstRaw=rawdt(first),LastRaw=rawdt(last),Status='PASS'))
 return paths,audit

def simulate(anchor,bars,label):
 entry=anchor['_entry'];scheduled=anchor['_scheduled'];target=checkpoint(entry,scheduled,LABELS[label]);idx=bars.index
 ei=idx.searchsorted(pd.Timestamp(entry))
 if ei>=len(idx) or idx[ei]!=pd.Timestamp(entry):raise ValueError('missing exact anchor entry bar')
 actual_exit=None;delay=None
 for k in range(5):
  t=target+timedelta(minutes=k);j=idx.searchsorted(pd.Timestamp(t))
  if j<len(idx) and idx[j]==pd.Timestamp(t):actual_exit=t;delay=k;xi=j;break
 if actual_exit is None:return dict(Status='MISSING_CHECKPOINT_BAR',Label=label)
 if xi<=ei:raise ValueError('invalid checkpoint window')
 n=anchor['_n'];s=STRATEGY[n];long=anchor['Direction']=='Long';pip=PIP_SIZE[s.pair];spread=SPREAD_PIPS[s.pair];sl=float(anchor['SL']);tp=float(anchor['TP']) if anchor['TP'] else None
 raw=float(bars.iloc[ei]['Open']);price=raw+(spread*pip if long else -spread*pip)
 slprice=price+(-sl*pip if long else sl*pip);tpprice=None if tp is None else price+(tp*pip if long else -tp*pip)
 window=bars.iloc[ei:xi+1];high=window['High'].to_numpy();low=window['Low'].to_numpy()
 slhit=(low<=slprice) if long else (high>=slprice)
 tphit=np.zeros(len(window),dtype=bool) if tpprice is None else ((high>=tpprice) if long else (low<=tpprice))
 hits=np.flatnonzero(slhit|tphit)
 if len(hits):
  offset=int(hits[0]);close=idx[ei+offset].to_pydatetime();reason='SL' if slhit[offset] else 'TP';closeprice=slprice if reason=='SL' else tpprice;pips=-sl if reason=='SL' else tp
 else:
  close=actual_exit;reason='TimeExit';closeprice=float(bars.iloc[xi]['Open']);pips=(closeprice-price)/pip if long else (price-closeprice)/pip
 pips=round(float(pips),6);R=round(float(pips/sl),9)
 return dict(Status='OK',Label=label,StrategyNo=n,Strategy=anchor['Strategy'],Pair=anchor['Pair'],Direction=anchor['Direction'],Mode=anchor['Mode'],EntryTime=anchor['EntryTime'],ScheduledExitTime=anchor['ScheduledExitTime'],CheckpointTime=target.isoformat(sep=' '),CloseTime=close.isoformat(sep=' '),ExitDelayMinutes=delay,RawEntryOpen=raw,EntryPrice=price,ClosePrice=closeprice,SL=sl,TP=tp,Pips=pips,R=R,ExitReason=reason,Week=anchor['_week'])

def reconcile(anchor,result):
 if result['Status']!='OK':return ['MISSING_CHECKPOINT_BAR']
 errors=[]
 for k in ('StrategyNo','Strategy','Pair','Direction','Mode','EntryTime','ScheduledExitTime','CloseTime','ExitReason','ExitDelayMinutes'):
  if str(anchor[k])!=str(result[k]):errors.append(k)
 for k,tol in [('RawEntryOpen',1e-9),('EntryPrice',1e-9),('ClosePrice',1e-9),('SL',1e-9),('Pips',1e-6),('R',1e-8)]:
  if abs(float(anchor[k])-float(result[k]))>tol:errors.append(k)
 atp=anchor['TP'];rtp=result['TP']
 if (atp=='' and rtp is not None) or (atp!='' and (rtp is None or abs(float(atp)-rtp)>1e-9)):errors.append('TP')
 return errors

def e100_stage(rows,paths):
 bypair=defaultdict(list)
 for r in rows:bypair[r['Pair']].append(r)
 from daily_stop_baseline_revalidation import SYMBOL_TO_PAIR
 allresults=[];errors=[]
 for symbol,pair in SYMBOL_TO_PAIR.items():
  bars=load_pair(paths[symbol],symbol)
  for anchor in bypair[pair]:
   result=simulate(anchor,bars,'E100');allresults.append(result)
   bad=reconcile(anchor,result)
   if bad:errors.append(dict(StrategyNo=anchor['StrategyNo'],EntryTime=anchor['EntryTime'],MismatchFields='|'.join(bad)))
  del bars;gc.collect()
 return allresults,errors

def write(path,records):
 if not records:raise ValueError('no records')
 keys=list(dict.fromkeys(k for r in records for k in r))
 with open(path,'w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(records)

def run_reconcile(baseline,manifest,root,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=load_baseline(baseline);paths,audit=resolve_and_audit(manifest,root);write(out/'exit_efficiency_phase1_m1_audit.csv',audit)
 e100,errors=e100_stage(rows,paths)
 counts=Counter(e['StrategyNo'] for e in errors);detail=Counter(field for e in errors for field in e['MismatchFields'].split('|'))
 summary=[dict(BaselineSHA256=BASELINE_SHA,Anchors=len(rows),Reconstructed=len(e100),MismatchCount=len(errors),MismatchFields=json.dumps(detail,sort_keys=True),Status='PASS' if not errors else 'FAIL')]
 write(out/'exit_efficiency_phase1_e100_reconciliation.csv',summary)
 if errors:write(out/'exit_efficiency_phase1_e100_mismatch_local.csv',errors)
 print(json.dumps(summary[0],indent=2))
 if errors:raise RuntimeError('E100 reconciliation failed; variants barred')
 return rows,paths,audit,e100


def metric(rs):
 a=np.array([float(r['R']) for r in rs]);n=len(a);gain=float(a[a>0].sum());loss=float(-a[a<0].sum())
 reasons=Counter(r['ExitReason'] for r in rs)
 return dict(Trades=n,Weeks=len({r['Week'] for r in rs}),TotalR=float(a.sum()),AvgR=float(a.mean()) if n else None,PF=gain/loss if loss else (float('inf') if gain else None),WinRate=float(np.count_nonzero(a>0)/n) if n else None,AvgWinR=float(a[a>0].mean()) if gain else None,AvgLossR=float(a[a<0].mean()) if loss else None,SLRate=reasons['SL']/n if n else None,TPRate=reasons['TP']/n if n else None,TimeRate=reasons['TimeExit']/n if n else None)

def bootstrap_pair(pairs):
 by=defaultdict(list)
 for anchor,a,b in pairs:by[anchor['_week']].append((a,b))
 keys=sorted(by);s=np.array([[sum(x[0] for x in by[k]),sum(x[1] for x in by[k]),len(by[k])] for k in keys],dtype=float)
 rng=np.random.Generator(np.random.PCG64(SEED));draws=rng.integers(0,len(keys),size=(B,len(keys)))
 sums=s[draws].sum(axis=1);delta=(sums[:,0]-sums[:,1])/sums[:,2]
 return delta

def holm(pvalues):
 order=sorted(range(len(pvalues)),key=lambda i:(pvalues[i],i));out=[None]*len(pvalues);running=0
 for rank,i in enumerate(order):running=max(running,min(1.0,(len(pvalues)-rank)*pvalues[i]));out[i]=running
 return out

def full_variants(rows,paths):
 bypair=defaultdict(list)
 for r in rows:bypair[r['Pair']].append(r)
 from daily_stop_baseline_revalidation import SYMBOL_TO_PAIR
 output=[];missing=[]
 for symbol,pair in SYMBOL_TO_PAIR.items():
  bars=load_pair(paths[symbol],symbol)
  for anchor in bypair[pair]:
   for label in LABELS:
    v=simulate(anchor,bars,label)
    if v['Status']!='OK':missing.append(dict(StrategyNo=anchor['StrategyNo'],EntryTime=anchor['EntryTime'],Label=label,Status=v['Status']))
    output.append((anchor,v))
  del bars;gc.collect()
 return output,missing

def analyze(rows,variants):
 bykey={(a['_n'],a['EntryTime'],v['Label']):(a,v) for a,v in variants}
 if len(bykey)!=len(rows)*4:raise ValueError('variant identity mismatch')
 tables={k:[] for k in ('strategy_summary','period_summary','profit_accrual','contrasts','multiple_comparison','coverage','yearly_summary')}
 for n in range(1,29):
  own=[a for a in rows if a['_n']==n]
  vset={label:[bykey[(n,a['EntryTime'],label)][1] for a in own] for label in LABELS}
  for label,vs in vset.items():
   okay=[v for v in vs if v['Status']=='OK'];tables['strategy_summary'].append(dict(StrategyNo=n,Strategy=STRATEGY[n].name,Variant=label,**metric(okay)))
   for pname in PERIODS:
    group=[v for v in okay if pname=='ALL' or in_period(datetime.fromisoformat(v['EntryTime']),pname)]
    tables['period_summary'].append(dict(StrategyNo=n,Strategy=STRATEGY[n].name,Variant=label,Period=pname,**metric(group)))
   for year in range(2015,2027):
    group=[v for v in okay if datetime.fromisoformat(v['EntryTime']).year==year]
    tables['yearly_summary'].append(dict(StrategyNo=n,Variant=label,Year=year,**metric(group)))
  tables['coverage'].append(dict(StrategyNo=n,Strategy=STRATEGY[n].name,Anchors=len(own),E25_OK=sum(v['Status']=='OK' for v in vset['E25']),E50_OK=sum(v['Status']=='OK' for v in vset['E50']),E75_OK=sum(v['Status']=='OK' for v in vset['E75']),E100_OK=sum(v['Status']=='OK' for v in vset['E100']),FormalActive=n!=22))
  for pname in PERIODS:
   subset=[a for a in own if in_period(a['_entry'],pname)]
   paired=[(a,bykey[(n,a['EntryTime'],'E75')][1],bykey[(n,a['EntryTime'],'E100')][1]) for a in subset]
   good=[(a,float(e75['R']),float(e100['R'])) for a,e75,e100 in paired if e75['Status']=='OK' and e100['Status']=='OK']
   e75=[bykey[(n,a['EntryTime'],'E75')][1] for a in subset];e100=[bykey[(n,a['EntryTime'],'E100')][1] for a in subset]
   avg75=float(np.mean([x[1] for x in good])) if good else None;avg100=float(np.mean([x[2] for x in good])) if good else None
   delta=avg75-avg100 if good else None;totaldiff=float(sum(x[1]-x[2] for x in good)) if good else None
   ci=(None,None);p=1.0;valid=len(good)==len(subset) and len(good)>0
   if valid:
    boot=bootstrap_pair(good)
    valid=bool(np.isfinite(boot).all())
    if valid:
     ci=tuple(np.quantile(boot,[.025,.975],method='linear'))
     if pname=='Recent Combined':p=(1+int(np.count_nonzero(boot<=0)))/(B+1)
   rec=dict(StrategyNo=n,Strategy=STRATEGY[n].name,Period=pname,Anchors=len(subset),PairedTrades=len(good),Weeks=len({a['_week'] for a,_,_ in good}),E75AvgR=avg75,E100AvgR=avg100,Delta75=delta,TotalRDiff=totaldiff,CI_L=ci[0],CI_U=ci[1],RawP=p if pname=='Recent Combined' else '',Valid=valid)
   tables['profit_accrual'].append(rec)
  recent=next(x for x in tables['profit_accrual'] if x['StrategyNo']==n and x['Period']=='Recent Combined')
  historical=next(x for x in tables['profit_accrual'] if x['StrategyNo']==n and x['Period']=='Historical')
  recentA=next(x for x in tables['profit_accrual'] if x['StrategyNo']==n and x['Period']=='Recent A')
  recentB=next(x for x in tables['profit_accrual'] if x['StrategyNo']==n and x['Period']=='Recent B')
  allp=next(x for x in tables['profit_accrual'] if x['StrategyNo']==n and x['Period']=='ALL')
  sufficient=all(x['PairedTrades']>=30 and x['Weeks']>=20 and x['Valid'] and x['PairedTrades']==x['Anchors'] for x in (recent,historical))
  recentAok=recentA['PairedTrades']>=15 and recentA['Weeks']>=10 and recentA['Delta75'] is not None and recentA['Delta75']>0
  recentBok=recentB['PairedTrades']>=15 and recentB['Weeks']>=10 and recentB['Delta75'] is not None and recentB['Delta75']>0
  metrics_by_variant={label:metric([v for v in vset[label] if v['Status']=='OK' and in_period(datetime.fromisoformat(v['EntryTime']),'Recent Combined')]) for label in LABELS}
  tables['contrasts'].append(dict(StrategyNo=n,Strategy=STRATEGY[n].name,FormalActive=n!=22,RecentTrades=recent['PairedTrades'],RecentWeeks=recent['Weeks'],HistoricalTrades=historical['PairedTrades'],HistoricalWeeks=historical['Weeks'],E25AvgR=metrics_by_variant['E25']['AvgR'],E50AvgR=metrics_by_variant['E50']['AvgR'],E75AvgR=recent['E75AvgR'],E100AvgR=recent['E100AvgR'],HistoricalDelta75=historical['Delta75'],RecentADelta75=recentA['Delta75'],RecentBDelta75=recentB['Delta75'],MonitorDelta75=next(x for x in tables['profit_accrual'] if x['StrategyNo']==n and x['Period']=='2026 Monitor')['Delta75'],RecentCombinedDelta75=recent['Delta75'],AllDelta75=allp['Delta75'],RecentTotalRDiff=recent['TotalRDiff'],CI_L=recent['CI_L'],CI_U=recent['CI_U'],RawP=recent['RawP'],SampleSufficient=sufficient,RecentAStability=recentAok,RecentBStability=recentBok))
 formal=[x for x in tables['contrasts'] if x['FormalActive']];adjusted=holm([x['RawP'] if x['SampleSufficient'] else 1.0 for x in formal])
 for x,padj in zip(formal,adjusted):
  x['AdjustedP']=padj
  flags={'A':x['RecentCombinedDelta75'] is not None and x['RecentCombinedDelta75']>0,'B':x['CI_L'] is not None and x['CI_L']>0,'C':x['AllDelta75'] is not None and x['AllDelta75']>0,'D':x['RecentTotalRDiff'] is not None and x['RecentTotalRDiff']>0,'E':x['HistoricalDelta75'] is not None and x['HistoricalDelta75']>0,'F':x['SampleSufficient'],'G':padj<.05}
  for k,v in flags.items():x[k]='PASS' if v else 'FAIL'
  if all(flags.values()):label='ROBUST_EARLIER_EXIT_CANDIDATE'
  elif not flags['F']:label='INSUFFICIENT_SAMPLE'
  elif x['HistoricalDelta75'] is not None and x['HistoricalDelta75']<=0 and flags['A'] and flags['B'] and x['RecentAStability'] and x['RecentBStability']:label='RECENT_EXIT_SHIFT_WATCHLIST'
  elif ((x['E25AvgR'] is not None and x['E100AvgR'] is not None and x['E25AvgR']>x['E100AvgR']) or (x['E50AvgR'] is not None and x['E100AvgR'] is not None and x['E50AvgR']>x['E100AvgR'])):label='POTENTIAL_EARLIER_PEAK'
  else:label='NOT_SUPPORTED'
  x['Verdict']=label
  tables['multiple_comparison'].append(dict(StrategyNo=x['StrategyNo'],RawP=x['RawP'],AdjustedP=padj,FamilySize=27,Pass=flags['G']))
 x=next(x for x in tables['contrasts'] if x['StrategyNo']==22);x['AdjustedP']='';x['Verdict']='DESCRIPTIVE_ONLY'
 if len(formal)!=27:raise ValueError('formal family')
 return tables

def run_full(baseline,manifest,root,out,implementation_sha):
 rows,paths,audit,e100=run_reconcile(baseline,manifest,root,out)
 variants,missing=full_variants(rows,paths)
 out=Path(out);write(out/'exit_efficiency_phase1_trade_detail_local.csv',[v for a,v in variants])
 tables=analyze(rows,variants)
 for k,v in tables.items():write(out/f'exit_efficiency_phase1_{k}.csv',v)
 if missing:write(out/'exit_efficiency_phase1_missing_checkpoint_local.csv',missing)
 record=[dict(Branch='research/exit-efficiency-phase1',PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,BaselineSHA256=BASELINE_SHA,BaselineRows=len(rows),M1Files=len(audit),M1HashesMatched=True,E100Mismatches=0,VariantMissing=len(missing),BootstrapReplicates=B,Seed=SEED,Python=sys.version.split()[0],Numpy=np.__version__,Pandas=pd.__version__,ResultsPublic=False,PortfolioSimulated=False)]
 write(out/'exit_efficiency_phase1_run_record.csv',record)
 print(json.dumps({'E100':'PASS','missing_variants':len(missing),'labels':dict(Counter(x['Verdict'] for x in tables['contrasts']))},indent=2))
 return tables

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--manifest',default='research_inputs/a3_expected_m1_manifest.csv');p.add_argument('--m1-root',required=True);p.add_argument('--out',default='/content');p.add_argument('--stage',choices=['reconcile','full'],required=True);p.add_argument('--implementation-sha',default='UNCOMMITTED');a=p.parse_args()
 if a.stage=='reconcile':run_reconcile(a.baseline,a.manifest,a.m1_root,a.out)
 else:run_full(a.baseline,a.manifest,a.m1_root,a.out,a.implementation_sha)
