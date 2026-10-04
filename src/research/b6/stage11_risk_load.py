"""Elapsed [entry,close) exposure proxies, never actual lot or broker margin."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal as D
from .stage11_config import AJ,GJ
from .stage10_input import legacy


def exposure(rows,start,end):
    a,b=datetime.fromisoformat(start),datetime.fromisoformat(end)
    own=[r for r in rows if a<=r['EntryTime']<b]
    events=defaultdict(lambda: [[],[]])
    for i,r in enumerate(own):
        if r['EntryTime']==r['CloseTime']:continue
        events[r['EntryTime']][1].append(i);events[r['CloseTime']][0].append(i)
    active={};last=a;area=D(0);max_all=max_b6=0
    max_risk=D(0)
    both=either=D(0);both_weeks=set()
    candidate={cid:dict(AnyExistingOverlapMinutes=D(0),SameSymbolExistingOverlapMinutes=D(0),
                       MaxConcurrentExistingPlusCandidatePositions=0) for cid in (AJ,GJ)}
    for t in sorted({a,b,*events}):
        minutes=D(str((t-last).total_seconds()))/60
        if minutes>0:
            current=list(active.values());n=len(current)
            existing=[r for r in current if r['Source']=='BASELINE']
            b6=[r for r in current if r['Source']=='B6']
            max_risk=max(max_risk,sum((r['AppliedRiskPercent'] for r in current),D(0)))
            max_all=max(max_all,n);max_b6=max(max_b6,len(b6));area+=minutes*n
            ids={r['PortfolioComponentKey'] for r in b6}
            if ids:either+=minutes
            if {AJ,GJ}<=ids:
                both+=minutes;both_weeks.add(legacy.week_start(last))
            for cid in (AJ,GJ):
                matched=[r for r in b6 if r['PortfolioComponentKey']==cid]
                if not matched:continue
                o=candidate[cid]
                o['MaxConcurrentExistingPlusCandidatePositions']=max(o['MaxConcurrentExistingPlusCandidatePositions'],len(existing)+len(matched))
                if existing:o['AnyExistingOverlapMinutes']+=minutes
                if any(r['Symbol']==matched[0]['Symbol'] for r in existing):o['SameSymbolExistingOverlapMinutes']+=minutes
        for i in events[t][0]:active.pop(i)
        for i in events[t][1]:active[i]=own[i]
        last=t
    weeks={cid:{legacy.week_start(r['EntryTime']) for r in own if r['PortfolioComponentKey']==cid} for cid in (AJ,GJ)}
    concurrency=dict(MaxConcurrentPositions=max_all,AvgConcurrentPositions=area/(D(str((b-a).total_seconds()))/60),
                     MaxConcurrentB6Positions=max_b6,MaxConcurrentRiskPct=max_risk)
    overlap=[dict(Kind='B6_PAIR',CandidateID='AJ+GJ',BothOpenMinutes=both,EitherOpenMinutes=either,
        B6ExposureJaccard=both/either if either else None,WeeksBothTrade=len(weeks[AJ]&weeks[GJ]),
        WeeksBothSimultaneouslyOpen=len(both_weeks),AnyExistingOverlapMinutes=None,
        SameSymbolExistingOverlapMinutes=None,MaxConcurrentExistingPlusCandidatePositions=None)]
    overlap += [dict(Kind='B6_VS_EXISTING',CandidateID=cid,BothOpenMinutes=None,EitherOpenMinutes=None,
        B6ExposureJaccard=None,WeeksBothTrade=None,WeeksBothSimultaneouslyOpen=None,**candidate[cid]) for cid in (AJ,GJ)]
    return concurrency,overlap
