"""Fixed-quintile diagnostic study. No entry filters or risk allocation."""
from pathlib import Path
import argparse
import json
import math
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tests'))
import volatility_phase1 as p1

PLAN_COMMIT = '1acc1fa530610eafcd985d446ba86c4dc415b5d6'
PHASE1_COMMIT = 'cafbb6ff0bfe81e439b80ed62d50498494814e86'
BRANCH = 'research/volatility-environment-phase2'
QUINTILES = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']
SUPPORTED = 'ORDERED_POSITIVE_SUPPORTED'
SOURCE_HASHES = {
    'volatility_phase1.py': '65ef361509e5bb404be02bfb0d1bdefbc6f59acbe8a557cdee030dd3a69116a1',
    'volatility_phase1_frozen_inputs.json': 'bfc4b372247bc8def18f4a3768d855285559ffed2782de73737fda4eafb5c61b',
}
NO_CI = dict(CILow=np.nan, CIHigh=np.nan, ValidBootstraps=0)


def percentile_bin(percent):
    """Public percent-scale boundary specification, including exact equalities."""
    if np.isnan(percent):
        return p1.INS
    if not np.isfinite(percent) or not 0 <= percent <= 100:
        raise ValueError('Percentile outside [0,100]')
    return QUINTILES[int(np.searchsorted([20, 40, 60, 80], percent, side='right'))]


def numerator(rank):
    if np.isnan(rank):
        return None
    if not np.isfinite(rank) or not 0 <= rank <= 1:
        raise ValueError('Invalid midrank')
    n = int(round(rank * 504))
    if abs(rank - n / 504) > 1e-12:
        raise ValueError('Percentile is not a Phase 1 midrank')
    return n


def quintile(rank):
    n = numerator(rank)
    if n is None:
        return p1.INS
    return QUINTILES[int(np.searchsorted([504, 1008, 1512, 2016], 5*n, side='right'))]


def add_quintiles(a):
    a = a.copy()
    for method in p1.METHODS:
        ns = a[method+'Percentile'].map(numerator)
        old = ns.map(lambda n: p1.INS if pd.isna(n) else 'LOW' if n < 168 else 'NORMAL' if n < 336 else 'HIGH')
        if not old.equals(a[method]):
            raise AssertionError('Phase 1 regime/midrank mismatch')
        a[method+'Quintile'] = a[method+'Percentile'].map(quintile)
    return a


def indicators(avgs):
    x = np.asarray(avgs, dtype=float)
    if x.shape != (5,):
        raise ValueError('Exactly five prespecified means required')
    complete = bool(np.isfinite(x).all())
    d = np.diff(x)
    rank = pd.Series(x).rank(method='average').to_numpy()
    rho = float(np.corrcoef(np.arange(1, 6), rank)[0, 1]) if complete and np.ptp(rank) > 0 else np.nan
    return dict(**{f'Q{i+1}AvgR': x[i] for i in range(5)},
                Q5MinusQ1AvgR=x[4]-x[0],
                **{f'Q{i+2}MinusQ{i+1}AvgR': d[i] for i in range(4)},
                Spearman=rho, AdjacentIncreases=int((d > 0).sum()) if complete else np.nan,
                StrictlyIncreasing=bool(complete and (d > 0).all()),
                Nondecreasing=bool(complete and (d >= 0).all()), Complete=complete)


def ordered(z):
    return bool(z['Q5MinusQ1AvgR'] > 0 and z['Spearman'] > 0 and z['AdjacentIncreases'] >= 3)


def group_support(pooled, equal):
    if not pooled['Complete'] or not equal['Complete']:
        return 'UNDETERMINED'
    return SUPPORTED if ordered(pooled) and equal['Q5MinusQ1AvgR'] > 0 and equal['Spearman'] > 0 else 'NOT_SUPPORTED'


def combine(primary, robustness):
    if any(s in ('UNDETERMINED', 'LOW_SAMPLE') for s in (primary, robustness)):
        return 'UNDETERMINED'
    a, b = primary == SUPPORTED, robustness == SUPPORTED
    return 'BOTH_SUPPORTED' if a and b else 'PRIMARY_ONLY' if a else 'ROBUSTNESS_ONLY' if b else 'NOT_SUPPORTED'


def cell_stats(values):
    """Production aggregation; independent checker uses Decimal from CSV rows."""
    x = pd.Series(values, dtype=float)
    n = len(x); wins = x[x > 0]; losses = x[x < 0]
    profit = wins.sum(); loss = -losses.sum()
    return dict(Trades=n, TotalR=x.sum(), AvgR=x.mean() if n else np.nan,
                PF=profit/loss if loss else np.inf if profit else np.nan,
                WinRate=len(wins)/n*100 if n else np.nan,
                AvgWinR=wins.mean(), AvgLossR=losses.mean(), LOW_SAMPLE=n < 20)


def confidence(a, method, first, weights):
    # Reuse Phase 1's exact bootstrap implementation with Q1/Q5 mapped to endpoints.
    b = a[['EntryTime', 'R']].copy()
    b['endpoint'] = a[method+'Quintile'].map({'Q1': 'LOW', 'Q5': 'HIGH'}).to_numpy()
    return p1.confidence(b, 'endpoint', first, weights)


def tables_for(a, method, period, cis):
    cells, summaries = [], []
    by = {}
    grouped = {int(no): g for no, g in a.groupby('StrategyNo')}
    for s in p1.STRATEGIES:
        no = s['StrategyNo']; g = grouped.get(no, a.iloc[:0])
        metrics = {q: cell_stats(g.loc[g[method+'Quintile'] == q, 'R']) for q in QUINTILES}
        eligible = all(metrics[q]['Trades'] >= 20 for q in QUINTILES)
        z = indicators([metrics[q]['AvgR'] for q in QUINTILES])
        state = 'DESCRIPTIVE_ONLY' if period != 'FULL' else 'LOW_SAMPLE' if not eligible else SUPPORTED if ordered(z) else 'NOT_SUPPORTED'
        ci = cis.get((method, str(no)), NO_CI) if period == 'FULL' else NO_CI
        base = dict(Period=period, Method=method, Scope=str(no), ScopeType='Strategy',
                    StrategyNo=no, Strategy=s['Strategy'], Group='', Aggregation='trade_weighted',
                    Eligible=eligible, EligibleStrategies=int(eligible), EligibleIDs=str(no) if eligible else '',
                    PrespecifiedSubgroup=no in (1, 6, 12, 23), Support=state)
        summaries.append(dict(**base, **z, **ci))
        for q in QUINTILES:
            cells.append(dict(**base, Quintile=q, **metrics[q]))
        by[no] = (metrics, eligible)
    for name, ids in p1.GROUP_IDS.items():
        own = a[a.StrategyNo.isin(ids)]
        eligible = [no for no in ids if by[no][1]]
        metrics = {q: cell_stats(own.loc[own[method+'Quintile'] == q, 'R']) for q in QUINTILES}
        equal = {q: np.mean([by[no][0][q]['AvgR'] for no in eligible]) if eligible else np.nan for q in QUINTILES}
        pz = indicators([metrics[q]['AvgR'] for q in QUINTILES]); ez = indicators([equal[q] for q in QUINTILES])
        state = group_support(pz, ez) if period == 'FULL' else 'DESCRIPTIVE_ONLY'
        ci = cis.get((method, name), NO_CI) if period == 'FULL' else NO_CI
        base = dict(Period=period, Method=method, Scope=name, ScopeType='Group', Group=name,
                    StrategyNo=np.nan, Strategy='', Eligible=bool(eligible), EligibleStrategies=len(eligible),
                    EligibleIDs='|'.join(map(str, eligible)), PrespecifiedSubgroup=False, Support=state)
        for agg, z, interval in [('trade_weighted', pz, ci), ('strategy_equal_weighted', ez, NO_CI)]:
            summaries.append(dict(**base, Aggregation=agg, **z, **interval))
            for q in QUINTILES:
                stats = metrics[q] if agg == 'trade_weighted' else {'AvgR': equal[q]}
                cells.append(dict(**base, Aggregation=agg, Quintile=q, **stats))
    return pd.DataFrame(cells), pd.DataFrame(summaries)


def regression(a, reference_dir, first, weights):
    """Regenerate the preregistered Phase 1 tables from the identical feature rows."""
    from verify_volatility_phase1 import verify_tables
    cis = {(m, name): p1.confidence(a[a.StrategyNo.isin(ids)], m, first, weights)
           for m in p1.METHODS
           for name, ids in list(p1.GROUP_IDS.items()) + [(str(s['StrategyNo']), [s['StrategyNo']]) for s in p1.STRATEGIES]}
    tables, groups, periods, decisions, coverage = {}, [], [], [], []
    for period, (start, end) in p1.PERIODS.items():
        x = a[(a.EntryTime >= start) & (a.EntryTime < end)]
        for method in p1.METHODS:
            c, g, dec = p1.tables_for(x, method, period, cis)
            if period == 'FULL':
                tables['strategy_'+method] = c; groups.append(g); decisions.append(dec)
            else:
                periods.extend([c, g])
            for name, ids in list(p1.GROUP_IDS.items()) + [(str(s['StrategyNo']), [s['StrategyNo']]) for s in p1.STRATEGIES]:
                own = x[x.StrategyNo.isin(ids)]
                for reg in p1.REGIMES + [p1.INS]:
                    n = int(own[method].eq(reg).sum())
                    coverage.append(dict(Period=period, Method=method, Scope=name, Regime=reg,
                                         Trades=n, TotalTrades=len(own), CoveragePct=n/len(own)*100 if len(own) else np.nan))
    tables['group_summary'] = pd.concat(groups, ignore_index=True)
    tables['period_summary'] = pd.concat(periods, ignore_index=True)
    tables['decision'] = pd.concat(decisions, ignore_index=True)
    tables['combined_decision'] = p1.combined_decisions(tables['decision'])
    tables['regime_coverage'] = pd.DataFrame(coverage)
    verify_tables(a, tables)
    checks = []
    for name, actual in tables.items():
        expected = pd.read_csv(Path(reference_dir)/f'volatility_phase1_{name}.csv')
        assert len(actual) == len(expected), name
        assert list(actual.columns) == list(expected.columns), name
        for col in expected:
            x, y = actual[col].reset_index(drop=True), expected[col]
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                np.testing.assert_allclose(x.astype(float), y.astype(float), atol=1e-10, rtol=0, equal_nan=True, err_msg=name+':'+col)
            else:
                assert x.fillna('').astype(str).tolist() == y.fillna('').astype(str).tolist(), (name, col)
        checks.append(dict(Check='Phase1 regression '+name, Status='PASS', Rows=len(actual)))
    audit = pd.read_csv(Path(reference_dir)/'volatility_phase1_assignment_audit_light.csv')
    actual = a.set_index('TradeID').loc[audit.TradeID]
    for col in ['primaryPercentile', 'robustnessPercentile', 'ATR20', 'RV20']:
        np.testing.assert_allclose(actual[col], audit[col], atol=1e-10, rtol=0, equal_nan=True)
    for col in ['primary', 'robustness']:
        assert actual[col].tolist() == audit[col].tolist()
    checks.append(dict(Check='Phase1 stored feature/assignment audit', Status='PASS', Rows=len(audit)))
    return pd.DataFrame(checks)


def manual_quintiles(audits, d):
    out = []
    for row in audits:
        i = int(row['DailyIndex']); row = dict(row)
        for method, col in [('primary', 'ATR20'), ('robustness', 'RV20')]:
            ref = d[col].iloc[i-252:i].tolist(); value = d.iloc[i][col]
            if len(ref) == 252 and all(math.isfinite(v) for v in ref) and math.isfinite(value):
                n = 2*sum(v < value for v in ref) + sum(v == value for v in ref)
                label = 'Q1' if n <= 100 else 'Q2' if n <= 201 else 'Q3' if n <= 302 else 'Q4' if n <= 403 else 'Q5'
                assert label == quintile(d.iloc[i][method+'Percentile'])
                row[method+'Numerator'] = n
                row[method+'Quintile'] = label
            else:
                assert quintile(d.iloc[i][method+'Percentile']) == p1.INS
                row[method+'Quintile'] = p1.INS
        out.append(row)
    return out


def run(baseline, m1_root, output_dir, implementation_sha, reference_dir=None):
    if len(implementation_sha) != 40 or any(c not in '0123456789abcdef' for c in implementation_sha):
        raise ValueError('Remote-verified implementation SHA required')
    for filename, expected in SOURCE_HASHES.items():
        assert p1.sha(Path(p1.__file__).with_name(filename)) == expected, 'Phase1 source changed'
    ref = Path(reference_dir) if reference_dir else Path(__file__).resolve().parents[2]/'results/volatility_phase1'
    t = p1.load_baseline(baseline)
    expected_manifest = pd.read_csv(ref/'volatility_phase1_input_manifest.csv').set_index('Filename')
    files = list(Path(m1_root).rglob('*.csv'))
    selected = {}
    for symbol, names in p1.FROZEN['MANIFEST_NAMES'].items():
        selected[symbol] = []
        for name in names:
            hits = [p for p in files if p.name == name]
            if len(hits) != 1:
                raise FileNotFoundError(f'Expected exactly one {name}; found {len(hits)} under {m1_root}')
            assert p1.sha(hits[0]) == expected_manifest.loc[name, 'SHA256'], 'M1 hash mismatch: '+name
            selected[symbol].append(hits[0])
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    assignments, daily, manifest, audits = [], [], [], []
    for symbol, paths in selected.items():
        bars, m = p1.load_m1(paths)
        manifest.extend(dict(Symbol=symbol, **r) for r in m)
        d = p1.features(p1.make_daily(bars)); own = p1.assign(t[t.Symbol == symbol], d)
        audit = p1.manual_audit(bars, d, own)
        audits.extend(dict(Symbol=symbol, **r) for r in manual_quintiles(audit, d))
        assignments.append(add_quintiles(own)); daily.append(d.assign(Symbol=symbol))
        print(f'{symbol}: {len(bars):,} M1 / {len(d):,} daily; manual audit PASS', flush=True)
        del bars
    a = pd.concat(assignments).sort_values('TradeID').reset_index(drop=True)
    assert len(a) == 16298 and a.TradeID.nunique() == 16298
    first, weights = p1.bootstrap_weights()
    phase1_regression = regression(a, ref, first, weights)
    print('Phase 1 regression PASS', flush=True)
    cis = {(m, name): confidence(a[a.StrategyNo.isin(ids)], m, first, weights)
           for m in p1.METHODS
           for name, ids in list(p1.GROUP_IDS.items()) + [(str(s['StrategyNo']), [s['StrategyNo']]) for s in p1.STRATEGIES]}
    all_cells, all_summaries, coverage = [], [], []
    for period, (start, end) in p1.PERIODS.items():
        x = a[(a.EntryTime >= start) & (a.EntryTime < end)]
        for method in p1.METHODS:
            cells, summary = tables_for(x, method, period, cis)
            all_cells.append(cells); all_summaries.append(summary)
            for name, ids in list(p1.GROUP_IDS.items()) + [(str(s['StrategyNo']), [s['StrategyNo']]) for s in p1.STRATEGIES]:
                own = x[x.StrategyNo.isin(ids)]
                for q in QUINTILES + [p1.INS]:
                    n = int(own[method+'Quintile'].eq(q).sum())
                    coverage.append(dict(Period=period, Method=method, Scope=name, Quintile=q, Trades=n,
                                         TotalTrades=len(own), CoveragePct=n/len(own)*100 if len(own) else np.nan))
    cells = pd.concat(all_cells, ignore_index=True)
    summary = pd.concat(all_summaries, ignore_index=True)
    summary['CombinedConclusion'] = 'DESCRIPTIVE_ONLY'
    for (scope, agg), g in summary[summary.Period == 'FULL'].groupby(['Scope', 'Aggregation']):
        by = g.set_index('Method').Support
        summary.loc[g.index, 'CombinedConclusion'] = combine(by['primary'], by['robustness'])
    full = cells[cells.Period == 'FULL']
    tables = {
        'portfolio_quintiles': full[full.Group == 'Portfolio'].copy(),
        'strategy_quintiles': full[full.ScopeType == 'Strategy'].copy(),
        'group_quintiles': full[(full.ScopeType == 'Group') & (full.Group != 'Portfolio')].copy(),
        'period_quintiles': cells[cells.Period != 'FULL'].copy(),
        'monotonicity_summary': summary,
        'coverage': pd.DataFrame(coverage), 'manual_audit': pd.DataFrame(audits),
        'input_manifest': pd.DataFrame(manifest), 'phase1_regression': phase1_regression,
        'trade_assignments': a, 'daily_audit': pd.concat(daily, ignore_index=True),
    }
    ordered_a = a.sort_values(['EntryTime', 'TradeID'])
    audit_ids = set(ordered_a.groupby('StrategyNo').tail(1).TradeID)
    for m in p1.METHODS:
        audit_ids.update(ordered_a.groupby(['StrategyNo', m+'Quintile']).head(1).TradeID)
    cols = ['TradeID','StrategyNo','Strategy','Symbol','Direction','EntryTime','R','DailyDate','DailyIndex','LastM1','AvailableAt','ATR20','RV20','ReferenceStart','ReferenceEnd','primaryPercentile','robustnessPercentile','primary','robustness','primaryQuintile','robustnessQuintile']
    tables['assignment_audit_light'] = a[a.TradeID.isin(audit_ids)][cols]
    # Verify serialized assignments through an independent Decimal/csv path.
    assignment_path = out/'volatility_phase2_trade_assignments.csv'
    a.to_csv(assignment_path, index=False)
    from verify_volatility_phase2 import verify_tables
    tables['verification'] = pd.DataFrame(verify_tables(assignment_path, tables, first, weights))
    hashes = {}
    for name, frame in tables.items():
        path = out/f'volatility_phase2_{name}.csv'; frame.to_csv(path, index=False); hashes[path.name] = p1.sha(path)
    portfolio = summary[(summary.Period == 'FULL') & (summary.Scope == 'Portfolio') & (summary.Aggregation == 'trade_weighted')]
    record = dict(Status='COMPLETED', Branch=BRANCH, PlanCommit=PLAN_COMMIT,
                  ImplementationCommit=implementation_sha, Phase1Commit=PHASE1_COMMIT,
                  RunJST=pd.Timestamp.now(tz='Asia/Tokyo').isoformat(), BaselineSHA256=p1.sha(baseline),
                  BaselineTrades=len(t), StrategyCount=28, BaselineRecalculated=False,
                  EntryTradesRemoved=0, LiveChanged=False, FreshHoldout=False,
                  InputFiles=len(manifest), Phase1Regression='PASS', IndependentVerification='PASS',
                  PrimaryAssigned=int(a.primary.ne(p1.INS).sum()), RobustnessAssigned=int(a.robustness.ne(p1.INS).sum()),
                  PrimaryInsufficient=int(a.primary.eq(p1.INS).sum()), RobustnessInsufficient=int(a.robustness.eq(p1.INS).sum()),
                  Conclusion=portfolio.CombinedConclusion.iloc[0], CIFormalCondition=False,
                  Bootstrap='5000 calendar weeks; default_rng seed20260913;95% linear;min4750',
                  Python=sys.version.split()[0], Pandas=pd.__version__, Numpy=np.__version__,
                  SourceHashes=json.dumps(SOURCE_HASHES, sort_keys=True), OutputHashes=json.dumps(hashes, sort_keys=True))
    tables['run_record'] = pd.DataFrame([record])
    tables['run_record'].to_csv(out/'volatility_phase2_run_record.csv', index=False)
    print(portfolio.to_string(index=False), flush=True)
    return tables


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', required=True); parser.add_argument('--m1-root', required=True)
    parser.add_argument('--output-dir', default='/content'); parser.add_argument('--implementation-sha', required=True)
    parser.add_argument('--reference-dir')
    args = parser.parse_args()
    run(args.baseline, args.m1_root, args.output_dir, args.implementation_sha, args.reference_dir)
