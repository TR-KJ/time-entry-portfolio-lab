import unittest, sys, re, math, random, copy
from pathlib import Path
from datetime import datetime,timedelta
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/research'))
import volatility_phase5_audit as a

def fixture(n=272):
    start=datetime(2025,1,1,12)
    return [dict(JST=(start+timedelta(days=i)).strftime(a.FORMAT),Open='129',High='130',Low='128',Close='129') for i in range(n)]

class ReferenceTests(unittest.TestCase):
    def test_warmup_271_272(self):
        self.assertEqual(a.feature(fixture(271),datetime(2026,1,1))['status'],'FALLBACK')
        self.assertEqual(a.feature(fixture(),datetime(2026,1,1))['q'],3)
    def test_midrank_ties(self):
        r=a.feature(fixture(),datetime(2026,1,1));self.assertEqual((r['rank'],r['percent']),(252,50))
    def test_extremes(self):
        for high,expected in [('150',5),('129',1)]:
            rows=fixture();rows[-1]['High']=high
            self.assertEqual(a.feature(rows,datetime(2026,1,1))['q'],expected)
    def test_daily_actual_saturday(self):
        rows=fixture(4);r=a.daily_from_rows(rows,datetime(2026,1,1))
        self.assertEqual(len(r),4);self.assertEqual(r[-1]['day'].weekday(),5)
    def test_daily_ohlc_and_gaps(self):
        rows=[dict(JST='2026.01.01 01:00:00',Open='100',High='103',Low='99',Close='102'),dict(JST='2026.01.01 23:59:00',Open='102',High='104',Low='98',Close='101'),dict(JST='2026.01.03 12:00:00',Open='105',High='106',Low='104',Close='105')]
        r=a.daily_from_rows(rows,datetime(2026,1,4));self.assertEqual(len(r),2)
        self.assertEqual([r[0][k] for k in ('open','high','low','close','count')],[100,104,98,101,2])
    def test_current_future_mutation(self):
        rows=fixture();when=datetime(2025,10,1)
        expected=a.feature(rows,when)
        rows.append(dict(JST='2025.10.01 00:00:00',Open='nan',High='-1',Low='0',Close='nan'))
        self.assertEqual(a.feature(rows,when),expected)
    def test_midnight_availability(self):
        rows=fixture(); rows[-1]['JST']='2025.09.29 23:59:00'
        self.assertEqual(a.feature(rows,datetime(2025,9,29,23,59,59))['status'],'FALLBACK')
        self.assertEqual(a.feature(rows,datetime(2025,9,30))['status'],'VALID')
    def test_duplicate_and_invalid(self):
        rows=fixture();rows.append(rows[-1].copy())
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):a.feature(rows,datetime(2026,1,1))
        rows=fixture();rows[10]['Close']='nan'
        with self.assertRaisesRegex(ValueError,'INVALID_OHLC'):a.feature(rows,datetime(2026,1,1))
    def test_dst(self):
        for raw,expected in [('2026.03.29 02:59:00','2026.03.29 09:59:00'),('2026.03.29 04:00:00','2026.03.29 10:00:00'),('2026.10.25 02:59:00','2026.10.25 08:59:00'),('2026.10.25 04:00:00','2026.10.25 11:00:00')]:
            self.assertEqual(a.jst_from_server(a.dt(raw)),a.dt(expected))
        for raw in ['2026.03.29 03:30:00','2026.10.25 03:30:00']:
            with self.assertRaisesRegex(ValueError,'AMBIGUOUS'):a.jst_from_server(a.dt(raw))
    def test_all_midrank_bins(self):
        # Independent percent boundaries vs the prescribed integer formulation.
        for n in range(505):
            self.assertEqual(1+sum(100*n/504>=x for x in (20,40,60,80)),1+sum(5*n>=x for x in (504,1008,1512,2016)))
    def test_risk_table(self):self.assertEqual(a.RISK,{0:.9,1:.5,2:.7,3:.9,4:1.1,5:1.3})
    def test_lot_floor_cap_min(self):
        self.assertEqual(a.lot(1000000,.9,50,1000)['lot'],.18)
        self.assertTrue(a.lot(100000000,.9,50,1000)['cap'])
        self.assertEqual(a.lot(100000000,.9,50,1000)['lot'],1)
        self.assertTrue(a.lot(1,.9,50,1000)['min_stop'])
        self.assertEqual(a.lot(100,.5,50,1)['lot'],.01)
    def test_invalid_lots(self):
        for v in [0,-1,math.nan,math.inf]:
            self.assertEqual(a.lot(v,.9,50,1000)['lot'],0)
            self.assertEqual(a.lot(100000,.9,v,1000)['lot'],0)
        self.assertEqual(a.lot(100000,.9,50,1000,step=.001)['reason'],'UNAPPROVED_VOLUME_SPEC')
    def test_existing_lot_formula_regression(self):
        rng=random.Random(20260916)
        for _ in range(1000):
            base=rng.uniform(1000,1e7);sl=rng.choice([15,30,50,70,100]);pv=rng.uniform(1,10000)
            raw=base*.9/100/(sl*pv)
            expected=0 if raw<.01 else round(math.floor(min(10,max(.01,min(raw,1)))/.01)*.01,2)
            self.assertEqual(a.lot(base,.9,sl,pv)['lot'],expected)
    def test_parser_and_missing_evidence(self):
        line='[P5] SchemaVersion=1|RunId=x|CandidateId=x_1|AttemptId=0|EventType=CANDIDATE|StrategyName=1_EJ_Log1|Magic=1|Symbol=EURJPY'
        ev=a.parse_experts(line);self.assertEqual(len(ev),1)
        self.assertEqual(a.audit(ev,Path('/nonexistent'))[0]['AuditStatus'],'PENDING')
        with self.assertRaises(ValueError):a.parse_experts(line+'|Magic=2')
    def test_verdict_priority(self):
        r={'checks':{k:{'status':'PASS','evidence':'hash/path'} for k in 'ABCDEFG'},'deployment_validation':'PASS',
           'start':'2026-09-16T00:00:00+09:00','cutoff':'2026-09-30T00:00:00+09:00',
           'qualifying_candidates':[{'id':str(i),'quintile':1+i%2,'symbol':['USDJPY','EURJPY'][i%2],'entry_jst':'2026-09-17T12:00:00+09:00','numeric_audit':'NUMERIC_MATCH'} for i in range(10)],
           'actual_entry_exit_reconciled':True,'week_rollover_observed':True,'within_week_reuse_observed':True,'all_candidates_audited':True}
        self.assertEqual(a.assess(r),'DEMO_FORWARD_PASS')
        for key in ['deployment_validation','start','qualifying_candidates','week_rollover_observed']:
            bad=copy.deepcopy(r);bad.pop(key);self.assertEqual(a.assess(bad),'INSUFFICIENT_OBSERVATIONS')
        r['checks']['F']['status']='FAIL';r['qualifying_candidates']=[]
        self.assertEqual(a.assess(r),'DEMO_FORWARD_FAIL')
    def test_no_profit_input_to_verdict(self):
        self.assertEqual(a.assess({'profit':10**12,'PF':100}),'INSUFFICIENT_OBSERVATIONS')

def function(s,name):
    m=re.search(r'\b(?:bool|void|int|double|string|datetime|long|ulong) '+name+r'\([^;]*?\)\s*\{',s)
    if not m:raise AssertionError(name)
    p=m.end();depth=1
    while depth:
        depth+=(s[p]=='{')-(s[p]=='}');p+=1
    return s[m.start():p]

class SourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=(ROOT/'src/EA/time_entry_step9_2_4_trade_result_reconcile_28strategies.mq5').read_text()
        cls.new=(ROOT/'src/EA/time_entry_step9_2_4_trade_result_reconcile_27strategies_vol_r2_demo.mq5').read_text()
        cls.dep=(ROOT/'src/EA/phase5_demo/step921_demo_dependency.mqh').read_text()
    def test_reconciliation_functions_unchanged(self):
        # Static regression only, NOT an MQL runtime assertion.
        names=['IsNormalTradeSuccessResult','ReconcileExecutedEntry','ReconcileExecutedExit','ProcessPendingEntryReconciliations','ProcessPendingExitReconciliations','ConfirmPendingEntryFromDeal','ConfirmPendingExitFromDeal','StartPendingEntryReconciliation','StartPendingExitReconciliation','HasPendingEntryReconciliation','IsPlausibleReconciledVolume','GetUJ12TradeMode','GetStrategySLPips']
        for name in names:self.assertEqual(function(self.old,name),function(self.new,name),name)
    def test_full_set_keys_and_27_enabled(self):
        keys=set(re.findall(r'^input\s+\w+\s+(\w+)\s*=',self.new+'\n'+self.dep,re.M))
        lines=(ROOT/'configs/phase5/step9_2_4_dell_demo_vol_r2_phase5.set').read_text().splitlines()
        config=dict(s.split('=',1) for s in lines if s and not s.startswith(';'))
        self.assertEqual(keys,set(config))
        enabled={k:v for k,v in config.items() if k.startswith('InpEnable_')}
        self.assertEqual(len(enabled),28);self.assertEqual(list(enabled.values()).count('true'),27)
        self.assertEqual(enabled['InpEnable_22_GA_C2'],'false')
        self.assertEqual(config['InpPhase5Approved'],'false');self.assertEqual(config['InpPhase5DemoLogin'],'0')
        self.assertEqual(config['InpAtrTimeframe'],'16385')
    def test_guards_at_active_submit(self):
        for name in ['SendBuyOrder','SendSellOrder','ClosePositionsByConfig']:
            s=function(self.new,name);self.assertIn('if(!P5Guard())',s)
        for name in ['OnTick','OnTimer','OnTradeTransaction']:self.assertIn('P5Guard()',function(self.new,name))
    def test_live_source_includes_not_used(self):
        self.assertNotIn('#include "time_entry_step9_2_1',self.new)
        self.assertNotIn('"TE_STEP7_WEEKLY_BASE_',self.dep)
        self.assertIn('P5GV("W"',self.dep)
    def test_strategy_identity_unchanged(self):
        original=(ROOT/'src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5').read_text()
        self.assertEqual(function(original,'SetupStrategies'),function(self.dep,'SetupStrategies'))

if __name__=='__main__':unittest.main(verbosity=2)
