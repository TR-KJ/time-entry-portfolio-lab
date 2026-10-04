"""Full pipeline uses generated synthetic ledgers and synthetic daily prices only."""
import unittest,sys,tempfile,json,contextlib,io
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage11_money import r
from test_b6_stage11_r2 import fixture,ENTRY
from b6.stage11_config import load_config,AJ,GJ,STATE
from b6.stage11_r2 import daily_from_rows
from b6.stage11_search import full_simulation,complete_summary

class WorkflowTests(unittest.TestCase):
    def synthetic(self):
        rows=[r(i+1,r='0') for i in range(9083)]
        rows += [r(10000+i,source='B6',cid=GJ,r='0') for i in range(338)]
        rows += [r(11000+i,source='B6',cid=AJ,r='0') for i in range(339)]
        for x in rows:x.pop('AppliedRiskPercent')
        return rows
    def context(self):
        c=load_config();stack=contextlib.ExitStack()
        stack.enter_context(patch('b6.stage11_search.require_authorization',return_value=(c,{'SyntheticRuntime':True})))
        stack.enter_context(patch('b6.stage11_search.load_inputs',return_value=(self.synthetic(),{'BaselineSHA256':'synthetic-baseline','B6LedgerSHA256':'synthetic-b6'})))
        manifest=type('Manifest',(),{'Symbol':['GBPJPY']})()
        stack.enter_context(patch('b6.stage11_search.audit_m1',return_value=(manifest,{}, {'Status':'SYNTHETIC'})))
        loader=stack.enter_context(patch('b6.stage11_search.load_daily',return_value=daily_from_rows(fixture(271),ENTRY)))
        stack.enter_context(patch('b6.stage11_search.stage10_archive_audit',return_value={'Status':'SYNTHETIC'}))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        return stack,loader
    def run_fake(self,out,code='a'*40):return full_simulation('/synthetic/base','/synthetic/b6','/synthetic/m1',out,code,True,True)
    def test_end_to_end_six_jobs_freeze_resume_and_tamper(self):
        stack,loader=self.context()
        with stack,tempfile.TemporaryDirectory() as t:
            out=Path(t)/'result';s=self.run_fake(out)
            self.assertEqual(s['State'],STATE);self.assertEqual(s['MoneyJobs'],6);self.assertEqual(complete_summary(out),s)
            self.assertEqual(loader.call_count,1)
            checkpoint=(out/'assignment_checkpoint.json').read_bytes()
            self.assertEqual(self.run_fake(out),s);self.assertEqual(loader.call_count,1)
            self.assertEqual((out/'assignment_checkpoint.json').read_bytes(),checkpoint)
            with self.assertRaisesRegex(ValueError,'resume identity'):self.run_fake(out,'b'*40)
            (out/'assignment_checkpoint.json').write_bytes(checkpoint+b' ')
            with self.assertRaisesRegex(ValueError,'assignment checkpoint'):self.run_fake(out)
    def test_partial_failure_and_resume_without_reassigning(self):
        from b6.stage11_search import run_job
        stack,loader=self.context();calls=[]
        def fail(rows,mode,name):
            calls.append(name)
            if len(calls)==2:raise RuntimeError('synthetic interruption')
            return run_job(rows,mode,name)
        with stack,tempfile.TemporaryDirectory() as t:
            out=Path(t)/'result'
            with patch('b6.stage11_search.run_job',side_effect=fail),self.assertRaises(RuntimeError):self.run_fake(out)
            self.assertFalse((out/'stage11_summary.json').exists());self.assertFalse((out/'stage11_portfolio_period_results.csv.gz').exists())
            with self.assertRaises(FileNotFoundError):complete_summary(out)
            self.assertEqual(self.run_fake(out)['CompletedJobs'],6);self.assertEqual(loader.call_count,1)
    def test_checkpoint_tamper_rejected(self):
        stack,_=self.context()
        with stack,tempfile.TemporaryDirectory() as t:
            out=Path(t)/'result';self.run_fake(out)
            (out/'shards/0-0.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'checkpoint hash'):self.run_fake(out)
    def test_output_tamper_cannot_display(self):
        stack,_=self.context()
        with stack,tempfile.TemporaryDirectory() as t:
            out=Path(t)/'result';self.run_fake(out)
            (out/'stage11_r2_distribution.csv.gz').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'output hash'):complete_summary(out)
