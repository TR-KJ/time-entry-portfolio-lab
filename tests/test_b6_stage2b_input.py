"""Synthetic full-schema audit fixtures; no runtime result reconstruction."""
import copy,gzip,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage2a import fifty
from b6.stage2a_config import settings,PATH as ACONFIG
from b6.stage2b_config import load_config
from b6.stage2b_input import SCHEMAS,load_input

class InputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidates=fifty();cls.c=load_config();c=cls.c
        cls.audit=dict(Status='PASS',CandidateCount=50,CandidateSHA256=c['candidate_sha256'],Stage1FreezeSHA=c['stage1_freeze_sha'],Stage1EffectiveConfigSHA256=c['stage1_effective_config_sha256'],CandidateIDs=[a['CandidateID'] for a in cls.candidates],Configurations=1500)
        inputs=pd.read_csv(ROOT/'research_inputs/b6/expected_m1_manifest.csv',dtype=str)[['Filename','SHA256']].to_dict('records')
        cls.meta={'identity.json':dict(code_sha=c['stage2a_freeze_sha'],config_sha256=c['stage2a_config_sha256'],candidate_sha256=c['candidate_sha256'],stage1_code_sha=c['stage1_freeze_sha'],stage1_config_sha256=c['stage1_effective_config_sha256'],scope='FULL_DISCOVERY_STAGE2A',inputs=inputs,runtime=dict(Python='3.13.15',Numpy='2.3.5',Pandas='2.2.3')),'candidate_input_audit.json':cls.audit,'progress.json':dict(CompletedJobs=50,ExpectedJobs=50,CompletedConfigurations=1500,State='COMPLETE_STAGE2A_ONLY'),'stage2a_summary.json':dict(State='COMPLETE_STAGE2A_ONLY',Candidates=50,Configurations=1500,PassCount=1500,FailCount=0,FormalRanking=False,Stage2BCentersSelected=False,ValidationExecuted=False,MonitorExecuted=False)}
        cls.tables={name:[] for name in SCHEMAS}
        for a in cls.candidates:
            for setting in settings(a):
                base={**a,**setting};base['RatioAliases']='|'.join(base['RatioAliases'])
                cls.tables['stage2a_all_results.csv.gz'].append({**base,'Wins':120,'Losses':40,'WinRate':.75,'TotalR':200.,'AvgR':1.25,'PF':6.,'MaxDDR':1.,'Trades':160,'ZeroR':0,'AvgWinR':2.,'AvgLossR':-1.,'Pass':True,'FailReasons':'','PositiveYears':4})
                for y in (2020,2021,2022,2023):cls.tables['stage2a_yearly_results.csv.gz'].append({**base,'Year':y,'Trades':40,'Wins':30,'Losses':10,'TotalR':50.,'AvgR':1.25,'PF':6.,'MaxDDR':1.})
                diag={**base,**{k:0 for k in SCHEMAS['stage2a_diagnostics.csv.gz'] if k not in base}};diag.update(SLCount=40,SLRate=.25,TimeExitCount=120,TimeExitRate=.75,Opportunities_OK=160)
                cls.tables['stage2a_diagnostics.csv.gz'].append(diag)
    def write_fixture(self,p,meta=None,tables=None):
        for name,value in (self.meta if meta is None else meta).items():(p/name).write_text(json.dumps(value))
        (p/'effective_config.json').write_bytes(ACONFIG.read_bytes())
        for name,rows in (self.tables if tables is None else tables).items():pd.DataFrame(rows,columns=SCHEMAS[name]).to_csv(p/name,index=False,compression='gzip')
        c=copy.deepcopy(self.c);c['stage2a_runtime_sha256']={name:hashlib.sha256((p/name).read_bytes()).hexdigest() for name in c['stage2a_required_files']};return c
    def check(self,p,c):
        with patch('b6.stage2b_input.load_candidates',return_value=(self.candidates,self.audit)):
            return load_input(p,p,c)
    def test_complete_input_audit_without_center_selection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=self.write_fixture(p);a,rows,audit,identity=self.check(p,c)
            self.assertEqual(len(a),50);self.assertEqual(len(rows),1500);self.assertEqual(audit['Rows']['stage2a_yearly_results.csv.gz'],6000);self.assertFalse(audit['CentersSelected'])
    def test_byte_hash_and_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=self.write_fixture(p);f=p/'progress.json';f.write_text(f.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.check(p,c)
            f.unlink()
            with self.assertRaisesRegex(ValueError,'missing'):self.check(p,c)
    def test_metadata_gates_even_if_hashes_rebound(self):
        mutations=[('progress.json','State','RUNNING'),('progress.json','CompletedJobs',49),('stage2a_summary.json','Configurations',1499),('stage2a_summary.json','Candidates',49),('stage2a_summary.json','ValidationExecuted',True),('stage2a_summary.json','PassCount',1499),('identity.json','code_sha','a'*40),('identity.json','config_sha256','a'*64),('identity.json','candidate_sha256','a'*64),('identity.json','inputs',[]),('identity.json','runtime',{}),('candidate_input_audit.json','CandidateCount',49)]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for name,key,value in mutations:
                meta=copy.deepcopy(self.meta);meta[name][key]=value;c=self.write_fixture(p,meta=meta)
                with self.subTest(name=name,key=key),self.assertRaises(ValueError):self.check(p,c)
    def test_row_schema_duplicate_candidate_sl_tp_mode_and_year(self):
        cases=['count','schema','duplicate','candidate','sl','tp','mode','year','pass','metric','diagnostic']
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            for case in cases:
                tables=copy.deepcopy(self.tables);allrows=tables['stage2a_all_results.csv.gz']
                if case=='count':allrows.pop()
                elif case=='duplicate':allrows[1]=allrows[0]
                elif case=='candidate':allrows[0]['CandidateID']='invented'
                elif case=='sl':allrows[0]['SL']=11
                elif case=='tp':allrows[0]['TP']=10
                elif case=='mode':allrows[0]['TPMode']='FINITE'
                elif case=='year':tables['stage2a_yearly_results.csv.gz'][0]['Year']=2024
                elif case=='pass':allrows[0]['Pass']=False
                elif case=='metric':allrows[0]['AvgR']=100
                elif case=='diagnostic':tables['stage2a_diagnostics.csv.gz'][0]['SLCount']=41
                c=self.write_fixture(p,tables=tables)
                if case=='schema':
                    f=p/'stage2a_all_results.csv.gz';df=pd.read_csv(f);df=df.drop(columns=['PF']);df.to_csv(f,index=False,compression='gzip');c['stage2a_runtime_sha256'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
                with self.subTest(case=case),self.assertRaises(ValueError):self.check(p,c)
    def test_effective_config_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);c=self.write_fixture(p);f=p/'effective_config.json';f.write_text('{}');c['stage2a_runtime_sha256'][f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):self.check(p,c)
