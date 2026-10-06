"""Extract only frozen Stage1 representatives, with exact source-file bindings."""
import json
from pathlib import Path
from .stage1_contract import ROOT,Structure,SL,SYMBOLS,jobs,digest,object_hash
from .stage1_metrics import point_result
from .stage1_runtime import checkpoint_identity
from .stage1_finalize_only import expected_original_identity

RESULT_SHA='72b8244c69d165fae4a3c806a1cdb5d6fcfa1a38'
SELECTED_SHA='b77baa21fc23da8ddf9ce6ad00bb863384d7b88b9c0b506d49b63bbc04b9370b'
SELECTED_BYTES=12600180
AUDIT_SHA='3db47c30905893b8af730a3b18c01e90aeb15b5f508fffaa439cbc380bf909b2'

def selected_records(selected):
    if len(selected)!=72:raise ValueError('72 representatives required')
    ids=[f['Representative'] for f in selected]
    if len(set(ids))!=72:raise ValueError('duplicate representative')
    if {f['Symbol'] for f in selected}!=set(SYMBOLS):raise ValueError('nine pairs')
    for symbol in SYMBOLS:
        if sorted(f['PairRank'] for f in selected if f['Symbol']==symbol)!=list(range(1,9)):raise ValueError('pair ranks')
    records={}
    for f in selected:
        s=Structure.from_id(f['Representative'])
        if f['Top8'] is not True or f['Symbol']!=s.symbol or f['AnchorWeekday']!=s.weekday:raise ValueError('representative schema')
        members=[m for m in f['Members'] if m['Definition']['CandidateID']==s.candidate_id]
        if len(members)!=1 or members[0]['Definition']!=s.definition():raise ValueError('representative member')
        records[s.candidate_id]=(f,members[0])
    return records

def extract(selected_path,checkpoint_root):
    p=Path(selected_path);root=Path(checkpoint_root)
    if p.stat().st_size!=SELECTED_BYTES or digest(p)!=SELECTED_SHA:raise ValueError('selected identity')
    selected=selected_records(json.loads(p.read_text()))
    ap=ROOT/'results/b7/stage1/source_checkpoint_audit.json'
    if digest(ap)!=AUDIT_SHA:raise ValueError('frozen source audit hash')
    audit=json.loads(ap.read_text());trusted={x['Path']:x['SHA256'] for x in audit['TrustedFiles']}
    expected={'identity.json'}|{f'jobs/{j.job_id}/{n}' for j in jobs() for n in ('checkpoint.json','summary.json','formal_pass.jsonl','point_map.npz')}
    if len(audit['TrustedFiles'])!=361 or set(trusted)!=expected or object_hash(audit['TrustedFiles'])!=audit['SourceTrustedFilesSHA256']:raise ValueError('source hash list')
    def read(rel):
        path=root/rel
        if path.is_symlink() or digest(path)!=trusted[rel]:raise ValueError('source file hash '+rel)
        return path
    identity=json.loads(read('identity.json').read_text())
    if identity!=expected_original_identity() or object_hash(identity)!=audit['OriginalIdentitySHA256']:raise ValueError('original identity')
    groups={}
    for cid in selected:
        s=Structure.from_id(cid);jid=next(j.job_id for j in jobs() if (j.symbol,j.direction,j.weekday)==(s.symbol,s.direction,s.weekday))
        groups.setdefault(jid,set()).add(cid)
    out=[]
    for jid,wanted in sorted(groups.items()):
        base='jobs/'+jid+'/';cp=json.loads(read(base+'checkpoint.json').read_text());summary=json.loads(read(base+'summary.json').read_text())
        wanted_identity=checkpoint_identity(identity,next(j for j in jobs() if j.job_id==jid))
        if cp['Status']!='JOB_COMPLETE' or cp['Identity']!=wanted_identity or cp['IdentitySHA256']!=object_hash(wanted_identity):raise ValueError('checkpoint identity')
        for name in ('summary.json','formal_pass.jsonl','point_map.npz'):
            if cp['Hashes'][name]!=trusted[base+name]:raise ValueError('checkpoint binding')
        if summary['Errors']!=0 or summary['EvaluatedStructures']!=81504 or summary['EvaluatedVariants']!=489024:raise ValueError('job summary')
        found={};path=read(base+'formal_pass.jsonl')
        with path.open() as f:
            for line in f:
                r=json.loads(line)
                if r['CandidateID'] in wanted:
                    if r['CandidateID'] in found:raise ValueError('duplicate source record')
                    found[r['CandidateID']]=r
        if set(found)!=wanted:raise ValueError('representative missing in checkpoint')
        if digest(path)!=trusted[base+'formal_pass.jsonl']:raise ValueError('source mutation')
        for cid in sorted(wanted):
            r=found[cid];family,member=selected[cid];s=Structure.from_id(cid)
            if any(r.get(k)!=v for k,v in s.definition().items()) or r['PureMetrics']!=member['PureMetrics']:raise ValueError('Pure/schedule mismatch')
            if [x['SLPips'] for x in r['FiveSLMetrics']]!=SL[s.symbol]:raise ValueError('official five-SL mismatch')
            gates=point_result(r['PureMetrics'],[x['Metrics'] for x in r['FiveSLMetrics']])
            if any(r.get(k)!=v for k,v in gates.items()) or not gates['FormalPASS']:raise ValueError('five-SL Gate mismatch')
            out.append(dict(CandidateID=cid,Symbol=s.symbol,PairRank=family['PairRank'],Schedule=s.definition(),PureMetrics=r['PureMetrics'],FiveSLMetrics=[dict(x,U02PASS=passed) for x,passed in zip(r['FiveSLMetrics'],gates['SLPASS'])],PassingSLCount=gates['PassingSLCount'],SourceFiles={base+n:trusted[base+n] for n in ('checkpoint.json','summary.json','formal_pass.jsonl','point_map.npz')}))
    if len(out)!=72 or digest(p)!=SELECTED_SHA:raise ValueError('final selected audit')
    return dict(Stage1ResultFreezeSHA=RESULT_SHA,SelectedSHA256=SELECTED_SHA,SelectedBytes=SELECTED_BYTES,SourceAuditSHA256=AUDIT_SHA,OriginalIdentitySHA256=object_hash(identity),SourceTrustedFilesSHA256=audit['SourceTrustedFilesSHA256'],Candidates=sorted(out,key=lambda r:(r['Symbol'],r['PairRank'])))
