"""Independent CSV/Decimal aggregation, hand ranks, and weekly sufficient statistics.
Does not import production Phase 2 statistics, decisions, or aggregation functions.
"""
import csv
import math
from collections import defaultdict
from decimal import Decimal
import numpy as np
import pandas as pd

PERIODS = {'FULL': ('2015-01-01', '2026-09-10'), 'Historical': ('2015-01-01', '2022-01-01'),
           'RecentA': ('2022-01-01', '2024-01-01'), 'RecentB': ('2024-01-01', '2026-01-01'),
           'Monitor2026': ('2026-01-01', '2026-09-10')}
QS = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']


def close(x, y):
    x, y = float(x), float(y)
    if math.isnan(x) and math.isnan(y):
        return
    if x == y:
        return
    assert math.isclose(x, y, abs_tol=1e-10, rel_tol=0), (x, y)


def metric(v):
    n = len(v); w = [z for z in v if z > 0]; l = [z for z in v if z < 0]
    total = sum(v, Decimal(0)); profit = sum(w, Decimal(0)); loss = -sum(l, Decimal(0))
    return dict(Trades=n, TotalR=total, AvgR=total/n if n else math.nan,
                PF=profit/loss if loss else math.inf if profit else math.nan,
                WinRate=Decimal(len(w))*100/n if n else math.nan,
                AvgWinR=profit/len(w) if w else math.nan,
                AvgLossR=-loss/len(l) if l else math.nan, LOW_SAMPLE=n < 20)


def monotonic(x):
    complete = all(math.isfinite(float(v)) for v in x)
    xx = [float(v) for v in x]
    diffs = [xx[i+1]-xx[i] for i in range(4)]
    rho = math.nan
    if complete:
        ranks = [1+sum(y < z for y in xx)+(sum(y == z for y in xx)-1)/2 for z in xx]
        denom = math.sqrt(10*sum((r-3)**2 for r in ranks))
        if denom:
            rho = sum((i-2)*(r-3) for i, r in enumerate(ranks))/denom
    return dict(**{f'Q{i+1}AvgR': xx[i] for i in range(5)}, Q5MinusQ1AvgR=xx[4]-xx[0],
                **{f'Q{i+2}MinusQ{i+1}AvgR': diffs[i] for i in range(4)}, Spearman=rho,
                AdjacentIncreases=sum(v > 0 for v in diffs) if complete else math.nan,
                StrictlyIncreasing=complete and all(v > 0 for v in diffs),
                Nondecreasing=complete and all(v >= 0 for v in diffs), Complete=complete)


def verify_tables(path, tables, first, weights):
    with open(path, newline='') as f:
        records = list(csv.DictReader(f))
    cache = defaultdict(list); ids = list(range(1, 29)); identity = {}
    for r in records:
        no = int(r['StrategyNo']); identity[no] = r
        assert pd.Timestamp(r['AvailableAt']) <= pd.Timestamp(r['EntryTime'])
        assert pd.Timestamp(r['LastM1']) + pd.Timedelta(minutes=1) <= pd.Timestamp(r['EntryTime'])
        assert pd.Timestamp(r['DailyDate']).normalize() < pd.Timestamp(r['EntryTime']).normalize()
        for m in ['primary', 'robustness']:
            raw = r[m+'Percentile']
            if raw:
                rank = float(raw); n = round(rank*504)
                assert abs(rank-n/504) <= 1e-12
                q = 'Q1' if n <= 100 else 'Q2' if n <= 201 else 'Q3' if n <= 302 else 'Q4' if n <= 403 else 'Q5'
                reg = 'LOW' if n < 168 else 'NORMAL' if n < 336 else 'HIGH'
                assert r[m] == reg
            else:
                q = 'INSUFFICIENT_VOL_HISTORY'
            assert q == r[m+'Quintile']
            for period, (start, end) in PERIODS.items():
                if start <= r['EntryTime'] < end:
                    cache[(period, m, no, q)].append(Decimal(r['R']))
    groups = {'Portfolio': ids, 'JPY': [no for no in ids if identity[no]['Pair'] in ['UJ','EJ','GJ','AJ']],
              'AUD_nonJPY': [no for no in ids if identity[no]['Pair'] in ['AU','EA','GA']],
              'Long': [no for no in ids if identity[no]['Direction'] == 'Long'],
              'Short': [no for no in ids if identity[no]['Direction'] == 'Short']}
    def scope_ids(scope):
        return [int(scope)] if str(scope).isdigit() else groups[scope]
    def eligible(period, method, own):
        return [no for no in own if all(len(cache[(period, method, no, q)]) >= 20 for q in QS)]
    def expected_means(period, method, own, agg):
        elig = eligible(period, method, own)
        if agg == 'strategy_equal_weighted':
            return [sum((metric(cache[(period, method, no, q)])['AvgR'] for no in elig), Decimal(0))/len(elig)
                    if elig else math.nan for q in QS]
        return [metric([v for no in own for v in cache[(period, method, no, q)]])['AvgR'] for q in QS]
    rows = pd.concat([tables[n] for n in ['portfolio_quintiles','strategy_quintiles','group_quintiles','period_quintiles']], ignore_index=True)
    for r in rows.to_dict('records'):
        period, method, scope, agg, q = (r[k] for k in ['Period','Method','Scope','Aggregation','Quintile'])
        own = scope_ids(scope); elig = eligible(period, method, own)
        assert r['EligibleStrategies'] == len(elig)
        assert r['EligibleIDs'] == '|'.join(map(str, elig))
        assert bool(r['Eligible']) == bool(elig)
        if agg == 'strategy_equal_weighted':
            close(r['AvgR'], expected_means(period, method, own, agg)[QS.index(q)])
            for col in ['Trades','TotalR','PF','WinRate','AvgWinR','AvgLossR']:
                assert pd.isna(r[col]), 'Pooled metrics leaked onto equal-weighted row'
        else:
            expected = metric([v for no in own for v in cache[(period, method, no, q)]])
            for col, value in expected.items():
                close(r[col], value)
    expected_states = {}
    for r in tables['monotonicity_summary'].to_dict('records'):
        period, method, scope, agg = (r[k] for k in ['Period','Method','Scope','Aggregation'])
        own = scope_ids(scope); elig = eligible(period, method, own)
        z = monotonic(expected_means(period, method, own, agg))
        for col, value in z.items():
            close(r[col], value)
        p = monotonic(expected_means(period, method, own, 'trade_weighted'))
        e = monotonic(expected_means(period, method, own, 'strategy_equal_weighted'))
        good = p['Q5MinusQ1AvgR'] > 0 and p['Spearman'] > 0 and p['AdjacentIncreases'] >= 3
        if period != 'FULL':
            state = 'DESCRIPTIVE_ONLY'
        elif str(scope).isdigit():
            state = 'LOW_SAMPLE' if not elig else 'ORDERED_POSITIVE_SUPPORTED' if good else 'NOT_SUPPORTED'
        elif not p['Complete'] or not e['Complete']:
            state = 'UNDETERMINED'
        else:
            state = 'ORDERED_POSITIVE_SUPPORTED' if good and e['Q5MinusQ1AvgR'] > 0 and e['Spearman'] > 0 else 'NOT_SUPPORTED'
        assert r['Support'] == state, (scope, method, r['Support'], state)
        expected_states[(period, method, scope, agg)] = state
        if agg == 'strategy_equal_weighted' or period != 'FULL':
            assert pd.isna(r['CILow']) and pd.isna(r['CIHigh']) and r['ValidBootstraps'] == 0
        if period == 'FULL' and agg == 'trade_weighted':
            weekly = defaultdict(list)
            for trade in records:
                if int(trade['StrategyNo']) in own and trade[method+'Quintile'] in ('Q1','Q5'):
                    week = (pd.Timestamp(trade['EntryTime']).normalize()-first).days//7
                    weekly[(week, trade[method+'Quintile'])].append(float(trade['R']))
            vectors = np.zeros((weights.shape[1], 4))
            for week in range(len(vectors)):
                lo = weekly[(week, 'Q1')]; hi = weekly[(week, 'Q5')]
                vectors[week] = [math.fsum(lo), math.fsum(hi), len(lo), len(hi)]
            values = weights.astype(float) @ vectors
            ok = (values[:,2] > 0) & (values[:,3] > 0)
            assert r['ValidBootstraps'] == int(ok.sum())
            if ok.sum() >= 4750:
                deltas = sorted((values[ok,1]/values[ok,3]-values[ok,0]/values[ok,2]).tolist())
                quantiles = []
                for quant in (.025,.975):
                    pos = (len(deltas)-1)*quant; low = math.floor(pos); high = math.ceil(pos)
                    quantiles.append(deltas[low]+(pos-low)*(deltas[high]-deltas[low]))
                close(r['CILow'], quantiles[0]); close(r['CIHigh'], quantiles[1])
            else:
                assert pd.isna(r['CILow']) and pd.isna(r['CIHigh'])
    for r in tables['monotonicity_summary'].to_dict('records'):
        if r['Period'] != 'FULL':
            assert r['CombinedConclusion'] == 'DESCRIPTIVE_ONLY'
            continue
        a, b = [expected_states[('FULL', m, r['Scope'], r['Aggregation'])] for m in ['primary','robustness']]
        if a in ['UNDETERMINED','LOW_SAMPLE'] or b in ['UNDETERMINED','LOW_SAMPLE']:
            combined = 'UNDETERMINED'
        else:
            yes_a, yes_b = a == 'ORDERED_POSITIVE_SUPPORTED', b == 'ORDERED_POSITIVE_SUPPORTED'
            combined = 'BOTH_SUPPORTED' if yes_a and yes_b else 'PRIMARY_ONLY' if yes_a else 'ROBUSTNESS_ONLY' if yes_b else 'NOT_SUPPORTED'
        assert r['CombinedConclusion'] == combined
    for r in tables['coverage'].to_dict('records'):
        own = scope_ids(r['Scope']); period = r['Period']; method = r['Method']
        count = sum(len(cache[(period, method, no, r['Quintile'])]) for no in own)
        total = sum(len(cache[(period, method, no, q)]) for no in own for q in QS+['INSUFFICIENT_VOL_HISTORY'])
        close(r['Trades'], count); close(r['TotalTrades'], total)
        close(r['CoveragePct'], count/total*100 if total else math.nan)
    assert len(records) == 16298 and len({r['TradeID'] for r in records}) == 16298
    return [dict(Check='Independent CSV Decimal metrics/equal weights/all periods',Status='PASS',Rows=len(rows)),
            dict(Check='Independent ranks/adjacent/eligibility/combined decisions',Status='PASS',Rows=len(tables['monotonicity_summary'])),
            dict(Check='Independent weekly sums and linear CI',Status='PASS',Rows=66),
            dict(Check='All assignments/quintiles/no-lookahead/retained trades',Status='PASS',Rows=len(records)),
            dict(Check='Coverage including insufficient history',Status='PASS',Rows=len(tables['coverage']))]
