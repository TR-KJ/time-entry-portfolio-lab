import unittest,sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import volatility_phase3 as p
from verify_volatility_phase3 import verify

def row(i,entry,close,r='1',q='Q5',sl='10'):
 return dict(RowId=i,StrategyNo=1,Strategy='test',Pair='EJ',EntryTime=datetime.fromisoformat(entry),CloseTime=datetime.fromisoformat(close),SL=D(sl),Pips=D(r)*D(sl),R=D(r),primaryQuintile=q,robustnessQuintile=q)
class Tests(unittest.TestCase):
 def test_mapping(self):
  for c,vs in p.RISKS.items():
   for q,v in zip(p.p2.QUINTILES,vs):self.assertEqual(p.risk(c,q),D(v))
   self.assertEqual(p.risk(c,p.p1.INS),D('.9'))
  with self.assertRaises(ValueError):p.risk('R1_MILD','Q6')
 def test_rollover(self):
  self.assertEqual(str(p.money.week_start(datetime(2025,1,6,5,59))),'2024-12-30 06:00:00')
  self.assertEqual(str(p.money.week_start(datetime(2025,1,6,6))),'2025-01-06 06:00:00')
 def test_fixed_and_compound(self):
  rows=[row(0,'2025-01-06 07:00','2025-01-06 08:00',q='Q1'),row(1,'2025-01-07 07:00','2025-01-07 08:00',q='Q5',sl='20'),row(2,'2025-01-13 07:00','2025-01-13 08:00')]
  m,l,w=p.simulate(rows,'R1_MILD','primary');self.assertEqual([r['WeeklyBase'] for r in l],[D(500000),D(500000),D(509000)])
  self.assertEqual([r['YenPnL'] for r in l],[D(3500),D(5500),D(5599)]);verify(rows,'R1_MILD','primary',m,l)
 def test_skip_ins_and_initial_dd(self):
  rows=[row(0,'2025-01-06 07:00','2025-01-06 08:00',q='Q1'),row(1,'2025-01-07 07:00','2025-01-07 08:00','-1',p.p1.INS)]
  m,l,_=p.simulate(rows,'F1_Q1_OFF','primary');self.assertEqual(len(l),1);self.assertEqual(m['SkippedTrades'],1);self.assertEqual(m['MaxDDPct'],D('.9'));verify(rows,'F1_Q1_OFF','primary',m,l)
 def test_boundaries_and_insolvency(self):
  for r in [row(0,'2025-01-06 07:00','2025-01-13 06:00'),row(0,'2023-12-31 07:00','2024-01-01 01:00'),row(0,'2025-01-06 07:00','2025-01-06 08:00','-200')]:
   with self.assertRaises(ValueError):p.simulate([r],'R0_FIXED_090','primary')
 def test_reset(self):
  r=row(0,'2026-01-02 07:00','2026-01-02 08:00');m,l,_=p.simulate([r],'R0_FIXED_090','primary');self.assertEqual(l[0]['WeeklyBase'],D(500000))
 def test_decision_equalities(self):
  s=[dict(Method=m,Candidate=c,Period=k,FinalCapital=D(600000),MaxDDPct=D(10)) for m in p.p1.METHODS for c in p.RISKS for k in p.PERIODS]
  self.assertTrue(all(r['Decision']=='NOT_CANDIDATE' for r in p.decide(s,True)))
  for r in s:
   if r['Candidate']=='R1_MILD' and r['Method']=='primary':
    if r['Period'] in ['ALL','RecentB']:r['FinalCapital']+=1
    r['MaxDDPct']=D('12.5')
  d=p.decide(s,True)[0];self.assertEqual(d['Decision'],'ECONOMIC_VALUE_CANDIDATE');self.assertTrue(d['RobustnessConsistent'])
  self.assertEqual(p.decide(s,False)[0]['Decision'],'UNDETERMINED')
  for r in s:
   if (r['Candidate'],r['Method'],r['Period'])==('R1_MILD','primary','ALL'):r['MaxDDPct']=D('12.50001')
  self.assertFalse(p.decide(s,True)[0]['DrawdownPass'])
if __name__=='__main__':unittest.main()
