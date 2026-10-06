import unittest,tempfile,json,copy,shutil
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import numpy as np
from b7 import u06_selection as u
from b7.u06_execution import Engine,evaluate
from b7.u06_reference import execute
from b7 import u06_runtime as rt
from b7 import u06_input as inp
from b7.stage1_contract import Structure,SYMBOLS,SL,SPREAD,PIPS,canonical
from b7.stage1_metrics import summarize,gate

def metrics(avg=2,pf=1.2):
    return dict(Trades=160,Losses=12,AvgPips=avg,PFState='FINITE',PFpips=pf,PositiveYearCount=4,MedianAnnualAvgPips=avg,WorstYearAvgPips=avg,Annual={str(y):dict(Trades=40) for y in range(2020,2024)})
def record():
    s=Structure('USDJPY','LONG',1,540,30)
    return dict(CandidateID=s.candidate_id,Symbol=s.symbol,PairRank=1,Schedule=s.definition(),PureMetrics=metrics(),FiveSLMetrics=[dict(SLPips=p,Metrics=metrics()) for p in (10,15,20,25,30)])
def bars(start='2020-02-04 09:00',n=35):
    return pd.DataFrame(dict(Open=np.full(n,100.),High=np.full(n,100.),Low=np.full(n,100.),Close=np.full(n,100.)),index=pd.date_range(start,periods=n,freq='min'))

class Selection(unittest.TestCase):
    def test_endpoint_examples(self):
        for a,expected in [(65,list(range(50,81,5))),(30,[25,30,35]),(25,[20,25,30]),(10,[5,10,15]),(15,[10,15,20])]:self.assertEqual(u.local_grid(a,True),expected)
    def test_half_up(self):self.assertEqual([u.round5(x) for x in (22.5,27.5)],[25,30])
    def test_tp_no_expansion(self):self.assertEqual(u.local_grid(10),[10])
    def test_dedup(self):self.assertEqual(u.merged_grid([10,15],True),[5,10,15,20])
    def test_two_reject_three_accept(self):
        self.assertFalse(u.zones({5:metrics(),10:metrics()}));self.assertEqual(len(u.zones({5:metrics(),10:metrics(),15:metrics()})),1)
    def test_maximal_multiple(self):
        p={x:metrics() for x in (5,10,15,20,30,35,40)};self.assertEqual([z['Points'] for z in u.zones(p)],[[5,10,15,20],[30,35,40]])
    def test_fail_splits(self):self.assertEqual(len(u.zones({x:metrics(-1 if x==20 else 2) for x in range(5,36,5)})),2)
    def test_retention_exact(self):self.assertTrue(u.zones({x:metrics(8) for x in (5,10,15)},10)[0]['Qualified'])
    def test_retention_below(self):self.assertFalse(u.zones({x:metrics(7.999) for x in (5,10,15)},10)[0]['Qualified'])
    def test_ranking_priorities(self):
        z=dict(Points=[5,10,15],MedianAvgPips=2,WorstAvgPips=1,MedianPFpips=1.2,CentralValue=10,Qualified=True)
        for k,v in [('MedianAvgPips',3),('Points',[5,10,15,20]),('WorstAvgPips',1.1),('MedianPFpips',1.3),('CentralValue',5)]:
            a=copy.deepcopy(z);a[k]=v;self.assertEqual(u.winner([z,a]),a)
    def test_lower_median(self):self.assertEqual(u.zones({p:metrics() for p in (50,55,60,65)})[0]['CentralValue'],55)
    def test_no_zone_drop(self):
        d=u.select(record(),lambda sl,tp:metrics(-1));self.assertEqual(d['Status'],'DROP_U06_SL');self.assertIsNone(d['TP'])
    def test_r_conversion(self):self.assertEqual(u.coarse_anchors(15),[10,15,25,30,45])
    def test_coarse_duplicate_minimum(self):self.assertEqual(u.coarse_anchors(5),[5,10,15])
    def test_isolated(self):self.assertEqual(u.eligible_anchors({5:metrics(-1),10:metrics(),15:metrics(-1)}),[])
    def test_endpoint_adjacent(self):self.assertEqual(u.eligible_anchors({5:metrics(),10:metrics(),15:metrics(-1),20:metrics(),25:metrics()}),[5,10,20,25])
    def test_tp_none_fallback(self):self.assertIsNone(u.select(record(),lambda sl,tp:metrics())['FormalTP'])
    def test_point_cache(self):
        seen=set()
        def ev(sl,tp):self.assertNotIn((sl,tp),seen);seen.add((sl,tp));return metrics()
        u.select(record(),ev)
    def test_tp_exact_point1(self):self.assertTrue(u.tp_comparison(metrics(.1),metrics(0))['AdoptFinite'])
    def test_tp_exact_five_percent(self):self.assertTrue(u.tp_comparison(metrics(10.5),metrics(10))['AdoptFinite'])
    def test_tp_below(self):self.assertFalse(u.tp_comparison(metrics(10.499),metrics(10))['AdoptFinite'])
    def test_positive_degrade(self):
        a=metrics(20);a['PositiveYearCount']=3;self.assertFalse(u.tp_comparison(a,metrics())['AdoptFinite'])
    def test_worst_degrade(self):
        a=metrics(20);a['WorstYearAvgPips']=1;self.assertFalse(u.tp_comparison(a,metrics())['AdoptFinite'])

class Execution(unittest.TestCase):
    def compare(self,b,d='LONG',sl=15,tp=10,entry=None,scheduled=None):
        e=b.index[0] if entry is None else pd.Timestamp(entry);x=e+pd.Timedelta(minutes=30) if scheduled is None else pd.Timestamp(scheduled)
        a=Engine(b,'USDJPY').execute(d,e,x,sl,(),tp);c=execute(b,'USDJPY',d,e,x,sl,(),tp);self.assertEqual(a,c);return a
    def test_hits_and_same_bar(self):
        for direction in ('LONG','SHORT'):
            for low,high,reason in [(99,100,'SL' if direction=='LONG' else 'TP'),(100,101,'TP' if direction=='LONG' else 'SL'),(99,101,'SL')]:
                b=bars();b.iloc[2,b.columns.get_loc('Low')]=low;b.iloc[2,b.columns.get_loc('High')]=high
                self.assertEqual(self.compare(b,direction)['ExitReason'],reason)
    def test_inclusive_entry_exit(self):
        for pos in (0,30):
            b=bars();b.iloc[pos,b.columns.get_loc('High')]=101;self.assertEqual(self.compare(b)['CloseTime'],str(b.index[pos]))
    def test_exit_fallback(self):
        for delay in range(5):
            b=bars();b=b.drop(b.index[30:30+delay]);self.assertEqual(self.compare(b)['ExitDelayMinutes'],delay)
    def test_plus5_reject_even_stop(self):
        b=bars(n=36);b.iloc[0,b.columns.get_loc('Low')]=99;b=b.drop(b.index[30:35]);self.assertEqual(self.compare(b)['Status'],'MISSING_EXIT')
    def test_missing_entry(self):
        b=bars().iloc[1:];self.assertEqual(self.compare(b,entry='2020-02-04 09:00')['Status'],'MISSING_ENTRY')
    def test_gap_no_interpolation(self):
        b=bars().drop(bars().index[5:10]);self.assertEqual(self.compare(b)['MissingPathMinutes'],5)
    def test_overnight(self):self.assertEqual(self.compare(bars('2020-02-04 23:45'))['Status'],'OK')
    def test_year_stop(self):self.assertEqual(self.compare(bars('2020-12-25 09:00'))['Status'],'YEAR_END_STOP')
    def test_boundary(self):self.assertEqual(self.compare(bars(),scheduled='2024-01-01')['Status'],'PERIOD_BOUNDARY')
    def test_isolation(self):
        with self.assertRaises(ValueError):Engine(bars('2024-01-04'),'USDJPY')
    def test_tp_none_spread(self):
        a=self.compare(bars(),tp=None);self.assertEqual(a['ExitReason'],'TimeExit');self.assertLess(a['Pips'],0)
    def test_raw_no_epsilon(self):
        b=bars();price=100+SPREAD['USDJPY']*PIPS['USDJPY'];stop=price-15*PIPS['USDJPY'];b['Low']=np.nextafter(stop,np.inf)
        self.assertEqual(self.compare(b,tp=None)['ExitReason'],'TimeExit')
    def test_synthetic_metric_selection_equivalence(self):
        b=bars();engine=Engine(b,'USDJPY');r=record();s=Structure.from_id(r['CandidateID'])
        def ref(sl,tp):
            t=execute(b,s.symbol,s.direction,b.index[0],b.index[30],sl,s.key,tp);return summarize([t])
        def opt(sl,tp):return evaluate(engine,s,sl,tp,days=['2020-02-04'])[0]
        self.assertEqual(u.select(r,ref),u.select(r,opt))

class Checkpoint(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.r=record();self.i=dict(Environment=dict(Python='3.13.15'),Config='x',Selected='y',Data='z',CandidateIDs=[self.r['CandidateID']]);self.result=u.select(self.r,lambda sl,tp:metrics())
        self.local=self.root/'local';self.drive=self.root/'drive';rt.complete_local(self.local,self.i,self.r,self.result)
    def tearDown(self):self.tmp.cleanup()
    def test_completed_local(self):self.assertEqual(rt.validate_job(self.local,self.i,self.r),self.result)
    def test_mirror(self):rt.mirror_job(self.local,self.drive,self.i,self.r);self.assertEqual(rt.validate_drive(self.drive,self.i,self.r),self.result)
    def test_missing_marker(self):
        shutil.copytree(self.local,self.drive)
        with self.assertRaises(FileNotFoundError):rt.validate_drive(self.drive,self.i,self.r)
    def test_corrupt_candidate(self):
        (self.local/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):rt.validate_job(self.local,self.i,self.r)
    def test_exact_identity_variants(self):
        for key in ('Config','Selected','Data','Environment'):
            i=copy.deepcopy(self.i);i[key]='changed'
            with self.assertRaises(ValueError):rt.validate_job(self.local,i,self.r)
    def test_drive_hash_failure(self):
        rt.mirror_job(self.local,self.drive,self.i,self.r);(self.drive/'candidate.json').write_text('{}')
        with self.assertRaises(ValueError):rt.validate_drive(self.drive,self.i,self.r)
    def test_incomplete_copy(self):
        with patch.object(rt.shutil,'copy2',side_effect=OSError('interrupt')):
            with self.assertRaises(OSError):rt.mirror_job(self.local,self.drive,self.i,self.r)
        self.assertFalse(self.drive.exists())
    def test_copy_corruption(self):
        def bad(src,dst):Path(dst).write_text('{}')
        with patch.object(rt.shutil,'copy2',side_effect=bad):
            with self.assertRaises(ValueError):rt.mirror_job(self.local,self.drive,self.i,self.r)
        self.assertFalse(self.drive.exists())
    def test_no_overwrite(self):
        rt.mirror_job(self.local,self.drive,self.i,self.r)
        with self.assertRaises(FileExistsError):rt.mirror_job(self.local,self.drive,self.i,self.r)
    def test_approval(self):
        with self.assertRaises(PermissionError):rt.run_formal(None,None,None,None,None,None)
    def test_incomplete_finalization(self):
        with self.assertRaises((FileNotFoundError,ValueError)):rt.finalize(self.root,self.drive,self.i,[self.r])
        self.assertFalse((self.root/'final/COMPLETE.json').exists())

class Inputs(unittest.TestCase):
    def fixture(self):
        out=[]
        for sym in SYMBOLS:
            for rank in range(1,9):
                s=Structure(sym,'LONG',0,rank*5,30)
                out.append(dict(Representative=s.candidate_id,Symbol=sym,PairRank=rank,Top8=True,AnchorWeekday=0,Members=[dict(Definition=s.definition(),PureMetrics=metrics())]))
        return out
    def test_valid72(self):self.assertEqual(len(inp.selected_records(self.fixture())),72)
    def test_count(self):
        with self.assertRaises(ValueError):inp.selected_records(self.fixture()[:-1])
    def test_duplicate(self):
        s=self.fixture();s[-1]=s[0]
        with self.assertRaises(ValueError):inp.selected_records(s)
    def test_pair_rank(self):
        s=self.fixture();s[0]['PairRank']=9
        with self.assertRaises(ValueError):inp.selected_records(s)
    def test_missing_member(self):
        s=self.fixture();s[0]['Members']=[]
        with self.assertRaises(ValueError):inp.selected_records(s)
    def test_selected_sha_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s';p.write_text('[]')
            with self.assertRaises(ValueError):inp.extract(p,Path(d))
            with patch.object(inp,'SELECTED_BYTES',2):
                with self.assertRaises(ValueError):inp.extract(p,Path(d))

class SourceInput(unittest.TestCase):
    def setUp(self):
        from b7.stage1_contract import object_hash,digest,jobs
        from b7.stage1_runtime import checkpoint_identity
        from b7.stage1_metrics import point_result
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.cp=self.root/'cp';self.cp.mkdir();self.sel=self.root/'selected.json';self.selected=Inputs().fixture();self.sel.write_text(canonical(self.selected))
        identity=inp.expected_original_identity();(self.cp/'identity.json').write_text(canonical(identity));self.records={}
        trusted={'identity.json':digest(self.cp/'identity.json')}
        for j in jobs():
            base='jobs/'+j.job_id+'/';folder=self.cp/'jobs'/j.job_id;folder.mkdir(parents=True)
            records=[]
            for f in self.selected:
                s=Structure.from_id(f['Representative'])
                if (s.symbol,s.direction,s.weekday)!=(j.symbol,j.direction,j.weekday):continue
                r=dict(s.definition(),PureMetrics=metrics(),FiveSLMetrics=[dict(SLPips=p,Metrics=metrics()) for p in SL[s.symbol]],**point_result(metrics(),[metrics()]*5));records.append(r)
            (folder/'formal_pass.jsonl').write_text(''.join(canonical(r)+'\n' for r in records));(folder/'point_map.npz').write_bytes(b'synthetic unused map')
            (folder/'summary.json').write_text(canonical(dict(Errors=0,EvaluatedStructures=81504,EvaluatedVariants=489024)))
            ci=checkpoint_identity(identity,j);(folder/'checkpoint.json').write_text(canonical(dict(Status='JOB_COMPLETE',Identity=ci,IdentitySHA256=object_hash(ci),Hashes={n:digest(folder/n) for n in ('summary.json','formal_pass.jsonl','point_map.npz')})))
            for n in ('checkpoint.json','summary.json','formal_pass.jsonl','point_map.npz'):trusted[base+n]=digest(folder/n)
        files=[dict(Path=k,SHA256=v) for k,v in trusted.items()]
        ap=self.root/'results/b7/stage1/source_checkpoint_audit.json';ap.parent.mkdir(parents=True);ap.write_text(canonical(dict(TrustedFiles=files,SourceTrustedFilesSHA256=object_hash(files),OriginalIdentitySHA256=object_hash(identity))))
        self.patches=[patch.object(inp,'ROOT',self.root),patch.object(inp,'AUDIT_SHA',digest(ap)),patch.object(inp,'SELECTED_SHA',digest(self.sel)),patch.object(inp,'SELECTED_BYTES',self.sel.stat().st_size)]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_extract72(self):self.assertEqual(len(inp.extract(self.sel,self.cp)['Candidates']),72)
    def test_source_audit_hash_mismatch(self):
        (self.root/'results/b7/stage1/source_checkpoint_audit.json').write_text('{}')
        with self.assertRaises(ValueError):inp.extract(self.sel,self.cp)
    def test_source_modified(self):
        (self.cp/'jobs/AUDJPY_LONG_MON/formal_pass.jsonl').write_text('')
        with self.assertRaises(ValueError):inp.extract(self.sel,self.cp)
    def change_record_with_rebound_hash(self,fn):
        from b7.stage1_contract import object_hash,digest
        base='jobs/AUDJPY_LONG_MON/';p=self.cp/base/'formal_pass.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()];fn(rows);p.write_text(''.join(canonical(x)+'\n' for x in rows))
        cp=self.cp/base/'checkpoint.json';d=json.loads(cp.read_text());d['Hashes']['formal_pass.jsonl']=digest(p);cp.write_text(canonical(d))
        ap=self.root/'results/b7/stage1/source_checkpoint_audit.json';a=json.loads(ap.read_text())
        for x in a['TrustedFiles']:
            if x['Path'] in (base+'formal_pass.jsonl',base+'checkpoint.json'):x['SHA256']=digest(self.cp/x['Path'])
        a['SourceTrustedFilesSHA256']=object_hash(a['TrustedFiles']);ap.write_text(canonical(a));inp.AUDIT_SHA=digest(ap)
    def test_missing_representative(self):
        self.change_record_with_rebound_hash(lambda rows:rows.pop())
        with self.assertRaises(ValueError):inp.extract(self.sel,self.cp)
    def test_five_sl_mismatch(self):
        self.change_record_with_rebound_hash(lambda rows:rows[0]['FiveSLMetrics'][0].update(SLPips=999))
        with self.assertRaises(ValueError):inp.extract(self.sel,self.cp)
    def test_gate_record_mismatch(self):
        self.change_record_with_rebound_hash(lambda rows:rows[0].update(PassingSLCount=2))
        with self.assertRaises(ValueError):inp.extract(self.sel,self.cp)

class FullSyntheticDurability(unittest.TestCase):
    def test_72_complete_and_archive(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);local=root/'local';drive=root/'drive';records=[]
            for f in Inputs().fixture():
                s=Structure.from_id(f['Representative']);r=record();r.update(CandidateID=s.candidate_id,Symbol=s.symbol,PairRank=f['PairRank'],Schedule=s.definition());records.append(r)
            identity=dict(CandidateIDs=[r['CandidateID'] for r in records],Environment={'Python':'3.13.15'})
            rt.init_root(local,identity,False);rt.init_root(drive,identity,False)
            for r in records:
                result=u.select(r,lambda sl,tp:metrics());l=local/'jobs'/r['CandidateID'];v=drive/'jobs'/r['CandidateID'];rt.complete_local(l,identity,r,result);rt.mirror_job(l,v,identity,r)
            rt.init_root(drive,identity,True)
            with self.assertRaises(ValueError):rt.init_root(drive,dict(identity,Environment={'Python':'3.13.16'}),True)
            self.assertEqual(rt.finalize(local,drive,identity,records)['Status'],'COMPLETE_U06_ONLY')
            rt.archive_completed(local/'final',root/'archive');self.assertTrue((root/'archive/archive.zip').is_file())
    def test_execution_weekend_and_invalid_hold(self):
        e=Execution();b=bars('2020-02-08 23:45');self.assertEqual(e.compare(b)['Status'],'INVALID_ENTRY_WEEKDAY')
        self.assertEqual(e.compare(bars(),scheduled='2020-02-04 09:29')['Status'],'INVALID_HOLD')
    def test_owned_discovery(self):
        b=bars();e=Engine(b,'USDJPY');b.iloc[0,0]=999;self.assertEqual(e.bars.iloc[0,0],100)

class PositiveReplay(unittest.TestCase):
    def test_nonempty_formal_zone_reference_optimized(self):
        frames=[];days=[]
        for year in range(2020,2024):
            dates=pd.date_range(f'{year}-02-01',f'{year}-11-30',freq='W-TUE')[:32]
            for n,day in enumerate(dates):
                b=bars(str(day+pd.Timedelta(hours=9)));change=.30 if n%4 else -.30
                b.iloc[30,b.columns.get_loc('Open')]+=change
                b.iloc[30,b.columns.get_loc('High')]=max(100,100+change)
                b.iloc[30,b.columns.get_loc('Low')]=min(100,100+change)
                frames.append(b);days.append(day)
        # 32/year meets annual minimum, but extend to >=150 total with extra dates.
        for year in range(2020,2024):
            dates=pd.date_range(f'{year}-10-01',f'{year}-12-20',freq='W-TUE')[-8:]
            for n,day in enumerate(dates):
                b=bars(str(day+pd.Timedelta(hours=9)));change=.30 if n%4 else -.30
                b.iloc[30,b.columns.get_loc('Open')]+=change;b.iloc[30,b.columns.get_loc('High')]=max(100,100+change);b.iloc[30,b.columns.get_loc('Low')]=min(100,100+change)
                frames.append(b);days.append(day)
        b=pd.concat(frames).sort_index();engine=Engine(b,'USDJPY');r=record();s=Structure.from_id(r['CandidateID'])
        # Scalar independently replays each daily window, with exact fields compared.
        def ref(sl,tp):
            ts=[]
            for day in sorted(days):
                e=day+pd.Timedelta(hours=9);x=e+pd.Timedelta(minutes=30)
                a=execute(b.loc[e:e+pd.Timedelta(minutes=34)],s.symbol,s.direction,e,x,sl,s.key,tp)
                opt=engine.execute(s.direction,e,x,sl,s.key,tp);self.assertEqual(a,opt)
                if a['Status']=='OK':ts.append(a)
            return summarize(ts)
        out=u.select(r,ref);other=u.select(r,lambda sl,tp:evaluate(engine,s,sl,tp,days)[0]);self.assertEqual(out,other);self.assertEqual(out['Status'],'PASS_U06');self.assertIsNotNone(out['ChosenSLZone'])

class Guards(unittest.TestCase):
    def test_notebook_flags_and_syntax(self):
        import ast
        from b7.stage1_contract import ROOT
        nb=json.loads((ROOT/'notebooks/b7_u06_sl_tp.ipynb').read_text());flags={}
        for c in nb['cells']:
            if c['cell_type']!='code':continue
            tree=ast.parse(''.join(c['source']))
            for n in ast.walk(tree):
                if isinstance(n,ast.Assign):
                    for t in n.targets:
                        if isinstance(t,ast.Name) and t.id.startswith('RUN_'):flags[t.id]=ast.literal_eval(n.value)
        self.assertEqual(len(flags),10);self.assertFalse(any(flags.values()))
    def test_execution_outside_colab_denied(self):
        with patch.object(rt.os,'environ',{}):
            with self.assertRaises(PermissionError):rt.run_formal(None,None,None,None,None,None,approval=rt.APPROVAL)
    def test_zone_finite_tp_selected(self):
        r=record()
        result=u.select(r,lambda sl,tp:metrics(4 if tp is not None else 2))
        self.assertEqual(result['Status'],'PASS_U06');self.assertIsNotNone(result['FormalTP'])
    def test_drop_never_calls_tp(self):
        def ev(sl,tp):self.assertIsNone(tp);return metrics(-1)
        self.assertEqual(u.select(record(),ev)['Status'],'DROP_U06_SL')
    def test_source_fields_schedule_unchanged(self):
        r=record();a=u.select(r,lambda sl,tp:metrics());self.assertEqual(a['Schedule'],r['Schedule'])
