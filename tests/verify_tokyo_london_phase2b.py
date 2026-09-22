"""Independent verification for the preregistered directional cells."""
from pathlib import Path
from decimal import Decimal
import argparse,sys,math
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src/research"))
import tokyo_london_phase2b as m

def verify(out,daily_path):
    out=Path(out);pre=m.PREFIX
    if m.p1.sha(daily_path)!=m.P2_DAILY_HASH:raise ValueError("Phase2 daily hash mismatch")
    daily=pd.read_csv(daily_path,
                      float_precision="round_trip",parse_dates=["Date","ReferenceStart","ReferenceEnd"])
    daily=daily[daily.Pair.isin(m.PAIRS)]
    cells=pd.read_csv(out/(pre+"period_cells.csv"))
    primary=pd.read_csv(out/(pre+"primary_cells.csv"))
    asym=pd.read_csv(out/(pre+"asymmetry_summary.csv"))
    multiple=pd.read_csv(out/(pre+"multiple_comparison.csv"))
    verdict=pd.read_csv(out/(pre+"pair_verdict.csv"))
    coverage=pd.read_csv(out/(pre+"coverage.csv"))
    checks=[]
    def ck(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(dict(Check=name,Pass=True))
    def close(x,y):return bool(np.isclose(x,y,rtol=1e-10,atol=1e-10,equal_nan=True))
    def week_count(z):return len({(d.isocalendar().year,d.isocalendar().week) for d in z.Date})
    by={}
    for r in cells.itertuples():
        start,end=m.PERIODS[r.Period]
        subset=daily[daily.Pair.eq(r.Pair)&daily.Method.eq(r.Method)&daily.Date.between(start,end)]
        z=subset[subset.Eligible&subset.Q.eq(5)]
        z=z[z.X.gt(0)] if r.TokyoDirection=="UP" else z[z.X.lt(0)]
        vals=z.AlignedLondonReturn.to_numpy(float);n=len(vals)
        avg=math.fsum(vals)/n if n else np.nan;total=math.fsum(vals)
        median=float(np.median(vals)) if n else np.nan
        sd=math.sqrt(math.fsum((v-avg)**2 for v in vals)/(n-1)) if n>1 else np.nan
        status="OK" if n>=40 and week_count(z)>=20 and r.ValidBootstraps>=4750 else "INSUFFICIENT_SAMPLE"
        ck(f"Cell/{r.Pair}/{r.Method}/{r.Period}/{r.TokyoDirection}",
           r.N==n and r.CalendarWeeks==week_count(z) and close(r.Mean,avg)
           and close(r.Median,median) and close(r.Std,sd) and close(r.TotalAlignedPips,total)
           and close(r.PositiveRate,np.mean(vals>0) if n else np.nan)
           and close(r.NegativeRate,np.mean(vals<0) if n else np.nan)
           and close(r.ZeroRate,np.mean(vals==0) if n else np.nan)
           and r.Status==status)
        by[(r.Pair,r.Method,r.Period,r.TokyoDirection)]=r
    for r in asym.itertuples():
        up=by[(r.Pair,r.Method,r.Period,"UP")]
        down=by[(r.Pair,r.Method,r.Period,"DOWN")]
        ck(f"Asymmetry/{r.Pair}/{r.Method}/{r.Period}",close(r.UPMinusDOWN,up.Mean-down.Mean))
    for r in coverage.itertuples():
        subset=daily[daily.Pair.eq(r.Pair)&daily.Method.eq(r.Method)&daily.Date.between(*m.PERIODS[r.Period])]
        ck(f"Coverage/{r.Pair}/{r.Method}/{r.Period}",len(subset)==r.CandidateDays and
           int(subset.Valid.sum())==r.ValidEndpointDays and
           int(subset.ExclusionReason.eq("INSUFFICIENT_RANK_HISTORY").sum())==r.RankHistoryExcluded and
           int(subset.Eligible.eq(True).mul(subset.Q.eq(5)).sum())==r.EligibleQ5Days)
    # Alternate stable sorting and Holm step-down, including all four tests.
    tests=multiple.to_dict("records")
    ordered=sorted(enumerate(tests),key=lambda iv:iv[1]["PUnadjusted"] if np.isfinite(iv[1]["PUnadjusted"]) else 1)
    adjusted={};running=0.
    for pos,(i,r) in enumerate(ordered):
        p=r["PUnadjusted"] if np.isfinite(r["PUnadjusted"]) else 1.
        running=max(running,(4-pos)*p);adjusted[(r["Pair"],r["TokyoDirection"])]=min(1.,running)
    for r in tests:
        ck("Holm/"+r["Pair"]+"/"+r["TokyoDirection"],
           close(r["PAdjusted"],adjusted[(r["Pair"],r["TokyoDirection"])]))
    labels={}
    for r in primary.itertuples():
        p=by[(r.Pair,"Primary","RecentCombined",r.TokyoDirection)]
        a=by[(r.Pair,"Primary","RecentA",r.TokyoDirection)]
        b=by[(r.Pair,"Primary","RecentB",r.TokyoDirection)]
        robust=by[(r.Pair,"Robustness","RecentCombined",r.TokyoDirection)]
        gates=dict(A=p.Status=="OK" and p.Mean>=2.,
                   B=p.Status=="OK" and p.CILow>0,
                   C=p.Status=="OK" and adjusted[(r.Pair,r.TokyoDirection)]<=.05,
                   D=a.Status=="OK" and b.Status=="OK" and a.Mean>0 and b.Mean>0,
                   E=robust.Status=="OK" and robust.Mean>0)
        label="CELL_INSUFFICIENT_SAMPLE" if p.Status!="OK" else (
            "CELL_STRONG" if all(gates.values()) else
            "CELL_WEAK" if gates["A"] and gates["D"] and gates["E"] and not(gates["B"] and gates["C"])
            else "CELL_NO_STRUCTURE")
        labels[(r.Pair,r.TokyoDirection)]=label
        ck("Gates/"+r.Pair+"/"+r.TokyoDirection,
           all(getattr(r,k)==("PASS" if v else "FAIL") for k,v in gates.items())
           and r.CellVerdict==label)
    ea=[labels[("EURAUD",s)] for s in m.SIDES]
    ea_label="INSUFFICIENT_SAMPLE" if "CELL_INSUFFICIENT_SAMPLE" in ea else (
        "DIRECTIONAL_STRUCTURE_PRESENT" if "CELL_STRONG" in ea else
        "WEAK_DIRECTIONAL_STRUCTURE" if "CELL_WEAK" in ea else "NO_DIRECTIONAL_STRUCTURE")
    uj=[labels[("USDJPY",s)] for s in m.SIDES]
    uj_label="SHADOW_INSUFFICIENT_SAMPLE" if "CELL_INSUFFICIENT_SAMPLE" in uj else (
        "SHADOW_STRUCTURE_PRESENT" if all(v=="CELL_STRONG" for v in uj) and ea_label=="DIRECTIONAL_STRUCTURE_PRESENT"
        else "SHADOW_WEAK_STRUCTURE" if any(v in ("CELL_STRONG","CELL_WEAK") for v in uj)
        else "SHADOW_NO_STRUCTURE")
    for pair,label in [("EURAUD",ea_label),("USDJPY",uj_label)]:
        r=verdict[verdict.Pair.eq(pair)].iloc[0]
        ck("PairVerdict/"+pair,r.Verdict==label and r.UPCell==labels[(pair,"UP")] and r.DOWNCell==labels[(pair,"DOWN")])
    # Independent actual-data full 5000 row replication, both sides and asymmetry.
    base=daily[daily.Pair.eq("EURAUD")&daily.Method.eq("Primary")&
               daily.Date.between(*m.PERIODS["RecentCombined"])&daily.Eligible&daily.Q.eq(5)]
    first=pd.Timestamp("2021-12-27");last=pd.Timestamp("2026-09-07");k=(last-first).days//7+1
    wk=((base.Date-first).dt.days//7).to_numpy()
    side=np.where(base.X.to_numpy()>0,1,-1)
    y=base.AlignedLondonReturn.to_numpy()
    rng=np.random.default_rng(m.SEED);ups=[];downs=[]
    week_ids=[np.flatnonzero(wk==i) for i in range(k)]
    for _ in range(m.B):
        draw=rng.integers(0,k,k)
        ids=np.concatenate([week_ids[i] for i in draw])
        u=y[ids][side[ids]==1];v=y[ids][side[ids]==-1]
        ups.append(u.mean() if len(u) else np.nan)
        downs.append(v.mean() if len(v) else np.nan)
    for s,samples in [("UP",np.asarray(ups)),("DOWN",np.asarray(downs))]:
        r=by[("EURAUD","Primary","RecentCombined",s)]
        valid=samples[np.isfinite(samples)]
        ci=np.quantile(valid,[.025,.975],method="linear")
        p=(1+np.sum(np.abs(valid-r.Mean)>=abs(r.Mean)))/(1+len(valid))
        ck("FullBootstrapCI/"+s,close(ci[0],r.CILow) and close(ci[1],r.CIHigh))
        ck("FullBootstrapP/"+s,close(p,r.PUnadjusted))
    vals=np.asarray(ups)-np.asarray(downs);vals=vals[np.isfinite(vals)]
    row=asym[asym.Pair.eq("EURAUD")&asym.Method.eq("Primary")&asym.Period.eq("RecentCombined")].iloc[0]
    ci=np.quantile(vals,[.025,.975],method="linear")
    ck("FullBootstrapAsymmetryCI",close(ci[0],row.CILow) and close(ci[1],row.CIHigh))
    manual=pd.read_csv(out/(pre+"manual_audit.csv"),parse_dates=["Date"])
    ck("Manual16Strata",len(manual)==16 and manual.Status.eq("CHECKED").all())
    for r in manual.itertuples():
        source=daily[daily.Pair.eq(r.Pair)&daily.Method.eq(r.Method)&daily.Date.eq(r.Date)].iloc[0]
        unit=Decimal(".0001" if r.Pair=="EURAUD" else Decimal(".01"))
        end=source.Tokyo15Open if r.Method=="Primary" else source.London08Open
        x=(Decimal(str(end))-Decimal(str(source.Tokyo09Open)))/unit
        y=(Decimal(str(source.London11Open))-Decimal(str(source.London08Open)))/unit
        align=(-1 if r.Pair=="EURAUD" else 1)*(1 if x>0 else -1)*y
        ck("ManualDecimal/"+r.Pair+"/"+r.Method+"/"+r.Period+"/"+r.TokyoDirection,
           r.Q==5 and r.ReferenceN==252 and r.ReferenceEnd<r.Date and
           abs(float(x)-r.X)<1e-8 and abs(float(y)-r.Y)<1e-8 and abs(float(align)-r.Aligned)<1e-8)
    summary=pd.DataFrame(checks)
    summary["Family"]=summary.Check.str.split("/").str[0]
    summary.groupby("Family",sort=False).agg(Checks=("Pass","size"),AllPassed=("Pass","all")).reset_index().to_csv(
        out/(pre+"independent_validation.csv"),index=False)
    record=pd.read_csv(out/(pre+"run_record.csv"))
    record["Status"]="VERIFIED";record["IndependentChecksPassed"]=len(checks)
    record.to_csv(out/(pre+"run_record.csv"),index=False)
    m.publication_manifest(out)
    print("Independent checks PASS:",len(checks))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);p.add_argument("--phase2-daily",required=True)
    args=p.parse_args();verify(args.out,args.phase2_daily)
