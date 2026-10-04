import unittest,sys,copy,random,math
from pathlib import Path
from datetime import datetime,timedelta
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage11_r2 import feature,daily_from_rows,feature_daily,true_ranges,quintile,risk,reference,assert_parity,Assigner
from b6.stage11_assignment import assign_rows,preflight,distribution
from test_b6_stage10_money import row

def fixture(n=272):
    return [dict(JST=datetime(2023,1,1,12)+timedelta(days=i),Open=100.,High=101.,Low=99.,Close=100.) for i in range(n)]
ENTRY=datetime(2024,1,8,8)

def oracle_rows(rows):return [dict(r,JST=r['JST'].strftime('%Y.%m.%d %H:%M:%S')) for r in rows]

class R2Tests(unittest.TestCase):
    def test_271_fallback(self):
        f=feature(fixture(271),ENTRY);self.assertEqual((f['FeatureStatus'],f['FallbackReason'],f['AppliedRiskPercent']),('FALLBACK','INSUFFICIENT_VOL_HISTORY',D('.90')))
    def test_272_valid_hand_ties(self):
        f=feature(fixture(),ENTRY)
        self.assertEqual((f['ATR20'],f['RankNumerator'],f['Percentile'],f['Quintile'],f['AppliedRiskPercent']),(2.,252,50.,'Q3',D('.90')))
        self.assertEqual(f['ReferenceCount'],252)
    def test_zero_history_normal_fallback(self):self.assertEqual(feature([],ENTRY)['FeatureStatus'],'FALLBACK')
    def test_actual_day_ohlc_saturday_missing_days(self):
        rows=[dict(JST=datetime(2024,1,4,8),Open=100,High=103,Low=99,Close=102),dict(JST=datetime(2024,1,4,22),Open=102,High=104,Low=98,Close=101),dict(JST=datetime(2024,1,6,8),Open=105,High=106,Low=104,Close=105)]
        d=daily_from_rows(rows,ENTRY)
        self.assertEqual(len(d),2);self.assertEqual(d[1]['day'].weekday(),5)
        self.assertEqual([d[0][k] for k in ('open','high','low','close','count')],[100,104,98,101,2])
        self.assertEqual(true_ranges(d),[6,5])
    def test_sma_not_wilder_hand_computed(self):
        rows=fixture();rows[-1].update(High=121.)
        f=feature(rows,ENTRY);self.assertEqual(f['ATR20'],3.);self.assertEqual(f['RankNumerator'],504);self.assertEqual(f['Quintile'],'Q5')
    def test_evaluated_atr_excluded(self):
        rows=fixture();rows[-1].update(High=100.,Low=100.)
        f=feature(rows,ENTRY);self.assertEqual(f['RankNumerator'],0);self.assertEqual(f['Quintile'],'Q1')
        self.assertEqual(f['ReferenceEnd'],rows[-2]['JST'].replace(hour=0))
    def test_reference_start_exact252(self):
        f=feature(fixture(),ENTRY);self.assertEqual(f['ReferenceStart'],datetime(2023,1,20))
    def test_integer_cut_all505(self):
        for n in range(505):self.assertEqual(quintile(n),'Q'+str(1+sum(100*n/504>=v for v in (20,40,60,80))))
    def test_cut_neighbours(self):
        for n,q in [(100,'Q1'),(101,'Q2'),(201,'Q2'),(202,'Q3'),(302,'Q3'),(303,'Q4'),(403,'Q4'),(404,'Q5')]:self.assertEqual(quintile(n),q)
    def test_invalid_rank(self):
        for n in (-1,505,.5,True):
            with self.assertRaises(ValueError):quintile(n)
    def test_risk_table_exact_unknown_reject(self):
        for q,v in zip(('Q1','Q2','Q3','Q4','Q5','FALLBACK'),('.50','.70','.90','1.10','1.30','.90')):self.assertEqual(risk(q),D(v))
        with self.assertRaises(ValueError):risk('Q6')
    def test_no_epsilon(self):
        rows=fixture();rows[-1]['High']=101.+1e-10
        self.assertEqual(feature(rows,ENTRY)['RankNumerator'],504)
    def test_current_future_mutation_ignored(self):
        rows=fixture();f=feature(rows,ENTRY)
        rows += [dict(JST=datetime(2024,1,8,0),Open=float('nan'),High=-1,Low=0,Close=0),dict(JST=datetime(2025,1,1),Open=999,High=0,Low=0,Close=0)]
        self.assertEqual(feature(rows,ENTRY),f)
    def test_current_day_excluded_even_before_entry(self):
        rows=fixture(271);rows.append(dict(JST=datetime(2024,1,8,0),Open=100,High=101,Low=99,Close=100))
        self.assertEqual(feature(rows,ENTRY)['FeatureStatus'],'FALLBACK')
        self.assertEqual(feature(rows,ENTRY+timedelta(days=1))['FeatureStatus'],'VALID')
    def test_duplicate_unsorted_reject(self):
        for rows in (fixture()+[fixture()[-1]],list(reversed(fixture()))):
            with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_UNSORTED'):feature(rows,ENTRY)
    def test_invalid_nonfinite_ohlc_reject_not_fallback(self):
        for v in (float('nan'),float('inf'),-1,0,200):
            rows=fixture(10);rows[0]['Close']=v
            with self.assertRaisesRegex(ValueError,'INVALID_OHLC'):feature(rows,ENTRY)
    def test_unavailable_symbol_reject(self):
        with self.assertRaisesRegex(ValueError,'UNAVAILABLE'):Assigner({},'fixture').assign('GBPJPY',ENTRY)
    def test_cache_uncached_parity(self):
        days={'GBPJPY':daily_from_rows(fixture(),ENTRY)}
        a=Assigner(days,'fixture');b=Assigner(days,'fixture',use_cache=False)
        for entry in (ENTRY,ENTRY+timedelta(hours=1),ENTRY+timedelta(days=1)):self.assertEqual(a.assign('GBPJPY',entry),b.assign('GBPJPY',entry))
        self.assertEqual(len(a.cache),2);self.assertTrue(all('fixture' in key for key in a.cache))
    def test_outcome_independent_and_no_filter(self):
        a=Assigner({'GBPJPY':daily_from_rows(fixture(10),ENTRY)},'fixture');rows=[row(),row(2,r='100')]
        assigned=assign_rows(rows,a)
        self.assertEqual(len(assigned),2);self.assertEqual(assigned[0]['AppliedRiskPercent'],assigned[1]['AppliedRiskPercent'])
        self.assertEqual(preflight(rows,assigned,False)['Status'],'PASS')
    def test_independent_oracle_random(self):
        rng=random.Random(11);oracle=reference();rows=fixture(330)
        for r in rows:
            width=rng.randrange(1,30);r.update(High=100+width,Low=100-width)
        for n in (10,271,272,280,330):assert_parity(feature(rows[:n],ENTRY),oracle.feature(oracle_rows(rows[:n]),ENTRY))
    def test_reduced_daily_reference_parity(self):
        rows=fixture()
        rows.insert(2,dict(rows[1],JST=rows[1]['JST']+timedelta(hours=1),High=110,Close=105))
        a=Assigner({'GBPJPY':daily_from_rows(rows,ENTRY)},'fixture')
        self.assertEqual(a.assign('GBPJPY',ENTRY),feature(rows,ENTRY))
    def test_preflight_mutation_rejected(self):
        rows=[row()];a=assign_rows(rows,Assigner({'GBPJPY':daily_from_rows(fixture(),ENTRY)},'fixture'))
        for key,value in [('R',D(2)),('AppliedRiskPercent',D('.50')),('FeatureDailyDate',ENTRY),('ReferenceCount',251),('Quintile','Q5')]:
            bad=copy.deepcopy(a);bad[0][key]=value
            with self.assertRaises(ValueError):preflight(rows,bad,False)
    def test_distribution_zero_bins_and_no_filter(self):
        rows=[row()];a=assign_rows(rows,Assigner({'GBPJPY':daily_from_rows(fixture(),ENTRY)},'fixture'))
        d=distribution(a);self.assertEqual(len(d),72)
        full=[r for r in d if r['Group']=='CURRENT27' and r['Period']=='FullAvailable'];self.assertEqual(sum(r['Trades'] for r in full),1)
    def test_pre2024_warmup_not_reset(self):
        f=feature(fixture(),ENTRY);self.assertEqual(f['FeatureStatus'],'VALID');self.assertLess(f['FeatureDailyDate'],datetime(2024,1,1))
