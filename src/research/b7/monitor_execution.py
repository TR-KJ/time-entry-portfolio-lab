"""Monitor optimized executable E0 -> E2 -> one frozen Protection mode; no search."""
from copy import deepcopy
import pandas as pd
import numpy as np
from .monitor_data import START,END
from .monitor_engine import Engine
from .stage1_contract import PIPS,object_hash
from .u10_calendar import EventIndex,event_set,audit_calendar
from .monitor_metrics import summarize,diagnostics
from .monitor_input import FREEZE_SHA,RESULT_SHA,PRODUCER_SHA,PERIOD
MODES={'P0':(None,None),'P1':(.5,0.),'P2':(.75,.25),'P3':(1.,.5)}

def calendar_days(r,days=None):
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D') if days is None else pd.DatetimeIndex(days)
    if dates.tz is not None or dates.has_duplicates or any(d!=d.normalize() or d<START or d>=END for d in dates):raise ValueError('Monitor dates only')
    if r['FormalExitDayOffset']*1440+r['FormalExitMinute']-r['FormalEntryMinute']!=r['FormalHoldingMinutes']:raise ValueError('frozen schedule')
    return [d for d in sorted(dates) if d.weekday() in r['FormalWeekdays'] and d.month in r['FormalMonths'] and ('D1' if d.day<=10 else 'D2' if d.day<=20 else 'D3') in r['FormalDOMBuckets']]

def executable(engine,r,days=None):
    if engine.symbol!=r['Symbol']:raise ValueError('engine symbol')
    ts=[];skips={}
    for day in calendar_days(r,days):
        e=day+pd.Timedelta(minutes=r['FormalEntryMinute']);x=day+pd.Timedelta(days=r['FormalExitDayOffset'],minutes=r['FormalExitMinute'])
        key=[r['Symbol'],int(r['Direction']=='SHORT'),day.weekday(),r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'],r['CandidateID']]
        t=engine.execute(r['Direction'],e,x,r['FormalSL'],key,r['FormalTP'])
        if t['Status']=='OK':
            t.update(CandidateID=r['CandidateID'],PlannedEntryTimeJST=str(e),PlannedTimeExitJST=str(x),TradeID=object_hash([r['CandidateID'],str(e),str(x)]));ts.append(t)
        else:skips[t['Status']]=skips.get(t['Status'],0)+1
    return sorted(ts,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey']))),skips

def filter_e2(ts,r,calendar):
    names=r['E2EventSet']
    if r['FormalEventMode']!='E2' or names!=event_set(r['Symbol'],'E2'):raise ValueError('saved E2 set identity')
    index=EventIndex(calendar);kept=[];removed=[];overlaps={};counts={n:0 for n in names};multi=0
    if len({t['TradeID'] for t in ts})!=len(ts):raise ValueError('unique executable IDs')
    for t in ts:
        found=index.matching(t['PlannedEntryTimeJST'],t['PlannedTimeExitJST'],names);overlaps[t['TradeID']]=found
        if found:
            removed.append(t['TradeID']);multi+=int(len(found)>1)
            for n in found:counts[n]+=1
        else:kept.append(t)
    d=dict(E0ExecutableTrades=len(ts),E2Trades=len(kept),RemovedTrades=len(removed),Retention=len(kept)/len(ts) if ts else None,RemovedByEvent=counts,MultiEventOverlapTradeCount=multi,RemovedTradeIDsSHA256=object_hash(removed))
    return kept,d,dict(RemovedTradeIDs=removed,OverlappingEvents=overlaps)

def simulate(bars,r,t,mode):
    if mode not in MODES:raise ValueError('fixed mode')
    if len(bars) and (bars.index[0]<START or bars.index[-1]>=END):raise ValueError('Monitor only')
    sign=1 if r['Direction']=='LONG' else -1;pip=PIPS[r['Symbol']];entry=t['EntryPrice'];sl=r['FormalSL'];tp=r['FormalTP'];tr,lk=MODES[mode]
    applicable=mode=='P0' or tp is None or tp>tr*sl
    if not applicable:raise ValueError('frozen selected Protection structural conflict')
    w=bars.loc[t['EntryTime']:t['CloseTime']]
    if w.empty or str(w.index[0])!=t['EntryTime'] or str(w.index[-1])!=t['CloseTime']:raise ValueError('exact actual path endpoints')
    high=w.High.to_numpy();low=w.Low.to_numpy();end=len(w)-1;trigger=None;activation=None;hit=False;stop=None
    out=deepcopy(t)
    if mode!='P0' and applicable:
        target=entry+sign*tr*sl*pip;hits=np.flatnonzero(high>=target if sign==1 else low<=target)
        if len(hits):
            trigger=int(hits[0]);stop=entry+sign*lk*sl*pip
            # The baseline already closes at the earliest original SL/TP/time exit.
            # A trigger on that closing bar can never activate protection.
            if trigger<end:
                activation=trigger+1
                stops=np.flatnonzero((low<=stop if sign==1 else high>=stop)[activation:])
                if len(stops):
                    end=activation+int(stops[0]);hit=True
                    out.update(CloseTime=str(w.index[end]),ClosePrice=stop,Pips=float(lk*sl),ExitReason='ProtectionSL')
    h=float(np.max(high[:end+1]));l=float(np.min(low[:end+1]))
    mfe=max(0.,(h-entry)/pip if sign==1 else (entry-l)/pip);mae=max(0.,(entry-l)/pip if sign==1 else (h-entry)/pip)
    out.update(Mode=mode,Direction=r['Direction'],FormalSL=sl,FormalTP=tp,PlannedTimeExit=t['PlannedTimeExitJST'],ActualCloseTime=out['CloseTime'],FinalPips=out['Pips'],MFEpips=mfe,MAEpips=mae,GivebackPips=mfe-out['Pips'],WinnerToLoser=mfe>=.5*sl and out['Pips']<0,Applicable=applicable,NotApplicableReason=None if applicable else 'NOT_APPLICABLE_TP_AT_OR_BEFORE_TRIGGER',TriggerR=tr,LockR=lk,TriggerReached=trigger is not None,TriggerBar=None if trigger is None else str(w.index[trigger]),ActivationBar=None if activation is None else str(w.index[activation]),ProtectionActivated=activation is not None,ProtectionStop=stop,ProtectionHit=hit)
    for name,value in [('025',.25),('050',.5),('075',.75),('100',1.)]:out['Reach'+name+'R']=mfe>=value*sl
    return out

def evaluate_candidate(engine,r,calendar=None,days=None,implementation_sha='SYNTHETIC',approval=None,run_identity=None):
    from .monitor_guard import guard
    guard(r,implementation_sha,approval,run_identity)
    if r['CandidateID'].startswith('B7S1:'):
        from .u10_calendar import audit_calendar as frozen_calendar
        if days is not None or calendar is not None and object_hash(calendar)!=object_hash(frozen_calendar()):raise PermissionError('full Monitor period and frozen event calendar only')
    mode=r['FormalProtectionMode']
    triggers={'P0':None,'P1':.5,'P2':.75,'P3':1.}
    if mode not in triggers or mode!='P0' and r['FormalTP'] is not None and r['FormalTP']<=triggers[mode]*r['FormalSL']:raise ValueError('frozen selected mode structurally inapplicable')
    calendar=audit_calendar() if calendar is None else calendar
    e0,skips=executable(engine,r,days);e2,events,detail=filter_e2(e0,r,calendar)
    selected=[simulate(engine.bars,r,t,mode) for t in e2]
    for t in selected:t['FormalProtectionMode']=mode
    selected.sort(key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    if {t['TradeID'] for t in selected}!={t['TradeID'] for t in e2}:raise ValueError('fixed E2 trade universe')
    m=summarize(selected)
    out=dict(deepcopy(r),CandidateFreezeSHA=FREEZE_SHA,MonitorImplementationSHA=implementation_sha,U11ResultFreezeSHA=RESULT_SHA,U11ProducerImplementationSHA=PRODUCER_SHA,MonitorPeriod=PERIOD,EventMode='E2',MonitorMetrics=m,MonitorStatus='OBSERVED_ONLY',Status='OBSERVED_ONLY',ValidationBaseline=deepcopy(r['ValidationMetrics']),DiscoveryBaseline=deepcopy(r['SelectedModeDiscoveryMetrics']),Diagnostics=diagnostics(selected,m,r),EventDiagnostics=events,ExecutionSkipped=skips,MonitorE2BaselineTradeStreamSHA256=object_hash(e2),E2TradeIDsSHA256=object_hash([t['TradeID'] for t in e2]),MonitorSelectedTradeStreamSHA256=object_hash(selected),MonitorTradeIDsSHA256=object_hash([t['TradeID'] for t in selected]),TradeResults=selected,NoReplacement=True,PostValidationRetuningAllowed=False,ValidationOverrideAllowed=False)
    audit=dict(CandidateDays=[str(d) for d in calendar_days(r,days)],E0Executable=e0,E2Survivors=e2,Filtering=detail)
    return out,audit
