"""Preregistered OAT sensitivity; frozen primary results and live code stay unchanged."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal as D
from edge_decay_analysis import load_baseline, analyze as primary_analyze, BASELINE_HASH, PERIODS

PLAN_COMMIT = 'b3b9aca221adb78c70a34eefcd5b8e98d4511d7c'
PRIMARY_COMMIT = '8c45becc49218d7dc971109bf140f71ce3e8099d'
PRIMARY_BLOB = '11080b0f8166fb67635d08bd625f26b209f2cbcf'
BRANCH = 'research/edge-decay-sensitivity-validation'
WARNING = {'EDGE LOST', 'EDGE DECAY'}
# axis, point, unique setting, Historical PF, decay ratio, Combined n, A/B n
SETTINGS = (
    ('PF', '1.00', 'PF_1.00', '1.00', '0.50', 30, 15),
    ('PF', '1.05', 'OFFICIAL', '1.05', '0.50', 30, 15),
    ('PF', '1.10', 'PF_1.10', '1.10', '0.50', 30, 15),
    ('RATIO', '0.25', 'RATIO_0.25', '1.05', '0.25', 30, 15),
    ('RATIO', '0.50', 'OFFICIAL', '1.05', '0.50', 30, 15),
    ('RATIO', '0.75', 'RATIO_0.75', '1.05', '0.75', 30, 15),
    ('SAMPLE', 'relaxed', 'SAMPLE_RELAXED', '1.05', '0.50', 20, 10),
    ('SAMPLE', 'official', 'OFFICIAL', '1.05', '0.50', 30, 15),
    ('SAMPLE', 'strict', 'SAMPLE_STRICT', '1.05', '0.50', 40, 20),
)

def classify(h, a, b, c, pf='1.05', ratio='0.50', combined=30, ab=15):
    """No Monitor argument; exactly the original formula except the three OAT axes."""
    if c['Trades'] < combined or min(a['Trades'], b['Trades']) < ab:
        return 'INSUFFICIENT SAMPLE'
    present = all(x['AvgR'] is not None for x in (h, a, b, c))
    persistent = present and a['AvgR'] < h['AvgR'] and b['AvgR'] < h['AvgR']
    pfs = h['PF'] is not None and c['PF'] is not None
    if persistent and pfs and h['AvgR'] > 0 and h['PF'] > D(pf) and c['AvgR'] <= 0 and c['PF'] <= 1:
        return 'EDGE LOST'
    if persistent and pfs and c['AvgR'] <= h['AvgR'] * D(ratio) and c['PF'] < h['PF']:
        return 'EDGE DECAY'
    return 'STABLE'

def avg_ratio(h, c):
    return c / h if h is not None and h > 0 and c is not None else 'NA'

def warning_label(primary, count):
    if primary not in WARNING:
        return 'NA (non-candidate)'
    return '頑健' if count == 7 else '中程度' if count >= 5 else '不安定'

def read_primary(path):
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != PRIMARY_BLOB:
        raise ValueError('Frozen primary CSV blob mismatch')
    with Path(path).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def check_primary(final, frozen):
    if len(final) != 28 or len(frozen) != 28:
        raise ValueError('Expected 28 primary rows')
    old = {int(r['StrategyNo']): r for r in frozen}
    if len(old) != 28:
        raise ValueError('Duplicate primary identity')
    for f in final:
        r = old[f['StrategyNo']]
        for k, value in f.items():
            if str(value) != r[k]:
                raise ValueError(f'Primary mismatch: {f["Strategy"]} {k}')

def analyze(rows, frozen):
    final = primary_analyze(rows)['final_classification']
    check_primary(final, frozen)
    classifications, summaries, continuous = [], [], []
    for f in final:
        ident = dict(StrategyNo=f['StrategyNo'], Strategy=f['Strategy'])
        p = {period: {k: f[period+'_'+k] for k in ('Trades', 'AvgR', 'PF')} for period in PERIODS}
        mine = []
        for axis, point, uid, pf, ratio, combined, ab in SETTINGS:
            label = classify(*(p[x] for x in ('Historical', 'RecentA', 'RecentB', 'RecentCombined')), pf, ratio, combined, ab)
            if uid == 'OFFICIAL' and label != f['Classification']:
                raise ValueError('Official sensitivity classification mismatch')
            mine.append(dict(**ident, Axis=axis, Point=point, UniqueSetting=uid,
                HistoricalPFThreshold=pf, DecayRatioThreshold=ratio, CombinedMinTrades=combined,
                ABMinTrades=ab, PrimaryClassification=f['Classification'], Classification=label,
                Warning=label in WARNING, MonitorUsedForClassification=False))
        classifications.extend(mine)
        unique = {r['UniqueSetting']: r['Classification'] for r in mine}
        count = sum(v in WARNING for v in unique.values())
        summary = dict(**ident, PrimaryClassification=f['Classification'], **unique,
            WarningCountUnique=count, UniqueSettings=7, WarningRateUnique=D(count)/7,
            WarningCountDisplayed=sum(r['Warning'] for r in mine), DisplayedSettings=9,
            InsufficientCountUnique=sum(v == 'INSUFFICIENT SAMPLE' for v in unique.values()),
            PrimaryMatchCountUnique=sum(v == f['Classification'] for v in unique.values()),
            DistinctClassifications=len(set(unique.values())), WarningRetentionLabel=warning_label(f['Classification'], count))
        for axis in ('PF', 'RATIO', 'SAMPLE'):
            summary[axis+'_WarningCount'] = sum(r['Warning'] for r in mine if r['Axis'] == axis)
        summary['WarningRateDisplayed'] = D(summary['WarningCountDisplayed'])/9
        summaries.append(summary)
        continuous.append(dict(**ident, PrimaryClassification=f['Classification'],
            **{k:v for k,v in f.items() if any(k.startswith(p+'_') for p in PERIODS)},
            RecentToHistoricalAvgR=avg_ratio(f['Historical_AvgR'], f['RecentCombined_AvgR']),
            MonitorUsedForClassification=False))
    return dict(classifications=classifications, strategy_summary=summaries, continuous_metrics=continuous)

def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def run(baseline, primary_csv, output_dir='/content', implementation_commit='UNRECORDED'):
    if len(implementation_commit) != 40 or any(c not in '0123456789abcdef' for c in implementation_commit):
        raise ValueError('An actual 40-character implementation commit SHA is required')
    rows = load_baseline(baseline)
    tables = analyze(rows, read_primary(primary_csv))
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, records in tables.items():
        path = out / ('edge_decay_sensitivity_'+name+'.csv'); write_csv(path, records)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    record = dict(Branch=BRANCH, PlanCommit=PLAN_COMMIT, ImplementationCommit=implementation_commit,
        PrimaryCommit=PRIMARY_COMMIT, PrimaryCSVBlob=PRIMARY_BLOB, PrimaryExactMatch=True,
        BaselineSHA256=BASELINE_HASH, BaselineTrades=len(rows), Strategies=28,
        RunJST=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(), Periods=json.dumps(PERIODS),
        Settings=json.dumps(SETTINGS), UniqueSettings=7, DisplayedSettings=9,
        WarningDefinition='EDGE LOST or EDGE DECAY', InsufficientIncludedInDenominator=True,
        Labels='Official warning candidates only: 7/7 頑健; 5-6/7 中程度; 0-4/7 不安定',
        RulesDocument='docs/40_edge_decay_sensitivity_validation_plan.md',
        BaselineRecalculated=False, PrimaryOverwritten=False, LiveChanged=False,
        MonitorUsedForClassification=False, FreshHoldout=False, NewOfficialThreshold=False,
        CSVHashes=json.dumps(hashes, sort_keys=True))
    write_csv(out/'edge_decay_sensitivity_run_record.csv', [record])
    print('SensitivityはPrimary Resultを置き換えません。警告残存回数は重複除外7設定。')
    for r in tables['strategy_summary']:
        print(r['Strategy'], r['PrimaryClassification'], f"warning {r['WarningCountUnique']}/7", r['WarningRetentionLabel'],
              ' | '.join(f"{u}:{r[u]}" for u in dict.fromkeys(s[2] for s in SETTINGS)))
    print('2026は補助表示のみ。CSV:', out)
    return tables

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', required=True); p.add_argument('--primary-csv', required=True)
    p.add_argument('--output-dir', default='/content'); p.add_argument('--implementation-commit', required=True)
    a = p.parse_args(); run(a.baseline, a.primary_csv, a.output_dir, a.implementation_commit)
