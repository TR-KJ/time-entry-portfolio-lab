"""Synthetic corruption gates for audited Stage3 results; no price execution."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage3 import fixed
from b6.stage3_search import prepare_jobs
from b6.stage3_config import load_config as prior_config
from b6.stage3_selection import select_final
from b6.stage4_config import load_config
from b6.stage4_input import validate_payload,compare_table,load_input

def payload():
    c=load_config();c['selected_candidate_count']=1;prev=prior_config();a=fixed();jobs,space=prepare_jobs([a],prev);grid=jobs[0]['grid'];rows=[dict(p,AvgR=1.,TotalR=200.,MaxDDR=1.,Pass=True) for p in grid];annual=[dict(r,Year=y) for r in rows for y in (2020,2021,2022,2023)]
    s=select_final(a,rows,annual,prev);cid=a['CandidateID'];audit=dict(FormalInputSHA256={'prior':'hash'});identity=dict(inputs=[])
    meta={'identity.json':dict(code_sha=c['stage3_freeze_sha'],config_sha256=c['stage3_config_sha256'],stage2b_code_sha=c['stage2b_freeze_sha'],selected_settings_sha256=prev['selected_settings_sha256'],stage2b_runtime_sha256=audit['FormalInputSHA256'],candidate_sha256=c['candidate_sha256'],scope='FULL_DISCOVERY_STAGE3',inputs=[],runtime=dict(Python='3.13',Numpy='2.3.5',Pandas='2.2.3')),'effective_config.json':prev,'stage2b_input_audit.json':audit,'stage3_summary.json':dict(State='COMPLETE_STAGE3_ONLY',Stage4Executed=False,EventFilterExecuted=False,ValidationExecuted=False,MonitorExecuted=False,Refill=False,CandidateCount=1,SelectedStructures=1,DroppedStructures=0,ActualUniqueConfigurations=len(grid),GatePass=len(grid),GateFail=0,StabilityPass=len(grid),StabilityFail=0),'progress.json':dict(State='COMPLETE_STAGE3_ONLY',CompletedJobs=1,ExpectedJobs=1,CompletedConfigurations=len(grid),ExpectedConfigurations=len(grid)),'search_space.json':space,'invalid_schedules.json':jobs[0]['invalid'],'stage3_selected_settings.json':[s['selected']]}
    shards={cid:dict(grid=grid,results=rows,yearly=annual,diagnostics=[dict(p) for p in grid])}
    return meta,shards,[a],c,audit,identity

class InputTests(unittest.TestCase):
    def test_valid_saved_ranking(self):self.assertEqual(len(validate_payload(*payload())[0]),1)
    def test_stage3_identity_tamper(self):
        args=payload();args[0]['identity.json']['code_sha']='bad'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_effective_config_tamper(self):
        args=payload();args[0]['effective_config.json']['schema']='bad'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_incomplete_progress(self):
        args=payload();args[0]['progress.json']['State']='RUNNING'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_later_stage_flags(self):
        for key in ('Stage4Executed','EventFilterExecuted','ValidationExecuted','MonitorExecuted','Refill'):
            args=payload();args[0]['stage3_summary.json'][key]=True
            with self.assertRaises(ValueError):validate_payload(*args)
    def test_selected_duplicate(self):
        args=payload();args[0]['stage3_selected_settings.json']*=2
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_selected_time_and_sl_tp_tamper(self):
        for key in ('FinalEntryJST','FinalExitJST','FinalExitDayOffset','FinalHoldingMinutes','SL','TP','AdjustedEntryMinute'):
            args=payload();args[0]['stage3_selected_settings.json'][0][key]='changed'
            with self.assertRaises(ValueError):validate_payload(*args)
    def test_saved_grid_cannot_restore_anchor(self):
        args=payload();cid=args[2][0]['CandidateID'];args[1][cid]['grid'][0]['SL']=999
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_summary_partition_counts(self):
        args=payload();args[0]['stage3_summary.json']['DroppedStructures']=1
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_missing_year(self):
        args=payload();cid=args[2][0]['CandidateID'];args[1][cid]['yearly'].pop()
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_saved_stability_ranking_not_manual_selection(self):
        args=payload();args[0]['stage3_selected_settings.json'][0]['NeighborhoodMedianAvgR']=99
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_table_schema_count_content(self):
        compare_table(b'a,b\n1,True\n',[dict(a=1,b=True)],'table')
        for raw in (b'a,b\n1,False\n',b'a,b\n',b'c,b\n1,True\n'):
            with self.assertRaises(ValueError):compare_table(raw,[dict(a=1,b=True)],'table')
    def test_exact_bytes_missing_and_tamper_before_chain_io(self):
        with tempfile.TemporaryDirectory() as out,patch('b6.stage4_input.previous_input',side_effect=AssertionError('chain read')):
            c=load_config();c['stage3_runtime_manifest']={'x.json':'a'*64}
            with self.assertRaises(ValueError):load_input(out,'','',c)
            (Path(out)/'x.json').write_text('{}')
            with self.assertRaises(ValueError):load_input(out,'','',c)
