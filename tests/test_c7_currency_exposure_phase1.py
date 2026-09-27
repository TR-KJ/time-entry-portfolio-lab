"""Synthetic C7 boundary, exposure, identification and bootstrap tests."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import c7_currency_exposure_phase1 as c7


def frame(rows):
    a=pd.DataFrame(rows,columns=['StrategyNo','Symbol','Direction','EntryTime','CloseTime','R2Category'])
    a['EntryTime']=pd.to_datetime(a.EntryTime);a['CloseTime']=pd.to_datetime(a.CloseTime)
    a['TradeID']=[f't{i}' for i in range(len(a))];a['Strategy']=a.StrategyNo.astype(str);a['R']=0.
    return a


class C7Tests(unittest.TestCase):
    def test_vector_and_fallback(self):
        np.testing.assert_array_equal(c7.vector('EURJPY','Long',11),[0,11,0,-11,0])
        np.testing.assert_array_equal(c7.vector('AUDUSD','Short',7),[7,0,0,0,-7])
        self.assertEqual(c7.TICKS['R2_UNAVAILABLE'],9)
        self.assertEqual(list(c7.TICKS.values()),[5,7,9,11,13,9])
        with self.assertRaises(ValueError):c7.vector('BAD','Long',1)
        with self.assertRaises(ValueError):c7.vector('EURJPY','buy',1)

    def test_boundaries_same_symbol_simultaneous_and_22(self):
        a=frame([(1,'GBPJPY','Long','2024-01-01 08:00','2024-01-01 12:00','Q4'),
                 (2,'AUDJPY','Long','2024-01-01 08:00','2024-01-01 10:00','Q2'),
                 (3,'EURJPY','Long','2024-01-01 09:00','2024-01-01 12:00','Q1'),
                 (22,'USDJPY','Long','2024-01-01 09:00','2024-01-01 12:00','Q5'),
                 (4,'EURJPY','Long','2024-01-01 10:00','2024-01-01 11:00','Q5'),
                 (5,'AUDUSD','Long','2024-01-01 10:00','2024-01-01 11:00','R2_UNAVAILABLE')])
        z,b=c7.reconstruct(a);r=z[z.StrategyNo==4].iloc[0]
        self.assertEqual(len(z),5);self.assertEqual(r.Primary_Count,1)
        self.assertEqual(r.SameSymbolIncluded_Count,2);self.assertEqual(r.SimultaneousOther,1)
        self.assertAlmostEqual(r.Primary_GrossBefore,2.2);self.assertAlmostEqual(r.Primary_GrossAfter,4.8)
        self.assertEqual(r.Primary_NIC,1);self.assertEqual(r.Primary_Before_JPY,-1.1)
        self.assertEqual(r.Primary_OpenIDs,'t0');self.assertEqual(z.iloc[0].Primary_Count,0)
        self.assertEqual(z[z.StrategyNo==5].iloc[0].RiskWeight,.9)
        self.assertEqual(b[-1]['PriorOpenCount'],2)
        with self.assertRaises(ValueError):c7.reconstruct(pd.concat([a,a.iloc[[0]]]))

    def test_diversifying_neutral_empty_and_net_zero(self):
        a=frame([(1,'EURAUD','Long','2024-01-05 23:59','2024-01-08 10:00','Q5'),
                 (2,'AUDJPY','Long','2024-01-05 23:59','2024-01-08 10:00','Q5'),
                 (3,'EURJPY','Short','2024-01-08 09:00','2024-01-08 11:00','Q3')])
        z,_=c7.reconstruct(a);r=z.iloc[-1]
        self.assertEqual(r.Primary_NIC,-1);self.assertEqual(r.EqualUnit_NIC,-1)
        self.assertAlmostEqual(r.Primary_GrossBefore,2.6);self.assertAlmostEqual(r.Primary_GrossAfter,.8)
        a.loc[1,'Direction']='Short';z,_=c7.reconstruct(a)
        self.assertEqual(z.iloc[-1].Primary_NIC,0)
        a=frame([(1,'GBPJPY','Long','2024-01-01 08:00','2024-01-01 12:00','Q3'),
                 (2,'GBPJPY','Short','2024-01-01 08:00','2024-01-01 12:00','Q3'),
                 (3,'EURJPY','Long','2024-01-01 09:00','2024-01-01 12:00','Q3')])
        z,_=c7.reconstruct(a);r=z.iloc[-1]
        self.assertEqual(r.Primary_HasOpen,1);self.assertEqual(r.Primary_GrossBefore,0);self.assertEqual(r.Primary_NIC,1)
        self.assertEqual(z.iloc[0].Primary_HasOpen,0);self.assertEqual(z.iloc[0].Primary_NIC,1)

    def test_weighted_vs_equal_unit(self):
        a=frame([(1,'EURAUD','Long','2024-01-01 08:00','2024-01-01 12:00','Q1'),
                 (2,'AUDJPY','Long','2024-01-01 08:00','2024-01-01 12:00','Q1'),
                 (3,'EURJPY','Short','2024-01-01 09:00','2024-01-01 12:00','Q5')])
        z,_=c7.reconstruct(a);r=z.iloc[-1]
        self.assertAlmostEqual(r.Primary_NIC,3/13);self.assertEqual(r.EqualUnit_NIC,-1)
        self.assertEqual(r.Primary_State,'CONCENTRATING')
        np.testing.assert_array_equal(c7.state(np.array([-1e-11,0,1e-11,-.1,.1])),['NEUTRAL','NEUTRAL','NEUTRAL','DIVERSIFYING','CONCENTRATING'])

    def test_design_OLS_bootstrap_and_rank_deficiency(self):
        rng=np.random.default_rng(7);n=600
        a=pd.DataFrame(dict(StrategyNo=rng.integers(1,5,n),R2Category=rng.choice(['Q1','Q3','R2_UNAVAILABLE'],n),
                            Primary_GrossBefore=rng.uniform(0,6,n),Primary_Count=rng.integers(0,6,n),
                            Primary_NIC=rng.uniform(-1,1,n),Week=np.repeat(np.arange(30).astype(str),20)))
        a['Primary_HasOpen']=a.Primary_Count.gt(0).astype(int)
        a['R']=.23*a.Primary_NIC+.1*a.Primary_GrossBefore+.06*a.Primary_Count+.2*a.Primary_HasOpen+.1*a.StrategyNo+rng.normal(0,.1,n)
        def direct(weights=None):
            z=pd.get_dummies(a[['StrategyNo','R2Category']].astype(str),dtype=float).to_numpy()
            x=np.column_stack([np.ones(n),z,a[['Primary_GrossBefore','Primary_Count','Primary_HasOpen','Primary_NIC']]])
            y=a.R.to_numpy()
            if weights is not None:x=x*np.sqrt(weights)[:,None];y=y*np.sqrt(weights)
            return np.linalg.lstsq(x,y,rcond=None)[0][-1]
        self.assertAlmostEqual(c7.adjusted(a,'Primary'),direct(),places=10)
        audit=c7.design_audit(a,'Primary','synthetic');self.assertEqual(audit['Rank'],audit['Columns'])
        b,_,_,valid=c7.bootstrap(a,'Primary',reps=40);self.assertEqual(valid,40)
        weeks=sorted(a.Week.unique());rng=np.random.Generator(np.random.PCG64(20260913))
        for i in range(5):
            mult=np.bincount(rng.integers(len(weeks),size=len(weeks)),minlength=len(weeks))
            w=a.Week.map(dict(zip(weeks,mult))).to_numpy()
            self.assertAlmostEqual(b[i],direct(w),places=10)
        a['Primary_GrossBefore']=2*a.Primary_Count
        self.assertAlmostEqual(c7.adjusted(a,'Primary'),direct(),places=10)
        a['Primary_NIC']=1
        self.assertTrue(np.isnan(c7.adjusted(a,'Primary')))


if __name__=='__main__':unittest.main()
