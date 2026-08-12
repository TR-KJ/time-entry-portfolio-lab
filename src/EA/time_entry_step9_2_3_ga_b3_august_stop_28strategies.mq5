//+------------------------------------------------------------------+
//| time_entry_step9_2_3_ga_b3_august_stop_28strategies.mq5         |
//| Time Entry Portfolio Lab                                         |
//| Step 9.2.3: Step 9.2.2 plus 21_GA_B3 August entry stop           |
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

// Keep the proven Step 9.2.1 body and override only the functions that need changed behavior.
#define OnTick OnTick_Base_Step921
#define OnTimer OnTimer_Base_Step921
#define RunStrategies RunStrategies_Base_Step921
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
#undef RunStrategies
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
   bool result = trade.Buy(lot, cfg.symbol, ask, sl, tp, comment);
   if(result)
   {
      MarkEnteredToday(cfg, jst_time);
      if(tp > 0) PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
      else PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
      return true;
   }
   int retcode = (int)trade.ResultRetcode();
   string desc = trade.ResultRetcodeDescription();
   PrintDebug(cfg.strategy_name, "BUY entry failed. Symbol=" + cfg.symbol + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
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
   bool result = trade.Sell(lot, cfg.symbol, bid, sl, tp, comment);
   if(result)
   {
      MarkEnteredToday(cfg, jst_time);
      if(tp > 0) PrintDebug(cfg.strategy_name, "SELL entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
      else PrintDebug(cfg.strategy_name, "SELL entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
      return true;
   }
   int retcode = (int)trade.ResultRetcode();
   string desc = trade.ResultRetcodeDescription();
   PrintDebug(cfg.strategy_name, "SELL entry failed. Symbol=" + cfg.symbol + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
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

void OnTick()
{
   RunStrategies();
}

void OnTimer()
{
   RunStrategies();
}
