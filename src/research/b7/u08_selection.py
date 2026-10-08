"""Frozen calendar policy. No price loading or earlier-stage reselection."""
from copy import deepcopy
from .stage1_metrics import gate
from .stage1_contract import YEARS

BUCKETS = ('D1', 'D2', 'D3')
MONTHS = tuple(range(1, 13))


def pf_off(m):
    return m['PFState'] == 'FINITE' and m['PFpips'] < 1.0


def improvement(baseline, candidate):
    def greater(key):
        return baseline[key] is not None and candidate[key] is not None and candidate[key] > baseline[key]
    checks = dict(AvgPips=greater('AvgPips'),
                  PFpips=baseline['PFState'] == candidate['PFState'] == 'FINITE' and greater('PFpips'),
                  MedianAnnualAvgPips=greater('MedianAnnualAvgPips'),
                  PositiveYearCount=candidate['PositiveYearCount'] >= baseline['PositiveYearCount'],
                  MaxDDPips=candidate['MaxDDPips'] <= baseline['MaxDDPips'])
    return dict(Checks=checks, Adopt=all(checks.values()))


def dom_sample(m, baseline):
    checks = dict(Overall=m['Trades']*5 >= baseline['Trades'],
                  Annual={str(y): m['Annual'][str(y)]['Trades']*5 >= baseline['Annual'][str(y)]['Trades'] for y in YEARS})
    def fraction(a, b):return a/b if b else None
    return dict(OverallTradeFraction=fraction(m['Trades'], baseline['Trades']),
                AnnualTradeFraction={str(y): fraction(m['Annual'][str(y)]['Trades'], baseline['Annual'][str(y)]['Trades']) for y in YEARS},
                SampleChecks=checks, MinimumSamplePASS=checks['Overall'] and all(checks['Annual'].values()))


def dom_off(m, sample):
    return bool(sample and m['TotalPips'] < 0 and m['AvgPips'] is not None and m['AvgPips'] < 0
                and pf_off(m) and m['NegativeYearCount'] >= 3)


def month_sample(m):
    return m['Trades'] >= 16 and all(m['Annual'][str(y)]['Trades'] >= 3 for y in YEARS)


def month_off(m, sample):
    # No AvgPips condition is added to the frozen Month OFF predicate.
    return bool(sample and m['TotalPips'] < 0 and pf_off(m) and m['NegativeYearCount'] >= 3)


def off_key(item):
    m = item['Metrics']
    return (-m['NegativeYearCount'], m['AvgPips'], m['PFpips'], m['TotalPips'], item['Order'])


def dom_stage(view):
    baseline = view.metrics(); diagnostics = []
    for order, bucket in enumerate(BUCKETS):
        m = view.metrics(buckets=[bucket]); sample = dom_sample(m, baseline)
        diagnostics.append(dict(Bucket=bucket, Order=order, Metrics=m, **sample,
                                OFFCandidate=dom_off(m, sample['MinimumSamplePASS'])))
    ranked = sorted((d for d in diagnostics if d['OFFCandidate']), key=off_key)
    ranking = [d['Bucket'] for d in ranked]
    states = [dict(Name='DOM0', OFFBuckets=[], Metrics=baseline, Comparison=None, Adopted=True)]
    current = states[0]
    for count in (1, 2):
        if len(ranking) < count:
            break
        disabled = ranking[:count]; active = [b for b in BUCKETS if b not in disabled]
        m = view.metrics(buckets=active); comparison = improvement(current['Metrics'], m)
        trial = dict(Name=f'DOM{count}', OFFBuckets=disabled, Metrics=m, Comparison=comparison, Adopted=comparison['Adopt'])
        states.append(trial)
        if not comparison['Adopt']:
            break  # No alternate bucket or DOM2 rescue after DOM1 rejection.
        current = trial
    return dict(DOM0=baseline, Diagnostics=diagnostics, InitialOFFCandidates=[d['Bucket'] for d in diagnostics if d['OFFCandidate']],
                OFFRanking=ranking, States=states, AdoptedState=current['Name'], OFFBuckets=current['OFFBuckets'],
                ActiveBuckets=[b for b in BUCKETS if b not in current['OFFBuckets']], FinalMetrics=current['Metrics'],
                FinalGatePASS=gate(current['Metrics']))


def month_stage(view, buckets):
    baseline = view.metrics(buckets=buckets); diagnostics = []; lomo = []
    for month in MONTHS:
        m = view.metrics(buckets=buckets, months=[month]); sample = month_sample(m)
        initial = month_off(m, sample)
        remaining = view.metrics(buckets=buckets, months=[n for n in MONTHS if n != month])
        comparison = improvement(baseline, remaining)
        lomo.append(dict(Month=month, Metrics=remaining, Comparison=comparison))
        diagnostics.append(dict(Month=month, Order=month, Metrics=m, MinimumSamplePASS=sample,
                                InitialOFFCandidate=initial, FormalOFFCandidate=initial and comparison['Adopt']))
    ranked = sorted((d for d in diagnostics if d['FormalOFFCandidate']), key=off_key)
    ranking = [d['Month'] for d in ranked]
    states = [dict(Name='M0', OFFMonths=[], Metrics=baseline, Comparison=None, Adopted=True)]
    current = states[0]
    if ranking:
        first = lomo[ranking[0]-1]
        comparison = improvement(baseline, first['Metrics'])
        if not comparison['Adopt']:
            raise ValueError('Formal OFF/M1 LOMO contradiction; STOP')
        current = dict(Name='M1', OFFMonths=ranking[:1], Metrics=first['Metrics'], Comparison=comparison, Adopted=True)
        states.append(current)
        if len(ranking) >= 2:
            m = view.metrics(buckets=buckets, months=[n for n in MONTHS if n not in ranking[:2]])
            comparison = improvement(current['Metrics'], m)
            trial = dict(Name='M2', OFFMonths=ranking[:2], Metrics=m, Comparison=comparison, Adopted=comparison['Adopt'])
            states.append(trial)
            if comparison['Adopt']:current = trial
    # There is deliberately no additional final U01 gate in Month.
    return dict(M0=baseline, Diagnostics=diagnostics, LOMO=lomo,
                InitialOFFCandidates=[d['Month'] for d in diagnostics if d['InitialOFFCandidate']],
                FormalOFFCandidates=[d['Month'] for d in diagnostics if d['FormalOFFCandidate']],
                OFFRanking=ranking, States=states, AdoptedState=current['Name'], OFFMonths=current['OFFMonths'],
                ActiveMonths=[n for n in MONTHS if n not in current['OFFMonths']], FinalMetrics=current['Metrics'])


def source_identity(record):
    return {k: deepcopy(record[k]) for k in ('U07Status', 'U07CandidateSHA256', 'U07CheckpointSHA256', 'U07ProducerImplementationSHA', 'U06SourceIdentity')}


def select(record, view):
    out = {k: deepcopy(record[k]) for k in ('CandidateID', 'Symbol', 'PairRank', 'Schedule', 'FormalSL', 'FormalTP', 'AnchorWeekday', 'FormalWeekdays', 'SetName')}
    dom = dom_stage(view)
    out.update(U07SourceIdentity=source_identity(record), DOM=dom, Month=None, FormalDOM=None, FormalMonths=None,
               CalendarFreeze=None, Status='DROP_U08_DOM_FINAL_GATE', DropReason='DOM_FINAL_GATE')
    if not dom['FinalGatePASS']:
        return out  # No prior DOM fallback, no Month evaluation, no replacement.
    month = month_stage(view, dom['ActiveBuckets'])
    calendar = dict(FormalWeekdays=deepcopy(record['FormalWeekdays']), FormalDOMBuckets=dom['ActiveBuckets'],
                    OFFBuckets=dom['OFFBuckets'], FormalMonths=month['ActiveMonths'], OFFMonths=month['OFFMonths'])
    out.update(Month=month, FormalDOM=dom['ActiveBuckets'], FormalMonths=month['ActiveMonths'], CalendarFreeze=calendar,
               Status='PASS_U08', DropReason=None)
    return out
