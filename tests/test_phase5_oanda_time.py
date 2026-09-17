"""Calendar-mirror versus independent zoneinfo oracle; NOT actual MQL execution."""
import unittest,sys
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/research'))
import volatility_phase5_audit as a

def nth_sunday(y,m,n):
    d=datetime(y,m,1)
    return d+timedelta(days=(6-d.weekday())%7+7*(n-1))
def mirror_offset(u):
    if u.year<2007:return 0
    return 3 if nth_sunday(u.year,3,2)+timedelta(hours=7)<=u<nth_sunday(u.year,11,1)+timedelta(hours=6) else 2
def mirror_server(t):
    candidates=[t-timedelta(hours=h) for h in (2,3) if mirror_offset(t-timedelta(hours=h))==h]
    if len(candidates)!=1:raise ValueError('invalid')
    return candidates[0]+timedelta(hours=9)

class OandaClockTests(unittest.TestCase):
    def test_calendar_mirror_against_zoneinfo_2007_2035(self):
        for y in range(2007,2036):
            dates=[datetime(y,m,15,12) for m in range(1,13)]
            for transition in (nth_sunday(y,3,2)+timedelta(hours=7),nth_sunday(y,11,1)+timedelta(hours=6)):
                dates.extend(transition+timedelta(minutes=i) for i in range(-180,181))
            for u in dates:
                j=u+timedelta(hours=9)
                s=u+timedelta(hours=mirror_offset(u))
                self.assertEqual(a.server_from_jst(j),s)
                try: expected=a.jst_from_server(s)
                except ValueError:
                    with self.assertRaises(ValueError):mirror_server(s)
                else:self.assertEqual(mirror_server(s),expected)
    def test_us_eu_mismatch(self):
        for t in [datetime(2025,3,17,12),datetime(2025,10,28,12),datetime(2026,3,16,12),datetime(2026,10,27,12)]:
            eu=t.replace(tzinfo=ZoneInfo('Europe/Helsinki')).astimezone(ZoneInfo('Asia/Tokyo')).replace(tzinfo=None)
            self.assertEqual(eu-a.jst_from_server(t),timedelta(hours=1))
    def test_eu_switch_dates_are_ordinary_oanda_times(self):
        for s in ['2026.03.29 03:30:00','2026.10.25 03:30:00']:
            self.assertEqual(a.jst_from_server(a.dt(s)),a.dt(s)+timedelta(hours=6))
    def test_unsupported_dates(self):
        with self.assertRaises(ValueError):a.jst_from_server(datetime(2006,7,1))
        with self.assertRaises(ValueError):a.server_from_jst(datetime(2006,7,1))
    def test_jst_midnight_week_and_history_boundaries(self):
        for j in [datetime(2026,3,9),datetime(2026,11,2),datetime(2026,9,16)]:
            raw=a.server_from_jst(j)
            self.assertEqual(a.jst_from_server(raw),j)
            self.assertEqual(a.jst_from_server(raw-timedelta(seconds=1)),j-timedelta(seconds=1))
            begin=j-timedelta(days=600)
            self.assertEqual(a.jst_from_server(a.server_from_jst(begin)),begin)
    def test_true_jst_daily_boundary_and_no_lookahead(self):
        rows=[]
        for j,price in [(datetime(2026,3,16,23,59),100),(datetime(2026,3,17),999)]:
            rows.append(dict(ServerTime=a.server_from_jst(j).strftime(a.FORMAT),JST=j.strftime(a.FORMAT),Open=price,High=price,Low=price,Close=price))
        d=a.daily_from_rows(rows,datetime(2026,3,17))
        self.assertEqual(len(d),1);self.assertEqual(d[0]['close'],100)
    def test_fixture_timestamp_roundtrip(self):
        import csv
        with (ROOT/'research_inputs/phase5/synthetic_m1_fixture.csv').open() as f:
            rows=list(csv.DictReader(f))
        for r in rows:self.assertEqual(a.jst_from_server(a.dt(r['ServerTime'])),a.dt(r['JST']))
        result=a.feature(rows,datetime(2026,1,1))
        self.assertEqual((result['days'],result['rank'],result['q'],result['risk']),(280,311,4,1.1))
    def test_adapter_wiring_and_default_disabled(self):
        ea=(ROOT/'src/EA/time_entry_step9_2_4_trade_result_reconcile_27strategies_vol_r2_demo.mq5').read_text()
        runtime=(ROOT/'src/EA/phase5_demo/vol_r2_runtime.mqh').read_text()
        dep=(ROOT/'src/EA/phase5_demo/step921_demo_dependency.mqh').read_text()
        config=(ROOT/'configs/phase5/step9_2_4_dell_demo_vol_r2_phase5.set').read_text()
        self.assertNotIn('Helsinki',ea+runtime+config)
        self.assertIn('InpPhase5OandaTimeVerified=false',config)
        self.assertIn('InpPhase5Approved=false',config)
        self.assertIn('return P5Now()',dep)
        self.assertIn('OANDA_US_DST_V1',runtime)

if __name__=='__main__':unittest.main(verbosity=2)
