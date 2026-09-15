import unittest, sys, tempfile, copy
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import volatility_phase4 as p
from test_volatility_phase3 import row
from verify_volatility_phase4 import verify, verify_decision

class Tests(unittest.TestCase):
 def test_fixed_mapping(self):
  for c,values in [('R0_FIXED_090',['.9']*5),('R2_MODERATE',['.5','.7','.9','1.1','1.3'])]:
   for q,v in zip(['Q1','Q2','Q3','Q4','Q5'],values):self.assertEqual(p.risk(c,q),D(v))
   self.assertEqual(p.risk(c,p.p3.p1.INS),D('.9'))
  for c,q in [('R1_MILD','Q1'),('R3','Q5'),('R2_MODERATE','Q6')]:
   with self.assertRaises(ValueError):p.risk(c,q)
 def test_exact_exclusion(self):
  rows=[dict(RowId=i,StrategyNo=s['StrategyNo'],Strategy=s['Strategy']) for i,s in enumerate(p.p3.p1.STRATEGIES)]
  before=copy.deepcopy(rows);own=p.scenario(rows)
  self.assertEqual(len(own),27);self.assertEqual(rows,before);self.assertNotIn(22,[r['StrategyNo'] for r in own])
  rows[0]['Strategy']='wrong'
  with self.assertRaises(ValueError):p.scenario(rows)
 def test_r2_compound_and_independent(self):
  rows=[row(0,'2025-01-06 07:00','2025-01-06 08:00',q='Q1'),row(1,'2025-01-07 07:00','2025-01-07 08:00',q='Q5',sl='20'),row(2,'2025-01-13 07:00','2025-01-13 08:00','-1',p.p3.p1.INS)]
  m,l,w=p.simulate(rows,'R2_MODERATE','primary');self.assertEqual([r['WeeklyBase'] for r in l],[D(500000),D(500000),D(509000)])
  self.assertEqual([r['YenPnL'] for r in l],[D(2500),D(6500),D('-4581')]);verify(rows,'R2_MODERATE','primary',m,l)
 def fixture(self):
  s=[dict(Method=m,Candidate=c,Period=k,FinalCapital=D(600000),MaxDDPct=D(10),WorstDayPct=D(-10)) for m in p.p3.p1.METHODS for c in p.CANDIDATES for k in p.p3.PERIODS]
  for r in s:
   if r['Candidate']=='R2_MODERATE' and r['Method']=='primary':
    if r['Period'] in ['ALL','RecentB']:r['FinalCapital']+=1
    r['MaxDDPct']=D('12.5')
  return s
 def test_gate_equalities_and_missing(self):
  s=self.fixture();d=p.decide(s,True,True);self.assertEqual(d['Decision'],'DEMO_FORWARD_CANDIDATE');verify_decision(s,d)
  for r in s:
   if (r['Candidate'],r['Method'],r['Period'])==('R2_MODERATE','primary','ALL'):r['WorstDayPct']=D('-20')
  self.assertEqual(p.decide(s,True,True)['Decision'],'NOT_CANDIDATE')
  s=self.fixture();self.assertEqual(p.decide(s,True,None)['Decision'],'UNDETERMINED')
  self.assertEqual(p.decide([],None,None)['Decision'],'UNDETERMINED')
  for r in s:
   if (r['Candidate'],r['Method'],r['Period'])==('R2_MODERATE','robustness','ALL'):r['FinalCapital']-=1
  self.assertEqual(p.decide(s,True,True)['Decision'],'NOT_CANDIDATE')
 def test_missing_inputs_never_pass(self):
  with tempfile.TemporaryDirectory() as tmp:
   p.run(tmp,'a'*40)
   text=(Path(tmp)/'volatility_phase4_decision.csv').read_text();self.assertIn('UNDETERMINED',text)
   self.assertIn('NOT_RUN_INPUT_MISSING',(Path(tmp)/'volatility_phase4_run_record.csv').read_text())
   with self.assertRaises(ValueError):p.run(tmp,'a'*40)

if __name__=='__main__':unittest.main()
