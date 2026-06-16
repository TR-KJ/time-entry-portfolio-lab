//+------------------------------------------------------------------+
//| time_entry_step2d1_uj_short_core_mock_date_test.mq5              |
//| Time Entry Portfolio Lab                                         |
//| Step 2D.1: 12_UJ_Short_Core mock JST date test EA                |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
input string InpExpectedSymbol = "USDJPY";
input bool   InpAllowOtherSymbol = false;

input double InpFixedLot = 0.01;
input int    InpMagicNumber = 12001;

input int    InpJstOffsetHours = 6;
input int    InpSlippagePoints = 30;
input int    InpEntryWindowMinutes = 2;
input bool   InpPrintDebug = true;

// Test mode
input bool   InpTestMode = true;
input bool   InpTestModeIgnoreDateRules = false;
input bool   InpUseTestTimes = false;

// Mock JST datetime test
input bool   InpUseMockJstDateTime = true;
input int    InpMockYear = 2026;
input int    InpMockMonth = 2;
input int    InpMockDay = 20;
input int    InpMockHour = 9;
input int    InpMockMinute = 55;

// Mode force
input bool   InpForceGotoMode = false;
input bool   InpForceNormalMode = false;

// Test times
input int    InpTestEntryHourJST = 12;
input int    InpTestEntryMinuteJST = 0;
input int    InpTestExitHourJST = 12;
input int    InpTestExitMinuteJST = 5;

// Normal production settings
input int    InpNormalEntryHourJST = 8;
input int    InpNormalEntryMinuteJST = 4;

input int    InpGotoEntryHourJST = 9;
input int    InpGotoEntryMinuteJST = 55;

input int    InpExitHourJST = 14;
input int    InpExitMinuteJST = 56;

input double InpNormalSLPips = 50.0;
input double InpNormalTPPips = 0.0;

input double InpGotoSLPips = 20.0;
input double InpGotoTPPips = 50.0;

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

void PrintDebug(string message)
{
   if(InpPrintDebug)
   {
      Print("[Step2D.1 12_UJ_Short_Core] ", message);
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

double GetPipSize()
{
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   if(digits == 3 || digits == 5)
   {
      return point * 10.0;
   }

   return point;
}

double NormalizeLot(double lot)
{
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

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

string EntryGlobalVariableName(int date_key)
{
   string name = "TE_STEP2D1_12_UJ_SHORT_CORE_" + _Symbol + "_" + IntegerToString(InpMagicNumber) + "_" + IntegerToString(date_key);

   return name;
}

bool AlreadyEnteredToday(datetime jst_time)
{
   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(key);

   if(GlobalVariableCheck(gv_name))
   {
      return true;
   }

   return false;
}

void MarkEnteredToday(datetime jst_time)
{
   int key = DateKey(jst_time);
   string gv_name = EntryGlobalVariableName(key);

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

bool HasOpenPosition()
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

      string symbol = PositionGetString(POSITION_SYMBOL);
      long magic = PositionGetInteger(POSITION_MAGIC);

      if(symbol == _Symbol && magic == InpMagicNumber)
      {
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| 12_UJ_Short_Core date rules                                      |
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

bool IsGotoDay(int day)
{
   // Backtest reproduction only.
   // No forward-shift goto day handling in Step 2D.1.
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

bool IsActiveDate(datetime jst_time)
{
   if(InpTestMode && InpTestModeIgnoreDateRules)
   {
      return true;
   }

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   // Active only from 20th to month end.
   if(dt.day < 20)
   {
      PrintDebug("Date rule reject: before 20th. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop 21st / 22nd.
   if(dt.day == 21)
   {
      PrintDebug("Date rule reject: 21st stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   if(dt.day == 22)
   {
      PrintDebug("Date rule reject: 22nd stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop August.
   if(dt.mon == 8)
   {
      PrintDebug("Date rule reject: August stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop Wednesday. Sunday=0, Monday=1, Tuesday=2, Wednesday=3.
   if(dt.day_of_week == 3)
   {
      PrintDebug("Date rule reject: Wednesday stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   // Stop calendar month end.
   if(IsCalendarMonthEnd(dt))
   {
      PrintDebug("Date rule reject: calendar month end stop. JST=" + DateTimeText(jst_time));
      return false;
   }

   return true;
}

int GetTradeMode(datetime jst_time)
{
   // 1 = goto mode
   // 2 = normal mode
   // 0 = invalid

   if(InpForceGotoMode && InpForceNormalMode)
   {
      return 0;
   }

   if(InpForceGotoMode)
   {
      return 1;
   }

   if(InpForceNormalMode)
   {
      return 2;
   }

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(IsGotoDay(dt.day))
   {
      return 1;
   }

   return 2;
}

int GetEntryHour(datetime jst_time)
{
   if(InpTestMode && InpUseTestTimes)
   {
      return InpTestEntryHourJST;
   }

   int mode = GetTradeMode(jst_time);

   if(mode == 1)
   {
      return InpGotoEntryHourJST;
   }

   return InpNormalEntryHourJST;
}

int GetEntryMinute(datetime jst_time)
{
   if(InpTestMode && InpUseTestTimes)
   {
      return InpTestEntryMinuteJST;
   }

   int mode = GetTradeMode(jst_time);

   if(mode == 1)
   {
      return InpGotoEntryMinuteJST;
   }

   return InpNormalEntryMinuteJST;
}

int GetExitHour()
{
   if(InpTestMode && InpUseTestTimes)
   {
      return InpTestExitHourJST;
   }

   return InpExitHourJST;
}

int GetExitMinute()
{
   if(InpTestMode && InpUseTestTimes)
   {
      return InpTestExitMinuteJST;
   }

   return InpExitMinuteJST;
}

double GetSLPips(datetime jst_time)
{
   int mode = GetTradeMode(jst_time);

   if(mode == 1)
   {
      return InpGotoSLPips;
   }

   return InpNormalSLPips;
}

double GetTPPips(datetime jst_time)
{
   int mode = GetTradeMode(jst_time);

   if(mode == 1)
   {
      return InpGotoTPPips;
   }

   return InpNormalTPPips;
}

string GetModeText(datetime jst_time)
{
   int mode = GetTradeMode(jst_time);

   if(mode == 1)
   {
      return "GOTO";
   }

   if(mode == 2)
   {
      return "NORMAL";
   }

   return "INVALID";
}

bool IsEntryTime(datetime jst_time)
{
   if(!IsActiveDate(jst_time))
   {
      return false;
   }

   int mode = GetTradeMode(jst_time);

   if(mode == 0)
   {
      PrintDebug("Invalid mode: both InpForceGotoMode and InpForceNormalMode are true.");
      return false;
   }

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int entry_hour = GetEntryHour(jst_time);
   int entry_minute = GetEntryMinute(jst_time);

   if(dt.hour != entry_hour)
   {
      PrintDebug("Time reject: hour mismatch. JST=" + DateTimeText(jst_time) + ", ExpectedHour=" + IntegerToString(entry_hour));
      return false;
   }

   if(dt.min < entry_minute)
   {
      PrintDebug("Time reject: before entry minute. JST=" + DateTimeText(jst_time) + ", ExpectedMinute=" + IntegerToString(entry_minute));
      return false;
   }

   if(dt.min >= entry_minute + InpEntryWindowMinutes)
   {
      PrintDebug("Time reject: outside entry window. JST=" + DateTimeText(jst_time) + ", EntryMinute=" + IntegerToString(entry_minute));
      return false;
   }

   return true;
}

bool IsExitTime(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   int exit_hour = GetExitHour();
   int exit_minute = GetExitMinute();

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

//+------------------------------------------------------------------+
//| Trading                                                          |
//+------------------------------------------------------------------+
void TryEntry()
{
   if(!IsCorrectSymbol())
   {
      PrintDebug("Symbol mismatch. Current=" + _Symbol + ", Expected=" + InpExpectedSymbol);
      return;
   }

   datetime jst_time = GetJstTime();

   if(!IsEntryTime(jst_time))
   {
      return;
   }

   if(AlreadyEnteredToday(jst_time))
   {
      PrintDebug("Skip entry: already entered today.");
      return;
   }

   if(HasOpenPosition())
   {
      PrintDebug("Skip entry: position already exists.");
      return;
   }

   double lot = NormalizeLot(InpFixedLot);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double pip = GetPipSize();

   if(bid <= 0)
   {
      PrintDebug("Skip entry: invalid BID.");
      return;
   }

   double sl_pips = GetSLPips(jst_time);
   double tp_pips = GetTPPips(jst_time);

   double sl = bid + sl_pips * pip;
   double tp = 0.0;

   if(tp_pips > 0)
   {
      tp = bid - tp_pips * pip;
   }

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   sl = NormalizeDouble(sl, digits);

   if(tp > 0)
   {
      tp = NormalizeDouble(tp, digits);
   }

   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippagePoints);

   string mode_text = GetModeText(jst_time);
   string comment = "12_UJ_Short_Core_step2d1_" + mode_text;

   bool result = trade.Sell(lot, _Symbol, bid, sl, tp, comment);

   if(result)
   {
      MarkEnteredToday(jst_time);

      if(tp > 0)
      {
         PrintDebug("SELL entry success. Mode=" + mode_text + ", JST=" + DateTimeText(jst_time) + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
      }
      else
      {
         PrintDebug("SELL entry success. Mode=" + mode_text + ", JST=" + DateTimeText(jst_time) + ", Lot=" + DoubleToString(lot, 2) + ", Bid=" + DoubleToString(bid, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=None");
      }
   }
   else
   {
      int retcode = (int)trade.ResultRetcode();
      string desc = trade.ResultRetcodeDescription();

      PrintDebug("SELL entry failed. Retcode=" + IntegerToString(retcode) + ", " + desc);
   }
}

void TryExit()
{
   datetime jst_time = GetJstTime();

   if(!IsExitTime(jst_time))
   {
      return;
   }

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

      string symbol = PositionGetString(POSITION_SYMBOL);
      long magic = PositionGetInteger(POSITION_MAGIC);

      if(symbol != _Symbol)
      {
         continue;
      }

      if(magic != InpMagicNumber)
      {
         continue;
      }

      trade.SetExpertMagicNumber(InpMagicNumber);
      trade.SetDeviationInPoints(InpSlippagePoints);

      bool result = trade.PositionClose(ticket);

      if(result)
      {
         PrintDebug("Time exit success. JST=" + DateTimeText(jst_time) + ", Ticket=" + IntegerToString((int)ticket));
      }
      else
      {
         int retcode = (int)trade.ResultRetcode();
         string desc = trade.ResultRetcodeDescription();

         PrintDebug("Time exit failed. Ticket=" + IntegerToString((int)ticket) + ", Retcode=" + IntegerToString(retcode) + ", " + desc);
      }
   }
}

//+------------------------------------------------------------------+
//| Expert Events                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippagePoints);

   EventSetTimer(10);

   PrintDebug("EA initialized.");
   PrintDebug("Symbol=" + _Symbol);
   PrintDebug("ExpectedSymbol=" + InpExpectedSymbol);
   PrintDebug("JST Offset Hours=" + IntegerToString(InpJstOffsetHours));
   PrintDebug("MagicNumber=" + IntegerToString(InpMagicNumber));
   PrintDebug("FixedLot=" + DoubleToString(InpFixedLot, 2));
   PrintDebug("TestMode=" + BoolText(InpTestMode));
   PrintDebug("IgnoreDateRules=" + BoolText(InpTestModeIgnoreDateRules));
   PrintDebug("UseTestTimes=" + BoolText(InpUseTestTimes));
   PrintDebug("UseMockJstDateTime=" + BoolText(InpUseMockJstDateTime));
   PrintDebug("MockJST=" + DateTimeText(BuildMockJstTime()));
   PrintDebug("ForceGotoMode=" + BoolText(InpForceGotoMode));
   PrintDebug("ForceNormalMode=" + BoolText(InpForceNormalMode));
   PrintDebug("GotoDay=20/25/30 calendar day only. No forward goto day.");

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();

   PrintDebug("EA deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
   TryExit();
   TryEntry();
}

void OnTimer()
{
   TryExit();
   TryEntry();
}
