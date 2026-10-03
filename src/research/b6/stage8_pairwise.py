"""Raw pairwise structural evidence. No cutoffs, families, ranking or selection."""
from itertools import combinations
import numpy as np
import pandas as pd
from .stage8_data import PERIODS
from .stage8_metrics import validate_ledger,period_records

UNDEFINED='UNDEFINED'
MATRIX_METRICS=('PearsonR','SpearmanR','TradeJaccard','LossJaccard','ActualExposureJaccard')

def ratio(n,d):return float(n/d) if d else UNDEFINED

def correlation(a,b):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    if len(a)!=len(b) or not np.isfinite(a).all() or not np.isfinite(b).all():raise ValueError('finite aligned correlation arrays required')
    if len(a)<2 or (a==a[0]).all() or (b==b[0]).all():return UNDEFINED
    return float(np.corrcoef(a,b)[0,1])

def interval(a,b):
    """Elapsed-minute intervals; missing exposure is empty, not an invented trade."""
    def duration(x):
        if x is None:return 0.
        d=(x[1]-x[0]).total_seconds()/60
        if d<0:raise ValueError('negative exposure duration')
        return d
    da,db=duration(a),duration(b)
    intersection=max(0.,(min(a[1],b[1])-max(a[0],b[0])).total_seconds()/60) if a is not None and b is not None else 0.
    return intersection,da+db-intersection,min(da,db)

def planned(point):
    start=pd.Timestamp('2020-01-06')+pd.Timedelta(days=point['Weekday'],minutes=point['AdjustedEntryMinute'])
    return start,start+pd.Timedelta(minutes=point['PlannedHoldingMinutes'])

def pair_metrics(a,b,records,label):
    if a['CandidateID']==b['CandidateID']:raise ValueError('no self-pair')
    rows=period_records(records,label)
    def indexed(cid):
        found=[r for r in rows if r['CandidateID']==cid];out={r['WeekKey']:r for r in found}
        if len(out)!=len(found):raise ValueError('duplicate WeekKey')
        return out
    aa,bb=indexed(a['CandidateID']),indexed(b['CandidateID']);wa,wb=set(aa),set(bb);both=sorted(wa&wb);either=sorted(wa|wb)
    ar=[float(aa[w]['R']) for w in both];br=[float(bb[w]['R']) for w in both]
    la={w for w,r in aa.items() if r['R']<0};lb={w for w,r in bb.items() if r['R']<0}
    inter=union=short=0.
    def exposure(row):return (pd.Timestamp(row['ActualEntry']),pd.Timestamp(row['ActualClose'])) if row else None
    for w in either:
        i,u,minimum=interval(exposure(aa.get(w)),exposure(bb.get(w)));inter+=i;union+=u
        if w in wa&wb:short+=minimum
    pi,pu,_=interval(planned(a),planned(b))
    return dict(Period=label,CandidateA=a['CandidateID'],CandidateB=b['CandidateID'],SameSymbol=a['Symbol']==b['Symbol'],ATradeWeeks=len(wa),BTradeWeeks=len(wb),BothTradeWeeks=len(both),EitherTradeWeeks=len(either),TradeJaccard=ratio(len(both),len(either)),PearsonR=correlation(ar,br),SpearmanR=correlation(pd.Series(ar,dtype=float).rank(method='average'),pd.Series(br,dtype=float).rank(method='average')),ALossWeeks=len(la),BLossWeeks=len(lb),BothLossWeeks=len(la&lb),EitherLossWeeks=len(la|lb),LossJaccard=ratio(len(la&lb),len(la|lb)),SignAgreementRate=ratio(sum(np.sign(x)==np.sign(y) for x,y in zip(ar,br)),len(both)),PlannedIntersectionMinutes=pi,PlannedUnionMinutes=pu,PlannedScheduleOverlapRatio=ratio(pi,pu),ActualIntersectionMinutes=inter,ActualUnionMinutes=union,ActualExposureJaccard=ratio(inter,union),BothTradeShorterMinutes=short,ShorterExposureCoverage=ratio(inter,short),EntryMinuteDifference=abs(a['AdjustedEntryMinute']-b['AdjustedEntryMinute']),ExitMinuteDifference=abs(a['AdjustedExitMinute']+1440*a['AdjustedExitDayOffset']-b['AdjustedExitMinute']-1440*b['AdjustedExitDayOffset']),HoldingMinuteDifference=abs(a['PlannedHoldingMinutes']-b['PlannedHoldingMinutes']),SLDifferencePips=abs(a['SL']-b['SL']),SameTPMode=a['TPMode']==b['TPMode'],SameEventMode=a['SelectedEventMode']==b['SelectedEventMode'])

def all_pairs(points,records):
    validate_ledger(records);ids=[p['CandidateID'] for p in points]
    if len(set(ids))!=len(ids) or any(r['CandidateID'] not in ids for r in records):raise ValueError('pool/ledger identity mismatch')
    return [pair_metrics(a,b,records,label) for label in PERIODS for a,b in combinations(points,2)]

def matrices(points,rows):
    """Display derivatives only, diagonal UNDEFINED; long form stays authoritative."""
    ids=[p['CandidateID'] for p in points];expected={(label,a,b) for label in PERIODS for a,b in combinations(ids,2)}
    if len(rows)!=len(expected) or {(r['Period'],r['CandidateA'],r['CandidateB']) for r in rows}!=expected:raise ValueError('incomplete/noncanonical long-form matrix input')
    result={}
    for label in PERIODS:
        for metric in MATRIX_METRICS:
            frame=pd.DataFrame(UNDEFINED,index=ids,columns=ids,dtype=object);frame.index.name='CandidateID'
            for r in rows:
                if r['Period']==label:frame.loc[r['CandidateA'],r['CandidateB']]=frame.loc[r['CandidateB'],r['CandidateA']]=r[metric]
            result[label+'_'+metric]=frame
    return result
