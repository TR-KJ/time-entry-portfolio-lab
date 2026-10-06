"""Read-only completed-job finalization. Never creates/recalculates job outputs."""
from collections import defaultdict
from itertools import product
from pathlib import Path
import json
import os
import re
import shutil
import tempfile
import numpy as np
from .stage1_contract import ROOT, FROZEN, CONDITIONS_SHA, PRESPEC, Structure, jobs, canonical, object_hash, digest, verify_conditions
from .stage1_family import plateau, near, _bucket
from . import stage1_runtime as runtime

ORIGINAL_SHA = 'abe588cf14c225f1cc8f9f991700fbe815618cc2'
APPROVAL = 'CHAT_APPROVED_COLAB_STAGE1_FINALIZE_ONLY'
CONFIG = 'research_inputs/b7/stage1_finalize_only_config.json'
RELEASE = 'results/b7/stage1_finalize_only/release_manifest.json'
JOB_FILES = ('checkpoint.json','summary.json','formal_pass.jsonl','point_map.npz')


def _read(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    def bad(v):raise ValueError('nonfinite JSON token')
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,parse_constant=bad)


def expected_original_identity():
    """Bind the explicitly supported producer, not an arbitrary stored identity."""
    verify_conditions()
    cfg=_read(ROOT/CONFIG)
    expected=cfg['OriginalIdentity']
    if expected['ImplementationCommitSHA']!=ORIGINAL_SHA or expected['ConditionsFreezeSHA']!=CONDITIONS_SHA:
        raise ValueError('unsupported original producer')
    # These are frozen repository metadata reads, never M1 file reads.
    checks={'FullPrespecSHA256':'research_inputs/b7/full_research_prespec.json',
            'Stage1PrespecSHA256':'research_inputs/b7/stage1_prespec.json',
            'RuntimeConfigSHA256':'research_inputs/b7/stage1_runtime_config.json',
            'ManifestSHA256':'research_inputs/b7/expected_m1_manifest.csv'}
    for key,path in checks.items():
        if expected[key]!=digest(ROOT/path):raise ValueError('frozen original config hash mismatch')
    return expected


def check_environment(current,original):
    version=re.fullmatch(r'(\d+)\.(\d+)\.(\d+)',current.get('Python',''))
    if version is None or tuple(map(int,version.groups()[:2]))!=(3,13):raise ValueError('Finalize-Only requires Python3.13 patch series')
    if original!={'Python':'3.13.15','NumPy':'2.3.5','pandas':'2.2.3'}:raise ValueError('original environment mismatch')
    if current.get('NumPy')!='2.3.5' or current.get('pandas')!='2.2.3':raise ValueError('NumPy/pandas exact match required')


def _regular(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('required regular source file missing/symlink')
    return path


def _fresh(source,output):
    source,output=Path(source).resolve(),Path(output).absolute()
    # Disallow source/output ancestor relationships, including an output symlink.
    if output.exists() or output.is_symlink():raise FileExistsError('fresh output directory required')
    resolved=output.resolve()
    if source==resolved or source in resolved.parents or resolved in source.parents:raise ValueError('source/output must be separate')
    return source,output


def _point_arrays(path):
    with np.load(path,allow_pickle=False) as z:
        if set(z.files)!={'avg','formal','valid'}:raise ValueError('point-map keys')
        a={k:z[k].copy() for k in z.files}
    if any(x.shape!=(288,283) for x in a.values()):raise ValueError('point-map shape')
    if a['formal'].dtype!=np.dtype(bool) or a['valid'].dtype!=np.dtype(bool) or a['avg'].dtype!=np.dtype('float64'):raise ValueError('point-map dtypes')
    if np.isinf(a['avg']).any() or np.any(a['formal'] & ~a['valid']):raise ValueError('invalid point map')
    return a


def _records(folder,job,points):
    seen=set();records=[]
    with (folder/'formal_pass.jsonl').open() as f:
        for line in f:
            r=json.loads(line);s=Structure.from_id(r['CandidateID'])
            if s.candidate_id in seen:raise ValueError('duplicate formal CandidateID')
            if (s.symbol,s.direction,s.weekday)!=(job.symbol,job.direction,job.weekday):raise ValueError('formal record job mismatch')
            if any(r.get(k)!=v for k,v in s.definition().items()):raise ValueError('fixed structure/key mismatch')
            ei,hi=s.entry//5,(s.holding-30)//5
            if r.get('FormalPASS') is not True or not points['formal'][ei,hi]:raise ValueError('stored formal status inconsistent')
            if r['PureMetrics']['AvgPips']!=float(points['avg'][ei,hi]):raise ValueError('stored point AvgPips mismatch')
            # Structural validation only; never re-evaluate U01/U02 or trades.
            if r['PureMetrics']['PFState']!='FINITE':raise ValueError('nonfinite stored formal PF state')
            _stored_ranking_key(r)
            records.append(r);seen.add(s.candidate_id)
    if len(seen)!=int(np.count_nonzero(points['formal'])):raise ValueError('formal JSONL/map count mismatch')
    return sorted(records,key=lambda r:tuple(r['FixedKey']))


def audit_source(source):
    """No files outside identity +90x4 allowlist are read, including partial COMPLETE."""
    source=Path(source)
    if source.is_symlink() or not source.is_dir():raise ValueError('source directory')
    identity=_read(_regular(source/'identity.json'))
    if identity!=expected_original_identity():raise ValueError('stored original identity mismatch')
    job_root=source/'jobs'
    if job_root.is_symlink() or not job_root.is_dir():raise ValueError('jobs directory')
    expected={j.job_id for j in jobs()};actual=list(job_root.iterdir())
    if len(actual)!=90 or {p.name for p in actual}!=expected or any(p.is_symlink() or not p.is_dir() for p in actual):raise ValueError('90 exact job directories required')
    identity_hash=digest(source/'identity.json')
    if _read(source/'identity.json')!=identity:raise ValueError('identity changed during audit')
    files=[dict(Path='identity.json',SHA256=identity_hash)]
    summaries=[]
    for job in sorted(jobs(),key=lambda j:(j.symbol,int(j.direction=='SHORT'),j.weekday)):
        folder=job_root/job.job_id
        for name in JOB_FILES:_regular(folder/name)
        checkpoint=_read(folder/'checkpoint.json')
        if set(checkpoint)!={'Status','Identity','IdentitySHA256','Hashes'} or set(checkpoint['Hashes'])!=set(JOB_FILES)-{'checkpoint.json'}:raise ValueError('checkpoint schema')
        initial={'checkpoint.json':digest(folder/'checkpoint.json'),**checkpoint['Hashes']}
        # The legacy validator enforces JOB_COMPLETE, identities, all three hashes,
        # exact counts, errors, shape and formal map count. Its code is unchanged.
        summary=runtime.validate_checkpoint(folder,identity,job)
        if (summary.get('Symbol'),summary.get('Direction'),summary.get('Weekday'))!=(job.symbol,job.direction,job.weekday):raise ValueError('summary job fields')
        points=_point_arrays(folder/'point_map.npz')
        records=_records(folder,job,points)
        if len(records)!=summary['FormalPointPassCount']:raise ValueError('summary formal count')
        for name in JOB_FILES:
            if digest(folder/name)!=initial[name]:raise ValueError('source changed during audit')
            files.append(dict(Path=f'jobs/{job.job_id}/{name}',SHA256=initial[name]))
        summaries.append(summary)
    if sum(s['EvaluatedStructures'] for s in summaries)!=7335360 or sum(s['EvaluatedVariants'] for s in summaries)!=44012160:raise ValueError('global counts')
    audit=dict(Status='PASS',SourceJobCount=90,OriginalIdentitySHA256=object_hash(identity),
        EvaluatedStructures=7335360,EvaluatedVariants=44012160,TrustedFiles=files,
        SourceTrustedFilesSHA256=object_hash(files),PartialFinalizeArtifacts='IGNORED_NOT_READ')
    _unchanged(source,audit)
    return identity,audit


def _unchanged(source,audit):
    for item in audit['TrustedFiles']:
        p=_regular(Path(source)/item['Path'])
        if digest(p)!=item['SHA256']:raise ValueError('source changed during finalization')


def _stored_ranking_key(r):
    """Same frozen lexicographic fields, without calling the old gate re-check."""
    m=r['PureMetrics']
    fields=('PositiveYearCount','MedianAnnualAvgPips','WorstYearAvgPips','PFpips','AvgPips','TotalPips','MaxDDPips')
    if any(not isinstance(m.get(k),(int,float)) or not np.isfinite(m[k]) for k in fields):raise ValueError('undefined stored ranking metric')
    return (-m['PositiveYearCount'],-m['MedianAnnualAvgPips'],-m['WorstYearAvgPips'],-m['PFpips'],
            -m['AvgPips'],-m['TotalPips'],m['MaxDDPips'],*r['FixedKey'])


def _stored_families(records):
    """Original direct-representative algorithm, consuming stored formal eligibility."""
    if not records:return []
    if len({r['Symbol'] for r in records})!=1:raise ValueError('no cross-pair ranking')
    ordered=sorted(records,key=_stored_ranking_key)
    structs=[Structure.from_record(r) for r in ordered];buckets=defaultdict(set)
    for i,s in enumerate(structs):buckets[_bucket(s)].add(i)
    remaining=set(range(len(ordered)));output=[]
    for i,r in enumerate(ordered):
        if i not in remaining:continue
        rep=structs[i];nearby=set()
        for de,dx,dh in product((-1,0,1),repeat=3):
            nearby.update(buckets.get((rep.direction,rep.offset,(rep.entry//30+de)%48,(rep.exit//30+dx)%48,rep.holding//30+dh),()))
        members=sorted(j for j in nearby & remaining if near(rep,structs[j]))
        remaining.difference_update(members)
        output.append(dict(Representative=r['CandidateID'],AnchorWeekday=rep.weekday,
            SupportingWeekdays=sorted({structs[j].weekday for j in members}),
            SuppressedCandidateIDs=[ordered[j]['CandidateID'] for j in members if j!=i],
            SuppressionReason='DIRECT_REPRESENTATIVE_DISTANCE_NON_TRANSITIVE',
            Members=[dict(Definition=structs[j].definition(),PureMetrics=ordered[j]['PureMetrics']) for j in members],
            PairRank=len(output)+1,Top8=len(output)<8))
    return output


def current_preflight(reviewed_sha,original_environment):
    if not re.fullmatch('[0-9a-f]{40}',reviewed_sha) or runtime.git('rev-parse','HEAD')!=reviewed_sha:raise ValueError('reviewed finalizer SHA required')
    if runtime.git('status','--porcelain'):raise ValueError('dirty checkout')
    runtime.git('merge-base','--is-ancestor',ORIGINAL_SHA,reviewed_sha)
    verify_conditions();current=runtime.environment();check_environment(current,original_environment)
    runtime.release_manifest(ROOT/RELEASE)
    tests=runtime.run_tests()
    return dict(Status='PASS',FinalizerImplementationSHA=reviewed_sha,FinalizerEnvironment=current,Tests=tests)


def _finalize_audited(source,output,original,audit,preflight,progress=None):
    """Private processing kernel for synthetic tests; public API owns every barrier."""
    source,output=_fresh(source,output)
    _unchanged(source,audit)
    output.mkdir(parents=True,exist_ok=False)
    final_identity=dict(Mode='FINALIZE_ONLY',OriginalImplementationSHA=ORIGINAL_SHA,
        OriginalRuntimeEnvironment=original['Environment'],OriginalIdentitySHA256=object_hash(original),
        SourceTrustedFilesSHA256=audit['SourceTrustedFilesSHA256'],
        FinalizerImplementationSHA=preflight['FinalizerImplementationSHA'],FinalizerEnvironment=preflight['FinalizerEnvironment'],
        Approval=APPROVAL,ConditionsFreezeSHA=CONDITIONS_SHA,JobRecomputation=False)
    runtime.save_json(output/'finalize_identity.json',final_identity)
    runtime.save_json(output/'finalize_environment.json',preflight['FinalizerEnvironment'])
    runtime.save_json(output/'source_checkpoint_audit.json',audit)
    runtime.save_json(output/'finalize_preflight.json',preflight)
    selections=[];family_count=0;processed=0
    with (output/'plateau_diagnostics.jsonl').open('w') as diag,(output/'family_suppression.jsonl').open('w') as famout:
        for symbol in sorted(PRESPEC['P01']['SLGridPips']):
            eligible=[]
            for job in sorted((j for j in jobs() if j.symbol==symbol),key=lambda j:(int(j.direction=='SHORT'),j.weekday)):
                folder=source/'jobs'/job.job_id
                arrays=_point_arrays(folder/'point_map.npz') # Decompress each array once per job.
                def lookup(s):
                    ei,hi=s.entry//5,(s.holding-30)//5;v=float(arrays['avg'][ei,hi])
                    return dict(ScheduleValid=bool(arrays['valid'][ei,hi]),FormalPASS=bool(arrays['formal'][ei,hi]),AvgPips=None if np.isnan(v) else v)
                for record in _records(folder,job,arrays):
                    structure=Structure.from_record(record);p=plateau(structure,lookup)
                    diag.write(canonical(p)+'\n')
                    if p['PlateauPASS']:
                        eligible.append(dict(structure.definition(),PureMetrics=record['PureMetrics'],FormalPASS=True,PlateauPASS=True))
                processed+=1
                status=dict(Mode='FINALIZE_ONLY',ProcessedJobs=processed,ExpectedJobs=90,Status='IN_PROGRESS_NOT_CANDIDATES')
                runtime.save_json(output/'progress.json',status)
                if progress:progress(status)
            for family in _stored_families(eligible):
                family['Symbol']=symbol;famout.write(canonical(family)+'\n');family_count+=1
                if family['Top8']:selections.append(family)
    _unchanged(source,audit)
    runtime.save_json(output/'selected_top8.json',selections)
    review=dict(Status='COMPLETE_STAGE1_ONLY',SourceJobCount=90,OriginalImplementationSHA=ORIGINAL_SHA,
        OriginalRuntimeEnvironment=original['Environment'],FinalizerImplementationSHA=preflight['FinalizerImplementationSHA'],
        FinalizerEnvironment=preflight['FinalizerEnvironment'],EvaluatedStructures=7335360,EvaluatedVariants=44012160,
        RankingComplete=True,PlateauComplete=True,FamilyComplete=True,Top8Complete=True,ExecutionStopsAt='STAGE1_ONLY',
        Families=family_count,SelectedCount=len(selections),Mode='FINALIZE_ONLY',JobRecomputation=False)
    runtime.save_json(output/'progress.json',dict(Mode='FINALIZE_ONLY',ProcessedJobs=90,ExpectedJobs=90,Status='ALL_PHASES_FINISHED'))
    # Prepare a manifest binding the final review bytes before exposing COMPLETE status.
    review_bytes=(canonical(review)+'\n').encode()
    manifest=runtime.make_manifest(output)
    import hashlib
    manifest['Files'].append(dict(Path='review.json',SHA256=hashlib.sha256(review_bytes).hexdigest(),Bytes=len(review_bytes)))
    manifest['Files'].sort(key=lambda r:r['Path'])
    runtime.save_json(output/'artifact_manifest.json',manifest)
    runtime.save_json(output/'review.json',review)
    runtime.save_json(output/'COMPLETE.json',dict(Status='COMPLETE_STAGE1_ONLY',ManifestSHA256=digest(output/'artifact_manifest.json'),ReviewSHA256=digest(output/'review.json')))
    return review


def finalize_from_completed_jobs(source,output,reviewed_sha,approval=None,progress=None):
    if approval!=APPROVAL:raise PermissionError('dedicated Finalize-Only Chat approval required')
    if not Path('/content').is_dir() or not os.environ.get('COLAB_RELEASE_TAG'):raise PermissionError('production Finalize-Only is Colab-only')
    source,output=_fresh(source,output)
    # Fail current environment before reading result-bearing artifacts.
    original_expected=expected_original_identity()
    preflight=current_preflight(reviewed_sha,original_expected['Environment'])
    original,audit=audit_source(source)
    return _finalize_audited(source,output,original,audit,preflight,progress)


def restore_completed_jobs(source,destination):
    """Copy only approved source inputs, verify twice, publish restore marker last."""
    source,destination=_fresh(source,destination)
    original,audit=audit_source(source)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='b7-restore-incomplete-',dir=destination.parent) as tmp:
        staging=Path(tmp)/'checkpoint';staging.mkdir()
        for item in audit['TrustedFiles']:
            target=staging/item['Path'];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/item['Path'],target)
        copied_identity,copied_audit=audit_source(staging)
        if copied_identity!=original or copied_audit!=audit:raise ValueError('restored identity/hash mismatch')
        _unchanged(source,audit)
        runtime.save_json(staging/'RESTORE_COMPLETE.json',dict(Status='RESTORE_COMPLETE_90_JOBS',SourceTrustedFilesSHA256=audit['SourceTrustedFilesSHA256']))
        if destination.exists():raise FileExistsError('restore destination appeared')
        os.rename(staging,destination)
    return dict(Status='RESTORE_COMPLETE_90_JOBS',SourceJobCount=90,SourceTrustedFilesSHA256=audit['SourceTrustedFilesSHA256'])
