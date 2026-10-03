import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage10_config import sha,read,INPUT,OUTPUT


class ReleaseTests(unittest.TestCase):
    def test_manifest_and_frozen_dependencies_unchanged(self):
        for name,h in read(ROOT/INPUT/'stage10_release_manifest.json').items():self.assertEqual(sha(ROOT/name),h,name)
        for name,h in read(ROOT/INPUT/'stage9_release_manifest.json').items():
            if name not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(sha(ROOT/name),h,name)
    def test_no_price_engine_or_adoption_imports(self):
        forbidden=('stage1_engine','stage2a_engine','stage8_engine','stage8_data','volatility_phase1','volatility_phase2','volatility_phase3')
        for p in (ROOT/'src/research/b6').glob('stage10*.py'):
            s=p.read_text()
            self.assertTrue(all(n not in s for n in forbidden),p.name)
            if p.name!='stage10_test_suite.py':self.assertNotIn('.decide(',s)
    def test_actual_audit_only_no_formal_money(self):
        a=read(ROOT/OUTPUT/'input_trade_ledger_audit.json')
        self.assertEqual(a['Current2020Trades'],9083);self.assertEqual(sum(a['B6Trades'].values()),677)
        for k in ('PortfolioSimulationExecuted','M1Read','ReplayExecuted','GlobalR2Applied'):self.assertFalse(a[k])
    def test_fresh_checkout_import_keeps_clean_no_bytecode(self):
        # Track a byte-identical small checkout, then execute Notebook preparation's import order.
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);import shutil
            shutil.copytree(ROOT/'src/research/b6',p/'src/research/b6')
            shutil.copy2(ROOT/'src/research/edge_decay_phase2_money_simulation.py',p/'src/research/edge_decay_phase2_money_simulation.py')
            subprocess.run(['git','init','-q',str(p)],check=True)
            subprocess.run(['git','add','.'],cwd=p,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],cwd=p,check=True)
            code="import sys;sys.dont_write_bytecode=True;sys.path.insert(0,'src/research');from b6.stage10_search import verify_release"
            env=dict(os.environ);env.pop('PYTHONDONTWRITEBYTECODE',None)
            subprocess.run([sys.executable,'-c',code],cwd=p,env=env,check=True)
            self.assertFalse(list(p.rglob('__pycache__')));self.assertFalse(list(p.rglob('*.pyc')))
            self.assertEqual(subprocess.check_output(['git','status','--porcelain'],cwd=p,text=True),'')
