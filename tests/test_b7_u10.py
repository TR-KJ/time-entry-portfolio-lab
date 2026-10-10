import unittest,tempfile,copy,json,os,sys,subprocess,ast
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import u10_input as inp,u10_runtime as rt,u10_finalize_only as fin,u10_calendar as cal
from b7 import u10_execution as opt,u10_reference as ref
from b7.u10_artifacts import identity,validate_result,result,summaries,project_u10p
from b7.u10_smoke import synthetic_record
from b7.stage1_contract import ROOT,digest,canonical,object_hash
from b7.stage1_metrics import summarize
from test_b7_u08 import metrics

def record(symbol='USDJPY',entry=540,exit=570,offset=0,direction='LONG',tp=None):
 return synthetic_record(symbol,direction,15,tp,dict(EntryMinute=entry,ExitMinute=exit,ExitDayOffset=offset,HoldingMinutes=offset*1440+exit-entry))

def empty_result(r):
 modes,streams,_=opt.filter_modes([],r['Symbol'],cal.EventIndex(cal.audit_calendar()))
 return result(r,modes,opt.gate_checks(modes['E2']['Metrics']),streams)

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
        for key in ('U10ConfigSHA256','U10InputSHA256','M1ExactIdentity','U09ResultFreezeSHA','U10SupplementalConditionsFreezeSHA','SupplementalPrespecSHA256','CandidateIDs','FullPrespecSHA256'):
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
        targets=['b7.stage1_input.load_discovery','b7.stage1_input.read_mt5','b7.u06_execution.Engine','b7.u06_reference.execute',
                 'b7.u10_execution.Engine','b7.u10_execution.execution_stream','b7.u10_execution.filter_modes','b7.u10_execution.gate_checks','b7.u10_execution.evaluate_candidate',
                 'b7.u10_reference.execute','b7.u10_reference.evaluate_candidate','b7.u10_reference.filter_modes','b7.u10_reference.gate_checks','b7.u10_reference.windows','b7.u10_reference.event_set',
                 'b7.u10_calendar.windows','b7.u10_calendar.event_set','b7.u10_calendar.EventIndex.matching','b7.u10_calendar.EventIndex',
                 'b7.stage1_metrics.summarize','b7.stage1_metrics.gate','b7.u10_runtime.load_discovery','b7.u10_runtime.Engine','b7.u10_runtime.evaluate_candidate','b7.stage1_runtime.run_tests']
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
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json','status_summary.json','event_summary.json','mode_summary.json'):
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
        self.assertEqual(result['CompletedJobs'],54)
    def test_public_finalize_no_evaluation_and_portable_paths(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True);shutil.copytree(self.drive,content/'drive'/'source')
        with patch.object(fin,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(fin.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(fin,'current_preflight',return_value=self.proof), patch.object(opt,'filter_modes',side_effect=AssertionError('no filtering')), patch.object(opt,'evaluate_candidate',side_effect=AssertionError('no evaluation')):
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


class CalendarAndIdentity(unittest.TestCase):
 def test_exact_source_extraction_and_legacy(self):
  source=subprocess.check_output(['git','show',cal.CALENDAR_COMMIT+':'+cal.SOURCE_PATH]);import hashlib
  self.assertEqual(hashlib.sha256(source).hexdigest(),cal.SOURCE_SHA)
  self.assertEqual(subprocess.check_output(['git','rev-parse',cal.CALENDAR_COMMIT+':'+cal.SOURCE_PATH],text=True).strip(),cal.SOURCE_BLOB)
  ns={};initial={}
  for n in ast.parse(source).body:
   if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.endswith('_DATES'):
    k=n.targets[0].id;v=n.value
    if isinstance(v,ast.List):ns[k]=ast.literal_eval(v);initial[k]=len(ns[k])
    elif isinstance(v,ast.BinOp) and isinstance(v.op,ast.Add):ns[k]=ns[v.left.id]+ns[v.right.id]
  c=cal.audit_calendar()
  for e in c['Events']:self.assertEqual(e['SourceDates'],ns[e['SourceArray']]);self.assertEqual(e['ExtractedArraySHA256'],object_hash(ns[e['SourceArray']]))
  self.assertEqual(initial['AUD_CPI_DATES'],44);self.assertEqual(initial['AUD_CPI_2026_DATES'],4);self.assertEqual(len(ns['AUD_CPI_DATES']),48);self.assertNotIn('AU_CPI_DATES',ns)
  legacy=subprocess.check_output(['git','show',cal.CALENDAR_COMMIT+':src/filter_validation/event_filter_validation_v1.py'])
  helpers=[n for n in ast.parse(legacy).body if isinstance(n,ast.FunctionDef) and n.name in ('as_set','event_dates_for_name')]
  exec(compile(ast.Module(body=helpers,type_ignores=[]),'<pure lookup>','exec'),ns)
  self.assertEqual(ns['event_dates_for_name']('AU_CPI'),set())
 def test_aud_discovery_exact(self):
  e=next(e for e in cal.audit_calendar()['Events'] if e['CanonicalEventName']=='AUD_CPI')
  self.assertEqual([d for d in e['SourceDates'] if '2020-01-01'<=d<'2024-01-01'],['2020-01-29','2020-04-29','2020-07-29','2020-10-28','2021-01-27','2021-04-28','2021-07-28','2021-10-27','2022-01-25','2022-04-27','2022-07-27','2022-10-26','2023-01-25','2023-04-26','2023-07-26','2023-10-25'])
 def test_known_times_and_windows(self):
  c=cal.audit_calendar();a=cal.windows(c);self.assertEqual(a,ref.windows(c))
  cases={'FOMC':('2020-01-29','2020-01-30 03:00:00'),'US_NFP':('2020-01-10','2020-01-10 21:30:00'),'US_CPI':('2020-01-14','2020-01-14 21:30:00'),'BOJ':('2020-01-21','2020-01-21 12:00:00'),'BOE':('2020-01-30','2020-01-30 21:00:00'),'ECB':('2020-01-23','2020-01-23 21:15:00'),'RBA':('2020-02-04','2020-02-04 13:30:00'),'AUD_CPI':('2020-01-29','2020-01-29 10:30:00')}
  for n,(ds,t) in cases.items():
   w=next(w for w in a if w['Event']==n and w['SourceDate']==ds);self.assertEqual(w['EventTimestampJST'],t);self.assertEqual(pd.Timestamp(w['End'])-pd.Timestamp(w['Start']),pd.Timedelta(minutes=cal.FIXED[n][1]*2))
 def test_no_dst_all_dates(self):
  for w in cal.windows(cal.audit_calendar()):self.assertEqual(w['EventTimestampJST'][11:16],cal.FIXED[w['Event']][0])
 def test_all_pair_sets(self):
  expected={'USDJPY':{'FOMC','BOJ'},'EURJPY':{'ECB','BOJ'},'GBPJPY':{'BOE','BOJ'},'AUDJPY':{'RBA','BOJ'},'AUDUSD':{'RBA','FOMC'},'EURAUD':{'ECB','RBA'},'GBPAUD':{'BOE','RBA'},'EURUSD':{'ECB','FOMC'},'GBPUSD':{'BOE','FOMC'}}
  for s,e in expected.items():
   for mode,want in [('E0',[]),('E1',sorted(e)),('E2',sorted(e|{'US_NFP','US_CPI'}|({'AUD_CPI'} if 'AUD' in s else set())))]:self.assertEqual(cal.event_set(s,mode),want);self.assertEqual(ref.event_set(s,mode),want)
 def test_unknown_symbol_mode_fail_closed(self):
  for s,m in [('USDCHF','E2'),('AUDUSD','AU_CPI'),('AUD','E1')]:
   with self.assertRaises(ValueError):cal.event_set(s,m)
 def test_frozen_input(self):self.assertEqual(len(inp.input_config()[1]['Candidates']),54)
 def test_config_freezes(self):
  c,_=inp.input_config();p=c['FrozenEventContract'];self.assertEqual(p['FormalMode'],'E2');self.assertTrue(p['ModeChosenBeforeResults']);self.assertFalse(p['OptimizationStage']);self.assertFalse(p['B6CandidateCStrategyMatrixAllowed']);self.assertFalse(p['HistoricalReleaseTimeReconstructionAllowed']);self.assertFalse(p['FallbackToE0E1Allowed'])
 def test_supplement_bound(self):
  i=identity('a'*40,{});self.assertEqual(i['U10SupplementalConditionsFreezeSHA'],inp.SUPPLEMENT_SHA);self.assertEqual(i['SupplementalPrespecSHA256'],inp.SUPPLEMENT_HASH);self.assertEqual(i['EventCalendarSHA256'],inp.CALENDAR_SHA)
 def test_calendar_hash_reject(self):
  with patch.object(cal,'digest',return_value='bad'):
   with self.assertRaises(ValueError):cal.audit_calendar()
 def test_runtime_no_legacy_or_network(self):
  for name in ['u10_calendar.py','u10_execution.py','u10_reference.py']:
   tree=ast.parse((ROOT/'src/research/b7'/name).read_text());names=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
   self.assertFalse(any(x and ('urllib' in x or 'legacy' in x or 'event_filter_validation' in x) for x in names))

class InputMutations(unittest.TestCase):pass
for key in ['CandidateID','Symbol','PairRank','Direction','U09Status','U09Decision','FormalEntryMinute','FormalExitMinute','FormalExitDayOffset','FormalHoldingMinutes','EntryShiftMinutes','ExitShiftMinutes','FormalSL','FormalTP','FormalWeekdays','FormalDOMBuckets','FormalMonths','OFFMonths','CalendarFreeze','U09CandidateSHA256','U09CheckpointSHA256','U08SourceIdentity','U07SourceIdentity','U06SourceIdentity']:
 def check(self,k=key):
  d=inp.read(inp.INPUT);d['Candidates'][0][k]='MUTATED'
  with self.assertRaises(ValueError):inp.validate(d)
 setattr(InputMutations,'test_reject_'+key,check)
for key in ['CandidateCount','NoReplacement','FormalEventMode','ModeChosenBeforeResults','U10PerformanceEvaluated','CalendarSourceCommit']:
 def check(self,k=key):
  d=inp.read(inp.INPUT);d[k]='MUTATED'
  with self.assertRaises(ValueError):inp.validate(d)
 setattr(InputMutations,'test_top_'+key,check)
def test_order(self):
 for duplicate in [False,True]:
  d=inp.read(inp.INPUT)
  if duplicate:d['Candidates'][1]=d['Candidates'][0]
  else:d['Candidates'].reverse()
  with self.assertRaises(ValueError):inp.validate(d)
InputMutations.test_order_duplicate=test_order


def trade(e='2020-01-10 20:00:00',x='2020-01-10 23:00:00',close=None,pips=2):
 return dict(TradeID=object_hash([e,x]),EntryTime=e,ScheduledExitTime=x,PlannedEntryTimeJST=e,PlannedTimeExitJST=x,CloseTime=close or x,Pips=pips,FixedKey=['fixture'],ExitReason='SL' if close else 'TimeExit',EntryPrice=1,ClosePrice=1.1)

class OverlapAndMetrics(unittest.TestCase):
 def compare(self,ts,symbol='USDJPY',calendar=None):
  c=cal.audit_calendar() if calendar is None else calendar;a=opt.filter_modes(ts,symbol,cal.EventIndex(c));self.assertEqual(a,ref.filter_modes(ts,symbol,c));return a
 def test_inclusive_endpoints(self):
  idx=cal.EventIndex(cal.audit_calendar())
  for e,x,want in [('18:00','19:30',True),('23:30','23:59',True),('18:00','19:29',False),('23:31','23:59',False)]:self.assertEqual(bool(idx.matching('2020-01-10 '+e,'2020-01-10 '+x,['US_NFP'])),want)
 def test_overnight_fomc(self):
  m,ts,d=self.compare([trade('2020-01-29 23:00:00','2020-01-30 04:00:00')]);self.assertEqual(m['E1']['RemovedTrades'],1)
 def test_early_close_planned_exit(self):
  m,ts,d=self.compare([trade(close='2020-01-10 20:30:00')]);self.assertEqual(m['E2']['RemovedTrades'],1)
 def test_fallback_not_used(self):
  c=copy.deepcopy(cal.audit_calendar());c['Events']=[dict(CanonicalEventName='US_NFP',SourceDates=['2020-01-10'],FixedJST='23:01',WindowPlusMinusMinutes=120)]
  m,ts,d=self.compare([trade('2020-01-10 20:00:00','2020-01-10 21:00:00','2020-01-10 21:03:00')],calendar=c);self.assertEqual(m['E2']['RemovedTrades'],0)
 def test_multiple_remove_once(self):
  c=copy.deepcopy(cal.audit_calendar());c['Events']=[dict(CanonicalEventName=n,SourceDates=['2020-01-10'],FixedJST='21:30',WindowPlusMinusMinutes=120) for n in ['US_NFP','US_CPI']]
  m,ts,d=self.compare([trade()],calendar=c);self.assertEqual(m['E2']['RemovedTrades'],1);self.assertEqual(m['E2']['MultiEventOverlapTradeCount'],1);self.assertEqual(sum(m['E2']['RemovedByEvent'].values()),2)
 def test_period_adjacent_event_not_discarded(self):
  c={'Events':[dict(CanonicalEventName='US_NFP',SourceDates=['2024-01-01'],FixedJST='00:00',WindowPlusMinusMinutes=120)]}
  m,ts,d=self.compare([trade('2023-12-31 22:00:00','2023-12-31 23:00:00')],calendar=c);self.assertEqual(m['E2']['RemovedTrades'],1)
 def test_e0_and_subset_and_unchanged(self):
  t=[trade(),trade('2020-01-13 08:00:00','2020-01-13 09:00:00',pips=-1)];before=copy.deepcopy(t);m,ts,d=self.compare(t)
  self.assertEqual(t,before);self.assertEqual(m['E0']['RemovedTrades'],0);self.assertEqual(m['E0']['Retention'],1);self.assertEqual(m['E2']['Retention'],.5)
  for mode in ts:
   for x in ts[mode]:self.assertIn(x,t)
 def test_empty_retention_null(self):
  m,ts,d=self.compare([])
  for mode in m:self.assertIsNone(m[mode]['Retention']);self.assertEqual(m[mode]['RemovedTrades'],0)
 def test_order_and_dd(self):
  t=[trade('2020-02-03 08:00:00','2020-02-03 09:00:00',pips=-5),trade('2020-02-04 08:00:00','2020-02-04 09:00:00',pips=2)]
  a=self.compare(t);self.assertEqual(a,self.compare(list(reversed(t))));self.assertEqual(a[0]['E0']['Metrics']['MaxDDPips'],5)
 def test_discovery_filter_reject(self):
  for y in (2024,2025,2026):
   with self.assertRaises(ValueError):self.compare([trade(f'{y}-01-10 20:00:00',f'{y}-01-10 23:00:00')])

class GateAndStatus(unittest.TestCase):
 def test_exact_boundaries(self):
  m=metrics(trades=150,annual=30,losses=10,pf=1.10,positive=3);self.assertTrue(all(opt.gate_checks(m).values()));self.assertEqual(opt.gate_checks(m),ref.gate_checks(m))
  for k,v in [('Trades',149),('Losses',9),('AvgPips',0),('AvgPips',None),('PFpips',np.nextafter(1.1,0)),('PFState','INF'),('PFState','UNDEFINED'),('PositiveYearCount',2)]:
   b=copy.deepcopy(m);b[k]=v;self.assertFalse(all(opt.gate_checks(b).values()));self.assertEqual(opt.gate_checks(b),ref.gate_checks(b))
  for y in range(2020,2024):
   b=copy.deepcopy(m);b['Annual'][str(y)]['Trades']=29;self.assertFalse(all(opt.gate_checks(b).values()))
 def test_no_diagnostic_gate_no_mode_selection(self):
  r=record();o=empty_result(r);m=metrics();checks=opt.gate_checks(m)
  for retention,removed in [(.1,100),(1,0)]:
   modes=copy.deepcopy(o['Modes']);modes['E2'].update(Metrics=m,Retention=retention,RemovedTrades=removed);modes['E0']['Metrics']=metrics(avg=100,pf=100);modes['E1']['Metrics']=metrics(avg=200,pf=200)
   a=result(r,modes,checks,{x:[] for x in modes});self.assertEqual(a['Status'],'PASS_U10');self.assertEqual(a['FormalEventMode'],'E2')
 def test_e0_e1_pass_e2_fail_no_fallback(self):
  r=record();o=empty_result(r);modes=o['Modes'];modes['E0']['Metrics']=metrics();modes['E1']['Metrics']=metrics();bad=metrics(trades=149);modes['E2']['Metrics']=bad
  a=result(r,modes,opt.gate_checks(bad),{x:[] for x in modes});self.assertEqual(a['Status'],'DROP_U10_E2_GATE');self.assertEqual(a['FailedChecks'],['TotalTrades'])
 def test_all_failures_canonical(self):
  o=empty_result(record());self.assertEqual(o['FailedChecks'],list(opt.CHECKS));self.assertEqual(o['Status'],'DROP_U10_E2_GATE')
 def test_no_dd_gate(self):
  m=metrics();m['MaxDDPips']=1e20;self.assertTrue(all(opt.gate_checks(m).values()))
 def test_schema_and_fixed_fields(self):
  r=record();o=empty_result(r);self.assertEqual(validate_result(o,r),o)
  for k in r:
   d=copy.deepcopy(o);d[k]='changed'
   with self.assertRaises(ValueError):validate_result(d,r)
 def test_future_projection_rejects_drop(self):
  r=record()
  with self.assertRaises(ValueError):project_u10p(r,empty_result(r),'a'*64,'b'*64,'c'*40)

class ExecutionReplay(unittest.TestCase):
 def test_actual_schedule_not_anchor(self):
  from test_b7_u06 import bars
  r=record(entry=541,exit=571);r['AnchorEntryMinute']=540;r['AnchorExitMinute']=570;b=bars('2020-02-03 09:00',n=45);c=cal.audit_calendar()
  a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-03'],c);self.assertEqual(a,ref.evaluate_candidate(b,r,c,['2020-02-03']));self.assertEqual(a[1]['Streams']['E0'][0]['EntryTime'],'2020-02-03 09:01:00')
 def test_long_short_tp_and_overnight(self):
  from test_b7_u06 import bars
  for direction in ('LONG','SHORT'):
   for tp in (None,10):
    for e,x,o,ds in [(540,570,0,'2020-02-03 08:55'),(1380,240,1,'2020-01-29 22:55')]:
     r=record(entry=e,exit=x,offset=o,direction=direction,tp=tp);b=bars(ds,n=320);c=cal.audit_calendar();days=[ds[:10]]
     self.assertEqual(opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,days,c),ref.evaluate_candidate(b,r,c,days))
 def test_calendar_exclusion(self):
  from test_b7_u06 import bars
  for k,v in [('FormalWeekdays',[1]),('FormalDOMBuckets',['D2']),('FormalMonths',[3])]:
   r=record();r[k]=v;b=bars('2020-02-03 08:55',n=45);a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-02-03']);self.assertEqual(a[1]['Streams']['E0'],[])
 def test_missing_not_removed(self):
  from test_b7_u06 import bars
  r=record(entry=1200,exit=1380);b=bars('2020-01-10 20:00',n=190).iloc[1:];a=opt.evaluate_candidate(opt.Engine(b,'USDJPY'),r,['2020-01-10']);self.assertEqual(a[0]['Modes']['E2']['RemovedTrades'],0)
 def test_discovery_reject(self):
  from test_b7_u06 import bars
  for y in (2024,2025,2026):
   with self.assertRaises(ValueError):opt.Engine(bars(f'{y}-02-03'),'USDJPY')
   with self.assertRaises(ValueError):ref.evaluate_candidate(bars(f'{y}-02-03'),record(),cal.audit_calendar(),[])

from test_b7_u06 import Execution as _Execution
class ExecutionCompatibility(_Execution):
 def compare(self,b,d='LONG',sl=15,tp=10,entry=None,scheduled=None):
  e=b.index[0] if entry is None else pd.Timestamp(entry);x=e+pd.Timedelta(minutes=30) if scheduled is None else pd.Timestamp(scheduled)
  a=opt.Engine(b,'USDJPY').execute(d,e,x,sl,(),tp);self.assertEqual(a,ref.execute(b,'USDJPY',d,e,x,sl,(),tp));return a
del _Execution
class IntegratedModes(unittest.TestCase):
 def fixture(self):
  ts=[];events=[]
  for y in range(2020,2024):
   days=pd.bdate_range(f'{y}-02-03',periods=38)
   for i,d in enumerate(days):ts.append(trade(str(d+pd.Timedelta(hours=20)),str(d+pd.Timedelta(hours=23)),pips=-1 if i%4==0 else 2))
   events.extend(str(d.date()) for d in days[:2])
  c={'Events':[dict(CanonicalEventName='US_NFP',SourceDates=events,FixedJST='21:30',WindowPlusMinusMinutes=120)]};return ts,c
 def test_nonempty_full_metrics_reference_e2_drop(self):
  ts,c=self.fixture();a=opt.filter_modes(ts,'EURJPY',cal.EventIndex(c));self.assertEqual(a,ref.filter_modes(ts,'EURJPY',c))
  self.assertTrue(all(opt.gate_checks(a[0]['E0']['Metrics']).values()));self.assertTrue(all(opt.gate_checks(a[0]['E1']['Metrics']).values()));self.assertFalse(all(opt.gate_checks(a[0]['E2']['Metrics']).values()))
  out=result(record('EURJPY'),a[0],opt.gate_checks(a[0]['E2']['Metrics']),a[1]);self.assertEqual(out['Status'],'DROP_U10_E2_GATE');self.assertEqual(out['FailedChecks'],['TotalTrades']);validate_result(out,record('EURJPY'))
 def test_pass_projection_schema(self):
  ts,c=self.fixture();c={'Events':[]};a=opt.filter_modes(ts,'EURJPY',cal.EventIndex(c));r=record('EURJPY');out=result(r,a[0],opt.gate_checks(a[0]['E2']['Metrics']),a[1]);self.assertEqual(out['Status'],'PASS_U10');validate_result(out,r)
  p=project_u10p(r,out,'a'*64,'b'*64,'c'*40);self.assertEqual(p['U10CandidateSHA256'],'a'*64);self.assertEqual(p['FormalEntryMinute'],r['FormalEntryMinute']);self.assertEqual(p['E2TradeStreamSHA256'],out['TradeStreamSHA256']['E2'])
 def test_summary_completion_order(self):
  a=empty_result(record('AUDUSD'));b=empty_result(record('EURJPY'));self.assertEqual(summaries([a,b]),summaries([b,a]))
 def test_hashseed_deterministic(self):
  script='from test_b7_u10 import *; print(canonical(empty_result(record())))';outputs=[]
  for seed in ('1','93'):
   env={**os.environ,'PYTHONHASHSEED':seed,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')+os.pathsep+str(ROOT/'tests')};outputs.append(subprocess.check_output([sys.executable,'-c',script],env=env,cwd=ROOT))
  self.assertEqual(*outputs)
 def test_notebook_flags_default_false(self):
  for name in ('b7_u10_event_e2.ipynb','b7_u10_finalize_only.ipynb'):
   flags=[]
   for c in json.loads((ROOT/'notebooks'/name).read_text())['cells']:
    if c['cell_type']=='code':
     self.assertEqual(c['outputs'],[])
     for n in ast.walk(ast.parse(''.join(c['source']))):
      if isinstance(n,ast.Assign):
       for t in n.targets:
        if isinstance(t,ast.Name) and t.id.startswith('RUN_'):flags.append(ast.literal_eval(n.value))
   self.assertTrue(flags);self.assertFalse(any(flags))
 def test_approvals_and_import_no_run(self):
  with self.assertRaises(PermissionError):rt.run_formal({},'',None,None)
  with self.assertRaises(PermissionError):fin.finalize_from_completed_jobs(None,None,'','')
  script="import b7.stage1_input as s;s.read_mt5=lambda *a,**k:(_ for _ in ()).throw(AssertionError('M1'));import b7.u10_runtime,b7.u10_finalize_only;print('NO_RUN')"
  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')};self.assertIn(b'NO_RUN',subprocess.check_output([sys.executable,'-c',script],env=env))
 def test_completed_preflight_no_price_or_evaluator(self):
  # Actual preflight path, with environment/git/release external facts supplied by fixture.
  env=dict(Python='3.13.16',NumPy='2.3.5',pandas='2.2.3')
  def git(*args):return 'a'*40 if args==('rev-parse','HEAD') else ''
  original=rt.read
  def read(p):
   if Path(p).name in ('test_results.json','smoke_results.json'):return {'Status':'PASS'}
   return original(p)
  with patch.object(rt.shared,'git',side_effect=git),patch.object(rt.shared,'release_manifest'),patch.object(rt.shared,'environment',return_value=env),patch.object(rt,'read',side_effect=read),patch.object(rt,'audit_inputs',side_effect=AssertionError('no M1')),patch.object(rt.shared,'run_tests',side_effect=AssertionError('no evaluator tests')),patch('b7.u10_smoke.run_smoke',side_effect=AssertionError('no smoke recomputation')):
   p=rt.preflight({},'a'*40,completed_only=True)
  self.assertEqual(p['Smoke']['JobRecomputation'],False)
