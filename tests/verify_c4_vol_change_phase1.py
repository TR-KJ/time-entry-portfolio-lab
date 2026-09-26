"""Independent reconstruction checks for C4 trade assignments and published summaries."""
from __future__ import annotations
import argparse, hashlib, math
from pathlib import Path
import numpy as np
import pandas as pd

BASELINE_SHA='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def independent_effect(x):
    rows=[]
    for key,g in x[x.C4State.isin(['COMPRESSION','EXPANSION'])].groupby(['StrategyNo','primaryQuintile']):
        c=g[g.C4State.eq('COMPRESSION')].R.to_numpy();e=g[g.C4State.eq('EXPANSION')].R.to_numpy()
        if len(c) and len(e):rows.append((len(c),len(e),e.mean()-c.mean()))
    w=np.array([c*e/(c+e) for c,e,d in rows]);d=np.array([d for c,e,d in rows])
    fe=float((w*d).sum()/w.sum());eligible=np.array([c>=20 and e>=20 for c,e,d in rows])
    return fe,float(d[eligible].mean()),len(rows),int(eligible.sum())

def independent_ci(x):
    x=x[x.C4State.isin(['COMPRESSION','EXPANSION'])].copy();weeks=sorted(x.Week.unique());strata=sorted(set(zip(x.StrategyNo,x.primaryQuintile)))
    wi={v:i for i,v in enumerate(weeks)};si={v:i for i,v in enumerate(strata)};n=np.zeros((len(weeks),len(strata),2));s=np.zeros_like(n)
    for r in x.itertuples():
        i=wi[r.Week];j=si[(r.StrategyNo,r.primaryQuintile)];k=int(r.C4State=='EXPANSION');n[i,j,k]+=1;s[i,j,k]+=r.R
    rng=np.random.Generator(np.random.PCG64(20260913));draw=rng.integers(0,len(weeks),(5000,len(weeks)));z=[]
    for sample in draw:
        mult=np.bincount(sample,minlength=len(weeks));nn=np.tensordot(mult,n,axes=(0,0));ss=np.tensordot(mult,s,axes=(0,0));ok=(nn[:,0]>0)&(nn[:,1]>0)
        delta=ss[ok,1]/nn[ok,1]-ss[ok,0]/nn[ok,0];w=nn[ok,0]*nn[ok,1]/(nn[ok,0]+nn[ok,1]);z.append(np.average(delta,weights=w))
    return np.quantile(z,[.025,.975],method='linear')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--out',required=True);ap.add_argument('--report',required=True);a=ap.parse_args();out=Path(a.out)
    d=pd.read_csv(out/'c4_vol_change_phase1_trade_assignments_local.csv');adj=pd.read_csv(out/'c4_vol_change_phase1_adjusted_summary.csv');raw=pd.read_csv(out/'c4_vol_change_phase1_portfolio_raw_summary.csv');cov=pd.read_csv(out/'c4_vol_change_phase1_feature_coverage.csv')
    checks=[]
    def ck(name,ok,detail):checks.append(dict(Check=name,Status='PASS' if ok else 'FAIL',Detail=detail))
    ck('baseline_hash',sha(a.baseline)==BASELINE_SHA,sha(a.baseline));ck('active_identity',len(d)==15837 and d.StrategyNo.nunique()==27 and not d.StrategyNo.eq(22).any() and not d.TradeID.duplicated().any(),f'rows={len(d)}')
    for method in ('ATR','RV'):
        ratio=d[method+'5']/d[method+'20'];ck(method.lower()+'_ratio',np.allclose(ratio,d[method+'ChangeRatio'],rtol=0,atol=1e-12,equal_nan=True),'component ratio')
        valid=d[method+'FeatureStatus'].eq('VALID');states=np.where(d[method+'ChangeNumerator']<168,'COMPRESSION',np.where(d[method+'ChangeNumerator']<336,'NEUTRAL','EXPANSION'))
        ck(method.lower()+'_state_boundaries',(states[valid]==d.loc[valid,method+'State']).all(),'integer 168/336 boundaries')
        cc=cov[cov.Method.eq(method)].iloc[0];ck(method.lower()+'_coverage',int(valid.sum())==int(cc.Valid) and math.isclose(valid.mean(),cc.Coverage,abs_tol=1e-15),f'{valid.sum()}/{len(d)}')
        x=d[valid].copy();x['C4State']=x[method+'State'];fe,equal,cs,ins=independent_effect(x);row=adj[(adj.Method.eq(method))&adj.Period.eq('ALL')].iloc[0]
        ck(method.lower()+'_fixed_effect',math.isclose(fe,row.AdjustedEffect,abs_tol=1e-14),f'{fe:.12f}')
        ck(method.lower()+'_equal_weight',math.isclose(equal,row.EqualWeightEffect,abs_tol=1e-14) and cs==row.ContributingStrata and ins==row.InformativeStrata,f'{equal:.12f}; strata={cs}/{ins}')
        for state in ('COMPRESSION','NEUTRAL','EXPANSION'):
            g=x[x.C4State.eq(state)];r=raw[(raw.Method.eq(method))&raw.Period.eq('ALL')&raw.State.eq(state)].iloc[0]
            ck(method.lower()+'_raw_'+state.lower(),len(g)==r.Trades and math.isclose(g.R.mean(),r.AvgR,abs_tol=1e-14),f'n={len(g)} avg={g.R.mean():.12f}')
        ci=independent_ci(x);ck(method.lower()+'_bootstrap',np.allclose(ci,[row.CILow,row.CIHigh],rtol=0,atol=1e-12),f'[{ci[0]:.12f},{ci[1]:.12f}]')
    report=pd.DataFrame(checks);report.to_csv(a.report,index=False);print(report.to_string(index=False))
    if not report.Status.eq('PASS').all():raise SystemExit(1)
if __name__=='__main__':main()
