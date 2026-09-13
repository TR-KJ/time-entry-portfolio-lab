"""Independent Decimal audit of exported features, cell and group summaries."""
import csv
from decimal import Decimal as D
from pathlib import Path
def read(p): return list(csv.DictReader(Path(p).open()))
def verify(out,baseline):
    out=Path(out)
    daily=read(out/"jpy_regime_phase1_daily_audit.csv")
    for i,r in enumerate(daily):
        c=[D(x["Close"]) for x in daily[max(0,i-219):i+1]]
        if i>=126: assert D(r["Return126"])==c[-1]/c[-127]-1
        if i>=199: assert D(r["MA200"])==sum(c[-200:])/200
        if i>=219: assert D(r["MA200Lag20"])==sum(c[:200])/200
    trades={(r["StrategyNo"],r["EntryTime"]):D(r["R"]) for r in read(baseline)}
    audit=read(out/"jpy_regime_phase1_regime_assignments_audit.csv")
    for r in audit:
        if r["DailyDate"]:
            assert r["DailyDate"][:10]<r["EntryTime"][:10]
            assert r["AvailableAt"]<=r["EntryTime"]
    groups=read(out/"jpy_regime_phase1_group_summary.csv")
    for method in ("primary","robustness"):
        cells=read(out/("jpy_regime_phase1_strategy_"+method+".csv"))
        for cell in cells:
            vals=[trades[r["StrategyNo"],r["EntryTime"]] for r in audit if r["StrategyNo"]==cell["StrategyNo"] and r[method.title()]==cell["Regime"]]
            assert len(vals)==int(cell["Trades"])
            assert sum(vals,D(0))==D(cell["TotalR"])
        for g in [r for r in groups if r["Method"]==method]:
            if g["Aggregation"]=="trade_weighted":
                vals=[trades[r["StrategyNo"],r["EntryTime"]] for r in audit if r["Group"]==g["Group"] and r[method.title()]==g["Regime"]]
                assert len(vals)==int(g["Trades"])
                assert sum(vals,D(0))==D(g["TotalR"])
                if vals: assert sum(vals,D(0))/len(vals)==D(g["AvgR"])
            elif g["EligibleIDs"]:
                ids=g["EligibleIDs"].split("|")
                vals=[D(c["AvgR"]) for c in cells if c["StrategyNo"] in ids and c["Regime"]==g["Regime"]]
                assert len(vals)==len(ids)
                assert sum(vals)/len(vals)==D(g["AvgR"])
    print("PASS: independent Decimal daily windows, assignments, cells, pooled and equal-weighted aggregation")
if __name__=="__main__":
    import sys
    verify(*sys.argv[1:])
