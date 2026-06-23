//+------------------------------------------------------------------+
//| time_entry_step4_3_config_managed_28strategies_atr_p70.mq5       |
//| Time Entry Portfolio Lab                                         |
//| Step 4.3: 28 strategy EA with Global H1 ATR P70 filter           |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

input double InpFixedLot = 0.01;
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

void PrintDebug(string strategy, string message)
{
   if(InpPrintDebug)
   {
      Print("[Step4.3 ATR ", strategy, "] ", message);
   }
}

void PrintSkip(string strategy, string message)
{
   if(InpPrintDebug && InpPrintSkipLogs)
   {
      Print("[Step4.3 ATR ", strategy, "] ", message);
   }
}

void PrintRuleReject(string strategy, string message)
{
   if(InpPrintDebug && InpPrintRuleRejectLogs)
   {
      Print("[Step4.3 ATR ", strategy, "] ", message);
   }
}

void PrintAtrLog(string strategy, string message)
{
   if(InpPrintDebug && InpPrintAtrFilterLogs)
   {
      Print("[Step4.3 ATR ", strategy, "] ", message);
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

double GetStrategyLot(StrategyConfig &cfg)
{
   return NormalizeLot(cfg.symbol, InpFixedLot);
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
      PrintAtrLog(cfg.strategy_name, "ATR ERROR. Symbol=" + cfg.symbol + ", Reason=" + error_message);
      return false;
   }
   double atr_pips = ToPips(cfg.symbol, current_atr);
   double p70_pips = ToPips(cfg.symbol, p70_value);
   bool pass = current_atr >= p70_value;
   string msg = "Symbol=" + cfg.symbol + ", TF=" + TimeframeText(InpAtrTimeframe) + ", ATR_Pips=" + DoubleToString(atr_pips, 1) + ", P" + DoubleToString(InpAtrPercentile, 1) + "_Pips=" + DoubleToString(p70_pips, 1) + ", CopiedBars=" + IntegerToString(copied_bars);
   if(pass)
   {
      PrintAtrLog(cfg.strategy_name, "ATR PASS. " + msg);
      return true;
   }
   PrintAtrLog(cfg.strategy_name, "ATR REJECT. " + msg);
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
   SetStrategy(0, InpEnable_17_EA_1B, "17_EA_1B_Wed_Short", "17_EA_1B", "EURAUD", 17001, DIR_SHORT, 9, 59, 20, 58, 70.0, 175.0, "17_EA_1B_step4_3", RULE_NONE);
   SetWeekdays(strategies[0], false, false, false, true, false, false, false);
   SetStrategy(1, InpEnable_18_EA_2, "18_EA_2_MonWed_Short", "18_EA_2", "EURAUD", 18002, DIR_SHORT, 9, 59, 5, 26, 90.0, 180.0, "18_EA_2_step4_3", RULE_NONE);
   SetWeekdays(strategies[1], false, true, true, true, false, false, false);
   SetStrategy(2, InpEnable_19_EA_3, "19_EA_3_WedThu_Long", "19_EA_3", "EURAUD", 19003, DIR_LONG, 20, 56, 10, 0, 90.0, 0.0, "19_EA_3_step4_3", RULE_NONE);
   SetWeekdays(strategies[2], false, false, false, true, true, false, false);
   SetStrategy(3, InpEnable_21_GA_B3, "21_GA_B_3", "21_GA_B3", "GBPAUD", 21003, DIR_LONG, 21, 2, 10, 0, 220.0, 100.0, "21_GA_B_3_step4_3", RULE_NONE);
   SetWeekdays(strategies[3], false, true, false, false, false, false, false);
   SetStrategy(4, InpEnable_22_GA_C2, "22_GA_C_2", "22_GA_C2", "GBPAUD", 22002, DIR_LONG, 16, 56, 1, 15, 70.0, 80.0, "22_GA_C_2_step4_3", RULE_NONE);
   SetWeekdays(strategies[4], false, false, false, false, true, false, false);
   SetStrategy(5, InpEnable_23_GA_F2, "23_GA_F_2", "23_GA_F2", "GBPAUD", 23002, DIR_SHORT, 19, 42, 22, 45, 90.0, 200.0, "23_GA_F_2_step4_3", RULE_NONE);
   SetWeekdays(strategies[5], false, false, false, false, false, true, false);
   SetStrategy(6, InpEnable_24_GA_D1, "24_GA_D_1", "24_GA_D1", "GBPAUD", 24001, DIR_LONG, 22, 44, 3, 8, 90.0, 200.0, "24_GA_D_1_step4_3", RULE_NONE);
   SetWeekdays(strategies[6], false, false, false, false, false, true, false);
   SetStrategy(7, InpEnable_5_GJ_Log2, "5_GJ_Port_Log2", "5_GJ_Log2", "GBPJPY", 50002, DIR_SHORT, 9, 55, 23, 55, 90.0, 0.0, "5_GJ_Port_Log2_step4_3", RULE_NONE);
   SetWeekdays(strategies[7], false, false, true, false, true, true, false);
   SetStrategy(8, InpEnable_12_UJ_Short_Core, "12_UJ_Short_Core", "12_UJ_Short_Core", "USDJPY", 12001, DIR_SHORT, 8, 4, 14, 56, 50.0, 0.0, "12_UJ_Short_Core_step4_3", RULE_UJ_SHORT_CORE);
   SetWeekdays(strategies[8], false, true, true, true, true, true, false);
   SetStrategy(9, InpEnable_13_UJ_Fix_MidWeek, "13_UJ_Fix_MidWeek", "13_UJ_Fix_MidWeek", "USDJPY", 13001, DIR_LONG, 18, 4, 22, 3, 95.0, 95.0, "13_UJ_Fix_MidWeek_step4_3", RULE_UJ_FIX_MIDWEEK);
   SetWeekdays(strategies[9], false, false, false, true, true, false, false);
   SetStrategy(10, InpEnable_14_UJ_Sat_3rd, "14_UJ_Sat_3rd", "14_UJ_Sat_3rd", "USDJPY", 14001, DIR_SHORT, 20, 1, 3, 8, 45.0, 70.0, "14_UJ_Sat_3rd_step4_3", RULE_UJ_SAT_3RD);
   SetWeekdays(strategies[10], false, true, true, true, true, true, false);
   SetStrategy(11, InpEnable_15_UJ_Sat_Aug, "15_UJ_Sat_Aug", "15_UJ_Sat_Aug", "USDJPY", 15001, DIR_SHORT, 19, 0, 23, 30, 20.0, 35.0, "15_UJ_Sat_Aug_step4_3", RULE_UJ_SAT_AUG);
   SetWeekdays(strategies[11], false, true, true, true, true, true, false);
   SetStrategy(12, InpEnable_16_UJ_T10A, "16_UJ_T10A", "16_UJ_T10A", "USDJPY", 16001, DIR_LONG, 2, 58, 9, 50, 45.0, 110.0, "16_UJ_T10A_step4_3", RULE_UJ_T10A);
   SetWeekdays(strategies[12], false, true, true, true, true, true, false);
   SetStrategy(13, InpEnable_1_EJ_Log1, "1_EJ_Log1", "1_EJ_Log1", "EURJPY", 10001, DIR_LONG, 13, 55, 4, 55, 70.0, 250.0, "1_EJ_Log1_step4_3", RULE_NONE);
   SetWeekdays(strategies[13], false, true, false, true, false, false, false);
   SetStrategy(14, InpEnable_2_EJ_NightBlitz_20, "2_EJ_NightBlitz_20", "2_EJ_NightBlitz_20", "EURJPY", 20001, DIR_LONG, 20, 56, 4, 45, 45.0, 70.0, "2_EJ_NightBlitz_20_step4_3", RULE_NONE);
   SetWeekdays(strategies[14], false, true, false, true, false, false, false);
   SetStrategy(15, InpEnable_3_EJ_NightBlitz_21, "3_EJ_NightBlitz_21", "3_EJ_NightBlitz_21", "EURJPY", 30001, DIR_LONG, 21, 56, 5, 27, 75.0, 70.0, "3_EJ_NightBlitz_21_step4_3", RULE_NONE);
   SetWeekdays(strategies[15], false, true, false, true, false, false, false);
   SetStrategy(16, InpEnable_4_GJ_Port_Log1, "4_GJ_Port_Log1", "4_GJ_Port_Log1", "GBPJPY", 40001, DIR_LONG, 0, 0, 8, 55, 130.0, 90.0, "4_GJ_Port_Log1_step4_3", RULE_NONE);
   SetWeekdays(strategies[16], false, false, true, true, false, false, false);
   SetStrategy(17, InpEnable_6_GJ_Old_Mon, "6_GJ_Old_Mon", "6_GJ_Old_Mon", "GBPJPY", 60001, DIR_LONG, 15, 45, 22, 50, 50.0, 210.0, "6_GJ_Old_Mon_step4_3", RULE_NONE);
   SetWeekdays(strategies[17], false, true, false, false, false, false, false);
   SetStrategy(18, InpEnable_7_GJ_Mon_Blitz, "7_GJ_Mon_Blitz", "7_GJ_Mon_Blitz", "GBPJPY", 70001, DIR_LONG, 18, 2, 23, 2, 130.0, 250.0, "7_GJ_Mon_Blitz_step4_3", RULE_NONE);
   SetWeekdays(strategies[18], false, true, false, false, false, false, false);
   SetStrategy(19, InpEnable_8_AJ_Core1, "8_AJ_Core1", "8_AJ_Core1", "AUDJPY", 80001, DIR_LONG, 8, 1, 22, 46, 70.0, 110.0, "8_AJ_Core1_step4_3", RULE_NONE);
   SetWeekdays(strategies[19], false, true, false, false, false, false, false);
   SetStrategy(20, InpEnable_10_AJ_SatA, "10_AJ_SatA", "10_AJ_SatA", "AUDJPY", 10002, DIR_SHORT, 10, 58, 13, 51, 50.0, 25.0, "10_AJ_SatA_step4_3", RULE_NONE);
   SetWeekdays(strategies[20], false, false, false, false, false, true, false);
   SetStrategy(21, InpEnable_11_AJ_SatB, "11_AJ_SatB", "11_AJ_SatB", "AUDJPY", 11001, DIR_SHORT, 18, 57, 1, 43, 55.0, 95.0, "11_AJ_SatB_step4_3", RULE_NONE);
   SetWeekdays(strategies[21], false, false, false, false, false, true, false);
   SetStrategy(22, InpEnable_20_EA_1A, "20_EA_1A_MonTue_Short", "20_EA_1A", "EURAUD", 20002, DIR_SHORT, 10, 1, 16, 0, 50.0, 125.0, "20_EA_1A_step4_3", RULE_NONE);
   SetWeekdays(strategies[22], false, true, true, false, false, false, false);
   SetStrategy(23, InpEnable_25_AU_China_Demand, "25_AU_China_Demand", "25_AU_China_Demand", "AUDUSD", 25001, DIR_LONG, 10, 0, 15, 50, 40.0, 40.0, "25_AU_China_Demand_step4_3", RULE_CHINA_AU_DEMAND);
   SetWeekdays(strategies[23], false, true, true, true, true, true, false);
   SetStrategy(24, InpEnable_26_AJ_China_Demand, "26_AJ_China_Demand", "26_AJ_China_Demand", "AUDJPY", 26001, DIR_LONG, 10, 0, 15, 50, 45.0, 80.0, "26_AJ_China_Demand_step4_3", RULE_CHINA_9_15);
   SetWeekdays(strategies[24], false, true, true, true, true, true, false);
   SetStrategy(25, InpEnable_27_EA_China_Demand, "27_EA_China_Demand", "27_EA_China_Demand", "EURAUD", 27001, DIR_SHORT, 10, 0, 15, 50, 60.0, 60.0, "27_EA_China_Demand_step4_3", RULE_CHINA_9_15);
   SetWeekdays(strategies[25], false, true, true, true, true, true, false);
   SetStrategy(26, InpEnable_28_GA_China_Demand, "28_GA_China_Demand", "28_GA_China_Demand", "GBPAUD", 28001, DIR_SHORT, 10, 0, 16, 10, 75.0, 70.0, "28_GA_China_Demand_step4_3", RULE_CHINA_9_15);
   SetWeekdays(strategies[26], false, true, true, true, true, true, false);
   SetStrategy(27, InpEnable_9_AJ_Core2, "9_AJ_Core2", "9_AJ_Core2", "AUDJPY", 90001, DIR_SHORT, 17, 14, 1, 14, 30.0, 80.0, "9_AJ_Core2_step4_3", RULE_AJ_CORE2);
   SetWeekdays(strategies[27], false, false, false, false, true, false, false);
}

bool SendBuyOrder(StrategyConfig &cfg, datetime jst_time)
{
   double ask = SymbolInfoDouble(cfg.symbol, SYMBOL_ASK);
   if(ask <= 0){ PrintDebug(cfg.strategy_name, "Skip entry: invalid ASK."); return false; }
   double lot = GetStrategyLot(cfg);
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
   double lot = GetStrategyLot(cfg);
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

void PrintInitSummary()
{
   PrintDebug("EA", "Step 4.3 ATR initialized.");
   PrintDebug("EA", "Config-managed 28 strategy EA with Global H1 ATR P70.");
   PrintDebug("EA", "JST Offset Hours=" + IntegerToString(InpJstOffsetHours));
   PrintDebug("EA", "FixedLot=" + DoubleToString(InpFixedLot, 2));
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
   PrintDebug("EA", "Step 4.3 ATR deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
   RunStrategies();
}

void OnTimer()
{
   RunStrategies();
}
