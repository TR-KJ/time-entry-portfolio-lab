"""Audit only frozen U07 result metadata; never evaluate performance."""
from .stage1_contract import ROOT, Structure, digest, object_hash, verify_conditions
from .u06_finalize_only import read
RESULT_SHA = '21140269596584575677421934399122614f6cd6'
PRODUCER_SHA = '9adeef8514fb76efec70a2cc46ce85e306ea0597'
INPUT_SHA = '7c49b9cd0374b57f4da78eb784aa646050cba507b0ff037e303085a61deb7616'
INPUT = ROOT/'research_inputs/b7/u08_selected56_input.json'
CONFIG = ROOT/'research_inputs/b7/u08_config.json'


def validate(data, audit, source_identity, original, summary, archive):
    records = data['Candidates']
    if data['CandidateCount'] != 56 or len(records) != 56 or data['NoReplacement'] is not True:
        raise ValueError('56 candidates / NoReplacement')
    ids = [r['CandidateID'] for r in records]
    if len(set(ids)) != 56 or ids != source_identity['CandidateIDs']:
        raise ValueError('ordered unique56')
    if data['U07ProducerImplementationSHA'] != PRODUCER_SHA or source_identity['ImplementationSHA'] != PRODUCER_SHA or data['SourceIdentitySHA256'] != object_hash(source_identity):
        raise ValueError('U07 producer identity')
    files = {f['Path']: f for f in archive['Files']}
    if data['SourceArchiveZIP'] != files['archive.zip'] or data['SourceManifest'] != files['artifact_manifest.json'] or data['SourceCandidateResultsSHA256'] != files['candidate_results.json']['SHA256']:
        raise ValueError('archive identity')
    hashes = {f['Path']: f['SHA256'] for f in audit['TrustedFiles']}
    originals = {r['CandidateID']: r for r in original['Candidates']}
    weekdays = {r['CandidateID']: r for r in summary['CandidateWeekdaySummary']}
    for r in records:
        cid = r['CandidateID']; s = Structure.from_id(cid); old = originals[cid]; w = weekdays[cid]
        if r['Schedule'] != s.definition() or r['U07Status'] != 'PASS_U07' or r['U07ProducerImplementationSHA'] != PRODUCER_SHA:
            raise ValueError('PASS source/schedule/producer')
        for k in ('Symbol', 'PairRank', 'Schedule', 'FormalSL', 'FormalTP'):
            if r[k] != old[k]:
                raise ValueError('fixed field mutation')
        for k in ('Direction', 'EntryMinute', 'ExitMinute', 'ExitDayOffset', 'HoldingMinutes'):
            if r[k] != s.definition()[k]:
                raise ValueError('schedule projection')
        for k in ('AnchorWeekday', 'FormalWeekdays', 'SetName'):
            if r[k] != w[k]:
                raise ValueError('weekday provenance mutation')
        if r['U06SourceIdentity'] != {k: old[k] for k in ('SourceCandidateSHA256', 'SourceCheckpointSHA256', 'U06Status')}:
            raise ValueError('U06 provenance')
        for k, name in [('U07CandidateSHA256', 'candidate.json'), ('U07CheckpointSHA256', 'checkpoint.json')]:
            if r[k] != hashes[f'jobs/{cid}/{name}']:
                raise ValueError('U07 candidate/checkpoint hash')
    return data


def input_config():
    verify_conditions(); cfg = read(CONFIG)
    if cfg['U07ResultFreezeSHA'] != RESULT_SHA or cfg['InputSHA256'] != INPUT_SHA or digest(INPUT) != INPUT_SHA:
        raise ValueError('frozen U08 input identity')
    for path, expected in cfg['FrozenSources'].items():
        if digest(ROOT/path) != expected:
            raise ValueError('frozen source hash')
    data = validate(read(INPUT), read(ROOT/'results/b7/u07/drive_checkpoint_audit.json'),
                    read(ROOT/'results/b7/u07/input_identity.json'), read(ROOT/'research_inputs/b7/u07_selected56_input.json'),
                    read(ROOT/'results/b7/u07/u07_result_summary.json'), read(ROOT/'results/b7/u07/u07_archive_manifest.json'))
    return cfg, data
