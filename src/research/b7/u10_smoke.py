"""Prespecified synthetic schedules on bounded actual Discovery rows; never formal54."""
from copy import deepcopy
from .stage1_input import load_discovery
from .u10_input import input_config
from .u10_calendar import audit_calendar
from .u10_execution import Engine,evaluate_candidate
from .u10_reference import evaluate_candidate as reference

def synthetic_record(symbol,direction,sl,tp,schedule):
    cal=dict(FormalWeekdays=list(range(5)),FormalDOMBuckets=['D1','D2','D3'],OFFBuckets=[],FormalMonths=list(range(1,13)),OFFMonths=[])
    return dict(CandidateID='U10_SMOKE:'+symbol+':'+direction+':'+str(schedule['EntryMinute'])+':'+str(tp),Symbol=symbol,PairRank=0,Direction=direction,FormalEntryMinute=schedule['EntryMinute'],FormalExitMinute=schedule['ExitMinute'],FormalExitDayOffset=schedule['ExitDayOffset'],FormalHoldingMinutes=schedule['HoldingMinutes'],FormalSL=sl,FormalTP=tp,AnchorWeekday=0,SetName='SYNTHETIC',CalendarFreeze=deepcopy(cal),**cal,EntryShiftMinutes=0,ExitShiftMinutes=0,U09Decision='SYNTHETIC_ONLY',U09Status='PASS_U09',U09ProducerImplementationSHA='SYNTHETIC',U09CandidateSHA256='SYNTHETIC',U09CheckpointSHA256='SYNTHETIC',U08SourceIdentity={},U07SourceIdentity={},U06SourceIdentity={})

def run_smoke(paths):
    cfg,data=input_config();s=cfg['Smoke'];calendar=audit_calendar();replays=trades=0
    formal={(r['Symbol'],r['Direction'],r['FormalEntryMinute'],r['FormalExitMinute'],r['FormalExitDayOffset']) for r in data['Candidates']}
    for sym in s['Symbols']:
        bars=load_discovery(paths,sym,s['Bounds']);engine=Engine(bars,sym)
        for direction in s['Directions']:
            for tp in s['TPPips']:
                for schedule in s['Schedules']:
                    if (sym,direction,schedule['EntryMinute'],schedule['ExitMinute'],schedule['ExitDayOffset']) in formal:raise ValueError('smoke must be separate from formal schedules')
                    r=synthetic_record(sym,direction,s['SLPips'],tp,schedule)
                    a=evaluate_candidate(engine,r,s['Days'],calendar);b=reference(bars,r,calendar,s['Days'])
                    if a!=b:raise AssertionError('U10 reference/optimized mismatch')
                    replays+=1;trades+=len(a[1]['Streams']['E0'])
    if replays!=16 or trades==0:raise AssertionError('bounded actual smoke inventory')
    return dict(Status='PASS',FixedScheduleReplays=replays,E0TradeCases=trades,Bounds=s['Bounds'],Days=s['Days'],Comparison='EXACT_E0_TRADES_PLANNED_TIMES_CLOSE_PIPS_EVENTS_WINDOWS_OVERLAPS_REMOVED_IDS_RETAINED_IDS_METRICS_ANNUAL_PF_DD_GATE_STATUS',Formal54Used=False,FormalCandidateStatusProduced=False,FormalU10PerformanceSaved=False,Full54Run=False,ValidationUsed=False,MonitorUsed=False)
