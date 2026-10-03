import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage8_pairwise import point,trade
from b6.stage8_search import finish,full_analysis,validate_job
from b6.stage8_config import load_config
from b6.stage8_data import START,END
from b6.stage8_adapter import modules
from b6.stage8_metrics import evaluate
from b6.stage2a_search import open_store,save_job
from b6.stage1_search import atomic_json

class RunnerTests(unittest.TestCase):
    def test_authorization_before_price_io(self):
        with patch('b6.stage8_search.load_input',side_effect=AssertionError('input')):
            for run,confirmed in ((False,False),(False,True),(True,False)):
                with self.assertRaises(PermissionError):full_analysis('data','out','a'*40,run,confirmed)
            with patch('b6.stage8_search.importlib.util.find_spec',return_value=None):
                with self.assertRaises(PermissionError):full_analysis('data','out','a'*40,True,True)
    def test_runtime_mismatch_before_m1_read(self):
        with patch('b6.stage8_search.require_authorization',return_value='a'*40),patch('b6.stage8_search.load_input',return_value=([],{},{})),patch('b6.stage8_search.platform.python_version',return_value='wrong'),patch('b6.stage8_search.audit_inputs',side_effect=AssertionError('price read')):
            with self.assertRaisesRegex(ValueError,'runtime'):full_analysis('/synthetic-data','/synthetic-out','a'*40,True,True)
    def test_resume_identity_every_field_and_runtime(self):
        i=dict(code_sha='a',config_sha256='b',eligibility_sha256='c',candidate_pool_sha256='d',stage7_code_sha='e',candidate_count=9,candidate_ids=['a','b'],inputs=[dict(Filename='x',SHA256='y')],calendar_sha256='f',runtime=dict(Python='p',Numpy='n',Pandas='v'))
        with tempfile.TemporaryDirectory() as out:
            open_store(out,i)
            for k in i:
                with self.assertRaises(ValueError):open_store(out,{**i,k:'changed'})
            for k in i['runtime']:
                changed=copy.deepcopy(i);changed['runtime'][k]='changed'
                with self.assertRaises(ValueError):open_store(out,changed)
    def test_partial_finish_no_metrics(self):
        with tempfile.TemporaryDirectory() as out,patch('b6.stage8_search.all_pairs',side_effect=AssertionError('partial pairwise')):
            with self.assertRaises(ValueError):finish(out,{},[point('synthetic')],load_config())
            self.assertEqual(list(Path(out).iterdir()),[])
    def synthetic_job(self,p):
        dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D');dates=dates[dates.weekday==p['Weekday']];rows=[dict(Status='MISSING_ENTRY') for _ in dates];status=np.full(len(dates),3);raw=np.full((1,len(dates)),np.nan)
        for date,r in [('2020-02-03',1.),('2024-02-05',-1.),('2026-02-02',0.)]:
            i=dates.get_loc(pd.Timestamp(date));t=trade(p,date,r)
            rows[i]=dict(Status='OK',EntryTime=t['ActualEntry'],ScheduledExitTime=t['PlannedExit'],CloseTime=t['ActualClose'],ExitReason='TimeExit',ExitDelayMinutes=0,missing_path_minutes=0);status[i]=0;raw[0,i]=r
        replay=modules()['stage2a_engine'].Replay(dates,status,[rows],raw);return evaluate(p,replay,{})
    def test_synthetic_nine_candidate_complete_outputs(self):
        points=[point('SYNTHETIC-'+str(i),600+i,symbol='AUDJPY' if i==8 else 'GBPJPY') for i in range(9)]
        with tempfile.TemporaryDirectory() as out:
            ledger=open_store(out,dict(test=True,inputs=[]))
            for p in points:save_job(out,ledger,p['CandidateID'],self.synthetic_job(p))
            for name in ('effective_config.json','stage7_input_audit.json','m1_input_audit.json','deployment_eligibility_audit.json','stage8_deployment_eligibility.json','stage8_candidate_pool.json'):atomic_json(Path(out)/name,{})
            s=finish(out,ledger,points,load_config());self.assertEqual(s['State'],'COMPLETE_STAGE8_OVERLAP_CORRELATION_ONLY');self.assertEqual(s['PairwiseRows'],144);self.assertEqual(s['CandidatePeriodRows'],36);self.assertEqual(s['TradeLedgerRows'],27)
            self.assertFalse(s['FamilyConsolidationExecuted']);self.assertFalse(s['PortfolioExecuted']);self.assertFalse(s['LiveChanged']);self.assertTrue(s['NoSelection'])
            self.assertEqual(len(list(Path(out).glob('matrix_*.csv'))),20);self.assertTrue((Path(out)/'stage8_review.zip').exists())
    def test_missing_opportunity_or_schedule_mutation_rejected(self):
        p=point('SYNTHETIC');job=self.synthetic_job(p);validate_job(job,p)
        for mode in ('opportunity','schedule','research'):
            d=copy.deepcopy(job)
            if mode=='opportunity':d['diagnostics'].pop()
            if mode=='schedule':d['ledger'][0]['PlannedEntry']='2020-02-03 00:00:00'
            if mode=='research':d['candidate']['SL']=999
            with self.assertRaises(ValueError):validate_job(d,p)
    def test_no_stage9_or_selection_api(self):
        import b6.stage8_search as module
        c=load_config()
        for k in ('no_thresholds','no_ranking','no_selection','no_clustering','no_retuning'):self.assertTrue(c[k])
        for k in ('stage9_enabled','portfolio_enabled','live_enabled','strategy_numbering_enabled'):self.assertFalse(c[k])
        for key in ('cluster','select_representative','rank','stage9','portfolio'):self.assertFalse(any(key in n for n in vars(module) if callable(getattr(module,n))))
