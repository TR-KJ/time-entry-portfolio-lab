import unittest
import numpy as np
import pandas as pd
from b7.stage1 import Engine
from b7.stage1_reference import execute
from b7.execution import discovery_view, validate
from b7.stage1_contract import SYMBOLS, SL, SPREAD, PIPS, Structure, jobs
from b7.stage1_metrics import summarize, gate


def bars(start='2020-02-04 09:00',periods=40,price=100.):
    idx=pd.date_range(start,periods=periods,freq='min')
    return pd.DataFrame(dict(Open=price,High=price+.01,Low=price-.01,Close=price),index=idx)

class ExecutionTests(unittest.TestCase):
    def check_case(self,frame,direction='LONG',entry='2020-02-04 09:00',exit='2020-02-04 09:30',sl=None,status='OK'):
        a=Engine(frame,'USDJPY').execute(direction,entry,exit,sl)
        b=execute(frame,'USDJPY',direction,entry,exit,sl)
        self.assertEqual(a,b);self.assertEqual(a['Status'],status)
        return a
    def test_long_spread_unrounded(self):
        f=bars();f.loc['2020-02-04 09:30','Open']=100.00123456789
        a=self.check_case(f);self.assertEqual(a['Pips'],(100.00123456789-(100.+.5*.01))/.01)
        self.assertNotEqual(a['Pips'],round(a['Pips'],6))
    def test_short_spread(self):self.assertEqual(self.check_case(bars(),'SHORT')['EntryPrice'],100-.005)
    def test_missing_entry(self):self.check_case(bars().iloc[1:],status='MISSING_ENTRY')
    def test_exact_exit(self):self.assertEqual(self.check_case(bars())['ExitDelayMinutes'],0)
    def test_exit_plus1(self):self.assertEqual(self.check_case(bars().drop(pd.Timestamp('2020-02-04 09:30')))['ExitDelayMinutes'],1)
    def test_exit_plus4(self):self.assertEqual(self.check_case(bars().drop(pd.date_range('2020-02-04 09:30',periods=4,freq='min')))['ExitDelayMinutes'],4)
    def test_exit_plus5_rejected(self):self.check_case(bars().drop(pd.date_range('2020-02-04 09:30',periods=5,freq='min')),status='MISSING_EXIT')
    def test_exit_required_before_sl(self):
        f=bars(periods=30);f.iloc[0,f.columns.get_loc('Low')]=99
        self.check_case(f,sl=10,status='MISSING_EXIT')
    def test_overnight(self):self.check_case(bars('2020-02-04 23:45'),entry='2020-02-04 23:45',exit='2020-02-05 00:15')
    def test_friday_saturday_matches_reference(self):self.check_case(bars('2020-02-07 23:45'),entry='2020-02-07 23:45',exit='2020-02-08 00:15')
    def test_no_weekend_bridge(self):self.check_case(bars('2020-02-07 09:00'),entry='2020-02-07 09:00',exit='2020-02-10 09:00',status='INVALID_HOLD')
    def test_period_boundary(self):self.check_case(bars(),entry='2019-12-31 09:00',exit='2019-12-31 09:30',status='PERIOD_BOUNDARY')
    def test_yearend_stop(self):self.check_case(bars('2020-12-25 09:00'),entry='2020-12-25 09:00',exit='2020-12-25 09:30',status='YEAR_END_STOP')
    def test_january_stop(self):self.check_case(bars('2023-01-03 09:00'),entry='2023-01-03 09:00',exit='2023-01-03 09:30',status='YEAR_END_STOP')
    def test_long_sl_entry_inclusive(self):
        f=bars();f.iloc[0,f.columns.get_loc('Low')]=99
        a=self.check_case(f,sl=10);self.assertEqual(a['ExitReason'],'SL');self.assertEqual(a['CloseTime'],'2020-02-04 09:00:00');self.assertEqual(a['Pips'],-10.)
    def test_short_sl(self):
        f=bars();f.iloc[10,f.columns.get_loc('High')]=101
        self.assertEqual(self.check_case(f,'SHORT',sl=10)['ExitReason'],'SL')
    def test_sl_exit_inclusive(self):
        f=bars();f.loc['2020-02-04 09:30','Low']=99
        self.assertEqual(self.check_case(f,sl=10)['ExitReason'],'SL')
    def test_no_sl_hit(self):self.assertEqual(self.check_case(bars(),sl=10)['ExitReason'],'TimeExit')
    def test_raw_no_epsilon(self):
        f=bars();stop=100.+.005-.1
        f.loc['2020-02-04 09:10','Low']=np.nextafter(stop,np.inf)
        self.assertEqual(self.check_case(f,sl=10)['ExitReason'],'TimeExit')
        f.loc['2020-02-04 09:10','Low']=stop
        self.assertEqual(self.check_case(f,sl=10)['ExitReason'],'SL')
    def test_no_gap_interpolation(self):
        f=bars().drop(pd.Timestamp('2020-02-04 09:15'))
        self.assertEqual(self.check_case(f,sl=10)['MissingPathMinutes'],1)
    def test_future_array_rejected(self):
        for start in ['2019-12-01','2024-01-01','2026-01-01']:
            with self.assertRaises(ValueError):Engine(bars(start),'USDJPY')
    def test_owned_discovery_arrays(self):
        full=pd.concat([bars(),bars('2024-01-01')]);v=discovery_view(full);e=Engine(v,'USDJPY')
        full.iloc[0,0]=999;v.iloc[0,0]=888
        self.assertEqual(e.open[0],100);self.assertLess(e.time[-1],pd.Timestamp('2024-01-01').value);self.assertFalse(e.open.flags.writeable)
    def test_duplicate_and_ohlc_rejected(self):
        with self.assertRaises(ValueError):Engine(pd.concat([bars(),bars()]),'USDJPY')
        f=bars();f.iloc[0,1]=99
        with self.assertRaises(ValueError):Engine(f,'USDJPY')
    def test_all_nine_pure_and_five_sl_reference(self):
        rng=np.random.default_rng(7401)
        for symbol in SYMBOLS:
            pip=PIPS[symbol];price=100 if pip==.01 else 1.2
            f=bars(price=price);f['High']=price+rng.random(len(f))*pip*180;f['Low']=price-rng.random(len(f))*pip*180
            engine=Engine(f,symbol)
            for d in ('LONG','SHORT'):
                for sl in [None]+SL[symbol]:
                    a=engine.execute(d,f.index[0],f.index[30],sl)
                    b=execute(f,symbol,d,f.index[0],f.index[30],sl)
                    self.assertEqual(a,b)
                    self.assertEqual(summarize([a]),summarize([b]))
    def test_batch_holding_cache_exact_replay(self):
        f=bars(periods=1500);f.iloc[72,f.columns.get_loc('Low')]=99
        engine=Engine(f,'USDJPY');batch=engine.prepare([f.index[0]],'LONG',SL['USDJPY'])
        for h in [30,65,75,600,1440]:
            out=batch.evaluate(h,trades=True)
            for k,sl in enumerate([None]+SL['USDJPY']):
                self.assertEqual(out['Trades'][k],[execute(f,'USDJPY','LONG',f.index[0],f.index[h],sl)])
    def test_id_roundtrip_search_counts(self):
        js=jobs();self.assertEqual(len(js),90);self.assertEqual(len({j.job_id for j in js}),90)
        self.assertEqual(sum(1 for _ in js[0].structures()),81504)
        self.assertEqual(90*81504,7335360);self.assertEqual(90*81504*6,44012160)
        for s in [Structure('EURUSD','LONG',0,0,30),Structure('GBPUSD','SHORT',4,1435,1440)]:self.assertEqual(Structure.from_id(s.candidate_id),s)
        with self.assertRaises(ValueError):Structure.from_id('B7S1:EURUSD:LONG:MON:E0000:D1:X0030:H0030')

class IntegratedReplayTests(unittest.TestCase):
    def test_four_year_metrics_gates_and_trade_regeneration(self):
        from b7.stage1 import evaluate_structure,regenerate
        for direction in ['LONG','SHORT']:
            sign=1 if direction=='LONG' else -1
            chunks=[];entries=[]
            for year in range(2020,2024):
                days=pd.date_range(f'{year}-02-01',f'{year}-11-30',freq='W-TUE')[:40]
                for n,day in enumerate(days):
                    e=day+pd.Timedelta(hours=9);entries.append(e)
                    f=bars(str(e),periods=31)
                    close=100+sign*(.005+(.02 if n%4 else -.01))
                    f['High']=max(100,close)+.001;f['Low']=min(100,close)-.001
                    f.iloc[-1,f.columns.get_loc('Open')]=close;f.iloc[-1,f.columns.get_loc('Close')]=close
                    chunks.append(f)
            frame=pd.concat(chunks);engine=Engine(frame,'USDJPY');s=Structure('USDJPY',direction,1,540,30)
            record,ledgers=evaluate_structure(engine,s,True)
            self.assertTrue(record['FormalPASS']);self.assertEqual(record['PassingSLCount'],5)
            self.assertEqual(record['PureMetrics']['Trades'],160)
            self.assertEqual(regenerate(engine,s.candidate_id),ledgers)
            for variant,sl in enumerate([None]+SL['USDJPY']):
                reference=[execute(frame,'USDJPY',direction,e,e+pd.Timedelta(minutes=30),sl,s.key) for e in entries]
                self.assertEqual(ledgers[variant],reference)
                actual=record['PureMetrics'] if variant==0 else record['FiveSLMetrics'][variant-1]['Metrics']
                self.assertEqual(actual,summarize(reference));self.assertTrue(gate(actual,sl is not None))
