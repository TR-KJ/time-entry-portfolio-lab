"""Synthetic-only Stage7 checks; never replay real 2026 candidate prices."""
import ast,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage1 import fixture
from test_b6_stage6 import candidate as base_candidate,calendar,trades
from b6.stage7_config import load_config
from b6.stage7_adapter import modules,adapted_tree
from b6.stage7_data import canonical_slice,validate_prices,availability,START,END
from b6.stage7_engine import make_engine,replay_candidate
from b6.stage7_metrics import aggregate,evaluate
from b6.stage7_search import full_monitor,finish
from b6.stage2a_search import open_store,save_job
from b6.stage1_search import atomic_json
from b6.execution import PIPS,SPREAD

def candidate(*args,**kwargs):
    return dict(base_candidate(*args,**kwargs),FormalValidationStatus='PASS',ValidationProvenance={f'Combined_{k}':'synthetic' for k in ('PF','AvgR','TotalR','MaxDDR')})

def compare(test,bars,p,dates,cal=None):
    cal=calendar() if cal is None else cal
    f,fd=replay_candidate(p,dates,cal,engine=make_engine(bars,p['Symbol']));r,rd=replay_candidate(p,dates,cal,bars=bars)
    np.testing.assert_array_equal(f.status,r.status);np.testing.assert_array_equal(f.raw_r,r.raw_r);test.assertEqual(fd,rd)
    for a,b in zip(f.rows[0],r.rows[0]):
        for k,v in a.items():test.assertEqual(v,b[k],(k,a,b))
    coverage=availability(bars,p['Symbol'])
    test.assertEqual(evaluate(p,f,fd,coverage),evaluate(p,r,rd,coverage));return f

class ExecutionTests(unittest.TestCase):
    def test_seven_pairs_both_directions_none_finite_same_overnight(self):
        dates=pd.to_datetime(['2026-02-02','2026-02-09'])
        for s in PIPS:
            bars=fixture(s,dates,n=1600)
            for direction in ('L','S'):
                for tp in (None,25):
                    for entry,hold in ((601,58),(1439,61)):compare(self,bars,candidate(s,direction,entry,hold,tp),dates)
    def test_all_event_modes_frozen_subset(self):
        dates=pd.to_datetime(['2026-02-02','2026-02-09']);b=fixture('AUDJPY',dates,n=1600);cal=calendar({'BOJ':['2026-02-02'],'AUD_CPI':['2026-02-09']})
        for mode in ('E0','E1','E2'):compare(self,b,candidate('AUDJPY',entry=600,hold=60,mode=mode),dates,cal)
    def test_sl_first_entry_exit_inclusive_raw_boundary(self):
        date=pd.Timestamp('2026-02-02');p=candidate(entry=60,hold=60,tp=20);pip=PIPS['USDJPY'];price=100+SPREAD['USDJPY']*pip;sl=price-20*pip;tp=price+20*pip
        for minute in (60,120):
            for low in (sl,np.nextafter(sl,np.inf)):
                b=pd.DataFrame(dict(Open=100.,High=100.,Low=100.,Close=100.),index=pd.date_range(date,periods=130,freq='min'));b.loc[date+pd.Timedelta(minutes=minute),['Low','High']]=[low,tp]
                r=compare(self,b,p,[date]);self.assertEqual(r.rows[0][0]['ExitReason'],'SL' if low==sl else 'TP')
    def test_fallback_zero_through_four_plus_five_missing_entry_exit_gap(self):
        date=pd.Timestamp('2026-02-02');p=candidate(entry=60,hold=60);base=fixture('USDJPY',[date],n=140)
        for delay in range(6):
            b=base.drop(pd.date_range(date+pd.Timedelta(minutes=120),periods=delay,freq='min'));r=compare(self,b,p,[date]);self.assertEqual(r.status[0]==0,delay<=4)
            if delay<=4:self.assertEqual(r.rows[0][0]['ExitDelayMinutes'],delay)
        for minutes in ([60],list(range(120,125)),[90,91]):compare(self,base.drop([date+pd.Timedelta(minutes=i) for i in minutes]),p,[date])
    def test_exit_required_before_early_sl(self):
        date=pd.Timestamp('2026-02-02');p=candidate(entry=60,hold=60);b=fixture('USDJPY',[date],n=120);b.loc[date+pd.Timedelta(minutes=60),'Low']=1
        r=compare(self,b,p,[date]);self.assertEqual(r.rows[0][0]['Status'],'MISSING_EXIT')
    def test_year_end_stop_and_future_date_rejection(self):
        for d in ('2026-01-01','2026-01-02'):
            date=pd.Timestamp(d);b=fixture('USDJPY',[date],n=1400);r=compare(self,b,candidate(weekday=date.weekday()),[d]);self.assertEqual(r.rows[0][0]['Status'],'FILTERED_YEAR_END')
        with self.assertRaises(ValueError):replay_candidate(candidate(),['2026-09-14'],calendar(),bars=fixture('USDJPY',[pd.Timestamp('2026-02-02')]))
    def test_fomc_next_day_planned_exit_early_sl_fallback(self):
        d=pd.Timestamp('2026-02-02');b=fixture('USDJPY',[d],n=1600);p=candidate(entry=1380,hold=180,mode='E1');cal=calendar({'FOMC':['2026-02-02']})
        r=compare(self,b,p,[d],cal);self.assertEqual(r.rows[0][0]['Status'],'FILTERED_EVENT')
        p=candidate(entry=480,hold=59,mode='E1');b=fixture('USDJPY',[d],n=600).drop(pd.date_range(d+pd.Timedelta(minutes=539),periods=4,freq='min'));r=compare(self,b,p,[d],calendar({'BOJ':['2026-02-02']}));self.assertEqual(r.status[0],0)
    def test_event_window_edges(self):
        m=modules()['stage4_events'];cal=calendar({'BOJ':['2026-02-02']})
        for e,h,hit in ((480,60,True),(900,30,True),(480,59,False),(901,30,False)):
            self.assertEqual(bool(m.matches(candidate(entry=e,hold=h),['2026-02-02'],'E1',cal)[0]),hit)

class PeriodTests(unittest.TestCase):
    def test_canonical_boundaries(self):
        raw=pd.to_datetime(['2025-12-31 16:59','2025-12-31 17:00','2026-09-08 18:00','2026-09-09 17:59','2026-09-09 18:00'])
        b=canonical_slice([pd.DataFrame(dict(RawDatetime=raw,Open=1.,High=1.,Low=1.,Close=1.))])
        self.assertEqual(list(b.index),list(pd.to_datetime(['2026-01-01','2026-09-09','2026-09-09 23:59'],format='mixed')))
    def test_outside_executor_rows(self):
        for d in ('2025-12-31','2026-09-10'):
            with self.assertRaises(ValueError):make_engine(fixture('USDJPY',[pd.Timestamp(d)],n=1),'USDJPY')
    def test_mixed_array_rejected(self):
        b=fixture('USDJPY',[pd.Timestamp('2026-02-02')],n=2);bad=b.iloc[:1].copy();bad.index=pd.DatetimeIndex(['2026-09-10'])
        with self.assertRaises(ValueError):validate_prices(pd.concat([b,bad]))
    def test_actual_end_no_forward_fill(self):
        raw=pd.to_datetime(['2026-09-08 23:58','2026-09-09 00:00'])
        b=canonical_slice([pd.DataFrame(dict(RawDatetime=raw,Open=1.,High=1.,Low=1.,Close=1.))])
        self.assertEqual(len(b),2);self.assertEqual(b.index.max(),pd.Timestamp('2026-09-09 06:00'))
        self.assertNotIn(pd.Timestamp('2026-09-09 05:59'),b.index)
    def test_missing_exit_at_data_end_no_trade(self):
        d=pd.Timestamp('2026-09-09');b=fixture('USDJPY',[d],n=361)
        r=compare(self,b,candidate(entry=350,hold=30,weekday=2),[d]);self.assertEqual(r.rows[0][0]['Status'],'MISSING_EXIT')
    def test_private_modules_no_shared_global_mutation(self):
        from b6 import execution,stage1_engine
        from b6.stage6_adapter import modules as previous
        before=(execution.START,execution.END,stage1_engine.MINUTES,previous()['execution'].START,previous()['execution'].END)
        m=modules();self.assertEqual((m['execution'].START,m['execution'].END),(START,END))
        self.assertEqual(before,(execution.START,execution.END,stage1_engine.MINUTES,previous()['execution'].START,previous()['execution'].END))
    def test_checked_ast_transform(self):
        for name in ('execution','stage1_engine','stage2a_engine','stage4_events'):
            self.assertIsInstance(adapted_tree(name,(ROOT/f'src/research/b6/{name}.py').read_text()),ast.Module)
        with self.assertRaises(ValueError):adapted_tree('stage1_engine',(ROOT/'src/research/b6/stage1_engine.py').read_text().replace('chosen//1440+2','chosen//1440+3'))
    def test_weekday_epoch(self):
        for date in ('2026-02-02','2026-02-06'):
            d=pd.Timestamp(date);b=fixture('USDJPY',[d],n=1400);r=compare(self,b,candidate(weekday=d.weekday()),[d]);self.assertEqual(r.status[0],0)

class MetricsTests(unittest.TestCase):
    def test_raw_r(self):self.assertEqual(aggregate(trades([.02000000000001],2026))['AvgR'],.02000000000001)
    def test_zero_inf_undefined(self):
        m=aggregate(trades([1.,0.],2026));self.assertEqual((m['Trades'],m['Wins'],m['Losses'],m['ZeroR'],m['PF']),(2,1,0,1,'INF'))
        self.assertEqual(aggregate(trades([0.],2026))['PF'],'UNDEFINED');self.assertEqual(aggregate([])['PF'],'UNDEFINED')
    def test_chronological_dd_initial_peak_zero(self):
        self.assertEqual(aggregate(list(reversed(trades([-2.,5.,-4.,-4.],2026))))['MaxDDR'],8.)
        self.assertEqual(aggregate(trades([-2.,-3.],2026))['MaxDDR'],5.)
    def test_negative_and_positive_do_not_change_formal_status(self):
        for raw in (-100.,100.,0.):
            p=candidate();d=pd.Timestamp('2026-02-02');row=dict(Status='OK',EntryTime=str(d+pd.Timedelta(hours=10)),CloseTime=str(d+pd.Timedelta(hours=11)),ScheduledExitTime=str(d+pd.Timedelta(hours=11)),ExitReason='TimeExit',ExitDelayMinutes=0,missing_path_minutes=0)
            replay=modules()['stage2a_engine'].Replay(pd.DatetimeIndex([d]),np.array([0]),[[row]],np.array([[raw]]))
            job=evaluate(p,replay,{},dict(FirstAvailableJST=str(d),LastAvailableJST=str(d+pd.Timedelta(days=1))))
            self.assertEqual(job['monitor']['FormalValidationStatus'],'PASS');self.assertEqual(job['monitor']['MonitorState'],'OBSERVED')
            self.assertEqual(job['monitor']['MonitorTotalR'],raw);self.assertFalse(any(k in job['monitor'] for k in ('MonitorPass','MonitorFail','MonitorRank','MonitorThreshold')))
    def test_outside_trade_rejected(self):
        d=pd.Timestamp('2026-09-09');row=dict(Status='OK',EntryTime=str(d),CloseTime='2026-09-10',ScheduledExitTime='2026-09-10')
        r=modules()['stage2a_engine'].Replay(pd.DatetimeIndex([d]),np.array([0]),[[row]],np.array([[1.]]))
        with self.assertRaises(ValueError):evaluate(candidate(),r,{}, {})

class RunnerTests(unittest.TestCase):
    def test_authorization_before_io(self):
        with patch('b6.stage7_search.load_input',side_effect=AssertionError('input')):
            for run,confirmed in ((False,False),(False,True),(True,False)):
                with self.assertRaises(PermissionError):full_monitor('data','out','a'*40,run,confirmed)
            with patch('b6.stage7_search.importlib.util.find_spec',return_value=None):
                with self.assertRaises(PermissionError):full_monitor('data','out','a'*40,True,True)
    def test_resume_identity(self):
        identity=dict(code_sha='a',config_sha256='b',monitor_candidate_sha256='c',stage6_code_sha='d',stage6_validation_results_sha256='e',candidate_count=17,candidate_ids=['a'],inputs=[{'Filename':'a','SHA256':'b'}],calendar_sha256='f',runtime=dict(Python='p',Numpy='n',Pandas='v'))
        with tempfile.TemporaryDirectory() as out:
            open_store(out,identity)
            for k in identity:
                with self.assertRaises(ValueError):open_store(out,{**identity,k:'changed'})
            for key in identity['runtime']:
                changed=copy.deepcopy(identity);changed['runtime'][key]='changed'
                with self.assertRaises(ValueError):open_store(out,changed)
    def test_incomplete_no_results(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError):finish(out,{},[candidate()],load_config())
            self.assertEqual(list(Path(out).iterdir()),[])
    def test_synthetic_finish_observed_no_ranking(self):
        p=candidate();dates=pd.to_datetime(['2026-02-02']);bars=fixture('USDJPY',dates,n=1400);r,d=replay_candidate(p,dates,calendar(),bars=bars);coverage=availability(bars,'USDJPY');job=evaluate(p,r,d,coverage)
        with tempfile.TemporaryDirectory() as out:
            ledger=open_store(out,dict(test=True,inputs=[]));save_job(out,ledger,p['CandidateID'],job)
            for n in ('effective_config.json','stage6_input_audit.json'):atomic_json(Path(out)/n,{})
            atomic_json(Path(out)/'m1_input_audit.json',dict(CanonicalCoverage=[coverage]))
            result=finish(out,ledger,[p],{**load_config(),'candidate_count':1})
            self.assertEqual(result['State'],'COMPLETE_STAGE7_MONITOR_ONLY');self.assertTrue(result['NoMonitorPassFail']);self.assertFalse(result['FormalValidationChanged']);self.assertFalse(result['PortfolioExecuted']);self.assertFalse(result['LiveChanged']);self.assertTrue(result['NoRanking'])
            job['monitor']['FormalValidationStatus']='FAIL';save_job(out,ledger,p['CandidateID'],job)
            with self.assertRaises(ValueError):finish(out,ledger,[p],{**load_config(),'candidate_count':1})
    def test_no_portfolio_live_or_thresholds(self):
        c=load_config()
        for k in ('no_formal_monitor_gate','no_ranking','no_retuning','formal_validation_immutable'):self.assertTrue(c[k])
        for k in ('portfolio_enabled','live_enabled'):self.assertFalse(c[k])
        for k in ('pass_conditions','sample_sufficiency','dd_limit','monitor_thresholds'):self.assertNotIn(k,c)
