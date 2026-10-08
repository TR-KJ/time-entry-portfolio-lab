"""Completed U08 Drive outputs only: no evaluator, input loader or selector imports."""
from pathlib import Path
from collections import Counter
import json,os,re,hashlib
from .stage1_contract import ROOT,CONDITIONS_SHA,digest,object_hash,canonical,verify_conditions
from . import stage1_runtime as shared

from .u08_artifacts import identity as make_identity, validate_result, summaries
from .u08_input import input_config, RESULT_SHA
APPROVAL='CHAT_APPROVED_COLAB_B7_U08_FINALIZE_ONLY'
RELEASE=ROOT/'results/b7/u08_implementation/release_manifest.json'
FILES=('candidate.json','checkpoint.json','DRIVE_COMPLETE.json')

def read(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    def bad(v):raise ValueError('nonfinite JSON value')
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=bad)

def regular(p):
    if p.is_symlink() or not p.is_file():raise ValueError('regular source file required')
    return p

def expected_identity(producer_sha):
    if not re.fullmatch('[0-9a-f]{40}',producer_sha):raise ValueError('explicit reviewed Producer SHA required')
    _,data=input_config()
    expected=make_identity(producer_sha,{})
    del expected['Environment']
    return expected,data['Candidates']

def check_environment(producer,current):
    def version(d):
        v=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',d.get('Python',''))
        if not v:raise ValueError('canonical Python version required')
        return tuple(map(int,v.groups()[:2]))
    if set(producer)!={'Python','NumPy','pandas'} or set(current)!=set(producer):raise ValueError('environment schema')
    if version(producer)!=version(current):raise ValueError('Python major.minor mismatch')
    for k,wanted in [('NumPy','2.3.5'),('pandas','2.2.3')]:
        if producer[k]!=wanted or current[k]!=producer[k]:raise ValueError('exact NumPy/pandas required')

def fresh(source,output):
    source,output=Path(source),Path(output)
    if source.is_symlink() or not source.is_dir():raise ValueError('regular source root')
    if output.exists() or output.is_symlink():raise FileExistsError('fresh output required')
    s,o=source.resolve(),output.resolve()
    if s==o or s in o.parents or o in s.parents:raise ValueError('separate source/output')
    return source,output

def unchanged(source,audit):
    for f in audit['TrustedFiles']:
        if digest(regular(Path(source)/f['Path']))!=f['SHA256']:raise ValueError('source changed')

def audit_source(source,current,producer_sha,progress=None):
    source=Path(source)
    if source.is_symlink() or not source.is_dir():raise ValueError('source root')
    expected,records=expected_identity(producer_sha);identity=read(regular(source/'identity.json'))
    if {k:v for k,v in identity.items() if k!='Environment'}!=expected:raise ValueError('producer identity mismatch')
    check_environment(identity['Environment'],current)
    jr=source/'jobs'
    if jr.is_symlink() or not jr.is_dir():raise ValueError('jobs root')
    entries=list(jr.iterdir());ids=set(expected['CandidateIDs'])
    # Staging directories are not trusted candidates and are never opened.
    completed=[p for p in entries if not (p.name.startswith('.incomplete-') and p.is_dir() and not p.is_symlink())]
    if len(completed)!=56 or {p.name for p in completed}!=ids or any(not p.is_dir() or p.is_symlink() for p in completed):raise ValueError('56 exact completed job directories')
    ih=digest(source/'identity.json')
    if read(source/'identity.json')!=identity:raise ValueError('identity changed')
    files=[dict(Path='identity.json',SHA256=ih)];results=[];jobs=[]
    for n,r in enumerate(records,1):
        folder=jr/r['CandidateID'];hashes={name:digest(regular(folder/name)) for name in FILES}
        cp=read(folder/'checkpoint.json');marker=read(folder/'DRIVE_COMPLETE.json');candidate=read(folder/'candidate.json')
        if cp!=dict(Status='JOB_COMPLETE',Identity=identity,IdentitySHA256=object_hash(identity),CandidateID=r['CandidateID'],CandidateSHA256=hashes['candidate.json']):raise ValueError('checkpoint identity/hash/status')
        if marker!=dict(Status='DRIVE_JOB_COMPLETE',CheckpointSHA256=hashes['checkpoint.json'],CandidateSHA256=hashes['candidate.json']):raise ValueError('Drive marker/hash')
        validate_result(candidate,r)
        for name in FILES:
            if digest(folder/name)!=hashes[name]:raise ValueError('source mutation during audit')
            files.append(dict(Path=f'jobs/{r["CandidateID"]}/{name}',SHA256=hashes[name]))
        results.append(candidate);jobs.append(dict(CandidateID=r['CandidateID'],CheckpointSHA256=hashes['checkpoint.json']))
        if progress:progress(dict(ProcessedJobs=n,ExpectedJobs=56))
    audit=dict(Status='PASS',JobCount=56,ProducerImplementationSHA=producer_sha,ProducerIdentitySHA256=object_hash(identity),TrustedFiles=files,TrustedFilesSHA256=object_hash(files),IgnoredStagingDirectories=len(entries)-len(completed),PartialRootArtifacts='IGNORED_NOT_READ',JobRecomputation=False)
    unchanged(source,audit)
    return identity,audit,results,jobs

def current_preflight(reviewed_sha,producer_sha):
    if reviewed_sha!=producer_sha:raise ValueError('checkout must equal separately reviewed Producer pin')
    if not re.fullmatch('[0-9a-f]{40}',reviewed_sha) or shared.git('rev-parse','HEAD')!=reviewed_sha or shared.git('status','--porcelain'):raise ValueError('exact reviewed clean checkout')
    shared.git('merge-base','--is-ancestor',RESULT_SHA,reviewed_sha)
    expected_identity(producer_sha);shared.release_manifest(RELEASE)
    # Verify frozen implementation-test evidence; do not launch evaluator tests in a recovery run.
    tests=read(ROOT/'results/b7/u08_implementation/test_results.json')
    if tests['Status']!='PASS' or tests['Failed']!=0 or tests['Skipped']!=0:raise ValueError('frozen tests must PASS')
    env=shared.environment()
    return dict(Status='PASS',ProducerImplementationSHA=producer_sha,FinalizerImplementationSHA=reviewed_sha,FinalizerEnvironment=env,ImplementationTests=dict(Status='PASS',Total=tests['Total'],SHA256=digest(ROOT/'results/b7/u08_implementation/test_results.json')),RuntimeEvaluatorTestsExecuted=False)

def _finalize(source,output,preflight,progress=None):
    source,output=fresh(source,output)
    producer_sha=preflight['ProducerImplementationSHA']
    identity,audit,results,jobs=audit_source(source,preflight['FinalizerEnvironment'],producer_sha,progress)
    # No result is written/returned until all56 audits pass.
    output.mkdir(parents=True,exist_ok=False)
    save=shared.save_json
    fi=dict(Mode='FINALIZE_ONLY',JobRecomputation=False,ProducerImplementationSHA=producer_sha,ProducerIdentitySHA256=object_hash(identity),ProducerEnvironment=identity['Environment'],FinalizerImplementationSHA=preflight['FinalizerImplementationSHA'],FinalizerEnvironment=preflight['FinalizerEnvironment'],SourceTrustedFilesSHA256=audit['TrustedFilesSHA256'],Approval=APPROVAL)
    save(output/'finalize_preflight.json',preflight);save(output/'finalize_identity.json',fi)
    save(output/'finalize_environment.json',preflight['FinalizerEnvironment']);save(output/'source_checkpoint_audit.json',audit)
    save(output/'candidate_results.json',results);save(output/'checkpoint_audit.json',dict(Status='PASS',JobCount=56,Jobs=jobs))
    pairs={symbol:dict(Counter(r['Status'] for r in results if r['Symbol']==symbol)) for symbol in sorted({r['Symbol'] for r in results})}
    save(output/'pair_summary.json',pairs)
    for name,data in summaries(results).items():save(output/name,data)
    review=dict(Status='COMPLETE_U08_ONLY',Mode='FINALIZE_ONLY',JobRecomputation=False,InputCandidates=56,CompletedJobs=56,Counts=dict(Counter(r['Status'] for r in results)),ExecutionStopsAt='U08_ONLY',NoReplacement=True,ProducerImplementationSHA=producer_sha,ProducerEnvironment=identity['Environment'],FinalizerImplementationSHA=preflight['FinalizerImplementationSHA'],FinalizerEnvironment=preflight['FinalizerEnvironment'])
    unchanged(source,audit)
    manifest=shared.make_manifest(output)
    rb=(canonical(review)+'\n').encode()
    manifest['Files'].append(dict(Path='review.json',SHA256=hashlib.sha256(rb).hexdigest(),Bytes=len(rb)));manifest['Files'].sort(key=lambda x:x['Path'])
    save(output/'artifact_manifest.json',manifest);save(output/'review.json',review)
    save(output/'COMPLETE.json',dict(Status='COMPLETE_U08_ONLY',ManifestSHA256=digest(output/'artifact_manifest.json'),ReviewSHA256=digest(output/'review.json')))
    return review

def finalize_from_completed_jobs(source,output,reviewed_sha,producer_sha,approval=None,progress=None):
    if approval!=APPROVAL:raise PermissionError('dedicated U08 Finalize-Only approval required')
    if not Path('/content').is_dir() or not os.environ.get('COLAB_RELEASE_TAG'):raise PermissionError('Colab only')
    source,output=fresh(source,output)
    if Path('/content/drive') not in source.resolve().parents:raise ValueError('Drive checkpoint source required')
    if Path('/content') not in output.resolve().parents or Path('/content/drive') in output.resolve().parents:raise ValueError('fresh local Colab output required')
    proof=current_preflight(reviewed_sha,producer_sha)
    return _finalize(source,output,proof,progress)
