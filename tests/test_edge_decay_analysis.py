import sys
import unittest
import tempfile
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"/"research"))
from edge_decay_analysis import classify, metrics, select_period, load_baseline, analyze

def m(avg="0.1", pf="1.2", n=30):
    return dict(AvgR=D(avg), PF=D(pf), Trades=n)

def row(r, time="2022-01-01 00:00:00", reason="TimeExit"):
    return dict(R=D(r), EntryTime=time, CloseTime=time, StrategyNo=1, Strategy="test", ExitReason=reason)

class Rules(unittest.TestCase):
    def test_lost_zero_and_priority(self):
        self.assertEqual(classify(m(), m("0"), m("0"), m("0", "1")), "EDGE LOST")
    def test_historical_pf_strict_boundary(self):
        self.assertEqual(classify(m(pf="1.05"), m("0"), m("0"), m("0","1")), "EDGE DECAY")
    def test_decay_inclusive_half(self):
        self.assertEqual(classify(m(), m("0.05"), m("0.05"), m("0.05","1.1")), "EDGE DECAY")
        self.assertEqual(classify(m(), m("0.05"), m("0.05"), m("0.0500000001","1.1")), "STABLE")
    def test_strict_persistence_and_pf(self):
        self.assertEqual(classify(m(), m(), m("0.01"), m("0.05","1.1")), "STABLE")
        self.assertEqual(classify(m(), m("0.01"), m("0.01"), m("0.01","1.2")), "STABLE")
    def test_sample_boundaries_and_priority(self):
        self.assertEqual(classify(m(), m("0",n=15), m("0",n=15), m("0","1",30)), "EDGE LOST")
        for a,b,r in ((14,15,30),(15,14,30),(15,15,29)):
            self.assertEqual(classify(m(),m("0",n=a),m("0",n=b),m("0","1",r)), "INSUFFICIENT SAMPLE")
    def test_no_extra_decay_eligibility(self):
        self.assertEqual(classify(m("-0.1","0.9"),m("-0.2"),m("-0.2"),m("-0.2","0.8")), "EDGE DECAY")
    def test_undefined_and_infinite_pf(self):
        h=m(); h["PF"]=None
        self.assertEqual(classify(h,m("0"),m("0"),m("0","1")), "STABLE")
        self.assertEqual(classify(m(pf="Infinity"),m("0"),m("0"),m("0","1")), "EDGE LOST")
    def test_period_boundaries(self):
        rows=[row("1",x+" 00:00:00") for x in ("2021-12-31","2022-01-01","2023-12-31","2024-01-01","2025-12-31","2026-01-01","2026-09-09","2026-09-10")]
        self.assertEqual(len(select_period(rows,"2022-01-01","2024-01-01")),2)
        self.assertEqual(len(select_period(rows,"2024-01-01","2026-01-01")),2)
        self.assertEqual(len(select_period(rows,"2026-01-01","2026-09-10")),2)
    def test_metrics_drawdown_streak_rates(self):
        rows=[row(v, f"2022-01-0{i+1} 00:00:00", reason) for i,(v,reason) in enumerate([("-1","SL"),("-1","SL"),("0","TimeExit"),("-1","Other"),("4","TP")])]
        a=metrics(list(reversed(rows)))
        self.assertEqual((a["MaxDDR"],a["MaxLosingStreak"],a["TotalR"]), (D(3),2,D(1)))
        self.assertEqual(a["AvgR"],D("0.2")); self.assertEqual(a["WinRate"],D("0.2"))
        self.assertEqual(a["PF"],D(4)/3)
        self.assertEqual(a["AvgWinR"],D(4)); self.assertEqual(a["AvgLossR"],D(-1))
        self.assertEqual(a["SLRate"]+a["TPRate"]+a["TimeRate"]+a["OtherRate"],1)
        self.assertEqual(metrics([row("1")])["PF"],D("Infinity"))
        self.assertIsNone(metrics([row("0")])["PF"])
        self.assertIsNone(metrics([])["AvgR"])
    def test_monitor_cannot_change_classification(self):
        rows=[row("0.1","2020-01-01 00:00:00")]+[row("0","2022-01-01 00:00:00") for _ in range(15)]+[row("0","2024-01-01 00:00:00") for _ in range(15)]
        before=analyze(rows)["final_classification"][0]["Classification"]
        for value in ("-99999","99999"):
            self.assertEqual(analyze(rows+[row(value,"2026-01-01 00:00:00")])["final_classification"][0]["Classification"], before)
    def test_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.csv"; p.write_text("bad")
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                load_baseline(p)

if __name__ == "__main__":
    unittest.main()
