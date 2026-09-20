import unittest
import numpy as np
import pandas as pd
from pre_entry_price_action_phase1 import assign,classify,combined,ci_for,bootstrap,tables,INS,FLAT,BUCKETS
from trend_strength_phase1 import to_jst

class PreEntryTests(unittest.TestCase):
    def fixture(self,n=200):
        e=pd.Timestamp('2026-01-05 01:00');idx=pd.date_range(e-pd.Timedelta(minutes=n),periods=n+2,freq='min');b=pd.DataFrame(dict(Open=2.,High=4.,Low=1.,Close=3.),index=idx);t=pd.DataFrame([dict(TradeID=0,StrategyNo=1,EntryTime=e,Direction='Long',R=1.)]);return t,b
    def test_boundaries(self):
        for x,label in [(0,BUCKETS[0]),(np.nextafter(1/3,0),BUCKETS[0]),(1/3,BUCKETS[1]),(np.nextafter(2/3,0),BUCKETS[1]),(2/3,BUCKETS[2]),(1,BUCKETS[2])]:self.assertEqual(classify(x),label)
    def test_exact_windows(self):
        t,b=self.fixture();e=t.EntryTime[0]
        for w in [60,180]:
            z=b.copy();z.loc[e-pd.Timedelta(minutes=w),'High']=10;z.loc[e-pd.Timedelta(minutes=w+1),'High']=100;r=assign(t,z,w).iloc[0];self.assertEqual(r.Bars,w);self.assertEqual(r.H,10);self.assertEqual(r.FirstM1,e-pd.Timedelta(minutes=w));self.assertEqual(r.LastM1,e-pd.Timedelta(minutes=1))
    def test_entry_and_future_exclusion(self):
        t,b=self.fixture();e=t.EntryTime[0];changed=b.copy();changed.loc[e:]=999
        for w in [60,180]:pd.testing.assert_frame_equal(assign(t,b,w),assign(t,changed,w))
    def test_prefix_invariance(self):
        t,b=self.fixture()
        for w in [60,180]:pd.testing.assert_frame_equal(assign(t,b,w),assign(t,b[b.index<t.EntryTime[0]],w))
    def test_inversion(self):
        t,b=self.fixture();s=t.copy();s.Direction='Short'
        for w in [60,180]:self.assertAlmostEqual(assign(t,b,w).PDRP[0]+assign(s,b,w).PDRP[0],1)
    def test_price_boundaries(self):
        t,b=self.fixture()
        for c,label in [(1,BUCKETS[0]),(2,BUCKETS[1]),(3,BUCKETS[2]),(4,BUCKETS[2])]:
            b.Close=c;self.assertEqual(assign(t,b,60).Bucket[0],label)
    def test_coverage_edges(self):
        t,b=self.fixture();e=t.EntryTime[0]
        for w,n in [(60,48),(180,144)]:
            z=b[(b.index>=e-pd.Timedelta(minutes=n))&(b.index<e)];self.assertNotEqual(assign(t,z,w).Bucket[0],INS);self.assertEqual(assign(t,z.iloc[1:],w).Bucket[0],INS)
    def test_freshness(self):
        t,b=self.fixture();e=t.EntryTime[0]
        for w in [60,180]:
            self.assertNotEqual(assign(t,b[b.index<=e-pd.Timedelta(minutes=5)],w).Bucket[0],INS);self.assertEqual(assign(t,b[b.index<=e-pd.Timedelta(minutes=6)],w).Bucket[0],INS)
    def test_flat_and_precedence(self):
        t,b=self.fixture();b[:]=2
        for w in [60,180]:
            r=assign(t,b,w).iloc[0];self.assertEqual(r.Bucket,FLAT);self.assertTrue(np.isnan(r.PDRP));self.assertEqual(assign(t,b.iloc[0:3],w).Bucket[0],INS)
    def test_no_history(self):
        t,b=self.fixture();r=assign(t,b.iloc[:0],60).iloc[0];self.assertEqual(r.Bucket,INS);self.assertEqual(r.Bars,0)
    def test_overnight(self):
        t,b=self.fixture();r=assign(t,b,180).iloc[0];self.assertLess(r.WindowStart.date(),t.EntryTime[0].date());self.assertEqual(r.Bars,180)
    def test_monday_closure(self):
        t,b=self.fixture();e=t.EntryTime[0];z=b[b.index>=e-pd.Timedelta(minutes=30)]
        for w in [60,180]:self.assertEqual(assign(t,z,w).Bucket[0],INS)
    def test_missing_interior(self):
        t,b=self.fixture();e=t.EntryTime[0];z=b.drop(pd.date_range(e-pd.Timedelta(minutes=20),periods=12,freq='min'));self.assertEqual(assign(t,z,60).Bars[0],48)
    def test_nonminute_rejected(self):
        t,b=self.fixture();t.EntryTime+=pd.Timedelta(seconds=1)
        with self.assertRaises(ValueError):assign(t,b,60)
    def test_duplicate_rejected(self):
        t,b=self.fixture()
        with self.assertRaises(ValueError):assign(t,pd.concat([b,b.iloc[-1:]]),60)
    def test_timezone(self):
        got=to_jst(pd.DatetimeIndex(['2026-01-05 00:00','2026-07-06 00:00']));self.assertEqual(list(got.hour),[7,6]);self.assertIsNone(got.tz)
    def test_bad_value(self):
        for v in [-.1,1.1,np.nan]:
            with self.assertRaises(ValueError):classify(v)
    def test_overall_verdict(self):
        def d(s,x):return dict(Support=s,PooledDelta=x)
        self.assertEqual(combined(d('SUPPORTED',1),d('SUPPORTED',1)),'BOTH_SUPPORTED');self.assertEqual(combined(d('SUPPORTED',1),d('NOT_SUPPORTED',1)),'PRIMARY_SUPPORTED_ROBUSTNESS_ALIGNED');self.assertEqual(combined(d('SUPPORTED',1),d('NOT_SUPPORTED',-1)),'UNSTABLE');self.assertEqual(combined(d('NOT_SUPPORTED',1),d('SUPPORTED',1)),'NOT_SUPPORTED');self.assertEqual(combined(d('SUPPORTED',1),d('NOT_SUPPORTED',0)),'UNSTABLE')
    def test_bootstrap_empty(self):
        bs=np.zeros((5000,28,2));self.assertTrue(np.isnan(ci_for(bs,bs,[1])['CILow']))
    def test_inadequate_bootstrap_count(self):
        bs=np.ones((5000,28,2));bc=np.ones_like(bs);bc[:251]=0;self.assertEqual(ci_for(bs,bc,[1])['ValidBootstraps'],4749);self.assertTrue(np.isnan(ci_for(bs,bc,[1])['CILow']))

if __name__=='__main__':unittest.main()
