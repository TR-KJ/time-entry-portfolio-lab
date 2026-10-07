"""Explicit Colab-only U07 runner with synchronous per-candidate Drive durability."""
import json,os,shutil,tempfile,zipfile
from pathlib import Path
from collections import Counter
from .stage1_contract import ROOT,CONDITIONS_SHA,Structure,digest,object_hash,verify_conditions
from . import stage1_runtime as shared
from .stage1_input import audit_inputs,load_discovery
from .u07_input import input_config, RESULT_SHA
from .u07_artifacts import identity as make_identity, validate_result, RELEASE
from .u07_execution import Engine,evaluate_candidate
from .u06_finalize_only import read, regular

APPROVAL='CHAT_APPROVED_COLAB_B7_U07_ONLY'
CONFIG=ROOT/'research_inputs/b7/u07_config.json'
INPUT=ROOT/'research_inputs/b7/u07_selected56_input.json'
RELEASE=ROOT/'results/b7/u07_implementation/release_manifest.json'

def save(p,d):shared.save_json(p,d)

def preflight(paths,reviewed_sha):
    if len(reviewed_sha)!=40 or shared.git('rev-parse','HEAD')!=reviewed_sha or shared.git('status','--porcelain'):raise ValueError('reviewed clean checkout')
    shared.git('merge-base','--is-ancestor',RESULT_SHA,reviewed_sha)
    c,d=input_config();shared.release_manifest(RELEASE)
    env=shared.environment()
    if env['NumPy']!='2.3.5' or env['pandas']!='2.2.3':raise ValueError('dependencies')
    tests=shared.run_tests();inputs=audit_inputs(paths)
    from .u07_smoke import run_smoke
    smoke=run_smoke(paths)
    identity=make_identity(reviewed_sha,env)
    if inputs!=identity['M1ExactIdentity']:raise ValueError('exact M1 identity')
    return dict(Status='PASS',Identity=identity,Tests=tests,Smoke=smoke)

def validate_job(folder,identity,record):
    folder=Path(folder)
    if folder.is_symlink() or any((folder/n).is_symlink() for n in ('checkpoint.json','candidate.json')):raise ValueError('symlink job')
    cp=read(folder/'checkpoint.json')
    if cp.get('Status')!='JOB_COMPLETE' or cp.get('Identity')!=identity or cp.get('IdentitySHA256')!=object_hash(identity) or cp.get('CandidateID')!=record['CandidateID']:raise ValueError('job identity/incomplete')
    if cp.get('CandidateSHA256')!=digest(folder/'candidate.json'):raise ValueError('candidate hash')
    d=read(folder/'candidate.json')
    return validate_result(d,record)

def complete_local(folder,identity,record,result):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    save(folder/'candidate.json',result)
    save(folder/'checkpoint.json',dict(Status='JOB_COMPLETE',Identity=identity,IdentitySHA256=object_hash(identity),CandidateID=record['CandidateID'],CandidateSHA256=digest(folder/'candidate.json')))
    return validate_job(folder,identity,record)

def mirror_job(local,drive,identity,record):
    """Synchronous: verify local, copy staging, verify destination, marker last, publish."""
    local,drive=Path(local),Path(drive);validate_job(local,identity,record)
    if drive.exists():raise FileExistsError('Drive job exists')
    drive.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.incomplete-',dir=drive.parent) as tmp:
        stage=Path(tmp)/'job';stage.mkdir()
        shutil.copy2(local/'candidate.json',stage/'candidate.json')
        if digest(stage/'candidate.json')!=digest(local/'candidate.json'):raise ValueError('Drive copy hash')
        shutil.copy2(local/'checkpoint.json',stage/'checkpoint.json')
        validate_job(stage,identity,record)
        save(stage/'DRIVE_COMPLETE.json',dict(Status='DRIVE_JOB_COMPLETE',CheckpointSHA256=digest(stage/'checkpoint.json'),CandidateSHA256=digest(stage/'candidate.json')))
        if drive.exists():raise FileExistsError('Drive job appeared')
        os.rename(stage,drive)

def validate_drive(folder,identity,record):
    folder=Path(folder);m=read(regular(folder/'DRIVE_COMPLETE.json'))
    if m.get('Status')!='DRIVE_JOB_COMPLETE' or m.get('CheckpointSHA256')!=digest(folder/'checkpoint.json') or m.get('CandidateSHA256')!=digest(folder/'candidate.json'):raise ValueError('Drive completion/hash')
    return validate_job(folder,identity,record)

def init_root(root,identity,resume):
    root=Path(root)
    if root.is_symlink() or (root/'identity.json').is_symlink() or (root/'jobs').is_symlink():raise ValueError('symlink root')
    if root.exists():
        if not resume:raise FileExistsError('fresh run root required')
        if read(root/'identity.json')!=identity:raise ValueError('exact resume identity')
    else:
        root.mkdir(parents=True);save(root/'identity.json',identity);(root/'jobs').mkdir()
    allowed=set(identity['CandidateIDs'])
    if any(p.name not in allowed and not p.name.startswith('.incomplete-') for p in (root/'jobs').iterdir()):raise ValueError('extra candidate job')

def finalize(local,drive,identity,records):
    for root in (local,drive):
        init_root(root,identity,True)
    results=[]
    for r in records:
        a=validate_job(Path(local)/'jobs'/r['CandidateID'],identity,r);b=validate_drive(Path(drive)/'jobs'/r['CandidateID'],identity,r)
        if a!=b:raise ValueError('local/Drive results differ')
        results.append(a)
    if len(results)!=56 or len({r['CandidateID'] for r in results})!=56:raise ValueError('56 completed candidates required')
    out=Path(local)/'final';out.mkdir(exist_ok=False)
    save(out/'input_identity.json',identity);save(out/'candidate_results.json',results)
    if (Path(local)/'preflight.json').exists():shutil.copy2(Path(local)/'preflight.json',out/'preflight.json')
    audit=[dict(CandidateID=r['CandidateID'],CheckpointSHA256=digest(Path(drive)/'jobs'/r['CandidateID']/'checkpoint.json')) for r in records]
    save(out/'checkpoint_audit.json',dict(Status='PASS',JobCount=56,Jobs=audit))
    pairs={s:dict(Counter(r['Status'] for r in results if r['Symbol']==s)) for s in sorted({r['Symbol'] for r in records})}
    save(out/'pair_summary.json',pairs)
    review=dict(Status='COMPLETE_U07_ONLY',InputCandidates=56,CompletedJobs=56,Counts=dict(Counter(r['Status'] for r in results)),ExecutionStopsAt='U07_ONLY',NoReplacement=True)
    save(out/'review.json',review)
    save(out/'artifact_manifest.json',shared.make_manifest(out))
    save(out/'COMPLETE.json',dict(Status='COMPLETE_U07_ONLY',ManifestSHA256=digest(out/'artifact_manifest.json'),ReviewSHA256=digest(out/'review.json')))
    return review

def run_formal(paths,reviewed_sha,local,drive,approval=None,resume=False):
    if approval!=APPROVAL:raise PermissionError('U07 dedicated approval required')
    if not Path('/content').is_dir() or not os.environ.get('COLAB_RELEASE_TAG'):raise PermissionError('Colab only')
    local,drive=Path(local),Path(drive)
    if not Path('/content/drive').is_dir() or Path('/content/drive') not in drive.absolute().parents:raise ValueError('mounted Drive checkpoint root required')
    if Path('/content') not in local.resolve().parents or Path('/content/drive') in local.resolve().parents:raise ValueError('local Colab output required')
    if local.resolve()==drive.resolve() or local.resolve() in drive.resolve().parents or drive.resolve() in local.resolve().parents:raise ValueError('separate local/Drive')
    proof=preflight(paths,reviewed_sha);identity=proof['Identity'];_,data=input_config();records=data['Candidates']
    # Validate both existing roots before any new root is created.
    for root in (local,drive):
        if root.exists() and (not resume or read(root/'identity.json')!=identity):raise ValueError('fresh/exact identity required')
    init_root(local,identity,resume);init_root(drive,identity,resume)
    save(local/'preflight.json',proof)
    engine=None;symbol=None
    for r in records:
        l=local/'jobs'/r['CandidateID'];d=drive/'jobs'/r['CandidateID']
        if d.exists():
            validate_drive(d,identity,r)
            if not l.exists():
                with tempfile.TemporaryDirectory(prefix='.incomplete-',dir=l.parent) as tmp:
                    stage=Path(tmp)/'job';shutil.copytree(d,stage);validate_job(stage,identity,r);os.rename(stage,l)
            validate_job(l,identity,r)
        else:
            if not l.exists():
                if symbol!=r['Symbol']:engine=Engine(load_discovery(paths,r['Symbol']),r['Symbol']);symbol=r['Symbol']
                result,_=evaluate_candidate(engine,r)
                complete_local(l,identity,r,result)
            mirror_job(l,d,identity,r)
        # Do not expose intermediate candidate selections.
        save(local/'progress.json',dict(CompletedJobs=records.index(r)+1,ExpectedJobs=56,Status='IN_PROGRESS_NOT_FINAL'))
    return finalize(local,drive,identity,records)

def archive_completed(final,destination):
    final,destination=Path(final),Path(destination)
    c=read(final/'COMPLETE.json')
    if c['Status']!='COMPLETE_U07_ONLY' or digest(final/'artifact_manifest.json')!=c['ManifestSHA256'] or digest(final/'review.json')!=c['ReviewSHA256']:raise ValueError('completion')
    m=read(final/'artifact_manifest.json')
    for x in m['Files']:
        p=final/x['Path']
        if digest(p)!=x['SHA256'] or p.stat().st_size!=x['Bytes']:raise ValueError('artifact hash/size')
    if destination.exists():raise FileExistsError('archive exists')
    destination.parent.mkdir(parents=True,exist_ok=True)
    names=[x['Path'] for x in m['Files']]+['artifact_manifest.json','COMPLETE.json']
    with tempfile.TemporaryDirectory(prefix='.archive-incomplete-',dir=destination.parent) as tmp:
        staging=Path(tmp)/'archive';staging.mkdir()
        for n in names:
            if n!='COMPLETE.json':shutil.copy2(final/n,staging/n)
        with zipfile.ZipFile(staging/'archive.zip','w',zipfile.ZIP_DEFLATED) as z:
            for n in names:z.write(final/n,n)
        with zipfile.ZipFile(staging/'archive.zip') as z:
            import hashlib
            for n in names:
                if hashlib.sha256(z.read(n)).hexdigest()!=digest(final/n):raise ValueError('ZIP member hash')
        for n in names:
            if n!='COMPLETE.json' and digest(final/n)!=digest(staging/n):raise ValueError('archive copy hash')
        shutil.copy2(final/'COMPLETE.json',staging/'COMPLETE.json')
        if digest(final/'COMPLETE.json')!=digest(staging/'COMPLETE.json'):raise ValueError('archive marker')
        if destination.exists():raise FileExistsError('archive appeared')
        os.rename(staging,destination)
    return str(destination)
