import contextlib,hashlib,io,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage3_config import CONFIG_SHA,PATH,load_config
from b6.stage3_search import verify_release

class ReleaseTests(unittest.TestCase):
    def test_current_release_hashes(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage3_release_manifest.json').read_text())
        for n,h in lock.items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
        self.assertEqual(hashlib.sha256(PATH.read_bytes()).hexdigest(),CONFIG_SHA)
        for n in ('stage3_input','stage3_grid','stage3_metrics','stage3_selection','stage3_search','stage2a_engine','execution'):self.assertIn(f'src/research/b6/{n}.py',lock)
    def test_prior_frozen_code_tests_notebooks_results_unchanged(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage2b_release_manifest.json').read_text())
        for n,h in lock.items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
        subprocess.run(['git','diff','--exit-code','686b4b8b479055e3ff43a21f450b1a7182367ebe','--','results/b6/stage1_freeze','results/b6/stage2a_freeze','results/b6/stage2b_freeze','research_inputs/b6/stage2b_release_manifest.json'],cwd=ROOT,check=True)
    def test_notebook_default_no_data_metrics_or_selection(self):
        nb=json.loads((ROOT/'notebooks/b6_stage3_time_finetune.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('command')),patch('b6.stage3_search.full_sweep',side_effect=AssertionError('full')),patch('b6.stage3_search.load_input',side_effect=AssertionError('input')),patch('b6.stage3_search.prepare_jobs',side_effect=AssertionError('grid')),contextlib.redirect_stdout(io.StringIO()):
            for cell in nb['cells']:
                if cell['cell_type']=='code':
                    self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[]);exec(compile(''.join(cell['source']),'stage3_notebook','exec'),ns)
        for flag in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE3_FULL','CHAT_CONFIRMED_STAGE3_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[flag],False)
        self.assertEqual(ns['STAGE3_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage3');self.assertTrue(ns['STAGE2B_RESULT_ROOT'].endswith('b6_stage2b_archive'))
        source='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        for forbidden in ('stage4_sweep','validation_sweep','monitor_sweep','stage2a_search','stage2b_search'):self.assertNotIn(forbidden,source)
    def test_release_config_and_sha_guards(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage3_search.subprocess.check_output',return_value='a'*40):
            with self.assertRaises(ValueError):verify_release('b'*40)
        with patch('b6.stage3_search.subprocess.check_output',return_value='a'*40),patch('b6.stage3_search.subprocess.run'),patch('b6.stage3_search.sha',return_value='bad'):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage3_config.sha',return_value='bad'):
            with self.assertRaises(ValueError):load_config()
