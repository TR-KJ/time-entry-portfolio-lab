// Isolated no-order component regression. Never attach as a trading EA.
#property strict
#property script_show_inputs
#include "reconcile_test_adapters.mqh"
#include "reconcile_frozen_functions.mqh"
int passed=0,failed=0;
void Check(bool ok,string name)
{ if(ok) passed++; else failed++; Print("[P5 RECON TEST] ",name,"=",ok?"PASS":"FAIL"); }
long RequestTime() { return (long)RServer()*1000; }
void Reset()
{
   ArrayResize(strategies,1); strategies[0].symbol="USDJPY"; strategies[0].magic=10001;
   strategies[0].strategy_name="FIXTURE_ONLY";
   ArrayResize(rd,0); ArrayResize(rp,0); ArrayResize(selected_history,0);
   ArrayResize(pending_entry_reconciliations,0); ArrayResize(pending_exit_reconciliations,0);
   clock_ms=1000; marks=0; entry_events=0; exit_events=0; runs=0;
   guard_ok=true; selected_position=-1; last_log=""; InpTradeReconcileTimeoutSeconds=10;
}
void Deal()
{
   ArrayResize(rd,1); rd[0].ticket=101; rd[0].order=501; rd[0].position=901;
   rd[0].symbol="USDJPY"; rd[0].magic=10001; rd[0].entry=DEAL_ENTRY_IN;
   rd[0].type=DEAL_TYPE_BUY; rd[0].time=RequestTime(); rd[0].lot=.10;
}
void Position()
{
   ArrayResize(rp,1); rp[0].ticket=701; rp[0].identifier=901; rp[0].symbol="USDJPY";
   rp[0].magic=10001; rp[0].type=POSITION_TYPE_BUY; rp[0].time=RequestTime(); rp[0].lot=.10;
}
void StartEntry(int direction=DIR_LONG)
{ StartPendingEntryReconciliation(strategies[0],direction,.10,RequestTime(),0,501,0,D'2026.09.16 12:00',0,"fixture"); }
void ExitFixture(PendingExitReconciliation &p)
{
   ZeroMemory(p);p.strategy_index=0;p.position_ticket=701;p.position_identifier=901;
   p.close_direction=DIR_SHORT;p.requested_lot=.10;p.request_time_msc=RequestTime();p.result_order=501;
}
bool EntryReset()
{
   PendingEntryReconciliation p=pending_entry_reconciliations[0];
   return !p.active && p.strategy_index==0 && p.direction==0 && p.requested_lot==0 &&
      p.request_time_msc==0 && p.previous_deal_ticket==0 && p.result_order==0 && p.result_deal==0 &&
      p.entry_jst_time==0 && p.deadline_tick_msc==0 && p.retcode==0 && p.retcode_description=="";
}
void OnStart()
{
   Reset();
   Check(IsNormalTradeSuccessResult(true,TRADE_RETCODE_DONE),"normal DONE");
   Check(IsNormalTradeSuccessResult(true,TRADE_RETCODE_PLACED),"normal PLACED");
   Check(IsNormalTradeSuccessResult(true,TRADE_RETCODE_DONE_PARTIAL),"normal PARTIAL");
   Check(!IsNormalTradeSuccessResult(false,TRADE_RETCODE_DONE),"false return rejected");
   Check(!IsNormalTradeSuccessResult(true,0),"zero retcode rejected");
   EnsurePendingEntryReconciliationArray();Check(EntryReset(),"initial state fully reset");
   StartEntry();Check(HasPendingEntryReconciliation(0) && pending_entry_reconciliations[0].deadline_tick_msc==11000,"pending and deadline");
   EnsurePendingEntryReconciliationArray();Check(HasPendingEntryReconciliation(0),"same size preserves pending");
   ArrayResize(strategies,2);EnsurePendingEntryReconciliationArray();
   Check(HasPendingEntryReconciliation(0) && !pending_entry_reconciliations[1].active && pending_entry_reconciliations[1].strategy_index==1,"growth preserves and initializes");
   ClearPendingEntryReconciliation(0);Check(EntryReset(),"clear fully resets");
   Check(!HasPendingEntryReconciliation(-1) && !HasPendingEntryReconciliation(5),"invalid strategy index");
   Reset();StartEntry();clock_ms=10999;ProcessPendingEntryReconciliations();
   Check(HasPendingEntryReconciliation(0) && marks==0,"before timeout stays pending");
   clock_ms=11000;ProcessPendingEntryReconciliations();
   Check(EntryReset() && marks==0 && StringFind(last_log,"timeout_no_matching_position_or_deal")>=0,"timeout without evidence");
   Reset();StartEntry();Deal();Check(ConfirmPendingEntryFromDeal(0,101) && marks==1 && entry_events==1 && EntryReset(),"delayed entry DEAL_ADD");
   Check(!ConfirmPendingEntryFromDeal(0,101) && marks==1,"duplicate deal not marked twice");
   Reset();StartEntry(DIR_SHORT);Deal();rd[0].type=DEAL_TYPE_SELL;
   Check(ConfirmPendingEntryFromDeal(0,101) && marks==1,"SELL deal evidence");
   for(int bad=0;bad<8;bad++)
   {
      Reset();Deal();
      if(bad==0)rd[0].symbol="EURJPY"; if(bad==1)rd[0].magic=999;
      if(bad==2)rd[0].type=DEAL_TYPE_SELL; if(bad==3)rd[0].entry=DEAL_ENTRY_OUT;
      if(bad==4)rd[0].order=999; if(bad==5)rd[0].time=RequestTime()-2001;
      if(bad==6)rd[0].lot=.20; if(bad==7)rd[0].lot=0;
      double lot=0;Check(!IsMatchingEntryDeal(101,strategies[0],DIR_LONG,.10,RequestTime()-2000,501,lot),"reject unrelated entry "+IntegerToString(bad));
   }
   Reset();Deal();rd[0].time=RequestTime()-2000;double lot=0;
   Check(IsMatchingEntryDeal(101,strategies[0],DIR_LONG,.10,RequestTime()-2000,501,lot),"two second boundary");
   ulong ticket=0;Check(!FindMatchingNewDeal(strategies[0],DIR_LONG,.10,RequestTime()-2000,101,501,101,ticket,lot),"previous deal excluded");
   Reset();StartEntry();Position();clock_ms=11000;ProcessPendingEntryReconciliations();
   Check(marks==1 && entry_events==1 && EntryReset(),"position evidence precedes timeout");
   Reset();StartEntry();Deal();ROnTick();ROnTimer();
   Check(marks==1 && entry_events==1 && runs==2,"tick timer repeated evidence once");
   Reset();StartEntry();Deal();guard_ok=false;ROnTick();ROnTimer();
   Check(marks==0 && runs==0 && HasPendingEntryReconciliation(0),"disabled callback guard");
   Reset();StartEntry();Deal();MqlTradeTransaction tx;MqlTradeRequest req;MqlTradeResult res;
   ZeroMemory(tx);ZeroMemory(req);ZeroMemory(res);tx.type=TRADE_TRANSACTION_DEAL_ADD;tx.deal=101;
   ROnTradeTransaction(tx,req,res);ROnTradeTransaction(tx,req,res);
   Check(marks==1 && entry_events==1,"transaction callback matching once");
   Reset();StartEntry();Deal();rd[0].magic=999;ROnTradeTransaction(tx,req,res);
   Check(marks==0 && HasPendingEntryReconciliation(0),"transaction unrelated magic");
   PendingExitReconciliation p;Reset();ExitFixture(p);string evidence="";ticket=0;lot=0;
   Check(ReconcileExecutedExit(p,strategies[0],evidence,ticket,lot) && evidence=="POSITION_GONE","exit position gone");
   Reset();ExitFixture(p);Position();StartPendingExitReconciliation(p,strategies[0]);
   Check(HasPendingExitReconciliation(701),"exit pending ticket lookup");
   clock_ms=10999;ProcessPendingExitReconciliations();Check(HasPendingExitReconciliation(701) && exit_events==0,"exit before timeout");
   clock_ms=11000;ProcessPendingExitReconciliations();
   Check(!HasPendingExitReconciliation(701) && exit_events==0 && StringFind(last_log,"timeout_position_still_open")>=0,"exit timeout still open");
   Reset();ExitFixture(p);Position();StartPendingExitReconciliation(p,strategies[0]);ArrayResize(rp,0);ProcessPendingExitReconciliations();
   Check(!HasPendingExitReconciliation(701) && exit_events==1,"pending exit position disappears");
   Reset();ExitFixture(p);Deal();rd[0].entry=DEAL_ENTRY_OUT;rd[0].type=DEAL_TYPE_SELL;
   Check(IsMatchingExitDeal(101,p,strategies[0],lot),"matching OUT");
   rd[0].entry=DEAL_ENTRY_OUT_BY;Check(IsMatchingExitDeal(101,p,strategies[0],lot),"matching OUT_BY");
   for(int bad=0;bad<8;bad++)
   {
      Reset();ExitFixture(p);Deal();rd[0].entry=DEAL_ENTRY_OUT;rd[0].type=DEAL_TYPE_SELL;
      if(bad==0)rd[0].symbol="EURJPY";if(bad==1)rd[0].magic=999;
      if(bad==2)rd[0].type=DEAL_TYPE_BUY;if(bad==3)rd[0].entry=DEAL_ENTRY_IN;
      if(bad==4)rd[0].position=999;if(bad==5)rd[0].order=999;
      if(bad==6)rd[0].time=RequestTime()-2001;if(bad==7)rd[0].lot=.05;
      Check(!IsMatchingExitDeal(101,p,strategies[0],lot),"reject unrelated partial exit "+IntegerToString(bad));
   }
   Reset();ExitFixture(p);Position();StartPendingExitReconciliation(p,strategies[0]);Deal();rd[0].entry=DEAL_ENTRY_OUT;rd[0].type=DEAL_TYPE_SELL;
   Check(ConfirmPendingExitFromDeal(101) && !HasPendingExitReconciliation(701) && exit_events==1,"delayed exit DEAL_ADD");
   Check(!ConfirmPendingExitFromDeal(101) && exit_events==1,"duplicate exit event");
   Reset();ExitFixture(p);Position();StartPendingExitReconciliation(p,strategies[0]);Deal();rd[0].entry=DEAL_ENTRY_OUT;rd[0].type=DEAL_TYPE_SELL;
   ArrayResize(rd,2);rd[1]=rd[0];rd[1].ticket=102;rd[1].position=999;
   Check(FindMatchingExitDeal(p,strategies[0],ticket,lot) && ticket==101,"history selection preserves candidate iteration");
   ROnTimer();ROnTick();Check(exit_events==1 && !HasPendingExitReconciliation(701),"exit timer tick once");
   Print("[P5 RECON TEST] SUMMARY Passed=",passed," Failed=",failed," NO_ORDERS=true COMPONENT_ONLY=true");
}
