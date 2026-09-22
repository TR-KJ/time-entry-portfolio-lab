import sys
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'research'))
from c1_path_management_phase1 import replay, holm


def anchor(pair='UJ', long=True, sl=100, tp=None, duration=4):
    entry = datetime(2026, 1, 5, 9)
    return dict(_n=1, Strategy='synthetic', Pair=pair, Direction='Long' if long else 'Short',
                Mode='STANDARD', EntryTime=str(entry), ScheduledExitTime=str(entry + pd.Timedelta(minutes=duration)),
                _entry=entry, _scheduled=entry + pd.Timedelta(minutes=duration),
                _week='2026-01-05', SL=str(sl), TP='' if tp is None else str(tp))


def bars(*ohlc, start='2026-01-05 09:00'):
    return pd.DataFrame(ohlc, columns=['Open','High','Low','Close'],
                        index=pd.date_range(start, periods=len(ohlc), freq='min'))


class C1ReplayTests(unittest.TestCase):
    def test_next_bar_be_and_exact_half(self):
        a = anchor()
        # Entry fill 100.005, half-R is 100.505. The same bar returns below BE;
        # the revised stop may first operate on the following bar.
        data = bars((100,100.505,99.8,100.1), (100.1,100.2,99.99,100.1),
                    (100.1,100.2,100.0,100.1), (100.1,100.2,100.0,100.1),
                    (100.1,100.2,100.0,100.1))
        self.assertEqual(replay(a,data,'R0')['ExitReason'],'TimeExit')
        r = replay(a,data,'R1_BE50')
        self.assertEqual(r['ExitReason'],'DynamicSL')
        self.assertEqual(r['CloseTime'],'2026-01-05 09:01:00')
        self.assertEqual(r['R'],0)

    def test_exact_one_and_lock(self):
        a = anchor()
        data = bars((100,101.005,99.8,100.9), (100.9,101.0,100.4,100.5),
                    (100.5,100.6,100.4,100.5), (100.5,100.6,100.4,100.5),
                    (100.5,100.6,100.4,100.5))
        r = replay(a,data,'R2_LOCK100')
        self.assertEqual(r['R'],.5)
        self.assertEqual(r['CloseTime'],'2026-01-05 09:01:00')

    def test_same_bar_stop_before_tp_and_before_milestone(self):
        a = anchor(tp=100)
        data = bars((100,102,98,100), *(4*((100,100.1,99.9,100),)))
        for v in ('R0','R1_BE50','R2_LOCK100','R3_STAGED'):
            r = replay(a,data,v)
            self.assertEqual(r['ExitReason'],'SL')
            self.assertFalse(r['Reached05'])

    def test_tp_before_milestone_and_overnight(self):
        a = anchor(tp=20)
        data = bars((100,100.3,99.8,100.2), *(4*((100.2,100.21,100.1,100.2),)))
        self.assertEqual(replay(a,data,'R3_STAGED')['ExitReason'],'TP')
        b = anchor(duration=3)
        b['_entry'] = datetime(2026,1,5,23,59)
        b['_scheduled'] = datetime(2026,1,6,0,2)
        b['EntryTime'] = str(b['_entry']); b['ScheduledExitTime'] = str(b['_scheduled'])
        overnight = bars(*(4*((100,100.1,99.9,100),)),start='2026-01-05 23:59')
        self.assertEqual(replay(b,overnight,'R0')['ExitReason'],'TimeExit')

    def test_missing_bar_and_plus_four_fallback(self):
        a = anchor(duration=1)
        data = bars(*(6*((100,100.1,99.9,100),))).drop(pd.Timestamp('2026-01-05 09:01'))
        r = replay(a,data,'R0')
        self.assertEqual(r['ExitDelayMinutes'],1)
        self.assertEqual(r['CloseTime'],'2026-01-05 09:02:00')
        with self.assertRaises(ValueError):
            replay(a,data.iloc[:1],'R0')

    def test_holm(self):
        self.assertEqual(holm([.01,.04,.03]),[.03,.06,.06])


if __name__ == '__main__':
    unittest.main()
