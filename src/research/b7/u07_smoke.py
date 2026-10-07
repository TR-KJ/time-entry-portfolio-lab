"""Fixed tiny week, two symbols, no frozen 56-candidate performance."""
import pandas as pd
from .stage1_contract import Structure
from .stage1_input import load_discovery
from .u07_execution import Engine, evaluate_candidate
from .u07_reference import evaluate_candidate as reference
from .u07_input import input_config


def run_smoke(paths):
    cfg, _ = input_config()
    smoke = cfg['Smoke']
    cases = 0
    for symbol in smoke['Symbols']:
        bars = load_discovery(paths, symbol, smoke['Bounds'])
        engine = Engine(bars, symbol)
        for direction in smoke['Directions']:
            for tp in smoke['TPPips']:
                s = Structure(symbol, direction, 0, smoke['EntryMinute'], smoke['HoldingMinutes'])
                record = dict(CandidateID=s.candidate_id, Symbol=s.symbol, PairRank=1, Schedule=s.definition(),
                              FormalSL=smoke['SLPips'], FormalTP=tp, U06Status='PASS_U06',
                              SourceCandidateSHA256='synthetic', SourceCheckpointSHA256='synthetic')
                days = pd.date_range('2020-02-03', '2020-02-07')
                actual = evaluate_candidate(engine, record, days)
                expected = reference(bars, record, days)
                if actual != expected or any(len(actual[1][w]) != 1 for w in range(5)):
                    raise AssertionError('exact U07 weekday trades/metrics/selection replay')
                cases += 5
    return dict(Status='PASS',TradeCases=cases,FullCandidateReplays=8,Bounds=smoke['Bounds'],Symbols=smoke['Symbols'],
                Comparison='EXACT_TRADES_TIMES_REASONS_PIPS_METRICS_CLASSIFICATION_SETS_BEST_PLATEAU_STATUS',
                Formal56Used=False,FormalWeekdaysProduced=False,PerformanceSaved=False,FullSearch=False)
