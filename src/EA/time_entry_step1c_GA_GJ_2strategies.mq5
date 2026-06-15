//+------------------------------------------------------------------+
//| time_entry_step1c_GA_GJ_2strategies.mq5                          |
//| Time Entry Portfolio Lab                                         |
//| Step 1C: 22_GA_C_2 + 5_GJ_Port_Log2 integrated EA                |
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

//+------------------------------------------------------------------+
//| 22_GA_C_2 Inputs                                                  |
//+------------------------------------------------------------------+
input bool   InpEnable_GA_C2 = true;
input string InpSymbol_GA_C2 = "GBPAUD";
input int    InpMagic_GA_C2 = 22002;

input int    InpEntryWeekday_GA_C2 = 4;     // Thursday=4
input int    InpEntryHour_GA_C2 = 16;
input int    InpEntryMinute_GA_C2 = 56;

input int    InpExitWeekday_GA_C2 = 5;      // Friday=5
input int    InpExitHour_GA_C2 = 1;
input int    InpExitMinute_GA_C2 = 15;

input double InpSLPips_GA_C2 = 70.0;
input double InpTPPips_GA_C2 = 80.0;

//+------------------------------------------------------------------+
//| 5_GJ_Port_Log2 Inputs                                             |
//+------------------------------------------------------------------+
input bool   InpEnable_GJ_Log2 = true;
input string InpSymbol_GJ_Log2 = "GBPJPY";
input int    InpMagic_GJ_Log2 = 50002;

// Tuesday=2, Thursday=4, Friday=5
input bool   InpTradeTuesday_GJ_Log2 = true;
input bool   InpTradeThursday_GJ_Log2 = true;
input bool   InpTradeFriday_GJ_Log2 = true;

input int    InpEntryHour_GJ_Log2 = 9;
input int    InpEntryMinute_GJ_Log2 = 55;

input int    InpExitHour_GJ_Log2 = 23;
input int    InpExitMinute_GJ_Log2 = 55;

input double InpSLPips_GJ_Log2 = 90.0;

// TPなし。0以下ならTPなし。
input double InpTPPips_GJ_Log2 = 0.0;

//+------------------------------------------------------------------+
//| Utility                                                          |
//+------------------------------------------------------------------+
datetime GetJstTime()
{
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
      Print("[Step1C ", strategy, "] ", message);
   }
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

string EntryGlobalVariableName(string strategy_code, string symbol, int magic, int date_key)
{
   string name = "TE_STEP1C_" + strategy_code + "_" + symbol + "_" + IntegerToString(magic) + "_" + IntegerToString(date_key);

   return name;
}

bool AlreadyEnteredToday(string strategy_code, string symbol, int magic, datetime jst_time)
{
   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(strategy_code, symbol, magic, key);

   if(GlobalVariableCheck(gv_name))
   {
      return true;
   }

   return false;
}

void MarkEnteredToday(string strategy_code, string symbol, int magic, datetime jst_time)
{
   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(strategy_code, symbol, magic, key);

   GlobalVariableSet(gv_name, TimeTradeServer());
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

bool IsSpecificEntryTime(datetime jst_time, int entry_weekday, int entry_hour, int entry_minute)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(!InpTestModeIgnoreEntryWeekday)
   {
      if(dt.day_of_week != entry_weekday)
      {
         return false;
      }
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

bool IsGJAllowedEntryWeekday(int day_of_week)
{
   if(InpTestModeIgnoreEntryWeekday)
   {
      return true;
   }

   if(day_of_week == 2 && InpTradeTuesday_GJ_Log2)
   {
      return true;
   }

   if(day_of_week == 4 && InpTradeThursday_GJ_Log2)
   {
      return true;
   }

   if(day_of_week == 5 && InpTradeFriday_GJ_Log2)
   {
      return true;
   }

   return false;
}

bool IsGJEntryTime(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(!IsGJAllowedEntryWeekday(dt.day_of_week))
   {
      return false;
   }

   if(dt.hour != InpEntryHour_GJ_Log2)
   {
      return false;
   }

   if(dt.min < InpEntryMinute_GJ_Log2)
   {
      return false;
   }

   if(dt.min >= InpEntryMinute_GJ_Log2 + InpEntryWindowMinutes)
   {
      return false;
   }

   return true;
}

bool IsSpecificExitTime(datetime jst_time, int exit_weekday, int exit_hour, int exit_minute)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(!InpTestModeIgnoreExitWeekday)
   {
      if(dt.day_of_week != exit_weekday)
      {
         return false;
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

bool IsGJExitTime(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.hour < InpExitHour_GJ_Log2)
   {
      return false;
   }

   if(dt.hour == InpExitHour_GJ_Log2 && dt.min < InpExitMinute_GJ_Log2)
   {
      return false;
   }

   return true;
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

//+------------------------------------------------------------------+
//| Entry functions                                                  |
//+------------------------------------------------------------------+
void TryEntry_GA_C2(datetime jst_time)
{
   string strategy = "22_GA_C_2";
   string symbol = InpSymbol_GA_C2;
   int magic = InpMagic_GA_C2;

   if(!InpEnable_GA_C2)
   {
      return;
   }

   if(!EnsureSymbolReady(symbol, strategy))
   {
      return;
   }

   if(!IsSpecificEntryTime(jst_time, InpEntryWeekday_GA_C2, InpEntryHour_GA_C2, InpEntryMinute_GA_C2))
   {
      return;
   }

   if(AlreadyEnteredToday(strategy, symbol, magic, jst_time))
   {
      PrintDebug(strategy, "Skip entry: already entered today.");
      return;
   }

   if(HasOpenPosition(symbol, magic))
   {
      PrintDebug(strategy, "Skip entry: position already exists.");
      return;
   }

   double lot = NormalizeLot(symbol, InpFixedLot);
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double pip = GetPipSize(symbol);

   if(ask <= 0)
   {
      PrintDebug(strategy, "Skip entry: invalid ASK.");
      return;
   }

   double sl = ask - InpSLPips_GA_C2 * pip;
   double tp = ask + InpTPPips_GA_C2 * pip;

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);

   trade.SetExpertMagicNumber(magic);
   trade.SetDeviationInPoints(InpSlippagePoints);

   string comment = "22_GA_C_2_step1c";

   bool result = trade.Buy(lot, symbol, ask, sl, tp, comment);

   if(result)
   {
      MarkEnteredToday(strategy, symbol, magic, jst_time);
      PrintDebug(strategy, "BUY entry success. Symbol=" + symbol + ", Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
   }
   else
   {
      int retcode = (int)trade.ResultRetcode();
      string desc = trade.ResultRetcodeDescription();

      PrintDebug(strategy, "BUY entry failed. Symbol=" + symbol + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
   }
}

void TryEntry_GJ_Log2(datetime jst_time)
{
   string strategy = "5_GJ_Port_Log2";
   string symbol = InpSymbol_GJ_Log2;
   int magic = InpMagic_GJ_Log2;

   if(!InpEnable_GJ_Log2)
   {
      return;
   }

   if(!EnsureSymbolReady(symbol, strategy))
   {
      return;
   }

   if(!IsGJEntryTime(jst_time))
   {
      return;
   }

   if(AlreadyEnteredToday(strategy, symbol, magic, jst_time))
   {
      PrintDebug(strategy, "Skip entry: already entered today.");
      return;
   }

   if(HasOpenPosition(symbol, magic))
   {
      PrintDebug(strategy, "Skip entry: position already exists.");
      return;
   }

   double lot = NormalizeLot(symbol, InpFixedLot);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   double pip = GetPipSize(symbol);

   if(bid <= 0)
   {
      PrintDebug(strategy, "Skip entry: invalid BID.");
      return;
   }

   double sl = bid + InpSLPips_GJ_Log2 * pip;
   double tp = 0.0;

   if(InpTPPips_GJ_Log2 > 0)
   {
      tp = bid - InpTPPips_GJ_Log2 * pip;
   }

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   sl = NormalizeDouble(sl, digits);

   if(tp > 0)
   {
      tp = NormalizeDouble(tp, digits);
   }

   trade.SetExpertMagicNumber(magic);
   trade.SetDeviationInPoints(InpSlippagePoints);

   string comment = "5_GJ_Port_Log2_step1c";

   bool result = trade.Sell(lot, symbol, bid, sl, tp, comment);

   if(result)
   {
      MarkEnteredToday(strategy, symbol, magic, jst_time);

      if(tp > 0)
      {
         PrintDebug(strategy, "SELL entry success. Symbol=" + symbol + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
      }
      else
      {
         PrintDebug(strategy, "SELL entry success. Symbol=" + symbol + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
      }
   }
   else
   {
      int retcode = (int)trade.ResultRetcode();
      string desc = trade.ResultRetcodeDescription();

      PrintDebug(strategy, "SELL entry failed. Symbol=" + symbol + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
   }
}

//+------------------------------------------------------------------+
//| Exit functions                                                   |
//+------------------------------------------------------------------+
void ClosePositionsByMagic(string strategy, string symbol, int magic)
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

      if(pos_symbol != symbol)
      {
         continue;
      }

      if(pos_magic != magic)
      {
         continue;
      }

      trade.SetExpertMagicNumber(magic);
      trade.SetDeviationInPoints(InpSlippagePoints);

      bool result = trade.PositionClose(ticket);

      if(result)
      {
         PrintDebug(strategy, "Time exit success. Symbol=" + symbol + ", Ticket=" + IntegerToString((int)ticket));
      }
      else
      {
         int retcode = (int)trade.ResultRetcode();
         string desc = trade.ResultRetcodeDescription();

         PrintDebug(strategy, "Time exit failed. Symbol=" + symbol + ", Ticket=" + IntegerToString((int)ticket) + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
      }
   }
}

void TryExit_GA_C2(datetime jst_time)
{
   string strategy = "22_GA_C_2";

   if(!InpEnable_GA_C2)
   {
      return;
   }

   if(!IsSpecificExitTime(jst_time, InpExitWeekday_GA_C2, InpExitHour_GA_C2, InpExitMinute_GA_C2))
   {
      return;
   }

   ClosePositionsByMagic(strategy, InpSymbol_GA_C2, InpMagic_GA_C2);
}

void TryExit_GJ_Log2(datetime jst_time)
{
   string strategy = "5_GJ_Port_Log2";

   if(!InpEnable_GJ_Log2)
   {
      return;
   }

   if(!IsGJExitTime(jst_time))
   {
      return;
   }

   ClosePositionsByMagic(strategy, InpSymbol_GJ_Log2, InpMagic_GJ_Log2);
}

//+------------------------------------------------------------------+
//| Main execution                                                   |
//+------------------------------------------------------------------+
void RunStrategies()
{
   datetime jst_time = GetJstTime();

   TryExit_GA_C2(jst_time);
   TryExit_GJ_Log2(jst_time);

   TryEntry_GA_C2(jst_time);
   TryEntry_GJ_Log2(jst_time);
}

//+------------------------------------------------------------------+
//| Expert events                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   EventSetTimer(10);

   EnsureSymbolReady(InpSymbol_GA_C2, "22_GA_C_2");
   EnsureSymbolReady(InpSymbol_GJ_Log2, "5_GJ_Port_Log2");

   PrintDebug("EA", "Step 1C initialized.");
   PrintDebug("EA", "JST Offset Hours=" + IntegerToString(InpJstOffsetHours));
   PrintDebug("EA", "FixedLot=" + DoubleToString(InpFixedLot, 2));
   PrintDebug("EA", "TestMode=" + (InpTestMode ? "true" : "false"));
   PrintDebug("EA", "IgnoreEntryWeekday=" + (InpTestModeIgnoreEntryWeekday ? "true" : "false"));
   PrintDebug("EA", "IgnoreExitWeekday=" + (InpTestModeIgnoreExitWeekday ? "true" : "false"));
   PrintDebug("22_GA_C_2", "Symbol=" + InpSymbol_GA_C2 + ", Magic=" + IntegerToString(InpMagic_GA_C2));
   PrintDebug("5_GJ_Port_Log2", "Symbol=" + InpSymbol_GJ_Log2 + ", Magic=" + IntegerToString(InpMagic_GJ_Log2));

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();

   PrintDebug("EA", "Step 1C deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
   RunStrategies();
}

void OnTimer()
{
   RunStrategies();
}
