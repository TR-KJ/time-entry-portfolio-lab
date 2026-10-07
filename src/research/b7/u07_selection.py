"""Frozen weekday policy. Evaluators supply trades; sets are re-aggregated."""
from copy import deepcopy
import pandas as pd
from .stage1_metrics import gate, summarize
from .stage1_contract import Structure

PRIORITY = ('W3', 'W2', 'W1', 'W0')


def classification(metrics):
    return 'CORE' if gate(metrics) else ('SUPPORT' if gate(metrics, True) else 'NON_SUPPORT')


def generated_sets(anchor, classes):
    if len(classes) != 5 or classes[anchor] != 'CORE':
        raise ValueError('Anchor CORE required')
    generated = {'W0': [anchor], 'W1': [w for w in range(5) if classes[w] == 'CORE'],
                 'W2': [w for w in range(5) if classes[w] in ('CORE', 'SUPPORT')], 'W3': list(range(5))}
    groups = {}
    for name in PRIORITY:
        groups.setdefault(tuple(generated[name]), []).append(name)
    unique = [dict(SetName=names[0], Aliases=names, Weekdays=list(days)) for days, names in groups.items()]
    return generated, unique


def aggregate(streams):
    trades = [t for stream in streams for t in stream]
    # A candidate has one entry per date; identical entry cannot appear twice,
    # even if a caller changes its fixed key or result fields.
    entries = [t['EntryTime'] for t in trades]
    if len(set(entries)) != len(entries):
        raise ValueError('duplicate trade')
    return summarize(trades)


def choose(sets):
    passed = [s for s in sets if s['FormalGatePASS']]
    if not passed:
        raise ValueError('Anchor CORE contradicts absent Formal PASS W0; STOP')
    best = min(passed, key=lambda s: (-s['Metrics']['MedianAnnualAvgPips'],
                                     -s['Metrics']['PositiveYearCount'], PRIORITY.index(s['SetName'])))
    threshold = best['Metrics']['MedianAnnualAvgPips'] * .80
    plateau = [s for s in passed if s['Metrics']['MedianAnnualAvgPips'] >= threshold
               and s['Metrics']['PositiveYearCount'] >= best['Metrics']['PositiveYearCount']]
    selected = min(plateau, key=lambda s: (-len(s['Weekdays']), PRIORITY.index(s['SetName'])))
    return best, plateau, selected


def select(record, weekday_trades):
    """Five weekdays, fixed SL/TP/schedule; never reselect Anchor."""
    s = Structure.from_id(record['CandidateID'])
    if record['Schedule'] != s.definition() or set(weekday_trades) != set(range(5)):
        raise ValueError('frozen schedule / five weekdays')
    streams = deepcopy(weekday_trades)
    for w, trades in streams.items():
        for t in trades:
            if t['Status'] != 'OK' or pd.Timestamp(t['EntryTime']).weekday() != w:
                raise ValueError('weekday trade membership')
    metrics = [aggregate([streams[w]]) for w in range(5)]
    classes = [classification(m) for m in metrics]
    out = {k: deepcopy(record[k]) for k in ('CandidateID', 'Symbol', 'PairRank', 'Schedule', 'FormalSL', 'FormalTP')}
    out.update(U06SourceIdentity={k: record[k] for k in ('SourceCandidateSHA256', 'SourceCheckpointSHA256', 'U06Status')},
               AnchorWeekday=s.weekday, WeekdayDiagnostics=[dict(Weekday=w, Classification=classes[w], Metrics=metrics[w]) for w in range(5)],
               GeneratedSets={}, Sets=[], Best=None, Plateau=[], FormalWeekdays=None, SetName=None,
               Status='DROP_U07_ANCHOR_NOT_CORE', DropReason='ANCHOR_NOT_CORE')
    if classes[s.weekday] != 'CORE':
        return out
    generated, sets = generated_sets(s.weekday, classes)
    for item in sets:
        item['Metrics'] = aggregate([streams[w] for w in item['Weekdays']])
        item['FormalGatePASS'] = gate(item['Metrics'])
    best, plateau, selected = choose(sets)
    for item in sets:
        item['Plateau'] = item in plateau
    out.update(GeneratedSets=generated, Sets=sets, Best=best['SetName'], Plateau=[s['SetName'] for s in plateau],
               FormalWeekdays=selected['Weekdays'], SetName=selected['SetName'], Status='PASS_U07', DropReason=None)
    return out
