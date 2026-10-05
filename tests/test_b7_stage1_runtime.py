import ast
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from b7.stage1_contract import ROOT, jobs, canonical, digest, object_hash, verify_conditions
from b7.stage1_input import raw_identity, read_mt5, audit_inputs, load_discovery
from b7.stage1_runtime import checkpoint_identity, validate_checkpoint, validate_all_jobs, run_formal, make_manifest, save_json, archive_completed, make_identity, finalize

class InputTests(unittest.TestCase):
    def write(self,root,text=None):
        p=root/'a.csv';p.write_text(text or '<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n2020.02.04\t03:00:00\t100\t101\t99\t100\n2020.07.07\t03:00:00\t100\t101\t99\t100\n');return p
    def test_raw_identity_and_timezone(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.write(Path(t));r=raw_identity(p);self.assertEqual(r['Rows'],2);self.assertEqual(r['FirstRaw'],'2020-02-04 03:00:00')
            b=read_mt5(p);self.assertEqual(str(b.index[0]),'2020-02-04 10:00:00');self.assertEqual(str(b.index[1]),'2020-07-07 09:00:00')
    def test_barrier_all_fields_and_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.write(Path(t));row=dict(Symbol='USDJPY',**raw_identity(p))
            with patch('b7.stage1_input.manifest_rows',return_value=[row]):
                self.assertEqual(len(audit_inputs({'a.csv':p})),1)
                for k,v in [('SHA256','0'*64),('Rows',3),('FirstRaw','wrong'),('LastRaw','wrong')]:
                    bad=dict(row);bad[k]=v
                    with patch('b7.stage1_input.manifest_rows',return_value=[bad]):
                        with self.assertRaises(ValueError):audit_inputs({'a.csv':p})
                with self.assertRaises(ValueError):audit_inputs({})
    def test_duplicate_jst_reject(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.write(Path(t));lines=p.read_text().splitlines();p.write_text('\n'.join([lines[0],lines[1],lines[1]])+'\n')
            with self.assertRaises(ValueError):read_mt5(p)
    def test_discovery_load_never_retains_future(self):
        with tempfile.TemporaryDirectory() as t:
            p=self.write(Path(t));p.write_text(p.read_text()+'2024.02.04\t03:00:00\t100\t101\t99\t100\n')
            row=dict(Symbol='USDJPY',**raw_identity(p))
            with patch('b7.stage1_input.manifest_rows',return_value=[row]):
                b=load_discovery({'a.csv':p},'USDJPY');self.assertLess(b.index.max(),pd.Timestamp('2024-01-01'))
                with self.assertRaises(ValueError):load_discovery({'a.csv':p},'USDJPY',('2023-01-01','2025-01-01'))

class RuntimeTests(unittest.TestCase):
    def fixture(self,path,identity,job):
        path.mkdir();save_json(path/'summary.json',dict(JobID=job.job_id,ExpectedStructures=81504,EvaluatedStructures=81504,EvaluatedVariants=489024,RuntimeIdentitySHA256=object_hash(identity),Errors=0,FormalPointPassCount=0))
        (path/'formal_pass.jsonl').write_text('')
        np.savez_compressed(path/'point_map.npz',avg=np.zeros((288,283)),formal=np.zeros((288,283),bool),valid=np.ones((288,283),bool))
        ci=checkpoint_identity(identity,job)
        save_json(path/'checkpoint.json',dict(Status='JOB_COMPLETE',Identity=ci,IdentitySHA256=object_hash(ci),Hashes={n:digest(path/n) for n in ['summary.json','formal_pass.jsonl','point_map.npz']}))
    def test_checkpoint_exact_and_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'job';identity={'code':'a','env':{'numpy':'x'}};j=jobs()[0];self.fixture(p,identity,j)
            self.assertEqual(validate_checkpoint(p,identity,j)['EvaluatedStructures'],81504)
            for bad in [{'code':'b','env':{'numpy':'x'}},{'code':'a','env':{'numpy':'y'}}]:
                with self.assertRaises(ValueError):validate_checkpoint(p,bad,j)
            with self.assertRaises(ValueError):validate_checkpoint(p,identity,jobs()[1])
    def test_checkpoint_corruption(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'job';self.fixture(p,{},jobs()[0]);(p/'formal_pass.jsonl').write_text('corrupt')
            with self.assertRaises(ValueError):validate_checkpoint(p,{},jobs()[0])
    def test_complete_rejects_missing_jobs(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'jobs').mkdir();self.fixture(p/'jobs'/jobs()[0].job_id,{},jobs()[0])
            with self.assertRaises(ValueError):validate_all_jobs(p,{})
            with self.assertRaises(ValueError):finalize(p,{})
            self.assertFalse((p/'COMPLETE.json').exists())
    def test_formal_guard_before_any_data(self):
        with self.assertRaises(PermissionError):run_formal({},'x','unused')
        with patch('b7.stage1_runtime.Path.is_dir',return_value=False):
            with self.assertRaises(PermissionError):run_formal({},'x','unused',approval='CHAT_APPROVED_COLAB_STAGE1_ONLY')
    def test_90_empty_synthetic_checkpoints_complete_only(self):
        # Artifact lifecycle test, no evaluator, no M1, no search or candidate metrics.
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'jobs').mkdir()
            for j in jobs():self.fixture(p/'jobs'/j.job_id,{},j)
            r=finalize(p,{});self.assertEqual(r['Status'],'COMPLETE_STAGE1_ONLY');self.assertEqual(r['SelectedCount'],0)
            target=p.parent/(p.name+'_archive')
            try:
                archive_completed(p,target);self.assertTrue((target/'archive.zip').exists())
                with self.assertRaises(FileExistsError):archive_completed(p,target)
            finally:
                import shutil
                if target.exists():shutil.rmtree(target)
    def test_identity_has_required_fields(self):
        d=make_identity('a'*40,[])
        for key in ['ImplementationCommitSHA','FullPrespecSHA256','Stage1PrespecSHA256','ManifestSHA256','M1ExactIdentity','Spreads','PipSizes','OfficialSLGrid','ExecutionConvention','DiscoveryBounds','Environment','GateConfig','Ranking','Plateau','Family','JobDefinitions']:self.assertIn(key,d)
        self.assertEqual(len(d['JobDefinitions']),90)
    def test_frozen_conditions_unchanged(self):verify_conditions()
    def test_notebook_defaults_and_python_cells(self):
        notebook=json.loads((ROOT/'notebooks/b7_stage1_discovery.ipynb').read_text());self.assertEqual(notebook['nbformat'],4)
        sources=[''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code']
        for source in sources:ast.parse(source)
        switches={}
        for source in sources:
            for node in ast.walk(ast.parse(source)):
                if isinstance(node,ast.Assign):
                    for target in node.targets:
                        if isinstance(target,ast.Name) and target.id.startswith('RUN_'):switches[target.id]=ast.literal_eval(node.value)
        self.assertIn('RUN_FORMAL',switches);self.assertTrue(all(v is False for v in switches.values()))
