"""Prespecified two-month/six-date actual replay; never uses formal56 schedules."""
import pandas as pd
from .stage1_contract import Structure
from .stage1_input import load_discovery
from .u08_input import input_config
from .u08_execution import Engine, evaluate_candidate
from .u08_reference import evaluate_candidate as reference
from .u08_calendar import ScalarView, VectorView
from .u08_selection import month_stage


def run_smoke(paths):
    cfg, _ = input_config(); smoke = cfg['Smoke']; cases = 0
    for symbol in smoke['Symbols']:
        bars = load_discovery(paths, symbol, smoke['Bounds']); engine = Engine(bars, symbol)
        for direction in smoke['Directions']:
            for tp in smoke['TPPips']:
                s = Structure(symbol, direction, 1, smoke['EntryMinute'], smoke['HoldingMinutes'])
                r = dict(CandidateID=s.candidate_id, Symbol=s.symbol, PairRank=1, Schedule=s.definition(), FormalSL=smoke['SLPips'], FormalTP=tp,
                         AnchorWeekday=1, FormalWeekdays=smoke['FormalWeekdays'], SetName='W0', U07Status='PASS_U07',
                         U07CandidateSHA256='synthetic', U07CheckpointSHA256='synthetic', U07ProducerImplementationSHA='synthetic', U06SourceIdentity={})
                a = evaluate_candidate(engine, r, pd.DatetimeIndex(smoke['Days']))
                b = reference(bars, r, pd.DatetimeIndex(smoke['Days']))
                if a != b or len(a[1]) != 6:raise AssertionError('U08 exact price/selection replay')
                av,bv = VectorView(a[1],r),ScalarView(b[1],r)
                for bucket in ('D1','D2','D3'):
                    for month in (1,2):
                        if av.filtered([bucket],[month]) != bv.filtered([bucket],[month]) or len(av.filtered([bucket],[month])) != 1:
                            raise AssertionError('Entry calendar filter replay')
                # Tiny formal pipeline correctly stops at DOM gate. Independently
                # exercise all12 Month LOMO diagnostics on this fixed smoke stream.
                if month_stage(av,['D1','D2','D3']) != month_stage(bv,['D1','D2','D3']):raise AssertionError('Month/12 LOMO replay')
                cases += len(a[1])
    return dict(Status='PASS',TradeCases=cases,FullFixedScheduleReplays=8,Bounds=smoke['Bounds'],Days=smoke['Days'],
                DOMBuckets=['D1','D2','D3'],Months=[1,2],LOMOCasesPerReplay=12,Comparison='EXACT_TRADES_FILTERS_METRICS_DOM_MONTH_LOMO_SELECTION_STATUS',
                Formal56Used=False,PerformanceSaved=False,FullSearch=False,FormalCalendarProduced=False,
                MonthSmoke='Standalone diagnostics on tiny fixed stream; formal DOM gate is not bypassed')
