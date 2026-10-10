import unittest,tempfile,copy,json,os,sys,subprocess,ast
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import u10p_input as inp,u10p_runtime as rt,u10p_finalize_only as fin
from b7 import u10p_execution as opt,u10p_reference as ref
from b7.u10p_artifacts import identity,validate_result,summaries,project_candidate_freeze
from b7.u10_smoke import synthetic_record
from b7.stage1_contract import ROOT,digest,canonical,object_hash,PIPS,SPREAD
from b7.stage1_metrics import summarize
from test_b7_u08 import metrics
from test_b7_u06 import bars

def record(direction='LONG',tp=None):
 r=synthetic_record('USDJPY',direction,20,tp,dict(EntryMinute=540,ExitMinute=570,ExitDayOffset=0,HoldingMinutes=30))
 r.update(E2TradeStreamSHA256=object_hash([]),DiscoveryE2Metrics=summarize([]),FormalEventMode='E2',U10Status='PASS_U10',U10PFixture=True)
 return r

def empty_result(r):
 # Zero trades on synthetic schedules; never formal Candidate performance.
 return opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),r,days=[],calendar={'Events':[]})

class CheckpointAndFinalize(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.producer='a'*40;self.env=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
        self.records=[record() for _ in range(40)]
        for i,r in enumerate(self.records):r['CandidateID']='SYNTHETIC_U10P:'+str(i)
        self.identity=identity(self.producer,self.env);self.identity['CandidateIDs']=[r['CandidateID'] for r in self.records]
        expected={k:v for k,v in self.identity.items() if k!='Environment'}
        def expected_identity(sha):return dict(expected,ImplementationSHA=sha),self.records
        for target,value in [('b7.u10p_finalize_only.expected_identity',expected_identity),('b7.u10p_runtime.input_config',lambda:({},dict(Candidates=self.records))),('b7.u10p_runtime.make_identity',lambda sha,env:dict(self.identity,ImplementationSHA=sha,Environment=env))]:
            p=patch(target,side_effect=value);p.start();self.addCleanup(p.stop)
        self.local=self.root/'local';self.drive=self.root/'drive'
        rt.init_root(self.local,self.identity,False);rt.init_root(self.drive,self.identity,False)
        for r in self.records:
            result=empty_result(r) # Synthetic null metrics only; no actual candidate price evaluation.
            l=self.local/'jobs'/r['CandidateID'];d=self.drive/'jobs'/r['CandidateID']
            rt.complete_local(l,self.identity,r,result);rt.mirror_job(l,d,self.identity,r)
        self.job=self.drive/'jobs'/self.records[0]['CandidateID']
        self.proof=dict(Status='PASS',ProducerImplementationSHA=self.producer,FinalizerImplementationSHA=self.producer,FinalizerEnvironment={**self.env,'Python':'3.13.16'})
    def audit(self):return fin.audit_source(self.drive,self.proof['FinalizerEnvironment'],self.producer)
    def test_all40(self):self.assertEqual(self.audit()[1]['JobCount'],40)
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
        for key in ('U10PConfigSHA256','U10PInputSHA256','M1ExactIdentity','U09ResultFreezeSHA','U10PSupplementalConditionsFreezeSHA','SupplementalPrespecSHA256','CandidateIDs','FullPrespecSHA256'):
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
        self.assertEqual(values[-1],dict(ProcessedJobs=40,ExpectedJobs=40));self.assertTrue(all(set(v)=={'ProcessedJobs','ExpectedJobs'} for v in values))
    def test_source_unchanged_and_no_recompute(self):
        before={str(p):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()}
        targets=['b7.stage1_input.load_discovery','b7.stage1_input.read_mt5','b7.u06_execution.Engine','b7.u06_reference.execute','b7.u10_execution.execution_stream','b7.u10_execution.filter_modes','b7.u10_calendar.EventIndex','b7.stage1_metrics.summarize','b7.stage1_metrics.gate','b7.stage1_runtime.run_tests']
        targets += ['b7.u10p_execution.'+n for n in ['Engine','regenerate','barrier','simulate','describe','adoption','select','evaluate_candidate','summarize','gate_checks']]
        targets += ['b7.u10p_reference.'+n for n in ['regenerate','simulate','describe','adoption','select','evaluate_candidate','summarize','gate_checks']]
        targets += ['b7.u10p_runtime.'+n for n in ['Engine','load_discovery','evaluate_candidate']]
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
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json','protection_summary.json','winner_to_loser_summary.json','mode_summary.json'):
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
        with patch.object(rt,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(rt.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(rt,'preflight',return_value=proof), patch.object(rt.shared,'environment',return_value=self.env), patch.object(rt,'Engine',side_effect=AssertionError('no engine')), patch.object(rt,'load_discovery',side_effect=AssertionError('no M1')), patch.object(rt,'evaluate_candidate',side_effect=AssertionError('no recomputation')):
            result=rt.run_formal({},self.producer,'/content/out','/content/drive/source',approval=rt.APPROVAL,resume=True)
        self.assertEqual(result['CompletedJobs'],40)
    def test_public_finalize_no_evaluation_and_portable_paths(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True);shutil.copytree(self.drive,content/'drive'/'source')
        with patch.object(fin,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(fin.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(fin,'current_preflight',return_value=self.proof), patch.object(opt,'regenerate',side_effect=AssertionError('no filtering')), patch.object(opt,'evaluate_candidate',side_effect=AssertionError('no evaluation')):
            result=fin.finalize_from_completed_jobs('/content/drive/source','/content/out',self.producer,self.producer,fin.APPROVAL)
        self.assertFalse(result['JobRecomputation'])
    def test_source_mutation_stops_without_output(self):
        def progress(p):
            if p['ProcessedJobs']==40:(self.job/'candidate.json').write_text('{}')
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


class ProtectionPaths(unittest.TestCase):
 def run_path(self,changes,direction='LONG',tp=None,remove=(),mode='P1'):
  b=bars(n=31);r=record(direction,tp)
  for i,h,l in changes:b.iloc[i,b.columns.get_loc('High')]=h;b.iloc[i,b.columns.get_loc('Low')]=l
  b=b.drop(b.index[list(remove)])
  with patch.dict(PIPS,USDJPY=1.),patch.dict(SPREAD,USDJPY=0.):
   ts=opt.regenerate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2020-02-04']);self.assertEqual(ts,ref.regenerate(b,r,{'Events':[]},['2020-02-04']))
   r.update(E2TradeStreamSHA256=object_hash(ts),DiscoveryE2Metrics=summarize(ts))
   a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-04'],{'Events':[]});z=ref.evaluate_candidate(b,r,{'Events':[]},['2020-02-04']);self.assertEqual(a,z);validate_result(a,r)
  return a['Modes'][mode]['TradeResults'][0],a
 def test_p1_next_bar_be(self):
  t,_=self.run_path([(0,110,99),(1,105,99)]);self.assertEqual(t['FinalPips'],0);self.assertEqual(t['ActivationBar'],'2020-02-04 09:01:00');self.assertEqual(t['TriggerBar'],'2020-02-04 09:00:00');self.assertTrue(t['ProtectionHit'])
 def test_p2_lock(self):
  t,_=self.run_path([(0,115,99),(1,106,99)],mode='P2');self.assertEqual(t['FinalPips'],5)
 def test_p3_lock(self):
  t,_=self.run_path([(0,120,99),(1,111,99)],mode='P3');self.assertEqual(t['FinalPips'],10)
 def test_trigger_original_sl_same_bar(self):
  t,_=self.run_path([(0,115,80)]);self.assertEqual(t['FinalPips'],-20);self.assertFalse(t['ProtectionActivated']);self.assertEqual(t['ExitReason'],'SL')
 def test_trigger_tp_same_bar(self):
  t,_=self.run_path([(0,130,99)],tp=25);self.assertEqual(t['FinalPips'],25);self.assertFalse(t['ProtectionActivated']);self.assertEqual(t['ExitReason'],'TP')
 def test_active_stop_tp_same_bar(self):
  t,_=self.run_path([(0,110,99),(1,130,99)],tp=25);self.assertEqual(t['FinalPips'],0);self.assertTrue(t['ProtectionHit'])
 def test_missing_next_minute(self):
  t,_=self.run_path([(0,110,99),(3,104,99)],remove=(1,2));self.assertEqual(t['ActivationBar'],'2020-02-04 09:03:00')
 def test_no_next_bar_before_close(self):
  t,_=self.run_path([(30,110,99)]);self.assertFalse(t['ProtectionActivated']);self.assertEqual(t['ActualCloseTime'],'2020-02-04 09:30:00')
 def test_structural_na_equal(self):
  _,a=self.run_path([(0,110,99)],tp=10)
  for m in ('P1','P2','P3'):self.assertFalse(a['Modes'][m]['Applicable']);self.assertFalse(a['Modes'][m]['AdoptionPASS'])
  self.assertEqual(a['FormalProtectionMode'],'P0');self.assertEqual(a['Status'],'PASS_U10P')
 def test_structural_tp15(self):
  _,a=self.run_path([(0,110,99)],tp=15);self.assertTrue(a['Modes']['P1']['Applicable']);self.assertFalse(a['Modes']['P2']['Applicable']);self.assertFalse(a['Modes']['P3']['Applicable'])
 def test_tp_none_applicable(self):
  _,a=self.run_path([])
  for m in ('P1','P2','P3'):self.assertTrue(a['Modes'][m]['Applicable'])
 def test_short_lock(self):
  t,_=self.run_path([(0,101,85),(1,101,94)],direction='SHORT',mode='P2');self.assertEqual(t['FinalPips'],5);self.assertEqual(t['MFEpips'],15);self.assertEqual(t['MAEpips'],1)
 def test_horizon_stops_at_protection_close(self):
  t,_=self.run_path([(0,110,99),(1,105,99),(2,150,50)]);self.assertEqual(t['MFEpips'],10);self.assertEqual(t['MAEpips'],1)
 def test_floor_and_zero_wtl(self):
  t,_=self.run_path([]);self.assertEqual(t['MFEpips'],0);self.assertEqual(t['MAEpips'],0);self.assertFalse(t['WinnerToLoser'])
 def test_giveback_negative_final(self):
  t,_=self.run_path([(0,110,80)],mode='P0');self.assertEqual(t['GivebackPips'],30);self.assertTrue(t['WinnerToLoser']);self.assertTrue(t['Reach050R'])
 def test_just_below_reach(self):
  t,_=self.run_path([(0,np.nextafter(110.,0),80)],mode='P0');self.assertFalse(t['Reach050R']);self.assertFalse(t['WinnerToLoser'])
 def test_giveback_positive_final(self):
  t,_=self.run_path([(0,120,99),(1,106,99)],mode='P2');self.assertEqual(t['GivebackPips'],15)
 def test_spread_entry_raw_high_low(self):
  b=bars(n=31);r=record();ts=opt.regenerate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2020-02-04']);t=opt.simulate(b,r,ts[0],'P0');self.assertEqual(t,ref.simulate(b,r,ts[0],'P0'));self.assertEqual(t['EntryPrice'],100+SPREAD['USDJPY']*PIPS['USDJPY']);self.assertEqual(t['MFEpips'],0);self.assertEqual(t['MAEpips'],(t['EntryPrice']-100)/PIPS['USDJPY'])
 def test_barrier_before_any_simulation(self):
  b=bars(n=31);r=record()
  for module,args in [(opt,(opt.Engine(b,'USDJPY'),r,['2020-02-04'],{'Events':[]})),(ref,(b,r,{'Events':[]},['2020-02-04']))]:
   with patch.object(module,'simulate',side_effect=AssertionError('must not evaluate')):
    with self.assertRaises(ValueError):module.evaluate_candidate(*args)
 def test_metrics_barrier(self):
  b=bars(n=31);r=record();ts=opt.regenerate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2020-02-04']);r['E2TradeStreamSHA256']=object_hash(ts)
  with patch.object(opt,'simulate',side_effect=AssertionError('must not simulate')):
   with self.assertRaises(ValueError):opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-04'],{'Events':[]})
 def test_discovery_reject(self):
  for year in (2024,2025,2026):
   b=bars(f'{year}-02-04')
   with self.assertRaises(ValueError):opt.Engine(b,'USDJPY')
   with self.assertRaises(ValueError):ref.regenerate(b,record(),{'Events':[]},[])
 def test_event_excluded_not_reintroduced(self):
  b=bars(n=31);r=record();c={'Events':[dict(CanonicalEventName='US_NFP',SourceDates=['2020-02-04'],FixedJST='09:00',WindowPlusMinusMinutes=120)]}
  a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-04'],c);self.assertEqual(a,ref.evaluate_candidate(b,r,c,['2020-02-04']))
  self.assertTrue(all(not d['TradeResults'] for d in a['Modes'].values()))
 def test_unknown_mode(self):
  with self.assertRaises(ValueError):opt.simulate(None,None,None,'P4')
 def test_reference_independent(self):
  with patch.object(opt,'simulate',side_effect=AssertionError()),patch.object(opt,'adoption',side_effect=AssertionError()),patch.object(opt,'select',side_effect=AssertionError()),patch.object(opt,'regenerate',side_effect=AssertionError()):
   self.assertEqual(ref.evaluate_candidate(bars(),record(),{'Events':[]},[])['FormalProtectionMode'],'P0')

class Adoption(unittest.TestCase):
 def fixture(self,base=25,mode=20):
  m=metrics(trades=150,annual=30,losses=10,pf=1.10,positive=3);m.update(TotalPips=100,MaxDDPips=20,MedianAnnualAvgPips=2)
  return dict(Metrics=m,WinnerToLoserCount=base),dict(Metrics=copy.deepcopy(m),WinnerToLoserCount=mode,U01GatePASS=True,Applicable=True)
 def compare(self,b,d):
  a=opt.adoption(copy.deepcopy(b),copy.deepcopy(d));self.assertEqual(a,ref.adoption(copy.deepcopy(b),copy.deepcopy(d)));return a
 def test_exact_thresholds(self):
  for b,d,expected in [(25,20,True),(24,19,True),(30,25,False),(25,21,False),(0,0,False),(5,6,False)]:
   base,mode=self.fixture(b,d);a=self.compare(base,mode);self.assertEqual(a['AdoptionPASS'],expected);self.assertEqual(a['ReductionCount'],b-d);self.assertEqual(a['ReductionFraction'],(b-d)/b if b else None)
 def test_worse_each_metric(self):
  for key in ['TotalPips','PFpips','MedianAnnualAvgPips','PositiveYearCount','MaxDDPips']:
   b,d=self.fixture();d['Metrics'][key]=np.nextafter(d['Metrics'][key],np.inf if key=='MaxDDPips' else -np.inf);self.assertFalse(self.compare(b,d)['AdoptionPASS'])
 def test_invariant_null_inf(self):
  for target in ('base','mode'):
   for k,v in [('PFState','INF'),('PFpips',None),('MedianAnnualAvgPips',None)]:
    b,d=self.fixture();(b if target=='base' else d)['Metrics'][k]=v
    for module in (opt,ref):
     with self.assertRaises(ValueError):module.adoption(b,d)
 def test_na_and_u01_fail(self):
  for key in ['Applicable','U01GatePASS']:
   b,d=self.fixture();d[key]=False;self.assertFalse(self.compare(b,d)['AdoptionPASS'])
 def test_gate_boundaries(self):
  m=self.fixture()[0]['Metrics'];self.assertTrue(all(opt.gate_checks(m).values()))
  for k,v in [('Trades',149),('Losses',9),('AvgPips',0),('PFpips',np.nextafter(1.1,0)),('PFState','INF'),('PFState','UNDEFINED'),('PositiveYearCount',2)]:
   x=copy.deepcopy(m);x[k]=v;self.assertEqual(opt.gate_checks(x),ref.gate_checks(x));self.assertFalse(all(opt.gate_checks(x).values()))
  for y in range(2020,2024):
   x=copy.deepcopy(m);x['Annual'][str(y)]['Trades']=29;self.assertFalse(all(opt.gate_checks(x).values()))
 def test_ranking_all_priorities(self):
  b,d=self.fixture();base=self.compare(b,d)
  for key,delta in [('ReductionCount',1),('MaxDDPips',-1),('PFpips',1),('TotalPips',1),('tie',0)]:
   modes={n:copy.deepcopy(base) for n in ('P1','P2','P3')}
   if key=='ReductionCount':modes['P3'][key]+=delta
   elif key!='tie':modes['P3']['Metrics'][key]+=delta
   a=opt.select(modes);self.assertEqual(a,ref.select(modes));self.assertEqual(a[1],'P1' if key=='tie' else 'P3')
 def test_fallback_no_drop(self):
  a=empty_result(record());self.assertEqual(a['FormalProtectionMode'],'P0');self.assertEqual(a['Status'],'PASS_U10P')
 def test_mode_specific_dd_order(self):
  ts=[dict(CloseTime='2020-02-04 10:00',EntryTime='2020-02-04 09:00',FixedKey=['a'],Pips=-5),dict(CloseTime='2020-02-04 09:30',EntryTime='2020-02-04 09:10',FixedKey=['b'],Pips=10)]
  self.assertEqual(summarize(ts)['MaxDDPips'],5);self.assertEqual(summarize(ts),summarize(ts[::-1]))

class InputAndRelease(unittest.TestCase):
 def test_input40(self):
  c,d=inp.input_config();self.assertEqual(d['CandidateCount'],40);self.assertFalse(any(r['Symbol']=='AUDUSD' for r in d['Candidates']));self.assertEqual(digest(inp.INPUT),inp.INPUT_SHA)
 def test_duplicate_order_reject(self):
  for dup in [False,True]:
   d=inp.read(inp.INPUT)
   if dup:d['Candidates'][1]=d['Candidates'][0]
   else:d['Candidates'].reverse()
   with self.assertRaises(ValueError):inp.validate(d)
 def test_future_projection(self):
  r=record();a=empty_result(r);p=project_candidate_freeze(r,a,'a'*64,'b'*64,'c'*40,'d'*64,'e'*64);self.assertEqual(p['FormalProtectionMode'],'P0');self.assertEqual(p['SelectedModeDiscoveryMetrics'],a['Modes']['P0']['Metrics'])
 def test_summary_order_determinism(self):
  r=record();a=empty_result(r);b=copy.deepcopy(a);b['CandidateID']='other';self.assertEqual(summaries([a,b]),summaries([b,a]))
 def test_no_import_execution(self):
  script="import b7.stage1_input as s;s.read_mt5=lambda *a,**k:(_ for _ in ()).throw(AssertionError());import b7.u10p_runtime,b7.u10p_finalize_only;print('NO_RUN')"
  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')};self.assertIn(b'NO_RUN',subprocess.check_output([sys.executable,'-c',script],env=env))
 def test_notebook_flags_false(self):
  for name in ['b7_u10p_profit_protection.ipynb','b7_u10p_finalize_only.ipynb']:
   flags=[]
   for c in json.loads((ROOT/'notebooks'/name).read_text())['cells']:
    if c['cell_type']!='code':continue
    self.assertEqual(c['outputs'],[])
    for n in ast.walk(ast.parse(''.join(c['source']))):
     if isinstance(n,ast.Assign):
      for t in n.targets:
       if isinstance(t,ast.Name) and t.id.startswith('RUN_'):flags.append(ast.literal_eval(n.value))
   self.assertTrue(flags);self.assertFalse(any(flags))

for key in ['CandidateID','Symbol','Direction','FormalEntryMinute','FormalExitMinute','FormalHoldingMinutes','FormalSL','FormalTP','CalendarFreeze','FormalWeekdays','FormalDOMBuckets','FormalMonths','E2EventSet','DiscoveryE2Metrics','E2TradeStreamSHA256','U10Status','U10CandidateSHA256','U10CandidateObjectSHA256','U10CheckpointSHA256','U10ProducerImplementationSHA','EventCalendarSHA256','CalendarSourceCommit','U09Status','U08SourceIdentity','U07SourceIdentity','U06SourceIdentity']:
 def check(self,k=key):
  d=inp.read(inp.INPUT);d['Candidates'][0][k]='MUTATED'
  with self.assertRaises(ValueError):inp.validate(d)
 setattr(InputAndRelease,'test_mutation_'+key,check)
for key in ['CandidateCount','NoReplacement','FormalEventMode','U10PPerformanceEvaluated','FrozenU10PContract','SourceArchive','SourceManifest']:
 def check(self,k=key):
  d=inp.read(inp.INPUT);d[k]='MUTATED'
  with self.assertRaises(ValueError):inp.validate(d)
 setattr(InputAndRelease,'test_top_'+key,check)
class AdditionalIntegrity(unittest.TestCase):
 def test_random_paths_exact(self):
  rng=np.random.default_rng(19241)
  for direction in ('LONG','SHORT'):
   for tp in (None,10,15,25):
    for _ in range(4):
     b=bars(n=31);b['High']=100+rng.uniform(0,25,len(b));b['Low']=100-rng.uniform(0,25,len(b));b=b.drop(b.index[[3,5,11]]);r=record(direction,tp)
     with patch.dict(PIPS,USDJPY=1.),patch.dict(SPREAD,USDJPY=0.):
      ts=ref.regenerate(b,r,{'Events':[]},['2020-02-04']);r.update(E2TradeStreamSHA256=object_hash(ts),DiscoveryE2Metrics=summarize(ts))
      self.assertEqual(opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-04'],{'Events':[]}),ref.evaluate_candidate(b,r,{'Events':[]},['2020-02-04']))
 def test_hashseed_determinism(self):
  outputs=[]
  for seed in ('1','97'):
   env={**os.environ,'PYTHONHASHSEED':seed,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')+os.pathsep+str(ROOT/'tests')}
   outputs.append(subprocess.check_output([sys.executable,'-c','from test_b7_u10p import *;print(canonical(empty_result(record())))'],env=env,cwd=ROOT))
  self.assertEqual(*outputs)
 def test_completed_preflight_no_m1_smoke_tests(self):
  env=dict(Python='3.13.16',NumPy='2.3.5',pandas='2.2.3')
  def git(*args):return 'a'*40 if args==('rev-parse','HEAD') else ''
  original=rt.read
  def read(p):return {'Status':'PASS'} if Path(p).name in ('test_results.json','smoke_results.json') else original(p)
  with patch.object(rt.shared,'git',side_effect=git),patch.object(rt.shared,'release_manifest'),patch.object(rt.shared,'environment',return_value=env),patch.object(rt,'read',side_effect=read),patch.object(rt,'audit_inputs',side_effect=AssertionError('M1 forbidden')),patch.object(rt.shared,'run_tests',side_effect=AssertionError('test execution forbidden')),patch('b7.u10p_smoke.run_smoke',side_effect=AssertionError('smoke forbidden')):
   p=rt.preflight({},'a'*40,completed_only=True)
  self.assertFalse(p['Smoke']['JobRecomputation'])
 def test_fixed_fields_and_stream_corruption(self):
  r=record();out=empty_result(r)
  for k in ('FormalSL','FormalTP','FormalEntryMinute','FormalWeekdays','CalendarFreeze','E2TradeStreamSHA256'):
   d=copy.deepcopy(out);d[k]='changed'
   with self.assertRaises(ValueError):validate_result(d,r)
  d=copy.deepcopy(out);d['Modes']['P0']['TradeStreamSHA256']='0'*64
  with self.assertRaises(ValueError):validate_result(d,r)
 def test_40_candidates_121_files(self):
  f=CheckpointAndFinalize();f.setUp()
  try:self.assertEqual(len(f.audit()[1]['TrustedFiles']),121)
  finally:f.doCleanups()
class FourYearIntegration(unittest.TestCase):
 def test_nonempty_adoption_and_metrics_exact(self):
  frames=[];days=[]
  for year in range(2020,2024):
   for i,day in enumerate(pd.bdate_range(f'{year}-02-03',periods=40)):
    b=bars(str(day+pd.Timedelta(hours=9)),n=31);days.append(day)
    if i<5:
     b.iloc[0,b.columns.get_loc('High')]=110;b.iloc[1,b.columns.get_loc('Low')]=80
    elif i<8:b.iloc[0,b.columns.get_loc('Low')]=80
    else:b.iloc[0,b.columns.get_loc('High')]=125
    frames.append(b)
  b=pd.concat(frames);r=record(tp=25)
  with patch.dict(PIPS,USDJPY=1.),patch.dict(SPREAD,USDJPY=0.):
   ts=ref.regenerate(b,r,{'Events':[]},days);r.update(E2TradeStreamSHA256=object_hash(ts),DiscoveryE2Metrics=summarize(ts))
   a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,days,{'Events':[]});z=ref.evaluate_candidate(b,r,{'Events':[]},days)
  self.assertEqual(a,z);validate_result(a,r);self.assertEqual(a['FormalProtectionMode'],'P1');self.assertEqual(a['Status'],'PASS_U10P');self.assertEqual(a['Modes']['P0']['WinnerToLoserCount'],20);self.assertEqual(a['Modes']['P1']['ReductionCount'],20);self.assertEqual(a['Modes']['P1']['Metrics']['Losses'],12)
  for m in a['Modes'].values():self.assertEqual(m['Metrics']['Trades'],160)
class P0Compatibility(unittest.TestCase):
 def test_frozen_u10_stream_exact(self):
  from b7 import u10_execution as old
  from b7.u10_calendar import audit_calendar
  for direction in ['LONG','SHORT']:
   for tp in [None,10,25]:
    b=bars(n=35);r=record(direction,tp);c=audit_calendar()
    prior=old.evaluate_candidate(old.Engine(b,'USDJPY'),r,['2020-02-04'],c)[1]['Streams']['E2']
    current=opt.regenerate(opt.Engine(b,'USDJPY'),r,c,['2020-02-04'])
    self.assertEqual(prior,current);self.assertEqual(object_hash(prior),object_hash(current));self.assertEqual([t['TradeID'] for t in prior],[t['TradeID'] for t in current])
 def test_excluded_trade_execution_not_called(self):
  b=bars(n=31);r=record();c={'Events':[dict(CanonicalEventName='US_NFP',SourceDates=['2020-02-04'],FixedJST='09:00',WindowPlusMinusMinutes=120)]};engine=opt.Engine(b,'USDJPY')
  with patch.object(engine,'execute',side_effect=AssertionError('excluded trade')),patch.object(ref,'execute',side_effect=AssertionError('excluded trade')):
   self.assertEqual(opt.regenerate(engine,r,c,['2020-02-04']),[]);self.assertEqual(ref.regenerate(b,r,c,['2020-02-04']),[])
