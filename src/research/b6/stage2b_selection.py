"""Pure deterministic selection/grid/stability; no IO or execution imports."""
import math,statistics
from .stage2b_config import load_config
from .stage2a_config import STRUCTURE_KEYS

def setting_key(row):return (int(row['SL']),None if row['TP'] is None else int(row['TP']))

def fixed_key(row):
    return tuple(row[k] for k in ('Symbol','Direction','Weekday','EntryMinute','ExitDayOffset','ExitMinute','HoldingMinutes','CandidateID'))

def price_key(row):return (0 if row['TP'] is None else 1,row['SL'],-1 if row['TP'] is None else row['TP'])

def growth_key(row):return (-row['AvgR'],-row['TotalR'],row['MaxDDR'],*price_key(row),*fixed_key(row))

def efficiency(row):return row['TotalR']/max(row['MaxDDR'],1)

def efficiency_key(row):return (-efficiency(row),*growth_key(row))

def select_centers(candidate,rows):
    if any(r['CandidateID']!=candidate['CandidateID'] for r in rows):raise ValueError('mixed candidates')
    eligible=[r for r in rows if r['Pass'] is True]
    if not eligible:return []
    if any(not all(math.isfinite(r[k]) for k in ('AvgR','TotalR','MaxDDR')) for r in eligible):raise ValueError('nonfinite center metric')
    selected=[]
    for kind,key in (('GROWTH',growth_key),('EFFICIENCY',efficiency_key)):
        point=min(eligible,key=key);match=next((x for x in selected if setting_key(x)==setting_key(point)),None)
        if match is not None:match['CenterAliases'].append(kind);continue
        selected.append({**candidate,'SL':point['SL'],'TP':point['TP'],'TPMode':point['TPMode'],'CenterType':kind,'CenterAliases':[kind],'AvgR':point['AvgR'],'TotalR':point['TotalR'],'MaxDDR':point['MaxDDR'],'Efficiency':efficiency(point)})
    return selected

def center_grid(center,c):
    g=c['local_grid'];step=g['step_pips'];radius=g['radius_pips'];slo,shi=g['sl_bounds'];tlo,thi=g['tp_bounds']
    return [(sl,tp) for sl in range(center['SL']-radius,center['SL']+radius+1,step) if slo<=sl<=shi for tp in ([None] if center['TP'] is None else range(center['TP']-radius,center['TP']+radius+1,step)) if tp is None or tlo<=tp<=thi]

def local_grid(centers,c=None):
    c=load_config() if c is None else c;points={}
    for center in centers:
        for sl,tp in center_grid(center,c):
            row=points.setdefault((sl,tp),dict(SL=sl,TP=tp,TPMode='TP_NONE' if tp is None else 'FINITE',TPRatio=None if tp is None else tp/sl,ActualTPRatio=None if tp is None else tp/sl,RatioAliases=[],CenterAliases=[]))
            row['CenterAliases']=list(dict.fromkeys(row['CenterAliases']+center['CenterAliases']))
    grid=sorted(points.values(),key=price_key)
    if len(grid)>c['theoretical_max_per_candidate']:raise ValueError('grid exceeds bound')
    return grid

def final_key(row):
    return (-row['NeighborhoodMedianAvgR'],-row['NeighborhoodPassRate'],-row['AvgR'],row['CenterDistance'],row['MaxDDR'],*price_key(row),*fixed_key(row))

def distance(point,center,step):
    return (abs(point['SL']-center['SL'])+(0 if point['TP'] is None else abs(point['TP']-center['TP'])))/step

def stability(candidate,centers,rows,c=None):
    c=load_config() if c is None else c
    expected=local_grid(centers,c);lookup={setting_key(r):r for r in rows}
    if len(lookup)!=len(rows) or set(lookup)!={setting_key(x) for x in expected}:raise ValueError('incomplete/duplicate local evaluation grid')
    scoped=[];unique=[];radius=c['stability']['radius_pips'];step=c['local_grid']['step_pips']
    scopes=[(center,set(center_grid(center,c))) for center in centers]
    for gridrow in expected:
        key=setting_key(gridrow);point=lookup[key]
        if any(point[k]!=candidate[k] for k in STRUCTURE_KEYS):raise ValueError('time structure changed')
        aliases=[(center,keys) for center,keys in scopes if key in keys]
        min_distance=min(distance(point,center,step) for center,_ in aliases);versions=[]
        for center,keys in aliases:
            neighbors=[lookup[k] for k in sorted(keys,key=lambda x:(x[0],-1 if x[1] is None else x[1])) if abs(k[0]-key[0])<=radius and (k[1] is None if key[1] is None else k[1] is not None and abs(k[1]-key[1])<=radius)]
            n=len(neighbors);passed=sum(r['Pass'] is True for r in neighbors)
            finite=all(isinstance(r[k],(int,float)) and math.isfinite(r[k]) for r in neighbors for k in ('AvgR','TotalR','MaxDDR'))
            ma=statistics.median(r['AvgR'] for r in neighbors) if finite else None
            reasons=[]
            if point['Pass'] is not True:reasons.append('POINT_P02_FAIL')
            if passed*c['stability']['pass_fraction_denominator']<n*c['stability']['pass_fraction_numerator']:reasons.append('NEIGHBOR_PASS_FRACTION')
            if not finite:reasons.append('UNDEFINED_NEIGHBOR_METRICS')
            elif ma<point['AvgR']*c['stability']['median_avg_r_factor']:reasons.append('NEIGHBOR_MEDIAN_AVGR')
            row={**point,'PointAvgR':point['AvgR'],'CenterAliases':gridrow['CenterAliases'],'SourceCenterType':center['CenterType'],'SourceCenterAliases':center['CenterAliases'],'SourceCenterSL':center['SL'],'SourceCenterTP':center['TP'],'CenterDistance':min_distance,'SourceCenterDistance':distance(point,center,step),'NeighborhoodCount':n,'NeighborhoodPassCount':passed,'NeighborhoodPassRate':passed/n,'NeighborhoodMedianAvgR':ma,'NeighborhoodMedianTotalR':statistics.median(r['TotalR'] for r in neighbors) if finite else None,'NeighborhoodWorstMaxDDR':max(r['MaxDDR'] for r in neighbors) if finite else None,'StabilityPass':not reasons,'StabilityFailReasons':'|'.join(reasons)}
            scoped.append(row);versions.append(row)
        passing=[r for r in versions if r['StabilityPass']]
        # Only passing aliases may supply the representative metrics.
        best=min(passing,key=lambda r:(final_key(r),r['SourceCenterType'])) if passing else versions[0]
        unique.append(best)
    return unique,scoped

def final_selection(candidate,centers,rows,yearly,c=None):
    unique,scoped=stability(candidate,centers,rows,c)
    passing=[r for r in unique if r['StabilityPass']]
    if not passing:
        reason='STAGE2B_DROPPED_NO_P02_CENTER' if not centers else 'STAGE2B_DROPPED_NO_STABLE_POINT'
        return dict(selected=None,dropped={**candidate,'Reason':reason},stability=unique,neighborhoods=scoped)
    best=dict(min(passing,key=final_key));best['YearlyMetrics']=[y for y in yearly if setting_key(y)==setting_key(best)];best['SelectedSL']=best['SL'];best['SelectedTP']=best['TP'];best['Status']='STAGE2B_SELECTED_SL_TP_FROZEN'
    return dict(selected=best,dropped=None,stability=unique,neighborhoods=scoped)
