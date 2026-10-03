import contextlib,io,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage7_config import CONFIG_SHA,PATH,load_config,sha
from b6.stage7_search import verify_release

class ReleaseTests(unittest.TestCase):
    def test_release_integrity(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage7_release_manifest.json').read_text())
        for n,h in lock.items():self.assertEqual(sha(ROOT/n),h,n)
        self.assertEqual(sha(PATH),CONFIG_SHA)
        self.assertEqual(load_config()['monitor_candidate_sha256'],'c973c541726efba057b2c07a19cc99ffd2b5a2d457328d1e9df8e813d5e96b86')
    def test_stage1_through_stage6_frozen_files_unchanged(self):
        old=json.loads((ROOT/'research_inputs/b6/stage6_release_manifest.json').read_text())
        for n,h in old.items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(sha(ROOT/n),h,n)
        subprocess.run(['git','diff','--exit-code','a1f9e0266801d3d0b4cd383f8fea909fdbc0a678','--','src/research/b6/stage6*','tests/test_b6_stage6*','research_inputs/b6/stage5_candidate_freeze.json','research_inputs/b6/stage5_validation_contract.json','research_inputs/b6/stage6_config.json','research_inputs/b6/stage6_release_manifest.json','results/b6/stage6_freeze','notebooks/b6_stage6_validation.ipynb'],cwd=ROOT,check=True)
    def test_default_notebook_no_io(self):
        n=json.loads((ROOT/'notebooks/b6_stage7_monitor.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('command')),patch('b6.stage7_search.load_input',side_effect=AssertionError('input')),patch('b6.stage7_search.audit_inputs',side_effect=AssertionError('M1')),patch('b6.stage7_search.full_monitor',side_effect=AssertionError('Monitor')),contextlib.redirect_stdout(io.StringIO()):
            for cell in n['cells']:
                if cell['cell_type']=='code':
                    self.assertEqual(cell['outputs'],[]);self.assertIsNone(cell['execution_count']);exec(''.join(cell['source']),ns)
        for key in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE7_FULL','CHAT_CONFIRMED_STAGE7_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[key],False)
        self.assertEqual(ns['STAGE7_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['DATA_ROOT'],'/content/drive/MyDrive/ゆうのすけさん2025');self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage7');self.assertEqual(ns['DRIVE_OUTPUT_ROOT'],'/content/drive/MyDrive/b6_stage7_archive')
    def test_incomplete_display_rejected(self):
        n=json.loads((ROOT/'notebooks/b6_stage7_monitor.ipynb').read_text());c=load_config()
        for state,count in [('RUNNING_STAGE7',17),('COMPLETE_STAGE7_MONITOR_ONLY',16)]:
            with patch('pathlib.Path.read_text',return_value=json.dumps(dict(State=state,CompletedJobs=count,ExpectedJobs=17,MonitoredCount=count))):
                with self.assertRaises(RuntimeError):exec(''.join(n['cells'][6]['source']),dict(RUN_STAGE7_FULL=True,OUTPUT_ROOT='/unused',FROZEN_CONFIG=c,json=json))
    def test_release_guards(self):
        for sha_value in ('','z'*40,'a'*39):
            with self.assertRaises(ValueError):verify_release(sha_value)
        with patch('b6.stage7_search.subprocess.check_output',return_value='b'*40):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage7_search.subprocess.check_output',side_effect=['a'*40,'?? unexpected.txt']):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage7_search.subprocess.check_output',side_effect=['a'*40,'']),patch('b6.stage7_search.sha',return_value='0'*64):
            with self.assertRaises(ValueError):verify_release('a'*40)
    def test_m1_audit_no_candidate_performance(self):
        a=json.loads((ROOT/'results/b6/stage7_freeze/m1_availability_audit.json').read_text());self.assertEqual(a['FileCount'],56);self.assertFalse(a['CandidatePerformanceCalculated']);self.assertFalse(a['MonitorExecuted'])
        self.assertEqual(len(a['CanonicalCoverage']),7)
        for row in a['CanonicalCoverage']:
            self.assertEqual(row['LastAvailableJST'],'2026-09-09 06:00:00');self.assertEqual(row['SourceRows'],row['MonitorRows']+row['OutsideMonitorWindowRows']);self.assertFalse(row['CandidatePerformanceCalculated'])
