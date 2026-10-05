"""Independent slow scalar executor for bounded reference replay; no B6 selections."""
import pandas as pd
import numpy as np
from .execution import validate, START, END
from .stage1_contract import SPREAD, PIPS

def execute(bars, symbol, direction, entry, scheduled, sl=None, fixed_key=()):
    validate(bars)
    e, x = pd.Timestamp(entry), pd.Timestamp(scheduled)
    if e.tzinfo is not None or x.tzinfo is not None: raise ValueError('naive JST')
    if sl is not None and (not np.isfinite(sl) or sl <= 0): raise ValueError('SL')
    if direction not in ('LONG', 'SHORT'): raise ValueError('direction')
    def skip(s): return {'Status': s}
    if not START <= e < END or not START <= x < END: return skip('PERIOD_BOUNDARY')
    h = (x-e).total_seconds()/60
    if h != int(h) or not 30 <= h <= 1440: return skip('INVALID_HOLD')
    if e.weekday() >= 5: return skip('INVALID_ENTRY_WEEKDAY')
    if (e.month == 12 and e.day >= 25) or (e.month == 1 and e.day <= 3): return skip('YEAR_END_STOP')
    if e not in bars.index: return skip('MISSING_ENTRY')
    chosen = None
    for delay in range(5):
        t = x + pd.Timedelta(minutes=delay)
        if t >= END: return skip('PERIOD_BOUNDARY')
        if t in bars.index: chosen = t; break
    if chosen is None: return skip('MISSING_EXIT')
    if chosen.weekday() == 6 or (chosen.weekday() == 0 and chosen.date() != e.date()): return skip('WEEKEND_BOUNDARY')
    sign = 1 if direction == 'LONG' else -1
    raw = float(bars.at[e, 'Open']); price = raw + sign*SPREAD[symbol]*PIPS[symbol]
    stop = None if sl is None else price-sign*sl*PIPS[symbol]
    close, fill, reason = chosen, float(bars.at[chosen, 'Open']), 'TimeExit'
    window = bars.loc[e:chosen]
    for t, row in window.iterrows():
        if stop is not None and (row.Low <= stop if sign == 1 else row.High >= stop):
            close, fill, reason = t, stop, 'SL'; break
    pips = -float(sl) if reason == 'SL' else sign*(fill-price)/PIPS[symbol]
    return dict(Status='OK', EntryTime=str(e), ScheduledExitTime=str(x), CloseTime=str(close),
                RawEntryOpen=raw, EntryPrice=price, ClosePrice=fill, Pips=pips, ExitReason=reason,
                SL=sl, TP=None, ExitDelayMinutes=int((chosen-x).total_seconds()/60),
                MissingPathMinutes=int((chosen-e).total_seconds()/60)+1-len(window), FixedKey=list(fixed_key))
