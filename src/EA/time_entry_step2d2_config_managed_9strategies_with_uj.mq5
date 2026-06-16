//+------------------------------------------------------------------+
//| time_entry_step2d2_config_managed_9strategies_with_uj.mq5        |
//| Time Entry Portfolio Lab                                         |
//| Step 2D.2: Config-managed 9 strategy EA with UJ special rule      |
//|                                                                  |
//| Strategies:                                                      |
//| - 22_GA_C_2               GBPAUD Long                            |
//| - 5_GJ_Port_Log2          GBPJPY Short                           |
//| - 21_GA_B_3               GBPAUD Long                            |
//| - 23_GA_F_2               GBPAUD Short                           |
//| - 24_GA_D_1               GBPAUD Long                            |
//| - 17_EA_1B_Wed_Short      EURAUD Short                           |
//| - 18_EA_2_MonWed_Short    EURAUD Short                           |
//| - 19_EA_3_WedThu_Long     EURAUD Long                            |
//| - 12_UJ_Short_Core        USDJPY Short, special date rule         |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

//+------------------------------------------------------------------+
//| Common Inputs                                                    |
//+------------------------------------------------------------------+
input double InpFixedLot = 0.01;
input int    InpJstOffsetHours = 6;
input int    InpSlippagePoints = 30;
input int    InpEntryWindowMinutes = 2;
input bool   InpPrintDebug = true;

// Test mode
input bool   InpTestMode = true;
input bool   InpTestModeIgnoreEntryWeekday = true;
input bool   InpTestModeIgnoreExitWeekday = true;

// If true, all enabled normal strategies use these test entry/exit times.
// UJ can also use these times if InpUJUseTestTimes = true.
input bool   InpUseTestTimes = false;
input int    InpTestEntryHourJST = 12;
input int    InpTestEntryMinuteJST = 0;
input int    InpTestExitHourJST = 12;
input int    InpTestExitMinuteJST = 5;

// Mock JST datetime for date-condition tests
input bool   InpUseMockJstDateTime = false;
input int    InpMockYear = 2026;
input int    InpMockMonth = 2;
input int    InpMockDay = 20;
input int    InpMockHour = 9;
input int    InpMockMinute = 55;

//+------------------------------------------------------------------+
//| Strategy Enable Inputs                                           |
//+------------------------------------------------------------------+
input bool InpEnable_22_GA_C2 = true;
input bool InpEnable_5_GJ_Log2 = true;
input bool InpEnable_21_GA_B3 = true;
input bool InpEnable_23_GA_F2 = true;
input bool InpEnable_24_GA_D1 = true;
input bool InpEnable_17_EA_1B = true;
input bool InpEnable_18_EA_2 = true;
input bool InpEnable_19_EA_3 = true;
input bool InpEnable_12_UJ_Short_Core = true;

//+------------------------------------------------------------------+
//| UJ special test inputs                                           |
//+------------------------------------------------------------------+
input bool InpUJIgnoreDateRules = false;
input bool InpUJUseTestTimes = false;
input bool InpUJForceGotoMode = false;
input bool InpUJForceNormalMode = false;

//+------------------------------------------------------------------+
//| Constants                                                        |
//+------------------------------------------------------------------+
#define DIR_LONG  1
#define DIR_SHORT -1

#define EXIT_SAME_DAY         0
#define EXIT_NEXT_DAY         1
#define EXIT_SPECIFIC_WEEKDAY 2

#define RULE_NONE             0
#define RULE_UJ_SHORT_CORE    1

#define UJ_MODE_INVALID       0
#define UJ_MODE_GOTO          1
#define UJ_MODE_NORMAL        2

//+------------------------------------------------------------------+
//| Strategy Config                                                  |
//+------------------------------------------------------------------+
struct StrategyConfig
{
   bool   enabled;
   string strategy_name;
   string strategy_code;
   string symbol;
   int    magic;
   int    direction;

   bool   trade_sunday;
   bool   trade_monday;
   bool   trade_tuesday;
   bool   trade_wednesday;
   bool   trade_thursday;
   bool   trade_friday;
   bool   trade_saturday;

   int    entry_hour;
   int    entry_minute;

   int    exit_mode;
   int    exit_weekday;
   int    exit_hour;
   int    exit_minute;

   double sl_pips;
   double tp_pips;

   bool   one_entry_per_day;
   string comment;

   int    special_rule;
};

StrategyConfig strategies[9];

//+------------------------------------------------------------------+
//| Utility                                                          |
//+------------------------------------------------------------------+
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

   datetime jst_time = server_time + InpJstOffsetHours * 3600;

   return jst_time;
}

void PrintDebug(string strategy, string message)
{
   if(InpPrintDebug)
   {
      Print("[Step2D.2 ", strategy, "] ", message);
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

double NormalizeLot(string symbol, double lot)
{
   double min_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   double result = lot;

   if(result < min_lot)
   {
      result = min_lot;
   }

   if(result > max_lot)
   {
      result = max_lot;
   }

   if(step_lot > 0)
   {
      result = MathFloor(result / step_lot) * step_lot;
   }

   return NormalizeDouble(result, 2);
}

int DateKey(datetime t)
{
   MqlDateTime dt;
   TimeToStruct(t, dt);

   int key = dt.year * 10000 + dt.mon * 100 + dt.day;

   return key;
}

string EntryGlobalVariableName(StrategyConfig &cfg, int date_key)
{
   string name = "TE_STEP2D2_" + cfg.strategy_code + "_" + cfg.symbol + "_" + IntegerToString(cfg.magic) + "_" + IntegerToString(date_key);

   return name;
}

bool AlreadyEnteredToday(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.one_entry_per_day)
   {
      return false;
   }

   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(cfg, key);

   if(GlobalVariableCheck(gv_name))
   {
      return true;
   }

   return false;
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

bool HasOpenPosition(string symbol, int magic)
{
   int total = PositionsTotal();

   for(int i = 0; i < total; i++)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == 0)
      {
         continue;
      }

      if(!PositionSelectByTicket(ticket))
      {
         continue;
      }

      string pos_symbol = PositionGetString(POSITION_SYMBOL);
      long pos_magic = PositionGetInteger(POSITION_MAGIC);

      if(pos_symbol == symbol && pos_magic == magic)
      {
         return true;
      }
   }

   return false;
}

bool IsAllowedWeekday(StrategyConfig &cfg, int day_of_week)
{
   if(InpTestMode && InpTestModeIgnoreEntryWeekday)
   {
      return true;
   }

   if(day_of_week == 0 && cfg.trade_sunday)
   {
      return true;
   }

   if(day_of_week == 1 && cfg.trade_monday)
   {
      return true;
   }

   if(day_of_week == 2 && cfg.trade_tuesday)
   {
      return true;
   }

   if(day_of_week == 3 && cfg.trade_wednesday)
   {
      return true;
   }

   if(day_of_week == 4 && cfg.trade_thursday)
   {
      return true;
   }

   if(day_of_week == 5 && cfg.trade_friday)
   {
      return true;
   }

   if(day_of_week == 6 && cfg.trade_saturday)
   {
      return true;
   }

   return false;
}

void SetWeekdays(
   StrategyConfig &cfg,
   bool sunday,
   bool monday,
   bool tuesday,
   bool wednesday,
   bool thursday,
   bool friday,
   bool saturday
)
{
   cfg.trade_sunday = sunday;
   cfg.trade_monday = monday;
   cfg.trade_tuesday = tuesday;
   cfg.trade_wednesday = wednesday;
   cfg.trade_thursday = thursday;
   cfg.trade_friday = friday;
   cfg.trade_saturday = saturday;
}

void SetStrategy(
   int index,
   bool enabled,
   string strategy_name,
   string strategy_code,
   string symbol,
   int magic,
   int direction,
   int entry_hour,
   int entry_minute,
   int exit_mode,
   int exit_weekday,
   int exit_hour,
   int exit_minute,
   double sl_pips,
   double tp_pips,
   string comment,
   int special_rule
)
{
   strategies[index].enabled = enabled;
   strategies[index].strategy_name = strategy_name;
   strategies[index].strategy_code = strategy_code;
   strategies[index].symbol = symbol;
   strategies[index].magic = magic;
   strategies[index].direction = direction;
   strategies[index].entry_hour = entry_hour;
   strategies[index].entry_minute = entry_minute;
   strategies[index].exit_mode = exit_mode;
   strategies[index].exit_weekday = exit_weekday;
   strategies[index].exit_hour = exit_hour;
   strategies[index].exit_minute = exit_minute;
   strategies[index].sl_pips = sl_pips;
   strategies[index].tp_pips = tp_pips;
   strategies[index].one_entry_per_day = true;
   strategies[index].comment = comment;
   strategies[index].special_rule = special_rule;
}

//+------------------------------------------------------------------+
//| UJ special date rules                                            |
//+------------------------------------------------------------------+
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

bool IsUJGotoDay(int day)
{
   // Backtest reproduction only.
   // No forward-shift goto day handling in Step 2D.2.
   if(day == 20)
   {
      return true;
   }

   if(day == 25)
   {
      return true;
   }

   if(day == 30)
   {
      return true;
   }

   return false;
}

bool IsUJActiveDate(datetime jst_time, string strategy_name)
{
   if(InpTestMode && InpUJIgnoreDateRules)
   {
      return true;
   }

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   // Active only from 20th to month end.
   if(dt.day < 20)
   {
      PrintDebug(strategy_name, "Date rule reject: before 20th. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop 21st / 22nd.
   if(dt.day == 21)
   {
      PrintDebug(strategy_name, "Date rule reject: 21st stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(dt.day == 22)
   {
      PrintDebug(strategy_name, "Date rule reject: 22nd stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop August.
   if(dt.mon == 8)
   {
      PrintDebug(strategy_name, "Date rule reject: August stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop Wednesday. Sunday=0, Monday=1, Tuesday=2, Wednesday=3.
   if(dt.day_of_week == 3)
   {
      PrintDebug(strategy_name, "Date rule reject: Wednesday stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop calendar month end.
   if(IsCalendarMonthEnd(dt))
   {
      PrintDebug(strategy_name, "Date rule reject: calendar month end stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   return true;
}

int GetUJTradeMode(datetime jst_time)
{
   // 1 = GOTO
   // 2 = NORMAL
   // 0 = INVALID

   if(InpUJForceGotoMode && InpUJForceNormalMode)
   {
      return UJ_MODE_INVALID;
   }

   if(InpUJForceGotoMode)
   {
      return UJ_MODE_GOTO;
   }

   if(InpUJForceNormalMode)
   {
      return UJ_MODE_NORMAL;
   }

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(IsUJGotoDay(dt.day))
   {
      return UJ_MODE_GOTO;
   }

   return UJ_MODE_NORMAL;
}

string UJModeText(datetime jst_time)
{
   int mode = GetUJTradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return "GOTO";
   }

   if(mode == UJ_MODE_NORMAL)
   {
      return "NORMAL";
   }

   return "INVALID";
}

int GetUJEntryHour(datetime jst_time)
{
   if(InpTestMode && InpUJUseTestTimes)
   {
      return InpTestEntryHourJST;
   }

   int mode = GetUJTradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 9;
   }

   return 8;
}

int GetUJEntryMinute(datetime jst_time)
{
   if(InpTestMode && InpUJUseTestTimes)
   {
      return InpTestEntryMinuteJST;
   }

   int mode = GetUJTradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 55;
   }

   return 4;
}

int GetUJExitHour()
{
   if(InpTestMode && InpUJUseTestTimes)
   {
      return InpTestExitHourJST;
   }

   return 14;
}

int GetUJExitMinute()
{
   if(InpTestMode && InpUJUseTestTimes)
   {
      return InpTestExitMinuteJST;
   }

   return 56;
}

double GetUJSLPips(datetime jst_time)
{
   int mode = GetUJTradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 20.0;
   }

   return 50.0;
}

double GetUJTPPips(datetime jst_time)
{
   int mode = GetUJTradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 50.0;
   }

   return 0.0;
}

//+------------------------------------------------------------------+
//| Entry / Exit time checks                                         |
//+------------------------------------------------------------------+
bool IsNormalEntryTime(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(!IsAllowedWeekday(cfg, dt.day_of_week))
   {
      return false;
   }

   int entry_hour = cfg.entry_hour;
   int entry_minute = cfg.entry_minute;

   if(InpTestMode && InpUseTestTimes)
   {
      entry_hour = InpTestEntryHourJST;
      entry_minute = InpTestEntryMinuteJST;
   }

   if(dt.hour != entry_hour)
   {
      return false;
   }

   if(dt.min < entry_minute)
   {
      return false;
   }

   if(dt.min >= entry_minute + InpEntryWindowMinutes)
   {
      return false;
   }

   return true;
}

bool IsUJEntryTime(StrategyConfig &cfg, datetime jst_time)
{
   if(!IsUJActiveDate(jst_time, cfg.strategy_name))
   {
      return false;
   }

   int mode = GetUJTradeMode(jst_time);

   if(mode == UJ_MODE_INVALID)
   {
      PrintDebug(cfg.strategy_name, "Invalid UJ mode: both force flags are true.");
      return false;
   }

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int entry_hour = GetUJEntryHour(jst_time);
   int entry_minute = GetUJEntryMinute(jst_time);

   if(dt.hour != entry_hour)
   {
      return false;
   }

   if(dt.min < entry_minute)
   {
      return false;
   }

   if(dt.min >= entry_minute + InpEntryWindowMinutes)
   {
      return false;
   }

   return true;
}

bool IsEntryTime(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return IsUJEntryTime(cfg, jst_time);
   }

   return IsNormalEntryTime(cfg, jst_time);
}

bool IsNormalExitTime(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int exit_hour = cfg.exit_hour;
   int exit_minute = cfg.exit_minute;

   if(InpTestMode && InpUseTestTimes)
   {
      exit_hour = InpTestExitHourJST;
      exit_minute = InpTestExitMinuteJST;
   }

   if(!InpTestModeIgnoreExitWeekday)
   {
      if(cfg.exit_mode == EXIT_SPECIFIC_WEEKDAY)
      {
         if(dt.day_of_week != cfg.exit_weekday)
         {
            return false;
         }
      }
   }

   if(dt.hour < exit_hour)
   {
      return false;
   }

   if(dt.hour == exit_hour && dt.min < exit_minute)
   {
      return false;
   }

   return true;
}

bool IsUJExitTime(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int exit_hour = GetUJExitHour();
   int exit_minute = GetUJExitMinute();

   if(dt.hour < exit_hour)
   {
      return false;
   }

   if(dt.hour == exit_hour && dt.min < exit_minute)
   {
      return false;
   }

   return true;
}

bool IsExitTime(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return IsUJExitTime(jst_time);
   }

   return IsNormalExitTime(cfg, jst_time);
}

double GetStrategySLPips(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return GetUJSLPips(jst_time);
   }

   return cfg.sl_pips;
}

double GetStrategyTPPips(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return GetUJTPPips(jst_time);
   }

   return cfg.tp_pips;
}

string GetStrategyComment(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return cfg.comment + "_" + UJModeText(jst_time);
   }

   return cfg.comment;
}

//+------------------------------------------------------------------+
//| Config Setup                                                     |
//+------------------------------------------------------------------+
void SetupStrategies()
{
   // 0: 22_GA_C_2
   SetStrategy(
      0,
      InpEnable_22_GA_C2,
      "22_GA_C_2",
      "22_GA_C2",
      "GBPAUD",
      22002,
      DIR_LONG,
      16,
      56,
      EXIT_SPECIFIC_WEEKDAY,
      5,
      1,
      15,
      70.0,
      80.0,
      "22_GA_C_2_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[0], false, false, false, false, true, false, false);

   // 1: 5_GJ_Port_Log2
   SetStrategy(
      1,
      InpEnable_5_GJ_Log2,
      "5_GJ_Port_Log2",
      "5_GJ_Log2",
      "GBPJPY",
      50002,
      DIR_SHORT,
      9,
      55,
      EXIT_SAME_DAY,
      -1,
      23,
      55,
      90.0,
      0.0,
      "5_GJ_Port_Log2_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[1], false, false, true, false, true, true, false);

   // 2: 21_GA_B_3
   SetStrategy(
      2,
      InpEnable_21_GA_B3,
      "21_GA_B_3",
      "21_GA_B3",
      "GBPAUD",
      21003,
      DIR_LONG,
      21,
      2,
      EXIT_NEXT_DAY,
      -1,
      10,
      0,
      220.0,
      100.0,
      "21_GA_B_3_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[2], false, true, false, false, false, false, false);

   // 3: 23_GA_F_2
   SetStrategy(
      3,
      InpEnable_23_GA_F2,
      "23_GA_F_2",
      "23_GA_F2",
      "GBPAUD",
      23002,
      DIR_SHORT,
      19,
      42,
      EXIT_SAME_DAY,
      -1,
      22,
      45,
      90.0,
      200.0,
      "23_GA_F_2_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[3], false, false, false, false, false, true, false);

   // 4: 24_GA_D_1
   SetStrategy(
      4,
      InpEnable_24_GA_D1,
      "24_GA_D_1",
      "24_GA_D1",
      "GBPAUD",
      24001,
      DIR_LONG,
      22,
      44,
      EXIT_NEXT_DAY,
      -1,
      3,
      8,
      90.0,
      200.0,
      "24_GA_D_1_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[4], false, false, false, false, false, true, false);

   // 5: 17_EA_1B_Wed_Short
   SetStrategy(
      5,
      InpEnable_17_EA_1B,
      "17_EA_1B_Wed_Short",
      "17_EA_1B",
      "EURAUD",
      17001,
      DIR_SHORT,
      9,
      59,
      EXIT_SAME_DAY,
      -1,
      20,
      58,
      70.0,
      175.0,
      "17_EA_1B_Wed_Short_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[5], false, false, false, true, false, false, false);

   // 6: 18_EA_2_MonWed_Short
   SetStrategy(
      6,
      InpEnable_18_EA_2,
      "18_EA_2_MonWed_Short",
      "18_EA_2",
      "EURAUD",
      18002,
      DIR_SHORT,
      9,
      59,
      EXIT_NEXT_DAY,
      -1,
      5,
      26,
      90.0,
      180.0,
      "18_EA_2_MonWed_Short_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[6], false, true, true, true, false, false, false);

   // 7: 19_EA_3_WedThu_Long
   SetStrategy(
      7,
      InpEnable_19_EA_3,
      "19_EA_3_WedThu_Long",
      "19_EA_3",
      "EURAUD",
      19003,
      DIR_LONG,
      20,
      56,
      EXIT_NEXT_DAY,
      -1,
      10,
      0,
      90.0,
      0.0,
      "19_EA_3_WedThu_Long_step2d2",
      RULE_NONE
   );
   SetWeekdays(strategies[7], false, false, false, true, true, false, false);

   // 8: 12_UJ_Short_Core
   // Dynamic entry/sl/tp:
   // GOTO day 20/25/30: Entry 09:55, Exit 14:56, SL 20, TP 50
   // Normal day: Entry 08:04, Exit 14:56, SL 50, TP none
   SetStrategy(
      8,
      InpEnable_12_UJ_Short_Core,
      "12_UJ_Short_Core",
      "12_UJ_Short_Core",
      "USDJPY",
      12001,
      DIR_SHORT,
      8,
      4,
      EXIT_SAME_DAY,
      -1,
      14,
      56,
      50.0,
      0.0,
      "12_UJ_Short_Core_step2d2",
      RULE_UJ_SHORT_CORE
   );
   SetWeekdays(strategies[8], false, true, true, true, true, true, false);
}

//+------------------------------------------------------------------+
//| Trading                                                          |
//+------------------------------------------------------------------+
void TryEntry(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.enabled)
   {
      return;
   }

   if(!EnsureSymbolReady(cfg.symbol, cfg.strategy_name))
   {
      return;
   }

   if(!IsEntryTime(cfg, jst_time))
   {
      return;
   }

   if(AlreadyEnteredToday(cfg, jst_time))
   {
      PrintDebug(cfg.strategy_name, "Skip entry: already entered today.");
      return;
   }

   if(HasOpenPosition(cfg.symbol, cfg.magic))
   {
      PrintDebug(cfg.strategy_name, "Skip entry: position already exists.");
      return;
   }

   double lot = NormalizeLot(cfg.symbol, InpFixedLot);
   double pip = GetPipSize(cfg.symbol);

   int digits = (int)SymbolInfoInteger(cfg.symbol, SYMBOL_DIGITS);

   double sl_pips = GetStrategySLPips(cfg, jst_time);
   double tp_pips = GetStrategyTPPips(cfg, jst_time);
   string comment = GetStrategyComment(cfg, jst_time);

   trade.SetExpertMagicNumber(cfg.magic);
   trade.SetDeviationInPoints(InpSlippagePoints);

   if(cfg.direction == DIR_LONG)
   {
      double ask = SymbolInfoDouble(cfg.symbol, SYMBOL_ASK);

      if(ask <= 0)
      {
         PrintDebug(cfg.strategy_name, "Skip entry: invalid ASK.");
         return;
      }

      double sl = ask - sl_pips * pip;
      double tp = 0.0;

      if(tp_pips > 0)
      {
         tp = ask + tp_pips * pip;
      }

      sl = NormalizeDouble(sl, digits);

      if(tp > 0)
      {
         tp = NormalizeDouble(tp, digits);
      }

      bool result = trade.Buy(lot, cfg.symbol, ask, sl, tp, comment);

      if(result)
      {
         MarkEnteredToday(cfg, jst_time);

         if(tp > 0)
         {
            PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
         }
         else
         {
            PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
         }
      }
      else
      {
         int retcode = (int)trade.ResultRetcode();
         string desc = trade.ResultRetcodeDescription();

         PrintDebug(cfg.strategy_name, "BUY entry failed. Symbol=" + cfg.symbol + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
      }

      return;
   }

   if(cfg.direction == DIR_SHORT)
   {
      double bid = SymbolInfoDouble(cfg.symbol, SYMBOL_BID);

      if(bid <= 0)
      {
         PrintDebug(cfg.strategy_name, "Skip entry: invalid BID.");
         return;
      }

      double sl = bid + sl_pips * pip;
      double tp = 0.0;

      if(tp_pips > 0)
      {
         tp = bid - tp_pips * pip;
      }

      sl = NormalizeDouble(sl, digits);

      if(tp > 0)
      {
         tp = NormalizeDouble(tp, digits);
      }

      bool result = trade.Sell(lot, cfg.symbol, bid, sl, tp, comment);

      if(result)
      {
         MarkEnteredToday(cfg, jst_time);

         string extra = "";

         if(cfg.special_rule == RULE_UJ_SHORT_CORE)
         {
            extra = ", Mode=" + UJModeText(jst_time);
         }

         if(tp > 0)
         {
            PrintDebug(cfg.strategy_name, "SELL entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
         }
         else
         {
            PrintDebug(cfg.strategy_name, "SELL entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
         }
      }
      else
      {
         int retcode = (int)trade.ResultRetcode();
         string desc = trade.ResultRetcodeDescription();

         PrintDebug(cfg.strategy_name, "SELL entry failed. Symbol=" + cfg.symbol + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
      }

      return;
   }

   PrintDebug(cfg.strategy_name, "Unknown direction. Direction=" + IntegerToString(cfg.direction));
}

void ClosePositionsByConfig(StrategyConfig &cfg)
{
   int total = PositionsTotal();

   for(int i = total - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);

      if(ticket == 0)
      {
         continue;
      }

      if(!PositionSelectByTicket(ticket))
      {
         continue;
      }

      string pos_symbol = PositionGetString(POSITION_SYMBOL);
      long pos_magic = PositionGetInteger(POSITION_MAGIC);

      if(pos_symbol != cfg.symbol)
      {
         continue;
      }

      if(pos_magic != cfg.magic)
      {
         continue;
      }

      trade.SetExpertMagicNumber(cfg.magic);
      trade.SetDeviationInPoints(InpSlippagePoints);

      bool result = trade.PositionClose(ticket);

      if(result)
      {
         PrintDebug(cfg.strategy_name, "Time exit success. Symbol=" + cfg.symbol + ", Ticket=" + IntegerToString((int)ticket));
      }
      else
      {
         int retcode = (int)trade.ResultRetcode();
         string desc = trade.ResultRetcodeDescription();

         PrintDebug(cfg.strategy_name, "Time exit failed. Symbol=" + cfg.symbol + ", Ticket=" + IntegerToString((int)ticket) + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
      }
   }
}

void TryExit(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.enabled)
   {
      return;
   }

   if(!IsExitTime(cfg, jst_time))
   {
      return;
   }

   ClosePositionsByConfig(cfg);
}

void RunStrategies()
{
   datetime jst_time = GetJstTime();

   int strategy_count = ArraySize(strategies);

   for(int i = 0; i < strategy_count; i++)
   {
      TryExit(strategies[i], jst_time);
   }

   for(int i = 0; i < strategy_count; i++)
   {
      TryEntry(strategies[i], jst_time);
   }
}

//+------------------------------------------------------------------+
//| Expert Events                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   SetupStrategies();

   EventSetTimer(10);

   int strategy_count = ArraySize(strategies);

   for(int i = 0; i < strategy_count; i++)
   {
      EnsureSymbolReady(strategies[i].symbol, strategies[i].strategy_name);
   }

   PrintDebug("EA", "Step 2D.2 initialized.");
   PrintDebug("EA", "Config-managed 9 strategies with UJ special date rule.");
   PrintDebug("EA", "JST Offset Hours=" + IntegerToString(InpJstOffsetHours));
   PrintDebug("EA", "FixedLot=" + DoubleToString(InpFixedLot, 2));
   PrintDebug("EA", "TestMode=" + BoolText(InpTestMode));
   PrintDebug("EA", "UseTestTimes=" + BoolText(InpUseTestTimes));
   PrintDebug("EA", "UseMockJstDateTime=" + BoolText(InpUseMockJstDateTime));
   PrintDebug("EA", "MockJST=" + DateTimeText(BuildMockJstTime()));
   PrintDebug("EA", "UJIgnoreDateRules=" + BoolText(InpUJIgnoreDateRules));
   PrintDebug("EA", "UJUseTestTimes=" + BoolText(InpUJUseTestTimes));
   PrintDebug("EA", "UJForceGotoMode=" + BoolText(InpUJForceGotoMode));
   PrintDebug("EA", "UJForceNormalMode=" + BoolText(InpUJForceNormalMode));
   PrintDebug("EA", "UJ GotoDay=20/25/30 calendar day only. No forward goto day.");

   for(int i = 0; i < strategy_count; i++)
   {
      PrintDebug(
         strategies[i].strategy_name,
         "Enabled=" + BoolText(strategies[i].enabled) +
         ", Symbol=" + strategies[i].symbol +
         ", Magic=" + IntegerToString(strategies[i].magic) +
         ", Direction=" + IntegerToString(strategies[i].direction) +
         ", SpecialRule=" + IntegerToString(strategies[i].special_rule) +
         ", SL=" + DoubleToString(strategies[i].sl_pips, 1) +
         ", TP=" + DoubleToString(strategies[i].tp_pips, 1)
      );
   }

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();

   PrintDebug("EA", "Step 2D.2 deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
   RunStrategies();
}

void OnTimer()
{
   RunStrategies();
}
