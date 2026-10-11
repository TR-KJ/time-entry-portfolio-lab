import unittest,tempfile,copy,json,os,ast
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import monitor_input as inp,monitor_runtime as rt,monitor_finalize_only as fin
from b7 import monitor_execution as opt,monitor_reference as ref,monitor_metrics as met,monitor_data as data
from b7.monitor_artifacts import identity,validate_result,summaries
from b7.monitor_smoke import synthetic_record
from b7.stage1_contract import ROOT,digest,canonical,object_hash,PIPS,SPREAD
from test_b7_u06 import bars as old_bars

def bars(start='2026-02-03 09:00',n=35):return old_bars(start,n)
def record(direction='LONG',tp=None,mode='P0'):
 r=synthetic_record('USDJPY',direction,mode,540,570,0,tp);r['FormalSL']=20
 return r

def empty_result(r):
 return opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),r,days=[],calendar={'Events':[]},implementation_sha='a'*40)[0]


class CheckpointAndFinalize(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.producer='a'*40;self.env=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
        self.records=[record() for _ in range(22)]
        for i,r in enumerate(self.records):r['CandidateID']='SYNTHETIC_MONITOR:'+str(i)
        self.identity=identity(self.producer,self.env);self.identity['CandidateIDs']=[r['CandidateID'] for r in self.records]
        expected={k:v for k,v in self.identity.items() if k!='Environment'}
        def expected_identity(sha):return dict(expected,ImplementationSHA=sha),self.records
        for target,value in [('b7.monitor_finalize_only.expected_identity',expected_identity),('b7.monitor_runtime.input_config',lambda:({},dict(Candidates=self.records))),('b7.monitor_runtime.make_identity',lambda sha,env:dict(self.identity,ImplementationSHA=sha,Environment=env))]:
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
    def test_all22(self):self.assertEqual(self.audit()[1]['JobCount'],22)
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
        for key in ('MonitorConfigSHA256','MonitorInputSHA256','CandidateFreezeSHA','CandidateFingerprints','U11ContractSHA256','M1ExactIdentity','U09ResultFreezeSHA','FrozenU11Contract','SupplementalPrespecSHA256','CandidateIDs','FullPrespecSHA256'):
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
        self.assertEqual(values[-1],dict(ProcessedJobs=22,ExpectedJobs=22));self.assertTrue(all(set(v)=={'ProcessedJobs','ExpectedJobs'} for v in values))
    def test_source_unchanged_and_no_recompute(self):
        before={str(p):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()}
        targets=['b7.stage1_input.load_discovery','b7.stage1_input.read_mt5','b7.u06_execution.Engine','b7.u06_reference.execute','b7.u10_execution.execution_stream','b7.u10_execution.filter_modes','b7.u10_calendar.EventIndex','b7.stage1_metrics.summarize','b7.stage1_metrics.gate','b7.stage1_runtime.run_tests']
        targets += ['b7.monitor_execution.'+n for n in ['Engine','executable','filter_e2','simulate','evaluate_candidate','summarize','calendar_days']]
        targets += ['b7.monitor_reference.'+n for n in ['executable','filter_e2','simulate','evaluate_candidate','summarize','calendar_days']]
        targets += ['b7.monitor_metrics.'+n for n in ['metric_block','summarize','diagnostics']]
        targets += ['b7.monitor_data.load_monitor','b7.monitor_engine.Engine','b7.monitor_reference.execute']
        targets += ['b7.monitor_runtime.'+n for n in ['Engine','load_monitor','evaluate_candidate']]
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
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json','monitor_summary.json','event_summary.json','diagnostic_summary.json'):
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
        with patch.object(rt,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(rt.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(rt,'preflight',return_value=proof), patch.object(rt.shared,'environment',return_value=self.env), patch.object(rt,'Engine',side_effect=AssertionError('no engine')), patch.object(rt,'load_monitor',side_effect=AssertionError('no M1')), patch.object(rt,'evaluate_candidate',side_effect=AssertionError('no recomputation')):
            result=rt.run_formal({},self.producer,'/content/out','/content/drive/source',approval=rt.APPROVAL,resume=True)
        self.assertEqual(result['CompletedJobs'],22)
    def test_public_finalize_no_evaluation_and_portable_paths(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True);shutil.copytree(self.drive,content/'drive'/'source')
        with patch.object(fin,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(fin.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(fin,'current_preflight',return_value=self.proof), patch.object(opt,'executable',side_effect=AssertionError('no filtering')), patch.object(opt,'evaluate_candidate',side_effect=AssertionError('no evaluation')):
            result=fin.finalize_from_completed_jobs('/content/drive/source','/content/out',self.producer,self.producer,fin.APPROVAL)
        self.assertFalse(result['JobRecomputation'])
    def test_source_mutation_stops_without_output(self):
        def progress(p):
            if p['ProcessedJobs']==22:(self.job/'candidate.json').write_text('{}')
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
  b=bars(n=31);r=record(direction,tp,mode);r['CandidateID']='SYNTHETIC_MONITOR_PATH'
  for i,h,l in changes:b.iloc[i,b.columns.get_loc('High')]=h;b.iloc[i,b.columns.get_loc('Low')]=l
  b=b.drop(b.index[list(remove)])
  with patch.dict(PIPS,USDJPY=1.),patch.dict(SPREAD,USDJPY=0.):
   a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2026-02-03'],implementation_sha='a'*40)
   z,zd=ref.evaluate_candidate(b,r,{'Events':[]},['2026-02-03'],implementation_sha='a'*40)
   self.assertEqual(a,z);self.assertEqual(ad,zd);validate_result(a,r)
  return a['TradeResults'][0],a
 def test_p1_next_bar_be(self):
  t,_=self.run_path([(0,110,99),(1,105,99)]);self.assertEqual(t['FinalPips'],0);self.assertEqual(t['ActivationBar'],'2026-02-03 09:01:00');self.assertEqual(t['TriggerBar'],'2026-02-03 09:00:00')
 def test_p2_lock(self):self.assertEqual(self.run_path([(0,115,99),(1,106,99)],mode='P2')[0]['FinalPips'],5)
 def test_p3_lock(self):self.assertEqual(self.run_path([(0,120,99),(1,111,99)],mode='P3')[0]['FinalPips'],10)
 def test_trigger_original_sl_same_bar(self):
  t,_=self.run_path([(0,115,80)]);self.assertEqual(t['FinalPips'],-20);self.assertFalse(t['ProtectionActivated'])
 def test_trigger_tp_same_bar(self):
  t,_=self.run_path([(0,130,99)],tp=25);self.assertEqual(t['FinalPips'],25);self.assertFalse(t['ProtectionActivated'])
 def test_active_stop_tp_same_bar(self):
  t,_=self.run_path([(0,110,99),(1,130,99)],tp=25);self.assertEqual(t['FinalPips'],0);self.assertTrue(t['ProtectionHit'])
 def test_missing_next_minute(self):self.assertEqual(self.run_path([(0,110,99),(3,104,99)],remove=(1,2))[0]['ActivationBar'],'2026-02-03 09:03:00')
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
  r=record();b=bars(n=31);ts,_=opt.executable(opt.Engine(b,'USDJPY'),r,['2026-02-03']);t=opt.simulate(b,r,ts[0],'P0')
  self.assertEqual(t,ref.simulate(b,r,ts[0],'P0'));self.assertEqual(t['EntryPrice'],100+SPREAD['USDJPY']*PIPS['USDJPY']);self.assertEqual(t['MFEpips'],0)
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
 def test_missing_entry(self):self.assertEqual(self.compare(bars().iloc[1:],entry='2026-02-03 09:00')['Status'],'MISSING_ENTRY')
 def test_gap_no_interpolation(self):self.assertEqual(self.compare(bars().drop(bars().index[5:10]))['MissingPathMinutes'],5)
 def test_holding_boundaries(self):
  for hold in (29,1441):self.assertEqual(self.compare(bars(),scheduled=bars().index[0]+pd.Timedelta(minutes=hold))['Status'],'INVALID_HOLD')
 def test_overnight(self):self.assertEqual(self.compare(bars('2026-02-03 23:45'))['Status'],'OK')
 def test_no_epsilon(self):
  b=bars();entry=100+SPREAD['USDJPY']*PIPS['USDJPY'];b['Low']=np.nextafter(entry-15*PIPS['USDJPY'],np.inf)
  self.assertEqual(self.compare(b,tp=None)['ExitReason'],'TimeExit')
 def test_chosen_sunday_fallback_reject(self):
  b=bars('2026-02-06 23:59',n=1443);b=b.drop(b.index[1440]);self.assertEqual(self.compare(b,scheduled='2026-02-07 23:59')['Status'],'WEEKEND_BOUNDARY')
 def test_owned_validation_engine(self):
  b=bars();e=opt.Engine(b,'USDJPY');b.iloc[0,0]=999;self.assertNotEqual(e.bars.iloc[0,0],999)
class Calendar(unittest.TestCase):
 def test_saved_filters(self):
  r=record();r.update(FormalWeekdays=[1],FormalDOMBuckets=['D1'],FormalMonths=[2])
  a=opt.calendar_days(r);self.assertEqual(a,ref.calendar_days(r));self.assertTrue(all(d.weekday()==1 and d.month==2 and d.day<=10 for d in a));self.assertTrue(all(d.year==2026 for d in a))
 def test_event_planned_window_even_early_sl(self):
  r=record();b=bars();b.iloc[0,b.columns.get_loc('Low')]=99
  c={'Events':[dict(CanonicalEventName='US_NFP',SourceDates=['2026-02-03'],FixedJST='09:30',WindowPlusMinusMinutes=0)]}
  a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,c,['2026-02-03'],implementation_sha='a'*40)
  z,zd=ref.evaluate_candidate(b,r,c,['2026-02-03'],implementation_sha='a'*40)
  self.assertEqual((a,ad),(z,zd));self.assertEqual(a['EventDiagnostics']['E0ExecutableTrades'],1);self.assertEqual(a['EventDiagnostics']['E2Trades'],0)
 def test_unique_exclusion_multiple_events(self):
  r=record();b=bars();c={'Events':[dict(CanonicalEventName=n,SourceDates=['2026-02-02' if n=='FOMC' else '2026-02-03'],FixedJST='09:00',WindowPlusMinusMinutes=0) for n in ('US_NFP','FOMC')]}
  a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,c,['2026-02-03'],implementation_sha='a'*40)
  z,zd=ref.evaluate_candidate(b,r,c,['2026-02-03'],implementation_sha='a'*40)
  self.assertEqual((a,ad),(z,zd));e=a['EventDiagnostics'];self.assertEqual((e['RemovedTrades'],e['MultiEventOverlapTradeCount']),(1,1));self.assertEqual(sum(e['RemovedByEvent'].values()),2)
 def test_no_missing_entry_in_e0(self):
  r=record();a,_=opt.evaluate_candidate(opt.Engine(bars().iloc[1:],'USDJPY'),r,{'Events':[]},['2026-02-03'],implementation_sha='a'*40);self.assertEqual(a['EventDiagnostics']['E0ExecutableTrades'],0)
 def test_wrong_event_set_reject(self):
  r=record();r['E2EventSet']=[]
  with self.assertRaises(ValueError):opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),r,{'Events':[]},[])
 def test_duplicate_dates_reject(self):
  with self.assertRaises(ValueError):opt.calendar_days(record(),['2026-02-03']*2)
class ValidationIsolation(unittest.TestCase):
 def test_index_and_ohlc_reject(self):
  variants=[pd.concat([bars(),bars()]),bars().iloc[::-1],bars().tz_localize('UTC'),bars().iloc[:0]]
  for key,v in [('Open',np.nan),('High',99),('Low',101)]:
   b=bars();b.iloc[0,b.columns.get_loc(key)]=v;variants.append(b)
  for b in variants:
   with self.assertRaises(ValueError):data.validate(b)
 def test_loader_mutation_and_wrong_filename(self):
  row=dict(Filename='synthetic.csv',Symbol='USDJPY',FirstRaw='2026-01-01',LastRaw='2026-09-09',SHA256='x')
  with patch.object(data,'manifest_rows',return_value=[row]),patch.object(data,'digest',side_effect=['x','bad']),patch.object(data,'read_mt5',return_value=bars()):
   with self.assertRaises(ValueError):data.load_monitor({'synthetic.csv':'/tmp/synthetic.csv'},'USDJPY')
  with patch.object(data,'manifest_rows',return_value=[row]):
   with self.assertRaises(ValueError):data.load_monitor({'synthetic.csv':'/tmp/wrong.csv'},'USDJPY')

class MonitorContract(unittest.TestCase):
 def test_static_input_identity_eligibility(self):
  c,d=inp.input_config();self.assertEqual(len(d['Candidates']),22);self.assertEqual(len(set(d['CandidateIDs'])),22)
  self.assertEqual(d['CandidateIDs'],[r['CandidateID'] for r in d['Candidates']]);self.assertEqual(d['PairCounts'],inp.PAIRS);self.assertEqual(d['ProtectionModeCounts'],inp.MODES)
  fail=json.loads((ROOT/'results/b7/u11/fail_inventory.json').read_text());self.assertFalse(set(d['CandidateIDs'])&{r['CandidateID'] for r in fail})
  self.assertTrue(all(r['U11ValidationStatus']=='PASS' for r in d['Candidates']))
 def test_input_mutations_rejected(self):
  _,d=inp.input_config()
  for key,v in [('CandidateCount',21),('CandidateIDs',d['CandidateIDs'][::-1]),('NoReplacement',False),('MonitorPerformanceEvaluated',True),('ValidationOverrideAllowed',True),('MonitorStatus','PASS'),('MonitorPeriod','bad'),('Scope','bad'),('PairCounts',{}),('ProtectionModeCounts',{}),('U11ProducerImplementationSHA','a'*40),('CandidateFreezeSHA','a'*40),('EventCalendarSHA256','a'*64),('SourceTrustedFilesSHA256','a'*64)]:
   x=copy.deepcopy(d);x[key]=v
   with self.assertRaises(ValueError):inp.validate(x)
  for key,v in [('FormalSL',1),('U11ValidationStatus','FAIL'),('FormalProtectionMode','P1'),('ValidationMetrics',{})]:
   x=copy.deepcopy(d);x['Candidates'][0][key]=v
   with self.assertRaises(ValueError):inp.validate(x)
 def test_file_and_config_identity(self):
  with patch.object(inp,'digest',return_value='bad'):
   with self.assertRaises(ValueError):inp.input_config()
  self.assertEqual(inp.INPUT.stat().st_size,260069);self.assertEqual(object_hash(inp.input_config()[1]),inp.INPUT_OBJECT)
 def test_observed_empty_and_negative(self):
  for low in (100.,99.):
   b=bars();b['Low']=low;r=record();out,_=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2026-02-03'],implementation_sha='a'*40)
   self.assertEqual(validate_result(out,r)['Status'],'OBSERVED_ONLY');self.assertFalse(out['ValidationOverrideAllowed'])
   self.assertEqual(out['ValidationBaseline'],r['ValidationMetrics']);self.assertFalse(set(out)&{'FormalChecks','SampleChecks','SampleSufficient','FormalConditionsPASS','ValidationStatus'})
  self.assertEqual(empty_result(record())['Status'],'OBSERVED_ONLY')
 def test_gate_fields_and_tampered_metrics_reject(self):
  r=record();d=empty_result(r)
  for key,v in [('FormalChecks',{}),('SampleChecks',{}),('FormalConditionsPASS',False),('Status','FAIL'),('ValidationOverrideAllowed',True),('MonitorPeriod','bad'),('MonitorSelectedTradeStreamSHA256','0'*64),('ValidationBaseline',{})]:
   z=copy.deepcopy(d);z[key]=v
   with self.assertRaises(ValueError):validate_result(z,r)
  for key,v in [('AvgPips',0.),('TotalPips',1.),('MaxDDPips',-1.),('Trades',True),('PFState','FINITE')]:
   z=copy.deepcopy(d)
   for k in ('Combined','Annual2026'):z['MonitorMetrics'][k][key]=v
   with self.assertRaises(ValueError):validate_result(z,r)
 def test_metrics_months_annual_pf_dd(self):
  ts=[dict(Pips=p,EntryTime=e,CloseTime=x,FixedKey=[i]) for i,(p,e,x) in enumerate([(-3.,'2026-01-30 23:50:00','2026-01-31 00:20:00'),(5.,'2026-02-03 09:00:00','2026-02-03 09:30:00'),(-10.,'2026-09-09 09:00:00','2026-09-09 09:30:00')])]
  m=met.summarize(ts[::-1]);self.assertEqual(m,ref.summarize(ts));self.assertEqual(m['Annual2026'],m['Combined']);self.assertEqual(m['Combined']['MaxDDPips'],10);self.assertEqual(m['Monthly']['2026-09']['Trades'],1);self.assertEqual(len(m['Monthly']),9)
  for ps,state,value in [([], 'UNDEFINED',None),([0.], 'UNDEFINED',None),([1.], 'INF',None),([-1.], 'FINITE',0.)]:
   v=met.metric_block(ps);self.assertEqual((v['PFState'],v['PFpips']),(state,value));self.assertEqual(v,ref.metric_block(ps))
 def test_monitor_start_end_owned(self):
  data.validate(bars('2026-01-01 00:00',1));data.validate(bars('2026-09-09 23:59',1))
  for day in ('2023-12-31','2024-02-01','2025-12-31','2026-09-10','2026-10-01'):
   with self.assertRaises(ValueError):data.validate(bars(day))
 def test_jan1_3_no_entries(self):
  for day,reason in [('2026-01-01','YEAR_END_STOP'),('2026-01-02','YEAR_END_STOP'),('2026-01-03','INVALID_ENTRY_WEEKDAY')]:
   b=bars(day+' 09:00');self.assertEqual(opt.Engine(b,'USDJPY').execute('LONG',b.index[0],b.index[30])['Status'],reason)
 def test_end_crossing_and_fallback(self):
  b=bars('2026-09-09 23:30',30);e=opt.Engine(b,'USDJPY')
  self.assertEqual(e.execute('LONG',b.index[0],'2026-09-10 00:00')['Status'],'PERIOD_BOUNDARY')
  b=bars('2026-09-09 23:00',59);self.assertEqual(opt.Engine(b,'USDJPY').execute('LONG',b.index[0],'2026-09-09 23:59')['Status'],'PERIOD_BOUNDARY')
 def test_loader_owned_slice_only(self):
  frames=pd.concat([bars('2025-12-31'),bars(),bars('2026-09-10')]);row=dict(Filename='synthetic.csv',Symbol='USDJPY',FirstRaw='2025-12-30',LastRaw='2026-10-01',SHA256='x')
  with patch.object(data,'manifest_rows',return_value=[row]),patch.object(data,'digest',return_value='x'),patch.object(data,'read_mt5',return_value=frames):
   b=data.load_monitor({'synthetic.csv':'/tmp/synthetic.csv'},'USDJPY');self.assertEqual(list(b.index),list(bars().index));frames.loc[b.index,'Open']=999;self.assertTrue((b.Open==100).all())
 def test_loader_invalid_bounds(self):
  with patch.object(data,'manifest_rows',return_value=[]):
   for bounds in [('2025-01-01','2026-02-01'),('2026-01-01','2026-09-11')]:
    with self.assertRaises(ValueError):data.load_monitor({},'USDJPY',bounds)
 def test_u11_function_parity(self):
  def function(file,name):
   n=next(x for x in ast.parse((ROOT/'src/research/b7'/file).read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name)
   # Diagnostic labels do not change execution.
   for v in ast.walk(n):
    if isinstance(v,ast.Constant) and isinstance(v.value,str):v.value=v.value.replace('Monitor','Validation')
   return ast.dump(n,include_attributes=False)
  self.assertEqual(function('monitor_engine.py','_execute'),function('u11_engine.py','_execute'))
  for n in ('calendar_days','executable','filter_e2','simulate'):self.assertEqual(function('monitor_execution.py',n),function('u11_execution.py',n))
 def test_shifted_u11_identical_fixture(self):
  from b7 import u11_execution as old,u11_metrics as oldmet
  from b7.u11_smoke import synthetic_record as oldrecord
  for mode in ('P0','P2'):
   r=record(mode=mode);b=bars();b.iloc[0,b.columns.get_loc('High')]=100.18;b=b.drop(b.index[1:3]);oldbars=b.copy();oldbars.index=oldbars.index-pd.Timedelta(days=728)
   original=oldrecord('USDJPY','LONG',mode,540,570);original['FormalSL']=r['FormalSL'];original['CandidateID']=r['CandidateID']
   a,ad=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,{'Events':[]},['2026-02-03'],implementation_sha='a'*40)
   z,zd=old.evaluate_candidate(old.Engine(oldbars,'USDJPY'),original,{'Events':[]},['2024-02-06'],implementation_sha='a'*40)
   self.assertEqual(a['MonitorMetrics']['Combined'],z['ValidationMetrics']['Combined'])
   def normalize(ts):
    ts=copy.deepcopy(ts)
    for t in ts:
     t.pop('TradeID')
     for k,v in t.items():
      if isinstance(v,str) and v.startswith('2026-02-03'):t[k]=v.replace('2026-02-03','2024-02-06')
    return ts
   self.assertEqual(normalize(a['TradeResults']),normalize(z['TradeResults']))
 def test_reference_independent(self):
  with ExitStack() as stack:
   for n in ('calendar_days','executable','filter_e2','simulate','summarize','diagnostics','evaluate_candidate'):stack.enter_context(patch.object(opt,n,side_effect=AssertionError('optimized call')))
   for n in ('summarize','diagnostics','metric_block'):stack.enter_context(patch.object(met,n,side_effect=AssertionError('shared metrics')))
   z,_=ref.evaluate_candidate(bars(),record(),{'Events':[]},['2026-02-03'],implementation_sha='a'*40)
  self.assertEqual(z['Status'],'OBSERVED_ONLY')
 def test_formal_guard_each_barrier_before_evaluation(self):
  from b7 import monitor_guard as g
  _,d=inp.input_config();r=d['Candidates'][0];env=dict(Python='3.12.14',NumPy='2.3.5',pandas='2.2.3');sha='a'*40;ident=identity(sha,env)
  def git(*a):return sha if a==('rev-parse','HEAD') else ''
  with patch.dict(os.environ,{'COLAB_RELEASE_TAG':'synthetic'}),patch.object(g,'Path') as path,patch.object(rt.shared,'git',side_effect=git),patch.object(rt.shared,'environment',return_value=env):
   path.return_value.is_dir.return_value=True
   for approval,reviewed,run in [(None,sha,ident),(g.APPROVAL,'',ident),(g.APPROVAL,sha,None),(g.APPROVAL,sha,{**ident,'MonitorPeriod':'bad'})]:
    with self.assertRaises(PermissionError):g.guard(r,reviewed,approval,run)
   bad=copy.deepcopy(r);bad['FormalSL']+=5
   with self.assertRaises(PermissionError):g.guard(bad,sha,g.APPROVAL,ident)
   # Positive test audits identity only; NEVER evaluates a formal candidate.
   g.guard(r,sha,g.APPROVAL,ident)
   with patch.object(inp,'digest',return_value='bad'):
    with self.assertRaises(ValueError):g.guard(r,sha,g.APPROVAL,ident)
 def test_smoke_no_actual_reads(self):
  from b7.monitor_smoke import run_smoke
  with ExitStack() as stack:
   for target in ['b7.stage1_input.read_mt5','b7.stage1_input.load_discovery','b7.monitor_data.read_mt5','b7.monitor_data.load_monitor','b7.u11_data.load_validation','b7.monitor_input.input_config']:
    stack.enter_context(patch(target,side_effect=AssertionError('actual data/formal input forbidden in smoke')))
   d=run_smoke()
  self.assertEqual(d['Status'],'PASS')
  for k in ('Formal22Used','ActualMonitorRowsUsed','FormalMonitorPerformanceSaved','Full22Run','ValidationStatusChanged'):self.assertFalse(d[k])
 def test_no_hidden_selection_or_gates(self):
  for name in ('monitor_execution.py','monitor_metrics.py','monitor_reference.py'):
   tree=ast.parse((ROOT/'src/research/b7'/name).read_text());calls={n.func.id if isinstance(n.func,ast.Name) else n.func.attr if isinstance(n.func,ast.Attribute) else '' for n in ast.walk(tree) if isinstance(n,ast.Call)}
   self.assertFalse(calls&{'load_discovery','load_validation','checks','select','gate','adoption','local_grid'})
 def test_notebooks_default_off_and_no_output(self):
  for name in ('b7_monitor_2026.ipynb','b7_monitor_finalize_only.ipynb'):
   d=json.loads((ROOT/'notebooks'/name).read_text());code='\n'.join(''.join(c['source']) for c in d['cells'] if c['cell_type']=='code');tree=ast.parse(code)
   values={n.targets[0].id:ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and (n.targets[0].id.startswith('RUN_') or n.targets[0].id in ('APPROVAL','REVIEWED_SHA','REVIEWED_PRODUCER_SHA'))}
   self.assertTrue(values);self.assertTrue(all(v is False if k.startswith('RUN_') else v=='' for k,v in values.items()));self.assertIn('archive_completed',code);self.assertTrue(all(not c.get('outputs') for c in d['cells']))
 def test_preflight_synthetic_only_and_exact72_audit(self):
  sha='a'*40;env=dict(Python='3.12.14',NumPy='2.3.5',pandas='2.2.3');i=identity(sha,env)
  def git(*a):return sha if a==('rev-parse','HEAD') else ''
  with patch.object(rt.shared,'git',side_effect=git),patch.object(rt.shared,'release_manifest'),patch.object(rt.shared,'environment',return_value=env),patch.object(rt.shared,'run_tests',return_value={'Status':'PASS'}),patch.object(rt,'audit_inputs',return_value=i['M1ExactIdentity']) as audit,patch.object(rt,'load_monitor',side_effect=AssertionError('preflight cannot evaluate actual rows')),patch('b7.monitor_smoke.run_smoke',return_value={'Status':'PASS','ActualMonitorRowsUsed':False}) as smoke:
   p=rt.preflight({},sha);audit.assert_called_once_with({});smoke.assert_called_once_with();self.assertEqual(p['Identity'],i)
 def test_formal_period_and_calendar_override_rejected(self):
  r=record();r['CandidateID']='B7S1:SYNTHETIC_GUARD_ONLY'
  for module in (opt,ref):
   with patch('b7.monitor_guard.guard'),patch.object(module,'executable',side_effect=AssertionError('must STOP first')):
    with self.assertRaises(PermissionError):module.evaluate_candidate(None,r,days=[])
    with self.assertRaises(PermissionError):module.evaluate_candidate(None,r,calendar={'Events':[]})

 def test_synthetic_default_frozen_calendar(self):
  a,_=opt.evaluate_candidate(opt.Engine(bars(),'USDJPY'),record(),days=[],implementation_sha='a'*40)
  self.assertEqual(a['Status'],'OBSERVED_ONLY')
