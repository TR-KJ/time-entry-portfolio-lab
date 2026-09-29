import contextlib,hashlib,io,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage2b_config import CONFIG_SHA,PATH,load_config
from b6.stage2b_search import verify_release

class ReleaseTests(unittest.TestCase):
    def test_all_current_release_hashes(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage2b_release_manifest.json').read_text())
        for name,digest in lock.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        for name in ('stage2b_config','stage2b_input','stage2b_selection','stage2b_metrics','stage2b_search','stage2a_engine','stage2a_metrics','execution'):
            self.assertIn(f'src/research/b6/{name}.py',lock)
        self.assertEqual(hashlib.sha256(PATH.read_bytes()).hexdigest(),CONFIG_SHA)
    def test_stage1_stage2a_code_tests_results_unchanged(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage2a_release_manifest.json').read_text());evolving={'docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'}
        for name,digest in lock.items():
            if name not in evolving:self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        subprocess.run(['git','diff','--exit-code','50f83f3904acc3bc3abe54204db7a2ab4964b024','--','results/b6/stage1_freeze','results/b6/stage2a_freeze','research_inputs/b6/stage2a_release_manifest.json'],cwd=ROOT,check=True)
    def test_notebook_default_no_io_no_centers_no_run(self):
        nb=json.loads((ROOT/'notebooks/b6_stage2b_local_optimization.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('unexpected commands')),patch('b6.stage2b_search.full_sweep',side_effect=AssertionError('sweep')),patch('b6.stage2b_search.load_input',side_effect=AssertionError('input')),patch('b6.stage2b_search.prepare_jobs',side_effect=AssertionError('centers')),contextlib.redirect_stdout(io.StringIO()):
            for cell in nb['cells']:
                if cell['cell_type']=='code':
                    self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[])
                    exec(compile(''.join(cell['source']),'stage2b_notebook','exec'),ns)
        for flag in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE2B_FULL','CHAT_CONFIRMED_STAGE2B_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[flag],False)
        self.assertEqual(ns['STAGE2B_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage2b')
        code='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        for forbidden in ('validation_sweep','monitor_sweep','stage3_sweep'):self.assertNotIn(forbidden,code)
    def test_sha_and_config_mutation_guard(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage2b_search.subprocess.check_output',return_value='a'*40):
            with self.assertRaises(ValueError):verify_release('b'*40)
        with patch('b6.stage2b_search.subprocess.check_output',return_value='a'*40),patch('b6.stage2b_search.subprocess.run'),patch('b6.stage2b_search.sha',return_value='bad'):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage2b_config.sha',return_value='bad'):
            with self.assertRaises(ValueError):load_config()
