"""Independent scalar E2/protection/adoption/ranking oracle; no optimized imports."""
from copy import deepcopy
from datetime import timedelta,datetime
import pandas as pd
import numpy as np
from .execution import validate,START,END
from .u06_reference import execute
from .stage1_contract import PIPS,object_hash
from .stage1_metrics import summarize
from .u10_reference import windows,event_set,gate_checks

def regenerate(bars,r,calendar,days=None):
    validate(bars);dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D') if days is None else pd.DatetimeIndex(days)
    if dates.tz is not None or dates.has_duplicates or any(d!=d.normalize() or d<START or d>=END for d in dates):raise ValueError('Discovery dates')
    if r['FormalExitDayOffset']*1440+r['FormalExitMinute']-r['FormalEntryMinute']!=r['FormalHoldingMinutes']:raise ValueError('schedule')
    ws=windows(calendar);names=event_set(r['Symbol'],'E2');ts=[]
    for day in sorted(dates):
        bucket='D1' if day.day<11 else 'D2' if day.day<21 else 'D3'
        if day.weekday() not in r['FormalWeekdays'] or day.month not in r['FormalMonths'] or bucket not in r['FormalDOMBuckets']:continue
        e=day+timedelta(minutes=r['FormalEntryMinute']);x=day+timedelta(days=r['FormalExitDayOffset'],minutes=r['FormalExitMinute'])
        key=[r['Symbol'],int(r['Direction']=='SHORT'),day.weekday(),r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'],r['CandidateID']]
        excluded=False
        for w in ws:
            if w['Event'] in names and e<=datetime.fromisoformat(w['End']) and x>=datetime.fromisoformat(w['Start']):excluded=True;break
        if excluded:continue
        t=execute(bars,r['Symbol'],r['Direction'],e,x,r['FormalSL'],key,r['FormalTP'])
        if t['Status']!='OK':continue
        t.update(PlannedEntryTimeJST=str(e),PlannedTimeExitJST=str(x),TradeID=object_hash([r['CandidateID'],str(e),str(x)]));ts.append(t)
    return sorted(ts,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))

def simulate(bars,r,t,mode):
    if mode not in ['P0','P1','P2','P3']:raise ValueError('fixed mode')
    if len(bars) and (bars.index[0]<START or bars.index[-1]>=END):raise ValueError('Discovery only')
    trigger_r={'P0':None,'P1':.5,'P2':.75,'P3':1.}[mode];lock_r={'P0':None,'P1':0.,'P2':.25,'P3':.5}[mode]
    sl=r['FormalSL'];tp=r['FormalTP'];pip=PIPS[r['Symbol']];price=t['EntryPrice'];long=r['Direction']=='LONG';sign=1 if long else -1
    app=mode=='P0' or tp is None or tp>trigger_r*sl
    path=bars.loc[t['EntryTime']:t['CloseTime']]
    if path.empty or str(path.index[0])!=t['EntryTime'] or str(path.index[-1])!=t['CloseTime']:raise ValueError('exact path')
    out=deepcopy(t);trigger=None;activation=None;stop=None;hit=False;hi=None;lo=None
    for when,row in path.iterrows():
        hi=float(row.High) if hi is None else max(hi,float(row.High));lo=float(row.Low) if lo is None else min(lo,float(row.Low))
        if trigger is not None and activation is None:activation=str(when)
        if activation is not None and (row.Low<=stop if long else row.High>=stop):
            out.update(CloseTime=str(when),ClosePrice=stop,Pips=float(lock_r*sl),ExitReason='ProtectionSL');hit=True;break
        if mode!='P0' and app and trigger is None:
            target=price+sign*trigger_r*sl*pip
            if row.High>=target if long else row.Low<=target:
                trigger=str(when);stop=price+sign*lock_r*sl*pip
        # Baseline first-hit close handles original SL/TP, including SL-first ties.
        if str(when)==t['CloseTime']:break
    mfe=max(0.,(hi-price)/pip if long else (price-lo)/pip);mae=max(0.,(price-lo)/pip if long else (hi-price)/pip)
    out.update(Mode=mode,Direction=r['Direction'],FormalSL=sl,FormalTP=tp,PlannedTimeExit=t['PlannedTimeExitJST'],ActualCloseTime=out['CloseTime'],FinalPips=out['Pips'],MFEpips=mfe,MAEpips=mae,GivebackPips=mfe-out['Pips'],WinnerToLoser=mfe>=.5*sl and out['Pips']<0,Applicable=app,NotApplicableReason=None if app else 'NOT_APPLICABLE_TP_AT_OR_BEFORE_TRIGGER',TriggerR=trigger_r,LockR=lock_r,TriggerReached=trigger is not None,TriggerBar=trigger,ActivationBar=activation,ProtectionActivated=activation is not None,ProtectionStop=stop,ProtectionHit=hit)
    for suffix,reach in [('025',.25),('050',.5),('075',.75),('100',1.)]:out['Reach'+suffix+'R']=mfe>=reach*sl
    return out

def describe(mode,trades,r):
    trigger={'P0':None,'P1':.5,'P2':.75,'P3':1.}[mode];lock={'P0':None,'P1':0.,'P2':.25,'P3':.5}[mode]
    app=mode=='P0' or r['FormalTP'] is None or r['FormalTP']>trigger*r['FormalSL'];m=summarize(trades);checks=gate_checks(m);wtl=[t for t in trades if t['WinnerToLoser']];g=[t['GivebackPips'] for t in wtl]
    return dict(Mode=mode,Applicable=app,NotApplicableReason=None if app else 'NOT_APPLICABLE_TP_AT_OR_BEFORE_TRIGGER',TriggerR=trigger,LockR=lock,Metrics=m,U01GatePASS=all(checks.values()),U01GateChecks=checks,WinnerToLoserCount=len(wtl),WinnerToLoserFraction=len(wtl)/len(trades) if trades else None,WinnerToLoserGiveback=dict(Total=float(np.sum(g)),Mean=float(np.mean(g)) if g else None,Median=float(np.median(g)) if g else None),TradeResults=trades,TradeStreamSHA256=object_hash(trades),TradeIDsSHA256=object_hash([t['TradeID'] for t in trades]))

def adoption(base,mode):
    b=base['Metrics'];m=mode['Metrics'];reduction=base['WinnerToLoserCount']-mode['WinnerToLoserCount'];fraction=None
    if base['WinnerToLoserCount']!=0:fraction=reduction/base['WinnerToLoserCount']
    nw={}
    for key in ['TotalPips','PFpips','MedianAnnualAvgPips','PositiveYearCount','MaxDDPips']:
        if not mode['U01GatePASS']:nw[key]=False;continue
        for x in [b,m]:
            if x['PFState']!='FINITE' or x['PFpips'] is None or x['MedianAnnualAvgPips'] is None:raise ValueError('defined comparison invariant')
        nw[key]=m[key]<=b[key] if key=='MaxDDPips' else m[key]>=b[key]
    checks={'Applicable':mode['Applicable'],'U01Equivalent':mode['U01GatePASS']};checks.update(nw);checks['ReductionFraction']=fraction is not None and fraction>=.2;checks['ReductionCount']=reduction>=5
    mode.update(ReductionCount=reduction,ReductionFraction=fraction,DoNotWorsenChecks=nw,AdoptionChecks=checks,AdoptionPASS=all(checks.values()))
    return mode

def select(modes):
    ranking=[]
    for name in ['P1','P2','P3']:
        if modes[name]['AdoptionPASS']:ranking.append(name)
    # Stable successive sorts implement the fixed lexicographic priorities.
    for key,reverse in [('TotalPips',True),('PFpips',True),('MaxDDPips',False)]:ranking.sort(key=lambda n:modes[n]['Metrics'][key],reverse=reverse)
    ranking.sort(key=lambda n:modes[n]['ReductionCount'],reverse=True)
    return ranking,ranking[0] if ranking else 'P0'

def evaluate_candidate(bars,r,calendar,days=None):
    ts=regenerate(bars,r,calendar,days)
    if object_hash(ts)!=r['E2TradeStreamSHA256'] or summarize(ts)!=r['DiscoveryE2Metrics']:raise ValueError('P0 exact barrier')
    modes={}
    for name in ['P0','P1','P2','P3']:
        ts_mode=[simulate(bars,r,t,name) for t in ts];ts_mode.sort(key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
        modes[name]=describe(name,ts_mode,r)
    modes['P0'].update(ReductionCount=None,ReductionFraction=None,DoNotWorsenChecks={},AdoptionChecks={},AdoptionPASS=False)
    for name in ['P1','P2','P3']:adoption(modes['P0'],modes[name])
    ranked,chosen=select(modes);reason=None
    if not ranked:reason='ALL_PROTECTION_MODES_NOT_APPLICABLE' if all(not modes[k]['Applicable'] for k in ['P1','P2','P3']) else 'NO_PROTECTION_MODE_PASS'
    return dict(deepcopy(r),Status='PASS_U10P',NoReplacement=True,FormalProtectionMode=chosen,RankedPASSModes=ranked,P0RetentionReason=reason,P0Barrier=dict(Status='PASS',E2TradeStreamSHA256=object_hash(ts),P0TradeIDsSHA256=object_hash([t['TradeID'] for t in ts]),MetricsExact=True),Modes=modes)
