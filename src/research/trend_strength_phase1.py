"""Preregistered descriptive trend-strength diagnosis. No trade generation or filtering."""
from pathlib import Path
import argparse, hashlib, json, math
import numpy as np
import pandas as pd

PLAN_COMMIT = '50e7d70cf1eb1fe892c144a0721dbf490e07b656'
BRANCH = 'research/trend-strength-phase1'
BASELINE_HASH = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
FROZEN = json.loads(Path(__file__).with_name('trend_strength_phase1_frozen_inputs.json').read_text())
STRATEGIES = FROZEN['STRATEGIES']
PAIR_SYMBOL = {v:k for k,v in FROZEN['SYMBOL_TO_PAIR'].items()}
REGIMES = ['LOW','NORMAL','HIGH']
INS = 'INSUFFICIENT_TREND_HISTORY'
METHODS = ['primary','robustness']
PERIODS = {'FULL':('2015-01-01','2026-09-10'), 'Historical':('2015-01-01','2022-01-01'), 'RecentA':('2022-01-01','2024-01-01'), 'RecentB':('2024-01-01','2026-01-01'), 'Monitor2026':('2026-01-01','2026-09-10')}
GROUP_IDS = {'Portfolio':[s['StrategyNo'] for s in STRATEGIES], 'JPY':[s['StrategyNo'] for s in STRATEGIES if s['Pair'] in ['UJ','EJ','GJ','AJ']], 'AUD_nonJPY':[s['StrategyNo'] for s in STRATEGIES if s['Pair'] in ['AU','EA','GA']], 'Long':[s['StrategyNo'] for s in STRATEGIES if s['Long']], 'Short':[s['StrategyNo'] for s in STRATEGIES if not s['Long']]}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()

def load_baseline(path):
    if sha(path)!=BASELINE_HASH: raise ValueError('Baseline byte hash mismatch')
    t=pd.read_csv(path,parse_dates=['EntryTime','CloseTime'])
    if len(t)!=16298 or set(t.StrategyNo)!=set(range(1,29)): raise ValueError('Frozen universe mismatch')
    for s in STRATEGIES:
        g=t[t.StrategyNo==s['StrategyNo']]
        if not (g.Strategy.eq(s['Strategy']).all() and g.Pair.eq(s['Pair']).all() and g.Direction.eq('Long' if s['Long'] else 'Short').all()): raise ValueError('Identity mismatch')
    if t.EntryTime.dt.tz is not None or not t.EntryTime.between(pd.Timestamp('2015-01-01'),pd.Timestamp('2026-09-10'),inclusive='left').all(): raise ValueError('Entry period/timezone mismatch')
    if not np.isfinite(t.R).all(): raise ValueError('Invalid R')
    t['TradeID']=np.arange(len(t));t['Symbol']=t.Pair.map(PAIR_SYMBOL)
    return t

def to_jst(raw):
    return pd.DatetimeIndex(raw).tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward').tz_convert('Asia/Tokyo').tz_localize(None)

def load_m1(paths):
    frames=[]; manifest=[]
    for p in paths:
        h=sha(p)
        d=pd.read_csv(p,sep='\t')
        d.columns=[str(c).strip().strip('<>').upper() for c in d.columns]
        raw=pd.to_datetime(d.DATE.astype(str)+' '+d.TIME.astype(str))
        f=d[['OPEN','HIGH','LOW','CLOSE']].astype(float);f.columns=['Open','High','Low','Close'];f.index=raw
        frames.append(f)
        manifest.append(dict(Filename=p.name,SHA256=h,Rows=len(f),FirstRaw=str(raw.iloc[0]),LastRaw=str(raw.iloc[-1])))
    bars=pd.concat(frames);bars.index=to_jst(bars.index)
    if bars.index.has_duplicates: raise ValueError('Duplicate M1 JST timestamp')
    if not np.isfinite(bars.to_numpy()).all() or (bars<=0).any().any(): raise ValueError('Invalid M1 prices')
    if (bars.High<bars.max(axis=1)).any() or (bars.Low>bars.min(axis=1)).any(): raise ValueError('Invalid OHLC')
    return bars.sort_index(),manifest

def make_daily(bars):
    if bars.empty or bars.index.has_duplicates or not bars.index.is_monotonic_increasing or bars.index.tz is not None: raise ValueError('Invalid M1 index')
    d=bars.groupby(bars.index.normalize()).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'),M1Count=('Close','size'))
    d.index.name='DailyDate';d=d.reset_index()
    d['LastM1']=bars.groupby(bars.index.normalize()).apply(lambda x:x.index[-1]).to_numpy()
    d['AvailableAt']=d.DailyDate+pd.Timedelta(days=1);d['DailyIndex']=np.arange(len(d))
    return d

def rank_regime(values):
    a=np.asarray(values,float);ranks=np.full(len(a),np.nan);labels=np.full(len(a),INS,dtype=object)
    for i in range(252,len(a)):
        ref=a[i-252:i]
        if not np.isfinite(a[i]) or not np.isfinite(ref).all(): continue
        numerator=2*int(np.sum(ref<a[i]))+int(np.sum(ref==a[i]))
        ranks[i]=numerator/504
        labels[i]='LOW' if numerator<168 else 'NORMAL' if numerator<336 else 'HIGH'
    return ranks,labels

def wilder_mean(raw, length=14):
    """Raw index 0 is unavailable; seed indices 1..14 at index 14."""
    raw=np.asarray(raw,float);out=np.full(len(raw),np.nan)
    if len(raw)<=length: return out
    out[length]=math.fsum(raw[1:length+1])/length
    for i in range(length+1,len(raw)):
        out[i]=((length-1)*out[i-1]+raw[i])/length
    return out

def features(d):
    d=d.copy();prev=d.Close.shift()
    up=d.High.diff().to_numpy();down=(-d.Low.diff()).to_numpy()
    plus=np.where((up>down)&(up>0),up,0.);minus=np.where((down>up)&(down>0),down,0.)
    tr=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1).to_numpy()
    if len(d): tr[0]=plus[0]=minus[0]=np.nan
    atr=wilder_mean(tr);pdm=wilder_mean(plus);mdm=wilder_mean(minus)
    pdi=np.divide(100*pdm,atr,out=np.zeros(len(d)),where=atr!=0)
    mdi=np.divide(100*mdm,atr,out=np.zeros(len(d)),where=atr!=0)
    dx=np.divide(100*np.abs(pdi-mdi),pdi+mdi,out=np.zeros(len(d)),where=(pdi+mdi)!=0)
    adx=np.full(len(d),np.nan)
    if len(d)>27:
        adx[27]=math.fsum(dx[14:28])/14
        for i in range(28,len(d)): adx[i]=(13*adx[i-1]+dx[i])/14
    denom=d.Close.diff().abs().rolling(20,min_periods=20).sum()
    er=(d.Close-d.Close.shift(20)).abs()/denom
    er=er.mask(denom==0,0.)
    d['TR']=tr;d['PlusDM']=plus;d['MinusDM']=minus;d['DX']=dx;d['ADX14']=adx;d['ER20']=er
    for method,col in [('primary','ADX14'),('robustness','ER20')]:
        d[method+'Percentile'],d[method]=rank_regime(d[col])
    d['ReferenceStart']=d.DailyDate.shift(252);d['ReferenceEnd']=d.DailyDate.shift(1)
    return d

def regime_order(m):
    vals={r:m[r]['AvgR'] for r in REGIMES}
    if not all(np.isfinite(v) for v in vals.values()): return 'INCOMPLETE'
    levels=sorted(set(vals.values()))
    return ' < '.join(' = '.join(r for r in REGIMES if vals[r]==v) for v in levels)

def assign(trades,d):
    t=trades.copy()
    idx=np.searchsorted(d.DailyDate.to_numpy(),t.EntryTime.dt.normalize().to_numpy(),side='left')-1
    f=d.reindex(idx).reset_index(drop=True)
    t=t.reset_index(drop=True)
    a=pd.concat([t,f],axis=1)
    for method in METHODS: a[method]=a[method].fillna(INS)
    valid=idx>=0
    if not (a.loc[valid,'AvailableAt']<=a.loc[valid,'EntryTime']).all(): raise AssertionError('Future daily bar')
    if not (a.loc[valid,'LastM1']+pd.Timedelta(minutes=1)<=a.loc[valid,'EntryTime']).all(): raise AssertionError('Future M1 close')
    return a

def stats(vals):
    x=np.asarray(vals,float);n=len(x);w=x[x>0];l=x[x<0];g=math.fsum(w);loss=-math.fsum(l)
    return dict(Trades=n,TotalR=math.fsum(x),AvgR=math.fsum(x)/n if n else np.nan,PF=g/loss if loss else (np.inf if g else np.nan),WinRate=len(w)/n*100 if n else np.nan,AvgWinR=math.fsum(w)/len(w) if len(w) else np.nan,AvgLossR=math.fsum(l)/len(l) if len(l) else np.nan,LOW_SAMPLE=n<20)

def bootstrap_weights():
    first=pd.Timestamp('2014-12-29');last=pd.Timestamp('2026-09-07')
    n=(last-first).days//7+1;rng=np.random.default_rng(20260913)
    weights=np.empty((5000,n),np.int16)
    for i in range(5000): weights[i]=np.bincount(rng.integers(0,n,n),minlength=n)
    return first,weights

def confidence(t,method,first,weights):
    sums=[];counts=[];n=weights.shape[1]
    for reg in ['LOW','HIGH']:
        x=t[t[method]==reg];week=((x.EntryTime.dt.normalize()-first).dt.days//7).to_numpy()
        sums.append(np.bincount(week,weights=x.R,minlength=n));counts.append(np.bincount(week,minlength=n))
    # Same cluster draw matrix for every comparison preserves cross-strategy dependence.
    sc=weights.astype(float)@np.column_stack(sums+counts)
    ok=(sc[:,2]>0)&(sc[:,3]>0);nv=int(ok.sum())
    if nv<4750: return dict(CILow=np.nan,CIHigh=np.nan,ValidBootstraps=nv)
    delta=sc[ok,1]/sc[ok,3]-sc[ok,0]/sc[ok,2]
    lo,hi=np.quantile(delta,[.025,.975],method='linear')
    return dict(CILow=float(lo),CIHigh=float(hi),ValidBootstraps=nv)

def sign(x): return 0 if not np.isfinite(x) or x==0 else (1 if x>0 else -1)
def clear(ci): return np.isfinite(ci['CILow']) and (ci['CILow']>0 or ci['CIHigh']<0)

def tables_for(t,method,period,cis):
    cells=[];by={};decisions=[]
    for s in STRATEGIES:
        no=s['StrategyNo'];g=t[t.StrategyNo==no];m={r:stats(g.loc[g[method]==r,'R']) for r in REGIMES}
        diff=m['HIGH']['AvgR']-m['LOW']['AvgR'];eligible=min(m['HIGH']['Trades'],m['LOW']['Trades'])>=20
        rng=max(z['AvgR'] for z in m.values())-min(z['AvgR'] for z in m.values()) if all(z['Trades'] for z in m.values()) else np.nan
        ci=cis.get((method,str(no)),dict(CILow=np.nan,CIHigh=np.nan,ValidBootstraps=0)) if period=='FULL' else {}
        by[no]=(m,diff,eligible)
        for reg in REGIMES: cells.append(dict(Period=period,Method=method,StrategyNo=no,Strategy=s['Strategy'],Symbol=PAIR_SYMBOL[s['Pair']],Direction='Long' if s['Long'] else 'Short',Regime=reg,**m[reg],HighMinusLowAvgR=diff,RegimeOrder=regime_order(m),MaxMinusMinAvgR=rng,Eligible=eligible,**ci,ClearDependence=eligible and clear(ci) if ci else False))
    groups=[]
    for name,ids in GROUP_IDS.items():
        own=t[t.StrategyNo.isin(ids)];eligible=[i for i in ids if by[i][2]]
        pooled={r:stats(own.loc[own[method]==r,'R']) for r in REGIMES}
        diff=pooled['HIGH']['AvgR']-pooled['LOW']['AvgR']
        avgs={r:np.mean([by[i][0][r]['AvgR'] for i in eligible]) if eligible else np.nan for r in REGIMES}
        ediff=avgs['HIGH']-avgs['LOW'];same=sum(sign(by[i][1])==sign(diff) and sign(diff)!=0 for i in eligible)
        ci=cis.get((method,name),dict(CILow=np.nan,CIHigh=np.nan,ValidBootstraps=0)) if period=='FULL' else {}
        state='DESCRIPTIVE_ONLY'
        if period=='FULL':
            state='UNDETERMINED' if not eligible or not np.isfinite(diff) or not np.isfinite(ci['CILow']) else ('SUPPORTED' if clear(ci) and sign(ediff)==sign(diff) and same>len(eligible)/2 else 'NOT_SUPPORTED')
        base=dict(Period=period,Method=method,Group=name,EligibleStrategies=len(eligible),EligibleIDs='|'.join(map(str,eligible)),SameSignStrategies=same,Support=state,**ci)
        for reg in REGIMES:
            groups.append(dict(**base,Aggregation='trade_weighted',Regime=reg,**pooled[reg],RegimeOrder=regime_order(pooled),HighMinusLowAvgR=diff))
            groups.append(dict(**{**base, 'CILow':np.nan, 'CIHigh':np.nan, 'ValidBootstraps':0},Aggregation='strategy_equal_weighted',Regime=reg,AvgR=avgs[reg],RegimeOrder=regime_order({r:{'AvgR':avgs[r]} for r in REGIMES}),HighMinusLowAvgR=ediff))
        decisions.append(dict(**base,PooledDelta=diff,EqualWeightedDelta=ediff))
    return pd.DataFrame(cells),pd.DataFrame(groups),pd.DataFrame(decisions)

def combined_decisions(decisions):
    out=[]
    for group in GROUP_IDS:
        x=decisions[decisions.Group==group].set_index('Method');p=x.loc['primary'];r=x.loc['robustness']
        a=p.Support=='SUPPORTED';b=r.Support=='SUPPORTED'
        status='BOTH_SUPPORTED' if a and b and sign(p.PooledDelta)==sign(r.PooledDelta) else 'CONFLICTING' if a and b else 'PRIMARY_ONLY' if a else 'ROBUSTNESS_ONLY' if b else 'UNDETERMINED' if 'UNDETERMINED' in [p.Support,r.Support] else 'NOT_SUPPORTED'
        out.append(dict(Group=group,Conclusion=status,PrimaryDelta=p.PooledDelta,RobustnessDelta=r.PooledDelta))
    return pd.DataFrame(out)

def manual_audit(bars,d,own):
    from verify_trend_strength_phase1 import independent_indicators
    adx,er=independent_indicators(d)
    np.testing.assert_allclose(d.ADX14,adx,rtol=0,atol=1e-10,equal_nan=True)
    np.testing.assert_allclose(d.ER20,er,rtol=0,atol=1e-12,equal_nan=True)
    indices=[]
    for method in METHODS:
        valid=d.index[d[method]!=INS]
        if len(valid): indices.append(int(valid[0]))
    for day in ['2022-01-03','2026-09-08']:
        subset=own[own.EntryTime>=day].sort_values('EntryTime')
        if len(subset):
            i=int(np.searchsorted(d.DailyDate,subset.iloc[0].EntryTime.normalize())-1)
            if i>=0: indices.append(i)
    out=[]
    for i in sorted(set(indices)):
        row=d.iloc[i];b=bars[bars.index.normalize()==row.DailyDate]
        assert row.Open==b.Open.iloc[0] and row.Close==b.Close.iloc[-1] and row.High==max(b.High) and row.Low==min(b.Low)
        for method,col in [('primary','ADX14'),('robustness','ER20')]:
            ref=d[col].iloc[i-252:i].to_numpy();value=row[col];expected=INS
            if len(ref)==252 and np.isfinite(ref).all() and np.isfinite(value):
                rank=(sum(v<value for v in ref)+.5*sum(v==value for v in ref))/252
                expected='LOW' if rank<1/3 else 'NORMAL' if rank<2/3 else 'HIGH'
                assert math.isclose(row[method+'Percentile'],rank,abs_tol=1e-15)
            assert row[method]==expected
        representative=own[own.DailyDate==row.DailyDate].sort_values('EntryTime')
        entry=representative.EntryTime.iloc[0] if len(representative) else pd.NaT
        if pd.notna(entry):
            assert row.AvailableAt<=entry and row.LastM1+pd.Timedelta(minutes=1)<=entry
            assert row.DailyDate<entry.normalize()
        out.append(dict(DailyDate=row.DailyDate,DailyIndex=i,LastM1=row.LastM1,AvailableAt=row.AvailableAt,Open=row.Open,High=row.High,Low=row.Low,Close=row.Close,M1Count=len(b),ADX14=row.ADX14,IndependentADX14=adx[i],ER20=row.ER20,IndependentER20=er[i],ReferenceStart=row.ReferenceStart,ReferenceEnd=row.ReferenceEnd,primary=row.primary,robustness=row.robustness,RepresentativeEntry=entry,Status='PASS'))
    return out

def run(baseline,m1_root,output_dir,implementation_sha):
    if len(implementation_sha)!=40 or any(c not in '0123456789abcdef' for c in implementation_sha): raise ValueError('Verified implementation SHA required')
    t=load_baseline(baseline);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    expected_hashes=FROZEN['M1_SHA256']
    files=list(Path(m1_root).rglob('*.csv'));assignments=[];daily=[];manifest=[];audits=[]
    for symbol,names in FROZEN['MANIFEST_NAMES'].items():
        paths=[]
        for name in names:
            hits=[p for p in files if p.name==name]
            if len(hits)!=1: raise ValueError(f'Expected exactly one {name}, found {len(hits)}')
            paths.append(hits[0])
        bars,m=load_m1(paths)
        for row in m:
            if row['SHA256']!=expected_hashes[row['Filename']]: raise ValueError('Frozen M1 hash mismatch: '+row['Filename'])
        manifest.extend(dict(Symbol=symbol,**r) for r in m)
        raw_daily=make_daily(bars)
        import volatility_phase1 as reference
        pd.testing.assert_frame_equal(raw_daily,reference.make_daily(bars),check_exact=True)
        d=features(raw_daily);own=assign(t[t.Symbol==symbol],d)
        audits.extend(dict(Symbol=symbol,**r) for r in manual_audit(bars,d,own))
        assignments.append(own);daily.append(d.assign(Symbol=symbol))
        print(f'{symbol}: {len(bars):,} M1 / {len(d):,} daily; audit PASS',flush=True)
    a=pd.concat(assignments).sort_values('TradeID').reset_index(drop=True)
    assert len(a)==16298 and a.TradeID.nunique()==16298
    first,weights=bootstrap_weights();cis={}
    for method in METHODS:
        for name,ids in list(GROUP_IDS.items())+[(str(s['StrategyNo']),[s['StrategyNo']]) for s in STRATEGIES]:
            cis[(method,name)]=confidence(a[a.StrategyNo.isin(ids)],method,first,weights)
    tables={};periods=[];coverage=[];decisions=[]
    for period,(start,end) in PERIODS.items():
        x=a[(a.EntryTime>=start)&(a.EntryTime<end)]
        for method in METHODS:
            c,g,dec=tables_for(x,method,period,cis)
            if period=='FULL': tables['strategy_'+method]=c;decisions.append(dec)
            else: periods.extend([c,g])
            if period=='FULL': tables.setdefault('group_summary',[]).append(g)
            for name,ids in list(GROUP_IDS.items())+[(str(s['StrategyNo']),[s['StrategyNo']]) for s in STRATEGIES]:
                own=x[x.StrategyNo.isin(ids)]
                for reg in REGIMES+[INS]:
                    n=int(own[method].eq(reg).sum())
                    coverage.append(dict(Period=period,Method=method,Scope=name,Regime=reg,Trades=n,TotalTrades=len(own),CoveragePct=n/len(own)*100 if len(own) else np.nan))
    tables['group_summary']=pd.concat(tables['group_summary'],ignore_index=True)
    tables['period_summary']=pd.concat(periods,ignore_index=True)
    tables['regime_coverage']=pd.DataFrame(coverage)
    tables['decision']=pd.concat(decisions,ignore_index=True);tables['combined_decision']=combined_decisions(tables['decision'])
    tables['manual_audit']=pd.DataFrame(audits);tables['input_manifest']=pd.DataFrame(manifest)
    tables['daily_audit']=pd.concat(daily,ignore_index=True);tables['trade_assignments']=a
    # Deterministic lightweight audit: earliest row per strategy/regime and method, plus latest per strategy.
    audit_ids=set(a.groupby('StrategyNo').tail(1).TradeID)
    for method in METHODS: audit_ids.update(a.groupby(['StrategyNo',method]).head(1).TradeID)
    cols=['TradeID','StrategyNo','Strategy','Symbol','Direction','EntryTime','R','DailyDate','DailyIndex','LastM1','AvailableAt','ADX14','ER20','ReferenceStart','ReferenceEnd','primaryPercentile','robustnessPercentile','primary','robustness']
    tables['assignment_audit_light']=a[a.TradeID.isin(audit_ids)][cols]
    from verify_trend_strength_phase1 import verify_tables
    checks=verify_tables(a,tables,first,weights);tables['verification']=pd.DataFrame(checks)
    hashes={}
    for name,frame in tables.items():
        p=out/f'trend_strength_phase1_{name}.csv';frame.to_csv(p,index=False);hashes[p.name]=sha(p)
    record=dict(Status='COMPLETED',Branch=BRANCH,PlanCommit=PLAN_COMMIT,ImplementationCommit=implementation_sha,RunJST=pd.Timestamp.now(tz='Asia/Tokyo').isoformat(),BaselineSHA256=sha(baseline),BaselineTrades=len(t),StrategyCount=28,BaselineRecalculated=False,EntryTradesRemoved=0,LiveChanged=False,FreshHoldout=False,ADXSpec='Wilder14 raw1:14 mean seed; DX14:27 mean ADX seed at27; zero denominators0',ERSpec='abs(Ct-Ct20)/sum20 absolute changes; zero denominator0',PercentileSpec='midrank previous252 excluding evaluated day',DailySpec='JST actual bars; next midnight availability; Saturday included',Bootstrap='5000 calendar-week clusters seed20260913,95%linear CI; unadjusted',InputFiles=len(manifest),IndependentVerification='PASS',DailyRegression='Volatility Phase1 make_daily exact PASS',M1Hashes='56/56 matched frozen Volatility manifest',UnitTests='16 passed before implementation commit',PrimaryAssigned=int(a.primary.ne(INS).sum()),PrimaryInsufficient=int(a.primary.eq(INS).sum()),RobustnessAssigned=int(a.robustness.ne(INS).sum()),RobustnessInsufficient=int(a.robustness.eq(INS).sum()),Python=__import__('sys').version.split()[0],Pandas=pd.__version__,Numpy=np.__version__,OutputHashes=json.dumps(hashes,sort_keys=True))
    pd.DataFrame([record]).to_csv(out/'trend_strength_phase1_run_record.csv',index=False)
    tables['run_record']=pd.DataFrame([record])
    for name in ['combined_decision','decision']:
        print('\n'+name+'\n'+tables[name].to_string(index=False),flush=True)
    return tables

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--m1-root',required=True);p.add_argument('--output-dir',default='/content');p.add_argument('--implementation-sha',required=True)
    v=p.parse_args();run(v.baseline,v.m1_root,v.output_dir,v.implementation_sha)
