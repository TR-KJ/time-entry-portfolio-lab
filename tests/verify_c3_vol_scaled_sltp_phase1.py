"""Independent post-run checks for C3 published aggregates and local trade detail."""
from __future__ import annotations

import argparse
import hashlib
import math
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

import numpy as np
import pandas as pd

BASELINE_SHA = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def outward(original, scale):
    q = Decimal(str(original)) * Decimal(str(scale)) / Decimal('0.1')
    return float(q.quantize(Decimal('1'), rounding=ROUND_CEILING) * Decimal('0.1'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--report', required=True)
    a = ap.parse_args()
    out = Path(a.out)
    detail = pd.read_csv(out / 'c3_vol_scaled_sltp_phase1_trade_detail_local.csv')
    portfolio = pd.read_csv(out / 'c3_vol_scaled_sltp_phase1_portfolio_summary.csv')
    coverage = pd.read_csv(out / 'c3_vol_scaled_sltp_phase1_coverage.csv')
    periods = pd.read_csv(out / 'c3_vol_scaled_sltp_phase1_period_summary.csv')
    formal = pd.read_csv(out / 'c3_vol_scaled_sltp_phase1_formal_gates.csv').iloc[0]
    baseline = pd.read_csv(a.baseline)
    baseline = baseline[baseline.StrategyNo.ne(22)]
    baseline_r = baseline.set_index(['StrategyNo', 'EntryTime']).R
    checks = []

    def check(name, ok, detail_text):
        checks.append({'Check': name, 'Status': 'PASS' if ok else 'FAIL', 'Detail': detail_text})

    check('baseline_hash', sha256(a.baseline) == BASELINE_SHA, sha256(a.baseline))
    check('paired_cardinality', len(detail) == 2 * 15837 and
          not detail.duplicated(['Method', 'StrategyNo', 'EntryTime']).any(), str(len(detail)))
    expected_sl = np.array([outward(x, y) for x, y in zip(detail.OriginalSL, detail.ScaleFactor)])
    check('outward_sl_rounding', np.allclose(expected_sl, detail.ActualSLPips, atol=1e-12),
          f'max_abs={np.max(np.abs(expected_sl-detail.ActualSLPips)):.3g}')
    no_tp = detail.OriginalTP.isna()
    expected_tp = np.array([outward(x, y) for x, y in
                            zip(detail.loc[~no_tp, 'OriginalTP'], detail.loc[~no_tp, 'ScaleFactor'])])
    check('tp_presence_and_rounding', detail.loc[no_tp, 'ActualTPPips'].isna().all() and
          np.allclose(expected_tp, detail.loc[~no_tp, 'ActualTPPips'], atol=1e-12),
          f'no_tp={int(no_tp.sum())}')
    check('actual_sl_defines_r', np.allclose(detail.Pips / detail.ActualSLPips, detail.R, atol=5e-9),
          f'max_abs={np.max(np.abs(detail.Pips/detail.ActualSLPips-detail.R)):.3g}')
    fallback = detail.FeatureStatus.ne('VALID')
    check('fallback_is_one', detail.loc[fallback, 'ScaleFactor'].eq(1.0).all(),
          f'fallback={int(fallback.sum())}')
    check('valid_scale_bounds', detail.loc[~fallback, 'ScaleFactor'].between(.5, 2).all(),
          f'valid={int((~fallback).sum())}')
    for method in ('ATR', 'RV'):
        own = detail[detail.Method.eq(method)]
        row = portfolio[portfolio.Variant.eq(method)].iloc[0]
        check(f'{method.lower()}_aggregate', math.isclose(own.R.sum(), row.TotalR, abs_tol=1e-7),
              f'detail={own.R.sum():.9f}; published={row.TotalR:.9f}')
        cov = coverage[coverage.Method.eq(method)].iloc[0]
        check(f'{method.lower()}_coverage', int((own.FeatureStatus == 'VALID').sum()) == int(cov.Valid),
              f"valid={int(cov.Valid)}; coverage={cov.Coverage:.9f}")
    atr = detail[detail.Method.eq('ATR')].copy()
    atr['R0'] = [baseline_r.loc[(n, t)] for n, t in zip(atr.StrategyNo, atr.EntryTime)]
    atr['Delta'] = atr.R - atr.R0
    weekly = atr.groupby('Week').Delta.agg(['sum', 'size'])
    rng = np.random.Generator(np.random.PCG64(20260913))
    draw = rng.integers(0, len(weekly), (5000, len(weekly)))
    samples = weekly['sum'].to_numpy()[draw].sum(1) / weekly['size'].to_numpy()[draw].sum(1)
    ci = np.quantile(samples, [.025, .975], method='linear')
    published_ci = periods[(periods.Method.eq('ATR')) & (periods.Period.eq('ALL'))].iloc[0]
    check('atr_cluster_bootstrap', np.allclose(ci, [published_ci.CI_L, published_ci.CI_U], atol=1e-12),
          f'independent=[{ci[0]:.12f},{ci[1]:.12f}]')
    by_strategy = atr.groupby('StrategyNo').Delta.sum()
    positive = by_strategy[by_strategy.gt(0)]
    concentration = positive.max() / positive.sum()
    check('concentration_arithmetic', math.isclose(concentration, formal.ConcentrationRatio, abs_tol=1e-12),
          f'independent={concentration:.12f}; positive={len(positive)}')
    report = pd.DataFrame(checks)
    report.to_csv(a.report, index=False)
    if not report.Status.eq('PASS').all():
        raise SystemExit(report.to_string(index=False))
    print(report.to_string(index=False))


if __name__ == '__main__':
    main()
