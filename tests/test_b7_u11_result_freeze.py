import unittest,copy
from b7.u11_result_freeze import audit_saved_decision,validate_monitor
from b7.stage1_contract import object_hash
from test_b7_u11 import record,empty_result
import test_b7_u11 as fixtures
from b7.u11_metrics import checks

class PersistedDecision(unittest.TestCase):
 def test_insufficient_precedence(self):
  r=empty_result(record());self.assertEqual(audit_saved_decision(r)['Status'],'INSUFFICIENT_SAMPLE')
 def fixture(self):
  r=empty_result(record());m=fixtures.Metrics().fixture();sample,formal,status,limit=checks(m,r);r.update(ValidationMetrics=m,SampleChecks=sample,FormalChecks=formal,SampleSufficient=True,FormalConditionsPASS=True,Status=status,ValidationStatus=status,DDThreshold=limit);return r
 def test_pass(self):self.assertEqual(audit_saved_decision(self.fixture())['Status'],'PASS')
 def test_no_near_threshold_rescue(self):
  r=self.fixture();r['ValidationMetrics']['Combined']['PFpips']=1.0904444444443533;r['FormalChecks']['PFpips']=False;r.update(Status='FAIL',ValidationStatus='FAIL',FormalConditionsPASS=False);self.assertEqual(audit_saved_decision(r)['Status'],'FAIL')
 def test_each_persisted_mismatch(self):
  for key,val in [('SampleSufficient',False),('FormalConditionsPASS',False),('Status','FAIL'),('ValidationStatus','FAIL'),('DDThreshold',999)]:
   r=self.fixture();r[key]=val
   with self.assertRaises(ValueError):audit_saved_decision(r)
 def test_wrong_dd_baseline(self):
  r=self.fixture();r['SelectedModeDiscoveryMetrics']['MaxDDPips']=1
  with self.assertRaises(ValueError):audit_saved_decision(r)
 def test_nonfinite_sufficient_reject(self):
  r=self.fixture();r['ValidationMetrics']['Combined'].update(PFState='INF',PFpips=None)
  with self.assertRaises(ValueError):audit_saved_decision(r)

class MonitorProjection(unittest.TestCase):
 def setUp(self):
  self.sha='a'*40;self.records=[dict(CandidateID=f'SYNTHETIC:{i}',Symbol='EURJPY',FormalProtectionMode='P2' if i==2 else 'P0',FixedSchedule={'Entry':i}) for i in range(40)]
  chosen=self.records[:22];self.inv=[dict(r,Status='PASS',FailedChecks=[],TotalPips2024=1.,TotalPips2025=2.,AvgPips=3.,PFpips=1.2,ValidationDD=4.) for r in chosen]
  self.trusted=[dict(Path='identity.json',SHA256='d'*64)]+[dict(Path='jobs/'+r['CandidateID']+'/'+n,SHA256='b'*64) for r in self.records for n in ('candidate.json','checkpoint.json','DRIVE_COMPLETE.json')]
  candidates=[dict(copy.deepcopy(r),U11ValidationStatus='PASS',U11ProducerImplementationSHA=self.sha,U11CandidateSHA256='b'*64,U11CheckpointSHA256='b'*64,ValidationMetrics=dict(Annual2024=dict(TotalPips=1.),Annual2025=dict(TotalPips=2.),Combined=dict(AvgPips=3.,PFpips=1.2,MaxDDPips=4.))) for r in chosen]
  self.data=dict(Scope='B7_MONITOR_FORMAL_INPUT',CandidateCount=22,CandidateIDs=[r['CandidateID'] for r in chosen],Candidates=candidates,MonitorPerformanceEvaluated=False,ValidationOverrideAllowed=False,NoReplacement=True,MonitorStatus='OBSERVED_ONLY',MonitorPeriod='[2026-01-01, 2026-09-10) JST',U11ProducerImplementationSHA=self.sha,SourceTrustedFilesSHA256=object_hash(self.trusted),PairCounts=dict(EURJPY=22),ProtectionModeCounts=dict(P0=21,P1=0,P2=1,P3=0))
 def verify(self):return validate_monitor(self.data,self.records,self.inv,self.trusted,self.sha)
 def test_exact(self):self.assertEqual(self.verify(),self.data)
 def test_order_reject(self):
  self.data['Candidates'].reverse()
  with self.assertRaises(ValueError):self.verify()
 def test_fail_absent(self):
  self.inv[0]['Status']='FAIL'
  with self.assertRaises(ValueError):self.verify()
 def test_insufficient_absent(self):
  self.inv[0]['Status']='INSUFFICIENT_SAMPLE'
  with self.assertRaises(ValueError):self.verify()
 def test_duplicate_reject(self):
  self.inv[1]=copy.deepcopy(self.inv[0])
  with self.assertRaises(ValueError):self.verify()
 def test_strategy_mutation(self):
  self.data['Candidates'][0]['FixedSchedule']['Entry']=999
  with self.assertRaises(ValueError):self.verify()
 def test_source_hash_mismatch(self):
  self.data['Candidates'][0]['U11CandidateSHA256']='c'*64
  with self.assertRaises(ValueError):self.verify()
 def test_no_monitor_execution_or_override(self):
  for key in ('MonitorPerformanceEvaluated','ValidationOverrideAllowed'):
   self.data[key]=True
   with self.assertRaises(ValueError):self.verify()
   self.data[key]=False
 def test_metric_projection_exact(self):
  self.data['Candidates'][0]['ValidationMetrics']['Combined']['AvgPips']=999
  with self.assertRaises(ValueError):self.verify()
 def test_protection_unchanged(self):
  self.data['Candidates'][0]['FormalProtectionMode']='P1'
  with self.assertRaises(ValueError):self.verify()
 def test_source_unchanged_owned_result(self):
  before=copy.deepcopy(self.data);out=self.verify();out['Candidates'][0]['FixedSchedule']['Entry']=999;self.assertEqual(before,self.data)
 def test_aggregate_mismatch(self):
  self.data['SourceTrustedFilesSHA256']='c'*64
  with self.assertRaises(ValueError):self.verify()
