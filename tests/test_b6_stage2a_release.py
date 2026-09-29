import contextlib,hashlib,io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage2a_config import load_config,CONFIG_SHA,PATH
from b6.stage2a_search import verify_release

class ReleaseTests(unittest.TestCase):
    def test_manifest_and_config(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage2a_release_manifest.json').read_text())
        for name,digest in lock.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)
        for name in ('stage2a_config','stage2a_engine','stage2a_metrics','stage2a_search','execution','stage1_engine','stage1_data','stage1_metrics'):
            self.assertIn(f'src/research/b6/{name}.py',lock)
        self.assertEqual(hashlib.sha256(PATH.read_bytes()).hexdigest(),CONFIG_SHA)
    def test_default_notebook_has_no_io_or_full_run(self):
        nb=json.loads((ROOT/'notebooks/b6_stage2a_tp_discovery.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('unexpected subprocess')),patch('b6.stage2a_search.full_sweep',side_effect=AssertionError('unexpected full sweep')),patch('b6.stage2a_search.audit_inputs',side_effect=AssertionError('unexpected data IO')),contextlib.redirect_stdout(io.StringIO()):
            for cell in nb['cells']:
                if cell['cell_type']=='code':
                    self.assertEqual(cell['outputs'],[]);self.assertIsNone(cell['execution_count'])
                    exec(compile(''.join(cell['source']),'stage2a_notebook','exec'),ns)
        for flag in ('RUN_STAGE2A_FULL','CHAT_CONFIRMED_STAGE2A_FREEZE','PREPARE_ENVIRONMENT','MOUNT_DRIVE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[flag],False)
        self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage2a')
        self.assertIn('b6_stage1_20260929',ns['CANDIDATE_PATH'])
        code='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        self.assertNotIn('validation_sweep',code);self.assertNotIn('monitor_sweep',code)
    def test_sha_guard(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage2a_search.subprocess.check_output',return_value='a'*40):
            with self.assertRaises(ValueError):verify_release('b'*40)
        with patch('b6.stage2a_search.subprocess.check_output',return_value='a'*40),patch('b6.stage2a_search.subprocess.run'),patch('b6.stage2a_search.sha',return_value='bad'):
            with self.assertRaises(ValueError):verify_release('a'*40)
