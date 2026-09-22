import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from component_edge_decay_phase1 import nominal_gotobi,period,holm,metrics,assign,COMPONENTS

class TestA1(unittest.TestCase):
    def test_nominal(self):
        self.assertEqual(nominal_gotobi(date(2026,9,25)),'25')
        self.assertEqual(nominal_gotobi(date(2025,10,24)),'25') # Saturday 25
        self.assertEqual(nominal_gotobi(date(2025,8,29)),'30') # Saturday 30
        self.assertEqual(nominal_gotobi(date(2026,6,19)),None) # Saturday 20 not shifted
        self.assertEqual(nominal_gotobi(date(2026,7,20)),'20')
    def test_period_boundaries(self):
        self.assertTrue(period(date(2021,12,31),'Historical'))
        self.assertFalse(period(date(2022,1,1),'Historical'))
        self.assertTrue(period(date(2022,1,1),'Recent A'))
        self.assertTrue(period(date(2024,1,1),'Recent B'))
        self.assertTrue(period(date(2026,9,9),'2026 Monitor'))
        self.assertFalse(period(date(2026,9,10),'ALL'))
    def test_holm(self):
        self.assertEqual(holm([.01,.03,.04]),[.03,.06,.06])
        self.assertEqual(len(COMPONENTS),10)
        self.assertEqual(sum(map(len,COMPONENTS.values())),23)
    def test_metrics(self):
        rows=[dict(Rfloat=x,Week=w) for x,w in [(1,'2026-01-05'),(-.5,'2026-01-05'),(0,'2026-01-12')]]
        m=metrics(rows)
        self.assertEqual(m['Trades'],3);self.assertEqual(m['Weeks'],2)
        self.assertAlmostEqual(m['TotalR'],.5);self.assertAlmostEqual(m['AvgR'],1/6)
        self.assertEqual(m['PF'],2);self.assertEqual(m['WinRate'],1/3)
    def test_assign(self):
        base=dict(No=12,Strategy='12_UJ_Short_Core',Mode='GOTO',SL='20',TP='50')
        r=dict(base,Day=date(2025,10,24),EntryTime='2025-10-24 09:55:00')
        self.assertEqual(assign(r),'25')
        r=dict(base,Day=date(2025,8,29),EntryTime='2025-08-29 09:55:00')
        self.assertEqual(assign(r),'30')
        r=dict(base,Day=date(2026,6,19),EntryTime='2026-06-19 09:55:00')
        with self.assertRaises(ValueError): assign(r)
        r=dict(base,Mode='NORMAL',Day=date(2026,6,19),EntryTime='2026-06-19 08:04:00')
        self.assertIsNone(assign(r))

if __name__=='__main__': unittest.main()
