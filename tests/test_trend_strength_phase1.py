import unittest,math,tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import trend_strength_phase1 as v
from verify_trend_strength_phase1 import independent_indicators

class TestTrend(unittest.TestCase):
    def daily(self,n=350,flat=False):
        c=np.full(n,100.) if flat else 100+np.arange(n)*.1+np.sin(np.arange(n))
        dates=pd.date_range('2020-01-01',periods=n)
        return pd.DataFrame(dict(DailyDate=dates,Open=c,High=c+1,Low=c-1,Close=c,LastM1=dates+pd.Timedelta(hours=23,minutes=59),AvailableAt=dates+pd.Timedelta(days=1),DailyIndex=range(n)))
    def test_adx_hand_monotone(self):
        d=self.daily();d[['Open','Close']]=np.column_stack([100+np.arange(len(d))]*2);d.High=d.Close+1;d.Low=d.Close-1
        x=v.features(d)
        self.assertTrue(x.ADX14.iloc[:27].isna().all());self.assertEqual(x.ADX14.iloc[27],100.);self.assertEqual(x.ADX14.iloc[28],100.)
        self.assertEqual(x.ER20.iloc[20],1.);self.assertTrue(x.ER20.iloc[:20].isna().all())
    def test_zero_denominators(self):
        d=self.daily(flat=True);d.High=d.Low=d.Close
        x=v.features(d);self.assertTrue((x.ADX14.iloc[27:]==0).all());self.assertTrue((x.ER20.iloc[20:]==0).all())
        self.assertEqual(x.primary.iloc[279],'NORMAL');self.assertEqual(x.robustness.iloc[272],'NORMAL')
    def test_adx_scalar_reference_and_ties(self):
        d=self.daily();d.loc[17,'High']=d.High.iloc[16]+2;d.loc[17,'Low']=d.Low.iloc[16]-2
        x=v.features(d);a,e=independent_indicators(d)
        self.assertEqual(x.PlusDM.iloc[17],0);self.assertEqual(x.MinusDM.iloc[17],0)
        np.testing.assert_allclose(x.ADX14,a,atol=1e-11,rtol=0,equal_nan=True)
        np.testing.assert_allclose(x.ER20,e,atol=1e-12,rtol=0,equal_nan=True)
    def test_wilder_seed_and_update(self):
        raw=np.arange(30,dtype=float);raw[0]=np.nan;x=v.wilder_mean(raw)
        self.assertEqual(x[14],7.5);self.assertEqual(x[15],(13*7.5+15)/14)
    def test_er_hand_zigzag(self):
        d=self.daily(30);d.Close=[100+(-1)**i for i in range(30)]
        x=v.features(d);self.assertEqual(x.ER20.iloc[20],0.)
        d.Close=np.arange(30.)+100;d.loc[20,'Close']=118
        self.assertAlmostEqual(v.features(d).ER20.iloc[20],18/20)
    def test_history_indices(self):
        x=v.features(self.daily());self.assertEqual(x.primary.iloc[278],v.INS);self.assertNotEqual(x.primary.iloc[279],v.INS)
        self.assertEqual(x.robustness.iloc[271],v.INS);self.assertNotEqual(x.robustness.iloc[272],v.INS)
    def test_rank_excludes_current_and_nan(self):
        a=np.arange(300,dtype=float);p,r=v.rank_regime(a);self.assertEqual(p[252],1);self.assertEqual(r[251],v.INS)
        a[0]=np.nan;p,r=v.rank_regime(a);self.assertEqual(r[252],v.INS);self.assertEqual(r[253],'HIGH')
    def test_boundary_and_ties(self):
        for less,e in [(83,'LOW'),(84,'NORMAL'),(167,'NORMAL'),(168,'HIGH')]:
            p,r=v.rank_regime(np.r_[np.zeros(less),np.full(252-less,2.),1.]);self.assertEqual(r[-1],e)
        p,r=v.rank_regime(np.ones(253));self.assertEqual(p[-1],.5);self.assertEqual(r[-1],'NORMAL')
    def test_jst_ohlc_weekend_and_dst(self):
        ix=v.to_jst(pd.to_datetime(['2026-01-02 16:59','2026-01-02 17:00','2026-01-02 23:59']))
        self.assertEqual(ix[0],pd.Timestamp('2026-01-02 23:59'));self.assertEqual(ix[1],pd.Timestamp('2026-01-03'))
        self.assertEqual(v.to_jst(pd.to_datetime(['2026-07-03 18:00']))[0],pd.Timestamp('2026-07-04'))
        b=pd.DataFrame(dict(Open=[1,2,3],High=[2,4,5],Low=[.5,1,2],Close=[1.5,3,4]),index=ix)
        d=v.make_daily(b);self.assertEqual(len(d),2);self.assertEqual(d.Close.iloc[1],4);self.assertEqual(d.High.iloc[1],5)
        self.assertEqual(d.Open.iloc[1],2);self.assertEqual(d.Low.iloc[1],1)
        import volatility_phase1 as reference
        pd.testing.assert_frame_equal(d,reference.make_daily(b))
    def test_no_lookahead_m1_mutation_and_prefix(self):
        d=self.daily();bars=d.set_index('LastM1')[['Open','High','Low','Close']]
        t=pd.DataFrame({'EntryTime':pd.to_datetime(['2020-11-01 00:00','2020-11-01 12:00'])})
        before=v.assign(t,v.features(v.make_daily(bars)))
        changed=bars.copy();changed.loc[changed.index.normalize()>=pd.Timestamp('2020-11-01')]*=7
        after=v.assign(t,v.features(v.make_daily(changed)))
        pd.testing.assert_frame_equal(before,after)
        prefix=v.assign(t,v.features(v.make_daily(bars[bars.index<pd.Timestamp('2020-11-01')])));pd.testing.assert_frame_equal(before,prefix)
    def test_monday_and_pre_history(self):
        d=self.daily(2);d.DailyDate=pd.to_datetime(['2026-01-02','2026-01-03']);d.AvailableAt=d.DailyDate+pd.Timedelta(days=1);d.LastM1=d.DailyDate+pd.Timedelta(hours=6)
        a=v.assign(pd.DataFrame({'EntryTime':pd.to_datetime(['2026-01-01 00:00','2026-01-05 08:01'])}),v.features(d))
        self.assertEqual(a.primary.iloc[0],v.INS);self.assertEqual(a.DailyDate.iloc[1],pd.Timestamp('2026-01-03'))
    def test_stats_and_order(self):
        self.assertTrue(v.stats([])['LOW_SAMPLE']);self.assertTrue(math.isnan(v.stats([])['AvgR']));self.assertTrue(math.isinf(v.stats([1])['PF']))
        self.assertEqual(v.stats([-1,0,1])['PF'],1);self.assertFalse(v.stats([0]*20)['LOW_SAMPLE'])
        self.assertEqual(v.regime_order({r:{'AvgR':1} for r in v.REGIMES}),'LOW = NORMAL = HIGH')
    def test_empty_eligibility(self):
        t=pd.DataFrame({'StrategyNo':[1],'R':[1.],'primary':['LOW']});c,g,d=v.tables_for(t,'primary','FULL',{})
        self.assertTrue((d.Support=='UNDETERMINED').all());self.assertFalse(c.Eligible.any())
    def test_ci_formal_and_equal_weight_sample(self):
        t=pd.DataFrame([dict(StrategyNo=n,R=val,primary=r) for n in [1,2] for r,val in [('LOW',0.),('HIGH',1.)] for _ in range(20)])
        cis={('primary','Portfolio'):dict(CILow=-.1,CIHigh=2.,ValidBootstraps=5000)}
        c,g,d=v.tables_for(t,'primary','FULL',cis);self.assertEqual(d.loc[d.Group=='Portfolio','Support'].iloc[0],'NOT_SUPPORTED')
        cis[('primary','Portfolio')]['CILow']=.1;c,g,d=v.tables_for(t,'primary','FULL',cis)
        z=d[d.Group=='Portfolio'].iloc[0];self.assertEqual(z.Support,'SUPPORTED');self.assertEqual(z.EligibleStrategies,2)
        self.assertTrue(g.loc[(g.Group=='Portfolio')&(g.Aggregation=='strategy_equal_weighted')&(g.Regime=='NORMAL'),'AvgR'].isna().all())
    def test_bootstrap_shared_week(self):
        first,w=v.bootstrap_weights();self.assertEqual(w.shape,(5000,611));self.assertTrue((w.sum(axis=1)==w.shape[1]).all())
        t=pd.DataFrame({'EntryTime':pd.to_datetime(['2020-01-06']*4),'R':[1,1,2,2],'primary':['LOW','LOW','HIGH','HIGH']})
        ci=v.confidence(t,'primary',first,w);self.assertLess(ci['ValidBootstraps'],4750);self.assertTrue(math.isnan(ci['CILow']))
    def test_baseline_wrong_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'wrong.csv';p.write_text('wrong')
            with self.assertRaisesRegex(ValueError,'hash'): v.load_baseline(p)

if __name__=='__main__': unittest.main()
