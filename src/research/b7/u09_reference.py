"""Independent scalar schedule, execution, neighborhood, ranking and adoption oracle."""
from datetime import datetime,timedelta
from statistics import median
import pandas as pd
from .execution import START,END,validate
from .u06_reference import execute
from .stage1_metrics import summarize
from .u09_selection import result  # serialization only, not policy

def schedule(record,es,xs):
    if type(es)!=int or type(xs)!=int or not -5<=es<=5 or not -5<=xs<=5:raise ValueError('frozen grid')
    s=record['Schedule'];d=datetime(2020,1,6)+timedelta(days=record['AnchorWeekday'])
    e=d.replace(hour=s['EntryMinute']//60,minute=s['EntryMinute']%60)
    x=(d+timedelta(days=s['ExitDayOffset'])).replace(hour=s['ExitMinute']//60,minute=s['ExitMinute']%60)
    if int((x-e).total_seconds()/60)!=s['HoldingMinutes']:raise ValueError('anchor holding')
    a=e+timedelta(minutes=es);b=x+timedelta(minutes=xs);off=(b.date()-a.date()).days;h=int((b-a).total_seconds()/60)
    reason=None
    if a.date()!=e.date():reason='ENTRY_DATE_CHANGED'
    elif a.weekday()!=e.weekday():reason='ENTRY_WEEKDAY_CHANGED'
    elif off!=s['ExitDayOffset']:reason='EXIT_DAY_OFFSET_CHANGED'
    elif h<30 or h>1440:reason='HOLDING_OUT_OF_RANGE'
    elif a.weekday()>4:reason='EXECUTION_SCHEDULE_INVALID'
    p=dict(PointID=f'{es:+d}/{xs:+d}',EntryShiftMinutes=es,ExitShiftMinutes=xs,EntryMinute=a.hour*60+a.minute,ExitMinute=b.hour*60+b.minute,ExitDayOffset=off,HoldingMinutes=h,Valid=reason is None,InvalidReason=reason)
    p['FixedKey']=[record['Symbol'],0 if s['Direction']=='LONG' else 1,record['AnchorWeekday'],p['EntryMinute'],off,p['ExitMinute'],h,record['CandidateID']];return p

def formal(m):
    return bool(m['Trades']>=150 and min(m['Annual'][str(y)]['Trades'] for y in range(2020,2024))>=30 and m['Losses']>=10 and m['AvgPips'] is not None and m['AvgPips']>0 and m['PFState']=='FINITE' and m['PFpips']>=1.10 and m['PositiveYearCount']>=3)

def assemble(record,points):
    ps=sorted(points,key=lambda p:(p['EntryShiftMinutes'],p['ExitShiftMinutes']));ns=[]
    for c in ps:
        ms=[]
        for p in ps:
            if p['Valid'] and p['EntryShiftMinutes'] in range(c['EntryShiftMinutes']-1,c['EntryShiftMinutes']+2) and p['ExitShiftMinutes'] in range(c['ExitShiftMinutes']-1,c['ExitShiftMinutes']+2):ms.append(p)
        vals=[p['Metrics']['AvgPips'] for p in ms];finite=[p['Metrics']['PFpips'] for p in ms if p['Metrics']['PFState']=='FINITE' and p['Metrics']['PFpips'] is not None]
        avg=None if not vals or None in vals else median(vals);pf=median(finite) if finite else None
        cm=c['Metrics'];ca=cm['AvgPips'] if cm else None
        if c['FormalPASS'] and ca is None:raise ValueError('FormalPASS center invariant')
        n=len(ms);passed=sum(p['FormalPASS'] for p in ms)
        checks=dict(CenterFormalPASS=c['FormalPASS'],MinimumValidPoints=n>=4,FormalPASSRatio=3*passed>=2*n if n else False,MedianRetention=avg is not None and ca is not None and avg>=0.8*ca)
        ok=all(checks.values())
        if ok and not finite:raise ValueError('ranking finite-set invariant')
        ns.append(dict(CenterPointID=c['PointID'],EntryShiftMinutes=c['EntryShiftMinutes'],ExitShiftMinutes=c['ExitShiftMinutes'],CenterMetrics=cm,NeighborhoodMembers=[p['PointID'] for p in ms],ValidPointCount=n,FormalPASSCount=passed,FormalPASSRatio=passed/n if n else None,AllValidMedianAvgPips=avg,NeighborhoodMedianPFpips=pf,Center80Threshold=ca*0.8 if ca is not None else None,Checks=checks,PlateauPASS=ok,Reason='UNDEFINED_VALID_NEIGHBOR_AVG' if None in vals else ('EMPTY_VALID_NEIGHBORHOOD' if not n else None),L1=abs(c['EntryShiftMinutes'])+abs(c['ExitShiftMinutes']),FixedKey=c['FixedKey']))
    ranked=sorted([n for n in ns if n['PlateauPASS']],key=lambda n:(-n['AllValidMedianAvgPips'],-n['NeighborhoodMedianPFpips'],-n['CenterMetrics']['MedianAnnualAvgPips'],n['L1'],*n['FixedKey']))
    anchor=next(n for n in ns if n['CenterPointID']=='+0/+0');base=anchor['AllValidMedianAvgPips'];best=ranked[0] if ranked else None
    threshold=None if base is None else max(0.05,0.025*base);delta=None if best is None or base is None else best['AllValidMedianAvgPips']-base
    if not ranked:decision='ANCHOR_RETAINED_NO_1M_PLATEAU'
    elif best['CenterPointID']=='+0/+0':decision='ANCHOR_RETAINED_BEST_IS_ANCHOR'
    elif base is None:decision='ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE'
    elif delta>=threshold:decision='FINE_TUNED'
    else:decision='ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT'
    selection=dict(Decision=decision,BestCandidate=best['CenterPointID'] if best else None,AnchorBaseline=base,RequiredImprovement=threshold,ActualImprovement=delta)
    chosen=next(p for p in ps if p['PointID']==(best['CenterPointID'] if decision=='FINE_TUNED' else '+0/+0'))
    return result(record,ps,ns,ranked,anchor,selection,chosen)

def evaluate_candidate(bars,record,days=None):return evaluate_points(bars,record,[(e,x) for e in range(-5,6) for x in range(-5,6)],days)

def evaluate_points(bars,record,shifts,days=None):
    validate(bars);dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D') if days is None else pd.DatetimeIndex(days)
    if dates.tz is not None or dates.has_duplicates or any(dates!=dates.normalize()) or any(d<START or d>=END for d in dates):raise ValueError('Discovery dates')
    if len(set(shifts))!=len(shifts):raise ValueError('duplicate point')
    points=[];logs={}
    for es,xs in sorted(shifts):
        p=schedule(record,es,xs);trades=[];m=None
        if p['Valid']:
            for d in sorted(dates):
                bucket='D1' if d.day<=10 else ('D2' if d.day<=20 else 'D3')
                if d.weekday() not in record['FormalWeekdays'] or d.month not in record['FormalMonths'] or bucket not in record['FormalDOMBuckets']:continue
                e=d+pd.Timedelta(minutes=p['EntryMinute']);x=d+pd.Timedelta(days=p['ExitDayOffset'],minutes=p['ExitMinute']);key=list(p['FixedKey']);key[2]=d.weekday()
                t=execute(bars,record['Symbol'],record['Schedule']['Direction'],e,x,record['FormalSL'],key,record['FormalTP'])
                if t['Status']=='OK':trades.append(t)
            logs[p['PointID']]=trades;m=summarize(trades)
        points.append(dict(p,Metrics=m,FormalPASS=formal(m) if p['Valid'] else False))
    return assemble(record,points),logs
