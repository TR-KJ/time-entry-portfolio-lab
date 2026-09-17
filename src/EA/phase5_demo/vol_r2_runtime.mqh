// Included after the dedicated Step9.2.1 dependency and before Step9.2.4 methods.
// Functions declared later are resolved by the MQL compiler; runtime compile remains required.
P5Feature p5_features[28];
string p5_candidate[28],p5_snapshot[28],p5_last_decision[28];
string p5_position_candidate[28];
int p5_position_attempt[28];
int p5_attempt[28];
bool p5_loaded[28];
datetime p5_cache_day[28],p5_cache_start[28],p5_cache_end[28];
int p5_cache_count[28];
string p5_week_action="NOT_REQUESTED";
double p5_equity=0,p5_balance=0;

string P5Num(double n){ return StringFormat("%.17g",n); }
string P5Time(datetime t){ return t>0?TimeToString(t,TIME_DATE|TIME_SECONDS):"NOT_AVAILABLE"; }
uint P5Hash(string s)
{
   uint h=2166136261;
   for(int i=0;i<StringLen(s);i++){ h^=StringGetCharacter(s,i); h*=16777619; }
   return h;
}
string P5GV(string kind,string suffix)
{
   string prefix="P5R2_"+IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN))+"_"+
      IntegerToString((long)P5Hash(AccountInfoString(ACCOUNT_SERVER)))+"_"+kind+"_";
   if(StringLen(prefix+suffix)>63) suffix=IntegerToString((long)P5Hash(suffix));
   return prefix+suffix;
}
bool P5Guard()
{
   return InpPhase5Approved && InpPhase5DemoLogin>0 && InpPhase5DemoServer!="" &&
      AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_DEMO &&
      AccountInfoInteger(ACCOUNT_LOGIN)==InpPhase5DemoLogin &&
      AccountInfoString(ACCOUNT_SERVER)==InpPhase5DemoServer;
}
datetime P5Now()
{
   datetime jst=0,server=TimeTradeServer();
   if(server<=0) server=TimeCurrent();
   if(!InpPhase5OandaTimeVerified || !P5ServerToJst(server,jst)) return 0;
   return jst;
}
int P5Index(StrategyConfig &cfg)
{
   for(int i=0;i<ArraySize(strategies);i++)
      if(strategies[i].magic==cfg.magic && strategies[i].symbol==cfg.symbol) return i;
   return -1;
}
void P5Emit(StrategyConfig &cfg,string event,string fields)
{
   if(!InpPrintVolR2Diagnostics) return;
   int i=P5Index(cfg); if(i<0) return;
   if(event=="ORDER_ATTEMPT"){ p5_position_candidate[i]=p5_candidate[i]; p5_position_attempt[i]=p5_attempt[i]; }
   bool position_event=StringFind(event,"EXIT_")==0 || event=="DEAL_ADD";
   string id=position_event?p5_position_candidate[i]:p5_candidate[i];
   int attempt=position_event?p5_position_attempt[i]:p5_attempt[i];
   Print("[P5] SchemaVersion=1|RunId=",InpPhase5RunId,"|CandidateId=",id,
      "|AttemptId=",attempt,"|EventType=",event,"|StrategyNo=",StringToInteger(cfg.strategy_name),
      "|StrategyName=",cfg.strategy_name,"|Magic=",cfg.magic,"|Symbol=",cfg.symbol,
      "|ObservedAtJST=",P5Time(P5Now()),"|",fields);
}
// All input evidence exports are in this demo terminal's MQL5/Files only.
// A new candidate gets its own immutable file: expensive but no stale-cache reuse.
bool P5Export(string file,MqlRates &bars[],datetime &raw_times[])
{
   if(FileIsExist(file)) return false; // RunId/candidate reuse cannot overwrite evidence.
   int h=FileOpen(file,FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(h==INVALID_HANDLE) return false;
   bool ok=FileWrite(h,"ServerTime","JST","Open","High","Low","Close")>0;
   for(int j=0;j<ArraySize(bars) && ok;j++)
      ok=FileWrite(h,P5Time(raw_times[j]),P5Time(bars[j].time),P5Num(bars[j].open),P5Num(bars[j].high),
         P5Num(bars[j].low),P5Num(bars[j].close))>0;
   FileFlush(h); FileClose(h); return ok;
}
void P5Load(StrategyConfig &cfg,datetime t,int i)
{
   P5Empty(p5_features[i],"HISTORY_NOT_READY");
   MqlRates bars[]; ArraySetAsSeries(bars,false);
   datetime start=P5JstToServer(P5Midnight(t)-600*86400);
   datetime end=P5JstToServer(P5Midnight(t))-1;
   if(start<=0 || end<=0 || end<start)
   { P5Empty(p5_features[i],"UNSUPPORTED_SERVER_TIME"); return; }
   // Same-symbol same-JST-day immutable snapshot reuse. No partial/current day cached.
   // History expansion or a day rollover invalidates it; fallbacks are never shared.
   for(int k=0;k<ArraySize(strategies);k++)
   {
      if(k==i || strategies[k].symbol!=cfg.symbol || p5_cache_day[k]!=P5Midnight(t) ||
         p5_features[k].status!="VALID" || p5_snapshot[k]=="EXPORT_FAILED") continue;
      if(!SeriesInfoInteger(cfg.symbol,PERIOD_M1,SERIES_SYNCHRONIZED) ||
         Bars(cfg.symbol,PERIOD_M1,p5_cache_start[k],p5_cache_end[k])!=p5_cache_count[k]) continue;
      p5_features[i]=p5_features[k]; p5_snapshot[i]=p5_snapshot[k];
      p5_cache_day[i]=p5_cache_day[k]; p5_cache_start[i]=p5_cache_start[k];
      p5_cache_end[i]=p5_cache_end[k]; p5_cache_count[i]=p5_cache_count[k];
      P5Emit(cfg,"HISTORY","EvidencePath="+p5_snapshot[i]+"|HistoryStart="+P5Time(start)+
         "|HistoryEnd="+P5Time(end)+"|ServerTimezoneRule=OANDA_US_DST_V1|CachePolicy=JST_DAY_COUNT_SYNC|CacheReused=true");
      return;
   }
   ulong began=GetTickCount64();
   int count=CopyRates(cfg.symbol,PERIOD_M1,start,end,bars);
   if(count<=0 || !SeriesInfoInteger(cfg.symbol,PERIOD_M1,SERIES_SYNCHRONIZED) ||
      count!=Bars(cfg.symbol,PERIOD_M1,start,end)) return;
   // If local history begins later than requested, the first loaded day may be partial.
   // Drop that first day; more history than mathematical warmup is intentionally requested.
   datetime firstday=0; int kept=0; datetime raw_times[]; ArrayResize(raw_times,count);
   for(int j=0;j<count;j++)
   {
      datetime jt=0;
      if(!P5ServerToJst(bars[j].time,jt))
      { P5Empty(p5_features[i],"AMBIGUOUS_SERVER_TIME"); return; }
      if(j==0) firstday=P5Midnight(jt);
      if(P5Midnight(jt)==firstday) continue;
      raw_times[kept]=bars[j].time;
      bars[kept]=bars[j]; bars[kept].time=jt; kept++;
   }
   ArrayResize(bars,kept);
   P5Daily daily[]; P5Calculate(bars,t,daily,p5_features[i]);
   string file="P5_"+InpPhase5RunId+"_"+IntegerToString(cfg.magic)+"_"+
      IntegerToString((long)P5Midnight(t))+"_m1.csv";
   if(!P5Export(file,bars,raw_times))
   { p5_snapshot[i]="EXPORT_FAILED"; }
   else p5_snapshot[i]=file;
   p5_cache_day[i]=P5Midnight(t); p5_cache_start[i]=start; p5_cache_end[i]=end; p5_cache_count[i]=count;
   P5Emit(cfg,"HISTORY","EvidencePath="+p5_snapshot[i]+"|HistoryStart="+P5Time(start)+
      "|HistoryEnd="+P5Time(end)+"|ServerTimezoneRule=OANDA_US_DST_V1|LoadMilliseconds="+
      IntegerToString((long)(GetTickCount64()-began)));
}
void P5FeatureLog(StrategyConfig &cfg,datetime t,int i)
{
   P5Feature f=p5_features[i];
   P5Emit(cfg,"FEATURE","EntryCandidateJST="+P5Time(t)+"|VolFeatureStatus="+f.status+
      "|ATR20="+(f.status=="VALID"?P5Num(f.atr):"NOT_AVAILABLE")+
      "|RankNumerator="+IntegerToString(f.numerator)+"|Percentile="+
      (f.status=="VALID"?P5Num(f.percent):"NOT_AVAILABLE")+"|Quintile="+IntegerToString(f.q)+
      "|AppliedRiskPercent="+P5Num(f.risk)+"|FallbackReason="+f.reason+
      "|FeatureDailyDate="+P5Time(f.day)+"|AvailableAtJST="+P5Time(f.available)+
      "|LastM1JST="+P5Time(f.last)+"|ReferenceStart="+P5Time(f.ref_start)+
      "|ReferenceEnd="+P5Time(f.ref_end)+"|ReferenceCount="+(f.status=="VALID"?"252":"0")+
      "|DailyCount="+IntegerToString(f.days)+"|M1Count="+IntegerToString(f.bars)+
      "|WeeklyBase=NOT_REQUESTED|RiskAmount=NOT_REQUESTED|RawLot=NOT_REQUESTED|FinalLot=NOT_REQUESTED");
}
void P5Candidate(StrategyConfig &cfg,datetime t)
{
   int i=P5Index(cfg); if(i<0) return;
   datetime planned=P5Midnight(t)+GetStrategyEntryHour(cfg,t)*3600+GetStrategyEntryMinute(cfg,t)*60;
   string id=InpPhase5RunId+"_"+IntegerToString(cfg.magic)+"_"+IntegerToString((long)planned);
   if(p5_candidate[i]==id) return;
   p5_candidate[i]=id; p5_attempt[i]=0; p5_last_decision[i]="";
   p5_loaded[i]=false; p5_snapshot[i]="NOT_AVAILABLE";
   P5Emit(cfg,"CANDIDATE","PlannedEntryJST="+P5Time(planned)+"|EntryCandidateJST="+P5Time(t));
   P5Load(cfg,t,i); p5_loaded[i]=true; P5FeatureLog(cfg,t,i);
}
void P5Decision(StrategyConfig &cfg,string reason)
{
   int i=P5Index(cfg); if(i<0 || p5_last_decision[i]==reason) return;
   p5_last_decision[i]=reason; P5Emit(cfg,"DECISION","SkipReason="+reason);
}
double P5GetLot(StrategyConfig &cfg,datetime t)
{
   if(!P5Guard()) return 0;
   int i=P5Index(cfg); if(i<0 || !p5_loaded[i]) return 0;
   p5_attempt[i]++;
   if(p5_snapshot[i]=="EXPORT_FAILED")
   { P5Emit(cfg,"LOT_STOP","LotStopReason=EVIDENCE_EXPORT_FAILED|FinalLot=0"); return 0; }
   // Feature frozen for this candidate, including a legitimate history fallback.
   double sl=GetStrategySLPips(cfg,t),pip=GetPipSize(cfg.symbol);
   double ts=SymbolInfoDouble(cfg.symbol,SYMBOL_TRADE_TICK_SIZE);
   double tv=SymbolInfoDouble(cfg.symbol,SYMBOL_TRADE_TICK_VALUE);
   double pv=(P5Positive(ts)&&P5Positive(tv)&&P5Positive(pip))?tv*(pip/ts):0;
   double minimum=SymbolInfoDouble(cfg.symbol,SYMBOL_VOLUME_MIN);
   double maximum=SymbolInfoDouble(cfg.symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(cfg.symbol,SYMBOL_VOLUME_STEP);
   if(!P5Positive(sl)) { P5Emit(cfg,"LOT_STOP","LotStopReason=INVALID_SL|WeeklyBase=NOT_REQUESTED|FinalLot=0"); return 0; }
   double base=GetWeeklyBaseAmount(t); P5Lot r;
   P5Size(base,p5_features[i].risk,sl,pv,minimum,maximum,step,InpMaxAutoLot,r);
   P5Emit(cfg,"SIZING","AppliedRiskPercent="+P5Num(p5_features[i].risk)+
      "|WeeklyBase="+P5Num(base)+"|WeekKey="+IntegerToString(WeekStartDateKey(t))+
      "|GVName="+WeeklyBaseGlobalVariableName(WeekStartDateKey(t))+"|WeeklyBaseAction="+p5_week_action+
      "|EquitySnapshot="+P5Num(p5_equity)+"|BalanceSnapshot="+P5Num(p5_balance)+
      "|RiskAmount="+P5Num(r.amount)+"|SLPips="+P5Num(sl)+"|PipValuePerLot="+P5Num(pv)+
      "|PipSize="+P5Num(pip)+"|TickSize="+P5Num(ts)+
      "|TickValue="+P5Num(tv)+
      "|AccountCurrency="+AccountInfoString(ACCOUNT_CURRENCY)+"|RawLot="+P5Num(r.raw)+
      "|CappedLot="+P5Num(r.capped)+"|RoundedLot="+P5Num(r.final_lot)+"|FinalLot="+P5Num(r.final_lot)+
      "|VolumeMin="+P5Num(minimum)+"|VolumeMax="+P5Num(maximum)+"|VolumeStep="+P5Num(step)+
      "|MaxAutoLot="+P5Num(InpMaxAutoLot)+"|MaxAutoLotCap="+BoolText(r.cap)+
      "|MinLotStop="+BoolText(r.min_stop)+"|LotStopReason="+r.reason);
   return r.final_lot;
}
bool P5Config()
{
   if(!P5Guard() || !InpPhase5OandaTimeVerified || StringLen(InpPhase5RunId)<1 || StringLen(InpPhase5RunId)>24) return false;
   for(int j=0;j<StringLen(InpPhase5RunId);j++)
   { ushort c=StringGetCharacter(InpPhase5RunId,j); if(!((c>=48&&c<=57)||(c>=65&&c<=90)||(c>=97&&c<=122)||c==95)) return false; }
   if(InpLotMode!=1 || !InpWeeklyBaseUseEquity || InpRiskPercentPerTrade!=0.90 || InpMaxAutoLot!=1.0 ||
      InpAllowMinLotWhenBelowMinimum || InpTestMode || InpUseTestTimes || InpUseMockJstDateTime ||
      InpUJ12ForceGotoMode || InpUJ12ForceNormalMode || InpUseGlobalAtrP70Filter ||
      !InpUseEventFilter || !InpUseEventCandidateC || !InpUseWeekendMarketClosedGuard ||
      !InpPrintVolR2Diagnostics || !InpPrintTradeResultDiagnostics || !InpPrintWeeklyBaseDiagnostics) return false;
   if(ArraySize(strategies)!=28) return false;
   int enabled=0;
   for(int i=0;i<ArraySize(strategies);i++)
   {
      bool expected=strategies[i].strategy_name!="22_GA_C_2";
      if(strategies[i].enabled!=expected) return false;
      if(expected) enabled++;
      string s=strategies[i].symbol;
      if(!EnsureSymbolReady(s,strategies[i].strategy_name)) return false;
      if(SymbolInfoDouble(s,SYMBOL_VOLUME_MIN)!=0.01 || SymbolInfoDouble(s,SYMBOL_VOLUME_MAX)!=10.0 ||
         SymbolInfoDouble(s,SYMBOL_VOLUME_STEP)!=0.01) return false;
      if(HasOpenPosition(s,strategies[i].magic)) return false;
      for(int o=0;o<OrdersTotal();o++)
      {
         if(OrderGetTicket(o)==0) continue;
         if(OrderGetString(ORDER_SYMBOL)==s && OrderGetInteger(ORDER_MAGIC)==strategies[i].magic) return false;
      }
   }
   return enabled==27 && P5Now()>0;
}
