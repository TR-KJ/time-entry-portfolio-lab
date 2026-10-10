"""Bounded actual Discovery replay on prespecified synthetic schedules only."""
from .stage1_input import load_discovery
from .stage1_contract import object_hash
from .stage1_metrics import summarize
from .u10p_input import input_config
from .u10_calendar import audit_calendar
from .u10_smoke import synthetic_record
from . import u10p_execution as opt,u10p_reference as ref

def run_smoke(paths):
    cfg,data=input_config();s=cfg['Smoke'];calendar=audit_calendar();replays=trades=0
    formal={(r['Symbol'],r['Direction'],r['FormalEntryMinute'],r['FormalExitMinute'],r['FormalExitDayOffset']) for r in data['Candidates']}
    for sym in s['Symbols']:
        bars=load_discovery(paths,sym,s['Bounds']);engine=opt.Engine(bars,sym)
        for direction in s['Directions']:
            for tp in s['TPPips']:
                for schedule in s['Schedules']:
                    if (sym,direction,schedule['EntryMinute'],schedule['ExitMinute'],schedule['ExitDayOffset']) in formal:raise ValueError('separate synthetic smoke schedule required')
                    r=synthetic_record(sym,direction,s['SLPips'],tp,schedule);r['CandidateID']=r['CandidateID'].replace('U10_SMOKE','U10P_SMOKE')
                    baseline=ref.regenerate(bars,r,calendar,s['Days'])
                    if baseline!=opt.regenerate(engine,r,calendar,s['Days']):raise AssertionError('P0 reference mismatch')
                    r.update(E2TradeStreamSHA256=object_hash(baseline),DiscoveryE2Metrics=summarize(baseline))
                    a=opt.evaluate_candidate(engine,r,s['Days'],calendar);b=ref.evaluate_candidate(bars,r,calendar,s['Days'])
                    if a!=b:raise AssertionError('U10P exact reference/optimized mismatch')
                    replays+=1;trades+=len(baseline)
    if replays!=16 or trades==0:raise AssertionError('bounded actual smoke inventory')
    return dict(Status='PASS',FixedScheduleReplays=replays,E2TradeCases=trades,ModeTradeCases=trades*4,Bounds=s['Bounds'],Days=s['Days'],Comparison='EXACT_P0_STREAM_IDS_HASH_METRICS_ENTRY_SLTP_MFE_MAE_REACH_GIVEBACK_TRIGGER_ACTIVATION_LOCK_HIT_CLOSE_PIPS_REASON_WTL_DD_ANNUAL_GATE_COMPARATORS_REDUCTION_ADOPTION_RANKING_FALLBACK',Formal40Used=False,FormalProtectionModeProduced=False,FormalU10PPerformanceSaved=False,Full40Run=False,ValidationUsed=False,MonitorUsed=False)
