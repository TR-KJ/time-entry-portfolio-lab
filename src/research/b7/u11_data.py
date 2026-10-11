"""Exact-file integrity plus owned Validation-only arrays; no Discovery loader."""
from pathlib import Path
import numpy as np
import pandas as pd
from .stage1_input import manifest_rows,read_mt5,audit_inputs,resolve_exact
from .stage1_contract import digest,SYMBOLS
START=pd.Timestamp('2024-01-01');END=pd.Timestamp('2026-01-01')

def validate(bars):
    if not isinstance(bars.index,pd.DatetimeIndex) or bars.index.tz is not None:raise ValueError('naive JST required')
    if bars.empty or not bars.index.is_unique or not bars.index.is_monotonic_increasing:raise ValueError('empty/duplicate/unsorted Validation bars')
    if bars.index[0]<START or bars.index[-1]>=END:raise ValueError('outside Validation period')
    a=bars[['Open','High','Low','Close']]
    if not np.isfinite(a.to_numpy()).all():raise ValueError('nonfinite OHLC')
    if (a.High<a[['Open','Low','Close']].max(axis=1)).any() or (a.Low>a[['Open','High','Close']].min(axis=1)).any():raise ValueError('OHLC validity')

def load_validation(paths,symbol,bounds=None):
    if symbol not in SYMBOLS:raise ValueError('symbol')
    rows=manifest_rows()
    if set(paths)!={r['Filename'] for r in rows}:raise ValueError('exact72 mapping')
    lo,hi=(START,END) if bounds is None else tuple(pd.Timestamp(t) for t in bounds)
    if lo.tzinfo is not None or hi.tzinfo is not None or not START<=lo<hi<=END:raise ValueError('Validation bounds')
    frames=[]
    for r in rows:
        if r['Symbol']!=symbol:continue
        if pd.Timestamp(r['LastRaw'])<lo-pd.Timedelta(days=1) or pd.Timestamp(r['FirstRaw'])>=hi:continue
        p=Path(paths[r['Filename']])
        if p.name!=r['Filename'] or digest(p)!=r['SHA256']:raise ValueError('frozen file identity')
        full=read_mt5(p)
        a=full[['Open','High','Low','Close']]
        if (a.High<a[['Open','Low','Close']].max(axis=1)).any() or (a.Low>a[['Open','High','Close']].min(axis=1)).any():raise ValueError('raw OHLC validity')
        frame=full.loc[(full.index>=lo)&(full.index<hi),['Open','High','Low','Close']].copy(deep=True)
        del a,full
        if len(frame):frames.append(frame)
        if digest(p)!=r['SHA256']:raise ValueError('source mutated during load')
    if not frames:raise ValueError('no Validation input')
    bars=pd.concat(frames).sort_index().copy(deep=True);del frames
    validate(bars)
    if bars.index[0]<lo or bars.index[-1]>=hi:raise ValueError('smoke bound escape')
    return bars
