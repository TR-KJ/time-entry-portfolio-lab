import unittest,sys
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage10_money import row
from b6.stage11_config import CONFIGS,AJ,GJ,MODES
from b6.stage11_input import portfolio
from b6.stage11_money import simulate
from b6.stage11_risk_load import exposure
from b6.stage11_search import run_job,incremental,job_specs

def r(i=1,risk='.5',**kwargs):return dict(row(i,**kwargs),AppliedRiskPercent=D(risk))
class MoneyTests(unittest.TestCase):
    def test_same_week_variable_amount_no_intra_compounding(self):
        logs,w,s=simulate([r(r='1'),r(2,risk='1.3',r='-1')],'POSTDISCOVERY_RESET_2024')
        self.assertEqual([x['WeeklyBase'] for x in logs],[D(500000)]*2)
        self.assertEqual([x['RiskAmount'] for x in logs],[D(2500),D(6500)]);self.assertEqual(s['PostDiscovery']['FinalCapital'],D(496000))
        self.assertEqual(w[0]['GrossRiskAllocationPct'],D('1.8'))
    def test_next_week_compounds(self):
        logs,_,_=simulate([r(r='1'),r(2,risk='1.3',entry='2024-01-15 08:00:00',close='2024-01-15 09:00:00')],'POSTDISCOVERY_RESET_2024')
        self.assertEqual(logs[1]['WeeklyBase'],D(502500));self.assertEqual(logs[1]['RiskAmount'],D('6532.5'))
    def test_two_modes_capital_only_reset(self):
        rows=[r(entry='2023-12-20 08:00:00',close='2023-12-20 09:00:00',r='1'),r(2)]
        logs,_,_=simulate(rows,'CONTINUOUS_2020');reset,_,_=simulate(rows,'POSTDISCOVERY_RESET_2024')
        self.assertEqual(logs[-1]['WeeklyBase'],D(502500));self.assertEqual(reset[0]['WeeklyBase'],D(500000));self.assertEqual(logs[-1]['AppliedRiskPercent'],reset[0]['AppliedRiskPercent'])
    def test_no2026_reset(self):
        rows=[r(entry='2025-12-20 08:00:00',close='2025-12-20 09:00:00',r='1'),r(2,entry='2026-01-05 08:00:00',close='2026-01-05 09:00:00')]
        for mode in MODES:self.assertEqual(simulate(rows,mode)[0][-1]['WeeklyBase'],D(502500))
    def test_rawr_b6_and_canonical_baseline(self):
        rows=[r(source='B6',cid=GJ,r='0.123456789123'),r(2,r='0.123456789123')]
        logs,_,_=simulate(rows,'POSTDISCOVERY_RESET_2024');self.assertEqual(logs[0]['YenPnL'],logs[1]['YenPnL'])
    def test_invalid_risk_rejected(self):
        with self.assertRaises(ValueError):simulate([r(risk='2')],'CONTINUOUS_2020')
    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):simulate([r()],'MONITOR_RESET')
    def test_crossing_rejected(self):
        with self.assertRaises(ValueError):simulate([r(close='2024-01-15 06:00:00')],'CONTINUOUS_2020')
    def test_initial_peak_loss_dd(self):
        _,_,s=simulate([r()],'CONTINUOUS_2020');self.assertEqual(s['FullAvailable']['MaxDDJPY'],D(2500));self.assertEqual(s['FullAvailable']['MaxDDPct'],D('.5'))
    def test_risk_metrics_mean_median_extremes(self):
        _,_,s=simulate([r(),r(2,risk='1.3')],'CONTINUOUS_2020');s=s['FullAvailable']
        self.assertEqual([s[k] for k in ('MeanAppliedRiskPct','MedianAppliedRiskPct','MinAppliedRiskPct','MaxAppliedRiskPct')],[D('.9'),D('.9'),D('.5'),D('1.3')])
    def test_concurrent_sum_not_count_constant(self):
        con,_=exposure([r(),r(2,risk='1.3')],'2024-01-01','2024-02-01')
        self.assertEqual(con['MaxConcurrentPositions'],2);self.assertEqual(con['MaxConcurrentRiskPct'],D('1.8'))
    def test_half_open_tie_no_double_exposure(self):
        con,_=exposure([r(),r(2,risk='1.3',entry='2024-01-08 09:00:00',close='2024-01-08 10:00:00')],'2024-01-01','2024-02-01')
        self.assertEqual(con['MaxConcurrentPositions'],1);self.assertEqual(con['MaxConcurrentRiskPct'],D('1.3'))
    def test_zero_duration_no_exposure(self):
        con,_=exposure([r(close='2024-01-08 08:00:00')],'2024-01-01','2024-02-01');self.assertEqual(con['MaxConcurrentRiskPct'],0)
    def test_overlap_hand_fixture(self):
        rows=[r(source='B6',cid=GJ),r(2,source='B6',cid=AJ,entry='2024-01-08 08:30:00',close='2024-01-08 09:30:00'),r(3)]
        _,ov=exposure(rows,'2024-01-01','2024-02-01')
        self.assertEqual((ov[0]['BothOpenMinutes'],ov[0]['EitherOpenMinutes'],ov[0]['WeeksBothTrade'],ov[0]['WeeksBothSimultaneouslyOpen']),(D(30),D(90),1,1))
        self.assertEqual(ov[2]['AnyExistingOverlapMinutes'],60)
    def test_exact_three_portfolios_no_aj_only(self):
        rows=[r(),r(2,source='B6',cid=GJ),r(3,source='B6',cid=AJ)]
        self.assertEqual([len(portfolio(rows,n)) for n in CONFIGS],[1,2,3]);self.assertNotIn((AJ,),CONFIGS.values())
        with self.assertRaises(ValueError):portfolio(rows,'AJ_ONLY')
    def test_six_jobs24_rows_and_hand_deltas(self):
        rows=[r(r='0'),r(2,source='B6',cid=GJ,r='1'),r(3,source='B6',cid=AJ,r='2')]
        results=[]
        for _,mode,name in job_specs():results+=run_job(rows,mode,name)['PeriodResults']
        inc=incremental(results);self.assertEqual(len(results),24);self.assertEqual(len(inc),24)
        d={x['Comparison']:x['DeltaFinalCapital'] for x in inc if x['MoneyMode']=='CONTINUOUS_2020' and x['Period']=='FullAvailable'}
        self.assertEqual(d,{'GJ_INCREMENTAL':D(2500),'AJ_CONDITIONAL_INCREMENTAL':D(5000),'TOTAL_B6_INCREMENTAL':D(7500)})
    def test_weekly_counts_and_sum(self):
        _,w,_=simulate([r(),r(2,risk='1.3',source='B6',cid=GJ),r(3,risk='.7',source='B6',cid=AJ)],'CONTINUOUS_2020')
        self.assertEqual((w[0]['BaselineTrades'],w[0]['GJTrades'],w[0]['AJTrades']),(1,1,1));self.assertEqual(w[0]['GrossRiskAllocationPct'],D('2.5'));self.assertEqual(w[0]['MaxConcurrentRiskPct'],D('2.5'))
