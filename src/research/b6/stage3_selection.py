"""Valid evaluated neighbors only; exactly median, anchor distance, time key."""
import math,statistics
from .stage3_grid import time_grid,point_key

def final_key(row):
    return (-row['NeighborhoodMedianAvgR'],row['AnchorDistance'],row['AdjustedEntryMinute'],row['AdjustedExitDayOffset'],row['AdjustedExitMinute'],row['EntryDeltaMinutes'],row['ExitDeltaMinutes'],row['CandidateID'])

def stability(candidate,rows,c):
    grid,_=time_grid(candidate,c);lookup={point_key(r):r for r in rows}
    if len(lookup)!=len(rows) or set(lookup)!={point_key(p) for p in grid}:raise ValueError('incomplete/duplicate time grid')
    for p in grid:
        if any(lookup[point_key(p)][k]!=v for k,v in p.items()):raise ValueError('schedule or fixed SL/TP changed')
    result=[];s=c['stability']
    for p in grid:
        e,x=point_key(p);point=lookup[(e,x)]
        neighbors=[lookup[(ee,xx)] for ee in range(e-1,e+2) for xx in range(x-1,x+2) if (ee,xx) in lookup]
        n=len(neighbors);passed=sum(r['Pass'] is True for r in neighbors)
        finite=all(isinstance(r[k],(int,float)) and math.isfinite(r[k]) for r in neighbors for k in ('AvgR','TotalR','MaxDDR'))
        med=statistics.median(r['AvgR'] for r in neighbors) if finite else None;reasons=[]
        if point['Pass'] is not True:reasons.append('POINT_P02_FAIL')
        if passed*s['pass_denominator']<n*s['pass_numerator']:reasons.append('NEIGHBOR_PASS_FRACTION')
        if not finite:reasons.append('UNDEFINED_NEIGHBOR_METRICS')
        elif med<point['AvgR']*s['median_avgr_factor']:reasons.append('NEIGHBOR_MEDIAN_AVGR')
        result.append({**point,'NeighborhoodCount':n,'NeighborhoodPassCount':passed,'NeighborhoodPassRate':passed/n,'NeighborhoodMedianAvgR':med,'NeighborhoodMedianTotalR':statistics.median(r['TotalR'] for r in neighbors) if finite else None,'NeighborhoodWorstMaxDDR':max(r['MaxDDR'] for r in neighbors) if finite else None,'PointAvgR':point['AvgR'],'StabilityPass':not reasons,'StabilityFailReason':'|'.join(reasons)})
    return result

def select_final(candidate,rows,yearly,c):
    stable=stability(candidate,rows,c);passing=[r for r in stable if r['StabilityPass']]
    if not passing:return dict(stability=stable,selected=None,dropped=dict(CandidateID=candidate['CandidateID'],Reason='STAGE3_DROPPED_NO_STABLE_TIME'))
    best=dict(min(passing,key=final_key));e=best['AdjustedEntryMinute'];x=best['AdjustedExitMinute']
    best.update(FinalEntryJST=f'{e//60:02d}:{e%60:02d}',FinalExitJST=f'{x//60:02d}:{x%60:02d}',FinalExitDayOffset=best['AdjustedExitDayOffset'],FinalHoldingMinutes=best['PlannedHoldingMinutes'],YearlyMetrics=[r for r in yearly if point_key(r)==point_key(best)],Status='STAGE3_SELECTED_TIME_AND_SL_TP_FROZEN')
    if len(best['YearlyMetrics'])!=4:raise ValueError('four Discovery yearly metrics required')
    return dict(stability=stable,selected=best,dropped=None)
