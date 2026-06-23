//+------------------------------------------------------------------+
//| time_entry_step8_config_managed_28strategies_forward_test_ready.mq5      |
//| Time Entry Portfolio Lab                                         |
//| Step 8.2: Forward test ready with emergency stop log fix   |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

input double InpFixedLot = 0.01;

// Emergency stop
// false = normal
// true  = block new entries only. Time exits remain active.
input bool   InpEmergencyStop = false;

// Lot mode
// 0 = Fixed Lot
// 1 = Weekly Compound Risk Lot
input int    InpLotMode = 0;
input bool   InpWeeklyBaseUseEquity = true;
input double InpRiskPercentPerTrade = 0.50;
input double InpMaxAutoLot = 1.00;
input bool   InpAllowMinLotWhenBelowMinimum = true;
input bool   InpPrintLotLogs = true;
input int    InpJstOffsetHours = 6;
input int    InpSlippagePoints = 30;
input int    InpEntryWindowMinutes = 2;

input bool   InpPrintDebug = true;
input bool   InpPrintSkipLogs = false;
input bool   InpPrintRuleRejectLogs = true;

input bool   InpTestMode = true;
input bool   InpTestModeIgnoreEntryWeekday = true;
input bool   InpTestModeIgnoreExitWeekday = true;

input bool   InpUseTestTimes = false;
input int    InpTestEntryHourJST = 12;
input int    InpTestEntryMinuteJST = 0;
input int    InpTestExitHourJST = 12;
input int    InpTestExitMinuteJST = 5;

input bool   InpUseMockJstDateTime = false;
input int    InpMockYear = 2026;
input int    InpMockMonth = 7;
input int    InpMockDay = 2;
input int    InpMockHour = 17;
input int    InpMockMinute = 14;

input bool   InpUJ12ForceGotoMode = false;
input bool   InpUJ12ForceNormalMode = false;

input bool            InpUseGlobalAtrP70Filter = true;
input ENUM_TIMEFRAMES InpAtrTimeframe = PERIOD_H1;
input int             InpAtrPeriod = 14;
input int             InpAtrP70LookbackBars = 500;
input double          InpAtrPercentile = 70.0;
input bool            InpAtrUseClosedBar = true;
input bool            InpPrintAtrFilterLogs = true;
input bool            InpSuppressAtrLogsOncePerDay = true;

input bool            InpUseEventFilter = true;
input bool            InpPrintEventFilterLogs = true;
input bool            InpSuppressEventLogsOncePerDay = true;
input bool            InpSuppressRuleRejectLogsOncePerDay = true;

input bool            InpStopOnUS_NFP = true;
input bool            InpStopOnUS_CPI = true;
input bool            InpStopOnFOMC = true;
input bool            InpStopOnBOJ = true;
input bool            InpStopOnBOE = true;
input bool            InpStopOnECB = true;
input bool            InpStopOnRBA = true;
input bool            InpStopOnAU_CPI = true;

input bool InpEnable_17_EA_1B = true;
input bool InpEnable_18_EA_2 = true;
input bool InpEnable_19_EA_3 = true;
input bool InpEnable_21_GA_B3 = true;
input bool InpEnable_22_GA_C2 = true;
input bool InpEnable_23_GA_F2 = true;
input bool InpEnable_24_GA_D1 = true;
input bool InpEnable_5_GJ_Log2 = true;
input bool InpEnable_12_UJ_Short_Core = true;
input bool InpEnable_13_UJ_Fix_MidWeek = true;
input bool InpEnable_14_UJ_Sat_3rd = true;
input bool InpEnable_15_UJ_Sat_Aug = true;
input bool InpEnable_16_UJ_T10A = true;
input bool InpEnable_1_EJ_Log1 = true;
input bool InpEnable_2_EJ_NightBlitz_20 = true;
input bool InpEnable_3_EJ_NightBlitz_21 = true;
input bool InpEnable_4_GJ_Port_Log1 = true;
input bool InpEnable_6_GJ_Old_Mon = true;
input bool InpEnable_7_GJ_Mon_Blitz = true;
input bool InpEnable_8_AJ_Core1 = true;
input bool InpEnable_10_AJ_SatA = true;
input bool InpEnable_11_AJ_SatB = true;
input bool InpEnable_20_EA_1A = true;
input bool InpEnable_25_AU_China_Demand = true;
input bool InpEnable_26_AJ_China_Demand = true;
input bool InpEnable_27_EA_China_Demand = true;
input bool InpEnable_28_GA_China_Demand = true;
input bool InpEnable_9_AJ_Core2 = true;

#define STRATEGY_COUNT 28
#define DIR_LONG 1
#define DIR_SHORT -1
#define RULE_NONE 0
#define RULE_AJ_CORE2 9
#define RULE_UJ_SHORT_CORE 12
#define RULE_UJ_FIX_MIDWEEK 13
#define RULE_UJ_SAT_3RD 14
#define RULE_UJ_SAT_AUG 15
#define RULE_UJ_T10A 16
#define RULE_CHINA_AU_DEMAND 25
#define RULE_CHINA_9_15 26
#define UJ_MODE_INVALID 0
#define UJ_MODE_GOTO 1
#define UJ_MODE_NORMAL 2


//+------------------------------------------------------------------+
//| 2026 Event Date Lists                                            |
//+------------------------------------------------------------------+
int FOMC_2026_DATES[] = {20260128,20260318,20260429,20260617,20260729,20260916,20261028,20261209};
int US_NFP_2026_DATES[] = {20260109,20260206,20260306,20260403,20260501,20260605,20260702,20260807,20260904,20261002,20261106,20261204};
int US_CPI_2026_DATES[] = {20260114,20260211,20260311,20260415,20260513,20260610,20260715,20260812,20260916,20261014,20261112,20261216};
int BOJ_2026_DATES[] = {20260123,20260319,20260428,20260616,20260731,20260918,20261030,20261218};
int BOE_2026_DATES[] = {20260205,20260319,20260430,20260618,20260730,20260917,20261105,20261217};
int ECB_2026_DATES[] = {20260205,20260319,20260430,20260611,20260723,20260910,20261029,20261217};
int RBA_2026_DATES[] = {20260203,20260317,20260505,20260616,20260804,20260922,20261103,20261208};
int AU_CPI_2026_DATES[] = {20260128,20260429,20260729,20261028};
int US_CPI_WED_2026_DATES[] = {20260114,20260211,20260311,20260415,20260513,20260610,20260715,20260812,20260916,20261014,20261111,20261216};

struct StrategyConfig
{
   bool enabled;
   string strategy_name;
   string strategy_code;
   string symbol;
   int magic;
   int direction;
   bool trade_sunday;
   bool trade_monday;
   bool trade_tuesday;
   bool trade_wednesday;
   bool trade_thursday;
   bool trade_friday;
   bool trade_saturday;
   int entry_hour;
   int entry_minute;
   int exit_hour;
   int exit_minute;
   double sl_pips;
   double tp_pips;
   bool one_entry_per_day;
   string comment;
   int special_rule;
};

StrategyConfig strategies[STRATEGY_COUNT];

// Runtime event-log suppression cache
string printed_event_log_keys[];
int printed_event_log_count = 0;

// Runtime date-rule reject log suppression cache
string printed_rule_reject_log_keys[];
int printed_rule_reject_log_count = 0;

// Runtime emergency-stop skip log suppression cache
string printed_emergency_stop_log_keys[];
int printed_emergency_stop_log_count = 0;

void PrintDebug(string strategy, string message)
{
   if(InpPrintDebug)
   {
      Print("[Step6.3 Stops ", strategy, "] ", message);
   }
}

void PrintSkip(string strategy, string message)
{
   if(InpPrintDebug && InpPrintSkipLogs)
   {
      Print("[Step6.3 Stops ", strategy, "] ", message);
   }
}

bool WasEmergencyStopLogPrintedRuntime(string log_key)
{
   for(int i = 0; i < printed_emergency_stop_log_count; i++)
   {
      if(printed_emergency_stop_log_keys[i] == log_key)
      {
         return true;
      }
   }

   return false;
}

void MarkEmergencyStopLogPrintedRuntime(string log_key)
{
   int new_size = printed_emergency_stop_log_count + 1;
   ArrayResize(printed_emergency_stop_log_keys, new_size);
   printed_emergency_stop_log_keys[printed_emergency_stop_log_count] = log_key;
   printed_emergency_stop_log_count = new_size;
}

void PrintEmergencyStopSkip(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpPrintDebug || !InpPrintSkipLogs)
   {
      return;
   }

   int key = DateKey(jst_time);
   string log_key = cfg.strategy_code + "|" + cfg.symbol + "|" + IntegerToString(cfg.magic) + "|" + IntegerToString(key) + "|EMERGENCY_STOP";

   if(WasEmergencyStopLogPrintedRuntime(log_key))
   {
      return;
   }

   MarkEmergencyStopLogPrintedRuntime(log_key);
   Print("[Step8 Forward ", cfg.strategy_name, "] Skip entry: emergency stop active.");
}

string RuleRejectReasonKey(string message)
{
   int pos = StringFind(message, ". JST=");

   if(pos >= 0)
   {
      return StringSubstr(message, 0, pos);
   }

   pos = StringFind(message, " JST=");

   if(pos >= 0)
   {
      return StringSubstr(message, 0, pos);
   }

   return message;
}

bool GetStrategyLogIdentity(string strategy, string &symbol, int &magic)
{
   int strategy_count = ArraySize(strategies);

   for(int i = 0; i < strategy_count; i++)
   {
      if(strategies[i].strategy_name == strategy)
      {
         symbol = strategies[i].symbol;
         magic = strategies[i].magic;
         return true;
      }
   }

   symbol = "NA";
   magic = 0;
   return false;
}

bool WasRuleRejectLogPrintedRuntime(string log_key)
{
   for(int i = 0; i < printed_rule_reject_log_count; i++)
   {
      if(printed_rule_reject_log_keys[i] == log_key)
      {
         return true;
      }
   }

   return false;
}

void MarkRuleRejectLogPrintedRuntime(string log_key)
{
   int new_size = printed_rule_reject_log_count + 1;
   ArrayResize(printed_rule_reject_log_keys, new_size);
   printed_rule_reject_log_keys[printed_rule_reject_log_count] = log_key;
   printed_rule_reject_log_count = new_size;
}

bool ShouldPrintRuleRejectLog(string strategy, string message)
{
   if(!InpPrintDebug)
   {
      return false;
   }

   if(!InpPrintRuleRejectLogs)
   {
      return false;
   }

   if(!InpSuppressRuleRejectLogsOncePerDay)
   {
      return true;
   }

   string symbol = "NA";
   int magic = 0;
   GetStrategyLogIdentity(strategy, symbol, magic);

   int key = DateKey(GetJstTime());
   string reason = RuleRejectReasonKey(message);
   string log_key = strategy + "|" + symbol + "|" + IntegerToString(magic) + "|" + IntegerToString(key) + "|" + reason;

   if(WasRuleRejectLogPrintedRuntime(log_key))
   {
      return false;
   }

   MarkRuleRejectLogPrintedRuntime(log_key);
   return true;
}

void PrintRuleReject(string strategy, string message)
{
   if(ShouldPrintRuleRejectLog(strategy, message))
   {
      Print("[Step6.3 Stops ", strategy, "] ", message);
   }
}

void PrintAtrLog(string strategy, string message)
{
   if(InpPrintDebug && InpPrintAtrFilterLogs)
   {
      Print("[Step6.3 Stops ", strategy, "] ", message);
   }
}

string BoolText(bool value)
{
   if(value)
   {
      return "true";
   }
   return "false";
}

string DateTimeText(datetime value)
{
   return TimeToString(value, TIME_DATE | TIME_MINUTES);
}

string TimeframeText(ENUM_TIMEFRAMES tf)
{
   if(tf == PERIOD_M1) return "M1";
   if(tf == PERIOD_M5) return "M5";
   if(tf == PERIOD_M15) return "M15";
   if(tf == PERIOD_M30) return "M30";
   if(tf == PERIOD_H1) return "H1";
   if(tf == PERIOD_H4) return "H4";
   if(tf == PERIOD_D1) return "D1";
   return IntegerToString((int)tf);
}

datetime BuildMockJstTime()
{
   MqlDateTime dt;
   dt.year = InpMockYear;
   dt.mon = InpMockMonth;
   dt.day = InpMockDay;
   dt.hour = InpMockHour;
   dt.min = InpMockMinute;
   dt.sec = 0;
   return StructToTime(dt);
}

datetime GetJstTime()
{
   if(InpUseMockJstDateTime)
   {
      return BuildMockJstTime();
   }
   datetime server_time = TimeTradeServer();
   if(server_time <= 0)
   {
      server_time = TimeCurrent();
   }
   return server_time + InpJstOffsetHours * 3600;
}

int DateKey(datetime value)
{
   MqlDateTime dt;
   TimeToStruct(value, dt);
   return dt.year * 10000 + dt.mon * 100 + dt.day;
}

string AtrLogGlobalVariableName(StrategyConfig &cfg, datetime jst_time)
{
   int key = DateKey(jst_time);
   string name = "TE_STEP4_3_ATRLOG_" + cfg.strategy_code + "_" + cfg.symbol + "_" + IntegerToString(cfg.magic) + "_" + IntegerToString(key);

   return name;
}

bool ShouldPrintAtrDecisionLog(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpPrintDebug)
   {
      return false;
   }

   if(!InpPrintAtrFilterLogs)
   {
      return false;
   }

   if(!InpSuppressAtrLogsOncePerDay)
   {
      return true;
   }

   string gv_name = AtrLogGlobalVariableName(cfg, jst_time);

   if(GlobalVariableCheck(gv_name))
   {
      return false;
   }

   GlobalVariableSet(gv_name, TimeTradeServer());

   return true;
}

void PrintAtrDecisionLog(StrategyConfig &cfg, datetime jst_time, string message)
{
   if(ShouldPrintAtrDecisionLog(cfg, jst_time))
   {
      Print("[Step6.3 Stops ", cfg.strategy_name, "] ", message);
   }
}


//+------------------------------------------------------------------+
//| Runtime log suppression helpers                                  |
//+------------------------------------------------------------------+
bool WasEventLogPrintedRuntime(string log_key)
{
   for(int i = 0; i < printed_event_log_count; i++)
   {
      if(printed_event_log_keys[i] == log_key)
      {
         return true;
      }
   }

   return false;
}

void MarkEventLogPrintedRuntime(string log_key)
{
   int new_size = printed_event_log_count + 1;
   ArrayResize(printed_event_log_keys, new_size);
   printed_event_log_keys[printed_event_log_count] = log_key;
   printed_event_log_count = new_size;
}

//+------------------------------------------------------------------+
//| Event filter logging                                             |
//+------------------------------------------------------------------+
string EventLogGlobalVariableName(StrategyConfig &cfg, datetime jst_time, string event_name)
{
   int key = DateKey(jst_time);
   string name = "TE_STEP5_EVENTLOG_" + cfg.strategy_code + "_" + cfg.symbol + "_" + IntegerToString(cfg.magic) + "_" + event_name + "_" + IntegerToString(key);

   return name;
}

bool ShouldPrintEventDecisionLog(StrategyConfig &cfg, datetime jst_time, string event_name)
{
   if(!InpPrintDebug)
   {
      return false;
   }

   if(!InpPrintEventFilterLogs)
   {
      return false;
   }

   if(!InpSuppressEventLogsOncePerDay)
   {
      return true;
   }

   string log_key = EventLogGlobalVariableName(cfg, jst_time, event_name);

   if(WasEventLogPrintedRuntime(log_key))
   {
      return false;
   }

   MarkEventLogPrintedRuntime(log_key);

   return true;
}

void PrintEventDecisionLog(StrategyConfig &cfg, datetime jst_time, string event_name)
{
   if(ShouldPrintEventDecisionLog(cfg, jst_time, event_name))
   {
      int key = DateKey(jst_time);
      Print("[Step6.3 Stops ", cfg.strategy_name, "] EVENT REJECT. Symbol=", cfg.symbol, ", Event=", event_name, ", Date=", IntegerToString(key));
   }
}

bool IsCalendarMonthEnd(MqlDateTime &dt)
{
   datetime current = StructToTime(dt);
   datetime tomorrow = current + 86400;
   MqlDateTime tm;
   TimeToStruct(tomorrow, tm);
   if(tm.mon != dt.mon)
   {
      return true;
   }
   return false;
}

bool IsWednesday(MqlDateTime &dt)
{
   return dt.day_of_week == 3;
}

bool IsThursday(MqlDateTime &dt)
{
   return dt.day_of_week == 4;
}

bool IsWeekday(MqlDateTime &dt)
{
   return dt.day_of_week >= 1 && dt.day_of_week <= 5;
}

bool EnsureSymbolReady(string symbol, string strategy)
{
   if(!SymbolSelect(symbol, true))
   {
      PrintDebug(strategy, "SymbolSelect failed. Symbol=" + symbol);
      return false;
   }
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(point <= 0)
   {
      PrintDebug(strategy, "Invalid symbol point. Symbol=" + symbol);
      return false;
   }
   return true;
}

double GetPipSize(string symbol)
{
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);
   if(digits == 3 || digits == 5)
   {
      return point * 10.0;
   }
   return point;
}

double ToPips(string symbol, double price_value)
{
   double pip = GetPipSize(symbol);
   if(pip <= 0)
   {
      return 0.0;
   }
   return price_value / pip;
}

double NormalizeLot(string symbol, double lot)
{
   double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   double result = lot;
   if(result < min_lot) result = min_lot;
   if(result > max_lot) result = max_lot;
   if(step_lot > 0) result = MathFloor(result / step_lot) * step_lot;
   return NormalizeDouble(result, 2);
}

int WeekStartDateKey(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int days_from_monday = dt.day_of_week - 1;

   if(days_from_monday < 0)
   {
      days_from_monday = 6;
   }

   datetime week_start = jst_time - days_from_monday * 86400;

   MqlDateTime ws;
   TimeToStruct(week_start, ws);
   ws.hour = 0;
   ws.min = 0;
   ws.sec = 0;

   return DateKey(StructToTime(ws));
}

string WeeklyBaseGlobalVariableName(int week_key)
{
   return "TE_STEP7_WEEKLY_BASE_" + IntegerToString(week_key);
}

double GetCurrentBaseAmount()
{
   if(InpWeeklyBaseUseEquity)
   {
      return AccountInfoDouble(ACCOUNT_EQUITY);
   }

   return AccountInfoDouble(ACCOUNT_BALANCE);
}

double GetWeeklyBaseAmount(datetime jst_time)
{
   int week_key = WeekStartDateKey(jst_time);
   string gv_name = WeeklyBaseGlobalVariableName(week_key);

   if(GlobalVariableCheck(gv_name))
   {
      return GlobalVariableGet(gv_name);
   }

   double base_amount = GetCurrentBaseAmount();

   if(base_amount <= 0)
   {
      base_amount = AccountInfoDouble(ACCOUNT_BALANCE);
   }

   if(base_amount > 0)
   {
      GlobalVariableSet(gv_name, base_amount);
   }

   return base_amount;
}

double GetPipValuePerLot(string symbol)
{
   double pip_size = GetPipSize(symbol);
   double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);

   if(pip_size <= 0)
   {
      return 0.0;
   }

   if(tick_value <= 0)
   {
      return 0.0;
   }

   if(tick_size <= 0)
   {
      return 0.0;
   }

   return tick_value * (pip_size / tick_size);
}

void PrintLotLog(string strategy, string message)
{
   if(InpPrintDebug && InpPrintLotLogs)
   {
      Print("[Step7 Lot ", strategy, "] ", message);
   }
}

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

bool HasOpenPosition(string symbol, int magic)
{
   int total = PositionsTotal();
   for(int i = 0; i < total; i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      string pos_symbol = PositionGetString(POSITION_SYMBOL);
      long pos_magic = PositionGetInteger(POSITION_MAGIC);
      if(pos_symbol == symbol && pos_magic == magic)
      {
         return true;
      }
   }
   return false;
}

string EntryGlobalVariableName(StrategyConfig &cfg, int date_key)
{
   return "TE_STEP4_3_" + cfg.strategy_code + "_" + cfg.symbol + "_" + IntegerToString(cfg.magic) + "_" + IntegerToString(date_key);
}

bool AlreadyEnteredToday(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.one_entry_per_day)
   {
      return false;
   }
   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(cfg, key);
   return GlobalVariableCheck(gv_name);
}

void MarkEnteredToday(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.one_entry_per_day)
   {
      return;
   }
   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(cfg, key);
   GlobalVariableSet(gv_name, TimeTradeServer());
}

void SetWeekdays(StrategyConfig &cfg, bool sunday, bool monday, bool tuesday, bool wednesday, bool thursday, bool friday, bool saturday)
{
   cfg.trade_sunday = sunday;
   cfg.trade_monday = monday;
   cfg.trade_tuesday = tuesday;
   cfg.trade_wednesday = wednesday;
   cfg.trade_thursday = thursday;
   cfg.trade_friday = friday;
   cfg.trade_saturday = saturday;
}

void SetStrategy(int index, bool enabled, string strategy_name, string strategy_code, string symbol, int magic, int direction, int entry_hour, int entry_minute, int exit_hour, int exit_minute, double sl_pips, double tp_pips, string comment, int special_rule)
{
   strategies[index].enabled = enabled;
   strategies[index].strategy_name = strategy_name;
   strategies[index].strategy_code = strategy_code;
   strategies[index].symbol = symbol;
   strategies[index].magic = magic;
   strategies[index].direction = direction;
   strategies[index].entry_hour = entry_hour;
   strategies[index].entry_minute = entry_minute;
   strategies[index].exit_hour = exit_hour;
   strategies[index].exit_minute = exit_minute;
   strategies[index].sl_pips = sl_pips;
   strategies[index].tp_pips = tp_pips;
   strategies[index].one_entry_per_day = true;
   strategies[index].comment = comment;
   strategies[index].special_rule = special_rule;
}

bool CalculatePercentile(double &values[], int count, double percentile, double &result)
{
   if(count <= 0) return false;
   if(percentile < 0.0) percentile = 0.0;
   if(percentile > 100.0) percentile = 100.0;
   ArrayResize(values, count);
   ArraySort(values);
   double ratio = percentile / 100.0;
   int index = (int)MathFloor((count - 1) * ratio);
   if(index < 0) index = 0;
   if(index >= count) index = count - 1;
   result = values[index];
   return true;
}

bool GetAtrP70Values(string symbol, double &current_atr, double &p70_value, int &copied_bars, string &error_message)
{
   current_atr = 0.0;
   p70_value = 0.0;
   copied_bars = 0;
   error_message = "";
   if(!EnsureSymbolReady(symbol, "ATR"))
   {
      error_message = "symbol not ready";
      return false;
   }
   int atr_handle = iATR(symbol, InpAtrTimeframe, InpAtrPeriod);
   if(atr_handle == INVALID_HANDLE)
   {
      error_message = "ATR handle create failed";
      return false;
   }
   int start_pos = InpAtrUseClosedBar ? 1 : 0;
   double current_buffer[];
   ArraySetAsSeries(current_buffer, true);
   ArrayResize(current_buffer, 1);
   int copied_current = CopyBuffer(atr_handle, 0, start_pos, 1, current_buffer);
   if(copied_current != 1)
   {
      IndicatorRelease(atr_handle);
      error_message = "CopyBuffer current ATR failed. Copied=" + IntegerToString(copied_current);
      return false;
   }
   current_atr = current_buffer[0];
   if(current_atr <= 0)
   {
      IndicatorRelease(atr_handle);
      error_message = "Invalid current ATR value";
      return false;
   }
   if(InpAtrP70LookbackBars <= 0)
   {
      IndicatorRelease(atr_handle);
      error_message = "Invalid P70 lookback";
      return false;
   }
   double atr_values[];
   ArraySetAsSeries(atr_values, true);
   ArrayResize(atr_values, InpAtrP70LookbackBars);
   int copied = CopyBuffer(atr_handle, 0, start_pos, InpAtrP70LookbackBars, atr_values);
   copied_bars = copied;
   IndicatorRelease(atr_handle);
   if(copied <= 0)
   {
      error_message = "CopyBuffer P70 ATR failed. Copied=" + IntegerToString(copied);
      return false;
   }
   if(copied < InpAtrP70LookbackBars)
   {
      error_message = "Not enough ATR bars. Requested=" + IntegerToString(InpAtrP70LookbackBars) + ", Copied=" + IntegerToString(copied);
      return false;
   }
   double sorted_values[];
   ArrayResize(sorted_values, copied);
   for(int i = 0; i < copied; i++)
   {
      sorted_values[i] = atr_values[i];
   }
   if(!CalculatePercentile(sorted_values, copied, InpAtrPercentile, p70_value))
   {
      error_message = "Percentile calculation failed";
      return false;
   }
   if(p70_value <= 0)
   {
      error_message = "Invalid P70 value";
      return false;
   }
   return true;
}

bool PassGlobalAtrP70Filter(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpUseGlobalAtrP70Filter)
   {
      return true;
   }
   double current_atr = 0.0;
   double p70_value = 0.0;
   int copied_bars = 0;
   string error_message = "";
   bool atr_ok = GetAtrP70Values(cfg.symbol, current_atr, p70_value, copied_bars, error_message);
   if(!atr_ok)
   {
      PrintAtrDecisionLog(cfg, jst_time, "ATR ERROR. Symbol=" + cfg.symbol + ", Reason=" + error_message);
      return false;
   }
   double atr_pips = ToPips(cfg.symbol, current_atr);
   double p70_pips = ToPips(cfg.symbol, p70_value);
   bool pass = current_atr >= p70_value;
   string msg = "Symbol=" + cfg.symbol + ", TF=" + TimeframeText(InpAtrTimeframe) + ", ATR_Pips=" + DoubleToString(atr_pips, 1) + ", P" + DoubleToString(InpAtrPercentile, 1) + "_Pips=" + DoubleToString(p70_pips, 1) + ", CopiedBars=" + IntegerToString(copied_bars);
   if(pass)
   {
      PrintAtrDecisionLog(cfg, jst_time, "ATR PASS. " + msg);
      return true;
   }
   PrintAtrDecisionLog(cfg, jst_time, "ATR REJECT. " + msg);
   return false;
}

bool IsUJGotoDay(int day)
{
   return day == 20 || day == 25 || day == 30;
}

bool IsUJ12ActiveDate(datetime jst_time, string strategy_name)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   if(dt.day < 20){ PrintRuleReject(strategy_name, "Date rule reject: before 20th. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.day == 21){ PrintRuleReject(strategy_name, "Date rule reject: 21st stop. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.day == 22){ PrintRuleReject(strategy_name, "Date rule reject: 22nd stop. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.mon == 8){ PrintRuleReject(strategy_name, "Date rule reject: August stop. JST=" + DateTimeText(jst_time)); return false; }
   if(IsWednesday(dt)){ PrintRuleReject(strategy_name, "Date rule reject: Wednesday stop. JST=" + DateTimeText(jst_time)); return false; }
   if(IsCalendarMonthEnd(dt)){ PrintRuleReject(strategy_name, "Date rule reject: calendar month end stop. JST=" + DateTimeText(jst_time)); return false; }
   return true;
}

int GetUJ12TradeMode(datetime jst_time)
{
   if(InpUJ12ForceGotoMode && InpUJ12ForceNormalMode) return UJ_MODE_INVALID;
   if(InpUJ12ForceGotoMode) return UJ_MODE_GOTO;
   if(InpUJ12ForceNormalMode) return UJ_MODE_NORMAL;
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   if(IsUJGotoDay(dt.day)) return UJ_MODE_GOTO;
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

bool IsChinaAUDemandActiveDate(datetime jst_time, string strategy_name)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   if(!IsWeekday(dt)){ PrintRuleReject(strategy_name, "Date rule reject: not weekday. JST=" + DateTimeText(jst_time)); return false; }
   if((dt.day >= 9 && dt.day <= 15) || dt.day >= 25) return true;
   PrintRuleReject(strategy_name, "Date rule reject: outside AU China date window. JST=" + DateTimeText(jst_time));
   return false;
}

bool IsChina915ActiveDate(datetime jst_time, string strategy_name)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   if(!IsWeekday(dt)){ PrintRuleReject(strategy_name, "Date rule reject: not weekday. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.day >= 9 && dt.day <= 15) return true;
   PrintRuleReject(strategy_name, "Date rule reject: outside 9-15 window. JST=" + DateTimeText(jst_time));
   return false;
}

bool IsAJCore2ActiveDate(datetime jst_time, string strategy_name)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   if(!IsThursday(dt)){ PrintRuleReject(strategy_name, "Date rule reject: not Thursday. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.mon == 6){ PrintRuleReject(strategy_name, "Date rule reject: June stop. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.mon == 9){ PrintRuleReject(strategy_name, "Date rule reject: September stop. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.day == 1){ PrintRuleReject(strategy_name, "Date rule reject: 1st stop. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.day == 20){ PrintRuleReject(strategy_name, "Date rule reject: 20th stop. JST=" + DateTimeText(jst_time)); return false; }
   if(dt.day >= 26){ PrintRuleReject(strategy_name, "Date rule reject: after 26th stop. JST=" + DateTimeText(jst_time)); return false; }
   return true;
}


//+------------------------------------------------------------------+
//| Event filter helpers - Step 5.3 master-list aligned              |
//+------------------------------------------------------------------+
bool IsDateInList(int date_key, int &dates[])
{
   int total = ArraySize(dates);

   for(int i = 0; i < total; i++)
   {
      if(dates[i] == date_key)
      {
         return true;
      }
   }

   return false;
}

int DateKeyFromYmd(int year, int month, int day)
{
   return year * 10000 + month * 100 + day;
}

int DaysInMonth(int year, int month)
{
   MqlDateTime dt;
   dt.year = year;
   dt.mon = month;
   dt.day = 1;
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;

   if(month == 12)
   {
      dt.year = year + 1;
      dt.mon = 1;
   }
   else
   {
      dt.mon = month + 1;
   }

   datetime next_month = StructToTime(dt);
   datetime last_time = next_month - 86400;

   MqlDateTime last_dt;
   TimeToStruct(last_time, last_dt);

   return last_dt.day;
}

bool IsYmdWeekday(int year, int month, int day)
{
   MqlDateTime dt;
   dt.year = year;
   dt.mon = month;
   dt.day = day;
   dt.hour = 0;
   dt.min = 0;
   dt.sec = 0;

   datetime t = StructToTime(dt);

   MqlDateTime out;
   TimeToStruct(t, out);

   if(out.day_of_week >= 1 && out.day_of_week <= 5)
   {
      return true;
   }

   return false;
}

bool IsYearEndStopDate(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.mon == 12 && dt.day >= 25)
   {
      return true;
   }

   if(dt.mon == 1 && dt.day <= 3)
   {
      return true;
   }

   return false;
}

bool IsMonthEndLast3BusinessDays(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int last_day = DaysInMonth(dt.year, dt.mon);
   int business_count = 0;

   for(int day = last_day; day >= 1; day--)
   {
      if(IsYmdWeekday(dt.year, dt.mon, day))
      {
         business_count++;

         if(day == dt.day && business_count <= 3)
         {
            return true;
         }
      }

      if(business_count >= 3 && day < dt.day)
      {
         break;
      }
   }

   return false;
}

bool IsFomcPrevOrToday(int date_key, string &event_name)
{
   if(InpStopOnFOMC && IsDateInList(date_key, FOMC_2026_DATES))
   {
      event_name = "FOMC";
      return true;
   }

   int total = ArraySize(FOMC_2026_DATES);

   for(int i = 0; i < total; i++)
   {
      if(date_key == FOMC_2026_DATES[i] - 1)
      {
         event_name = "FOMC_PREV";
         return true;
      }
   }

   return false;
}

bool IsEvents4Date(int date_key, string &event_name)
{
   if(InpStopOnFOMC && IsDateInList(date_key, FOMC_2026_DATES))
   {
      event_name = "FOMC";
      return true;
   }

   if(InpStopOnUS_NFP && IsDateInList(date_key, US_NFP_2026_DATES))
   {
      event_name = "US_NFP";
      return true;
   }

   if(InpStopOnUS_CPI && IsDateInList(date_key, US_CPI_2026_DATES))
   {
      event_name = "US_CPI";
      return true;
   }

   if(InpStopOnBOJ && IsDateInList(date_key, BOJ_2026_DATES))
   {
      event_name = "BOJ";
      return true;
   }

   return false;
}

bool IsEvents5ECBDate(int date_key, string &event_name)
{
   if(IsEvents4Date(date_key, event_name))
   {
      return true;
   }

   if(InpStopOnECB && IsDateInList(date_key, ECB_2026_DATES))
   {
      event_name = "ECB";
      return true;
   }

   return false;
}

bool IsEvents5BOEDate(int date_key, string &event_name)
{
   if(IsEvents4Date(date_key, event_name))
   {
      return true;
   }

   if(InpStopOnBOE && IsDateInList(date_key, BOE_2026_DATES))
   {
      event_name = "BOE";
      return true;
   }

   return false;
}

bool IsAJ6EventsDate(int date_key, string &event_name)
{
   if(IsEvents4Date(date_key, event_name))
   {
      return true;
   }

   if(InpStopOnRBA && IsDateInList(date_key, RBA_2026_DATES))
   {
      event_name = "RBA";
      return true;
   }

   if(InpStopOnAU_CPI && IsDateInList(date_key, AU_CPI_2026_DATES))
   {
      event_name = "AU_CPI";
      return true;
   }

   return false;
}

bool IsEACommonEventsDate(int date_key, string &event_name)
{
   if(InpStopOnFOMC && IsDateInList(date_key, FOMC_2026_DATES))
   {
      event_name = "FOMC";
      return true;
   }

   if(InpStopOnUS_NFP && IsDateInList(date_key, US_NFP_2026_DATES))
   {
      event_name = "US_NFP";
      return true;
   }

   if(InpStopOnUS_CPI && IsDateInList(date_key, US_CPI_2026_DATES))
   {
      event_name = "US_CPI";
      return true;
   }

   if(InpStopOnECB && IsDateInList(date_key, ECB_2026_DATES))
   {
      event_name = "ECB";
      return true;
   }

   if(InpStopOnRBA && IsDateInList(date_key, RBA_2026_DATES))
   {
      event_name = "RBA";
      return true;
   }

   if(InpStopOnAU_CPI && IsDateInList(date_key, AU_CPI_2026_DATES))
   {
      event_name = "AU_CPI";
      return true;
   }

   return false;
}

bool IsGACommonEventsDate(int date_key, string &event_name)
{
   if(InpStopOnFOMC && IsDateInList(date_key, FOMC_2026_DATES))
   {
      event_name = "FOMC";
      return true;
   }

   if(InpStopOnUS_NFP && IsDateInList(date_key, US_NFP_2026_DATES))
   {
      event_name = "US_NFP";
      return true;
   }

   if(InpStopOnUS_CPI && IsDateInList(date_key, US_CPI_2026_DATES))
   {
      event_name = "US_CPI";
      return true;
   }

   if(InpStopOnBOE && IsDateInList(date_key, BOE_2026_DATES))
   {
      event_name = "BOE";
      return true;
   }

   if(InpStopOnRBA && IsDateInList(date_key, RBA_2026_DATES))
   {
      event_name = "RBA";
      return true;
   }

   if(InpStopOnAU_CPI && IsDateInList(date_key, AU_CPI_2026_DATES))
   {
      event_name = "AU_CPI";
      return true;
   }

   return false;
}

bool IsAUCPIorRBADate(int date_key, string &event_name)
{
   if(InpStopOnRBA && IsDateInList(date_key, RBA_2026_DATES))
   {
      event_name = "RBA";
      return true;
   }

   if(InpStopOnAU_CPI && IsDateInList(date_key, AU_CPI_2026_DATES))
   {
      event_name = "AU_CPI";
      return true;
   }

   return false;
}

bool IsAUChinaEventsDate(int date_key, string &event_name)
{
   if(IsAUCPIorRBADate(date_key, event_name))
   {
      return true;
   }

   if(IsFomcPrevOrToday(date_key, event_name))
   {
      return true;
   }

   return false;
}

bool IsAJChinaEventsDate(int date_key, string &event_name)
{
   if(InpStopOnBOJ && IsDateInList(date_key, BOJ_2026_DATES))
   {
      event_name = "BOJ";
      return true;
   }

   if(IsAUCPIorRBADate(date_key, event_name))
   {
      return true;
   }

   return false;
}

bool IsEAChinaEventsDate(int date_key, string &event_name)
{
   if(IsAUCPIorRBADate(date_key, event_name))
   {
      return true;
   }

   if(IsFomcPrevOrToday(date_key, event_name))
   {
      return true;
   }

   if(InpStopOnECB && IsDateInList(date_key, ECB_2026_DATES))
   {
      event_name = "ECB";
      return true;
   }

   return false;
}

bool IsGAChinaEventsDate(int date_key, string &event_name)
{
   if(IsAUCPIorRBADate(date_key, event_name))
   {
      return true;
   }

   if(IsFomcPrevOrToday(date_key, event_name))
   {
      return true;
   }

   if(InpStopOnBOE && IsDateInList(date_key, BOE_2026_DATES))
   {
      event_name = "BOE";
      return true;
   }

   return false;
}

bool IsCpiWednesdayDate(int date_key)
{
   if(InpStopOnUS_CPI && IsDateInList(date_key, US_CPI_WED_2026_DATES))
   {
      return true;
   }

   return false;
}

bool PassPythonCalendarEventFilter(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpUseEventFilter)
   {
      return true;
   }

   int date_key = DateKey(jst_time);
   string event_name = "";

   if(IsYearEndStopDate(jst_time))
   {
      PrintEventDecisionLog(cfg, jst_time, "YEAR_END_STOP");
      return false;
   }

   if(cfg.strategy_code == "1_EJ_Log1")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 2)
      {
         PrintEventDecisionLog(cfg, jst_time, "EJ_LOG1_FEB_STOP");
         return false;
      }

      if(dt.day == 1)
      {
         PrintEventDecisionLog(cfg, jst_time, "EJ_LOG1_DAY1_STOP");
         return false;
      }

      if(IsCpiWednesdayDate(date_key))
      {
         PrintEventDecisionLog(cfg, jst_time, "US_CPI_WEEK_WED");
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "2_EJ_NightBlitz_20" || cfg.strategy_code == "3_EJ_NightBlitz_21")
   {
      if(IsEvents5ECBDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "4_GJ_Port_Log1")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 12)
      {
         PrintEventDecisionLog(cfg, jst_time, "GJ_PORT_LOG1_DEC_STOP");
         return false;
      }

      if(dt.day == 1 || dt.day == 2 || dt.day == 29 || dt.day == 30 || dt.day == 31)
      {
         PrintEventDecisionLog(cfg, jst_time, "GJ_PORT_LOG1_DAY_STOP");
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "5_GJ_Log2")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.day == 18 || dt.day == 19 || dt.day == 27)
      {
         PrintEventDecisionLog(cfg, jst_time, "GJ_PORT_LOG2_DAY_STOP");
         return false;
      }

      if(IsEvents5BOEDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "6_GJ_Old_Mon")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 1 || dt.mon == 2)
      {
         PrintEventDecisionLog(cfg, jst_time, "GJ_OLD_MON_MONTH_STOP");
         return false;
      }

      if(IsEvents5BOEDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "7_GJ_Mon_Blitz")
   {
      if(IsEvents5BOEDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "8_AJ_Core1" || cfg.strategy_code == "9_AJ_Core2" || cfg.strategy_code == "10_AJ_SatA" || cfg.strategy_code == "11_AJ_SatB")
   {
      if(IsAJ6EventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "12_UJ_Short_Core" || cfg.strategy_code == "13_UJ_Fix_MidWeek" || cfg.strategy_code == "14_UJ_Sat_3rd" || cfg.strategy_code == "15_UJ_Sat_Aug")
   {
      if(IsEvents4Date(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "16_UJ_T10A")
   {
      if(InpStopOnBOJ && IsDateInList(date_key, BOJ_2026_DATES))
      {
         PrintEventDecisionLog(cfg, jst_time, "BOJ");
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "17_EA_1B" || cfg.strategy_code == "18_EA_2" || cfg.strategy_code == "19_EA_3" || cfg.strategy_code == "20_EA_1A")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 10)
      {
         PrintEventDecisionLog(cfg, jst_time, "EA_OCT_STOP");
         return false;
      }

      if(cfg.strategy_code == "17_EA_1B" && dt.mon == 8)
      {
         PrintEventDecisionLog(cfg, jst_time, "EA_1B_AUG_STOP");
         return false;
      }

      if(cfg.strategy_code == "18_EA_2" && (dt.mon == 1 || dt.mon == 8))
      {
         PrintEventDecisionLog(cfg, jst_time, "EA_2_MONTH_STOP");
         return false;
      }

      if(cfg.strategy_code == "20_EA_1A" && dt.mon == 8)
      {
         PrintEventDecisionLog(cfg, jst_time, "EA_1A_AUG_STOP");
         return false;
      }

      if(IsMonthEndLast3BusinessDays(jst_time))
      {
         PrintEventDecisionLog(cfg, jst_time, "EA_MONTH_END_3_BIZ_DAYS");
         return false;
      }

      if(IsEACommonEventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "21_GA_B3" || cfg.strategy_code == "22_GA_C2" || cfg.strategy_code == "23_GA_F2" || cfg.strategy_code == "24_GA_D1")
   {
      if(IsGACommonEventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "25_AU_China_Demand")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 8 || dt.mon == 10)
      {
         PrintEventDecisionLog(cfg, jst_time, "AU_CHINA_MONTH_STOP");
         return false;
      }

      if(IsAUChinaEventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "26_AJ_China_Demand")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 2 || dt.mon == 8 || dt.mon == 10)
      {
         PrintEventDecisionLog(cfg, jst_time, "AJ_CHINA_MONTH_STOP");
         return false;
      }

      if(IsAJChinaEventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "27_EA_China_Demand")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 8 || dt.mon == 10)
      {
         PrintEventDecisionLog(cfg, jst_time, "EA_CHINA_MONTH_STOP");
         return false;
      }

      if(IsEAChinaEventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   if(cfg.strategy_code == "28_GA_China_Demand")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 8 || dt.mon == 10)
      {
         PrintEventDecisionLog(cfg, jst_time, "GA_CHINA_MONTH_STOP");
         return false;
      }

      if(IsGAChinaEventsDate(date_key, event_name))
      {
         PrintEventDecisionLog(cfg, jst_time, event_name);
         return false;
      }

      return true;
   }

   return true;
}

bool IsAllowedWeekday(StrategyConfig &cfg, int day_of_week)
{
   if(InpTestMode && InpTestModeIgnoreEntryWeekday) return true;
   if(day_of_week == 0 && cfg.trade_sunday) return true;
   if(day_of_week == 1 && cfg.trade_monday) return true;
   if(day_of_week == 2 && cfg.trade_tuesday) return true;
   if(day_of_week == 3 && cfg.trade_wednesday) return true;
   if(day_of_week == 4 && cfg.trade_thursday) return true;
   if(day_of_week == 5 && cfg.trade_friday) return true;
   if(day_of_week == 6 && cfg.trade_saturday) return true;
   return false;
}

bool IsStrategyActiveDate(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   if(cfg.special_rule == RULE_NONE) return IsAllowedWeekday(cfg, dt.day_of_week);
   if(cfg.special_rule == RULE_UJ_SHORT_CORE) return IsUJ12ActiveDate(jst_time, cfg.strategy_name);
   if(cfg.special_rule == RULE_UJ_FIX_MIDWEEK)
   {
      if(dt.day < 25){ PrintRuleReject(cfg.strategy_name, "Date rule reject: before 25th. JST=" + DateTimeText(jst_time)); return false; }
      if(dt.day_of_week == 3 || dt.day_of_week == 4) return true;
      PrintRuleReject(cfg.strategy_name, "Date rule reject: not Wed/Thu. JST=" + DateTimeText(jst_time));
      return false;
   }
   if(cfg.special_rule == RULE_UJ_SAT_3RD)
   {
      if(dt.day == 3) return true;
      PrintRuleReject(cfg.strategy_name, "Date rule reject: not 3rd. JST=" + DateTimeText(jst_time));
      return false;
   }
   if(cfg.special_rule == RULE_UJ_SAT_AUG)
   {
      if(dt.mon != 8){ PrintRuleReject(cfg.strategy_name, "Date rule reject: not August. JST=" + DateTimeText(jst_time)); return false; }
      if(dt.day > 10){ PrintRuleReject(cfg.strategy_name, "Date rule reject: after Aug 10. JST=" + DateTimeText(jst_time)); return false; }
      return true;
   }
   if(cfg.special_rule == RULE_UJ_T10A)
   {
      if(dt.day != 10){ PrintRuleReject(cfg.strategy_name, "Date rule reject: not 10th. JST=" + DateTimeText(jst_time)); return false; }
      if(IsWednesday(dt)){ PrintRuleReject(cfg.strategy_name, "Date rule reject: Wednesday stop. JST=" + DateTimeText(jst_time)); return false; }
      return true;
   }
   if(cfg.special_rule == RULE_CHINA_AU_DEMAND) return IsChinaAUDemandActiveDate(jst_time, cfg.strategy_name);
   if(cfg.special_rule == RULE_CHINA_9_15) return IsChina915ActiveDate(jst_time, cfg.strategy_name);
   if(cfg.special_rule == RULE_AJ_CORE2) return IsAJCore2ActiveDate(jst_time, cfg.strategy_name);
   return false;
}

bool PassEntryFilters(StrategyConfig &cfg, datetime jst_time)
{
   if(!PassGlobalAtrP70Filter(cfg, jst_time)) return false;
   if(!PassPythonCalendarEventFilter(cfg, jst_time)) return false;
   return true;
}

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

int GetStrategyExitHour(StrategyConfig &cfg)
{
   if(cfg.special_rule == RULE_NONE && InpTestMode && InpUseTestTimes) return InpTestExitHourJST;
   return cfg.exit_hour;
}

int GetStrategyExitMinute(StrategyConfig &cfg)
{
   if(cfg.special_rule == RULE_NONE && InpTestMode && InpUseTestTimes) return InpTestExitMinuteJST;
   return cfg.exit_minute;
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

bool IsOvernightExit(StrategyConfig &cfg, datetime jst_time)
{
   int entry_hour = GetStrategyEntryHour(cfg, jst_time);
   int entry_minute = GetStrategyEntryMinute(cfg, jst_time);
   int exit_hour = GetStrategyExitHour(cfg);
   int exit_minute = GetStrategyExitMinute(cfg);
   if(exit_hour < entry_hour) return true;
   if(exit_hour == entry_hour && exit_minute < entry_minute) return true;
   return false;
}

bool IsExitTime(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);
   int entry_hour = GetStrategyEntryHour(cfg, jst_time);
   int entry_minute = GetStrategyEntryMinute(cfg, jst_time);
   int exit_hour = GetStrategyExitHour(cfg);
   int exit_minute = GetStrategyExitMinute(cfg);
   bool overnight_exit = IsOvernightExit(cfg, jst_time);
   if(overnight_exit)
   {
      if(dt.hour > entry_hour) return false;
      if(dt.hour == entry_hour && dt.min >= entry_minute) return false;
      if(dt.hour < exit_hour) return false;
      if(dt.hour == exit_hour && dt.min < exit_minute) return false;
      return true;
   }
   if(dt.hour < exit_hour) return false;
   if(dt.hour == exit_hour && dt.min < exit_minute) return false;
   return true;
}

void SetupStrategies()
{
   SetStrategy(0, InpEnable_17_EA_1B, "17_EA_1B_Wed_Short", "17_EA_1B", "EURAUD", 17001, DIR_SHORT, 9, 59, 20, 58, 70.0, 175.0, "17_EA_1B_step5_3", RULE_NONE);
   SetWeekdays(strategies[0], false, false, false, true, false, false, false);
   SetStrategy(1, InpEnable_18_EA_2, "18_EA_2_MonWed_Short", "18_EA_2", "EURAUD", 18002, DIR_SHORT, 9, 59, 5, 26, 90.0, 180.0, "18_EA_2_step5_3", RULE_NONE);
   SetWeekdays(strategies[1], false, true, true, true, false, false, false);
   SetStrategy(2, InpEnable_19_EA_3, "19_EA_3_WedThu_Long", "19_EA_3", "EURAUD", 19003, DIR_LONG, 20, 56, 10, 0, 90.0, 0.0, "19_EA_3_step5_3", RULE_NONE);
   SetWeekdays(strategies[2], false, false, false, true, true, false, false);
   SetStrategy(3, InpEnable_21_GA_B3, "21_GA_B_3", "21_GA_B3", "GBPAUD", 21003, DIR_LONG, 21, 2, 10, 0, 220.0, 100.0, "21_GA_B_3_step5_3", RULE_NONE);
   SetWeekdays(strategies[3], false, true, false, false, false, false, false);
   SetStrategy(4, InpEnable_22_GA_C2, "22_GA_C_2", "22_GA_C2", "GBPAUD", 22002, DIR_LONG, 16, 56, 1, 15, 70.0, 80.0, "22_GA_C_2_step5_3", RULE_NONE);
   SetWeekdays(strategies[4], false, false, false, false, true, false, false);
   SetStrategy(5, InpEnable_23_GA_F2, "23_GA_F_2", "23_GA_F2", "GBPAUD", 23002, DIR_SHORT, 19, 42, 22, 45, 90.0, 200.0, "23_GA_F_2_step5_3", RULE_NONE);
   SetWeekdays(strategies[5], false, false, false, false, false, true, false);
   SetStrategy(6, InpEnable_24_GA_D1, "24_GA_D_1", "24_GA_D1", "GBPAUD", 24001, DIR_LONG, 22, 44, 3, 8, 90.0, 200.0, "24_GA_D_1_step5_3", RULE_NONE);
   SetWeekdays(strategies[6], false, false, false, false, false, true, false);
   SetStrategy(7, InpEnable_5_GJ_Log2, "5_GJ_Port_Log2", "5_GJ_Log2", "GBPJPY", 50002, DIR_SHORT, 9, 55, 23, 55, 90.0, 0.0, "5_GJ_Port_Log2_step5_3", RULE_NONE);
   SetWeekdays(strategies[7], false, false, true, false, true, true, false);
   SetStrategy(8, InpEnable_12_UJ_Short_Core, "12_UJ_Short_Core", "12_UJ_Short_Core", "USDJPY", 12001, DIR_SHORT, 8, 4, 14, 56, 50.0, 0.0, "12_UJ_Short_Core_step5_3", RULE_UJ_SHORT_CORE);
   SetWeekdays(strategies[8], false, true, true, true, true, true, false);
   SetStrategy(9, InpEnable_13_UJ_Fix_MidWeek, "13_UJ_Fix_MidWeek", "13_UJ_Fix_MidWeek", "USDJPY", 13001, DIR_LONG, 18, 4, 22, 3, 95.0, 95.0, "13_UJ_Fix_MidWeek_step5_3", RULE_UJ_FIX_MIDWEEK);
   SetWeekdays(strategies[9], false, false, false, true, true, false, false);
   SetStrategy(10, InpEnable_14_UJ_Sat_3rd, "14_UJ_Sat_3rd", "14_UJ_Sat_3rd", "USDJPY", 14001, DIR_SHORT, 20, 1, 3, 8, 45.0, 70.0, "14_UJ_Sat_3rd_step5_3", RULE_UJ_SAT_3RD);
   SetWeekdays(strategies[10], false, true, true, true, true, true, false);
   SetStrategy(11, InpEnable_15_UJ_Sat_Aug, "15_UJ_Sat_Aug", "15_UJ_Sat_Aug", "USDJPY", 15001, DIR_SHORT, 19, 0, 23, 30, 20.0, 35.0, "15_UJ_Sat_Aug_step5_3", RULE_UJ_SAT_AUG);
   SetWeekdays(strategies[11], false, true, true, true, true, true, false);
   SetStrategy(12, InpEnable_16_UJ_T10A, "16_UJ_T10A", "16_UJ_T10A", "USDJPY", 16001, DIR_LONG, 2, 58, 9, 50, 45.0, 110.0, "16_UJ_T10A_step5_3", RULE_UJ_T10A);
   SetWeekdays(strategies[12], false, true, true, true, true, true, false);
   SetStrategy(13, InpEnable_1_EJ_Log1, "1_EJ_Log1", "1_EJ_Log1", "EURJPY", 10001, DIR_LONG, 13, 55, 4, 55, 70.0, 250.0, "1_EJ_Log1_step5_3", RULE_NONE);
   SetWeekdays(strategies[13], false, true, false, true, false, false, false);
   SetStrategy(14, InpEnable_2_EJ_NightBlitz_20, "2_EJ_NightBlitz_20", "2_EJ_NightBlitz_20", "EURJPY", 20001, DIR_LONG, 20, 56, 4, 45, 45.0, 70.0, "2_EJ_NightBlitz_20_step5_3", RULE_NONE);
   SetWeekdays(strategies[14], false, true, false, true, false, false, false);
   SetStrategy(15, InpEnable_3_EJ_NightBlitz_21, "3_EJ_NightBlitz_21", "3_EJ_NightBlitz_21", "EURJPY", 30001, DIR_LONG, 21, 56, 5, 27, 75.0, 70.0, "3_EJ_NightBlitz_21_step5_3", RULE_NONE);
   SetWeekdays(strategies[15], false, true, false, true, false, false, false);
   SetStrategy(16, InpEnable_4_GJ_Port_Log1, "4_GJ_Port_Log1", "4_GJ_Port_Log1", "GBPJPY", 40001, DIR_LONG, 0, 0, 8, 55, 130.0, 90.0, "4_GJ_Port_Log1_step5_3", RULE_NONE);
   SetWeekdays(strategies[16], false, false, true, true, false, false, false);
   SetStrategy(17, InpEnable_6_GJ_Old_Mon, "6_GJ_Old_Mon", "6_GJ_Old_Mon", "GBPJPY", 60001, DIR_LONG, 15, 45, 22, 50, 50.0, 210.0, "6_GJ_Old_Mon_step5_3", RULE_NONE);
   SetWeekdays(strategies[17], false, true, false, false, false, false, false);
   SetStrategy(18, InpEnable_7_GJ_Mon_Blitz, "7_GJ_Mon_Blitz", "7_GJ_Mon_Blitz", "GBPJPY", 70001, DIR_LONG, 18, 2, 23, 2, 130.0, 250.0, "7_GJ_Mon_Blitz_step5_3", RULE_NONE);
   SetWeekdays(strategies[18], false, true, false, false, false, false, false);
   SetStrategy(19, InpEnable_8_AJ_Core1, "8_AJ_Core1", "8_AJ_Core1", "AUDJPY", 80001, DIR_LONG, 8, 1, 22, 46, 70.0, 110.0, "8_AJ_Core1_step5_3", RULE_NONE);
   SetWeekdays(strategies[19], false, true, false, false, false, false, false);
   SetStrategy(20, InpEnable_10_AJ_SatA, "10_AJ_SatA", "10_AJ_SatA", "AUDJPY", 10002, DIR_SHORT, 10, 58, 13, 51, 50.0, 25.0, "10_AJ_SatA_step5_3", RULE_NONE);
   SetWeekdays(strategies[20], false, false, false, false, false, true, false);
   SetStrategy(21, InpEnable_11_AJ_SatB, "11_AJ_SatB", "11_AJ_SatB", "AUDJPY", 11001, DIR_SHORT, 18, 57, 1, 43, 55.0, 95.0, "11_AJ_SatB_step5_3", RULE_NONE);
   SetWeekdays(strategies[21], false, false, false, false, false, true, false);
   SetStrategy(22, InpEnable_20_EA_1A, "20_EA_1A_MonTue_Short", "20_EA_1A", "EURAUD", 20002, DIR_SHORT, 10, 1, 16, 0, 50.0, 125.0, "20_EA_1A_step5_3", RULE_NONE);
   SetWeekdays(strategies[22], false, true, true, false, false, false, false);
   SetStrategy(23, InpEnable_25_AU_China_Demand, "25_AU_China_Demand", "25_AU_China_Demand", "AUDUSD", 25001, DIR_LONG, 10, 0, 15, 50, 40.0, 40.0, "25_AU_China_Demand_step5_3", RULE_CHINA_AU_DEMAND);
   SetWeekdays(strategies[23], false, true, true, true, true, true, false);
   SetStrategy(24, InpEnable_26_AJ_China_Demand, "26_AJ_China_Demand", "26_AJ_China_Demand", "AUDJPY", 26001, DIR_LONG, 10, 0, 15, 50, 45.0, 80.0, "26_AJ_China_Demand_step5_3", RULE_CHINA_9_15);
   SetWeekdays(strategies[24], false, true, true, true, true, true, false);
   SetStrategy(25, InpEnable_27_EA_China_Demand, "27_EA_China_Demand", "27_EA_China_Demand", "EURAUD", 27001, DIR_SHORT, 10, 0, 15, 50, 60.0, 60.0, "27_EA_China_Demand_step5_3", RULE_CHINA_9_15);
   SetWeekdays(strategies[25], false, true, true, true, true, true, false);
   SetStrategy(26, InpEnable_28_GA_China_Demand, "28_GA_China_Demand", "28_GA_China_Demand", "GBPAUD", 28001, DIR_SHORT, 10, 0, 16, 10, 75.0, 70.0, "28_GA_China_Demand_step5_3", RULE_CHINA_9_15);
   SetWeekdays(strategies[26], false, true, true, true, true, true, false);
   SetStrategy(27, InpEnable_9_AJ_Core2, "9_AJ_Core2", "9_AJ_Core2", "AUDJPY", 90001, DIR_SHORT, 17, 14, 1, 14, 30.0, 80.0, "9_AJ_Core2_step5_3", RULE_AJ_CORE2);
   SetWeekdays(strategies[27], false, false, false, false, true, false, false);
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

void ClosePositionsByConfig(StrategyConfig &cfg)
{
   int total = PositionsTotal();
   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(!PositionSelectByTicket(ticket)) continue;
      string pos_symbol = PositionGetString(POSITION_SYMBOL);
      long pos_magic = PositionGetInteger(POSITION_MAGIC);
      if(pos_symbol != cfg.symbol) continue;
      if(pos_magic != cfg.magic) continue;
      trade.SetExpertMagicNumber(cfg.magic);
      trade.SetDeviationInPoints(InpSlippagePoints);
      bool result = trade.PositionClose(ticket);
      if(result) PrintDebug(cfg.strategy_name, "Time exit success. Symbol=" + cfg.symbol + ", Ticket=" + IntegerToString((int)ticket));
      else
      {
         int retcode = (int)trade.ResultRetcode();
         string desc = trade.ResultRetcodeDescription();
         PrintDebug(cfg.strategy_name, "Time exit failed. Symbol=" + cfg.symbol + ", Ticket=" + IntegerToString((int)ticket) + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
      }
   }
}

void TryEntry(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.enabled) return;
   if(!EnsureSymbolReady(cfg.symbol, cfg.strategy_name)) return;
   if(!IsEntryTime(cfg, jst_time)) return;
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
   if(AlreadyEnteredToday(cfg, jst_time)){ PrintSkip(cfg.strategy_name, "Skip entry: already entered today."); return; }
   if(HasOpenPosition(cfg.symbol, cfg.magic)){ PrintSkip(cfg.strategy_name, "Skip entry: position already exists."); return; }
   if(cfg.direction == DIR_LONG){ SendBuyOrder(cfg, jst_time); return; }
   if(cfg.direction == DIR_SHORT){ SendSellOrder(cfg, jst_time); return; }
   PrintDebug(cfg.strategy_name, "Unknown direction. Direction=" + IntegerToString(cfg.direction));
}

void TryExit(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.enabled) return;
   if(!IsExitTime(cfg, jst_time)) return;
   ClosePositionsByConfig(cfg);
}

void RunStrategies()
{
   datetime jst_time = GetJstTime();
   int strategy_count = ArraySize(strategies);
   for(int i = 0; i < strategy_count; i++) TryExit(strategies[i], jst_time);
   for(int i = 0; i < strategy_count; i++) TryEntry(strategies[i], jst_time);
}


void PrintLotModeCheck()
{
   if(InpLotMode == 0)
   {
      PrintDebug("EA", "LOT MODE CHECK. Mode=Fixed Lot, FixedLot=" + DoubleToString(InpFixedLot, 2));
   }
   else if(InpLotMode == 1)
   {
      PrintDebug("EA", "LOT MODE CHECK. Mode=Weekly Compound, RiskPercent=" + DoubleToString(InpRiskPercentPerTrade, 2) + ", MaxAutoLot=" + DoubleToString(InpMaxAutoLot, 2) + ", WeeklyBaseUseEquity=" + BoolText(InpWeeklyBaseUseEquity));
   }
   else
   {
      PrintDebug("EA", "LOT MODE CHECK. Mode=Unknown, InpLotMode=" + IntegerToString(InpLotMode));
   }

   if(InpEmergencyStop)
   {
      PrintDebug("EA", "EMERGENCY STOP ACTIVE. New entries are blocked. Time exits remain active.");
   }

   if(InpLotMode == 1 && InpRiskPercentPerTrade > 2.0)
   {
      PrintDebug("EA", "WARNING. RiskPercentPerTrade is high. RiskPercent=" + DoubleToString(InpRiskPercentPerTrade, 2));
   }

   if(InpLotMode == 1 && InpMaxAutoLot > 1.0)
   {
      PrintDebug("EA", "WARNING. MaxAutoLot is high. MaxAutoLot=" + DoubleToString(InpMaxAutoLot, 2));
   }
}

void PrintInitSummary()
{
   PrintDebug("EA", "Step 8 Forward test ready initialized.");
   PrintDebug("EA", "Config-managed 28 strategy EA with emergency stop and lot mode check.");
   PrintDebug("EA", "JST Offset Hours=" + IntegerToString(InpJstOffsetHours));
   PrintDebug("EA", "EmergencyStop=" + BoolText(InpEmergencyStop));
   PrintDebug("EA", "FixedLot=" + DoubleToString(InpFixedLot, 2));
   PrintDebug("EA", "LotMode=" + IntegerToString(InpLotMode));
   PrintDebug("EA", "WeeklyBaseUseEquity=" + BoolText(InpWeeklyBaseUseEquity));
   PrintDebug("EA", "RiskPercentPerTrade=" + DoubleToString(InpRiskPercentPerTrade, 2));
   PrintDebug("EA", "MaxAutoLot=" + DoubleToString(InpMaxAutoLot, 2));
   PrintDebug("EA", "AllowMinLotWhenBelowMinimum=" + BoolText(InpAllowMinLotWhenBelowMinimum));
   PrintDebug("EA", "PrintLotLogs=" + BoolText(InpPrintLotLogs));
   PrintDebug("EA", "TestMode=" + BoolText(InpTestMode));
   PrintDebug("EA", "UseTestTimes=" + BoolText(InpUseTestTimes));
   PrintDebug("EA", "UseMockJstDateTime=" + BoolText(InpUseMockJstDateTime));
   PrintDebug("EA", "MockJST=" + DateTimeText(BuildMockJstTime()));
   PrintDebug("EA", "UseGlobalAtrP70Filter=" + BoolText(InpUseGlobalAtrP70Filter));
   PrintDebug("EA", "ATR Timeframe=" + TimeframeText(InpAtrTimeframe));
   PrintDebug("EA", "ATR Period=" + IntegerToString(InpAtrPeriod));
   PrintDebug("EA", "ATR P70 Lookback=" + IntegerToString(InpAtrP70LookbackBars));
   PrintDebug("EA", "ATR Percentile=" + DoubleToString(InpAtrPercentile, 1));
   PrintDebug("EA", "ATR UseClosedBar=" + BoolText(InpAtrUseClosedBar));
   PrintDebug("EA", "PrintAtrFilterLogs=" + BoolText(InpPrintAtrFilterLogs));
   PrintDebug("EA", "SuppressAtrLogsOncePerDay=" + BoolText(InpSuppressAtrLogsOncePerDay));
   PrintDebug("EA", "UseEventFilter=" + BoolText(InpUseEventFilter));
   PrintDebug("EA", "PrintEventFilterLogs=" + BoolText(InpPrintEventFilterLogs));
   PrintDebug("EA", "SuppressEventLogsOncePerDay=" + BoolText(InpSuppressEventLogsOncePerDay));
   PrintLotModeCheck();
}

void PrintStrategySummary()
{
   int strategy_count = ArraySize(strategies);
   for(int i = 0; i < strategy_count; i++)
   {
      PrintDebug(strategies[i].strategy_name, "Enabled=" + BoolText(strategies[i].enabled) + ", Symbol=" + strategies[i].symbol + ", Magic=" + IntegerToString(strategies[i].magic) + ", Direction=" + IntegerToString(strategies[i].direction) + ", SpecialRule=" + IntegerToString(strategies[i].special_rule) + ", SL=" + DoubleToString(strategies[i].sl_pips, 1) + ", TP=" + DoubleToString(strategies[i].tp_pips, 1));
   }
}

int OnInit()
{
   SetupStrategies();
   trade.SetExpertMagicNumber(0);
   trade.SetDeviationInPoints(InpSlippagePoints);
   EventSetTimer(10);
   int strategy_count = ArraySize(strategies);
   for(int i = 0; i < strategy_count; i++) EnsureSymbolReady(strategies[i].symbol, strategies[i].strategy_name);
   PrintInitSummary();
   PrintStrategySummary();
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   PrintDebug("EA", "Step 8 Forward test ready deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
   RunStrategies();
}

void OnTimer()
{
   RunStrategies();
}
