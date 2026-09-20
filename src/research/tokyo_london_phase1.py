"""Preregistered Tokyo/London Phase 1. No trading or Phase 2 calculations."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, platform, sys
import numpy as np
import pandas as pd

PLAN_SHA = "9a51295b5e5868bb2f7ba909206a8fc0588dafdb"
BRANCH = "research/tokyo-london-market-effect-phase1"
PAIRS = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD", "GBPAUD"]
PERIODS = {
    "Historical": ("2015-01-01", "2021-12-31"),
    "RecentA": ("2022-01-01", "2023-12-31"),
    "RecentB": ("2024-01-01", "2025-12-31"),
    "Monitor2026": ("2026-01-01", "2026-09-09"),
    "RecentCombined": ("2022-01-01", "2026-09-09"),
    "ALL": ("2015-01-01", "2026-09-09"),
}
SEED, B = 20260913, 5000
PREFIX = "tokyo_london_phase1_"
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research_inputs/tokyo_london_phase1_expected_manifest.csv"
ENDPOINTS = ["Tokyo09", "Tokyo15", "London08", "London11"]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def pip(pair):
    if pair not in PAIRS: raise ValueError(pair)
    return .01 if pair.endswith("JPY") else .0001

def to_utc(raw):
    return pd.DatetimeIndex(raw).tz_localize(
        "Europe/Helsinki", ambiguous="infer", nonexistent="shift_forward"
    ).tz_convert("UTC")

def endpoints():
    dates = pd.bdate_range("2015-01-01", "2026-09-09")
    out = pd.DataFrame({"Date": dates})
    for name, hour, zone in [
        ("Tokyo09", 9, "Asia/Tokyo"), ("Tokyo15", 15, "Asia/Tokyo"),
        ("London08", 8, "Europe/London"), ("London11", 11, "Europe/London")
    ]:
        out[name] = (dates + pd.Timedelta(hours=hour)).tz_localize(zone).tz_convert("UTC")
    assert (out.Tokyo09 < out.Tokyo15).all()
    assert (out.Tokyo15 < out.London08).all()
    assert (out.London08 < out.London11).all()
    return out

def discover(roots, expected):
    found = {}
    names = set(expected.Filename)
    for root in roots:
        for p in Path(root).rglob("*.csv"):
            if p.name in names:
                found.setdefault(p.name, set()).add(p.resolve())
    bad = {n: len(found.get(n, [])) for n in names if len(found.get(n, [])) != 1}
    if bad: raise ValueError("Missing/ambiguous sources: " + json.dumps(bad))
    return {n: next(iter(v)) for n, v in found.items()}

def load_pair(pair, expected, paths):
    target = endpoints()
    needed = pd.DatetimeIndex(pd.concat([target[e] for e in ENDPOINTS]).unique())
    selected, indices, audits = [], [], []
    for row in expected[expected.Symbol.eq(pair)].itertuples():
        p = paths[row.Filename]
        actual_hash = sha(p)
        if actual_hash != row.SHA256: raise ValueError("Source hash mismatch: " + p.name)
        d = pd.read_csv(p, sep="\t")
        d.columns = [str(c).strip().strip("<>").upper() for c in d.columns]
        raw = pd.to_datetime(d.DATE.astype(str) + " " + d.TIME.astype(str),
                             format="%Y.%m.%d %H:%M:%S")
        if len(d) != row.Rows or str(raw.iloc[0]) != row.FirstRaw or str(raw.iloc[-1]) != row.LastRaw:
            raise ValueError("Source metadata mismatch: " + p.name)
        values = d[["OPEN", "HIGH", "LOW", "CLOSE"]].to_numpy(float)
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("Invalid prices: " + p.name)
        if (values[:,1] < values.max(axis=1)).any() or (values[:,2] > values.min(axis=1)).any():
            raise ValueError("Invalid OHLC: " + p.name)
        utc = to_utc(raw)
        adjusted = int(np.sum(utc.tz_convert("Europe/Helsinki").tz_localize(None) != pd.DatetimeIndex(raw)))
        indices.append(utc.asi8.copy())
        mask = utc.isin(needed)
        chosen = pd.DataFrame({
            "UTC": utc[mask], "Open": values[mask,0],
            "RawTime": raw[mask].astype(str).to_numpy(), "Filename": p.name,
            "SourceRow": np.flatnonzero(mask) + 2,
        })
        selected.append(chosen)
        audits.append(dict(Symbol=pair, Filename=p.name, SHA256=actual_hash,
                           Rows=len(d), FirstRaw=str(raw.iloc[0]), LastRaw=str(raw.iloc[-1]),
                           AdjustedTimestampCount=adjusted, HashMatch=True, MetadataMatch=True))
    all_index = np.concatenate(indices)
    if len(np.unique(all_index)) != len(all_index): raise ValueError("Duplicate UTC: " + pair)
    bars = pd.concat(selected, ignore_index=True).set_index("UTC").sort_index()
    if bars.index.has_duplicates: raise ValueError("Duplicate endpoint")
    daily = target.copy()
    for e in ENDPOINTS:
        daily[e + "Open"] = bars.Open.reindex(pd.DatetimeIndex(daily[e])).to_numpy()
    records = []
    for method, required in [("Primary", ENDPOINTS), ("Robustness", ["Tokyo09","London08","London11"])]:
        a = daily.copy()
        a["Pair"], a["Method"] = pair, method
        a["MissingReason"] = a.apply(
            lambda r: "|".join(sorted(e for e in required if pd.isna(r[e+"Open"]))), axis=1)
        a["Valid"] = a.MissingReason.eq("")
        end = "Tokyo15" if method == "Primary" else "London08"
        a["X"] = ((a[end+"Open"] - a.Tokyo09Open) / pip(pair)).where(a.Valid)
        a["Y"] = ((a.London11Open - a.London08Open) / pip(pair)).where(a.Valid)
        records.append(a)
    return pd.concat(records, ignore_index=True), pd.DataFrame(audits), bars

def ols(x, y):
    x, y = np.asarray(x,float), np.asarray(y,float)
    n = len(x)
    out = dict(N=n, Alpha=np.nan, Beta=np.nan, PearsonR=np.nan, R2=np.nan)
    for label, a in [("X",x), ("Y",y)]:
        out.update({label+"Mean": float(a.mean()) if n else np.nan,
                    label+"Median": float(np.median(a)) if n else np.nan,
                    label+"Std": float(a.std(ddof=1)) if n>1 else np.nan})
    if n < 2: return out
    dx, dy = x-x.mean(), y-y.mean()
    xx, yy, xy = dx@dx, dy@dy, dx@dy
    if xx <= 0: return out
    out["Beta"] = float(xy/xx)
    out["Alpha"] = float(y.mean()-out["Beta"]*x.mean())
    if yy > 0:
        out["PearsonR"] = float(xy/np.sqrt(xx*yy))
        out["R2"] = out["PearsonR"]**2
    return out

def week_weights(start, end, b=B):
    first = pd.Timestamp(start) - pd.Timedelta(days=pd.Timestamp(start).weekday())
    last = pd.Timestamp(end) - pd.Timedelta(days=pd.Timestamp(end).weekday())
    k = (last-first).days//7 + 1
    rng = np.random.default_rng(SEED)
    w = np.zeros((b,k),dtype=np.int16)
    for i in range(b):
        w[i] = np.bincount(rng.integers(0,k,k), minlength=k)
    return first, w

def bootstrap(g, first, weights, estimate):
    k = weights.shape[1]
    week = ((g.Date-first).dt.days//7).to_numpy()
    x, y = g.X.to_numpy(), g.Y.to_numpy()
    x, y = x-x.mean(), y-y.mean()
    sums = np.column_stack([np.bincount(week,weights=a,minlength=k)
                            for a in [np.ones(len(g)),x,y,x*x,y*y,x*y]])
    total = weights.astype(float) @ sums
    n, sx, sy, xx, yy, xy = total.T
    with np.errstate(divide="ignore", invalid="ignore"):
        xx = xx-sx*sx/n
        yy = yy-sy*sy/n
        slopes = (xy-sx*sy/n)/xx
    ok = (n>=2) & (xx>0) & (yy>0) & np.isfinite(slopes)
    valid = slopes[ok]
    out = dict(CILow=np.nan, CIHigh=np.nan, PUnadjusted=np.nan, ValidBootstraps=len(valid))
    if len(valid) >= 4750:
        out["CILow"], out["CIHigh"] = np.quantile(valid,[.025,.975],method="linear")
        out["PUnadjusted"] = (1+np.sum(np.abs(valid-estimate)>=abs(estimate)))/(1+len(valid))
    return out, slopes, ok

def holm(pvalues):
    p = np.array(pvalues,float)
    p = np.where(np.isfinite(p),p,1.)
    order = np.argsort(p,kind="stable")
    adjusted = np.minimum(1,np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]))
    result = np.empty(len(p))
    result[order] = adjusted
    return result

def sign(x):
    return int(np.sign(x)) if np.isfinite(x) else 0

def verdicts(period):
    allp = period[period.Period.eq("ALL") & period.Method.eq("Primary")].set_index("Pair").loc[PAIRS]
    adjusted = holm(allp.PUnadjusted.to_numpy())
    rows = []
    for i, pair in enumerate(PAIRS):
        sub = period[period.Pair.eq(pair)].set_index(["Method","Period"])
        a = sub.loc[("Primary","ALL")]
        s = sign(a.Beta)
        def same(method, per):
            r = sub.loc[(method,per)]
            return bool(r.Status=="OK" and s!=0 and sign(r.Beta)==s)
        recent = ["RecentA","RecentB","Monitor2026"]
        gates = dict(
            A=bool(a.Status=="OK" and (a.CILow>0 or a.CIHigh<0)),
            B=bool(a.Status=="OK" and adjusted[i]<=.05),
            C=all(same("Primary",p) for p in ["Historical","RecentCombined"]),
            D=sum(sub.loc[("Primary",p)].Status=="OK" for p in recent)>=2 and sum(same("Primary",p) for p in recent)>=2,
            E=same("Robustness","ALL"))
        row = dict(**a.to_dict(), PAdjusted=adjusted[i],
                   **{k: "PASS" if v else "FAIL" for k,v in gates.items()})
        row["Verdict"] = ("REVERSAL_SUPPORTED" if s<0 else "CONTINUATION_SUPPORTED") if all(gates.values()) else "NOT_SUPPORTED"
        for per in ["Historical","RecentCombined"]+recent:
            r = sub.loc[("Primary",per)]
            row[per+"Sign"] = sign(r.Beta)
            row[per+"Status"] = r.Status
        row["RobustnessBeta"] = sub.loc[("Robustness","ALL")].Beta
        row["RobustnessSign"] = sign(row["RobustnessBeta"])
        rows.append(row)
    return pd.DataFrame(rows)

def summarize(daily):
    periods, coverage, directions, checks = [], [], [], []
    for period, (start,end) in PERIODS.items():
        first, weights = week_weights(start,end)
        for pair in PAIRS:
            for method in ["Primary","Robustness"]:
                c = daily[daily.Pair.eq(pair) & daily.Method.eq(method) & daily.Date.between(start,end)]
                g = c[c.Valid]
                nweek = g.Date.dt.to_period("W-SUN").nunique()
                reasons = {e: int(c.MissingReason.str.contains(e,regex=False).sum()) for e in ENDPOINTS}
                coverage.append(dict(Pair=pair, Method=method, Period=period,
                    CandidateDays=len(c), ValidDays=len(g), ExcludedDays=len(c)-len(g),
                    ObservedWeeks=nweek, **{e+"Missing":v for e,v in reasons.items()}))
                m = ols(g.X,g.Y)
                status = "OK"
                if len(g)<80 or nweek<20: status = "INSUFFICIENT_SAMPLE"
                elif not np.isfinite(m["Beta"]): status = "DEGENERATE_X"
                elif not np.isfinite(m["PearsonR"]): status = "DEGENERATE_Y"
                ci = dict(CILow=np.nan,CIHigh=np.nan,PUnadjusted=np.nan,ValidBootstraps=0)
                if np.isfinite(m["PearsonR"]):
                    ci, slopes, ok = bootstrap(g,first,weights,m["Beta"])
                    if ci["ValidBootstraps"]<4750 and status=="OK": status="BOOTSTRAP_INSUFFICIENT"
                    # Independently solve the design matrix for every cell.
                    independent = np.linalg.lstsq(np.column_stack([np.ones(len(g)),g.X]),g.Y,rcond=None)[0]
                    np.testing.assert_allclose(independent,[m["Alpha"],m["Beta"]],rtol=1e-10,atol=1e-10)
                    checks.append(dict(Check="IndependentOLS",Pair=pair,Method=method,Period=period,Pass=True))
                    # Spot-check first three actual cluster row replications in every cell.
                    wk = ((g.Date-first).dt.days//7).to_numpy()
                    for j in range(3):
                        ids = np.repeat(np.arange(len(g)),weights[j,wk])
                        fit = np.linalg.lstsq(np.column_stack([np.ones(len(ids)),g.X.to_numpy()[ids]]),g.Y.to_numpy()[ids],rcond=None)[0]
                        np.testing.assert_allclose(fit[1],slopes[j],rtol=1e-9,atol=1e-10)
                    checks.append(dict(Check="BootstrapRowReplication3",Pair=pair,Method=method,Period=period,Pass=True))
                periods.append(dict(Pair=pair,Method=method,Period=period,ObservedWeeks=nweek,Status=status,**m,**ci))
                for direction, mask in [("UP",g.X>0),("DOWN",g.X<0),("NEUTRAL",g.X==0)]:
                    z = g[mask]; n=len(z)
                    directions.append(dict(Pair=pair,Method=method,Period=period,Direction=direction,N=n,
                        LondonMean=z.Y.mean(),LondonMedian=z.Y.median(),
                        ReversalRate=float((z.X*z.Y<0).mean()) if n and direction!="NEUTRAL" else np.nan,
                        ContinuationRate=float((z.X*z.Y>0).mean()) if n and direction!="NEUTRAL" else np.nan,
                        LondonNeutralRate=float((z.Y==0).mean()) if n else np.nan))
    period = pd.DataFrame(periods)
    pair = verdicts(period)
    families=[]
    for (method,per), sub in period.groupby(["Method","Period"],sort=False):
        for name,members in [("JPY",PAIRS[:4]),("AUD-cross",PAIRS[4:]),("All-6",PAIRS)]:
            z=sub[sub.Pair.isin(members)]
            complete=len(z)==len(members) and z.Status.eq("OK").all()
            families.append(dict(Family=name,Method=method,Period=per,Members="|".join(members),
                PairCount=len(members),MeanStandardizedBeta=z.PearsonR.mean() if complete else np.nan,
                Status="DESCRIPTIVE_ONLY" if complete else "INCOMPLETE"))
    return dict(pair_summary=pair, period_summary=period, coverage=pd.DataFrame(coverage),
                direction_summary=pd.DataFrame(directions),family_summary=pd.DataFrame(families),
                multiple_comparison=pair[["Pair","PUnadjusted","PAdjusted","B"]],
                validation=pd.DataFrame(checks))

def manual_candidates(daily, bars_by_pair):
    rows=[]
    for pair in PAIRS:
        g=daily[daily.Pair.eq(pair) & daily.Method.eq("Primary") & daily.Valid].sort_values("Date")
        for summer in [False,True]:
            season=g.London08.map(lambda t: bool(t.tz_convert("Europe/London").dst().total_seconds()))
            for direction in ["UP","DOWN"]:
                z=g[(season==summer) & (g.X>0 if direction=="UP" else g.X<0)]
                if z.empty:
                    rows.append(dict(Pair=pair,Season="summer" if summer else "winter",Direction=direction,Status="MISSING_STRATUM"))
                    continue
                r=z.iloc[0]
                for e in ENDPOINTS:
                    b=bars_by_pair[pair].loc[r[e]]
                    rows.append(dict(Pair=pair,Date=str(r.Date.date()),Season="summer" if summer else "winter",
                        Direction=direction,Endpoint=e,RawTime=b.RawTime,UTC=str(r[e]),
                        JST=str(r[e].tz_convert("Asia/Tokyo")),London=str(r[e].tz_convert("Europe/London")),
                        Open=b.Open,Filename=b.Filename,SourceRow=b.SourceRow,Pip=pip(pair),X=r.X,Y=r.Y,Status="SELECTED"))
    return pd.DataFrame(rows)

def run(roots,out,implementation_sha):
    if len(implementation_sha)!=40: raise ValueError("Full preregistered implementation SHA required")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    expected=pd.read_csv(MANIFEST)
    assert len(expected)==48 and set(expected.Symbol)==set(PAIRS)
    paths=discover(roots,expected)
    daily, audits, bars_by_pair=[],[],{}
    for pair in PAIRS:
        print("Auditing and extracting",pair,flush=True)
        d,a,bars=load_pair(pair,expected,paths)
        daily.append(d);audits.append(a);bars_by_pair[pair]=bars
    daily=pd.concat(daily,ignore_index=True)
    assert not daily.duplicated(["Pair","Method","Date"]).any()
    daily.to_csv(out/(PREFIX+"daily_assignment.csv"),index=False)
    daily[~daily.Valid].to_csv(out/(PREFIX+"exclusions.csv"),index=False)
    print("Estimating fixed regressions and cluster bootstrap",flush=True)
    tables=summarize(daily)
    tables["input_audit"]=pd.concat(audits,ignore_index=True)
    tables["manual_audit"]=manual_candidates(daily,bars_by_pair)
    for name,table in tables.items(): table.to_csv(out/(PREFIX+name+".csv"),index=False)
    record=dict(PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,Branch=BRANCH,
        ExecutedUTC=datetime.now(timezone.utc).isoformat(),Python=platform.python_version(),
        Numpy=np.__version__,Pandas=pd.__version__,Seed=SEED,Bootstraps=B,
        ExpectedManifestSHA256=sha(MANIFEST),SourceCount=48,AllSourceHashesMatch=True,
        Phase2Computed=False,LiveChanged=False,Status="COMPUTED_PENDING_INDEPENDENT_AUDIT")
    pd.DataFrame([record]).to_csv(out/(PREFIX+"run_record.csv"),index=False)
    publication_manifest(out)
    return tables

def publication_manifest(out):
    out=Path(out)
    files=[]
    for p in sorted(out.glob(PREFIX+"*.csv")):
        if p.name==PREFIX+"publication_manifest.csv": continue
        files.append(dict(Filename=p.name,SHA256=sha(p),Bytes=p.stat().st_size,
                          Rows=len(pd.read_csv(p)),Publication="LOCAL_COLAB_ONLY" if p.name in
                          [PREFIX+"daily_assignment.csv",PREFIX+"exclusions.csv"] else "GITHUB"))
    pd.DataFrame(files).to_csv(out/(PREFIX+"publication_manifest.csv"),index=False)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--data-root",action="append",required=True)
    p.add_argument("--out",required=True)
    p.add_argument("--implementation-sha",required=True)
    a=p.parse_args()
    run(a.data_root,a.out,a.implementation_sha)
