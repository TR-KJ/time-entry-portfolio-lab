"""Independent scalar execution/date mapping/overlap/mode/gate oracle."""
from datetime import datetime,timedelta
import pandas as pd
from .execution import validate,START,END
from .u06_reference import execute
from .stage1_contract import object_hash,PIPS
from .stage1_metrics import summarize
from .u10_artifacts import result

def event_set(symbol,mode):
    if symbol not in PIPS or mode not in ['E0','E1','E2']:raise ValueError('symbol/mode')
    if mode=='E0':return []
    banks={'USD':'FOMC','JPY':'BOJ','EUR':'ECB','GBP':'BOE','AUD':'RBA'};names=[]
    for c in [symbol[0:3],symbol[3:6]]:names.append(banks[c])
    if mode=='E2':
        names+=['US_NFP','US_CPI']
        if symbol[:3]=='AUD' or symbol[3:]=='AUD':names.append('AUD_CPI')
    return sorted(set(names))

def windows(calendar):
    out=[]
    for e in calendar['Events']:
        for ds in e['SourceDates']:
            t=datetime.strptime(ds+' '+e['FixedJST'],'%Y-%m-%d %H:%M')
            if e['CanonicalEventName']=='FOMC':t+=timedelta(days=1)
            w=timedelta(minutes=e['WindowPlusMinusMinutes']);out.append(dict(Event=e['CanonicalEventName'],SourceDate=ds,EventTimestampJST=str(t),Start=str(t-w),End=str(t+w)))
    return sorted(out,key=lambda w:(w['Start'],w['End'],w['Event'],w['SourceDate']))

def gate_checks(m):
    checks={'TotalTrades':m['Trades']>=150}
    for year in (2020,2021,2022,2023):checks['Annual'+str(year)]=m['Annual'][str(year)]['Trades']>=30
    checks['TotalLosses']=m['Losses']>=10;checks['AvgPips']=False if m['AvgPips'] is None else m['AvgPips']>0
    checks['FinitePF']=m['PFState']=='FINITE';checks['PFpips']=False
    if m['PFState']=='FINITE' and m['PFpips'] is not None:checks['PFpips']=m['PFpips']>=1.10
    checks['PositiveYearCount']=m['PositiveYearCount']>=3
    return checks

def filter_modes(trades,symbol,calendar):
    ws=windows(calendar);modes={};streams={};detail={};ts=sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    if len({t['TradeID'] for t in ts})!=len(ts):raise ValueError('duplicate trade')
    for mode in ['E0','E1','E2']:
        names=event_set(symbol,mode);removed=[];kept=[];overlaps={};counts={n:0 for n in names};multi=0
        for t in ts:
            e=datetime.fromisoformat(t['PlannedEntryTimeJST']);x=datetime.fromisoformat(t['PlannedTimeExitJST'])
            if not datetime(2020,1,1)<=e<=x<datetime(2024,1,1):raise ValueError('Discovery interval')
            found=[]
            for w in ws:
                if w['Event'] in names and e<=datetime.fromisoformat(w['End']) and x>=datetime.fromisoformat(w['Start']):found.append(w['Event'])
            found=sorted(set(found));overlaps[t['TradeID']]=found
            if found:
                removed.append(t['TradeID']);multi+=int(len(found)>1)
                for n in found:counts[n]+=1
            else:kept.append(t)
        streams[mode]=kept;detail[mode]=dict(RemovedTradeIDs=removed,OverlappingEvents=overlaps)
        modes[mode]=dict(EventSet=names,Metrics=summarize(kept),RemovedTrades=len(removed),Retention=len(kept)/len(ts) if ts else None,RemovedByEvent=counts,MultiEventOverlapTradeCount=multi,RemovedTradeIDsSHA256=object_hash(removed))
    return modes,streams,detail

def evaluate_candidate(bars,r,calendar,days=None):
    validate(bars);dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D') if days is None else pd.DatetimeIndex(days)
    if dates.tz is not None or dates.has_duplicates or any(d!=d.normalize() or d<START or d>=END for d in dates):raise ValueError('Discovery dates')
    if r['FormalExitDayOffset']*1440+r['FormalExitMinute']-r['FormalEntryMinute']!=r['FormalHoldingMinutes']:raise ValueError('formal schedule')
    trades=[]
    for d in sorted(dates):
        bucket='D1' if d.day<11 else ('D2' if d.day<21 else 'D3')
        if d.weekday() not in r['FormalWeekdays'] or d.month not in r['FormalMonths'] or bucket not in r['FormalDOMBuckets']:continue
        e=d+timedelta(minutes=r['FormalEntryMinute']);x=d+timedelta(days=r['FormalExitDayOffset'],minutes=r['FormalExitMinute'])
        key=[r['Symbol'],int(r['Direction']=='SHORT'),d.weekday(),r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'],r['CandidateID']]
        t=execute(bars,r['Symbol'],r['Direction'],e,x,r['FormalSL'],key,r['FormalTP'])
        if t['Status']=='OK':t.update(PlannedEntryTimeJST=str(e),PlannedTimeExitJST=str(x),TradeID=object_hash([r['CandidateID'],str(e),str(x)]));trades.append(t)
    modes,streams,detail=filter_modes(trades,r['Symbol'],calendar)
    return result(r,modes,gate_checks(modes['E2']['Metrics']),streams),dict(Streams=streams,Filtering=detail,EventWindows=windows(calendar))
