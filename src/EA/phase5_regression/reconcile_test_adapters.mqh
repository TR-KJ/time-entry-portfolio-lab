// TEST ONLY. All data in memory. No trade or terminal mutation APIs.
#define DIR_LONG 1
#define DIR_SHORT -1
struct StrategyConfig { string symbol,strategy_name; long magic; };
StrategyConfig strategies[];
int InpTradeReconcileTimeoutSeconds=10;
struct RDeal { ulong ticket,order,position; string symbol; long magic,entry,type,time; double lot; };
struct RPosition { ulong ticket,identifier; string symbol; long magic,type,time; double lot; };
RDeal rd[]; RPosition rp[];
ulong selected_history[];
int selected_position=-1;
ulong clock_ms=1000;
int marks=0,entry_events=0,exit_events=0,runs=0;
bool guard_ok=true;
string last_log="";
void PrintDebug(string name,string message) { last_log=message; }
void MarkEnteredToday(StrategyConfig &cfg,datetime at) { marks++; }
void P5Emit(StrategyConfig &cfg,string kind,string fields)
{ if(kind=="ENTRY_RECONCILED") entry_events++; if(kind=="EXIT_RECONCILED") exit_events++; }
bool P5Guard() { return guard_ok; }
datetime P5Now() { return D'2026.09.16 12:00'; }
void RunStrategies() { runs++; } // No actual scheduling/submission in this component test.
ulong RClock() { return clock_ms; }
datetime RServer() { return D'2026.09.16 06:00'; }
double RSymbol(string symbol,int property)
{ if(property==SYMBOL_VOLUME_STEP || property==SYMBOL_VOLUME_MIN) return .01;
  if(property==SYMBOL_VOLUME_MAX) return 10; return 0; }
int RDealIndex(ulong ticket)
{ for(int i=0;i<ArraySize(rd);i++) if(rd[i].ticket==ticket) return i; return -1; }
bool RHistorySelect(datetime from,datetime to)
{
   ArrayResize(selected_history,0);
   for(int i=0;i<ArraySize(rd);i++) if(rd[i].time>=(long)from*1000 && rd[i].time<=(long)to*1000)
   { int n=ArraySize(selected_history); ArrayResize(selected_history,n+1); selected_history[n]=rd[i].ticket; }
   return true;
}
bool RHistoryDealSelect(ulong ticket)
{
   ArrayResize(selected_history,0);
   if(RDealIndex(ticket)<0) return false;
   ArrayResize(selected_history,1); selected_history[0]=ticket; return true;
}
int RHistoryTotal() { return ArraySize(selected_history); }
ulong RHistoryTicket(int i)
{ return i>=0 && i<ArraySize(selected_history)?selected_history[i]:0; }
string RDealString(ulong ticket,int property)
{ int i=RDealIndex(ticket); if(i<0) return ""; return property==DEAL_SYMBOL?rd[i].symbol:""; }
long RDealInteger(ulong ticket,int property)
{
   int i=RDealIndex(ticket); if(i<0) return 0;
   if(property==DEAL_MAGIC) return rd[i].magic;
   if(property==DEAL_ENTRY) return rd[i].entry;
   if(property==DEAL_TYPE) return rd[i].type;
   if(property==DEAL_ORDER) return (long)rd[i].order;
   if(property==DEAL_POSITION_ID) return (long)rd[i].position;
   if(property==DEAL_TIME_MSC) return rd[i].time;
   return 0;
}
double RDealDouble(ulong ticket,int property)
{ int i=RDealIndex(ticket); if(i<0) return 0; return property==DEAL_VOLUME?rd[i].lot:0; }
int RPositionsTotal() { return ArraySize(rp); }
ulong RPositionTicket(int i)
{ if(i<0 || i>=ArraySize(rp)) return 0; selected_position=i; return rp[i].ticket; }
bool RPositionSelect(ulong ticket)
{ selected_position=-1; for(int i=0;i<ArraySize(rp);i++) if(rp[i].ticket==ticket){selected_position=i;return true;} return false; }
string RPositionString(int property)
{ if(selected_position<0) return ""; return property==POSITION_SYMBOL?rp[selected_position].symbol:""; }
long RPositionInteger(int property)
{
   int i=selected_position; if(i<0) return 0;
   if(property==POSITION_MAGIC) return rp[i].magic;
   if(property==POSITION_TYPE) return rp[i].type;
   if(property==POSITION_TIME_MSC) return rp[i].time;
   if(property==POSITION_IDENTIFIER) return (long)rp[i].identifier;
   return 0;
}
double RPositionDouble(int property)
{ if(selected_position<0) return 0; return property==POSITION_VOLUME?rp[selected_position].lot:0; }
// Only the extracted code below these aliases sees these stand-ins.
#define GetTickCount64 RClock
#define TimeTradeServer RServer
#define TimeCurrent RServer
#define SymbolInfoDouble RSymbol
#define HistorySelect RHistorySelect
#define HistoryDealSelect RHistoryDealSelect
#define HistoryDealsTotal RHistoryTotal
#define HistoryDealGetTicket RHistoryTicket
#define HistoryDealGetString RDealString
#define HistoryDealGetInteger RDealInteger
#define HistoryDealGetDouble RDealDouble
#define PositionsTotal RPositionsTotal
#define PositionGetTicket RPositionTicket
#define PositionSelectByTicket RPositionSelect
#define PositionGetString RPositionString
#define PositionGetInteger RPositionInteger
#define PositionGetDouble RPositionDouble
#define OnTick ROnTick
#define OnTimer ROnTimer
#define OnTradeTransaction ROnTradeTransaction
