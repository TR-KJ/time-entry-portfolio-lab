import unittest
from decimal import Decimal
import pandas as pd
from china_demand_group_analysis import metrics, select_period, decide, load_baseline

class ResearchTests(unittest.TestCase):
    def test_period_boundaries(self):
        df = pd.DataFrame({'EntryTime':pd.to_datetime(['2021-12-31 23:59:59','2022-01-01','2025-12-31 23:59:59','2026-01-01','2026-09-09 23:59:59','2026-09-10'],format='mixed')})
        self.assertEqual(list(select_period(df,'2022-01-01','2026-01-01').index),[1,2])
        self.assertEqual(list(select_period(df,'2026-01-01','2026-09-10').index),[3,4])

    def test_initial_loss_and_week_boundary(self):
        times = pd.to_datetime(['2026-01-04 12:00','2026-01-05 12:00','2026-01-05 13:00'])
        df = pd.DataFrame({'EntryTime':times,'CloseTime':times,'StrategyNo':[1,2,3],'R':[-2.,1.,-3.],'_ExactR':[Decimal('-2'),Decimal('1'),Decimal('-3')]})
        m=metrics(df)
        self.assertEqual(m['MaxDDR'],4.)
        self.assertEqual(m['WorstDayR'],-2.)
        self.assertEqual(m['WorstWeekR'],-2.)
        self.assertEqual(m['PF'],0.2)

    def test_decision_zero_boundary(self):
        for d in [Decimal('-1'),Decimal('0')]:
            self.assertEqual(decide(d),'REJECT_C1_KEEP_C0')
        self.assertEqual(decide(Decimal('0.000000000001')),'REVIEW_REQUIRED_NOT_ADOPTED')

    def test_bad_hash_fails(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.csv';p.write_text('R\n0\n')
            with self.assertRaisesRegex(ValueError,'SHA-256'):
                load_baseline(p)

if __name__ == '__main__':
    unittest.main()
