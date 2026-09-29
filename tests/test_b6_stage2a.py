"""Synthetic/limited compatibility only. Never starts a production sweep."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage2a_config import load_config,tp_grid,settings,validate_structures,load_candidates,sha
from b6.stage2a_engine import FastEngine,Replay,fast_replay,reference_replay
from b6.stage2a_metrics import summarize
from b6.stage2a_search import open_store,save_job,read_job,finish,require_full_authorization,full_sweep
from b6.stage1_engine import STATUS
from b6.execution import PIPS,SPREAD,END
from test_b6_stage1 import fixture

def candidate(symbol='USDJPY',direction='L',weekday=1,entry=0,hold=30):
    return dict(CandidateID=f'B6-{symbol}-{direction}-W{weekday}-E{entry:04d}-H{hold:04d}',Symbol=symbol,Direction=direction,Weekday=weekday,EntryMinute=entry,ExitMinute=(entry+hold)%1440,ExitDayOffset=(entry+hold)//1440,HoldingMinutes=hold)

def fifty():return [candidate(entry=i*5) for i in range(50)]

def compare(test,bars,a,dates,grid):
    fast=fast_replay(FastEngine(bars,a['Symbol']),a,dates,grid)
    slow=reference_replay(bars,a['Symbol'],a,dates,grid)
    np.testing.assert_array_equal(fast.status,slow.status);np.testing.assert_array_equal(fast.raw_r,slow.raw_r)
    for i in range(len(grid)):
        for f,s in zip(fast.records(i),slow.records(i)):
            for k,v in f.items():test.assertEqual(v,s[k],(a,grid[i],k,f,s))
    test.assertEqual(summarize(a,grid,fast,load_config()['gate']),summarize(a,grid,slow,load_config()['gate']))
    return fast

class GridTests(unittest.TestCase):
    def test_half_up_example_and_minimum_dedup(self):
        self.assertEqual(tp_grid(25)[1]['TP'],15)
        g=tp_grid(5);self.assertEqual([x['TP'] for x in g],[None,5,10,15]);self.assertEqual(g[1]['RatioAliases'],['0.5','1.0'])
    def test_all_fixed_pairs_1500(self):
        c=load_config()
        for symbol in c['sl_pips']:
            g=settings(candidate(symbol));self.assertEqual(len(g),30)
            for sl in c['sl_pips'][symbol]:self.assertEqual(len({x['TP'] for x in g if x['SL']==sl}),6)
        self.assertEqual(sum(len(settings(a)) for a in validate_structures(fifty(),c)),1500)
    def test_count_id_structure_gates(self):
        c=load_config()
        for mutation in ('count','duplicate','id','schedule','type','weekday','direction','hold','grid'):
            rows=fifty();cfg=copy.deepcopy(c)
            if mutation=='count':rows.pop()
            elif mutation=='duplicate':rows[1]=rows[0]
            elif mutation=='id':rows[0]['CandidateID']='made-up'
            elif mutation=='schedule':rows[0]['ExitMinute']=31
            elif mutation=='type':rows[0]['EntryMinute']=False
            elif mutation=='weekday':rows[0]['Weekday']=6
            elif mutation=='direction':rows[0]['Direction']='BUY'
            elif mutation=='hold':rows[0]['HoldingMinutes']=1445
            elif mutation=='grid':cfg['tp_ratios']=['1.0']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):validate_structures(rows,cfg)
    def test_exact_bytes_and_stage1_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);cf=p/'candidate.json';ef=p/'effective.json';it=p/'identity.json';rows=fifty();rows[0]['MedianAvgR']=999
            cf.write_text(json.dumps(rows));ef.write_text('{}');c=copy.deepcopy(load_config());c.update(candidate_sha256=sha(cf),stage1_effective_config_sha256=sha(ef))
            ident=dict(code_sha=c['stage1_freeze_sha'],config_sha256=c['stage1_effective_config_sha256']);it.write_text(json.dumps(ident))
            got,audit=load_candidates(cf,it,ef,c);self.assertEqual(got,fifty());self.assertEqual(audit['Configurations'],1500)
            for name in ('candidate','effective','code','identity_config'):
                cc=copy.deepcopy(c);ii=ident.copy()
                if name=='candidate':cc['candidate_sha256']='0'*64
                elif name=='effective':cc['stage1_effective_config_sha256']='0'*64
                elif name=='code':ii['code_sha']='0'*40
                else:ii['config_sha256']='0'*64
                it.write_text(json.dumps(ii))
                with self.subTest(name=name),self.assertRaises(ValueError):load_candidates(cf,it,ef,cc)

class ReplayTests(unittest.TestCase):
    def test_seven_pairs_both_directions_same_day_overnight(self):
        dates=pd.DatetimeIndex(['2020-02-04','2021-02-02','2022-02-01','2023-02-07'])
        for symbol,sls in load_config()['sl_pips'].items():
            bars=fixture(symbol,dates,n=1500)
            for direction in ('L','S'):
                for entry,hold in ((0,30),(1410,60)):
                    a=candidate(symbol,direction,entry=entry,hold=hold);grid=[x for sl in (sls[0],sls[-1]) for x in tp_grid(sl)]
                    compare(self,bars,a,dates,grid)
    def test_entry_exit_sl_tp_ties_raw_boundaries(self):
        d=pd.Timestamp('2020-02-04');idx=pd.date_range(d,periods=31,freq='min')
        for symbol in load_config()['sl_pips']:
            base=100. if PIPS[symbol]==.01 else 1.;pip=PIPS[symbol]
            for direction in ('L','S'):
                sign=1 if direction=='L' else -1;entry=base+sign*SPREAD[symbol]*pip;stop=entry-sign*20*pip;target=entry+sign*20*pip
                a=candidate(symbol,direction);grid=[tp_grid(20)[2]]
                for bar in (0,30):
                    for kind in ('SL','TP','TIE','TP_BELOW','SL_BELOW'):
                        bars=pd.DataFrame(base,index=idx,columns=['Open','High','Low','Close'])
                        if kind in ('SL','TIE','SL_BELOW'):bars.loc[idx[bar],'Low' if sign==1 else 'High']=np.nextafter(stop,np.inf if sign==1 else -np.inf) if kind=='SL_BELOW' else stop
                        if kind in ('TP','TIE','TP_BELOW'):bars.loc[idx[bar],'High' if sign==1 else 'Low']=np.nextafter(target,-np.inf if sign==1 else np.inf) if kind=='TP_BELOW' else target
                        out=compare(self,bars,a,[d],grid);reason=out.records(0)[0]['ExitReason']
                        self.assertEqual(reason,'SL' if kind in ('SL','TIE') else 'TP' if kind=='TP' else 'TimeExit')
    def test_tp_before_sl_and_sl_before_tp(self):
        d=pd.Timestamp('2020-02-04');idx=pd.date_range(d,periods=31,freq='min');a=candidate();grid=[tp_grid(20)[2]]
        for first in ('SL','TP'):
            bars=pd.DataFrame(100.,index=idx,columns=['Open','High','Low','Close'])
            bars.loc[idx[1 if first=='SL' else 2],'Low']=99.;bars.loc[idx[1 if first=='TP' else 2],'High']=101.
            self.assertEqual(compare(self,bars,a,[d],grid).records(0)[0]['ExitReason'],first)
    def test_fallback_missing_intermediate_and_no_early_rescue(self):
        dates=pd.date_range('2020-02-04',periods=7,freq='7D');bars=fixture('USDJPY',dates,n=40)
        for i,d in enumerate(dates[:6]):bars=bars.drop(pd.date_range(d+pd.Timedelta(minutes=30),periods=i,freq='min'))
        bars=bars.drop(dates[6]);bars=bars.drop(dates[0]+pd.Timedelta(minutes=10));bars.loc[dates[5],'High']=110;bars.loc[dates[5],'Low']=90
        for direction in ('L','S'):
            out=compare(self,bars,candidate(direction=direction),dates,tp_grid(10))
            self.assertEqual(out.status[-2],STATUS.index('MISSING_EXIT'));self.assertEqual(out.status[-1],STATUS.index('MISSING_ENTRY'))
            self.assertEqual([r['ExitDelayMinutes'] for r in out.records(1)[:5]],list(range(5)))
            self.assertEqual(out.records(1)[0]['missing_path_minutes'],1)
    def test_year_end_discovery_boundary_and_weekday(self):
        dates=pd.DatetimeIndex(['2020-01-01','2020-12-30']);bars=fixture('USDJPY',dates,n=1500)
        out=compare(self,bars,candidate(weekday=2),dates,tp_grid(10));self.assertTrue((out.status==STATUS.index('FILTERED_YEAR_END')).all())
        outside=pd.concat([bars,pd.DataFrame(100.,index=[END],columns=bars.columns)])
        for fn in (lambda:FastEngine(outside,'USDJPY'),lambda:reference_replay(outside,'USDJPY',candidate(weekday=2),dates,tp_grid(10)),lambda:fast_replay(FastEngine(bars,'USDJPY'),candidate(),dates,tp_grid(10))):
            with self.assertRaises(ValueError):fn()

class MetricTests(unittest.TestCase):
    def test_raw_r_zero_pf_and_gate_no_pruning(self):
        dates=pd.date_range('2020-02-04',periods=4,freq='7D');r=np.array([[1.00000000001,-1.,0.,np.nan]])
        rows=[[dict(Status='OK',ExitReason='TP' if i==0 else 'SL' if i==1 else 'TimeExit',ExitDelayMinutes=0,missing_path_minutes=0,exit_bar_first_hit=False) if i<3 else dict(Status='MISSING_ENTRY') for i in range(4)]]
        rep=Replay(dates,np.array([0,0,0,STATUS.index('MISSING_ENTRY')]),rows,r);g=[tp_grid(10)[0]]
        m=summarize(candidate(),g,rep,load_config()['gate']);x=m['results'][0]
        self.assertEqual((x['Trades'],x['Wins'],x['Losses'],x['ZeroR']),(3,1,1,1));self.assertGreater(x['TotalR'],0);self.assertLess(x['TotalR'],1e-9);self.assertFalse(x['Pass']);self.assertEqual(len(m['yearly']),4)
        self.assertAlmostEqual(x['PF'],1.00000000001);self.assertEqual(x['MaxDDR'],1.);self.assertEqual(x['AvgLossR'],-1.)
    def test_gate_pass_and_each_threshold(self):
        dates=pd.DatetimeIndex([d for y in (2020,2021,2022,2023) for d in pd.date_range(f'{y}-02-04',periods=40,freq='7D')])
        raw=np.tile(np.array([2.,2.,2.,-1.]),40)[None,:]
        rows=[[dict(Status='OK',ExitReason='TP' if v>0 else 'SL',ExitDelayMinutes=0,missing_path_minutes=0,exit_bar_first_hit=False) for v in raw[0]]]
        rep=Replay(dates,np.zeros(160,dtype=int),rows,raw);grid=[tp_grid(10)[4]];gate=load_config()['gate']
        self.assertTrue(summarize(candidate(),grid,rep,gate)['results'][0]['Pass'])
        for name,value,reason in (('min_trades',161,'TOTAL_TRADES'),('min_annual_trades',41,'ANNUAL_TRADES_2020'),('min_losses',41,'LOSS_COUNT'),('min_pf',6.1,'PF'),('min_positive_years',5,'POSITIVE_YEARS')):
            g=dict(gate);g[name]=value;result=summarize(candidate(),grid,rep,g)['results'][0]
            self.assertFalse(result['Pass']);self.assertIn(reason,result['FailReasons'])

    def test_empty_conditions_saved(self):
        d=pd.DatetimeIndex(['2020-02-04']);grid=tp_grid(10);rep=Replay(d,np.array([STATUS.index('MISSING_EXIT')]),[[dict(Status='MISSING_EXIT')] for _ in grid],np.full((len(grid),1),np.nan))
        m=summarize(candidate(),grid,rep,load_config()['gate']);self.assertEqual(len(m['results']),6)
        self.assertTrue(all(r['PF']=='UNDEFINED' and not r['Pass'] and r['Trades']==0 for r in m['results']))

class StoreTests(unittest.TestCase):
    def test_identity_all_fields_and_corruption(self):
        identity=dict(code_sha='a',config_sha256='b',candidate_sha256='c',inputs=[dict(Filename='x',SHA256='d')],runtime=dict(Python='x',Numpy='y',Pandas='z'))
        with tempfile.TemporaryDirectory() as d:
            ledger=open_store(d,identity);save_job(d,ledger,'candidate',{'test':1});self.assertEqual(read_job(d,open_store(d,identity),'candidate'),{'test':1})
            for k in identity:
                changed=copy.deepcopy(identity);changed[k]='changed'
                with self.subTest(field=k),self.assertRaises(ValueError):open_store(d,changed)
            (Path(d)/'shards/candidate.json').write_text('{}')
            with self.assertRaises(ValueError):read_job(d,ledger,'candidate')
    def test_finish_small_synthetic_all_failed_and_resume(self):
        a=candidate();c=copy.deepcopy(load_config());c['expected_configurations']=30;grid=settings(a,c)
        rep=Replay(pd.DatetimeIndex(['2020-02-04']),np.array([STATUS.index('MISSING_EXIT')]),[[dict(Status='MISSING_EXIT')] for _ in grid],np.full((30,1),np.nan));job=summarize(a,grid,rep,c['gate'])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);identity={'inputs':[]};ledger=open_store(p,identity)
            for name in ('candidate_input_audit','effective_config','search_space'):(p/(name+'.json')).write_text('{}')
            with self.assertRaises(ValueError):finish(p,ledger,[a],c)
            save_job(p,ledger,a['CandidateID'],job);summary=finish(p,ledger,[a],c)
            self.assertEqual(summary['Configurations'],30);self.assertEqual(summary['FailCount'],30);self.assertFalse(summary['Stage2BCentersSelected']);self.assertTrue((p/'stage2a_review.zip').exists())
            self.assertEqual(len(pd.read_csv(p/'stage2a_all_results.csv.gz')),30);self.assertEqual(len(pd.read_csv(p/'stage2a_yearly_results.csv.gz')),120)
            self.assertFalse(any('selected' in f.name for f in p.iterdir()));self.assertEqual(finish(p,open_store(p,identity),[a],c),summary)
    def test_full_guard_before_any_input_access(self):
        with patch('b6.stage2a_search.load_candidates',side_effect=AssertionError('opened input')):
            with self.assertRaises(PermissionError):full_sweep('missing','missing','missing','missing','missing','',False)
        with patch('b6.stage2a_search.importlib.util.find_spec',return_value=None):
            with self.assertRaises(PermissionError):require_full_authorization('a'*40,True)

if __name__=='__main__':unittest.main()
