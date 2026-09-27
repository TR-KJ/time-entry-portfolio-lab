"""C6 fixed-entry signal crowding, additive Strategy and R2 fixed effects."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import volatility_phase1 as p1
from exit_efficiency_phase1 import BASELINE_SHA, PERIODS, load_baseline
from c4_vol_change_phase1 import metric

PLAN_SHA='24653fa83a652a18ca6d0ed20a113680a73f35a3'
R2_SHA='49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021'
ROOT=Path(__file__).resolve().parents[2]
PREFIX='c6_signal_crowding_phase1_'
FEATURES=('SIGNAL_COUNT_6H','SIGNAL_COUNT_12H')


def sign(x):
    return 1 if np.isfinite(x) and x>1e-12 else -1 if np.isfinite(x) and x< -1e-12 else 0


def timeline(frame):
    a=frame[frame.StrategyNo.ne(22)].copy()
    if a.duplicated(['StrategyNo','EntryTime']).any(): raise ValueError('duplicate trade identity')
    a=a.sort_values(['EntryTime','StrategyNo'],kind='stable').reset_index(drop=True)
    t=a.EntryTime.to_numpy(dtype='datetime64[ns]')
    if pd.isna(t).any(): raise ValueError('invalid timestamp')
    for h,col in zip((6,12),FEATURES):
        a[col]=np.searchsorted(t,t,side='right')-np.searchsorted(t,t-np.timedelta64(h,'h'),side='left')-1
    a['SAME_TIMESTAMP_OTHER_SIGNALS']=np.searchsorted(t,t,side='right')-np.searchsorted(t,t,side='left')-1
    a['Week']=a.EntryTime.dt.to_period('W-SUN').dt.start_time.astype(str)
    return a


def load_inputs(baseline,r2_path):
    load_baseline(baseline)  # inherited fixed anchor metadata and hash gate
    b=p1.load_baseline(baseline); b=b[b.StrategyNo.ne(22)].copy()
    path=Path(r2_path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=R2_SHA or path.stat().st_size!=3756484:
        raise ValueError('C4 assignment source hash/size mismatch')
    q=pd.read_csv(path,parse_dates=['EntryTime'])
    if len(q)!=15837 or q.duplicated(['StrategyNo','EntryTime']).any(): raise ValueError('R2 identity')
    merged=b.merge(q[['StrategyNo','EntryTime','Strategy','Symbol','R','primaryQuintile','TradeID']],
                   on=['StrategyNo','EntryTime'],suffixes=('','_r2'),validate='one_to_one',how='outer',indicator=True)
    assert len(merged)==15837 and merged['_merge'].eq('both').all()
    for col in ('Strategy','Symbol','TradeID'): assert merged[col].equals(merged[col+'_r2'])
    np.testing.assert_allclose(merged.R,merged.R_r2,atol=1e-12,rtol=0)
    allowed={'Q1','Q2','Q3','Q4','Q5','INSUFFICIENT_VOL_HISTORY'}
    assert set(merged.primaryQuintile)<=allowed
    merged['R2Category']=merged.primaryQuintile.replace({'INSUFFICIENT_VOL_HISTORY':'R2_UNAVAILABLE'})
    audit=pd.read_csv(ROOT/'research_inputs/c4_reference_assignment_audit_light.csv')
    audit=audit[audit.StrategyNo.ne(22)]
    actual=merged.set_index('TradeID').loc[audit.TradeID]
    assert actual.primaryQuintile.tolist()==audit.primaryQuintile.tolist()
    refs=pd.read_csv(ROOT/'research_inputs/c4_reference_strategy_quintiles.csv')
    refs=refs[(refs.ScopeType=='Strategy')&(refs.Method=='primary')&refs.StrategyNo.ne(22)]
    for r in refs.itertuples():
        g=merged[(merged.StrategyNo==int(r.StrategyNo))&(merged.primaryQuintile==r.Quintile)]
        assert len(g)==int(r.Trades)
        np.testing.assert_allclose([g.R.sum(),g.R.mean()],[r.TotalR,r.AvgR],rtol=0,atol=1e-10,equal_nan=True)
    out=timeline(merged[['TradeID','StrategyNo','Strategy','Symbol','Direction','EntryTime','R','R2Category']])
    assert len(out)==15837 and out.StrategyNo.nunique()==27
    return out,[dict(Check='baseline_sha',Status='PASS',Detail=BASELINE_SHA),
        dict(Check='R2_full_assignment_hash',Status='PASS',Detail=R2_SHA),
        dict(Check='R2_identity_outcome_regression',Status='PASS',Detail='15837 exact identities; Strategy/Symbol/R/TradeID agree'),
        dict(Check='R2_reference_audit',Status='PASS',Detail=str(len(audit))+' active reference assignments'),
        dict(Check='R2_reference_aggregates',Status='PASS',Detail=str(len(refs))+' primary Strategy/Q rows'),
        dict(Check='universe',Status='PASS',Detail='27 active / 15837; Strategy22 absent from observations and timeline')]


def design(a):
    cols=[np.ones(len(a))]
    for col in ('StrategyNo','R2Category'):
        levels=sorted(a[col].unique())
        cols.extend(a[col].eq(v).to_numpy(float) for v in levels[1:])
    return np.column_stack(cols)


def beta_from_moments(m):
    """FWL using FE Gram pseudoinverse, supporting a batch of moments."""
    g=m[..., :-2,:-2]; zx=m[..., :-2,-2]; zy=m[..., :-2,-1]
    inv=np.linalg.pinv(g,rcond=1e-12,hermitian=True)
    fitted=np.einsum('...ij,...j->...i',inv,zx)
    den=m[..., -2,-2]-np.einsum('...i,...i->...',zx,fitted)
    num=m[..., -2,-1]-np.einsum('...i,...i->...',zy,fitted)
    ok=den>1e-10*np.maximum(1,m[..., -2,-2])
    return np.divide(num,den,out=np.full_like(np.asarray(num,float),np.nan),where=ok)


def adjusted(a,col):
    f=np.column_stack([design(a),a[col].to_numpy(float),a.R.to_numpy(float)])
    return float(beta_from_moments(f.T@f))


def raw_slope(a,col):
    x=a[col].to_numpy(float); y=a.R.to_numpy(float); xc=x-x.mean()
    den=xc@xc
    return float(xc@(y-y.mean())/den) if den>0 else np.nan


def strategy_rows(a,col,period):
    rows=[]
    for no,g in a.groupby('StrategyNo'):
        eligible=len(g)>=30 and g.Week.nunique()>=20 and g[col].nunique()>=3
        rows.append(dict(Feature=col,Period=period,StrategyNo=no,Strategy=g.Strategy.iloc[0],
            Trades=len(g),Weeks=g.Week.nunique(),MeanCount=g[col].mean(),Distinct=g[col].nunique(),
            RawSlope=raw_slope(g,col),QAdjustedSlope=adjusted(g,col),Eligible=eligible,
            DiagnosticLabel='EXPLORATORY_STRATEGY_SIGNAL' if eligible else 'INSUFFICIENT_SAMPLE'))
    return rows


def bootstrap(a,col,reps=5000):
    z=design(a); f=np.column_stack([z,a[col],a.R])
    weeks=sorted(a.Week.unique())
    moments=np.stack([f[a.Week.eq(w)].T@f[a.Week.eq(w)] for w in weeks])
    rng=np.random.Generator(np.random.PCG64(20260913))
    draws=rng.integers(0,len(weeks),(reps,len(weeks)))
    weights=np.stack([np.bincount(d,minlength=len(weeks)) for d in draws])
    b=[]
    for start in range(0,reps,250):
        m=(weights[start:start+250]@moments.reshape(len(weeks),-1)).reshape(-1,f.shape[1],f.shape[1])
        b.extend(beta_from_moments(m))
    b=np.asarray(b); good=b[np.isfinite(b)]
    ci=np.quantile(good,[.025,.975],method='linear') if len(good)>=.95*reps else [np.nan,np.nan]
    return b,float(ci[0]),float(ci[1]),len(good)


def distribution(a,col):
    x=a[col]
    return dict(Trades=len(a),Weeks=a.Week.nunique(),Strategies=a.StrategyNo.nunique(),
        Min=int(x.min()),Max=int(x.max()),Mean=float(x.mean()),Median=float(x.median()),
        P05=float(x.quantile(.05)),P25=float(x.quantile(.25)),P75=float(x.quantile(.75)),
        P95=float(x.quantile(.95)),P99=float(x.quantile(.99)),Distinct=x.nunique(),
        LargestBucketFraction=float(x.value_counts().max()/len(x)))


def decide(periods,loso):
    p={(r['Feature'],r['Period']):r for r in periods}; a=p[FEATURES[0],'ALL']; s=sign(a['Beta'])
    hist=p[FEATURES[0],'Historical']; rec=p[FEATURES[0],'Recent Combined']
    recent=[p[FEATURES[0],k] for k in ('Recent A','Recent B','2026 Monitor')]
    enough=(a['Trades']==15837 and a['EligibleStrategies']>=10 and a['Distinct']>=4 and
        a['LargestBucketFraction']<.9 and np.isfinite(a['CILower']) and
        all(x['Distinct']>=2 and np.isfinite(x['Beta']) for x in (hist,rec)))
    gates=dict(A=s!=0 and sign(a['RawSlope'])==s,
        B=np.isfinite(a['CILower']) and (a['CILower']>0 or a['CIUpper']<0),
        C=s!=0 and sign(a['EqualWeightSlope'])==s,
        D=s!=0 and all(sign(x['Beta'])==s for x in (hist,rec)),
        E=s!=0 and sum(x['PeriodEligible'] for x in recent)>=2 and sum(x['PeriodEligible'] and sign(x['Beta'])==s for x in recent)>=2,
        F=s!=0 and sign(p[FEATURES[1],'ALL']['Beta'])==s,G=bool(enough),
        H=s!=0 and len(loso)==27 and all(sign(x['Beta'])==s for x in loso))
    if not gates['G']: verdict='INSUFFICIENT_CROWDING_VARIATION'
    elif all(gates.values()): verdict='SIGNAL_CROWDING_SUPPORTED_'+('POSITIVE' if s>0 else 'NEGATIVE')
    elif not gates['A'] or not gates['B']: verdict='NOT_SUPPORTED'
    elif not gates['D'] or not gates['E']: verdict='UNSTABLE_ACROSS_PERIODS'
    else: verdict='ROBUSTNESS_FAIL'
    return gates,verdict


def save(out,name,rows):
    pd.DataFrame(rows).to_csv(out/(PREFIX+name+'.csv'),index=False,float_format='%.15g')


def analyse(a,out):
    periods=[]; strategies=[]; counts=[]; distributions=[]; draws=[]; symbols=[]
    for col in FEATURES:
        for period,(start,end) in PERIODS.items():
            g=a[(a.EntryTime>=start)&(a.EntryTime<end)]
            dist=distribution(g,col); sr=strategy_rows(g,col,period); strategies.extend(sr)
            beta=adjusted(g,col); eligible=[r['RawSlope'] for r in sr if r['Eligible']]
            b,lo,hi,valid=bootstrap(g,col)
            pe=len(g)>=200 and dist['Weeks']>=20 and dist['Strategies']>=10 and dist['Distinct']>=4 and dist['LargestBucketFraction']<.9 and np.isfinite(beta)
            periods.append(dict(Feature=col,Period=period,**dist,RawSlope=raw_slope(g,col),Beta=beta,
                CILower=lo,CIUpper=hi,ValidBootstrap=valid,EqualWeightSlope=float(np.mean(eligible)) if eligible else np.nan,
                EligibleStrategies=len(eligible),PeriodEligible=bool(pe),SampleStatus='ELIGIBLE' if pe else 'INSUFFICIENT_SAMPLE'))
            draws.extend(dict(Feature=col,Period=period,Replicate=i,Beta=float(v)) for i,v in enumerate(b))
            distributions.append(dict(Feature=col,Scope='Period',Name=period,**dist))
            for count,q in g.groupby(col): counts.append(dict(Feature=col,Period=period,SignalCount=int(count),**metric(q.R)))
            print(col+' '+period+' fitted',flush=True)
        for no,g in a.groupby('StrategyNo'):
            distributions.append(dict(Feature=col,Scope='Strategy',Name=str(no),**distribution(g,col)))
        for symbol,g in a.groupby('Symbol'):
            for count,q in g.groupby(col): symbols.append(dict(Feature=col,Symbol=symbol,SignalCount=int(count),**metric(q.R)))
    beta=next(r['Beta'] for r in periods if r['Feature']==FEATURES[0] and r['Period']=='ALL')
    loso=[dict(OmittedStrategy=int(no),Beta=adjusted(a[a.StrategyNo.ne(no)],FEATURES[0])) for no in sorted(a.StrategyNo.unique())]
    for r in loso:r.update(Sign=sign(r['Beta']),DeltaVsFull=r['Beta']-beta)
    simultaneous=[]
    for label,mask in [('0',a.SAME_TIMESTAMP_OTHER_SIGNALS==0),('1',a.SAME_TIMESTAMP_OTHER_SIGNALS==1),
                       ('2',a.SAME_TIMESTAMP_OTHER_SIGNALS==2),('>=3',a.SAME_TIMESTAMP_OTHER_SIGNALS>=3)]:
        simultaneous.append(dict(OtherSimultaneous=label,**metric(a.loc[mask,'R'])))
    gates,verdict=decide(periods,loso)
    tables=dict(portfolio_summary=[r for r in periods if r['Period']=='ALL'],period_summary=periods,
        strategy_summary=strategies,count_summary=counts,distribution_summary=distributions,
        symbol_summary=symbols,simultaneous_summary=simultaneous,
        leave_one_strategy_out=loso,formal_gates=[dict(Gate=k,Pass=bool(v),Verdict=verdict) for k,v in gates.items()],
        bootstrap_draws_local=draws)
    tables['12h_robustness']=[r for r in periods if r['Feature']==FEATURES[1]]
    tables['trade_feature_summary']=[dict(Trades=len(a),Strategies=a.StrategyNo.nunique(),
        EntryMin=str(a.EntryTime.min()),EntryMax=str(a.EntryTime.max()),R2Unavailable=int(a.R2Category.eq('R2_UNAVAILABLE').sum()),
        SimultaneousTrades=int(a.SAME_TIMESTAMP_OTHER_SIGNALS.gt(0).sum()),TotalR=float(a.R.sum()))]
    for name,rs in tables.items():save(out,name,rs)
    save(out,'trade_assignments_local',a)
    indices={0,len(a)-1}
    for q in (0,.5,1):
        target=a[FEATURES[0]].quantile(q)
        indices.add(int((a[FEATURES[0]]-target).abs().idxmin()))
    indices.update(a[a.SAME_TIMESTAMP_OTHER_SIGNALS.gt(0)].groupby('SAME_TIMESTAMP_OTHER_SIGNALS').head(1).index)
    indices.update(a.groupby('Symbol').head(1).index)
    manual=[]
    for i in sorted(indices):
        r=a.loc[i]; window=a[(a.EntryTime>=r.EntryTime-pd.Timedelta(hours=6))&(a.EntryTime<=r.EntryTime)&a.TradeID.ne(r.TradeID)]
        manual.append(dict(TradeID=r.TradeID,EntryTime=str(r.EntryTime),StrategyNo=r.StrategyNo,Symbol=r.Symbol,
            Count6H=r[FEATURES[0]],Count12H=r[FEATURES[1]],Simultaneous=r.SAME_TIMESTAMP_OTHER_SIGNALS,
            WindowOtherIDs='|'.join(map(str,window.TradeID)),WindowSymbols='|'.join(sorted(window.Symbol.unique()))))
    save(out,'manual_audit',manual)
    return verdict


def main():
    ap=argparse.ArgumentParser()
    for k in ('baseline','r2-assignment','out','implementation-sha'):ap.add_argument('--'+k,required=True)
    args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    a,checks=load_inputs(args.baseline,args.r2_assignment)
    print('Baseline, active universe and frozen R2 regression PASS',flush=True)
    result=analyse(a,out)
    save(out,'validation',checks)
    save(out,'run_record',[dict(PlanSHA=PLAN_SHA,ImplementationSHA=args.implementation_sha,BaselineSHA=BASELINE_SHA,
        R2AssignmentSHA=R2_SHA,Trades=len(a),Verdict=result,Phase2Eligible=result.startswith('SIGNAL_CROWDING_SUPPORTED'),
        BootstrapSeed=20260913,BootstrapReplicates=5000,Phase2Run=False,LiveChanged=False)])
    print(result,flush=True)


if __name__=='__main__':main()
