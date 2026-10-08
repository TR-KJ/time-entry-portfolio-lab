import unittest, tempfile, copy, json, subprocess, os, sys
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import pandas as pd
import numpy as np
from b7 import u08_selection as sel, u08_input as inp, u08_runtime as rt, u08_finalize_only as fin
from b7 import u08_execution as opt, u08_reference as ref
from b7.u08_calendar import ScalarView, VectorView, dom_bucket
from b7.u08_artifacts import identity
from b7.stage1_contract import ROOT, Structure, digest, canonical
from b7.stage1_metrics import summarize, gate
from test_b7_u06 import Execution as _Execution


def record():
    s=Structure('USDJPY','LONG',0,540,30)
    return dict(CandidateID=s.candidate_id,Symbol=s.symbol,PairRank=1,Schedule=s.definition(),FormalSL=15,FormalTP=None,
                AnchorWeekday=0,FormalWeekdays=[0,1,2,3,4],SetName='W1',U07Status='PASS_U07',U07CandidateSHA256='a'*64,
                U07CheckpointSHA256='b'*64,U07ProducerImplementationSHA='c'*40,U06SourceIdentity={})


def metrics(avg=1,pf=1.2,median=1,positive=4,negative=0,dd=10,total=200,trades=200,annual=50,losses=20):
    return dict(Trades=trades,Wins=trades-losses,Losses=losses,ZeroPips=0,AvgPips=avg,TotalPips=total,PFState='FINITE',PFpips=pf,
                MaxDDPips=dd,PositiveYearCount=positive,NegativeYearCount=negative,MedianAnnualAvgPips=median,
                Annual={str(y):dict(Trades=annual) for y in range(2020,2024)})


def bad(negative=4,avg=-1,pf=.8,total=-20):return metrics(avg,pf,negative=negative,total=total,trades=80,annual=20)
def better(n=1):return metrics(avg=1+n,pf=1.2+n,median=1+n)


class FakeView:
    """Explicit metric oracle for policy branches, independent of price/calendar code."""
    def __init__(self, values):self.values=values;self.calls=[]
    def metrics(self,buckets=None,months=None):
        key=(None if buckets is None else tuple(buckets),None if months is None else tuple(months));self.calls.append(key)
        return copy.deepcopy(self.values[key])


def dom_view(first=None,second=None,off=2):
    values={(None,None):metrics()}
    for i,b in enumerate(sel.BUCKETS):values[((b,),None)]=bad(avg=-3+i) if i<off else metrics(trades=80,annual=20)
    if off:
        values[(('D2','D3'),None)]=better(1) if first is None else first
    if off>=2:values[(('D3',),None)]=better(2) if second is None else second
    return FakeView(values)


def month_view(second=None,eligible=(1,2,3),failed_lomo=()):
    buckets=sel.BUCKETS;values={(buckets,None):metrics()}
    for m in range(1,13):
        values[(buckets,(m,))]=bad(avg=-4+m) if m in eligible else metrics(trades=16,annual=4)
        values[(buckets,tuple(n for n in range(1,13) if n!=m))]=metrics() if m in failed_lomo else better(1)
    values[(buckets,tuple(range(3,13)))]=better(2) if second is None else second
    return FakeView(values)


def trades():
    out=[]
    for y in range(2020,2024):
        days=pd.bdate_range(f'{y}-02-03',periods=200)
        for n,day in enumerate(days):
            e=day+pd.Timedelta(hours=9)
            out.append(dict(Status='OK',EntryTime=str(e),CloseTime=str(e+pd.Timedelta(minutes=30)),Pips=-1 if n%4==0 else 2,FixedKey=[0]))
    return out


class Comparisons(unittest.TestCase):
    def test_pf_finite_strict(self):self.assertTrue(sel.improvement(metrics(),better())['Adopt'])
    def test_pf_equal(self):
        m=better();m['PFpips']=1.2;self.assertFalse(sel.improvement(metrics(),m)['Checks']['PFpips'])
    def test_pf_all_state_crossings(self):
        for a in ('FINITE','INF','UNDEFINED'):
            for b in ('FINITE','INF','UNDEFINED'):
                x=metrics();y=better();x.update(PFState=a,PFpips=0 if a=='FINITE' else None);y.update(PFState=b,PFpips=1 if b=='FINITE' else None)
                self.assertEqual(sel.improvement(x,y)['Checks']['PFpips'],a==b=='FINITE')
    def test_finite_zero(self):
        a=metrics(pf=0);b=better();b['PFpips']=.1;self.assertTrue(sel.improvement(a,b)['Checks']['PFpips']);self.assertTrue(sel.pf_off(a))
    def test_off_pf_states(self):
        for state in ('INF','UNDEFINED'):
            m=bad();m.update(PFState=state,PFpips=None);self.assertFalse(sel.dom_off(m,True));self.assertFalse(sel.month_off(m,True))
    def test_median_null_either(self):
        for a,b in [(None,2),(1,None),(None,None)]:
            self.assertFalse(sel.improvement(metrics(median=a),metrics(median=b))['Checks']['MedianAnnualAvgPips'])
    def test_each_comparison_required(self):
        for key,value in [('AvgPips',1),('PFpips',1.2),('MedianAnnualAvgPips',1),('PositiveYearCount',3),('MaxDDPips',11)]:
            m=better();m[key]=value;self.assertFalse(sel.improvement(metrics(),m)['Adopt'],key)
    def test_no_absolute_floor(self):
        m=better();m.update(AvgPips=1.0000001,PFpips=1.2000001,MedianAnnualAvgPips=1.0000001)
        self.assertTrue(sel.improvement(metrics(),m)['Adopt'])
    def test_no_three_year_median(self):
        ts=trades();ts=[t for t in ts if not t['EntryTime'].startswith('2023')]+[t for t in ts if t['EntryTime'].startswith('2023')][:29]
        m=summarize(ts);self.assertIsNone(m['MedianAnnualAvgPips'])
        self.assertFalse(sel.improvement(metrics(),m)['Checks']['MedianAnnualAvgPips'])


class DOMPolicy(unittest.TestCase):
    def test_boundaries(self):
        for d,want in [(1,'D1'),(10,'D1'),(11,'D2'),(20,'D2'),(21,'D3'),(28,'D3'),(29,'D3'),(30,'D3'),(31,'D3')]:self.assertEqual(dom_bucket(d),want)
    def test_exact20(self):self.assertTrue(sel.dom_sample(metrics(trades=40,annual=10),metrics())['MinimumSamplePASS'])
    def test_below20(self):self.assertFalse(sel.dom_sample(metrics(trades=39,annual=10),metrics())['MinimumSamplePASS'])
    def test_one_year_below(self):
        m=metrics(trades=40,annual=10);m['Annual']['2022']['Trades']=9;self.assertFalse(sel.dom_sample(m,metrics())['MinimumSamplePASS'])
    def test_no_display_rounding(self):
        self.assertFalse(sel.dom_sample(metrics(trades=20000,annual=10000),metrics(trades=100001,annual=10000))['MinimumSamplePASS'])
    def test_off_all_required(self):
        self.assertTrue(sel.dom_off(bad(),True));self.assertFalse(sel.dom_off(bad(),False))
        for k,v in [('TotalPips',0),('AvgPips',0),('PFpips',1),('NegativeYearCount',2)]:
            m=bad();m[k]=v;self.assertFalse(sel.dom_off(m,True),k)
    def test_ranking_each_priority(self):
        a=dict(Metrics=bad(),Order=1)
        for k,v in [('NegativeYearCount',3),('AvgPips',-.9),('PFpips',.9),('TotalPips',-19)]:
            b=copy.deepcopy(a);b['Metrics'][k]=v;self.assertLess(sel.off_key(a),sel.off_key(b),k)
        self.assertLess(sel.off_key({**a,'Order':0}),sel.off_key(a))
    def test_no_off(self):
        d=sel.dom_stage(dom_view(off=0));self.assertEqual(d['AdoptedState'],'DOM0');self.assertEqual(len(d['States']),1)
    def test_one_off_only(self):
        d=sel.dom_stage(dom_view(off=1));self.assertEqual(d['AdoptedState'],'DOM1');self.assertEqual(len(d['States']),2)
    def test_two_adopt_one_active_bucket(self):
        d=sel.dom_stage(dom_view());self.assertEqual(d['AdoptedState'],'DOM2');self.assertEqual(d['ActiveBuckets'],['D3'])
    def test_first_reject_no_alternate_no_dom2(self):
        v=dom_view(first=metrics());d=sel.dom_stage(v);self.assertEqual(d['AdoptedState'],'DOM0');self.assertEqual(len(d['States']),2)
        self.assertEqual(v.calls.count((('D3',),None)),1) # Initial diagnostic only, no DOM2 evaluation.
    def test_second_reject_keeps_dom1(self):self.assertEqual(sel.dom_stage(dom_view(second=better(1)))['AdoptedState'],'DOM1')
    def test_initial_candidates_never_regenerated(self):
        v=dom_view(off=1);d=sel.dom_stage(v);self.assertEqual(d['OFFRanking'],['D1']);self.assertEqual(len(v.calls),5)
    def test_max2_off_limit(self):
        d=sel.dom_stage(dom_view(off=2));self.assertEqual(len(d['OFFBuckets']),2);self.assertEqual(len(d['States']),3)
    def test_final_gate_drop_no_fallback_no_month(self):
        m=better(2);m['Trades']=149
        with patch.object(sel,'month_stage',side_effect=AssertionError('Month forbidden')):
            r=sel.select(record(),dom_view(second=m))
        self.assertEqual(r['DOM']['AdoptedState'],'DOM2');self.assertEqual(r['Status'],'DROP_U08_DOM_FINAL_GATE');self.assertIsNone(r['Month'])
    def test_dom1_gate_failure_no_fallback(self):
        m=better();m['Losses']=9;r=sel.select(record(),dom_view(first=m,off=1))
        self.assertEqual(r['DOM']['AdoptedState'],'DOM1');self.assertEqual(r['Status'],'DROP_U08_DOM_FINAL_GATE')
    def test_final_gate_exact_boundaries(self):
        m=metrics(trades=150,annual=30,losses=10,pf=1.1,positive=3);self.assertTrue(gate(m))
        for k,v in [('Trades',149),('Losses',9),('PFpips',1.099999),('PositiveYearCount',2),('AvgPips',0)]:
            x=copy.deepcopy(m);x[k]=v;self.assertFalse(gate(x),k)
        m['Annual']['2023']['Trades']=29;self.assertFalse(gate(m))


class MonthPolicy(unittest.TestCase):
    def test_sample_boundaries(self):
        self.assertTrue(sel.month_sample(metrics(trades=16,annual=3)))
        self.assertFalse(sel.month_sample(metrics(trades=15,annual=3)))
        m=metrics(trades=16,annual=3);m['Annual']['2021']['Trades']=2;self.assertFalse(sel.month_sample(m))
    def test_initial_off(self):
        self.assertTrue(sel.month_off(bad(),True));self.assertFalse(sel.month_off(bad(),False))
        for k,v in [('TotalPips',0),('PFpips',1),('NegativeYearCount',2)]:
            m=bad();m[k]=v;self.assertFalse(sel.month_off(m,True))
    def test_no_extra_avg_condition(self):
        # Deliberately inconsistent isolated predicate fixture detects an added Avg gate.
        m=bad();m['AvgPips']=1;self.assertTrue(sel.month_off(m,True))
    def test_all12_lomo(self):
        v=month_view(eligible=());m=sel.month_stage(v,sel.BUCKETS)
        self.assertEqual([x['Month'] for x in m['LOMO']],list(range(1,13)))
        for n in range(1,13):self.assertIn((sel.BUCKETS,tuple(k for k in range(1,13) if k!=n)),v.calls)
        self.assertEqual(len(v.calls),25)
    def test_initial_off_needs_lomo(self):
        m=sel.month_stage(month_view(eligible=(1,),failed_lomo=(1,)),sel.BUCKETS)
        self.assertEqual(m['InitialOFFCandidates'],[1]);self.assertEqual(m['FormalOFFCandidates'],[]);self.assertEqual(m['AdoptedState'],'M0')
    def test_m1(self):self.assertEqual(sel.month_stage(month_view(eligible=(1,)),sel.BUCKETS)['AdoptedState'],'M1')
    def test_m2(self):
        m=sel.month_stage(month_view(),sel.BUCKETS);self.assertEqual(m['OFFMonths'],[1,2]);self.assertEqual(m['AdoptedState'],'M2')
    def test_m2_fail_no_rank3(self):
        v=month_view(second=better(1));m=sel.month_stage(v,sel.BUCKETS)
        self.assertEqual(m['OFFMonths'],[1]);self.assertEqual(len(v.calls),26)
        self.assertNotIn((sel.BUCKETS,tuple(n for n in range(1,13) if n not in (1,3))),v.calls)
    def test_rank_individual_not_lomo_gain(self):
        v=month_view();v.values[(sel.BUCKETS,tuple(n for n in range(1,13) if n!=3))]=better(99)
        self.assertEqual(sel.month_stage(v,sel.BUCKETS)['OFFRanking'],[1,2,3])
    def test_month_tie_number(self):
        v=month_view()
        for n in (1,2,3):v.values[(sel.BUCKETS,(n,))]=bad()
        self.assertEqual(sel.month_stage(v,sel.BUCKETS)['OFFRanking'],[1,2,3])
    def test_no_added_month_final_gate(self):
        v=month_view(eligible=(1,));after=better();after['Trades']=149;after['Losses']=9
        v.values[(sel.BUCKETS,tuple(range(2,13)))]=after
        dom=sel.dom_stage(dom_view(off=0))
        with patch.object(sel,'dom_stage',return_value=dom):r=sel.select(record(),v)
        self.assertFalse(gate(r['Month']['FinalMetrics']));self.assertEqual(r['Status'],'PASS_U08')
    def test_m1_contradiction_stop(self):
        original=sel.improvement;calls=0
        def compare(a,b):
            nonlocal calls
            calls+=1
            return dict(Checks={},Adopt=False) if calls==13 else original(a,b)
        with patch.object(sel,'improvement',side_effect=compare):
            with self.assertRaises(ValueError):sel.month_stage(month_view(eligible=(1,)),sel.BUCKETS)
    def test_lomo_retains_dom_filter(self):
        v=month_view(eligible=());sel.month_stage(v,sel.BUCKETS)
        self.assertTrue(all(k[0]==sel.BUCKETS for k in v.calls))


class CalendarReplay(unittest.TestCase):
    def test_entry_not_exit_date(self):
        r=record();s=Structure('USDJPY','LONG',0,1425,30);r.update(CandidateID=s.candidate_id,Schedule=s.definition())
        t=dict(Status='OK',EntryTime='2020-08-31 23:45:00',CloseTime='2020-09-01 00:15:00',Pips=1,FixedKey=[0])
        for cls in (ScalarView,VectorView):
            v=cls([t],r);self.assertEqual(v.filtered(['D3'],[8]),[t]);self.assertEqual(v.filtered(['D1'],[9]),[])
    def test_filter_metrics_exact_all_subsets_used(self):
        a=ScalarView(trades(),record());b=VectorView(trades(),record())
        for buckets in [None,['D1'],['D2'],['D3'],['D2','D3']]:
            for months in [None,[1],[2],list(range(2,13))]:
                self.assertEqual(a.filtered(buckets,months),b.filtered(buckets,months));self.assertEqual(a.metrics(buckets,months),b.metrics(buckets,months))
        self.assertEqual(sel.select(record(),a),sel.select(record(),b))
    def test_calendar_immutability(self):
        r=record();before=copy.deepcopy(r);result=sel.select(r,VectorView(trades(),r));self.assertEqual(r,before)
        for k in ('Schedule','FormalSL','FormalTP','FormalWeekdays','AnchorWeekday','SetName'):self.assertEqual(result[k],r[k])
    def test_duplicate_and_isolation(self):
        r=record();t=trades()[0]
        for cls in (ScalarView,VectorView):
            with self.assertRaises(ValueError):cls([t,t],r)
            for year in (2024,2025,2026):
                u={**t,'EntryTime':f'{year}-02-05 09:00:00','CloseTime':f'{year}-02-05 09:30:00'}
                with self.assertRaises(ValueError):cls([u],r)
    def test_order_and_annual(self):
        ts=trades();a=VectorView(ts,record()).metrics();b=ScalarView(list(reversed(ts)),record()).metrics();self.assertEqual(a,b)
        self.assertEqual(a['Annual']['2020']['Trades'],200)
    def test_no_average_of_bucket_metrics(self):
        v=VectorView(trades(),record());a=v.filtered(['D1']);b=v.filtered(['D2'])[:5]
        for t in b:t['Pips']=10
        m=summarize(a+b);self.assertNotEqual(m['AvgPips'],(summarize(a)['AvgPips']+summarize(b)['AvgPips'])/2)
    def test_reference_optimized_nonempty_pass(self):
        r=record();parts=[];days=[]
        for n,t in enumerate(trades()):
            e=pd.Timestamp(t['EntryTime']);days.append(e.normalize());price=100 if n%4==0 else 100.05
            parts.append(pd.DataFrame(dict(Open=[100,price],High=[100,price],Low=[100,price],Close=[100,price]),index=[e,e+pd.Timedelta(minutes=30)]))
        bars=pd.concat(parts).sort_index();a=opt.evaluate_candidate(opt.Engine(bars,'USDJPY'),r,days);b=ref.evaluate_candidate(bars,r,days)
        self.assertEqual(a,b);self.assertEqual(a[0]['Status'],'PASS_U08');self.assertEqual(len(a[0]['Month']['LOMO']),12)
    def test_engine_discovery_isolation(self):
        from test_b7_u06 import bars
        for year in (2024,2025,2026):
            with self.assertRaises(ValueError):opt.Engine(bars(f'{year}-02-04'),'USDJPY')
            with self.assertRaises(ValueError):ref.evaluate_candidate(bars(f'{year}-02-04'),record(),[])


    def test_trade_level_dom2_replay(self):
        ts=trades();r=record()
        for t in ts:
            day=pd.Timestamp(t['EntryTime']).day
            t['Pips']=-1 if day<=10 else (-.5 if day<=20 else (-.1 if day%3==0 else 10))
        a=sel.select(r,ScalarView(ts,r));b=sel.select(r,VectorView(ts,r))
        self.assertEqual(a,b);self.assertEqual(a['DOM']['AdoptedState'],'DOM2');self.assertEqual(a['Status'],'PASS_U08')
    def test_trade_level_month_m2_replay(self):
        ts=trades();r=record()
        for t in ts:
            e=pd.Timestamp(t['EntryTime'])
            t['Pips']=-2 if e.month==2 else (-1 if e.month==3 else (-.2 if e.day%4==0 else 2))
        a=sel.select(r,ScalarView(ts,r));b=sel.select(r,VectorView(ts,r))
        self.assertEqual(a,b);self.assertEqual(a['DOM']['AdoptedState'],'DOM0');self.assertEqual(a['Month']['AdoptedState'],'M2')
        self.assertEqual(a['Month']['OFFMonths'],[2,3]);self.assertEqual(a['Status'],'PASS_U08')


class ExecutionCompatibility(_Execution):
    def compare(self,b,d='LONG',sl=15,tp=10,entry=None,scheduled=None):
        e=b.index[0] if entry is None else pd.Timestamp(entry);x=e+pd.Timedelta(minutes=30) if scheduled is None else pd.Timestamp(scheduled)
        a=opt.Engine(b,'USDJPY').execute(d,e,x,sl,(),tp);self.assertEqual(a,ref.execute(b,'USDJPY',d,e,x,sl,(),tp));return a
    def test_friday_no_reconnect(self):
        from test_b7_u06 import bars
        b=pd.concat([bars('2020-02-07 23:45',n=15),bars('2020-02-10 00:15')])
        self.assertEqual(self.compare(b)['Status'],'MISSING_EXIT')
del _Execution


class InputAudit(unittest.TestCase):
    def setUp(self):
        self.data=inp.read(inp.INPUT);self.audit=inp.read(ROOT/'results/b7/u07/drive_checkpoint_audit.json');self.identity=inp.read(ROOT/'results/b7/u07/input_identity.json')
        self.original=inp.read(ROOT/'research_inputs/b7/u07_selected56_input.json');self.summary=inp.read(ROOT/'results/b7/u07/u07_result_summary.json');self.archive=inp.read(ROOT/'results/b7/u07/u07_archive_manifest.json')
    def check(self):return inp.validate(self.data,self.audit,self.identity,self.original,self.summary,self.archive)
    def test_frozen56(self):self.assertEqual(len(inp.input_config()[1]['Candidates']),56)
    def test_sha_mismatch(self):
        with patch.object(inp,'digest',return_value='bad'):
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
    def test_mutations(self):
        for key,value in [('U07Status','DROP'),('U07CandidateSHA256','bad'),('U07CheckpointSHA256','bad'),('U07ProducerImplementationSHA','bad'),('FormalSL',999),('FormalTP',999),('FormalWeekdays',[4]),('AnchorWeekday',4),('SetName','W3')]:
            before=copy.deepcopy(self.data);self.data['Candidates'][0][key]=value
            with self.subTest(key=key):
                with self.assertRaises(ValueError):self.check()
            self.data=before
    def test_schedule_mutation(self):
        self.data['Candidates'][0]['Schedule']['EntryMinute']+=5
        with self.assertRaises(ValueError):self.check()
    def test_producer_mismatch(self):
        self.data['U07ProducerImplementationSHA']='wrong'
        with self.assertRaises(ValueError):self.check()


class CheckpointAndFinalize(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.producer='a'*40;self.env=dict(Python='3.13.15',NumPy='2.3.5',pandas='2.2.3')
        self.identity=identity(self.producer,self.env);self.records=inp.input_config()[1]['Candidates']
        self.local=self.root/'local';self.drive=self.root/'drive'
        rt.init_root(self.local,self.identity,False);rt.init_root(self.drive,self.identity,False)
        for r in self.records:
            result=sel.select(r,VectorView([],r)) # Synthetic absence only; no M1 opened.
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
        for key in ('U08ConfigSHA256','U08InputSHA256','M1ExactIdentity','U07ResultFreezeSHA','CandidateIDs','FullPrespecSHA256'):
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
                 'b7.u06_selection.select','b7.u08_selection.select','b7.u08_selection.dom_stage','b7.u08_selection.month_stage','b7.u08_calendar.ScalarView.metrics','b7.u08_calendar.VectorView.metrics','b7.u08_execution.Engine',
                 'b7.u08_execution.evaluate_candidate','b7.u08_reference.evaluate_candidate','b7.u08_runtime.Engine',
                 'b7.u08_runtime.load_discovery','b7.u08_runtime.evaluate_candidate','b7.stage1_runtime.run_tests']
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
        for n in ('candidate_results.json','checkpoint_audit.json','pair_summary.json','dom_summary.json','month_summary.json','calendar_summary.json'):
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
        self.assertEqual(result['CompletedJobs'],56)
    def test_public_finalize_no_evaluation_and_portable_paths(self):
        import shutil
        from test_b7_u06_finalize_only import synthetic_colab_path
        content=self.root.resolve()/'content';(content/'drive').mkdir(parents=True);shutil.copytree(self.drive,content/'drive'/'source')
        with patch.object(fin,'Path',side_effect=lambda p:synthetic_colab_path(content,p)), patch.dict(fin.os.environ,{'COLAB_RELEASE_TAG':'synthetic'}), patch.object(fin,'current_preflight',return_value=self.proof), patch.object(sel,'select',side_effect=AssertionError('no selection')), patch.object(opt,'evaluate_candidate',side_effect=AssertionError('no evaluation')):
            result=fin.finalize_from_completed_jobs('/content/drive/source','/content/out',self.producer,self.producer,fin.APPROVAL)
        self.assertFalse(result['JobRecomputation'])
    def test_source_mutation_stops_without_output(self):
        def progress(p):
            if p['ProcessedJobs']==56:(self.job/'candidate.json').write_text('{}')
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

class ReleaseGuards(unittest.TestCase):
    def test_notebooks_off(self):
        import ast
        for n in ('b7_u08_dom_month.ipynb','b7_u08_finalize_only.ipynb'):
            flags=[]
            for c in json.loads((ROOT/'notebooks'/n).read_text())['cells']:
                if c['cell_type']!='code':continue
                self.assertEqual(c['outputs'],[])
                for node in ast.walk(ast.parse(''.join(c['source']))):
                    if isinstance(node,ast.Assign):
                        for target in node.targets:
                            if isinstance(target,ast.Name) and target.id.startswith('RUN_'):flags.append(ast.literal_eval(node.value))
            self.assertTrue(flags);self.assertFalse(any(flags))
    def test_config_supplement(self):
        cfg,_=inp.input_config();s=cfg['ComparisonSupplement'];self.assertFalse(s['MonthFinalU01Gate']);self.assertFalse(s['NewSampleGate'])
        self.assertIn('Both PFState FINITE',s['PFStrictImprovement']);self.assertIn('either null is false',s['MedianStrictImprovement'])
    def test_deterministic_process(self):
        script='from test_b7_u08 import *; print(canonical(sel.select(record(),VectorView(trades(),record()))))'
        out=[]
        for seed in ('1','82'):
            env={**os.environ,'PYTHONHASHSEED':seed,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(ROOT/'src/research')+os.pathsep+str(ROOT/'tests')}
            out.append(subprocess.check_output([sys.executable,'-c',script],env=env,cwd=ROOT))
        self.assertEqual(*out)
    def test_pass_checkpoint(self):
        r=record();result=sel.select(r,VectorView(trades(),r));self.assertEqual(result['Status'],'PASS_U08')
        i={'CandidateIDs':[r['CandidateID']]}
        with tempfile.TemporaryDirectory() as tmp:
            l=Path(tmp)/'l';d=Path(tmp)/'d';rt.complete_local(l,i,r,result);rt.mirror_job(l,d,i,r);self.assertEqual(rt.validate_drive(d,i,r),result)
    def test_public_api_default_unapproved(self):
        with self.assertRaises(PermissionError):rt.run_formal({},'',None,None)
        with self.assertRaises(PermissionError):fin.finalize_from_completed_jobs(None,None,'','')
