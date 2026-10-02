"""Synthetic-only Validation replay/period/metrics; no formal candidate performance."""
import ast,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage1 import fixture
from b6.stage6_config import load_config
from b6.stage6_input import load_input,validate_payload,assert_frozen_candidate
from b6.stage6_adapter import modules,adapted_tree
from b6.stage6_data import canonical_slice,validate_prices,START,END
from b6.stage6_engine import make_engine,replay_candidate
from b6.stage6_metrics import aggregate,evaluate
from b6.stage6_search import full_validation,finish,space
from b6.stage4_calendar import CLOCKS
from b6.stage4_events import applicable_events
from b6.stage5_validation import assess
from b6.stage2a_search import open_store,save_job
from b6.stage1_search import atomic_json
from b6.execution import PIPS,SPREAD

def candidate(symbol='USDJPY',direction='L',entry=600,hold=60,tp=None,weekday=0,mode='E0'):
    return dict(CandidateID='SYNTHETIC-'+symbol+'-'+direction,Symbol=symbol,Direction=direction,Weekday=weekday,FinalEntryJST=f'{entry//60:02d}:{entry%60:02d}',FinalExitJST=f'{(entry+hold)%1440//60:02d}:{(entry+hold)%60:02d}',FinalExitDayOffset=(entry+hold)//1440,FinalHoldingMinutes=hold,AdjustedEntryMinute=entry,AdjustedExitMinute=(entry+hold)%1440,AdjustedExitDayOffset=(entry+hold)//1440,PlannedHoldingMinutes=hold,SL=20,TP=tp,TPMode='TP_NONE' if tp is None else 'FINITE',SelectedEventMode=mode,ApplicableEvents=applicable_events(symbol,mode),FixedSpreadPips=SPREAD[symbol],PipSize=PIPS[symbol],DiscoveryMaxDDR=5.,DiscoveryMetrics=dict(MaxDDR=5.))

def calendar(dates=None):return dict(Clocks=CLOCKS,Dates={e:(dates or {}).get(e,[]) for e in CLOCKS})

def compare(test,bars,p,dates,cal=None):
    cal=calendar() if cal is None else cal
    f,fd=replay_candidate(p,dates,cal,engine=make_engine(bars,p['Symbol']));r,rd=replay_candidate(p,dates,cal,bars=bars)
    np.testing.assert_array_equal(f.status,r.status);np.testing.assert_array_equal(f.raw_r,r.raw_r);test.assertEqual(fd,rd)
    for a,b in zip(f.rows[0],r.rows[0]):
        for k,v in a.items():test.assertEqual(v,b[k],(k,a,b))
    test.assertEqual(evaluate(p,f,fd),evaluate(p,r,rd));return f

class InputTests(unittest.TestCase):
    def test_exact_stage5_artifacts_and_count(self):
        points,_,a=load_input();self.assertEqual(len(points),50);self.assertTrue(a['CandidateArtifactUnchanged']);self.assertTrue(a['ContractUnchanged'])
    def test_wrong_stage5_commit(self):
        c=load_config();c['stage5_commit']='0'*40
        with self.assertRaises(Exception):load_input(c)
    def test_wrong_candidate_and_contract_sha(self):
        for k in ('candidate_sha256','contract_sha256','stage5_config_sha256'):
            c=load_config();c[k]='0'*64
            with self.assertRaises(ValueError):load_input(c)
    def test_count_duplicate_execution_calendar_dd_mutations(self):
        c=load_config();f=json.loads((ROOT/c['candidate_file']).read_text());v=json.loads((ROOT/c['contract_file']).read_text())
        for change in ('count','duplicate','execution','calendar','dd'):
            d=copy.deepcopy(f)
            if change=='count':d['Candidates'].pop()
            if change=='duplicate':d['Candidates'][1]['CandidateID']=d['Candidates'][0]['CandidateID']
            if change=='execution':d['ExecutionContract']['HitEpsilon']=1e-8
            if change=='calendar':d['EventCalendarProvenance']['SHA256']='bad'
            if change=='dd':d['Candidates'][0]['DiscoveryMaxDDR']=float('nan')
            with self.assertRaises(ValueError):validate_payload(d,v,c)
    def test_all_candidate_conditions_immutable(self):
        p=candidate()
        for key in ('CandidateID','Symbol','Direction','Weekday','FinalEntryJST','FinalExitJST','FinalExitDayOffset','FinalHoldingMinutes','SL','TP','SelectedEventMode','FixedSpreadPips','PipSize'):
            q=copy.deepcopy(p);q[key]='mutation'
            with self.assertRaises(ValueError):assert_frozen_candidate(q,p)
    def test_contract_rule_mismatch(self):
        c=load_config();f=json.loads((ROOT/c['candidate_file']).read_text());v=json.loads((ROOT/c['contract_file']).read_text());c['sample_sufficiency']['AnnualMinTrades']=29
        with self.assertRaises(ValueError):validate_payload(f,v,c)

class PeriodTests(unittest.TestCase):
    def test_jst_exact_boundaries_and_entry_year(self):
        raw=pd.to_datetime(['2023-12-31 16:59','2023-12-31 17:00','2024-12-31 17:00','2025-12-31 16:59','2025-12-31 17:00'])
        frames=[pd.DataFrame(dict(RawDatetime=raw,Open=1.,High=1.,Low=1.,Close=1.))];b=canonical_slice(frames)
        self.assertEqual(list(b.index),list(pd.to_datetime(['2024-01-01 00:00','2025-01-01 00:00','2025-12-31 23:59'])));self.assertEqual(list(b.index.year),[2024,2025,2025])
    def test_2023_and_2026_executor_rows_rejected(self):
        for d in ('2023-12-31','2026-01-01'):
            b=fixture('USDJPY',[pd.Timestamp(d)],n=1)
            with self.assertRaises(ValueError):make_engine(b,'USDJPY')
    def test_mixed_array_single_bad_row_rejected(self):
        b=fixture('USDJPY',[pd.Timestamp('2024-02-05')],n=2);bad=b.iloc[:1].copy();bad.index=pd.DatetimeIndex(['2026-01-01'])
        with self.assertRaises(ValueError):validate_prices(pd.concat([b,bad]))
    def test_canonical_duplicate_and_ohlc_reject(self):
        frame=pd.DataFrame(dict(RawDatetime=pd.to_datetime(['2024-02-05','2024-02-05']),Open=1.,High=1.,Low=1.,Close=1.))
        with self.assertRaises(ValueError):canonical_slice([frame])
        frame=frame.iloc[:1].copy();frame['High']=.5
        with self.assertRaises(ValueError):canonical_slice([frame])
    def test_shared_discovery_modules_unchanged(self):
        from b6 import execution,stage1_engine,stage4_events
        before=(execution.START,execution.END,stage1_engine.START,stage1_engine.MINUTES)
        m=modules();self.assertEqual(before,(execution.START,execution.END,stage1_engine.START,stage1_engine.MINUTES));self.assertEqual(execution.START,pd.Timestamp('2020-01-01'));self.assertEqual(m['execution'].START,START);self.assertEqual(m['execution'].END,END)
        with self.assertRaises(ValueError):stage4_events.matches(candidate(),['2024-02-05'],'E0',calendar())
    def test_only_allowlisted_ast_period_changes(self):
        for name in ('execution','stage1_engine','stage2a_engine','stage4_events'):
            source=(ROOT/f'src/research/b6/{name}.py').read_text();tree=adapted_tree(name,source);self.assertIsInstance(tree,ast.Module)
        with self.assertRaises(ValueError):adapted_tree('stage1_engine',(ROOT/'src/research/b6/stage1_engine.py').read_text().replace('chosen//1440+2','chosen//1440+3'))
    def test_weekday_epoch_monday_and_friday(self):
        for date,weekday in [('2024-02-05',0),('2024-02-09',4)]:
            b=fixture('USDJPY',[pd.Timestamp(date)],n=1440);r=compare(self,b,candidate(weekday=weekday),[date]);self.assertEqual(r.status[0],0)

class ExecutionTests(unittest.TestCase):
    def test_seven_pairs_both_directions_none_finite_same_overnight(self):
        dates=pd.to_datetime(['2024-02-05','2025-02-03'])
        for s in PIPS:
            bars=fixture(s,dates,n=1600)
            for direction in ('L','S'):
                for tp in (None,25):
                    for entry,hold in ((601,58),(1439,61)):compare(self,bars,candidate(s,direction,entry,hold,tp),dates)
    def test_all_event_modes_frozen_subset(self):
        dates=pd.to_datetime(['2024-02-05','2025-02-03']);b=fixture('AUDJPY',dates,n=1600);cal=calendar({'BOJ':['2024-02-05'],'AUD_CPI':['2025-02-03']})
        for mode in ('E0','E1','E2'):compare(self,b,candidate('AUDJPY',entry=600,hold=60,mode=mode),dates,cal)
    def test_sl_first_entry_exit_inclusive_raw_boundary(self):
        date=pd.Timestamp('2024-02-05');p=candidate(entry=60,hold=60,tp=20);pip=PIPS['USDJPY'];price=100+SPREAD['USDJPY']*pip;sl=price-20*pip;tp=price+20*pip
        for minute in (60,120):
            for low in (sl,np.nextafter(sl,np.inf)):
                b=pd.DataFrame(dict(Open=100.,High=100.,Low=100.,Close=100.),index=pd.date_range(date,periods=130,freq='min'));b.loc[date+pd.Timedelta(minutes=minute),['Low','High']]=[low,tp]
                r=compare(self,b,p,[date]);self.assertEqual(r.rows[0][0]['ExitReason'],'SL' if low==sl else 'TP')
    def test_fallback_zero_through_four_plus_five_missing_entry_exit_gap(self):
        date=pd.Timestamp('2024-02-05');p=candidate(entry=60,hold=60);base=fixture('USDJPY',[date],n=140)
        for delay in range(6):
            b=base.drop(pd.date_range(date+pd.Timedelta(minutes=120),periods=delay,freq='min'));r=compare(self,b,p,[date]);self.assertEqual(r.status[0]==0,delay<=4)
            if delay<=4:self.assertEqual(r.rows[0][0]['ExitDelayMinutes'],delay)
        for minutes in ([60],list(range(120,125)),[90,91]):compare(self,base.drop([date+pd.Timedelta(minutes=i) for i in minutes]),p,[date])
    def test_exit_required_before_early_sl(self):
        date=pd.Timestamp('2024-02-05');p=candidate(entry=60,hold=60);b=fixture('USDJPY',[date],n=120);b.loc[date+pd.Timedelta(minutes=60),'Low']=1
        r=compare(self,b,p,[date]);self.assertEqual(r.rows[0][0]['Status'],'MISSING_EXIT')
    def test_year_end_stop_and_future_date_rejection(self):
        for d in ('2024-01-01','2024-12-30','2025-12-29'):
            b=fixture('USDJPY',[pd.Timestamp(d)],n=1400);r=compare(self,b,candidate(),[d]);self.assertEqual(r.rows[0][0]['Status'],'FILTERED_YEAR_END')
        with self.assertRaises(ValueError):replay_candidate(candidate(),['2026-02-02'],calendar(),bars=fixture('USDJPY',[pd.Timestamp('2024-02-05')]))
    def test_fomc_next_day_planned_exit_early_sl_fallback(self):
        d=pd.Timestamp('2024-02-05');b=fixture('USDJPY',[d],n=1600);p=candidate(entry=1380,hold=180,mode='E1');cal=calendar({'FOMC':['2024-02-05']})
        r=compare(self,b,p,[d],cal);self.assertEqual(r.rows[0][0]['Status'],'FILTERED_EVENT')
        p=candidate(entry=480,hold=59,mode='E1');b=fixture('USDJPY',[d],n=600).drop(pd.date_range(d+pd.Timedelta(minutes=539),periods=4,freq='min'));r=compare(self,b,p,[d],calendar({'BOJ':['2024-02-05']}));self.assertEqual(r.status[0],0)
    def test_event_window_edges(self):
        m=modules()['stage4_events'];cal=calendar({'BOJ':['2024-02-05']})
        for e,h,hit in ((480,60,True),(900,30,True),(480,59,False),(901,30,False)):
            self.assertEqual(bool(m.matches(candidate(entry=e,hold=h),['2024-02-05'],'E1',cal)[0]),hit)


def trades(values,year):
    return [dict(CandidateID='synthetic',EntryTime=f'{year}-02-{i+1:02d} 10:00:00',CloseTime=f'{year}-02-{i+1:02d} 11:00:00',RawR=r) for i,r in enumerate(values)]

class MetricTests(unittest.TestCase):
    def test_combined_trade_weighted_not_annual_average(self):
        a=trades([4.],2024);b=trades([-1.,0.,0.],2025);m=aggregate(a+b);self.assertEqual(m['AvgR'],.75);self.assertNotEqual(m['AvgR'],(aggregate(a)['AvgR']+aggregate(b)['AvgR'])/2);self.assertEqual(m['PF'],4.)
    def test_combined_dd_continues_across_years_and_sorts(self):
        a=trades([5.,-4.],2024);b=trades([-4.,2.],2025);m=aggregate(list(reversed(a+b)));self.assertEqual(m['MaxDDR'],8.);self.assertGreater(m['MaxDDR'],max(aggregate(a)['MaxDDR'],aggregate(b)['MaxDDR']))
    def test_zero_inf_undefined(self):
        m=aggregate(trades([1.,0.],2024));self.assertEqual((m['Trades'],m['Wins'],m['Losses'],m['ZeroR'],m['PF']),(2,1,0,1,'INF'));self.assertEqual(aggregate(trades([0.],2024))['PF'],'UNDEFINED');self.assertEqual(aggregate([])['AvgR'],'UNDEFINED')
    def test_raw_r_not_display(self):self.assertEqual(aggregate(trades([.02000000000001],2024))['AvgR'],.02000000000001)
    def test_entry_year_not_close_year(self):
        m=modules()['stage2a_engine'];p=candidate();dates=pd.to_datetime(['2024-12-31','2025-02-03']);rows=[dict(Status='OK',EntryTime=str(dates[0]+pd.Timedelta(hours=23)),CloseTime='2025-01-01 00:10:00',ScheduledExitTime='2025-01-01 00:10:00',ExitReason='TimeExit',ExitDelayMinutes=0,missing_path_minutes=0),dict(Status='OK',EntryTime=str(dates[1]+pd.Timedelta(hours=10)),CloseTime='2025-02-03 11:00:00',ScheduledExitTime='2025-02-03 11:00:00',ExitReason='TimeExit',ExitDelayMinutes=0,missing_path_minutes=0)]
        replay=m.Replay(dates,np.array([0,0]),[rows],np.array([[2.,-1.]]));d=evaluate(p,replay,dict(EventMode='E0'));self.assertEqual([r['TotalR'] for r in d['periods']],[2.,-1.,1.])
    def test_future_trade_close_rejected(self):
        m=modules()['stage2a_engine'];row=dict(Status='OK',EntryTime='2025-12-31 23:00:00',CloseTime='2026-01-01 00:00:00',ScheduledExitTime='2026-01-01 00:00:00')
        with self.assertRaises(ValueError):evaluate(candidate(),m.Replay(pd.to_datetime(['2025-12-31']),np.array([0]),[[row]],np.array([[1.]])),{})

class RunnerTests(unittest.TestCase):
    def test_both_flags_and_colab_before_any_io(self):
        with patch('b6.stage6_search.load_input',side_effect=AssertionError('input')):
            for run,confirmed in ((False,False),(False,True),(True,False)):
                with self.assertRaises(PermissionError):full_validation('data','out','a'*40,run,confirmed)
            with patch('b6.stage6_search.importlib.util.find_spec',return_value=None):
                with self.assertRaises(PermissionError):full_validation('data','out','a'*40,True,True)
    def test_resume_identity_all_fields(self):
        identity=dict(code_sha='a',config_sha='b',stage5_commit='c',candidate_sha='d',contract_sha='e',candidate_count=50,inputs=[{'hash':'f'}],calendar='g',runtime=dict(Python='p',Numpy='n',Pandas='v'))
        with tempfile.TemporaryDirectory() as out:
            open_store(out,identity)
            for key in identity:
                with self.assertRaises(ValueError):open_store(out,{**identity,key:'changed'})
    def test_incomplete_completion_rejected_before_results(self):
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(ValueError):finish(out,{},[candidate()],{**load_config(),'candidate_count':1})
            self.assertEqual(list(Path(out).iterdir()),[])
    def test_synthetic_finish_preserves_all_statuses_and_no_ranking(self):
        p=candidate();d=pd.to_datetime(['2024-02-05','2025-02-03']);r,diag=replay_candidate(p,d,calendar(),bars=fixture('USDJPY',d,n=1400));job=evaluate(p,r,diag)
        with tempfile.TemporaryDirectory() as out:
            ledger=open_store(out,dict(test=True,inputs=[]));save_job(out,ledger,p['CandidateID'],job)
            for n in ('effective_config.json','stage5_input_audit.json','m1_input_audit.json','search_space.json'):atomic_json(Path(out)/n,{})
            s=finish(out,ledger,[p],{**load_config(),'candidate_count':1});self.assertEqual(s['State'],'COMPLETE_STAGE6_VALIDATION_ONLY');self.assertEqual(s['CandidateCount'],1);self.assertEqual(s['PeriodRows'],3);self.assertEqual(s['INSUFFICIENT_SAMPLE'],1);self.assertFalse(s['MonitorExecuted']);self.assertTrue(s['NoRanking'])
    def test_no_stage7_api(self):
        import b6.stage6_search as module
        for name in ('monitor','stage7','portfolio'):self.assertFalse(any(name in k for k in vars(module) if callable(getattr(module,k))))

class ContractTests(unittest.TestCase):
    def rows(self):return [dict(Trades=30,Losses=5,TotalR=1.,PF=.1,AvgR=-1),dict(Trades=40,Losses=5,TotalR=1.,PF=.1,AvgR=-1),dict(Trades=70,PF=1.1,AvgR=.02,MaxDDR=10.)]
    def test_exact_thresholds_pass(self):self.assertEqual(assess(*self.rows(),5.)['ValidationStatus'],'PASS')
    def test_2025_thirty_sample_sufficient(self):
        rows=self.rows();rows[1]['Trades']=30;self.assertTrue(assess(*rows,5.)['SampleSufficient'])
    def test_all_sample_reasons_and_no_formal_fail(self):
        rows=self.rows()
        for r in rows:r['Trades']=0
        rows[0]['Losses']=rows[1]['Losses']=0;rows[0].pop('TotalR');r=assess(*rows,5.)
        self.assertEqual(r['ValidationStatus'],'INSUFFICIENT_SAMPLE');self.assertEqual(r['SampleFailReasons'],['2024_TRADES','2024_LOSSES','2025_TRADES','2025_LOSSES','COMBINED_TRADES']);self.assertEqual(r['ValidationFailReasons'],[])
    def test_dd_raw_stage5_limit_and_no_additional_gates(self):
        r=self.rows();r[2]['MaxDDR']=12.123456789123*1.5;r[0].update(WinRate=0,Monthly=-99,Quarter=-99);r[1].update(WinRate=0,Monthly=-99,Quarter=-99)
        self.assertEqual(assess(*r,12.123456789123)['ValidationStatus'],'PASS')
for name,i,k,value,expected in [('2024_trades29',0,'Trades',29,'INSUFFICIENT_SAMPLE'),('2024_losses4',0,'Losses',4,'INSUFFICIENT_SAMPLE'),('2025_trades29',1,'Trades',29,'INSUFFICIENT_SAMPLE'),('2025_losses4',1,'Losses',4,'INSUFFICIENT_SAMPLE'),('combined69',2,'Trades',69,'INSUFFICIENT_SAMPLE'),('2024_total_zero',0,'TotalR',0,'FAIL'),('2025_total_zero',1,'TotalR',0,'FAIL'),('pf_below',2,'PF',np.nextafter(1.1,0),'FAIL'),('avg_below',2,'AvgR',np.nextafter(.02,0),'FAIL'),('tiny_dd_excess',2,'MaxDDR',np.nextafter(10.,11.),'FAIL')]:
    def check(self,i=i,k=k,value=value,expected=expected):
        rows=self.rows();rows[i][k]=value;self.assertEqual(assess(*rows,5.)['ValidationStatus'],expected)
    setattr(ContractTests,'test_'+name,check)
