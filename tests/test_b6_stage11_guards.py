import unittest,sys,json,tempfile,subprocess,os,shutil,hashlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage11_config import load_config,read,sha,INPUT,OUTPUT,CONFIGS,GJ,AJ,SOURCE_HASHES,PHASE5_SHA
from b6.stage11_r2 import source_audit
from b6.stage11_search import require_authorization,full_simulation,finish,complete_summary,verify_release
from b6.stage11_assignment import preflight

class GuardTests(unittest.TestCase):
    def test_default_notebook_has_no_io(self):
        nb=read(ROOT/'notebooks/b6_stage11_r2_incremental_portfolio.ipynb');scope={}
        with patch('builtins.open',side_effect=AssertionError('no file IO')),patch('subprocess.run',side_effect=AssertionError('no process')):
            for c in nb['cells']:
                if c['cell_type']=='code':exec(''.join(c['source']),scope)
        for k in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE11_FULL','CHAT_CONFIRMED_STAGE11_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(scope[k],False)
        self.assertEqual(scope['STAGE11_FREEZE_SHA'],'')
    def test_preparation_bytecode_before_import(self):
        nb=read(ROOT/'notebooks/b6_stage11_r2_incremental_portfolio.ipynb');s=''.join(nb['cells'][3]['source'])
        self.assertLess(s.index('sys.dont_write_bytecode = True'),s.index('from b6.'))
    def test_fresh_checkout_import_clean(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);shutil.copytree(ROOT/'src/research/b6',p/'src/research/b6');shutil.copy2(ROOT/'src/research/edge_decay_phase2_money_simulation.py',p/'src/research/edge_decay_phase2_money_simulation.py')
            subprocess.run(['git','init','-q',str(p)],check=True);subprocess.run(['git','add','.'],cwd=p,check=True)
            subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],cwd=p,check=True)
            env=dict(os.environ);env.pop('PYTHONDONTWRITEBYTECODE',None)
            subprocess.run([sys.executable,'-c',"import sys;sys.dont_write_bytecode=True;sys.path.insert(0,'src/research');from b6.stage11_search import verify_release"],cwd=p,env=env,check=True)
            self.assertFalse(list(p.rglob('__pycache__')));self.assertFalse(list(p.rglob('*.pyc')));self.assertEqual(subprocess.check_output(['git','status','--porcelain'],cwd=p,text=True),'')
    def test_auth_flags_before_any_inputs(self):
        with patch('b6.stage11_search.load_inputs',side_effect=AssertionError('input read')):
            for a,b in ((False,False),(True,False),(False,True)):
                with self.assertRaises(PermissionError):full_simulation('','','','', '',a,b)
    def test_noncolab_reject(self):
        with patch('b6.stage11_search.importlib.util.find_spec',return_value=None),self.assertRaises(PermissionError):require_authorization('a'*40,True,True)
    def test_clean_guard_not_weakened(self):
        with patch('b6.stage11_search.subprocess.check_output',side_effect=['a'*40,'?? random.txt']),self.assertRaisesRegex(ValueError,'clean'):verify_release('a'*40)
    def test_wrong_sha_reject(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage11_search.subprocess.check_output',return_value='b'*40),self.assertRaises(ValueError):verify_release('a'*40)
    def test_runtime_mismatch_reject(self):
        with patch('b6.stage11_search.importlib.util.find_spec',return_value=True),patch('b6.stage11_search.verify_release',return_value=load_config()),patch('b6.stage11_search.platform.python_version',return_value='0'),self.assertRaisesRegex(ValueError,'runtime'):require_authorization('a'*40,True,True)
    def test_partial_finish_rejected(self):
        with tempfile.TemporaryDirectory() as t,self.assertRaises(ValueError):finish(t,{}, {},[],{'Status':'PASS','Assignments':9760})
    def test_partial_display_rejected(self):
        with tempfile.TemporaryDirectory() as t,self.assertRaises(FileNotFoundError):complete_summary(t)
    def test_assignment_counts_required(self):
        with self.assertRaises(ValueError):preflight([],[])
    def test_safety_config(self):
        c=load_config()
        for k in ('AJOnlyConfigurationExists','FixedRiskFallbackResearch','LiveEnabled','StrategyNumberingEnabled','R2TradeFilter'):self.assertIs(c[k],False)
        for k in ('NoAdoptionThreshold','NoRanking','NoRiskSelection'):self.assertIs(c[k],True)
        self.assertEqual(len(c['PortfolioConfigs']),3);self.assertEqual(len(c['MoneyModes']),2)
    def test_source_content_commit_path_sha_exact(self):
        self.assertEqual(source_audit()['Status'],'PASS')
        for path,h in SOURCE_HASHES.items():
            x=read(ROOT/INPUT/'stage11_provenance'/(Path(path).name+'.json'))
            self.assertEqual(x['SourceCommit'],PHASE5_SHA);self.assertEqual(x['SourcePath'],path)
            self.assertRegex(x['SourceSHA256'],'^[0-9a-f]{64}$');self.assertEqual(hashlib.sha256(x['Content'].encode()).hexdigest(),h)
    def test_source_tamper_reject(self):
        with patch('b6.stage11_r2.read',return_value={'SourceCommit':'bad'}),self.assertRaises(ValueError):source_audit()
    def test_source_spec_locks_upstreams(self):
        spec=read(ROOT/INPUT/'stage11_source_spec.json')
        self.assertFalse(spec['HistoricalAssignment']['ScientificInput'])
        for n,h in spec['FrozenArtifactSHA256'].items():self.assertEqual(sha(ROOT/n),h)
    def test_actual_audits_counts_and_no_calculation(self):
        a=read(ROOT/OUTPUT/'trade_input_audit.json');self.assertEqual(a['Current2020Trades'],9083)
        self.assertEqual(a['B6Trades'],{AJ:339,GJ:338});self.assertEqual(list(sorted(a['Stage11PortfolioCounts'].values())),[9083,9421,9760])
        self.assertFalse(a['R2AssignmentsGenerated']);self.assertFalse(a['MoneySimulationExecuted'])
    def test_current27_identities20kept22excluded(self):
        ids=read(ROOT/INPUT/'stage10_portfolio_baseline.json')['CurrentStrategyIDs'];self.assertEqual(len(ids),27)
        self.assertIn('20_EA_1A_MonTue_Short',ids);self.assertNotIn('22_GA_C_2',ids)
    def test_m1_56_exact_audit_warmup(self):
        a=read(ROOT/OUTPUT/'m1_input_audit.json');self.assertEqual(len(a['Files']),56)
        self.assertTrue(all(x['Status']=='PASS' for x in a['Files']))
        self.assertTrue(all(x['ActualDatesBefore2020']>=272 for x in a['Coverage']));self.assertFalse(a['R2AssignmentsGenerated'])
    def test_stage10_archive_metadata_not_scientific_input(self):
        a=read(ROOT/OUTPUT/'stage10_input_audit.json');self.assertEqual(a['Status'],'PASS')
        for k in ('GlobalR2Applied','RiskAllocationDecided','LiveChanged','ScientificInput','PerformanceUsed'):self.assertFalse(a[k])
    def test_no_live_ea_set_write_or_decision_calls(self):
        for p in (ROOT/'src/research/b6').glob('stage11*.py'):
            s=p.read_text();self.assertNotIn('.decide(',s);self.assertNotIn('AJ_ONLY_ADOPTION',s)
    def test_release_manifest(self):
        for n,h in read(ROOT/INPUT/'stage11_release_manifest.json').items():self.assertEqual(sha(ROOT/n),h,n)
    def test_stage10_immutable_except_appended_docs(self):
        for n,h in read(ROOT/INPUT/'stage10_release_manifest.json').items():
            if n not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):self.assertEqual(sha(ROOT/n),h,n)
