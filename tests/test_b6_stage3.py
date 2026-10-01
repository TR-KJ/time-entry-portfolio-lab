"""Synthetic Stage3 schedules/selection and minute-level frozen execution."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage2a import candidate
from test_b6_stage1 import fixture
from b6.stage3_config import load_config
from b6.stage3_grid import time_grid,point_key,execution_candidate,fixed_setting
from b6.stage3_selection import stability,select_final,final_key
from b6.stage3_metrics import evaluate_candidate,evaluate_point
from b6.stage3_search import prepare_jobs,finish,full_sweep,require_full_authorization
from b6.stage2a_engine import FastEngine,Replay,fast_replay,reference_replay
from b6.stage2a_search import open_store,save_job,read_job
from b6.execution import PIPS,SPREAD,END


def fixed(symbol='USDJPY',direction='L',entry=60,hold=60,tp=None,weekday=1):
    return {**candidate(symbol,direction,weekday,entry,hold),'SL':20,'TP':tp,'TPMode':'TP_NONE' if tp is None else 'FINITE'}

def synthetic(a,c,avg=1.):
    grid,_=time_grid(a,c)
    return [{**p,'AvgR':avg,'TotalR':160*avg,'PF':2.,'MaxDDR':1.,'Pass':True} for p in grid]

def compare(test,bars,a,p,dates):
    engine=FastEngine(bars,a['Symbol']);c=load_config()
    fast=fast_replay(engine,execution_candidate(p),dates,[fixed_setting(p)]);slow=reference_replay(bars,a['Symbol'],execution_candidate(p),dates,[fixed_setting(p)])
    np.testing.assert_array_equal(fast.status,slow.status);np.testing.assert_array_equal(fast.raw_r,slow.raw_r)
    for f,s in zip(fast.records(0),slow.records(0)):
        for k,v in f.items():test.assertEqual(v,s[k],(k,f,s))
    test.assertEqual(evaluate_point(engine,p,dates,c),evaluate_point(None,p,dates,c,bars=bars))
    return fast

class GridTests(unittest.TestCase):
    def test_121_minute_steps_no_expansion_duplicates(self):
        g,bad=time_grid(fixed());self.assertEqual(len(g),121);self.assertEqual(bad,[])
        self.assertEqual({p['EntryDeltaMinutes'] for p in g},set(range(-5,6)));self.assertEqual({p['ExitDeltaMinutes'] for p in g},set(range(-5,6)));self.assertEqual(len({point_key(p) for p in g}),121)
    def test_same_day_overnight_and_fixed_fields(self):
        for a in (fixed(),fixed(entry=1410,hold=60),fixed(tp=25)):
            g,_=time_grid(a)
            for p in g:
                for k in ('CandidateID','Symbol','Direction','Weekday','ExitDayOffset','SL','TP'):self.assertEqual(p[k],a[k])
                self.assertEqual(p['AdjustedExitDayOffset'],a['ExitDayOffset']);self.assertEqual(p['PlannedHoldingMinutes'],a['HoldingMinutes']+p['ExitDeltaMinutes']-p['EntryDeltaMinutes'])
    def test_entry_midnight_reject_previous_next_day(self):
        for e in (0,1435):
            g,bad=time_grid(fixed(entry=e,hold=60));self.assertTrue(bad)
            self.assertTrue(all(0<=p['AdjustedEntryMinute']<1440 for p in g));self.assertTrue(any('ENTRY_DATE_WEEKDAY_CHANGED' in p['Reasons'] for p in bad))
    def test_exit_day_offset_midnight_unchanged(self):
        g,bad=time_grid(fixed(entry=1410,hold=30));self.assertTrue(any('EXIT_DAY_OFFSET_CHANGED' in x['Reasons'] for x in bad));self.assertTrue(all(p['ExitDeltaMinutes']>=0 for p in g))
    def test_holding_30_and_1440_boundaries(self):
        for h in (30,1440):
            g,bad=time_grid(fixed(hold=h));self.assertEqual(len(g),66);self.assertEqual(len(bad),55)
            self.assertTrue(all(30<=p['PlannedHoldingMinutes']<=1440 for p in g))
        g,bad=time_grid(fixed(hold=30));self.assertIn((1,0),{point_key(p) for p in bad})
        g,bad=time_grid(fixed(hold=1440));self.assertIn((0,1),{point_key(p) for p in bad})
    def test_anchor_not_rebased(self):
        a=fixed();a['EntryMinute']+=1;a['ExitMinute']+=1
        with self.assertRaises(ValueError):time_grid(a)
    def test_search_counts_account_invalid(self):
        jobs,s=prepare_jobs([fixed(),fixed(entry=0,hold=30)],load_config());self.assertEqual(s['TheoreticalMax'],242);self.assertEqual(s['RawGridPoints'],s['InvalidSchedulePoints']+s['ActualUniqueConfigurations'])

class StabilityTests(unittest.TestCase):
    def test_full_edge_corner_self(self):
        a=fixed();c=load_config();rows=synthetic(a,c);out={point_key(r):r for r in stability(a,rows,c)}
        self.assertEqual(out[(0,0)]['NeighborhoodCount'],9);self.assertEqual(out[(-5,0)]['NeighborhoodCount'],6);self.assertEqual(out[(-5,-5)]['NeighborhoodCount'],4)
        rows[60]['Pass']=False;out={point_key(r):r for r in stability(a,rows,c)};self.assertFalse(out[(0,0)]['StabilityPass']);self.assertEqual(out[(0,0)]['NeighborhoodPassCount'],8)
    def test_invalid_neighbors_excluded_and_no_minimum(self):
        a=fixed(hold=30);c=load_config();out={point_key(r):r for r in stability(a,synthetic(a,c),c)}
        self.assertLess(out[(5,5)]['NeighborhoodCount'],9);self.assertEqual(out[(5,5)]['NeighborhoodPassRate'],1);self.assertTrue(out[(5,5)]['StabilityPass']);self.assertNotIn('minimum_neighbor_count',c['stability'])
    def test_exact_two_thirds_and_below(self):
        a=fixed();c=load_config();rows=synthetic(a,c)
        for r in rows:
            if r['EntryDeltaMinutes']==-1 and abs(r['ExitDeltaMinutes'])<=1:r['Pass']=False
        out={point_key(r):r for r in stability(a,rows,c)};self.assertEqual(out[(0,0)]['NeighborhoodPassRate'],2/3);self.assertTrue(out[(0,0)]['StabilityPass'])
        next(r for r in rows if point_key(r)==(0,1))['Pass']=False;out={point_key(r):r for r in stability(a,rows,c)};self.assertFalse(out[(0,0)]['StabilityPass'])
    def test_exact_eighty_percent_and_below(self):
        a=fixed();c=load_config();rows=synthetic(a,c,.8);next(r for r in rows if point_key(r)==(0,0))['AvgR']=1
        self.assertTrue(next(r for r in stability(a,rows,c) if point_key(r)==(0,0))['StabilityPass'])
        for r in rows:
            if point_key(r)!=(0,0):r['AvgR']=.799
        self.assertFalse(next(r for r in stability(a,rows,c) if point_key(r)==(0,0))['StabilityPass'])
    def test_incomplete_duplicate_and_fixed_field_mutations(self):
        a=fixed();c=load_config();rows=synthetic(a,c)
        for bad in (rows[:-1],rows+[rows[0]]):
            with self.assertRaises(ValueError):stability(a,bad,c)
        for k,v in [('SL',25),('TP',20),('Symbol','GBPJPY'),('Direction','S'),('Weekday',2),('ExitDayOffset',1)]:
            bad=copy.deepcopy(rows);bad[0][k]=v
            with self.subTest(k=k),self.assertRaises(ValueError):stability(a,bad,c)
    def test_undefined_is_not_zero_imputed(self):
        a=fixed();c=load_config();rows=synthetic(a,c);rows[60]['AvgR']='UNDEFINED';rows[60]['Pass']=False
        self.assertTrue(any('UNDEFINED_NEIGHBOR_METRICS' in r['StabilityFailReason'] for r in stability(a,rows,c)))

class SelectionTests(unittest.TestCase):
    def test_only_three_ranking_layers(self):
        a=fixed();p=time_grid(a)[0][0];base={**p,'NeighborhoodMedianAvgR':1,'AnchorDistance':5}
        self.assertLess(final_key({**base,'NeighborhoodMedianAvgR':2,'AnchorDistance':10}),final_key(base))
        self.assertLess(final_key({**base,'AnchorDistance':4}),final_key(base))
        self.assertLess(final_key({**base,'AdjustedEntryMinute':base['AdjustedEntryMinute']-1}),final_key(base))
        for k in ('PointAvgR','AvgR','PF','MaxDDR','TotalR','WinRate','NeighborhoodPassRate','Stage2BScore'):
            self.assertEqual(final_key({**base,k:999999}),final_key({**base,k:-999999}),k)
    def test_anchor_wins_tie_one_selected_four_years(self):
        a=fixed();c=load_config();rows=synthetic(a,c);years=[{**r,'Year':y} for r in rows for y in (2020,2021,2022,2023)]
        result=select_final(a,rows,years,c);self.assertEqual(point_key(result['selected']),(0,0));self.assertEqual(len(result['selected']['YearlyMetrics']),4);self.assertEqual(result['selected']['SL'],a['SL']);self.assertIsNone(result['selected']['TP'])
    def test_no_stable_drop_no_refill(self):
        a=fixed();c=load_config();rows=synthetic(a,c)
        for r in rows:r['Pass']=False
        result=select_final(a,rows,[],c);self.assertIsNone(result['selected']);self.assertEqual(result['dropped']['Reason'],'STAGE3_DROPPED_NO_STABLE_TIME')

class ExecutionTests(unittest.TestCase):
    def test_seven_pairs_directions_none_finite_one_minute_same_overnight(self):
        dates=pd.DatetimeIndex(['2020-02-04','2021-02-02','2022-02-01','2023-02-07'])
        for symbol in load_config()['spread_pips']:
            bars=fixture(symbol,dates,n=1500)
            for direction in ('L','S'):
                for e in (60,1410):
                    for tp in (None,20):
                        a=fixed(symbol,direction,e,60,tp);p=next(p for p in time_grid(a)[0] if point_key(p)==(1,2));compare(self,bars,a,p,dates)
    def test_entry_exit_inclusive_tie_and_raw_boundaries(self):
        d=pd.Timestamp('2020-02-04');idx=pd.date_range(d,periods=40,freq='min')
        for direction in ('L','S'):
            sign=1 if direction=='L' else -1;a=fixed(direction=direction,entry=0,hold=30,tp=20);p=next(p for p in time_grid(a)[0] if point_key(p)==(1,2));entry=100+sign*.005;sl=entry-sign*.2;tp=entry+sign*.2
            for bar in (1,32):
                for kind in ('SL','TP','BOTH','NEAR_TP','NEAR_SL'):
                    bars=pd.DataFrame(100.,index=idx,columns=['Open','High','Low','Close'])
                    if kind in ('SL','BOTH','NEAR_SL'):bars.loc[idx[bar],'Low' if sign==1 else 'High']=np.nextafter(sl,np.inf if sign==1 else -np.inf) if kind=='NEAR_SL' else sl
                    if kind in ('TP','BOTH','NEAR_TP'):bars.loc[idx[bar],'High' if sign==1 else 'Low']=np.nextafter(tp,-np.inf if sign==1 else np.inf) if kind=='NEAR_TP' else tp
                    replay=compare(self,bars,a,p,[d]);self.assertEqual(replay.records(0)[0]['ExitReason'],'SL' if kind in ('SL','BOTH') else 'TP' if kind=='TP' else 'TimeExit')
    def test_fallback_missing_entry_exit_and_intermediate(self):
        dates=pd.date_range('2020-02-04',periods=7,freq='7D');bars=fixture('USDJPY',dates,n=45);a=fixed(entry=0,hold=30,tp=20);p=next(p for p in time_grid(a)[0] if point_key(p)==(1,2))
        for i,d in enumerate(dates[:6]):bars=bars.drop(pd.date_range(d+pd.Timedelta(minutes=32),periods=i,freq='min'))
        bars=bars.drop(dates[-1]+pd.Timedelta(minutes=1));bars=bars.drop(dates[0]+pd.Timedelta(minutes=10));bars.loc[dates[5]+pd.Timedelta(minutes=1),'High']=110
        replay=compare(self,bars,a,p,dates);rows=replay.records(0)
        self.assertEqual([r['ExitDelayMinutes'] for r in rows[:5]],list(range(5)));self.assertEqual(rows[5]['Status'],'MISSING_EXIT');self.assertEqual(rows[6]['Status'],'MISSING_ENTRY');self.assertEqual(rows[0]['missing_path_minutes'],1)
    def test_year_end_stop_future_rejection(self):
        dates=pd.DatetimeIndex(['2020-01-01','2020-12-30']);bars=fixture('USDJPY',dates,n=100);a=fixed(weekday=2,entry=0,hold=30);p=next(p for p in time_grid(a)[0] if point_key(p)==(1,2));r=compare(self,bars,a,p,dates);self.assertTrue(all(x['Status']=='FILTERED_YEAR_END' for x in r.records(0)))
        with self.assertRaises(ValueError):FastEngine(pd.concat([bars,pd.DataFrame(100.,index=[END],columns=bars.columns)]),'USDJPY')

class RunnerTests(unittest.TestCase):
    def test_no_authorization_no_input_price_or_grid(self):
        with patch('b6.stage3_search.load_input',side_effect=AssertionError('input opened')),patch('b6.stage3_search.prepare_jobs',side_effect=AssertionError('grid')):
            with self.assertRaises(PermissionError):full_sweep('x','x','x','x','',False)
        with patch('b6.stage3_search.importlib.util.find_spec',return_value=None):
            with self.assertRaises(PermissionError):require_full_authorization('a'*40,True)
    def test_resume_all_identity_fields_and_corruption(self):
        identity=dict(code_sha='a',config_sha256='b',stage2b_code_sha='c',selected_settings_sha256='d',stage2b_runtime_sha256={'a':'e'},candidate_sha256='f',inputs=[{'SHA256':'g'}],runtime={'Python':'p','Numpy':'n','Pandas':'x'})
        with tempfile.TemporaryDirectory() as d:
            ledger=open_store(d,identity);save_job(d,ledger,'test',{'ok':1});self.assertEqual(read_job(d,open_store(d,identity),'test'),{'ok':1})
            for k in identity:
                changed=copy.deepcopy(identity);changed[k]='changed'
                with self.assertRaises(ValueError):open_store(d,changed)
            (Path(d)/'shards/test.json').write_text('{}')
            with self.assertRaises(ValueError):read_job(d,ledger,'test')
    def test_finish_synthetic_pass_fail_resume_and_schemas(self):
        from b6.stage2a_metrics import summarize
        from b6.stage1_search import json_safe
        c=load_config();a=fixed();jobs,space=prepare_jobs([a],c);grid=jobs[0]['grid'];dates=pd.DatetimeIndex([d for y in (2020,2021,2022,2023) for d in pd.date_range(f'{y}-02-04',periods=40,freq='7D')]);raw=np.tile([2.,2.,2.,-1.],40)[None,:]
        rec=[[dict(Status='OK',ExitReason='TimeExit' if r>0 else 'SL',ExitDelayMinutes=0,missing_path_minutes=0,exit_bar_first_hit=False) for r in raw[0]]];rep=Replay(dates,np.zeros(160,dtype=int),rec,raw)
        data=dict(results=[],yearly=[],diagnostics=[],grid=grid)
        for p in grid:
            m=summarize(execution_candidate(p),[fixed_setting(p)],rep,c['gate'])
            for k in m:
                for row in m[k]:row.update(p)
                data[k].extend(m[k])
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);ledger=open_store(out,{'inputs':[]})
            for n in ('effective_config','stage2b_input_audit','search_space','invalid_schedules'):(out/(n+'.json')).write_text('{}')
            with self.assertRaises(ValueError):finish(out,ledger,jobs,c,space)
            save_job(out,ledger,a['CandidateID'],data);s=finish(out,ledger,jobs,c,space);self.assertEqual(s['SelectedStructures'],1);self.assertEqual(s['AnchorUnchangedCount'],1)
            self.assertEqual(len(pd.read_csv(out/'stage3_all_results.csv.gz')),121);self.assertEqual(len(pd.read_csv(out/'stage3_yearly_results.csv.gz')),484);self.assertEqual(len(json.loads((out/'stage3_selected_settings.json').read_text())[0]['YearlyMetrics']),4)
            self.assertEqual(finish(out,open_store(out,{'inputs':[]}),jobs,c,space),s)
            for row in data['results']:row['Pass']=False
            save_job(out,ledger,a['CandidateID'],data);s=finish(out,ledger,jobs,c,space);self.assertEqual(s['SelectedStructures'],0);self.assertEqual(s['DroppedStructures'],1)
