"""Immutable U08 PASS54 projection and independently pinned supplement."""
from .stage1_contract import ROOT,Structure,digest,object_hash,verify_conditions
from .u06_finalize_only import read
RESULT_SHA='382f351c169da48e1fe4eadf31fc858bbd57eed0'
PRODUCER_SHA='0b33aa5ff6ff769b11212e9b8593242fb71c680c'
SUPPLEMENT_SHA='1466a2c3e8b3d523233c45d665a6cac21e974393'
SUPPLEMENT_HASH='cefa5aed9fc820c8bbf4dd4a57622263cd2443bc8509f8016f62bb20e76a92f3'
INPUT_SHA='8faa886c3d1a72e8020688b8931481d81d1df637d63b0b368e0171b8d1dce2ca'
INPUT=ROOT/'research_inputs/b7/u09_selected54_input.json'
CONFIG=ROOT/'research_inputs/b7/u09_config.json'
SUPPLEMENT=ROOT/'research_inputs/b7/u09_supplemental_prespec.json'

def validate(data,audit,identity,original,summary,archive):
    rs=data['Candidates'];cal={x['CandidateID']:x['CalendarFreeze'] for x in summary['CalendarFreeze']}
    if data['CandidateCount']!=54 or len(rs)!=54 or data['NoReplacement'] is not True:raise ValueError('54/NoReplacement')
    ids=[r['CandidateID'] for r in rs]
    if len(set(ids))!=54 or ids!=[c for c in identity['CandidateIDs'] if c in cal]:raise ValueError('ordered unique PASS54')
    if data['U08ProducerImplementationSHA']!=PRODUCER_SHA or identity['ImplementationSHA']!=PRODUCER_SHA or data['SourceIdentitySHA256']!=object_hash(identity):raise ValueError('U08 producer identity')
    fs={f['Path']:f for f in archive['Files']}
    if data['SourceArchiveZIP']!=fs['archive.zip'] or data['SourceManifest']!=fs['artifact_manifest.json'] or data['SourceCandidateResultsSHA256']!=fs['candidate_results.json']['SHA256']:raise ValueError('archive identity')
    hs={f['Path']:f['SHA256'] for f in audit['TrustedFiles']};old={r['CandidateID']:r for r in original['Candidates']}
    for r in rs:
        cid=r['CandidateID'];s=Structure.from_id(cid);o=old[cid]
        if r['U08Status']!='PASS_U08' or r['U08ProducerImplementationSHA']!=PRODUCER_SHA or r['Schedule']!=s.definition():raise ValueError('PASS/schedule/producer')
        for k in ('Symbol','PairRank','Schedule','FormalSL','FormalTP','AnchorWeekday','FormalWeekdays','SetName','U06SourceIdentity'):
            if r[k]!=o[k]:raise ValueError('fixed input field')
        for k in ('Direction','EntryMinute','ExitMinute','ExitDayOffset','HoldingMinutes'):
            if r[k]!=s.definition()[k]:raise ValueError('schedule projection')
        if r['CalendarFreeze']!=cal[cid] or any(r[k]!=v for k,v in cal[cid].items()):raise ValueError('CalendarFreeze')
        if r['U07SourceIdentity']!={k:o[k] for k in ('U07Status','U07CandidateSHA256','U07CheckpointSHA256','U07ProducerImplementationSHA','U06SourceIdentity')}:raise ValueError('U07 identity')
        for k,n in [('U08CandidateSHA256','candidate.json'),('U08CheckpointSHA256','checkpoint.json')]:
            if r[k]!=hs[f'jobs/{cid}/{n}']:raise ValueError('U08 candidate/checkpoint')
    return data

def input_config():
    verify_conditions();c=read(CONFIG)
    if c['U08ResultFreezeSHA']!=RESULT_SHA or c['InputSHA256']!=INPUT_SHA or digest(INPUT)!=INPUT_SHA:raise ValueError('U09 input identity')
    if c['SupplementalFreezeSHA']!=SUPPLEMENT_SHA or c['SupplementalPrespecSHA256']!=SUPPLEMENT_HASH or digest(SUPPLEMENT)!=SUPPLEMENT_HASH:raise ValueError('supplement identity')
    for p,h in c['FrozenSources'].items():
        if digest(ROOT/p)!=h:raise ValueError('frozen source hash')
    return c,validate(read(INPUT),read(ROOT/'results/b7/u08/drive_checkpoint_audit.json'),read(ROOT/'results/b7/u08/input_identity.json'),read(ROOT/'research_inputs/b7/u08_selected56_input.json'),read(ROOT/'results/b7/u08/u08_result_summary.json'),read(ROOT/'results/b7/u08/u08_archive_manifest.json'))
