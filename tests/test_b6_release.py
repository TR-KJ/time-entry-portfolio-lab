import hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage1_config import load_config,PATH,CONFIG_SHA
class FreezeTests(unittest.TestCase):
    def test_all_release_hashes_and_reference_unchanged(self):
        lock=json.loads((ROOT/'research_inputs/b6/stage1_release_manifest.json').read_text())
        # Stage1 is an immutable historical commit. Later stage documentation and
        # this archive-aware regression may evolve; executable Stage1 files may not.
        evolving={'docs/b6/research_plan.md','docs/b6/parameter_decision_register.md','tests/test_b6_release.py'}
        freeze='920b9be5c8f1bcf46a46dbbd4ac06dc19eb295b1'
        for name,h in lock.items():
            frozen=subprocess.check_output(['git','show',freeze+':'+name],cwd=ROOT)
            self.assertEqual(hashlib.sha256(frozen).hexdigest(),h,name)
            if name not in evolving:self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),h,name)
        self.assertIn('src/research/b6/stage1_search.py',lock);self.assertIn('notebooks/b6_stage1_discovery.ipynb',lock)
        self.assertEqual(lock['src/research/daily_stop_baseline_revalidation.py'],'08b9717a3a94a0066e7ef7ebfa0f4802cbc84ae0570c3b875d96729877f4e216')
        self.assertEqual(hashlib.sha256(PATH.read_bytes()).hexdigest(),CONFIG_SHA)
    def test_config_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config.json';p.write_text('{}')
            with patch('b6.stage1_config.PATH',p):
                with self.assertRaises(ValueError):load_config()
