// Script: tests the ACTUAL shared MQL core without placing any orders.
// This script is not an EA; do not enable test/mock flags in the forward EA.
#property strict
#property script_show_inputs
#include "vol_r2_core.mqh"
int passed=0,failed=0;
void Check(bool ok,string name)
{
   if(ok) passed++; else failed++;
   Print("[P5 CORE TEST] ",name,"=",ok?"PASS":"FAIL");
}
void Fill(MqlRates &bars[],int count)
{
   ArrayResize(bars,count);
   for(int i=0;i<count;i++)
   {
      bars[i].time=D'2025.01.01 12:00:00'+i*86400;
      bars[i].open=129; bars[i].high=130; bars[i].low=128; bars[i].close=129;
   }
}
void OnStart()
{
   MqlRates b[]; P5Daily d[]; P5Feature f; P5Lot l;
   datetime when=D'2026.01.01';
   Fill(b,271); Check(!P5Calculate(b,when,d,f) && f.risk==.9,"271 fallback");
   Fill(b,272); Check(P5Calculate(b,when,d,f) && f.q==3 && f.numerator==252 && f.atr==2,"272 tie Q3");
   Check(ArraySize(d)==272 && d[3].day==D'2025.01.04',"actual Saturday included");
   b[271].high=150; Check(P5Calculate(b,when,d,f) && f.q==5,"Q5");
   b[271].high=129; Check(P5Calculate(b,when,d,f) && f.q==1,"Q1");
   Fill(b,272); ArrayResize(b,273); b[272]=b[271]; b[272].time=when; b[272].close=-1;
   Check(P5Calculate(b,when,d,f) && f.q==3,"current invalid bar excluded");
   b[272].time=when+86400; Check(P5Calculate(b,when,d,f) && f.q==3,"future invalid bar excluded");
   b[272]=b[271]; Check(!P5Calculate(b,when,d,f) && f.reason=="DUPLICATE_OR_UNSORTED_M1","duplicate fallback");
   Fill(b,272); b[10].low=-1; Check(!P5Calculate(b,when,d,f) && f.risk==.9,"invalid OHLC fallback");
   Fill(b,272); b[271].time=D'2025.09.29 23:59';
   Check(!P5Calculate(b,D'2025.09.29 23:59:59',d,f),"incomplete daily excluded");
   Check(P5Calculate(b,D'2025.09.30 00:00',d,f),"next midnight eligible");
   bool ranks=true;
   for(int n=0;n<=504;n++)
   {
      double p=100.0*n/504.0;
      int q=1+(p>=20?1:0)+(p>=40?1:0)+(p>=60?1:0)+(p>=80?1:0);
      if(P5Quintile(n)!=q) ranks=false;
   }
   Check(ranks,"505 numerator bins");
   Check(P5Risk(1)==.5 && P5Risk(2)==.7 && P5Risk(3)==.9 && P5Risk(4)==1.1 && P5Risk(5)==1.3 && P5Risk(0)==.9,"risk table");
   Check(P5Size(1000000,.9,50,1000,.01,10,.01,1,l) && l.final_lot==.18,"ordinary lot");
   Check(P5Size(100000000,.9,50,1000,.01,10,.01,1,l) && l.cap && l.final_lot==1,"lot cap");
   Check(!P5Size(1,.9,50,1000,.01,10,.01,1,l) && l.min_stop && l.final_lot==0,"min stop");
   Check(!P5Size(1000000,.9,0,1000,.01,10,.01,1,l),"zero SL");
   Check(!P5Size(1000000,.9,50,1000,.01,10,.001,1,l),"unapproved step");
   Check(P5Size(100,.5,50,1,.01,10,.01,1,l) && l.final_lot==.01,"exact min");
   datetime jst;
   Check(P5ServerToJst(D'2026.03.29 02:59',jst) && jst==D'2026.03.29 09:59',"DST before spring");
   Check(P5ServerToJst(D'2026.03.29 04:00',jst) && jst==D'2026.03.29 10:00',"DST after spring");
   Check(!P5ServerToJst(D'2026.03.29 03:30',jst),"nonexistent hour fallback");
   Check(!P5ServerToJst(D'2026.10.25 03:30',jst),"ambiguous hour fallback");
   Check(P5ServerToJst(D'2026.10.25 04:00',jst) && jst==D'2026.10.25 11:00',"DST after autumn");
   Print("[P5 CORE TEST] SUMMARY Passed=",passed," Failed=",failed," NO_ORDERS=true");
}
