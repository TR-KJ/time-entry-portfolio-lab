"""Independent Decimal aggregation; does not call production stats/tables."""
import math
from decimal import Decimal
import numpy as np
import pandas as pd

def close(a,b):
    if pd.isna(a) and pd.isna(b): return
    if math.isinf(float(a)) and a==b: return
    assert math.isclose(float(a),float(b),rel_tol=1e-9,abs_tol=1e-9),(a,b)

def verify_tables(a,tables):
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
    return checks
