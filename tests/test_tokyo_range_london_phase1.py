import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

spec=importlib.util.spec_from_file_location('b1',Path(__file__).resolve().parents[1]/'src/research/tokyo_range_london_phase1.py')
b1=importlib.util.module_from_spec(spec);spec.loader.exec_module(b1)

class B1Tests(unittest.TestCase):
 def test_event_classes_and_equality(self):
  h,l=110,90
  cases=[(True,False,111,'UP_BREAKOUT'),(True,False,110,'UP_SWEEP'),
         (True,False,90,'UP_SWEEP'),(False,True,89,'DOWN_BREAKOUT'),
         (False,True,90,'DOWN_SWEEP'),(False,True,110,'DOWN_SWEEP'),
         (True,True,100,'BOTH_SIDES'),(False,False,100,'NO_BREAK')]
  for u,d,o,want in cases: self.assertEqual(b1.classify(u,d,o,h,l),want)
 def test_alignment_and_pip(self):
  self.assertEqual([b1.aligned(e,3) for e in ['UP_BREAKOUT','DOWN_BREAKOUT','UP_SWEEP','DOWN_SWEEP']],[3,-3,-3,3])
  self.assertEqual(b1.pip_size('USDJPY'),.01)
  self.assertEqual(b1.pip_size('AUDUSD'),.0001)
 def test_dst_and_clock_boundaries(self):
  dates=pd.DatetimeIndex(['2026-03-27','2026-03-30','2026-10-23','2026-10-26'])
  ep=b1.london_endpoints(dates)
  self.assertEqual(list(ep[8].hour),[8,7,7,8])
  self.assertTrue(np.all((ep[9].asi8-ep[8].asi8)==3600*10**9))
  self.assertTrue(np.all((ep[11].asi8-ep[9].asi8)==2*3600*10**9))
 def test_synthetic_daily_and_no_lookahead(self):
  d=pd.Timestamp('2026-06-01')
  ts=[]
  # Tokyo 09:00-14:59 JST (00:00-05:59 UTC).
  for n in range(360):
   t=pd.Timestamp('2026-06-01',tz='UTC')+pd.Timedelta(minutes=n)
   ts.append((t,100.,101.,99.))
  # London 08:00-08:59 BST (07:00-07:59 UTC): one strict high break.
  for n in range(60):
   t=pd.Timestamp('2026-06-01 07:00',tz='UTC')+pd.Timedelta(minutes=n)
   ts.append((t,100.,102. if n==59 else 101.,99.))
  ts += [(pd.Timestamp('2026-06-01 08:00',tz='UTC'),101.5,999.,0.1),
         (pd.Timestamp('2026-06-01 10:00',tz='UTC'),102.5,999.,0.1)]
  utc=pd.DatetimeIndex([x[0] for x in ts]);j=utc.tz_convert('Asia/Tokyo');l=utc.tz_convert('Europe/London')
  bars=pd.DataFrame({'UTC':utc,'JDate':j.tz_localize(None).normalize(),'LDate':l.tz_localize(None).normalize(),
       'JMinute':j.hour*60+j.minute,'LMinute':l.hour*60+l.minute,
       'Open':[x[1] for x in ts],'High':[x[2] for x in ts],'Low':[x[3] for x in ts]})
  row=b1.daily_events('AUDUSD',bars).set_index('Date').loc[d]
  self.assertEqual(row.TokyoBars,360);self.assertEqual(row.EventBars,60)
  self.assertEqual(row.TokyoHigh,101);self.assertEqual(row.TokyoLow,99)
  self.assertEqual(row.Event,'UP_BREAKOUT')
  self.assertAlmostEqual(row.AlignedPips,10000)
  # The extreme 09:00 and 11:00 bar highs/lows must never classify an event.
  bars.loc[bars.LMinute.eq(540),'High']=1000
  row2=b1.daily_events('AUDUSD',bars).set_index('Date').loc[d]
  self.assertEqual(row2.Event,'UP_BREAKOUT')
  bars=bars[~bars.UTC.eq(pd.Timestamp('2026-06-01 00:00',tz='UTC'))]
  row3=b1.daily_events('AUDUSD',bars).set_index('Date').loc[d]
  self.assertEqual(row3.Status,'INSUFFICIENT_TOKYO_RANGE_DATA')
 def test_holm_and_bootstrap_replication(self):
  np.testing.assert_allclose(b1.holm([.02,.001,.04]),[.04,.003,.04])
  vals=np.array([1.,2.,4.]);dates=pd.to_datetime(['2026-01-05','2026-01-06','2026-01-12'])
  first,draws=b1.week_draws('2026-01-05','2026-01-18')
  lo,hi,p,n,dist=b1.bootstrap(vals,dates,first,draws)
  self.assertEqual(n,5000)
  sample=draws[0]
  replicated=[]
  for i in sample: replicated.extend(vals[[0,1]] if i==0 else vals[[2]])
  self.assertAlmostEqual(dist[0],np.mean(replicated))
  self.assertLessEqual(lo,hi)

if __name__=='__main__': unittest.main()
