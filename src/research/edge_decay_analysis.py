"""Precommitted diagnostic rules; consumes a frozen log, never backtests."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
import pandas as pd

BASELINE_HASH = "cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359"
PLAN_COMMIT = "402fc221b307985b8eb75abcc84bc3b0888400b5"
BRANCH = "research/edge-decay-validation"
PERIODS = {
    "Historical": ("2015-01-01", "2022-01-01"),
    "RecentA": ("2022-01-01", "2024-01-01"),
    "RecentB": ("2024-01-01", "2026-01-01"),
    "RecentCombined": ("2022-01-01", "2026-01-01"),
    "Monitor2026": ("2026-01-01", "2026-09-10"),
}
D = Decimal

def select_period(rows, start, end):
    return [r for r in rows if start <= r["EntryTime"][:10] < end]

def load_baseline(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_HASH:
        raise ValueError("Baseline SHA-256 mismatch")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if len(rows) != 16298:
        raise ValueError("Expected 16,298 trades")
    identities = {(int(r["StrategyNo"]), r["Strategy"]) for r in rows}
    if len(identities) != 28 or sorted(n for n, _ in identities) != list(range(1, 29)):
        raise ValueError("Expected 28 unique strategy identities")
    if len({(r["StrategyNo"], r["EntryTime"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate strategy entry")
    for r in rows:
        r["StrategyNo"] = int(r["StrategyNo"])
        r["R"] = D(r["R"])
        if not r["R"].is_finite():
            raise ValueError("Non-finite R")
        for k in ("EntryTime", "CloseTime"):
            t = datetime.fromisoformat(r[k])
            if t.tzinfo is not None:
                raise ValueError("Expected naive JST timestamps")
        if r["CloseTime"] < r["EntryTime"]:
            raise ValueError("Close precedes entry")
        if abs(r["R"] - D(r["Pips"]) / D(r["SL"])) > D("0.00000001"):
            raise ValueError("R integrity failure")
    if len(select_period(rows, "2015-01-01", "2026-09-10")) != len(rows):
        raise ValueError("Trades outside fixed coverage")
    return rows

def metrics(rows):
    ordered = sorted(rows, key=lambda r: (r["CloseTime"], r["EntryTime"], r["StrategyNo"]))
    rs = [r["R"] for r in ordered]
    n = len(rs)
    wins, losses = [r for r in rs if r > 0], [r for r in rs if r < 0]
    gain, loss = sum(wins, D(0)), -sum(losses, D(0))
    total = sum(rs, D(0))
    pf = gain / loss if loss else (D("Infinity") if gain else None)
    equity = peak = dd = D(0)
    streak = longest = 0
    for r in rs:
        equity += r
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
        streak = streak + 1 if r < 0 else 0
        longest = max(longest, streak)
    reasons = {k: sum(r["ExitReason"] == v for r in rows)
               for k, v in (("SL", "SL"), ("TP", "TP"), ("Time", "TimeExit"))}
    reasons["Other"] = n - sum(reasons.values())
    result = dict(Trades=n, TotalR=total, AvgR=total/n if n else None, PF=pf,
                  WinRate=D(len(wins))/n if n else None,
                  AvgWinR=gain/len(wins) if wins else None,
                  AvgLossR=-loss/len(losses) if losses else None,
                  MaxDDR=dd, MaxLosingStreak=longest)
    for reason, count in reasons.items():
        result[reason+"Count"] = count
        result[reason+"Rate"] = D(count)/n if n else None
    return result

def classify(h, a, b, r):
    # This API deliberately has no 2026 argument.
    if r["Trades"] < 30 or a["Trades"] < 15 or b["Trades"] < 15:
        return "INSUFFICIENT SAMPLE"
    avgs = [x["AvgR"] for x in (h, a, b, r)]
    persistent = all(v is not None for v in avgs) and a["AvgR"] < h["AvgR"] and b["AvgR"] < h["AvgR"]
    pfs = h["PF"] is not None and r["PF"] is not None
    if persistent and pfs and h["AvgR"] > 0 and h["PF"] > D("1.05") and r["AvgR"] <= 0 and r["PF"] <= 1:
        return "EDGE LOST"
    if persistent and pfs and r["AvgR"] <= h["AvgR"] * D("0.50") and r["PF"] < h["PF"]:
        return "EDGE DECAY"
    return "STABLE"

def analyze(rows):
    summary, yearly, final = [], [], []
    for number, name in sorted({(r["StrategyNo"], r["Strategy"]) for r in rows}):
        own = [r for r in rows if r["StrategyNo"] == number]
        period = {}
        for label, (start, end) in PERIODS.items():
            period[label] = metrics(select_period(own, start, end))
            summary.append(dict(StrategyNo=number, Strategy=name, Period=label, Start=start, EndExclusive=end, **period[label]))
        for year in range(2015, 2027):
            end = "2026-09-10" if year == 2026 else str(year+1)+"-01-01"
            yearly.append(dict(StrategyNo=number, Strategy=name, Year=year,
                               **metrics(select_period(own, str(year)+"-01-01", end))))
        label = classify(*(period[k] for k in ("Historical", "RecentA", "RecentB", "RecentCombined")))
        f = dict(StrategyNo=number, Strategy=name, Classification=label)
        for p, m in period.items():
            for k in ("Trades", "AvgR", "TotalR", "PF"):
                f[p+"_"+k] = m[k]
        f["HistoricalEdgeConfirmed"] = period["Historical"]["AvgR"] is not None and period["Historical"]["PF"] is not None and period["Historical"]["AvgR"] > 0 and period["Historical"]["PF"] > D("1.05")
        f["UndefinedClassificationMetric"] = any(period[p][k] is None for p in ("Historical", "RecentA", "RecentB", "RecentCombined") for k in ("AvgR", "PF"))
        f["MonitorUsedForClassification"] = False
        f["AutomaticStop"] = False
        final.append(f)
    return {"summary": summary, "yearly": yearly, "final_classification": final}

def run(baseline, output_dir="/content"):
    rows = load_baseline(baseline)
    tables = analyze(rows)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, records in tables.items():
        p = out / ("strategy_edge_decay_"+name+".csv")
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        files[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    record = dict(BaselineSHA256=BASELINE_HASH, BaselineTrades=len(rows), Strategies=28,
                  Branch=BRANCH, PlanCommit=PLAN_COMMIT,
                  RunJST=datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),
                  Periods=json.dumps(PERIODS), PrimaryMetric="Avg R / Trade",
                  RulesDocument="docs/38_edge_decay_validation_plan.md",
                  RuleOrder="INSUFFICIENT SAMPLE > EDGE LOST > EDGE DECAY > STABLE",
                  BaselineRecalculated=False, LiveChanged=False, MonitorUsedForClassification=False,
                  FreshHoldout=False, CSVHashes=json.dumps(files, sort_keys=True))
    with (out/"strategy_edge_decay_run_record.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(record)); w.writeheader(); w.writerow(record)
    df = pd.DataFrame(tables["final_classification"])
    print("Edge Decay診断（停止指示ではありません）")
    print(df.Classification.value_counts().to_string())
    cols = ["Strategy", "Classification", "Historical_AvgR", "RecentA_AvgR", "RecentB_AvgR", "RecentCombined_AvgR", "Monitor2026_AvgR"]
    print(df[cols].to_string(index=False))
    print("2026は補助表示のみ。CSV出力:", out)
    return tables

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--output-dir", default="/content", type=Path)
    args = parser.parse_args()
    run(args.baseline, args.output_dir)
