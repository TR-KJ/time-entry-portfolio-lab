import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src/research'))
import edge_decay_phase2_single_stop as m
D=m.D

def annual(*values): return dict(zip(range(2022,2027), map(D, values)))
def row(r, close='2022-01-03 12:00:00', entry='2022-01-03 10:00:00', strategy=m.FAMILY[0]):
    return dict(R=D(r), CloseTime=close, EntryTime=entry, Strategy=strategy, StrategyNo=int(strategy.split('_')[0]))

class Tests(unittest.TestCase):
    def test_zero_rejected(self):
        self.assertEqual(m.decide(annual('0','0','0','0','0'))['Decision'],'REJECT')
    def test_three_years_including_zero(self):
        self.assertEqual(m.decide(annual('5','5','0','-1','-1'))['Decision'],'ADOPTION_CANDIDATE')
        self.assertEqual(m.decide(annual('5','5','-1','-1','-1'))['Decision'],'REJECT')
    def test_seventy_exact_and_sides(self):
        for value, expected in [('6.999','ADOPTION_CANDIDATE'),('7','REJECT'),('7.001','REJECT')]:
            self.assertEqual(m.decide(annual(value,str(D(10)-D(value)),'0','0','0'))['Decision'],expected)
    def test_net_denominator(self):
        d=m.decide(annual('6','4','0','-1','-1'))
        self.assertEqual(d['MaxAnnualShare'],D('.75'))
        self.assertEqual(d['Decision'],'REJECT')
    def test_initial_dd(self):
        self.assertEqual(m.metrics([row('-2'),row('1')])['MaxDDR'],D(2))
    def test_pf_edge_cases(self):
        self.assertIsNone(m.metrics([])['PF'])
        self.assertEqual(m.metrics([row('1')])['PF'],D('Infinity'))
        self.assertIsNone(m.compare([row('1')],m.FAMILY[0],'X')[0][2]['PF'])
    def test_day_week_boundary(self):
        rows=[row('-2','2022-01-02 23:59:00','2022-01-01 00:00:00'),row('-3','2022-01-03 00:00:00','2022-01-01 00:00:00'),row('1','2022-01-03 01:00:00','2022-01-01 00:00:00')]
        self.assertEqual(m.metrics(rows)['WorstWeekR'],D(-2))
        self.assertEqual(m.metrics(rows)['WorstDayR'],D(-2))
    def test_entry_period_close_order(self):
        rows=[row('-2','2022-01-01 01:00:00','2021-12-31 23:00:00')]
        self.assertEqual(len(m.select(rows,*m.PERIODS['IS'])),1)
        self.assertEqual(len(m.select(rows,*m.PERIODS['OOS1'])),0)
    def test_single_stop(self):
        rows=[row('-2'),row('3',strategy=m.FAMILY[1])]
        result,delta=m.compare(rows,m.FAMILY[0],'X')
        self.assertEqual(delta,D(2)); self.assertEqual(result[1]['Trades'],1)
        self.assertEqual(result[1]['TotalR'],D(3))
        with self.assertRaises(ValueError):m.compare(rows,','.join(m.FAMILY),'X')
    def test_bad_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.csv';p.write_text('invalid')
            with self.assertRaises(ValueError):m.load_baseline(p)
    def test_predecessor_required(self):
        with self.assertRaises(ValueError):m.validate_predecessor(m.FAMILY[1])
        m.validate_predecessor(m.FAMILY[0])
    def test_five_years_required(self):
        with self.assertRaises(ValueError):m.decide({2022:D(1)})

if __name__=='__main__':unittest.main()
