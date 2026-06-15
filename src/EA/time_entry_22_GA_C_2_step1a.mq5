//+------------------------------------------------------------------+
//| time_entry_22_GA_C_2_step1a.mq5                                  |
//| Time Entry Portfolio Lab                                         |
//| Step 1A: 22_GA_C_2 single strategy EA                            |
//+------------------------------------------------------------------+
#property strict

#include <Trade/Trade.mqh>

CTrade trade;

//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
input string InpExpectedSymbol = "GBPAUD";
input bool   InpAllowOtherSymbol = false;

input double InpFixedLot = 0.01;
input int    InpMagicNumber = 22002;

input int    InpJstOffsetHours = 6;

input int    InpEntryWeekdayJST = 4;      // Sunday=0, Monday=1, ... Thursday=4
input int    InpEntryHourJST = 16;
input int    InpEntryMinuteJST = 56;

input int    InpExitWeekdayJST = 5;       // Friday=5
input int    InpExitHourJST = 1;
input int    InpExitMinuteJST = 15;

input double InpSLPips = 70.0;
input double InpTPPips = 80.0;

input int    InpEntryWindowMinutes = 2;
input int    InpSlippagePoints = 30;

input bool   InpPrintDebug = true;

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

void PrintDebug(string message)
{
   if(InpPrintDebug)
   {
      Print("[22_GA_C_2 Step1A] ", message);
   }
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
   string name = "TE_22_GA_C_2_STEP1A_" + _Symbol + "_" + IntegerToString(InpMagicNumber) + "_" + IntegerToString(date_key);

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

int CountOpenPositions()
{
   int count = 0;
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
         count++;
      }
   }

   return count;
}

bool IsEntryTime(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.day_of_week != InpEntryWeekdayJST)
   {
      return false;
   }

   if(dt.hour != InpEntryHourJST)
   {
      return false;
   }

   if(dt.min < InpEntryMinuteJST)
   {
      return false;
   }

   if(dt.min >= InpEntryMinuteJST + InpEntryWindowMinutes)
   {
      return false;
   }

   return true;
}

bool IsExitTime(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.day_of_week != InpExitWeekdayJST)
   {
      return false;
   }

   if(dt.hour < InpExitHourJST)
   {
      return false;
   }

   if(dt.hour == InpExitHourJST && dt.min < InpExitMinuteJST)
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
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double pip = GetPipSize();

   if(ask <= 0)
   {
      PrintDebug("Skip entry: invalid ASK.");
      return;
   }

   double sl = ask - InpSLPips * pip;
   double tp = ask + InpTPPips * pip;

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);

   sl = NormalizeDouble(sl, digits);
   tp = NormalizeDouble(tp, digits);

   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippagePoints);

   string comment = "22_GA_C_2_step1a";

   bool result = trade.Buy(lot, _Symbol, ask, sl, tp, comment);

   if(result)
   {
      MarkEnteredToday(jst_time);
      PrintDebug("BUY entry success. Lot=" + DoubleToString(lot, 2) + ", Ask=" + DoubleToString(ask, digits) + ", SL=" + DoubleToString(sl, digits) + ", TP=" + DoubleToString(tp, digits));
   }
   else
   {
      int retcode = (int)trade.ResultRetcode();
      string desc = trade.ResultRetcodeDescription();

      PrintDebug("BUY entry failed. Retcode=" + IntegerToString(retcode) + ", " + desc);
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
         PrintDebug("Time exit success. Ticket=" + IntegerToString((int)ticket));
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
//| Expert events                                                    |
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
