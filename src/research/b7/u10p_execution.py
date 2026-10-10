"""Vectorized protection paths on frozen E2 survivors; no E0/E1 metrics."""
from copy import deepcopy
import numpy as np
import pandas as pd
from .execution import validate,START,END
from .stage1_contract import PIPS,object_hash
from .stage1_metrics import summarize
from .u06_execution import Engine
from .u10_execution import gate_checks
from .u09_execution import calendar_days
from .u10_calendar import EventIndex,event_set,audit_calendar
MODES={'P0':(None,None),'P1':(.5,0.),'P2':(.75,.25),'P3':(1.,.5)}

def regenerate(engine,r,calendar,days=None):
    if engine.symbol!=r['Symbol'] or r['FormalExitDayOffset']*1440+r['FormalExitMinute']-r['FormalEntryMinute']!=r['FormalHoldingMinutes']:raise ValueError('fixed schedule/symbol')
    index=EventIndex(calendar);names=event_set(r['Symbol'],'E2');trades=[]
    for d in calendar_days(r,days):
        e=d+pd.Timedelta(minutes=r['FormalEntryMinute']);x=d+pd.Timedelta(days=r['FormalExitDayOffset'],minutes=r['FormalExitMinute'])
        if index.matching(str(e),str(x),names):continue
        key=[r['Symbol'],int(r['Direction']=='SHORT'),d.weekday(),r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'],r['CandidateID']]
        t=engine.execute(r['Direction'],e,x,r['FormalSL'],key,r['FormalTP'])
        if t['Status']=='OK':
            t.update(PlannedEntryTimeJST=str(e),PlannedTimeExitJST=str(x),TradeID=object_hash([r['CandidateID'],str(e),str(x)]));trades.append(t)
    return sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))

def barrier(ts,r):
    m=summarize(ts)
    if object_hash(ts)!=r['E2TradeStreamSHA256'] or m!=r['DiscoveryE2Metrics']:raise ValueError('P0 exact E2 stream/metrics barrier')
    return m

def simulate(bars,r,t,mode):
    if mode not in MODES:raise ValueError('fixed mode')
    if len(bars) and (bars.index[0]<START or bars.index[-1]>=END):raise ValueError('Discovery only')
    sign=1 if r['Direction']=='LONG' else -1;pip=PIPS[r['Symbol']];entry=t['EntryPrice'];sl=r['FormalSL'];tp=r['FormalTP'];tr,lk=MODES[mode]
    applicable=mode=='P0' or tp is None or tp>tr*sl
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

def describe(mode,trades,r):
    tr,lk=MODES[mode];app=mode=='P0' or r['FormalTP'] is None or r['FormalTP']>tr*r['FormalSL'];m=summarize(trades);wtl=[t for t in trades if t['WinnerToLoser']];gs=[t['GivebackPips'] for t in wtl];checks=gate_checks(m)
    return dict(Mode=mode,Applicable=app,NotApplicableReason=None if app else 'NOT_APPLICABLE_TP_AT_OR_BEFORE_TRIGGER',TriggerR=tr,LockR=lk,Metrics=m,U01GatePASS=all(checks.values()),U01GateChecks=checks,WinnerToLoserCount=len(wtl),WinnerToLoserFraction=len(wtl)/len(trades) if trades else None,WinnerToLoserGiveback=dict(Total=float(np.sum(gs)),Mean=float(np.mean(gs)) if gs else None,Median=float(np.median(gs)) if gs else None),TradeResults=trades,TradeStreamSHA256=object_hash(trades),TradeIDsSHA256=object_hash([t['TradeID'] for t in trades]))

def adoption(base,d):
    count=base['WinnerToLoserCount']-d['WinnerToLoserCount'];fraction=count/base['WinnerToLoserCount'] if base['WinnerToLoserCount'] else None
    b,m=base['Metrics'],d['Metrics'];nw={k:False for k in ('TotalPips','PFpips','MedianAnnualAvgPips','PositiveYearCount','MaxDDPips')}
    if d['U01GatePASS']:
        if any(x['PFState']!='FINITE' or x['PFpips'] is None or x['MedianAnnualAvgPips'] is None for x in (b,m)):raise ValueError('defined finite baseline/comparison invariant')
        nw={k:m[k]>=b[k] for k in nw};nw['MaxDDPips']=m['MaxDDPips']<=b['MaxDDPips']
    checks=dict(Applicable=d['Applicable'],U01Equivalent=d['U01GatePASS'],**nw,ReductionFraction=fraction is not None and fraction>=.20,ReductionCount=count>=5)
    d.update(ReductionCount=count,ReductionFraction=fraction,DoNotWorsenChecks=nw,AdoptionChecks=checks,AdoptionPASS=all(checks.values()))
    return d

def select(modes):
    passed=[m for m in ('P1','P2','P3') if modes[m]['AdoptionPASS']]
    ranked=sorted(passed,key=lambda k:(-modes[k]['ReductionCount'],modes[k]['Metrics']['MaxDDPips'],-modes[k]['Metrics']['PFpips'],-modes[k]['Metrics']['TotalPips'],('P1','P2','P3').index(k)))
    return ranked,ranked[0] if ranked else 'P0'

def evaluate_candidate(engine,r,days=None,calendar=None):
    calendar=audit_calendar() if calendar is None else calendar;ts=regenerate(engine,r,calendar,days)
    barrier(ts,r) # Must precede all diagnostics, simulations and protection output.
    modes={}
    for mode in MODES:
        trades=[simulate(engine.bars,r,t,mode) for t in ts]
        trades.sort(key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
        modes[mode]=describe(mode,trades,r)
    modes['P0'].update(ReductionCount=None,ReductionFraction=None,DoNotWorsenChecks={},AdoptionChecks={},AdoptionPASS=False)
    for mode in ('P1','P2','P3'):adoption(modes['P0'],modes[mode])
    ranked,chosen=select(modes)
    reason=None if ranked else ('ALL_PROTECTION_MODES_NOT_APPLICABLE' if all(not modes[m]['Applicable'] for m in ('P1','P2','P3')) else 'NO_PROTECTION_MODE_PASS')
    return dict(deepcopy(r),Status='PASS_U10P',NoReplacement=True,FormalProtectionMode=chosen,RankedPASSModes=ranked,P0RetentionReason=reason,P0Barrier=dict(Status='PASS',E2TradeStreamSHA256=object_hash(ts),P0TradeIDsSHA256=object_hash([t['TradeID'] for t in ts]),MetricsExact=True),Modes=modes)
