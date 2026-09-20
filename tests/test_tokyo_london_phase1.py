"""Synthetic validation only; never computes Phase 2."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

P=Path(__file__).resolve().parents[1]/"src/research/tokyo_london_phase1.py"
spec=importlib.util.spec_from_file_location("tl",P)
tl=importlib.util.module_from_spec(spec);spec.loader.exec_module(tl)

class Phase1Tests(unittest.TestCase):
    def test_timezone_boundaries(self):
        for day,utc_hour,london_hour in [
            ("2026-03-27",7,7),("2026-03-30",6,7),
            ("2025-10-24",6,7),("2025-10-27",7,7)]:
            u=tl.to_utc([pd.Timestamp(day+" 09:00")])[0]
            self.assertEqual(u.hour,utc_hour)
            self.assertEqual(u.tz_convert("Europe/London").hour,london_hour)
            self.assertEqual(u.tz_convert("Asia/Tokyo").hour,utc_hour+9)
        u=tl.to_utc([pd.Timestamp("2026-03-29 03:30")])[0]
        self.assertEqual(str(u.tz_convert("Europe/Helsinki")),"2026-03-29 04:00:00+03:00")
        raw=pd.to_datetime(["2025-10-26 03:00","2025-10-26 03:30","2025-10-26 03:00","2025-10-26 03:30"])
        u=tl.to_utc(raw)
        self.assertTrue(u.is_monotonic_increasing)
        self.assertEqual((u[-1]-u[0]).total_seconds(),5400)

    def test_exact_endpoints_and_no_overlap(self):
        e=tl.endpoints()
        self.assertEqual(len(e),len(pd.bdate_range("2015-01-01","2026-09-09")))
        for name,zone,hour in [("Tokyo09","Asia/Tokyo",9),("Tokyo15","Asia/Tokyo",15),
                               ("London08","Europe/London",8),("London11","Europe/London",11)]:
            local=e[name].dt.tz_convert(zone)
            self.assertTrue(local.dt.hour.eq(hour).all())
            self.assertTrue(local.dt.minute.eq(0).all())
            self.assertTrue(local.dt.tz_localize(None).dt.normalize().equals(e.Date))
        self.assertTrue((e.Tokyo15<e.London08).all())
        self.assertTrue((e.London11-e.London08).eq(pd.Timedelta(hours=3)).all())
        # An adjacent 08:01 bar must never satisfy exact 08:00.
        t=e.London08.iloc[0]
        s=pd.Series([123.],index=pd.DatetimeIndex([t+pd.Timedelta(minutes=1)]))
        self.assertTrue(np.isnan(s.reindex([t]).iloc[0]))

    def test_pips(self):
        for pair in tl.PAIRS:
            self.assertAlmostEqual(tl.pip(pair),.01 if pair.endswith("JPY") else .0001)
            self.assertAlmostEqual((2*tl.pip(pair))/tl.pip(pair),2.)

    def test_regression(self):
        x=np.arange(100.)-50;y=3-.25*x
        r=tl.ols(x,y)
        self.assertAlmostEqual(r["Alpha"],3)
        self.assertAlmostEqual(r["Beta"],-.25)
        self.assertAlmostEqual(r["PearsonR"],-1)
        self.assertAlmostEqual(r["R2"],1)
        self.assertTrue(np.isnan(tl.ols([1,1],[2,3])["Beta"]))
        self.assertTrue(np.isnan(tl.ols([],[])["Beta"]))

    def test_holm_independent(self):
        p=np.array([.03,.001,.02,.05,np.nan,.001])
        actual=tl.holm(p)
        order=sorted(range(len(p)),key=lambda i:p[i] if np.isfinite(p[i]) else 1)
        expected=np.zeros(len(p));running=0.
        for rank,i in enumerate(order):
            running=max(running,(len(p)-rank)*(p[i] if np.isfinite(p[i]) else 1))
            expected[i]=min(1,running)
        np.testing.assert_array_equal(actual,expected)
        np.testing.assert_allclose(tl.holm([.01,.04,.03]),[.03,.06,.06])

    def test_bootstrap_ci_independent_full_replicates(self):
        dates=pd.bdate_range("2020-01-01","2020-06-30")
        rng=np.random.default_rng(9)
        g=pd.DataFrame({"Date":dates,"X":rng.normal(size=len(dates))})
        g["Y"]=-.2*g.X+rng.normal(size=len(g))
        first,w=tl.week_weights("2020-01-01","2020-06-30")
        beta=tl.ols(g.X,g.Y)["Beta"]
        ci,slopes,ok=tl.bootstrap(g,first,w,beta)
        wk=((g.Date-first).dt.days//7).to_numpy()
        independently=[]
        for weights in w:
            ids=np.repeat(np.arange(len(g)),weights[wk])
            fit=np.linalg.lstsq(np.column_stack([np.ones(len(ids)),g.X.to_numpy()[ids]]),g.Y.to_numpy()[ids],rcond=None)[0]
            independently.append(fit[1])
        np.testing.assert_allclose(slopes,independently,atol=1e-12)
        np.testing.assert_allclose([ci["CILow"],ci["CIHigh"]],np.quantile(independently,[.025,.975]),atol=1e-12)
        self.assertEqual(ci["PUnadjusted"],(1+sum(abs(v-beta)>=abs(beta) for v in independently))/5001)
        np.testing.assert_array_equal(w,tl.week_weights("2020-01-01","2020-06-30")[1])

    def test_gate_sample_denominator_and_sign(self):
        rows=[]
        for pair in tl.PAIRS:
            for method in ["Primary","Robustness"]:
                for per in tl.PERIODS:
                    rows.append(dict(Pair=pair,Method=method,Period=per,Status="OK",
                                     Beta=-.2,CILow=-.3,CIHigh=-.1,PUnadjusted=.001))
        df=pd.DataFrame(rows)
        self.assertTrue(tl.verdicts(df).Verdict.eq("REVERSAL_SUPPORTED").all())
        df.loc[df.Period.isin(["RecentA","RecentB"]),"Status"]="INSUFFICIENT_SAMPLE"
        self.assertTrue(tl.verdicts(df).D.eq("FAIL").all())
        self.assertTrue(tl.verdicts(df).Verdict.eq("NOT_SUPPORTED").all())
        df.loc[:,"Status"]="OK"
        df.loc[df.Method.eq("Robustness"),"Beta"]=.2
        self.assertTrue(tl.verdicts(df).E.eq("FAIL").all())


    def test_ingestion_missing_bar_and_future_invariance(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"fixture.csv"
            stamps=["2026.01.05\t02:00:00","2026.01.05\t08:00:00",
                    "2026.01.05\t10:00:00","2026.01.05\t13:00:00","2026.01.05\t13:01:00"]
            def write(stamps,values):
                p.write_text("<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n"+
                    "\n".join(t+"\t"+"\t".join([str(v)]*4) for t,v in zip(stamps,values))+"\n")
                raw=pd.to_datetime([s.replace("\t"," ") for s in stamps],format="%Y.%m.%d %H:%M:%S")
                m=pd.DataFrame([dict(Symbol="USDJPY",Filename=p.name,SHA256=tl.sha(p),
                    Rows=len(values),FirstRaw=str(raw[0]),LastRaw=str(raw[-1]))])
                return tl.load_pair("USDJPY",m,{p.name:p})[0]
            d=write(stamps,[100,101,102,103,999])
            a=d[d.Date.eq("2026-01-05")].set_index("Method")
            self.assertAlmostEqual(a.loc["Primary","X"],100)
            self.assertAlmostEqual(a.loc["Robustness","X"],200)
            self.assertAlmostEqual(a.loc["Primary","Y"],100)
            altered=write(stamps,[100,101,102,103,1])
            pd.testing.assert_frame_equal(d,altered)
            missing=write([stamps[i] for i in [0,2,3,4]],[100,102,103,999])
            z=missing[missing.Date.eq("2026-01-05")].set_index("Method")
            self.assertFalse(z.loc["Primary","Valid"])
            self.assertEqual(z.loc["Primary","MissingReason"],"Tokyo15")
            self.assertTrue(z.loc["Robustness","Valid"])

if __name__=="__main__": unittest.main()
