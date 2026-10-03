"""Historical weekly Balance/metrics semantics; component-key settlement adapter."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal as D, localcontext
from .stage10_config import RISKS,MODES,PERIODS,require
from .stage10_input import legacy,validate_rows


def settlement(r):return (r['CloseTime'],r['EntryTime'],r['PortfolioComponentKey'],r['RowId'])


def simulate(rows,risk,mode):
    require(risk in RISKS,'unregistered fixed risk')
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
            base=balance;amount=base*risk/100;pnl=D(0)
            for r in sorted(group,key=lambda r:(r['EntryTime'],r['CloseTime'],r['PortfolioComponentKey'],r['RowId'])):
                # Existing Pips/SL arithmetic unchanged; B6 uses saved raw R directly.
                value=amount*r['Pips']/r['SL'] if r['Source']=='BASELINE' else amount*r['R']
                pnl+=value
                logs.append(dict(r,RiskPct=risk,TradingWeekStart=week,WeeklyBase=base,RiskAmount=amount,YenPnL=value))
            balance+=pnl
            weekly.append(dict(TradingWeekStart=week,StartCapital=base,RiskAmount=amount,Trades=len(group),
                BaselineTrades=sum(r['Source']=='BASELINE' for r in group),B6Trades=sum(r['Source']=='B6' for r in group),
                GrossRiskAllocationPct=len(group)*risk,NetProfitJPY=pnl,ReturnPct=pnl/base*100,FinalCapital=balance))
        balance=peak=legacy.INITIAL
        logs.sort(key=settlement)
        for r in logs:
            balance+=r['YenPnL'];require(balance>0,'insolvent closed balance')
            peak=max(peak,balance)
            r.update(Capital=balance,PeakCapital=peak,DrawdownJPY=peak-balance,DrawdownPct=(peak-balance)/peak*100)
        stats={p:legacy.metrics(logs,*PERIODS[p]) for p in MODES[mode][1]}
        return logs,weekly,stats


def deltas(current,baseline):
    fields={'FinalCapital':'DeltaFinalCapital','NetProfitJPY':'DeltaNetProfitJPY','ReturnPct':'DeltaReturnPct',
        'MaxDDJPY':'DeltaMaxDDJPY','MaxDDPct':'DeltaMaxDDPct','WorstDayPct':'DeltaWorstDayPct',
        'WorstWeekPct':'DeltaWorstWeekPct','MoneyRoMD':'DeltaMoneyRoMD','MoneyPF':'DeltaMoneyPF',
        'Trades':'DeltaTrades','MaxConcurrentPositions':'DeltaMaxConcurrentPositions',
        'MaxConcurrentRiskPct':'DeltaMaxConcurrentRiskPct'}
    return {dest:current[src]-baseline[src] if current[src] is not None and baseline[src] is not None else None for src,dest in fields.items()}
