"""Exact NumPy Stage1 engine. No executable sweep on import or direct invocation."""
from collections import Counter
import numpy as np
import pandas as pd
from .execution import validate, START, END
from .stage1_contract import SL, SPREAD, PIPS, Structure
from .stage1_metrics import summarize_arrays, point_result

MINUTE = 60_000_000_000

def ns(t): return pd.Timestamp(t).value

def text_time(t): return str(pd.Timestamp(int(t)))

class Engine:
    def __init__(self, bars, symbol):
        validate(bars)
        self.symbol = symbol
        # Owned read-only arrays: no reference to the all-period parser frame.
        self.time = bars.index.asi8.copy()
        self.open = bars.Open.to_numpy(dtype=np.float64, copy=True)
        self.high = bars.High.to_numpy(dtype=np.float64, copy=True)
        self.low = bars.Low.to_numpy(dtype=np.float64, copy=True)
        for a in (self.time, self.open, self.high, self.low): a.flags.writeable = False

    def exact(self, targets):
        pos = np.searchsorted(self.time, targets)
        safe = np.minimum(pos, len(self.time)-1)
        return np.where((pos < len(self.time)) & (self.time[safe] == targets), pos, -1)

    def prepare(self, entries, direction, sls):
        return Batch(self, np.array([ns(t) for t in entries], dtype=np.int64), direction, sls)

    def prepare_job_entry(self, job, minute):
        days = pd.date_range(START, END-pd.Timedelta(days=1), freq='D')
        days = days[days.weekday == job.weekday]
        return self.prepare(days + pd.Timedelta(minutes=minute), job.direction, SL[job.symbol])

    def execute(self, direction, entry, scheduled, sl=None, fixed_key=()):
        e, x = pd.Timestamp(entry), pd.Timestamp(scheduled)
        if e.tzinfo is not None or x.tzinfo is not None: raise ValueError('naive JST')
        h = (x-e).total_seconds()/60
        if h != int(h) or not 30 <= h <= 1440: return {'Status': 'INVALID_HOLD'}
        batch = self.prepare([e], direction, [] if sl is None else [sl])
        output = batch.evaluate(int(h), fixed_key, trades=True)
        index = 0 if sl is None else 1
        if output['Trades'][index]: return output['Trades'][index][0]
        return {'Status': output['Status'][0]}

class Batch:
    """Cache first SL hit for all five levels once per entry date, across all283 holds."""
    def __init__(self, engine, entries, direction, sls):
        if direction not in ('LONG', 'SHORT'): raise ValueError('direction')
        if any(not np.isfinite(s) or s <= 0 for s in sls): raise ValueError('SL')
        self.e = engine; self.entries = entries; self.sls = list(sls)
        self.sign = 1 if direction == 'LONG' else -1
        self.pos = engine.exact(entries)
        times = pd.DatetimeIndex(entries)
        self.years = times.year.to_numpy()
        self.base = np.full(len(entries), 'OK', dtype='U24')
        self.base[(entries < ns(START)) | (entries >= ns(END))] = 'PERIOD_BOUNDARY'
        def mark(mask, label): self.base[(self.base == 'OK') & mask] = label
        mark(times.weekday >= 5, 'INVALID_ENTRY_WEEKDAY')
        mark(((times.month == 12) & (times.day >= 25)) | ((times.month == 1) & (times.day <= 3)), 'YEAR_END_STOP')
        mark(self.pos < 0, 'MISSING_ENTRY')
        self.prices = engine.open[np.maximum(self.pos, 0)] + self.sign*SPREAD[engine.symbol]*PIPS[engine.symbol]
        self.stops = self.prices[:, None] - self.sign*np.array(sls)[None, :]*PIPS[engine.symbol]
        self.hits = np.full((len(entries), len(sls)), -1, dtype=np.int64)
        for i in np.flatnonzero(self.base == 'OK'):
            end = np.searchsorted(engine.time, entries[i] + 1444*MINUTE, side='right')
            window = (engine.low if self.sign == 1 else engine.high)[self.pos[i]:end]
            for k, stop in enumerate(self.stops[i]):
                hit = np.flatnonzero(window <= stop if self.sign == 1 else window >= stop)
                if len(hit): self.hits[i, k] = self.pos[i]+int(hit[0])

    def evaluate(self, holding, fixed_key=(), trades=False):
        if holding not in range(30, 1441): raise ValueError('holding')
        e = self.e; scheduled = self.entries + holding*MINUTE
        chosen_pos = np.searchsorted(e.time, scheduled)
        safe = np.minimum(chosen_pos, len(e.time)-1)
        chosen = e.time[safe]
        status = self.base.copy()
        def mark(mask, label): status[(status == 'OK') & mask] = label
        mark(scheduled >= ns(END), 'PERIOD_BOUNDARY')
        found = (chosen_pos < len(e.time)) & (chosen <= scheduled+4*MINUTE)
        # If the five-minute exit search would cross END without finding an in-period bar,
        # reference returns PERIOD_BOUNDARY instead of MISSING_EXIT.
        mark((~found | (chosen >= ns(END))) & (scheduled+4*MINUTE >= ns(END)), 'PERIOD_BOUNDARY')
        mark(~found, 'MISSING_EXIT')
        day = pd.DatetimeIndex(chosen)
        different_day = chosen//(1440*MINUTE) != self.entries//(1440*MINUTE)
        mark((day.weekday == 6) | ((day.weekday == 0) & different_day), 'WEEKEND_BOUNDARY')
        good = np.flatnonzero(status == 'OK'); starts = self.entries[good]
        cp = safe[good]; prices = self.prices[good]
        time_pips = self.sign*(e.open[cp]-prices)/PIPS[e.symbol]
        metrics, all_trades = [], []
        for variant in range(len(self.sls)+1):
            close_pos = cp.copy(); values = time_pips.copy(); fills = e.open[cp].copy()
            reasons = np.full(len(good), 'TimeExit', dtype='U8')
            sl = None if variant == 0 else self.sls[variant-1]
            if variant:
                hits = self.hits[good, variant-1]; hit = (hits >= 0) & (hits <= cp)
                close_pos[hit] = hits[hit]; values[hit] = -float(sl)
                fills[hit] = self.stops[good[hit], variant-1]; reasons[hit] = 'SL'
            metrics.append(summarize_arrays(values, starts, e.time[close_pos], self.years[good]))
            if trades:
                records=[]
                for n, i in enumerate(good):
                    records.append(dict(Status='OK', EntryTime=text_time(starts[n]), ScheduledExitTime=text_time(scheduled[i]),
                        CloseTime=text_time(e.time[close_pos[n]]), RawEntryOpen=float(e.open[self.pos[i]]),
                        EntryPrice=float(prices[n]), ClosePrice=float(fills[n]), Pips=float(values[n]), ExitReason=str(reasons[n]),
                        SL=sl, TP=None, ExitDelayMinutes=int((chosen[i]-scheduled[i])//MINUTE),
                        MissingPathMinutes=int((chosen[i]-starts[n])//MINUTE)+1-int(cp[n]-self.pos[i]+1), FixedKey=list(fixed_key)))
                all_trades.append(records)
        return {'Metrics': metrics, 'Status': status.tolist(), 'Missing': dict(Counter(status[status != 'OK'].tolist())), 'Trades': all_trades}

def evaluate_structure(engine, structure, with_trades=False):
    if engine.symbol != structure.symbol: raise ValueError('symbol mismatch')
    batch = engine.prepare_job_entry(type('JobFields', (), {'weekday':structure.weekday, 'direction':structure.direction, 'symbol':structure.symbol})(), structure.entry)
    result = batch.evaluate(structure.holding, structure.key, with_trades)
    return record_result(structure, result), result['Trades']

def record_result(structure, result):
    pure, fixed = result['Metrics'][0], result['Metrics'][1:]
    if len(fixed) != 5: raise ValueError('official five-SL required')
    record = structure.definition()
    record.update(PureMetrics=pure, FiveSLMetrics=[dict(SLPips=s, Metrics=m) for s,m in zip(SL[structure.symbol], fixed)],
                  MissingDiagnostics=result['Missing'], **point_result(pure, fixed))
    return record

def regenerate(engine, candidate_id):
    """Return exact six variant ledgers on demand; never save every search ledger."""
    return evaluate_structure(engine, Structure.from_id(candidate_id), True)[1]
