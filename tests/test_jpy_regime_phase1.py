import unittest
import tempfile
from pathlib import Path
from decimal import Decimal as D
import pandas as pd
import jpy_regime_phase1 as m

def bars(values):
    return pd.DataFrame({"Close":values},index=pd.date_range("2020-01-01 23:59",periods=len(values)))
def targets(entry):
    return [dict(StrategyNo=n,Strategy=name,Direction=g,Pair=name.split("_")[1],EntryTime=entry,R=D("0.1"),CloseTime=entry,ExitReason="TimeExit") for g,ns in m.GROUPS.items() for n,name in ns.items()]
class Tests(unittest.TestCase):
    def test_indices(self):
        f=m.daily_features(bars(list(range(100,340))))
        self.assertEqual(f[125]["Primary"],m.INS)
        self.assertEqual(f[126]["Return126"],D(226)/100-1)
        self.assertEqual(f[218]["Robustness"],m.INS)
        self.assertEqual(f[219]["MA200"],sum(map(D,range(120,320)))/200)
        self.assertEqual(f[219]["MA200Lag20"],sum(map(D,range(100,300)))/200)
        self.assertEqual(f[219]["Robustness"],"JPY_WEAK_TREND")
    def test_zero_and_falling(self):
        f=m.daily_features(bars([100]*240))
        self.assertEqual(f[-1]["Primary"],"NEUTRAL_ZERO")
        self.assertEqual(f[-1]["Robustness"],"NEUTRAL_MIXED")
        f=m.daily_features(bars(list(range(340,100,-1))))
        self.assertEqual(f[-1]["Robustness"],"JPY_STRONG_TREND")
    def test_no_lookahead(self):
        b=bars(list(range(100,340)))
        entry="2020-08-01 00:00:00"
        a=m.assign(targets(entry),m.daily_features(b))
        b.loc[b.index.normalize()>=pd.Timestamp("2020-08-01"),"Close"]=9999
        self.assertEqual(a,m.assign(targets(entry),m.daily_features(b)))
        self.assertEqual(a[0]["DailyDate"],pd.Timestamp("2020-07-31"))
    def test_weekend(self):
        b=pd.DataFrame({"Close":[100,101,102]},index=pd.to_datetime(["2020-01-03 23:59","2020-01-04 06:59","2020-01-06 23:59"]))
        a=m.assign(targets("2020-01-06 08:00:00"),m.daily_features(b))
        self.assertEqual(a[0]["DailyDate"],pd.Timestamp("2020-01-04"))
    def test_timezone(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"m.csv"
            p.write_text("<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n2020.01.02\t17:00:00\t100\t101\t99\t100\n2020.07.02\t18:00:00\t100\t101\t99\t100\n")
            from daily_stop_baseline_revalidation import load_pair
            b=load_pair([p],"USDJPY")
            self.assertEqual(list(b.index),list(pd.to_datetime(["2020-01-03","2020-07-03"])))
    def test_sample_and_empty(self):
        rows=[]
        for reg,count,value in [("JPY_WEAK",20,D("0.2")),("JPY_STRONG",20,D("-0.1"))]:
            for _ in range(count):
                r=targets("2020-01-01")[0];r.update(Group="Long",Primary=reg,R=value);rows.append(r)
        cells,summary,decision=m.summarize(rows,"Long","primary","FULL")
        self.assertEqual(decision["Support"],"SUPPORTED")
        self.assertEqual(decision["EqualWeightedDelta"],D("0.3"))
        self.assertEqual(decision["EligibleStrategies"],1)
        m.verify_aggregation(rows,cells)
        rows.pop()
        self.assertEqual(m.summarize(rows,"Long","primary","FULL")[2]["Support"],"UNDETERMINED")
        self.assertEqual(m.summarize([],"Long","primary","FULL")[0][0]["Flag"],"LOW_SAMPLE")
    def test_identity(self):
        rows=targets("2020-01-01");rows[0]["Direction"]="Short"
        with self.assertRaises(ValueError):m.assign(rows,[])
if __name__=="__main__":unittest.main()
