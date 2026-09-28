import contextlib,io,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage1_config import load_config
class NotebookTests(unittest.TestCase):
    def test_default_run_all_no_io_or_full_sweep(self):
        nb=json.loads((ROOT/'notebooks/b6_stage1_discovery.ipynb').read_text());namespace={}
        self.assertEqual(nb['nbformat'],4)
        with patch('subprocess.run',side_effect=AssertionError('default notebook must not launch commands')),contextlib.redirect_stdout(io.StringIO()) as stream:
            for cell in nb['cells']:
                if cell['cell_type']=='code':
                    self.assertEqual(cell['outputs'],[]);self.assertIsNone(cell['execution_count'])
                    exec(compile(''.join(cell['source']),'b6_stage1_notebook','exec'),namespace)
        self.assertFalse(namespace['RUN_FULL_SWEEP']);self.assertEqual(namespace['DISPLAY_CONFIG'],load_config())
        self.assertIn('FULL SWEEP: NOT RUN',stream.getvalue())
        self.assertEqual(namespace['structures'],5705280)
    def test_no_future_period_executor_cells(self):
        nb=json.loads((ROOT/'notebooks/b6_stage1_discovery.ipynb').read_text());code='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        self.assertNotIn('validation_start',code);self.assertNotIn('2026-01-01',code)
        self.assertIn('verify_release(FREEZE_SHA)',code);self.assertIn('CHAT_CONFIRMED_FREEZE',code)
