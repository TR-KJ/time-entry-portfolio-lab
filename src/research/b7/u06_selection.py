"""Frozen U06 policy, without data access."""
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from .stage1_metrics import gate

def round5(v):return int((Decimal(str(v))/5).quantize(Decimal('1'),rounding=ROUND_HALF_UP))*5

def local_grid(a,sl=False):
    if not isinstance(a,int) or a<=0 or a%5:raise ValueError('positive five-pip anchor')
    lo=round5(Decimal(a)*Decimal('.8'));hi=round5(Decimal(a)*Decimal('1.2'))
    pts=sorted(set(range(lo,hi+1,5))|{a})
    if sl and len(pts)<3:pts=[a-5,a,a+5]
    if min(pts)<=0:raise ValueError('nonpositive grid')
    return pts

def merged_grid(anchors,sl=False):return sorted({p for a in anchors for p in local_grid(a,sl)})
def zone_key(z):return (-z['MedianAvgPips'],-len(z['Points']),-z['WorstAvgPips'],-z['MedianPFpips'],z['CentralValue'])
def zones(points,pure=None):
    runs=[];run=[]
    for p in sorted(points):
        if not gate(points[p],True):
            if run:runs.append(run);run=[]
            continue
        if run and p!=run[-1]+5:runs.append(run);run=[]
        run.append(p)
    if run:runs.append(run)
    out=[]
    for pts in runs:
        if len(pts)<3:continue
        avgs=[points[p]['AvgPips'] for p in pts]
        z=dict(Points=pts,MedianAvgPips=median(avgs),WorstAvgPips=min(avgs),MedianPFpips=median(points[p]['PFpips'] for p in pts),CentralValue=pts[(len(pts)-1)//2])
        z.update(RetentionThreshold=None if pure is None else pure*.8,Qualified=pure is None or z['MedianAvgPips']>=pure*.8);out.append(z)
    return out

def winner(zs):return min((z for z in zs if z['Qualified']),key=zone_key,default=None)
def coarse_anchors(sl):return sorted({max(5,round5(Decimal(sl)*r)) for r in map(Decimal,('.5','1','1.5','2','3'))})
def eligible_anchors(points):
    keys=sorted(points);ok={p for p in keys if gate(points[p],True)}
    return [p for j,p in enumerate(keys) if p in ok and any(keys[k] in ok for k in (j-1,j+1) if 0<=k<len(keys))]
def tp_comparison(finite,base):
    threshold=max(.10,base['MedianAnnualAvgPips']*.05);delta=finite['MedianAnnualAvgPips']-base['MedianAnnualAvgPips']
    checks=dict(PositiveYearNonDegradation=finite['PositiveYearCount']>=base['PositiveYearCount'],WorstYearNonDegradation=finite['WorstYearAvgPips']>=base['WorstYearAvgPips'],MedianAnnualImprovement=delta>=threshold)
    return dict(RequiredImprovement=threshold,ActualImprovement=delta,Checks=checks,AdoptFinite=all(checks.values()))
def select(record,evaluate):
    cache={}
    def ev(sl,tp):
        if (sl,tp) not in cache:cache[sl,tp]=evaluate(sl,tp)
        return cache[sl,tp]
    anchors=[x['SLPips'] for x in record['FiveSLMetrics'] if gate(x['Metrics'],True)]
    grid=merged_grid(anchors,True);sm={p:ev(p,None) for p in grid};zs=zones(sm,record['PureMetrics']['AvgPips']);chosen=winner(zs)
    out=dict(CandidateID=record['CandidateID'],PairRank=record['PairRank'],Symbol=record['Symbol'],Schedule=record['Schedule'],PASSAnchors=anchors,SLGrid=grid,SLPoints=[dict(SLPips=p,Metrics=sm[p],GatePASS=gate(sm[p],True)) for p in grid],SLZones=zs,ChosenSLZone=chosen,FormalSL=None,FormalTP=None,Status='DROP_U06_SL',DropReason='CANDIDATE_DROP_U06_SL',TP=None)
    if chosen is None:return out
    sl=chosen['CentralValue'];base=ev(sl,None);coarse={p:ev(sl,p) for p in coarse_anchors(sl)};eligible=eligible_anchors(coarse);tg=merged_grid(eligible);tm={p:ev(sl,p) for p in tg};tz=zones(tm);tw=winner(tz);finite=None if tw is None else tw['CentralValue'];cmp=None if finite is None else tp_comparison(tm[finite],base)
    out.update(FormalSL=sl,FormalTP=finite if cmp and cmp['AdoptFinite'] else None,Status='PASS_U06',DropReason=None,TP=dict(Baseline=base,Coarse=[dict(TPPips=p,Metrics=coarse[p],GatePASS=gate(coarse[p],True)) for p in coarse],EligibleAnchors=eligible,LocalGrid=tg,Local=[dict(TPPips=p,Metrics=tm[p],GatePASS=gate(tm[p],True)) for p in tg],Zones=tz,ChosenZone=tw,FiniteTPCandidate=finite,Comparison=cmp))
    return out
