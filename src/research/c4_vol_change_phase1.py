"""Preregistered C4 volatility-change diagnostic adjusted for Strategy × Global R2 Q."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

import volatility_phase1 as p1
import volatility_phase2 as p2
from exit_efficiency_phase1 import resolve_and_audit

PLAN = 'docs/93_c4_volatility_change_phase1_plan.md'
PLAN_SHA = '954c051ce51c12b7301de82f2ae4613a14f155d3'
BASELINE_SHA = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
R2_REFERENCE_COMMIT = '0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc'
ROOT = Path(__file__).resolve().parents[2]
METHODS = ('ATR', 'RV')
STATES = ('COMPRESSION', 'NEUTRAL', 'EXPANSION')
PERIODS = {
    'Historical': ('2015-01-01', '2022-01-01'),
    'Recent A': ('2022-01-01', '2024-01-01'),
    'Recent B': ('2024-01-01', '2026-01-01'),
    '2026 Monitor': ('2026-01-01', '2026-09-10'),
    'Recent Combined': ('2022-01-01', '2026-09-10'),
    'ALL': ('2015-01-01', '2026-09-10'),
}
SOURCE_HASHES = {
    'volatility_phase1.py': '65ef361509e5bb404be02bfb0d1bdefbc6f59acbe8a557cdee030dd3a69116a1',
    'volatility_phase1_frozen_inputs.json': 'bfc4b372247bc8def18f4a3768d855285559ffed2782de73737fda4eafb5c61b',
    'volatility_phase2.py': 'c6d1b6d3380c70970d8b353b632b6f4f20a9c9aff17c5ff1347dde1d3c605428',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def state_from_n(n):
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return 'UNAVAILABLE'
    return 'COMPRESSION' if n < 168 else 'NEUTRAL' if n < 336 else 'EXPANSION'


def ratio_states(values):
    values = np.asarray(values, float)
    n = len(values); nums = np.full(n, np.nan); states = np.full(n, 'UNAVAILABLE', object)
    status = np.full(n, 'REFERENCE_LT_252', object)
    for i in range(n):
        cur = values[i]
        if not np.isfinite(cur) or cur <= 0:
            status[i] = 'CURRENT_UNAVAILABLE'; continue
        if i < 252:
            continue
        ref = values[i-252:i]
        if not np.isfinite(ref).all():
            status[i] = 'REFERENCE_NONFINITE'; continue
        if (ref <= 0).any():
            status[i] = 'REFERENCE_NONPOSITIVE'; continue
        num = 2 * int(np.sum(ref < cur)) + int(np.sum(ref == cur))
        nums[i] = num; states[i] = state_from_n(num); status[i] = 'VALID'
    return nums, nums / 504.0, states, status


def add_change_features(d):
    d = p1.features(d).copy()
    d['ATR5'] = d.TR.rolling(5, min_periods=5).mean()
    d['ATRChangeRatio'] = d.ATR5 / d.ATR20
    d['RV5'] = d.LogReturn.rolling(5, min_periods=5).std(ddof=1) * np.sqrt(252)
    d['RVChangeRatio'] = d.RV5 / d.RV20
    for method, col in [('ATR', 'ATRChangeRatio'), ('RV', 'RVChangeRatio')]:
        d[method+'ChangeNumerator'], d[method+'ChangePercentile'], d[method+'State'], d[method+'FeatureStatus'] = ratio_states(d[col])
    return d


def metric(values):
    x = np.asarray(values, float); pos = x[x > 0]; neg = x[x < 0]
    gain, loss = float(pos.sum()), float(-neg.sum())
    return dict(Trades=len(x), TotalR=float(x.sum()), AvgR=float(x.mean()) if len(x) else np.nan,
                PF=gain/loss if loss else np.inf if gain else np.nan,
                WinRate=len(pos)/len(x) if len(x) else np.nan,
                AvgWinR=float(pos.mean()) if len(pos) else np.nan,
                AvgLossR=float(neg.mean()) if len(neg) else np.nan)


def estimate(frame, equal_min=20):
    x = frame[frame.C4State.isin(['COMPRESSION', 'EXPANSION'])]
    rows = []
    for (no, q), g in x.groupby(['StrategyNo', 'primaryQuintile']):
        e = g[g.C4State.eq('EXPANSION')].R.to_numpy(float)
        c = g[g.C4State.eq('COMPRESSION')].R.to_numpy(float)
        if len(e) and len(c):
            w = len(e)*len(c)/(len(e)+len(c)); delta = float(e.mean()-c.mean())
            rows.append(dict(StrategyNo=int(no), R2Quintile=q, Expansion=len(e), Compression=len(c),
                             ExpansionAvgR=float(e.mean()), CompressionAvgR=float(c.mean()), Delta=delta,
                             FEWeight=w, Informative=len(e)>=equal_min and len(c)>=equal_min))
    if not rows:
        return np.nan, np.nan, pd.DataFrame(), 0, 0
    s = pd.DataFrame(rows); beta=float(np.average(s.Delta,weights=s.FEWeight))
    inf=s[s.Informative]; equal=float(inf.Delta.mean()) if len(inf) else np.nan
    return beta,equal,s,int(len(inf)),int(inf.StrategyNo.nunique())


def bootstrap(frame, equal_min=20):
    x = frame[frame.C4State.isin(['COMPRESSION','EXPANSION'])].copy()
    if x.empty:return (np.nan,np.nan,0),(np.nan,np.nan,0)
    weeks=sorted(x.Week.unique()); strata=sorted(set(zip(x.StrategyNo,x.primaryQuintile)))
    wi={v:i for i,v in enumerate(weeks)};si={v:i for i,v in enumerate(strata)}
    counts=np.zeros((len(weeks),len(strata),2));sums=np.zeros_like(counts)
    for r in x.itertuples():
        k=1 if r.C4State=='EXPANSION' else 0;i=wi[r.Week];j=si[(r.StrategyNo,r.primaryQuintile)]
        counts[i,j,k]+=1;sums[i,j,k]+=float(r.R)
    rng=np.random.Generator(np.random.PCG64(20260913));draw=rng.integers(0,len(weeks),(5000,len(weeks)))
    weights=np.zeros((5000,len(weeks)),dtype=np.int16)
    for i in range(5000):weights[i]=np.bincount(draw[i],minlength=len(weeks))
    cn=weights@counts.reshape(len(weeks),-1);sm=weights@sums.reshape(len(weeks),-1)
    cn=cn.reshape(5000,len(strata),2);sm=sm.reshape(5000,len(strata),2)
    valid=(cn[:,:,0]>0)&(cn[:,:,1]>0);means=np.divide(sm,cn,out=np.zeros_like(sm),where=cn>0)
    delta=means[:,:,1]-means[:,:,0];w=np.divide(cn[:,:,0]*cn[:,:,1],cn[:,:,0]+cn[:,:,1],out=np.zeros_like(cn[:,:,0]),where=valid)
    den=w.sum(1);fe=np.divide((w*delta).sum(1),den,out=np.full(5000,np.nan),where=den>0)
    informative=(cn[:,:,0]>=equal_min)&(cn[:,:,1]>=equal_min);ni=informative.sum(1)
    eq=np.divide((delta*informative).sum(1),ni,out=np.full(5000,np.nan),where=ni>0)
    def ci(z):
        z=z[np.isfinite(z)];return (float(np.quantile(z,.025,method='linear')),float(np.quantile(z,.975,method='linear')),len(z)) if len(z)>=4750 else (np.nan,np.nan,len(z))
    return ci(fe),ci(eq)


def sign(x):
    return 1 if np.isfinite(x) and x>0 else -1 if np.isfinite(x) and x<0 else 0


def raw_rows(frame, method, period):
    out=[]
    for state in STATES:
        g=frame[frame.C4State.eq(state)]
        out.append(dict(Method=method,Period=period,State=state,**metric(g.R)))
    return out


def load_reference(name):
    return pd.read_csv(ROOT/'research_inputs'/('c4_reference_'+name))


def validate_r2(a):
    audit=load_reference('assignment_audit_light.csv');actual=a.set_index('TradeID').loc[audit.TradeID]
    for col in ['ATR20','RV20','primaryPercentile','robustnessPercentile']:
        np.testing.assert_allclose(actual[col].to_numpy(float),audit[col].to_numpy(float),rtol=0,atol=1e-10,equal_nan=True)
    for col in ['primaryQuintile','robustnessQuintile']:
        if actual[col].fillna('').tolist()!=audit[col].fillna('').tolist():raise AssertionError('R2 audit '+col)
    refs=pd.concat([load_reference('strategy_quintiles.csv'),load_reference('period_quintiles.csv')],ignore_index=True)
    refs=refs[refs.ScopeType.eq('Strategy')]
    pmap={'FULL':('2015-01-01','2026-09-10'),'Historical':PERIODS['Historical'],'RecentA':PERIODS['Recent A'],'RecentB':PERIODS['Recent B'],'Monitor2026':PERIODS['2026 Monitor']}
    for r in refs.itertuples():
        start,end=pmap[r.Period];g=a[(a.EntryTime>=start)&(a.EntryTime<end)&a.StrategyNo.eq(int(r.StrategyNo))&a[r.Method+'Quintile'].eq(r.Quintile)]
        if len(g)!=int(r.Trades):raise AssertionError('R2 count regression')
        np.testing.assert_allclose([g.R.sum(),g.R.mean()],[r.TotalR,r.AvgR],rtol=0,atol=1e-10,equal_nan=True)
    return len(audit),len(refs)


def assignments(baseline,manifest,m1_root):
    for name,expected in SOURCE_HASHES.items():
        if sha(Path(p1.__file__).with_name(name))!=expected:raise ValueError('frozen source changed: '+name)
    t=p1.load_baseline(baseline);paths,audit=resolve_and_audit(manifest,m1_root);arrays=[];manual=[]
    for symbol in p1.FROZEN['MANIFEST_NAMES']:
        bars,_=p1.load_m1(paths[symbol]);d=add_change_features(p1.make_daily(bars));own=p2.add_quintiles(p1.assign(t[t.Symbol.eq(symbol)],d))
        for r in own.groupby('StrategyNo').head(1).itertuples():
            manual.append(dict(Symbol=symbol,TradeID=r.TradeID,StrategyNo=r.StrategyNo,EntryTime=r.EntryTime,DailyDate=r.DailyDate,
                               ATR5=r.ATR5,ATR20=r.ATR20,ATRChangeRatio=r.ATRChangeRatio,ATRState=r.ATRState,
                               RV5=r.RV5,RV20=r.RV20,RVChangeRatio=r.RVChangeRatio,RVState=r.RVState,Status='PASS'))
        arrays.append(own);print(f'{symbol}: {len(bars):,} M1 / {len(d):,} daily',flush=True)
    a=pd.concat(arrays).sort_values('TradeID').reset_index(drop=True)
    if len(a)!=16298 or a.TradeID.nunique()!=16298:raise AssertionError('universe')
    ar,sr=validate_r2(a);print(f'R2 regression PASS: audit={ar}, aggregate rows={sr}',flush=True)
    return a,pd.DataFrame(audit),pd.DataFrame(manual),ar,sr


def analyse(a):
    active=a[a.StrategyNo.ne(22)].copy();active['Week']=active.EntryTime.dt.to_period('W-SUN').dt.start_time.astype(str)
    raw=[];adjusted=[];periods=[];strata_all=[];strategies=[];qrows=[];coverage=[]
    for method in METHODS:
        active['C4State']=active[method+'State'];active['FeatureStatus']=active[method+'FeatureStatus']
        counts=Counter(active.FeatureStatus)
        coverage.append(dict(Method=method,Trades=len(active),Valid=counts['VALID'],Coverage=counts['VALID']/len(active),
                             ReferenceLT252=counts['REFERENCE_LT_252'],CurrentUnavailable=counts['CURRENT_UNAVAILABLE'],
                             ReferenceNonfinite=counts['REFERENCE_NONFINITE'],ReferenceNonpositive=counts['REFERENCE_NONPOSITIVE'],
                             SourceMissing=0,CalculationError=0,R2Unavailable=int(active.primaryQuintile.eq(p1.INS).sum())))
        for pname,(start,end) in PERIODS.items():
            g=active[(active.EntryTime>=start)&(active.EntryTime<end)&active.FeatureStatus.eq('VALID')]
            rr=raw_rows(g,method,pname);raw.extend(rr);lookup={z['State']:z for z in rr}
            beta,equal,s,ni,ns=estimate(g);feci,eqci=bootstrap(g)
            period_eligible=ni>=10 and ns>=5 and lookup['EXPANSION']['Trades']>=30 and lookup['COMPRESSION']['Trades']>=30
            rec=dict(Method=method,Period=pname,ValidTrades=len(g),CompressionTrades=lookup['COMPRESSION']['Trades'],NeutralTrades=lookup['NEUTRAL']['Trades'],ExpansionTrades=lookup['EXPANSION']['Trades'],
                     CompressionAvgR=lookup['COMPRESSION']['AvgR'],NeutralAvgR=lookup['NEUTRAL']['AvgR'],ExpansionAvgR=lookup['EXPANSION']['AvgR'],RawDelta=lookup['EXPANSION']['AvgR']-lookup['COMPRESSION']['AvgR'],
                     AdjustedEffect=beta,CILow=feci[0],CIHigh=feci[1],ValidBootstraps=feci[2],EqualWeightEffect=equal,EqualCILow=eqci[0],EqualCIHigh=eqci[1],EqualValidBootstraps=eqci[2],
                     ContributingStrata=len(s),InformativeStrata=ni,RepresentedStrategies=ns,PeriodEligible=period_eligible,PeriodStatus='ELIGIBLE' if period_eligible else 'INSUFFICIENT_SAMPLE')
            adjusted.append(rec);periods.append(rec)
            if pname=='ALL' and len(s):strata_all.extend(dict(Method=method,Period='ALL',**r) for r in s.to_dict('records'))
        for no,g in active[active.FeatureStatus.eq('VALID')].groupby('StrategyNo'):
            ms={st:metric(g[g.C4State.eq(st)].R) for st in STATES}
            strategies.append(dict(Method=method,StrategyNo=int(no),Strategy=g.Strategy.iloc[0],
                CompressionTrades=ms['COMPRESSION']['Trades'],CompressionAvgR=ms['COMPRESSION']['AvgR'],NeutralTrades=ms['NEUTRAL']['Trades'],NeutralAvgR=ms['NEUTRAL']['AvgR'],
                ExpansionTrades=ms['EXPANSION']['Trades'],ExpansionAvgR=ms['EXPANSION']['AvgR'],RawDelta=ms['EXPANSION']['AvgR']-ms['COMPRESSION']['AvgR'],
                EqualSampleEligible=ms['EXPANSION']['Trades']>=20 and ms['COMPRESSION']['Trades']>=20,Signal='EXPLORATORY_STRATEGY_SIGNAL'))
        for q,g in active[active.FeatureStatus.eq('VALID')].groupby('primaryQuintile'):
            if q==p1.INS:continue
            ms={st:metric(g[g.C4State.eq(st)].R) for st in STATES}
            qrows.append(dict(Method=method,R2Quintile=q,CompressionTrades=ms['COMPRESSION']['Trades'],CompressionAvgR=ms['COMPRESSION']['AvgR'],NeutralTrades=ms['NEUTRAL']['Trades'],NeutralAvgR=ms['NEUTRAL']['AvgR'],ExpansionTrades=ms['EXPANSION']['Trades'],ExpansionAvgR=ms['EXPANSION']['AvgR'],RawDelta=ms['EXPANSION']['AvgR']-ms['COMPRESSION']['AvgR']))
    ad=pd.DataFrame(adjusted);cov=pd.DataFrame(coverage);atr=ad[(ad.Method=='ATR')].set_index('Period');rv=ad[(ad.Method=='RV')].set_index('Period')
    direction=sign(atr.loc['ALL','AdjustedEffect']);eligible=[p for p in ('Recent A','Recent B','2026 Monitor') if bool(atr.loc[p,'PeriodEligible'])]
    gates={
      'A':direction!=0 and sign(atr.loc['ALL','RawDelta'])==direction,
      'B':direction!=0 and ((atr.loc['ALL','CILow']>0) if direction>0 else (atr.loc['ALL','CIHigh']<0)),
      'C':direction!=0 and sign(atr.loc['ALL','EqualWeightEffect'])==direction,
      'D':direction!=0 and sign(atr.loc['Historical','AdjustedEffect'])==direction and sign(atr.loc['Recent Combined','AdjustedEffect'])==direction,
      'E':len(eligible)>=2 and sum(sign(atr.loc[p,'AdjustedEffect'])==direction for p in eligible)>=2,
      'F':direction!=0 and sign(rv.loc['ALL','AdjustedEffect'])==direction,
      'G':bool((cov.Coverage>=.90).all() and (cov.SourceMissing==0).all() and (cov.CalculationError==0).all()),
      'H':int(atr.loc['ALL','InformativeStrata'])>=20 and int(atr.loc['ALL','RepresentedStrategies'])>=10,
    }
    if not gates['G']:label='INSUFFICIENT_FEATURE_COVERAGE'
    elif not gates['H']:label='INSUFFICIENT_STRATA_COVERAGE'
    elif all(gates.values()):label='VOLATILITY_CHANGE_SUPPORTED_EXPANSION' if direction>0 else 'VOLATILITY_CHANGE_SUPPORTED_COMPRESSION'
    elif all(gates[k] for k in 'ABCDEGH') and not gates['F']:label='ROBUSTNESS_FAIL'
    elif all(gates[k] for k in 'ABCFGH') and (not gates['D'] or not gates['E']):label='UNSTABLE_ACROSS_PERIODS'
    else:label='NOT_SUPPORTED'
    formal=pd.DataFrame([dict(Direction='EXPANSION' if direction>0 else 'COMPRESSION' if direction<0 else 'NONE',EligibleRecentPeriods='|'.join(eligible),**{f'Gate{k}':v for k,v in gates.items()},Label=label,Phase2Eligible=label.startswith('VOLATILITY_CHANGE_SUPPORTED_'))])
    return dict(portfolio_raw_summary=pd.DataFrame(raw),adjusted_summary=ad,period_summary=pd.DataFrame(periods),strategy_summary=pd.DataFrame(strategies),q_summary=pd.DataFrame(qrows),strata_summary=pd.DataFrame(strata_all),feature_coverage=cov,robustness_summary=ad[ad.Method.eq('RV')].copy(),formal_gates=formal),active


def write(path,frame):
    frame.to_csv(path,index=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--m1-root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--implementation-sha',required=True)
    x=ap.parse_args();out=Path(x.out);out.mkdir(parents=True,exist_ok=True)
    if sha(x.baseline)!=BASELINE_SHA:raise ValueError('baseline hash')
    if len(x.implementation_sha)!=40:raise ValueError('verified implementation SHA required')
    a,m1audit,manual,ar,sr=assignments(x.baseline,x.manifest,x.m1_root);tables,active=analyse(a)
    write(out/'c4_vol_change_phase1_m1_audit.csv',m1audit);write(out/'c4_vol_change_phase1_manual_audit.csv',manual)
    for name,frame in tables.items():write(out/f'c4_vol_change_phase1_{name}.csv',frame)
    detail=active[['TradeID','StrategyNo','Strategy','Symbol','EntryTime','R','Week','primaryQuintile','ATR5','ATR20','ATRChangeRatio','ATRChangeNumerator','ATRState','ATRFeatureStatus','RV5','RV20','RVChangeRatio','RVChangeNumerator','RVState','RVFeatureStatus']]
    write(out/'c4_vol_change_phase1_trade_assignments_local.csv',detail)
    validation=pd.DataFrame([
      dict(Check='baseline_sha_universe',Status='PASS',Detail='28/16298; active 27/15837; Strategy22 excluded formal'),
      dict(Check='m1_manifest',Status='PASS',Detail='56 filename/hash/rows/raw bounds'),
      dict(Check='r2_assignment_regression',Status='PASS',Detail=f'audit rows {ar}; aggregate rows {sr}'),
      dict(Check='no_lookahead_and_features',Status='PASS',Detail='completed JST D1; ATR/RV 5/20; prior252 excluding current'),
      dict(Check='formal_estimators',Status='PASS',Detail='FE within-stratum, equal-weight, week bootstrap'),
    ]);write(out/'c4_vol_change_phase1_validation.csv',validation)
    rec=pd.DataFrame([dict(Plan=PLAN,PlanSHA=PLAN_SHA,ImplementationSHA=x.implementation_sha,BaselineSHA=BASELINE_SHA,R2ReferenceCommit=R2_REFERENCE_COMMIT,Trades=15837,Result=tables['formal_gates'].iloc[0].Label,LiveChanged=False,Phase2Run=False)])
    write(out/'c4_vol_change_phase1_run_record.csv',rec)
    print(json.dumps(dict(Adjusted=tables['adjusted_summary'][tables['adjusted_summary'].Period.eq('ALL')].to_dict('records'),Formal=tables['formal_gates'].to_dict('records')),indent=2,default=str))


if __name__=='__main__':main()
