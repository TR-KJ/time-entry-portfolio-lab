"""Fixed U07 weekdays over unchanged U06 vectorized raw-price execution."""
from dataclasses import replace
from .stage1_contract import Structure
from .u06_execution import Engine, evaluate
from .u08_calendar import VectorView
from .u08_selection import select


def evaluate_candidate(engine, record, days=None):
    s = Structure.from_id(record['CandidateID'])
    if engine.symbol != s.symbol:raise ValueError('engine symbol')
    trades = [t for w in record['FormalWeekdays']
              for t in evaluate(engine, replace(s, weekday=w), record['FormalSL'], record['FormalTP'], days)[1]]
    return select(record, VectorView(trades, record)), trades
