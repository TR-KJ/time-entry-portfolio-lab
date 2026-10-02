"""Canonical Validation-only data boundary; source audit never returns full data."""
import numpy as np
import pandas as pd
from .stage1_data import audit_inputs
from .stage0 import reference
START=pd.Timestamp('2024-01-01');END=pd.Timestamp('2026-01-01')

def validate_prices(bars):
    if not isinstance(bars.index,pd.DatetimeIndex) or bars.index.tz is not None or not bars.index.is_unique or not bars.index.is_monotonic_increasing:raise ValueError('unique sorted naive JST prices required')
    if bars.empty or bars.index.min()<START or bars.index.max()>=END:raise ValueError('outside Validation price interval')
    if (bars.index.as_unit('ns').asi8%60_000_000_000).any():raise ValueError('exact M1 alignment required')
    a=bars[['Open','High','Low','Close']]
    if not np.isfinite(a.to_numpy()).all() or (a.High<a[['Open','Low','Close']].max(axis=1)).any() or (a.Low>a[['Open','High','Close']].min(axis=1)).any():raise ValueError('invalid Validation OHLC')

def canonical_slice(frames):
    full=pd.concat(frames,ignore_index=True)
    raw=full.RawDatetime.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward')
    full.index=pd.DatetimeIndex(raw.dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
    if full.index.duplicated().any():raise ValueError('duplicate canonical JST')
    a=full[['Open','High','Low','Close']]
    if not np.isfinite(a.to_numpy()).all() or (a.High<a[['Open','Low','Close']].max(axis=1)).any() or (a.Low>a[['Open','High','Close']].min(axis=1)).any():raise ValueError('source OHLC integrity failed')
    result=full.loc[(full.index>=START)&(full.index<END),['Open','High','Low','Close']].sort_index().copy()
    validate_prices(result);return result

def load_validation(symbol,manifest,paths):
    ref=reference();frames=[]
    for row in manifest[manifest.Symbol==symbol].itertuples():
        if pd.Timestamp(row.LastRaw)<START-pd.Timedelta(days=1) or pd.Timestamp(row.FirstRaw)>=END+pd.Timedelta(days=1):continue
        frames.append(ref.read_mt5_file(paths[row.Filename]))
    if not frames:raise ValueError('Validation inputs unavailable')
    return canonical_slice(frames)

def availability(bars,symbol):
    validate_prices(bars)
    return dict(Symbol=symbol,Rows=len(bars),FirstJST=str(bars.index.min()),LastJST=str(bars.index.max()),Rows2024=int((bars.index.year==2024).sum()),Rows2025=int((bars.index.year==2025).sum()),OutsidePeriodRows=0,Status='PASS',CandidatePerformanceCalculated=False)
