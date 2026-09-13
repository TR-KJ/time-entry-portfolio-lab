"""Preregistered 2026 reset adapter; reuse the unchanged prior money engine."""
import argparse
import hashlib
import json
import re
from datetime import datetime
from decimal import localcontext
from pathlib import Path
from zoneinfo import ZoneInfo
import edge_decay_phase2_money_simulation as engine

D = engine.D
RISKS = engine.RISKS
PRIMARY = engine.PRIMARY
INITIAL = engine.INITIAL
BASELINE_HASH = engine.BASELINE_HASH
PLAN_SHA = '524b93bdcfc3cccf739c85cf8826f236e511fa47'
SOURCE_SHA = 'abd9b87b498e0cccdcf2d33ed71736aa32e491fb'
BRANCH = 'research/deployment-reset-2026-validation'
PREFIX = 'deployment_reset_2026_'
START, END = '2026-01-01', '2026-09-10'
CANDIDATES = {
    'D0_BASELINE': None,
    'D1_MINUS_22': '22_GA_C_2',
    'D2_MINUS_18': '18_EA_2_MonWed_Short',
    'D3_MINUS_20': '20_EA_1A_MonTue_Short',
    'D4_MINUS_23': '23_GA_F_2',
}
RULE = 'Primary 1.5% FinalCapital delta > 0; 0.25/1.0/2.0% deltas >= 0; validation PASS; Shadow Forward candidate only; no live adoption'
WEEK_SPEC = 'EntryTime JST Monday 06:00; weekly starting Balance times Risk fixed per trade; previous closed PnL compounds next week; all capital and DD peaks reset to JPY 500000 on 2026-01-01; first partial week also JPY 500000'


def reset_rows(rows):
    engine.validate_rows(rows)
    a, b = datetime.fromisoformat(START), datetime.fromisoformat(END)
    return [r for r in rows if a <= r['EntryTime'] < b]


def simulate(rows, risk, candidate):
    if candidate not in CANDIDATES or risk not in RISKS:
        raise ValueError('Unregistered candidate/risk')
    selected = [r for r in reset_rows(rows) if r['Strategy'] != CANDIDATES[candidate]]
    # The prior M0 path is a general all-supplied-rows engine. No engine mutation.
    logs, weekly = engine.simulate(selected, risk, 'M0_BASELINE')
    for r in logs + weekly:
        r['Candidate'] = candidate
    return logs, weekly


def decide(deltas, verified=False):
    if set(deltas) != set(RISKS) or any(not x.is_finite() for x in deltas.values()):
        raise ValueError('Four finite registered risk deltas required')
    primary = deltas[PRIMARY] > 0
    robust = all(deltas[r] >= 0 for r in RISKS if r != PRIMARY)
    arithmetic = 'DEPLOYMENT_RESET_CANDIDATE' if primary and robust else 'NOT_CANDIDATE'
    return dict(ResetImprovement1_5=primary, OtherRiskRobustness=robust,
                ArithmeticDecision=arithmetic, Decision=arithmetic if verified else 'PENDING',
                ShadowForwardCandidate=bool(verified and primary and robust),
                VerificationStatus='PASS' if verified else 'PENDING', LiveAdopted=False)


def run(baseline, output_dir, implementation_sha, execution='LOCAL'):
    if not re.fullmatch('[0-9a-f]{40}', implementation_sha):
        raise ValueError('Confirmed implementation SHA required')
    out = Path(output_dir)
    with localcontext() as ctx:
        ctx.prec = 40
        rows = engine.load_baseline(baseline)
        identities = {r['Strategy'] for r in rows}
        if not set(CANDIDATES.values()) - {None} <= identities:
            raise ValueError('Candidate identity mismatch')
        selected = reset_rows(rows)
        if len(selected) != 995:
            raise ValueError('2026 baseline count mismatch')
        tables = {k: [] for k in ('summary', 'risk_comparison', 'detailed_metrics', 'weekly', 'trade_log', 'decision')}
        deltas = {c: {} for c in CANDIDATES if c != 'D0_BASELINE'}
        metric_names = None
        for risk in RISKS:
            metrics = {}
            for candidate in CANDIDATES:
                log, weekly = simulate(selected, risk, candidate)
                m = engine.metrics(log, START, END)
                metric_names = list(m)
                metrics[candidate] = m
                tables['weekly'].extend(weekly)
                tables['trade_log'].extend(log)
            base = metrics['D0_BASELINE']
            for candidate, m in metrics.items():
                differences = {'Delta'+k: m[k]-base[k] if m[k] is not None and base[k] is not None else None for k in metric_names}
                tables['summary'].append(dict(Candidate=candidate, ExcludedStrategy=CANDIDATES[candidate] or '', RiskPct=risk, **m,
                                              DeltaFinalCapital=differences['DeltaFinalCapital'], DeltaNetProfitJPY=differences['DeltaNetProfitJPY']))
                if candidate != 'D0_BASELINE':
                    tables['risk_comparison'].append(dict(Candidate=candidate, RiskPct=risk, BaselineFinalCapital=base['FinalCapital'], CandidateFinalCapital=m['FinalCapital'], **differences))
                    deltas[candidate][risk] = differences['DeltaFinalCapital']
                if risk == PRIMARY:
                    tables['detailed_metrics'].append(dict(Candidate=candidate, RiskPct=risk, **m, **differences))
        tables['decision'] = [dict(Candidate=c, **decide(v), Rule=RULE) for c, v in deltas.items()]
        tables['verification'] = [dict(Check='Baseline_hash_count_identities_boundaries_and_reset', Status='PASS'), dict(Check='Independent_metrics_tests_and_notebook', Status='PENDING')]
        tables['constraint_status'] = [dict(Mode='THEORETICAL_UNCAPPED', Status='RUN', Description=engine.LOT_SPEC), dict(Mode='EA_CONSTRAINED', Status=engine.CONSTRAINT_STATUS, Description='Historical JPY pip value, volume min/max/step and weekly floating equity unavailable')]
        out.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for name, records in tables.items():
            path = out / (PREFIX+name+'.csv')
            engine.write_csv(path, records)
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        record = dict(BaselineSHA256=BASELINE_HASH, BaselineTrades=len(rows), BaselineStrategies=28,
                      ResetBaselineTrades=len(selected), SourceCommit=SOURCE_SHA, Branch=BRANCH, PlanSHA=PLAN_SHA,
                      ImplementationSHA=implementation_sha, RunJST=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
                      Candidates=json.dumps(CANDIDATES), InitialCapitalJPY=INITIAL, RiskPcts=json.dumps([str(r) for r in RISKS]),
                      PrimaryRiskPct=PRIMARY, LiveReferenceRiskPct='0.25', StartJST=START, EndExclusiveJST=END,
                      WeeklyBaseSpec=WEEK_SPEC, LotSpec=engine.LOT_SPEC, DecisionRule=RULE,
                      SavedRMaxRoundingDifference=max(abs(r['R']-r['Pips']/r['SL']) for r in rows),
                      Execution=execution, ConstrainedStatus=engine.CONSTRAINT_STATUS,
                      VerificationStatus='PENDING', BaselineRecalculated=False, FreshOOS=False, LiveChanged=False,
                      CSVHashes=json.dumps(hashes, sort_keys=True), RunRecordCSV=PREFIX+'run_record.csv')
        engine.write_csv(out/(PREFIX+'run_record.csv'), [record])
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--implementation-sha', required=True)
    run(**vars(p.parse_args()))
