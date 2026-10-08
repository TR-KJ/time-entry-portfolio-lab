"""U08 checkpoint schemas and summary projection; no performance evaluation."""
from collections import Counter
from .stage1_contract import ROOT, CONDITIONS_SHA, digest
from .u08_input import input_config, INPUT, CONFIG, RESULT_SHA
from .u06_finalize_only import read
RELEASE = ROOT/'results/b7/u08_implementation/release_manifest.json'


def identity(producer_sha, environment):
    _, data = input_config()
    return dict(ImplementationSHA=producer_sha, ConditionsFreezeSHA=CONDITIONS_SHA,
                FullPrespecSHA256=digest(ROOT/'research_inputs/b7/full_research_prespec.json'),
                U08ConfigSHA256=digest(CONFIG), U07ResultFreezeSHA=RESULT_SHA, U08InputSHA256=digest(INPUT),
                M1ManifestSHA256=digest(ROOT/'research_inputs/b7/expected_m1_manifest.csv'),
                M1ExactIdentity=read(ROOT/'results/b7/u07/input_identity.json')['M1ExactIdentity'],
                Environment=environment, CandidateIDs=[r['CandidateID'] for r in data['Candidates']])


def validate_result(result, record):
    for k in ('CandidateID', 'Symbol', 'PairRank', 'Schedule', 'FormalSL', 'FormalTP', 'AnchorWeekday', 'FormalWeekdays', 'SetName'):
        if result.get(k) != record[k]:raise ValueError('fixed candidate identity')
    source = {k: record[k] for k in ('U07Status', 'U07CandidateSHA256', 'U07CheckpointSHA256', 'U07ProducerImplementationSHA', 'U06SourceIdentity')}
    if result.get('U07SourceIdentity') != source:raise ValueError('U07 source identity')
    dom = result['DOM']
    if [d['Bucket'] for d in dom['Diagnostics']] != ['D1', 'D2', 'D3']:raise ValueError('DOM diagnostics')
    if dom['AdoptedState'] not in ('DOM0', 'DOM1', 'DOM2'):raise ValueError('DOM state')
    if len(dom['OFFBuckets']) > 2 or len(set(dom['OFFBuckets'])) != len(dom['OFFBuckets']) or any(b not in ('D1','D2','D3') for b in dom['OFFBuckets']):raise ValueError('DOM OFF')
    if dom['ActiveBuckets'] != [b for b in ('D1','D2','D3') if b not in dom['OFFBuckets']]:raise ValueError('DOM complement')
    adopted = [s for s in dom['States'] if s['Name'] == dom['AdoptedState'] and s['Adopted']]
    if len(adopted) != 1 or adopted[0]['OFFBuckets'] != dom['OFFBuckets'] or adopted[0]['Metrics'] != dom['FinalMetrics']:raise ValueError('DOM completion')
    if result['Status'] == 'DROP_U08_DOM_FINAL_GATE':
        if dom['FinalGatePASS'] is not False or result['DropReason'] != 'DOM_FINAL_GATE' or any(result[k] is not None for k in ('Month','FormalDOM','FormalMonths','CalendarFreeze')):raise ValueError('DROP schema')
    elif result['Status'] == 'PASS_U08':
        month = result['Month']
        if dom['FinalGatePASS'] is not True or result['DropReason'] is not None:raise ValueError('PASS gate')
        if [m['Month'] for m in month['Diagnostics']] != list(range(1,13)) or [m['Month'] for m in month['LOMO']] != list(range(1,13)):raise ValueError('12 Month/LOMO diagnostics')
        off = month['OFFMonths']
        if len(off) > 2 or len(set(off)) != len(off) or any(type(m) is not int or m not in range(1,13) for m in off):raise ValueError('Month OFF')
        if month['ActiveMonths'] != [m for m in range(1,13) if m not in off] or month['AdoptedState'] not in ('M0','M1','M2'):raise ValueError('Month complement/state')
        adopted = [s for s in month['States'] if s['Name'] == month['AdoptedState'] and s['Adopted']]
        if len(adopted) != 1 or adopted[0]['OFFMonths'] != off or adopted[0]['Metrics'] != month['FinalMetrics']:raise ValueError('Month completion')
        expected = dict(FormalWeekdays=record['FormalWeekdays'], FormalDOMBuckets=dom['ActiveBuckets'], OFFBuckets=dom['OFFBuckets'], FormalMonths=month['ActiveMonths'], OFFMonths=off)
        if result['CalendarFreeze'] != expected or result['FormalDOM'] != dom['ActiveBuckets'] or result['FormalMonths'] != month['ActiveMonths']:raise ValueError('Calendar Freeze')
    else:raise ValueError('nonterminal candidate')
    return result


def summaries(results):
    passed = [r for r in results if r['Status'] == 'PASS_U08']
    return {'dom_summary.json': dict(AdoptedStates=dict(Counter(r['DOM']['AdoptedState'] for r in results)),
                                    FinalGatePASS=sum(r['DOM']['FinalGatePASS'] for r in results)),
            'month_summary.json': dict(EvaluatedCandidates=len(passed), AdoptedStates=dict(Counter(r['Month']['AdoptedState'] for r in passed)),
                                       OFFMonths={str(m): sum(m in r['Month']['OFFMonths'] for r in passed) for m in range(1,13)}),
            'calendar_summary.json': [dict(CandidateID=r['CandidateID'], Status=r['Status'], CalendarFreeze=r['CalendarFreeze']) for r in results]}
