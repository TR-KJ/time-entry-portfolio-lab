"""Independent direct counting / row least-squares verification; no C6 imports."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

PREFIX='c6_signal_crowding_phase1_'
ROOT=Path(__file__).resolve().parents[1]


def matrix(a,col):
    # Full dummy coding intentionally differs from production reference coding.
    z=pd.get_dummies(a[['StrategyNo','R2Category']].astype(str),dtype=float).to_numpy()
    return np.column_stack([np.ones(len(a)),z,a[col].to_numpy(float)])


def direct(a,col,weights=None):
    x=matrix(a,col); y=a.R.to_numpy(float)
    if weights is not None:
        w=np.sqrt(weights);x=x*w[:,None];y=y*w
    residual=x[:,-1]-x[:,:-1]@np.linalg.lstsq(x[:,:-1],x[:,-1],rcond=None)[0]
    if residual@residual<=1e-10*max(1,x[:,-1]@x[:,-1]):return np.nan
    return float(np.linalg.lstsq(x,y,rcond=None)[0][-1])


def raw(g,col):
    x=g[col].to_numpy(float)
    return float(np.cov(x,g.R,ddof=0)[0,1]/np.var(x)) if np.var(x)>0 else np.nan


def main():
    ap=argparse.ArgumentParser()
    for k in ('baseline','r2-assignment','out'):ap.add_argument('--'+k,required=True)
    args=ap.parse_args();out=Path(args.out)
    def read(name):return pd.read_csv(out/(PREFIX+name+'.csv'))
    a=read('trade_assignments_local');a['EntryTime']=pd.to_datetime(a.EntryTime)
    checks=[]
    def check(name,ok,detail=''):
        checks.append(dict(Check=name,Status='PASS' if ok else 'FAIL',Detail=detail))
        if not ok:raise AssertionError(name)
    def close(x,y):return bool(np.allclose(x,y,rtol=0,atol=1e-9,equal_nan=True))
    check('baseline_sha',hashlib.sha256(Path(args.baseline).read_bytes()).hexdigest()=='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359')
    check('R2_assignment_sha',hashlib.sha256(Path(args.r2_assignment).read_bytes()).hexdigest()=='49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021')
    baseline=pd.read_csv(args.baseline,parse_dates=['EntryTime']);b=baseline[baseline.StrategyNo!=22]
    check('universe',len(a)==len(b)==15837 and set(a.StrategyNo)==set(range(1,29))-{22})
    check('identity_unique_and_ordered',not a.duplicated(['StrategyNo','EntryTime']).any() and a.EntryTime.is_monotonic_increasing)
    identity=a.merge(b,on=['StrategyNo','EntryTime'],validate='one_to_one',suffixes=('','_baseline'))
    check('preserved_outcomes',len(identity)==15837 and close(identity.R,identity.R_baseline))
    q=pd.read_csv(args.r2_assignment,parse_dates=['EntryTime'])
    joined=a.merge(q,on=['StrategyNo','EntryTime'],validate='one_to_one',suffixes=('','_c4'))
    check('all_R2_assignments',len(joined)==15837 and (joined.R2Category==joined.primaryQuintile.replace({'INSUFFICIENT_VOL_HISTORY':'R2_UNAVAILABLE'})).all())
    refs=pd.read_csv(ROOT/'research_inputs/c4_reference_assignment_audit_light.csv')
    refs=refs[refs.StrategyNo!=22]
    mapped=q.set_index('TradeID').loc[refs.TradeID]
    check('R2_saved_audit',mapped.primaryQuintile.tolist()==refs.primaryQuintile.tolist(),str(len(refs)))
    refs=pd.read_csv(ROOT/'research_inputs/c4_reference_strategy_quintiles.csv')
    refs=refs[(refs.ScopeType=='Strategy')&(refs.Method=='primary')&(refs.StrategyNo!=22)]
    for r in refs.itertuples():
        g=a[(a.StrategyNo==r.StrategyNo)&(a.R2Category==r.Quintile)]
        assert len(g)==r.Trades and close(g.R.sum(),r.TotalR) and close(g.R.mean(),r.AvgR)
    check('R2_saved_aggregate_regression',True,str(len(refs)))
    times=a.EntryTime.to_numpy(dtype='datetime64[ns]')
    for h in (6,12):
        expected=np.array([np.sum((times>=t-np.timedelta64(h,'h'))&(times<=t))-1 for t in times])
        check('independent_every_count_'+str(h)+'h',np.array_equal(expected,a['SIGNAL_COUNT_'+str(h)+'H']))
    check('every_simultaneous_count',np.array_equal([np.sum(times==t)-1 for t in times],a.SAME_TIMESTAMP_OTHER_SIGNALS))
    periods=read('period_summary'); draws=read('bootstrap_draws_local')
    ranges={'Historical':('2015-01-01','2022-01-01'),'Recent A':('2022-01-01','2024-01-01'),
        'Recent B':('2024-01-01','2026-01-01'),'2026 Monitor':('2026-01-01','2026-09-10'),
        'Recent Combined':('2022-01-01','2026-09-10'),'ALL':('2015-01-01','2026-09-10')}
    for r in periods.itertuples():
        lo,hi=ranges[r.Period];g=a[(a.EntryTime>=lo)&(a.EntryTime<hi)];col=r.Feature; tag=col+'_'+r.Period
        check('direct_beta_'+tag,close(direct(g,col),r.Beta))
        check('raw_slope_'+tag,close(raw(g,col),r.RawSlope))
        eligible=[raw(z,col) for _,z in g.groupby('StrategyNo') if len(z)>=30 and z.Week.nunique()>=20 and z[col].nunique()>=3]
        check('equal_weight_'+tag,len(eligible)==r.EligibleStrategies and close(np.mean(eligible),r.EqualWeightSlope))
        saved=draws[(draws.Feature==col)&(draws.Period==r.Period)].sort_values('Replicate')
        check('bootstrap_saved_CI_'+tag,len(saved)==5000 and saved.Beta.notna().sum()==r.ValidBootstrap and close(saved.Beta.dropna().quantile([.025,.975]),[r.CILower,r.CIUpper]))
        weeks=sorted(g.Week.unique());rng=np.random.Generator(np.random.PCG64(20260913))
        n=32 if r.Period=='ALL' else 8
        for i in range(n):
            picked=rng.integers(len(weeks),size=len(weeks)); multiplicity=np.bincount(picked,minlength=len(weeks))
            weights=g.Week.map(dict(zip(weeks,multiplicity))).to_numpy()
            assert close(direct(g,col,weights),saved.iloc[i].Beta),(tag,i)
        check('direct_row_bootstrap_spot_'+tag,True,str(n)+' replicates')
        check('distribution_'+tag,r.Trades==len(g) and close(r.Mean,g[col].mean()) and close(r.Median,g[col].median()) and r.Min==g[col].min() and r.Max==g[col].max() and r.Distinct==g[col].nunique())
        print('Verified '+tag,flush=True)
    srows=read('strategy_summary')
    for r in srows.itertuples():
        lo,hi=ranges[r.Period];g=a[(a.StrategyNo==r.StrategyNo)&(a.EntryTime>=lo)&(a.EntryTime<hi)]
        assert close(raw(g,r.Feature),r.RawSlope) and close(direct(g,r.Feature),r.QAdjustedSlope)
    check('all_strategy_slopes',True,str(len(srows)))
    for r in read('count_summary').itertuples():
        lo,hi=ranges[r.Period];g=a[(a.EntryTime>=lo)&(a.EntryTime<hi)&a[r.Feature].eq(r.SignalCount)]
        assert len(g)==r.Trades and close(g.R.sum(),r.TotalR) and close(g.R.mean(),r.AvgR)
    check('all_count_summaries',True)
    loso=read('leave_one_strategy_out')
    for r in loso.itertuples():assert close(direct(a[a.StrategyNo!=r.OmittedStrategy],'SIGNAL_COUNT_6H'),r.Beta)
    check('all_27_LOSO',len(loso)==27)
    def sg(x):return int(x>1e-12)-int(x< -1e-12) if np.isfinite(x) else 0
    p={(r.Feature,r.Period):r for r in periods.itertuples()};all_=p['SIGNAL_COUNT_6H','ALL'];s=sg(all_.Beta)
    hist=p['SIGNAL_COUNT_6H','Historical']; rec=p['SIGNAL_COUNT_6H','Recent Combined']
    recent=[p['SIGNAL_COUNT_6H',k] for k in ('Recent A','Recent B','2026 Monitor')]
    def eligible(r):return r.Trades>=200 and r.Weeks>=20 and r.Strategies>=10 and r.Distinct>=4 and r.LargestBucketFraction<.9 and np.isfinite(r.Beta)
    gates=dict(A=s!=0 and sg(all_.RawSlope)==s,B=all_.CILower>0 or all_.CIUpper<0,
        C=s!=0 and sg(all_.EqualWeightSlope)==s,D=s!=0 and all(sg(x.Beta)==s for x in (hist,rec)),
        E=s!=0 and sum(eligible(x) and sg(x.Beta)==s for x in recent)>=2,
        F=s!=0 and sg(p['SIGNAL_COUNT_12H','ALL'].Beta)==s,
        G=all_.Trades==15837 and all_.EligibleStrategies>=10 and all_.Distinct>=4 and all_.LargestBucketFraction<.9 and np.isfinite(all_.CILower) and all(x.Distinct>=2 and np.isfinite(x.Beta) for x in (hist,rec)),
        H=s!=0 and all(sg(v)==s for v in loso.Beta))
    check('formal_gates',all(bool(r.Pass)==bool(gates[r.Gate]) for r in read('formal_gates').itertuples()))
    for r in read('manual_audit').itertuples():
        row=a[a.TradeID==r.TradeID].iloc[0];g=a[(a.EntryTime>=row.EntryTime-pd.Timedelta(hours=6))&(a.EntryTime<=row.EntryTime)&a.TradeID.ne(r.TradeID)]
        observed='' if pd.isna(r.WindowOtherIDs) else str(r.WindowOtherIDs)
        assert observed=='|'.join(map(str,g.TradeID)) and len(g)==r.Count6H
    check('manual_audit_identities',True,str(len(read('manual_audit'))))
    pd.DataFrame(checks).to_csv(out/(PREFIX+'independent_verification.csv'),index=False)
    print(str(len(checks))+'/'+str(len(checks))+' independent checks PASS',flush=True)


if __name__=='__main__':main()
