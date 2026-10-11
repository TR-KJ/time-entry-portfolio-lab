"""U11 vectorized raw High/Low first-hit evaluator; separate from scalar reference."""
import pandas as pd
import numpy as np
from .u11_data import validate, START, END
from .stage1_contract import SPREAD, PIPS

def _execute(bars, symbol, direction, entry, scheduled, sl=None, fixed_key=(), tp=None):
    e, x = pd.Timestamp(entry), pd.Timestamp(scheduled)
    if e.tzinfo is not None or x.tzinfo is not None: raise ValueError('naive JST')
    if sl is not None and (not np.isfinite(sl) or sl <= 0): raise ValueError('SL')
    if tp is not None and (not np.isfinite(tp) or tp <= 0): raise ValueError('TP')
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
    target = None if tp is None else price+sign*tp*PIPS[symbol]
    close, fill, reason = chosen, float(bars.at[chosen, 'Open']), 'TimeExit'
    window = bars.loc[e:chosen]
    lows=window.Low.to_numpy();highs=window.High.to_numpy()
    sh=np.array([],dtype=int) if stop is None else np.flatnonzero(lows<=stop if sign==1 else highs>=stop)
    th=np.array([],dtype=int) if target is None else np.flatnonzero(highs>=target if sign==1 else lows<=target)
    si=int(sh[0]) if len(sh) else len(window);ti=int(th[0]) if len(th) else len(window)
    if si<len(window) and si<=ti:close,fill,reason=window.index[si],stop,'SL'
    elif ti<len(window):close,fill,reason=window.index[ti],target,'TP'
    pips = -float(sl) if reason == 'SL' else (float(tp) if reason == 'TP' else sign*(fill-price)/PIPS[symbol])
    return dict(Status='OK', EntryTime=str(e), ScheduledExitTime=str(x), CloseTime=str(close),
                RawEntryOpen=raw, EntryPrice=price, ClosePrice=fill, Pips=pips, ExitReason=reason,
                SL=sl, TP=tp, ExitDelayMinutes=int((chosen-x).total_seconds()/60),
                MissingPathMinutes=int((chosen-e).total_seconds()/60)+1-len(window), FixedKey=list(fixed_key))

class Engine:
    """Validate once; own a Validation copy; vectorized raw price hit detection."""
    def __init__(self,bars,symbol):
        validate(bars);self.bars=bars.copy(deep=True);self.symbol=symbol
    def execute(self,direction,entry,scheduled,sl=None,fixed_key=(),tp=None):
        return _execute(self.bars,self.symbol,direction,entry,scheduled,sl,fixed_key,tp)
