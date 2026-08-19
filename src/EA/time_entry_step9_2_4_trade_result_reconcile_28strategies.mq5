//+------------------------------------------------------------------+
//| time_entry_step9_2_4_trade_result_reconcile_28strategies.mq5    |
//| Time Entry Portfolio Lab                                         |
//| Step 9.2.4: Step 9.2.3 plus trade-result reconciliation          |
//+------------------------------------------------------------------+
#property strict

// Step 9.2.2 input additions for 1_EJ_Log1 position_overlap.
input int InpNfpEventHourJST = 21;
input int InpNfpEventMinuteJST = 30;
input int InpNfpPreMinutes = 120;
input int InpNfpPostMinutes = 120;
input int InpBojEventHourJST = 12;
input int InpBojEventMinuteJST = 0;
input int InpBojPreMinutes = 180;
input int InpBojPostMinutes = 180;

// Step 9.2.4 trade-result diagnostics.
input bool InpPrintTradeResultDiagnostics = true;
input int InpTradeReconcileTimeoutSeconds = 10;

// Keep the proven Step 9.2.1 body and override only the functions that need changed behavior.
#define OnTick OnTick_Base_Step921
#define OnTimer OnTimer_Base_Step921
#define OnTradeTransaction OnTradeTransaction_Base_Step921
#define RunStrategies RunStrategies_Base_Step921
#define TryExit TryExit_Base_Step921
#define ClosePositionsByConfig ClosePositionsByConfig_Base_Step921
#define TryEntry TryEntry_Base_Step921
#define IsEntryTime IsEntryTime_Base_Step921
#define PassEntryFilters PassEntryFilters_Base_Step921
#define GetUJ12TradeMode GetUJ12TradeMode_Base_Step921
#define UJ12ModeText UJ12ModeText_Base_Step921
#define GetUJ12EntryHour GetUJ12EntryHour_Base_Step921
#define GetUJ12EntryMinute GetUJ12EntryMinute_Base_Step921
#define GetUJ12SLPips GetUJ12SLPips_Base_Step921
#define GetUJ12TPPips GetUJ12TPPips_Base_Step921
#define GetStrategyEntryHour GetStrategyEntryHour_Base_Step921
#define GetStrategyEntryMinute GetStrategyEntryMinute_Base_Step921
#define GetStrategySLPips GetStrategySLPips_Base_Step921
#define GetStrategyTPPips GetStrategyTPPips_Base_Step921
#define GetStrategyComment GetStrategyComment_Base_Step921
#define GetExtraLogText GetExtraLogText_Base_Step921
#define GetStrategyLot GetStrategyLot_Base_Step921
#define SendBuyOrder SendBuyOrder_Base_Step921
#define SendSellOrder SendSellOrder_Base_Step921

#include "time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5"

#undef OnTick
#undef OnTimer
#undef OnTradeTransaction
#undef RunStrategies
#undef TryExit
#undef ClosePositionsByConfig
#undef TryEntry
#undef IsEntryTime
#undef PassEntryFilters
#undef GetUJ12TradeMode
#undef UJ12ModeText
#undef GetUJ12EntryHour
#undef GetUJ12EntryMinute
#undef GetUJ12SLPips
#undef GetUJ12TPPips
#undef GetStrategyEntryHour
#undef GetStrategyEntryMinute
#undef GetStrategySLPips
#undef GetStrategyTPPips
#undef GetStrategyComment
#undef GetExtraLogText
#undef GetStrategyLot
#undef SendBuyOrder
#undef SendSellOrder

//+------------------------------------------------------------------+
//| Step 9.2.2 UJ12 forward gotobi logic                             |
//+------------------------------------------------------------------+
bool IsUJ12ForwardGotobi(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   // Forward gotobi is only considered on Friday.
   if(dt.day_of_week != 5)
   {
      return false;
   }

   // The 20th is intentionally not forward-shifted.
   // Only 25th and 30th on Saturday/Sunday are shifted to the previous Friday.
   datetime next_day = jst_time + 86400;
   MqlDateTime d1;
   TimeToStruct(next_day, d1);
   if(d1.day == 25 || d1.day == 30)
   {
      return true;
   }

   datetime day_after_next = jst_time + 86400 * 2;
   MqlDateTime d2;
   TimeToStruct(day_after_next, d2);
   if(d2.day == 25 || d2.day == 30)
   {
      return true;
   }

   return false;
}

int GetUJ12TradeMode(datetime jst_time)
{
   if(InpUJ12ForceGotoMode && InpUJ12ForceNormalMode) return UJ_MODE_INVALID;
   if(InpUJ12ForceGotoMode) return UJ_MODE_GOTO;
   if(InpUJ12ForceNormalMode) return UJ_MODE_NORMAL;

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(IsUJGotoDay(dt.day)) return UJ_MODE_GOTO;
   if(IsUJ12ForwardGotobi(jst_time)) return UJ_MODE_GOTO;

   return UJ_MODE_NORMAL;
}

string UJ12ModeText(datetime jst_time)
{
   int mode = GetUJ12TradeMode(jst_time);
   if(mode == UJ_MODE_GOTO) return "GOTO";
   if(mode == UJ_MODE_NORMAL) return "NORMAL";
   return "INVALID";
}

int GetUJ12EntryHour(datetime jst_time)
{
   if(GetUJ12TradeMode(jst_time) == UJ_MODE_GOTO) return 9;
   return 8;
}

int GetUJ12EntryMinute(datetime jst_time)
{
   if(GetUJ12TradeMode(jst_time) == UJ_MODE_GOTO) return 55;
   return 4;
}

double GetUJ12SLPips(datetime jst_time)
{
   if(GetUJ12TradeMode(jst_time) == UJ_MODE_GOTO) return 20.0;
   return 50.0;
}

double GetUJ12TPPips(datetime jst_time)
{
   if(GetUJ12TradeMode(jst_time) == UJ_MODE_GOTO) return 50.0;
   return 0.0;
}

//+------------------------------------------------------------------+
//| Step 9.2.2 strategy dynamic fields                               |
//+------------------------------------------------------------------+
int GetStrategyEntryHour(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return GetUJ12EntryHour(jst_time);
   if(cfg.special_rule == RULE_NONE && InpTestMode && InpUseTestTimes) return InpTestEntryHourJST;
   return cfg.entry_hour;
}

int GetStrategyEntryMinute(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return GetUJ12EntryMinute(jst_time);
   if(cfg.special_rule == RULE_NONE && InpTestMode && InpUseTestTimes) return InpTestEntryMinuteJST;
   return cfg.entry_minute;
}

double GetStrategySLPips(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return GetUJ12SLPips(jst_time);
   return cfg.sl_pips;
}

double GetStrategyTPPips(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return GetUJ12TPPips(jst_time);
   return cfg.tp_pips;
}

string GetStrategyComment(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return cfg.comment + "_" + UJ12ModeText(jst_time);
   return cfg.comment;
}

string GetExtraLogText(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return ", Mode=" + UJ12ModeText(jst_time);
   return "";
}

//+------------------------------------------------------------------+
//| Step 9.2.2 lot / order helpers using updated UJ12 mode            |
//+------------------------------------------------------------------+
double GetStrategyLot(StrategyConfig &cfg, datetime jst_time)
{
   if(InpLotMode == 0)
   {
      double fixed_lot = NormalizeLot(cfg.symbol, InpFixedLot);
      PrintLotLog(cfg.strategy_name, "LOT FIXED. Symbol=" + cfg.symbol + ", Lot=" + DoubleToString(fixed_lot, 2));
      return fixed_lot;
   }

   if(InpLotMode != 1)
   {
      PrintLotLog(cfg.strategy_name, "LOT ERROR. Unknown InpLotMode=" + IntegerToString(InpLotMode));
      return 0.0;
   }

   double sl_pips = GetStrategySLPips(cfg, jst_time);

   if(sl_pips <= 0)
   {
      PrintLotLog(cfg.strategy_name, "LOT ERROR. Invalid SL pips. SL=" + DoubleToString(sl_pips, 1));
      return 0.0;
   }

   double weekly_base = GetWeeklyBaseAmount(jst_time);

   if(weekly_base <= 0)
   {
      PrintLotLog(cfg.strategy_name, "LOT ERROR. Invalid weekly base amount.");
      return 0.0;
   }

   double risk_amount = weekly_base * InpRiskPercentPerTrade / 100.0;

   if(risk_amount <= 0)
   {
      PrintLotLog(cfg.strategy_name, "LOT ERROR. Invalid risk amount.");
      return 0.0;
   }

   double pip_value_per_lot = GetPipValuePerLot(cfg.symbol);

   if(pip_value_per_lot <= 0)
   {
      PrintLotLog(cfg.strategy_name, "LOT ERROR. Invalid pip value per lot. Symbol=" + cfg.symbol);
      return 0.0;
   }

   double loss_per_lot = sl_pips * pip_value_per_lot;

   if(loss_per_lot <= 0)
   {
      PrintLotLog(cfg.strategy_name, "LOT ERROR. Invalid loss per lot.");
      return 0.0;
   }

   double raw_lot = risk_amount / loss_per_lot;
   double min_lot = SymbolInfoDouble(cfg.symbol, SYMBOL_VOLUME_MIN);

   if(raw_lot < min_lot && !InpAllowMinLotWhenBelowMinimum)
   {
      PrintLotLog(cfg.strategy_name, "LOT STOP. Raw lot below minimum. RawLot=" + DoubleToString(raw_lot, 4) + ", MinLot=" + DoubleToString(min_lot, 2));
      return 0.0;
   }

   double capped_lot = raw_lot;

   if(InpMaxAutoLot > 0 && capped_lot > InpMaxAutoLot)
   {
      capped_lot = InpMaxAutoLot;
   }

   double normalized_lot = NormalizeLot(cfg.symbol, capped_lot);

   PrintLotLog(
      cfg.strategy_name,
      "LOT CALC. Symbol=" + cfg.symbol +
      ", WeeklyBase=" + DoubleToString(weekly_base, 2) +
      ", RiskPercent=" + DoubleToString(InpRiskPercentPerTrade, 2) +
      ", RiskAmount=" + DoubleToString(risk_amount, 2) +
      ", SL=" + DoubleToString(sl_pips, 1) +
      ", PipValuePerLot=" + DoubleToString(pip_value_per_lot, 4) +
      ", RawLot=" + DoubleToString(raw_lot, 4) +
      ", Lot=" + DoubleToString(normalized_lot, 2)
   );

   return normalized_lot;
}

//+------------------------------------------------------------------+
//| Step 9.2.4 trade-result diagnostics and reconciliation           |
//+------------------------------------------------------------------+
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

PendingEntryReconciliation pending_entry_reconciliations[];

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

long CaptureTradeRequestTimeMsc(string symbol)
{
   MqlTick tick;
   if(SymbolInfoTick(symbol, tick) && tick.time_msc > 0)
   {
      return tick.time_msc;
   }

   datetime server_time = TimeTradeServer();
   if(server_time <= 0) server_time = TimeCurrent();
   return (long)server_time * 1000;
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

ulong CaptureLatestMatchingEntryDeal(StrategyConfig &cfg, int direction)
{
   datetime history_to = TimeTradeServer();
   if(history_to <= 0) history_to = TimeCurrent();
   datetime history_from = history_to - 86400 * 30;

   if(!HistorySelect(history_from, history_to + 1)) return 0;

   int total = HistoryDealsTotal();
   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0) continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != cfg.symbol) continue;
      if(HistoryDealGetInteger(ticket, DEAL_MAGIC) != cfg.magic) continue;
      if(HistoryDealGetInteger(ticket, DEAL_ENTRY) != DEAL_ENTRY_IN) continue;
      if(!IsExpectedDealDirection(direction, HistoryDealGetInteger(ticket, DEAL_TYPE))) continue;
      return ticket;
   }

   return 0;
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


struct PendingExitReconciliation
{
   bool active; int strategy_index; ulong position_ticket; ulong position_identifier;
   int close_direction; double requested_lot; long request_time_msc;
   ulong result_order; ulong result_deal; ulong deadline_tick_msc;
   long retcode; string retcode_description; int last_error;
};
PendingExitReconciliation pending_exit_reconciliations[];

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
void PrintExitTradeResultDiagnostic(StrategyConfig &cfg,
                                    PendingExitReconciliation &pending,bool result)
{
   if(!InpPrintTradeResultDiagnostics) return;
   Print("[Step9.2.4 Time Exit Result ",cfg.strategy_name,"] ",
      "Returned=",(result?"true":"false"),
      ", ResultRetcode=",IntegerToString(pending.retcode),
      ", ResultRetcodeDescription=",pending.retcode_description,
      ", ResultOrder=",TicketToText(pending.result_order),
      ", ResultDeal=",TicketToText(pending.result_deal),
      ", GetLastError=",IntegerToString(pending.last_error),
      ", PositionTicket=",TicketToText(pending.position_ticket),
      ", PositionIdentifier=",TicketToText(pending.position_identifier),
      ", Symbol=",cfg.symbol,", Magic=",IntegerToString(cfg.magic),
      ", CloseDirection=",TradeDirectionText(pending.close_direction),
      ", Lot=",DoubleToString(pending.requested_lot,2));
}
void PrintReconciledExitSuccess(StrategyConfig &cfg,PendingExitReconciliation &pending,
                                string source,ulong ticket,double actual_lot)
{
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
void ClosePositionsByConfig(StrategyConfig &cfg)
{
   int strategy_index=FindStrategyIndexByMagicAndSymbol(cfg.magic,cfg.symbol);
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong ticket=PositionGetTicket(i);
      if(ticket==0 || HasPendingExitReconciliation(ticket)) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=cfg.symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC)!=cfg.magic) continue;
      PendingExitReconciliation pending;
      pending.active=false; pending.strategy_index=strategy_index;
      pending.position_ticket=ticket;
      pending.position_identifier=(ulong)PositionGetInteger(POSITION_IDENTIFIER);
      long type=PositionGetInteger(POSITION_TYPE);
      pending.close_direction=(type==POSITION_TYPE_BUY ? DIR_SHORT : DIR_LONG);
      pending.requested_lot=PositionGetDouble(POSITION_VOLUME);
      pending.request_time_msc=CaptureTradeRequestTimeMsc(cfg.symbol);
      pending.result_order=0; pending.result_deal=0; pending.deadline_tick_msc=0;
      pending.retcode=0; pending.retcode_description=""; pending.last_error=0;
      trade.SetExpertMagicNumber(cfg.magic);
      trade.SetDeviationInPoints(InpSlippagePoints);
      ResetLastError();
      bool result=trade.PositionClose(ticket);
      pending.last_error=GetLastError();
      pending.retcode=(long)trade.ResultRetcode();
      pending.retcode_description=trade.ResultRetcodeDescription();
      pending.result_order=trade.ResultOrder();
      pending.result_deal=trade.ResultDeal();
      if(IsNormalTradeSuccessResult(result,pending.retcode))
      {
         PrintDebug(cfg.strategy_name,"Time exit success. Symbol="+cfg.symbol+
                    ", Ticket="+TicketToText(ticket));
         continue;
      }
      PrintExitTradeResultDiagnostic(cfg,pending,result);
      string source=""; ulong evidence=0; double lot=0.0;
      if(ReconcileExecutedExit(pending,cfg,source,evidence,lot))
      { PrintReconciledExitSuccess(cfg,pending,source,evidence,lot); continue; }
      StartPendingExitReconciliation(pending,cfg);
   }
}
void TryExit(StrategyConfig &cfg,datetime jst_time)
{
   if(!cfg.enabled) return;
   if(!IsExitTime(cfg,jst_time)) return;
   ClosePositionsByConfig(cfg);
}

void PrintTradeResultDiagnostic(StrategyConfig &cfg,
                                int direction,
                                double requested_lot,
                                bool call_result,
                                long retcode,
                                string retcode_description,
                                ulong result_order,
                                ulong result_deal,
                                int last_error)
{
   if(!InpPrintTradeResultDiagnostics) return;

   Print(
      "[Step9.2.4 Trade Result ", cfg.strategy_name, "] ",
      "Side=", TradeDirectionText(direction),
      ", Returned=", (call_result ? "true" : "false"),
      ", ResultRetcode=", IntegerToString(retcode),
      ", ResultRetcodeDescription=", retcode_description,
      ", ResultOrder=", TicketToText(result_order),
      ", ResultDeal=", TicketToText(result_deal),
      ", GetLastError=", IntegerToString(last_error),
      ", Symbol=", cfg.symbol,
      ", Magic=", IntegerToString(cfg.magic),
      ", Direction=", IntegerToString(direction),
      ", RequestedLot=", DoubleToString(requested_lot, 2)
   );
}

void PrintReconciledEntrySuccess(StrategyConfig &cfg,
                                 int direction,
                                 double requested_lot,
                                 string evidence_source,
                                 ulong evidence_ticket,
                                 double actual_lot)
{
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

bool SendBuyOrder(StrategyConfig &cfg, datetime jst_time)
{
   double ask = SymbolInfoDouble(cfg.symbol, SYMBOL_ASK);
   if(ask <= 0){ PrintDebug(cfg.strategy_name, "Skip entry: invalid ASK."); return false; }
   double lot = GetStrategyLot(cfg, jst_time);
   if(lot <= 0)
   {
      PrintDebug(cfg.strategy_name, "Skip entry: invalid lot.");
      return false;
   }
   double pip = GetPipSize(cfg.symbol);
   int digits = (int)SymbolInfoInteger(cfg.symbol, SYMBOL_DIGITS);
   double sl_pips = GetStrategySLPips(cfg, jst_time);
   double tp_pips = GetStrategyTPPips(cfg, jst_time);
   double sl = NormalizeDouble(ask - sl_pips * pip, digits);
   double tp = 0.0;
   if(tp_pips > 0) tp = NormalizeDouble(ask + tp_pips * pip, digits);
   trade.SetExpertMagicNumber(cfg.magic);
   trade.SetDeviationInPoints(InpSlippagePoints);
   string comment = GetStrategyComment(cfg, jst_time);
   string extra = GetExtraLogText(cfg, jst_time);

   long request_time_msc = CaptureTradeRequestTimeMsc(cfg.symbol);
   ulong previous_deal_ticket = CaptureLatestMatchingEntryDeal(cfg, DIR_LONG);
   ResetLastError();
   bool result = trade.Buy(lot, cfg.symbol, ask, sl, tp, comment);
   int last_error = GetLastError();
   long retcode = (long)trade.ResultRetcode();
   string desc = trade.ResultRetcodeDescription();
   ulong result_order = trade.ResultOrder();
   ulong result_deal = trade.ResultDeal();

   PrintTradeResultDiagnostic(cfg, DIR_LONG, lot, result, retcode, desc, result_order, result_deal, last_error);

   // Preserve the proven normal-success path for the documented success retcodes.
   if(IsNormalTradeSuccessResult(result, retcode))
   {
      MarkEnteredToday(cfg, jst_time);
      if(tp > 0) PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
      else PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
      return true;
   }

   string evidence_source = "";
   ulong evidence_ticket = 0;
   double actual_lot = 0.0;
   if(ReconcileExecutedEntry(cfg,
                             DIR_LONG,
                             lot,
                             request_time_msc,
                             previous_deal_ticket,
                             result_order,
                             result_deal,
                             evidence_source,
                             evidence_ticket,
                             actual_lot))
   {
      MarkEnteredToday(cfg, jst_time);
      PrintReconciledEntrySuccess(cfg, DIR_LONG, lot, evidence_source, evidence_ticket, actual_lot);
      return true;
   }

   StartPendingEntryReconciliation(cfg,
                                   DIR_LONG,
                                   lot,
                                   request_time_msc,
                                   previous_deal_ticket,
                                   result_order,
                                   result_deal,
                                   jst_time,
                                   retcode,
                                   desc);
   return false;
}

bool SendSellOrder(StrategyConfig &cfg, datetime jst_time)
{
   double bid = SymbolInfoDouble(cfg.symbol, SYMBOL_BID);
   if(bid <= 0){ PrintDebug(cfg.strategy_name, "Skip entry: invalid BID."); return false; }
   double lot = GetStrategyLot(cfg, jst_time);
   if(lot <= 0)
   {
      PrintDebug(cfg.strategy_name, "Skip entry: invalid lot.");
      return false;
   }
   double pip = GetPipSize(cfg.symbol);
   int digits = (int)SymbolInfoInteger(cfg.symbol, SYMBOL_DIGITS);
   double sl_pips = GetStrategySLPips(cfg, jst_time);
   double tp_pips = GetStrategyTPPips(cfg, jst_time);
   double sl = NormalizeDouble(bid + sl_pips * pip, digits);
   double tp = 0.0;
   if(tp_pips > 0) tp = NormalizeDouble(bid - tp_pips * pip, digits);
   trade.SetExpertMagicNumber(cfg.magic);
   trade.SetDeviationInPoints(InpSlippagePoints);
   string comment = GetStrategyComment(cfg, jst_time);
   string extra = GetExtraLogText(cfg, jst_time);

   long request_time_msc = CaptureTradeRequestTimeMsc(cfg.symbol);
   ulong previous_deal_ticket = CaptureLatestMatchingEntryDeal(cfg, DIR_SHORT);
   ResetLastError();
   bool result = trade.Sell(lot, cfg.symbol, bid, sl, tp, comment);
   int last_error = GetLastError();
   long retcode = (long)trade.ResultRetcode();
   string desc = trade.ResultRetcodeDescription();
   ulong result_order = trade.ResultOrder();
   ulong result_deal = trade.ResultDeal();

   PrintTradeResultDiagnostic(cfg, DIR_SHORT, lot, result, retcode, desc, result_order, result_deal, last_error);

   // Preserve the proven normal-success path for the documented success retcodes.
   if(IsNormalTradeSuccessResult(result, retcode))
   {
      MarkEnteredToday(cfg, jst_time);
      if(tp > 0) PrintDebug(cfg.strategy_name, "SELL entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
      else PrintDebug(cfg.strategy_name, "SELL entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
      return true;
   }

   string evidence_source = "";
   ulong evidence_ticket = 0;
   double actual_lot = 0.0;
   if(ReconcileExecutedEntry(cfg,
                             DIR_SHORT,
                             lot,
                             request_time_msc,
                             previous_deal_ticket,
                             result_order,
                             result_deal,
                             evidence_source,
                             evidence_ticket,
                             actual_lot))
   {
      MarkEnteredToday(cfg, jst_time);
      PrintReconciledEntrySuccess(cfg, DIR_SHORT, lot, evidence_source, evidence_ticket, actual_lot);
      return true;
   }

   StartPendingEntryReconciliation(cfg,
                                   DIR_SHORT,
                                   lot,
                                   request_time_msc,
                                   previous_deal_ticket,
                                   result_order,
                                   result_deal,
                                   jst_time,
                                   retcode,
                                   desc);
   return false;
}

//+------------------------------------------------------------------+
//| Step 9.2.2 event overlap additions                               |
//+------------------------------------------------------------------+
bool IsStep922EventDateKey(string event_name, int date_key)
{
   if(event_name == "FOMC") return InpStopOnFOMC && IsDateInList(date_key, FOMC_2026_DATES);
   if(event_name == "US_NFP") return InpStopOnUS_NFP && IsDateInList(date_key, US_NFP_2026_DATES);
   if(event_name == "BOJ") return InpStopOnBOJ && IsDateInList(date_key, BOJ_2026_DATES);
   if(event_name == "ECB") return InpStopOnECB && IsDateInList(date_key, ECB_2026_DATES);
   return false;
}

bool GetStep922EventTimeAndWindow(string event_name, int event_date_key, datetime &event_time_jst, int &pre_minutes, int &post_minutes)
{
   if(event_name == "FOMC")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpFomcEventHourJST, InpFomcEventMinuteJST);
      pre_minutes = InpFomcPreMinutes;
      post_minutes = InpFomcPostMinutes;
      return true;
   }

   if(event_name == "US_NFP")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpNfpEventHourJST, InpNfpEventMinuteJST);
      pre_minutes = InpNfpPreMinutes;
      post_minutes = InpNfpPostMinutes;
      return true;
   }

   if(event_name == "BOJ")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpBojEventHourJST, InpBojEventMinuteJST);
      pre_minutes = InpBojPreMinutes;
      post_minutes = InpBojPostMinutes;
      return true;
   }

   if(event_name == "ECB")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpEcbEventHourJST, InpEcbEventMinuteJST);
      pre_minutes = InpEcbPreMinutes;
      post_minutes = InpEcbPostMinutes;
      return true;
   }

   return false;
}

datetime BuildStep922PlannedEntryTime(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   dt.hour = GetStrategyEntryHour(cfg, jst_time);
   dt.min = GetStrategyEntryMinute(cfg, jst_time);
   dt.sec = 0;
   return StructToTime(dt);
}

datetime BuildStep922PlannedExitTime(StrategyConfig &cfg, datetime jst_time, datetime entry_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   dt.hour = GetStrategyExitHour(cfg);
   dt.min = GetStrategyExitMinute(cfg);
   dt.sec = 0;
   datetime exit_time = StructToTime(dt);

   if(exit_time <= entry_time)
   {
      exit_time = exit_time + 86400;
   }

   return exit_time;
}

bool DoesStep922PlannedPositionOverlapEventWindow(StrategyConfig &cfg, datetime jst_time, string event_name, int event_date_key, datetime &event_time_jst, int &pre_minutes, int &post_minutes)
{
   if(!GetStep922EventTimeAndWindow(event_name, event_date_key, event_time_jst, pre_minutes, post_minutes))
   {
      return false;
   }

   datetime entry_time = BuildStep922PlannedEntryTime(cfg, jst_time);
   datetime exit_time = BuildStep922PlannedExitTime(cfg, jst_time, entry_time);
   datetime window_start = event_time_jst - pre_minutes * 60;
   datetime window_end = event_time_jst + post_minutes * 60;

   if(entry_time < window_end && exit_time > window_start)
   {
      return true;
   }

   return false;
}

bool RejectStep922SpecialOverlapIfMatched(StrategyConfig &cfg, datetime jst_time, string event_name)
{
   int date_key = DateKey(jst_time);
   int next_key = DateKey(jst_time + 86400);
   datetime event_time_jst = 0;
   int pre_minutes = 0;
   int post_minutes = 0;

   if(IsStep922EventDateKey(event_name, date_key))
   {
      if(DoesStep922PlannedPositionOverlapEventWindow(cfg, jst_time, event_name, date_key, event_time_jst, pre_minutes, post_minutes))
      {
         PrintCandidateCOverlapStopLog(cfg, jst_time, event_name, event_time_jst, pre_minutes, post_minutes);
         return true;
      }
   }

   if(next_key != date_key && IsStep922EventDateKey(event_name, next_key))
   {
      if(DoesStep922PlannedPositionOverlapEventWindow(cfg, jst_time, event_name, next_key, event_time_jst, pre_minutes, post_minutes))
      {
         PrintCandidateCOverlapStopLog(cfg, jst_time, event_name, event_time_jst, pre_minutes, post_minutes);
         return true;
      }
   }

   return false;
}

bool RejectStep922SpecialOverlapEvents(StrategyConfig &cfg, datetime jst_time)
{
   // 1_EJ_Log1: FOMC / US_NFP / BOJ / ECB position_overlap.
   // US CPI remains handled by the existing US_CPI_WEEK_WED special stop.
   if(cfg.strategy_code == "1_EJ_Log1")
   {
      if(RejectStep922SpecialOverlapIfMatched(cfg, jst_time, "FOMC")) return true;
      if(RejectStep922SpecialOverlapIfMatched(cfg, jst_time, "US_NFP")) return true;
      if(RejectStep922SpecialOverlapIfMatched(cfg, jst_time, "BOJ")) return true;
      if(RejectStep922SpecialOverlapIfMatched(cfg, jst_time, "ECB")) return true;
      return false;
   }

   // 4_GJ_Port_Log1: FOMC position_overlap.
   if(cfg.strategy_code == "4_GJ_Port_Log1")
   {
      if(RejectStep922SpecialOverlapIfMatched(cfg, jst_time, "FOMC")) return true;
      return false;
   }

   // 16_UJ_T10A: FOMC position_overlap. BOJ date stop remains in the base event filter.
   if(cfg.strategy_code == "16_UJ_T10A")
   {
      if(RejectStep922SpecialOverlapIfMatched(cfg, jst_time, "FOMC")) return true;
      return false;
   }

   return false;
}

bool PassEntryFilters(StrategyConfig &cfg, datetime jst_time)
{
   // Step 9.2.3: only 21_GA_B3 is stopped for all August entries (JST).
   if(cfg.strategy_code == "21_GA_B3")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);
      if(dt.mon == 8)
      {
         PrintEventDecisionLog(cfg, jst_time, "GA_B3_AUG_STOP");
         return false;
      }
   }

   if(!PassGlobalAtrP70Filter(cfg, jst_time)) return false;
   if(!PassPythonCalendarEventFilter(cfg, jst_time)) return false;

   if(InpUseEventFilter && InpUseEventCandidateC)
   {
      if(RejectStep922SpecialOverlapEvents(cfg, jst_time)) return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Step 9.2.2 entry loop using updated dynamic fields                |
//+------------------------------------------------------------------+
bool IsEntryTime(StrategyConfig &cfg, datetime jst_time)
{
   if(!IsStrategyActiveDate(cfg, jst_time)) return false;
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      int mode = GetUJ12TradeMode(jst_time);
      if(mode == UJ_MODE_INVALID)
      {
         PrintDebug(cfg.strategy_name, "Invalid UJ12 mode: both force flags are true.");
         return false;
      }
   }
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   int entry_hour = GetStrategyEntryHour(cfg, jst_time);
   int entry_minute = GetStrategyEntryMinute(cfg, jst_time);
   if(dt.hour != entry_hour) return false;
   if(dt.min < entry_minute) return false;
   if(dt.min >= entry_minute + InpEntryWindowMinutes) return false;
   return true;
}

void TryEntry(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.enabled) return;
   if(!EnsureSymbolReady(cfg.symbol, cfg.strategy_name)) return;
   if(!IsEntryTime(cfg, jst_time)) return;
   if(!PassWeekendMarketClosedGuard(cfg, jst_time))
   {
      return;
   }
   if(InpEmergencyStop)
   {
      PrintEmergencyStopSkip(cfg, jst_time);
      return;
   }
   if(!PassEntryFilters(cfg, jst_time))
   {
      PrintSkip(cfg.strategy_name, "Skip entry: entry filter rejected.");
      return;
   }
   if(AlreadyEnteredToday(cfg, jst_time)){ PrintSkipOncePerDay(cfg, jst_time, "already_entered_today", "Skip entry: already entered today."); return; }
   int strategy_index = FindStrategyIndexByMagicAndSymbol(cfg.magic, cfg.symbol);
   if(HasPendingEntryReconciliation(strategy_index)){ PrintSkipOncePerDay(cfg, jst_time, "entry_reconciliation_pending", "Skip entry: entry reconciliation pending."); return; }
   if(HasOpenPosition(cfg.symbol, cfg.magic)){ PrintSkipOncePerDay(cfg, jst_time, "position_already_exists", "Skip entry: position already exists."); return; }
   if(cfg.direction == DIR_LONG){ SendBuyOrder(cfg, jst_time); return; }
   if(cfg.direction == DIR_SHORT){ SendSellOrder(cfg, jst_time); return; }
   PrintDebug(cfg.strategy_name, "Unknown direction. Direction=" + IntegerToString(cfg.direction));
}

void RunStrategies()
{
   datetime jst_time = GetJstTime();
   int strategy_count = ArraySize(strategies);
   for(int i = 0; i < strategy_count; i++) TryExit(strategies[i], jst_time);
   for(int i = 0; i < strategy_count; i++) TryEntry(strategies[i], jst_time);
}

void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD || trans.deal == 0) return;
   if(!HistoryDealSelect(trans.deal)) return;

   ConfirmPendingExitFromDeal(trans.deal);

   string symbol = HistoryDealGetString(trans.deal, DEAL_SYMBOL);
   long magic = HistoryDealGetInteger(trans.deal, DEAL_MAGIC);
   int strategy_index = FindStrategyIndexByMagicAndSymbol(magic, symbol);
   if(strategy_index < 0 || !HasPendingEntryReconciliation(strategy_index)) return;

   ConfirmPendingEntryFromDeal(strategy_index, trans.deal);
}

void OnTick()
{
   ProcessPendingEntryReconciliations();
   ProcessPendingExitReconciliations();
   RunStrategies();
}

void OnTimer()
{
   ProcessPendingEntryReconciliations();
   ProcessPendingExitReconciliations();
   RunStrategies();
}
