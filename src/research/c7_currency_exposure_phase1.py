"""Preregistered C7 currency exposure diagnosis; fixed baseline outcomes only."""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

import c6_signal_crowding_phase1 as c6
from c4_vol_change_phase1 import metric
from exit_efficiency_phase1 import BASELINE_SHA, PERIODS

PLAN_SHA = '2cd828fe008303ab07838d38b5a8cbc9d02ed55f'
PREFIX = 'c7_currency_exposure_phase1_'
CURRENCIES = ('USD', 'EUR', 'GBP', 'JPY', 'AUD')
SYMBOLS = ('USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'AUDUSD', 'EURAUD', 'GBPAUD')
TICKS = {'Q1': 5, 'Q2': 7, 'Q3': 9, 'Q4': 11, 'Q5': 13, 'R2_UNAVAILABLE': 9}
VARIANTS = ('Primary', 'EqualUnit', 'SameSymbolIncluded')
STATES = ('DIVERSIFYING', 'NEUTRAL', 'CONCENTRATING')
TOL = 1e-10
sign = c6.sign


def vector(symbol, direction, weight):
    if symbol not in SYMBOLS or direction not in ('Long', 'Short'):
        raise ValueError('invalid currency pair/direction')
    v = np.zeros(5, dtype=np.int64)
    d = 1 if direction == 'Long' else -1
    v[CURRENCIES.index(symbol[:3])] = d * weight
    v[CURRENCIES.index(symbol[3:])] = -d * weight
    return v


def state(nic):
    return np.where(nic < -TOL, STATES[0], np.where(nic > TOL, STATES[2], STATES[1]))


def load_inputs(baseline, r2):
    a, checks = c6.load_inputs(baseline, r2)
    b = pd.read_csv(baseline, parse_dates=['EntryTime', 'CloseTime'])
    a = a.merge(b[['StrategyNo', 'EntryTime', 'CloseTime']], on=['StrategyNo', 'EntryTime'], validate='one_to_one')
    # Remove inherited crowding diagnostics; these never enter C7 models.
    a = a.drop(columns=['SIGNAL_COUNT_6H', 'SIGNAL_COUNT_12H', 'SAME_TIMESTAMP_OTHER_SIGNALS'])
    assert a.CloseTime.gt(a.EntryTime).all() and a.EntryTime.is_monotonic_increasing
    a['RiskWeight'] = a.R2Category.map(TICKS) / 10
    assert a.RiskWeight.notna().all()
    checks.append(dict(Check='actual_exit_order', Status='PASS', Detail='CloseTime > EntryTime for every active trade'))
    return a, checks


def reconstruct(frame):
    """Sweep complete timestamp batches; append batch only after all candidates."""
    a = frame[frame.StrategyNo.ne(22)].sort_values(['EntryTime', 'StrategyNo'], kind='stable').reset_index(drop=True).copy()
    if a.duplicated(['StrategyNo', 'EntryTime']).any():
        raise ValueError('duplicate identity')
    if not a.CloseTime.gt(a.EntryTime).all():
        raise ValueError('invalid actual exit')
    ticks = a.R2Category.map(TICKS)
    if ticks.isna().any():
        raise ValueError('unrecognized R2 category')
    a['RiskWeight'] = ticks / 10
    vectors = np.stack([vector(s, d, int(w)) for s, d, w in zip(a.Symbol, a.Direction, ticks)])
    units = np.stack([vector(s, d, 1) for s, d in zip(a.Symbol, a.Direction)])
    rows = []; batches = []; active = []
    for t, batch in a.groupby('EntryTime', sort=True):
        active = [j for j in active if a.at[j, 'CloseTime'] > t]
        for i in batch.index:
            cross = [j for j in active if a.at[j, 'Symbol'] != a.at[i, 'Symbol']]
            row = {'SimultaneousOther': len(batch) - 1}
            for v in VARIANTS:
                ids = active if v == 'SameSymbolIncluded' else cross
                source = units if v == 'EqualUnit' else vectors
                scale = 1 if v == 'EqualUnit' else 10
                weight = 1 if v == 'EqualUnit' else int(ticks.iloc[i])
                before = source[ids].sum(axis=0) if ids else np.zeros(5, dtype=np.int64)
                after = before + source[i]
                gb = int(np.abs(before).sum()); ga = int(np.abs(after).sum())
                nic = (ga - gb) / (2 * weight)
                assert -1 - TOL <= nic <= 1 + TOL and before.sum() == after.sum() == 0
                row.update({v+'_GrossBefore': gb/scale, v+'_GrossAfter': ga/scale,
                            v+'_Count': len(ids), v+'_HasOpen': int(bool(ids)), v+'_NIC': nic,
                            v+'_OpenIDs': '|'.join(a.loc[ids, 'TradeID'].astype(str))})
                for k, c in enumerate(CURRENCIES):
                    row[v+'_Before_'+c] = before[k]/scale
                    row[v+'_After_'+c] = after[k]/scale
                    row[v+'_DeltaAbs_'+c] = (abs(after[k])-abs(before[k]))/scale
            rows.append(row)
        if len(batch) > 1:
            before = vectors[active].sum(axis=0) if active else np.zeros(5, dtype=np.int64)
            after = before + vectors[batch.index].sum(axis=0)
            r = dict(EntryTime=t, Trades=len(batch), PriorOpenCount=len(active),
                     TradeIDs='|'.join(batch.TradeID.astype(str)),
                     PriorOpenIDs='|'.join(a.loc[active, 'TradeID'].astype(str)),
                     GrossBefore=np.abs(before).sum()/10, GrossAfter=np.abs(after).sum()/10)
            for k, c in enumerate(CURRENCIES):
                r['Before_'+c] = before[k]/10; r['After_'+c] = after[k]/10
                r['DeltaAbs_'+c] = (abs(after[k])-abs(before[k]))/10
            batches.append(r)
        active.extend(batch.index)
    a = pd.concat([a, pd.DataFrame(rows)], axis=1)
    a['Week'] = a.EntryTime.dt.to_period('W-SUN').dt.start_time.astype(str)
    for v in VARIANTS:
        a[v+'_State'] = state(a[v+'_NIC'])
    return a, batches


def design(a, variant):
    z = np.column_stack([c6.design(a), a[[variant+'_GrossBefore', variant+'_Count', variant+'_HasOpen']].to_numpy(float)])
    scales = np.sqrt(np.mean(z*z, axis=0)); scales[scales == 0] = 1
    return z / scales


def model_matrix(a, variant):
    return np.column_stack([design(a, variant), a[variant+'_NIC'], a.R])


def adjusted(a, variant):
    f = model_matrix(a, variant)
    return float(c6.beta_from_moments(f.T @ f))


def design_audit(a, variant, scope):
    z = design(a, variant); x = a[variant+'_NIC'].to_numpy(float)
    m = np.column_stack([z, x]); sv = np.linalg.svd(m, compute_uv=False)
    residual = x-z@np.linalg.lstsq(z, x, rcond=None)[0]
    return dict(Variant=variant, Scope=scope, Trades=len(a), Columns=m.shape[1],
                Rank=int(np.linalg.matrix_rank(m)), MinSingular=float(sv[-1]),
                MaxSingular=float(sv[0]), Condition=float(sv[0]/sv[-1]) if sv[-1]>0 else np.inf,
                NICResidualSS=float(residual@residual), Identifiable=bool(residual@residual>TOL*max(1, x@x)))


def bootstrap(a, variant, reps=5000):
    f = model_matrix(a, variant); weeks = sorted(a.Week.unique())
    moments = np.stack([f[a.Week.eq(w)].T@f[a.Week.eq(w)] for w in weeks])
    rng = np.random.Generator(np.random.PCG64(20260913))
    draws = rng.integers(len(weeks), size=(reps, len(weeks)))
    weights = np.stack([np.bincount(d, minlength=len(weeks)) for d in draws])
    betas = []
    for start in range(0, reps, 250):
        m = (weights[start:start+250] @ moments.reshape(len(weeks), -1)).reshape(-1, f.shape[1], f.shape[1])
        betas.extend(c6.beta_from_moments(m))
    betas = np.asarray(betas); good = betas[np.isfinite(betas)]
    lo, hi = np.quantile(good, [.025, .975], method='linear') if len(good)>=.95*reps else (np.nan, np.nan)
    return betas, lo, hi, len(good)


def distribution(a, v):
    x = a[v+'_NIC']; n = len(a); has = a[v+'_HasOpen'].eq(1)
    return dict(Trades=n, Weeks=a.Week.nunique(), Strategies=a.StrategyNo.nunique(),
                MeanGrossBefore=a[v+'_GrossBefore'].mean(), MedianGrossBefore=a[v+'_GrossBefore'].median(),
                OpenTrades=int(has.sum()), NoOpenTrades=int((~has).sum()), OpenStrategies=a.loc[has, 'StrategyNo'].nunique(),
                Min=x.min(), Max=x.max(), Mean=x.mean(), Median=x.median(), SD=x.std(ddof=0), Variance=x.var(ddof=0),
                Q10=x.quantile(.1), Q25=x.quantile(.25), Q75=x.quantile(.75), Q90=x.quantile(.9),
                Negative=int(x.lt(-TOL).sum()), Zero=int(x.abs().le(TOL).sum()), Positive=int(x.gt(TOL).sum()),
                Distinct=x.round(12).nunique(), PlusOneFraction=float(np.isclose(x,1,rtol=0,atol=TOL).mean()))


def eligible(r):
    return (r['Trades']>=200 and r['Weeks']>=20 and r['Strategies']>=10 and r['Negative']>=30 and
            r['Positive']>=30 and r['Distinct']>=3 and r['Variance']>=.01 and r['OpenTrades']>=100 and np.isfinite(r['Beta']))


def decide(periods, loso):
    p = {(r['Variant'], r['Period']):r for r in periods}; a=p['Primary','ALL']; s=sign(a['Beta'])
    hr=[p['Primary', k] for k in ('Historical','Recent Combined')]
    recent=[p['Primary', k] for k in ('Recent A','Recent B','2026 Monitor')]
    enough=(a['Trades']==15837 and a['Strategies']==27 and a['Negative']>=200 and a['Positive']>=200 and
            a['Distinct']>=3 and a['Variance']>=.01 and a['OpenTrades']>=500 and a['OpenStrategies']>=10 and
            np.isfinite(a['Beta']) and np.isfinite(a['CILower']) and all(
                r['Negative']>=30 and r['Positive']>=30 and r['Weeks']>=20 and r['Distinct']>=3 and
                r['Variance']>=.01 and np.isfinite(r['Beta']) for r in hr))
    gates=dict(A=s!=0 and sign(a['RawSignDifference'])==s,
               B=np.isfinite(a['CILower']) and (a['CILower']>0 or a['CIUpper']<0),
               C=s!=0 and all(sign(r['Beta'])==s for r in hr),
               D=s!=0 and sum(eligible(r) and sign(r['Beta'])==s for r in recent)>=2,
               E=s!=0 and sign(p['EqualUnit','ALL']['Beta'])==s,
               F=s!=0 and sign(p['SameSymbolIncluded','ALL']['Beta'])==s,
               G=s!=0 and len(loso)==27 and all(sign(r['Beta'])==s for r in loso), H=bool(enough))
    if not gates['H']: verdict='INSUFFICIENT_EXPOSURE_VARIATION'
    elif all(gates.values()): verdict='CURRENCY_EXPOSURE_SUPPORTED_'+('POSITIVE' if s>0 else 'NEGATIVE')
    elif not gates['A'] or not gates['B']: verdict='NOT_SUPPORTED'
    elif not gates['C'] or not gates['D']: verdict='UNSTABLE_ACROSS_PERIODS'
    else: verdict='ROBUSTNESS_FAIL'
    return gates, verdict


def save(out, name, rows):
    pd.DataFrame(rows).to_csv(Path(out)/(PREFIX+name+'.csv'), index=False, float_format='%.15g')


def analyse(a, batches, out):
    periods=[]; draws=[]; dist=[]; raw=[]; designs=[]; strategies=[]; symbols=[]; currencies=[]
    for v in VARIANTS:
        selected=PERIODS if v=='Primary' else {'ALL':PERIODS['ALL']}
        for period,(start,end) in selected.items():
            g=a[(a.EntryTime>=start)&(a.EntryTime<end)]
            d=distribution(g,v); beta=adjusted(g,v); b,lo,hi,valid=bootstrap(g,v)
            means={s:g.loc[g[v+'_State'].eq(s),'R'].mean() for s in STATES}
            r=dict(Variant=v,Period=period,**d,Beta=beta,CILower=lo,CIUpper=hi,ValidBootstrap=valid,
                   RawSlope=c6.raw_slope(g,v+'_NIC'),RawSignDifference=means[STATES[2]]-means[STATES[0]])
            r['PeriodEligible']=eligible(r); periods.append(r)
            draws.extend(dict(Variant=v,Period=period,Replicate=i,Beta=value) for i,value in enumerate(b))
            dist.append(dict(Variant=v,Scope='Period',Name=period,**d)); designs.append(design_audit(g,v,period))
            for s in STATES:
                raw.append(dict(Variant=v,Period=period,State=s,**metric(g.loc[g[v+'_State'].eq(s),'R'])))
            print(v+' '+period+' fitted',flush=True)
    for no,g in a.groupby('StrategyNo'):
        d=distribution(g,'Primary'); beta=adjusted(g,'Primary')
        ok=len(g)>=30 and d['Weeks']>=20 and d['Negative']>=10 and d['Positive']>=10 and d['Distinct']>=3 and np.isfinite(beta)
        strategies.append(dict(StrategyNo=no,Strategy=g.Strategy.iloc[0],**d,RawSlope=c6.raw_slope(g,'Primary_NIC'),
                               WithinStrategyAdjustedSlope=beta,SampleEligible=bool(ok),
                               DiagnosticLabel='EXPLORATORY_STRATEGY_SIGNAL' if ok else 'INSUFFICIENT_SAMPLE',
                               **{'AvgR_'+s:g.loc[g.Primary_State.eq(s),'R'].mean() for s in STATES}))
        dist.append(dict(Variant='Primary',Scope='Strategy',Name=str(no),**d))
        designs.append(design_audit(g,'Primary','Strategy'+str(no)))
    for symbol,g in a.groupby('Symbol'):
        d=distribution(g,'Primary');dist.append(dict(Variant='Primary',Scope='Symbol',Name=symbol,**d))
        for s in STATES:
            symbols.append(dict(Symbol=symbol,State=s,MeanNIC=g.Primary_NIC.mean(),
                                ConcentrationRate=d['Positive']/len(g),DiversificationRate=d['Negative']/len(g),
                                **metric(g.loc[g.Primary_State.eq(s),'R'])))
    for label,g in [('NoOpen',a[a.Primary_Count.eq(0)]),('HasOpen',a[a.Primary_Count.gt(0)])]:
        if len(g):dist.append(dict(Variant='Primary',Scope='OpenState',Name=label,**distribution(g,'Primary')))
    for c in CURRENCIES:
        col='Primary_DeltaAbs_'+c
        for s in STATES:
            g=a[state(a[col])==s]
            currencies.append(dict(Currency=c,AbsChangeState=s,MeanAbsChange=g[col].mean(),**metric(g.R)))
    full=next(r['Beta'] for r in periods if r['Variant']=='Primary' and r['Period']=='ALL')
    loso=[]
    for no in sorted(a.StrategyNo.unique()):
        g=a[a.StrategyNo.ne(no)];beta=adjusted(g,'Primary')
        loso.append(dict(OmittedStrategy=no,Beta=beta,Sign=sign(beta),DeltaVsFull=beta-full))
        designs.append(design_audit(g,'Primary','LOSO'+str(no)))
    gates,verdict=decide(periods,loso)
    tables=dict(portfolio_summary=[r for r in periods if r['Period']=='ALL'],period_summary=periods,
                nic_distribution=dist,raw_sign_summary=raw,strategy_summary=strategies,symbol_summary=symbols,
                currency_summary=currencies,equal_unit_robustness=[r for r in periods if r['Variant']=='EqualUnit'],
                same_symbol_robustness=[r for r in periods if r['Variant']=='SameSymbolIncluded'],
                leave_one_strategy_out=loso,simultaneous_diagnostic=batches,design_audit=designs,
                formal_gates=[dict(Gate=k,Pass=bool(v),Verdict=verdict) for k,v in gates.items()],bootstrap_draws_local=draws)
    tables['trade_feature_summary']=[dict(**distribution(a,'Primary'),TotalR=a.R.sum(),
        R2Unavailable=int(a.R2Category.eq('R2_UNAVAILABLE').sum()),FallbackWeight=.9,FallbackReason='INSUFFICIENT_VOL_HISTORY',
        SimultaneousTrades=int(a.SimultaneousOther.gt(0).sum()),SimultaneousBatches=len(batches))]
    masks={'no_open':a.Primary_Count.eq(0),'JPY_concentration':a.Primary_DeltaAbs_JPY.gt(TOL),
           'EUR_concentration':a.Primary_DeltaAbs_EUR.gt(TOL),'diversification':a.Primary_NIC.lt(-TOL),
           'multiple_open':a.Primary_Count.gt(1),'simultaneous_batch':a.SimultaneousOther.gt(0)}
    manual=[]
    for label,mask in masks.items():
        if mask.any():manual.append(dict(Case=label,**a.loc[mask].iloc[0].to_dict()))
        else:manual.append(dict(Case=label,Status='NO_OBSERVATION'))
    tables['manual_audit']=manual
    for name, rows in tables.items():save(out,name,rows)
    save(out,'trade_assignments_local',a)
    return verdict


def main():
    p=argparse.ArgumentParser()
    for k in ('baseline','r2-assignment','out','implementation-sha'):p.add_argument('--'+k,required=True)
    args=p.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    a,checks=load_inputs(args.baseline,args.r2_assignment)
    a,batches=reconstruct(a)
    print('Input validation and fixed full-timeline exposure reconstruction PASS',flush=True)
    verdict=analyse(a,batches,out)
    save(out,'validation',checks)
    save(out,'run_record',[dict(PlanSHA=PLAN_SHA,ImplementationSHA=args.implementation_sha,BaselineSHA=BASELINE_SHA,
        R2AssignmentSHA=c6.R2_SHA,Trades=len(a),Verdict=verdict,Phase2Eligible=verdict.startswith('CURRENCY_EXPOSURE_SUPPORTED'),
        BootstrapSeed=20260913,BootstrapReplicates=5000,Phase2Run=False,LiveChanged=False)])
    print(verdict,flush=True)


if __name__=='__main__':main()
