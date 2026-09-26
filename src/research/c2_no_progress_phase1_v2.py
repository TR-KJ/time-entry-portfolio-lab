"""C2 Plan 97 amendment: absent executable checkpoint retains complete R0."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import c2_no_progress_phase1 as frozen
from c1_path_management_phase1 import r0_gate
from daily_stop_baseline_revalidation import SYMBOL_TO_PAIR, load_pair
from exit_efficiency_phase1 import BASELINE_SHA, PERIODS, in_period, load_baseline, resolve_and_audit, write

PLAN_SHA = '3e99c78855ba09b6be1a95fb13318b35d551d473'
PREFIX = frozen.PREFIX
KEEP_BASELINE = 'MISSING_EXECUTION_KEEP_BASELINE'
EXPECTED_MISSING = {(19, '2021-06-17 20:56:00', 'NP50'), (20, '2025-01-07 10:01:00', 'NP50')}


def no_progress(anchor, bars, base, variant):
    result = frozen.no_progress(anchor, bars, base, variant)
    if result['Status'] == 'MISSING_CHECKPOINT_BAR':
        result.update(Status='OK', Assessment=KEEP_BASELINE, Triggered=False)
        for field in ('CloseTime', 'ExitReason', 'ClosePrice', 'Pips', 'R', 'ExitDelayMinutes'):
            assert result[field] == base[field], field
    return result


def sensitivity_pairs(pairs, excluded):
    """Remove whole paired observations, using the same anchor set for both variants."""
    return [p for p in pairs if (p[0]['_n'], p[0]['EntryTime']) not in excluded]


def summarize_sensitivity(r0, variants, out):
    baseline = {(a['_n'], a['EntryTime']): b for a, b in r0}
    excluded = {(a['_n'], a['EntryTime']) for a, r in variants if r['Assessment'] == KEEP_BASELINE}
    pairs = defaultdict(list)
    for a, r in variants:
        if a['_n'] != 22:
            pairs[r['Variant']].append((a, baseline[a['_n'], a['EntryTime']], r))
    periods = []
    for v in frozen.VARIANTS:
        retained = sensitivity_pairs(pairs[v], excluded)
        assert len(retained) == 15835
        for period in PERIODS:
            subset = [p for p in retained if in_period(p[0]['_entry'], period)]
            row = dict(Variant=v, Period=period, **frozen.paired_summary(subset))
            row['SafetyPass'] = frozen.safety(row)
            row['Analysis'] = 'EXCLUDE_BOTH_SIDES_DESCRIPTIVE_ONLY'
            periods.append(row)
    gates, verdict = frozen.decide(periods)
    write(out/(PREFIX+'sensitivity_period_summary.csv'), periods)
    write(out/(PREFIX+'sensitivity_gates.csv'), [dict(Gate=k, Pass=v, DiagnosticVerdict=verdict,
          Analysis='DESCRIPTIVE_ONLY_NOT_FORMAL_SELECTION') for k,v in gates.items()])
    return verdict


def main():
    ap = argparse.ArgumentParser()
    for name in ('baseline','manifest','m1-root','out','implementation-sha'):
        ap.add_argument('--'+name, required=True)
    args = ap.parse_args()
    out = Path(args.out)
    if out.name == 'c2_no_progress_phase1':
        raise ValueError('Use a separate v2 output directory; preserve original stopped artifacts')
    out.mkdir(parents=True, exist_ok=True)
    rows = load_baseline(args.baseline)
    print('v2: auditing frozen baseline and 56 M1 sources', flush=True)
    paths, audit = resolve_and_audit(args.manifest, args.m1_root)
    write(out/(PREFIX+'m1_audit.csv'), audit)
    print('v2: R0 hard gate before NP outcomes', flush=True)
    r0, checks = r0_gate(rows, paths, out)
    (out/'c1_path_management_phase1_r0_reconciliation.csv').replace(out/(PREFIX+'r0_reconciliation.csv'))
    print('R0 PASS: 16298 reference / 15837 formal; zero mismatches', flush=True)
    grouped = defaultdict(list)
    for a,b in r0: grouped[a['Pair']].append((a,b))
    variants = []
    for symbol,pair in SYMBOL_TO_PAIR.items():
        print('v2 NP50/NP75 '+symbol, flush=True)
        bars = load_pair(paths[symbol],symbol)
        for a,b in grouped[pair]:
            for v in frozen.VARIANTS: variants.append((a,no_progress(a,bars,b,v)))
        del bars; gc.collect()
    missing = {(a['_n'],a['EntryTime'],r['Variant']) for a,r in variants if r['Assessment']==KEEP_BASELINE}
    if missing != EXPECTED_MISSING or any(r['Status']!='OK' for _,r in variants):
        raise RuntimeError('Unexpected missing-execution set or status; reproducibility gate failed')
    baseline = {(a['_n'],a['EntryTime']):b for a,b in r0}
    fallbacks = []
    for a,r in variants:
        if r['Assessment'] != KEEP_BASELINE: continue
        b=baseline[a['_n'],a['EntryTime']]
        fallbacks.append(dict(StrategyNo=a['_n'],EntryTime=a['EntryTime'],Variant=r['Variant'],
            CheckpointTime=r['CheckpointTime'],CheckpointMFE_R=r['CheckpointMFE_R'],
            Assessment=KEEP_BASELINE,Triggered=False,R0R=b['R'],NPR=r['R'],DeltaR=r['R']-b['R'],
            R0CloseTime=b['CloseTime'],NPCloseTime=r['CloseTime'],R0ExitReason=b['ExitReason'],NPExitReason=r['ExitReason'],
            R0ClosePrice=b['ClosePrice'],NPClosePrice=r['ClosePrice'],R0Pips=b['Pips'],NPPips=r['Pips']))
    write(out/(PREFIX+'missing_execution_policy_audit.csv'),fallbacks)
    print('Two known NP50 gaps retained as full R0; zero NP75 gaps', flush=True)
    verdict = frozen.summarize(r0,variants,out)
    sensitivity = summarize_sensitivity(r0,variants,out)
    detail=out/(PREFIX+'trade_detail_local.csv')
    write(out/(PREFIX+'validation.csv'),[dict(Check=k,Status='PASS',Detail=v) for k,v in [
        ('baseline_sha',BASELINE_SHA),('m1_manifest','56 exact hashes/rows/raw bounds'),
        ('r0_reconciliation','ALL28 16298 / ACTIVE27 15837; zero mismatches'),
        ('formal_universe','27 active strategies; Strategy22 excluded'),
        ('missing_execution_identity','Exactly 2 known NP50 cases and 0 NP75'),
        ('missing_execution_fallback','Full R0 retained; delta 0R; Triggered=False'),
        ('sensitivity_universe','Same 2 identities removed from both sides of both variants; ALL 15835')]])
    write(out/(PREFIX+'run_record.csv'),[dict(PlanSHA=PLAN_SHA,OriginalPlanSHA=frozen.PLAN_SHA,
        OriginalStoppedResultSHA='5d5f0b17412b713b44a1f651c7a9bd1037eeaa22',
        ImplementationSHA=args.implementation_sha,BaselineSHA=BASELINE_SHA,Verdict=verdict,
        Phase2Eligible=verdict=='NO_PROGRESS_EXIT_CANDIDATE',SensitivityVerdict=sensitivity,
        SensitivityVerdictAgrees=sensitivity==verdict,NP50MissingExecutionKept=2,NP75MissingExecutionKept=0,
        BootstrapSeed=20260913,BootstrapReplicates=5000,DetailBytes=detail.stat().st_size,
        DetailSHA256=hashlib.sha256(detail.read_bytes()).hexdigest())])
    print(json.dumps(dict(Verdict=verdict,SensitivityVerdict=sensitivity,Output=str(out))),flush=True)


if __name__ == '__main__': main()
