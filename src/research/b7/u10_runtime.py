"""Explicit Colab-only U10 runner with synchronous per-candidate Drive durability."""
import json,os,shutil,tempfile,zipfile
from pathlib import Path
from collections import Counter
from .stage1_contract import ROOT,CONDITIONS_SHA,Structure,digest,object_hash,verify_conditions
from . import stage1_runtime as shared
from .stage1_input import audit_inputs,load_discovery
from .u10_input import input_config, RESULT_SHA, SUPPLEMENT_SHA
from .u10_artifacts import identity as make_identity, validate_result, RELEASE, summaries
from .u10_execution import Engine,evaluate_candidate
from .u06_finalize_only import read, regular

APPROVAL='CHAT_APPROVED_COLAB_B7_U10_ONLY'
CONFIG=ROOT/'research_inputs/b7/u10_config.json'
INPUT=ROOT/'research_inputs/b7/u10_selected54_input.json'
RELEASE=ROOT/'results/b7/u10_implementation/release_manifest.json'

def save(p,d):shared.save_json(p,d)

def preflight(paths,reviewed_sha,completed_only=False):
    if len(reviewed_sha)!=40 or shared.git('rev-parse','HEAD')!=reviewed_sha or shared.git('status','--porcelain'):raise ValueError('reviewed clean checkout')
    shared.git('merge-base','--is-ancestor',RESULT_SHA,reviewed_sha)
    shared.git('merge-base','--is-ancestor',SUPPLEMENT_SHA,reviewed_sha)
    c,d=input_config();shared.release_manifest(RELEASE)
    from .u10_calendar import audit_calendar
    audit_calendar()
    env=shared.environment()
    if env['NumPy']!='2.3.5' or env['pandas']!='2.2.3':raise ValueError('dependencies')
    if completed_only:
        tests=read(ROOT/'results/b7/u10_implementation/test_results.json')
        frozen_smoke=read(ROOT/'results/b7/u10_implementation/smoke_results.json')
        if tests['Status']!='PASS' or frozen_smoke['Status']!='PASS':raise ValueError('frozen preflight evidence')
        inputs=make_identity(reviewed_sha,env)['M1ExactIdentity']
    else:
        tests=shared.run_tests();inputs=audit_inputs(paths)
    from .u10_smoke import run_smoke
    smoke=dict(Status='NOT_RERUN_COMPLETED_CHECKPOINT',JobRecomputation=False) if completed_only else run_smoke(paths)
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
        if digest(stage/'checkpoint.json')!=digest(local/'checkpoint.json'):raise ValueError('Drive checkpoint copy hash')
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
    if len(results)!=54 or len({r['CandidateID'] for r in results})!=54:raise ValueError('54 completed candidates required')
    out=Path(local)/'final';out.mkdir(exist_ok=False)
    save(out/'input_identity.json',identity);save(out/'candidate_results.json',results)
    if (Path(local)/'preflight.json').exists():shutil.copy2(Path(local)/'preflight.json',out/'preflight.json')
    audit=[dict(CandidateID=r['CandidateID'],CheckpointSHA256=digest(Path(drive)/'jobs'/r['CandidateID']/'checkpoint.json')) for r in records]
    save(out/'checkpoint_audit.json',dict(Status='PASS',JobCount=54,Jobs=audit))
    pairs={s:dict(Counter(r['Status'] for r in results if r['Symbol']==s)) for s in sorted({r['Symbol'] for r in records})}
    save(out/'pair_summary.json',pairs)
    for name,data in summaries(results).items():save(out/name,data)
    review=dict(Status='COMPLETE_U10_ONLY',InputCandidates=54,CompletedJobs=54,Counts=dict(Counter(r['Status'] for r in results)),ExecutionStopsAt='U10_ONLY',NoReplacement=True)
    save(out/'review.json',review)
    save(out/'artifact_manifest.json',shared.make_manifest(out))
    save(out/'COMPLETE.json',dict(Status='COMPLETE_U10_ONLY',ManifestSHA256=digest(out/'artifact_manifest.json'),ReviewSHA256=digest(out/'review.json')))
    return review

def run_formal(paths,reviewed_sha,local,drive,approval=None,resume=False):
    if approval!=APPROVAL:raise PermissionError('U10 dedicated approval required')
    if not Path('/content').is_dir() or not os.environ.get('COLAB_RELEASE_TAG'):raise PermissionError('Colab only')
    local,drive=Path(local),Path(drive)
    if not Path('/content/drive').is_dir() or Path('/content/drive') not in drive.resolve().parents:raise ValueError('mounted Drive checkpoint root required')
    if Path('/content') not in local.resolve().parents or Path('/content/drive') in local.resolve().parents:raise ValueError('local Colab output required')
    if local.resolve()==drive.resolve() or local.resolve() in drive.resolve().parents or drive.resolve() in local.resolve().parents:raise ValueError('separate local/Drive')
    _,data=input_config();records=data['Candidates']
    expected=make_identity(reviewed_sha,shared.environment())
    completed=False
    if resume and drive.exists():
        if read(drive/'identity.json')!=expected:raise ValueError('exact resume identity')
        init_root(drive,expected,True)
        completed=all((drive/'jobs'/r['CandidateID']).exists() for r in records)
        for r in records:
            d=drive/'jobs'/r['CandidateID']
            if d.exists():validate_drive(d,expected,r)
    proof=preflight(paths,reviewed_sha,completed_only=completed);identity=proof['Identity']
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
        save(local/'progress.json',dict(CompletedJobs=records.index(r)+1,ExpectedJobs=54,Status='IN_PROGRESS_NOT_FINAL'))
    return finalize(local,drive,identity,records)

def archive_completed(final,destination):
    final,destination=Path(final),Path(destination)
    c=read(final/'COMPLETE.json')
    if c['Status']!='COMPLETE_U10_ONLY' or digest(final/'artifact_manifest.json')!=c['ManifestSHA256'] or digest(final/'review.json')!=c['ReviewSHA256']:raise ValueError('completion')
    m=read(final/'artifact_manifest.json')
    allowed={'input_identity.json','preflight.json','candidate_results.json','checkpoint_audit.json','pair_summary.json','status_summary.json','event_summary.json','mode_summary.json','review.json','finalize_preflight.json','finalize_identity.json','finalize_environment.json','source_checkpoint_audit.json'}
    listed=[x['Path'] for x in m['Files']]
    if len(listed)!=len(set(listed)) or not set(listed)<=allowed:raise ValueError('archive artifact inventory; no raw M1')
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
            if z.namelist()!=names or z.testzip() is not None:raise ValueError('ZIP inventory/CRC')
            for n in names:
                if z.getinfo(n).file_size!=(final/n).stat().st_size or hashlib.sha256(z.read(n)).hexdigest()!=digest(final/n):raise ValueError('ZIP member hash')
        for n in names:
            if n!='COMPLETE.json' and digest(final/n)!=digest(staging/n):raise ValueError('archive copy hash')
        shutil.copy2(final/'COMPLETE.json',staging/'COMPLETE.json')
        if digest(final/'COMPLETE.json')!=digest(staging/'COMPLETE.json'):raise ValueError('archive marker')
        if destination.exists():raise FileExistsError('archive appeared')
        os.rename(staging,destination)
    return str(destination)
