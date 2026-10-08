"""Two calendar filtering paths over owned formal trade records."""
from copy import deepcopy
import pandas as pd
import numpy as np
from .execution import START, END
from .stage1_metrics import summarize
from .stage1_contract import Structure


def dom_bucket(day):
    if not 1 <= day <= 31:raise ValueError('day of month')
    return 'D1' if day <= 10 else ('D2' if day <= 20 else 'D3')


def owned_trades(trades, record):
    s = Structure.from_id(record['CandidateID'])
    if record['Schedule'] != s.definition():raise ValueError('fixed schedule')
    weekdays = record['FormalWeekdays']
    if not weekdays or weekdays != sorted(set(weekdays)) or any(type(w) is not int or w not in range(5) for w in weekdays):
        raise ValueError('formal weekdays')
    out = deepcopy(trades); entries = set()
    for t in out:
        e, c = pd.Timestamp(t['EntryTime']), pd.Timestamp(t['CloseTime'])
        if e.tzinfo is not None or c.tzinfo is not None or not START <= e <= c < END:raise ValueError('Discovery JST only')
        if t['Status'] != 'OK' or e.weekday() not in weekdays or e.hour*60+e.minute != s.entry:
            raise ValueError('formal entry')
        if e in entries:raise ValueError('duplicate trade')
        entries.add(e)
    return out


class ScalarView:
    def __init__(self, trades, record):self.trades = owned_trades(trades, record)
    def filtered(self, buckets=None, months=None):
        return [t for t in self.trades if (buckets is None or dom_bucket(pd.Timestamp(t['EntryTime']).day) in buckets)
                and (months is None or pd.Timestamp(t['EntryTime']).month in months)]
    def metrics(self, buckets=None, months=None):return summarize(self.filtered(buckets, months))


class VectorView:
    def __init__(self, trades, record):
        self.trades = owned_trades(trades, record)
        entries = pd.DatetimeIndex([t['EntryTime'] for t in self.trades])
        self.buckets = np.where(entries.day <= 10, 'D1', np.where(entries.day <= 20, 'D2', 'D3'))
        self.months = entries.month.to_numpy()
    def filtered(self, buckets=None, months=None):
        mask = np.ones(len(self.trades), dtype=bool)
        if buckets is not None:mask &= np.isin(self.buckets, buckets)
        if months is not None:mask &= np.isin(self.months, months)
        return [self.trades[i] for i in np.flatnonzero(mask)]
    def metrics(self, buckets=None, months=None):return summarize(self.filtered(buckets, months))
