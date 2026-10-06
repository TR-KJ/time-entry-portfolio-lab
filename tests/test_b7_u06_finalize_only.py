import unittest,tempfile,copy,json,subprocess,os
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
from b7 import u06_finalize_only as f
from b7 import u06_runtime as producer
from b7.stage1_contract import canonical,digest,object_hash,ROOT

ENV=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
CURRENT=dict(ENV,Python='3.13.16')
PROOF=dict(Status='PASS',FinalizerImplementationSHA='a'*40,FinalizerEnvironment=CURRENT)

class FinalizeOnly(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.source=self.root/'source';self.source.mkdir();e,self.records=f.expected_identity();self.identity=dict(e,Environment=ENV)
        producer.save(self.source/'identity.json',self.identity)
        for n,r in enumerate(self.records):
            status='DROP_U06_SL' if n%3==0 else 'PASS_U06'
            result=dict(CandidateID=r['CandidateID'],Symbol=r['Symbol'],PairRank=r['PairRank'],Schedule=r['Schedule'],Status=status,FormalSL=None if n%3==0 else 25,FormalTP=None,TP=None,ChosenSLZone=None if n%3==0 else {'Points':[20,25,30]})
            job=self.source/'jobs'/r['CandidateID'];producer.complete_local(job,self.identity,r,result)
            producer.save(job/'DRIVE_COMPLETE.json',dict(Status='DRIVE_JOB_COMPLETE',CheckpointSHA256=digest(job/'checkpoint.json'),CandidateSHA256=digest(job/'candidate.json')))
        self.job=self.source/'jobs'/self.records[0]['CandidateID']
    def tearDown(self):self.tmp.cleanup()
    def audit(self):return f.audit_source(self.source,CURRENT)
    def mutate(self,path,fn):
        d=json.loads(path.read_text());fn(d);producer.save(path,d)
    def snapshot(self):return {p.relative_to(self.source).as_posix():digest(p) for p in self.source.rglob('*') if p.is_file()}
    def test_valid72(self):
        identity,audit,rs,jobs=self.audit();self.assertEqual(identity,self.identity);self.assertEqual(len(rs),72);self.assertEqual(len(jobs),72);self.assertEqual(len(audit['TrustedFiles']),217)
    def test_missing_job(self):
        self.job.rename(self.root/'removed')
        with self.assertRaises(ValueError):self.audit()
    def test_extra_job(self):
        (self.source/'jobs/extra').mkdir()
        with self.assertRaises(ValueError):self.audit()
    def test_duplicate_identity_ids(self):
        self.mutate(self.source/'identity.json',lambda d:d['CandidateIDs'].__setitem__(1,d['CandidateIDs'][0]))
        with self.assertRaises(ValueError):self.audit()
    def test_duplicate_candidate(self):
        other=self.source/'jobs'/self.records[1]['CandidateID']/'candidate.json';self.mutate(other,lambda d:d.update(CandidateID=self.records[0]['CandidateID']))
        with self.assertRaises(ValueError):self.audit()
    def test_duplicate_json_key(self):
        p=self.source/'identity.json';p.write_text(p.read_text().rstrip()[:-1]+',"ImplementationSHA":"x"}')
        with self.assertRaises(ValueError):self.audit()
    def test_candidate_corruption(self):
        (self.job/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):self.audit()
    def test_checkpoint_corruption(self):
        self.mutate(self.job/'checkpoint.json',lambda d:d.update(IdentitySHA256='0'*64))
        with self.assertRaises(ValueError):self.audit()
    def test_drive_hash_mismatch(self):
        self.mutate(self.job/'DRIVE_COMPLETE.json',lambda d:d.update(CheckpointSHA256='0'*64))
        with self.assertRaises(ValueError):self.audit()
    def test_missing_drive_marker(self):
        (self.job/'DRIVE_COMPLETE.json').unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):self.audit()
    def test_producer_mismatch(self):
        self.mutate(self.source/'identity.json',lambda d:d.update(ImplementationSHA='b'*40))
        with self.assertRaises(ValueError):self.audit()
    def test_config_input_data_mismatch(self):
        original=(self.source/'identity.json').read_bytes()
        for key in ('ConditionsFreezeSHA','U06ConfigSHA256','FullPrespecSHA256','Stage1ResultFreezeSHA','SelectedSHA256','CompactInputSHA256','SourceAuditSHA256','M1ManifestSHA256','M1ExactIdentity'):
            with self.subTest(key=key):
                self.mutate(self.source/'identity.json',lambda d:d.update({key:'changed'}))
                with self.assertRaises(ValueError):self.audit()
                (self.source/'identity.json').write_bytes(original)
    def test_environment_policy(self):
        for version in ('3.13.0','3.13.15','3.13.16','3.13.99'):f.check_environment(ENV,dict(CURRENT,Python=version))
        for version in ('3.12.15','3.14.0','4.13.0','3.13.16rc1'):
            with self.assertRaises(ValueError):f.check_environment(ENV,dict(CURRENT,Python=version))
        for key in ('NumPy','pandas'):
            with self.assertRaises(ValueError):f.check_environment(ENV,dict(CURRENT,**{key:'x'}))
        f.check_environment(dict(ENV,Python='3.12.1'),dict(CURRENT,Python='3.12.2'))
    def test_nonterminal_status_rebound(self):
        self.mutate(self.job/'candidate.json',lambda d:d.update(Status='RUNNING'))
        self.mutate(self.job/'checkpoint.json',lambda d:d.update(CandidateSHA256=digest(self.job/'candidate.json')))
        producer.save(self.job/'DRIVE_COMPLETE.json',dict(Status='DRIVE_JOB_COMPLETE',CheckpointSHA256=digest(self.job/'checkpoint.json'),CandidateSHA256=digest(self.job/'candidate.json')))
        with self.assertRaises(ValueError):self.audit()
    def traps(self):
        from b7 import u06_execution,u06_selection,u06_reference,stage1_input
        stack=ExitStack()
        for module,names in [(producer,['Engine','evaluate','select','load_discovery','preflight']), (u06_execution,['Engine','evaluate','_execute']), (u06_selection,['select']), (u06_reference,['execute']), (stage1_input,['load_discovery','read_mt5','audit_inputs']), (f.shared,['run_tests','Engine','load_discovery','evaluate_job'])]:
            for name in names:stack.enter_context(patch.object(module,name,side_effect=AssertionError('recomputation forbidden')))
        return stack
    def test_no_recomputation_source_unchanged_complete_last(self):
        before=self.snapshot();writes=[];actual=f.shared.save_json;progress=[]
        def save(path,value):writes.append(Path(path).name);actual(path,value)
        with self.traps(),patch.object(f.shared,'save_json',side_effect=save):
            review=f._finalize(self.source,self.root/'output',PROOF,progress.append)
        self.assertEqual(review['Status'],'COMPLETE_U06_ONLY');self.assertFalse(review['JobRecomputation']);self.assertEqual(writes[-1],'COMPLETE.json');self.assertEqual(before,self.snapshot())
        self.assertTrue(all(set(p)=={'ProcessedJobs','ExpectedJobs'} for p in progress));self.assertEqual(progress[-1]['ProcessedJobs'],72)
        out=self.root/'output';c=f.read(out/'COMPLETE.json');self.assertEqual(c['ManifestSHA256'],digest(out/'artifact_manifest.json'));self.assertEqual(c['ReviewSHA256'],digest(out/'review.json'))
        for item in f.read(out/'artifact_manifest.json')['Files']:
            self.assertEqual(item['SHA256'],digest(out/item['Path']));self.assertEqual(item['Bytes'],(out/item['Path']).stat().st_size)
    def test_fresh_and_separate(self):
        for out in (self.source,self.source/'new',self.root):
            with self.assertRaises((ValueError,FileExistsError)):f._finalize(self.source,out,PROOF)
    def test_staging_and_partial_root_ignored(self):
        a=self.root/'a';b=self.root/'b';f._finalize(self.source,a,PROOF)
        (self.source/'jobs/.incomplete-test').mkdir();(self.source/'jobs/.incomplete-test/candidate.json').write_text('invalid')
        for name in ('candidate_results.json','COMPLETE.json','review.json'):(self.source/name).write_text('invalid')
        f._finalize(self.source,b,PROOF)
        for name in ('candidate_results.json','pair_summary.json','checkpoint_audit.json','review.json'):self.assertEqual((a/name).read_bytes(),(b/name).read_bytes())
    def test_deterministic_process_replay(self):
        a=self.root/'a';b=self.root/'b';f._finalize(self.source,a,PROOF)
        code="from pathlib import Path; import json; from b7.u06_finalize_only import _finalize; _finalize(Path(__import__('sys').argv[1]),Path(__import__('sys').argv[2]),json.loads(__import__('sys').argv[3]))"
        env=dict(os.environ,PYTHONPATH=str(ROOT/'src/research'),PYTHONDONTWRITEBYTECODE='1',PYTHONHASHSEED='876')
        subprocess.check_call([__import__('sys').executable,'-c',code,str(self.source),str(b),canonical(PROOF)],env=env)
        self.assertEqual({p.name:digest(p) for p in a.iterdir()},{p.name:digest(p) for p in b.iterdir()})
    def test_filesystem_order(self):
        src=self.root/'reversed';src.mkdir();(src/'jobs').mkdir();(src/'identity.json').write_bytes((self.source/'identity.json').read_bytes())
        import shutil
        for r in reversed(self.records):shutil.copytree(self.source/'jobs'/r['CandidateID'],src/'jobs'/r['CandidateID'])
        a=self.root/'a';b=self.root/'b';f._finalize(self.source,a,PROOF);f._finalize(src,b,PROOF)
        self.assertEqual({p.name:digest(p) for p in a.iterdir()},{p.name:digest(p) for p in b.iterdir()})
    def test_audit_failure_no_outputs(self):
        (self.job/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):f._finalize(self.source,self.root/'out',PROOF)
        self.assertFalse((self.root/'out').exists())
    def test_write_failure_no_complete(self):
        original=f.shared.save_json
        def save(path,value):
            if Path(path).name=='artifact_manifest.json':raise OSError('interrupted')
            original(path,value)
        with patch.object(f.shared,'save_json',side_effect=save):
            with self.assertRaises(OSError):f._finalize(self.source,self.root/'out',PROOF)
        self.assertFalse((self.root/'out/COMPLETE.json').exists());self.assertFalse((self.root/'out/review.json').exists())
    def test_source_mutation_rejected(self):
        def progress(p):
            if p['ProcessedJobs']==72:(self.job/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):f._finalize(self.source,self.root/'out',PROOF,progress)
        self.assertFalse((self.root/'out').exists())
    def test_dedicated_approval(self):
        for approval in (None,producer.APPROVAL):
            with self.assertRaises(PermissionError):f.finalize_from_completed_jobs(self.source,self.root/'out','a'*40,approval)
    def test_existing_exact_resume_unchanged(self):
        root=self.root/'resume';producer.init_root(root,self.identity,False)
        with self.assertRaises(ValueError):producer.init_root(root,dict(self.identity,Environment=CURRENT),True)
    def test_symlink_marker_rejected(self):
        p=self.job/'DRIVE_COMPLETE.json';p.rename(self.root/'marker');p.symlink_to(self.root/'marker')
        with self.assertRaises(ValueError):self.audit()
    def test_producer_byte_identity(self):
        for name in ('u06_execution.py','u06_selection.py','u06_runtime.py','u06_reference.py','u06_input.py','u06_smoke.py'):
            rel='src/research/b7/'+name
            self.assertEqual((ROOT/rel).read_bytes(),subprocess.check_output(['git','-C',str(ROOT),'show',f.PRODUCER_SHA+':'+rel]))
    def test_public_api_no_recomputation(self):
        import shutil
        content=self.root.resolve()/'content';drive=content/'drive';drive.mkdir(parents=True);source=drive/'source';shutil.copytree(self.source,source)
        realpath=Path
        def mapped(p):
            s=str(p)
            return content/s.removeprefix('/content/').lstrip('/') if s.startswith('/content/') else (content if s=='/content' else realpath(p))
        with self.traps(),patch.object(f,'Path',side_effect=mapped),patch.object(f,'current_preflight',return_value=PROOF),patch.dict(f.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}):
            result=f.finalize_from_completed_jobs('/content/drive/source','/content/out','a'*40,f.APPROVAL)
        self.assertEqual(result['CompletedJobs'],72)
    def test_preflight_guards(self):
        original=f.read
        def read(p):return dict(Status='PASS',Total=1,Failed=0,Skipped=0) if Path(p).name=='test_results.json' else original(p)
        def git(*args):return 'a'*40 if args[0]=='rev-parse' else ''
        with self.traps(),patch.object(f.shared,'git',side_effect=git),patch.object(f.shared,'release_manifest'),patch.object(f,'read',side_effect=read),patch.object(f,'digest',side_effect=lambda p:'0'*64 if Path(p).name=='test_results.json' else digest(p)):
            self.assertEqual(f.current_preflight('a'*40)['Status'],'PASS')
            with self.assertRaises(ValueError):f.current_preflight('b'*40)
        with patch.object(f.shared,'git',side_effect=lambda *a:'a'*40 if a[0]=='rev-parse' else 'dirty'):
            with self.assertRaises(ValueError):f.current_preflight('a'*40)
    def test_identity_matches_producer_builder(self):
        expected,records=f.expected_identity();data=f.read(producer.INPUT)
        def git(*args):return f.PRODUCER_SHA if args[0]=='rev-parse' else ''
        with patch.object(producer.shared,'git',side_effect=git),patch.object(producer.shared,'release_manifest'),patch.object(producer,'extract',return_value=data),patch.object(producer.shared,'run_tests',return_value={'Status':'PASS'}),patch.object(producer,'audit_inputs',return_value=expected['M1ExactIdentity']),patch('b7.u06_smoke.run_smoke',return_value={'Status':'PASS'}):
            actual=producer.preflight(None,None,None,f.PRODUCER_SHA)['Identity']
        self.assertEqual({k:v for k,v in actual.items() if k!='Environment'},expected)
    def test_notebook_off(self):
        import ast
        nb=json.loads((ROOT/'notebooks/b7_u06_finalize_only.ipynb').read_text());flags=[]
        for c in nb['cells']:
            if c['cell_type']!='code':continue
            for n in ast.walk(ast.parse(''.join(c['source']))):
                if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('RUN_') for t in n.targets):flags.append(ast.literal_eval(n.value))
        self.assertEqual(len(flags),6);self.assertFalse(any(flags))
    def test_aggregation_matches_unchanged_producer(self):
        producer.finalize(self.source,self.source,self.identity,self.records)
        out=self.root/'finalizer';f._finalize(self.source,out,PROOF)
        for name in ('candidate_results.json','pair_summary.json','checkpoint_audit.json'):
            self.assertEqual((self.source/'final'/name).read_bytes(),(out/name).read_bytes())
