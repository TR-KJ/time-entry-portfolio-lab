"""Synthetic tests: run before any Phase 2 real-data assignment."""
from pathlib import Path
import sys,unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src/research"))
import tokyo_london_phase2 as m

def fixture(n=600):
    rows=[]
    dates=pd.bdate_range("2020-01-01",periods=n)
    for pair in m.PAIRS:
        for method in m.METHODS:
            x=np.sin(np.arange(n)*.23)*30
            for i,date in enumerate(dates):
                rows.append(dict(Pair=pair,Method=method,Date=date,Valid=True,X=x[i],Y=(-1)**i*2.))
    return pd.DataFrame(rows)

class Tests(unittest.TestCase):
    def test_first252_and_midrank(self):
        p,q,l,e=m.classify(np.ones(255))
        self.assertTrue(np.isnan(p[:252]).all())
        self.assertTrue((q[:252]==0).all())
        self.assertEqual(p[252],.5);self.assertEqual(q[252],3)
        self.assertEqual(l[252],0);self.assertEqual(e[252],252)

    def test_boundaries(self):
        for num,want in [(0,1),(100,1),(101,2),(201,2),(202,3),(302,3),(303,4),(403,4),(404,5),(504,5)]:
            less=num//2;equal=num%2
            a=[0.]*less+[1.]*equal+[2.]*(252-less-equal)+[1.]
            p,q,_,_=m.classify(a)
            self.assertEqual(q[-1],want);self.assertEqual(p[-1],num/504)

    def test_no_lookahead_and_period_continuity(self):
        d=fixture();a=m.assign(d)
        changed=d.copy();changed.loc[changed.Date>="2022-01-01",["X","Y"]]=999.
        b=m.assign(changed)
        pd.testing.assert_frame_equal(a[a.Date<"2022-01-01"],b[b.Date<"2022-01-01"])
        first=a[a.Date>="2022-01-01"].groupby(["Pair","Method"]).first()
        self.assertTrue(first.ReferenceN.eq(252).all())
        self.assertTrue(first.ReferenceStart.lt(pd.Timestamp("2022-01-01")).all())

    def test_neutral_missing_and_alignment(self):
        d=fixture(300)
        d.loc[d.Date.eq(pd.bdate_range("2020-01-01",periods=300)[260]),"X"]=0
        d.loc[d.Date.eq(pd.bdate_range("2020-01-01",periods=300)[270]),"Y"]=0
        d.loc[d.Date.eq(pd.bdate_range("2020-01-01",periods=300)[280]),"Valid"]=False
        a=m.assign(d)
        self.assertTrue(a[a.TokyoNeutral&a.Q.gt(0)].ExclusionReason.eq("TOKYO_NEUTRAL").all())
        self.assertTrue(a[a.Y.eq(0)&a.Eligible].AlignedLondonReturn.eq(0).all())
        self.assertTrue(a[~a.Valid].ExclusionReason.eq("MISSING_ENDPOINT").all())
        for r in a[a.Eligible].itertuples():
            expected=(1 if r.X>0 else -1)*r.Y*(-1 if r.Pair=="EURAUD" else 1)
            self.assertEqual(r.AlignedLondonReturn,expected)
            self.assertLess(r.ReferenceEnd,r.Date)

    def test_gate_branches(self):
        rows=[]
        for pair in m.PAIRS:
            for method in m.METHODS:
                for per in m.PERIODS:
                    rows.append(dict(Pair=pair,Method=method,Period=per,Status="OK",Delta=4.,
                                     Q5Mean=2.,CILow=1.,PUnadjusted=.001))
        d=pd.DataFrame(rows)
        self.assertTrue(m.verdicts(d).Verdict.eq("EXPLORATORY_SUPPORTED").all())
        d["PUnadjusted"]=.2
        self.assertTrue(m.verdicts(d).Verdict.eq("EXPLORATORY_WATCHLIST").all())
        d["Q5Mean"]=-1
        self.assertTrue(m.verdicts(d).Verdict.eq("NOT_SUPPORTED").all())
        d["Status"]="INSUFFICIENT_SAMPLE"
        self.assertTrue(m.verdicts(d).Verdict.eq("INSUFFICIENT_SAMPLE").all())

    def test_gj_main_recent_and_gate_d(self):
        d=pd.DataFrame([dict(Pair=p,Method=meth,Period=per,Status="OK",Delta=4.,Q5Mean=2.,CILow=1.,PUnadjusted=.001)
            for p in m.PAIRS for meth in m.METHODS for per in m.PERIODS])
        d.loc[d.Pair.eq("GBPJPY")&d.Period.eq("ALL"),"Delta"]=-10.
        self.assertEqual(m.verdicts(d).set_index("Pair").loc["GBPJPY","Verdict"],"EXPLORATORY_SUPPORTED")
        d.loc[d.Pair.eq("GBPJPY")&d.Period.eq("RecentB")&d.Method.eq("Primary"),"Delta"]=-1
        self.assertEqual(m.verdicts(d).set_index("Pair").loc["GBPJPY","D"],"FAIL")

    def test_bootstrap_independent(self):
        d=fixture(500);a=m.assign(d);g=a[a.Pair.eq("USDJPY")&a.Method.eq("Primary")&a.Eligible]
        means,bs,ok,first,w=m.bootstrap(g,"2020-01-01","2021-12-31")
        wk=((g.Date-first).dt.days//7).to_numpy();x=g.AlignedLondonReturn.to_numpy();q=g.Q.to_numpy()
        independent=[]
        for weight in w:
            ids=np.repeat(np.arange(len(g)),weight[wk]);vals=x[ids];qs=q[ids]
            independent.append(vals[qs==5].mean()-vals[qs==1].mean())
        np.testing.assert_allclose(bs,independent,atol=1e-12,equal_nan=True)
        np.testing.assert_allclose(np.quantile(bs[ok],[.025,.975]),np.quantile(np.asarray(independent)[ok],[.025,.975]),atol=1e-12)

    def test_holm_and_sample(self):
        np.testing.assert_allclose(m.p1.holm([.04,.01,.02]),[.04,.03,.04])
        g=pd.DataFrame({"Date":pd.bdate_range("2020-01-01",periods=100),"Q":[1]*50+[5]*50})
        self.assertTrue(m.sample_ok(g))
        self.assertFalse(m.sample_ok(g.iloc[:79]))
        self.assertFalse(m.sample_ok(g.assign(Q=1)))

if __name__=="__main__":unittest.main()
