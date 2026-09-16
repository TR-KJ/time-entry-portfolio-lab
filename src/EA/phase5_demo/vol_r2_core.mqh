// Frozen Phase5 mathematical core. No terminal access or orders.
#ifndef P5_VOL_CORE
#define P5_VOL_CORE
struct P5Daily
{
   datetime day,last;
   double open,high,low,close,tr,atr;
   int count;
};
struct P5Feature
{
   string status,reason;
   double atr,percent,risk;
   int numerator,q,days,bars;
   datetime day,last,available,ref_start,ref_end;
};
void P5Empty(P5Feature &f,string reason)
{
   f.status="FALLBACK"; f.reason=reason; f.atr=0; f.percent=0;
   f.risk=0.90; f.numerator=-1; f.q=0; f.days=0; f.bars=0;
   f.day=0; f.last=0; f.available=0; f.ref_start=0; f.ref_end=0;
}
datetime P5Midnight(datetime t)
{
   MqlDateTime d; TimeToStruct(t,d); d.hour=0; d.min=0; d.sec=0;
   return StructToTime(d);
}
datetime P5LastSunday(int year,int month)
{
   MqlDateTime d; ZeroMemory(d); d.year=year; d.mon=month; d.day=31;
   datetime t=StructToTime(d); TimeToStruct(t,d);
   return t-d.day_of_week*86400;
}
// EU rule in force throughout the research period: last Sunday 01:00 UTC.
int P5UtcOffset(datetime utc)
{
   MqlDateTime d; TimeToStruct(utc,d);
   datetime a=P5LastSunday(d.year,3)+3600;
   datetime b=P5LastSunday(d.year,10)+3600;
   return (utc>=a && utc<b)?3:2;
}
bool P5ServerToJst(datetime server,datetime &jst)
{
   datetime u2=server-7200,u3=server-10800;
   bool a=P5UtcOffset(u2)==2,b=P5UtcOffset(u3)==3;
   // Ambiguous/nonexistent local hour cannot be inferred from a lone timestamp.
   if(a==b) return false;
   jst=(a?u2:u3)+32400; return true;
}
datetime P5JstToServer(datetime jst)
{
   datetime utc=jst-32400; return utc+P5UtcOffset(utc)*3600;
}
int P5Quintile(int n)
{
   if(n<0 || n>504) return 0;
   if(5*n<504) return 1;
   if(5*n<1008) return 2;
   if(5*n<1512) return 3;
   if(5*n<2016) return 4;
   return 5;
}
double P5Risk(int q)
{
   if(q==1) return 0.50; if(q==2) return 0.70;
   if(q==4) return 1.10; if(q==5) return 1.30; return 0.90;
}
bool P5Positive(double x){ return MathIsValidNumber(x) && x>0; }
// Input bars already in JST. Current/future bars are excluded before OHLC validation.
bool P5Calculate(MqlRates &bars[],datetime candidate,P5Daily &daily[],P5Feature &f)
{
   P5Empty(f,"INSUFFICIENT_VOL_HISTORY"); ArrayResize(daily,0);
   datetime cutoff=P5Midnight(candidate),previous=0;
   int n=0;
   for(int i=0;i<ArraySize(bars);i++)
   {
      datetime t=bars[i].time;
      if(t>=cutoff || t+60>candidate) continue;
      if(t<=previous){ P5Empty(f,"DUPLICATE_OR_UNSORTED_M1"); return false; }
      previous=t;
      double o=bars[i].open,h=bars[i].high,l=bars[i].low,c=bars[i].close;
      if(!P5Positive(o)||!P5Positive(h)||!P5Positive(l)||!P5Positive(c)||h<MathMax(o,c)||l>MathMin(o,c)||h<l)
      { P5Empty(f,"INVALID_OHLC"); return false; }
      datetime day=P5Midnight(t);
      if(n==0 || daily[n-1].day!=day)
      {
         n++; ArrayResize(daily,n);
         daily[n-1].day=day; daily[n-1].open=o;
         daily[n-1].high=h; daily[n-1].low=l; daily[n-1].count=0;
      }
      daily[n-1].high=MathMax(daily[n-1].high,h);
      daily[n-1].low=MathMin(daily[n-1].low,l);
      daily[n-1].close=c; daily[n-1].last=t; daily[n-1].count++;
      f.bars++;
   }
   f.days=n;
   for(int i=0;i<n;i++)
   {
      double tr=daily[i].high-daily[i].low;
      if(i>0) tr=MathMax(tr,MathMax(MathAbs(daily[i].high-daily[i-1].close),MathAbs(daily[i].low-daily[i-1].close)));
      daily[i].tr=tr; daily[i].atr=0;
      if(i>=19)
      {
         // Compensated rolling-window sum, no price rounding before rank comparisons.
         double sum=0,comp=0;
         for(int j=i-19;j<=i;j++)
         { double y=daily[j].tr-comp; double v=sum+y; comp=(v-sum)-y; sum=v; }
         daily[i].atr=sum/20.0;
      }
   }
   if(n<272) return false;
   int k=n-1,rank=0;
   double value=daily[k].atr;
   if(!MathIsValidNumber(value)){ f.reason="NONFINITE_ATR"; return false; }
   for(int i=k-252;i<k;i++)
   {
      if(!MathIsValidNumber(daily[i].atr)){ f.reason="NONFINITE_REFERENCE"; return false; }
      if(daily[i].atr<value) rank+=2;
      else if(daily[i].atr==value) rank++;
   }
   f.status="VALID"; f.reason=""; f.atr=value; f.numerator=rank;
   f.percent=100.0*rank/504.0; f.q=P5Quintile(rank); f.risk=P5Risk(f.q);
   f.day=daily[k].day; f.last=daily[k].last; f.available=f.day+86400;
   f.ref_start=daily[k-252].day; f.ref_end=daily[k-1].day;
   return true;
}
struct P5Lot
{
   double amount,raw,capped,final_lot;
   bool cap,min_stop;
   string reason;
};
bool P5Size(double base,double risk,double sl,double pipvalue,double minimum,double maximum,double step,double cap,P5Lot &r)
{
   r.amount=0; r.raw=0; r.capped=0; r.final_lot=0; r.cap=false; r.min_stop=false; r.reason="";
   if(!P5Positive(base)||!P5Positive(risk)||!P5Positive(sl)||!P5Positive(pipvalue))
   { r.reason="INVALID_BASE_RISK_SL_PIPVALUE"; return false; }
   if(minimum!=0.01 || maximum!=10.0 || step!=0.01 || cap!=1.0)
   { r.reason="UNAPPROVED_VOLUME_SPEC"; return false; }
   r.amount=base*risk/100.0; r.raw=r.amount/(sl*pipvalue);
   if(!P5Positive(r.amount)||!P5Positive(r.raw)){ r.reason="NONFINITE_LOT"; return false; }
   if(r.raw<minimum){ r.min_stop=true; r.reason="BELOW_MINIMUM"; return false; }
   r.cap=r.raw>cap; r.capped=MathMin(r.raw,cap);
   r.final_lot=NormalizeDouble(MathFloor(MathMin(maximum,MathMax(minimum,r.capped))/step)*step,2);
   if(r.final_lot<minimum || r.final_lot>cap || r.final_lot>maximum)
   { r.final_lot=0; r.reason="INVALID_FINAL_LOT"; return false; }
   return true;
}
#endif
