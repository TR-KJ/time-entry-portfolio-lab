import unittest
from datetime import datetime,timedelta
from decimal import Decimal as D,localcontext
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage10_config import AJ,GJ,RISKS,CONFIGS,MODES,PERIODS
from b6.stage10_input import legacy,portfolio,validate_rows
from b6.stage10_money import simulate,deltas,settlement
from b6.stage10_risk_load import exposure


def row(i=1,entry='2024-01-08 08:00:00',close='2024-01-08 09:00:00',r='-1',source='BASELINE',cid=None,symbol='GBPJPY'):
    return dict(RowId=i,StrategyNo=i if source=='BASELINE' else None,Strategy=cid or '1_X',Pair='GJ',Symbol=symbol,
        Source=source,PortfolioComponentKey=cid or 'BASELINE:1_X',EntryTime=datetime.fromisoformat(entry),
        CloseTime=datetime.fromisoformat(close),SL=D(30),Pips=D(r)*30,R=D(r))


class MoneyTests(unittest.TestCase):
    def run_money(self,rows,risk='1.0',mode='POSTDISCOVERY_RESET_2024'):return simulate(rows,D(risk),mode)
    def test_exact_risks(self):self.assertEqual(RISKS,tuple(map(D,['.25','1','1.5','2'])))
    def test_unknown_risk_rejected(self):
        for risk in ('.5','0','3'):
            with self.subTest(risk=risk),self.assertRaises(ValueError):self.run_money([row()],risk)
    def test_initial_first_loss_metrics_hand_calculated(self):
        log,week,stats=self.run_money([row()]);s=stats['PostDiscovery']
        self.assertEqual(log[0]['RiskAmount'],D(5000));self.assertEqual(s['FinalCapital'],D(495000))
        self.assertEqual(s['NetProfitJPY'],D(-5000));self.assertEqual(s['ReturnPct'],D(-1))
        self.assertEqual(s['MaxDDJPY'],D(5000));self.assertEqual(s['MaxDDPct'],D(1))
        self.assertEqual(s['WorstDayPct'],D(-1));self.assertEqual(s['WorstWeekPct'],D(-1))
        self.assertEqual(s['MoneyPF'],D(0));self.assertEqual(s['MoneyRoMD'],D(-1))
    def test_weekly_amount_fixed_no_intraweek_compounding(self):
        log,_,_=self.run_money([row(),row(2,entry='2024-01-09 08:00:00',close='2024-01-09 09:00:00',r='2')])
        self.assertEqual([r['RiskAmount'] for r in log],[D(5000)]*2)
        self.assertEqual(log[-1]['Capital'],D(505000))
    def test_prior_week_compounds_next_week(self):
        log,_,_=self.run_money([row(),row(2,entry='2024-01-15 08:00:00',close='2024-01-15 09:00:00')])
        self.assertEqual(log[1]['WeeklyBase'],D(495000));self.assertEqual(log[1]['RiskAmount'],D(4950))
    def test_monday06_and_sunday(self):
        for t,w in [('2024-01-08 05:59:00','2024-01-01 06:00:00'),('2024-01-08 06:00:00','2024-01-08 06:00:00'),('2024-01-07 23:59:00','2024-01-01 06:00:00')]:
            self.assertEqual(legacy.week_start(datetime.fromisoformat(t)),datetime.fromisoformat(w))
    def test_week_crossing_rejected(self):
        with self.assertRaises(ValueError):self.run_money([row(close='2024-01-15 06:00:00')])
    def test_reporting_crossing_rejected(self):
        with self.assertRaises(ValueError):self.run_money([row(entry='2025-12-31 23:00:00',close='2026-01-01 01:00:00')])
    def test_insolvency_rejected(self):
        with self.assertRaises(ValueError):self.run_money([row(r='-100')])
    def test_duplicate_source_row_rejected(self):
        with self.assertRaises(ValueError):self.run_money([row(),row()])
    def test_fixed_risk_all_components(self):
        rows=[row(),row(2,source='B6',cid=AJ),row(3,source='B6',cid=GJ)]
        for risk in RISKS:
            for name in CONFIGS:
                log,_,_=simulate(portfolio(rows,name),risk,'POSTDISCOVERY_RESET_2024')
                self.assertTrue(all(r['RiskAmount']==D(500000)*risk/100 for r in log))
    def test_config_compositions_exact(self):
        rows=[row(),row(2,source='B6',cid=AJ),row(3,source='B6',cid=GJ)]
        for name,added in CONFIGS.items():
            out=portfolio(rows,name);self.assertEqual([r['PortfolioComponentKey'] for r in out],['BASELINE:1_X',*added])
        with self.assertRaises(ValueError):portfolio(rows,'EXTRA')
    def test_continuous_no_reset_and_reset2024(self):
        rows=[row(entry='2020-01-06 08:00:00',close='2020-01-06 09:00:00',r='1'),row(2),row(3,entry='2026-01-05 08:00:00',close='2026-01-05 09:00:00')]
        a,_,s=self.run_money(rows,mode='CONTINUOUS_2020');b,_,t=self.run_money(rows)
        self.assertEqual(a[1]['WeeklyBase'],D(505000));self.assertEqual(a[2]['WeeklyBase'],D(499950))
        self.assertEqual(b[0]['WeeklyBase'],D(500000));self.assertEqual(s['Validation']['StartCapital'],D(505000))
        self.assertNotIn('Discovery',t);self.assertEqual(set(t),{'Validation','Monitor','PostDiscovery'})
    def test_unknown_mode_rejected(self):
        with self.assertRaises(ValueError):self.run_money([row()],mode='MONITOR_RESET')
    def test_no_loss_no_dd_undefined(self):
        _,_,s=self.run_money([row(r='1')]);self.assertIsNone(s['PostDiscovery']['MoneyPF']);self.assertIsNone(s['PostDiscovery']['MoneyRoMD'])
    def test_hand_calculated_win_loss_and_day_base(self):
        _,_,s=self.run_money([row(r='2'),row(2,entry='2024-01-09 08:00:00',close='2024-01-09 09:00:00')]);s=s['PostDiscovery']
        self.assertEqual(s['FinalCapital'],D(505000));self.assertEqual(s['MoneyPF'],D(2));self.assertEqual(s['MoneyRoMD'],D(1))
        with localcontext() as ctx:
            ctx.prec=40;self.assertEqual(s['WorstDayPct'],D(-5000)/D(510000)*100)
    def test_settlement_component_then_rowid(self):
        rows=[row(2,source='B6',cid=GJ),row(1,source='B6',cid=AJ),row(3)]
        log,_,_=self.run_money(rows);self.assertEqual([settlement(r) for r in log],sorted(settlement(r) for r in rows))
    def test_b6_raw_r_used_directly(self):
        r=row(source='B6',cid=AJ);r['Pips']=D('-30.0000000000001')
        log,_,_=self.run_money([r]);self.assertEqual(log[0]['YenPnL'],D(-5000))
    def test_existing_legacy_money_regression(self):
        rows=[row(),row(2,r='2'),row(3,entry='2024-01-15 08:00:00',close='2024-01-15 09:00:00')]
        with localcontext() as ctx:
            ctx.prec=40
            old,_=legacy.simulate(rows,D(1),'M0_BASELINE');new,_,stats=self.run_money(rows)
            for a,b in zip(old,new):
                for key in ('WeeklyBase','RiskAmount','YenPnL','Capital','DrawdownJPY','DrawdownPct'):self.assertEqual(a[key],b[key])
            self.assertEqual(stats['PostDiscovery'],legacy.metrics(old,'2024-01-01','2026-09-10'))
    def test_delta_signs(self):
        base={k:D(1) for k in ('FinalCapital','NetProfitJPY','ReturnPct','MaxDDJPY','MaxDDPct','WorstDayPct','WorstWeekPct','MoneyRoMD','MoneyPF','Trades','MaxConcurrentPositions','MaxConcurrentRiskPct')}
        after=dict(base,MaxDDJPY=D('.5'),WorstDayPct=D(-1));d=deltas(after,base)
        self.assertEqual(d['DeltaMaxDDJPY'],D('-.5'));self.assertEqual(d['DeltaWorstDayPct'],D(-2))
    def test_undefined_delta(self):
        _,_,s=self.run_money([row(r='1')]);r={**s['PostDiscovery'],'MaxConcurrentPositions':1,'MaxConcurrentRiskPct':D(1)}
        self.assertIsNone(deltas(r,r)['DeltaMoneyPF'])
    def test_risk_load_hand_calculated(self):
        rows=[row(close='2024-01-08 10:00:00'),row(2,entry='2024-01-08 09:00:00',close='2024-01-08 11:00:00',source='B6',cid=AJ,symbol='AUDJPY'),row(3,entry='2024-01-08 09:30:00',close='2024-01-08 10:30:00',source='B6',cid=GJ)]
        con,ov=exposure(rows,D('.25'),'2024-01-08','2024-01-09')
        self.assertEqual(con['MaxConcurrentPositions'],3);self.assertEqual(con['MaxConcurrentB6Positions'],2);self.assertEqual(con['MaxConcurrentRiskPct'],D('.75'))
        self.assertEqual(con['AvgConcurrentPositions'],D(300)/D(1440))
        self.assertEqual(ov[0]['BothOpenMinutes'],60);self.assertEqual(ov[0]['EitherOpenMinutes'],120);self.assertEqual(ov[0]['B6ExposureJaccard'],D('.5'))
        self.assertEqual(ov[0]['WeeksBothTrade'],1);self.assertEqual(ov[0]['WeeksBothSimultaneouslyOpen'],1)
        self.assertEqual(ov[1]['AnyExistingOverlapMinutes'],60);self.assertEqual(ov[1]['SameSymbolExistingOverlapMinutes'],0)
        self.assertEqual(ov[2]['SameSymbolExistingOverlapMinutes'],30)
        _,w,_=self.run_money(rows,'.25');self.assertEqual(w[0]['GrossRiskAllocationPct'],D('.75'))
    def test_close_open_ties_do_not_overlap(self):
        con,_=exposure([row(),row(2,entry='2024-01-08 09:00:00',close='2024-01-08 10:00:00')],D(1),'2024-01-08','2024-01-09')
        self.assertEqual(con['MaxConcurrentPositions'],1)
    def test_zero_duration_no_exposure(self):
        con,ov=exposure([row(close='2024-01-08 08:00:00',source='B6',cid=AJ)],D(1),'2024-01-08','2024-01-09')
        self.assertEqual(con['MaxConcurrentPositions'],0);self.assertIsNone(ov[0]['B6ExposureJaccard'])

    def test_two_week_nonadditive_interaction_independent_product(self):
        from b6.stage10_search import run_job
        rows=[]
        for week,day in enumerate(('2024-01-08','2024-01-15')):
            rows += [row(week*3+i+1,entry=day+' 08:00:00',close=day+' 09:00:00',r='1',source=source,cid=cid) for i,(source,cid) in enumerate([('BASELINE',None),('B6',AJ),('B6',GJ)])]
        values=[]
        for n,name in enumerate(CONFIGS):
            result=run_job(rows,'POSTDISCOVERY_RESET_2024',D(1),name)['PeriodResults'][-1]
            number={'P0_CURRENT':1,'P1_CURRENT_PLUS_AJ':2,'P2_CURRENT_PLUS_GJ':2,'P3_CURRENT_PLUS_B6_BOTH':3}[name]
            expected=D(500000)*(1+D(number)/100)**2
            self.assertEqual(result['FinalCapital'],expected);values.append(expected)
        self.assertEqual(values[3]-values[1]-values[2]+values[0],D(100))
