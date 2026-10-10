import unittest,tempfile,copy,json,os,sys,subprocess
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import u09_selection as sel,u09_input as inp,u09_runtime as rt,u09_finalize_only as fin
from b7 import u09_execution as opt,u09_reference as ref,u09_schedule as sch
from b7.u09_artifacts import identity,validate_result
from b7.stage1_contract import ROOT,Structure,digest,canonical
from b7.stage1_metrics import summarize,gate
from test_b7_u08 import metrics

def record(entry=540,holding=35,direction='LONG'):
    s=Structure('USDJPY',direction,0,entry,holding)
    cal=dict(FormalWeekdays=[0,1,2,3,4],FormalDOMBuckets=['D1','D2','D3'],OFFBuckets=[],FormalMonths=list(range(1,13)),OFFMonths=[])
    return dict(CandidateID=s.candidate_id,Symbol=s.symbol,PairRank=1,Schedule=s.definition(),FormalSL=15,FormalTP=None,AnchorWeekday=0,SetName='W1',CalendarFreeze=cal,**cal,U08Status='PASS_U08',U08CandidateSHA256='a'*64,U08CheckpointSHA256='b'*64,U08ProducerImplementationSHA='c'*40,U07SourceIdentity={},U06SourceIdentity={})

def empty_result(r):return sel.assemble(r,[sel.point(p,summarize([]) if p['Valid'] else None) for p in sch.grid(r)])

def points(r=None,changes=None):
    r=record() if r is None else r;changes={} if changes is None else changes
    return [sel.point(p,copy.deepcopy(changes.get(p['PointID'],metrics())) if p['Valid'] else None) for p in sch.grid(r)]

class CheckpointAndFinalize(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.producer='a'*40;self.env=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
        self.identity=identity(self.producer,self.env);self.records=inp.input_config()[1]['Candidates']
        self.local=self.root/'local';self.drive=self.root/'drive'
        rt.init_root(self.local,self.identity,False);rt.init_root(self.drive,self.identity,False)
        for r in self.records:
            result=empty_result(r) # Synthetic null metrics only; no actual candidate price evaluation.
            l=self.local/'jobs'/r['CandidateID'];d=self.drive/'jobs'/r['CandidateID']
            rt.complete_local(l,self.identity,r,result);rt.mirror_job(l,d,self.identity,r)
        self.job=self.drive/'jobs'/self.records[0]['CandidateID']
        self.proof=dict(Status='PASS',ProducerImplementationSHA=self.producer,FinalizerImplementationSHA=self.producer,FinalizerEnvironment={**self.env,'Python':'3.13.16'})
    def audit(self):return fin.audit_source(self.drive,self.proof['FinalizerEnvironment'],self.producer)
    def test_all54(self):self.assertEqual(self.audit()[1]['JobCount'],54)
    def test_missing(self):
        import shutil
        shutil.rmtree(self.job)
        with self.assertRaises(ValueError):self.audit()
    def test_extra_duplicate_directory(self):
        import shutil
        shutil.copytree(self.job,self.job.parent/'duplicate')
        with self.assertRaises(ValueError):self.audit()
    def test_duplicate_candidate_identity(self):
        d=fin.read(self.job/'candidate.json');d['CandidateID']=self.records[1]['CandidateID'];rt.save(self.job/'candidate.json',d)
        with self.assertRaises(ValueError):self.audit()
    def test_corrupt_candidate(self):
        (self.job/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):self.audit()
    def test_corrupt_checkpoint(self):
        (self.job/'checkpoint.json').write_text('{}')
        with self.assertRaises(ValueError):self.audit()
    def test_marker_mismatch(self):
        (self.job/'DRIVE_COMPLETE.json').write_text('{}')
        with self.assertRaises(ValueError):self.audit()
    def test_producer_mismatch(self):
        with self.assertRaises(ValueError):fin.audit_source(self.drive,self.env,'b'*40)
    def test_identity_mutations(self):
        for key in ('U09ConfigSHA256','U09InputSHA256','M1ExactIdentity','U08ResultFreezeSHA','U09SupplementalConditionsFreezeSHA','SupplementalPrespecSHA256','CandidateIDs','FullPrespecSHA256'):
            d=copy.deepcopy(self.identity);d[key]='bad';rt.save(self.drive/'identity.json',d)
            with self.assertRaises(ValueError):self.audit()
        rt.save(self.drive/'identity.json',self.identity)
    def test_patch_allowed(self):self.assertEqual(self.audit()[1]['Status'],'PASS')
    def test_major_minor_rejected(self):
        for version in ('3.14.0','4.13.15'):
            with self.assertRaises(ValueError):fin.audit_source(self.drive,{**self.env,'Python':version},self.producer)
    def test_dependencies_exact(self):
        for key in ('NumPy','pandas'):
            with self.assertRaises(ValueError):fin.audit_source(self.drive,{**self.env,key:'9.0.0'},self.producer)
    def test_normal_resume_patch_exact(self):
        d=copy.deepcopy(self.identity);d['Environment']['Python']='3.13.16'
        with self.assertRaises(ValueError):rt.init_root(self.drive,d,True)
    def test_staging_ignored(self):
        (self.drive/'jobs'/'.incomplete-test').mkdir();self.assertEqual(self.audit()[1]['IgnoredStagingDirectories'],1)
    def test_progress_counts_only(self):
        values=[];fin.audit_source(self.drive,self.env,self.producer,values.append)
        self.assertEqual(values[-1],dict(ProcessedJobs=54,ExpectedJobs=54));self.assertTrue(all(set(v)=={'ProcessedJobs','ExpectedJobs'} for v in values))
    def test_source_unchanged_and_no_recompute(self):
        before={str(p):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()}
        targets=['b7.stage1_input.load_discovery','b7.stage1_input.read_mt5','b7.u06_execution.Engine','b7.u06_execution.evaluate',
                 'b7.u06_selection.select','b7.u09_selection.assemble','b7.u09_selection.neighborhood','b7.u09_selection.ranking_key','b7.u09_selection.decide','b7.u09_schedule.grid','b7.u09_schedule.schedule','b7.u09_execution.evaluate_point','b7.u09_execution.evaluate_points','b7.u09_reference.assemble','b7.u09_reference.schedule','b7.u09_reference.evaluate_points','b7.u09_reference.formal','b7.u09_reference.execute','b7.u09_selection.point','b7.u09_selection.median_pf','b7.u09_execution.calendar_days','b7.stage1_metrics.summarize','b7.stage1_metrics.gate','b7.u09_execution.Engine',
                 'b7.u09_execution.evaluate_candidate','b7.u09_reference.evaluate_candidate','b7.u09_runtime.Engine',
                 'b7.u09_runtime.load_discovery','b7.u09_runtime.evaluate_candidate','b7.stage1_runtime.run_tests']
        with ExitStack() as stack:
            for name in targets:stack.enter_context(patch(name,side_effect=AssertionError('recomputation forbidden')))
            review=fin._finalize(self.drive,self.root/'output',self.proof)
        self.assertFalse(review['JobRecomputation']);self.assertEqual(before,{str(p):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()})
    def test_fresh_required(self):
        with self.assertRaises(FileExistsError):fin._finalize(self.drive,self.local,self.proof)
    def test_no_output_before_all_audit(self):
        (self.job/'candidate.json').write_text('{}');out=self.root/'out'
        with self.assertRaises(ValueError):fin._finalize(self.drive,out,self.proof)
        self.assertFalse(out.exists())
    def test_complete_last(self):
        names=[];save=fin.shared.save_json
        def watch(p,d):names.append(Path(p).name);return save(p,d)
        with patch.object(fin.shared,'save_json',side_effect=watch):fin._finalize(self.drive,self.root/'out',self.proof)
        self.assertEqual(names[-1],'COMPLETE.json')
    def test_deterministic_replay_and_normal_aggregation(self):
        a=self.root/'a';b=self.root/'b';fin._finalize(self.drive,a,self.proof);fin._finalize(self.drive,b,self.proof)
        self.assertEqual({p.name:p.read_bytes() for p in a.iterdir()},{p.name:p.read_bytes() for p in b.iterdir()})
        rt.finalize(self.local,self.drive,self.identity,self.records)
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json','decision_summary.json','shift_summary.json'):
            self.assertEqual((a/n).read_bytes(),(self.local/'final'/n).read_bytes())
    def test_explicit_producer_pin(self):
        with self.assertRaises(ValueError):fin.current_preflight('a'*40,'b'*40)
    def test_separate_approvals(self):
        with self.assertRaises(PermissionError):fin.finalize_from_completed_jobs(self.drive,self.root/'o',self.producer,self.producer,rt.APPROVAL)
        with self.assertRaises(PermissionError):rt.run_formal({},self.producer,self.local,self.drive,fin.APPROVAL)
    def test_interrupted_mirror(self):
        import shutil
        shutil.rmtree(self.job)
        with patch.object(rt.shutil,'copy2',side_effect=OSError('interrupt')):
            with self.assertRaises(OSError):rt.mirror_job(self.local/'jobs'/self.records[0]['CandidateID'],self.job,self.identity,self.records[0])
        self.assertFalse(self.job.exists())
    def test_duplicate_json_keys(self):
        (self.job/'DRIVE_COMPLETE.json').write_text('{"Status":1,"Status":2}')
        with self.assertRaises(ValueError):self.audit()


    def test_normal_resume_all_jobs_no_evaluation(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True)
        source=content/'drive'/'source';shutil.copytree(self.drive,source)
        proof=dict(Status='PASS',Identity=self.identity)
        with patch.object(rt,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(rt.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(rt,'preflight',return_value=proof), patch.object(rt,'Engine',side_effect=AssertionError('no engine')), patch.object(rt,'load_discovery',side_effect=AssertionError('no M1')), patch.object(rt,'evaluate_candidate',side_effect=AssertionError('no recomputation')):
            result=rt.run_formal({},self.producer,'/content/out','/content/drive/source',approval=rt.APPROVAL,resume=True)
        self.assertEqual(result['CompletedJobs'],54)
    def test_public_finalize_no_evaluation_and_portable_paths(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True);shutil.copytree(self.drive,content/'drive'/'source')
        with patch.object(fin,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(fin.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(fin,'current_preflight',return_value=self.proof), patch.object(sel,'assemble',side_effect=AssertionError('no selection')), patch.object(opt,'evaluate_candidate',side_effect=AssertionError('no evaluation')):
            result=fin.finalize_from_completed_jobs('/content/drive/source','/content/out',self.producer,self.producer,fin.APPROVAL)
        self.assertFalse(result['JobRecomputation'])
    def test_source_mutation_stops_without_output(self):
        def progress(p):
            if p['ProcessedJobs']==54:(self.job/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):fin._finalize(self.drive,self.root/'o',self.proof,progress)
        self.assertFalse((self.root/'o').exists())
    def test_archive_member_identity_and_fresh(self):
        import zipfile,hashlib
        rt.finalize(self.local,self.drive,self.identity,self.records)
        final=self.local/'final';destination=self.root/'archive';rt.archive_completed(final,destination)
        with zipfile.ZipFile(destination/'archive.zip') as z:
            self.assertIsNone(z.testzip())
            for name in z.namelist():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest(final/name));self.assertEqual(z.getinfo(name).file_size,(final/name).stat().st_size)
        with self.assertRaises(FileExistsError):rt.archive_completed(final,destination)
    def test_archive_tampering_reject(self):
        rt.finalize(self.local,self.drive,self.identity,self.records)
        (self.local/'final'/'candidate_results.json').write_text('{}')
        with self.assertRaises(ValueError):rt.archive_completed(self.local/'final',self.root/'archive')
    def test_fresh_root_reject(self):
        with self.assertRaises(FileExistsError):rt.init_root(self.drive,self.identity,False)


class SearchAndSchedule(unittest.TestCase):
    def test_grid_exact(self):
        ps=sch.grid(record());self.assertEqual(len(ps),121);self.assertEqual(len({p['PointID'] for p in ps}),121)
        self.assertEqual({p['EntryShiftMinutes'] for p in ps},set(range(-5,6)));self.assertEqual({p['ExitShiftMinutes'] for p in ps},set(range(-5,6)));self.assertIn('+0/+0',[p['PointID'] for p in ps])
    def test_shift_datetime_holding(self):
        r=record()
        for e,x,h in [(1,0,34),(0,1,36),(-5,5,45),(5,-5,25)]:self.assertEqual(sch.schedule(r,e,x)['HoldingMinutes'],h)
    def test_independent_schedule_all_boundaries(self):
        for entry,hold in [(0,30),(1435,30),(540,1440),(540,35),(1410,30),(5,1435)]:
            r=record(entry,hold)
            for p in sch.grid(r):self.assertEqual(p,ref.schedule(r,p['EntryShiftMinutes'],p['ExitShiftMinutes']))
    def test_entry_previous_day(self):self.assertEqual(sch.schedule(record(0,30),-1,0)['InvalidReason'],'ENTRY_DATE_CHANGED')
    def test_entry_next_day(self):self.assertEqual(sch.schedule(record(1435,30),5,0)['InvalidReason'],'ENTRY_DATE_CHANGED')
    def test_exit_offset_changed(self):self.assertEqual(sch.schedule(record(1410,30),0,-1)['InvalidReason'],'EXIT_DAY_OFFSET_CHANGED')
    def test_holding_boundaries(self):
        for hold,e,x,want in [(30,1,0,False),(30,0,0,True),(1440,0,0,True),(1440,0,1,False)]:self.assertEqual(sch.schedule(record(540,hold),e,x)['Valid'],want)
    def test_no_modulo_repair(self):self.assertFalse(sch.schedule(record(0,30),-5,0)['Valid'])
    def test_execution_invalid(self):
        r=record();r['AnchorWeekday']=5;self.assertEqual(sch.schedule(r,0,0)['InvalidReason'],'EXECUTION_SCHEDULE_INVALID')
    def test_no_extension(self):
        for e,x in [(-6,0),(6,0),(0,-6),(0,6),(.5,0)]:
            with self.assertRaises(ValueError):sch.schedule(record(),e,x)
    def test_lineage_not_regenerated(self):
        r=record();out=sel.assemble(r,points(r));self.assertEqual(out['CandidateID'],r['CandidateID']);self.assertEqual(out['AnchorSchedule'],r['Schedule'])
    def test_gate_boundaries(self):
        m=metrics(trades=150,annual=30,losses=10,pf=1.10,positive=3);self.assertTrue(gate(m));self.assertTrue(ref.formal(m))
        for k,v in [('Trades',149),('Losses',9),('AvgPips',0),('AvgPips',None),('PFpips',np.nextafter(1.1,0)),('PFState','INF'),('PFState','UNDEFINED'),('PositiveYearCount',2)]:
            a=copy.deepcopy(m);a[k]=v;self.assertFalse(gate(a));self.assertFalse(ref.formal(a))
        m['Annual']['2022']['Trades']=29;self.assertFalse(gate(m))

class NeighborhoodAndSupplement(unittest.TestCase):
    def n(self,ps,c='+0/+0'):return sel.neighborhood(next(p for p in ps if p['PointID']==c),ps)
    def test_center_and_middle9(self):
        n=self.n(points());self.assertEqual(n['ValidPointCount'],9);self.assertIn('+0/+0',n['NeighborhoodMembers']);self.assertTrue(n['PlateauPASS'])
    def test_search_corner4(self):
        n=self.n(points(),'+5/+5');self.assertEqual(n['ValidPointCount'],4);self.assertTrue(n['PlateauPASS']);self.assertFalse(any('+6' in x for x in n['NeighborhoodMembers']))
    def test_schedule_invalid_excluded_and_three_fails(self):
        n=self.n(points(record(0,30)));self.assertEqual(n['ValidPointCount'],3);self.assertFalse(n['PlateauPASS']);self.assertEqual(n['AllValidMedianAvgPips'],1)
    def test_exact_two_thirds_and_below(self):
        ps=points();members=self.n(ps)['NeighborhoodMembers'];bad=[i for i in members if i!='+0/+0']
        for p in ps:
            if p['PointID'] in bad[:3]:p['FormalPASS']=False
        n=self.n(ps);self.assertEqual(n['FormalPASSCount'],6);self.assertTrue(n['PlateauPASS'])
        next(p for p in ps if p['PointID']==bad[3])['FormalPASS']=False;self.assertFalse(self.n(ps)['PlateauPASS'])
    def test_fail_points_in_avg(self):
        ps=points();members=self.n(ps)['NeighborhoodMembers']
        for p in ps:
            if p['PointID'] in members[:3]:p['Metrics']['AvgPips']=-50;p['FormalPASS']=False
        self.assertEqual(self.n(ps)['AllValidMedianAvgPips'],1)
        for p in ps:
            if p['PointID'] in members[3:5]:p['Metrics']['AvgPips']=0.1;p['FormalPASS']=False
        self.assertEqual(self.n(ps)['AllValidMedianAvgPips'],0.1)
    def test_exact80_and_below(self):
        for v,expected in [(.8,True),(np.nextafter(.8,0),False)]:
            ps=points()
            for p in ps:
                if p['Valid'] and p['PointID']!='+0/+0':p['Metrics']['AvgPips']=v
            self.assertEqual(self.n(ps)['PlateauPASS'],expected)
    def test_center_formal_fail(self):
        ps=points();next(p for p in ps if p['PointID']=='+0/+0')['FormalPASS']=False;self.assertFalse(self.n(ps)['PlateauPASS'])
    def test_no_recursive_plateau(self):
        ps=points()
        for p in ps:p['PlateauPASS']=False
        self.assertTrue(self.n(ps)['PlateauPASS'])
    def test_valid_null_count_and_denominator(self):
        ps=points(changes={'+1/+1':metrics(avg=None,trades=0)});n=self.n(ps)
        self.assertEqual(n['ValidPointCount'],9);self.assertEqual(n['FormalPASSCount'],8);self.assertEqual(n['FormalPASSRatio'],8/9)
        self.assertIsNone(n['AllValidMedianAvgPips']);self.assertFalse(n['PlateauPASS']);self.assertEqual(n['Reason'],'UNDEFINED_VALID_NEIGHBOR_AVG')
    def test_invalid_null_excluded(self):
        ps=points();p=next(p for p in ps if p['PointID']=='+1/+1');p.update(Valid=False,InvalidReason='TEST',Metrics=None,FormalPASS=False)
        n=self.n(ps);self.assertEqual(n['ValidPointCount'],8);self.assertEqual(n['AllValidMedianAvgPips'],1);self.assertTrue(n['PlateauPASS'])
    def test_formal_pass_null_invariant(self):
        ps=points();next(p for p in ps if p['PointID']=='+0/+0')['Metrics']['AvgPips']=None
        with self.assertRaises(ValueError):self.n(ps)
    def test_pf_finite_even_unrounded(self):
        ps=points()[:2];ps[0]['Metrics']['PFpips']=1.123456789;ps[1]['Metrics']['PFpips']=1.987654321
        self.assertEqual(sel.median_pf(ps),1.555555555)
    def test_pf_states_and_null_excluded_fail_finite_included(self):
        ps=points()[:5]
        for p,v in zip(ps,[1,3,None,None,None]):p['Metrics']['PFpips']=v
        ps[0]['FormalPASS']=False;ps[2]['Metrics']['PFState']='INF';ps[3]['Metrics']['PFState']='UNDEFINED'
        self.assertEqual(sel.median_pf(ps),2)
    def test_empty_pf_ranking_stop(self):
        ps=points()[:1];ps[0]['Metrics'].update(PFState='INF',PFpips=None)
        with self.assertRaises(ValueError):sel.median_pf(ps,True)
        self.assertIsNone(sel.median_pf(ps))
    def test_anchor_null_keeps_candidate_and_no_fallback(self):
        r=record();ps=points(r,{'+1/+1':metrics(avg=None,trades=0)});a=sel.assemble(r,ps);b=ref.assemble(r,copy.deepcopy(ps));self.assertEqual(a,b)
        self.assertEqual(a['Decision'],'ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE');self.assertEqual(a['Status'],'PASS_U09');self.assertEqual((a['EntryShiftMinutes'],a['ExitShiftMinutes']),(0,0));self.assertEqual(len(a['Points']),121)
    def test_anchor_three_valid_no_new_baseline_gate(self):
        r=record(0,30);out=sel.assemble(r,points(r));self.assertEqual(out['AnchorNeighborhood']['ValidPointCount'],3);self.assertEqual(out['AnchorBaseline'],1)
    def test_policy_reference_mixed_states(self):
        r=record();ps=points(r)
        for i,p in enumerate(ps):
            if p['Valid']:
                m=p['Metrics'];m['AvgPips']=1+(i%7)/10;m['PFpips']=1.1+(i%5)/10
                if i%11==0:m.update(PFState='INF',PFpips=None);p['FormalPASS']=False
                if i%13==0:m.update(PFState='UNDEFINED',PFpips=None);p['FormalPASS']=False
        self.assertEqual(sel.assemble(r,ps),ref.assemble(r,copy.deepcopy(ps)))

class RankingAndDecision(unittest.TestCase):
    def node(self,e=1,x=0,avg=2,pf=2,annual=2):
        p=next(p for p in points() if p['EntryShiftMinutes']==e and p['ExitShiftMinutes']==x);n=sel.neighborhood(p,points());n.update(AllValidMedianAvgPips=avg,NeighborhoodMedianPFpips=pf);n['CenterMetrics']['MedianAnnualAvgPips']=annual;return n
    def test_priorities(self):
        a=self.node()
        for k,v in [('AllValidMedianAvgPips',1.9),('NeighborhoodMedianPFpips',1.9),('L1',2)]:
            b=copy.deepcopy(a);b[k]=v;self.assertLess(sel.ranking_key(a),sel.ranking_key(b))
        b=copy.deepcopy(a);b['CenterMetrics']['MedianAnnualAvgPips']=1.9;self.assertLess(sel.ranking_key(a),sel.ranking_key(b))
        b=copy.deepcopy(a);b['FixedKey'][3]+=1;self.assertLess(sel.ranking_key(a),sel.ranking_key(b))
    def test_metric_before_anchor_distance(self):self.assertLess(sel.ranking_key(self.node(5,5,3)),sel.ranking_key(self.node(0,0,2)))
    def test_l1(self):
        for e,x,w in [(0,0,0),(1,0,1),(-2,3,5)]:self.assertEqual(self.node(e,x)['L1'],w)
    def test_no_plateau_precedence(self):self.assertEqual(sel.decide([],{'AllValidMedianAvgPips':None})['Decision'],'ANCHOR_RETAINED_NO_1M_PLATEAU')
    def test_best_anchor_no_rank2(self):
        d=sel.decide([self.node(0,0),self.node(1,0,9)],{'AllValidMedianAvgPips':None});self.assertEqual(d['Decision'],'ANCHOR_RETAINED_BEST_IS_ANCHOR')
    def test_undefined_precedence(self):self.assertEqual(sel.decide([self.node()],{'AllValidMedianAvgPips':None})['Decision'],'ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE')
    def test_threshold_exact_and_below(self):
        # Baseline zero yields exactly representable subtraction at the 0.05 boundary.
        for v,want in [(.05,'FINE_TUNED'),(np.nextafter(.05,0),'ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT')]:
            self.assertEqual(sel.decide([self.node(avg=v)],{'AllValidMedianAvgPips':0})['Decision'],want)
    def test_relative_threshold(self):
        d=sel.decide([self.node(avg=20.5)],{'AllValidMedianAvgPips':20});self.assertEqual(d['RequiredImprovement'],.5);self.assertEqual(d['Decision'],'FINE_TUNED')
    def test_negative_zero_absolute_floor(self):
        for v in (-1,0,1):self.assertEqual(sel.decide([self.node()],{'AllValidMedianAvgPips':v})['RequiredImprovement'],.05)
    def test_insufficient_no_rank2(self):
        d=sel.decide([self.node(avg=1.01),self.node(avg=10)],{'AllValidMedianAvgPips':1});self.assertEqual(d['Decision'],'ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT')
    def test_baseline_neighborhood_not_center(self):
        ps=points();next(p for p in ps if p['PointID']=='+0/+0')['Metrics']['AvgPips']=20
        out=sel.assemble(record(),ps);self.assertEqual(out['AnchorBaseline'],1)
    def test_all_fields_and_order_immutable(self):
        r=record();r['OFFMonths']=[7,1];r['FormalMonths']=[m for m in range(1,13) if m not in [7,1]];r['CalendarFreeze'].update(OFFMonths=r['OFFMonths'],FormalMonths=r['FormalMonths']);before=copy.deepcopy(r)
        out=sel.assemble(r,points(r));self.assertEqual(r,before)
        for k in ('FormalSL','FormalTP','FormalWeekdays','FormalDOMBuckets','FormalMonths','OFFMonths','CalendarFreeze'):self.assertEqual(out[k],r[k])
    def test_finetuned_output_and_reference(self):
        r=record();ps=points(r)
        for p in ps:
            if p['Valid']:p['Metrics']['AvgPips']=1+.1*(p['EntryShiftMinutes']+p['ExitShiftMinutes'])
        a=sel.assemble(r,ps);self.assertEqual(a,ref.assemble(r,copy.deepcopy(ps)));self.assertEqual(a['Decision'],'FINE_TUNED');self.assertEqual(a['CandidateID'],r['CandidateID'])

class InputAudit(unittest.TestCase):
    def setUp(self):
        self.d=inp.read(inp.INPUT);self.args=[inp.read(ROOT/p) for p in ['results/b7/u08/drive_checkpoint_audit.json','results/b7/u08/input_identity.json','research_inputs/b7/u08_selected56_input.json','results/b7/u08/u08_result_summary.json','results/b7/u08/u08_archive_manifest.json']]
    def test_frozen54(self):self.assertEqual(len(inp.input_config()[1]['Candidates']),54)
    def test_sha_reject(self):
        with patch.object(inp,'digest',return_value='bad'):
            with self.assertRaises(ValueError):inp.input_config()
    def test_supplement_hash_reject(self):
        digest0=inp.digest
        with patch.object(inp,'digest',side_effect=lambda p:'bad' if p==inp.SUPPLEMENT else digest0(p)):
            with self.assertRaises(ValueError):inp.input_config()
    def test_count_duplicate_replacement(self):
        for mode in range(3):
            d=copy.deepcopy(self.d)
            if mode==0:d['Candidates'].pop()
            elif mode==1:d['Candidates'][-1]=d['Candidates'][0]
            else:d['NoReplacement']=False
            with self.assertRaises(ValueError):inp.validate(d,*self.args)
    def test_fixed_fields_reject(self):
        for k,v in [('U08Status','DROP'),('U08CandidateSHA256','bad'),('U08CheckpointSHA256','bad'),('U08ProducerImplementationSHA','bad'),('FormalSL',999),('FormalTP',999),('FormalWeekdays',[4]),('FormalDOMBuckets',['D2']),('FormalMonths',[]),('OFFMonths',[12]),('CalendarFreeze',{}),('Schedule',{})]:
            d=copy.deepcopy(self.d);d['Candidates'][0][k]=v
            with self.subTest(k=k):
                with self.assertRaises(ValueError):inp.validate(d,*self.args)
    def test_source_producer_reject(self):
        self.d['U08ProducerImplementationSHA']='bad'
        with self.assertRaises(ValueError):inp.validate(self.d,*self.args)

class ExecutionReplay(unittest.TestCase):
    def test_synthetic_nonempty_reference_optimized(self):
        r=record();parts=[];days=[]
        for y in range(2020,2024):
            for n,d in enumerate(pd.bdate_range(f'{y}-02-03',periods=40)):
                days.append(d);idx=pd.date_range(d+pd.Timedelta(minutes=535),periods=46,freq='min')
                prices=np.array([100+(0 if k<20 else (-.03 if n%4==0 else .08))+(k*.0003) for k in range(46)])
                parts.append(pd.DataFrame(dict(Open=prices,High=prices+.001,Low=prices-.001,Close=prices),index=idx))
        bars=pd.concat(parts).sort_index();shifts=[(e,x) for e in (-1,0,1) for x in (-1,0,1)]
        a=opt.evaluate_points(opt.Engine(bars,'USDJPY'),r,[sch.schedule(r,e,x) for e,x in shifts],days);b=ref.evaluate_points(bars,r,shifts,days)
        self.assertEqual(a,b);self.assertTrue(all(len(ts)==160 for ts in a[1].values()));self.assertTrue(a[0]['PlateauCandidateCount']>0)
    def test_calendar_planned_entry_and_overnight(self):
        from test_b7_u06 import bars
        r=record(1435,35);r['FormalWeekdays']=[0];r['FormalMonths']=[8];r['FormalDOMBuckets']=['D3']
        b=bars('2020-08-31 23:30',n=90);p=sch.schedule(r,0,0)
        a=opt.evaluate_points(opt.Engine(b,'USDJPY'),r,[p],['2020-08-31']);z=ref.evaluate_points(b,r,[(0,0)],['2020-08-31']);self.assertEqual(a,z);self.assertEqual(len(a[1]['+0/+0']),1)
        self.assertTrue(a[1]['+0/+0'][0]['ScheduledExitTime'].startswith('2020-09-01'))
        r['FormalMonths']=[9];self.assertEqual(opt.evaluate_points(opt.Engine(b,'USDJPY'),r,[p],['2020-08-31'])[1]['+0/+0'],[])
    def test_discovery_isolation(self):
        from test_b7_u06 import bars
        for y in (2024,2025,2026):
            with self.assertRaises(ValueError):opt.Engine(bars(f'{y}-02-03'),'USDJPY')
            with self.assertRaises(ValueError):ref.evaluate_candidate(bars(f'{y}-02-03'),record(),[])
            with self.assertRaises(ValueError):opt.calendar_days(record(),[f'{y}-02-03'])
    def test_each_valid_point_once_and_no_neighborhood_execution(self):
        from test_b7_u06 import bars
        r=record(0,30);ps=sch.grid(r);calls=[]
        def fake(engine,record,p,dates):calls.append(p['PointID']);return metrics(),[]
        with patch.object(opt,'evaluate_point',side_effect=fake):out,_=opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),r,[])
        self.assertEqual(len(calls),sum(p['Valid'] for p in ps));self.assertEqual(len(calls),len(set(calls)));self.assertEqual(out['NominalPointCount'],121)
    def test_shuffled_points_deterministic(self):
        ps=points();self.assertEqual(sel.assemble(record(),ps),sel.assemble(record(),list(reversed(ps))))
    def test_hashseed_determinism(self):
        script='from test_b7_u09 import *;print(canonical(sel.assemble(record(),points())))';outputs=[]
        for seed in ('1','93'):
            env={**os.environ,'PYTHONHASHSEED':seed,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')+os.pathsep+str(ROOT/'tests')}
            outputs.append(subprocess.check_output([sys.executable,'-c',script],env=env,cwd=ROOT))
        self.assertEqual(*outputs)

from test_b7_u06 import Execution as _Execution
class ExecutionCompatibility(_Execution):
    def compare(self,b,d='LONG',sl=15,tp=10,entry=None,scheduled=None):
        e=b.index[0] if entry is None else pd.Timestamp(entry);x=e+pd.Timedelta(minutes=30) if scheduled is None else pd.Timestamp(scheduled)
        a=opt.Engine(b,'USDJPY').execute(d,e,x,sl,(),tp);self.assertEqual(a,ref.execute(b,'USDJPY',d,e,x,sl,(),tp));return a
del _Execution

class ReleaseGuards(unittest.TestCase):
    def test_supplement_bound(self):
        c,_=inp.input_config();i=identity('a'*40,{})
        self.assertEqual(c['SupplementalPrespecSHA256'],inp.SUPPLEMENT_HASH);self.assertEqual(i['U09SupplementalConditionsFreezeSHA'],inp.SUPPLEMENT_SHA)
    def test_approvals_default_false(self):
        with self.assertRaises(PermissionError):rt.run_formal({},'',None,None)
        with self.assertRaises(PermissionError):fin.finalize_from_completed_jobs(None,None,'','')
    def test_notebooks_guards(self):
        import ast
        for name in ('b7_u09_1m_finetune.ipynb','b7_u09_finalize_only.ipynb'):
            flags=[]
            for c in json.loads((ROOT/'notebooks'/name).read_text())['cells']:
                if c['cell_type']=='code':
                    self.assertEqual(c['outputs'],[])
                    for n in ast.walk(ast.parse(''.join(c['source']))):
                        if isinstance(n,ast.Assign):
                            for t in n.targets:
                                if isinstance(t,ast.Name) and t.id.startswith('RUN_'):flags.append(ast.literal_eval(n.value))
            self.assertTrue(flags);self.assertFalse(any(flags))

class AdditionalCoverage(unittest.TestCase):
    def test_all121_nonempty_kernel_replay(self):
        from test_b7_u06 import bars
        for direction in ('LONG','SHORT'):
            for tp in (None,10):
                r=record(direction=direction);r['FormalTP']=tp;b=bars('2020-02-03 08:50',n=80)
                a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-03']);z=ref.evaluate_candidate(b,r,['2020-02-03']);self.assertEqual(a,z)
                self.assertEqual(a[0]['NominalPointCount'],121);self.assertEqual(a[0]['Status'],'PASS_U09')
    def test_off_calendar_all_dimensions(self):
        from test_b7_u06 import bars
        b=bars('2020-02-03 08:50',n=80)
        for k,v in [('FormalWeekdays',[1]),('FormalDOMBuckets',['D2']),('FormalMonths',[3])]:
            r=record();r[k]=v;a=opt.evaluate_points(opt.Engine(b,'USDJPY'),r,[sch.schedule(r,0,0)],['2020-02-03']);z=ref.evaluate_points(b,r,[(0,0)],['2020-02-03']);self.assertEqual(a,z);self.assertEqual(a[1]['+0/+0'],[])
    def test_formal_output_schema_roundtrip(self):
        r=record();out=empty_result(r);self.assertEqual(validate_result(json.loads(canonical(out)),r),out)
        for k,v in [('Status','DROP'),('FormalSL',999),('FormalEntryMinute',999),('CalendarFreeze',{}),('CandidateID','new')]:
            d=copy.deepcopy(out);d[k]=v
            with self.assertRaises(ValueError):validate_result(d,r)
    def test_normal_environment_full_identity(self):
        i=identity('a'*40,dict(Python='3.13.16',NumPy='2.3.5',pandas='2.2.3'))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'jobs';rt.init_root(root,i,False)
            for k in ('Python','NumPy','pandas'):
                j=copy.deepcopy(i);j['Environment'][k]='different'
                with self.assertRaises(ValueError):rt.init_root(root,j,True)
    def test_complete_output_contains_future_projection(self):
        r=record();o=empty_result(r)
        for k in ('CandidateID','Symbol','PairRank','Direction','FormalSL','FormalTP','CalendarFreeze','FormalEntryMinute','FormalExitMinute','FormalExitDayOffset','FormalHoldingMinutes','EntryShiftMinutes','ExitShiftMinutes','Decision','U08SourceIdentity'):self.assertIn(k,o)
