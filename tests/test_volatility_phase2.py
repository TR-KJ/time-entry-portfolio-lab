import unittest
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import volatility_phase1 as p1
import volatility_phase2 as v


class TestPhase2(unittest.TestCase):
    def test_percent_boundaries(self):
        for point, q in [(0,'Q1'),(20,'Q2'),(40,'Q3'),(60,'Q4'),(80,'Q5'),(100,'Q5')]:
            self.assertEqual(v.percentile_bin(point), q)
        for i, point in enumerate([20,40,60,80]):
            self.assertEqual(v.percentile_bin(np.nextafter(float(point),-np.inf)), v.QUINTILES[i])
            self.assertEqual(v.percentile_bin(np.nextafter(float(point),np.inf)), v.QUINTILES[i+1])
        self.assertEqual(v.percentile_bin(np.nan), p1.INS)
        for point in [-1,101,np.inf,-np.inf]:
            with self.assertRaises(ValueError): v.percentile_bin(point)

    def test_all_midrank_numerators(self):
        for n in range(505):
            expected = 'Q1' if n<=100 else 'Q2' if n<=201 else 'Q3' if n<=302 else 'Q4' if n<=403 else 'Q5'
            self.assertEqual(v.quintile(n/504), expected)
            self.assertEqual(v.quintile(n/504), v.percentile_bin(n/504*100))
        for bad in [.2,.123456,-.1,1.1,np.inf]:
            with self.assertRaises(ValueError): v.quintile(bad)
        self.assertEqual(v.quintile(np.nan),p1.INS)

    def test_actual_midrank_and_history(self):
        ranks, regs = p1.rank_regime(np.ones(253))
        self.assertEqual(v.quintile(ranks[-1]), 'Q3')
        self.assertEqual(v.quintile(ranks[-2]), p1.INS)
        for less in [0,50,51,100,101,151,152,201,202,252]:
            a=np.r_[np.zeros(less),np.full(252-less,2.),1.]
            ranks,_=p1.rank_regime(a)
            self.assertEqual(v.quintile(ranks[-1]),v.percentile_bin(100*less/252))

    def test_decision_three_vs_two(self):
        three = v.indicators([0,2,1,3,4]); two=v.indicators([0,2,1,4,3])
        self.assertEqual(three['AdjacentIncreases'],3); self.assertTrue(v.ordered(three))
        self.assertEqual(two['AdjacentIncreases'],2); self.assertFalse(v.ordered(two))
        self.assertEqual(v.group_support(three,two),v.SUPPORTED) # EW 3/4 is not required.
        self.assertFalse(three['StrictlyIncreasing'])
        self.assertTrue(v.indicators([0,1,2,3,4])['StrictlyIncreasing'])
        equal=v.indicators([1,1,1,1,1]); self.assertTrue(equal['Nondecreasing'])
        self.assertTrue(np.isnan(equal['Spearman']));self.assertFalse(v.ordered(equal))
        self.assertEqual(v.group_support(equal,equal),'NOT_SUPPORTED')
        self.assertEqual(v.group_support(three,v.indicators([np.nan]*5)),'UNDETERMINED')
        tied=v.indicators([0,1,1,2,3]);self.assertEqual(tied['AdjacentIncreases'],3)
        self.assertGreater(tied['Spearman'],0)

    def test_combined(self):
        self.assertEqual(v.combine(v.SUPPORTED,v.SUPPORTED),'BOTH_SUPPORTED')
        self.assertEqual(v.combine(v.SUPPORTED,'NOT_SUPPORTED'),'PRIMARY_ONLY')
        self.assertEqual(v.combine('NOT_SUPPORTED',v.SUPPORTED),'ROBUSTNESS_ONLY')
        self.assertEqual(v.combine('NOT_SUPPORTED','NOT_SUPPORTED'),'NOT_SUPPORTED')
        self.assertEqual(v.combine('LOW_SAMPLE',v.SUPPORTED),'UNDETERMINED')

    def test_eligibility_fixed_same_five(self):
        rows=[]
        for no in [1,2]:
            for i,q in enumerate(v.QUINTILES):
                for _ in range(19 if no==2 and q=='Q3' else 20):
                    rows.append(dict(StrategyNo=no,R=float(i+no),primaryQuintile=q))
        a=pd.DataFrame(rows); c,s=v.tables_for(a,'primary','FULL',{})
        e=c[(c.Scope=='Portfolio') & (c.Aggregation=='strategy_equal_weighted')]
        self.assertTrue((e.EligibleIDs=='1').all());self.assertTrue((e.EligibleStrategies==1).all())
        np.testing.assert_equal(e.AvgR.to_numpy(),[1,2,3,4,5])
        self.assertTrue((s[s.Scope=='2'].Support=='LOW_SAMPLE').all())
        self.assertTrue((s[s.Scope=='1'].Support==v.SUPPORTED).all())
        self.assertEqual(c[(c.Scope=='Portfolio')&(c.Quintile=='Q3')&(c.Aggregation=='trade_weighted')].Trades.iloc[0],39)
        self.assertTrue(e.TotalR.isna().all())
        empty,summary=v.tables_for(a.iloc[:0],'primary','FULL',{})
        self.assertTrue((summary[summary.ScopeType=='Group'].Support=='UNDETERMINED').all())

    def test_metrics(self):
        self.assertEqual(v.cell_stats([-1,0,2])['TotalR'],1)
        self.assertEqual(v.cell_stats([-1,0,2])['PF'],2)
        self.assertAlmostEqual(v.cell_stats([-1,0,2])['WinRate'],100/3)
        self.assertTrue(v.cell_stats([0]*19)['LOW_SAMPLE']);self.assertFalse(v.cell_stats([0]*20)['LOW_SAMPLE'])
        self.assertTrue(np.isnan(v.cell_stats([])['AvgR']))
        self.assertTrue(np.isinf(v.cell_stats([1])['PF']))
        self.assertTrue(np.isnan(v.cell_stats([0])['PF']))

    def test_future_m1_mutation_no_lookahead(self):
        ix=pd.date_range('2019-01-01 00:00',periods=800,freq='12h')
        close=100+np.sin(np.arange(800)/10)
        b=pd.DataFrame(dict(Open=close,High=close+.1,Low=close-.1,Close=close),index=ix)
        t=pd.DataFrame({'EntryTime':pd.to_datetime(['2019-12-01 00:00','2019-12-01 08:01'])})
        a=v.add_quintiles(p1.assign(t,p1.features(p1.make_daily(b))))
        future=b.copy();future.loc[future.index>='2019-12-01',:]*=5
        z=v.add_quintiles(p1.assign(t,p1.features(p1.make_daily(future))))
        pd.testing.assert_frame_equal(a,z)

    def test_ci_shared_week_and_mapping(self):
        first,w=p1.bootstrap_weights()
        times=pd.date_range(first,periods=w.shape[1],freq='7D')
        a=pd.DataFrame({'EntryTime':np.repeat(times,2),'R':np.tile([1.,3.],len(times)),
                        'primaryQuintile':np.tile(['Q1','Q5'],len(times))})
        ci=v.confidence(a,'primary',first,w)
        self.assertEqual(ci['ValidBootstraps'],5000)
        self.assertEqual(ci['CILow'],2);self.assertEqual(ci['CIHigh'],2)
        ci=v.confidence(a.iloc[:2],'primary',first,w)
        self.assertLess(ci['ValidBootstraps'],4750);self.assertTrue(np.isnan(ci['CILow']))
        self.assertTrue((w.sum(axis=1)==len(times)).all())

    def test_phase1_code_hashes(self):
        for name,expected in v.SOURCE_HASHES.items():
            self.assertEqual(p1.sha(Path(p1.__file__).with_name(name)),expected)


if __name__=='__main__': unittest.main()
