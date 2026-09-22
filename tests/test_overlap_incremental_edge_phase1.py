import sys,unittest
from datetime import datetime,date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from overlap_incremental_edge_phase1 import state_for,vector,period,holm,week,metrics

def row(symbol='EURJPY',direction='Long',entry='2026-01-05 09:00:00',exit='2026-01-05 10:00:00'):
 return dict(Symbol=symbol,Direction=direction,Entry=datetime.fromisoformat(entry),Exit=datetime.fromisoformat(exit),Rfloat=1.0,Week='2026-01-05')
class TestOverlap(unittest.TestCase):
 def test_strict_open(self):
  old=row();new=row(entry='2026-01-05 09:30:00',exit='2026-01-05 10:30:00')
  self.assertEqual(state_for(new,[old],1)[0],'SAME_SYMBOL_SAME_DIR_OPEN')
  self.assertEqual(state_for(new,[old],2)[0],'SIMULTANEOUS_BATCH')
  self.assertEqual(state_for(row(entry='2026-01-05 10:00:00',exit='2026-01-05 11:00:00'),[old],1)[:2],('BOUNDARY_AMBIGUOUS','EXIT_EQUALS_ENTRY'))
 def test_opposite_and_mixed(self):
  old=row(direction='Short');new=row(entry='2026-01-05 09:30:00')
  self.assertEqual(state_for(new,[old],1)[0],'SAME_SYMBOL_OPPOSITE_DIR_OPEN')
  self.assertEqual(state_for(new,[old,row()],1)[:2],('BOUNDARY_AMBIGUOUS','MIXED_DIRECTIONS'))
 def test_cross(self):
  new=row(symbol='GBPJPY',entry='2026-01-05 09:30:00')
  self.assertEqual(state_for(new,[row()],1)[2],'CROSS_SYMBOL_ALIGNED_EXPOSURE')
  self.assertEqual(state_for(new,[row(direction='Short')],1)[2],'CROSS_SYMBOL_OPPOSED_EXPOSURE')
  self.assertEqual(vector('EURJPY','Long'),{'EUR':1,'JPY':-1})
 def test_period(self):
  self.assertTrue(period(date(2021,12,31),'Historical'));self.assertFalse(period(date(2022,1,1),'Historical'))
  self.assertTrue(period(date(2026,9,9),'2026 Monitor'));self.assertFalse(period(date(2026,9,10),'ALL'))
  self.assertEqual(week(date(2026,1,11)),'2026-01-05')
 def test_holm_and_metrics(self):
  self.assertEqual(holm([.01,.03,.04]),[.03,.06,.06])
  m=metrics([dict(Rfloat=x,Week='2026-01-05') for x in (1,-.5,0)])
  self.assertEqual(m['Trades'],3);self.assertEqual(m['PF'],2);self.assertEqual(m['WinRate'],1/3)
if __name__=='__main__':unittest.main()
