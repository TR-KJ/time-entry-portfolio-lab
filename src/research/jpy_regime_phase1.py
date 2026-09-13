"""Frozen Phase 1 diagnostic; never generates trades or changes live settings."""
import argparse
import csv
import hashlib
import json
import math
from bisect import bisect_left
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
from edge_decay_analysis import load_baseline, metrics, BASELINE_HASH
from daily_stop_baseline_revalidation import MANIFEST_NAMES, load_pair

PLAN_COMMIT = "11541f39730fcbae7dd7dfb5fc82c95bf7c18652"
BRANCH = "research/jpy-regime-dependency-phase1"
LONG = {1:"1_EJ_Log1",2:"2_EJ_NightBlitz_20",3:"3_EJ_NightBlitz_21",4:"4_GJ_Port_Log1",6:"6_GJ_Old_Mon",7:"7_GJ_Mon_Blitz",8:"8_AJ_Core1",13:"13_UJ_Fix_MidWeek",16:"16_UJ_T10A",26:"26_AJ_China_Demand"}
SHORT = {5:"5_GJ_Port_Log2",9:"9_AJ_Core2",10:"10_AJ_SatA",11:"11_AJ_SatB",12:"12_UJ_Short_Core",14:"14_UJ_Sat_3rd",15:"15_UJ_Sat_Aug"}
GROUPS = {"Long":LONG,"Short":SHORT}
PERIODS = {"FULL":("2015-01-01","2026-09-10"),"Historical":("2015-01-01","2022-01-01"),"RecentA":("2022-01-01","2024-01-01"),"RecentB":("2024-01-01","2026-01-01"),"Monitor2026":("2026-01-01","2026-09-10")}
INS = "INSUFFICIENT_REGIME_HISTORY"
REGIMES = {"primary":("JPY_WEAK","JPY_STRONG","NEUTRAL_ZERO"),"robustness":("JPY_WEAK_TREND","JPY_STRONG_TREND","NEUTRAL_MIXED")}

def daily_features(bars):
    if bars.empty or bars.index.has_duplicates or not bars.index.is_monotonic_increasing:
        raise ValueError("Invalid M1 index")
    if bars.index.tz is not None:
        raise ValueError("Expected naive JST")
    if not all(math.isfinite(float(c)) and c > 0 for c in bars.Close):
        raise ValueError("Invalid Close")
    last = bars.groupby(bars.index.normalize()).tail(1)
    closes = [D(str(c)) for c in last.Close]
    prefix = [D(0)]
    for c in closes: prefix.append(prefix[-1]+c)
    result = []
    for i, ((stamp, row), c) in enumerate(zip(last.iterrows(), closes)):
        date = stamp.normalize()
        r = dict(DailyDate=date, LastM1=stamp, AvailableAt=date+pd.Timedelta(days=1),
                 Index=i, Close=c, Return126=None, MA200=None, MA200Lag20=None,
                 Primary=INS, Robustness=INS)
        if i >= 126:
            r["Return126"] = c/closes[i-126]-1
            r["Primary"] = "JPY_WEAK" if c>closes[i-126] else "JPY_STRONG" if c<closes[i-126] else "NEUTRAL_ZERO"
        if i >= 199: r["MA200"] = (prefix[i+1]-prefix[i-199])/200
        if i >= 219:
            lag = (prefix[i-19]-prefix[i-219])/200
            ma = r["MA200"]
            r["MA200Lag20"] = lag
            r["Robustness"] = "JPY_WEAK_TREND" if c>ma>lag else "JPY_STRONG_TREND" if c<ma<lag else "NEUTRAL_MIXED"
        result.append(r)
    return result

def assign(rows, daily):
    dates = [r["DailyDate"] for r in daily]
    out = []
    for row in rows:
        n = row["StrategyNo"]
        if n not in LONG and n not in SHORT: continue
        group = "Long" if n in LONG else "Short"
        if row["Strategy"] != GROUPS[group][n] or row["Direction"] != group or row["Pair"] != row["Strategy"].split("_")[1]:
            raise ValueError("Fixed identity mismatch")
        entry = pd.Timestamp(row["EntryTime"])
        i = bisect_left(dates, entry.normalize())-1
        feat = daily[i] if i >= 0 else dict(Primary=INS,Robustness=INS)
        if i >= 0:
            assert feat["AvailableAt"] <= entry
            assert feat["LastM1"]+pd.Timedelta(minutes=1) <= entry
        out.append(dict(row, Group=group, **feat))
    if set(r["StrategyNo"] for r in out) != set(LONG)|set(SHORT):
        raise ValueError("Missing fixed target strategy")
    return out

def stat(rows):
    m = metrics(rows)
    return {k:m[k] for k in ("Trades","TotalR","AvgR","PF","WinRate","AvgWinR","AvgLossR")}

def summarize(rows, group, method, period):
    names = GROUPS[group]
    weak,strong,neutral = REGIMES[method]
    key = method.title()
    own = [r for r in rows if r["Group"]==group]
    cells, paired = [], []
    for n,name in names.items():
        ms = {reg:stat([r for r in own if r["StrategyNo"]==n and r[key]==reg]) for reg in (weak,strong,neutral)}
        delta = ms[weak]["AvgR"]-ms[strong]["AvgR"] if ms[weak]["Trades"] and ms[strong]["Trades"] else None
        eligible = min(ms[weak]["Trades"],ms[strong]["Trades"])>=20
        if eligible: paired.append((n,ms[weak]["AvgR"],ms[strong]["AvgR"]))
        for reg,m in ms.items():
            cells.append(dict(Group=group,Method=method,Period=period,StrategyNo=n,Strategy=name,Regime=reg,
                              **m,Flag="LOW_SAMPLE" if m["Trades"]<20 else "",EligiblePair=eligible,WeakMinusStrongAvgR=delta))
    summaries = []
    pooled = {}
    for reg in (weak,strong,neutral):
        pooled[reg] = stat([r for r in own if r[key]==reg])
    pdiff = pooled[weak]["AvgR"]-pooled[strong]["AvgR"] if pooled[weak]["Trades"] and pooled[strong]["Trades"] else None
    for reg,m in pooled.items():
        summaries.append(dict(Group=group,Method=method,Period=period,Aggregation="trade_weighted",Regime=reg,**m,
                              EligibleStrategies=None,EligibleIDs="",WeakMinusStrongAvgR=pdiff))
    ew = sum((p[1] for p in paired),D(0))/len(paired) if paired else None
    es = sum((p[2] for p in paired),D(0))/len(paired) if paired else None
    ediff = ew-es if paired else None
    for reg,avg in ((weak,ew),(strong,es)):
        summaries.append(dict(Group=group,Method=method,Period=period,Aggregation="strategy_equal_weighted",Regime=reg,
                              Trades=None,TotalR=None,AvgR=avg,PF=None,WinRate=None,AvgWinR=None,AvgLossR=None,
                              EligibleStrategies=len(paired),EligibleIDs="|".join(str(p[0]) for p in paired),WeakMinusStrongAvgR=ediff))
    positive = sum(w>s for _,w,s in paired)
    support = None if not paired or pdiff is None else pdiff>0 and ediff>0 and positive>len(paired)/2
    decision = dict(Group=group,Method=method,Period=period,PooledDelta=pdiff,EqualWeightedDelta=ediff,
                    EligibleStrategies=len(paired),PositiveStrategies=positive,
                    Support="UNDETERMINED" if support is None else "SUPPORTED" if support else "NOT_SUPPORTED",
                    ControlOnly=group=="Short")
    return cells,summaries,decision

def verify_aggregation(rows, cells):
    # Independent math.fsum route, directly selecting original assigned R values.
    for cell in cells:
        vals = [float(r["R"]) for r in rows if r["StrategyNo"]==cell["StrategyNo"]
                and r[cell["Method"].title()]==cell["Regime"]]
        assert len(vals)==cell["Trades"]
        assert math.isclose(math.fsum(vals),float(cell["TotalR"]),abs_tol=1e-10)
        if vals: assert math.isclose(math.fsum(vals)/len(vals),float(cell["AvgR"]),abs_tol=1e-12)

def save(path, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def run(baseline, m1_root, output_dir="/content", implementation_sha="UNRECORDED"):
    if len(implementation_sha)!=40: raise ValueError("Provide verified implementation commit SHA")
    rows = load_baseline(baseline)
    paths=[]
    for name in MANIFEST_NAMES["USDJPY"]:
        hits=list(Path(m1_root).rglob(name))
        if len(hits)!=1: raise ValueError(f"Expected one audited file: {name}; found {len(hits)}")
        paths.append(hits[0])
    input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    bars=load_pair(paths,"USDJPY")
    daily=daily_features(bars)
    assigned=assign(rows,daily)
    tables={"strategy_primary":[],"strategy_robustness":[],"group_summary":[],"period_summary":[],"decision":[],"coverage":[]}
    for period,(start,end) in PERIODS.items():
        selected=[r for r in assigned if start<=r["EntryTime"][:10]<end]
        for group in GROUPS:
            for method in REGIMES:
                cells,summary,decision=summarize(selected,group,method,period)
                verify_aggregation(selected,cells)
                if period=="FULL":
                    tables["strategy_"+method]+=cells
                    tables["group_summary"]+=summary
                    tables["decision"].append(decision)
                else: tables["period_summary"]+=cells+summary
                own=[r for r in selected if r["Group"]==group]
                for reg in (*REGIMES[method],INS):
                    tables["coverage"].append(dict(Period=period,Group=group,Method=method,Regime=reg,
                        Trades=sum(r[method.title()]==reg for r in own),TotalTargetTrades=len(own)))
    tables["regime_assignments_audit"]=[{k:r.get(k) for k in ("StrategyNo","Strategy","EntryTime","Group","DailyDate","LastM1","AvailableAt","Index","Close","Return126","MA200","MA200Lag20","Primary","Robustness")} for r in assigned]
    tables["daily_audit"]=daily
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name,data in tables.items():
        path=out/("jpy_regime_phase1_"+name+".csv");save(path,data)
        hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    record=dict(Status="COMPLETED",PlanCommit=PLAN_COMMIT,ImplementationCommit=implementation_sha,Branch=BRANCH,
                RunJST=datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(),BaselineSHA256=BASELINE_HASH,
                BaselineTrades=len(rows),TargetTrades=len(assigned),DailyRows=len(daily),FirstDaily=str(daily[0]["DailyDate"]),LastDaily=str(daily[-1]["DailyDate"]),
                InputHashes=json.dumps(input_hashes),OutputHashes=json.dumps(hashes),
                BaselineRecalculated=False,LiveChanged=False,FreshHoldout=False,IndependentAggregation="PASS")
    save(out/"jpy_regime_phase1_run_record.csv",[record])
    for name in ("decision","group_summary","strategy_primary","strategy_robustness","coverage"):
        print("\n"+name);print(pd.DataFrame(tables[name]).to_string(index=False))
    return tables

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True);p.add_argument("--m1-root",required=True)
    p.add_argument("--output-dir",default="/content");p.add_argument("--implementation-sha",required=True)
    a=p.parse_args();run(a.baseline,a.m1_root,a.output_dir,a.implementation_sha)
