"""U09 fixed-grid policy and U09-S01/S02; no price loading or re-anchor."""
from copy import deepcopy
from statistics import median
from .stage1_metrics import gate
from .u09_schedule import SHIFTS

def point(p,metrics):
    out=dict(p,Metrics=metrics,FormalPASS=False)
    if p['Valid']:
        if metrics is None:raise ValueError('valid point metrics required')
        out['FormalPASS']=gate(metrics)
    elif metrics is not None:raise ValueError('invalid point evaluated')
    return out

def median_pf(members,required=False):
    values=[p['Metrics']['PFpips'] for p in members if p['Metrics']['PFState']=='FINITE' and p['Metrics']['PFpips'] is not None]
    if not values and required:raise ValueError('ranking finite-set invariant')
    return median(values) if values else None

def neighborhood(center,points):
    e,x=center['EntryShiftMinutes'],center['ExitShiftMinutes']
    members=[p for p in points if p['Valid'] and abs(p['EntryShiftMinutes']-e)<=1 and abs(p['ExitShiftMinutes']-x)<=1]
    n=len(members);pc=sum(p['FormalPASS'] for p in members)
    vals=[p['Metrics']['AvgPips'] for p in members]
    avg=median(vals) if vals and all(v is not None for v in vals) else None
    cm=center['Metrics'];ca=cm['AvgPips'] if cm else None
    if center['FormalPASS'] and ca is None:raise ValueError('FormalPASS center Avg invariant')
    checks=dict(CenterFormalPASS=center['FormalPASS'],MinimumValidPoints=n>=4,FormalPASSRatio=pc*3>=n*2 if n else False,MedianRetention=avg is not None and ca is not None and avg>=ca*0.80)
    passed=all(checks.values());pf=median_pf(members,passed)
    reason='UNDEFINED_VALID_NEIGHBOR_AVG' if any(v is None for v in vals) else ('EMPTY_VALID_NEIGHBORHOOD' if not n else None)
    return dict(CenterPointID=center['PointID'],EntryShiftMinutes=e,ExitShiftMinutes=x,CenterMetrics=cm,NeighborhoodMembers=[p['PointID'] for p in members],ValidPointCount=n,FormalPASSCount=pc,FormalPASSRatio=pc/n if n else None,AllValidMedianAvgPips=avg,NeighborhoodMedianPFpips=pf,Center80Threshold=ca*0.80 if ca is not None else None,Checks=checks,PlateauPASS=passed,Reason=reason,L1=abs(e)+abs(x),FixedKey=center['FixedKey'])

def ranking_key(n):
    if not n['PlateauPASS'] or n['NeighborhoodMedianPFpips'] is None:raise ValueError('eligible finite ranking invariant')
    return (-n['AllValidMedianAvgPips'],-n['NeighborhoodMedianPFpips'],-n['CenterMetrics']['MedianAnnualAvgPips'],n['L1'],*n['FixedKey'])

def decide(ranked,anchor):
    baseline=anchor['AllValidMedianAvgPips'];best=ranked[0] if ranked else None
    required=max(0.05,baseline*0.025) if baseline is not None else None
    actual=best['AllValidMedianAvgPips']-baseline if best and baseline is not None else None
    if best is None:d='ANCHOR_RETAINED_NO_1M_PLATEAU'
    elif best['EntryShiftMinutes']==best['ExitShiftMinutes']==0:d='ANCHOR_RETAINED_BEST_IS_ANCHOR'
    elif baseline is None:d='ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE'
    elif actual<required:d='ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT'
    else:d='FINE_TUNED'
    return dict(Decision=d,BestCandidate=best['CenterPointID'] if best else None,AnchorBaseline=baseline,RequiredImprovement=required,ActualImprovement=actual)

def assemble(record,points):
    points=sorted(deepcopy(points),key=lambda p:(p['EntryShiftMinutes'],p['ExitShiftMinutes']))
    shifts=[(p['EntryShiftMinutes'],p['ExitShiftMinutes']) for p in points]
    if len(set(shifts))!=len(points) or (0,0) not in shifts or any(e not in SHIFTS or x not in SHIFTS for e,x in shifts):raise ValueError('unique bounded grid with anchor')
    ns=[neighborhood(p,points) for p in points];ranked=sorted((n for n in ns if n['PlateauPASS']),key=ranking_key)
    anchor=next(n for n in ns if n['EntryShiftMinutes']==n['ExitShiftMinutes']==0);sel=decide(ranked,anchor)
    wanted=sel['BestCandidate'] if sel['Decision']=='FINE_TUNED' else '+0/+0';chosen=next(p for p in points if p['PointID']==wanted)
    return result(record,points,ns,ranked,anchor,sel,chosen)

def result(record,points,ns,ranked,anchor,sel,chosen):
    if not chosen['Valid']:raise ValueError('invalid final schedule')
    out={k:deepcopy(record[k]) for k in ('CandidateID','Symbol','PairRank','FormalSL','FormalTP','AnchorWeekday','FormalWeekdays','SetName','FormalDOMBuckets','OFFBuckets','FormalMonths','OFFMonths','CalendarFreeze')}
    out['U08SourceIdentity']={k:deepcopy(record[k]) for k in ('U08Status','U08CandidateSHA256','U08CheckpointSHA256','U08ProducerImplementationSHA','U07SourceIdentity','U06SourceIdentity')}
    out.update(AnchorSchedule=deepcopy(record['Schedule']),Direction=record['Schedule']['Direction'],NominalPointCount=len(points),ValidPointCount=sum(p['Valid'] for p in points),InvalidPointCount=sum(not p['Valid'] for p in points),Points=points,Plateaus=ns,PlateauCandidateCount=len(ranked),RankedPlateau=[n['CenterPointID'] for n in ranked],AnchorNeighborhood=anchor,**sel,Status='PASS_U09')
    for k in ('EntryMinute','ExitMinute','ExitDayOffset','HoldingMinutes'):
        out['Anchor'+k]=record['Schedule'][k];out['Formal'+k]=chosen[k]
    for k in ('EntryShiftMinutes','ExitShiftMinutes'):out[k]=chosen[k]
    return out
