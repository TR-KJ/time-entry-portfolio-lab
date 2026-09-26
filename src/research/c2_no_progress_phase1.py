"""Preregistered C2 NP50; NP75 robustness only. R0 is a hard pre-outcome gate."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from c1_path_management_phase1 import bootstrap_deltas, metric, r0_gate
from daily_stop_baseline_revalidation import PIP_SIZE, SYMBOL_TO_PAIR, load_pair
from exit_efficiency_phase1 import BASELINE_SHA, PERIODS, checkpoint, in_period, load_baseline, resolve_and_audit, write

PLAN_SHA = '1b211146d4aa7610df9663693e586890d4dba4fe'
PREFIX = 'c2_no_progress_phase1_'
VARIANTS = {'NP50': .5, 'NP75': .75}
EPS = 1e-9


def no_progress(anchor, bars, base, variant):
    """Only pre-checkpoint bars inform the decision; Open precedes bar extrema."""
    target = checkpoint(anchor['_entry'], anchor['_scheduled'], VARIANTS[variant])
    result = dict(base)
    result.update(Variant=variant, Triggered=False, CheckpointTime=str(target),
                  CheckpointActual='', CheckpointDelay='', CheckpointMFE_R='',
                  Assessed=False, Assessment='CLOSED_BEFORE_CHECKPOINT')
    close = datetime.fromisoformat(base['CloseTime'])
    if close < target:
        return result
    idx = bars.index
    left = idx.searchsorted(anchor['_entry'])
    right = idx.searchsorted(target)
    if left == right:
        raise ValueError('no completed entry bar')
    long = anchor['Direction'] == 'Long'
    entry = float(base['EntryPrice'])
    unit = float(anchor['SL']) * PIP_SIZE[anchor['Pair']]
    extreme = float(bars['High'].iloc[left:right].max() if long else bars['Low'].iloc[left:right].min())
    mfe = max(0., (extreme-entry)/unit if long else (entry-extreme)/unit)
    progress = extreme >= entry + .25*unit if long else extreme <= entry - .25*unit
    result.update(Assessed=True, CheckpointMFE_R=mfe)
    if progress:
        result['Assessment'] = 'PROGRESS_REACHED'
        return result
    actual = None
    for delay in range(5):
        candidate = target + timedelta(minutes=delay)
        j = idx.searchsorted(candidate)
        if j < len(idx) and idx[j] == candidate:
            actual = candidate
            break
    if actual is None:
        result.update(Status='MISSING_CHECKPOINT_BAR', Assessment='MISSING_CHECKPOINT_BAR')
        return result
    result.update(CheckpointActual=str(actual), CheckpointDelay=delay)
    if close < actual:
        result['Assessment'] = 'CLOSED_BEFORE_EXECUTION'
        return result
    price = float(bars['Open'].iloc[j])
    r = (price-entry)/unit if long else (entry-price)/unit
    result.update(Triggered=True, Assessment='NO_PROGRESS_EXIT', CloseTime=str(actual),
                  ClosePrice=price, R=round(r, 9), Pips=round(r*float(anchor['SL']), 6),
                  ExitReason=variant, ExitDelayMinutes=delay)
    return result


def recovery(base):
    r = float(base['R'])
    reason = base['ExitReason']
    return dict(RECOVERED_POSITIVE=r > 0, RECOVERED_HALF_R=r >= .5,
                NEVER_RECOVERED=r <= 0, LATER_HIT_TP=reason == 'TP',
                LATER_HIT_SL=reason == 'SL', TIME_EXIT_POSITIVE=reason == 'TimeExit' and r > 0,
                TIME_EXIT_NEGATIVE=reason == 'TimeExit' and r < 0,
                TIME_EXIT_ZERO=reason == 'TimeExit' and r == 0)


def paired_summary(pairs, ci=True):
    bases = [b for _, b, _ in pairs]
    others = [c for _, _, c in pairs]
    b, c = metric(bases), metric(others)
    ds = np.asarray([float(y['R'])-float(x['R']) for x, y in zip(bases, others)])
    triggered = [(a, x, y) for a, x, y in pairs if y['Triggered']]
    recs = [recovery(x) for _, x, _ in triggered]
    out = dict(Trades=len(pairs), TriggerCount=len(triggered),
               TriggerRate=len(triggered)/len(pairs) if pairs else None,
               TriggerWeeks=len({a['_week'] for a, _, _ in triggered}),
               R0TotalR=b['TotalR'], NPTotalR=c['TotalR'], DeltaTotalR=float(ds.sum()),
               R0AvgR=b['AvgR'], NPAvgR=c['AvgR'], AvgDeltaR=float(ds.mean()) if len(ds) else None,
               Improved=int(sum(ds > EPS)), Harmed=int(sum(ds < -EPS)), Unchanged=int(sum(abs(ds) <= EPS)),
               AvgGainWhenImproved=float(ds[ds > EPS].mean()) if any(ds > EPS) else None,
               AvgDamageWhenHarmed=float(ds[ds < -EPS].mean()) if any(ds < -EPS) else None,
               BaselineTriggerAvgR=float(np.mean([x['R'] for _, x, _ in triggered])) if triggered else None,
               NPTriggerAvgR=float(np.mean([y['R'] for _, _, y in triggered])) if triggered else None,
               RecoveryRate=sum(r['RECOVERED_POSITIVE'] for r in recs)/len(recs) if recs else None,
               LaterTPRate=sum(r['LATER_HIT_TP'] for r in recs)/len(recs) if recs else None)
    for key in ('PF','WinRate','AvgWinR','AvgLossR','SLRate','TPRate','TimeExitRate','WorstDayR','WorstWeekR','MaxDDR'):
        out['R0'+key], out['NP'+key] = b[key], c[key]
    out['NPExitRate'] = out['TriggerRate']
    out['PeriodEligible'] = len(triggered) >= 30 and out['TriggerWeeks'] >= 20
    out['SampleStatus'] = 'ELIGIBLE' if out['PeriodEligible'] else 'INSUFFICIENT_SAMPLE'
    if ci and pairs:
        out['CILower'], out['CIUpper'], out['BootstrapNonpositiveFractionPlusOne'] = bootstrap_deltas(pairs)
    return out


def safety(row):
    return all((max(0., -row['NP'+m]) if m != 'MaxDDR' else row['NP'+m]) <=
               1.1*(max(0., -row['R0'+m]) if m != 'MaxDDR' else row['R0'+m]) + EPS
               for m in ('WorstDayR','WorstWeekR','MaxDDR'))


def decide(periods):
    p = {(r['Variant'], r['Period']): r for r in periods}
    all_ = p['NP50','ALL']
    recent = [p['NP50', k] for k in ('Recent A','Recent B','2026 Monitor')]
    gates = dict(A=all_['DeltaTotalR'] > 0, B=all_['CILower'] > 0,
                 C=p['NP50','Historical']['DeltaTotalR'] >= 0,
                 D=p['NP50','Recent Combined']['DeltaTotalR'] > 0,
                 E=sum(x['PeriodEligible'] for x in recent) >= 2 and
                   sum(x['PeriodEligible'] and x['DeltaTotalR'] > 0 for x in recent) >= 2,
                 F=p['NP75','ALL']['DeltaTotalR'] >= 0 and p['NP75','Recent Combined']['DeltaTotalR'] >= 0,
                 G=all_['TriggerCount'] >= 200 and all_['TriggerWeeks'] >= 100,
                 H=all(safety(r) for r in periods if r['Variant'] == 'NP50'))
    if not gates['G']: verdict = 'INSUFFICIENT_TRIGGER_SAMPLE'
    elif all(gates.values()): verdict = 'NO_PROGRESS_EXIT_CANDIDATE'
    elif not gates['A'] or not gates['B']: verdict = 'NOT_SUPPORTED'
    elif not all(gates[k] for k in ('C','D','E')): verdict = 'UNSTABLE_ACROSS_PERIODS'
    elif not gates['F']: verdict = 'ROBUSTNESS_FAIL'
    else: verdict = 'SAFETY_FAIL'
    return gates, verdict


def summarize(r0, variants, out):
    baseline = {(a['_n'], a['EntryTime']): b for a, b in r0}
    pairs = defaultdict(list)
    for a, v in variants:
        if a['_n'] != 22:
            pairs[v['Variant']].append((a, baseline[a['_n'], a['EntryTime']], v))
    assert all(len(pairs[v]) == 15837 for v in VARIANTS)
    assert {a['_n'] for a, _, _ in pairs['NP50']} == set(range(1,29)) - {22}
    periods, strategies, triggers, recoveries, detail, coverage = [], [], [], [], [], []
    for variant in VARIANTS:
        for period in PERIODS:
            subset = [p for p in pairs[variant] if in_period(p[0]['_entry'], period)]
            row = dict(Variant=variant, Period=period, **paired_summary(subset))
            row['SafetyPass'] = safety(row)
            periods.append(row)
            selected = [p for p in subset if p[2]['Triggered']]
            triggers.append(dict(Variant=variant, Period=period, **paired_summary(selected, ci=False)))
            for flag in recovery({'R':0,'ExitReason':'TimeExit'}):
                count = sum(recovery(b)[flag] for _, b, _ in selected)
                recoveries.append(dict(Variant=variant, Period=period, Category=flag,
                                       TriggerCount=len(selected), Count=count, Rate=count/len(selected) if selected else None))
        for n in sorted(set(a['_n'] for a, _, _ in pairs[variant])):
            subset = [p for p in pairs[variant] if p[0]['_n'] == n]
            row = dict(Variant=variant, StrategyNo=n, Strategy=subset[0][0]['Strategy'], **paired_summary(subset, ci=False))
            row['DiagnosticLabel'] = 'EXPLORATORY_STRATEGY_SIGNAL' if row['PeriodEligible'] and row['DeltaTotalR'] > 0 else 'NO_EXPLORATORY_SIGNAL'
            strategies.append(row)
        for assessment, count in Counter(c['Assessment'] for _, _, c in pairs[variant]).items():
            coverage.append(dict(Variant=variant, Assessment=assessment, Trades=count))
    for a, c in variants:
        b = baseline[a['_n'], a['EntryTime']]
        detail.append(dict(StrategyNo=a['_n'], Strategy=a['Strategy'], Pair=a['Pair'], Direction=a['Direction'],
                           Formal=a['_n'] != 22, EntryTime=a['EntryTime'], ScheduledExitTime=a['ScheduledExitTime'],
                           Week=a['_week'], SL=a['SL'], TP=a['TP'], EntryPrice=b['EntryPrice'], Variant=c['Variant'],
                           CheckpointTime=c['CheckpointTime'], CheckpointActual=c['CheckpointActual'],
                           CheckpointDelay=c['CheckpointDelay'], CheckpointMFE_R=c['CheckpointMFE_R'],
                           Assessed=c['Assessed'], Assessment=c['Assessment'], Triggered=c['Triggered'],
                           R0CloseTime=b['CloseTime'], NPCloseTime=c['CloseTime'], R0ClosePrice=b['ClosePrice'],
                           NPClosePrice=c['ClosePrice'], R0ExitReason=b['ExitReason'], NPExitReason=c['ExitReason'],
                           R0R=b['R'], NPR=c['R'], DeltaR=float(c['R'])-float(b['R']),
                           **{'Recovery_'+k: v if c['Triggered'] else '' for k, v in recovery(b).items()}))
    gates, verdict = decide(periods)
    tables = dict(portfolio_summary=[r for r in periods if r['Period'] == 'ALL'], period_summary=periods,
                  strategy_summary=strategies, trigger_summary=triggers, recovery_summary=recoveries,
                  np75_robustness=[r for r in periods if r['Variant'] == 'NP75'],
                  trade_delta_summary=[{k:r[k] for k in ('Variant','Period','Trades','DeltaTotalR','AvgDeltaR','CILower','CIUpper','Improved','Harmed','Unchanged')} for r in periods],
                  coverage=coverage,
                  formal_gates=[dict(Gate=k, Pass=v, Verdict=verdict, Phase2Eligible=all(gates.values())) for k,v in gates.items()])
    for name, records in tables.items():
        write(out / (PREFIX+name+'.csv'), records)
    write(out / (PREFIX+'trade_detail_local.csv'), detail)
    return verdict


def main():
    ap = argparse.ArgumentParser()
    for name in ('baseline','manifest','m1-root','out','implementation-sha'):
        ap.add_argument('--'+name, required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rows = load_baseline(args.baseline)
    print('Auditing 56 M1 inputs', flush=True)
    paths, audit = resolve_and_audit(args.manifest, args.m1_root)
    write(out / (PREFIX+'m1_audit.csv'), audit)
    print('Reconstructing R0; NP calculations remain gated', flush=True)
    r0, checks = r0_gate(rows, paths, out)
    (out/'c1_path_management_phase1_r0_reconciliation.csv').replace(out/(PREFIX+'r0_reconciliation.csv'))
    print('R0 PASS: ALL28 16298 / ACTIVE27 15837, zero mismatches', flush=True)
    by_pair = defaultdict(list)
    for a, b in r0: by_pair[a['Pair']].append((a,b))
    variants = []
    for symbol, pair in SYMBOL_TO_PAIR.items():
        print('NP50/NP75 '+symbol, flush=True)
        bars = load_pair(paths[symbol], symbol)
        for a, b in by_pair[pair]:
            for v in VARIANTS: variants.append((a,no_progress(a,bars,b,v)))
        del bars; gc.collect()
    missing = [dict(StrategyNo=a['_n'], EntryTime=a['EntryTime'], Variant=r['Variant']) for a,r in variants if r['Status'] != 'OK']
    if missing:
        write(out/(PREFIX+'missing_checkpoint_local.csv'),missing)
        raise RuntimeError('VALIDATION_FAIL: missing checkpoint, formal outcomes barred')
    verdict = summarize(r0, variants, out)
    detail = out/(PREFIX+'trade_detail_local.csv')
    write(out/(PREFIX+'validation.csv'), [dict(Check=k, Status='PASS', Detail=v) for k,v in
          [('baseline_sha',BASELINE_SHA),('m1_manifest','56 exact hashes/rows/bounds'),
           ('r0_reconciliation','16298 reference, 15837 formal, zero mismatches'),
           ('formal_universe','27 strategies, Strategy22 excluded'),('missing_checkpoint','0')]])
    write(out/(PREFIX+'run_record.csv'), [dict(PlanSHA=PLAN_SHA, ImplementationSHA=args.implementation_sha,
          BaselineSHA=BASELINE_SHA, Verdict=verdict, Phase2Eligible=verdict=='NO_PROGRESS_EXIT_CANDIDATE',
          BootstrapSeed=20260913, BootstrapReplicates=5000, DetailBytes=detail.stat().st_size,
          DetailSHA256=hashlib.sha256(detail.read_bytes()).hexdigest())])
    print(json.dumps(dict(Verdict=verdict, Output=str(out))), flush=True)


if __name__ == '__main__':
    main()
