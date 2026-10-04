"""Stage10 money semantics with per-trade Frozen R2 risk only."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal as D, localcontext
from .stage11_config import RISK,MODES,PERIODS,require,AJ,GJ
from .stage11_risk_load import exposure
from statistics import median
from .stage10_input import legacy,validate_rows


def settlement(r):return (r['CloseTime'],r['EntryTime'],r['PortfolioComponentKey'],r['RowId'])


def simulate(rows,mode):
    for r in rows:require(r['AppliedRiskPercent'] in RISK.values(),'unregistered R2 risk')
    require(mode in MODES,'unregistered money mode')
    validate_rows(rows)
    start=datetime.fromisoformat(MODES[mode][0]);end=datetime(2026,9,10)
    own=[r for r in rows if start<=r['EntryTime']<end]
    with localcontext() as ctx:
        ctx.prec=40
        groups=defaultdict(list)
        for r in own:groups[legacy.week_start(r['EntryTime'])].append(r)
        balance=legacy.INITIAL;logs=[];weekly=[]
        for week,group in sorted(groups.items()):
            require(balance>0,'insolvent weekly base')
            base=balance;pnl=D(0)
            for r in sorted(group,key=lambda r:(r['EntryTime'],r['CloseTime'],r['PortfolioComponentKey'],r['RowId'])):
                risk=r['AppliedRiskPercent'];amount=base*risk/100
                # Existing Pips/SL arithmetic unchanged; B6 uses saved raw R directly.
                value=amount*r['Pips']/r['SL'] if r['Source']=='BASELINE' else amount*r['R']
                pnl+=value
                logs.append(dict(r,RiskPct=risk,TradingWeekStart=week,WeeklyBase=base,RiskAmount=amount,YenPnL=value))
            balance+=pnl
            weekly.append(dict(TradingWeekStart=week,StartCapital=base,Trades=len(group),
                BaselineTrades=sum(r['Source']=='BASELINE' for r in group),B6Trades=sum(r['Source']=='B6' for r in group),
                GJTrades=sum(r['PortfolioComponentKey']==GJ for r in group),AJTrades=sum(r['PortfolioComponentKey']==AJ for r in group),
                MeanAppliedRiskPct=sum(r['AppliedRiskPercent'] for r in group)/len(group),MaxAppliedRiskPct=max(r['AppliedRiskPercent'] for r in group),
                GrossRiskAllocationPct=sum(r['AppliedRiskPercent'] for r in group),NetProfitJPY=pnl,ReturnPct=pnl/base*100,FinalCapital=balance))
            from datetime import timedelta
            con,_=exposure(group,str(week),str(week+timedelta(days=7)))
            weekly[-1].update(MaxConcurrentPositions=con['MaxConcurrentPositions'],MaxConcurrentRiskPct=con['MaxConcurrentRiskPct'])
        balance=peak=legacy.INITIAL
        logs.sort(key=settlement)
        for r in logs:
            balance+=r['YenPnL'];require(balance>0,'insolvent closed balance')
            peak=max(peak,balance)
            r.update(Capital=balance,PeakCapital=peak,DrawdownJPY=peak-balance,DrawdownPct=(peak-balance)/peak*100)
        stats={p:legacy.metrics(logs,*PERIODS[p]) for p in MODES[mode][1]}
        for p,stat in stats.items():
            a,b=map(datetime.fromisoformat,PERIODS[p]);rs=[r['AppliedRiskPercent'] for r in own if a<=r['EntryTime']<b]
            stat.update(MeanAppliedRiskPct=sum(rs)/len(rs) if rs else None,MedianAppliedRiskPct=median(rs) if rs else None,MinAppliedRiskPct=min(rs) if rs else None,MaxAppliedRiskPct=max(rs) if rs else None)
        return logs,weekly,stats


def deltas(current,baseline):
    fields={'FinalCapital':'DeltaFinalCapital','NetProfitJPY':'DeltaNetProfitJPY','ReturnPct':'DeltaReturnPct',
        'MaxDDJPY':'DeltaMaxDDJPY','MaxDDPct':'DeltaMaxDDPct','WorstDayPct':'DeltaWorstDayPct',
        'WorstWeekPct':'DeltaWorstWeekPct','MoneyRoMD':'DeltaMoneyRoMD','MoneyPF':'DeltaMoneyPF',
        'Trades':'DeltaTrades','MaxConcurrentPositions':'DeltaMaxConcurrentPositions',
        'MaxConcurrentRiskPct':'DeltaMaxConcurrentRiskPct'}
    return {dest:current[src]-baseline[src] if current[src] is not None and baseline[src] is not None else None for src,dest in fields.items()}
