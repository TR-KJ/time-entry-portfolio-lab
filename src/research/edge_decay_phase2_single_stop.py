"""Preregistered single-stop family; frozen log aggregation only."""
import argparse
import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

D = Decimal
BASELINE_HASH = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PLAN_COMMIT = 'ead9384028145bb3ac2bf6a093bbfb4b13feb723'
BRANCH = 'research/edge-decay-phase2-single-stop-validation'
RULES_DOCUMENT = 'docs/42_edge_decay_phase2_single_stop_plan.md'
FAMILY = ('22_GA_C_2', '18_EA_2_MonWed_Short', '20_EA_1A_MonTue_Short', '23_GA_F_2')
PERIODS = {'IS': ('2015-01-01', '2022-01-01'), 'OOS1': ('2022-01-01', '2026-01-01'), 'OOS2': ('2026-01-01', '2026-09-10'), 'OOS_COMBINED': ('2022-01-01', '2026-09-10'), 'ALL': ('2015-01-01', '2026-09-10')}
RULE = 'OOS DeltaTotalR > 0 AND nonnegative years >= 3/5 AND max annual DeltaTotalR < 0.70 * net OOS DeltaTotalR; secondary metrics disclosed; no live adoption'

def select(rows, start, end):
    return [r for r in rows if start <= r['EntryTime'][:10] < end]

def load_baseline(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_HASH:
        raise ValueError('Baseline SHA-256 mismatch')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if len(rows) != 16298:
        raise ValueError('Expected 16298 trades')
    identities = {(int(r['StrategyNo']), r['Strategy']) for r in rows}
    if len(identities) != 28 or sorted(n for n, _ in identities) != list(range(1, 29)):
        raise ValueError('Expected 28 strategy identities')
    if any((int(s.split('_')[0]), s) not in identities for s in FAMILY):
        raise ValueError('Family identity mismatch')
    if len({(r['StrategyNo'], r['EntryTime']) for r in rows}) != len(rows):
        raise ValueError('Duplicate strategy entry')
    for r in rows:
        r['StrategyNo'] = int(r['StrategyNo'])
        r['R'] = D(r['R'])
        if not r['R'].is_finite():
            raise ValueError('Nonfinite R')
        for k in ('EntryTime', 'CloseTime'):
            if datetime.fromisoformat(r[k]).tzinfo is not None:
                raise ValueError('Expected naive JST timestamp')
        if r['CloseTime'] < r['EntryTime']:
            raise ValueError('Close before entry')
        if abs(r['R'] - D(r['Pips']) / D(r['SL'])) > D('0.00000001'):
            raise ValueError('R integrity mismatch')
    if len(select(rows, *PERIODS['ALL'])) != 16298:
        raise ValueError('Coverage mismatch')
    if [len(select(rows, *PERIODS[p])) for p in ('IS', 'OOS1', 'OOS2')] != [9756, 5547, 995]:
        raise ValueError('Period counts mismatch')
    return rows

def metrics(rows):
    gain = loss = equity = peak = dd = D(0)
    daily, weekly = defaultdict(lambda: D(0)), defaultdict(lambda: D(0))
    for r in sorted(rows, key=lambda r: (r['CloseTime'], r['EntryTime'], r['StrategyNo'])):
        value = r['R']
        gain += max(value, D(0))
        loss -= min(value, D(0))
        equity += value
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
        date = datetime.fromisoformat(r['CloseTime']).date()
        daily[date] += value
        weekly[date - timedelta(days=date.weekday())] += value
    return dict(Trades=len(rows), TotalR=equity,
                PF=gain/loss if loss else (D('Infinity') if gain else None),
                MaxDDR=dd, WorstDayR=min(daily.values(), default=D(0)),
                WorstWeekR=min(weekly.values(), default=D(0)))

def compare(rows, strategy, period):
    if strategy not in FAMILY:
        raise ValueError('Not a preregistered single strategy')
    kept = [r for r in rows if r['Strategy'] != strategy]
    removed = [r for r in rows if r['Strategy'] == strategy]
    a, b = metrics(rows), metrics(kept)
    delta = {k: b[k]-a[k] for k in a if k != 'PF'}
    delta['PF'] = b['PF']-a['PF'] if all(v is not None and v.is_finite() for v in (a['PF'], b['PF'])) else None
    if delta['TotalR'] != -sum((r['R'] for r in removed), D(0)):
        raise ValueError('Removal identity failed')
    labels = ('E0_BASELINE', 'E1_MINUS_'+strategy.split('_')[0], 'DELTA_E1_MINUS_E0')
    result = [dict(Strategy=strategy, Period=period, Candidate=c, **{k:m[k] for k in a}) for c,m in zip(labels, (a,b,delta))]
    return result, delta['TotalR']

def decide(year_deltas):
    if set(year_deltas) != set(range(2022, 2027)):
        raise ValueError('Exactly five fixed years required')
    values = list(year_deltas.values())
    if any(not v.is_finite() for v in values):
        raise ValueError('Finite annual deltas required')
    total = sum(values, D(0))
    count = sum(v >= 0 for v in values)
    max_year = max(values)
    concentration_ok = total > 0 and max_year < D('0.70') * total
    passed = total > 0 and count >= 3 and concentration_ok
    reasons = []
    if total <= 0: reasons.append('OOS_TOTAL_NOT_POSITIVE')
    if count < 3: reasons.append('FEWER_THAN_THREE_NONNEGATIVE_YEARS')
    if total > 0 and not concentration_ok: reasons.append('SINGLE_YEAR_SHARE_AT_LEAST_70_PERCENT')
    return dict(Decision='ADOPTION_CANDIDATE' if passed else 'REJECT', Reason=';'.join(reasons) or 'ALL_PRIMARY_AND_STABILITY_GATES_PASSED',
                OOSDeltaTotalR=total, NonnegativeYears=count, Years=5,
                MaxAnnualDeltaR=max_year, MaxAnnualShare=max_year/total if total>0 else None,
                ConcentrationPass=concentration_ok, MoneySimulationEligible=passed,
                MoneySimulation='NOT_RUN', LiveAdopted=False)

def validate_predecessor(strategy, record_path=None, result_sha=None):
    index = FAMILY.index(strategy)
    if index == 0: return
    if not record_path or not result_sha or not re.fullmatch('[0-9a-f]{40}', result_sha):
        raise ValueError('Previous committed result SHA and run record required; verify SHA on GitHub before execution')
    with Path(record_path).open(newline='') as f:
        records = list(csv.DictReader(f))
    if len(records) != 1:
        raise ValueError('One predecessor record required')
    r = records[0]
    for key, value in {'Strategy':FAMILY[index-1], 'PlanCommit':PLAN_COMMIT, 'BaselineSHA256':BASELINE_HASH, 'Branch':BRANCH}.items():
        if r.get(key) != value: raise ValueError('Predecessor provenance mismatch: '+key)
    if r.get('Decision') not in ('REJECT', 'ADOPTION_CANDIDATE'):
        raise ValueError('Predecessor not finalized')

def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader(); w.writerows(records)

def run(baseline, output_dir='/content', strategy=FAMILY[0], implementation_commit='LOCAL_UNCOMMITTED', predecessor_record=None, predecessor_result_sha=None):
    if strategy not in FAMILY: raise ValueError('Unknown strategy')
    validate_predecessor(strategy, predecessor_record, predecessor_result_sha)
    rows = load_baseline(baseline)
    results, deltas, yearly, annual = [], {}, [], {}
    for label, bounds in PERIODS.items():
        part, deltas[label] = compare(select(rows, *bounds), strategy, label)
        results.extend(part)
    for year in range(2022, 2027):
        end = '2026-09-10' if year == 2026 else f'{year+1}-01-01'
        part, annual[year] = compare(select(rows, f'{year}-01-01', end), strategy, str(year))
        yearly.extend(part)
    if deltas['ALL'] != deltas['IS']+deltas['OOS1']+deltas['OOS2'] or deltas['OOS_COMBINED'] != sum(annual.values(), D(0)):
        raise ValueError('Period additivity failure')
    decision = dict(Strategy=strategy, **decide(annual))
    secondary = next(r for r in results if r['Period']=='OOS_COMBINED' and r['Candidate']=='DELTA_E1_MINUS_E0')
    worsened = [k for k in ('PF','MaxDDR','WorstDayR','WorstWeekR') if secondary[k] is not None and (secondary[k]>0 if k=='MaxDDR' else secondary[k]<0)]
    decision['SecondaryWorsened'] = ';'.join(worsened) or 'NONE'
    decision['PFDeltaNote'] = 'NONFINITE_PF_DELTA_IS_NA' if any(r['PF'] is None for r in results+yearly if r['Candidate']=='DELTA_E1_MINUS_E0') else 'ALL_PF_DELTAS_FINITE'
    tables = {'period_results':results, 'yearly_results':yearly, 'decision':[decision]}
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    prefix = 'edge_decay_phase2_'+strategy.split('_')[0]+'_'
    hashes = {}
    for name, records in tables.items():
        path = out/(prefix+name+'.csv')
        write_csv(path, records)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    record = dict(Strategy=strategy, BaselineSHA256=BASELINE_HASH, BaselineTrades=len(rows), Strategies=28,
        Branch=BRANCH, PlanCommit=PLAN_COMMIT, ImplementationCommit=implementation_commit,
        RunJST=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(), Family=json.dumps(FAMILY),
        PredecessorResultSHA=predecessor_result_sha or 'NONE_FIRST', Periods=json.dumps(PERIODS),
        RulesDocument=RULES_DOCUMENT, DecisionRule=RULE, Decision=decision['Decision'],
        SecondaryWorsened=decision['SecondaryWorsened'], PFDeltaNote=decision['PFDeltaNote'],
        CSVHashes=json.dumps(hashes, sort_keys=True), RunRecordCSV=prefix+'run_record.csv',
        FreshHoldout=False, BaselineRecalculated=False, LiveChanged=False, MoneySimulation='NOT_RUN',
        NextStrategy=FAMILY[FAMILY.index(strategy)+1] if strategy!=FAMILY[-1] else 'FAMILY_COMPLETE')
    write_csv(out/(prefix+'run_record.csv'), [record])
    tables['run_record'] = [record]
    for name in ('period_results','yearly_results','decision'):
        print(name)
        for row in tables[name]: print(row)
    return tables

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True)
    p.add_argument('--output-dir', default='/content')
    p.add_argument('--strategy', choices=FAMILY, default=FAMILY[0])
    p.add_argument('--implementation-commit', required=True)
    p.add_argument('--predecessor-record')
    p.add_argument('--predecessor-result-sha')
    run(**vars(p.parse_args()))
