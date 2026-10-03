import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage8_freeze import derive,spec,validate_formal,build_outputs
from b6.stage8_input import load_input
from b6.stage7_input import load_input as previous
from b6.stage6_input import FIELDS

class EligibilityTests(unittest.TestCase):
    def setUp(self):
        self.points=previous()[0];self.s=spec();self.audit=json.loads((ROOT/'results/b6/stage8_freeze/stage7_input_audit.json').read_text());self.states=self.audit['ResearchStates']
    def test_exact_partition_research_history_and_pool_order(self):
        e,p=derive(self.points,self.states,self.s);self.assertEqual(len(e['Candidates']),17);self.assertEqual(len(p['Candidates']),9)
        self.assertEqual([r['CandidateID'] for r in e['Candidates'] if r['DeploymentReviewEligibility']=='INELIGIBLE_EXECUTION_RISK'],self.s['excluded_ids']);self.assertEqual([r['CandidateID'] for r in p['Candidates']],self.s['eligible_ids'])
        for row in e['Candidates']:
            self.assertEqual(row['FormalValidationStatus'],'PASS');self.assertEqual(row['MonitorState'],'OBSERVED')
            if row['DeploymentReviewEligibility']=='INELIGIBLE_EXECUTION_RISK':self.assertEqual((row['Symbol'],row['FinalEntryJST'],row['EligibilityReasonCode']),('AUDJPY','07:01','WEEKLY_OPEN_EXECUTION_MODEL_RISK'))
    def test_aj_singleton_and_gbp8_conditions_unchanged(self):
        pool=load_input()[0];self.assertEqual(sum(p['Symbol']=='GBPJPY' for p in pool),8);aj=[p for p in pool if p['Symbol']=='AUDJPY'];self.assertEqual(len(aj),1);self.assertEqual((aj[0]['CandidateID'],aj[0]['FinalEntryJST']),('B6-AUDJPY-L-W0-E0950-H1440','15:50'))
        source={p['CandidateID']:p for p in self.points}
        for p in pool:self.assertEqual({k:p[k] for k in FIELDS},{k:source[p['CandidateID']][k] for k in FIELDS})
    def test_monitor_metrics_never_used(self):
        original=derive(self.points,self.states,self.s)
        for value in (-1e9,0,1e9,'UNDEFINED'):
            states=copy.deepcopy(self.states);points=copy.deepcopy(self.points)
            for row in states:row.update(MonitorPF=value,MonitorAvgR=value,MonitorTotalR=value,MonitorMaxDDR=value)
            for p in points:p['MonitorTotalR']=value
            self.assertEqual(derive(points,states,self.s),original)
    def test_source_count_duplicate_order_rejected(self):
        for points in (self.points[:-1],self.points+[self.points[0]],list(reversed(self.points))):
            with self.assertRaises(ValueError):derive(points,self.states,self.s)
    def test_excluded_symbol_time_weekday_rejected(self):
        for key,value in [('Symbol','GBPJPY'),('FinalEntryJST','07:02'),('Weekday',1)]:
            points=copy.deepcopy(self.points);p=next(p for p in points if p['CandidateID'] in self.s['excluded_ids']);p[key]=value
            with self.assertRaises(ValueError):derive(points,self.states,self.s)
    def test_wrong_exclusion_or_pool_ids_rejected(self):
        for key in ('excluded_ids','eligible_ids'):
            s=copy.deepcopy(self.s);s[key][0]='invented'
            with self.assertRaises(ValueError):derive(self.points,self.states,s)
    def test_formal_status_and_monitor_state_immutable(self):
        for key,value in [('FormalValidationStatus','FAIL'),('MonitorState','PASS')]:
            rows=copy.deepcopy(self.states);rows[0][key]=value
            with self.assertRaises(ValueError):derive(self.points,rows,self.s)
    def test_no_reranking(self):
        s=copy.deepcopy(self.s);s['eligible_ids'].reverse()
        with self.assertRaises(ValueError):derive(self.points,self.states,s)
    def test_input_hash_gate(self):
        with patch('b6.stage8_input.sha',return_value='0'*64):
            with self.assertRaises(ValueError):load_input()
    def test_missing_or_zip_archive_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):build_outputs(root)
        with tempfile.NamedTemporaryFile(suffix='.zip') as f:
            with self.assertRaises(ValueError):build_outputs(f.name)
    def test_actual_formal_identity_gates(self):
        a=self.audit;validate_formal(a['FormalIdentity'],a['FormalSummary'],a['FormalProgress'],self.points,self.s)
        for k in a['FormalIdentity']:
            identity=copy.deepcopy(a['FormalIdentity']);identity[k]='mutation'
            with self.assertRaises(ValueError):validate_formal(identity,a['FormalSummary'],a['FormalProgress'],self.points,self.s)
    def test_actual_completion_gates(self):
        a=self.audit
        for key in self.s['expected_stage7_summary']:
            for target in ('FormalSummary','FormalProgress'):
                changed=copy.deepcopy(a);changed[target][key]='mutation'
                with self.assertRaises(ValueError):validate_formal(changed['FormalIdentity'],changed['FormalSummary'],changed['FormalProgress'],self.points,self.s)
        for key in ('CompletedJobs','ExpectedJobs'):
            p=copy.deepcopy(a['FormalProgress']);p[key]=16
            with self.assertRaises(ValueError):validate_formal(a['FormalIdentity'],a['FormalSummary'],p,self.points,self.s)
