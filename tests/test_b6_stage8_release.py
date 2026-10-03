import contextlib,io,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage8_config import CONFIG_SHA,PATH,load_config,sha
from b6.stage8_search import verify_release

class ReleaseTests(unittest.TestCase):
    def test_release_integrity_and_exact_pool_eligibility(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage8_release_manifest.json').read_text())
        for n,h in lock.items():self.assertEqual(sha(ROOT/n),h,n)
        self.assertEqual(sha(PATH),CONFIG_SHA)
        c=load_config();self.assertEqual(c['candidate_pool_sha256'],'dfe25f015da9532535fb9aae3e580e59835f68cf6f9c0e2b0fc6b4a215ec6d68');self.assertEqual(c['eligibility_sha256'],'7e62f0ca36a8160233a7f037c08f1c084cab49f418688718559afefa30adf852')
    def test_stage1_through_stage7_frozen_artifacts_unchanged(self):
        old=json.loads((ROOT/'research_inputs/b6/stage7_release_manifest.json').read_text())
        for n,h in old.items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(sha(ROOT/n),h,n)
        subprocess.run(['git','diff','--exit-code','805fccbb2dac5dddd4e4ed24d14bedf8887d3b1a','--','src/research/b6/stage7*','tests/test_b6_stage7*','research_inputs/b6/stage5_candidate_freeze.json','research_inputs/b6/stage5_validation_contract.json','research_inputs/b6/stage7_config.json','research_inputs/b6/stage7_monitor_candidates.json','research_inputs/b6/stage7_release_manifest.json','results/b6/stage7_freeze','notebooks/b6_stage7_monitor.ipynb'],cwd=ROOT,check=True)
    def test_notebook_default_all_flags_false_no_m1_no_pairwise(self):
        n=json.loads((ROOT/'notebooks/b6_stage8_overlap_correlation.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('command')),patch('b6.stage8_search.load_input',side_effect=AssertionError('input')),patch('b6.stage8_search.audit_inputs',side_effect=AssertionError('M1')),patch('b6.stage8_search.full_analysis',side_effect=AssertionError('full')),patch('b6.stage8_search.all_pairs',side_effect=AssertionError('pairwise')),contextlib.redirect_stdout(io.StringIO()):
            for cell in n['cells']:
                if cell['cell_type']=='code':
                    self.assertEqual(cell['outputs'],[]);self.assertIsNone(cell['execution_count']);exec(''.join(cell['source']),ns)
        for key in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE8_FULL','CHAT_CONFIRMED_STAGE8_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[key],False)
        self.assertEqual(ns['STAGE8_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['DATA_ROOT'],'/content/drive/MyDrive/ゆうのすけさん2025');self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage8');self.assertEqual(ns['DRIVE_OUTPUT_ROOT'],'/content/drive/MyDrive/b6_stage8_archive')
    def test_incomplete_run_display_rejected(self):
        n=json.loads((ROOT/'notebooks/b6_stage8_overlap_correlation.ipynb').read_text());c=load_config();complete=dict(State='COMPLETE_STAGE8_OVERLAP_CORRELATION_ONLY',CompletedJobs=9,ExpectedJobs=9,PairwiseRows=144,CandidatePeriodRows=36)
        for key,value in [('State','RUNNING_STAGE8'),('CompletedJobs',8),('ExpectedJobs',8),('PairwiseRows',143),('CandidatePeriodRows',35)]:
            with patch('pathlib.Path.read_text',return_value=json.dumps({**complete,key:value})):
                with self.assertRaises(RuntimeError):exec(''.join(n['cells'][6]['source']),dict(RUN_STAGE8_FULL=True,OUTPUT_ROOT='/unused',FROZEN_CONFIG=c,json=json))
    def test_release_guards_strict(self):
        for value in ('','z'*40,'a'*39):
            with self.assertRaises(ValueError):verify_release(value)
        with patch('b6.stage8_search.subprocess.check_output',return_value='b'*40):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage8_search.subprocess.check_output',side_effect=['a'*40,'?? unknown.txt']):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage8_search.subprocess.check_output',side_effect=['a'*40,'']),patch('b6.stage8_search.sha',return_value='0'*64):
            with self.assertRaises(ValueError):verify_release('a'*40)
    def test_actual_m1_audit_only_no_replay(self):
        a=json.loads((ROOT/'results/b6/stage8_freeze/m1_availability_audit.json').read_text());self.assertEqual(a['FileCount'],56);self.assertFalse(a['CandidateReplayPerformed']);self.assertFalse(a['OverlapCorrelationExecuted']);self.assertFalse(a['ForwardFill']);self.assertFalse(a['SyntheticBarsAdded'])
        self.assertEqual(len(a['CanonicalCoverage']),7)
        for r in a['CanonicalCoverage']:
            self.assertEqual(r['LastAvailableJST'],'2026-09-09 06:00:00');self.assertEqual(r['PeriodRows']['FullAvailable'],sum(r['PeriodRows'][k] for k in ('Discovery','Validation','Monitor')))
