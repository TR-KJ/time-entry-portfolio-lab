"""No full sweep; deterministic synthetic fixtures and bounded pipeline tests."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
from b6.stage1_config import load_config,search_space
from b6.stage1_engine import ExtremeTree,FastEngine,reference_batch,STATUS
from b6.stage1_metrics import metrics
from b6.stage1_search import open_store,save_job,done,finish,job_arrays,require_full_authorization
from b6.execution import START,END,discovery_view,PIPS,SPREAD
from b6.rules import rank_key

def fixture(symbol,dates,n=1500,seed=7):
    rng=np.random.default_rng(seed);frames=[];pip=PIPS[symbol];base=100.0 if pip==.01 else 1.0
    for d in dates:
        index=pd.date_range(d,periods=n,freq='min');walk=base+np.cumsum(rng.normal(0,.45,n))*pip
        high=walk+rng.uniform(.1,3,n)*pip;low=walk-rng.uniform(.1,3,n)*pip
        frames.append(pd.DataFrame(dict(Open=walk,High=high,Low=low,Close=walk),index=index))
    return pd.concat(frames).sort_index()

def compare(test,bars,symbol,dates,entry,long,sls,holds):
    engine=FastEngine(bars,symbol);batch=engine.prepare(dates,entry,long,sls).evaluate(holds)
    records,r,status=reference_batch(bars,symbol,dates,entry,long,sls,holds)
    np.testing.assert_array_equal(batch.status,status)
    np.testing.assert_array_equal(batch.r,r)
    gate=load_config()['gate']
    for si in range(len(sls)):
        for fast,slow in zip(batch.records(si),records[si]):
            for key,value in fast.items():test.assertEqual(value,slow[key],(symbol,long,key,fast,slow))
        expected=metrics(r[si],status==0,pd.DatetimeIndex(dates).year,gate)
        for key,value in batch.summary(gate)[si].items():np.testing.assert_array_equal(value,expected[key])
    return batch

class TreeTests(unittest.TestCase):
    def test_random_range_first_exact(self):
        rng=np.random.default_rng(31)
        for n in (1,3,16,71):
            a=rng.normal(size=n)
            for is_min in (True,False):
                tree=ExtremeTree(a,is_min);starts=rng.integers(0,n,size=100);ends=np.array([rng.integers(s,n) for s in starts]);levels=rng.normal(size=100)
                result=tree.first(starts,ends,levels)
                expected=[]
                for s,e,t in zip(starts,ends,levels):
                    hits=np.flatnonzero(a[s:e+1]<=t if is_min else a[s:e+1]>=t);expected.append(s+hits[0] if len(hits) else -1)
                np.testing.assert_array_equal(result,expected)
    def test_no_epsilon_and_missing(self):
        t=.12345;a=np.array([np.inf,np.nextafter(t,np.inf),t,t-1]);tree=ExtremeTree(a,True)
        np.testing.assert_array_equal(tree.first(np.array([0,0,0]),np.array([1,2,3]),np.array([t,t,t])),[-1,2,2])

class FastCompatibility(unittest.TestCase):
    def test_all_pairs_directions_narrow_wide_same_day_overnight(self):
        dates=pd.DatetimeIndex(['2020-02-04','2021-02-02','2022-02-01','2023-02-07'])
        c=load_config()
        for symbol in c['symbols']:
            bars=fixture(symbol,dates)
            for long in (True,False):
                for e in (0,1410):
                    compare(self,bars,symbol,dates,e,long,[c['sl_pips'][symbol][0],c['sl_pips'][symbol][-1]],[30,60,1440])
    def test_fallback_internal_missing_entry_and_exit_missing_even_if_sl(self):
        dates=pd.DatetimeIndex(['2020-02-04','2020-02-11','2020-02-18','2020-02-25','2020-03-03','2020-03-10','2020-03-17'])
        bars=fixture('USDJPY',dates,n=40)
        for i,d in enumerate(dates[:5]):bars=bars.drop(pd.date_range(d+pd.Timedelta(minutes=30),periods=i,freq='min'))
        bars=bars.drop(pd.date_range(dates[5]+pd.Timedelta(minutes=30),periods=5,freq='min'))
        bars.loc[dates[5],'Low']=90
        bars=bars.drop(dates[6]);bars=bars.drop(dates[0]+pd.Timedelta(minutes=10))
        for long in (True,False):
            batch=compare(self,bars,'USDJPY',dates,0,long,[10,95],[30])
            self.assertEqual(batch.status[-2,0],STATUS.index('MISSING_EXIT'));self.assertEqual(batch.status[-1,0],STATUS.index('MISSING_ENTRY'))
            np.testing.assert_array_equal(batch.exits[:5,0]-batch.scheduled[:5,0],np.arange(5))
    def test_exact_exit_first_and_entry_hit(self):
        d=pd.Timestamp('2020-02-04');index=pd.date_range(d,periods=31,freq='min')
        for long in (True,False):
            bars=pd.DataFrame(100.,index=index,columns=['Open','High','Low','Close'])
            stop=100+(1 if long else -1)*.005-(1 if long else -1)*.2
            bars.loc[index[-1],'Low' if long else 'High']=stop
            batch=compare(self,bars,'USDJPY',[d],0,long,[20],[30]);self.assertTrue(batch.records(0)[0]['exit_bar_first_hit'])
            bars.loc[index[0],'Low' if long else 'High']=stop
            batch=compare(self,bars,'USDJPY',[d],0,long,[20],[30]);self.assertEqual(batch.records(0)[0]['CloseTime'],str(d))
    def test_year_end_and_period_exit_not_rescued_by_sl(self):
        dates=pd.DatetimeIndex(['2020-01-01','2023-12-22','2023-12-29']);bars=fixture('USDJPY',dates)
        compare(self,bars,'USDJPY',dates,0,True,[10,95],[30,1440])
        # Raw out-of-period arrays are rejected before any trigger calculations.
        outside=pd.concat([bars,pd.DataFrame(100.,index=[END],columns=bars.columns)])
        with self.assertRaises(ValueError):FastEngine(outside,'USDJPY')
        isolated=discovery_view(outside);self.assertLess(isolated.index.max(),END)
    def test_duplicates_and_weekday_bounds(self):
        b=fixture('USDJPY',[pd.Timestamp('2020-02-04')],n=60)
        with self.assertRaises(ValueError):FastEngine(pd.concat([b,b.iloc[:1]]),'USDJPY')
        eng=FastEngine(b,'USDJPY')
        for d in ([pd.Timestamp('2024-01-01')],[pd.Timestamp('2020-02-08')]):
            with self.assertRaises(ValueError):eng.prepare(d,0,True,[10])

class MetricsTests(unittest.TestCase):
    def test_independent_known_values_dd_zero_pf(self):
        r=np.array([[1.,0,np.nan],[-2,0,np.nan],[3,0,np.nan],[-1,0,np.nan]])
        valid=np.isfinite(r);m=metrics(r,valid,np.array([2020,2021,2022,2023]),load_config()['gate'])
        self.assertEqual(m['N'].tolist(),[4,4,0]);self.assertEqual(m['ZeroTrades'].tolist(),[0,4,0])
        self.assertEqual(m['TotalR'][0],1);self.assertEqual(m['AvgR'][0],.25);self.assertEqual(m['MaxDDR'][0],2);self.assertEqual(m['PF'][0],4/3)
        self.assertTrue(np.isnan(m['PF'][1]));self.assertTrue(np.isnan(m['AvgR'][2]));self.assertFalse(m['Pass'].any())
    def test_annual_gate_three_years_and_min_loss(self):
        years=np.repeat([2020,2021,2022,2023],40);r=np.tile(np.r_[np.ones(30),-np.ones(10)],4)[:,None]
        m=metrics(r,np.ones_like(r,dtype=bool),years,load_config()['gate']);self.assertTrue(m['Pass'][0])
        r[years==2020]*=-1;self.assertTrue(metrics(r,np.ones_like(r,dtype=bool),years,load_config()['gate'])['Pass'][0])
        r[years==2021]*=-1;self.assertFalse(metrics(r,np.ones_like(r,dtype=bool),years,load_config()['gate'])['Pass'][0])
        one=metrics(np.ones((160,1)),np.ones((160,1),bool),years,load_config()['gate']);self.assertTrue(np.isinf(one['PF'][0]));self.assertFalse(one['Pass'][0])
    def test_new_ranking_total_before_worstdd_no_recovery(self):
        def c(name,total,dd):
            m=dict(N=160,annual_N={y:40 for y in range(2020,2024)},losses=20,PF=1.1,AvgR=.1,TotalR=total,MaxDDR=dd,annual_TotalR={y:1 for y in range(2020,2024)})
            return dict(id=name,symbol='USDJPY',direction='L',weekday=0,entry=60,hold=60,sl_metrics=[copy.deepcopy(m) for _ in range(5)])
        a=c('a',20,100);b=c('b',19,1);self.assertLess(rank_key(a),rank_key(b))
        b=c('b',20,2);self.assertLess(rank_key(b),rank_key(a))
        b['sl_metrics'][0]['MaxDDR']=101;self.assertLess(rank_key(a),rank_key(b))

class PipelineTests(unittest.TestCase):
    def test_config_and_work_full_guard(self):
        self.assertEqual(search_space()['time_structures'],5705280);self.assertEqual(search_space()['SL_settings'],28526400)
        with self.assertRaises(PermissionError):require_full_authorization('a'*40,False)
        with patch('b6.stage1_search.importlib.util.find_spec',return_value=None):
            with self.assertRaises(PermissionError):require_full_authorization('a'*40,True)
    def test_shard_smoke_resume_all_five_without_real_ranking(self):
        c=load_config();dates=pd.DatetimeIndex(['2020-02-04','2020-02-11']);b=fixture('USDJPY',dates,n=65);engine=FastEngine(b,'USDJPY')
        arrays,rows=job_arrays(engine,'USDJPY','L',0,dates,np.array([30,60]),c)
        self.assertEqual(arrays['AvgR'].shape,(5,5,2));self.assertEqual(rows,[])
        with tempfile.TemporaryDirectory() as d:
            db=open_store(d,{'test':'synthetic'});save_job(db,d,'fixture',arrays,rows)
            self.assertTrue(done(db,d,'fixture'));self.assertEqual(finish(db,d,c),[])
            with self.assertRaises(ValueError):open_store(d,{'test':'changed'})
            (Path(d)/'shards/fixture.npz').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):done(db,d,'fixture')
            db.close()
    def test_sql_ranking_direct_clusters_and_cap(self):
        c=load_config();c['clustering']['max_structures']=2
        with tempfile.TemporaryDirectory() as d:
            db=open_store(d,{'test':'synthetic-order'})
            arrays={'SL':np.array([10,25,40,60,95]),'AvgR':np.ones((5,5,1))}
            rows=[]
            for i,e in enumerate([60,90,120,180]):
                rows.append((f'synthetic-{i}','USDJPY','L',0,e,60,0,e+60,.1,3,10.,4.,0,0))
            save_job(db,d,'fixture',arrays,list(reversed(rows)));chosen=finish(db,d,c)
            self.assertEqual([r['EntryMinute'] for r in chosen],[60,120]);self.assertEqual(len(chosen[0]['SLResults']),5)
            import gzip
            content=gzip.open(Path(d)/'assignments.csv.gz','rt').read();self.assertIn('SUPPRESSED,synthetic-0',content);self.assertIn('OUTSIDE_TOP50',content)
            db.close()


class AdditionalRegression(unittest.TestCase):
    def test_one_full_sized_job_synthetic_all_holds(self):
        c=load_config();dates=pd.date_range('2020-01-01','2023-12-31',freq='W-TUE')
        bars=fixture('USDJPY',dates,n=1445);engine=FastEngine(bars,'USDJPY')
        arrays,rows=job_arrays(engine,'USDJPY','L',0,dates,np.arange(30,1441,5),c)
        self.assertEqual(arrays['AvgR'].shape,(5,5,283))
        self.assertTrue(np.all(arrays['N'][0]==0))
        self.assertTrue(np.all(arrays['N'][1]>150))
        self.assertTrue(np.all(arrays['N'][1]==arrays['N'][1,0,0]))
        self.assertEqual(int(arrays['Opportunities_OK'].sum()+sum(arrays['Opportunities_'+s].sum() for s in STATUS[1:])),len(dates)*283)
    def test_sql_and_python_rank_agree_with_ties_and_worst_dd(self):
        c=load_config();c['clustering']['max_structures']=50
        from b6.rules import shortlist
        from test_b6_rules import candidate
        aa=[candidate('synthetic-'+str(i),e=i*100) for i in range(4)]
        for i,a in enumerate(aa):
            for m in a['sl_metrics']:m['TotalR']=20 if i<3 else 19;m['MaxDDR']=100 if i==0 else 5
            if i==2:a['sl_metrics'][0]['MaxDDR']=101
        expected=[a['id'] for a in sorted(aa,key=rank_key)]
        with tempfile.TemporaryDirectory() as d:
            db=open_store(d,{'test':'new-rank'})
            z={'SL':np.array([10,25,40,60,95]),'AvgR':np.ones((5,5,1))};rows=[]
            for a in aa:
                k=rank_key(a);e=a['entry'];rows.append((a['id'],'USDJPY','L',0,e,60,0,e+60,-k[0],-k[1],-k[2],k[3],0,0))
            save_job(db,d,'fixture',z,rows);got=finish(db,d,c)
            self.assertEqual([r['CandidateID'] for r in got],expected);db.close()

if __name__=='__main__':unittest.main(verbosity=2)
