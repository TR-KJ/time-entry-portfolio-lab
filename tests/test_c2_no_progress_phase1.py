import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'/'research'))
from c1_path_management_phase1 import replay, bootstrap_deltas
from c2_no_progress_phase1 import no_progress, recovery, safety, decide, paired_summary
from exit_efficiency_phase1 import checkpoint


def fixture(long=True, duration=8, tp='', start='2026-01-05 09:00', pair='UJ', sl=100):
    e = datetime.fromisoformat(start)
    a = dict(_n=1, Strategy='synthetic', Pair=pair, Direction='Long' if long else 'Short',
             Mode='STANDARD', EntryTime=str(e), ScheduledExitTime=str(e+timedelta(minutes=duration)),
             _entry=e, _scheduled=e+timedelta(minutes=duration), _week='2026-01-05', SL=str(sl), TP=tp)
    d = pd.DataFrame([(100.,100.1,99.9,100.)]*(duration+1), columns=['Open','High','Low','Close'],
                     index=pd.date_range(e,periods=duration+1,freq='min'))
    return a,d


def run(a,d,v='NP50'):
    b = replay(a,d,'R0')
    return b,no_progress(a,d,b,v)


class C2Tests(unittest.TestCase):
    def test_duration_rounding_and_overnight(self):
        e=datetime(2026,1,5,23,58); s=e+timedelta(minutes=11)
        self.assertEqual(checkpoint(e,s,.5),datetime(2026,1,6,0,3))
        self.assertEqual(checkpoint(e,s,.75),datetime(2026,1,6,0,6))
        for bad in (e,e-timedelta(minutes=1),e+timedelta(seconds=90)):
            with self.assertRaises(ValueError): checkpoint(e,bad,.5)
        a,d=fixture(duration=11,start=str(e))
        self.assertEqual(run(a,d)[1]['CloseTime'],'2026-01-06 00:03:00')
        self.assertEqual(run(a,d,'NP75')[1]['CloseTime'],'2026-01-06 00:06:00')

    def test_duration_ignores_actual_exit(self):
        a,d=fixture(); d.iloc[1,d.columns.get_loc('Low')]=98
        b,n=run(a,d)
        self.assertEqual(n['CheckpointTime'],'2026-01-05 09:04:00')
        self.assertEqual(n['Assessment'],'CLOSED_BEFORE_CHECKPOINT')
        self.assertEqual(n['R'],b['R'])

    def test_open_and_completed_only(self):
        a,d=fixture(tp='100')
        d.iloc[4]=[100.02,102,98,100]
        b,n=run(a,d)
        self.assertEqual(b['ExitReason'],'SL')
        self.assertEqual(n['ExitReason'],'NP50')
        self.assertAlmostEqual(n['R'],.015)
        self.assertAlmostEqual(n['CheckpointMFE_R'],.095)
        self.assertEqual(n['ClosePrice'],100.02)

    def test_exact_boundary_both_directions_and_below(self):
        for long in (True,False):
            a,d=fixture(long=long)
            level=100.005+.25 if long else 99.995-.25
            col='High' if long else 'Low'
            d.loc[d.index[2],col]=level
            b,n=run(a,d)
            self.assertFalse(n['Triggered'])
            self.assertEqual(n['Assessment'],'PROGRESS_REACHED')
            self.assertAlmostEqual(n['CheckpointMFE_R'],.25)
            d.loc[d.index[2],col]=np.nextafter(level, -np.inf if long else np.inf)
            self.assertTrue(run(a,d)[1]['Triggered'])

    def test_giveback_uses_mfe_not_current_r(self):
        a,d=fixture(); d.loc[d.index[1],'High']=100.505
        d.loc[d.index[4],'Open']=99.7
        self.assertFalse(run(a,d)[1]['Triggered'])

    def test_short_nonjpy_spread_and_mfe(self):
        a,d=fixture(long=False,pair='AU',sl=10000)
        b,n=run(a,d)
        self.assertAlmostEqual(b['EntryPrice'],99.99985)
        self.assertAlmostEqual(n['R'],-.00015)
        self.assertAlmostEqual(n['CheckpointMFE_R'],.09985)

    def test_sl_and_tp_before_checkpoint(self):
        for reason in ('SL','TP'):
            a,d=fixture(tp='100')
            d.loc[d.index[1], 'Low' if reason=='SL' else 'High']=98 if reason=='SL' else 102
            b,n=run(a,d)
            self.assertEqual(n['ExitReason'],reason)
            self.assertFalse(n['Assessed'])
            self.assertEqual(n['CloseTime'],b['CloseTime'])

    def test_same_bar_sl_first(self):
        a,d=fixture(tp='100'); d.iloc[1]=[100,102,98,100]
        self.assertEqual(run(a,d)[1]['ExitReason'],'SL')

    def test_four_min_fallback_and_missing(self):
        a,d=fixture(duration=20)
        d=d.drop(d.index[10:14]); b,n=run(a,d)
        self.assertEqual(n['CheckpointDelay'],4)
        self.assertEqual(n['CloseTime'],'2026-01-05 09:14:00')
        d=d.drop(pd.Timestamp('2026-01-05 09:14'))
        self.assertEqual(run(a,d)[1]['Status'],'MISSING_CHECKPOINT_BAR')

    def test_later_bars_cannot_change_checkpoint_mfe(self):
        a,d=fixture(); n=run(a,d)[1]
        d.loc[d.index[4:],'High']=103
        self.assertEqual(run(a,d)[1]['CheckpointMFE_R'],n['CheckpointMFE_R'])
        self.assertEqual(run(a,d)[1]['R'],n['R'])

    def test_recovery_categories(self):
        for r,reason in ((-.2,'TimeExit'),(.2,'TimeExit'),(0,'TimeExit'),(-1,'SL'),(1,'TP')):
            c=recovery(dict(R=r,ExitReason=reason))
            self.assertEqual(c['RECOVERED_POSITIVE'],r>0)
            self.assertEqual(c['NEVER_RECOVERED'],r<=0)
            self.assertEqual(c['RECOVERED_HALF_R'],r>=.5)
            self.assertEqual(c['LATER_HIT_TP'],reason=='TP')
            self.assertEqual(c['LATER_HIT_SL'],reason=='SL')
            self.assertEqual(c['TIME_EXIT_ZERO'],reason=='TimeExit' and r==0)

    def test_paired_summary_and_bootstrap(self):
        a,d=fixture(); b,n=run(a,d)
        n['R']=b['R']+.125
        pairs=[(a,b,n)]
        row=paired_summary(pairs)
        self.assertAlmostEqual(row['DeltaTotalR'],.125)
        self.assertAlmostEqual(row['CILower'],.125)
        self.assertEqual(row['Improved'],1)
        self.assertEqual(row['Harmed'],0)
        p=[]
        for w,ds in [('2026-01-05',[.2,-.1]),('2026-01-12',[-.3]),('2026-01-19',[.7,.4,.1])]:
            for delta in ds: p.append((dict(_week=w),dict(R=0),dict(R=delta)))
        lo,hi,_=bootstrap_deltas(p)
        rng=np.random.Generator(np.random.PCG64(20260913))
        dist=[]
        clusters=[[.2,-.1],[-.3],[.7,.4,.1]]
        for _ in range(5000):
            sample=[x for i in rng.integers(0,3,3) for x in clusters[i]]
            dist.append(sum(sample)/len(sample))
        np.testing.assert_allclose([lo,hi],np.quantile(dist,[.025,.975]),atol=1e-12)

    def test_safety_threshold(self):
        row={p+k:v for p in ('R0','NP') for k,v in [('WorstDayR',-10.),('WorstWeekR',-20.),('MaxDDR',30.)]}
        row['NPWorstDayR']=-11
        self.assertTrue(safety(row))
        row['NPWorstDayR']=-11.001
        self.assertFalse(safety(row))


if __name__ == '__main__': unittest.main()
