"""Stage0 isolation only. No candidate executor or sweep API."""
import pandas as pd
import numpy as np
START=pd.Timestamp("2020-01-01"); END=pd.Timestamp("2024-01-01")
PIPS={s:(.01 if s.endswith("JPY") else .0001) for s in ("USDJPY","EURJPY","GBPJPY","AUDJPY","AUDUSD","EURAUD","GBPAUD","EURUSD","GBPUSD")}

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
