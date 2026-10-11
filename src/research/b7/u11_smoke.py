"""Prespecified bounded actual Validation replay with synthetic schedules only."""
from .u11_input import input_config
from .u11_data import load_validation
from .u11_engine import Engine
from .u11_execution import evaluate_candidate
from . import u11_reference as reference
from .u10_calendar import audit_calendar,event_set
from .candidate_freeze import exact

def synthetic_record(symbol='EURJPY',direction='LONG',mode='P0',entry=547,exit=1387,offset=0,tp=None):
    return dict(CandidateID=f'B7_U11_SMOKE:{symbol}:{direction}:{mode}:{entry}:{offset}:{exit}:{tp}',Symbol=symbol,Direction=direction,PairRank=0,FormalEntryMinute=entry,FormalExitMinute=exit,FormalExitDayOffset=offset,FormalHoldingMinutes=offset*1440+exit-entry,FormalWeekdays=[0,1,2,3,4],FormalDOMBuckets=['D1','D2','D3'],FormalMonths=list(range(1,13)),FormalSL=10,FormalTP=tp,FormalProtectionMode=mode,FormalEventMode='E2',E2EventSet=event_set(symbol,'E2'),SelectedModeDiscoveryMetrics=dict(Trades=200,Wins=120,Losses=80,ZeroPips=0,TotalPips=100.,AvgPips=.5,PFState='FINITE',PFpips=1.5,MaxDDPips=100.,Annual={},PositiveYearCount=4,NegativeYearCount=0,MedianAnnualAvgPips=.5,WorstYearAvgPips=.5),Synthetic=True)

def schedule_tuple(r):return (r['Symbol'],r['Direction'],r['FormalWeekdays'],r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'])

def run_smoke(paths):
    cfg,data=input_config();s=cfg['Smoke'];calendar=audit_calendar();replays=cases=baseline=0
    forbidden=[schedule_tuple(r) for r in data['Candidates']]
    for symbol in s['Symbols']:
        bars=load_validation(paths,symbol,s['Bounds']);engine=Engine(bars,symbol)
        for direction in s['Directions']:
            for sc in s['Schedules']:
                for tp in s['TPPips']:
                    for mode in s['Modes']:
                        r=synthetic_record(symbol,direction,mode,sc['EntryMinute'],sc['ExitMinute'],sc['ExitDayOffset'],tp)
                        if schedule_tuple(r) in forbidden or r['CandidateID'] in data['CandidateIDs']:raise ValueError('formal40 smoke contamination')
                        a,ad=evaluate_candidate(engine,r,calendar,s['Days'],implementation_sha='0'*40)
                        b,bd=reference.evaluate_candidate(bars,r,calendar,s['Days'],implementation_sha='0'*40)
                        if not exact(a,b) or not exact(ad,bd):raise ValueError('exact reference/optimized smoke mismatch')
                        replays+=1;cases+=len(a['TradeResults']);baseline+=len(ad['E0Executable'])
        del bars,engine
    return dict(Status='PASS',FixedScheduleReplays=replays,E0TradeCases=baseline,SelectedTradeCases=cases,ExactComparison='DAYS_E0_IDS_E2_OVERLAPS_BASELINE_EXECUTION_SELECTED_PROTECTION_MFE_MAE_WTL_METRICS_ANNUAL_MONTHLY_DD_SAMPLE_FORMAL_STATUS_DIAGNOSTICS',Bounds=s['Bounds'],Days=s['Days'],Formal40Used=False,FormalValidationStatusProduced=False,FormalU11PerformanceSaved=False,Full40Run=False,MonitorUsed=False,ActualValidationRowsUsed=True,SyntheticSchedulesOnly=True)
