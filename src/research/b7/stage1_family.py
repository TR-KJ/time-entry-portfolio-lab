"""Nonrecursive all-valid Plateau and direct (non-transitive) family suppression."""
from collections import defaultdict
from itertools import product
import numpy as np
from .stage1_contract import Structure
from .stage1_metrics import ranking_key

def neighbors(s):
    for de, dx in product((-5, 0, 5), repeat=2):
        e, x = s.entry+de, s.exit+dx
        h = s.offset*1440+x-e
        # No date/weekday or exit-offset shift through midnight.
        if 0 <= e < 1440 and 0 <= x < 1440 and 30 <= h <= 1440:
            yield Structure(s.symbol, s.direction, s.weekday, e, h)

def plateau(s, lookup):
    members=[]
    for n in neighbors(s):
        r = lookup(n)
        if not r['ScheduleValid']: continue
        members.append(dict(CandidateID=n.candidate_id, FormalPASS=bool(r['FormalPASS']), AvgPips=r['AvgPips']))
    center=lookup(s); count=len(members); passes=sum(m['FormalPASS'] for m in members)
    # A data-empty but schedule-valid point stays in the population. Undefined
    # AvgPips makes the median undefined, rather than silently dropping that point.
    median = float(np.median([m['AvgPips'] for m in members])) if count and all(m['AvgPips'] is not None for m in members) else None
    passed=bool(center['FormalPASS'] and count>=4 and passes*3>=count*2 and median is not None
                and center['AvgPips'] is not None and median >= center['AvgPips']*.80)
    return dict(CandidateID=s.candidate_id, NeighborhoodMembers=members, ValidCount=count, PassCount=passes,
                PassRatio=passes/count if count else None, AllValidMedianAvgPips=median, PlateauPASS=passed)

def circular(a,b): return min(abs(a-b),1440-abs(a-b))

def near(a,b):
    return (a.symbol==b.symbol and a.direction==b.direction and a.offset==b.offset and circular(a.entry,b.entry)<=30
            and circular(a.exit,b.exit)<=30 and abs(a.holding-b.holding)<=30)

def _bucket(s): return (s.direction,s.offset,s.entry//30,s.exit//30,s.holding//30)

def families(records):
    if not records:return []
    if len({r['Symbol'] for r in records})!=1:raise ValueError('no cross-pair ranking')
    if len({r['CandidateID'] for r in records})!=len(records):raise ValueError('duplicate candidate')
    if any(not r['PlateauPASS'] for r in records):raise ValueError('non-Plateau candidate')
    ordered=sorted(records,key=ranking_key)
    structs=[Structure.from_record(r) for r in ordered]; buckets=defaultdict(set)
    for i,s in enumerate(structs):buckets[_bucket(s)].add(i)
    remaining=set(range(len(ordered))); output=[]
    for i,r in enumerate(ordered):
        if i not in remaining:continue
        rep=structs[i]; nearby=set()
        for de,dx,dh in product((-1,0,1),repeat=3):
            nearby.update(buckets.get((rep.direction,rep.offset,(rep.entry//30+de)%48,(rep.exit//30+dx)%48,rep.holding//30+dh),()))
        members=sorted(j for j in nearby & remaining if near(rep,structs[j]))
        remaining.difference_update(members)
        family=dict(Representative=r['CandidateID'], AnchorWeekday=rep.weekday,
                    SupportingWeekdays=sorted({structs[j].weekday for j in members}),
                    SuppressedCandidateIDs=[ordered[j]['CandidateID'] for j in members if j!=i],
                    SuppressionReason='DIRECT_REPRESENTATIVE_DISTANCE_NON_TRANSITIVE',
                    Members=[dict(Definition=structs[j].definition(), PureMetrics=ordered[j]['PureMetrics']) for j in members],
                    PairRank=len(output)+1, Top8=len(output)<8)
        output.append(family)
    return output
