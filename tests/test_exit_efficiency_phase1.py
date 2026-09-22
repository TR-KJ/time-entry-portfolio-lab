import sys,unittest
from datetime import datetime,timedelta
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from exit_efficiency_phase1 import checkpoint,simulate,reconcile,holm,metric,in_period

def anchor():
 e=datetime(2026,9,7,13,55);x=e+timedelta(minutes=4)
 return dict(_n=1,_entry=e,_scheduled=x,_week='2026-09-07',StrategyNo='1',Strategy='1_EJ_Log1',Pair='EJ',Direction='Long',Mode='STANDARD',EntryTime=e.isoformat(sep=' '),ScheduledExitTime=x.isoformat(sep=' '),CloseTime=x.isoformat(sep=' '),ExitReason='TimeExit',ExitDelayMinutes='0',RawEntryOpen='100',EntryPrice='100.01',ClosePrice='100',SL='70',TP='250',Pips='-1',R=str(round(-1/70,9)))
def bars():
 idx=pd.date_range('2026-09-07 13:55',periods=5,freq='min')
 return pd.DataFrame(dict(Open=[100]*5,High=[100.1]*5,Low=[99.9]*5,Close=[100]*5),index=idx)
class TestA3(unittest.TestCase):
 def test_checkpoint_floor_overnight(self):
  e=datetime(2026,9,7,20,56);x=datetime(2026,9,8,4,45)
  self.assertEqual(checkpoint(e,x,.75),datetime(2026,9,8,2,47))
  self.assertEqual(checkpoint(e,x,1),x)
 def test_time_exit_spread_pip(self):
  r=simulate(anchor(),bars(),'E100');self.assertEqual(r['ExitReason'],'TimeExit');self.assertEqual(r['EntryPrice'],100.01);self.assertEqual(r['Pips'],-1)
  self.assertEqual(reconcile(anchor(),r),[])
 def test_sl_before_checkpoint_and_sl_first(self):
  b=bars();b.loc[b.index[1],'Low']=99;b.loc[b.index[1],'High']=103
  r=simulate(anchor(),b,'E75');self.assertEqual(r['ExitReason'],'SL');self.assertEqual(r['CloseTime'],'2026-09-07 13:56:00')
 def test_tp_before_checkpoint(self):
  b=bars();b.loc[b.index[1],'High']=103
  r=simulate(anchor(),b,'E75');self.assertEqual(r['ExitReason'],'TP');self.assertEqual(r['Pips'],250)
 def test_fallback(self):
  b=bars().drop(pd.Timestamp('2026-09-07 13:59'))
  r=simulate(anchor(),b,'E100');self.assertEqual(r['Status'],'MISSING_CHECKPOINT_BAR')
  extra=pd.DataFrame(dict(Open=[100],High=[100.1],Low=[99.9],Close=[100]),index=[pd.Timestamp('2026-09-07 14:00')]);b=pd.concat([b,extra])
  r=simulate(anchor(),b,'E100');self.assertEqual(r['ExitDelayMinutes'],1)
 def test_holm_period_metric(self):
  self.assertEqual(holm([.01,.03,.04]),[.03,.06,.06]);self.assertTrue(in_period(datetime(2026,9,9),'2026 Monitor'));self.assertFalse(in_period(datetime(2026,9,10),'ALL'))
  m=metric([dict(R=x,Week='2026-09-07',ExitReason=r) for x,r in [(1,'TP'),(-1,'SL'),(0,'TimeExit')]])
  self.assertEqual(m['Trades'],3);self.assertEqual(m['PF'],1);self.assertEqual(m['TimeRate'],1/3)
if __name__=='__main__':unittest.main()
