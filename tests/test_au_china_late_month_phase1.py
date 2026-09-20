import sys,unittest
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import au_china_late_month_phase1 as a

class Tests(unittest.TestCase):
 def test_segments_jst(self):
  for d in (8,16,24):
   with self.assertRaises(ValueError): a.segment(datetime(2024,1,d,tzinfo=ZoneInfo('Asia/Tokyo')))
  for d in (9,15,25,31):
   self.assertEqual(a.segment(datetime(2024,1,d,tzinfo=ZoneInfo('Asia/Tokyo'))),'EARLY_MONTH' if d<20 else 'LATE_MONTH')
  self.assertEqual(a.segment(datetime.fromisoformat('2024-01-24T16:00:00+00:00')),'LATE_MONTH')
 def test_boundaries(self):
  for p,(start,end) in a.PERIODS.items():
   for date,expected in ((start,1),(end,0),((datetime.fromisoformat(start)-timedelta(days=1)).date().isoformat(),0),((datetime.fromisoformat(end)-timedelta(days=1)).date().isoformat(),1)):
    self.assertEqual(len(a.select([{'EntryJSTDate':date}],p)),expected)
 def test_week_and_identity(self):
  r=dict(StrategyNo=25,Strategy='25_AU_China_Demand',Pair='AU',Direction='Long',EntryTime='2024-02-29 10:00:00',ScheduledExitTime='2024-02-29 15:50:00',SL='40',TP='40',R=Decimal('1'))
  self.assertEqual(a.assign([r])[0]['WeekMondayJST'],'2024-02-26')
  for key,value in [('Pair','USDJPY'),('Direction','Short'),('SL','30'),('EntryTime','2024-02-29 01:00:00'),('Strategy','wrong')]:
   with self.assertRaises(ValueError): a.assign([{**r,key:value}])
 def test_metrics(self):
  rs=[{'R':x,'WeekMondayJST':'2024-01-01'} for x in (1,-.5,0)]
  m=a.metrics(rs); self.assertAlmostEqual(m['AvgR'],1/6); self.assertEqual(m['PF'],2); self.assertEqual(m['TotalR'],.5)
  self.assertEqual(m['WinRate'],1/3); self.assertEqual(m['AvgLossR'],-.5)
  self.assertIsNone(a.metrics([])['AvgR']); self.assertIsNone(a.metrics([])['PF'])
 def test_classifier(self):
  ok=dict(CIStatus='OK',CIUpper=-.01)
  checks,v=a.classify(.2,-.1,-.02,-.08,ok,.1,.3)
  self.assertEqual(v,'LATE_MONTH_DECAY_SUPPORTED'); self.assertTrue(all(x=='PASS' for x in checks.values()))
  self.assertEqual(a.classify(.2,-.1,-.02,-.08,{**ok,'CIUpper':0},.1,.3)[1],'WEAK_DECAY_SIGNAL')
  self.assertEqual(a.classify(.2,-.1,-.2,.1,ok,.1,.3)[1],'NOT_SUPPORTED')
  self.assertEqual(a.classify(0,-.1,-.02,-.08,ok,.1,.3)[1],'NOT_SUPPORTED')
 def test_paired_bootstrap_and_low_sample(self):
  h=[];r=[]
  for i in range(24):
   for s in a.SEGMENTS:
    for _ in range(2):
     h.append(dict(WeekMondayJST=f'{i:03d}',Segment=s,R=i/24))
     r.append(dict(WeekMondayJST=f'{i:03d}',Segment=s,R=i/24-.1))
  d=a.bootstrap(h,r,100)
  np.testing.assert_allclose(d[:,2],0,atol=1e-15)
  self.assertEqual(a.confidence(d,h,r,0)['CIStatus'],'OK')
  self.assertEqual(a.confidence(d,h[:2],r,0)['CIStatus'],'INSUFFICIENT_SAMPLE')
  np.testing.assert_array_equal(d,a.bootstrap(h,r,100))
 def test_hash_rejection(self):
  import tempfile
  with tempfile.NamedTemporaryFile() as f:
   f.write(b'wrong');f.flush()
   with self.assertRaises(ValueError): a.load_baseline(f.name)

if __name__=='__main__':unittest.main()
