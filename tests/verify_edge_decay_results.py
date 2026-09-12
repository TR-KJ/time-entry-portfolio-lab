"""Independent pandas/float aggregation audit of a generated fixed-log result set."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

def verify(baseline, output):
    assert hashlib.sha256(Path(baseline).read_bytes()).hexdigest() == "cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359"
    df = pd.read_csv(baseline, parse_dates=["EntryTime", "CloseTime"])
    assert len(df) == 16298 and df.Strategy.nunique() == 28
    output = Path(output)
    summary = pd.read_csv(output/"strategy_edge_decay_summary.csv")
    yearly = pd.read_csv(output/"strategy_edge_decay_yearly.csv")
    final = pd.read_csv(output/"strategy_edge_decay_final_classification.csv")
    assert len(summary) == 140 and len(yearly) == 336 and len(final) == 28
    def independent(sub):
        s = sub.sort_values(["CloseTime","EntryTime","StrategyNo"]).R
        n = len(s); w=s[s>0]; l=s[s<0]
        e = pd.concat([pd.Series([0.]), s.reset_index(drop=True)], ignore_index=True).cumsum()
        losing = s.lt(0)
        longest = losing.groupby((~losing).cumsum()).sum().max() if n else 0
        m=dict(Trades=n,TotalR=s.sum(),AvgR=s.mean(),PF=w.sum()/-l.sum() if len(l) else (np.inf if len(w) else np.nan),
               WinRate=len(w)/n if n else np.nan, AvgWinR=w.mean(),AvgLossR=l.mean(),
               MaxDDR=(e.cummax()-e).max(),MaxLosingStreak=longest)
        for reason,label in (("SL","SL"),("TP","TP"),("Time","TimeExit")):
            m[reason+"Count"]=sub.ExitReason.eq(label).sum()
        m["OtherCount"]=n-sum(m[k+"Count"] for k in ("SL","TP","Time"))
        for reason in ("SL","TP","Time","Other"):
            m[reason+"Rate"]=m[reason+"Count"]/n if n else np.nan
        return m
    calculated={}
    checked=0
    for _, r in summary.iterrows():
        sub=df.loc[df.StrategyNo.eq(r.StrategyNo)&df.EntryTime.ge(r.Start)&df.EntryTime.lt(r.EndExclusive)]
        m=independent(sub); calculated[(r.StrategyNo,r.Period)]=m
        for k,v in m.items():
            assert np.isclose(v,r[k],atol=1e-10,rtol=1e-10,equal_nan=True),(r.Strategy,k,v,r[k])
        checked+=1
    for _, r in yearly.iterrows():
        m=independent(df.loc[df.StrategyNo.eq(r.StrategyNo)&df.EntryTime.dt.year.eq(r.Year)])
        for k,v in m.items():
            assert np.isclose(v,r[k],atol=1e-10,rtol=1e-10,equal_nan=True),(r.Strategy,r.Year,k)
        checked+=1
    for _,r in final.iterrows():
        h,a,b,c=[calculated[(r.StrategyNo,p)] for p in ("Historical","RecentA","RecentB","RecentCombined")]
        insufficient=c["Trades"]<30 or min(a["Trades"],b["Trades"])<15
        lost=(h["AvgR"]>0 and h["PF"]>1.05 and c["AvgR"]<=0 and c["PF"]<=1 and max(a["AvgR"],b["AvgR"])<h["AvgR"])
        decay=(c["AvgR"]<=h["AvgR"]/2 and max(a["AvgR"],b["AvgR"])<h["AvgR"] and c["PF"]<h["PF"])
        expected="INSUFFICIENT SAMPLE" if insufficient else "EDGE LOST" if lost else "EDGE DECAY" if decay else "STABLE"
        assert r.Classification == expected
        for p in ("Historical","RecentA","RecentB","RecentCombined","Monitor2026"):
            for k in ("Trades","TotalR","AvgR","PF"):
                assert np.isclose(r[p+"_"+k],calculated[(r.StrategyNo,p)][k],atol=1e-10,rtol=1e-10,equal_nan=True)
    counts=summary.groupby("Period").Trades.sum().to_dict()
    assert {k:counts[k] for k in ("Historical","RecentCombined","Monitor2026")}==dict(Historical=9756,RecentCombined=5547,Monitor2026=995)
    assert counts["RecentA"]+counts["RecentB"]==counts["RecentCombined"]
    for p,anchor in (("Historical",768.488273),("RecentCombined",601.960585),("Monitor2026",19.818791)):
        assert abs(summary.loc[summary.Period.eq(p)].TotalR.sum()-anchor)<0.00000051
    assert (summary.OtherCount==0).all()
    report=dict(Status="PASS",MetricRowsChecked=checked,ClassificationsChecked=28,BaselineHashMatch=True,
                IndependentImplementation="pandas/numpy; no production-module import",Tolerance="atol=rtol=1e-10",
                Counts=final.Classification.value_counts().to_dict())
    print(json.dumps(report,indent=2))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True);p.add_argument("--output-dir",required=True)
    a=p.parse_args();verify(a.baseline,a.output_dir)
