import csv,hashlib,io,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage5_freeze import serialize,sha_bytes,summary_csv,CANDIDATE_PATH,CONTRACT_PATH
from b6.stage5_validation import contract
from b6.stage5_config import load_config,CONFIG_SHA,PATH
from b6.stage5_release import verify_release

class ReleaseTests(unittest.TestCase):
    def test_all_current_release_hashes(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage5_release_manifest.json').read_text())
        for n,h in lock.items():self.assertEqual(sha_bytes((ROOT/n).read_bytes()),h,n)
        for n in (CANDIDATE_PATH,CONTRACT_PATH,'src/research/b6/stage5_freeze.py','src/research/b6/stage5_input.py','src/research/b6/stage5_validation.py','results/b6/stage5_freeze/candidate_summary.csv','results/b6/stage5_freeze/test_summary.json'):self.assertIn(n,lock)
        self.assertEqual(sha_bytes(PATH.read_bytes()),CONFIG_SHA)
    def test_all_prior_frozen_files_unchanged(self):
        old=json.loads((ROOT/'research_inputs/b6/stage4_release_manifest.json').read_text())
        for n,h in old.items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(sha_bytes((ROOT/n).read_bytes()),h,n)
        subprocess.run(['git','diff','--exit-code','22a7b5ff8d49455afc730b446c666b1aa3a2a048','--','results/b6/stage1_freeze','results/b6/stage2a_freeze','results/b6/stage2b_freeze','results/b6/stage3_freeze','results/b6/stage4_freeze','research_inputs/b6/stage4_release_manifest.json'],cwd=ROOT,check=True)
    def test_exact_hash_binding_contract_docs_summary(self):
        b=(ROOT/CANDIDATE_PATH).read_bytes();h=sha_bytes(b);v=(ROOT/CONTRACT_PATH).read_bytes()
        self.assertEqual(v,serialize(contract(h)));self.assertEqual(b,serialize(json.loads(b)))
        text=(ROOT/'docs/b6/stage5_candidate_freeze.md').read_text();self.assertIn(h,text);self.assertIn(sha_bytes(v),text)
        report=json.loads((ROOT/'results/b6/stage5_freeze/test_summary.json').read_text());self.assertEqual(report['CandidateFreezeSHA256'],h);self.assertEqual(report['ValidationContractSHA256'],sha_bytes(v))
    def test_formal_json_csv_and_fifty_e0(self):
        f=json.loads((ROOT/CANDIDATE_PATH).read_text());self.assertEqual(f['CandidateCount'],50);self.assertEqual(len(f['Candidates']),50);self.assertEqual(len({p['CandidateID'] for p in f['Candidates']}),50)
        self.assertEqual(summary_csv(f),(ROOT/'results/b6/stage5_freeze/candidate_summary.csv').read_bytes())
        for p in f['Candidates']:
            self.assertEqual(p['SelectedEventMode'],'E0');self.assertEqual(p['DiscoveryMaxDDR'],p['DiscoveryMetrics']['MaxDDR']);self.assertEqual([y['Year'] for y in p['DiscoveryYearlyMetrics']],[2020,2021,2022,2023])
    def test_no_m1_or_future_performance_api_in_new_sources(self):
        for p in (ROOT/'src/research/b6').glob('stage5_*.py'):
            text=p.read_text()
            for forbidden in ('load_discovery(', 'audit_inputs(', 'fast_replay(', 'reference_replay(', 'full_sweep(', 'read_parquet(', 'read_pickle('):self.assertNotIn(forbidden,text,str(p))
        f=json.loads((ROOT/CANDIDATE_PATH).read_text());self.assertFalse(f['M1InputProvenance']['PriceFilesRead']);self.assertFalse(f['ValidationExecuted']);self.assertFalse(f['MonitorExecuted']);self.assertFalse(f['PortfolioExecuted']);self.assertFalse(f['LiveAdoption'])
    def test_stage5_release_guards(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage5_release.subprocess.check_output',return_value='a'*40):
            with self.assertRaises(ValueError):verify_release('b'*40)
        with patch('b6.stage5_release.subprocess.check_output',side_effect=['a'*40,'?? unexpected']):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage5_release.subprocess.check_output',side_effect=['a'*40,'']),patch('b6.stage5_release.sha',return_value='bad'):
            with self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage5_config.sha',return_value='bad'):
            with self.assertRaises(ValueError):load_config()
