"""Frozen 56-input audit; no prices or U07 performance evaluation."""
from .stage1_contract import ROOT, Structure, digest, object_hash, verify_conditions
from .u06_finalize_only import read

RESULT_SHA = 'c526dc1bb49d168376e5cb4858174524c0a63f7a'
INPUT_SHA = 'fbb78686e8a767bb8fbaa903e9b89eee99d9c856b2182d29f1953bb51273fe39'
INPUT = ROOT / 'research_inputs/b7/u07_selected56_input.json'
CONFIG = ROOT / 'research_inputs/b7/u07_config.json'


def validate(data, audit, source_identity, original):
    records = data['Candidates']
    if data['CandidateCount'] != 56 or len(records) != 56 or data['NoReplacement'] is not True:
        raise ValueError('56 candidates / NoReplacement required')
    if len({r['CandidateID'] for r in records}) != 56:
        raise ValueError('duplicate CandidateID')
    if data['SourceIdentitySHA256'] != object_hash(source_identity):
        raise ValueError('U06 identity')
    hashes = {x['Path']: x['SHA256'] for x in audit['TrustedFiles']}
    originals = {x['CandidateID']: x for x in original['Candidates']}
    for r in records:
        s = Structure.from_id(r['CandidateID'])
        if r['Schedule'] != s.definition() or r['Symbol'] != s.symbol:
            raise ValueError('schedule/anchor mutation')
        old = originals[r['CandidateID']]
        if any(r[k] != old[k] for k in ('Symbol', 'PairRank', 'Schedule')):
            raise ValueError('original representative mutation')
        if r['U06Status'] != 'PASS_U06':
            raise ValueError('U06 PASS only')
        if type(r['FormalSL']) is not int or r['FormalSL'] <= 0 or r['FormalSL'] % 5:
            raise ValueError('FormalSL')
        tp = r['FormalTP']
        if tp is not None and (type(tp) is not int or tp <= 0 or tp % 5):
            raise ValueError('FormalTP; null means TP_NONE')
        for field, name in [('SourceCandidateSHA256', 'candidate.json'), ('SourceCheckpointSHA256', 'checkpoint.json')]:
            if r[field] != hashes[f'jobs/{r["CandidateID"]}/{name}']:
                raise ValueError('source candidate/checkpoint hash')
    return data


def input_config():
    verify_conditions()
    cfg = read(CONFIG)
    if cfg['U06ResultFreezeSHA'] != RESULT_SHA or cfg['InputSHA256'] != INPUT_SHA or digest(INPUT) != INPUT_SHA:
        raise ValueError('frozen U07 input identity')
    for p, h in cfg['FrozenSources'].items():
        if digest(ROOT / p) != h:
            raise ValueError('frozen source hash')
    data = validate(read(INPUT), read(ROOT/'results/b7/u06/drive_checkpoint_audit.json'),
                    read(ROOT/'results/b7/u06/input_identity.json'), read(ROOT/'research_inputs/b7/u06_selected72_input.json'))
    return cfg, data
