"""Independent scalar trade path; shared frozen policy and metric contract."""
from dataclasses import replace
import pandas as pd
from .execution import START, END, validate
from .stage1_contract import Structure
from .u06_reference import execute
from .u07_selection import select


def evaluate_candidate(bars, record, days=None):
    validate(bars)
    base = Structure.from_id(record['CandidateID'])
    dates = pd.date_range(START, END-pd.Timedelta(days=1), freq='D') if days is None else pd.DatetimeIndex(days)
    streams = {}
    for w in range(5):
        structure = replace(base, weekday=w)
        trades = []
        for day in dates[dates.weekday == w]:
            entry = day + pd.Timedelta(minutes=structure.entry)
            trade = execute(bars, structure.symbol, structure.direction, entry, entry+pd.Timedelta(minutes=structure.holding),
                            record['FormalSL'], structure.key, record['FormalTP'])
            if trade['Status'] == 'OK':
                trades.append(trade)
        streams[w] = trades
    return select(record, streams), streams
