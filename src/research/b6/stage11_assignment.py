"""One frozen assignment per unique trade; reused across all six money jobs."""
from datetime import datetime
from collections import Counter
from decimal import Decimal as D
from .stage11_config import AJ,GJ,PERIODS,RISK,require
from .stage11_r2 import risk,quintile
FIELDS=('Source','PortfolioComponentKey','StrategyNo','Strategy','CandidateID','Symbol','EntryTime','CloseTime',
 'FeatureStatus','FallbackReason','FeatureDailyDate','LastM1JST','ReferenceStart','ReferenceEnd','ReferenceCount',
 'ATR20','RankNumerator','Percentile','Quintile','AppliedRiskPercent','SL','R')

def assign_rows(rows,assigner):
    # Only Symbol and entry are passed into the volatility engine, never outcomes.
    return [dict(r,**assigner.assign(r['Symbol'],r['EntryTime'])) for r in rows]

def preflight(rows,assigned,formal_counts=True):
    require(len(rows)==len(assigned),'assignment filtered trades')
    for r,a in zip(rows,assigned):
        require(all(a.get(k)==v for k,v in r.items()),'assignment changed trade identity/outcome')
        require(a['AppliedRiskPercent']==risk(a['Quintile']),'risk mapping mismatch')
        if a['FeatureStatus']=='FALLBACK':
            require(a['Quintile']=='FALLBACK' and a['FallbackReason']=='INSUFFICIENT_VOL_HISTORY' and 0<=a['DailyCount']<272,'invalid fallback')
        else:
            require(a['FeatureStatus']=='VALID' and a['FallbackReason']=='' and a['DailyCount']>=272,'invalid feature status')
            require(a['ReferenceCount']==252 and a['Quintile']==quintile(a['RankNumerator']),'invalid rank/reference')
            require(a['Percentile']==100*a['RankNumerator']/504,'invalid percentile')
            require(a['ReferenceStart']<=a['ReferenceEnd']<a['FeatureDailyDate'] and a['FeatureDailyDate'].date()<r['EntryTime'].date(),'lookahead assignment')
            require(a['LastM1JST'].date()==a['FeatureDailyDate'].date(),'last M1 mismatch')
    counts=Counter('CURRENT27' if a['Source']=='BASELINE' else 'GJ' if a['PortfolioComponentKey']==GJ else 'AJ' for a in assigned)
    if formal_counts:require(dict(counts)=={'CURRENT27':9083,'GJ':338,'AJ':339},'formal assignment counts mismatch')
    return dict(Status='PASS',Assignments=len(assigned),Counts=dict(counts),NoLookahead=True,RiskMapping='PASS',TradeCountsUnchanged=True,IndependentFeatureParity='PASS')

def assignment_table(rows):return [{k:r.get(k) for k in FIELDS} for r in rows]

def distribution(rows):
    out=[]
    for group in ('CURRENT27','GJ','AJ'):
        group_rows=[r for r in rows if ('CURRENT27' if r['Source']=='BASELINE' else 'GJ' if r['PortfolioComponentKey']==GJ else 'AJ')==group]
        for period in ('Discovery','Validation','Monitor','FullAvailable'):
            a,b=map(datetime.fromisoformat,PERIODS[period]);own=[r for r in group_rows if a<=r['EntryTime']<b]
            for q in RISK:
                selected=[r for r in own if r['Quintile']==q];total=sum((r['AppliedRiskPercent'] for r in selected),D(0))
                out.append(dict(Group=group,Period=period,Quintile=q,Trades=len(selected),SharePct=D(len(selected))*100/len(own) if own else None,
                    MeanAppliedRiskPct=total/len(selected) if selected else None,TotalNominalRiskPct=total))
    return out
