"""Independent post-run verification using raw CSV rows and alternate formulas."""
from pathlib import Path
from decimal import Decimal
import argparse,csv,importlib.util,math
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parents[1]/"src/research/tokyo_london_phase1.py"
spec=importlib.util.spec_from_file_location("tl",P)
tl=importlib.util.module_from_spec(spec);spec.loader.exec_module(tl)

def verify(roots,out):
    out=Path(out);pre=tl.PREFIX
    d=pd.read_csv(out/(pre+"daily_assignment.csv"),parse_dates=["Date"])
    periods=pd.read_csv(out/(pre+"period_summary.csv"))
    pairs=pd.read_csv(out/(pre+"pair_summary.csv"))
    expected=pd.read_csv(tl.MANIFEST);paths=tl.discover(roots,expected)
    checks=[]
    def check(name,ok):
        if not ok: raise AssertionError(name)
        checks.append(dict(Check=name,Pass=True))
    check("PairingUnique",not d.duplicated(["Pair","Method","Date"]).any())
    coverage=pd.read_csv(out/(pre+"coverage.csv"))
    directions=pd.read_csv(out/(pre+"direction_summary.csv"))
    for r in periods.itertuples():
        g=d[d.Pair.eq(r.Pair)&d.Method.eq(r.Method)&d.Valid&d.Date.between(*tl.PERIODS[r.Period])]
        x=g.X.tolist();y=g.Y.tolist();n=len(x)
        check(f"N/{r.Pair}/{r.Method}/{r.Period}",n==r.N)
        if n>=2 and np.isfinite(r.Beta):
            mx=math.fsum(x)/n;my=math.fsum(y)/n
            xx=math.fsum((v-mx)**2 for v in x)
            xy=math.fsum((a-mx)*(b-my) for a,b in zip(x,y))
            check(f"OLS_fsum/{r.Pair}/{r.Method}/{r.Period}",
                  math.isclose(xy/xx,r.Beta,abs_tol=1e-11))
        c=coverage[coverage.Pair.eq(r.Pair)&coverage.Method.eq(r.Method)&coverage.Period.eq(r.Period)].iloc[0]
        check(f"Coverage/{r.Pair}/{r.Method}/{r.Period}",
              c.ValidDays==n and c.CandidateDays==c.ValidDays+c.ExcludedDays)
        for side in ["UP","DOWN","NEUTRAL"]:
            z=g[g.X>0] if side=="UP" else g[g.X<0] if side=="DOWN" else g[g.X==0]
            dr=directions[directions.Pair.eq(r.Pair)&directions.Method.eq(r.Method)&directions.Period.eq(r.Period)&directions.Direction.eq(side)].iloc[0]
            check(f"DirectionN/{r.Pair}/{r.Method}/{r.Period}/{side}",len(z)==dr.N)
            if len(z) and side!="NEUTRAL":
                rev=sum(a*b<0 for a,b in zip(z.X,z.Y))/len(z)
                check(f"DirectionRate/{r.Pair}/{r.Method}/{r.Period}/{side}",math.isclose(rev,dr.ReversalRate,abs_tol=1e-12))
    # Alternate Holm loop and independently reconstruct all formal gates.
    ordered=sorted(pairs.to_dict("records"),key=lambda r:r["PUnadjusted"])
    adjusted={};previous=0
    for rank,r in enumerate(ordered):
        previous=max(previous,(6-rank)*r["PUnadjusted"])
        adjusted[r["Pair"]]=min(1,previous)
    for r in pairs.to_dict("records"):
        check("Holm/"+r["Pair"],math.isclose(adjusted[r["Pair"]],r["PAdjusted"],abs_tol=1e-14))
        sub=periods[periods.Pair.eq(r["Pair"])].set_index(["Method","Period"])
        a=sub.loc[("Primary","ALL")];s=np.sign(a.Beta)
        same=lambda p:sub.loc[("Primary",p)].Status=="OK" and sub.loc[("Primary",p)].Beta*a.Beta>0
        gates={"A":a.Status=="OK" and a.CILow*a.CIHigh>0,
               "B":a.Status=="OK" and adjusted[r["Pair"]]<=.05,
               "C":same("Historical") and same("RecentCombined"),
               "D":sum(same(p) for p in ["RecentA","RecentB","Monitor2026"])>=2,
               "E":sub.loc[("Robustness","ALL")].Status=="OK" and sub.loc[("Robustness","ALL")].Beta*a.Beta>0}
        for k,v in gates.items(): check("Gate"+k+"/"+r["Pair"],r[k]==("PASS" if v else "FAIL"))
        verdict=("REVERSAL_SUPPORTED" if s<0 else "CONTINUATION_SUPPORTED") if all(gates.values()) else "NOT_SUPPORTED"
        check("Verdict/"+r["Pair"],verdict==r["Verdict"])
    audit=pd.read_csv(out/(pre+"manual_audit.csv"))
    raw_opens={}
    for filename,z in audit[audit.Status.eq("SELECTED")].groupby("Filename"):
        need=set(z.SourceRow.astype(int))
        with paths[filename].open(newline="") as f:
            reader=csv.DictReader(f,delimiter="\t")
            for line,row in enumerate(reader,2):
                if line not in need: continue
                raw_opens[(filename,line)]=Decimal(row["<OPEN>"])
                expected_rows=z[z.SourceRow.eq(line)]
                for ar in expected_rows.itertuples():
                    ts=pd.Timestamp(row["<DATE>"]+" "+row["<TIME>"])
                    check("RawTimestamp/"+filename+"/"+str(line),str(ts)==ar.RawTime)
                    utc=ts.tz_localize("Europe/Helsinki").tz_convert("UTC")
                    check("RawUTC/"+filename+"/"+str(line),utc==pd.Timestamp(ar.UTC))
                    check("RawOpen/"+filename+"/"+str(line),math.isclose(float(row["<OPEN>"]),ar.Open,abs_tol=1e-12))
    for key,z in audit[audit.Status.eq("SELECTED")].groupby(["Pair","Season","Direction"]):
        p={r.Endpoint:raw_opens[(r.Filename,int(r.SourceRow))] for r in z.itertuples()}
        unit=Decimal(".01" if key[0].endswith("JPY") else ".0001")
        x=float((p["Tokyo15"]-p["Tokyo09"])/unit)
        y=float((p["London11"]-p["London08"])/unit)
        check("DecimalReturns/"+"/".join(key),math.isclose(x,z.X.iloc[0],abs_tol=1e-9) and math.isclose(y,z.Y.iloc[0],abs_tol=1e-9))
    audit.loc[audit.Status.eq("SELECTED"),"Status"]="RAW_CSV_DECIMAL_VERIFIED"
    audit.to_csv(out/(pre+"manual_audit.csv"),index=False)
    check("24RepresentativeStrata",len(audit.groupby(["Pair","Season","Direction"]))==24)
    pd.DataFrame(checks).to_csv(out/(pre+"independent_validation.csv"),index=False)
    record=pd.read_csv(out/(pre+"run_record.csv"))
    record["Status"]="VERIFIED"
    record["IndependentChecksPassed"]=len(checks)
    record.to_csv(out/(pre+"run_record.csv"),index=False)
    tl.publication_manifest(out)
    print("Independent checks passed:",len(checks))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data-root",action="append",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();verify(a.data_root,a.out)
