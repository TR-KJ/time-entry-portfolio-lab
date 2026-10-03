import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage7_freeze import validate_formal,spec,build_outputs
from b6.stage7_input import load_input
from b6.stage7_config import load_config,sha
from b6.stage6_input import load_input as previous,assert_frozen_candidate,FIELDS

class InputTests(unittest.TestCase):
    def setUp(self):
        self.e=json.loads((ROOT/'results/b6/stage7_freeze/stage6_formal_evidence.json').read_text());self.points=previous()[0];self.s=spec()
    def validate(self):
        e=self.e;return validate_formal(e['Identity'],e['Summary'],e['Progress'],e['ValidationRows'],e['PeriodRows'],self.points,self.s)
    def test_formal_pass_only_exact_order_composition_conditions(self):
        points,_,audit=load_input();self.assertEqual(points,self.validate());self.assertEqual(len(points),17)
        self.assertEqual([p['CandidateID'] for p in points],self.s['expected_pass_ids'])
        self.assertEqual(sum(p['Symbol']=='AUDJPY' for p in points),9);self.assertEqual(sum(p['Symbol']=='GBPJPY' for p in points),8);self.assertFalse(any(p['Symbol']=='EURJPY' for p in points))
        base={p['CandidateID']:p for p in self.points}
        for p in points:
            self.assertEqual(p['FormalValidationStatus'],'PASS')
            self.assertEqual({k:p[k] for k in FIELDS},{k:base[p['CandidateID']][k] for k in FIELDS})
        self.assertFalse(audit['Stage7MonitorExecuted']);self.assertTrue(audit['FrozenConditionsUnchanged'])
    def test_sha_mismatch_rejected_before_source_read(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'formal exact SHA mismatch'):build_outputs(root)
    def test_review_zip_is_not_archive(self):
        with tempfile.NamedTemporaryFile(suffix='.zip') as f:
            with self.assertRaisesRegex(ValueError,'formal Stage6 archive'):build_outputs(f.name)
    def test_duplicate_candidate(self):
        self.e['ValidationRows'][1]['CandidateID']=self.e['ValidationRows'][0]['CandidateID']
        with self.assertRaises(ValueError):self.validate()
    def test_no_drop_refill_rerank(self):
        for action in ('drop','append','reverse'):
            old=copy.deepcopy(self.e['ValidationRows'])
            if action=='drop':self.e['ValidationRows'].pop()
            if action=='append':self.e['ValidationRows'].append(copy.deepcopy(old[0]))
            if action=='reverse':self.e['ValidationRows'].reverse()
            with self.assertRaises(ValueError):self.validate()
            self.e['ValidationRows']=old
    def test_revival_of_fail_rejected(self):
        row=next(r for r in self.e['ValidationRows'] if r['ValidationStatus']=='FAIL');row['ValidationStatus']='PASS'
        with self.assertRaises(ValueError):self.validate()
    def test_expected_id_cross_check(self):
        self.s['expected_pass_ids'][0]='invented'
        with self.assertRaises(ValueError):self.validate()
    def test_pair_count_cross_check(self):
        self.s['pair_counts']['AUDJPY']=8
        with self.assertRaises(ValueError):self.validate()
    def test_conditions_and_provenance_immutable(self):
        points=load_input()[0]
        for k in points[0]:
            p=copy.deepcopy(points[0]);p[k]='changed'
            with self.assertRaises(ValueError):assert_frozen_candidate(p,points[0])
        self.e['ValidationRows'][0]['SL']='30.00000000000001'
        with self.assertRaises(ValueError):self.validate()
    def test_candidate_sha_hard_gate(self):
        with patch('b6.stage7_input.sha',return_value='0'*64):
            with self.assertRaises(ValueError):load_input()
    def test_evidence_no_2026_performance(self):
        self.assertEqual({r['Period'] for r in self.e['PeriodRows']},{'2024','2025','Combined'})
        for p in load_input()[0]:
            self.assertFalse(any(k.startswith('Monitor') for k in p['ValidationProvenance']))
            self.assertNotIn('Stage4DecisionAudit',p)
        for row in self.e['ValidationRows']:
            if row['ValidationStatus']!='PASS':self.assertFalse(any(k.startswith(('2024_','2025_','Combined_')) for k in row))
        for row in self.e['PeriodRows']:self.assertEqual(set(row),{'CandidateID','Period'})

for field,value in [('code_sha','0'*40),('config_sha256','0'*64),('scope','wrong'),('runtime',{}),('candidate_sha256','0'*64),('contract_sha256','0'*64),('calendar_sha256','0'*64),('inputs',[])]:
    def check(self,field=field,value=value):
        self.e['Identity'][field]=value
        with self.assertRaises(ValueError):self.validate()
    setattr(InputTests,'test_wrong_identity_'+field,check)
for field,value in [('State','RUNNING_STAGE6'),('CandidateCount',49),('PeriodRows',149),('PASS',16),('FAIL',34),('INSUFFICIENT_SAMPLE',1),('ValidationExecuted',False),('MonitorExecuted',True),('PortfolioExecuted',True),('LiveChanged',True),('NoRanking',False)]:
    def check(self,field=field,value=value):
        for target in ('Summary','Progress'):
            original=self.e[target][field];self.e[target][field]=value
            with self.assertRaises(ValueError):self.validate()
            self.e[target][field]=original
    setattr(InputTests,'test_formal_gate_'+field,check)
for field in ('CompletedJobs','ExpectedJobs'):
    def check(self,field=field):
        self.e['Progress'][field]=49
        with self.assertRaises(ValueError):self.validate()
    setattr(InputTests,'test_incomplete_'+field,check)
