"""Independent raw-CSV Decimal metrics and expanded-trade bootstrap verification."""
import sys,csv,json,hashlib
from decimal import Decimal as D
from pathlib import Path
from datetime import datetime,timedelta
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import au_china_late_month_phase1 as a

def verify(baseline,out):
 raw=Path(baseline).read_bytes(); assert hashlib.sha256(raw).hexdigest()==a.BASELINE_HASH
 original=list(csv.DictReader(raw.decode('utf-8-sig').splitlines())); assert len(original)==16298
 rows=[]
 for r in original:
  if r['StrategyNo']!='25': continue
  t=datetime.fromisoformat(r['EntryTime']); d=t.day
  assert (9<=d<=15) or d>=25
  rows.append({**r,'Segment':'EARLY_MONTH' if d<=15 else 'LATE_MONTH','EntryJSTDate':str(t.date()),'WeekMondayJST':str(t.date()-timedelta(days=t.weekday()))})
 out=Path(out)
 def read(name):return list(csv.DictReader((out/(a.PREFIX+name+'.csv')).open()))
 def check_metric(record,group):
  rs=[D(r['R']) for r in group]; n=len(rs); assert n==int(record['Trades'])
  total=sum(rs,D(0)); gain=sum((r for r in rs if r>0),D(0)); loss=-sum((r for r in rs if r<0),D(0))
  expected={'TotalR':total,'AvgR':total/n if n else None,'PF':gain/loss if loss else (D('Infinity') if gain else None)}
  for k,v in expected.items():
   if v is None:assert record[k]==''
   elif v.is_infinite():assert float(record[k])==float('inf')
   else:assert abs(D(record[k])-v)<D('1e-10'),(record,k,v)
 for record in read('segment_period_summary'):
  start,end=a.PERIODS[record['Period']]
  check_metric(record,[r for r in rows if start<=r['EntryJSTDate']<end and r['Segment']==record['Segment']])
 for record in read('yearly_summary'):
  check_metric(record,[r for r in rows if r['EntryJSTDate'][:4]==record['Year'] and r['Segment']==record['Segment']])
 assigned=read('trade_assignment');assert len(assigned)==len(rows)
 for actual,expected in zip(assigned,rows):
  for key in ('EntryTime','Segment','EntryJSTDate','WeekMondayJST','R'):assert actual[key]==expected[key]
 # Independently create buckets of actual trade arrays; expand sampled clusters.
 def buckets(group):
  keys=sorted(set(r['WeekMondayJST'] for r in group))
  return [[np.array([float(r['R']) for r in group if r['WeekMondayJST']==w and r['Segment']==s]) for s in a.SEGMENTS] for w in keys]
 h=[r for r in rows if '2015-01-01'<=r['EntryJSTDate']<'2022-01-01']; bh=buckets(h)
 comparisons=('Recent Combined','Recent A','Recent B','2026 Monitor'); ci=read('contrasts'); max_error=0
 for p in comparisons:
  start,end=a.PERIODS[p]; recent=[r for r in rows if start<=r['EntryJSTDate']<end]; br=buckets(recent)
  rng=np.random.Generator(np.random.PCG64(20260913)); expanded=[]
  for _ in range(5000):
   ih=rng.integers(len(bh),size=len(bh)); ir=rng.integers(len(br),size=len(br))
   means=[]
   for j in (0,1):
    hv=np.concatenate([bh[i][j] for i in ih]); rv=np.concatenate([br[i][j] for i in ir]);means.append(rv.mean()-hv.mean())
   expanded.append([means[1],means[0],means[1]-means[0]])
  expanded=np.array(expanded); aggregate=a.bootstrap(h,recent)
  np.testing.assert_allclose(expanded,aggregate,atol=2e-14,rtol=0)
  max_error=max(max_error,float(np.max(np.abs(expanded-aggregate))))
  for i,label in enumerate(('LATE_DECAY','EARLY_DECAY','RELATIVE_DECAY')):
   match=[x for x in ci if x['Comparison']==p and x['Contrast']==label]
   if not match:continue
   record=match[0]
   # Independent sorted order-statistic interpolation, no np.quantile.
   vals=sorted(expanded[:,i]); endpoints=[]
   for q in (.025,.975):
    pos=q*4999; k=int(pos);endpoints.append(vals[k]+(pos-k)*(vals[k+1]-vals[k]))
   if record['CIStatus']=='OK':np.testing.assert_allclose(endpoints,[float(record['CILower']),float(record['CIUpper'])],atol=2e-14,rtol=0)
 from edge_decay_analysis import PERIODS as old
 for new,prior in [('Historical','Historical'),('Recent A','RecentA'),('Recent B','RecentB'),('2026 Monitor','Monitor2026')]:assert a.PERIODS[new]==old[prior]
 assert old['RecentCombined']==('2022-01-01','2026-01-01')
 report=dict(Status='PASS',DecimalMetricCells=36,BootstrapReplicatesChecked=20000,MaxReplicateAbsError=max_error,
  AssignmentRowsChecked=len(rows),PeriodHelperMatch='four disjoint periods identical; Combined intentionally includes 2026',RepresentativeRows=len(read('representative_audit')))
 (out/(a.PREFIX+'verification.json')).write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__':verify(sys.argv[1],sys.argv[2])
