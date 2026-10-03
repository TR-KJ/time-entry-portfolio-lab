"""Synthetic-only Stage8 checks; never replay real 2026 candidate prices."""
import ast,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage1 import fixture
from test_b6_stage6 import candidate as base_candidate,calendar,trades
from b6.stage8_config import load_config
from b6.stage8_adapter import modules,adapted_tree
from b6.stage8_data import canonical_slice,validate_prices,availability,START,END
from b6.stage8_engine import make_engine,replay_candidate
from b6.stage8_metrics import aggregate,evaluate
from b6.stage8_search import full_analysis,finish
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
    test.assertEqual(evaluate(p,f,fd),evaluate(p,r,rd));return f

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
    def test_discovery_validation_monitor_full_boundaries(self):
        from b6.stage8_metrics import period_for,period_records
        from b6.stage8_data import PERIODS
        cases=[('2020-01-01','Discovery'),('2023-12-31 23:59','Discovery'),('2024-01-01','Validation'),('2025-12-31 23:59','Validation'),('2026-01-01','Monitor'),('2026-09-09 23:59','Monitor')]
        for date,label in cases:self.assertEqual(period_for(date),label)
        for date in ('2019-12-31 23:59','2026-09-10'):
            with self.assertRaises(ValueError):period_for(date)
        records=[dict(PlannedEntry=d) for d,label in cases]
        self.assertEqual([len(period_records(records,label)) for label in PERIODS],[2,2,2,6])
    def test_canonical_jst_slice_and_no_fill(self):
        raw=pd.to_datetime(['2019-12-31 16:59','2019-12-31 17:00','2026-09-08 23:58','2026-09-09 00:00','2026-09-09 18:00'])
        b=canonical_slice([pd.DataFrame(dict(RawDatetime=raw,Open=1.,High=1.,Low=1.,Close=1.))])
        self.assertEqual(list(b.index),list(pd.to_datetime(['2020-01-01','2026-09-09 05:58','2026-09-09 06:00'],format='mixed')))
        self.assertEqual(len(b),3);self.assertNotIn(pd.Timestamp('2026-09-09 05:59'),b.index)
    def test_outside_executor_2019_or_sep10_rejected(self):
        for date in ('2019-12-31','2026-09-10'):
            with self.assertRaises(ValueError):make_engine(fixture('USDJPY',[pd.Timestamp(date)],n=1),'USDJPY')
    def test_period_private_globals_and_source_sha(self):
        from b6 import execution,stage1_engine
        from b6.stage7_adapter import modules as previous
        before=(execution.START,execution.END,stage1_engine.MINUTES,previous()['execution'].START,previous()['execution'].END)
        m=modules();self.assertEqual((m['execution'].START,m['execution'].END),(START,END));self.assertEqual(before,(execution.START,execution.END,stage1_engine.MINUTES,previous()['execution'].START,previous()['execution'].END))
        modules.cache_clear()
        with patch('b6.stage8_adapter.sha',return_value='0'*64):
            with self.assertRaises(ValueError):modules()
        modules.cache_clear()
    def test_three_period_replay_weekday_epoch(self):
        dates=pd.to_datetime(['2020-02-03','2024-02-05','2026-02-02']);b=fixture('USDJPY',dates,n=1400)
        replay=compare(self,b,candidate(),dates);job=evaluate(candidate(),replay,{})
        self.assertEqual([r['Period'] for r in job['ledger']],['Discovery','Validation','Monitor']);self.assertEqual([r['WeekKey'] for r in job['ledger']],['2020-02-03','2024-02-05','2026-02-02'])
    def test_no_trade_availability_and_raw_ledger(self):
        dates=pd.to_datetime(['2026-02-02','2026-02-09']);b=fixture('USDJPY',[dates[0]],n=1400);p=candidate();r,diag=replay_candidate(p,dates,calendar(),bars=b);job=evaluate(p,r,diag)
        self.assertEqual(len(job['ledger']),1);self.assertEqual([r['Status'] for r in job['diagnostics']],['TRADE','NO_TRADE']);self.assertEqual(job['diagnostics'][1]['Reason'],'MISSING_ENTRY');self.assertEqual(job['ledger'][0]['R'],float(r.raw_r[0,0]))
    def test_end_missing_exit_not_extrapolated(self):
        d=pd.Timestamp('2026-09-09');p=candidate(entry=350,hold=30,weekday=2);b=fixture('USDJPY',[d],n=361);r=compare(self,b,p,[d]);job=evaluate(p,r,{})
        self.assertEqual(job['ledger'],[]);self.assertEqual(job['diagnostics'][0]['Reason'],'MISSING_EXIT')
