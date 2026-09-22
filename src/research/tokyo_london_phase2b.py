"""Preregistered final directional-asymmetry exploration; no trades."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, platform
import numpy as np
import pandas as pd
import tokyo_london_phase1 as p1
import tokyo_london_phase2 as p2

PLAN_SHA = "e4021d03b5e5f88a3b91db8d3b2ad8dc3a330b6d"
BASE_SHA = "046be86bffebd28dbd21a11e49fb9eb2e1d507ac"
P2_DAILY_HASH = "ab12358882adf6a165983710599f4524ce2b37f1409a9f9a04ad967cefdbc21d"
P2_BLOB = "9c6f640dff2151f4f03711e0a224c86b47f4a73f"
P1_BLOB = "f22231172df6e8c3ad90c46a34bc5fdf6675c9d0"
PAIRS = ["EURAUD","USDJPY"]
SIDES = ["UP","DOWN"]
METHODS = ["Primary","Robustness"]
PERIODS = p1.PERIODS
B,SEED = 5000,20260913
PREFIX = "tokyo_london_phase2b_"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT/"research_inputs/tokyo_london_phase2b_expected_manifest.csv"

def git_blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def read_input(path):
    if p1.sha(path)!=P2_DAILY_HASH:raise ValueError("Phase 2 daily SHA mismatch")
    if git_blob(Path(p2.__file__))!=P2_BLOB or git_blob(Path(p1.__file__))!=P1_BLOB:
        raise ValueError("Frozen Phase1/Phase2 source blob mismatch")
    d=pd.read_csv(path,float_precision="round_trip",parse_dates=["Date","ReferenceStart","ReferenceEnd"])
    if len(d)!=18300 or d.duplicated(["Pair","Method","Date"]).any():
        raise ValueError("Phase 2 daily identity mismatch")
    for e in p1.ENDPOINTS:d[e]=pd.to_datetime(d[e],utc=True)
    return d[d.Pair.isin(PAIRS)].copy()

def audit_sources(d,roots):
    expected=pd.read_csv(MANIFEST)
    if len(expected)!=16 or set(expected.Symbol)!=set(PAIRS):raise ValueError("Frozen source universe mismatch")
    paths=p1.discover(roots,expected)
    audits=[]
    for pair in PAIRS:
        print("Auditing",pair,flush=True)
        rebuilt,record,_=p1.load_pair(pair,expected,paths)
        original=d[d.Pair.eq(pair)].sort_values(["Method","Date"]).reset_index(drop=True)
        rebuilt=rebuilt.sort_values(["Method","Date"]).reset_index(drop=True)
        pd.testing.assert_series_equal(original.Date,rebuilt.Date)
        pd.testing.assert_series_equal(original.Valid,rebuilt.Valid)
        for e in p1.ENDPOINTS:
            pd.testing.assert_series_equal(original[e],rebuilt[e])
            np.testing.assert_allclose(original[e+"Open"],rebuilt[e+"Open"],rtol=0,atol=1e-12,equal_nan=True)
        for col in ["X","Y"]:
            np.testing.assert_allclose(original[col],rebuilt[col],rtol=0,atol=1e-10,equal_nan=True)
        eligible=original[original.Eligible]
        expected_align=np.where(pair=="EURAUD",-1,1)*np.sign(eligible.X)*eligible.Y
        np.testing.assert_allclose(expected_align,eligible.AlignedLondonReturn,rtol=0,atol=1e-10)
        # Every ranked row must use a strictly earlier reference and Phase 2's unchanged Q rule.
        ranked=original[original.Q.gt(0)]
        if not (ranked.ReferenceN.eq(252).all() and (ranked.ReferenceEnd<ranked.Date).all()
                and ranked.Percentile.ge(0).all() and ranked.Percentile.le(1).all()):raise ValueError("Rank identity mismatch")
        q=np.minimum(5,np.floor(ranked.Percentile.to_numpy()*5).astype(int)+1)
        if not np.array_equal(q,ranked.Q.to_numpy()):raise ValueError("Q identity mismatch")
        audits.append(record)
    return pd.concat(audits,ignore_index=True)

def observed_weeks(g):
    return g.Date.dt.to_period("W-SUN").nunique()

def stats(g):
    x=g.AlignedLondonReturn.to_numpy(float);n=len(x)
    return dict(N=n,CalendarWeeks=observed_weeks(g),
                Mean=float(x.mean()) if n else np.nan,
                Median=float(np.median(x)) if n else np.nan,
                Std=float(x.std(ddof=1)) if n>1 else np.nan,
                PositiveRate=float(np.mean(x>0)) if n else np.nan,
                NegativeRate=float(np.mean(x<0)) if n else np.nan,
                ZeroRate=float(np.mean(x==0)) if n else np.nan,
                TotalAlignedPips=float(np.sum(x)) if n else 0.)

def bootstrap(g,first,weights):
    k=weights.shape[1]
    wk=((g.Date-first).dt.days//7).to_numpy()
    n=np.bincount(wk,minlength=k)
    total=np.bincount(wk,weights=g.AlignedLondonReturn.to_numpy(float),minlength=k)
    ns=weights.astype(float)@n
    sums=weights.astype(float)@total
    with np.errstate(divide="ignore",invalid="ignore"):means=sums/ns
    return np.where(ns>0,means,np.nan),ns

def cell_metrics(g,first,w):
    basic=stats(g);point=basic["Mean"]
    samples,counts=bootstrap(g,first,w)
    valid=samples[np.isfinite(samples)]
    ci=np.quantile(valid,[.025,.975],method="linear") if len(valid)>=4750 else [np.nan,np.nan]
    p=(1+np.sum(np.abs(valid-point)>=abs(point)))/(1+len(valid)) if len(valid)>=4750 and np.isfinite(point) else np.nan
    status="OK" if basic["N"]>=40 and basic["CalendarWeeks"]>=20 else "INSUFFICIENT_SAMPLE"
    if status=="OK" and len(valid)<4750:status="BOOTSTRAP_INSUFFICIENT"
    return dict(**basic,CILow=ci[0],CIHigh=ci[1],PUnadjusted=p,
                ValidBootstraps=len(valid),Status=status),samples

def period_tables(d):
    cells=[];asym=[];coverage=[];checks=[]
    for period,(start,end) in PERIODS.items():
        first,w=p1.week_weights(start,end)
        for pair in PAIRS:
            for method in METHODS:
                base=d[d.Pair.eq(pair)&d.Method.eq(method)&d.Date.between(start,end)]
                candidate=base[base.Eligible&base.Q.eq(5)]
                cover=dict(Pair=pair,Method=method,Period=period,CandidateDays=len(base),
                    ValidEndpointDays=int(base.Valid.sum()),
                    RankHistoryExcluded=int(base.ExclusionReason.eq("INSUFFICIENT_RANK_HISTORY").sum()),
                    NeutralAfterRankExcluded=int(base.ExclusionReason.eq("TOKYO_NEUTRAL").sum()),
                    EligibleQ5Days=len(candidate))
                per={}
                for side in SIDES:
                    g=candidate[candidate.X.gt(0)] if side=="UP" else candidate[candidate.X.lt(0)]
                    m,boot=cell_metrics(g,first,w)
                    cells.append(dict(Pair=pair,Method=method,Period=period,TokyoDirection=side,**m))
                    cover[side+"N"]=m["N"];cover[side+"Weeks"]=m["CalendarWeeks"]
                    per[side]=(g,m,boot)
                    # First three replications materialize the actual daily rows.
                    wk=((g.Date-first).dt.days//7).to_numpy()
                    for j in range(3):
                        ids=np.repeat(np.arange(len(g)),w[j,wk])
                        independent=g.AlignedLondonReturn.to_numpy()[ids].mean() if len(ids) else np.nan
                        np.testing.assert_allclose(independent,boot[j],rtol=1e-11,atol=1e-10,equal_nan=True)
                    checks.append(dict(Check="ClusterRowReplication3",Pair=pair,Method=method,Period=period,
                                       TokyoDirection=side,Pass=True))
                up,down=per["UP"],per["DOWN"]
                diff=up[1]["Mean"]-down[1]["Mean"]
                dist=up[2]-down[2]
                ok=np.isfinite(dist);ci=np.quantile(dist[ok],[.025,.975],method="linear") if ok.sum()>=4750 else [np.nan,np.nan]
                asym.append(dict(Pair=pair,Method=method,Period=period,UPMean=up[1]["Mean"],
                    DOWNMean=down[1]["Mean"],UPMinusDOWN=diff,CILow=ci[0],CIHigh=ci[1],
                    ValidBootstraps=int(ok.sum()),Status="OK" if up[1]["Status"]==down[1]["Status"]=="OK" and ok.sum()>=4750 else "INSUFFICIENT_SAMPLE"))
                coverage.append(cover)
    return pd.DataFrame(cells),pd.DataFrame(asym),pd.DataFrame(coverage),pd.DataFrame(checks)

def holm_four(cells):
    sub=cells[cells.Method.eq("Primary")&cells.Period.eq("RecentCombined")]
    raw=[sub[sub.Pair.eq(p)&sub.TokyoDirection.eq(s)].iloc[0].PUnadjusted for p in PAIRS for s in SIDES]
    adjusted=p1.holm(raw)
    return pd.DataFrame([dict(Pair=p,TokyoDirection=s,PUnadjusted=raw[i],PAdjusted=adjusted[i],
                              Family="4_preregistered_Q5_direction_cells")
                         for i,(p,s) in enumerate((p,s) for p in PAIRS for s in SIDES)])

def decisions(cells,multiple):
    by=cells.set_index(["Pair","Method","Period","TokyoDirection"])
    adjusted=multiple.set_index(["Pair","TokyoDirection"])
    primary=[];cell_decisions={}
    for pair in PAIRS:
        for side in SIDES:
            p=by.loc[(pair,"Primary","RecentCombined",side)]
            a=by.loc[(pair,"Primary","RecentA",side)]
            b=by.loc[(pair,"Primary","RecentB",side)]
            r=by.loc[(pair,"Robustness","RecentCombined",side)]
            p_adj=adjusted.loc[(pair,side)].PAdjusted
            gates=dict(A=p.Status=="OK" and p.Mean>=2.,
                       B=p.Status=="OK" and p.CILow>0,
                       C=p.Status=="OK" and p_adj<=.05,
                       D=a.Status==b.Status=="OK" and a.Mean>0 and b.Mean>0,
                       E=r.Status=="OK" and r.Mean>0)
            if p.Status!="OK":label="CELL_INSUFFICIENT_SAMPLE"
            elif all(gates.values()):label="CELL_STRONG"
            elif gates["A"] and gates["D"] and gates["E"] and not(gates["B"] and gates["C"]):
                label="CELL_WEAK"
            else:label="CELL_NO_STRUCTURE"
            cell_decisions[(pair,side)]=label
            primary.append(dict(Pair=pair,Method="Primary",Period="RecentCombined",TokyoDirection=side,**p.to_dict(),PAdjusted=p_adj,
                RecentAMean=a.Mean,RecentAStatus=a.Status,
                RecentBMean=b.Mean,RecentBStatus=b.Status,
                RobustnessMean=r.Mean,RobustnessStatus=r.Status,
                **{k:"PASS" if v else "FAIL" for k,v in gates.items()},CellVerdict=label))
    ea=[cell_decisions[("EURAUD",s)] for s in SIDES]
    if "CELL_INSUFFICIENT_SAMPLE" in ea:ea_label="INSUFFICIENT_SAMPLE"
    elif "CELL_STRONG" in ea:ea_label="DIRECTIONAL_STRUCTURE_PRESENT"
    elif "CELL_WEAK" in ea:ea_label="WEAK_DIRECTIONAL_STRUCTURE"
    else:ea_label="NO_DIRECTIONAL_STRUCTURE"
    uj=[cell_decisions[("USDJPY",s)] for s in SIDES]
    if "CELL_INSUFFICIENT_SAMPLE" in uj:uj_label="SHADOW_INSUFFICIENT_SAMPLE"
    elif all(v=="CELL_STRONG" for v in uj) and ea_label=="DIRECTIONAL_STRUCTURE_PRESENT":
        uj_label="SHADOW_STRUCTURE_PRESENT"
    elif any(v in ("CELL_WEAK","CELL_STRONG") for v in uj):uj_label="SHADOW_WEAK_STRUCTURE"
    else:uj_label="SHADOW_NO_STRUCTURE"
    verdict=pd.DataFrame([
        dict(Pair="EURAUD",Role="MAIN",UPCell=ea[0],DOWNCell=ea[1],Verdict=ea_label,
             StrongSides=ea.count("CELL_STRONG"),Phase3Disposition="HUMAN_REVIEW_ELIGIBLE" if ea_label=="DIRECTIONAL_STRUCTURE_PRESENT" else "RESEARCH_STOP"),
        dict(Pair="USDJPY",Role="SHADOW",UPCell=uj[0],DOWNCell=uj[1],Verdict=uj_label,
             StrongSides=uj.count("CELL_STRONG"),Phase3Disposition="HUMAN_REVIEW_ELIGIBLE" if uj_label=="SHADOW_STRUCTURE_PRESENT" else "NO_PHASE3")])
    return pd.DataFrame(primary),verdict

def manual_audit(d):
    rows=[]
    for pair in PAIRS:
        for method in METHODS:
            for period in ["Historical","RecentCombined"]:
                start,end=PERIODS[period]
                for side in SIDES:
                    q=d[d.Pair.eq(pair)&d.Method.eq(method)&d.Date.between(start,end)&d.Eligible&d.Q.eq(5)]
                    q=q[q.X.gt(0)] if side=="UP" else q[q.X.lt(0)]
                    if q.empty:
                        rows.append(dict(Pair=pair,Method=method,Period=period,TokyoDirection=side,Status="MISSING_STRATUM"))
                        continue
                    row=q.sort_values("Date").iloc[0]
                    raw={e:str(row[e]) for e in p1.ENDPOINTS}
                    unit=.0001 if pair=="EURAUD" else .01
                    end_price=row.Tokyo15Open if method=="Primary" else row.London08Open
                    x=(end_price-row.Tokyo09Open)/unit;y=(row.London11Open-row.London08Open)/unit
                    aligned=(-1 if pair=="EURAUD" else 1)*np.sign(x)*y
                    np.testing.assert_allclose([x,y,aligned],[row.X,row.Y,row.AlignedLondonReturn],rtol=0,atol=1e-8)
                    rows.append(dict(Pair=pair,Method=method,Period=period,TokyoDirection=side,
                        Date=str(row.Date.date()),Q=int(row.Q),ReferenceStart=str(row.ReferenceStart.date()),
                        ReferenceEnd=str(row.ReferenceEnd.date()),ReferenceN=int(row.ReferenceN),
                        Percentile=row.Percentile,X=x,Y=y,Aligned=aligned,
                        Tokyo09Open=row.Tokyo09Open,Tokyo15Open=row.Tokyo15Open,
                        London08Open=row.London08Open,London11Open=row.London11Open,
                        **{e+"UTC":v for e,v in raw.items()},Status="CHECKED"))
    return pd.DataFrame(rows)

def publication_manifest(out):
    files=[]
    for p in sorted(Path(out).glob(PREFIX+"*.csv")):
        if p.name==PREFIX+"publication_manifest.csv":continue
        files.append(dict(Filename=p.name,SHA256=p1.sha(p),Bytes=p.stat().st_size,
                          Rows=len(pd.read_csv(p)),Publication="GITHUB"))
    pd.DataFrame(files).to_csv(Path(out)/(PREFIX+"publication_manifest.csv"),index=False)

def run(daily,roots,out,implementation_sha):
    if len(implementation_sha)!=40:raise ValueError("Full implementation SHA required")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    d=read_input(daily);source=audit_sources(d,roots)
    print("Calculating fixed Q5 directional cells",flush=True)
    cells,asym,coverage,validation=period_tables(d)
    multiple=holm_four(cells)
    primary,verdict=decisions(cells,multiple)
    tables=dict(primary_cells=primary,period_cells=cells,asymmetry_summary=asym,
                pair_verdict=verdict,coverage=coverage,multiple_comparison=multiple,
                input_audit=source,manual_audit=manual_audit(d),validation=validation)
    for name,t in tables.items():t.to_csv(out/(PREFIX+name+".csv"),index=False)
    pd.DataFrame([dict(PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,BaseSHA=BASE_SHA,
        ExecutedUTC=datetime.now(timezone.utc).isoformat(),Branch="research/tokyo-london-phase2b-directional-asymmetry",
        Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__,Seed=SEED,Bootstraps=B,
        Phase2DailySHA256=p1.sha(daily),SourceCount=16,Phase1VerdictChanged=False,Phase2VerdictChanged=False,
        LiveChanged=False,TradingStrategyCreated=False,Exploratory=True,
        Status="COMPUTED_PENDING_INDEPENDENT_VERIFICATION")]).to_csv(out/(PREFIX+"run_record.csv"),index=False)
    publication_manifest(out)
    return tables

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--phase2-daily",required=True);p.add_argument("--data-root",action="append",required=True)
    p.add_argument("--out",required=True);p.add_argument("--implementation-sha",required=True)
    a=p.parse_args();run(a.phase2_daily,a.data_root,a.out,a.implementation_sha)
