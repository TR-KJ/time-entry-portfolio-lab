// No-order script: compare actual core output on saved CSV against Python reference.
#property strict
#property script_show_inputs
#include "vol_r2_core.mqh"
input string InpSnapshotFile="";
input datetime InpCandidateJST=D'2026.01.01';
void OnStart()
{
   if(InpSnapshotFile==""){ Print("[P5 FIXTURE] NO_INPUT"); return; }
   int h=FileOpen(InpSnapshotFile,FILE_READ|FILE_CSV|FILE_ANSI,',');
   if(h==INVALID_HANDLE){ Print("[P5 FIXTURE] OPEN_FAILED"); return; }
   string cols[6]={"ServerTime","JST","Open","High","Low","Close"};
   for(int i=0;i<6;i++)
      if(FileReadString(h)!=cols[i]){ FileClose(h); Print("[P5 FIXTURE] BAD_HEADER"); return; }
   MqlRates bars[]; int n=0;
   while(!FileIsEnding(h))
   {
      string raw=FileReadString(h); if(raw=="" && FileIsEnding(h)) break;
      string time=FileReadString(h); datetime converted=0;
      if(!P5ServerToJst(StringToTime(raw),converted) || converted!=StringToTime(time))
      { FileClose(h); Print("[P5 FIXTURE] TIMEZONE_MISMATCH"); return; }
      // Reserve blocks for real M1 exports; does not alter CSV/order or calculations.
      if(ArrayResize(bars,n+1,8192)<0)
      { FileClose(h); Print("[P5 FIXTURE] ALLOCATION_FAILED"); return; }
      bars[n].time=converted;
      bars[n].open=StringToDouble(FileReadString(h)); bars[n].high=StringToDouble(FileReadString(h));
      bars[n].low=StringToDouble(FileReadString(h)); bars[n].close=StringToDouble(FileReadString(h)); n++;
   }
   FileClose(h); P5Daily daily[]; P5Feature f;
   P5Calculate(bars,InpCandidateJST,daily,f);
   Print("[P5 FIXTURE] Status=",f.status," Reason=",f.reason," ATR20=",StringFormat("%.17g",f.atr),
      " RankNumerator=",f.numerator," Quintile=",f.q," Risk=",StringFormat("%.17g",f.risk)," Days=",f.days,
      " Adapter=OANDA_US_DST_V1");
   string out=InpSnapshotFile+".mql_daily.csv";
   if(FileIsExist(out)){ Print("[P5 FIXTURE] OUTPUT_EXISTS"); return; }
   h=FileOpen(out,FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(h==INVALID_HANDLE){ Print("[P5 FIXTURE] OUTPUT_FAILED"); return; }
   FileWrite(h,"JST","Open","High","Low","Close","TR","ATR20","M1Count");
   for(int i=0;i<ArraySize(daily);i++)
      FileWrite(h,TimeToString(daily[i].day,TIME_DATE|TIME_SECONDS),StringFormat("%.17g",daily[i].open),
         StringFormat("%.17g",daily[i].high),StringFormat("%.17g",daily[i].low),StringFormat("%.17g",daily[i].close),
         StringFormat("%.17g",daily[i].tr),StringFormat("%.17g",daily[i].atr),daily[i].count);
   FileClose(h); Print("[P5 FIXTURE] OUTPUT=",out," NO_ORDERS=true");
}
