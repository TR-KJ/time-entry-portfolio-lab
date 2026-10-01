import contextlib,hashlib,io,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage4_config import CONFIG_SHA,PATH,load_config
from b6.stage4_search import verify_release
from b6.stage4_calendar import CLOCKS
from b6.stage4_events import BANKS

class ReleaseTests(unittest.TestCase):
    def test_current_release_hashes(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage4_release_manifest.json').read_text())
        for n,h in lock.items():self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
        self.assertEqual(hashlib.sha256(PATH.read_bytes()).hexdigest(),CONFIG_SHA)
        for n in ('stage4_calendar','stage4_input','stage4_events','stage4_metrics','stage4_selection','stage4_search','stage2a_engine','execution'):self.assertIn(f'src/research/b6/{n}.py',lock)
    def test_prior_freezes_unchanged(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage3_release_manifest.json').read_text())
        for n,h in lock.items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(hashlib.sha256((ROOT/n).read_bytes()).hexdigest(),h,n)
        subprocess.run(['git','diff','--exit-code','a2e689332a229d648ed26418f220df96d8ede196','--','results/b6/stage1_freeze','results/b6/stage2a_freeze','results/b6/stage2b_freeze','results/b6/stage3_freeze','research_inputs/b6/stage3_release_manifest.json'],cwd=ROOT,check=True)
    def test_notebook_default_no_io_calculation(self):
        nb=json.loads((ROOT/'notebooks/b6_stage4_event_filter.ipynb').read_text());ns={}
        with patch('subprocess.run',side_effect=AssertionError('command')),patch('b6.stage4_search.full_sweep',side_effect=AssertionError('full')),patch('b6.stage4_search.load_input',side_effect=AssertionError('input')),patch('b6.stage4_search.audit_inputs',side_effect=AssertionError('M1')),patch('b6.stage4_search.replay_all',side_effect=AssertionError('E0')),contextlib.redirect_stdout(io.StringIO()):
            for cell in nb['cells']:
                if cell['cell_type']=='code':
                    self.assertIsNone(cell['execution_count']);self.assertEqual(cell['outputs'],[]);exec(compile(''.join(cell['source']),'stage4_notebook','exec'),ns)
        for flag in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE4_FULL','CHAT_CONFIRMED_STAGE4_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[flag],False)
        self.assertEqual(ns['STAGE4_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],load_config());self.assertEqual(ns['STAGE3_RESULT_ROOT'],'/content/drive/MyDrive/b6_stage3_archive');self.assertEqual(ns['OUTPUT_ROOT'],'/content/b6_stage4');self.assertEqual(ns['DRIVE_OUTPUT_ROOT'],'/content/drive/MyDrive/b6_stage4_archive')
        source='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code')
        for forbidden in ('validation_sweep','monitor_sweep','stage3_search','stage2b_search','stage2a_search'):self.assertNotIn(forbidden,source)
    def test_config_executable_rules_match(self):
        c=load_config();self.assertEqual(c['event_clocks'],CLOCKS);self.assertEqual(c['currency_central_bank'],BANKS);self.assertEqual(c['adoption'],dict(min_retention=.8,min_removed=20,min_delta_total_r=2.,min_delta_avg_r=.01,max_dd_increase=0));self.assertEqual(c['tie_break'],['DeltaTotalR_DESC','FilterMaxDDR_ASC','E1_FIRST']);self.assertEqual(c['expected_variants'],3*c['selected_candidate_count'])
    def test_release_guards(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage4_search.subprocess.check_output',return_value='a'*40):
            with self.assertRaises(ValueError):verify_release('b'*40)
        with patch('b6.stage4_search.subprocess.check_output',return_value='a'*40),patch('b6.stage4_search.subprocess.run'),patch('b6.stage4_search.sha',return_value='bad'):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage4_config.sha',return_value='bad'):
            with self.assertRaises(ValueError):load_config()
