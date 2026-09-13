import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src/research'))
import deployment_reset_2026_money_simulation as m


def row(i=0, strategy='01_TEST', entry='2026-01-02 10:00', close='2026-01-02 11:00', pips='10', sl='20'):
    return dict(RowId=i, StrategyNo=i+1, Strategy=strategy, Pair='USDJPY',
                EntryTime=datetime.fromisoformat(entry), CloseTime=datetime.fromisoformat(close),
                Pips=m.D(pips), SL=m.D(sl), R=m.D(pips)/m.D(sl))


class ResetTests(unittest.TestCase):
    def test_reset_discards_previous_profit_and_peak(self):
        old = row(entry='2025-12-30 10:00', close='2025-12-30 11:00', pips='1000')
        new = row(1, pips='-20')
        a, w = m.simulate([old, new], m.D('1.0'), 'D0_BASELINE')
        self.assertEqual(len(a), 1)
        self.assertEqual(w[0]['StartCapital'], m.INITIAL)
        self.assertEqual(a[0]['Capital'], 495000)
        self.assertEqual(a[0]['PeakCapital'], m.INITIAL)
        self.assertEqual(a[0]['DrawdownPct'], 1)

    def test_partial_week_and_monday_0600(self):
        f = m.engine.week_start
        self.assertEqual(str(f(datetime(2026,1,1))), '2025-12-29 06:00:00')
        self.assertEqual(f(datetime(2026,1,5,5,59)), datetime(2025,12,29,6))
        self.assertEqual(f(datetime(2026,1,5,6)), datetime(2026,1,5,6))

    def test_same_week_fixed_next_week_compounds(self):
        rows = [row(0), row(1), row(2,entry='2026-01-05 06:00',close='2026-01-05 07:00')]
        log, w = m.simulate(rows,m.D('1.0'),'D0_BASELINE')
        self.assertEqual([r['RiskAmount'] for r in log], [5000,5000,5050])
        self.assertEqual(w[-1]['FinalCapital'], m.D('507525'))

    def test_variable_sl(self):
        log,_=m.simulate([row(0,sl='10'),row(1,sl='40')],m.D('1.0'),'D0_BASELINE')
        self.assertEqual([r['YenPnL'] for r in log],[5000,1250])

    def test_exact_single_exclusions(self):
        rows=[row(i,strategy=c) for i,c in enumerate(list(m.CANDIDATES.values())[1:])]
        for candidate,target in m.CANDIDATES.items():
            log,_=m.simulate(rows,m.PRIMARY,candidate)
            self.assertEqual({r['Strategy'] for r in log},{r['Strategy'] for r in rows if r['Strategy']!=target})

    def test_end_date_and_outside_period(self):
        rows=[row(0,entry='2026-09-09 10:00',close='2026-09-09 11:00'),row(1,entry='2026-09-10 10:00',close='2026-09-10 11:00')]
        self.assertEqual([r['RowId'] for r in m.reset_rows(rows)],[0])

    def test_period_crossing_stops(self):
        for a,b in [('2025-12-31 23:00','2026-01-01 01:00'),('2026-09-09 23:00','2026-09-10 01:00')]:
            with self.assertRaises(ValueError):m.reset_rows([row(entry=a,close=b)])

    def test_week_crossing_stops(self):
        with self.assertRaises(ValueError):m.reset_rows([row(entry='2026-01-05 05:00',close='2026-01-05 06:00')])

    def test_invalid_sl_and_insolvency(self):
        r=row();r['SL']=m.D(0)
        with self.assertRaises(ValueError):m.simulate([r],m.PRIMARY,'D0_BASELINE')
        with self.assertRaises(ValueError):m.simulate([row(pips='-2000')],m.D('2.0'),'D0_BASELINE')

    def test_hash_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';p.write_text('invalid')
            with self.assertRaisesRegex(ValueError,'SHA-256'):m.engine.load_baseline(p)

    def test_unregistered_candidate_and_risk(self):
        with self.assertRaises(ValueError):m.simulate([row()],m.PRIMARY,'D5_MINUS_1')
        with self.assertRaises(ValueError):m.simulate([row()],m.D('0.5'),'D0_BASELINE')

    def test_primary_equality_fails(self):
        v={r:m.D(1) for r in m.RISKS};v[m.PRIMARY]=m.D(0)
        self.assertFalse(m.decide(v,True)['ShadowForwardCandidate'])

    def test_other_risk_equality_passes_negative_fails(self):
        v={r:m.D(0) for r in m.RISKS};v[m.PRIMARY]=m.D(1)
        self.assertTrue(m.decide(v,True)['ShadowForwardCandidate'])
        v[m.D('0.25')]=m.D('-0.00000000001')
        self.assertFalse(m.decide(v,True)['ShadowForwardCandidate'])

    def test_pending_cannot_be_candidate(self):
        v={r:m.D(1) for r in m.RISKS}
        self.assertEqual(m.decide(v)['Decision'],'PENDING')
        self.assertFalse(m.decide(v)['ShadowForwardCandidate'])
        v.pop(m.PRIMARY)
        with self.assertRaises(ValueError):m.decide(v)

    def test_close_order_day_week_and_romd(self):
        rows=[row(0,entry='2026-01-02 09:00',close='2026-01-02 12:00',pips='20'),row(1,entry='2026-01-02 10:00',close='2026-01-02 11:00',pips='-20')]
        log,_=m.simulate(rows,m.D('1.0'),'D0_BASELINE')
        self.assertEqual([r['RowId'] for r in log],[1,0])
        v=m.engine.metrics(log,m.START,m.END)
        self.assertEqual(v['MaxDDJPY'],5000)
        self.assertEqual(v['MaxDDPct'],1)
        self.assertEqual(v['WorstDayPct'],0)
        self.assertEqual(v['WorstWeekPct'],0)
        self.assertEqual(v['MoneyRoMD'],0)


if __name__=='__main__':unittest.main()
