"""Execute U09 Final schedule once, then indexed E1/E2 filtering of that E0 stream."""
import pandas as pd
from .execution import START,END
from .u06_execution import Engine
from .u09_execution import calendar_days
from .stage1_contract import object_hash
from .stage1_metrics import summarize
from .u10_calendar import EventIndex,event_set,audit_calendar
from .u10_artifacts import result,CHECKS

def gate_checks(m):
    return dict(TotalTrades=m['Trades']>=150,**{'Annual'+str(y):m['Annual'][str(y)]['Trades']>=30 for y in range(2020,2024)},TotalLosses=m['Losses']>=10,AvgPips=m['AvgPips'] is not None and m['AvgPips']>0,FinitePF=m['PFState']=='FINITE',PFpips=m['PFState']=='FINITE' and m['PFpips'] is not None and m['PFpips']>=1.10,PositiveYearCount=m['PositiveYearCount']>=3)

def execution_stream(engine,r,days=None):
    if engine.symbol!=r['Symbol']:raise ValueError('symbol')
    if r['FormalExitDayOffset']*1440+r['FormalExitMinute']-r['FormalEntryMinute']!=r['FormalHoldingMinutes']:raise ValueError('formal schedule')
    trades=[]
    for d in calendar_days(r,days):
        e=d+pd.Timedelta(minutes=r['FormalEntryMinute']);x=d+pd.Timedelta(days=r['FormalExitDayOffset'],minutes=r['FormalExitMinute'])
        key=[r['Symbol'],0 if r['Direction']=='LONG' else 1,d.weekday(),r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'],r['CandidateID']]
        t=engine.execute(r['Direction'],e,x,r['FormalSL'],key,r['FormalTP'])
        if t['Status']=='OK':
            t.update(PlannedEntryTimeJST=str(e),PlannedTimeExitJST=str(x),TradeID=object_hash([r['CandidateID'],str(e),str(x)]));trades.append(t)
    return sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))

def filter_modes(trades,symbol,index):
    if len({t['TradeID'] for t in trades})!=len(trades):raise ValueError('duplicate trade')
    modes={};streams={};detail={}
    trades=sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    for mode in ('E0','E1','E2'):
        names=event_set(symbol,mode);kept=[];removed=[];overlaps={};counts={e:0 for e in names};multi=0
        for t in trades:
            e,x=t['PlannedEntryTimeJST'],t['PlannedTimeExitJST']
            if not START<=pd.Timestamp(e)<=pd.Timestamp(x)<END:raise ValueError('Discovery planned interval')
            hits=index.matching(e,x,names);overlaps[t['TradeID']]=hits
            if hits:
                removed.append(t['TradeID']);multi+=len(hits)>1
                for h in hits:counts[h]+=1
            else:kept.append(t)
        streams[mode]=kept;detail[mode]=dict(RemovedTradeIDs=removed,OverlappingEvents=overlaps)
        modes[mode]=dict(EventSet=names,Metrics=summarize(kept),RemovedTrades=len(removed),Retention=len(kept)/len(trades) if trades else None,RemovedByEvent=counts,MultiEventOverlapTradeCount=multi,RemovedTradeIDsSHA256=object_hash(removed))
    if not {t['TradeID'] for t in streams['E2']}<={t['TradeID'] for t in streams['E1']}<={t['TradeID'] for t in streams['E0']}:raise AssertionError('subset')
    return modes,streams,detail

def evaluate_candidate(engine,record,days=None,calendar=None):
    index=EventIndex(audit_calendar() if calendar is None else calendar)
    modes,streams,detail=filter_modes(execution_stream(engine,record,days),record['Symbol'],index)
    out=result(record,modes,gate_checks(modes['E2']['Metrics']),streams)
    return out,dict(Streams=streams,Filtering=detail,EventWindows=index.windows)
