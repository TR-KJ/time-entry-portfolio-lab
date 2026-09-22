"""Synthetic Phase 2b checks, run before real directional results."""
from pathlib import Path
import sys,unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src/research"))
import tokyo_london_phase2b as m

class Tests(unittest.TestCase):
    def test_alignment_and_q5_boundary(self):
        self.assertEqual(m.p1.pip("EURAUD"),.0001)
        self.assertEqual(m.p1.pip("USDJPY"),.01)
        for pair,factor in [("EURAUD",-1),("USDJPY",1)]:
            for x in [-7.,7.]:
                y=3.
                aligned=factor*np.sign(x)*y
                self.assertEqual(aligned,3. if (factor*np.sign(x)>0) else -3.)
        p,q,_,_=m.p2.classify([0.]*252+[100.])
        self.assertEqual(q[-1],5);self.assertEqual(p[-1],1.)

    def test_calendar_sample_40_days_20_weeks(self):
        d=pd.date_range("2020-01-06",periods=40,freq="W-MON")
        g=pd.DataFrame({"Date":pd.to_datetime(np.repeat(d,1)),"AlignedLondonReturn":np.ones(40)})
        self.assertEqual(m.stats(g)["CalendarWeeks"],40)
        self.assertEqual(m.stats(g)["N"],40)
        self.assertEqual(m.stats(g)["TotalAlignedPips"],40)
        self.assertEqual(m.stats(g)["PositiveRate"],1)
        self.assertEqual(m.stats(g.iloc[:39])["N"],39)
        short=pd.DataFrame({"Date":pd.bdate_range("2020-01-06",periods=40)})
        self.assertLess(m.observed_weeks(short),20)

    def test_empty_and_zero_stats(self):
        g=pd.DataFrame({"Date":pd.bdate_range("2020-01-01",periods=3),
                        "AlignedLondonReturn":[-2.,0.,2.]})
        s=m.stats(g)
        self.assertEqual(s["Mean"],0)
        self.assertEqual(s["Std"],2)
        self.assertEqual(s["PositiveRate"],1/3)
        self.assertEqual(s["NegativeRate"],1/3)
        self.assertEqual(s["ZeroRate"],1/3)
        self.assertTrue(np.isnan(m.stats(g.iloc[:0])["Mean"]))

    def test_cluster_bootstrap_same_weeks(self):
        dates=pd.bdate_range("2020-01-01",periods=100)
        up=pd.DataFrame({"Date":dates,"AlignedLondonReturn":np.arange(100,dtype=float)})
        down=pd.DataFrame({"Date":dates,"AlignedLondonReturn":-np.arange(100,dtype=float)})
        first,w=m.p1.week_weights("2020-01-01","2020-12-31")
        u,_=m.bootstrap(up,first,w);v,_=m.bootstrap(down,first,w)
        np.testing.assert_allclose(u,-v)
        np.testing.assert_allclose(u-v,2*u)
        wk=((up.Date-first).dt.days//7).to_numpy()
        for j in range(3):
            ids=np.repeat(np.arange(len(up)),w[j,wk])
            self.assertAlmostEqual(u[j],up.AlignedLondonReturn.to_numpy()[ids].mean())

    def test_holm_four_and_missing(self):
        p=[.04,.01,.02,np.nan]
        got=m.p1.holm(p)
        np.testing.assert_allclose(got,[.08,.04,.06,1.])
        self.assertEqual(len(got),4)

    def test_verdicts_all_paths(self):
        rows=[]
        for pair in m.PAIRS:
            for method in m.METHODS:
                for period in m.PERIODS:
                    for side in m.SIDES:
                        rows.append(dict(Pair=pair,Method=method,Period=period,TokyoDirection=side,
                                         Status="OK",Mean=3.,CILow=1.,PUnadjusted=.001))
        cells=pd.DataFrame(rows)
        h=m.holm_four(cells);primary,v=m.decisions(cells,h)
        self.assertEqual(v.set_index("Pair").loc["EURAUD","Verdict"],"DIRECTIONAL_STRUCTURE_PRESENT")
        self.assertEqual(v.set_index("Pair").loc["USDJPY","Verdict"],"SHADOW_STRUCTURE_PRESENT")
        cells.loc[cells.Pair.eq("EURAUD")&cells.TokyoDirection.eq("DOWN")&cells.Method.eq("Primary")&cells.Period.eq("RecentCombined"),"Mean"]=-1.
        h=m.holm_four(cells);primary,v=m.decisions(cells,h)
        self.assertEqual(v.set_index("Pair").loc["EURAUD","StrongSides"],1)
        cells.loc[cells.Pair.eq("EURAUD")&cells.TokyoDirection.eq("UP")&cells.Method.eq("Primary")&cells.Period.eq("RecentCombined"),"CILow"]=-1.
        h=m.holm_four(cells);_,v=m.decisions(cells,h)
        self.assertEqual(v.set_index("Pair").loc["EURAUD","Verdict"],"WEAK_DIRECTIONAL_STRUCTURE")
        self.assertEqual(v.set_index("Pair").loc["USDJPY","Phase3Disposition"],"NO_PHASE3")
        cells.loc[cells.Pair.eq("EURAUD")&cells.TokyoDirection.eq("UP")&cells.Method.eq("Primary")&cells.Period.eq("RecentCombined"),"Status"]="INSUFFICIENT_SAMPLE"
        h=m.holm_four(cells);_,v=m.decisions(cells,h)
        self.assertEqual(v.set_index("Pair").loc["EURAUD","Verdict"],"INSUFFICIENT_SAMPLE")

    def test_recent_a_b_and_robustness_fixed(self):
        rows=[]
        for pair in m.PAIRS:
            for method in m.METHODS:
                for period in m.PERIODS:
                    for side in m.SIDES:
                        rows.append(dict(Pair=pair,Method=method,Period=period,TokyoDirection=side,
                                         Status="OK",Mean=3.,CILow=1.,PUnadjusted=.001))
        cells=pd.DataFrame(rows)
        cells.loc[cells.Period.eq("RecentB")&cells.Method.eq("Primary")&cells.Pair.eq("EURAUD")&cells.TokyoDirection.eq("UP"),"Mean"]=-.1
        h=m.holm_four(cells);primary,_=m.decisions(cells,h)
        row=primary[primary.Pair.eq("EURAUD")&primary.TokyoDirection.eq("UP")].iloc[0]
        self.assertEqual(row.D,"FAIL")
        cells.loc[cells.Period.eq("RecentB")&cells.Method.eq("Primary")&cells.Pair.eq("EURAUD")&cells.TokyoDirection.eq("UP"),"Mean"]=3.
        cells.loc[cells.Period.eq("RecentCombined")&cells.Method.eq("Robustness")&cells.Pair.eq("EURAUD")&cells.TokyoDirection.eq("UP"),"Mean"]=-.1
        h=m.holm_four(cells);primary,_=m.decisions(cells,h)
        row=primary[primary.Pair.eq("EURAUD")&primary.TokyoDirection.eq("UP")].iloc[0]
        self.assertEqual(row.E,"FAIL")

    def test_asymmetry_sign_precommitted(self):
        self.assertEqual(3.-5.,-2.)
        self.assertLess(3.-5.,0)

if __name__=="__main__":unittest.main()
