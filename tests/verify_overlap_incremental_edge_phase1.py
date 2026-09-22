"""Independent source-CSV and output audit, including raw-trade bootstrap spot checks."""
import argparse,bisect,csv,hashlib,math,sys,json
from collections import defaultdict,Counter
from datetime import datetime,date,timedelta
from decimal import Decimal
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from overlap_incremental_edge_phase1 import BASELINE_SHA,PAIRS,STATES,PERIODS,holm,SEED,B

def read(path):return list(csv.DictReader(open(path,newline='',encoding='utf-8')))
def near(a,b):return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-9)
def verify(baseline,out):
 raw=Path(baseline).read_bytes();assert hashlib.sha256(raw).hexdigest()==BASELINE_SHA
 source=read(baseline);assert len(source)==16298
 assignment=read(Path(out)/'overlap_phase1_trade_assignment_local.csv');assert len(assignment)==32135
 byport=defaultdict(list)
 for r in assignment:byport[r['Portfolio']].append(r)
 assert len(byport['Primary27'])==15837 and len(byport['Old28'])==16298
 assert all(r['StrategyNo']!='22' for r in byport['Primary27'])
 for name,rr in byport.items():
  assert len({(r['StrategyNo'],r['EntryTime']) for r in rr})==len(rr)
  assert all(r['State'] in STATES for r in rr)
  # Independent strict-interval classification for deterministic first/last
  # overlap trade of each strategy, checking original source identities.
  representatives=[]
  for n in sorted({int(r['StrategyNo']) for r in rr}):
   ov=sorted((r for r in rr if int(r['StrategyNo'])==n and r['State']=='SAME_SYMBOL_SAME_DIR_OPEN'),key=lambda r:r['EntryTime'])
   if ov:representatives.extend([ov[0],ov[-1]])
  source_ids={(r['StrategyNo'],r['EntryTime']) for r in source}
  for r in representatives:
   assert (r['StrategyNo'],r['EntryTime']) in source_ids
   t=datetime.fromisoformat(r['EntryTime'])
   strict=[x for x in rr if x['Symbol']==r['Symbol'] and x['Direction']==r['Direction'] and datetime.fromisoformat(x['EntryTime'])<t<datetime.fromisoformat(x['CloseTime'])]
   assert strict
   opposite=[x for x in rr if x['Symbol']==r['Symbol'] and x['Direction']!=r['Direction'] and datetime.fromisoformat(x['EntryTime'])<t<datetime.fromisoformat(x['CloseTime'])]
   assert not opposite
   assert not any(x['Symbol']==r['Symbol'] and x['CloseTime']==r['EntryTime'] for x in rr)
  print(name,'representative overlap trades',len(representatives),'PASS')
 cells=read(Path(out)/'overlap_phase1_period_summary.csv');checked=0
 for x in cells:
  a,z=PERIODS[x['Period']]
  rr=[r for r in byport[x['Portfolio']] if r['StrategyNo']==x['StrategyNo'] and r['State']==x['State'] and a<=r['EntryTime'][:10]<z]
  vals=[Decimal(r['R']) for r in rr];total=sum(vals,Decimal(0));gain=sum((v for v in vals if v>0),Decimal(0));loss=-sum((v for v in vals if v<0),Decimal(0))
  assert len(rr)==int(x['Trades']) and near(total,x['TotalR'])
  if rr:assert near(total/len(rr),x['AvgR'])
  if loss:assert near(gain/loss,x['PF'])
  checked+=1
 contrasts=read(Path(out)/'overlap_phase1_contrasts.csv');primary=[x for x in contrasts if x['Portfolio']=='Primary27'];assert len(primary)==27
 adjusted=holm([float(x['RawP']) for x in primary])
 for x,p in zip(primary,adjusted):assert near(x['AdjustedP'],p)
 # Raw-trade cluster expansion, independent of production weekly sum array.
 for number in ('18','20'):
  x=next(x for x in primary if x['StrategyNo']==number)
  if x['SampleSufficient']!='True' or x['BootstrapValid']!='True':continue
  own=[r for r in byport['Primary27'] if r['StrategyNo']==number and '2022-01-01'<=r['EntryTime'][:10]<'2026-09-10']
  weeks=defaultdict(list)
  for r in own:
   d=date.fromisoformat(r['EntryTime'][:10]);k=(d-timedelta(days=d.weekday())).isoformat();weeks[k].append(r)
  keys=sorted(weeks);rng=np.random.Generator(np.random.PCG64(SEED));draws=rng.integers(0,len(keys),size=(B,len(keys)))
  vals=[]
  for draw in draws:
   group=[r for i in draw for r in weeks[keys[i]]]
   ov=[float(r['R']) for r in group if r['State']=='SAME_SYMBOL_SAME_DIR_OPEN']
   no=[float(r['R']) for r in group if r['State']=='NO_SAME_SYMBOL_OPEN']
   vals.append((np.mean(ov),np.mean(no)))
  vals=np.array(vals);d=vals[:,0]-vals[:,1]
  for actual,col in [(np.quantile(vals[:,0],[.025,.975]),('OverlapCI_L','OverlapCI_U')),(np.quantile(vals[:,1],[.025,.975]),('NoOverlapCI_L','NoOverlapCI_U')),(np.quantile(d,[.025,.975]),('DiffCI_L','DiffCI_U'))]:
   assert near(actual[0],x[col[0]]) and near(actual[1],x[col[1]])
  assert near((1+sum(d>=0))/(B+1),x['RawP'])
  print('bootstrap raw expansion',number,'5000 draws PASS')
 result=dict(BaselineSHA256=BASELINE_SHA,Primary27=15837,Old28=16298,PeriodCellsChecked=checked,HolmChecked=27)
 print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--out',required=True);a=p.parse_args();verify(a.baseline,a.out)
