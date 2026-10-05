import copy
import random
import unittest
import numpy as np
from b7.stage1_metrics import metric_block,summarize,summarize_arrays,gate,point_result,ranking_key
from b7.stage1_contract import Structure
from b7.stage1_family import neighbors,plateau,near,families


def passing():
    vals=np.array(([2.]*30+[-1.]*10)*4);years=np.repeat([2020,2021,2022,2023],40);order=np.arange(160)
    return summarize_arrays(vals,order,order,years)

def rec(s,metric=None):
    return dict(s.definition(),PureMetrics=passing() if metric is None else metric,FormalPASS=True,PlateauPASS=True)

class MetricsTests(unittest.TestCase):
    def test_pf_states(self):
        for values,pf,state in [([2,-1],2,'FINITE'),([-1],0,'FINITE'),([1],None,'INF'),([],None,'UNDEFINED'),([0,0],None,'UNDEFINED')]:
            m=metric_block(values);self.assertEqual((m['PFpips'],m['PFState']),(pf,state))
    def test_zero_counts(self):
        m=metric_block([1,-1,0]);self.assertEqual([m[k] for k in ['Trades','Wins','Losses','ZeroPips']],[3,1,1,1])
    def test_dd_initial_zero(self):self.assertEqual(metric_block([-3,1,-4,10,-2])['MaxDDPips'],6)
    def test_close_order_fixed_key_determinism(self):
        ts=[dict(Pips=p,EntryTime='2020-02-04 09:00:00',CloseTime=t,FixedKey=[k]) for p,t,k in [(5,'2020-02-04 10:00:00',1),(-4,'2020-02-04 09:30:00',2),(-2,'2020-02-04 10:00:00',0)]]
        a=summarize(ts);self.assertEqual(a['MaxDDPips'],6)
        random.Random(4).shuffle(ts);self.assertEqual(summarize(ts),a)
    def test_entry_year_not_close_year(self):
        m=summarize([dict(Pips=1,EntryTime='2020-12-31',CloseTime='2021-01-01',FixedKey=[])])
        self.assertEqual(m['Annual']['2020']['Trades'],1);self.assertEqual(m['Annual']['2021']['Trades'],0)
    def test_missing_year_no_three_year_median(self):
        m=summarize_arrays(np.ones(160),np.arange(160),np.arange(160),np.full(160,2020))
        self.assertIsNone(m['MedianAnnualAvgPips']);self.assertFalse(gate(m))
    def test_gate_three_vs_two_positive_years(self):
        for n in [3,2]:
            ps=[];ys=[]
            for i,y in enumerate([2020,2021,2022,2023]):ps.extend(([10.]*30+[-1.]*10) if i<n else ([-1.]*30+[1.]*10));ys.extend([y]*40)
            m=summarize_arrays(ps,np.arange(160),np.arange(160),ys);self.assertEqual(gate(m),n==3)
    def test_exact_pf_gate_no_epsilon(self):
        m=passing();m['PFpips']=1.10;self.assertTrue(gate(m));m['PFpips']=np.nextafter(1.10,0);self.assertFalse(gate(m))
        m['PFpips']=1.05;self.assertTrue(gate(m,True));self.assertFalse(gate(m))
    def test_point_requires_both_and_three_sl(self):
        good=passing();bad=copy.deepcopy(good);bad['Losses']=9
        self.assertTrue(point_result(good,[good]*3+[bad]*2)['FormalPASS'])
        self.assertFalse(point_result(good,[good]*2+[bad]*3)['FormalPASS'])
        self.assertFalse(point_result(bad,[good]*5)['FormalPASS'])
    def test_inf_never_formal(self):
        m=passing();m.update(PFState='INF',PFpips=None,Losses=0);self.assertFalse(gate(m));self.assertFalse(gate(m,True))

class PlateauTests(unittest.TestCase):
    def setUp(self):self.s=Structure('USDJPY','LONG',1,540,60)
    def lookup(self,pass_ids,avg=None):
        return lambda s:dict(ScheduleValid=True,FormalPASS=s.candidate_id in pass_ids,AvgPips=10 if avg is None else avg.get(s.candidate_id,10))
    def test_nine_and_two_thirds_boundary(self):
        ns=list(neighbors(self.s));self.assertEqual(len(ns),9)
        six={s.candidate_id for s in ns[:6]}|{self.s.candidate_id}
        self.assertTrue(plateau(self.s,self.lookup(six))['PlateauPASS'])
        five=set(list(six-{self.s.candidate_id})[:4])|{self.s.candidate_id}
        self.assertFalse(plateau(self.s,self.lookup(five))['PlateauPASS'])
    def test_fail_included_in_median(self):
        ns=list(neighbors(self.s));passes={s.candidate_id for s in ns[:6]};passes.add(self.s.candidate_id)
        # Center10, five other pass points7, three failed points-100: median7 fails80%.
        av={s.candidate_id:(7 if s.candidate_id in passes else -100) for s in ns};av[self.s.candidate_id]=10
        p=plateau(self.s,self.lookup(passes,av));self.assertEqual(p['AllValidMedianAvgPips'],7);self.assertFalse(p['PlateauPASS'])
    def test_edge_invalid_not_fail(self):
        s=Structure('USDJPY','LONG',0,0,30);ns=list(neighbors(s));self.assertLess(len(ns),9)
        p=plateau(s,self.lookup({x.candidate_id for x in ns}));self.assertEqual(p['ValidCount'],len(ns))
    def test_isolated_peak(self):self.assertFalse(plateau(self.s,self.lookup({self.s.candidate_id}))['PlateauPASS'])
    def test_undefined_valid_point_not_dropped(self):
        ns=list(neighbors(self.s));av={ns[0].candidate_id:None}
        p=plateau(self.s,self.lookup({s.candidate_id for s in ns},av));self.assertIsNone(p['AllValidMedianAvgPips']);self.assertFalse(p['PlateauPASS'])

class FamilyRankingTests(unittest.TestCase):
    def test_nontransitive_and_cross_weekday(self):
        a=Structure('USDJPY','LONG',0,540,60);b=Structure('USDJPY','LONG',1,570,60);c=Structure('USDJPY','LONG',2,600,60)
        fs=families([rec(c),rec(b),rec(a)]);self.assertEqual(len(fs),2)
        self.assertEqual(fs[0]['SuppressedCandidateIDs'],[b.candidate_id]);self.assertEqual(fs[0]['SupportingWeekdays'],[0,1]);self.assertEqual(len(fs[0]['Members']),2)
    def test_midnight_circular(self):
        a=Structure('USDJPY','LONG',0,5,30);b=Structure('USDJPY','LONG',1,1435,30)
        self.assertFalse(near(a,b)) # distinct exit offset still required
        a=Structure('USDJPY','LONG',0,5,1440);b=Structure('USDJPY','LONG',1,1435,1440)
        self.assertTrue(near(a,b));self.assertEqual(len(families([rec(a),rec(b)])),1)
    def test_all_lexicographic_priorities(self):
        s=Structure('USDJPY','LONG',0,540,60);base=passing()
        metrics=['PositiveYearCount','MedianAnnualAvgPips','WorstYearAvgPips','PFpips','AvgPips','TotalPips','MaxDDPips']
        for k in metrics:
            a=rec(s,copy.deepcopy(base));b=rec(s,copy.deepcopy(base));a['PureMetrics'][k]+=(-.1 if k=='MaxDDPips' else .1)
            self.assertLess(ranking_key(a),ranking_key(b))
    def test_fixed_key_parallel_order_independence(self):
        records=[rec(Structure('USDJPY',d,w,e,60)) for d in ['LONG','SHORT'] for w in range(5) for e in [0,180,360,540,720]]
        expected=families(records)
        for seed in range(4):random.Random(seed).shuffle(records);self.assertEqual(families(records),expected)
        self.assertEqual(sum(f['Top8'] for f in expected),8)
    def test_no_cross_pair(self):
        with self.assertRaises(ValueError):families([rec(Structure('USDJPY','LONG',0,0,30)),rec(Structure('EURUSD','LONG',0,0,30))])
