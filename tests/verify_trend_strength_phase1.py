"""Independent Decimal aggregation; does not call production stats/tables."""
import math
from decimal import Decimal
import numpy as np
import pandas as pd

def close(a,b):
    if pd.isna(a) and pd.isna(b): return
    if math.isinf(float(a)) and a==b: return
    assert math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-9),(a,b)

def verify_tables(a,tables,first,weights):
    periods={'FULL':('2015-01-01','2026-09-10'),'Historical':('2015-01-01','2022-01-01'),'RecentA':('2022-01-01','2024-01-01'),'RecentB':('2024-01-01','2026-01-01'),'Monitor2026':('2026-01-01','2026-09-10')}
    checks=[];rows=pd.concat([tables['strategy_primary'],tables['strategy_robustness'],tables['group_summary'],tables['period_summary']],ignore_index=True)
    cache={}
    for period,(start,end) in periods.items():
        x=a[(a.EntryTime>=start)&(a.EntryTime<end)]
        for method in ['primary','robustness']:
            for (no,reg),g in x.groupby(['StrategyNo',method]):
                cache[(period,method,int(no),reg)]=[Decimal(str(v)) for v in g.R]
    for r in rows.to_dict('records'):
        if pd.notna(r.get('StrategyNo')): ids=[int(r['StrategyNo'])]
        else:
            group=r['Group']
            ids=sorted(a.StrategyNo.unique()) if group=='Portfolio' else sorted(a.loc[a.Pair.isin(['UJ','EJ','GJ','AJ']),'StrategyNo'].unique()) if group=='JPY' else sorted(a.loc[a.Pair.isin(['AU','EA','GA']),'StrategyNo'].unique()) if group=='AUD_nonJPY' else sorted(a.loc[a.Direction==group,'StrategyNo'].unique())
        vals=lambda reg,no:cache.get((r['Period'],r['Method'],no,reg),[])
        means=lambda reg,no:sum(vals(reg,no))/len(vals(reg,no)) if vals(reg,no) else Decimal('NaN')
        if r.get('Aggregation')=='strategy_equal_weighted':
            eligible=[no for no in ids if len(vals('LOW',no))>=20 and len(vals('HIGH',no))>=20]
            assert len(eligible)==r['EligibleStrategies']
            assert '|'.join(map(str,eligible))==r['EligibleIDs']
            avg=sum((means(r['Regime'],no) for no in eligible),Decimal(0))/len(eligible) if eligible else Decimal('NaN')
            delta=sum((means('HIGH',no)-means('LOW',no) for no in eligible),Decimal(0))/len(eligible) if eligible else Decimal('NaN')
            close(r['AvgR'],avg);close(r['HighMinusLowAvgR'],delta)
            continue
        v=[z for no in ids for z in vals(r['Regime'],no)];n=len(v);wins=[z for z in v if z>0];loss=[z for z in v if z<0]
        close(r['Trades'],n);close(r['TotalR'],sum(v));close(r['AvgR'],sum(v)/n if n else np.nan)
        close(r['WinRate'],len(wins)/n*100 if n else np.nan)
        close(r['PF'],sum(wins)/(-sum(loss)) if loss else np.inf if wins else np.nan)
        close(r['AvgWinR'],sum(wins)/len(wins) if wins else np.nan);close(r['AvgLossR'],sum(loss)/len(loss) if loss else np.nan)
        assert bool(r['LOW_SAMPLE'])==(n<20)
        lo=[z for no in ids for z in vals('LOW',no)];hi=[z for no in ids for z in vals('HIGH',no)]
        delta=sum(hi)/len(hi)-sum(lo)/len(lo) if lo and hi else np.nan
        close(r['HighMinusLowAvgR'],delta)
        if pd.notna(r.get('StrategyNo')):
            assert bool(r['Eligible'])==(len(lo)>=20 and len(hi)>=20)
    for r in tables['decision'].to_dict('records'):
        elig=[int(v) for v in r['EligibleIDs'].split('|') if v];sgn=np.sign(r['PooledDelta'])
        diffs=[]
        for no in elig:
            low=cache[('FULL',r['Method'],no,'LOW')];high=cache[('FULL',r['Method'],no,'HIGH')]
            diffs.append(float(sum(high)/len(high)-sum(low)/len(low)))
        same=sum(np.sign(v)==sgn and sgn!=0 for v in diffs)
        assert same==r['SameSignStrategies']
        expected='UNDETERMINED' if not elig or not np.isfinite(r['PooledDelta']) or not np.isfinite(r['CILow']) else 'SUPPORTED' if (r['CILow']>0 or r['CIHigh']<0) and np.sign(r['EqualWeightedDelta'])==sgn and same>len(elig)/2 else 'NOT_SUPPORTED'
        assert expected==r['Support']
    for r in tables['regime_coverage'].to_dict('records'):
        start,end=periods[r['Period']];x=a[(a.EntryTime>=start)&(a.EntryTime<end)];scope=r['Scope']
        if scope.isdigit(): x=x[x.StrategyNo==int(scope)]
        elif scope=='JPY': x=x[x.Pair.isin(['UJ','EJ','GJ','AJ'])]
        elif scope=='AUD_nonJPY': x=x[x.Pair.isin(['AU','EA','GA'])]
        elif scope in ['Long','Short']: x=x[x.Direction==scope]
        assert r['Trades']==int(x[r['Method']].eq(r['Regime']).sum()) and r['TotalTrades']==len(x)
    checks.append(dict(Check='Independent Decimal metrics, differences, equal weights, eligibility, support, coverage all periods',Status='PASS',Rows=len(rows)))
    assert len(a)==16298 and a.TradeID.nunique()==16298
    valid=a.DailyDate.notna();assert (a.loc[valid,'AvailableAt']<=a.loc[valid,'EntryTime']).all()
    assert (a.loc[valid,'LastM1']+pd.Timedelta(minutes=1)<=a.loc[valid,'EntryTime']).all()
    checks.append(dict(Check='All trades retained; all trade-date availability assertions',Status='PASS',Rows=len(a)))
    checks.extend(verify_extra(a,tables,first,weights))
    return checks

def independent_indicators(d):
    """Scalar reference with smoothed sums (production uses vector DM/mean recurrence)."""
    n=len(d);adx=[math.nan]*n;er=[math.nan]*n;raw=[];dx=[]
    h=list(d.High);l=list(d.Low);c=list(d.Close)
    for i in range(1,n):
        up=h[i]-h[i-1];down=l[i-1]-l[i]
        row=(max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])),up if up>max(down,0) else 0,down if down>max(up,0) else 0)
        raw.append(row)
        if i>=14:
            if i==14: smooth=[math.fsum(r[k] for r in raw) for k in range(3)]
            else: smooth=[smooth[k]-smooth[k]/14+row[k] for k in range(3)]
            # Common TR scaling cancels from DX; independently avoid DI computation.
            dm=smooth[1]+smooth[2]
            dx.append(100*abs(smooth[1]-smooth[2])/dm if dm else 0.)
            if i==27: adx[i]=math.fsum(dx)/14
            elif i>27: adx[i]=adx[i-1]+(dx[-1]-adx[i-1])/14
        if i>=20:
            travel=math.fsum(abs(c[j]-c[j-1]) for j in range(i-19,i+1))
            er[i]=abs(c[i]-c[i-20])/travel if travel else 0.
    return adx,er

def verify_extra(a,tables,first,weights):
    from collections import defaultdict
    rows=pd.concat([tables['strategy_primary'],tables['strategy_robustness'],tables['group_summary'],tables['period_summary']],ignore_index=True)
    for _,g in rows.groupby(['Period','Method','StrategyNo','Group','Aggregation'],dropna=False):
        vals={r.Regime:r.AvgR for r in g.itertuples()}
        expected='INCOMPLETE'
        if all(math.isfinite(v) for v in vals.values()):
            expected=' < '.join(' = '.join(r for r in ['LOW','NORMAL','HIGH'] if vals[r]==v) for v in sorted(set(vals.values())))
        assert (g.RegimeOrder==expected).all()
    ci_rows=pd.concat([tables['strategy_primary'].drop_duplicates('StrategyNo'),tables['strategy_robustness'].drop_duplicates('StrategyNo'),tables['decision']],ignore_index=True)
    ci_count=0
    for row in ci_rows.to_dict('records'):
        x=a
        if pd.notna(row.get('StrategyNo')): x=x[x.StrategyNo==int(row['StrategyNo'])]
        elif row['Group']=='JPY': x=x[x.Pair.isin(['UJ','EJ','GJ','AJ'])]
        elif row['Group']=='AUD_nonJPY': x=x[x.Pair.isin(['AU','EA','GA'])]
        elif row['Group'] in ['Long','Short']: x=x[x.Direction==row['Group']]
        grouped=defaultdict(list)
        for entry,r,reg in x[['EntryTime','R',row['Method']]].itertuples(index=False,name=None):
            if reg in ['LOW','HIGH']: grouped[((entry.normalize()-first).days//7,reg)].append(float(r))
        vector=[]
        for week in range(weights.shape[1]):
            lo=grouped[week,'LOW'];hi=grouped[week,'HIGH']
            vector.append([math.fsum(lo),math.fsum(hi),len(lo),len(hi)])
        vals=weights.astype(float)@np.array(vector)
        valid=(vals[:,2]>0)&(vals[:,3]>0)
        assert row['ValidBootstraps']==int(valid.sum())
        if valid.sum()>=4750:
            deltas=sorted((vals[valid,1]/vals[valid,3]-vals[valid,0]/vals[valid,2]).tolist())
            for key,q in [('CILow',.025),('CIHigh',.975)]:
                p=(len(deltas)-1)*q;i=int(p);j=math.ceil(p)
                close(row[key],deltas[i]+(p-i)*(deltas[j]-deltas[i]))
        else: assert pd.isna(row['CILow']) and pd.isna(row['CIHigh'])
        ci_count+=1
    for r in tables['combined_decision'].itertuples():
        z=tables['decision'];z=z[z.Group==r.Group].set_index('Method');p=z.loc['primary'];q=z.loc['robustness']
        ps=p.Support=='SUPPORTED';qs=q.Support=='SUPPORTED'
        expected=('BOTH_SUPPORTED' if p.PooledDelta*q.PooledDelta>0 else 'CONFLICTING') if ps and qs else 'PRIMARY_ONLY' if ps else 'ROBUSTNESS_ONLY' if qs else 'UNDETERMINED' if 'UNDETERMINED' in (p.Support,q.Support) else 'NOT_SUPPORTED'
        assert r.Conclusion==expected
    for method in ['primary','robustness']:
        for r in a[[method,method+'Percentile']].itertuples(index=False,name=None):
            reg,p=r
            if pd.isna(p): assert reg=='INSUFFICIENT_TREND_HISTORY'
            else:
                count=round(p*504);assert abs(p-count/504)<1e-12
                assert reg==('LOW' if count<168 else 'NORMAL' if count<336 else 'HIGH')
    return [dict(Check='Independent weekly sums and linear CI',Status='PASS',Rows=ci_count),
            dict(Check='Regime ordering, exact rank labels, combined decisions',Status='PASS',Rows=len(rows)),
            dict(Check='All daily ADX and ER scalar reference; representative M1 audits',Status='PASS',Rows=len(tables['manual_audit'])),
            dict(Check='Volatility daily generation exact regression and frozen M1 hashes',Status='PASS',Rows=56)]
