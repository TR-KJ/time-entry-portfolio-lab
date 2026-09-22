"""Independent post-run aggregation, E100, Holm and bootstrap spot checks."""
import argparse,csv,hashlib,math,sys
from collections import defaultdict
from datetime import datetime,timedelta
from decimal import Decimal
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from exit_efficiency_phase1 import BASELINE_SHA,PERIODS,SEED,B,holm

def read(p):return list(csv.DictReader(open(p,newline='',encoding='utf-8')))
def near(a,b,tol=1e-9):return math.isclose(float(a),float(b),rel_tol=0,abs_tol=tol)
def verify(baseline,out):
 raw=Path(baseline).read_bytes();assert hashlib.sha256(raw).hexdigest()==BASELINE_SHA
 base=read(baseline);assert len(base)==16298
 recon=read(Path(out)/'exit_efficiency_phase1_e100_reconciliation.csv');assert len(recon)==1 and recon[0]['Status']=='PASS' and recon[0]['MismatchCount']=='0'
 details=read(Path(out)/'exit_efficiency_phase1_trade_detail_local.csv');assert len(details)==len(base)*4
 e100={(x['StrategyNo'],x['EntryTime']):x for x in details if x['Label']=='E100'}
 assert len(e100)==len(base)
 for r in base:
  v=e100[(r['StrategyNo'],r['EntryTime'])]
  assert v['Status']=='OK' and v['CloseTime']==r['CloseTime'] and v['ExitReason']==r['ExitReason'] and near(v['R'],r['R'],1e-8)
 grouped=defaultdict(list)
 for v in details:
  if v['Status']=='OK':grouped[(v['StrategyNo'],v['Label'])].append(v)
 checked=0
 for x in read(Path(out)/'exit_efficiency_phase1_period_summary.csv'):
  a,z=PERIODS[x['Period']]
  group=[v for v in grouped[(x['StrategyNo'],x['Variant'])] if a<=v['EntryTime'][:10]<z]
  values=[Decimal(v['R']) for v in group];total=sum(values,Decimal(0));gain=sum((v for v in values if v>0),Decimal(0));loss=-sum((v for v in values if v<0),Decimal(0))
  assert len(group)==int(x['Trades']) and near(total,x['TotalR'])
  if group:assert near(total/len(group),x['AvgR'])
  if loss:assert near(gain/loss,x['PF'])
  checked+=1
 contrasts=read(Path(out)/'exit_efficiency_phase1_contrasts.csv');formal=[x for x in contrasts if x['FormalActive']=='True'];assert len(formal)==27
 p=[float(x['RawP']) if x['SampleSufficient']=='True' else 1.0 for x in formal]
 for x,adj in zip(formal,holm(p)):assert near(x['AdjustedP'],adj)
 # Independent direct raw-trade cluster expansion for first two eligible strategies.
 eligible=[x for x in formal if x['SampleSufficient']=='True'][:2]
 for x in eligible:
  n=x['StrategyNo'];pairs=[]
  e75={(v['StrategyNo'],v['EntryTime']):v for v in details if v['Label']=='E75' and v['StrategyNo']==n and '2022-01-01'<=v['EntryTime'][:10]<'2026-09-10'}
  weeks=defaultdict(list)
  for (nn,t),v in e75.items():
   d=datetime.fromisoformat(t).date();k=(d-timedelta(days=d.weekday())).isoformat();weeks[k].append((float(v['R']),float(e100[(nn,t)]['R'])))
  keys=sorted(weeks);rng=np.random.Generator(np.random.PCG64(SEED));draws=rng.integers(0,len(keys),size=(B,len(keys)))
  vals=[]
  for draw in draws:
   pair=[v for i in draw for v in weeks[keys[i]]];vals.append(np.mean([a-b for a,b in pair]))
  ci=np.quantile(vals,[.025,.975]);assert near(ci[0],x['CI_L'],1e-12) and near(ci[1],x['CI_U'],1e-12)
  assert near((1+sum(v<=0 for v in vals))/(B+1),x['RawP'],1e-12)
 print('E100 rows',len(e100),'period cells',checked,'Holm',len(formal),'bootstrap spots',len(eligible),'PASS')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);a=p.parse_args();verify(a.baseline,a.out)
