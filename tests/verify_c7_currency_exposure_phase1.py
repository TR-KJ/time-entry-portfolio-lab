"""Independent C7 verification: direct masks/dictionaries/full-dummy row OLS."""
import argparse
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

PREFIX='c7_currency_exposure_phase1_'
ROOT=Path(__file__).resolve().parents[1]
CUR=('USD','EUR','GBP','JPY','AUD')
RANGES={'Historical':('2015-01-01','2022-01-01'),'Recent A':('2022-01-01','2024-01-01'),
        'Recent B':('2024-01-01','2026-01-01'),'2026 Monitor':('2026-01-01','2026-09-10'),
        'Recent Combined':('2022-01-01','2026-09-10'),'ALL':('2015-01-01','2026-09-10')}


def matrix(g,v):
    d=pd.get_dummies(g[['StrategyNo','R2Category']].astype(str),dtype=float).to_numpy()
    return np.column_stack([np.ones(len(g)),d,g[[v+'_GrossBefore',v+'_Count',v+'_HasOpen',v+'_NIC']].to_numpy(float)])


def direct(g,v,weights=None):
    x=matrix(g,v);y=g.R.to_numpy(float)
    if weights is not None:
        x=x*np.sqrt(weights)[:,None];y=y*np.sqrt(weights)
    residual=x[:,-1]-x[:,:-1]@np.linalg.lstsq(x[:,:-1],x[:,-1],rcond=None)[0]
    if residual@residual<=1e-10*max(1,x[:,-1]@x[:,-1]):return np.nan
    return float(np.linalg.lstsq(x,y,rcond=None)[0][-1])


def raw(g,v):
    x=g[v+'_NIC'].to_numpy();return np.cov(x,g.R,ddof=0)[0,1]/np.var(x) if np.var(x)>0 else np.nan


def sg(x):return (1 if x>1e-12 else -1 if x< -1e-12 else 0) if np.isfinite(x) else 0


def main():
    p=argparse.ArgumentParser()
    for k in ('baseline','r2-assignment','out'):p.add_argument('--'+k,required=True)
    args=p.parse_args();out=Path(args.out);checks=[]
    def read(name):return pd.read_csv(out/(PREFIX+name+'.csv'))
    def close(x,y):return bool(np.allclose(x,y,atol=1e-9,rtol=0,equal_nan=True))
    def check(name,ok,detail=''):
        checks.append(dict(Check=name,Status='PASS' if ok else 'FAIL',Detail=detail))
        if not ok:raise AssertionError(name)
    check('baseline_sha',hashlib.sha256(Path(args.baseline).read_bytes()).hexdigest()=='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359')
    check('R2_sha',hashlib.sha256(Path(args.r2_assignment).read_bytes()).hexdigest()=='49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021')
    a=read('trade_assignments_local');a.EntryTime=pd.to_datetime(a.EntryTime);a.CloseTime=pd.to_datetime(a.CloseTime)
    baseline=pd.read_csv(args.baseline,parse_dates=['EntryTime','CloseTime']);b=baseline[baseline.StrategyNo!=22]
    check('universe_and_unique',len(a)==15837 and a.StrategyNo.nunique()==27 and 22 not in set(a.StrategyNo) and not a.duplicated(['StrategyNo','EntryTime']).any())
    j=a.merge(b,on=['StrategyNo','EntryTime'],validate='one_to_one',suffixes=('','_b'))
    check('baseline_identity_outcome_exit',len(j)==15837 and close(j.R,j.R_b) and j.CloseTime.eq(j.CloseTime_b).all() and j.Direction.eq(j.Direction_b).all())
    check('timestamp_order',a.EntryTime.is_monotonic_increasing and a.CloseTime.gt(a.EntryTime).all())
    check('week_clusters',a.Week.eq(a.EntryTime.dt.to_period('W-SUN').dt.start_time.astype(str)).all())
    q=pd.read_csv(args.r2_assignment,parse_dates=['EntryTime']);j=a.merge(q,on=['StrategyNo','EntryTime'],validate='one_to_one',suffixes=('','_q'))
    check('all_R2_assignments',len(j)==15837 and j.R2Category.eq(j.primaryQuintile.replace({'INSUFFICIENT_VOL_HISTORY':'R2_UNAVAILABLE'})).all())
    expected_weight=a.R2Category.map({'Q1':.5,'Q2':.7,'Q3':.9,'Q4':1.1,'Q5':1.3,'R2_UNAVAILABLE':.9})
    check('risk_and_fallback',close(expected_weight,a.RiskWeight) and a.R2Category.eq('R2_UNAVAILABLE').sum()==1186)
    refs=pd.read_csv(ROOT/'research_inputs/c4_reference_assignment_audit_light.csv');refs=refs[refs.StrategyNo!=22]
    check('R2_audit_reference',q.set_index('TradeID').loc[refs.TradeID].primaryQuintile.tolist()==refs.primaryQuintile.tolist(),str(len(refs)))
    refs=pd.read_csv(ROOT/'research_inputs/c4_reference_strategy_quintiles.csv');refs=refs[(refs.ScopeType=='Strategy')&(refs.Method=='primary')&(refs.StrategyNo!=22)]
    for r in refs.itertuples():
        g=a[(a.StrategyNo==r.StrategyNo)&(a.R2Category==r.Quintile)]
        assert len(g)==r.Trades and close(g.R.sum(),r.TotalR) and close(g.R.mean(),r.AvgR)
    check('R2_aggregate_reference',True,str(len(refs)))
    entries=a.EntryTime.to_numpy();exits=a.CloseTime.to_numpy();symbols=a.Symbol.to_numpy();directions=a.Direction.to_numpy();risk=expected_weight.to_numpy()
    def vec(i,w):
        d=1 if directions[i]=='Long' else -1
        return {symbols[i][:3]:d*w,symbols[i][3:]:-d*w}
    variants=('Primary','EqualUnit','SameSymbolIncluded')
    for v in variants:
        exp=[];ids=[]
        for i,t in enumerate(entries):
            mask=(entries<t)&(exits>t)
            if v!='SameSymbolIncluded':mask&=symbols!=symbols[i]
            ix=np.flatnonzero(mask);before={c:0. for c in CUR}
            for j in ix:
                for c,w in vec(j,1 if v=='EqualUnit' else risk[j]).items():before[c]+=w
            after=before.copy();cw=1 if v=='EqualUnit' else risk[i]
            for c,w in vec(i,cw).items():after[c]+=w
            gb=sum(abs(w) for w in before.values());ga=sum(abs(w) for w in after.values())
            exp.append([gb,ga,len(ix),int(len(ix)>0),(ga-gb)/(2*cw),*[before[c] for c in CUR],*[after[c] for c in CUR],*[abs(after[c])-abs(before[c]) for c in CUR]])
            ids.append('|'.join(a.iloc[ix].TradeID.astype(str)))
        cols=[v+'_'+s for s in ['GrossBefore','GrossAfter','Count','HasOpen','NIC',*['Before_'+c for c in CUR],*['After_'+c for c in CUR],*['DeltaAbs_'+c for c in CUR]]]
        check('every_vector_gross_count_NIC_'+v,close(np.array(exp),a[cols].to_numpy(float)),'15837 direct masks and currency dictionaries')
        check('every_open_identity_'+v,ids==a[v+'_OpenIDs'].fillna('').tolist())
        check('NIC_range_'+v,a[v+'_NIC'].between(-1-1e-10,1+1e-10).all())
        x=a[v+'_NIC'];st=np.where(x< -1e-10,'DIVERSIFYING',np.where(x>1e-10,'CONCENTRATING','NEUTRAL'))
        check('sign_states_'+v,(st==a[v+'_State']).all())
        print('Verified all exposures '+v,flush=True)
    check('simultaneous_count',np.array_equal(a.SimultaneousOther,[sum(entries==t)-1 for t in entries]))
    periods=read('period_summary');draws=read('bootstrap_draws_local')
    for r in periods.itertuples():
        lo,hi=RANGES[r.Period];g=a[(a.EntryTime>=lo)&(a.EntryTime<hi)];v=r.Variant;tag=v+'_'+r.Period;x=g[v+'_NIC']
        check('OLS_'+tag,close(direct(g,v),r.Beta))
        check('raw_'+tag,close(raw(g,v),r.RawSlope) and close(g.loc[x>1e-10,'R'].mean()-g.loc[x< -1e-10,'R'].mean(),r.RawSignDifference))
        check('distribution_'+tag,len(g)==r.Trades and close([x.mean(),x.median(),x.std(ddof=0),x.min(),x.max(),*x.quantile([.1,.25,.75,.9])],[r.Mean,r.Median,r.SD,r.Min,r.Max,r.Q10,r.Q25,r.Q75,r.Q90]) and (x< -1e-10).sum()==r.Negative and (x>1e-10).sum()==r.Positive and (x.abs()<=1e-10).sum()==r.Zero)
        saved=draws[(draws.Variant==v)&(draws.Period==r.Period)].sort_values('Replicate')
        check('CI_'+tag,len(saved)==5000 and saved.Beta.notna().sum()==r.ValidBootstrap and close(saved.Beta.dropna().quantile([.025,.975]),[r.CILower,r.CIUpper]))
        weeks=sorted(g.Week.unique());rng=np.random.Generator(np.random.PCG64(20260913));n=32 if r.Period=='ALL' else 8
        for i in range(n):
            mult=np.bincount(rng.integers(len(weeks),size=len(weeks)),minlength=len(weeks))
            weights=g.Week.map(dict(zip(weeks,mult))).to_numpy()
            assert close(direct(g,v,weights),saved.iloc[i].Beta),(tag,i)
        check('row_bootstrap_'+tag,True,str(n)+' direct weighted refits')
        print('Verified '+tag,flush=True)
    for r in read('strategy_summary').itertuples():
        g=a[a.StrategyNo==r.StrategyNo]
        assert close(direct(g,'Primary'),r.WithinStrategyAdjustedSlope) and close(raw(g,'Primary'),r.RawSlope)
    check('all27_strategy_slopes',True)
    loso=read('leave_one_strategy_out')
    for r in loso.itertuples():assert close(direct(a[a.StrategyNo!=r.OmittedStrategy],'Primary'),r.Beta)
    check('all27_LOSO',len(loso)==27)
    for r in read('raw_sign_summary').itertuples():
        lo,hi=RANGES[r.Period];g=a[(a.EntryTime>=lo)&(a.EntryTime<hi)&a[r.Variant+'_State'].eq(r.State)]
        pos=g.R[g.R>0];neg=g.R[g.R<0]
        assert len(g)==r.Trades and close([g.R.mean(),g.R.sum(),pos.sum()/-neg.sum(),(g.R>0).mean(),pos.mean(),neg.mean()],[r.AvgR,r.TotalR,r.PF,r.WinRate,r.AvgWinR,r.AvgLossR])
    check('all_raw_sign_metrics',True)
    for r in read('simultaneous_diagnostic').itertuples():
        t=np.datetime64(r.EntryTime);ix=np.flatnonzero((entries<t)&(exits>t));batch=np.flatnonzero(entries==t)
        before={c:0. for c in CUR};after={c:0. for c in CUR}
        for j in ix:
            for c,w in vec(j,risk[j]).items():before[c]+=w
        after=before.copy()
        for j in batch:
            for c,w in vec(j,risk[j]).items():after[c]+=w
        assert close([sum(abs(w) for w in before.values()),sum(abs(w) for w in after.values())],[r.GrossBefore,r.GrossAfter])
        assert r.Trades==len(batch) and r.PriorOpenCount==len(ix)
        assert close([getattr(r,'DeltaAbs_'+c) for c in CUR],[abs(after[c])-abs(before[c]) for c in CUR])
    check('all_simultaneous_batches',True,str(len(read('simultaneous_diagnostic'))))
    for r in read('manual_audit').itertuples():
        g=a[a.TradeID==r.TradeID].iloc[0]
        assert close(g.Primary_NIC,r.Primary_NIC)
        assert ('' if pd.isna(r.Primary_OpenIDs) else r.Primary_OpenIDs)==('' if pd.isna(g.Primary_OpenIDs) else g.Primary_OpenIDs)
    check('manual_audit',True,str(len(read('manual_audit'))))
    p={(r.Variant,r.Period):r for r in periods.itertuples()};r=p['Primary','ALL'];s=sg(r.Beta)
    hr=[p['Primary',k] for k in ('Historical','Recent Combined')];recent=[p['Primary',k] for k in ('Recent A','Recent B','2026 Monitor')]
    def elig(z):return z.Trades>=200 and z.Weeks>=20 and z.Strategies>=10 and z.Negative>=30 and z.Positive>=30 and z.Distinct>=3 and z.Variance>=.01 and z.OpenTrades>=100 and np.isfinite(z.Beta)
    enough=r.Trades==15837 and r.Strategies==27 and r.Negative>=200 and r.Positive>=200 and r.Distinct>=3 and r.Variance>=.01 and r.OpenTrades>=500 and r.OpenStrategies>=10 and np.isfinite(r.Beta) and np.isfinite(r.CILower) and all(z.Negative>=30 and z.Positive>=30 and z.Weeks>=20 and z.Distinct>=3 and z.Variance>=.01 and np.isfinite(z.Beta) for z in hr)
    gates=dict(A=s!=0 and sg(r.RawSignDifference)==s,B=r.CILower>0 or r.CIUpper<0,C=s!=0 and all(sg(z.Beta)==s for z in hr),D=s!=0 and sum(elig(z) and sg(z.Beta)==s for z in recent)>=2,E=s!=0 and sg(p['EqualUnit','ALL'].Beta)==s,F=s!=0 and sg(p['SameSymbolIncluded','ALL'].Beta)==s,G=s!=0 and len(loso)==27 and all(sg(x)==s for x in loso.Beta),H=enough)
    check('formal_gates',all(bool(r.Pass)==bool(gates[r.Gate]) for r in read('formal_gates').itertuples()))
    for z in recent:assert bool(z.PeriodEligible)==bool(elig(z))
    check('period_eligibility',True)
    pd.DataFrame(checks).to_csv(out/(PREFIX+'independent_verification.csv'),index=False)
    print(str(len(checks))+'/'+str(len(checks))+' independent checks PASS',flush=True)


if __name__=='__main__':main()
