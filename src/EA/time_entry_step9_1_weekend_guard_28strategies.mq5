//+------------------------------------------------------------------+
//| time_entry_step9_1_weekend_guard_28strategies.mq5                 |
//| Time Entry Portfolio Lab                                         |
//| Step 9.1: Weekend / Market Closed Guard for 28 strategies         |
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
input bool   InpSuppressSkipLogsOncePerDay = true;
input bool   InpPrintRuleRejectLogs = true;

// Weekend / Market Closed Guard
// true = block new entries on Saturday / Sunday JST before Event / ATR filters.
input bool   InpUseWeekendMarketClosedGuard = true;
input bool   InpPrintWeekendGuardLogs = true;
input bool   InpSuppressWeekendGuardLogsOncePerDay = true;

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

// Runtime weekend / market closed guard log suppression cache
string printed_weekend_guard_log_keys[];
int printed_weekend_guard_log_count = 0;

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
   for(int i = 0; i < printed_emergency_stop_count; i++)
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

bool IsWeekendMarketClosedJST(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.day_of_week == 0)
   {
      return true;
   }

   if(dt.day_of_week == 6)
   {
      return true;
   }

   return false;
}

bool WasWeekendGuardLogPrintedRuntime(string log_key)
{
   for(int i = 0; i < printed_weekend_guard_log_count; i++)
   {
      if(printed_weekend_guard_log_keys[i] == log_key)
      {
         return true;
      }
   }

   return false;
}

void MarkWeekendGuardLogPrintedRuntime(string log_key)
{
   int new_size = printed_weekend_guard_log_count + 1;
   ArrayResize(printed_weekend_guard_log_keys, new_size);
   printed_weekend_guard_log_keys[printed_weekend_guard_log_count] = log_key;
   printed_weekend_guard_log_count = new_size;
}

void PrintWeekendGuardSkip(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpPrintDebug)
   {
      return;
   }

   if(!InpPrintWeekendGuardLogs)
   {
      return;
   }

   int key = DateKey(jst_time);
   string log_key = cfg.strategy_code + "|" + cfg.symbol + "|" + IntegerToString(cfg.magic) + "|" + IntegerToString(key) + "|WEEKEND_GUARD";

   if(InpSuppressWeekendGuardLogsOncePerDay && WasWeekendGuardLogPrintedRuntime(log_key))
   {
      return;
   }

   MarkWeekendGuardLogPrintedRuntime(log_key);

   Print(
      "[Step9 WeekendGuard ",
      cfg.strategy_name,
      "] Skip entry: weekend / market closed. Symbol=",
      cfg.symbol,
      ", JST=",
      DateTimeText(jst_time)
   );
}

bool PassWeekendMarketClosedGuard(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpUseWeekendMarketClosedGuard)
   {
      return true;
   }

   if(IsWeekendMarketClosedJST(jst_time))
   {
      PrintWeekendGuardSkip(cfg, jst_time);
      return false;
   }

   return true;
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

...TRUNCATED_BY_ASSISTANT...