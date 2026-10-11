"""B7 immutable Candidate Freeze and U11 input projection; no performance imports."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import math
import re

from .stage1_contract import ROOT, canonical, digest, object_hash, verify_conditions

SOURCE_COMMIT = 'e0c57c8815d7f49c158585218fe5300bda699f95'
PRODUCER = 'dc12531b559aaa7a821626e4813a2d291125efe4'
SOURCE_PATH = 'research_inputs/b7/candidate_freeze_selected40_input.json'
SOURCE = ROOT / SOURCE_PATH
SOURCE_SHA = 'ceacffaaf085cb3470b28548328315dfed9d817e53f368043f54b3583017b328'
SOURCE_BYTES = 254958
SOURCE_OBJECT_SHA = 'bfa0e1a06a8f2d7f30f8be842a7d2688fd3368a77f27af9817c4681203fff3ab'
INPUT_SHA = '7bce58b58102be11d8fe2debe4212b47a52cc685d10b044a9f7663e5b0bad11f'
CALENDAR_SHA = '7a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb'
CALENDAR_COMMIT = '173be2a114dad6bd183a0a1515581528850f0850'
PAIRS = dict(AUDJPY=4, AUDUSD=0, EURAUD=7, EURJPY=8, EURUSD=5, GBPAUD=5, GBPJPY=8, GBPUSD=2, USDJPY=1)
MODES = dict(P0=37, P1=2, P2=1, P3=0)
PROTECTION = {
    'B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610': 'P2',
    'B7S1:GBPUSD:LONG:TUE:E0365:D0:X1120:H0755': 'P1',
    'B7S1:GBPUSD:LONG:TUE:E0370:D0:X1180:H0810': 'P1',
}
FIXED_FIELDS = ('CandidateID Symbol Direction PairRank AnchorWeekday FormalEntryMinute '
                'FormalExitDayOffset FormalExitMinute FormalHoldingMinutes FormalSL FormalTP '
                'FormalWeekdays FormalDOMBuckets OFFBuckets FormalMonths OFFMonths CalendarFreeze '
                'EntryShiftMinutes ExitShiftMinutes U09Decision FormalEventMode E2EventSet '
                'EventCalendarSHA256 CalendarSourceCommit FormalProtectionMode').split()
PROVENANCE = ('U06SourceIdentity U07SourceIdentity U08SourceIdentity U09CandidateSHA256 '
              'U09CheckpointSHA256 U09ProducerImplementationSHA U10CandidateSHA256 '
              'U10CandidateObjectSHA256 U10CheckpointSHA256 U10ProducerImplementationSHA '
              'U10PCandidateSHA256 U10PCheckpointSHA256 U10PProducerImplementationSHA '
              'U10PConfigSHA256 DataManifestSHA256 EventCalendarSHA256 CalendarSourceCommit '
              'E2TradeStreamSHA256 SelectedModeTradeStreamSHA256').split()
BLOCK_FIELDS = 'Trades Wins Losses ZeroPips TotalPips AvgPips PFState PFpips MaxDDPips'.split()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    def nonfinite(value):
        raise ValueError('nonfinite JSON constant')
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=nonfinite)


def exact(a, b):
    """Recursive typed equality, including exact unrounded float encodings."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return math.isfinite(a) and math.isfinite(b) and a.hex() == b.hex()
    return a == b


def sha_fields(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith('SHA256'):
                require(isinstance(item, str) and re.fullmatch('[0-9a-f]{64}', item), 'SHA256 format: ' + key)
            elif key.endswith('SHA') or key == 'CalendarSourceCommit':
                require(isinstance(item, str) and re.fullmatch('[0-9a-f]{40}', item), 'commit SHA format: ' + key)
            sha_fields(item)
    elif isinstance(value, list):
        for item in value:
            sha_fields(item)


def metric_schema(block):
    require(isinstance(block, dict) and set(BLOCK_FIELDS) <= block.keys(), 'metric fields')
    for key in ('Trades', 'Wins', 'Losses', 'ZeroPips'):
        require(type(block[key]) is int and block[key] >= 0, 'metric count schema')
    for key in ('TotalPips', 'AvgPips', 'MaxDDPips'):
        value = block[key]
        require(value is None and key == 'AvgPips' or type(value) in (int, float) and math.isfinite(value), 'numeric metric schema')
    require(block['PFState'] in ('FINITE', 'INF', 'UNDEFINED'), 'PFState schema')
    pf = block['PFpips']
    require((type(pf) in (int, float) and math.isfinite(pf)) if block['PFState'] == 'FINITE' else pf is None, 'PF value schema')


def validate_source(data):
    require(isinstance(data, dict), 'source object')
    require(data['Scope'] == 'B7_CANDIDATE_FREEZE_INPUT', 'source scope')
    require(data['CandidateFreezeExecuted'] is False and data['NoReplacement'] is True, 'historical snapshot flags')
    require(data['ValidationPerformance'] == data['MonitorPerformance'] == 'NOT_RUN', 'blind snapshot')
    records, ids = data['Candidates'], data['CandidateIDs']
    require(data['CandidateCount'] == len(records) == len(ids) == len(set(ids)) == 40, 'ordered unique40')
    require(ids == [r['CandidateID'] for r in records], 'CandidateIDs order')
    require(data['U10PProducerImplementationSHA'] == PRODUCER and data['U10PInputSHA256'] == INPUT_SHA, 'producer/input')
    require(data['EventCalendarSHA256'] == CALENDAR_SHA and data['CalendarSourceCommit'] == CALENDAR_COMMIT, 'calendar identity')
    require(data['U10PResultFreezeReference'] and data['SourceArchive'] == '/MyDrive/b7_u10p_20261010_01_archive' and data['SourceCheckpointRoot'] == '/MyDrive/b7_u10p_20261010_01_checkpoints', 'source lineage')
    require(data['PairCounts'] == PAIRS == {s: sum(r['Symbol'] == s for r in records) for s in PAIRS}, 'pair counts')
    require(data['ProtectionModeCounts'] == MODES == {m: sum(r['FormalProtectionMode'] == m for r in records) for m in MODES}, 'mode counts')
    require({r['CandidateID']: r['FormalProtectionMode'] for r in records if r['FormalProtectionMode'] != 'P0'} == PROTECTION, 'protection mapping')
    for r in records:
        require(set(FIXED_FIELDS + PROVENANCE + ['SelectedModeDiscoveryMetrics', 'U10PStatus']) <= r.keys(), 'required fixed/provenance fields')
        require(r['U10PStatus'] == 'PASS_U10P' and r['FormalEventMode'] == 'E2', 'terminal/event identity')
        require(r['EventCalendarSHA256'] == CALENDAR_SHA and r['CalendarSourceCommit'] == CALENDAR_COMMIT, 'candidate calendar')
        require(r['U10PProducerImplementationSHA'] == PRODUCER, 'candidate producer')
        m = r['SelectedModeDiscoveryMetrics']
        metric_schema(m)
        require(set(['Annual', 'PositiveYearCount', 'NegativeYearCount', 'MedianAnnualAvgPips', 'WorstYearAvgPips']) <= m.keys(), 'Discovery baseline schema')
        require(set(m['Annual']) == {'2020', '2021', '2022', '2023'}, 'Discovery annual years only')
        for year in m['Annual'].values():
            metric_schema(year)
        for key in ('PositiveYearCount', 'NegativeYearCount'):
            require(type(m[key]) is int, 'year count schema')
        for key in ('MedianAnnualAvgPips', 'WorstYearAvgPips'):
            require(m[key] is None or type(m[key]) in (int, float) and math.isfinite(m[key]), 'annual summary schema')
    sha_fields(data)
    # Pins every original field, float, order, provenance and top-level snapshot.
    # No uniqueness constraint is imposed on trade stream hashes across candidates.
    require(object_hash(data) == SOURCE_OBJECT_SHA, 'exact frozen source object')
    return data


def load_source(path=SOURCE):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'regular source file')
    require(path.stat().st_size == SOURCE_BYTES and digest(path) == SOURCE_SHA, 'exact source SHA/Bytes')
    data = validate_source(read(path))
    require(digest(path) == SOURCE_SHA, 'source unchanged during read')
    return data


def encoded(value):
    return (canonical(value) + '\n').encode()


def file_identity(value):
    raw = encoded(value)
    return dict(SHA256=hashlib.sha256(raw).hexdigest(), Bytes=len(raw), ObjectSHA256=object_hash(value))


def build(source=None):
    """Construct only immutable identities/inventory and U11 input; never evaluate."""
    data = load_source() if source is None else validate_source(source)
    prespec = verify_conditions()
    contract = deepcopy(prespec['U11'])
    environment = deepcopy(prespec['InheritedEnvironmentAndExecution'])
    protocol = environment['FrozenStage0Protocol']
    require(digest(ROOT / protocol['Path']) == protocol['SHA256'], 'frozen execution protocol')
    records = data['Candidates']
    fingerprints = dict(
        CandidateSetSHA256=object_hash(records),
        ProtectionMappingSHA256=object_hash({r['CandidateID']: r['FormalProtectionMode'] for r in records}),
        ScheduleMappingSHA256=object_hash({r['CandidateID']: {k: r[k] for k in FIXED_FIELDS} for r in records}),
        DiscoveryBaselineSHA256=object_hash({r['CandidateID']: r['SelectedModeDiscoveryMetrics'] for r in records}),
        SelectedStreamMappingSHA256=object_hash({r['CandidateID']: r['SelectedModeTradeStreamSHA256'] for r in records}),
        EnvironmentExecutionSHA256=object_hash(environment),
    )
    inventory = dict(Scope='B7_CANDIDATE_FREEZE_INVENTORY', CandidateCount=40, Candidates=[
        dict({k: deepcopy(r[k]) for k in FIXED_FIELDS}, CandidateObjectSHA256=object_hash(r),
             SelectedModeDiscoveryMaxDDPips=r['SelectedModeDiscoveryMetrics']['MaxDDPips'],
             SelectedModeTradeStreamSHA256=r['SelectedModeTradeStreamSHA256']) for r in records])
    shared = dict(CandidateCount=40, CandidateIDs=deepcopy(data['CandidateIDs']), NoReplacement=True,
                  PairCounts=deepcopy(PAIRS), ProtectionModeCounts=deepcopy(MODES),
                  U10PResultFreezeSHA=SOURCE_COMMIT, U10PProducerImplementationSHA=PRODUCER,
                  U10PInputSHA256=INPUT_SHA, EventCalendarSHA256=CALENDAR_SHA, CalendarSourceCommit=CALENDAR_COMMIT)
    u11 = dict(shared, Scope='U11_VALIDATION_FORMAL_INPUT', Candidates=deepcopy(records),
               CandidateFreezeSourceSHA256=SOURCE_SHA, CandidateFreezeSourceBytes=SOURCE_BYTES,
               CandidateFreezeReference='Containing Candidate Freeze commit; bind its actual SHA in the future U11 implementation identity',
               FrozenU11Contract=contract, FrozenU11ContractSHA256=object_hash(contract),
               ValidationPeriod=contract['ValidationPeriod'], FrozenEnvironmentAndExecution=environment,
               FullPrespecSHA256=digest(ROOT / 'research_inputs/b7/full_research_prespec.json'),
               Fingerprints=fingerprints,
               CandidateFreezeArtifacts={'candidate_inventory.json': file_identity(inventory), 'u11_contract.json': file_identity(contract)},
               ValidationPerformanceEvaluated=False, MonitorPerformanceEvaluated=False,
               CandidateSetImmutable=True, PostValidationRetuningAllowed=False, RescuePASSAllowed=False)
    require(exact(u11['Candidates'], records), 'recursive exact projection')
    identity = dict(shared, Scope='B7_CANDIDATE_FREEZE', Status='COMPLETE_CANDIDATE_FREEZE',
                    SourceCommit=SOURCE_COMMIT, SourceCandidateFreezeInput=SOURCE_PATH,
                    SourceCandidateFreezeInputSHA256=SOURCE_SHA, SourceCandidateFreezeInputBytes=SOURCE_BYTES,
                    SourceCandidateFreezeInputObjectSHA256=SOURCE_OBJECT_SHA,
                    CandidateFreezeReference='Containing commit SHA', CandidateSetImmutable=True,
                    ValidationBlindSeal='Candidate set frozen before any U11 performance is opened',
                    ValidationPerformance='NOT_RUN', MonitorPerformance='NOT_RUN',
                    Fingerprints=fingerprints, FrozenEnvironmentAndExecution=environment,
                    U11Input=dict(Path='research_inputs/b7/u11_validation_selected40_input.json', **file_identity(u11)),
                    Inventory=file_identity(inventory), U11Contract=file_identity(contract))
    return {'candidate_freeze_identity.json': identity, 'candidate_inventory.json': inventory,
            'u11_contract.json': contract, 'u11_validation_selected40_input.json': u11}


def validate_u11(value, source=None):
    expected = build(source)['u11_validation_selected40_input.json']
    require(exact(value, expected), 'U11 exact structural projection')
    return value
