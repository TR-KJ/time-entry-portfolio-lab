import unittest,sys,json
from pathlib import Path
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
from b6.execution import execute,discovery_view,SPREAD,PIPS
from b6.stage0 import reference,round5

def fixture(start='2020-02-04 09:00',n=35,symbol='USDJPY'):
    base=100.0 if symbol.endswith('JPY') else 1.0
    return pd.DataFrame([[base]*4]*n,columns=['Open','High','Low','Close'],index=pd.date_range(start,periods=n,freq='min'))

def run(b,symbol='USDJPY',long=True,sl=20,tp=None,entry=None,scheduled=None):
    e=b.index[0] if entry is None else pd.Timestamp(entry)
    return execute(b,symbol,long,e,e+pd.Timedelta(minutes=30) if scheduled is None else scheduled,sl,tp)

class B6Tests(unittest.TestCase):
    def test_direction_pip_spread_and_reference(self):
        ref=reference();ref.EVENT_POLICY[999]={k:'-' for k in ref.EVENTS}
        for symbol in PIPS:
            for long in (True,False):
                for tp in (None,30):
                    b=fixture(symbol=symbol);r=run(b,symbol,long,tp=tp)
                    self.assertAlmostEqual(r['Pips'],-SPREAD[symbol])
                    e=b.index[0];x=e+pd.Timedelta(minutes=30)
                    s=ref.Strategy(999,'test',ref.SYMBOL_TO_PAIR[symbol],long,(1,),(9,0),(9,30),0,20,tp)
                    old=ref.run_strategy(s,b,{k:set() for k in ref.EVENTS},[])[0]
                    for k in ('EntryPrice','ClosePrice','Pips','R','ExitReason'):self.assertEqual(r[k],old[k])
    def test_entry_exact_hits_and_same_bar(self):
        for symbol in ('USDJPY','AUDUSD'):
            for long in (True,False):
                for mode in ('SL','TP','BOTH'):
                    b=fixture(symbol=symbol);pip=PIPS[symbol];sign=1 if long else -1
                    e=b.Open.iloc[0]+sign*SPREAD[symbol]*pip;sl=e-sign*20*pip;tp=e+sign*30*pip
                    extremes=[b.Open.iloc[0]]+([sl] if mode=='SL' else [tp] if mode=='TP' else [sl,tp])
                    b.iloc[0,b.columns.get_loc('High')]=max(extremes);b.iloc[0,b.columns.get_loc('Low')]=min(extremes)
                    r=run(b,symbol,long,tp=30)
                    self.assertEqual(r['ExitReason'],'TP' if mode=='TP' else 'SL')
                    self.assertEqual(r['CloseTime'],str(b.index[0]))
    def test_exit_bar_first_hit(self):
        for long in (True,False):
            for reason in ('SL','TP'):
                b=fixture();sign=1 if long else -1;entry=100+sign*.005
                target=entry+sign*(-.2 if reason=='SL' else .3)
                b.loc[b.index[30],'High']=max(100,target);b.loc[b.index[30],'Low']=min(100,target)
                r=run(b,long=long,tp=30);self.assertEqual(r['ExitReason'],reason);self.assertTrue(r['exit_bar_first_hit'])
    def test_time_exit_open_not_close(self):
        b=fixture();b.loc[b.index[30],['High','Close']]=100.1
        self.assertEqual(run(b)['Pips'],-.5)
    def test_fallback_all_delays(self):
        for delay in range(5):
            b=fixture();b=b.drop(b.index[30:30+delay]);r=run(b)
            self.assertEqual(r['ExitDelayMinutes'],delay)
        b=fixture(n=36);b=b.drop(b.index[30:35]);self.assertEqual(run(b)['Status'],'MISSING_EXIT')
    def test_missing_exit_not_rescued_by_early_sl(self):
        b=fixture(n=30);b.iloc[0,b.columns.get_loc('Low')]=99
        self.assertEqual(run(b)['Status'],'MISSING_EXIT')
    def test_missing_entry_and_internal_gap(self):
        b=fixture();e=b.index[0];self.assertEqual(run(b.iloc[1:],entry=e)['Status'],'MISSING_ENTRY')
        b=b.drop(b.index[10]);r=run(b);self.assertEqual(r['missing_path_minutes'],1);self.assertEqual(r['ExitReason'],'TimeExit')
    def test_overnight_and_holding_limits(self):
        b=fixture(start='2020-02-04 23:45');self.assertEqual(run(b)['CloseTime'],'2020-02-05 00:15:00')
        for mins in (29,1441):self.assertEqual(run(b,scheduled=b.index[0]+pd.Timedelta(minutes=mins))['Status'],'INVALID_HOLD')
    def test_boundary_even_if_sl_before_exit(self):
        b=fixture(start='2023-12-29 23:45');b.iloc[0,b.columns.get_loc('Low')]=99
        self.assertEqual(run(b,scheduled='2024-01-01')['Status'],'PERIOD_BOUNDARY')
        b=fixture(start='2023-12-31 23:20',n=45)
        isolated=discovery_view(b);self.assertLess(isolated.index.max(),pd.Timestamp('2024-01-01'))
        with self.assertRaises(ValueError):run(b)
        isolated.iloc[0,0]=123;self.assertNotEqual(b.iloc[0,0],123)
    def test_fallback_boundary_guard(self):
        # Boundary dates fall on Sunday in 2023: use patched window only for synthetic coverage.
        import b6.execution as ex
        old=ex.END
        try:
            ex.END=pd.Timestamp('2020-02-04 09:33');b=fixture(n=33).drop(pd.date_range('2020-02-04 09:30',periods=3,freq='min'))
            self.assertEqual(run(b)['Status'],'PERIOD_BOUNDARY')
        finally:ex.END=old
    def test_duplicates_unsorted_ohlc_timezone(self):
        b=fixture()
        for invalid in (pd.concat([b,b.iloc[:1]]),b.iloc[::-1],b.tz_localize('Asia/Tokyo')):
            with self.assertRaises(ValueError):run(invalid)
        b.iloc[0,1]=99
        with self.assertRaises(ValueError):run(b)
    def test_no_epsilon(self):
        b=fixture();stop=100+.005-.2;b.iloc[0,2]=np.nextafter(stop,np.inf)
        self.assertEqual(run(b)['ExitReason'],'TimeExit')
        b.iloc[0,2]=stop;self.assertEqual(run(b)['ExitReason'],'SL')
    def test_reproducible(self):
        b=fixture();self.assertEqual(json.dumps(run(b),sort_keys=True),json.dumps(run(b),sort_keys=True))
    def test_loader_timezone_and_duplicate_rejection(self):
        import tempfile
        ref=reference()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.csv'
            header='<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n'
            p.write_text(header+'2020.02.04\t03:00:00\t100\t100\t100\t100\n2020.07.07\t03:00:00\t100\t100\t100\t100\n')
            b=ref.load_pair([p],'USDJPY')
            self.assertEqual(list(b.index),[pd.Timestamp('2020-02-04 10:00'),pd.Timestamp('2020-07-07 09:00')])
            with self.assertRaises(ValueError):ref.load_pair([p,p],'USDJPY')
    def test_no_weekend_reconnection(self):
        b=fixture(start='2020-02-07 23:45',n=15)
        monday=fixture(start='2020-02-10 00:00',n=35)
        self.assertEqual(run(pd.concat([b,monday]))['Status'],'MISSING_EXIT')
        self.assertEqual(run(pd.concat([b,monday]),scheduled=monday.index[0])['Status'],'INVALID_HOLD')
    def test_rounding_and_search_locked(self):
        self.assertEqual(round5(12.5),15);self.assertEqual(round5(12.49),10)
        root=Path(__file__).resolve().parents[1];c=json.loads((root/'research_inputs/b6/proposal.json').read_text())
        self.assertFalse(c['stage1_enabled']);self.assertFalse(c['validation_enabled'])
        self.assertEqual(7*2*5*len(range(0,1440,5))*len(range(30,1441,5)),5705280)

if __name__=='__main__':unittest.main(verbosity=2)
