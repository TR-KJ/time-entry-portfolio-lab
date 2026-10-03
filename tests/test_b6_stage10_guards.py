import contextlib
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch
from test_b6_stage10_money import row,ROOT
from b6 import stage10_config as config
from b6.stage10_input import frozen_candidates,load_inputs
from b6.stage10_search import (atomic,pack,unpack,open_store,job_specs,finish,run_job,
    full_simulation,complete_summary,verify_release,require_authorization)


class GuardTests(unittest.TestCase):
    def test_final_two_exact_hash_and_conditions(self):
        p=frozen_candidates();self.assertEqual([r['CandidateID'] for r in p],[config.AJ,config.GJ])
        self.assertEqual([(r['Entry'],r['Exit'],r['SL'],r['TPMode'],r['EventMode']) for r in p],[('15:50','15:50',20,'TP_NONE','E0'),('13:57','13:31',30,'TP_NONE','E0')])
    def test_stage9_mutation_rejected(self):
        with patch('b6.stage10_input.sha',return_value='0'*64),self.assertRaises(ValueError):frozen_candidates()
    def test_baseline_or_b6_hash_mismatch_rejected(self):
        for failed in ('baseline','b6'):
            with patch('b6.stage10_input.frozen_candidates',return_value=[]),patch('b6.stage10_input.sha',side_effect=lambda p: '0'*64 if p==failed else (config.BASELINE_SHA if p=='baseline' else config.LEDGER_SHA)),self.assertRaises(ValueError):load_inputs('baseline','b6')
    def test_current_exact27_excludes22_retains20(self):
        b=config.read(ROOT/config.INPUT/'stage10_portfolio_baseline.json')
        self.assertEqual(b['CurrentStrategyCount'],27);self.assertEqual(len(b['CurrentStrategyIDs']),27)
        self.assertEqual([int(s.split('_')[0]) for s in b['CurrentStrategyIDs']],[i for i in range(1,29) if i!=22])
        self.assertEqual(b['ExcludedDeploymentIDs'],['22_GA_C_2']);self.assertIn('20_EA_1A_MonTue_Short',b['CurrentStrategyIDs'])
        self.assertEqual(b['BaselineTradeLogSHA256'],config.BASELINE_SHA)
    def test_user_override_disables_r2_all_configs(self):
        c=config.load_config();self.assertFalse(c['GlobalR2Applied']);self.assertEqual(c['RiskPolicy'],'SAME_FIXED_PER_TRADE_RISK_ALL_COMPONENTS')
        self.assertTrue(c['NoRiskNormalization']);self.assertTrue(c['NoAdoptionThreshold']);self.assertTrue(c['NoRiskSelection'])
    def test_active_or_unknown_r2_policy_rejected(self):
        c=config.load_config()
        for k,v in [('GlobalR2Applied',True),('RiskPolicy','UNKNOWN_R2')]:
            with patch('b6.stage10_config.read',return_value={**c,k:v}),self.assertRaises(ValueError):config.load_config()
    def test_extra_risk_or_mode_rejected(self):
        c=config.load_config()
        for k,v in [('Risks',['0.25','0.5','1.0','1.5','2.0']),('MoneyModes',{})]:
            with patch('b6.stage10_config.read',return_value={**c,k:v}),self.assertRaises(ValueError):config.load_config()
    def test_fixed_32_jobs(self):
        jobs=job_specs();self.assertEqual(len(jobs),32);self.assertEqual(len({j[0] for j in jobs}),32)
        self.assertEqual(len(config.CONFIGS),4);self.assertEqual(len(config.MODES),2)
    def test_full_flags_required(self):
        for flags in [(False,False),(True,False),(False,True)]:
            with self.subTest(flags=flags),self.assertRaises(PermissionError):require_authorization('a'*40,*flags)
    def test_non_colab_rejected(self):
        with patch('b6.stage10_search.importlib.util.find_spec',return_value=None),self.assertRaises(PermissionError):require_authorization('a'*40,True,True)
    def test_runtime_mismatch_rejected(self):
        c=config.load_config();c['FormalRuntime']['Python']='0.0.0'
        with patch('b6.stage10_search.importlib.util.find_spec',return_value=object()),patch('b6.stage10_search.verify_release',return_value=c),self.assertRaises(ValueError):require_authorization('a'*40,True,True)
    def test_release_wrong_sha_dirty_and_manifest_rejected(self):
        with self.assertRaises(ValueError):verify_release('')
        with patch('b6.stage10_search.subprocess.check_output',return_value='b'*40),self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage10_search.subprocess.check_output',side_effect=['a'*40,'?? unknown.txt']),self.assertRaises(ValueError):verify_release('a'*40)
        with patch('b6.stage10_search.subprocess.check_output',side_effect=['a'*40,'']),patch('b6.stage10_search.subprocess.run'),patch('b6.stage10_search.sha',return_value='0'*64),self.assertRaises(ValueError):verify_release('a'*40)
    def test_resume_identity_strict(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(open_store(t,{'CodeSHA':'a'}),{})
            with self.assertRaises(ValueError):open_store(t,{'CodeSHA':'b'})
    def test_unknown_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            open_store(t,{'CodeSHA':'a'});atomic(Path(t)/'checkpoints.json',{'unknown':'x'})
            with self.assertRaises(ValueError):open_store(t,{'CodeSHA':'a'})
    def test_partial_finish_rejected_before_metrics(self):
        with tempfile.TemporaryDirectory() as t,self.assertRaises(ValueError):finish(t,{}, {})
    def test_partial_display_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            for n in ('stage10_summary.json','progress.json'):atomic(Path(t)/n,dict(State='RUNNING_STAGE10',CompletedJobs=31,ExpectedJobs=32,PeriodResultRows=128))
            with self.assertRaises(ValueError):complete_summary(t)
    def test_checkpoint_roundtrip_no_float_precision_loss(self):
        r={'x':D('0.123456789012345678901234567890123456789'),'none':None,'t':row()['EntryTime']}
        self.assertEqual(unpack(json.loads(json.dumps(pack(r)))),r)
    def test_notebook_default_run_all_no_io(self):
        nb=config.read(ROOT/'notebooks/b6_stage10_incremental_portfolio.ipynb');ns={}
        with patch('subprocess.run',side_effect=AssertionError('command')),patch('b6.stage10_search.full_simulation',side_effect=AssertionError('full')),contextlib.redirect_stdout(io.StringIO()):
            for c in nb['cells']:
                if c['cell_type']=='code':
                    self.assertEqual(c['outputs'],[]);self.assertIsNone(c['execution_count']);exec(''.join(c['source']),ns)
        for k in ('PREPARE_ENVIRONMENT','MOUNT_DRIVE','RUN_STAGE10_FULL','CHAT_CONFIRMED_STAGE10_FREEZE','SAVE_OUTPUT_TO_DRIVE'):self.assertIs(ns[k],False)
        self.assertEqual(ns['STAGE10_FREEZE_SHA'],'');self.assertEqual(ns['FROZEN_CONFIG'],config.load_config())
    def test_preparation_dont_write_bytecode_before_b6_import(self):
        nb=config.read(ROOT/'notebooks/b6_stage10_incremental_portfolio.ipynb')
        cell=''.join(nb['cells'][3]['source'])
        self.assertLess(cell.index('sys.dont_write_bytecode = True'),cell.index('from b6.'))
    def test_synthetic_full_export_resume_and_interaction(self):
        # Synthetic trades only: formal input loader and Colab gate replaced explicitly.
        rows=[row(r='1'),row(2,r='1',source='B6',cid=config.AJ,symbol='AUDJPY'),row(3,r='1',source='B6',cid=config.GJ)]
        c=config.load_config();audit={'BaselineSHA256':config.BASELINE_SHA,'B6LedgerSHA256':config.LEDGER_SHA}
        with tempfile.TemporaryDirectory() as t,patch('b6.stage10_search.require_authorization',return_value=(c,{'Synthetic':True})),patch('b6.stage10_search.load_inputs',return_value=(rows,audit)),contextlib.redirect_stdout(io.StringIO()):
            out=Path(t)/'output';full_simulation(Path(t)/'base',Path(t)/'b6',out,'a'*40,True,True)
            s=complete_summary(out);self.assertEqual(s['CompletedJobs'],32);self.assertEqual(s['PeriodResultRows'],128)
            first={p.name:p.read_bytes() for p in out.glob('stage10_*') if p.is_file()}
            with patch('b6.stage10_search.run_job',side_effect=AssertionError('completed jobs must not rerun')):full_simulation(Path(t)/'base',Path(t)/'b6',out,'a'*40,True,True)
            self.assertEqual(first,{p.name:p.read_bytes() for p in out.glob('stage10_*') if p.is_file()})
            import gzip,csv,zipfile
            with gzip.open(out/'stage10_decision_evidence.csv.gz','rt') as f:e=list(csv.DictReader(f))
            self.assertTrue(all(D(r['FinalCapitalInteraction'])==0 for r in e))
            with zipfile.ZipFile(out/'stage10_review.zip') as z:self.assertFalse(any('trade_log' in n or 'baseline_trades' in n for n in z.namelist()))
            self.assertFalse(s['RiskAllocationDecided']);self.assertFalse(s['LiveChanged']);self.assertFalse(s['StrategyNumberingAssigned'])
    def test_review_output_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);s=dict(State=config.STATE,CompletedJobs=32,ExpectedJobs=32,PeriodResultRows=128)
            atomic(p/'stage10_summary.json',s);atomic(p/'progress.json',s);atomic(p/'stage10_review.json',{'Summary':s,'OutputSHA256':{'data':'0'*64}});(p/'data').write_bytes(b'changed')
            with self.assertRaises(ValueError):complete_summary(p)
