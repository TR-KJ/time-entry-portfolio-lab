"""Prespecified bounded 3x3 actual replay on synthetic schedules only."""
import pandas as pd
from .stage1_contract import Structure
from .stage1_input import load_discovery
from .u09_input import input_config
from .u09_execution import Engine,evaluate_points
from .u09_reference import evaluate_points as reference
from .u09_schedule import schedule

def run_smoke(paths):
    cfg,_=input_config();s=cfg['Smoke'];cases=0;replays=0
    for sym in s['Symbols']:
        bars=load_discovery(paths,sym,s['Bounds']);engine=Engine(bars,sym)
        for direction in s['Directions']:
            for tp in s['TPPips']:
                anchor=Structure(sym,direction,1,s['EntryMinute'],s['HoldingMinutes'])
                cal=dict(FormalWeekdays=s['FormalWeekdays'],FormalDOMBuckets=s['FormalDOMBuckets'],OFFBuckets=[],FormalMonths=s['FormalMonths'],OFFMonths=list(range(3,13)))
                r=dict(CandidateID=anchor.candidate_id,Symbol=sym,PairRank=1,Schedule=anchor.definition(),FormalSL=s['SLPips'],FormalTP=tp,AnchorWeekday=1,SetName='W0',CalendarFreeze=cal,**cal,U08Status='PASS_U08',U08CandidateSHA256='synthetic',U08CheckpointSHA256='synthetic',U08ProducerImplementationSHA='synthetic',U07SourceIdentity={},U06SourceIdentity={})
                shifts=[(e,x) for e in s['Shifts'] for x in s['Shifts']]
                a=evaluate_points(engine,r,[schedule(r,e,x) for e,x in shifts],s['Days']);b=reference(bars,r,shifts,s['Days'])
                if a!=b or any(len(ts)!=6 for ts in a[1].values()):raise AssertionError('U09 bounded exact trade/policy replay')
                cases+=sum(len(ts) for ts in a[1].values());replays+=1
    return dict(Status='PASS',TradeCases=cases,FixedScheduleReplays=replays,PointCases=replays*9,NeighborhoodGrid='3x3 only',Bounds=s['Bounds'],Days=s['Days'],Comparison='EXACT_SCHEDULE_TRADES_METRICS_GATES_NEIGHBORHOODS_PF_AVG_RANKING_ANCHOR_THRESHOLD_DECISION',Formal54Used=False,FormalScheduleProduced=False,PerformanceSaved=False,FullSearch=False)
