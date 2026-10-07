import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import u07_selection as sel, u07_input as inp, u07_runtime as rt, u07_finalize_only as fin
from b7 import u07_execution as opt, u07_reference as ref
from b7.u07_artifacts import identity
from b7.stage1_contract import ROOT, Structure, digest, object_hash, canonical
from b7.stage1_metrics import summarize, gate
from test_b7_u06 import Execution as U06Execution

# Run the existing execution edge fixtures through U07's actual reference/Engine exports.
class ExecutionCompatibility(U06Execution):
    def compare(self,b,d='LONG',sl=15,tp=10,entry=None,scheduled=None):
        e=b.index[0] if entry is None else pd.Timestamp(entry)
        x=e+pd.Timedelta(minutes=30) if scheduled is None else pd.Timestamp(scheduled)
        a=opt.Engine(b,'USDJPY').execute(d,e,x,sl,(),tp)
        self.assertEqual(a,ref.execute(b,'USDJPY',d,e,x,sl,(),tp));return a
    def test_friday_no_monday_reconnect(self):
        from test_b7_u06 import bars
        b=bars('2020-02-07 23:45',n=15)
        b=pd.concat([b,bars('2020-02-10 00:15')])
        self.assertEqual(self.compare(b)['Status'],'MISSING_EXIT')


del U06Execution  # Do not rediscover the imported base test class.

def metric(pf=1.1,positive=3,median=10):
    return dict(Trades=150,Losses=10,AvgPips=1,PFState='FINITE',PFpips=pf,PositiveYearCount=positive,
                MedianAnnualAvgPips=median,Annual={str(y):dict(Trades=30) for y in range(2020,2024)})

def record():
    s=Structure('USDJPY','LONG',0,540,30)
    return dict(CandidateID=s.candidate_id,Symbol=s.symbol,PairRank=1,Schedule=s.definition(),FormalSL=15,FormalTP=None,
                U06Status='PASS_U06',SourceCandidateSHA256='a'*64,SourceCheckpointSHA256='b'*64)

def streams():
    out={w:[] for w in range(5)}
    for y in range(2020,2024):
        for w in range(5):
            dates=pd.date_range(f'{y}-02-01',f'{y}-12-01')
            dates=dates[dates.weekday==w][:40]
            for n,d in enumerate(dates):
                e=d+pd.Timedelta(hours=9)
                out[w].append(dict(Status='OK',EntryTime=str(e),CloseTime=str(e+pd.Timedelta(minutes=30)),
                                   Pips=-1 if n%4==0 else 2,FixedKey=[w]))
    return out

class Classification(unittest.TestCase):
    def test_exact_core(self):self.assertEqual(sel.classification(metric()),'CORE')
    def test_exact_support(self):self.assertEqual(sel.classification(metric(1.05)),'SUPPORT')
    def test_between(self):self.assertEqual(sel.classification(metric(1.0999)),'SUPPORT')
    def test_core_not_support(self):self.assertNotEqual(sel.classification(metric(1.2)),'SUPPORT')
    def test_sample_failure(self):
        for k,v in [('Trades',149),('Losses',9),('AvgPips',0)]:
            m=metric();m[k]=v;self.assertEqual(sel.classification(m),'NON_SUPPORT')
    def test_annual_failure(self):
        m=metric();m['Annual']['2021']['Trades']=29;self.assertEqual(sel.classification(m),'NON_SUPPORT')
    def test_three_year_pass(self):self.assertEqual(sel.classification(metric(positive=3)),'CORE')
    def test_two_year_fail(self):self.assertEqual(sel.classification(metric(positive=2)),'NON_SUPPORT')
    def test_pf_states(self):
        for state in ('INF','UNDEFINED'):
            m=metric();m.update(PFState=state,PFpips=None);self.assertEqual(sel.classification(m),'NON_SUPPORT')

class Policy(unittest.TestCase):
    def test_anchor_core(self):self.assertEqual(sel.select(record(),streams())['Status'],'PASS_U07')
    def test_anchor_support_no_rescue(self):
        ms=[metric(1.06)]+[metric(2)]*4
        with patch.object(sel,'aggregate',side_effect=ms):r=sel.select(record(),{w:[] for w in range(5)})
        self.assertEqual(r['Status'],'DROP_U07_ANCHOR_NOT_CORE');self.assertEqual(r['Sets'],[])
    def test_anchor_non_support_no_rescue(self):
        s=streams();s[0]=[];r=sel.select(record(),s)
        self.assertEqual(r['Status'],'DROP_U07_ANCHOR_NOT_CORE');self.assertIsNone(r['FormalWeekdays'])
    def test_anchor_mutation(self):
        r=record();r['Schedule']['Weekday']=1
        with self.assertRaises(ValueError):sel.select(r,streams())
    def test_generated(self):
        g,u=sel.generated_sets(2,['SUPPORT','NON_SUPPORT','CORE','CORE','NON_SUPPORT'])
        self.assertEqual(g,{'W0':[2],'W1':[2,3],'W2':[0,2,3],'W3':[0,1,2,3,4]});self.assertEqual(len(u),4)
    def test_dedup_alias_priority(self):
        g,u=sel.generated_sets(0,['CORE']*5)
        self.assertEqual(len(u),2);self.assertEqual(u[0]['Aliases'],['W3','W2','W1']);self.assertEqual(u[0]['SetName'],'W3')
    def test_no_arbitrary_subsets(self):
        from itertools import product
        for c in product(('CORE','SUPPORT','NON_SUPPORT'),repeat=4):
            g,u=sel.generated_sets(0,['CORE',*c]);self.assertLessEqual(len(u),4)
            self.assertEqual({tuple(s['Weekdays']) for s in u},{tuple(v) for v in g.values()})
    def test_combined_not_average(self):
        s=streams();s[1]=s[1][:40]
        m=sel.aggregate([s[0],s[1]])
        self.assertEqual(m,summarize(s[0]+s[1]));self.assertEqual(m['Trades'],200)
        self.assertEqual(m['Annual']['2020']['Trades'],80)
    def test_duplicates(self):
        t=streams()[0][0]
        with self.assertRaises(ValueError):sel.aggregate([[t],[{**t,'FixedKey':[999]}]])
    def test_dd_order_and_entry_year(self):
        ts=[dict(EntryTime='2020-12-31 23:59:00',CloseTime='2021-01-01 00:30:00',Pips=-5,FixedKey=[0]),
            dict(EntryTime='2020-12-31 23:00:00',CloseTime='2021-01-01 00:00:00',Pips=10,FixedKey=[1])]
        m=sel.aggregate([ts]);self.assertEqual(m['MaxDDPips'],5);self.assertEqual(m['Annual']['2020']['Trades'],2)
        self.assertEqual(m,sel.aggregate([list(reversed(ts))]))
    def sets(self,spec):
        return [dict(SetName=f'W{i}',Weekdays=list(range(i+1)),FormalGatePASS=True,Metrics=metric(positive=p,median=m)) for i,(m,p) in enumerate(spec)]
    def test_best_metric_primary(self):self.assertEqual(sel.choose(self.sets([(10,4),(11,3)]))[0]['SetName'],'W1')
    def test_best_supplement_positive_years(self):self.assertEqual(sel.choose(self.sets([(10,4),(10,3)]))[0]['SetName'],'W0')
    def test_best_supplement_priority(self):self.assertEqual(sel.choose(self.sets([(10,4)]*4))[0]['SetName'],'W3')
    def test_exact80_widest(self):self.assertEqual(sel.choose(self.sets([(10,4),(8,4)]))[2]['SetName'],'W1')
    def test_below80(self):self.assertEqual(sel.choose(self.sets([(10,4),(7.999999,4)]))[2]['SetName'],'W0')
    def test_positive_degradation(self):self.assertEqual(sel.choose(self.sets([(10,4),(9,3)]))[2]['SetName'],'W0')
    def test_final_tie_priority(self):
        ss=self.sets([(10,4)]*4)
        for s in ss:s['Weekdays']=[0]
        self.assertEqual(sel.choose(ss)[2]['SetName'],'W3')
    def test_w0_contradiction_stop(self):
        with self.assertRaises(ValueError):sel.choose([])
    def test_deterministic_trade_order(self):
        a=streams();b={w:list(reversed(a[w])) for w in reversed(range(5))}
        self.assertEqual(sel.select(record(),a),sel.select(record(),b))
    def test_nonempty_reference_optimized(self):
        r=record();parts=[];days=[]
        for w,ts in streams().items():
            for n,t in enumerate(ts):
                e=pd.Timestamp(t['EntryTime']);days.append(e.normalize())
                p=100 if n%4==0 else 100.05
                parts.append(pd.DataFrame(dict(Open=[100,p],High=[100,p],Low=[100,p],Close=[100,p]),index=[e,e+pd.Timedelta(minutes=30)]))
        bars=pd.concat(parts).sort_index();a=opt.evaluate_candidate(opt.Engine(bars,'USDJPY'),r,sorted(days));b=ref.evaluate_candidate(bars,r,sorted(days))
        self.assertEqual(a,b);self.assertEqual(a[0]['Status'],'PASS_U07');self.assertTrue(a[0]['Sets'])
    def test_discovery_reject(self):
        from test_b7_u06 import bars
        for year in (2024,2025,2026):
            with self.assertRaises(ValueError):opt.Engine(bars(f'{year}-02-04'),'USDJPY')
            with self.assertRaises(ValueError):ref.evaluate_candidate(bars(f'{year}-02-04'),record(),[])

class InputAudit(unittest.TestCase):
    def setUp(self):
        self.data=inp.read(inp.INPUT);self.audit=inp.read(ROOT/'results/b7/u06/drive_checkpoint_audit.json')
        self.identity=inp.read(ROOT/'results/b7/u06/input_identity.json');self.original=inp.read(ROOT/'research_inputs/b7/u06_selected72_input.json')
    def check(self):return inp.validate(self.data,self.audit,self.identity,self.original)
    def test_frozen56(self):self.assertEqual(len(inp.input_config()[1]['Candidates']),56)
    def test_sha_mismatch(self):
        with patch.object(inp,'digest',return_value='wrong'):
            with self.assertRaises(ValueError):inp.input_config()
    def test_count(self):
        self.data['Candidates'].pop()
        with self.assertRaises(ValueError):self.check()
    def test_duplicate(self):
        self.data['Candidates'][-1]=self.data['Candidates'][0]
        with self.assertRaises(ValueError):self.check()
    def test_no_replacement(self):
        self.data['NoReplacement']=False
        with self.assertRaises(ValueError):self.check()
    def test_candidate_mutations(self):
        for key,value in [('U06Status','DROP_U06_SL'),('SourceCandidateSHA256','bad'),('SourceCheckpointSHA256','bad'),('FormalSL',None),('FormalTP','TP_NONE')]:
            with self.subTest(key=key):
                before=copy.deepcopy(self.data);self.data['Candidates'][0][key]=value
                with self.assertRaises((ValueError,TypeError)):self.check()
                self.data=before
    def test_schedule_anchor_mutations(self):
        for key in ('EntryMinute','Weekday'):
            before=copy.deepcopy(self.data);self.data['Candidates'][0]['Schedule'][key]+=1
            with self.assertRaises(ValueError):self.check()
            self.data=before

class CheckpointAndFinalize(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.producer='a'*40;self.env=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
        self.identity=identity(self.producer,self.env);self.records=inp.input_config()[1]['Candidates']
        self.local=self.root/'local';self.drive=self.root/'drive'
        rt.init_root(self.local,self.identity,False);rt.init_root(self.drive,self.identity,False)
        for r in self.records:
            result=sel.select(r,{w:[] for w in range(5)}) # Synthetic absence only; no M1 opened.
            l=self.local/'jobs'/r['CandidateID'];d=self.drive/'jobs'/r['CandidateID']
            rt.complete_local(l,self.identity,r,result);rt.mirror_job(l,d,self.identity,r)
        self.job=self.drive/'jobs'/self.records[0]['CandidateID']
        self.proof=dict(Status='PASS',ProducerImplementationSHA=self.producer,FinalizerImplementationSHA=self.producer,FinalizerEnvironment={**self.env,'Python':'3.13.16'})
    def audit(self):return fin.audit_source(self.drive,self.proof['FinalizerEnvironment'],self.producer)
    def test_all56(self):self.assertEqual(self.audit()[1]['JobCount'],56)
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
        for key in ('U07ConfigSHA256','U07InputSHA256','M1ExactIdentity','U06ResultFreezeSHA','CandidateIDs','FullPrespecSHA256'):
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
        self.assertEqual(values[-1],dict(ProcessedJobs=56,ExpectedJobs=56));self.assertTrue(all(set(v)=={'ProcessedJobs','ExpectedJobs'} for v in values))
    def test_source_unchanged_and_no_recompute(self):
        before={str(p):p.read_bytes() for p in self.drive.rglob('*') if p.is_file()}
        targets=['b7.stage1_input.load_discovery','b7.stage1_input.read_mt5','b7.u06_execution.Engine','b7.u06_execution.evaluate',
                 'b7.u06_selection.select','b7.u07_selection.select','b7.u07_selection.choose','b7.u07_execution.Engine',
                 'b7.u07_execution.evaluate_candidate','b7.u07_reference.evaluate_candidate','b7.u07_runtime.Engine',
                 'b7.u07_runtime.load_discovery','b7.u07_runtime.evaluate_candidate','b7.stage1_runtime.run_tests']
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
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json'):
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

if __name__=='__main__':unittest.main()

class ReleaseGuards(unittest.TestCase):
    def test_notebooks_all_flags_false(self):
        import ast
        for name in ('b7_u07_weekday.ipynb','b7_u07_finalize_only.ipynb'):
            cells=json.loads((ROOT/'notebooks'/name).read_text())['cells'];flags=[]
            for cell in cells:
                if cell['cell_type']!='code':continue
                self.assertEqual(cell['outputs'],[])
                for node in ast.walk(ast.parse(''.join(cell['source']))):
                    if isinstance(node,ast.Assign):
                        for target in node.targets:
                            if isinstance(target,ast.Name) and target.id.startswith('RUN_'):
                                self.assertIsInstance(node.value,ast.Constant);self.assertIs(node.value.value,False);flags.append(target.id)
            self.assertTrue(flags)
    def test_config_best_supplement(self):
        cfg,_=inp.input_config()
        self.assertEqual(cfg['BestTieSupplement']['BestRanking'],['MedianAnnualAvgPips DESC','PositiveYearCount DESC','W3 > W2 > W1 > W0'])
        self.assertTrue(cfg['BestTieSupplement']['PlateauUnchanged'])
    def test_process_determinism(self):
        import subprocess,sys,os
        script='from test_b7_u07 import record,streams,sel,canonical; print(canonical(sel.select(record(),streams())))'
        values=[]
        for seed in ('1','79'):
            env={**os.environ,'PYTHONHASHSEED':seed,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')+os.pathsep+str(ROOT/'tests')}
            values.append(subprocess.check_output([sys.executable,'-c',script],env=env,cwd=ROOT))
        self.assertEqual(*values)
    def test_nonaverage_unequal_weekdays(self):
        a=streams()[0];b=streams()[1][:40]
        for t in b:t['Pips']=10
        m=sel.aggregate([a,b]);unweighted=(summarize(a)['AvgPips']+summarize(b)['AvgPips'])/2
        self.assertNotEqual(m['AvgPips'],unweighted)
        self.assertEqual(m['AvgPips'],(summarize(a)['TotalPips']+summarize(b)['TotalPips'])/(len(a)+len(b)))
    def test_pass_checkpoint_roundtrip(self):
        r=record();result=sel.select(r,streams());i={'CandidateIDs':[r['CandidateID']]}
        with tempfile.TemporaryDirectory() as tmp:
            l=Path(tmp)/'local';d=Path(tmp)/'drive'
            rt.complete_local(l,i,r,result);rt.mirror_job(l,d,i,r)
            self.assertEqual(rt.validate_drive(d,i,r),result)
    def test_w0_identity_and_formal_gate(self):
        r=sel.select(record(),streams());w0=next(s for s in r['Sets'] if 'W0' in s['Aliases'])
        self.assertEqual(w0['Metrics'],r['WeekdayDiagnostics'][0]['Metrics']);self.assertTrue(w0['FormalGatePASS'])
    def test_empty_missing_not_zero_trade(self):
        r=sel.select(record(),{w:[] for w in range(5)})
        for d in r['WeekdayDiagnostics']:
            self.assertEqual(d['Metrics']['Trades'],0);self.assertIsNone(d['Metrics']['AvgPips'])
    def test_no_approval_import_run(self):
        with self.assertRaises(PermissionError):rt.run_formal({},'',None,None)
        with self.assertRaises(PermissionError):fin.finalize_from_completed_jobs(None,None,'','')
