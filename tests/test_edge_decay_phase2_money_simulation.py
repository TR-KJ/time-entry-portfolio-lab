import importlib.util
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/research/edge_decay_phase2_money_simulation.py'
spec=importlib.util.spec_from_file_location('money',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def row(no=1, entry='2022-01-03 08:00:00', close='2022-01-03 09:00:00', sl='50', pips='-50', strategy='1_X'):
    return dict(RowId=no,StrategyNo=no,Strategy=strategy,Pair='UJ',EntryTime=datetime.fromisoformat(entry),CloseTime=datetime.fromisoformat(close),SL=D(sl),Pips=D(pips),R=D(pips)/D(sl))

class MoneyTests(unittest.TestCase):
    def test_hash(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b'wrong');f.flush()
            with self.assertRaisesRegex(ValueError,'SHA'):m.load_baseline(f.name)
    def test_week(self):
        self.assertEqual(str(m.week_start(datetime(2022,1,3,5,59))), '2021-12-27 06:00:00')
        self.assertEqual(str(m.week_start(datetime(2022,1,3,6))), '2022-01-03 06:00:00')
    def test_fixed_and_compound(self):
        rows=[row(),row(2,sl='100',pips='100'),row(3,'2022-01-10 08:00:00','2022-01-10 09:00:00')]
        logs,weeks=m.simulate(rows,D('1.0'),'M0_BASELINE')
        self.assertEqual([r['RiskAmount'] for r in logs],[D(5000)]*3)
        self.assertEqual(weeks[-1]['FinalCapital'],D(495000))
    def test_compound_loss(self):
        logs,w=m.simulate([row(),row(2,'2022-01-10 08:00:00','2022-01-10 09:00:00')],D('1.0'),'M0_BASELINE')
        self.assertEqual(logs[-1]['RiskAmount'],D(4950))
    def test_initial_loss_dd(self):
        logs,_=m.simulate([row()],D('1.0'),'M0_BASELINE')
        stats=m.metrics(logs,*m.PERIODS['OOS1'])
        self.assertEqual(stats['MaxDDPct'],D(1))
        self.assertEqual(stats['WorstDayPct'],D(-1))
        self.assertEqual(stats['WorstWeekPct'],D(-1))
    def test_cross_week(self):
        with self.assertRaisesRegex(ValueError,'week'):m.validate_rows([row(close='2022-01-10 06:00:00')])
    def test_cross_period(self):
        with self.assertRaisesRegex(ValueError,'period'):m.validate_rows([row(entry='2021-12-31 20:00:00',close='2022-01-01 01:00:00')])
    def test_exact_exclusion(self):
        logs,_=m.simulate([row(22,strategy='22_GA_C_2'),row(1,strategy='22_GA_C_2_extra')],D('1.0'),'M1_MINUS_22')
        self.assertEqual([r['Strategy'] for r in logs],['22_GA_C_2_extra'])
    def test_bankrupt(self):
        with self.assertRaisesRegex(ValueError,'Insolvent'):m.simulate([row(pips='-5000')],D('1.0'),'M0_BASELINE')
    def test_rules(self):
        d={r:{'ALL_FinalCapital':D(1),'OOS_NetProfitJPY':D(1)} for r in m.RISKS}
        self.assertEqual(m.decide(d)['Decision'],'MONEY_ADOPTION_CANDIDATE')
        d[D('1.5')]['ALL_FinalCapital']=D(0)
        self.assertEqual(m.decide(d)['Decision'],'REJECT')
        d[D('1.5')]['ALL_FinalCapital']=D(1)
        d[D('.25')]['ALL_FinalCapital']=D(0)
        self.assertEqual(m.decide(d)['Decision'],'MONEY_ADOPTION_CANDIDATE')
        d[D('.25')]['ALL_FinalCapital']=D('-0.001')
        self.assertEqual(m.decide(d)['Decision'],'REJECT')
    def test_lot(self):
        args=[D(1000),D(50),D(1000),D('.01'),D(100),D('.01')]
        self.assertEqual(m.ea_lot(*args)[1],D('.02'))
        args[0]=D(1)
        self.assertEqual(m.ea_lot(*args)[1],D('.01'))
        self.assertEqual(m.ea_lot(*args,allow_min=False)[1],D(0))
        args[0]=D(1000000)
        self.assertEqual(m.ea_lot(*args)[1],D(1))
        args[0]=D(1499)
        self.assertEqual(m.ea_lot(*args)[1],D('.02'))
        args[0]=D(1000000);args[4]=D('.5')
        self.assertEqual(m.ea_lot(*args)[1],D('.50'))
    def test_unregistered(self):
        with self.assertRaises(ValueError):m.simulate([row()],D('.5'),'M0_BASELINE')

if __name__=='__main__':unittest.main()
