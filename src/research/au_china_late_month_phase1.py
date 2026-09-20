"""Preregistered Strategy25 diagnostic. Never generates or excludes trades."""
import argparse
import csv
import hashlib
import json
import platform
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
from edge_decay_analysis import load_baseline, BASELINE_HASH

PLAN_SHA = 'b49e7766bc2a710c3afae7685476e0fa47d2fecb'
BRANCH = 'research/au-china-late-month-edge-decay-phase1'
PREFIX = 'au_china_late_month_phase1_'
SEED, REPS = 20260913, 5000
SEGMENTS = ('EARLY_MONTH', 'LATE_MONTH')
PERIODS = {
 'Historical': ('2015-01-01','2022-01-01'),
 'Recent A': ('2022-01-01','2024-01-01'),
 'Recent B': ('2024-01-01','2026-01-01'),
 '2026 Monitor': ('2026-01-01','2026-09-10'),
 'Recent Combined': ('2022-01-01','2026-09-10'),
 'ALL': ('2015-01-01','2026-09-10'),
}

def segment(t):
 if t.tzinfo is None: raise ValueError('Explicit JST required')
 d = t.astimezone(ZoneInfo('Asia/Tokyo')).day
 if 9 <= d <= 15: return SEGMENTS[0]
 if d >= 25: return SEGMENTS[1]
 raise ValueError('Strategy25 calendar identity error')

def assign(rows):
 own = [r.copy() for r in rows if r['StrategyNo']==25]
 if not own: raise ValueError('No Strategy25 trades')
 for r in own:
  if r['Strategy'] != '25_AU_China_Demand' or r['Pair'] != 'AU' or r['Direction'] != 'Long':
   raise ValueError('Strategy25 identity error')
  t = datetime.fromisoformat(r['EntryTime'])
  if t.tzinfo is not None: raise ValueError('Expected naive JST')
  t = t.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
  scheduled = datetime.fromisoformat(r['ScheduledExitTime'])
  if (t.weekday()>4 or (t.hour,t.minute,t.second)!=(10,0,0) or
      scheduled != t.replace(tzinfo=None,hour=15,minute=50) or
      float(r['SL'])!=40 or float(r['TP'])!=40):
   raise ValueError('Strategy25 fixed rule error')
  # Frozen loader PAIR_ALIASES explicitly maps AUDUSD -> AU.
  r['CanonicalSymbol'] = 'AUDUSD'
  r['Segment'] = segment(t)
  r['EntryJSTDate'] = t.date().isoformat()
  r['WeekMondayJST'] = (t.date()-timedelta(days=t.weekday())).isoformat()
 return own

def select(rows, period):
 start,end = PERIODS[period]
 return [r for r in rows if start<=r['EntryJSTDate']<end]

def metrics(rows):
 rs = np.array([float(r['R']) for r in rows]); n=len(rs)
 wins, losses=rs[rs>0],rs[rs<0]
 gain, loss=float(wins.sum()), -float(losses.sum())
 return dict(Trades=n, Weeks=len({r['WeekMondayJST'] for r in rows}),
  AvgR=float(rs.mean()) if n else None, TotalR=float(rs.sum()),
  PF=gain/loss if loss else (float('inf') if gain else None),
  WinRate=len(wins)/n if n else None,
  AvgWinR=float(wins.mean()) if len(wins) else None,
  AvgLossR=float(losses.mean()) if len(losses) else None, LOW_SAMPLE=n<30)

def clusters(rows):
 keys=sorted({r['WeekMondayJST'] for r in rows}); lookup={k:i for i,k in enumerate(keys)}
 sums=np.zeros((len(keys),2)); counts=np.zeros((len(keys),2),dtype=int)
 for r in rows:
  i,j=lookup[r['WeekMondayJST']],SEGMENTS.index(r['Segment'])
  sums[i,j]+=float(r['R']); counts[i,j]+=1
 return sums,counts

def bootstrap(h,recent,reps=REPS):
 hs,hc=clusters(h); rs,rc=clusters(recent)
 draws=np.full((reps,3),np.nan); rng=np.random.Generator(np.random.PCG64(SEED))
 if not len(hs) or not len(rs): return draws
 for i in range(reps):
  hi=rng.integers(0,len(hs),size=len(hs)); ri=rng.integers(0,len(rs),size=len(rs))
  with np.errstate(invalid='ignore',divide='ignore'):
   decay=rs[ri].sum(axis=0)/rc[ri].sum(axis=0)-hs[hi].sum(axis=0)/hc[hi].sum(axis=0)
  draws[i]=decay[1],decay[0],decay[1]-decay[0]
 return draws

def sufficient(rows,seg):
 m=metrics([r for r in rows if r['Segment']==seg])
 return m['Trades']>=30 and m['Weeks']>=20

def confidence(draws,h,r,index):
 required=(SEGMENTS[1],) if index==0 else ((SEGMENTS[0],) if index==1 else SEGMENTS)
 ok=all(sufficient(p,s) for p in (h,r) for s in required) and np.isfinite(draws[:,index]).all()
 if not ok: return dict(CILower=None,CIUpper=None,CIStatus='INSUFFICIENT_SAMPLE')
 lo,hi=np.quantile(draws[:,index],[.025,.975],method='linear')
 return dict(CILower=float(lo),CIUpper=float(hi),CIStatus='OK')

def classify(historical,late,early,relative,ci,recentb,monitor):
 checks=dict(A=historical is not None and historical>0,
  B=late is not None and late<0,
  C=ci['CIStatus']=='OK' and ci['CIUpper']<0,
  D=relative is not None and relative<0,
  E=historical is not None and any(x is not None and x<historical for x in (recentb,monitor)))
 verdict=('LATE_MONTH_DECAY_SUPPORTED' if all(checks.values()) else
  'WEAK_DECAY_SIGNAL' if checks['B'] and checks['D'] and not checks['C'] else 'NOT_SUPPORTED')
 return {k:'PASS' if v else 'FAIL' for k,v in checks.items()},verdict

def write_csv(path,records):
 with Path(path).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)

def analyze(own):
 summary=[]; yearly=[]; contrasts=[]
 for p,(start,end) in PERIODS.items():
  for s in SEGMENTS:
   summary.append(dict(Period=p,Segment=s,Start=start,EndExclusive=end,
    **metrics([r for r in select(own,p) if r['Segment']==s])))
 for year in range(2015,2027):
  for s in SEGMENTS:
   yearly.append(dict(Year=year,Segment=s,**metrics([r for r in own if r['EntryJSTDate'][:4]==str(year) and r['Segment']==s])))
 lookup={(r['Period'],r['Segment']):r for r in summary}
 h=select(own,'Historical')
 for p in ('Recent Combined','Recent A','Recent B','2026 Monitor'):
  recent=select(own,p); draws=bootstrap(h,recent)
  d=[]
  for s in SEGMENTS:
   a,b=lookup[p,s]['AvgR'],lookup['Historical',s]['AvgR']; d.append(a-b if a is not None and b is not None else None)
  points=(d[1],d[0],d[1]-d[0] if None not in d else None)
  for i,label in enumerate(('LATE_DECAY','EARLY_DECAY','RELATIVE_DECAY')):
   if p!='Recent Combined' and i==2: continue
   contrasts.append(dict(Comparison=p,Contrast=label,Estimate=points[i],**confidence(draws,h,recent,i)))
 primary=contrasts[:3]
 checks,verdict=classify(lookup['Historical',SEGMENTS[1]]['AvgR'],*(c['Estimate'] for c in primary),primary[0],
  lookup['Recent B',SEGMENTS[1]]['AvgR'],lookup['2026 Monitor',SEGMENTS[1]]['AvgR'])
 lower=sum(lookup[p,SEGMENTS[1]]['AvgR']<lookup['Historical',SEGMENTS[1]]['AvgR'] for p in ('Recent A','Recent B','2026 Monitor'))
 return dict(segment_period_summary=summary,yearly_summary=yearly,contrasts=contrasts,
  bootstrap_ci=[dict(**c,Seed=SEED,Replicates=REPS,Method='calendar-week cluster percentile linear') for c in contrasts]),checks,verdict,lower

def run(baseline,output_dir,implementation_sha):
 if len(implementation_sha)!=40 or any(c not in '0123456789abcdef' for c in implementation_sha):
  raise ValueError('Exact committed implementation SHA required')
 rows=load_baseline(baseline); own=assign(rows)
 tables,checks,verdict,lower=analyze(own)
 out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
 for name,records in tables.items(): write_csv(out/(PREFIX+name+'.csv'),records)
 write_csv(out/(PREFIX+'trade_assignment.csv'),own)
 reps=[]
 for year in (2015,2021,2022,2024,2026):
  for s in SEGMENTS:
   group=sorted([r for r in own if r['Segment']==s and r['EntryJSTDate'][:4]==str(year)],key=lambda r:r['EntryTime'])
   if group: reps.extend([group[0],group[-1]] if len(group)>1 else group)
 write_csv(out/(PREFIX+'representative_audit.csv'),reps)
 record=dict(BaselineSHA256=BASELINE_HASH,BaselineTrades=len(rows),Strategies=28,Strategy25Trades=len(own),
  EarlyTrades=sum(r['Segment']==SEGMENTS[0] for r in own),LateTrades=sum(r['Segment']==SEGMENTS[1] for r in own),
  Branch=BRANCH,PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,RunJST=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
  Python=platform.python_version(),NumPy=np.__version__,Seed=SEED,Replicates=REPS,MinimumTrades=30,MinimumWeeks=20,
  **checks,Verdict=verdict,Phase2Candidate=verdict=='LATE_MONTH_DECAY_SUPPORTED',LateLowerPeriods=lower,
  FormalCIStatus=tables['contrasts'][0]['CIStatus'],FreshHoldout=False,BaselineRecalculated=False,
  PortfolioSimulation=False,LiveChanged=False,Periods=json.dumps(PERIODS),
  CSVHashes=json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob(PREFIX+'*.csv')) if not p.name.endswith('run_record.csv')},sort_keys=True))
 write_csv(out/(PREFIX+'run_record.csv'),[record])
 print(json.dumps(record,ensure_ascii=False,indent=2)); return tables,record

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--baseline',required=True)
 p.add_argument('--output-dir',default='/content'); p.add_argument('--implementation-sha',required=True)
 a=p.parse_args(); run(a.baseline,a.output_dir,a.implementation_sha)
