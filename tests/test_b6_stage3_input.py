"""Synthetic Stage2-B artifacts, independent of private Drive test data."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage3 import fixed
from b6.stage3_config import load_config
from b6.stage3_input import load_input,validate_payload,normalize
from b6.stage2b_config import load_config as previous_config,PATH as BPATH
from b6.stage2b_selection import select_centers,local_grid,final_selection
from b6.stage2a_config import STRUCTURE_KEYS
from b6.stage2a_engine import Replay
from b6.stage2a_metrics import summarize

class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c=load_config();b=previous_config();a={k:v for k,v in fixed().items() if k in STRUCTURE_KEYS};cls.candidates=[a];cls.audit={'CandidateSHA256':c['candidate_sha256']}
        center=select_centers(a,[{**a,'SL':50,'TP':None,'TPMode':'TP_NONE','AvgR':1.25,'TotalR':200.,'MaxDDR':1.,'Pass':True}]);grid=local_grid(center,b)
        dates=pd.DatetimeIndex([d for y in (2020,2021,2022,2023) for d in pd.date_range(f'{y}-02-04',periods=40,freq='7D')]);raw=np.tile(np.tile([2.,2.,2.,-1.],40),(5,1));records=[[dict(Status='OK',ExitReason='TimeExit' if r>0 else 'SL',ExitDelayMinutes=0,missing_path_minutes=0,exit_bar_first_hit=False) for r in raw[0]] for _ in grid]
        metrics=summarize(a,grid,Replay(dates,np.zeros(160,dtype=int),records,raw),b['gate']);selected=final_selection(a,center,metrics['results'],metrics['yearly'],b)
        cls.tables={'stage2b_all_results.csv.gz':metrics['results'],'stage2b_yearly_results.csv.gz':metrics['yearly'],'stage2b_diagnostics.csv.gz':metrics['diagnostics'],'stability_results.csv.gz':selected['stability'],'stability_by_center.csv.gz':selected['neighborhoods'],'dropped_structures.csv':[]}
        inputs=pd.read_csv(ROOT/'research_inputs/b6/expected_m1_manifest.csv',dtype=str)[['Filename','SHA256']].to_dict('records')
        cls.meta={'identity.json':dict(code_sha=c['stage2b_freeze_sha'],config_sha256=c['stage2b_config_sha256'],stage2a_code_sha=c['stage2a_freeze_sha'],stage2a_config_sha256=b['stage2a_config_sha256'],candidate_sha256=c['candidate_sha256'],scope='FULL_DISCOVERY_STAGE2B',stage2a_result_sha256=b['stage2a_runtime_sha256'],inputs=inputs,runtime=dict(Python='3.13.15',Numpy='2.3.5',Pandas='2.2.3')),'effective_config.json':b,'progress.json':dict(State='COMPLETE_STAGE2B_ONLY',CompletedJobs=1,ExpectedJobs=1,CompletedConfigurations=5,ExpectedConfigurations=5),'stage2b_summary.json':dict(State='COMPLETE_STAGE2B_ONLY',Stage3Executed=False,ValidationExecuted=False,MonitorExecuted=False,Refill=False,Candidates=1,UniqueCenters=1,ActualUniqueConfigurations=5,SelectedStructures=1,DroppedStructures=0,P02Pass=5,P02Fail=0,StabilityPass=5,StabilityFail=0),'centers.json':center,'stage2b_selected_settings.json':[selected['selected']],'search_space.json':{'ActualUniqueConditions':5},'stage2a_input_audit.json':dict(Status='PASS',RuntimeResultSHA256=b['stage2a_runtime_sha256'],CandidateSHA256=c['candidate_sha256'])}
        cls.c=copy.deepcopy(c);cls.c.update(selected_candidate_count=1,selected_tp_none_count=1)
    def write(self,p,meta=None,tables=None):
        meta=self.meta if meta is None else meta;tables=self.tables if tables is None else tables;c=copy.deepcopy(self.c);manifest={}
        for n,data in meta.items():
            f=p/n;f.write_bytes(BPATH.read_bytes()) if n=='effective_config.json' else f.write_text(json.dumps(data))
            manifest[n]={'SHA256':hashlib.sha256(f.read_bytes()).hexdigest()}
        for n,rows in tables.items():
            encoded=[{k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows];df=pd.DataFrame(encoded) if rows else pd.DataFrame(columns=[*STRUCTURE_KEYS,'Reason']);f=p/n;df.to_csv(f,index=False,compression='gzip' if n.endswith('.gz') else None)
            manifest[n]={'SHA256':hashlib.sha256(f.read_bytes()).hexdigest(),'Rows':len(df),'Columns':list(df.columns)}
        c['stage2b_runtime_manifest']=manifest;c['selected_settings_sha256']=manifest['stage2b_selected_settings.json']['SHA256'];return c
    def audit_input(self,p,c):
        with patch('b6.stage3_input.load_candidates',return_value=(self.candidates,self.audit)):return load_input(p,p,c)
    def test_complete_audit_no_stage3_selection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=self.write(p);rows,audit,identity=self.audit_input(p,c);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['SL'],50);self.assertIsNone(rows[0]['TP']);self.assertFalse(audit['Stage3SelectionPerformed'])
    def test_exact_hash_and_missing_root_or_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=self.write(p);f=p/'progress.json';f.write_text(f.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.audit_input(p,c)
            f.unlink()
            with self.assertRaisesRegex(ValueError,'missing'):self.audit_input(p,c)
            with self.assertRaises(ValueError):load_input(p/'absent',p,c)
    def test_provenance_and_incomplete_rejected_after_rehash(self):
        cases=[('identity.json','code_sha','a'*40),('identity.json','candidate_sha256','a'*64),('identity.json','inputs',[]),('progress.json','State','RUNNING'),('progress.json','CompletedJobs',0),('stage2b_summary.json','Stage3Executed',True),('stage2b_summary.json','ValidationExecuted',True),('stage2b_summary.json','MonitorExecuted',True),('stage2b_summary.json','SelectedStructures',2)]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name,k,v in cases:
                meta=copy.deepcopy(self.meta);meta[name][k]=v;c=self.write(p,meta=meta)
                with self.subTest(k=k),self.assertRaises(ValueError):self.audit_input(p,c)
    def test_selected_duplicate_sl_tp_status_and_yearly_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for case in ('duplicate','SL','TP','status','yearly'):
                meta=copy.deepcopy(self.meta);rows=meta['stage2b_selected_settings.json']
                if case=='duplicate':rows.append(rows[0])
                elif case=='SL':rows[0]['SelectedSL']+=5
                elif case=='TP':rows[0]['TP']=20
                elif case=='status':rows[0]['StabilityPass']=False
                else:rows[0]['YearlyMetrics'][0]['Year']=2024
                c=self.write(p,meta=meta)
                with self.subTest(case=case),self.assertRaises(ValueError):self.audit_input(p,c)
    def test_dropped_overlap_and_result_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for case in ('dropped','duplicate'):
                tables=copy.deepcopy(self.tables)
                if case=='dropped':tables['dropped_structures.csv']=[{**self.candidates[0],'Reason':'DROPPED'}]
                else:tables['stage2b_all_results.csv.gz'].append(tables['stage2b_all_results.csv.gz'][0])
                c=self.write(p,tables=tables)
                with self.assertRaises(ValueError):self.audit_input(p,c)
