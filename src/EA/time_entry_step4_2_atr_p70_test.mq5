//+------------------------------------------------------------------+
//| time_entry_step4_2_atr_p70_test.mq5                              |
//| Time Entry Portfolio Lab                                         |
//| Step 4.2: ATR P70 single test EA                                 |
//|                                                                  |
//| Purpose:                                                         |
//| - Test H1 ATR value acquisition                                  |
//| - Test ATR P70 calculation                                       |
//| - Print ATR / P70 / pass result                                  |
//| - No trading                                                     |
//+------------------------------------------------------------------+
#property strict

//+------------------------------------------------------------------+
//| Inputs                                                           |
//+------------------------------------------------------------------+
input string          InpTestSymbol = "GBPJPY";
input ENUM_TIMEFRAMES InpAtrTimeframe = PERIOD_H1;

input int             InpAtrPeriod = 14;
input int             InpAtrP70LookbackBars = 500;
input double          InpPercentile = 70.0;

input bool            InpUseClosedBar = true;

input bool            InpPrintOnInit = true;
input bool            InpPrintEveryTimer = true;
input int             InpTimerSeconds = 10;

//+------------------------------------------------------------------+
//| Globals                                                          |
//+------------------------------------------------------------------+
int atr_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Logging                                                          |
//+------------------------------------------------------------------+
void PrintDebug(string message)
{
   Print("[ATR P70 Test] ", message);
}

string BoolText(bool value)
{
   if(value)
   {
      return "true";
   }

   return "false";
}

string TimeframeText(ENUM_TIMEFRAMES tf)
{
   if(tf == PERIOD_M1)
   {
      return "M1";
   }

   if(tf == PERIOD_M5)
   {
      return "M5";
   }

   if(tf == PERIOD_M15)
   {
      return "M15";
   }

   if(tf == PERIOD_M30)
   {
      return "M30";
   }

   if(tf == PERIOD_H1)
   {
      return "H1";
   }

   if(tf == PERIOD_H4)
   {
      return "H4";
   }

   if(tf == PERIOD_D1)
   {
      return "D1";
   }

   return IntegerToString((int)tf);
}

//+------------------------------------------------------------------+
//| Symbol / pip helpers                                             |
//+------------------------------------------------------------------+
bool EnsureSymbolReady(string symbol)
{
   if(!SymbolSelect(symbol, true))
   {
      PrintDebug("SymbolSelect failed. Symbol=" + symbol);
      return false;
   }

   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);

   if(point <= 0)
   {
      PrintDebug("Invalid symbol point. Symbol=" + symbol);
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

//+------------------------------------------------------------------+
//| ATR handle                                                       |
//+------------------------------------------------------------------+
bool CreateAtrHandle()
{
   if(atr_handle != INVALID_HANDLE)
   {
      IndicatorRelease(atr_handle);
      atr_handle = INVALID_HANDLE;
   }

   atr_handle = iATR(InpTestSymbol, InpAtrTimeframe, InpAtrPeriod);

   if(atr_handle == INVALID_HANDLE)
   {
      PrintDebug("ATR handle create failed. Symbol=" + InpTestSymbol);
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Percentile                                                       |
//+------------------------------------------------------------------+
bool CalculatePercentile(double &values[], int count, double percentile, double &result)
{
   if(count <= 0)
   {
      return false;
   }

   if(percentile < 0.0)
   {
      percentile = 0.0;
   }

   if(percentile > 100.0)
   {
      percentile = 100.0;
   }

   ArrayResize(values, count);
   ArraySort(values);

   double ratio = percentile / 100.0;
   int index = (int)MathFloor((count - 1) * ratio);

   if(index < 0)
   {
      index = 0;
   }

   if(index >= count)
   {
      index = count - 1;
   }

   result = values[index];

   return true;
}

//+------------------------------------------------------------------+
//| ATR / P70 calculation                                            |
//+------------------------------------------------------------------+
bool GetCurrentAtr(double &current_atr)
{
   if(atr_handle == INVALID_HANDLE)
   {
      PrintDebug("ATR handle is invalid.");
      return false;
   }

   int start_pos = 0;

   if(InpUseClosedBar)
   {
      start_pos = 1;
   }

   double atr_one[];

   ArraySetAsSeries(atr_one, true);
   ArrayResize(atr_one, 1);

   int copied = CopyBuffer(atr_handle, 0, start_pos, 1, atr_one);

   if(copied != 1)
   {
      PrintDebug("CopyBuffer current ATR failed. Copied=" + IntegerToString(copied));
      return false;
   }

   current_atr = atr_one[0];

   if(current_atr <= 0)
   {
      PrintDebug("Invalid current ATR value. ATR=" + DoubleToString(current_atr, 10));
      return false;
   }

   return true;
}

bool GetAtrP70(double &p70_value, int &copied_bars)
{
   copied_bars = 0;

   if(atr_handle == INVALID_HANDLE)
   {
      PrintDebug("ATR handle is invalid.");
      return false;
   }

   if(InpAtrP70LookbackBars <= 0)
   {
      PrintDebug("Invalid lookback bars. Lookback=" + IntegerToString(InpAtrP70LookbackBars));
      return false;
   }

   int start_pos = 0;

   if(InpUseClosedBar)
   {
      start_pos = 1;
   }

   double atr_values[];

   ArraySetAsSeries(atr_values, true);
   ArrayResize(atr_values, InpAtrP70LookbackBars);

   int copied = CopyBuffer(atr_handle, 0, start_pos, InpAtrP70LookbackBars, atr_values);

   copied_bars = copied;

   if(copied <= 0)
   {
      PrintDebug("CopyBuffer P70 ATR failed. Copied=" + IntegerToString(copied));
      return false;
   }

   if(copied < InpAtrP70LookbackBars)
   {
      PrintDebug("Not enough ATR bars. Requested=" + IntegerToString(InpAtrP70LookbackBars) + ", Copied=" + IntegerToString(copied));
      return false;
   }

   double sorted_values[];

   ArrayResize(sorted_values, copied);

   for(int i = 0; i < copied; i++)
   {
      sorted_values[i] = atr_values[i];
   }

   bool percentile_ok = CalculatePercentile(sorted_values, copied, InpPercentile, p70_value);

   if(!percentile_ok)
   {
      PrintDebug("Percentile calculation failed.");
      return false;
   }

   if(p70_value <= 0)
   {
      PrintDebug("Invalid P70 value. P70=" + DoubleToString(p70_value, 10));
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Report                                                           |
//+------------------------------------------------------------------+
void PrintAtrReport()
{
   if(!EnsureSymbolReady(InpTestSymbol))
   {
      return;
   }

   if(atr_handle == INVALID_HANDLE)
   {
      if(!CreateAtrHandle())
      {
         return;
      }
   }

   int bars_available = Bars(InpTestSymbol, InpAtrTimeframe);

   double current_atr = 0.0;
   double p70_value = 0.0;
   int copied_bars = 0;

   bool atr_ok = GetCurrentAtr(current_atr);
   bool p70_ok = GetAtrP70(p70_value, copied_bars);

   if(!atr_ok || !p70_ok)
   {
      PrintDebug("ATR report failed. ATR_OK=" + BoolText(atr_ok) + ", P70_OK=" + BoolText(p70_ok));
      PrintDebug("Symbol=" + InpTestSymbol + ", Timeframe=" + TimeframeText(InpAtrTimeframe) + ", BarsAvailable=" + IntegerToString(bars_available));
      return;
   }

   double current_atr_pips = ToPips(InpTestSymbol, current_atr);
   double p70_pips = ToPips(InpTestSymbol, p70_value);

   bool pass_atr = false;

   if(current_atr >= p70_value)
   {
      pass_atr = true;
   }

   int digits = (int)SymbolInfoInteger(InpTestSymbol, SYMBOL_DIGITS);

   PrintDebug("--------------------------------------------------");
   PrintDebug("Symbol=" + InpTestSymbol);
   PrintDebug("Timeframe=" + TimeframeText(InpAtrTimeframe));
   PrintDebug("ATR Period=" + IntegerToString(InpAtrPeriod));
   PrintDebug("P" + DoubleToString(InpPercentile, 1) + " Lookback=" + IntegerToString(InpAtrP70LookbackBars));
   PrintDebug("UseClosedBar=" + BoolText(InpUseClosedBar));
   PrintDebug("BarsAvailable=" + IntegerToString(bars_available));
   PrintDebug("CopiedBars=" + IntegerToString(copied_bars));
   PrintDebug("CurrentATR=" + DoubleToString(current_atr, digits));
   PrintDebug("CurrentATR_Pips=" + DoubleToString(current_atr_pips, 1));
   PrintDebug("P70=" + DoubleToString(p70_value, digits));
   PrintDebug("P70_Pips=" + DoubleToString(p70_pips, 1));
   PrintDebug("PassATR_CurrentATR_GTE_P70=" + BoolText(pass_atr));
}

//+------------------------------------------------------------------+
//| Expert events                                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   if(!EnsureSymbolReady(InpTestSymbol))
   {
      return INIT_FAILED;
   }

   if(!CreateAtrHandle())
   {
      return INIT_FAILED;
   }

   if(InpTimerSeconds > 0)
   {
      EventSetTimer(InpTimerSeconds);
   }

   PrintDebug("ATR P70 Test initialized.");
   PrintDebug("Symbol=" + InpTestSymbol);
   PrintDebug("Timeframe=" + TimeframeText(InpAtrTimeframe));
   PrintDebug("ATR Period=" + IntegerToString(InpAtrPeriod));
   PrintDebug("P70 Lookback=" + IntegerToString(InpAtrP70LookbackBars));
   PrintDebug("Percentile=" + DoubleToString(InpPercentile, 1));
   PrintDebug("UseClosedBar=" + BoolText(InpUseClosedBar));
   PrintDebug("PrintEveryTimer=" + BoolText(InpPrintEveryTimer));
   PrintDebug("TimerSeconds=" + IntegerToString(InpTimerSeconds));

   if(InpPrintOnInit)
   {
      PrintAtrReport();
   }

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();

   if(atr_handle != INVALID_HANDLE)
   {
      IndicatorRelease(atr_handle);
      atr_handle = INVALID_HANDLE;
   }

   PrintDebug("ATR P70 Test deinitialized. Reason=" + IntegerToString(reason));
}

void OnTick()
{
}

void OnTimer()
{
   if(InpPrintEveryTimer)
   {
      PrintAtrReport();
   }
}
