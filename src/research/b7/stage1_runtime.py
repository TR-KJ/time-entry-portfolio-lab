"""Fail-closed Colab preflight, exact job checkpoints, and complete-only publication."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
import numpy as np
import pandas as pd
from .stage1_contract import ROOT, PRESPEC, FROZEN, CONDITIONS_SHA, SL, SPREAD, PIPS, jobs, Structure, canonical, object_hash, digest, verify_conditions
from .stage1_input import MANIFEST, audit_inputs, load_discovery, manifest_rows
from .stage1_smoke import run_smoke
from .stage1 import Engine, record_result
from .stage1_family import plateau, families

EXPECTED_STRUCTURES=81504
TOTAL_STRUCTURES=7335360
TOTAL_VARIANTS=44012160
APPROVAL='CHAT_APPROVED_COLAB_STAGE1_ONLY'


def save_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(canonical(obj)+'\n');os.replace(temporary,path)

def environment():return dict(Python=platform.python_version(),NumPy=np.__version__,pandas=pd.__version__)

def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()

def release_manifest(path=None):
    path=ROOT/'results/b7/stage1_implementation/release_manifest.json' if path is None else Path(path)
    doc=json.loads(path.read_text())
    for item in doc['Files']:
        if digest(ROOT/item['Path'])!=item['SHA256']:raise ValueError('release file hash mismatch')
    return doc

def make_manifest(root,exclude=()):
    root=Path(root)
    return {'Files':[dict(Path=p.relative_to(root).as_posix(),SHA256=digest(p),Bytes=p.stat().st_size)
                     for p in sorted(root.rglob('*')) if p.is_file() and p.relative_to(root).as_posix() not in exclude]}

def make_identity(implementation_sha,input_audit):
    return dict(ImplementationCommitSHA=implementation_sha,ConditionsFreezeSHA=CONDITIONS_SHA,
        FullPrespecSHA256=digest(ROOT/'research_inputs/b7/full_research_prespec.json'),
        Stage1PrespecSHA256=digest(ROOT/'research_inputs/b7/stage1_prespec.json'),
        RuntimeConfigSHA256=digest(ROOT/'research_inputs/b7/stage1_runtime_config.json'),
        ManifestSHA256=digest(ROOT/MANIFEST),M1ExactIdentity=input_audit,
        Spreads=SPREAD,PipSizes=PIPS,OfficialSLGrid=SL,
        ExecutionConvention=dict(PRESPEC['InheritedEnvironmentAndExecution']['FrozenStage0Protocol']),
        DiscoveryBounds=['2020-01-01','2024-01-01'],Environment=environment(),
        GateConfig={k:PRESPEC[k] for k in ('U01','U02','U05')},Ranking=PRESPEC['PairRanking'],
        Plateau=PRESPEC['U03'],Family=PRESPEC['U04'],JobDefinitions=[j.job_id for j in jobs()])

def run_tests():
    env=dict(os.environ,PYTHONPATH=str(ROOT/'src/research'),PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_b7*.py','-q'],cwd=ROOT,env=env,capture_output=True,text=True)
    if result.returncode:raise RuntimeError('preflight tests failed: '+result.stderr)
    return dict(Status='PASS',Output=result.stderr+result.stdout)

def preflight(paths,implementation_sha,output):
    """Always perform barriers; previously saved PASS booleans cannot skip verification."""
    verify_conditions()
    if len(implementation_sha)!=40 or git('rev-parse','HEAD')!=implementation_sha:raise ValueError('reviewed implementation SHA required')
    if git('status','--porcelain'):raise ValueError('dirty implementation checkout')
    if git('merge-base','--is-ancestor',CONDITIONS_SHA,implementation_sha)!='':raise ValueError('condition ancestry')
    release_manifest()
    env=environment()
    if env['NumPy']!='2.3.5' or env['pandas']!='2.2.3':raise ValueError('pin NumPy/pandas; restart runtime')
    tests=run_tests();audit=audit_inputs(paths);smoke=run_smoke(paths)
    identity=make_identity(implementation_sha,audit)
    proof=dict(Status='PREFLIGHT_PASS',Identity=identity,IdentitySHA256=object_hash(identity),Tests=tests,Smoke=smoke,
               PythonExactReference=env['Python']=='3.12.14',PythonDifferenceRequiresExactReplay=True)
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    save_json(out/'preflight.json',proof)
    return proof

def checkpoint_identity(identity,job):return dict(RunIdentity=identity,JobID=job.job_id,JobDefinition=dict(Symbol=job.symbol,Direction=job.direction,Weekday=job.weekday,Entries=288,Holdings=283))

def validate_checkpoint(folder,identity,job):
    folder=Path(folder);meta=json.loads((folder/'checkpoint.json').read_text())
    wanted=checkpoint_identity(identity,job)
    if meta['Identity']!=wanted or meta['IdentitySHA256']!=object_hash(wanted):raise ValueError('resume identity mismatch')
    if meta['Status']!='JOB_COMPLETE':raise ValueError('incomplete checkpoint')
    for filename,value in meta['Hashes'].items():
        if filename not in ('summary.json','formal_pass.jsonl','point_map.npz'):raise ValueError('checkpoint output schema')
        if digest(folder/filename)!=value:raise ValueError('checkpoint corruption')
    if set(meta['Hashes'])!={'summary.json','formal_pass.jsonl','point_map.npz'}:raise ValueError('missing checkpoint artifact')
    summary=json.loads((folder/'summary.json').read_text())
    if summary['JobID']!=job.job_id or summary['ExpectedStructures']!=EXPECTED_STRUCTURES or summary['EvaluatedStructures']!=EXPECTED_STRUCTURES or summary['EvaluatedVariants']!=EXPECTED_STRUCTURES*6:raise ValueError('incomplete job count')
    if summary['RuntimeIdentitySHA256']!=object_hash(identity) or summary['Errors']!=0:raise ValueError('job identity/error')
    with np.load(folder/'point_map.npz',allow_pickle=False) as points:
        if set(points.files)!={'avg','formal','valid'} or any(points[k].shape!=(288,283) for k in points.files):raise ValueError('point map dimensions')
        if int(np.count_nonzero(points['formal']))!=summary['FormalPointPassCount']:raise ValueError('point formal count mismatch')
        if not np.isfinite(points['avg'][points['formal']]).all():raise ValueError('undefined formal point metric')
    return summary

def evaluate_job(engine,job,folder,identity):
    """Exhaustive fixed job. Caller supplies authorized/preflight-checked runtime."""
    if engine.symbol!=job.symbol:raise ValueError('job symbol')
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    avg=np.full((288,283),np.nan);formal=np.zeros((288,283),dtype=bool);valid=np.ones((288,283),dtype=bool)
    summary=dict(JobID=job.job_id,Symbol=job.symbol,Direction=job.direction,Weekday=job.weekday,
        ExpectedStructures=EXPECTED_STRUCTURES,EvaluatedStructures=0,EvaluatedVariants=0,
        PurePassCount=0,SLRobustPassCount=0,FormalPointPassCount=0,Errors=0,MissingDiagnostics={},
        RuntimeIdentitySHA256=object_hash(identity))
    with (folder/'formal_pass.jsonl').open('w') as sink:
        for ei,entry in enumerate(range(0,1440,5)):
            batch=engine.prepare_job_entry(job,entry)
            for hi,holding in enumerate(range(30,1441,5)):
                s=Structure(job.symbol,job.direction,job.weekday,entry,holding)
                result=batch.evaluate(holding,s.key)
                record=record_result(s,result)
                if record['PureMetrics']['AvgPips'] is not None:avg[ei,hi]=record['PureMetrics']['AvgPips']
                formal[ei,hi]=record['FormalPASS']
                summary['EvaluatedStructures']+=1;summary['EvaluatedVariants']+=6
                for field,count in [('PurePASS','PurePassCount'),('SLRobustnessPASS','SLRobustPassCount'),('FormalPASS','FormalPointPassCount')]:summary[count]+=int(record[field])
                for key,count in result['Missing'].items():summary['MissingDiagnostics'][key]=summary['MissingDiagnostics'].get(key,0)+count
                if record['FormalPASS']:sink.write(canonical(record)+'\n')
    np.savez_compressed(folder/'point_map.npz',avg=avg,formal=formal,valid=valid)
    save_json(folder/'summary.json',summary)
    ci=checkpoint_identity(identity,job)
    save_json(folder/'checkpoint.json',dict(Status='JOB_COMPLETE',Identity=ci,IdentitySHA256=object_hash(ci),
        Hashes={name:digest(folder/name) for name in ('summary.json','formal_pass.jsonl','point_map.npz')}))
    return validate_checkpoint(folder,identity,job)

def validate_all_jobs(root,identity):
    directory=Path(root)/'jobs';expected={j.job_id for j in jobs()}
    found={p.name for p in directory.iterdir() if p.is_dir()}
    if found!=expected:raise ValueError('missing/extra/duplicate job directory')
    summaries=[validate_checkpoint(directory/j.job_id,identity,j) for j in jobs()]
    if len({s['JobID'] for s in summaries})!=90:raise ValueError('duplicate job')
    if sum(s['EvaluatedStructures'] for s in summaries)!=TOTAL_STRUCTURES or sum(s['EvaluatedVariants'] for s in summaries)!=TOTAL_VARIANTS:raise ValueError('total count')
    return summaries

def finalize(root,identity):
    """No selection until all90 exact jobs exist. FAIL/empty pairs are never refilled."""
    root=Path(root);summaries=validate_all_jobs(root,identity)
    selections=[];family_count=0
    diagnostics=root/'plateau_diagnostics.jsonl';family_path=root/'family_suppression.jsonl'
    with diagnostics.open('w') as diag, family_path.open('w') as famout:
        for symbol in sorted(SL):
            eligible=[]
            for job in (j for j in jobs() if j.symbol==symbol):
                folder=root/'jobs'/job.job_id
                with np.load(folder/'point_map.npz',allow_pickle=False) as z:
                    def lookup(s):
                        ei,hi=s.entry//5,(s.holding-30)//5
                        value=float(z['avg'][ei,hi])
                        return dict(ScheduleValid=bool(z['valid'][ei,hi]),FormalPASS=bool(z['formal'][ei,hi]),AvgPips=None if np.isnan(value) else value)
                    seen=set()
                    with (folder/'formal_pass.jsonl').open() as source:
                        for line in source:
                            r=json.loads(line);s=Structure.from_id(r['CandidateID'])
                            if r['CandidateID'] in seen:raise ValueError('duplicate formal structure')
                            seen.add(r['CandidateID'])
                            if (s.symbol,s.direction,s.weekday)!=(job.symbol,job.direction,job.weekday):raise ValueError('wrong job record')
                            if not lookup(s)['FormalPASS']:raise ValueError('point map inconsistency')
                            p=plateau(s,lookup);diag.write(canonical(p)+'\n')
                            if p['PlateauPASS']:r['PlateauPASS']=True;eligible.append(r)
                    summary=json.loads((folder/'summary.json').read_text())
                    if len(seen)!=summary['FormalPointPassCount']:raise ValueError('formal count inconsistency')
            for family in families(eligible):
                family['Symbol']=symbol;famout.write(canonical(family)+'\n');family_count+=1
                if family['Top8']:selections.append(family)
    save_json(root/'selected_top8.json',selections)
    review=dict(Status='COMPLETE_STAGE1_ONLY',Jobs=90,EvaluatedStructures=TOTAL_STRUCTURES,EvaluatedVariants=TOTAL_VARIANTS,
        IdentitySHA256=object_hash(identity),RankingComplete=True,PlateauComplete=True,FamilyComplete=True,Top8Complete=True,
        Families=family_count,SelectedCount=len(selections),ExecutionStopsAt='STAGE1_ONLY')
    save_json(root/'review.json',review)
    # A separate complete marker binds the completed artifact manifest; neither is self-hashed.
    save_json(root/'progress.json',dict(CompletedJobs=90,ExpectedJobs=90,Errors=0,Status='ALL_PHASES_FINISHED'))
    manifest=make_manifest(root,exclude=('artifact_manifest.json','COMPLETE.json'))
    save_json(root/'artifact_manifest.json',manifest)
    save_json(root/'COMPLETE.json',dict(Status='COMPLETE_STAGE1_ONLY',ManifestSHA256=digest(root/'artifact_manifest.json'),ReviewSHA256=digest(root/'review.json')))
    return review

def run_formal(paths,implementation_sha,output,approval=None,resume=False,progress=None):
    if approval!=APPROVAL:raise PermissionError('Separate Chat approval required; formal sweep not authorized by implementation')
    if not Path('/content').is_dir() or not os.environ.get('COLAB_RELEASE_TAG'):raise PermissionError('formal sweep is Colab-only')
    output=Path(output)
    if output.exists() and not resume:raise FileExistsError('new output folder required')
    if (output/'COMPLETE.json').exists():raise FileExistsError('completed run immutable')
    # Every invocation repeats all barriers, including resume.
    proof=preflight(paths,implementation_sha,output);identity=proof['Identity']
    identity_file=output/'identity.json'
    if identity_file.exists() and json.loads(identity_file.read_text())!=identity:raise ValueError('run resume identity mismatch')
    save_json(identity_file,identity);save_json(output/'effective_config.json',dict(FullResearchPrespec=PRESPEC,Runtime=json.loads((ROOT/'research_inputs/b7/stage1_runtime_config.json').read_text()),RuntimeExecutionAuthorization=dict(Approval=approval,Stage1ExecutionAuthorized=True,Environment='GOOGLE_COLAB')))
    save_json(output/'environment.json',environment());save_json(output/'input_audit.json',proof['Identity']['M1ExactIdentity'])
    job_root=output/'jobs';job_root.mkdir(exist_ok=True)
    expected={j.job_id for j in jobs()}
    if any(p.name not in expected for p in job_root.iterdir()):raise ValueError('unknown/incomplete job folder; inspect instead of auto-reuse')
    completed=0
    for symbol in sorted(SL):
        engine=None
        for job in (j for j in jobs() if j.symbol==symbol):
            folder=job_root/job.job_id
            if folder.exists():
                if not resume:raise FileExistsError('job exists')
                validate_checkpoint(folder,identity,job)
            else:
                if engine is None:engine=Engine(load_discovery(paths,symbol),symbol)

                with tempfile.TemporaryDirectory(prefix='b7-uncheckpointed-',dir=output.parent) as scratch:
                    pending=Path(scratch)/job.job_id
                    evaluate_job(engine,job,pending,identity)
                    os.replace(pending,folder)
            completed+=1
            status=dict(CompletedJobs=completed,ExpectedJobs=90,Errors=0,Status='IN_PROGRESS_NOT_CANDIDATES')
            save_json(output/'progress.json',status)
            if progress:progress(status)  # no IDs, times, rankings, candidate metrics
        del engine
    return finalize(output,identity)

def archive_completed(output,destination):
    output,destination=Path(output),Path(destination)
    complete=json.loads((output/'COMPLETE.json').read_text())
    if complete['Status']!='COMPLETE_STAGE1_ONLY' or digest(output/'artifact_manifest.json')!=complete['ManifestSHA256']:raise ValueError('not complete')
    manifest=json.loads((output/'artifact_manifest.json').read_text())
    for f in manifest['Files']:
        if digest(output/f['Path'])!=f['SHA256']:raise ValueError('output corruption')
    if destination.exists():raise FileExistsError('Drive overwrite forbidden')
    destination.mkdir(parents=True,exist_ok=False)
    # Copy only manifested artifacts and completion markers; never raw inputs/unlisted files.
    names=[f['Path'] for f in manifest['Files']]+['artifact_manifest.json','COMPLETE.json']
    for name in names:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(output/name,target)
    with zipfile.ZipFile(destination/'archive.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in names:z.write(output/name,name)
    return str(destination)

def new_run_id():
    # Random run identifier is permitted; CandidateIDs never use randomness.
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]


def implementation_manifest():
    """Hash explicit implementation release paths; never inspect data-root or .git."""
    files=set()
    for folder,pattern in [('src/research/b7','*.py'),('tests','test_b7*.py'),('docs/b7','*.md'),('research_inputs/b7','*'),('results/b7/stage1_implementation','*')]:
        files.update(p for p in (ROOT/folder).rglob(pattern) if p.is_file())
    files.add(ROOT/'notebooks/b7_stage1_discovery.ipynb')
    files.add(ROOT/'src/research/daily_stop_baseline_revalidation.py')
    files.add(ROOT/'results/b7/stage0/artifact_manifest.json')
    files.add(ROOT/'results/b7/stage0/run_status.json')
    files.discard(ROOT/'results/b7/stage1_implementation/release_manifest.json')
    return dict(Scope='B7_STAGE1_IMPLEMENTATION_ONLY',SelfExcluded=True,ConditionsFreezeSHA=CONDITIONS_SHA,
        Files=[dict(Path=p.relative_to(ROOT).as_posix(),SHA256=digest(p),Bytes=p.stat().st_size) for p in sorted(files)])
