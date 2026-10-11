"""Exact immutable U11 input and Candidate Freeze binding; no performance."""
from .stage1_contract import ROOT,digest,object_hash,verify_conditions
from .candidate_freeze import read,validate_u11,exact
FREEZE_SHA='ebfe204d3561b064c1b4dc98d2fd417631dcc009'
RESULT_SHA=FREEZE_SHA
SUPPLEMENT_SHA='e34099b9c807df1f145f96ca92c2443fe552fa36'
INPUT=ROOT/'research_inputs/b7/u11_validation_selected40_input.json'
CONFIG=ROOT/'research_inputs/b7/u11_config.json'
INPUT_SHA='0a9db7f5d65191cd88153199470034a78286880920960442b9e300d0fbb18ed4'
INPUT_OBJECT='b0ad97127368ec624f4c29cc3be711d3fa35d04d263da4950fd92355e8b95ec8'
CALENDAR=ROOT/'research_inputs/b7/u10_event_calendar.json'

def input_config():
    prespec=verify_conditions();cfg=read(CONFIG)
    if cfg['CandidateFreezeSHA']!=FREEZE_SHA or digest(INPUT)!=INPUT_SHA or INPUT.stat().st_size!=257887:raise ValueError('Candidate Freeze/input identity')
    d=validate_u11(read(INPUT))
    if object_hash(d)!=INPUT_OBJECT or cfg['U11InputSHA256']!=INPUT_SHA or cfg['U11InputObjectSHA256']!=INPUT_OBJECT:raise ValueError('object identity')
    for key in ('FrozenU11Contract','Fingerprints','EventCalendarSHA256','CalendarSourceCommit','FrozenEnvironmentAndExecution'):
        if not exact(cfg[key],d[key]):raise ValueError('exact contract/fingerprint')
    if not exact(read(ROOT/'results/b7/candidate_freeze/u11_contract.json'),prespec['U11']):raise ValueError('U11 contract')
    if cfg['ValidationStart']!='2024-01-01 00:00:00' or cfg['ValidationEnd']!='2026-01-01 00:00:00':raise ValueError('Validation period')
    for p,h in cfg['FrozenSources'].items():
        if digest(ROOT/p)!=h:raise ValueError('frozen source mutation: '+p)
    # Candidate Freeze release_manifest remains a historical snapshot. Its old
    # source_of_truth/run_status entries are NOT refreshed or treated as current.
    return cfg,d
