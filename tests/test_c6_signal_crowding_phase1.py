import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from c6_signal_crowding_phase1 import timeline,adjusted,bootstrap,design,strategy_rows,FEATURES


def sample(n=240):
    rng=np.random.default_rng(20)
    a=pd.DataFrame(dict(StrategyNo=np.arange(n)%3+1,R2Category=np.array(['Q1','Q2','R2_UNAVAILABLE'])[rng.integers(3,size=n)],
        SIGNAL_COUNT_6H=rng.integers(5,size=n),EntryTime=pd.date_range('2025-01-01',periods=n,freq='D'),Strategy='synthetic'))
    a['Week']=a.EntryTime.dt.to_period('W-SUN').dt.start_time.astype(str)
    a['R']=a.StrategyNo*.3+a.R2Category.map({'Q1':.1,'Q2':-.2,'R2_UNAVAILABLE':.5})+2.5*a.SIGNAL_COUNT_6H
    return a


class C6Tests(unittest.TestCase):
    def test_boundaries_self_and_simultaneous(self):
        a=pd.DataFrame(dict(StrategyNo=[1,2,3,4,5,6],EntryTime=pd.to_datetime([
            '2025-01-01 00:00','2025-01-01 06:00','2025-01-01 06:00','2025-01-01 06:01','2025-01-01 12:00','2025-01-01 12:01'])))
        r=timeline(a)
        self.assertEqual(r.SIGNAL_COUNT_6H.tolist(),[0,2,2,2,3,2])
        self.assertEqual(r.SIGNAL_COUNT_12H.tolist(),[0,2,2,3,4,4])
        self.assertEqual(r.SAME_TIMESTAMP_OTHER_SIGNALS.tolist(),[0,1,1,0,0,0])
        pd.testing.assert_frame_equal(r,timeline(a.sample(frac=1,random_state=1)))

    def test_exclude22_duplicates_and_cross_midnight(self):
        a=pd.DataFrame(dict(StrategyNo=[1,22,2,3],EntryTime=pd.to_datetime(['2025-01-03 23:00','2025-01-03 23:30','2025-01-04 01:00','2025-01-06 00:00'])))
        r=timeline(a);self.assertEqual(r.SIGNAL_COUNT_6H.tolist(),[0,1,0])
        self.assertEqual(r.SIGNAL_COUNT_12H.tolist(),[0,1,0])
        with self.assertRaises(ValueError):timeline(pd.concat([a,a.iloc[[0]]]))

    def test_additive_fe_and_unavailable(self):
        a=sample();self.assertAlmostEqual(adjusted(a,FEATURES[0]),2.5,places=9)
        direct=np.linalg.lstsq(np.column_stack([design(a),a.SIGNAL_COUNT_6H]),a.R,rcond=None)[0][-1]
        self.assertAlmostEqual(adjusted(a,FEATURES[0]),direct,places=9)
        self.assertEqual(len(a[a.R2Category=='R2_UNAVAILABLE'])>0,True)

    def test_unidentifiable_and_equal_eligibility(self):
        a=sample();a['SIGNAL_COUNT_6H']=a.StrategyNo
        self.assertTrue(np.isnan(adjusted(a,FEATURES[0])))
        a=sample();rows=strategy_rows(a,FEATURES[0],'ALL')
        self.assertTrue(all(r['Eligible'] for r in rows))
        rows=strategy_rows(a.iloc[:10],FEATURES[0],'ALL')
        self.assertFalse(any(r['Eligible'] for r in rows))

    def test_bootstrap_refits_weighted_rows(self):
        a=sample(100);a['R']+=np.sin(np.arange(len(a)))
        bs,lo,hi,n=bootstrap(a,FEATURES[0],reps=80)
        weeks=sorted(a.Week.unique());rng=np.random.Generator(np.random.PCG64(20260913))
        expected=[]
        for _ in range(80):
            draw=rng.integers(len(weeks),size=len(weeks))
            b=pd.concat([a[a.Week==weeks[i]] for i in draw])
            x=np.column_stack([design(b),b.SIGNAL_COUNT_6H])
            expected.append(np.linalg.lstsq(x,b.R,rcond=None)[0][-1])
        np.testing.assert_allclose(bs,expected,atol=1e-9,rtol=0)
        np.testing.assert_allclose([lo,hi],np.quantile(expected,[.025,.975]),atol=1e-9,rtol=0)


if __name__=='__main__':unittest.main()
