import contextlib,io,json,sys,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage6_config import PATH,CONFIG_SHA,load_config,sha
from b6.stage6_search import verify_release

class ReleaseTests(unittest.TestCase):
    def test_release_hashes_and_input_artifacts(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage6_release_manifest.json').read_text())
        for n,h in lock.items():self.assertEqual(sha(ROOT/n),h,n)
        self.assertEqual(sha(PATH),CONFIG_SHA)
        for n in ('stage6_input','stage6_adapter','stage6_data','stage6_engine','stage6_metrics','stage6_search','stage5_validation','execution'):self.assertIn('src/research/b6/'+n+'.py',lock)
    def test_stage1_through_stage5_freezes_unchanged(self):
        old=json.loads((ROOT/'research_inputs/b6/stage5_release_manifest.json').read_text())
        for n,h in old.items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(sha(ROOT/n),h,n)
        subprocess.run(['git','diff','--exit-code','e35225782c84a59dd7546e9ff8d3944705c3709a','--','research_inputs/b6/stage5_candidate_freeze.json','research_inputs/b6/stage5_validation_contract.json','research_inputs/b6/stage5_config.json','research_inputs/b6/stage5_release_manifest.json','results/b6/stage5_freeze','notebooks/b6_stage4_event_filter.ipynb'],cwd=ROOT,check=True)
    def test_notebook_default_no_io_no_run(self):
        nb=json.loads((ROOT/'notebooks/b6_stage6_validation.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('command')),patch('b6.stage6_search.load_input',side_effect=AssertionError('input')),patch('b6.stage6_search.audit_inputs',side_effect=AssertionError('M1')),patch('b6.stage6_search.full_validation',side_effect=AssertionError('full')),contextlib.redirect_stdout(io.StringIO()):
            for c in nb['cells']:
                if c['cell_type']=='code':
                    self.assertEqual(c['outputs'],[]);self.assertIsNone(c['execution_count']);exec(compile(''.join(c['source']),'stage6_notebook','exec'),ns)
        for flag in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE6_FULL','CHAT_CONFIRMED_STAGE6_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[flag],False)
        self.assertEqual(ns['STAGE6_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage6');self.assertEqual(ns['DRIVE_OUTPUT_ROOT'],'/content/drive/MyDrive/b6_stage6_archive')
    def test_notebook_partial_result_display_blocked(self):
        nb=json.loads((ROOT/'notebooks/b6_stage6_validation.ipynb').read_text());source=''.join(nb['cells'][6]['source']);config=load_config()
        for state in ('RUNNING_STAGE6','COMPLETE_STAGE6_VALIDATION_ONLY'):
            with patch('pathlib.Path.read_text',return_value=json.dumps(dict(State=state,CompletedJobs=49))):
                with self.assertRaises(RuntimeError):exec(source,dict(RUN_STAGE6_FULL=True,OUTPUT_ROOT='unused',json=json,FROZEN_CONFIG=config))
    def test_release_guards(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage6_search.subprocess.check_output',return_value='b'*40):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage6_search.subprocess.check_output',side_effect=['a'*40,'?? dirty']):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage6_search.subprocess.check_output',side_effect=['a'*40,'']),patch('b6.stage6_search.sha',return_value='bad'):
            with self.assertRaises(ValueError):verify_release('a'*40)
    def test_no_monitor_portfolio_or_live_switch(self):
        c=load_config()
        for k in ('stage7_enabled','monitor_enabled','portfolio_enabled','live_enabled'):self.assertIs(c[k],False)
