"""C1 fixed-anchor M1 replay. R0 reconciliation is a hard gate before variants."""
from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from daily_stop_baseline_revalidation import PIP_SIZE, SPREAD_PIPS, SYMBOL_TO_PAIR, load_pair
from exit_efficiency_phase1 import (
    BASELINE_SHA, PERIODS, STRATEGY, bootstrap_pair, holm, in_period,
    load_baseline, reconcile, resolve_and_audit, simulate as reference_replay,
    week, write,
)

VARIANTS = ('R0', 'R1_BE50', 'R2_LOCK100', 'R3_STAGED')
PLAN = 'docs/89_c1_path_management_phase1_plan.md'
EPS = 1e-10


def exit_bar_index(anchor, bars):
    idx = bars.index
    entry, scheduled = anchor['_entry'], anchor['_scheduled']
    ei = idx.searchsorted(entry)
    if ei >= len(idx) or idx[ei] != entry:
        raise ValueError('missing exact entry bar')
    for delay in range(5):
        t = scheduled + timedelta(minutes=delay)
        xi = idx.searchsorted(t)
        if xi < len(idx) and idx[xi] == t:
            if xi <= ei:
                raise ValueError('invalid exit window')
            return ei, xi, delay
    raise ValueError('missing Time Exit through +4 minutes')


def replay(anchor, bars, variant):
    """Replay a single fixed anchor, activating milestones on the next present bar."""
    if variant not in VARIANTS:
        raise ValueError(variant)
    ei, xi, delay = exit_bar_index(anchor, bars)
    pair = anchor['Pair']
    pip = PIP_SIZE[pair]
    sl_pips = float(anchor['SL'])
    tp_pips = float(anchor['TP']) if anchor['TP'] else None
    long = anchor['Direction'] == 'Long'
    sign = 1 if long else -1
    open_ = bars['Open'].to_numpy()
    high = bars['High'].to_numpy()
    low = bars['Low'].to_numpy()
    idx = bars.index
    raw = float(open_[ei])
    entry = raw + sign * SPREAD_PIPS[pair] * pip
    unit = sl_pips * pip
    stop_r = -1.0
    tp_level = None if tp_pips is None else entry + sign * tp_pips * pip
    pending = None
    mfe = mae = 0.0
    mfe_time = mae_time = anchor['_entry']
    first05 = first10 = None
    triggered = False
    close_r = None
    close_price = None
    close_time = None
    reason = None
    for i in range(ei, xi + 1):
        if pending is not None:
            stop_r = max(stop_r, pending)
            pending = None
        stop_level = entry + sign * stop_r * unit
        hit_stop = low[i] <= stop_level + EPS if long else high[i] >= stop_level - EPS
        hit_tp = False if tp_level is None else (high[i] >= tp_level - EPS if long else low[i] <= tp_level + EPS)
        if hit_stop or hit_tp:
            close_time = idx[i].to_pydatetime()
            if hit_stop:
                reason = 'SL' if stop_r == -1 else 'DynamicSL'
                close_r = stop_r
                close_price = stop_level
            else:
                reason = 'TP'
                close_r = tp_pips / sl_pips
                close_price = tp_level
            break
        favorable = ((float(high[i]) - entry) / unit if long else (entry - float(low[i])) / unit)
        adverse = ((float(low[i]) - entry) / unit if long else (entry - float(high[i])) / unit)
        if favorable > mfe:
            mfe = favorable
            mfe_time = idx[i].to_pydatetime()
        if adverse < mae:
            mae = adverse
            mae_time = idx[i].to_pydatetime()
        if first05 is None and favorable >= .5 - EPS:
            first05 = idx[i].to_pydatetime()
        if first10 is None and favorable >= 1 - EPS:
            first10 = idx[i].to_pydatetime()
        if variant in ('R1_BE50', 'R3_STAGED') and first05 is not None and stop_r < 0:
            pending = 0.0
            triggered = True
        if variant in ('R2_LOCK100', 'R3_STAGED') and first10 is not None and stop_r < .5:
            pending = .5
            triggered = True
        if i == xi:
            close_time = idx[i].to_pydatetime()
            reason = 'TimeExit'
            close_price = float(open_[i])
            close_r = sign * (close_price - entry) / unit
            break
    if close_time is None:
        raise AssertionError('unclosed replay')
    pips = close_r * sl_pips
    return dict(Status='OK', StrategyNo=anchor['_n'], Strategy=anchor['Strategy'], Pair=pair,
                Direction=anchor['Direction'], Mode=anchor['Mode'], EntryTime=anchor['EntryTime'],
                ScheduledExitTime=anchor['ScheduledExitTime'], CloseTime=close_time.isoformat(sep=' '),
                ExitDelayMinutes=delay, RawEntryOpen=raw, EntryPrice=entry, ClosePrice=close_price,
                SL=sl_pips, TP=tp_pips, Pips=round(pips, 6), R=round(close_r, 9),
                ExitReason=reason, Variant=variant, Triggered=triggered, Week=anchor['_week'],
                MFE_R=mfe, MAE_R=mae, MFETime=mfe_time.isoformat(sep=' '),
                MAETime=mae_time.isoformat(sep=' '),
                Reached05=first05 is not None, First05='' if first05 is None else first05.isoformat(sep=' '),
                Reached10=first10 is not None, First10='' if first10 is None else first10.isoformat(sep=' '))


def replay_all(rows, paths, variants):
    bypair = defaultdict(list)
    for a in rows:
        bypair[a['Pair']].append(a)
    results = []
    for symbol, pair in SYMBOL_TO_PAIR.items():
        bars = load_pair(paths[symbol], symbol)
        for anchor in bypair[pair]:
            for variant in variants:
                results.append((anchor, replay(anchor, bars, variant)))
        del bars
        gc.collect()
    return results


def r0_gate(rows, paths, out):
    output = replay_all(rows, paths, ('R0',))
    mismatches = []
    for anchor, row in output:
        bad = reconcile(anchor, row)
        if bad:
            mismatches.append(dict(StrategyNo=anchor['_n'], EntryTime=anchor['EntryTime'], Fields='|'.join(bad)))
    active = [(a, r) for a, r in output if a['_n'] != 22]
    checks = [
        dict(Scope='ALL28', AnchorTrades=len(rows), ReplayedTrades=len(output),
             MismatchCount=len(mismatches), Status='PASS' if len(rows) == len(output) == 16298 and not mismatches else 'FAIL'),
        dict(Scope='ACTIVE27', AnchorTrades=sum(a['_n'] != 22 for a in rows), ReplayedTrades=len(active),
             MismatchCount=sum(x['StrategyNo'] != 22 for x in mismatches),
             Status='PASS' if len(active) == 15837 and not mismatches else 'FAIL'),
    ]
    write(out / 'c1_path_management_phase1_r0_reconciliation.csv', checks)
    if mismatches:
        write(out / 'c1_path_management_phase1_r0_mismatch_local.csv', mismatches)
    if any(x['Status'] != 'PASS' for x in checks):
        raise RuntimeError('R0 reconciliation failed; dynamic outcomes barred')
    return output, checks


def metric(rows):
    a = np.asarray([float(x['R']) for x in rows])
    n = len(a)
    pos = a[a > 0]
    neg = a[a < 0]
    gross_win, gross_loss = float(pos.sum()), float(-neg.sum())
    reasons = Counter(x['ExitReason'] for x in rows)
    daily = defaultdict(float)
    weekly = defaultdict(float)
    for x in rows:
        daily[x['EntryTime'][:10]] += float(x['R'])
        weekly[x['Week']] += float(x['R'])
    balance = peak = dd = 0.0
    for x in sorted(rows, key=lambda t: (t['CloseTime'], t['StrategyNo'], t['EntryTime'])):
        balance += float(x['R'])
        peak = max(peak, balance)
        dd = max(dd, peak - balance)
    return dict(Trades=n, Weeks=len(weekly), TotalR=float(a.sum()), AvgR=float(a.mean()) if n else None,
                PF=gross_win/gross_loss if gross_loss else None, WinRate=len(pos)/n if n else None,
                AvgWinR=float(pos.mean()) if len(pos) else None,
                AvgLossR=float(neg.mean()) if len(neg) else None,
                TriggerRate=sum(bool(x['Triggered']) for x in rows)/n if n else None,
                SLRate=reasons['SL']/n if n else None, TPRate=reasons['TP']/n if n else None,
                TimeExitRate=reasons['TimeExit']/n if n else None,
                DynamicSLRate=reasons['DynamicSL']/n if n else None,
                WorstDayR=min(daily.values()) if daily else None,
                WorstWeekR=min(weekly.values()) if weekly else None, MaxDDR=dd)


def bootstrap_deltas(pairs):
    grouped = defaultdict(list)
    for anchor, base, other in pairs:
        grouped[anchor['_week']].append(float(other['R']) - float(base['R']))
    keys = sorted(grouped)
    sums = np.asarray([sum(grouped[k]) for k in keys])
    counts = np.asarray([len(grouped[k]) for k in keys])
    rng = np.random.Generator(np.random.PCG64(20260913))
    draws = rng.integers(0, len(keys), size=(5000, len(keys)))
    samples = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    return (float(np.quantile(samples, .025, method='linear')),
            float(np.quantile(samples, .975, method='linear')),
            (1 + int(np.count_nonzero(samples <= 0))) / 5001)


def summarize(rows, r0, dynamic):
    baseline = {(a['_n'], a['EntryTime']): r for a, r in r0}
    allrows = r0 + dynamic
    byvariant = defaultdict(list)
    pairs_by_variant = defaultdict(list)
    for a, r in allrows:
        if a['_n'] == 22:
            continue
        byvariant[r['Variant']].append(r)
        if r['Variant'] != 'R0':
            pairs_by_variant[r['Variant']].append((a, baseline[(a['_n'], a['EntryTime'])], r))
    if any(len(byvariant[v]) != 15837 for v in VARIANTS):
        raise ValueError('active paired coverage')
    portfolio = [dict(Variant=v, **metric(byvariant[v])) for v in VARIANTS]
    base_metric = metric(byvariant['R0'])
    for record in portfolio:
        v = record['Variant']
        record['DeltaTotalR'] = record['TotalR'] - base_metric['TotalR']
        record['AvgDeltaR'] = record['DeltaTotalR'] / record['Trades']
    periods = []
    strategies = []
    deltas = []
    anatomy = []
    for a, r in r0:
        if a['_n'] == 22:
            continue
        final = float(r['R'])
        anatomy.append(dict(StrategyNo=a['_n'], EntryTime=a['EntryTime'], MFE_R=r['MFE_R'],
                            MAE_R=r['MAE_R'], MFETime=r['MFETime'], MAETime=r['MAETime'],
                            Reached05=r['Reached05'], First05=r['First05'],
                            Reached10=r['Reached10'], First10=r['First10'], BaselineR=final,
                            MaxGivebackR=float(r['MFE_R'])-final,
                            Reached05FinalNegative=bool(r['Reached05'] and final < 0),
                            Reached10FinalBelow05=bool(r['Reached10'] and final < .5)))
    for v in VARIANTS:
        for period in PERIODS:
            subset = [x for x in byvariant[v] if in_period(datetime.fromisoformat(x['EntryTime']), period)]
            periods.append(dict(Variant=v, Period=period, **metric(subset)))
        for n in sorted({x['StrategyNo'] for x in byvariant[v]}):
            subset = [x for x in byvariant[v] if x['StrategyNo'] == n]
            sm = metric(subset)
            base_subset = [x for x in byvariant['R0'] if x['StrategyNo'] == n]
            base_total = metric(base_subset)['TotalR']
            changes = [float(d['R'])-float(b['R']) for a,b,d in pairs_by_variant[v] if a['_n'] == n] if v != 'R0' else []
            strategies.append(dict(Variant=v, StrategyNo=n, Strategy=STRATEGY[n].name,
                                   BaselineTotalR=base_total, DeltaTotalR=sm['TotalR']-base_total,
                                   Improved=sum(x > 1e-9 for x in changes),
                                   Harmed=sum(x < -1e-9 for x in changes),
                                   Unchanged=(len(changes)-sum(abs(x) > 1e-9 for x in changes)) if v != 'R0' else len(subset),
                                   SampleStatus='OK' if sm['Trades'] >= 30 and sm['Weeks'] >= 20 else 'INSUFFICIENT_SAMPLE',
                                   **sm))
    comparison = []
    for v in VARIANTS[1:]:
        pairs = pairs_by_variant[v]
        byperiod = {}
        for period in PERIODS:
            selected = [(a,b,d) for a,b,d in pairs if in_period(a['_entry'],period)]
            changes = np.asarray([float(d['R'])-float(b['R']) for _,b,d in selected])
            improved = changes[changes > 1e-9]
            harmed = changes[changes < -1e-9]
            rec = dict(Variant=v, Period=period, Trades=len(selected), Weeks=len({a['_week'] for a,_,_ in selected}),
                       DeltaTotalR=float(changes.sum()), AvgDeltaR=float(changes.mean()) if len(changes) else None,
                       Improved=len(improved), Harmed=len(harmed), Unchanged=len(changes)-len(improved)-len(harmed),
                       AvgBenefit=float(improved.mean()) if len(improved) else None,
                       AvgDamage=float(harmed.mean()) if len(harmed) else None)
            if period == 'ALL':
                rec['CI_L'], rec['CI_U'], rec['RawP'] = bootstrap_deltas(selected)
            byperiod[period] = rec
            deltas.append(rec)
        comparison.append((v, byperiod))
    adjusted = holm([cells['ALL']['RawP'] for _,cells in comparison])
    formal = []
    for (v, cells), p_adj in zip(comparison, adjusted):
        current = next(x for x in portfolio if x['Variant'] == v)
        enough = all(cells[p]['Trades'] >= 30 and cells[p]['Weeks'] >= 20 for p in ('ALL','Historical','Recent Combined'))
        sufficient_subperiods = [p for p in ('Recent A','Recent B','2026 Monitor') if cells[p]['Trades'] >= 30 and cells[p]['Weeks'] >= 20]
        allowance_day = max(1, .1*abs(base_metric['WorstDayR']))
        allowance_week = max(2, .1*abs(base_metric['WorstWeekR']))
        allowance_dd = max(5, .1*base_metric['MaxDDR'])
        gates = dict(A=cells['ALL']['DeltaTotalR']>0, B=cells['ALL']['CI_L']>0,
                     C=p_adj<.05, D=cells['Historical']['DeltaTotalR']>=0,
                     E=cells['Recent Combined']['DeltaTotalR']>0,
                     F=len(sufficient_subperiods)>=2 and sum(cells[p]['DeltaTotalR']>0 for p in sufficient_subperiods)>=2,
                     G=current['WorstDayR']>=base_metric['WorstDayR']-allowance_day and
                       current['WorstWeekR']>=base_metric['WorstWeekR']-allowance_week and
                       current['MaxDDR']<=base_metric['MaxDDR']+allowance_dd)
        if not enough:
            label = 'INSUFFICIENT_SAMPLE'
        elif all(gates.values()):
            label = 'GLOBAL_DYNAMIC_MANAGEMENT_CANDIDATE'
        elif all(gates[k] for k in 'ABCDEF') and not gates['G']:
            label = 'SAFETY_FAIL'
        elif all(gates[k] for k in 'ABC') and not all(gates[k] for k in 'DEF'):
            label = 'UNSTABLE_ACROSS_PERIODS'
        else:
            label = 'NOT_SUPPORTED'
        formal.append(dict(Variant=v, RawP=cells['ALL']['RawP'], HolmAdjustedP=p_adj,
                           CI_L=cells['ALL']['CI_L'], CI_U=cells['ALL']['CI_U'],
                           SampleSufficient=enough, EligibleSubperiods='|'.join(sufficient_subperiods),
                           **{f'Gate{k}':v for k,v in gates.items()}, Label=label))
    return portfolio, periods, strategies, deltas, anatomy, formal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--manifest', default='results/volatility_phase1/volatility_phase1_input_manifest.csv')
    ap.add_argument('--m1-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--stage', choices=('reconcile','full'), default='full')
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = load_baseline(args.baseline)
    if sum(a['_n'] != 22 for a in rows) != 15837:
        raise ValueError('active universe mismatch')
    paths, audit = resolve_and_audit(args.manifest, args.m1_root)
    write(out/'c1_path_management_phase1_m1_audit.csv', audit)
    r0, checks = r0_gate(rows, paths, out)
    if args.stage == 'reconcile':
        return
    dynamic = replay_all(rows, paths, VARIANTS[1:])
    portfolio, periods, strategies, deltas, anatomy, formal = summarize(rows, r0, dynamic)
    for name, records in [('portfolio_summary',portfolio),('period_summary',periods),
                          ('strategy_summary',strategies),('trade_delta_summary',deltas),
                          ('path_anatomy_summary',anatomy),('multiple_comparison',formal)]:
        write(out/f'c1_path_management_phase1_{name}.csv', records)
    coverage = [dict(Scope='ALL28', Trades=len(rows), Strategies=28, R0='PASS'),
                dict(Scope='ACTIVE27', Trades=15837, Strategies=27, R0='PASS',
                     VariantRows=len(dynamic)//3)]
    write(out/'c1_path_management_phase1_coverage.csv', coverage)
    write(out/'c1_path_management_phase1_validation.csv',
          [dict(Check='baseline_hash',Status='PASS',Detail=BASELINE_SHA),
           dict(Check='m1_hash_rows_range',Status='PASS',Detail=f'{len(audit)} files'),
           dict(Check='r0_reconciliation',Status='PASS',Detail=f'{len(r0)} trades, zero mismatches')])
    record = dict(Plan=PLAN, BaselineSHA=BASELINE_SHA, M1Files=len(audit),
                  R0Trades=len(r0), ActiveTrades=15837, Variants='|'.join(VARIANTS),
                  BootstrapSeed=20260913, BootstrapReplicates=5000,
                  Result='|'.join(f"{x['Variant']}:{x['Label']}" for x in formal))
    write(out/'c1_path_management_phase1_run_record.csv',[record])
    print(json.dumps(dict(Portfolio=portfolio,Formal=formal),ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
