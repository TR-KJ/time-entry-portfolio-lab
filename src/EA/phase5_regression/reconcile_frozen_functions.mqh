// Generated verbatim from frozen dedicated EA; DO NOT HAND EDIT.
struct PendingEntryReconciliation
{
   bool active;
   int strategy_index;
   int direction;
   double requested_lot;
   long request_time_msc;
   ulong previous_deal_ticket;
   ulong result_order;
   ulong result_deal;
   datetime entry_jst_time;
   ulong deadline_tick_msc;
   long retcode;
   string retcode_description;
};

struct PendingExitReconciliation
{
   bool active; int strategy_index; ulong position_ticket; ulong position_identifier;
   int close_direction; double requested_lot; long request_time_msc;
   ulong result_order; ulong result_deal; ulong deadline_tick_msc;
   long retcode; string retcode_description; int last_error;
};
PendingEntryReconciliation pending_entry_reconciliations[];
PendingExitReconciliation pending_exit_reconciliations[];
void ResetPendingEntryReconciliation(int index)
{
   if(index < 0 || index >= ArraySize(pending_entry_reconciliations)) return;

   pending_entry_reconciliations[index].active = false;
   pending_entry_reconciliations[index].strategy_index = index;
   pending_entry_reconciliations[index].direction = 0;
   pending_entry_reconciliations[index].requested_lot = 0.0;
   pending_entry_reconciliations[index].request_time_msc = 0;
   pending_entry_reconciliations[index].previous_deal_ticket = 0;
   pending_entry_reconciliations[index].result_order = 0;
   pending_entry_reconciliations[index].result_deal = 0;
   pending_entry_reconciliations[index].entry_jst_time = 0;
   pending_entry_reconciliations[index].deadline_tick_msc = 0;
   pending_entry_reconciliations[index].retcode = 0;
   pending_entry_reconciliations[index].retcode_description = "";
}

void EnsurePendingEntryReconciliationArray()
{
   int strategy_count = ArraySize(strategies);
   int previous_count = ArraySize(pending_entry_reconciliations);
   if(previous_count == strategy_count) return;

   ArrayResize(pending_entry_reconciliations, strategy_count);

   // Preserve existing pending entries and initialize only newly allocated slots.
   for(int i = previous_count; i < strategy_count; i++)
      ResetPendingEntryReconciliation(i);
}

bool HasPendingEntryReconciliation(int strategy_index)
{
   EnsurePendingEntryReconciliationArray();
   if(strategy_index < 0 || strategy_index >= ArraySize(pending_entry_reconciliations)) return false;
   return pending_entry_reconciliations[strategy_index].active;
}

int FindStrategyIndexByMagicAndSymbol(long magic, string symbol)
{
   for(int i = 0; i < ArraySize(strategies); i++)
      if(strategies[i].magic == magic && strategies[i].symbol == symbol) return i;
   return -1;
}

void ClearPendingEntryReconciliation(int strategy_index)
{
   ResetPendingEntryReconciliation(strategy_index);
}

void StartPendingEntryReconciliation(StrategyConfig &cfg,
                                     int direction,
                                     double requested_lot,
                                     long request_time_msc,
                                     ulong previous_deal_ticket,
                                     ulong result_order,
                                     ulong result_deal,
                                     datetime entry_jst_time,
                                     long retcode,
                                     string retcode_description)
{
   EnsurePendingEntryReconciliationArray();
   int strategy_index = FindStrategyIndexByMagicAndSymbol(cfg.magic, cfg.symbol);
   if(strategy_index < 0)
   {
      PrintDebug(cfg.strategy_name, TradeDirectionText(direction) + " entry failed. Reconcile=cannot_identify_strategy");
      return;
   }

   PendingEntryReconciliation pending;
   pending.active = true;
   pending.strategy_index = strategy_index;
   pending.direction = direction;
   pending.requested_lot = requested_lot;
   pending.request_time_msc = request_time_msc;
   pending.previous_deal_ticket = previous_deal_ticket;
   pending.result_order = result_order;
   pending.result_deal = result_deal;
   pending.entry_jst_time = entry_jst_time;
   int timeout_seconds = InpTradeReconcileTimeoutSeconds;
   if(timeout_seconds < 1) timeout_seconds = 1;
   pending.deadline_tick_msc = GetTickCount64() + (ulong)timeout_seconds * 1000;
   pending.retcode = retcode;
   pending.retcode_description = retcode_description;
   pending_entry_reconciliations[strategy_index] = pending;

   PrintDebug(cfg.strategy_name,
              TradeDirectionText(direction) +
              " entry reconciliation pending. Symbol=" + cfg.symbol +
              ", Magic=" + IntegerToString(cfg.magic) +
              ", RequestedLot=" + DoubleToString(requested_lot, 2) +
              ", ResultOrder=" + TicketToText(result_order) +
              ", TimeoutSeconds=" + IntegerToString(timeout_seconds));
}

string TicketToText(ulong ticket)
{
   return IntegerToString((long)ticket);
}

string TradeDirectionText(int direction)
{
   if(direction == DIR_LONG) return "BUY";
   if(direction == DIR_SHORT) return "SELL";
   return "UNKNOWN";
}

bool IsNormalTradeSuccessResult(bool call_result, long retcode)
{
   if(!call_result) return false;
   if(retcode == TRADE_RETCODE_PLACED) return true;
   if(retcode == TRADE_RETCODE_DONE) return true;
   if(retcode == TRADE_RETCODE_DONE_PARTIAL) return true;
   return false;
}

bool IsPlausibleReconciledVolume(string symbol, double actual_lot, double requested_lot)
{
   double volume_step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double tolerance = 0.0000001;
   if(volume_step > 0) tolerance = volume_step * 0.5;

   double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);

   if(actual_lot <= 0) return false;
   if(min_lot > 0 && actual_lot < min_lot - tolerance) return false;
   if(max_lot > 0 && actual_lot > max_lot + tolerance) return false;
   if(actual_lot > requested_lot + tolerance) return false;
   return true;
}

bool IsExpectedPositionDirection(int direction, long position_type)
{
   if(direction == DIR_LONG) return position_type == POSITION_TYPE_BUY;
   if(direction == DIR_SHORT) return position_type == POSITION_TYPE_SELL;
   return false;
}

bool IsExpectedDealDirection(int direction, long deal_type)
{
   if(direction == DIR_LONG) return deal_type == DEAL_TYPE_BUY;
   if(direction == DIR_SHORT) return deal_type == DEAL_TYPE_SELL;
   return false;
}

bool IsMatchingEntryDeal(ulong ticket,
                         StrategyConfig &cfg,
                         int direction,
                         double requested_lot,
                         long minimum_time_msc,
                         ulong expected_order,
                         double &actual_lot)
{
   if(ticket == 0) return false;
   if(HistoryDealGetString(ticket, DEAL_SYMBOL) != cfg.symbol) return false;
   if(HistoryDealGetInteger(ticket, DEAL_MAGIC) != cfg.magic) return false;
   if(HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_IN) return false;
   if(!IsExpectedDealDirection(direction, HistoryDealGetInteger(ticket, DEAL_TYPE))) return false;
   if(expected_order != 0 && (ulong)HistoryDealGetInteger(ticket, DEAL_ORDER) != expected_order) return false;

   long deal_time_msc = HistoryDealGetInteger(ticket, DEAL_TIME_MSC);
   if(deal_time_msc < minimum_time_msc) return false;

   actual_lot = HistoryDealGetDouble(ticket, DEAL_VOLUME);
   return IsPlausibleReconciledVolume(cfg.symbol, actual_lot, requested_lot);
}

bool FindMatchingNewPosition(StrategyConfig &cfg,
                             int direction,
                             double requested_lot,
                             long minimum_time_msc,
                             ulong &position_ticket,
                             double &actual_lot)
{
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL) != cfg.symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != cfg.magic) continue;
      if(!IsExpectedPositionDirection(direction, PositionGetInteger(POSITION_TYPE))) continue;

      long position_time_msc = PositionGetInteger(POSITION_TIME_MSC);
      if(position_time_msc < minimum_time_msc) continue;

      double position_lot = PositionGetDouble(POSITION_VOLUME);
      if(!IsPlausibleReconciledVolume(cfg.symbol, position_lot, requested_lot)) continue;

      position_ticket = ticket;
      actual_lot = position_lot;
      return true;
   }

   return false;
}

bool FindMatchingNewDeal(StrategyConfig &cfg,
                         int direction,
                         double requested_lot,
                         long minimum_time_msc,
                         ulong previous_deal_ticket,
                         ulong result_order,
                         ulong result_deal,
                         ulong &confirmed_deal_ticket,
                         double &actual_lot)
{
   if(result_deal != 0 && result_deal != previous_deal_ticket)
   {
      if(HistoryDealSelect(result_deal) &&
         IsMatchingEntryDeal(result_deal, cfg, direction, requested_lot, minimum_time_msc, result_order, actual_lot))
      {
         confirmed_deal_ticket = result_deal;
         return true;
      }
   }

   datetime history_from = (datetime)(minimum_time_msc / 1000 - 5);
   datetime history_to = TimeTradeServer();
   if(history_to <= 0) history_to = TimeCurrent();

   if(!HistorySelect(history_from, history_to + 5)) return false;

   int total = HistoryDealsTotal();
   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0 || ticket == previous_deal_ticket) continue;
      if(!IsMatchingEntryDeal(ticket, cfg, direction, requested_lot, minimum_time_msc, result_order, actual_lot)) continue;

      confirmed_deal_ticket = ticket;
      return true;
   }

   return false;
}

bool ReconcileExecutedEntry(StrategyConfig &cfg,
                            int direction,
                            double requested_lot,
                            long request_time_msc,
                            ulong previous_deal_ticket,
                            ulong result_order,
                            ulong result_deal,
                            string &evidence_source,
                            ulong &evidence_ticket,
                            double &actual_lot)
{
   // Allow a small clock-resolution margin while still excluding old positions/deals.
   long minimum_time_msc = request_time_msc - 2000;

   if(FindMatchingNewPosition(cfg, direction, requested_lot, minimum_time_msc, evidence_ticket, actual_lot))
   {
      evidence_source = "POSITION";
      return true;
   }

   if(FindMatchingNewDeal(cfg,
                          direction,
                          requested_lot,
                          minimum_time_msc,
                          previous_deal_ticket,
                          result_order,
                          result_deal,
                          evidence_ticket,
                          actual_lot))
   {
      evidence_source = "DEAL";
      return true;
   }

   return false;
}

bool ConfirmPendingEntryFromDeal(int strategy_index, ulong deal_ticket)
{
   if(strategy_index < 0 || strategy_index >= ArraySize(pending_entry_reconciliations)) return false;
   if(!pending_entry_reconciliations[strategy_index].active) return false;

   PendingEntryReconciliation pending = pending_entry_reconciliations[strategy_index];
   if(!HistoryDealSelect(deal_ticket)) return false;

   double actual_lot = 0.0;
   long minimum_time_msc = pending.request_time_msc - 2000;
   if(!IsMatchingEntryDeal(deal_ticket,
                           strategies[strategy_index],
                           pending.direction,
                           pending.requested_lot,
                           minimum_time_msc,
                           pending.result_order,
                           actual_lot))
      return false;

   ClearPendingEntryReconciliation(strategy_index);
   MarkEnteredToday(strategies[strategy_index], pending.entry_jst_time);
   PrintReconciledEntrySuccess(strategies[strategy_index],
                               pending.direction,
                               pending.requested_lot,
                               "DEAL_ADD",
                               deal_ticket,
                               actual_lot);
   return true;
}

void ProcessPendingEntryReconciliations()
{
   EnsurePendingEntryReconciliationArray();
   ulong now_tick_msc = GetTickCount64();

   for(int i = 0; i < ArraySize(pending_entry_reconciliations); i++)
   {
      if(!pending_entry_reconciliations[i].active) continue;

      PendingEntryReconciliation pending = pending_entry_reconciliations[i];
      string evidence_source = "";
      ulong evidence_ticket = 0;
      double actual_lot = 0.0;
      if(ReconcileExecutedEntry(strategies[i],
                                pending.direction,
                                pending.requested_lot,
                                pending.request_time_msc,
                                pending.previous_deal_ticket,
                                pending.result_order,
                                pending.result_deal,
                                evidence_source,
                                evidence_ticket,
                                actual_lot))
      {
         ClearPendingEntryReconciliation(i);
         MarkEnteredToday(strategies[i], pending.entry_jst_time);
         PrintReconciledEntrySuccess(strategies[i],
                                     pending.direction,
                                     pending.requested_lot,
                                     evidence_source,
                                     evidence_ticket,
                                     actual_lot);
         continue;
      }

      if(now_tick_msc < pending.deadline_tick_msc) continue;

      ClearPendingEntryReconciliation(i);
      PrintDebug(strategies[i].strategy_name,
                 TradeDirectionText(pending.direction) +
                 " entry failed. Symbol=" + strategies[i].symbol +
                 ", Retcode=" + IntegerToString(pending.retcode) +
                 ", " + pending.retcode_description +
                 ", Reconcile=timeout_no_matching_position_or_deal" +
                 ", ResultOrder=" + TicketToText(pending.result_order));
   }
}

void ResetPendingExitReconciliation(int index)
{
   if(index < 0 || index >= ArraySize(pending_exit_reconciliations)) return;
   pending_exit_reconciliations[index].active=false;
   pending_exit_reconciliations[index].strategy_index=-1;
   pending_exit_reconciliations[index].position_ticket=0;
   pending_exit_reconciliations[index].position_identifier=0;
   pending_exit_reconciliations[index].close_direction=0;
   pending_exit_reconciliations[index].requested_lot=0.0;
   pending_exit_reconciliations[index].request_time_msc=0;
   pending_exit_reconciliations[index].result_order=0;
   pending_exit_reconciliations[index].result_deal=0;
   pending_exit_reconciliations[index].deadline_tick_msc=0;
   pending_exit_reconciliations[index].retcode=0;
   pending_exit_reconciliations[index].retcode_description="";
   pending_exit_reconciliations[index].last_error=0;
}

int FindPendingExitByPositionTicket(ulong ticket)
{
   for(int i=0;i<ArraySize(pending_exit_reconciliations);i++)
      if(pending_exit_reconciliations[i].active &&
         pending_exit_reconciliations[i].position_ticket==ticket) return i;
   return -1;
}

bool HasPendingExitReconciliation(ulong ticket)
{ return FindPendingExitByPositionTicket(ticket)>=0; }

int AllocatePendingExitReconciliation()
{
   for(int i=0;i<ArraySize(pending_exit_reconciliations);i++)
      if(!pending_exit_reconciliations[i].active)
      { ResetPendingExitReconciliation(i); return i; }
   int index=ArraySize(pending_exit_reconciliations);
   ArrayResize(pending_exit_reconciliations,index+1);
   ResetPendingExitReconciliation(index);
   return index;
}

bool IsExactReconciledVolume(string symbol,double actual_lot,double requested_lot)
{
   double step=SymbolInfoDouble(symbol,SYMBOL_VOLUME_STEP);
   double tolerance=(step>0 ? step*0.5 : 0.0000001);
   return actual_lot>0 && MathAbs(actual_lot-requested_lot)<=tolerance;
}

bool IsMatchingExitDeal(ulong deal_ticket,PendingExitReconciliation &pending,
                        StrategyConfig &cfg,double &actual_lot)
{
   if(deal_ticket==0 || !HistoryDealSelect(deal_ticket)) return false;
   if(HistoryDealGetString(deal_ticket,DEAL_SYMBOL)!=cfg.symbol) return false;
   if(HistoryDealGetInteger(deal_ticket,DEAL_MAGIC)!=cfg.magic) return false;
   long entry=HistoryDealGetInteger(deal_ticket,DEAL_ENTRY);
   if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY) return false;
   if(!IsExpectedDealDirection(pending.close_direction,
                               HistoryDealGetInteger(deal_ticket,DEAL_TYPE))) return false;
   ulong position_id=(ulong)HistoryDealGetInteger(deal_ticket,DEAL_POSITION_ID);
   if(pending.position_identifier==0 || position_id!=pending.position_identifier) return false;
   if(pending.result_order!=0 &&
      (ulong)HistoryDealGetInteger(deal_ticket,DEAL_ORDER)!=pending.result_order) return false;
   if(HistoryDealGetInteger(deal_ticket,DEAL_TIME_MSC)<pending.request_time_msc-2000) return false;
   actual_lot=HistoryDealGetDouble(deal_ticket,DEAL_VOLUME);
   return IsExactReconciledVolume(cfg.symbol,actual_lot,pending.requested_lot);
}

bool FindMatchingExitDeal(PendingExitReconciliation &pending,StrategyConfig &cfg,
                          ulong &deal_ticket,double &actual_lot)
{
   if(pending.result_deal!=0 &&
      IsMatchingExitDeal(pending.result_deal,pending,cfg,actual_lot))
   { deal_ticket=pending.result_deal; return true; }
   datetime from=(datetime)(pending.request_time_msc/1000-5);
   datetime to=TimeTradeServer(); if(to<=0) to=TimeCurrent();
   if(!HistorySelect(from,to+5)) return false;
   ulong candidate_tickets[];
   int total=HistoryDealsTotal();
   ArrayResize(candidate_tickets,total);
   for(int i=0;i<total;i++)
      candidate_tickets[i]=HistoryDealGetTicket(i);
   for(int i=total-1;i>=0;i--)
   {
      ulong ticket=candidate_tickets[i];
      if(ticket!=0 && IsMatchingExitDeal(ticket,pending,cfg,actual_lot))
      { deal_ticket=ticket; return true; }
   }
   return false;
}

bool ReconcileExecutedExit(PendingExitReconciliation &pending,StrategyConfig &cfg,
                           string &source,ulong &ticket,double &actual_lot)
{
   if(!PositionSelectByTicket(pending.position_ticket))
   { source="POSITION_GONE"; ticket=pending.position_ticket; actual_lot=pending.requested_lot; return true; }
   if(PositionGetString(POSITION_SYMBOL)!=cfg.symbol ||
      PositionGetInteger(POSITION_MAGIC)!=cfg.magic ||
      (ulong)PositionGetInteger(POSITION_IDENTIFIER)!=pending.position_identifier) return false;
   if(FindMatchingExitDeal(pending,cfg,ticket,actual_lot))
   { source="DEAL"; return true; }
   return false;
}

void PrintReconciledExitSuccess(StrategyConfig &cfg,PendingExitReconciliation &pending,
                                string source,ulong ticket,double actual_lot)
{
   P5Emit(cfg,"EXIT_RECONCILED","ReconciliationStatus="+source+"|PositionId="+TicketToText(pending.position_identifier)+"|EvidenceTicket="+TicketToText(ticket));
   PrintDebug(cfg.strategy_name,
      "Time exit reconciled success. Symbol="+cfg.symbol+
      ", Magic="+IntegerToString(cfg.magic)+
      ", PositionTicket="+TicketToText(pending.position_ticket)+
      ", PositionIdentifier="+TicketToText(pending.position_identifier)+
      ", CloseDirection="+TradeDirectionText(pending.close_direction)+
      ", RequestedLot="+DoubleToString(pending.requested_lot,2)+
      ", ActualLot="+DoubleToString(actual_lot,2)+
      ", Evidence="+source+", EvidenceTicket="+TicketToText(ticket));
}

void StartPendingExitReconciliation(PendingExitReconciliation &pending,StrategyConfig &cfg)
{
   int index=AllocatePendingExitReconciliation();
   int seconds=InpTradeReconcileTimeoutSeconds; if(seconds<1) seconds=1;
   pending.active=true;
   pending.deadline_tick_msc=GetTickCount64()+(ulong)seconds*1000;
   pending_exit_reconciliations[index]=pending;
   PrintDebug(cfg.strategy_name,
      "Time exit reconciliation pending. Symbol="+cfg.symbol+
      ", Magic="+IntegerToString(cfg.magic)+
      ", PositionTicket="+TicketToText(pending.position_ticket)+
      ", PositionIdentifier="+TicketToText(pending.position_identifier)+
      ", ResultOrder="+TicketToText(pending.result_order)+
      ", TimeoutSeconds="+IntegerToString(seconds));
}

bool ConfirmPendingExitFromDeal(ulong deal_ticket)
{
   for(int i=0;i<ArraySize(pending_exit_reconciliations);i++)
   {
      if(!pending_exit_reconciliations[i].active) continue;
      PendingExitReconciliation pending=pending_exit_reconciliations[i];
      int s=pending.strategy_index;
      if(s<0 || s>=ArraySize(strategies)) continue;
      double lot=0.0;
      if(!IsMatchingExitDeal(deal_ticket,pending,strategies[s],lot)) continue;
      ResetPendingExitReconciliation(i);
      PrintReconciledExitSuccess(strategies[s],pending,"DEAL_ADD",deal_ticket,lot);
      return true;
   }
   return false;
}

void ProcessPendingExitReconciliations()
{
   ulong now=GetTickCount64();
   for(int i=0;i<ArraySize(pending_exit_reconciliations);i++)
   {
      if(!pending_exit_reconciliations[i].active) continue;
      PendingExitReconciliation pending=pending_exit_reconciliations[i];
      int s=pending.strategy_index;
      if(s<0 || s>=ArraySize(strategies))
      { ResetPendingExitReconciliation(i); continue; }
      string source=""; ulong ticket=0; double lot=0.0;
      if(ReconcileExecutedExit(pending,strategies[s],source,ticket,lot))
      {
         ResetPendingExitReconciliation(i);
         PrintReconciledExitSuccess(strategies[s],pending,source,ticket,lot);
         continue;
      }
      if(now<pending.deadline_tick_msc) continue;
      bool still_open=PositionSelectByTicket(pending.position_ticket) &&
         PositionGetString(POSITION_SYMBOL)==strategies[s].symbol &&
         PositionGetInteger(POSITION_MAGIC)==strategies[s].magic &&
         (ulong)PositionGetInteger(POSITION_IDENTIFIER)==pending.position_identifier;
      if(!still_open)
      {
         ResetPendingExitReconciliation(i);
         PrintReconciledExitSuccess(strategies[s],pending,"POSITION_GONE_AT_TIMEOUT",
                                    pending.position_ticket,pending.requested_lot);
         continue;
      }
      ResetPendingExitReconciliation(i);
      PrintDebug(strategies[s].strategy_name,
         "Time exit failed. Symbol="+strategies[s].symbol+
         ", Ticket="+TicketToText(pending.position_ticket)+
         ", Retcode="+IntegerToString(pending.retcode)+", "+pending.retcode_description+
         ", Reconcile=timeout_position_still_open"+
         ", ResultOrder="+TicketToText(pending.result_order)+
         ", ResultDeal="+TicketToText(pending.result_deal)+
         ", GetLastError="+IntegerToString(pending.last_error));
   }
}

void PrintReconciledEntrySuccess(StrategyConfig &cfg,
                                 int direction,
                                 double requested_lot,
                                 string evidence_source,
                                 ulong evidence_ticket,
                                 double actual_lot)
{
   P5Emit(cfg,"ENTRY_RECONCILED","ReconciliationStatus="+evidence_source+"|EvidenceTicket="+TicketToText(evidence_ticket));
   PrintDebug(
      cfg.strategy_name,
      TradeDirectionText(direction) +
      " entry reconciled success. Symbol=" + cfg.symbol +
      ", Magic=" + IntegerToString(cfg.magic) +
      ", RequestedLot=" + DoubleToString(requested_lot, 2) +
      ", ActualLot=" + DoubleToString(actual_lot, 2) +
      ", Evidence=" + evidence_source +
      ", Ticket=" + TicketToText(evidence_ticket)
   );
}

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(!P5Guard()) return;
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD || trans.deal == 0) return;
   if(!HistoryDealSelect(trans.deal)) return;

   int p5s=FindStrategyIndexByMagicAndSymbol(HistoryDealGetInteger(trans.deal,DEAL_MAGIC),HistoryDealGetString(trans.deal,DEAL_SYMBOL));
   if(p5s>=0) P5Emit(strategies[p5s],"DEAL_ADD","DealTicket="+TicketToText(trans.deal)+"|PositionId="+TicketToText((ulong)HistoryDealGetInteger(trans.deal,DEAL_POSITION_ID))+"|DealEntry="+IntegerToString(HistoryDealGetInteger(trans.deal,DEAL_ENTRY)));
   ConfirmPendingExitFromDeal(trans.deal);

   string symbol = HistoryDealGetString(trans.deal, DEAL_SYMBOL);
   long magic = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
   int strategy_index = FindStrategyIndexByMagicAndSymbol(magic, symbol);
   if(strategy_index < 0 || !HasPendingEntryReconciliation(strategy_index)) return;

   ConfirmPendingEntryFromDeal(strategy_index, trans.deal);
}

void OnTick()
{
   if(!P5Guard() || P5Now()<=0) return;
   ProcessPendingEntryReconciliations();
   ProcessPendingExitReconciliations();
   RunStrategies();
}

void OnTimer()
{
   if(!P5Guard() || P5Now()<=0) return;
   ProcessPendingEntryReconciliations();
   ProcessPendingExitReconciliations();
   RunStrategies();
}
