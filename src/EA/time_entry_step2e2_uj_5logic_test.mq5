//+------------------------------------------------------------------+
//| time_entry_step2e2_uj_5logic_test.mq5                            |
//| Time Entry Portfolio Lab                                         |
//| Step 2E.2: UJ 5 logic test EA                                    |
//|                                                                  |
//| Strategies:                                                      |
//| - 12_UJ_Short_Core        USDJPY Short special GOTO/NORMAL        |
//| - 13_UJ_Fix_MidWeek       USDJPY Long                            |
//| - 14_UJ_Sat_3rd           USDJPY Short                           |
//| - 15_UJ_Sat_Aug           USDJPY Short                           |
//| - 16_UJ_T10A              USDJPY Long                            |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

//+------------------------------------------------------------------+
//| Common Inputs                                                    |
//+------------------------------------------------------------------+
input string InpExpectedSymbol = "USDJPY";
input bool   InpAllowOtherSymbol = false;

input double InpFixedLot = 0.01;
input int    InpJstOffsetHours = 6;
input int    InpSlippagePoints = 30;
input int    InpEntryWindowMinutes = 2;

input bool   InpPrintDebug = true;
input bool   InpPrintSkipLogs = false;
input bool   InpPrintRuleRejectLogs = true;

// Test mode
input bool   InpTestMode = true;
input bool   InpUseMockJstDateTime = true;

// Mock JST datetime
input int    InpMockYear = 2026;
input int    InpMockMonth = 2;
input int    InpMockDay = 20;
input int    InpMockHour = 9;
input int    InpMockMinute = 55;

// Force mode for 12_UJ_Short_Core only
input bool   InpUJ12ForceGotoMode = false;
input bool   InpUJ12ForceNormalMode = false;

// Enable switches
input bool   InpEnable_12_UJ_Short_Core = true;
input bool   InpEnable_13_UJ_Fix_MidWeek = true;
input bool   InpEnable_14_UJ_Sat_3rd = true;
input bool   InpEnable_15_UJ_Sat_Aug = true;
input bool   InpEnable_16_UJ_T10A = true;

//+------------------------------------------------------------------+
//| Constants                                                        |
//+------------------------------------------------------------------+
#define DIR_LONG  1
#define DIR_SHORT -1

#define RULE_UJ_SHORT_CORE   12
#define RULE_UJ_FIX_MIDWEEK  13
#define RULE_UJ_SAT_3RD      14
#define RULE_UJ_SAT_AUG      15
#define RULE_UJ_T10A         16

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

   int    entry_hour;
   int    entry_minute;

   int    exit_hour;
   int    exit_minute;

   double sl_pips;
   double tp_pips;

   bool   one_entry_per_day;
   string comment;

   int    special_rule;
};

StrategyConfig strategies[5];

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
      Print("[Step2E.2 ", strategy, "] ", message);
   }
}

void PrintSkip(string strategy, string message)
{
   if(InpPrintDebug && InpPrintSkipLogs)
   {
      Print("[Step2E.2 ", strategy, "] ", message);
   }
}

void PrintRuleReject(string strategy, string message)
{
   if(InpPrintDebug && InpPrintRuleRejectLogs)
   {
      Print("[Step2E.2 ", strategy, "] ", message);
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
   string name = "TE_STEP2E2_" + cfg.strategy_code + "_" + cfg.symbol + "_" + IntegerToString(cfg.magic) + "_" + IntegerToString(date_key);

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

bool IsCorrectSymbol()
{
   if(InpAllowOtherSymbol)
   {
      return true;
   }

   if(_Symbol == InpExpectedSymbol)
   {
      return true;
   }

   return false;
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
   strategies[index].exit_hour = exit_hour;
   strategies[index].exit_minute = exit_minute;
   strategies[index].sl_pips = sl_pips;
   strategies[index].tp_pips = tp_pips;
   strategies[index].one_entry_per_day = true;
   strategies[index].comment = comment;
   strategies[index].special_rule = special_rule;
}

//+------------------------------------------------------------------+
//| Calendar helpers                                                 |
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

bool IsWednesday(MqlDateTime &dt)
{
   if(dt.day_of_week == 3)
   {
      return true;
   }

   return false;
}

bool IsUJGotoDay(int day)
{
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

//+------------------------------------------------------------------+
//| 12_UJ_Short_Core special                                         |
//+------------------------------------------------------------------+
bool IsUJ12ActiveDate(datetime jst_time, string strategy_name)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.day < 20)
   {
      PrintRuleReject(strategy_name, "Date rule reject: before 20th. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(dt.day == 21)
   {
      PrintRuleReject(strategy_name, "Date rule reject: 21st stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(dt.day == 22)
   {
      PrintRuleReject(strategy_name, "Date rule reject: 22nd stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(dt.mon == 8)
   {
      PrintRuleReject(strategy_name, "Date rule reject: August stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(IsWednesday(dt))
   {
      PrintRuleReject(strategy_name, "Date rule reject: Wednesday stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(IsCalendarMonthEnd(dt))
   {
      PrintRuleReject(strategy_name, "Date rule reject: calendar month end stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   return true;
}

int GetUJ12TradeMode(datetime jst_time)
{
   if(InpUJ12ForceGotoMode && InpUJ12ForceNormalMode)
   {
      return UJ_MODE_INVALID;
   }

   if(InpUJ12ForceGotoMode)
   {
      return UJ_MODE_GOTO;
   }

   if(InpUJ12ForceNormalMode)
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

string UJ12ModeText(datetime jst_time)
{
   int mode = GetUJ12TradeMode(jst_time);

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

int GetUJ12EntryHour(datetime jst_time)
{
   int mode = GetUJ12TradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 9;
   }

   return 8;
}

int GetUJ12EntryMinute(datetime jst_time)
{
   int mode = GetUJ12TradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 55;
   }

   return 4;
}

double GetUJ12SLPips(datetime jst_time)
{
   int mode = GetUJ12TradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 20.0;
   }

   return 50.0;
}

double GetUJ12TPPips(datetime jst_time)
{
   int mode = GetUJ12TradeMode(jst_time);

   if(mode == UJ_MODE_GOTO)
   {
      return 50.0;
   }

   return 0.0;
}

//+------------------------------------------------------------------+
//| Active date checks for UJ strategies                              |
//+------------------------------------------------------------------+
bool IsStrategyActiveDate(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return IsUJ12ActiveDate(jst_time, cfg.strategy_name);
   }

   if(cfg.special_rule == RULE_UJ_FIX_MIDWEEK)
   {
      if(dt.day < 25)
      {
         PrintRuleReject(cfg.strategy_name, "Date rule reject: before 25th. JST=" + DateTimeText(jst_time));
         return false;
      }

      if(dt.day_of_week == 3 || dt.day_of_week == 4)
      {
         return true;
      }

      PrintRuleReject(cfg.strategy_name, "Date rule reject: not Wed/Thu. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(cfg.special_rule == RULE_UJ_SAT_3RD)
   {
      if(dt.day == 3)
      {
         return true;
      }

      PrintRuleReject(cfg.strategy_name, "Date rule reject: not 3rd. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(cfg.special_rule == RULE_UJ_SAT_AUG)
   {
      if(dt.mon != 8)
      {
         PrintRuleReject(cfg.strategy_name, "Date rule reject: not August. JST=" + DateTimeText(jst_time));
         return false;
      }

      if(dt.day > 10)
      {
         PrintRuleReject(cfg.strategy_name, "Date rule reject: after Aug 10. JST=" + DateTimeText(jst_time));
         return false;
      }

      return true;
   }

   if(cfg.special_rule == RULE_UJ_T10A)
   {
      if(dt.day != 10)
      {
         PrintRuleReject(cfg.strategy_name, "Date rule reject: not 10th. JST=" + DateTimeText(jst_time));
         return false;
      }

      if(IsWednesday(dt))
      {
         PrintRuleReject(cfg.strategy_name, "Date rule reject: Wednesday stop. JST=" + DateTimeText(jst_time));
         return false;
      }

      return true;
   }

   return false;
}

//+------------------------------------------------------------------+
//| Dynamic strategy params                                          |
//+------------------------------------------------------------------+
int GetStrategyEntryHour(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return GetUJ12EntryHour(jst_time);
   }

   return cfg.entry_hour;
}

int GetStrategyEntryMinute(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return GetUJ12EntryMinute(jst_time);
   }

   return cfg.entry_minute;
}

double GetStrategySLPips(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return GetUJ12SLPips(jst_time);
   }

   return cfg.sl_pips;
}

double GetStrategyTPPips(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return GetUJ12TPPips(jst_time);
   }

   return cfg.tp_pips;
}

string GetStrategyComment(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return cfg.comment + "_" + UJ12ModeText(jst_time);
   }

   return cfg.comment;
}

string GetExtraLogText(StrategyConfig &cfg, datetime jst_time)
{
   if(cfg.special_rule == RULE_UJ_SHORT_CORE)
   {
      return ", Mode=" + UJ12ModeText(jst_time);
   }

   return "";
}

//+------------------------------------------------------------------+
//| Entry / Exit checks                                              |
//+------------------------------------------------------------------+
bool IsEntryTime(StrategyConfig &cfg, datetime jst_time)
{
   if(!IsStrategyActiveDate(cfg, jst_time))
   {
      return false;
   }

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

bool IsExitTime(StrategyConfig &cfg, datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.hour < cfg.exit_hour)
   {
      return false;
   }

   if(dt.hour == cfg.exit_hour && dt.min < cfg.exit_minute)
   {
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Config setup                                                     |
//+------------------------------------------------------------------+
void SetupStrategies()
{
   SetStrategy(
      0,
      InpEnable_12_UJ_Short_Core,
      "12_UJ_Short_Core",
      "12_UJ_Short_Core",
      "USDJPY",
      12001,
      DIR_SHORT,
      8,
      4,
      14,
      56,
      50.0,
      0.0,
      "12_UJ_Short_Core_step2e2",
      RULE_UJ_SHORT_CORE
   );

   SetStrategy(
      1,
      InpEnable_13_UJ_Fix_MidWeek,
      "13_UJ_Fix_MidWeek",
      "13_UJ_Fix_MidWeek",
      "USDJPY",
      13001,
      DIR_LONG,
      18,
      4,
      22,
      3,
      95.0,
      95.0,
      "13_UJ_Fix_MidWeek_step2e2",
      RULE_UJ_FIX_MIDWEEK
   );

   SetStrategy(
      2,
      InpEnable_14_UJ_Sat_3rd,
      "14_UJ_Sat_3rd",
      "14_UJ_Sat_3rd",
      "USDJPY",
      14001,
      DIR_SHORT,
      20,
      1,
      3,
      8,
      45.0,
      70.0,
      "14_UJ_Sat_3rd_step2e2",
      RULE_UJ_SAT_3RD
   );

   SetStrategy(
      3,
      InpEnable_15_UJ_Sat_Aug,
      "15_UJ_Sat_Aug",
      "15_UJ_Sat_Aug",
      "USDJPY",
      15001,
      DIR_SHORT,
      19,
      0,
      23,
      30,
      20.0,
      35.0,
      "15_UJ_Sat_Aug_step2e2",
      RULE_UJ_SAT_AUG
   );

   SetStrategy(
      4,
      InpEnable_16_UJ_T10A,
      "16_UJ_T10A",
      "16_UJ_T10A",
      "USDJPY",
      16001,
      DIR_LONG,
      2,
      58,
      9,
      50,
      45.0,
      110.0,
      "16_UJ_T10A_step2e2",
      RULE_UJ_T10A
   );
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
      PrintSkip(cfg.strategy_name, "Skip entry: already entered today.");
      return;
   }

   if(HasOpenPosition(cfg.symbol, cfg.magic))
   {
      PrintSkip(cfg.strategy_name, "Skip entry: position already exists.");
      return;
   }

   double lot = NormalizeLot(cfg.symbol, InpFixedLot);
   double pip = GetPipSize(cfg.symbol);

   int digits = (int)SymbolInfoInteger(cfg.symbol, SYMBOL_DIGITS);

   double sl_pips = GetStrategySLPips(cfg, jst_time);
   double tp_pips = GetStrategyTPPips(cfg, jst_time);
   string comment = GetStrategyComment(cfg, jst_time);
   string extra = GetExtraLogText(cfg, jst_time);

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
            PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
         }
         else
         {
            PrintDebug(cfg.strategy_name, "BUY entry success. Symbol=" + cfg.symbol + extra + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
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

   trade.SetExpertMagicNumber(0);
   trade.SetDeviationInPoints(InpSlippagePoints);

   EventSetTimer(10);

   if(!IsCorrectSymbol())
   {
      PrintDebug("EA", "Warning: Current chart symbol=" + _Symbol + ", Expected=" + InpExpectedSymbol);
   }

   int strategy_count = ArraySize(strategies);

   for(int i = 0; i < strategy_count; i++)
   {
      EnsureSymbolReady(strategies[i].symbol, strategies[i].strategy_name);
   }

   PrintDebug("EA", "Step 2E.2 initialized.");
   PrintDebug("EA", "UJ 5 logic test EA.");
   PrintDebug("EA", "Symbol=" + _Symbol);
   PrintDebug("EA", "ExpectedSymbol=" + InpExpectedSymbol);
   PrintDebug("EA", "JST Offset Hours=" + IntegerToString(InpJstOffsetHours));
   PrintDebug("EA", "FixedLot=" + DoubleToString(InpFixedLot, 2));
   PrintDebug("EA", "TestMode=" + BoolText(InpTestMode));
   PrintDebug("EA", "UseMockJstDateTime=" + BoolText(InpUseMockJstDateTime));
   PrintDebug("EA", "MockJST=" + DateTimeText(BuildMockJstTime()));
   PrintDebug("EA", "PrintSkipLogs=" + BoolText(InpPrintSkipLogs));
   PrintDebug("EA", "PrintRuleRejectLogs=" + BoolText(InpPrintRuleRejectLogs));

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

   PrintDebug("EA", "Step 2E.2 deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
   RunStrategies();
}

void OnTimer()
{
   RunStrategies();
}
