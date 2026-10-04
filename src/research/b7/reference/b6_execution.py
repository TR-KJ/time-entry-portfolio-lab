"""Discovery-only minimal historical execution, no optimization runner."""
from __future__ import annotations
import pandas as pd
import numpy as np
START=pd.Timestamp('2020-01-01'); END=pd.Timestamp('2024-01-01')
PIPS={s:(.01 if s.endswith('JPY') else .0001) for s in ('USDJPY','EURJPY','GBPJPY','AUDJPY','AUDUSD','EURAUD','GBPAUD')}
SPREAD=dict(zip(PIPS,(.5,1,2,1.5,1.5,1.5,2)))

def discovery_view(bars):
    """Only this copy crosses audit -> research boundary; no parent/full array retained."""
    return bars.loc[(bars.index>=START)&(bars.index<END),['Open','High','Low','Close']].copy()

def validate(bars):
    if not isinstance(bars.index,pd.DatetimeIndex) or bars.index.tz is not None: raise ValueError('naive JST required')
    if not bars.index.is_unique or not bars.index.is_monotonic_increasing: raise ValueError('duplicate/unsorted timestamps')
    if bars.empty: raise ValueError('empty Discovery input')
    if bars.index.min()<START or bars.index.max()>=END: raise ValueError('outside Discovery input')
    a=bars[['Open','High','Low','Close']]
    if not np.isfinite(a.to_numpy()).all(): raise ValueError('nonfinite OHLC')
    if (a.High<a[['Open','Low','Close']].max(axis=1)).any() or (a.Low>a[['Open','High','Close']].min(axis=1)).any(): raise ValueError('invalid OHLC')

def execute(bars, symbol, long, entry, scheduled, sl, tp=None):
    validate(bars)
    entry=pd.Timestamp(entry); scheduled=pd.Timestamp(scheduled)
    if entry.tzinfo is not None or scheduled.tzinfo is not None: raise ValueError('naive JST schedule required')
    if not np.isfinite(sl) or sl<=0 or (tp is not None and (not np.isfinite(tp) or tp<=0)): raise ValueError('invalid SL/TP')
    def skip(reason): return dict(Status=reason)
    if not START<=entry<END or not START<=scheduled<END: return skip('PERIOD_BOUNDARY')
    duration=(scheduled-entry).total_seconds()/60
    if duration<30 or duration>1440 or duration!=int(duration): return skip('INVALID_HOLD')
    if entry.weekday()>=5: return skip('INVALID_ENTRY_WEEKDAY')
    if entry not in bars.index: return skip('MISSING_ENTRY')
    chosen=None
    for k in range(5):
        t=scheduled+pd.Timedelta(minutes=k)
        if t>=END: return skip('PERIOD_BOUNDARY')
        if t in bars.index:
            chosen=t; break
    if chosen is None: return skip('MISSING_EXIT')
    # No time compression/reconnection across a weekend; <=24h already rules out Friday->Monday.
    if chosen.weekday()==6 or (chosen.weekday()==0 and chosen.date()!=entry.date()): return skip('WEEKEND_BOUNDARY')
    sign=1 if long else -1; pip=PIPS[symbol]
    raw=float(bars.at[entry,'Open']); price=raw+sign*SPREAD[symbol]*pip
    stop=price-sign*sl*pip; target=None if tp is None else price+sign*tp*pip
    window=bars.loc[entry:chosen]
    close=chosen; fill=float(bars.at[chosen,'Open']); reason='TimeExit'; pips=None
    for t,row in window.iterrows():
        if (row.Low<=stop if long else row.High>=stop):
            close=t;fill=stop;reason='SL';pips=-sl;break
        if target is not None and (row.High>=target if long else row.Low<=target):
            close=t;fill=target;reason='TP';pips=tp;break
    if pips is None:pips=sign*(fill-price)/pip
    return dict(Status='OK',EntryTime=str(entry),ScheduledExitTime=str(scheduled),CloseTime=str(close),
                RawEntryOpen=raw,EntryPrice=price,ClosePrice=fill,SL=float(sl),TP=tp,
                Pips=round(float(pips),6),R=round(float(pips/sl),9),ExitReason=reason,
                ExitDelayMinutes=int((chosen-scheduled).total_seconds()/60),
                missing_path_minutes=int((chosen-entry).total_seconds()/60)+1-len(window),
                exit_bar_first_hit=bool(close==chosen and reason!='TimeExit'))
