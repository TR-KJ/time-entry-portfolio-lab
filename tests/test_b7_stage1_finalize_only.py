"""Only manufactured90-job fixtures. Never reads a user's checkpoint or M1."""
import contextlib
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from b7 import stage1_finalize_only as final
from b7 import stage1_runtime as runtime
from b7.stage1_contract import ROOT, Structure, jobs, canonical, object_hash, digest
from b7.stage1_metrics import summarize_arrays
from b7.stage1_family import neighbors, families

ENV={'Python':'3.13.16','NumPy':'2.3.5','pandas':'2.2.3'}
PROOF={'Status':'PASS','FinalizerImplementationSHA':'f'*40,'FinalizerEnvironment':ENV,'Tests':{'Status':'SYNTHETIC_FIXTURE'}}
OUTPUTS=('plateau_diagnostics.jsonl','family_suppression.jsonl','selected_top8.json')


def fixture(root,reverse=False):
    root=Path(root);root.mkdir();identity=final.expected_original_identity();runtime.save_json(root/'identity.json',identity)
    values=np.array(([2.]*30+[-1.]*10)*4);index=np.arange(160)
    metric=summarize_arrays(values,index,index,np.repeat([2020,2021,2022,2023],40))
    js=list(jobs())
    if reverse:js.reverse()
    for job in js:
        folder=root/'jobs'/job.job_id;folder.mkdir(parents=True)
        formal=np.zeros((288,283),bool);avg=np.full((288,283),metric['AvgPips']);valid=np.ones((288,283),bool);records=[]
        if job.symbol=='AUDJPY' and job.direction=='LONG' and job.weekday in (0,1):
            structures={s.candidate_id:s for entry in (540,600) for s in neighbors(Structure(job.symbol,job.direction,job.weekday,entry,60))}
            for s in sorted(structures.values(),key=lambda s:s.key):
                formal[s.entry//5,(s.holding-30)//5]=True
                records.append(dict(s.definition(),PureMetrics=metric,PurePASS=True,SLPASS=[True]*5,PassingSLCount=5,SLRobustnessPASS=True,FormalPASS=True,FiveSLMetrics=[]))
        with (folder/'formal_pass.jsonl').open('w') as out:
            for r in records:out.write(canonical(r)+'\n')
        np.savez_compressed(folder/'point_map.npz',avg=avg,formal=formal,valid=valid)
        runtime.save_json(folder/'summary.json',dict(JobID=job.job_id,Symbol=job.symbol,Direction=job.direction,Weekday=job.weekday,
            ExpectedStructures=81504,EvaluatedStructures=81504,EvaluatedVariants=489024,Errors=0,FormalPointPassCount=len(records),PurePassCount=len(records),SLRobustPassCount=len(records),MissingDiagnostics={},RuntimeIdentitySHA256=object_hash(identity)))
        ci=runtime.checkpoint_identity(identity,job)
        runtime.save_json(folder/'checkpoint.json',dict(Status='JOB_COMPLETE',Identity=ci,IdentitySHA256=object_hash(ci),Hashes={n:digest(folder/n) for n in ('summary.json','formal_pass.jsonl','point_map.npz')}))
    return identity


def hashes(root):return {p.relative_to(root).as_posix():digest(p) for p in Path(root).rglob('*') if p.is_file()}


@contextlib.contextmanager
def no_calculation():
    with contextlib.ExitStack() as stack:
        for target in ['b7.stage1_runtime.Engine','b7.stage1_runtime.load_discovery','b7.stage1_runtime.evaluate_job',
                       'b7.stage1.Engine','b7.stage1.regenerate','b7.stage1_metrics.gate','b7.stage1_metrics.point_result',
                       'b7.stage1_runtime.audit_inputs','b7.stage1_runtime.run_smoke','b7.stage1_input.read_mt5']:
            stack.enter_context(patch(target,side_effect=AssertionError('forbidden calculation: '+target)))
        yield


class FinalizeOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name);cls.master=cls.root/'master';fixture(cls.master)
        cls.identity,cls.audit=final.audit_source(cls.master)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):self.temp_case=tempfile.TemporaryDirectory();self.root_case=Path(self.temp_case.name)
    def tearDown(self):self.temp_case.cleanup()
    def source(self):
        path=self.root_case/'source';shutil.copytree(self.master,path);return path
    def kernel(self,source,out):
        identity,audit=final.audit_source(source)
        return final._finalize_audited(source,out,identity,audit,PROOF)
    def mutate_json(self,path,fn):
        d=json.loads(path.read_text());fn(d);runtime.save_json(path,d)
    def test_original_identity_pin(self):
        self.assertEqual(self.identity['ImplementationCommitSHA'],'abe588cf14c225f1cc8f9f991700fbe815618cc2')
        self.assertEqual(len(self.identity['M1ExactIdentity']),72);self.assertEqual(self.audit['SourceJobCount'],90)
    def test_patch_only_environment(self):
        for version in ['3.13.0','3.13.15','3.13.16','3.13.99']:final.check_environment(dict(ENV,Python=version),self.identity['Environment'])
        for version in ['3.12.14','3.14.0','4.13.0','3.13.16rc1']:
            with self.assertRaises(ValueError):final.check_environment(dict(ENV,Python=version),self.identity['Environment'])
    def test_numpy_pandas_mismatch(self):
        for key in ['NumPy','pandas']:
            with self.assertRaises(ValueError):final.check_environment(dict(ENV,**{key:'0.0.0'}),self.identity['Environment'])
    def test_missing_job(self):
        source=self.source();shutil.rmtree(source/'jobs'/jobs()[0].job_id)
        with self.assertRaises(ValueError):final.audit_source(source)
    def test_extra_job(self):
        source=self.source();(source/'jobs'/'EXTRA').mkdir()
        with self.assertRaises(ValueError):final.audit_source(source)
    def test_modified_checkpoint(self):
        source=self.source();p=source/'jobs'/jobs()[0].job_id/'checkpoint.json';self.mutate_json(p,lambda d:d.update(IdentitySHA256='0'*64))
        with self.assertRaises(ValueError):final.audit_source(source)
    def test_incomplete_job(self):
        source=self.source();p=source/'jobs'/jobs()[0].job_id/'checkpoint.json';self.mutate_json(p,lambda d:d.update(Status='IN_PROGRESS'))
        with self.assertRaises(ValueError):final.audit_source(source)
    def test_three_output_corruptions(self):
        for name in ['summary.json','formal_pass.jsonl','point_map.npz']:
            with self.subTest(name=name):
                source=self.root_case/name;shutil.copytree(self.master,source);p=source/'jobs'/jobs()[0].job_id/name
                with p.open('ab') as f:f.write(b'changed')
                with self.assertRaises(ValueError):final.audit_source(source)
    def test_original_identity_fields_reject(self):
        source=self.source();p=source/'identity.json'
        for key,value in [('ImplementationCommitSHA','0'*40),('ConditionsFreezeSHA','0'*40),('RuntimeConfigSHA256','0'*64),('Ranking',[]),('M1ExactIdentity',[]),('DiscoveryBounds',[])]:
            with self.subTest(key=key):
                bad=copy.deepcopy(self.identity);bad[key]=value;runtime.save_json(p,bad)
                with self.assertRaises(ValueError):final.audit_source(source)
        for env in [dict(self.identity['Environment'],Python='3.13.16'),dict(self.identity['Environment'],NumPy='2.0.0'),dict(self.identity['Environment'],pandas='2.0.0')]:
            bad=copy.deepcopy(self.identity);bad['Environment']=env;runtime.save_json(p,bad)
            with self.assertRaises(ValueError):final.audit_source(source)
    def test_dedicated_approval(self):
        for approval in [None,'CHAT_APPROVED_COLAB_STAGE1_ONLY']:
            with self.assertRaises(PermissionError):final.finalize_from_completed_jobs(self.master,self.root_case/'out','f'*40,approval)
    def test_fresh_separate_output(self):
        for out in [self.master,self.master/'child',self.root]:
            with self.assertRaises((ValueError,FileExistsError)):final._fresh(self.master,out)
        existing=self.root_case/'exists';existing.mkdir()
        with self.assertRaises(FileExistsError):self.kernel(self.master,existing)
    def test_no_recalculation_public_api_and_source_unchanged(self):
        source=self.source();before=hashes(source);out=self.root_case/'out'
        original_is_dir=Path.is_dir
        def fake_is_dir(path):return True if str(path)=='/content' else original_is_dir(path)
        with no_calculation(),patch.object(final,'current_preflight',return_value=PROOF),patch.dict(os.environ,{'COLAB_RELEASE_TAG':'synthetic'}),patch.object(Path,'is_dir',fake_is_dir):
            r=final.finalize_from_completed_jobs(source,out,'f'*40,final.APPROVAL)
        self.assertEqual(r['Status'],'COMPLETE_STAGE1_ONLY');self.assertEqual(before,hashes(source));self.assertFalse(r['JobRecomputation'])
        self.assertTrue(json.loads((out/'selected_top8.json').read_text()))
        self.assertEqual(set(['plateau_diagnostics.jsonl','family_suppression.jsonl','selected_top8.json','review.json','progress.json','artifact_manifest.json','COMPLETE.json','finalize_identity.json','finalize_environment.json','source_checkpoint_audit.json'])-set(p.name for p in out.iterdir()),set())
        complete=json.loads((out/'COMPLETE.json').read_text());self.assertEqual(complete['ManifestSHA256'],digest(out/'artifact_manifest.json'))
        for f in json.loads((out/'artifact_manifest.json').read_text())['Files']:self.assertEqual(digest(out/f['Path']),f['SHA256'])
    def test_partial_artifacts_never_read_and_deterministic_order(self):
        source=self.source();a=self.root_case/'a';b=self.root_case/'b'
        self.kernel(source,a)
        for name in ['plateau_diagnostics.jsonl','family_suppression.jsonl','selected_top8.json','review.json','artifact_manifest.json','COMPLETE.json']:(source/name).write_text('not even valid JSON')
        with patch.object(final,'jobs',return_value=tuple(reversed(jobs()))):self.kernel(source,b)
        for name in OUTPUTS:self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())
    def test_filesystem_creation_order(self):
        source=self.root_case/'reverse';fixture(source,True)
        a=self.root_case/'a';b=self.root_case/'b';self.kernel(self.master,a);self.kernel(source,b)
        for name in OUTPUTS:self.assertEqual(digest(a/name),digest(b/name))
    def test_original_selection_semantics(self):
        old=self.source();new=self.root_case/'new';runtime.finalize(old,self.identity);self.kernel(self.master,new)
        for name in OUTPUTS:self.assertEqual((old/name).read_bytes(),(new/name).read_bytes())
    def test_process_replay_canonical_hash(self):
        for n in [1,2]:
            code="from b7.stage1_finalize_only import audit_source,_finalize_audited; import json; from pathlib import Path; s=Path("+repr(str(self.master))+"); i,a=audit_source(s); _finalize_audited(s,Path("+repr(str(self.root_case/str(n)))+"),i,a,"+repr(PROOF)+")"
            env=dict(os.environ,PYTHONPATH=str(ROOT/'src/research'),PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED=str(n))
            subprocess.run([sys.executable,'-B','-c',code],check=True,env=env,capture_output=True)
        for name in OUTPUTS:self.assertEqual(digest(self.root_case/'1'/name),digest(self.root_case/'2'/name))
    def test_restore_allowlist_and_revalidation(self):
        source=self.source();(source/'selected_top8.json').write_text('ignore');before=hashes(source);out=self.root_case/'restore'
        with no_calculation():r=final.restore_completed_jobs(source,out)
        self.assertEqual(r['SourceJobCount'],90);self.assertEqual(before,hashes(source));self.assertFalse((out/'selected_top8.json').exists());final.audit_source(out)
        with self.assertRaises(FileExistsError):final.restore_completed_jobs(source,out)
    def test_restore_partial_copy_rejected(self):
        out=self.root_case/'restore'
        with patch.object(final.shutil,'copy2',side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):final.restore_completed_jobs(self.master,out)
        self.assertFalse(out.exists())
    def test_failure_never_complete(self):
        out=self.root_case/'out'
        with patch.object(final,'plateau',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError):self.kernel(self.master,out)
        self.assertFalse((out/'COMPLETE.json').exists());self.assertFalse((out/'review.json').exists())
    def test_normal_identity_patch_difference_still_rejected(self):
        changed=copy.deepcopy(self.identity);changed['Environment']['Python']='3.13.16'
        with self.assertRaises(ValueError):runtime.validate_checkpoint(self.master/'jobs'/jobs()[0].job_id,changed,jobs()[0])
    def test_current_preflight_identity_clean_and_environment(self):
        def git_good(*args):return 'f'*40 if args==('rev-parse','HEAD') else ''
        with patch.object(runtime,'git',side_effect=git_good),patch.object(runtime,'environment',return_value=ENV),patch.object(runtime,'release_manifest',return_value={}),patch.object(runtime,'run_tests',return_value={'Status':'PASS'}):
            self.assertEqual(final.current_preflight('f'*40,self.identity['Environment'])['Status'],'PASS')
            with self.assertRaises(ValueError):final.current_preflight('a'*40,self.identity['Environment'])
        with patch.object(runtime,'git',side_effect=lambda *a:'f'*40 if a==('rev-parse','HEAD') else 'dirty'):
            with self.assertRaises(ValueError):final.current_preflight('f'*40,self.identity['Environment'])
    def test_existing_kernels_byte_identical(self):
        import subprocess
        g='git'
        for path in ['src/research/b7/stage1_runtime.py','src/research/b7/stage1.py','src/research/b7/stage1_metrics.py','src/research/b7/stage1_family.py','src/research/b7/stage1_contract.py','research_inputs/b7/stage1_runtime_config.json']:
            frozen=subprocess.check_output([g,'-C',str(ROOT),'show',final.ORIGINAL_SHA+':'+path])
            self.assertEqual((ROOT/path).read_bytes(),frozen)

    def test_pin_equals_original_identity_builder(self):
        from b7.stage1_input import manifest_rows
        expected=runtime.make_identity(final.ORIGINAL_SHA,[dict(r,Rows=int(r['Rows'])) for r in manifest_rows()])
        expected['Environment']={'Python':'3.13.15','NumPy':'2.3.5','pandas':'2.2.3'}
        self.assertEqual(expected,self.identity)

    def test_count_and_shape_rejections_even_when_rehashed(self):
        source=self.source();folder=source/'jobs'/jobs()[0].job_id
        for field,value in [('ExpectedStructures',1),('EvaluatedStructures',1),('EvaluatedVariants',1),('Errors',1),('FormalPointPassCount',999)]:
            original=(self.master/'jobs'/jobs()[0].job_id/'summary.json').read_text()
            (folder/'summary.json').write_text(original)
            self.mutate_json(folder/'summary.json',lambda d:d.update({field:value}))
            self.mutate_json(folder/'checkpoint.json',lambda d:d['Hashes'].update({'summary.json':digest(folder/'summary.json')}))
            with self.assertRaises(ValueError):final.audit_source(source)
        shutil.copy2(self.master/'jobs'/jobs()[0].job_id/'summary.json',folder/'summary.json')
        np.savez_compressed(folder/'point_map.npz',avg=np.zeros((1,1)),formal=np.zeros((1,1),bool),valid=np.ones((1,1),bool))
        self.mutate_json(folder/'checkpoint.json',lambda d:d['Hashes'].update({'summary.json':digest(folder/'summary.json'),'point_map.npz':digest(folder/'point_map.npz')}))
        with self.assertRaises(ValueError):final.audit_source(source)
