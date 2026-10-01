"""Stage4 raw gates, planned overlaps, immutable subsets and E0 barrier."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage3 import fixed
from b6.stage3_grid import time_grid
from b6.stage2a_engine import Replay
from b6.stage4_calendar import CLOCKS,artifact,extract,pinned_source,audit_calendar
from b6.stage4_config import load_config
from b6.stage4_events import applicable_events,matches,filter_replay,windows,SYMBOLS
from b6.stage4_selection import adoption,choose,compare
from b6.stage4_metrics import summarize_replay,verify_e0,preflight_all,evaluate_modes,FULL
from b6.stage4_search import run_after_preflight,full_sweep,search_space,finish
from b6.stage2a_search import open_store,save_job,read_job

def point(entry=600,hold=60,symbol='USDJPY',weekday=0):
    p=next(p for p in time_grid(fixed(symbol,entry=(entry//5)*5,hold=((hold+4)//5)*5,weekday=weekday))[0] if p['EntryDeltaMinutes']==p['ExitDeltaMinutes']==0)
    p.update(AdjustedEntryMinute=entry,AdjustedExitMinute=(entry+hold)%1440,AdjustedExitDayOffset=(entry+hold)//1440,PlannedHoldingMinutes=hold)
    p.update(FinalEntryJST=f'{entry//60:02d}:{entry%60:02d}',FinalExitJST=f'{p["AdjustedExitMinute"]//60:02d}:{p["AdjustedExitMinute"]%60:02d}',FinalExitDayOffset=p['AdjustedExitDayOffset'],FinalHoldingMinutes=p['PlannedHoldingMinutes'])
    return p

def calendar(events=None):return dict(Clocks=CLOCKS,Dates={e:(events or {}).get(e,[]) for e in CLOCKS})

def replay(dates=None,raw=None,status=None):
    dates=pd.DatetimeIndex(dates if dates is not None else ['2020-02-03','2021-02-01','2022-02-07','2023-02-06'])
    raw=np.array(raw if raw is not None else [1.,-1.,0.,2.]);status=np.array(status if status is not None else [0]*len(dates))
    rows=[dict(Status='OK',ExitReason='SL' if r<0 else 'TimeExit',ExitDelayMinutes=0,missing_path_minutes=0,exit_bar_first_hit=False,EntryTime=str(d),CloseTime=str(d+pd.Timedelta(minutes=660)),Pips=r*20,R=r,RawR=r) if status[i]==0 else dict(Status='MISSING_ENTRY') for i,(d,r) in enumerate(zip(dates,raw))]
    return Replay(dates,status,[rows],raw[None,:])

def official(p,r):
    d=summarize_replay(p,r);return dict(p,**{k:d['results'][0][k] for k in FULL},YearlyMetrics=d['yearly'])

def passing(mode='E1',**changes):
    return dict(EventMode=mode,RetentionRate=.8,RemovedTrades=20,DeltaTotalR=2.,DeltaAvgR=.01,FilterMaxDDR=4.,E0MaxDDR=4.,**changes) if not changes else {**passing(mode),**changes}

class CalendarTests(unittest.TestCase):
    def test_all_eight_source_lists_and_2026_appends_exact(self):
        data,audit=audit_calendar(load_config());self.assertEqual(data,artifact(pinned_source()));self.assertEqual(len(data['Dates']),8)
        self.assertTrue(all(any(d.startswith('2026') for d in ds) for ds in data['Dates'].values()));self.assertEqual(audit['Status'],'PASS')
    def test_source_no_execution_and_missing_append_rejected(self):
        source=pinned_source();self.assertEqual(extract(source+b'\nraise RuntimeError("must not execute")\n'),extract(source))
        with self.assertRaises(ValueError):extract(b'FOMC_DATES=[]')
        with self.assertRaises(ValueError):extract(source+b'\nFOMC_DATES=compute_dates()\n')
    def test_calendar_hash_tamper(self):
        c=load_config();c['calendar_sha256']='bad'
        with self.assertRaises(ValueError):audit_calendar(c)
    def test_fixed_clocks_offsets(self):
        expected={'FOMC':('03:00',180,1),'US_NFP':('21:30',120,0),'US_CPI':('21:30',120,0),'BOJ':('12:00',180,0),'BOE':('21:00',120,0),'ECB':('21:15',120,0),'RBA':('13:30',120,0),'AUD_CPI':('10:30',120,0)}
        for e,(t,m,o) in expected.items():self.assertEqual(CLOCKS[e],dict(Time=t,Before=m,After=m,DayOffset=o))
    def test_e1_all_pairs(self):
        expected={'USDJPY':['FOMC','BOJ'],'EURJPY':['ECB','BOJ'],'GBPJPY':['BOE','BOJ'],'AUDJPY':['RBA','BOJ'],'AUDUSD':['RBA','FOMC'],'EURAUD':['ECB','RBA'],'GBPAUD':['BOE','RBA']}
        for s,es in expected.items():self.assertEqual(applicable_events(s,'E1'),es);self.assertEqual(applicable_events(s,'E0'),[])
    def test_e2_all_pairs(self):
        for s in SYMBOLS:self.assertEqual(applicable_events(s,'E2'),applicable_events(s,'E1')+['US_NFP','US_CPI']+(['AUD_CPI'] if 'AUD' in s else []))
    def test_no_strategy_matrix_dependency(self):
        source=(ROOT/'src/research/b6/stage4_events.py').read_text()
        for forbidden in ('EVENT_POLICY','MATRIX_ROWS','portfolio_backtest','Candidate C'):self.assertNotIn(forbidden,source)
    def test_unknown_pair_mode_rejected(self):
        for s,m in [('EURUSD','E1'),('USDJPY','E3')]:
            with self.assertRaises(ValueError):applicable_events(s,m)

class OverlapTests(unittest.TestCase):
    def test_fomc_next_jst_day_overnight(self):
        p=point(1380,180,weekday=0);c=calendar({'FOMC':['2020-02-03']})
        self.assertEqual(matches(p,['2020-02-03'],'E1',c),[['FOMC']])
        a,b=windows(c,'FOMC');self.assertEqual(str(a[0]),'2020-02-04 00:00:00');self.assertEqual(str(b[0]),'2020-02-04 06:00:00')
    def test_event_inside_holding(self):
        self.assertEqual(matches(point(480,480),['2020-02-03'],'E1',calendar({'BOJ':['2020-02-03']})),[['BOJ']])
    def test_holding_inside_event(self):
        self.assertEqual(matches(point(600,30),['2020-02-03'],'E1',calendar({'BOJ':['2020-02-03']})),[['BOJ']])
    def test_early_sl_does_not_shorten_interval(self):
        p=point(480,480);r=replay();r.rows[0][0].update(ExitReason='SL',CloseTime='2020-02-03 08:01:00')
        f,d=filter_replay(p,r,'E1',calendar({'BOJ':['2020-02-03']}));self.assertEqual(f.status[0],-1)
    def test_exit_fallback_does_not_extend_interval(self):
        p=point(480,59);r=replay();r.rows[0][0].update(CloseTime='2020-02-03 09:03:00',ExitDelayMinutes=4)
        f,d=filter_replay(p,r,'E1',calendar({'BOJ':['2020-02-03']}));self.assertEqual(f.status[0],0)
    def test_multi_event_or_once(self):
        p=point(480,960);r=replay();c=calendar({'BOJ':['2020-02-03'],'US_CPI':['2020-02-03']});f,d=filter_replay(p,r,'E2',c)
        self.assertEqual(int((f.status==0).sum()),3);self.assertEqual(d['FilteredOpportunities'],1);self.assertEqual(d['MultiEventRemovedTrades'],1);self.assertEqual(sum(d['RemovedTradeCountByEvent'].values()),2)
    def test_actual_trade_denominator_missing_opportunity(self):
        p=point();r=replay(status=[0,3,0,0]);c=calendar({'BOJ':['2020-02-03','2021-02-01']});data=evaluate_modes(p,r,c);row=data['results'][1];diag=data['diagnostics'][1]
        self.assertEqual(row['E0Trades'],3);self.assertEqual(row['FilteredTrades'],2);self.assertEqual(row['RemovedTrades'],1);self.assertEqual(row['RetentionRate'],2/3);self.assertEqual(diag['FilteredOpportunities'],2)
    def test_retained_execution_exact_and_source_unmodified(self):
        p=point();r=replay();before=copy.deepcopy(r);c=calendar({'BOJ':['2020-02-03']})
        for mode in ('E0','E1','E2'):
            f,_=filter_replay(p,r,mode,c)
            for i in np.flatnonzero(f.status==0):self.assertIs(f.rows[0][i],r.rows[0][i]);self.assertEqual(f.rows[0][i],before.rows[0][i]);self.assertEqual(f.raw_r[0,i],r.raw_r[0,i])
        self.assertEqual(r.rows,before.rows);np.testing.assert_array_equal(r.status,before.status)
    def test_future_and_nonmidnight_rejected(self):
        for d in ('2024-02-05','2025-02-03','2026-02-02','2020-02-03 00:01'):
            with self.assertRaises(ValueError):matches(point(),[d],'E0',calendar())
    def test_identical_trade_sets_keep_three_variants(self):
        data=evaluate_modes(point(),replay(),calendar());self.assertEqual([r['EventMode'] for r in data['results']],['E0','E1','E2']);self.assertEqual(data['selected']['SelectedEventMode'],'E0');self.assertEqual(len(data['yearly']),12)

for name,entry,hold,expected in [('exact_start',480,60,True),('exact_end',900,30,True),('one_minute_before',480,59,False),('one_minute_after',901,30,False)]:
    def check(self,entry=entry,hold=hold,expected=expected):self.assertEqual(bool(matches(point(entry,hold),['2020-02-03'],'E1',calendar({'BOJ':['2020-02-03']}))[0]),expected)
    setattr(OverlapTests,'test_'+name,check)

class AdoptionTests(unittest.TestCase):
    def test_exact_all_boundaries_pass(self):self.assertTrue(adoption(passing())['AdoptionPass'])
    def test_no_extra_annual_pf_winrate_p02_gate(self):self.assertTrue(adoption(passing(Pass=False,PF=.1,WinRate=0,YearlyDelta=-100,Losses=0))['AdoptionPass'])
    def test_undefined_fails(self):
        for key in ('RetentionRate','RemovedTrades','DeltaTotalR','DeltaAvgR','FilterMaxDDR','E0MaxDDR'):
            for val in ('UNDEFINED',float('nan'),float('inf')):self.assertFalse(adoption(passing(**{key:val}))['AdoptionPass'])
    def test_zero_e0_falls_back(self):
        r=replay(status=[3]*4);data=evaluate_modes(point(),r,calendar());self.assertEqual(data['selected']['SelectedEventMode'],'E0');self.assertEqual(data['selected']['RetentionRate'],'UNDEFINED')
    def test_e1_only(self):self.assertEqual(choose([passing('E0'),passing('E1'),passing('E2',RemovedTrades=19)])[0]['EventMode'],'E1')
    def test_e2_only(self):self.assertEqual(choose([passing('E0'),passing('E1',RemovedTrades=19),passing('E2')])[0]['EventMode'],'E2')
    def test_both_fail_e0(self):self.assertEqual(choose([passing('E0'),passing('E1',RemovedTrades=19),passing('E2',RemovedTrades=19)])[0]['EventMode'],'E0')
    def test_delta_total_precedes_dd(self):self.assertEqual(choose([passing('E0'),passing('E1',FilterMaxDDR=1),passing('E2',DeltaTotalR=3)])[0]['EventMode'],'E2')
    def test_dd_precedes_mode(self):self.assertEqual(choose([passing('E0'),passing('E1'),passing('E2',FilterMaxDDR=3)])[0]['EventMode'],'E2')
    def test_e1_final_tie_ignores_other_metrics(self):self.assertEqual(choose([passing('E0'),passing('E1',PF=.1,DeltaAvgR=.01,WinRate=0),passing('E2',PF=100,DeltaAvgR=2,WinRate=1)])[0]['EventMode'],'E1')
    def test_unrounded_comparison(self):self.assertFalse(adoption(passing(DeltaTotalR=np.nextafter(2.,0)))['AdoptionPass'])

for name,key,val in [('retention_below','RetentionRate',np.nextafter(.8,0)),('removed_19','RemovedTrades',19),('total_below','DeltaTotalR',np.nextafter(2.,0)),('avg_below','DeltaAvgR',np.nextafter(.01,0)),('dd_tiny_worse','FilterMaxDDR',np.nextafter(4.,5.))]:
    def check(self,key=key,val=val):self.assertFalse(adoption(passing(**{key:val}))['AdoptionPass'])
    setattr(AdoptionTests,'test_'+name,check)

class PreflightTests(unittest.TestCase):
    def test_e0_exact_full_yearly(self):
        r=replay();p=official(point(),r);self.assertEqual(verify_e0(p,r)['FullMetrics'],'EXACT_PASS')
    def test_e0_mismatch_even_tiny(self):
        r=replay();p=official(point(),r);p['TotalR']=np.nextafter(p['TotalR'],100)
        with self.assertRaises(ValueError):verify_e0(p,r)
    def test_yearly_mismatch_blocks(self):
        r=replay();p=official(point(),r);p['YearlyMetrics'][0]['TotalR']+=1
        with self.assertRaises(ValueError):verify_e0(p,r)
    def test_global_barrier_no_filter_before_last_candidate_passes(self):
        r=replay();p=official(point(),r);q=copy.deepcopy(p);q['CandidateID']='second';q['TotalR']+=1
        with tempfile.TemporaryDirectory() as out,patch('b6.stage4_search.evaluate_modes',side_effect=AssertionError('filter must not start')):
            with self.assertRaises(ValueError):run_after_preflight(out,{},[p,q],{p['CandidateID']:r,q['CandidateID']:r},calendar())
            self.assertFalse((Path(out)/'e0_equivalence_audit.json').exists())
    def test_resume_still_checks_e0(self):
        r=replay();p=official(point(),r);p['TotalR']+=1
        with tempfile.TemporaryDirectory() as out,patch('b6.stage4_search.read_job',side_effect=AssertionError('checkpoint must not bypass')):
            with self.assertRaises(ValueError):run_after_preflight(out,{p['CandidateID']:'old'},[p],{p['CandidateID']:r},calendar())
    def test_search_space_150(self):self.assertEqual(search_space([point()]*50)['TheoreticalMax'],150)
    def test_work_full_sweep_rejected_before_io(self):
        with patch('b6.stage4_search.load_input',side_effect=AssertionError('IO')):
            with self.assertRaises(PermissionError):full_sweep('m','o','s3','s2','s1','a'*40,False)
            with patch('b6.stage4_search.importlib.util.find_spec',return_value=None):
                with self.assertRaises(PermissionError):full_sweep('m','o','s3','s2','s1','a'*40,True)
    def test_resume_every_identity_component(self):
        identity=dict(code='a',config='b',stage3='c',selected='d',runtime_inputs={'a':'e'},calendar='f',calendar_source='g',candidate='h',inputs=[{'SHA256':'i'}],runtime={'Python':'p','Numpy':'n','Pandas':'v'})
        with tempfile.TemporaryDirectory() as out:
            open_store(out,identity)
            for key in identity:
                with self.assertRaises(ValueError):open_store(out,{**identity,key:'changed'})
    def test_synthetic_completion_and_no_candidate_drop(self):
        r=replay();p=official(point(),r)
        with tempfile.TemporaryDirectory() as out:
            ledger=open_store(out,dict(test=True,inputs=[]));run_after_preflight(out,ledger,[p],{p['CandidateID']:r},calendar())
            from b6.stage1_search import atomic_json
            for n in ('stage3_input_audit.json','event_calendar_audit.json','effective_config.json','event_calendar.json','search_space.json'):atomic_json(Path(out)/n,{})
            result=finish(out,ledger,[p]);self.assertEqual(result['State'],'COMPLETE_STAGE4_ONLY');self.assertEqual(result['CandidateCount'],1);self.assertEqual(result['VariantCount'],3)
            for k in ('CandidateFreezeExecuted','ValidationExecuted','MonitorExecuted','PortfolioExecuted'):self.assertIs(result[k],False)
            self.assertTrue((Path(out)/'stage4_review.zip').is_file())

class ExecutionIntegrationTests(unittest.TestCase):
    def test_adjusted_schedule_stage3_full_and_yearly_metrics(self):
        from test_b6_stage1 import fixture
        from b6.stage2a_engine import FastEngine,fast_replay
        from b6.stage3_metrics import evaluate_point
        from b6.stage3_grid import execution_candidate,fixed_setting
        from b6.stage3_config import load_config as previous_config
        p=point();p.update(AdjustedEntryMinute=601,AdjustedExitMinute=659,PlannedHoldingMinutes=58,FinalEntryJST='10:01',FinalExitJST='10:59',FinalHoldingMinutes=58,EntryDeltaMinutes=1,ExitDeltaMinutes=-1)
        dates=pd.DatetimeIndex(['2020-02-03']);bars=fixture('USDJPY',dates);engine=FastEngine(bars,'USDJPY')
        old=evaluate_point(engine,p,dates,previous_config());p.update({k:old['results'][0][k] for k in FULL},YearlyMetrics=old['yearly'])
        r=fast_replay(engine,execution_candidate(p),dates,[fixed_setting(p)])
        self.assertEqual(verify_e0(p,r)['FullMetrics'],'EXACT_PASS');self.assertEqual(execution_candidate(p)['EntryMinute'],601)
        for mode in ('E1','E2'):
            f,_=filter_replay(p,r,mode,calendar());self.assertEqual(f.rows,r.rows);np.testing.assert_array_equal(f.raw_r,r.raw_r)
