"""Stage2-B synthetic tests only; no real center selection or research sweep."""
import copy,json,math,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage2a import candidate
from test_b6_stage1 import fixture
from b6.stage2b_config import load_config
from b6.stage2b_selection import select_centers,local_grid,center_grid,growth_key,efficiency,efficiency_key,setting_key,stability,final_selection,final_key
from b6.stage2b_metrics import evaluate_candidate
from b6.stage2b_search import prepare_jobs,finish,full_sweep,require_full_authorization
from b6.stage2a_search import open_store,save_job,read_job
from b6.stage2a_engine import FastEngine,reference_replay
from b6.stage2a_metrics import summarize


def point(sl=50,tp=100,avg=1.,total=160.,dd=2.,passed=True,a=None):
    return {**(candidate() if a is None else a),'SL':sl,'TP':tp,'TPMode':'TP_NONE' if tp is None else 'FINITE','AvgR':avg,'TotalR':total,'MaxDDR':dd,'PF':2.,'Pass':passed}

def center(sl=50,tp=100,kind='GROWTH'):
    return {**point(sl,tp),'CenterType':kind,'CenterAliases':[kind]}

def grid_rows(centers,avg=1.):return [point(x['SL'],x['TP'],avg=avg) for x in local_grid(centers,load_config())]

class CenterTests(unittest.TestCase):
    def test_growth_avgr_and_pass_only(self):
        rows=[point(avg=1.),point(55,110,avg=2.),point(60,120,avg=100,passed=False)]
        result=select_centers(candidate(),rows);self.assertEqual(setting_key(result[0]),(55,110))
    def test_growth_ties_all_priorities(self):
        cases=[(point(avg=2.),point(avg=1.)),(point(total=200),point(total=100)),(point(dd=1),point(dd=2)),(point(tp=None),point(tp=100)),(point(sl=45),point(sl=50)),(point(tp=95),point(tp=100))]
        for better,worse in cases:
            self.assertLess(growth_key(better),growth_key(worse))
    def test_efficiency_formula_and_distinct_centers(self):
        rows=[point(avg=3,total=300,dd=30),point(55,110,avg=2,total=200,dd=2)]
        result=select_centers(candidate(),rows);self.assertEqual(len(result),2);self.assertEqual(setting_key(result[1]),(55,110))
        self.assertEqual(efficiency(point(total=20,dd=0)),20);self.assertEqual(efficiency(point(total=20,dd=.5)),20)
    def test_efficiency_ties(self):
        better=point(avg=2,total=20,dd=2);worse=point(avg=1,total=10,dd=1)
        self.assertLess(efficiency_key(better),efficiency_key(worse))
        for better,worse in [(point(total=20,dd=2),point(total=10,dd=1)),(point(tp=None),point()),(point(sl=45),point(sl=50)),(point(tp=95),point(tp=100))]:self.assertLess(efficiency_key(better),efficiency_key(worse))
    def test_same_center_dedup_no_runner_up(self):
        result=select_centers(candidate(),[point(avg=2,total=300),point(55,110,avg=1,total=100)])
        self.assertEqual(len(result),1);self.assertEqual(result[0]['CenterAliases'],['GROWTH','EFFICIENCY'])
    def test_no_pass_and_wrong_candidate(self):
        self.assertEqual(select_centers(candidate(),[point(passed=False)]),[])
        self.assertEqual(select_centers(candidate(),[]),[])
        with self.assertRaises(ValueError):select_centers(candidate(),[point(a=candidate(entry=5))])
    def test_deterministic_input_order(self):
        rows=[point(55,110),point(50,100),point(45,95)]
        self.assertEqual(select_centers(candidate(),rows),select_centers(candidate(),list(reversed(rows))))

class GridTests(unittest.TestCase):
    def test_finite_25_none_5(self):
        self.assertEqual(len(local_grid([center()],load_config())),25)
        self.assertEqual([r['SL'] for r in local_grid([center(tp=None)],load_config())],[40,45,50,55,60])
    def test_bounds_no_replacement_or_extension(self):
        c=load_config()
        for sl,tp,expected in ((10,5,9),(300,900,9),(10,None,3),(300,None,3)):
            grid=local_grid([center(sl,tp)],c);self.assertEqual(len(grid),expected)
            self.assertTrue(all(10<=r['SL']<=300 and (r['TP'] is None or 5<=r['TP']<=900) for r in grid))
            self.assertTrue(all(abs(r['SL']-sl)<=10 and (tp is None or abs(r['TP']-tp)<=10) for r in grid))
    def test_overlap_aliases_evaluate_once(self):
        cs=[center(),center(55,105,'EFFICIENCY')];g=local_grid(cs,load_config());self.assertEqual(len(g),34)
        self.assertEqual(len({setting_key(x) for x in g}),34)
        self.assertEqual(next(x for x in g if setting_key(x)==(50,100))['CenterAliases'],['GROWTH','EFFICIENCY'])
    def test_none_and_finite_not_merged(self):
        g=local_grid([center(tp=None),center(kind='EFFICIENCY')],load_config());self.assertEqual(len(g),30)
    def test_theoretical_max_and_no_refill(self):
        g=local_grid([center(),center(100,200,'EFFICIENCY')],load_config());self.assertEqual(len(g),50)
        a=candidate();b=candidate(entry=5);jobs,space=prepare_jobs([a,b],[point(a=a),point(a=b,passed=False)],load_config())
        self.assertEqual(len(jobs),2);self.assertEqual(jobs[1]['grid'],[]);self.assertEqual(space['ActualUniqueConditions'],25);self.assertEqual(space['TheoreticalMax'],2500)

class StabilityTests(unittest.TestCase):
    def test_finite_nine_and_boundary_four(self):
        cs=[center()];u,s=stability(candidate(),cs,grid_rows(cs),load_config());lookup={setting_key(x):x for x in u}
        self.assertEqual(lookup[(50,100)]['NeighborhoodCount'],9);self.assertEqual(lookup[(40,90)]['NeighborhoodCount'],4)
        self.assertTrue(all(x['StabilityPass'] for x in u))
    def test_none_three_and_boundary_two_no_extra_minimum(self):
        cs=[center(tp=None)];u,s=stability(candidate(),cs,grid_rows(cs),load_config());lookup={setting_key(x):x for x in u}
        self.assertEqual(lookup[(50,None)]['NeighborhoodCount'],3);self.assertEqual(lookup[(40,None)]['NeighborhoodCount'],2);self.assertTrue(lookup[(40,None)]['StabilityPass'])
    def test_exact_two_thirds_and_below(self):
        cs=[center(tp=None)];rows=grid_rows(cs);rows[1]['Pass']=False
        u,_=stability(candidate(),cs,rows,load_config());mid=next(x for x in u if x['SL']==50);self.assertTrue(mid['StabilityPass']);self.assertEqual(mid['NeighborhoodPassRate'],2/3)
        rows[3]['Pass']=False;u,_=stability(candidate(),cs,rows,load_config());self.assertFalse(next(x for x in u if x['SL']==50)['StabilityPass'])
    def test_median_eighty_percent_inclusive_and_spike_fail(self):
        cs=[center(tp=None)];rows=grid_rows(cs,avg=.8);rows[2]['AvgR']=1
        u,_=stability(candidate(),cs,rows,load_config());self.assertTrue(u[2]['StabilityPass'])
        rows[1]['AvgR']=.799;rows[3]['AvgR']=.799;u,_=stability(candidate(),cs,rows,load_config());self.assertFalse(u[2]['StabilityPass'])
    def test_point_must_pass_and_undefined_neighbor_fails(self):
        cs=[center()];rows=grid_rows(cs);rows[12]['Pass']=False
        u,_=stability(candidate(),cs,rows,load_config());self.assertFalse(next(x for x in u if setting_key(x)==(50,100))['StabilityPass'])
        rows[12]['AvgR']='UNDEFINED';u,_=stability(candidate(),cs,rows,load_config());self.assertTrue(any('UNDEFINED_NEIGHBOR_METRICS' in x['StabilityFailReasons'] for x in u))
    def test_per_center_scope_any_pass_and_best_passing_alias(self):
        cs=[center(),center(60,100,'EFFICIENCY')];rows=grid_rows(cs)
        # At SL50/TP100 Growth has 5/9 PASS, Efficiency has 5/6 PASS.
        for r in rows:
            if r['SL']<50 or (r['SL']==50 and r['TP']==95):r['Pass']=False
        unique,scoped=stability(candidate(),cs,rows,load_config());versions=[r for r in scoped if setting_key(r)==(50,100)]
        self.assertEqual(sorted(r['NeighborhoodCount'] for r in versions),[6,9])
        chosen=next(r for r in unique if setting_key(r)==(50,100));self.assertTrue(chosen['StabilityPass']);self.assertEqual(chosen['SourceCenterType'],'EFFICIENCY')
        self.assertEqual(chosen['CenterDistance'],0)
    def test_alias_min_distance_l1(self):
        cs=[center(),center(60,110,'EFFICIENCY')];u,_=stability(candidate(),cs,grid_rows(cs),load_config())
        p=next(r for r in u if setting_key(r)==(55,105));self.assertEqual(p['CenterDistance'],2)
        p=next(r for r in u if setting_key(r)==(60,110));self.assertEqual(p['CenterDistance'],0)
    def test_missing_duplicate_and_changed_structure_rejected(self):
        cs=[center()];rows=grid_rows(cs)
        for bad in (rows[:-1],rows+[rows[0]],[{**r,'Weekday':2} for r in rows]):
            with self.assertRaises(ValueError):stability(candidate(),cs,bad,load_config())

class SelectionTests(unittest.TestCase):
    def test_final_lexicographic_order_all_keys(self):
        base={**point(),'NeighborhoodMedianAvgR':1.,'NeighborhoodPassRate':.9,'CenterDistance':1}
        for key,value in [('NeighborhoodMedianAvgR',2),('NeighborhoodPassRate',1),('AvgR',2),('CenterDistance',0),('MaxDDR',1),('TP',None),('SL',45),('TP',95)]:
            self.assertLess(final_key({**base,key:value}),final_key(base),key)
    def test_selected_one_yearly_and_no_stable_drop(self):
        cs=[center(tp=None)];rows=grid_rows(cs);annual=[{**r,'Year':y} for r in rows for y in (2020,2021,2022,2023)]
        result=final_selection(candidate(),cs,rows,annual,load_config());self.assertEqual(result['selected']['SL'],50);self.assertEqual(len(result['selected']['YearlyMetrics']),4);self.assertIsNone(result['dropped'])
        for r in rows:r['Pass']=False
        result=final_selection(candidate(),cs,rows,annual,load_config());self.assertIsNone(result['selected']);self.assertEqual(result['dropped']['Reason'],'STAGE2B_DROPPED_NO_STABLE_POINT')
        result=final_selection(candidate(),[],[],[],load_config());self.assertEqual(result['dropped']['Reason'],'STAGE2B_DROPPED_NO_P02_CENTER')

class RunnerTests(unittest.TestCase):
    def test_frozen_engine_adapter_all_pairs_directions_and_overnight(self):
        dates=pd.DatetimeIndex(['2020-02-04','2021-02-02','2022-02-01','2023-02-07']);c=load_config()
        for symbol in c['spread_pips']:
            bars=fixture(symbol,dates,n=1500)
            for direction in ('L','S'):
                for entry,hold in ((0,30),(1410,60)):
                    a=candidate(symbol,direction,entry=entry,hold=hold)
                    grid=local_grid([center(10,None),center(15,10,'EFFICIENCY')],c)[:4]+local_grid([center(15,10)],c)[-4:]
                    got=evaluate_candidate(FastEngine(bars,symbol),a,dates,grid,c)
                    expected=summarize(a,grid,reference_replay(bars,symbol,a,dates,grid),c['gate']);self.assertEqual(got,expected)
    def test_full_guard_before_inputs_centers_or_prices(self):
        with patch('b6.stage2b_search.load_input',side_effect=AssertionError('input access')),patch('b6.stage2b_search.prepare_jobs',side_effect=AssertionError('centers')):
            with self.assertRaises(PermissionError):full_sweep('x','x','x','x','',False)
        with patch('b6.stage2b_search.importlib.util.find_spec',return_value=None):
            with self.assertRaises(PermissionError):require_full_authorization('a'*40,True)
    def test_resume_identity_result_hash_and_corruption(self):
        identity=dict(code_sha='a',config_sha256='b',stage2a_code_sha='c',stage2a_config_sha256='d',stage2a_result_sha256={'all':'e'},candidate_sha256='f',inputs=[{'SHA256':'g'}],runtime={'Python':'p','Numpy':'n','Pandas':'x'})
        with tempfile.TemporaryDirectory() as d:
            ledger=open_store(d,identity);save_job(d,ledger,'test',{'value':1});self.assertEqual(read_job(d,open_store(d,identity),'test'),{'value':1})
            for k in identity:
                changed=copy.deepcopy(identity);changed[k]='changed'
                with self.assertRaises(ValueError):open_store(d,changed)
            (Path(d)/'shards/test.json').write_text('{}')
            with self.assertRaises(ValueError):read_job(d,ledger,'test')
    def test_synthetic_finish_all_fail_and_resume(self):
        c=load_config();a=candidate();jobs,space=prepare_jobs([a],[point(tp=None)],c)
        dates=pd.DatetimeIndex(['2020-02-04']);bars=fixture('USDJPY',dates,n=40)
        job=jobs[0];data=evaluate_candidate(FastEngine(bars,'USDJPY'),a,dates,job['grid'],c);data.update(centers=job['centers'],grid=job['grid'])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);ledger=open_store(p,{'inputs':[]})
            for name in ('effective_config','stage2a_input_audit','search_space'):(p/(name+'.json')).write_text('{}')
            with self.assertRaises(ValueError):finish(p,ledger,jobs,c,space)
            save_job(p,ledger,a['CandidateID'],data);result=finish(p,ledger,jobs,c,space)
            self.assertEqual(result['ActualUniqueConfigurations'],5);self.assertEqual(result['SelectedStructures'],0);self.assertEqual(result['DroppedStructures'],1)
            self.assertEqual(len(pd.read_csv(p/'stage2b_all_results.csv.gz')),5);self.assertEqual(len(pd.read_csv(p/'stage2b_yearly_results.csv.gz')),20)
            self.assertEqual(json.loads((p/'stage2b_selected_settings.json').read_text()),[]);self.assertEqual(finish(p,open_store(p,{'inputs':[]}),jobs,c,space),result)
    def test_passing_finalization_selected_yearly_and_overlap(self):
        from b6.stage2a_engine import Replay
        c=load_config();a=candidate();cs=[center(),center(55,105,'EFFICIENCY')];grid=local_grid(cs,c)
        dates=pd.DatetimeIndex([d for y in (2020,2021,2022,2023) for d in pd.date_range(f'{y}-02-04',periods=40,freq='7D')])
        raw=np.tile(np.tile([2.,2.,2.,-1.],40),(len(grid),1))
        records=[[dict(Status='OK',ExitReason='TP' if r>0 else 'SL',ExitDelayMinutes=0,missing_path_minutes=0,exit_bar_first_hit=False) for r in values] for values in raw]
        rep=Replay(dates,np.zeros(160,dtype=int),records,raw);data=summarize(a,grid,rep,c['gate']);data.update(centers=cs,grid=grid)
        jobs=[dict(candidate=a,centers=cs,grid=grid)];space={'ActualUniqueConditions':34}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);ledger=open_store(p,{'inputs':[]})
            for name in ('effective_config','stage2a_input_audit','search_space'):(p/(name+'.json')).write_text('{}')
            save_job(p,ledger,a['CandidateID'],data);result=finish(p,ledger,jobs,c,space)
            self.assertEqual(result['SelectedStructures'],1);self.assertEqual(result['ActualUniqueConfigurations'],34)
            selected=json.loads((p/'stage2b_selected_settings.json').read_text());self.assertEqual(len(selected),1);self.assertEqual(len(selected[0]['YearlyMetrics']),4)
            self.assertEqual(selected[0]['SelectedSL'],50);self.assertEqual(selected[0]['SelectedTP'],100);self.assertEqual(selected[0]['CenterDistance'],0)
            self.assertEqual(len(pd.read_csv(p/'stability_results.csv.gz')),34);self.assertEqual(len(pd.read_csv(p/'stability_by_center.csv.gz')),50)
            self.assertEqual(len(pd.read_csv(p/'dropped_structures.csv')),0)

    def test_zero_centers_empty_schema_and_no_refill(self):
        c=load_config();a=candidate();jobs,space=prepare_jobs([a],[point(passed=False)],c)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);ledger=open_store(p,{'inputs':[]})
            for name in ('effective_config','stage2a_input_audit','search_space'):(p/(name+'.json')).write_text('{}')
            save_job(p,ledger,a['CandidateID'],dict(results=[],yearly=[],diagnostics=[],centers=[],grid=[]));summary=finish(p,ledger,jobs,c,space)
            self.assertEqual(summary['ActualUniqueConfigurations'],0);self.assertEqual(summary['DroppedStructures'],1);self.assertIn('AvgR',pd.read_csv(p/'stage2b_all_results.csv.gz').columns)
