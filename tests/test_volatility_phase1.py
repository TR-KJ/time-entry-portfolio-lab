import unittest,math
import numpy as np
import pandas as pd
import volatility_phase1 as v

class TestVolatility(unittest.TestCase):
    def daily(self,n=300):
        return pd.DataFrame({'DailyDate':pd.date_range('2020-01-01',periods=n),'Open':100.,'High':np.arange(n)+101.,'Low':100.,'Close':100.,'LastM1':pd.date_range('2020-01-01 23:59',periods=n),'AvailableAt':pd.date_range('2020-01-02',periods=n),'DailyIndex':range(n)})
    def test_sma20_and_wilder_manual_distinction(self):
        d=v.features(self.daily())
        self.assertTrue(np.isnan(d.ATR20.iloc[18]));self.assertEqual(d.ATR20.iloc[19],10.5);self.assertEqual(d.ATR20.iloc[20],11.5)
        # Wilder hand example: seed mean(1..20)=10.5; next=(19*10.5+21)/20=11.025.
        w=10.5
        w=(19*w+21)/20
        self.assertEqual(w,11.025);self.assertNotEqual(w,d.ATR20.iloc[20])
    def test_history_indexes(self):
        d=v.features(self.daily())
        self.assertEqual(d.primary.iloc[270],v.INS);self.assertNotEqual(d.primary.iloc[271],v.INS)
        self.assertEqual(d.robustness.iloc[271],v.INS);self.assertEqual(d.robustness.iloc[272],'NORMAL')
    def test_rank_reference_exclusion(self):
        x=np.arange(300,dtype=float);p,r=v.rank_regime(x)
        self.assertEqual(p[252],1.);self.assertEqual(r[252],'HIGH');self.assertEqual(r[251],v.INS)
        x[0]=np.nan;p,r=v.rank_regime(x);self.assertEqual(r[252],v.INS);self.assertEqual(r[253],'HIGH')
    def test_exact_boundaries_and_ties(self):
        for less,expected in [(83,'LOW'),(84,'NORMAL'),(167,'NORMAL'),(168,'HIGH')]:
            a=np.r_[np.zeros(less),np.full(252-less,2.),1.];p,r=v.rank_regime(a);self.assertEqual(r[-1],expected)
        p,r=v.rank_regime(np.ones(253));self.assertEqual(p[-1],.5);self.assertEqual(r[-1],'NORMAL')
    def test_rv(self):
        d=self.daily();d.Close=np.exp(np.cumsum(np.r_[0,np.tile([.01,-.02,.03],100)[:299]]))*100
        z=v.features(d);r=np.log(d.Close.iloc[1:21].to_numpy()/d.Close.iloc[:20].to_numpy())
        mean=sum(r)/20;expected=math.sqrt(sum((a-mean)**2 for a in r)/19)*math.sqrt(252)
        self.assertAlmostEqual(z.RV20.iloc[20],expected,14)
    def test_jst_daily_ohlc_and_saturday(self):
        ix=v.to_jst(pd.to_datetime(['2026-01-02 16:59','2026-01-02 17:00','2026-01-02 23:59']))
        self.assertEqual(ix[0],pd.Timestamp('2026-01-02 23:59'));self.assertEqual(ix[1],pd.Timestamp('2026-01-03 00:00'))
        summer=v.to_jst(pd.to_datetime(['2026-07-03 18:00']))
        self.assertEqual(summer[0],pd.Timestamp('2026-07-04 00:00'))
        b=pd.DataFrame({'Open':[1,2,3],'High':[2,4,5],'Low':[.5,1,2],'Close':[1.5,3,4]},index=ix)
        d=v.make_daily(b);self.assertEqual(len(d),2);self.assertEqual(d.iloc[1].Close,4);self.assertEqual(d.iloc[1].High,5);self.assertEqual(d.iloc[1].Open,2);self.assertEqual(d.iloc[1].Low,1)
    def test_midnight_weekend_no_lookahead(self):
        d=v.features(self.daily());t=pd.DataFrame({'EntryTime':pd.to_datetime(['2020-10-01 00:00','2020-10-01 12:00'])})
        a=v.assign(t,d);d.loc[d.DailyDate>=pd.Timestamp('2020-10-01'),['Close','High']]=999999
        b=v.assign(t,v.features(d));self.assertTrue(a.primary.equals(b.primary));self.assertTrue(a.ATR20.equals(b.ATR20))
        dates=pd.to_datetime(['2026-01-02','2026-01-03']);d=self.daily(2);d.DailyDate=dates;d.AvailableAt=dates+pd.Timedelta(days=1);d.LastM1=dates+pd.Timedelta(hours=6)
        a=v.assign(pd.DataFrame({'EntryTime':pd.to_datetime(['2026-01-05 08:01'])}),v.features(d));self.assertEqual(a.DailyDate.iloc[0],pd.Timestamp('2026-01-03'))
    def test_stats_and_sample(self):
        self.assertTrue(v.stats([])['LOW_SAMPLE']);self.assertTrue(math.isnan(v.stats([])['AvgR']));self.assertTrue(math.isinf(v.stats([1])['PF']))
        self.assertAlmostEqual(v.stats([-1,0,1])['WinRate'],100/3);self.assertEqual(v.stats([-1,0,1])['PF'],1);self.assertFalse(v.stats([0]*20)['LOW_SAMPLE'])
    def test_bootstrap_shared_week(self):
        first,w=v.bootstrap_weights();self.assertTrue((w.sum(axis=1)==w.shape[1]).all())
        t=pd.DataFrame({'EntryTime':pd.to_datetime(['2020-01-06']*4),'R':[1,1,2,2],'primary':['LOW','LOW','HIGH','HIGH']})
        ci=v.confidence(t,'primary',first,w)
        self.assertLess(ci['ValidBootstraps'],4750) # an isolated week is frequently absent.
        self.assertTrue(math.isnan(ci['CILow']))
    def test_empty_eligibility(self):
        t=pd.DataFrame({'StrategyNo':[1],'R':[1.],'primary':['LOW']});c,g,d=v.tables_for(t,'primary','FULL',{})
        self.assertTrue((d.Support=='UNDETERMINED').all());self.assertFalse(c.Eligible.any())

if __name__=='__main__': unittest.main()
