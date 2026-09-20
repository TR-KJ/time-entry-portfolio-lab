"""Pre-registered PDRP diagnosis. Never generates or filters baseline trades."""
from pathlib import Path
import argparse, json, math, sys
import numpy as np
import pandas as pd
from trend_strength_phase1 import load_baseline, load_m1, sha, stats

PLAN_COMMIT='41a45c04d51f5be9bdc8c08aeb4c8cc398dcd787'
BRANCH='research/pre-entry-price-action-phase1'
FROZEN=json.loads(Path(__file__).with_name('pre_entry_phase1_frozen_inputs.json').read_text())
STRATEGIES=FROZEN['STRATEGIES']
BUCKETS=['AGAINST_SIDE','MIDDLE','WITH_SIDE']
INS='INSUFFICIENT_PREENTRY_HISTORY'; FLAT='FLAT_PREENTRY_WINDOW'
METHODS={'primary':60,'robustness':180}
PERIODS={'ALL':('2015-01-01','2026-09-10'),'Historical':('2015-01-01','2022-01-01'),'Recent A':('2022-01-01','2024-01-01'),'Recent B':('2024-01-01','2026-01-01'),'2026 Monitor':('2026-01-01','2026-09-10')}
GROUPS={'Portfolio':list(range(1,29)),'Long':[s['StrategyNo'] for s in STRATEGIES if s['Long']],'Short':[s['StrategyNo'] for s in STRATEGIES if not s['Long']],'JPY':[s['StrategyNo'] for s in STRATEGIES if s['Pair'] in ['UJ','EJ','GJ','AJ']],'AUD_nonJPY':[s['StrategyNo'] for s in STRATEGIES if s['Pair'] in ['AU','EA','GA']]}

def classify(x):
    if not np.isfinite(x) or not 0<=x<=1: raise ValueError('Invalid PDRP')
    return BUCKETS[0] if x<1/3 else BUCKETS[1] if x<2/3 else BUCKETS[2]

def validate_times(index):
    if index.tz is not None or index.has_duplicates or not index.is_monotonic_increasing or not (index==index.floor('min')).all(): raise ValueError('Invalid minute index')

def assign(trades,bars,window):
    if window not in (60,180): raise ValueError('Unregistered window')
    validate_times(bars.index)
    if not (trades.EntryTime==trades.EntryTime.dt.floor('min')).all(): raise ValueError('Non-minute entry')
    times=bars.index.to_numpy();h=bars.High.to_numpy();l=bars.Low.to_numpy();c=bars.Close.to_numpy();rows=[]
    for row in trades.itertuples(index=False):
        e=row.EntryTime;start=e-pd.Timedelta(minutes=window)
        left=np.searchsorted(times,start.to_datetime64(),'left');right=np.searchsorted(times,e.to_datetime64(),'left')
        n=int(right-left);last=bars.index[right-1] if n else pd.NaT;first=bars.index[left] if n else pd.NaT
        age=(e-last).total_seconds()/60 if n else np.nan
        high=float(np.max(h[left:right])) if n else np.nan;low=float(np.min(l[left:right])) if n else np.nan;close=float(c[right-1]) if n else np.nan
        reason=[]
        if n<window*4//5: reason.append('COUNT_BELOW_MINIMUM')
        if not n or age>5: reason.append('NO_FRESH_CLOSE')
        x=np.nan
        if reason: bucket=INS
        elif high==low: bucket=FLAT;reason=['ZERO_RANGE']
        else:
            x=(close-low)/(high-low) if row.Direction=='Long' else (high-close)/(high-low)
            bucket=classify(x)
        if n and (first<start or last+pd.Timedelta(minutes=1)>e or last>=e): raise AssertionError('Lookahead')
        rows.append(dict(TradeID=row.TradeID,WindowMinutes=window,WindowStart=start,FirstM1=first,LastM1=last,LastCompletedAt=last+pd.Timedelta(minutes=1) if n else pd.NaT,Bars=n,ExpectedBars=window,RequiredBars=window*4//5,LastOpenAgeMinutes=age,H=high,L=low,Cpre=close,PDRP=x,Bucket=bucket,MissingReason='|'.join(reason)))
    return pd.DataFrame(rows)

def sign(x): return 0 if not np.isfinite(x) or x==0 else (1 if x>0 else -1)
def clear(lo,hi): return np.isfinite(lo) and np.isfinite(hi) and (lo>0 or hi<0)

def bootstrap(a,start,end):
    first=pd.Timestamp(start);first-=pd.Timedelta(days=first.weekday())
    last=pd.Timestamp(end)-pd.Timedelta(days=1);last-=pd.Timedelta(days=last.weekday())
    nw=(last-first).days//7+1;rng=np.random.default_rng(20260913)
    weights=np.array([np.bincount(rng.integers(0,nw,nw),minlength=nw) for _ in range(5000)],dtype=float)
    sums=np.zeros((nw,28,2));counts=np.zeros_like(sums)
    for j,b in enumerate([BUCKETS[0],BUCKETS[2]]):
        x=a[a.Bucket==b];w=((x.EntryTime.dt.normalize()-first).dt.days//7).to_numpy();s=x.StrategyNo.to_numpy()-1
        np.add.at(sums,(w,s,np.full(len(x),j)),x.R.to_numpy());np.add.at(counts,(w,s,np.full(len(x),j)),1)
    bs=(weights@sums.reshape(nw,56)).reshape(5000,28,2);bc=(weights@counts.reshape(nw,56)).reshape(5000,28,2)
    return bs,bc

def ci_for(bs,bc,ids,equal=False):
    ids=np.asarray(ids,dtype=int)-1
    if len(ids)==0:return dict(CILow=np.nan,CIHigh=np.nan,ValidBootstraps=0)
    s=bs[:,ids,:];c=bc[:,ids,:]
    if equal:
        ok=(c>0).all(axis=(1,2));delta=np.mean(s[ok,:,1]/c[ok,:,1]-s[ok,:,0]/c[ok,:,0],axis=1)
    else:
        s=s.sum(axis=1);c=c.sum(axis=1);ok=(c>0).all(axis=1);delta=s[ok,1]/c[ok,1]-s[ok,0]/c[ok,0]
    nv=int(ok.sum());lo,hi=np.quantile(delta,[.025,.975],method='linear') if nv>=4750 else (np.nan,np.nan)
    return dict(CILow=float(lo),CIHigh=float(hi),ValidBootstraps=nv)

def support(delta,ediff,same,n,ci):
    reasons=[]
    if not clear(ci['CILow'],ci['CIHigh']): reasons.append('A_CI_NOT_EXCLUDING_ZERO')
    if not sign(delta) or sign(ediff)!=sign(delta): reasons.append('B_EQUAL_WEIGHT_NOT_ALIGNED')
    if not n or same<=n/2: reasons.append('C_NO_STRICT_MAJORITY')
    return ('SUPPORTED' if not reasons else 'NOT_SUPPORTED'),'|'.join(reasons)

def combined(p,r):
    if p['Support']!='SUPPORTED': return 'NOT_SUPPORTED'
    if sign(p['PooledDelta'])==sign(r['PooledDelta']) and sign(r['PooledDelta']):
        return 'BOTH_SUPPORTED' if r['Support']=='SUPPORTED' else 'PRIMARY_SUPPORTED_ROBUSTNESS_ALIGNED'
    return 'UNSTABLE'

def tables(a,period,method):
    bs,bc=bootstrap(a,*PERIODS[period]);cells=[];groups=[];decisions=[];by={}
    for s in STRATEGIES:
        no=s['StrategyNo'];own=a[a.StrategyNo==no];m={b:stats(own.loc[own.Bucket==b,'R']) for b in BUCKETS}
        eligible=m[BUCKETS[0]]['Trades']>=20 and m[BUCKETS[2]]['Trades']>=20
        delta=m[BUCKETS[2]]['AvgR']-m[BUCKETS[0]]['AvgR'];by[no]=(m,delta,eligible);ci=ci_for(bs,bc,[no])
        for b in BUCKETS:cells.append(dict(Period=period,Method=method,StrategyNo=no,Strategy=s['Strategy'],Symbol=next(k for k,v in FROZEN['SYMBOL_TO_PAIR'].items() if v==s['Pair']),Direction='Long' if s['Long'] else 'Short',Bucket=b,**m[b],WithMinusAgainstAvgR=delta,Eligible=eligible,**ci,ClearContrast=eligible and clear(ci['CILow'],ci['CIHigh'])))
    for name,ids in GROUPS.items():
        own=a[a.StrategyNo.isin(ids)];m={b:stats(own.loc[own.Bucket==b,'R']) for b in BUCKETS};eligible=[i for i in ids if by[i][2]]
        delta=m[BUCKETS[2]]['AvgR']-m[BUCKETS[0]]['AvgR'];avg={b:float(np.mean([by[i][0][b]['AvgR'] for i in eligible])) if eligible else np.nan for b in BUCKETS};ediff=avg[BUCKETS[2]]-avg[BUCKETS[0]]
        same=sum(sign(by[i][1])==sign(delta) and sign(delta)!=0 for i in eligible)
        ci=ci_for(bs,bc,ids);eci=ci_for(bs,bc,eligible,True);state,reason=support(delta,ediff,same,len(eligible),ci)
        base=dict(Period=period,Method=method,Group=name,EligibleStrategies=len(eligible),EligibleIDs='|'.join(map(str,eligible)),SameSignStrategies=same)
        decisions.append(dict(**base,PooledDelta=delta,EqualWeightedDelta=ediff,**ci,Support=state,Reason=reason,Formal=period=='ALL' and name=='Portfolio'))
        for b in BUCKETS:
            groups.append(dict(**base,Aggregation='trade_weighted',Bucket=b,**m[b],WithMinusAgainstAvgR=delta,**ci))
            groups.append(dict(**base,Aggregation='strategy_equal_weighted',Bucket=b,AvgR=avg[b],WithMinusAgainstAvgR=ediff,**eci))
    return pd.DataFrame(cells),pd.DataFrame(groups),pd.DataFrame(decisions)

def select_audit(a):
    ids=set()
    for method in METHODS:
        x=a[a.Method==method].sort_values(['EntryTime','TradeID'])
        for z,keys in [(x,['Symbol','Direction']),(x[x.EntryTime.dt.weekday==0],['Symbol','Direction']),(x[x.WindowStart.dt.normalize()<x.EntryTime.dt.normalize()],['Symbol','Direction']),(x[x.Bucket.isin([INS,FLAT])],['Symbol','Direction','Bucket']),(x,['StrategyNo','Bucket'])]:
            ids.update((method,int(i)) for i in z.groupby(keys).head(1).TradeID)
    return a[[ (r.Method,int(r.TradeID)) in ids for r in a.itertuples()]].copy()

def run(baseline,m1_root,output_dir,implementation_sha):
    if len(implementation_sha)!=40 or any(c not in '0123456789abcdef' for c in implementation_sha): raise ValueError('Verified implementation SHA required')
    from verify_pre_entry_phase1 import verify_features, verify_tables, verify_ci
    import unittest
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parents[2]/'tests'),pattern='test_pre_entry_phase1.py')
    testresult=unittest.TextTestRunner(verbosity=1).run(suite)
    if not testresult.wasSuccessful() or not testresult.testsRun: raise AssertionError('Unit tests failed/absent')
    t=load_baseline(baseline);out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    files=list(Path(m1_root).rglob('*.csv'));resolved={};manifest=[];checks=[];assignments=[]
    # Validate ALL 56 hashes before calculating any real-data feature.
    for symbol,names in FROZEN['MANIFEST_NAMES'].items():
        paths=[]
        for name in names:
            matches=[p for p in files if p.name==name]
            if len(matches)!=1:raise ValueError(f'Expected exactly one {name}; found {len(matches)}')
            p=matches[0];actual=sha(p)
            if actual!=FROZEN['M1_SHA256'][name]:raise ValueError('M1 hash mismatch: '+name)
            paths.append(p)
        resolved[symbol]=paths
    for symbol,paths in resolved.items():
        bars,rows=load_m1(paths)
        for r in rows:
            if r['SHA256']!=FROZEN['M1_SHA256'][r['Filename']]:raise ValueError('M1 changed during run')
        manifest.extend(dict(Symbol=symbol,**r) for r in rows);own=t[t.Symbol==symbol]
        for method,window in METHODS.items():
            f=assign(own,bars,window);checks.append(verify_features(own,bars,f,window,symbol))
            assignments.append(own.merge(f,on='TradeID',validate='one_to_one').assign(Method=method))
        print(f'{symbol}: {len(bars):,} M1; both assignments independently checked',flush=True)
    a=pd.concat(assignments,ignore_index=True).sort_values(['Method','TradeID']).reset_index(drop=True)
    assert len(a)==32596 and not a.duplicated(['Method','TradeID']).any()
    tab={};periodtables=[];decisions=[];group_tables=[];coverage=[]
    for period,(start,end) in PERIODS.items():
        for method in METHODS:
            x=a[(a.Method==method)&(a.EntryTime>=start)&(a.EntryTime<end)]
            c,g,d=tables(x,period,method);checks.extend(verify_tables(x,c,g,d));checks.extend(verify_ci(x,g,c,*PERIODS[period]) if period=='ALL' else [])
            decisions.append(d)
            if period=='ALL':tab['strategy_'+method]=c;group_tables.append(g)
            else:periodtables.extend([c,g])
            for name,ids in list(GROUPS.items())+[(str(s['StrategyNo']),[s['StrategyNo']]) for s in STRATEGIES]:
                z=x[x.StrategyNo.isin(ids)]
                for b in BUCKETS+[INS,FLAT]:
                    n=int(z.Bucket.eq(b).sum());coverage.append(dict(Period=period,Method=method,Scope=name,Bucket=b,Trades=n,TotalTrades=len(z),Pct=100*n/len(z) if len(z) else np.nan))
            print(period,method,'aggregation verification PASS',flush=True)
    tab['group_summary']=pd.concat(group_tables,ignore_index=True);tab['period_summary']=pd.concat(periodtables,ignore_index=True);tab['coverage']=pd.DataFrame(coverage);tab['decision']=pd.concat(decisions,ignore_index=True)
    decision=tab['decision'];rows=[]
    for name in GROUPS:
        d=decision[(decision.Period=='ALL')&(decision.Group==name)].set_index('Method');v=combined(d.loc['primary'],d.loc['robustness'])
        rows.append(dict(Group=name,Verdict=v,Phase2Candidate=name=='Portfolio' and v in ['BOTH_SUPPORTED','PRIMARY_SUPPORTED_ROBUSTNESS_ALIGNED'],Formal=name=='Portfolio'))
    tab['combined_decision']=pd.DataFrame(rows);tab['input_manifest']=pd.DataFrame(manifest);tab['verification']=pd.DataFrame(checks)
    tab['trade_assignments']=a;tab['manual_audit']=select_audit(a);tab['assignment_audit_light']=tab['manual_audit'].copy()
    hashes={}
    for name,frame in tab.items():
        p=out/f'pre_entry_phase1_{name}.csv';frame.to_csv(p,index=False);hashes[p.name]=sha(p)
    cov={method:{b:int(((a.Method==method)&(a.Bucket==b)).sum()) for b in BUCKETS+[INS,FLAT]} for method in METHODS}
    record=dict(Status='COMPLETED',Branch=BRANCH,PlanCommit=PLAN_COMMIT,ImplementationCommit=implementation_sha,RunJST=pd.Timestamp.now(tz='Asia/Tokyo').isoformat(),BaselineSHA256=sha(baseline),BaselineTrades=len(t),StrategyCount=28,BaselineRecalculated=False,LiveChanged=False,InputFiles=len(manifest),M1HashesMatched=56,UnitTestsRun=testresult.testsRun,UnitTestsPassed=testresult.wasSuccessful(),IndependentFeatureRows=len(a),IndependentVerification='PASS',FreshHoldout=False,Bootstrap='calendar-week;5000;seed20260913;linear95%;minimum4750',Coverage=json.dumps(cov),Python=sys.version.split()[0],Pandas=pd.__version__,Numpy=np.__version__,OutputHashes=json.dumps(hashes,sort_keys=True))
    tab['run_record']=pd.DataFrame([record]);tab['run_record'].to_csv(out/'pre_entry_phase1_run_record.csv',index=False)
    print(tab['combined_decision'].to_string(index=False));return tab

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--m1-root',required=True);p.add_argument('--output-dir',default='/content');p.add_argument('--implementation-sha',required=True);v=p.parse_args();run(v.baseline,v.m1_root,v.output_dir,v.implementation_sha)
