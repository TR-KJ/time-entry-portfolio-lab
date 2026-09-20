"""Preregistered exploratory magnitude diagnosis. No trade generation."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, platform, sys
import numpy as np
import pandas as pd
import tokyo_london_phase1 as p1

PLAN_SHA = "38fc59ba0b5f5b330ab0c1e8a057e20870e0efb3"
P1_RESULT = "40183638fe476a1776f6b55bbe69683e7ff558ab"
P1_DAILY_HASH = "d6a243fa93e4ca19af68caeee84e034acb8dc2382a1c15b510c61ce5ff1f1236"
P1_SOURCE_BLOB = "f22231172df6e8c3ad90c46a34bc5fdf6675c9d0"
BRANCH = "research/tokyo-london-market-effect-phase2-exploratory"
PAIRS = ["USDJPY", "EURAUD", "GBPJPY"]
DIRECTION = {"USDJPY":1, "EURAUD":-1, "GBPJPY":1}
MAIN_PERIOD = {"USDJPY":"ALL", "EURAUD":"ALL", "GBPJPY":"RecentCombined"}
RECENT_CHECK = {"USDJPY":"RecentCombined", "EURAUD":"RecentCombined", "GBPJPY":"RecentB"}
PERIODS = p1.PERIODS
METHODS = ["Primary", "Robustness"]
PREFIX = "tokyo_london_phase2_"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT/"research_inputs/tokyo_london_phase2_expected_manifest.csv"
B, SEED = 5000, 20260913

def git_blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read_input(path):
    if p1.sha(path)!=P1_DAILY_HASH: raise ValueError("Phase 1 daily hash mismatch")
    if git_blob(Path(p1.__file__))!=P1_SOURCE_BLOB: raise ValueError("Phase 1 source blob mismatch")
    d=pd.read_csv(path, float_precision="round_trip", parse_dates=["Date"])
    if len(d)!=36600: raise ValueError("Phase 1 row count mismatch")
    if d.duplicated(["Pair","Method","Date"]).any(): raise ValueError("Duplicate pairing")
    for e in p1.ENDPOINTS: d[e]=pd.to_datetime(d[e],utc=True)
    return d[d.Pair.isin(PAIRS)].copy()

def audit_raw(d, roots):
    expected=pd.read_csv(MANIFEST)
    assert len(expected)==24 and set(expected.Symbol)==set(PAIRS)
    paths=p1.discover(roots,expected)
    audits=[]
    for pair in PAIRS:
        print("Raw re-audit",pair,flush=True)
        rebuilt,a,_=p1.load_pair(pair,expected,paths)
        frozen=d[d.Pair.eq(pair)].sort_values(["Method","Date"]).reset_index(drop=True)
        rebuilt=rebuilt.sort_values(["Method","Date"]).reset_index(drop=True)
        pd.testing.assert_series_equal(frozen.Valid,rebuilt.Valid)
        for e in p1.ENDPOINTS:
            pd.testing.assert_series_equal(frozen[e],rebuilt[e])
            np.testing.assert_allclose(frozen[e+"Open"],rebuilt[e+"Open"],atol=1e-12,rtol=0,equal_nan=True)
        for col in ["X","Y"]:
            np.testing.assert_allclose(frozen[col],rebuilt[col],atol=1e-10,rtol=0,equal_nan=True)
        audits.append(a)
    return pd.concat(audits,ignore_index=True)

def classify(values):
    a=np.asarray(values,float);n=len(a)
    numerator=np.full(n,np.nan);less=np.full(n,np.nan);equal=np.full(n,np.nan)
    q=np.zeros(n,dtype=int)
    for i in range(252,n):
        ref=a[i-252:i]
        if not np.isfinite(ref).all() or not np.isfinite(a[i]): raise ValueError("Nonfinite magnitude")
        less[i]=np.count_nonzero(ref<a[i]);equal[i]=np.count_nonzero(ref==a[i])
        num=2*int(less[i])+int(equal[i]);numerator[i]=num
        q[i]=min(5,num*5//504+1)
    return numerator/504,q,less,equal

def assign(d):
    out=[]
    for pair in PAIRS:
        for method in METHODS:
            g=d[d.Pair.eq(pair)&d.Method.eq(method)].sort_values("Date").reset_index(drop=True).copy()
            if g.Date.duplicated().any(): raise ValueError("Duplicate daily key")
            valid=g.index[g.Valid].to_numpy()
            x=g.loc[valid,"X"].to_numpy()
            pct,q,less,equal=classify(np.abs(x))
            for c in ["Percentile","LessCount","EqualCount","AlignedLondonReturn"]: g[c]=np.nan
            g["Q"]=0;g["ReferenceN"]=0;g["ReferenceStart"]=pd.NaT;g["ReferenceEnd"]=pd.NaT
            g.loc[valid,"Percentile"]=pct;g.loc[valid,"Q"]=q
            g.loc[valid,"LessCount"]=less;g.loc[valid,"EqualCount"]=equal
            for i,k in enumerate(valid):
                g.loc[k,"ReferenceN"]=min(i,252)
                if i>=252:
                    g.loc[k,"ReferenceStart"]=g.loc[valid[i-252],"Date"]
                    g.loc[k,"ReferenceEnd"]=g.loc[valid[i-1],"Date"]
            g["TokyoNeutral"]=g.Valid & g.X.eq(0)
            g["Eligible"]=g.Valid & g.Q.gt(0) & ~g.TokyoNeutral
            g["ExclusionReason"]="MISSING_ENDPOINT"
            g.loc[g.Valid,"ExclusionReason"]="INSUFFICIENT_RANK_HISTORY"
            g.loc[g.Valid & g.Q.gt(0) & g.TokyoNeutral,"ExclusionReason"]="TOKYO_NEUTRAL"
            g.loc[g.Eligible,"ExclusionReason"]=""
            mask=g.Valid & ~g.TokyoNeutral
            g.loc[mask,"AlignedLondonReturn"]=DIRECTION[pair]*np.sign(g.loc[mask,"X"])*g.loc[mask,"Y"]
            g["Hypothesis"]="Continuation" if DIRECTION[pair]==1 else "Reversal"
            ranked=g[g.Q.gt(0)]
            assert (ranked.ReferenceEnd<ranked.Date).all()
            assert ranked.ReferenceN.eq(252).all()
            out.append(g)
    a=pd.concat(out,ignore_index=True)
    assert not a.duplicated(["Pair","Method","Date"]).any()
    return a

def weeks(g):
    return g.Date.dt.to_period("W-SUN").nunique()

def sample_ok(g):
    return len(g)>=80 and weeks(g)>=20 and all(
        len(g[g.Q.eq(q)])>=30 and weeks(g[g.Q.eq(q)])>=10 for q in [1,5])

def bootstrap(g,start,end):
    first,w=p1.week_weights(start,end)
    k=w.shape[1];s=[]
    for q in range(1,6):
        z=g[g.Q.eq(q)]
        wk=((z.Date-first).dt.days//7).to_numpy()
        s.extend([np.bincount(wk,minlength=k),
                  np.bincount(wk,weights=z.AlignedLondonReturn.to_numpy(),minlength=k)])
    totals=w.astype(float)@np.column_stack(s)
    with np.errstate(divide="ignore",invalid="ignore"):
        means=totals[:,1::2]/totals[:,::2]
    delta=means[:,4]-means[:,0];ok=np.isfinite(delta)
    return means,delta,ok,first,w

def summarize(a):
    quintiles=[];periods=[];coverage=[];shapes=[];directions=[];checks=[]
    for period,(start,end) in PERIODS.items():
        for pair in PAIRS:
            for method in METHODS:
                c=a[a.Pair.eq(pair)&a.Method.eq(method)&a.Date.between(start,end)]
                g=c[c.Eligible]
                coverage.append(dict(Pair=pair,Method=method,Period=period,CandidateDays=len(c),
                    ValidEndpointDays=int(c.Valid.sum()),MissingEndpointDays=int((~c.Valid).sum()),
                    RankHistoryExcluded=int(c.ExclusionReason.eq("INSUFFICIENT_RANK_HISTORY").sum()),
                    NeutralAfterRankExcluded=int(c.ExclusionReason.eq("TOKYO_NEUTRAL").sum()),
                    TokyoNeutralAllValid=int(c.TokyoNeutral.sum()),EligibleDays=len(g),ObservedWeeks=weeks(g)))
                means,bs,ok,first,w=bootstrap(g,start,end)
                point=[];ns=[]
                for q in range(1,6):
                    z=g[g.Q.eq(q)];v=z.AlignedLondonReturn
                    boot=means[:,q-1];boot=boot[np.isfinite(boot)]
                    ci=np.quantile(boot,[.025,.975],method="linear") if len(boot)>=4750 else [np.nan,np.nan]
                    avg=float(v.mean());point.append(avg);ns.append(len(v))
                    quintiles.append(dict(Pair=pair,Method=method,Period=period,Q=q,N=len(v),
                        ObservedWeeks=weeks(z),Mean=avg,Median=v.median(),Std=v.std(ddof=1),
                        PositiveRate=(v>0).mean() if len(v) else np.nan,
                        NegativeRate=(v<0).mean() if len(v) else np.nan,
                        NeutralRate=(v==0).mean() if len(v) else np.nan,
                        CILow=ci[0],CIHigh=ci[1],ValidBootstraps=len(boot)))
                delta=point[4]-point[0];nb=int(ok.sum())
                ci=np.quantile(bs[ok],[.025,.975],method="linear") if nb>=4750 else [np.nan,np.nan]
                p=(1+np.sum(np.abs(bs[ok]-delta)>=abs(delta)))/(1+nb) if nb>=4750 and np.isfinite(delta) else np.nan
                status="OK" if sample_ok(g) else "INSUFFICIENT_SAMPLE"
                if nb<4750 and status=="OK":status="BOOTSTRAP_INSUFFICIENT"
                periods.append(dict(Pair=pair,Method=method,Period=period,Status=status,N=len(g),
                    ObservedWeeks=weeks(g),Q1N=ns[0],Q5N=ns[4],Q1Mean=point[0],Q5Mean=point[4],
                    Delta=delta,CILow=ci[0],CIHigh=ci[1],PUnadjusted=p,ValidBootstraps=nb))
                adjacent=np.diff(point)
                ranks=pd.Series(point).rank(method="average").to_numpy()
                rho=float(np.corrcoef(np.arange(1,6),ranks)[0,1]) if np.isfinite(point).all() and np.std(ranks)>0 else np.nan
                shapes.append(dict(Pair=pair,Method=method,Period=period,SpearmanFiveMeans=rho,
                    PositiveAdjacent=int(np.sum(adjacent>0)) if np.isfinite(adjacent).all() else np.nan,
                    Q2MinusQ1=adjacent[0],Q3MinusQ2=adjacent[1],Q4MinusQ3=adjacent[2],
                    Q5MinusQ4=adjacent[3],Q4Mean=point[3],Q5Mean=point[4]))
                for side,sg in [("UP",g[g.X>0]),("DOWN",g[g.X<0])]:
                    sd=sg[sg.Q.eq(5)].AlignedLondonReturn.mean()-sg[sg.Q.eq(1)].AlignedLondonReturn.mean()
                    for q in range(1,6):
                        z=sg[sg.Q.eq(q)]
                        directions.append(dict(Pair=pair,Method=method,Period=period,TokyoSign=side,Q=q,
                            N=len(z),ObservedWeeks=weeks(z),Mean=z.AlignedLondonReturn.mean(),
                            Median=z.AlignedLondonReturn.median(),LowSample=len(z)<30 or weeks(z)<10,
                            SideDelta=sd,SideDeltaLowSample=not sample_ok(sg)))
                # Rebuild first 3 bootstrap samples by physically replicating daily rows.
                wk=((g.Date-first).dt.days//7).to_numpy()
                for j in range(3):
                    ids=np.repeat(np.arange(len(g)),w[j,wk]);z=g.iloc[ids]
                    check=z[z.Q.eq(5)].AlignedLondonReturn.mean()-z[z.Q.eq(1)].AlignedLondonReturn.mean()
                    np.testing.assert_allclose(check,bs[j],rtol=1e-11,atol=1e-10,equal_nan=True)
                checks.append(dict(Check="ExplicitClusterRowReplication3",Pair=pair,Method=method,Period=period,Pass=True))
    period=pd.DataFrame(periods)
    pair=verdicts(period)
    return dict(pair_summary=pair,period_summary=period,quintile_summary=pd.DataFrame(quintiles),
        coverage=pd.DataFrame(coverage),shape_summary=pd.DataFrame(shapes),
        direction_summary=pd.DataFrame(directions),validation=pd.DataFrame(checks),
        multiple_comparison=pair[["Pair","MainPeriod","PUnadjusted","PAdjusted","B"]])

def verdicts(period):
    main=[period[period.Pair.eq(p)&period.Method.eq("Primary")&period.Period.eq(MAIN_PERIOD[p])].iloc[0] for p in PAIRS]
    adj=p1.holm([r.PUnadjusted if r.Status=="OK" else np.nan for r in main])
    rows=[]
    for i,pair in enumerate(PAIRS):
        m=main[i]
        r=period[period.Pair.eq(pair)&period.Method.eq("Primary")&period.Period.eq(RECENT_CHECK[pair])].iloc[0]
        b=period[period.Pair.eq(pair)&period.Method.eq("Robustness")&period.Period.eq(MAIN_PERIOD[pair])].iloc[0]
        eligible=all(z.Status=="OK" for z in [m,r,b])
        gates=dict(A=m.Status=="OK" and m.Delta>0 and m.CILow>0,
                   B=m.Status=="OK" and adj[i]<=.05,
                   C=m.Status=="OK" and m.Q5Mean>0,
                   D=r.Status=="OK" and r.Delta>0,
                   E=b.Status=="OK" and b.Delta>0)
        if not eligible:verdict="INSUFFICIENT_SAMPLE"
        elif all(gates.values()):verdict="EXPLORATORY_SUPPORTED"
        elif m.Delta>0 and all(gates[k] for k in ["C","D","E"]):verdict="EXPLORATORY_WATCHLIST"
        else:verdict="NOT_SUPPORTED"
        row=dict(m.to_dict(),MainPeriod=MAIN_PERIOD[pair],Hypothesis="Continuation" if DIRECTION[pair]==1 else "Reversal",
                 PAdjusted=adj[i],RecentCheckPeriod=RECENT_CHECK[pair],RecentDelta=r.Delta,RecentStatus=r.Status,
                 RobustnessDelta=b.Delta,RobustnessStatus=b.Status,RobustnessQ5Mean=b.Q5Mean,
                 Verdict=verdict,**{k:"PASS" if v else "FAIL" for k,v in gates.items()})
        rows.append(row)
    return pd.DataFrame(rows)

def manual_audit(a):
    rows=[]
    for pair in PAIRS:
        for method in METHODS:
            g=a[a.Pair.eq(pair)&a.Method.eq(method)&a.Valid].sort_values("Date").reset_index(drop=True)
            picks=[("FirstQ"+str(q),int(g.index[g.Eligible&g.Q.eq(q)][0])) for q in range(1,6) if (g.Eligible&g.Q.eq(q)).any()]
            recent=g.index[g.Eligible&g.Date.ge("2022-01-01")]
            if len(recent):picks.append(("First2022",int(recent[0])))
            for tag,i in picks:
                row=g.iloc[i];ref=g.iloc[i-252:i];mag=abs(row.X)
                less=sum(abs(float(x))<mag for x in ref.X)
                eq=sum(abs(float(x))==mag for x in ref.X)
                num=2*less+eq;expected=min(5,(num*5)//504+1)
                assert len(ref)==252 and ref.Date.max()<row.Date
                assert expected==row.Q and less==row.LessCount and eq==row.EqualCount
                assert row.ReferenceStart==ref.Date.iloc[0] and row.ReferenceEnd==ref.Date.iloc[-1]
                aligned=(1 if row.X>0 else -1)*row.Y*DIRECTION[pair]
                np.testing.assert_allclose(aligned,row.AlignedLondonReturn,atol=1e-12)
                rows.append(dict(Pair=pair,Method=method,Selection=tag,Date=str(row.Date.date()),X=row.X,Y=row.Y,
                    ReferenceStart=str(ref.Date.iloc[0].date()),ReferenceEnd=str(ref.Date.iloc[-1].date()),
                    ReferenceN=len(ref),LessCount=less,EqualCount=eq,Percentile=num/504,Q=expected,
                    AlignedLondonReturn=aligned,Pass=True))
    return pd.DataFrame(rows)

def publication_manifest(out):
    rows=[]
    for p in sorted(Path(out).glob(PREFIX+"*.csv")):
        if p.name==PREFIX+"publication_manifest.csv":continue
        rows.append(dict(Filename=p.name,SHA256=p1.sha(p),Bytes=p.stat().st_size,
                         Rows=len(pd.read_csv(p)),Publication="LOCAL_COLAB_ONLY" if p.name==PREFIX+"daily_assignment.csv" else "GITHUB"))
    pd.DataFrame(rows).to_csv(Path(out)/(PREFIX+"publication_manifest.csv"),index=False)

def run(daily,roots,out,implementation_sha):
    if len(implementation_sha)!=40:raise ValueError("Full implementation SHA required")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    d=read_input(daily);audit=audit_raw(d,roots)
    print("Computing preregistered ranks and quintile summaries",flush=True)
    a=assign(d);a.to_csv(out/(PREFIX+"daily_assignment.csv"),index=False)
    tables=summarize(a);tables["input_audit"]=audit;tables["manual_audit"]=manual_audit(a)
    for name,t in tables.items():t.to_csv(out/(PREFIX+name+".csv"),index=False)
    record=dict(PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,Phase1ResultSHA=P1_RESULT,Branch=BRANCH,
        ExecutedUTC=datetime.now(timezone.utc).isoformat(),Python=platform.python_version(),Numpy=np.__version__,
        Pandas=pd.__version__,Seed=SEED,Bootstraps=B,Phase1DailySHA256=p1.sha(daily),Phase1SourceBlob=P1_SOURCE_BLOB,
        InputManifestSHA256=p1.sha(MANIFEST),RawSourceHashesMatched=24,Phase1VerdictChanged=False,
        LiveChanged=False,TradingStrategyCreated=False,ExploratorySelection=True,
        Status="COMPUTED_PENDING_INDEPENDENT_VERIFICATION")
    pd.DataFrame([record]).to_csv(out/(PREFIX+"run_record.csv"),index=False)
    publication_manifest(out)
    return tables

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--phase1-daily",required=True);p.add_argument("--data-root",action="append",required=True)
    p.add_argument("--out",required=True);p.add_argument("--implementation-sha",required=True)
    args=p.parse_args()
    run(args.phase1_daily,args.data_root,args.out,args.implementation_sha)
