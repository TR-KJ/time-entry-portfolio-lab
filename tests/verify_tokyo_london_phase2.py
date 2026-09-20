"""Independent Phase 2 verification without reusing assignment/summary/gate functions."""
from pathlib import Path
from decimal import Decimal
import sys,argparse,math
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src/research"))
import tokyo_london_phase2 as m

def verify(out):
    out=Path(out);pre=m.PREFIX
    a=pd.read_csv(out/(pre+"daily_assignment.csv"),float_precision="round_trip",parse_dates=["Date","ReferenceStart","ReferenceEnd"])
    periods=pd.read_csv(out/(pre+"period_summary.csv"))
    qtable=pd.read_csv(out/(pre+"quintile_summary.csv"))
    direction=pd.read_csv(out/(pre+"direction_summary.csv"))
    cover=pd.read_csv(out/(pre+"coverage.csv"))
    pair=pd.read_csv(out/(pre+"pair_summary.csv"))
    checks=[]
    def ck(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(dict(Check=name,Pass=True))
    def close(x,y):return bool(np.isclose(x,y,rtol=1e-10,atol=1e-10,equal_nan=True))
    def mean(z):return math.fsum(z)/len(z) if len(z) else np.nan
    ck("Uniqueness",not a.duplicated(["Pair","Method","Date"]).any())
    # Every rank checked using sorted historical magnitudes and searchsorted (different route).
    for (p,method),g in a[a.Valid].groupby(["Pair","Method"]):
        g=g.sort_values("Date").reset_index(drop=True);v=g.X.abs().to_numpy()
        for i,r in enumerate(g.itertuples()):
            if i<252:
                ck(f"Burnin/{p}/{method}/{i}",r.Q==0 and not r.Eligible);continue
            hist=np.sort(v[i-252:i]);lo=np.searchsorted(hist,v[i],"left");hi=np.searchsorted(hist,v[i],"right")
            num=int(lo+hi);q=1+min(4,int(num*5/504))
            ck(f"Rank/{p}/{method}/{i}",r.Q==q and r.LessCount==lo and r.EqualCount==hi-lo and close(r.Percentile,num/504))
            ck(f"Reference/{p}/{method}/{i}",r.ReferenceN==252 and r.ReferenceStart==g.Date.iloc[i-252] and r.ReferenceEnd==g.Date.iloc[i-1])
            if r.X!=0:
                val=(1 if r.X>0 else -1)*r.Y*(-1 if p=="EURAUD" else 1)
                ck(f"Aligned/{p}/{method}/{i}",close(val,r.AlignedLondonReturn) and r.Eligible)
            else:ck(f"Neutral/{p}/{method}/{i}",not r.Eligible and np.isnan(r.AlignedLondonReturn))
    for r in periods.itertuples():
        c=a[a.Pair.eq(r.Pair)&a.Method.eq(r.Method)&a.Date.between(*m.PERIODS[r.Period])]
        g=c[c.Eligible]
        means={}
        for q in range(1,6):
            z=g[g.Q.eq(q)].AlignedLondonReturn.to_numpy();means[q]=mean(z)
            qr=qtable[qtable.Pair.eq(r.Pair)&qtable.Method.eq(r.Method)&qtable.Period.eq(r.Period)&qtable.Q.eq(q)].iloc[0]
            ck(f"Quintile/{r.Pair}/{r.Method}/{r.Period}/{q}",len(z)==qr.N and close(means[q],qr.Mean) and close(np.median(z) if len(z) else np.nan,qr.Median))
        ck(f"Delta/{r.Pair}/{r.Method}/{r.Period}",close(means[5]-means[1],r.Delta))
        cv=cover[cover.Pair.eq(r.Pair)&cover.Method.eq(r.Method)&cover.Period.eq(r.Period)].iloc[0]
        ck(f"Coverage/{r.Pair}/{r.Method}/{r.Period}",cv.EligibleDays==len(g) and cv.CandidateDays==cv.MissingEndpointDays+cv.RankHistoryExcluded+cv.NeutralAfterRankExcluded+cv.EligibleDays)
        for side in ["UP","DOWN"]:
            sg=g[g.X>0] if side=="UP" else g[g.X<0]
            sd=mean(sg[sg.Q.eq(5)].AlignedLondonReturn.tolist())-mean(sg[sg.Q.eq(1)].AlignedLondonReturn.tolist())
            for q in range(1,6):
                z=sg[sg.Q.eq(q)].AlignedLondonReturn.tolist()
                dr=direction[direction.Pair.eq(r.Pair)&direction.Method.eq(r.Method)&direction.Period.eq(r.Period)&direction.TokyoSign.eq(side)&direction.Q.eq(q)].iloc[0]
                ck(f"Side/{r.Pair}/{r.Method}/{r.Period}/{side}/{q}",len(z)==dr.N and close(mean(z),dr.Mean) and close(sd,dr.SideDelta))
    # Independent Holm, retain full family size and make unavailable p equal 1.
    ordered=sorted(pair.to_dict("records"),key=lambda r:r["PUnadjusted"] if r["Status"]=="OK" else 1)
    adj={};last=0
    for i,r in enumerate(ordered):
        p=r["PUnadjusted"] if r["Status"]=="OK" else 1
        last=max(last,(3-i)*p);adj[r["Pair"]]=min(1,last)
    for r in pair.to_dict("records"):
        p=r["Pair"];sub=periods[periods.Pair.eq(p)].set_index(["Method","Period"])
        main=sub.loc[("Primary","RecentCombined" if p=="GBPJPY" else "ALL")]
        recent=sub.loc[("Primary","RecentB" if p=="GBPJPY" else "RecentCombined")]
        robust=sub.loc[("Robustness","RecentCombined" if p=="GBPJPY" else "ALL")]
        gates=dict(A=main.Status=="OK" and main.Delta>0 and main.CILow>0,B=main.Status=="OK" and adj[p]<=.05,
            C=main.Status=="OK" and main.Q5Mean>0,D=recent.Status=="OK" and recent.Delta>0,E=robust.Status=="OK" and robust.Delta>0)
        eligible=all(t.Status=="OK" for t in [main,recent,robust])
        verdict="INSUFFICIENT_SAMPLE" if not eligible else "EXPLORATORY_SUPPORTED" if all(gates.values()) else "EXPLORATORY_WATCHLIST" if main.Delta>0 and gates["C"] and gates["D"] and gates["E"] else "NOT_SUPPORTED"
        ck("Holm/"+p,close(r["PAdjusted"],adj[p]))
        ck("Gates/"+p,all(r[k]==("PASS" if v else "FAIL") for k,v in gates.items()))
        ck("Verdict/"+p,r["Verdict"]==verdict)
    # 36 preregistered examples: endpoint arithmetic independently checked with Decimal.
    manual=pd.read_csv(out/(pre+"manual_audit.csv"),parse_dates=["Date"])
    for r in manual.itertuples():
        z=a[a.Pair.eq(r.Pair)&a.Method.eq(r.Method)&a.Date.eq(r.Date)].iloc[0]
        unit=Decimal(".0001" if r.Pair=="EURAUD" else ".01")
        end="Tokyo15Open" if r.Method=="Primary" else "London08Open"
        x=float((Decimal(str(z[end]))-Decimal(str(z.Tokyo09Open)))/unit)
        y=float((Decimal(str(z.London11Open))-Decimal(str(z.London08Open)))/unit)
        aligned=(1 if x>0 else -1)*y*(-1 if r.Pair=="EURAUD" else 1)
        ck("ManualDecimal/"+r.Pair+"/"+r.Method+"/"+r.Selection,abs(x-r.X)<1e-8 and abs(y-r.Y)<1e-8 and abs(aligned-r.AlignedLondonReturn)<1e-8)
    ck("ManualThirtyQAndSixBoundary",len(manual)==36)
    # Actual UJ ALL Primary: independent RNG draw reproduction and daily row replication, all 5000.
    g=a[a.Pair.eq("USDJPY")&a.Method.eq("Primary")&a.Eligible]
    first=pd.Timestamp("2014-12-29");last=pd.Timestamp("2026-09-07");k=(last-first).days//7+1
    ids_by_week=[np.flatnonzero(((g.Date-first).dt.days//7).to_numpy()==i) for i in range(k)]
    values=g.AlignedLondonReturn.to_numpy();qs=g.Q.to_numpy()
    rng=np.random.default_rng(20260913);deltas=[]
    for _ in range(5000):
        ids=np.concatenate([ids_by_week[i] for i in rng.integers(0,k,k)])
        q=qs[ids];v=values[ids];deltas.append(v[q==5].mean()-v[q==1].mean())
    r=pair[pair.Pair.eq("USDJPY")].iloc[0];ci=np.quantile(deltas,[.025,.975],method="linear")
    p=(1+sum(abs(v-r.Delta)>=abs(r.Delta) for v in deltas))/5001
    ck("Real5000BootstrapCI",close(ci[0],r.CILow) and close(ci[1],r.CIHigh))
    ck("Real5000BootstrapP",close(p,r.PUnadjusted))
    # Large per-day verification remains local; publish compact check family counts.
    details=pd.DataFrame(checks)
    details["Family"]=details.Check.str.split("/").str[0]
    summary=details.groupby("Family",sort=False).agg(Checks=("Pass","size"),AllPassed=("Pass","all")).reset_index()
    summary.to_csv(out/(pre+"independent_validation.csv"),index=False)
    rec=pd.read_csv(out/(pre+"run_record.csv"));rec["Status"]="VERIFIED";rec["IndependentChecksPassed"]=len(checks)
    rec.to_csv(out/(pre+"run_record.csv"),index=False);m.publication_manifest(out)
    print("Independent verification PASS:",len(checks),"checks")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args();verify(a.out)
