"""Weekday adapter over byte-unchanged U06 vectorized execution."""
from dataclasses import replace
from .stage1_contract import Structure
from .u06_execution import Engine, evaluate
from .u07_selection import select


def evaluate_candidate(engine, record, days=None):
    structure = Structure.from_id(record['CandidateID'])
    if engine.symbol != structure.symbol:
        raise ValueError('engine symbol')
    streams = {w: evaluate(engine, replace(structure, weekday=w), record['FormalSL'], record['FormalTP'], days)[1]
               for w in range(5)}
    return select(record, streams), streams
