"""Hand-computed synthetic overlap fixtures; no actual candidate pairwise values."""
import copy,sys,unittest
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage6 import candidate
from b6.stage8_pairwise import pair_metrics,all_pairs,matrices,correlation,interval
from b6.stage8_metrics import candidate_periods,validate_ledger,period_for

def point(cid,entry=600,symbol='GBPJPY'):
    p=candidate(symbol,entry=entry,hold=60);p['CandidateID']=cid;return p

def trade(p,week,r,duration=60):
    entry=pd.Timestamp(week)+pd.Timedelta(minutes=p['AdjustedEntryMinute']);planned=entry+pd.Timedelta(minutes=p['PlannedHoldingMinutes'])
    return dict(CandidateID=p['CandidateID'],Symbol=p['Symbol'],WeekKey=week,PlannedEntry=str(entry),ActualEntry=str(entry),PlannedExit=str(planned),ActualClose=str(entry+pd.Timedelta(minutes=duration)),ExitReason='TimeExit',R=r,Pips=r*p['SL'],Period=period_for(entry),FallbackMinutes=0,MissingPathMinutes=0)

class PairwiseTests(unittest.TestCase):
    def setUp(self):
        self.a,self.b=point('A'),point('B',630,'AUDJPY');self.weeks=['2024-02-05','2024-02-12','2024-02-19','2024-02-26']
        self.rows=[trade(self.a,w,r) for w,r in zip(self.weeks,[1.,-1.,0.])]+[trade(self.b,self.weeks[i],r) for i,r in [(0,2.),(1,-2.),(3,-3.)]]
    def metric(self):return pair_metrics(self.a,self.b,self.rows,'Validation')
    def test_cooccurrence_jaccard_and_no_zero_fill(self):
        m=self.metric();self.assertEqual((m['ATradeWeeks'],m['BTradeWeeks'],m['BothTradeWeeks'],m['EitherTradeWeeks']),(3,3,2,4));self.assertEqual(m['TradeJaccard'],.5);self.assertAlmostEqual(m['PearsonR'],1.)
    def test_loss_jaccard(self):
        m=self.metric();self.assertEqual((m['ALossWeeks'],m['BLossWeeks'],m['BothLossWeeks'],m['EitherLossWeeks']),(1,2,1,2));self.assertEqual(m['LossJaccard'],.5)
    def test_planned_overlap(self):
        m=self.metric();self.assertEqual((m['PlannedIntersectionMinutes'],m['PlannedUnionMinutes']),(30,90));self.assertEqual(m['PlannedScheduleOverlapRatio'],1/3)
    def test_actual_exposure_and_shorter_coverage(self):
        m=self.metric();self.assertEqual((m['ActualIntersectionMinutes'],m['ActualUnionMinutes'],m['BothTradeShorterMinutes']),(60,300,120));self.assertEqual(m['ActualExposureJaccard'],.2);self.assertEqual(m['ShorterExposureCoverage'],.5)
    def test_pearson_exact_positive_negative(self):
        self.assertAlmostEqual(correlation([1,2,3],[2,4,6]),1.);self.assertAlmostEqual(correlation([1,2,3],[6,4,2]),-1.)
    def test_spearman_rank_and_average_ties(self):
        for ar,br,expected in [([1,2,10],[2,3,4],1.),([1,1,2],[1,2,3],np.sqrt(3)/2)]:
            rows=[trade(p,w,r) for p,rs in [(self.a,ar),(self.b,br)] for w,r in zip(self.weeks,rs)]
            self.assertAlmostEqual(pair_metrics(self.a,self.b,rows,'Validation')['SpearmanR'],expected)
    def test_correlation_undefined_small_sample_zero_variance(self):
        for a,b in [([],[]),([1],[2]),([1,1],[2,3]),([2,3],[1,1])]:self.assertEqual(correlation(a,b),'UNDEFINED')
    def test_empty_denominators(self):
        m=pair_metrics(self.a,self.b,[],'Monitor')
        for key in ('TradeJaccard','LossJaccard','PearsonR','SpearmanR','SignAgreementRate','ActualExposureJaccard','ShorterExposureCoverage'):self.assertEqual(m[key],'UNDEFINED')
    def test_zero_r_separate_sign(self):
        rows=[trade(p,w,r) for p,rs in [(self.a,[0.,1.,-1.]),(self.b,[0.,-1.,-1.])] for w,r in zip(self.weeks,rs)]
        m=pair_metrics(self.a,self.b,rows,'Validation');self.assertEqual(m['SignAgreementRate'],2/3);self.assertEqual(m['ALossWeeks'],1);self.assertEqual(m['BothLossWeeks'],1)
    def test_pair_metric_symmetry(self):
        a=self.metric();b=pair_metrics(self.b,self.a,self.rows,'Validation')
        for k in a:
            if k not in ('CandidateA','CandidateB','ATradeWeeks','BTradeWeeks','ALossWeeks','BLossWeeks'):self.assertEqual(a[k],b[k],k)
        self.assertEqual(a['ALossWeeks'],b['BLossWeeks']);self.assertEqual(a['ATradeWeeks'],b['BTradeWeeks'])
    def test_9_choose_2_four_periods_canonical_no_self(self):
        points=[point(str(i),symbol='AUDJPY' if i==8 else 'GBPJPY') for i in range(9)];rows=all_pairs(points,[])
        self.assertEqual(len(rows),144);self.assertEqual(len({(r['CandidateA'],r['CandidateB']) for r in rows}),36)
        self.assertEqual([(r['CandidateA'],r['CandidateB']) for r in rows[:36]],[(str(i),str(j)) for i in range(9) for j in range(i+1,9)])
        self.assertEqual(sum(r['SameSymbol'] for r in rows[:36]),28);self.assertEqual(sum(not r['SameSymbol'] for r in rows[:36]),8)
        self.assertTrue(all(r['CandidateA']!=r['CandidateB'] for r in rows))
        with self.assertRaises(ValueError):pair_metrics(self.a,self.a,[],'Monitor')
    def test_matrix_derivative_diagonal_and_symmetry(self):
        points=[self.a,self.b];rows=all_pairs(points,self.rows);frames=matrices(points,rows);self.assertEqual(len(frames),20)
        f=frames['Validation_TradeJaccard'];self.assertEqual(f.loc['A','A'],'UNDEFINED');self.assertEqual(f.loc['A','B'],.5);self.assertEqual(f.loc['A','B'],f.loc['B','A'])
        with self.assertRaises(ValueError):matrices(points,rows[:-1])
    def test_weekkey_date_not_iso_week_and_duplicate_reject(self):
        r=copy.deepcopy(self.rows[0]);r['WeekKey']='2024-W06'
        with self.assertRaises(ValueError):validate_ledger([r])
        with self.assertRaises(ValueError):all_pairs([self.a,self.b],self.rows+[self.rows[0]])
    def test_zero_duration_and_disjoint_intervals(self):
        t=pd.Timestamp('2024-02-05');self.assertEqual(interval((t,t),(t,t)),(0,0,0))
        self.assertEqual(interval((t,t+pd.Timedelta(minutes=10)),(t+pd.Timedelta(minutes=10),t+pd.Timedelta(minutes=20))),(0,20,10))
    def test_period_metrics_36_rows_raw_and_initial_dd(self):
        points=[point(str(i)) for i in range(9)];records=[trade(points[0],w,r) for w,r in zip(self.weeks,[-2.,0.,-3.])];rows=candidate_periods(points,records)
        self.assertEqual(len(rows),36);m=next(r for r in rows if r['CandidateID']=='0' and r['Period']=='Validation');self.assertEqual((m['Trades'],m['Wins'],m['Losses'],m['ZeroR'],m['MaxDDR']),(3,0,2,1,5.))
    def test_period_specific_correlation_not_full_only(self):
        rows=[trade(p,w,r) for p,values in [(self.a,[1.,2.,1.,2.]),(self.b,[1.,2.,2.,1.])] for w,r in zip(['2020-02-03','2020-02-10','2024-02-05','2024-02-12'],values)]
        m={r['Period']:r for r in all_pairs([self.a,self.b],rows)};self.assertAlmostEqual(m['Discovery']['PearsonR'],1);self.assertAlmostEqual(m['Validation']['PearsonR'],-1);self.assertEqual(m['FullAvailable']['BothTradeWeeks'],4)
