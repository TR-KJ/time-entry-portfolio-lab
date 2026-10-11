import unittest,tempfile,copy,json,os,ast
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import u11_input as inp,u11_runtime as rt,u11_finalize_only as fin
from b7 import u11_execution as opt,u11_reference as ref,u11_metrics as met,u11_data as data
from b7.u11_artifacts import identity,validate_result,summaries,project_monitor
from b7.u11_smoke import synthetic_record
from b7.stage1_contract import ROOT,digest,canonical,object_hash,PIPS,SPREAD
from test_b7_u06 import bars as old_bars

def bars(start='2024-02-06 09:00',n=35):return old_bars(start,n)
def record(direction='LONG',tp=None,mode='P0'):
 r=synthetic_record('USDJPY',direction,mode,540,570,0,tp);r['FormalSL']=20
 return r

def empty_result(r):
 return opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),r,days=[],calendar={'Events':[]},implementation_sha='a'*40)[0]

class CheckpointAndFinalize(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.producer='a'*40;self.env=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
        self.records=[record() for _ in range(40)]
        for i,r in enumerate(self.records):r['CandidateID']='SYNTHETIC_U11:'+str(i)
        self.identity=identity(self.producer,self.env);self.identity['CandidateIDs']=[r['CandidateID'] for r in self.records]
        expected={k:v for k,v in self.identity.items() if k!='Environment'}
        def expected_identity(sha):return dict(expected,ImplementationSHA=sha),self.records
        for target,value in [('b7.u11_finalize_only.expected_identity',expected_identity),('b7.u11_runtime.input_config',lambda:({},dict(Candidates=self.records))),('b7.u11_runtime.make_identity',lambda sha,env:dict(self.identity,ImplementationSHA=sha,Environment=env))]:
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
        for key in ('U11ConfigSHA256','U11InputSHA256','CandidateFreezeSHA','CandidateFingerprints','U11ContractSHA256','M1ExactIdentity','U09ResultFreezeSHA','FrozenU11Contract','SupplementalPrespecSHA256','CandidateIDs','FullPrespecSHA256'):
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
        targets += ['b7.u11_execution.'+n for n in ['Engine','executable','filter_e2','simulate','evaluate_candidate','summarize','checks','calendar_days']]
        targets += ['b7.u11_reference.'+n for n in ['executable','filter_e2','simulate','evaluate_candidate','summarize','checks','calendar_days']]
        targets += ['b7.u11_metrics.'+n for n in ['metric_block','summarize','checks','diagnostics']]
        targets += ['b7.u11_data.load_validation','b7.u11_engine.Engine','b7.u11_reference.execute']
        targets += ['b7.u11_runtime.'+n for n in ['Engine','load_validation','evaluate_candidate']]
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
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json','status_summary.json','sample_summary.json','formal_check_summary.json','event_summary.json','diagnostic_summary.json'):
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
        with patch.object(rt,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(rt.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(rt,'preflight',return_value=proof), patch.object(rt.shared,'environment',return_value=self.env), patch.object(rt,'Engine',side_effect=AssertionError('no engine')), patch.object(rt,'load_validation',side_effect=AssertionError('no M1')), patch.object(rt,'evaluate_candidate',side_effect=AssertionError('no recomputation')):
            result=rt.run_formal({},self.producer,'/content/out','/content/drive/source',approval=rt.APPROVAL,resume=True)
        self.assertEqual(result['CompletedJobs'],40)
    def test_public_finalize_no_evaluation_and_portable_paths(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True);shutil.copytree(self.drive,content/'drive'/'source')
        with patch.object(fin,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(fin.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(fin,'current_preflight',return_value=self.proof), patch.object(opt,'executable',side_effect=AssertionError('no filtering')), patch.object(opt,'evaluate_candidate',side_effect=AssertionError('no evaluation')):
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
  b=bars(n=31);r=record(direction,tp,mode);r['CandidateID']='SYNTHETIC_U11_PATH'
  for i,h,l in changes:b.iloc[i,b.columns.get_loc('High')]=h;b.iloc[i,b.columns.get_loc('Low')]=l
  b=b.drop(b.index[list(remove)])
  with patch.dict(PIPS,USDJPY=1.),patch.dict(SPREAD,USDJPY=0.):
   a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2024-02-06'],implementation_sha='a'*40)
   z,zd=ref.evaluate_candidate(b,r,{'Events':[]},['2024-02-06'],implementation_sha='a'*40)
   self.assertEqual(a,z);self.assertEqual(ad,zd);validate_result(a,r)
  return a['TradeResults'][0],a
 def test_p1_next_bar_be(self):
  t,_=self.run_path([(0,110,99),(1,105,99)]);self.assertEqual(t['FinalPips'],0);self.assertEqual(t['ActivationBar'],'2024-02-06 09:01:00');self.assertEqual(t['TriggerBar'],'2024-02-06 09:00:00')
 def test_p2_lock(self):self.assertEqual(self.run_path([(0,115,99),(1,106,99)],mode='P2')[0]['FinalPips'],5)
 def test_p3_lock(self):self.assertEqual(self.run_path([(0,120,99),(1,111,99)],mode='P3')[0]['FinalPips'],10)
 def test_trigger_original_sl_same_bar(self):
  t,_=self.run_path([(0,115,80)]);self.assertEqual(t['FinalPips'],-20);self.assertFalse(t['ProtectionActivated'])
 def test_trigger_tp_same_bar(self):
  t,_=self.run_path([(0,130,99)],tp=25);self.assertEqual(t['FinalPips'],25);self.assertFalse(t['ProtectionActivated'])
 def test_active_stop_tp_same_bar(self):
  t,_=self.run_path([(0,110,99),(1,130,99)],tp=25);self.assertEqual(t['FinalPips'],0);self.assertTrue(t['ProtectionHit'])
 def test_missing_next_minute(self):self.assertEqual(self.run_path([(0,110,99),(3,104,99)],remove=(1,2))[0]['ActivationBar'],'2024-02-06 09:03:00')
 def test_no_next_bar_before_close(self):self.assertFalse(self.run_path([(30,110,99)])[0]['ProtectionActivated'])
 def test_structural_conflict_hard_stop(self):
  for mode,tp in [('P1',10),('P2',15),('P3',20),('P2',10)]:
   with patch.object(opt,'executable',side_effect=AssertionError('must not evaluate')):
    with self.assertRaises(ValueError):opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),record(tp=tp,mode=mode),{'Events':[]},[])
   with self.assertRaises(ValueError):ref.evaluate_candidate(bars(),record(tp=tp,mode=mode),{'Events':[]},[])
 def test_short_lock(self):
  t,_=self.run_path([(0,101,85),(1,101,94)],direction='SHORT',mode='P2');self.assertEqual((t['FinalPips'],t['MFEpips'],t['MAEpips']),(5,15,1))
 def test_horizon_stops_at_protection_close(self):
  t,_=self.run_path([(0,110,99),(1,105,99),(2,150,50)]);self.assertEqual((t['MFEpips'],t['MAEpips']),(10,1))
 def test_floor_zero_and_no_wtl(self):
  t,_=self.run_path([]);self.assertEqual((t['MFEpips'],t['MAEpips']),(0,0));self.assertFalse(t['WinnerToLoser'])
 def test_wtl_exact_threshold_negative(self):
  t,_=self.run_path([(0,110,80)],mode='P0');self.assertEqual(t['GivebackPips'],30);self.assertTrue(t['WinnerToLoser'])
 def test_wtl_below_threshold(self):self.assertFalse(self.run_path([(0,np.nextafter(110.,0),80)],mode='P0')[0]['WinnerToLoser'])
 def test_positive_giveback(self):self.assertEqual(self.run_path([(0,120,99),(1,106,99)],mode='P2')[0]['GivebackPips'],15)
 def test_selected_mode_only(self):
  original=opt.simulate;seen=[]
  def watch(b,r,t,mode):seen.append(mode);return original(b,r,t,mode)
  with patch.object(opt,'simulate',side_effect=watch):self.run_path([],mode='P2')
  self.assertEqual(seen,['P2'])
 def test_spread_entry_raw_high_low(self):
  r=record();b=bars(n=31);ts,_=opt.executable(opt.Engine(b,'USDJPY'),r,['2024-02-06']);t=opt.simulate(b,r,ts[0],'P0')
  self.assertEqual(t,ref.simulate(b,r,ts[0],'P0'));self.assertEqual(t['EntryPrice'],100+SPREAD['USDJPY']*PIPS['USDJPY']);self.assertEqual(t['MFEpips'],0)
 def test_reference_independence(self):
  with ExitStack() as stack:
   for n in ('calendar_days','executable','filter_e2','simulate','summarize','checks','diagnostics','evaluate_candidate'):stack.enter_context(patch.object(opt,n,side_effect=AssertionError('optimized call')))
   for n in ('summarize','checks','diagnostics','metric_block'):stack.enter_context(patch.object(met,n,side_effect=AssertionError('shared performance call')))
   z,_=ref.evaluate_candidate(bars(),record(),{'Events':[]},['2024-02-06'],implementation_sha='a'*40)
  self.assertEqual(z['ValidationStatus'],'INSUFFICIENT_SAMPLE')
 def test_trade_id_stable_across_modes(self):
  ids=[]
  for mode in ('P0','P1','P2','P3'):ids.append(self.run_path([(0,120,99),(1,100,99)],mode=mode)[0]['TradeID'])
  self.assertEqual(len(set(ids)),1)
 def test_formal_work_guard(self):
  r=record();r['CandidateID']='B7S1:SYNTHETIC_GUARD'
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(PermissionError):opt.evaluate_candidate(None,r)
   with self.assertRaises(PermissionError):ref.evaluate_candidate(None,r)

class Execution(unittest.TestCase):
 def compare(self,b,d='LONG',sl=15,tp=10,entry=None,scheduled=None):
  e=b.index[0] if entry is None else pd.Timestamp(entry);x=e+pd.Timedelta(minutes=30) if scheduled is None else pd.Timestamp(scheduled)
  a=opt.Engine(b,'USDJPY').execute(d,e,x,sl,(),tp);z=ref.execute(b,'USDJPY',d,e,x,sl,(),tp);self.assertEqual(a,z);return a
 def test_hits_same_bar_sl_first(self):
  for direction in ('LONG','SHORT'):
   b=bars();b.iloc[2,b.columns.get_loc('Low')]=99;b.iloc[2,b.columns.get_loc('High')]=101;self.assertEqual(self.compare(b,direction)['ExitReason'],'SL')
 def test_inclusive_entry_exit(self):
  for i in (0,30):
   b=bars();b.iloc[i,b.columns.get_loc('High')]=101;self.assertEqual(self.compare(b)['CloseTime'],str(b.index[i]))
 def test_exit_fallback_zero_through_four(self):
  for delay in range(5):
   b=bars();b=b.drop(b.index[30:30+delay]);self.assertEqual(self.compare(b)['ExitDelayMinutes'],delay)
 def test_exit_plus_five_reject_even_stop(self):
  b=bars(n=36);b.iloc[0,b.columns.get_loc('Low')]=99;b=b.drop(b.index[30:35]);self.assertEqual(self.compare(b)['Status'],'MISSING_EXIT')
 def test_missing_entry(self):self.assertEqual(self.compare(bars().iloc[1:],entry='2024-02-06 09:00')['Status'],'MISSING_ENTRY')
 def test_gap_no_interpolation(self):self.assertEqual(self.compare(bars().drop(bars().index[5:10]))['MissingPathMinutes'],5)
 def test_holding_boundaries(self):
  for hold in (29,1441):self.assertEqual(self.compare(bars(),scheduled=bars().index[0]+pd.Timedelta(minutes=hold))['Status'],'INVALID_HOLD')
 def test_overnight(self):self.assertEqual(self.compare(bars('2024-02-06 23:45'))['Status'],'OK')
 def test_year_end_stop(self):
  for day in ('2024-12-25','2025-01-01','2025-01-03'):self.assertEqual(self.compare(bars(day+' 09:00'))['Status'],'YEAR_END_STOP')
 def test_boundary(self):self.assertEqual(self.compare(bars(),scheduled='2026-01-01')['Status'],'PERIOD_BOUNDARY')
 def test_no_epsilon(self):
  b=bars();entry=100+SPREAD['USDJPY']*PIPS['USDJPY'];b['Low']=np.nextafter(entry-15*PIPS['USDJPY'],np.inf)
  self.assertEqual(self.compare(b,tp=None)['ExitReason'],'TimeExit')
 def test_chosen_sunday_fallback_reject(self):
  b=bars('2024-02-09 23:59',n=1443);b=b.drop(b.index[1440]);self.assertEqual(self.compare(b,scheduled='2024-02-10 23:59')['Status'],'WEEKEND_BOUNDARY')
 def test_owned_validation_engine(self):
  b=bars();e=opt.Engine(b,'USDJPY');b.iloc[0,0]=999;self.assertNotEqual(e.bars.iloc[0,0],999)

class Calendar(unittest.TestCase):
 def test_saved_filters(self):
  r=record();r.update(FormalWeekdays=[1],FormalDOMBuckets=['D1'],FormalMonths=[2])
  a=opt.calendar_days(r);self.assertEqual(a,ref.calendar_days(r));self.assertTrue(all(d.weekday()==1 and d.month==2 and d.day<=10 for d in a));self.assertTrue(all(2024<=d.year<=2025 for d in a))
 def test_event_planned_window_even_early_sl(self):
  r=record();b=bars();b.iloc[0,b.columns.get_loc('Low')]=99
  c={'Events':[dict(CanonicalEventName='US_NFP',SourceDates=['2024-02-06'],FixedJST='09:30',WindowPlusMinusMinutes=0)]}
  a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,c,['2024-02-06'],implementation_sha='a'*40)
  z,zd=ref.evaluate_candidate(b,r,c,['2024-02-06'],implementation_sha='a'*40)
  self.assertEqual((a,ad),(z,zd));self.assertEqual(a['EventDiagnostics']['E0ExecutableTrades'],1);self.assertEqual(a['EventDiagnostics']['E2Trades'],0)
 def test_unique_exclusion_multiple_events(self):
  r=record();b=bars();c={'Events':[dict(CanonicalEventName=n,SourceDates=['2024-02-05' if n=='FOMC' else '2024-02-06'],FixedJST='09:00',WindowPlusMinusMinutes=0) for n in ('US_NFP','FOMC')]}
  a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,c,['2024-02-06'],implementation_sha='a'*40)
  z,zd=ref.evaluate_candidate(b,r,c,['2024-02-06'],implementation_sha='a'*40)
  self.assertEqual((a,ad),(z,zd));e=a['EventDiagnostics'];self.assertEqual((e['RemovedTrades'],e['MultiEventOverlapTradeCount']),(1,1));self.assertEqual(sum(e['RemovedByEvent'].values()),2)
 def test_no_missing_entry_in_e0(self):
  r=record();a,_=opt.evaluate_candidate(opt.Engine(bars().iloc[1:],'USDJPY'),r,{'Events':[]},['2024-02-06'],implementation_sha='a'*40);self.assertEqual(a['EventDiagnostics']['E0ExecutableTrades'],0)
 def test_wrong_event_set_reject(self):
  r=record();r['E2EventSet']=[]
  with self.assertRaises(ValueError):opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),r,{'Events':[]},[])
 def test_duplicate_dates_reject(self):
  with self.assertRaises(ValueError):opt.calendar_days(record(),['2024-02-06']*2)

class Metrics(unittest.TestCase):
 def trade(self,p,entry='2024-02-06 09:00:00',close='2024-02-06 09:30:00',key=0):return dict(Pips=p,EntryTime=entry,CloseTime=close,FixedKey=[key])
 def fixture(self):
  ts=[self.trade(p,entry=f'{y}-02-06 09:00:00',close=f'{y}-02-06 09:30:00',key=i) for y in (2024,2025) for i,p in enumerate([2.]*30+[-1.]*5)]
  return met.summarize(ts)
 def compare(self,m,r=None):
  r=record() if r is None else r;a=met.checks(m,r);self.assertEqual(a,ref.checks(m,r));return a
 def test_exact_sample_boundaries(self):self.assertEqual(self.compare(self.fixture())[2],'PASS')
 def test_every_sample_failure_precedes_formal(self):
  for year,key,value in [('Annual2024','Trades',29),('Annual2025','Trades',29),('Combined','Trades',69),('Annual2024','Losses',4),('Annual2025','Losses',4)]:
   m=self.fixture();m[year][key]=value;m['Combined']['AvgPips']=-1;self.assertEqual(self.compare(m)[2],'INSUFFICIENT_SAMPLE')
 def test_combined70_annual30_40(self):
  m=self.fixture();m['Annual2024']['Trades']=30;m['Annual2025']['Trades']=40;self.assertEqual(self.compare(m)[2],'PASS')
 def test_each_formal_failure(self):
  for block,key,value in [('Annual2024','TotalPips',0),('Annual2025','TotalPips',0),('Combined','AvgPips',0),('Combined','PFpips',np.nextafter(1.1,0)),('Combined','MaxDDPips',np.nextafter(150.,np.inf))]:
   m=self.fixture();m[block][key]=value;self.assertEqual(self.compare(m)[2],'FAIL')
 def test_exact_pf_dd_boundaries(self):
  m=self.fixture();m['Combined'].update(PFpips=1.1,MaxDDPips=150.);self.assertEqual(self.compare(m)[2],'PASS')
 def test_pf_states_no_sentinel(self):
  for values,state,pf in [([], 'UNDEFINED',None),([0.], 'UNDEFINED',None),([1.],'INF',None),([-1.],'FINITE',0.)]:
   m=met.metric_block(values);self.assertEqual((m['PFState'],m['PFpips']),(state,pf));self.assertEqual(m,ref.metric_block(values))
 def test_sufficient_nonfinite_invariant(self):
  for state in ('INF','UNDEFINED'):
   m=self.fixture();m['Combined'].update(PFState=state,PFpips=None)
   with self.assertRaises(ValueError):met.checks(m,record())
   with self.assertRaises(ValueError):ref.checks(m,record())
 def test_24_months_empty_metrics(self):
  m=met.summarize([]);self.assertEqual(m,ref.summarize([]));self.assertEqual(len(m['Monthly']),24);self.assertTrue(all(x['Trades']==0 and x['AvgPips'] is None for x in m['Monthly'].values()))
 def test_entry_year_month_and_combined_dd_no_reset(self):
  ts=[self.trade(-5,'2024-12-20 23:50:00','2024-12-21 00:20:00'),self.trade(-7,'2025-01-06 09:00:00','2025-01-06 09:30:00')];m=met.summarize(ts);self.assertEqual(m,ref.summarize(ts));self.assertEqual(m['Combined']['MaxDDPips'],12);self.assertEqual(m['Annual2025']['MaxDDPips'],7);self.assertEqual(m['Monthly']['2024-12']['TotalPips'],-5)
 def test_sort_close_entry_fixed_key(self):
  ts=[self.trade(-10,key=2),self.trade(5,key=1),self.trade(-3,key=0)];m=met.summarize(ts);self.assertEqual(m,ref.summarize(ts));self.assertEqual(m['Combined']['MaxDDPips'],10)
 def test_no_rounding(self):self.assertEqual(met.metric_block([.123456789])['AvgPips'],.123456789)
 def test_selected_discovery_dd_only(self):
  r=record();r['SelectedModeDiscoveryMetrics']['MaxDDPips']=2;r['P0DiscoveryMetrics']={'MaxDDPips':10000};m=self.fixture();self.assertEqual(self.compare(m,r)[3],3);self.assertEqual(self.compare(m,r)[2],'FAIL')
 def test_zero_discovery_dd_requires_zero_validation_dd(self):
  r=record();r['SelectedModeDiscoveryMetrics']['MaxDDPips']=0;m=self.fixture();m['Combined']['MaxDDPips']=0;self.assertEqual(self.compare(m,r)[2],'PASS');m['Combined']['MaxDDPips']=np.nextafter(0.,1);self.assertEqual(self.compare(m,r)[2],'FAIL')
 def test_retention_not_gate(self):
  r=record();r['SelectedModeDiscoveryMetrics']['AvgPips']=100000;self.assertEqual(self.compare(self.fixture(),r)[2],'PASS')
 def test_insufficient_formal_reasons_separated(self):
  out=empty_result(record());s=summaries([out]);self.assertTrue(all(v==0 for v in s['formal_check_summary.json']['SufficientSampleFormalFailureCounts'].values()));self.assertTrue(any(s['formal_check_summary.json']['InsufficientSampleDiagnosticFalseCounts'].values()))

class ValidationIsolation(unittest.TestCase):
 def test_out_of_period_reject(self):
  for day in ('2023-12-31','2026-01-01','2026-10-01'):
   b=bars(day)
   with self.assertRaises(ValueError):opt.Engine(b,'USDJPY')
   with self.assertRaises(ValueError):ref.validate(b)
 def test_index_and_ohlc_reject(self):
  variants=[pd.concat([bars(),bars()]),bars().iloc[::-1],bars().tz_localize('UTC'),bars().iloc[:0]]
  for key,v in [('Open',np.nan),('High',99),('Low',101)]:
   b=bars();b.iloc[0,b.columns.get_loc(key)]=v;variants.append(b)
  for b in variants:
   with self.assertRaises(ValueError):data.validate(b)
 def test_loader_owned_slice_only(self):
  frames=pd.concat([bars('2023-12-31 09:00'),bars(),bars('2026-01-01 09:00')]);row=dict(Filename='synthetic.csv',Symbol='USDJPY',FirstRaw='2023-01-01',LastRaw='2026-12-01',SHA256='x')
  with patch.object(data,'manifest_rows',return_value=[row]),patch.object(data,'digest',return_value='x'),patch.object(data,'read_mt5',return_value=frames),patch('b7.stage1_input.load_discovery',side_effect=AssertionError('forbidden')):
   b=data.load_validation({'synthetic.csv':'/tmp/synthetic.csv'},'USDJPY');self.assertEqual(list(b.index),list(bars().index));frames.loc[b.index,'Open']=999;self.assertTrue((b.Open==100).all())
 def test_loader_mutation_and_wrong_filename(self):
  row=dict(Filename='synthetic.csv',Symbol='USDJPY',FirstRaw='2024-01-01',LastRaw='2025-12-01',SHA256='x')
  with patch.object(data,'manifest_rows',return_value=[row]),patch.object(data,'digest',side_effect=['x','bad']),patch.object(data,'read_mt5',return_value=bars()):
   with self.assertRaises(ValueError):data.load_validation({'synthetic.csv':'/tmp/synthetic.csv'},'USDJPY')
  with patch.object(data,'manifest_rows',return_value=[row]):
   with self.assertRaises(ValueError):data.load_validation({'synthetic.csv':'/tmp/wrong.csv'},'USDJPY')
 def test_loader_invalid_bounds(self):
  with patch.object(data,'manifest_rows',return_value=[]):
   for bounds in [('2023-01-01','2025-01-01'),('2025-01-01','2026-01-02')]:
    with self.assertRaises(ValueError):data.load_validation({},'USDJPY',bounds)

class FrozenContract(unittest.TestCase):
 def test_input_exact_and_counts(self):
  c,d=inp.input_config();self.assertEqual(len(d['Candidates']),40);self.assertEqual(digest(inp.INPUT),'0a9db7f5d65191cd88153199470034a78286880920960442b9e300d0fbb18ed4');self.assertEqual([sum(r['FormalProtectionMode']==m for r in d['Candidates']) for m in ('P0','P1','P2','P3')],[37,2,1,0])
 def test_persisted_schema_and_flags(self):
  r=record();d=empty_result(r);validate_result(d,r)
  for key,value in [('Status','PASS'),('DDThreshold',999),('SampleSufficient',True),('FormalConditionsPASS',True),('NoReplacement',False),('RescuePASSAllowed',True),('FormalProtectionMode','P1'),('ValidationSelectedTradeStreamSHA256','0'*64)]:
   x=copy.deepcopy(d);x[key]=value
   with self.assertRaises(ValueError):validate_result(x,r)
 def test_monitor_projection_rejects_insufficient(self):
  r=record()
  with self.assertRaises(ValueError):project_monitor(r,empty_result(r),'a'*64,'b'*64,'c'*40)
 def test_synthetic_smoke_schedules_disjoint(self):
  from b7.u11_smoke import schedule_tuple
  cfg,d=inp.input_config();fixed=[schedule_tuple(r) for r in d['Candidates']]
  for sym in cfg['Smoke']['Symbols']:
   for direction in cfg['Smoke']['Directions']:
    for s in cfg['Smoke']['Schedules']:self.assertNotIn(schedule_tuple(synthetic_record(sym,direction,'P0',s['EntryMinute'],s['ExitMinute'],s['ExitDayOffset'])),fixed)
 def test_no_optimized_imports_in_reference(self):
  tree=ast.parse((ROOT/'src/research/b7/u11_reference.py').read_text())
  imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)];self.assertFalse(any(x in imports for x in ('u11_execution','u11_engine','u11_metrics','stage1_metrics')))
 def test_notebooks_default_off(self):
  for name in ('b7_u11_validation.ipynb','b7_u11_finalize_only.ipynb'):
   d=json.loads((ROOT/'notebooks'/name).read_text());code='\n'.join(''.join(c['source']) for c in d['cells'] if c['cell_type']=='code');tree=ast.parse(code)
   values={n.targets[0].id:ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('RUN_')}
   self.assertTrue(values);self.assertTrue(all(v is False for v in values.values()));self.assertIn('archive_completed',code)

class AdditionalBoundaries(unittest.TestCase):
 def test_validation_end_exclusive_start_inclusive(self):
  data.validate(bars('2024-01-01 00:00',1));data.validate(bars('2025-12-31 23:59',1))
  with self.assertRaises(ValueError):data.validate(bars('2026-01-01 00:00',1))
 def test_dec24_jan4_open(self):
  for day in ('2024-12-24','2024-01-04'):
   b=bars(day+' 09:00');self.assertEqual(opt.Engine(b,'USDJPY').execute('LONG',b.index[0],b.index[30])['Status'],'OK')
 def test_entry_year_assignment_over_year_end(self):
  ts=[dict(Pips=-2.,EntryTime='2024-12-31 23:50:00',CloseTime='2025-01-01 00:20:00',FixedKey=[1])]
  a=met.summarize(ts);self.assertEqual(a,ref.summarize(ts));self.assertEqual(a['Annual2024']['Trades'],1);self.assertEqual(a['Annual2025']['Trades'],0);self.assertEqual(a['Monthly']['2024-12']['Trades'],1)
 def test_zero_pips_not_losses(self):
  m=met.metric_block([0.,-1.,1.]);self.assertEqual((m['Wins'],m['Losses'],m['ZeroPips']),(1,1,1))
 def test_exact30_and1440_holding(self):
  b=bars(n=1441)
  for hold in (30,1440):self.assertEqual(opt.Engine(b,'USDJPY').execute('LONG',b.index[0],b.index[hold])['Status'],'OK')
 def test_fallback_period_guard_precedes_path(self):
  # Isolate the fallback guard from earlier frozen year-end entry exclusion.
  b=bars('2024-02-06 09:00',31);end=b.index[30]+pd.Timedelta(minutes=1);b=b.drop(b.index[30])
  with patch('b7.u11_engine.END',end):self.assertEqual(opt.Engine(b,'USDJPY').execute('LONG',b.index[0],end-pd.Timedelta(minutes=1))['Status'],'PERIOD_BOUNDARY')
 def test_audusd_no_formal_jobs(self):
  _,d=inp.input_config();self.assertEqual(sum(r['Symbol']=='AUDUSD' for r in d['Candidates']),0)
 def test_wtl_activation_retention_do_not_change_status(self):
  r=record();out=empty_result(r);before=out['ValidationStatus'];out['Diagnostics'].update(WinnerToLoserCount=999,ProtectionActivationCount=999,AvgPipsRetention=-999);self.assertEqual(validate_result(out,r)['ValidationStatus'],before)
 def test_selected_engine_period_only_change(self):
  # Execution function AST must match frozen U06; only its period globals differ.
  def function(path):
   t=ast.parse(path.read_text());return ast.dump(next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_execute'),include_attributes=False)
  self.assertEqual(function(ROOT/'src/research/b7/u11_engine.py'),function(ROOT/'src/research/b7/u06_execution.py'))
 def test_no_discovery_loader_or_hidden_optimizer_calls(self):
  for n in ('u11_data.py','u11_execution.py','u11_metrics.py','u11_reference.py'):
   t=ast.parse((ROOT/'src/research/b7'/n).read_text());calls=[x.func.id if isinstance(x.func,ast.Name) else x.func.attr if isinstance(x.func,ast.Attribute) else '' for x in ast.walk(t) if isinstance(x,ast.Call)]
   self.assertFalse(set(calls)&{'load_discovery','select','adoption','gate_checks','coarse_anchors','local_grid'})
 def test_raw_conversion_existing_helsinki(self):
  from b7.stage1_input import read_mt5
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'synthetic.csv';p.write_text('<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n2024.01.08\t00:00:00\t100\t100\t100\t100\t1\t0\t0\n')
   self.assertEqual(str(read_mt5(p).index[0]),'2024-01-08 07:00:00')
 def test_result_unrounded_trade_and_metrics(self):
  b=bars();b.loc[b.index[30],['Open','High','Low','Close']]=100.123456789
  r=record();a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2024-02-06'],implementation_sha='a'*40);z,zd=ref.evaluate_candidate(b,r,{'Events':[]},['2024-02-06'],implementation_sha='a'*40)
  self.assertEqual((a,ad),(z,zd));self.assertEqual(a['ValidationMetrics']['Combined']['TotalPips'],a['TradeResults'][0]['Pips'])
