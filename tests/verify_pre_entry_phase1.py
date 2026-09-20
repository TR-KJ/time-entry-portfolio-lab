"""Independent mask/reindex, Python aggregation and resampling checks."""
import math
import numpy as np
import pandas as pd

BUCKETS=['AGAINST_SIDE','MIDDLE','WITH_SIDE']

def close(a,b):
    np.testing.assert_allclose(a,b,rtol=1e-10,atol=1e-12,equal_nan=True)

def verify_features(trades,bars,features,window,symbol):
    # Reindex exact expected minutes, unlike production searchsorted slices.
    got=features.set_index('TradeID');count=0
    for row in trades.itertuples(index=False):
        expected=pd.date_range(row.EntryTime-pd.Timedelta(minutes=window),periods=window,freq='min')
        z=bars.reindex(expected).dropna();n=len(z);r=got.loc[row.TradeID]
        assert r.Bars==n
        if n:
            hi=max(z.High.tolist());lo=min(z.Low.tolist());c=z.Close.iloc[-1];age=(row.EntryTime-z.index[-1]).total_seconds()/60
            close([r.H,r.L,r.Cpre,r.LastOpenAgeMinutes],[hi,lo,c,age]);assert r.FirstM1==z.index[0] and r.LastM1==z.index[-1]
            assert z.index[-1]+pd.Timedelta(minutes=1)<=row.EntryTime
        else:hi=lo=c=age=np.nan
        if n<window*0.8 or n==0 or age>5:label='INSUFFICIENT_PREENTRY_HISTORY';v=np.nan
        elif hi==lo:label='FLAT_PREENTRY_WINDOW';v=np.nan
        else:
            v=(c-lo)/(hi-lo) if row.Direction=='Long' else (hi-c)/(hi-lo)
            label=BUCKETS[int(v>=1/3)+int(v>=2/3)]
        assert label==r.Bucket;close(v,r.PDRP);count+=1
    return dict(Check='IndependentAllFeatureAssignments',Scope=symbol,Window=window,Rows=count,Status='PASS')

def independent_stats(values):
    values=list(values);n=len(values);wins=[r for r in values if r>0];losses=[r for r in values if r<0];pos=math.fsum(wins);neg=-math.fsum(losses)
    return {'Trades':n,'TotalR':math.fsum(values),'AvgR':math.fsum(values)/n if n else np.nan,'PF':pos/neg if neg else (np.inf if pos else np.nan),'WinRate':100*len(wins)/n if n else np.nan,'AvgWinR':math.fsum(wins)/len(wins) if wins else np.nan,'AvgLossR':math.fsum(losses)/len(losses) if losses else np.nan,'LOW_SAMPLE':n<20}

def verify_tables(a,c,g,d):
    from pre_entry_price_action_phase1 import GROUPS
    values={}
    for r in a.itertuples(index=False):values.setdefault((r.StrategyNo,r.Bucket),[]).append(r.R)
    ds={};eligible={};nchecks=0
    for row in c.itertuples(index=False):
        m=independent_stats(values.get((row.StrategyNo,row.Bucket),[]))
        for k,v in m.items():close(getattr(row,k),v)
        lo=independent_stats(values.get((row.StrategyNo,BUCKETS[0]),[]));hi=independent_stats(values.get((row.StrategyNo,BUCKETS[2]),[]))
        delta=hi['AvgR']-lo['AvgR'];ok=lo['Trades']>=20 and hi['Trades']>=20
        close(row.WithMinusAgainstAvgR,delta);assert row.Eligible==ok;ds[row.StrategyNo]=delta;eligible[row.StrategyNo]=ok;nchecks+=1
    for row in g.itertuples(index=False):
        ids=GROUPS[row.Group];es=[i for i in ids if eligible[i]];assert row.EligibleIDs=='|'.join(map(str,es))
        if row.Aggregation=='trade_weighted':
            m=independent_stats([v for i in ids for v in values.get((i,row.Bucket),[])])
            for k,v in m.items():close(getattr(row,k),v)
            lo=independent_stats([v for i in ids for v in values.get((i,BUCKETS[0]),[])])['AvgR'];hi=independent_stats([v for i in ids for v in values.get((i,BUCKETS[2]),[])])['AvgR'];delta=hi-lo
        else:
            av=[independent_stats(values.get((i,row.Bucket),[]))['AvgR'] for i in es];expected=sum(av)/len(av) if av else np.nan;close(row.AvgR,expected);delta=sum(ds[i] for i in es)/len(es) if es else np.nan
        close(row.WithMinusAgainstAvgR,delta);nchecks+=1
    for row in d.itertuples(index=False):
        es=[i for i in GROUPS[row.Group] if eligible[i]];delta=row.PooledDelta
        same=sum((ds[i]>0 and delta>0) or (ds[i]<0 and delta<0) for i in es)
        assert row.SameSignStrategies==same and row.EligibleStrategies==len(es)
        ew=sum(ds[i] for i in es)/len(es) if es else np.nan;close(row.EqualWeightedDelta,ew)
        supported=(row.CILow>0 or row.CIHigh<0) and ((ew>0 and delta>0) or (ew<0 and delta<0)) and same>len(es)/2
        assert (row.Support=='SUPPORTED')==supported;nchecks+=1
    return [dict(Check='IndependentAllTables',Scope=f'{c.Period.iloc[0]}/{c.Method.iloc[0]}',Rows=nchecks,Status='PASS')]

def verify_ci(a,g,c,start,end):
    from pre_entry_price_action_phase1 import GROUPS
    first=pd.Timestamp(start)-pd.Timedelta(days=pd.Timestamp(start).weekday());last=pd.Timestamp(end)-pd.Timedelta(days=1);nw=(last-first).days//7+1
    # Build weekly sums/counts by Python dictionaries and calendar dates.
    cells={}
    for r in a.itertuples(index=False):
        if r.Bucket not in [BUCKETS[0],BUCKETS[2]]:continue
        monday=r.EntryTime.date()-__import__('datetime').timedelta(days=r.EntryTime.weekday());w=(monday-first.date()).days//7
        cells.setdefault((w,r.StrategyNo,0 if r.Bucket==BUCKETS[0] else 1),[]).append(r.R)
    sums=np.zeros((nw,28,2));counts=np.zeros_like(sums)
    for (w,s,b),v in cells.items():sums[w,s-1,b]=math.fsum(v);counts[w,s-1,b]=len(v)
    targets=[]
    for name,ids in GROUPS.items():
        for agg in ['trade_weighted','strategy_equal_weighted']:
            row=g[(g.Group==name)&(g.Aggregation==agg)].iloc[0];chosen=ids if agg=='trade_weighted' else [int(i) for i in row.EligibleIDs.split('|') if i]
            targets.append((name+'/'+agg,chosen,agg=='strategy_equal_weighted',row))
    for no in [1,14,28]:targets.append((str(no),[no],False,c[c.StrategyNo==no].iloc[0]))
    draws={name:[] for name,_,_,_ in targets};rng=np.random.default_rng(20260913)
    # Direct sampled-week addition, deliberately not production matrix multiplication.
    for _ in range(5000):
        sample=rng.integers(0,nw,nw);ss=sums[sample].sum(axis=0);cc=counts[sample].sum(axis=0)
        for name,ids,equal,row in targets:
            if not ids:continue
            idx=np.array(ids)-1;s=ss[idx];ct=cc[idx]
            if equal:
                if (ct==0).any():continue
                diff=np.mean(s[:,1]/ct[:,1]-s[:,0]/ct[:,0])
            else:
                s=s.sum(axis=0);ct=ct.sum(axis=0)
                if (ct==0).any():continue
                diff=s[1]/ct[1]-s[0]/ct[0]
            draws[name].append(diff)
    checks=[]
    for name,_,_,row in targets:
        v=sorted(draws[name]);assert len(v)==row.ValidBootstraps
        if len(v)>=4750:
            def percentile(q):
                p=(len(v)-1)*q;i=int(p);f=p-i;return v[i]+f*(v[min(i+1,len(v)-1)]-v[i])
            expected=[percentile(.025),percentile(.975)]
        else:expected=[np.nan,np.nan]
        close([row.CILow,row.CIHigh],expected);checks.append(dict(Check='IndependentBootstrapCI',Scope=a.Method.iloc[0]+'/'+name,Rows=len(v),Status='PASS'))
    return checks
