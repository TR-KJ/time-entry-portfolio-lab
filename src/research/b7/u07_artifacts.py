"""U07 identity and completed-result schema, without evaluation or selection."""
from .stage1_contract import ROOT, CONDITIONS_SHA, digest
from .u07_input import input_config, INPUT, CONFIG, RESULT_SHA
from .u06_finalize_only import read

RELEASE = ROOT/'results/b7/u07_implementation/release_manifest.json'


def identity(producer_sha, environment):
    _, data = input_config()
    return dict(ImplementationSHA=producer_sha, ConditionsFreezeSHA=CONDITIONS_SHA,
                FullPrespecSHA256=digest(ROOT/'research_inputs/b7/full_research_prespec.json'),
                U07ConfigSHA256=digest(CONFIG), U06ResultFreezeSHA=RESULT_SHA, U07InputSHA256=digest(INPUT),
                M1ManifestSHA256=digest(ROOT/'research_inputs/b7/expected_m1_manifest.csv'),
                M1ExactIdentity=read(ROOT/'results/b7/u06/input_identity.json')['M1ExactIdentity'],
                Environment=environment, CandidateIDs=[r['CandidateID'] for r in data['Candidates']])


def validate_result(result, record):
    for k in ('CandidateID', 'Symbol', 'PairRank', 'Schedule', 'FormalSL', 'FormalTP'):
        if result.get(k) != record[k]:
            raise ValueError('candidate definition')
    if result.get('U06SourceIdentity') != {k: record[k] for k in ('SourceCandidateSHA256', 'SourceCheckpointSHA256', 'U06Status')}:
        raise ValueError('U06 source identity')
    if result.get('AnchorWeekday') != record['Schedule']['Weekday']:
        raise ValueError('Anchor identity')
    diagnostics = result.get('WeekdayDiagnostics', [])
    if len(diagnostics) != 5 or [d['Weekday'] for d in diagnostics] != list(range(5)):
        raise ValueError('five weekday diagnostics')
    if any(d.get('Classification') not in ('CORE', 'SUPPORT', 'NON_SUPPORT') or not isinstance(d.get('Metrics'), dict) for d in diagnostics):
        raise ValueError('diagnostic schema')
    anchor = diagnostics[result['AnchorWeekday']]['Classification']
    status = result.get('Status')
    if status == 'PASS_U07':
        days = result.get('FormalWeekdays')
        if not isinstance(days, list) or not days or any(type(w) is not int or w not in range(5) for w in days) or days != sorted(set(days)):
            raise ValueError('FormalWeekdays')
        if anchor != 'CORE' or result['AnchorWeekday'] not in days or result.get('DropReason') is not None:
            raise ValueError('PASS anchor')
        sets = result.get('Sets', [])
        if not 1 <= len(sets) <= 4 or len({s['SetName'] for s in sets}) != len(sets):
            raise ValueError('completed sets')
        by_name = {s['SetName']: s for s in sets}
        selected = by_name.get(result.get('SetName'), {})
        if result.get('Best') not in by_name or selected.get('Weekdays') != days or selected.get('FormalGatePASS') is not True or selected.get('Plateau') is not True:
            raise ValueError('selected set schema')
        if result['SetName'] not in result.get('Plateau', []):
            raise ValueError('plateau schema')
    elif status == 'DROP_U07_ANCHOR_NOT_CORE':
        if anchor == 'CORE' or result.get('FormalWeekdays') is not None or result.get('SetName') is not None or result.get('Best') is not None or result.get('Sets') != [] or result.get('GeneratedSets') != {} or result.get('Plateau') != [] or result.get('DropReason') != 'ANCHOR_NOT_CORE':
            raise ValueError('DROP schema')
    else:
        raise ValueError('nonterminal candidate')
    return result
