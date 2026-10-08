"""Independent scalar price execution and Entry-JST calendar filtering."""
from dataclasses import replace
import pandas as pd
from .execution import START, END, validate
from .stage1_contract import Structure
from .u06_reference import execute
from .u08_calendar import ScalarView
from .u08_selection import select


def evaluate_candidate(bars, record, days=None):
    validate(bars); base = Structure.from_id(record['CandidateID'])
    dates = pd.date_range(START, END-pd.Timedelta(days=1), freq='D') if days is None else pd.DatetimeIndex(days)
    trades = []
    for w in record['FormalWeekdays']:
        s = replace(base, weekday=w)
        for day in dates[dates.weekday == w]:
            e = day+pd.Timedelta(minutes=s.entry)
            t = execute(bars, s.symbol, s.direction, e, e+pd.Timedelta(minutes=s.holding), record['FormalSL'], s.key, record['FormalTP'])
            if t['Status'] == 'OK':trades.append(t)
    return select(record, ScalarView(trades, record)), trades
