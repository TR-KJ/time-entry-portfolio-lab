"""Three pair-based modes and inclusive planned-interval deletion only."""
import numpy as np
import pandas as pd
from .stage4_calendar import CLOCKS
from .stage2a_engine import Replay
BANKS=dict(USD='FOMC',JPY='BOJ',EUR='ECB',GBP='BOE',AUD='RBA')
SYMBOLS=('USDJPY','EURJPY','GBPJPY','AUDJPY','AUDUSD','EURAUD','GBPAUD')
MODES=('E0','E1','E2')

def applicable_events(symbol,mode):
    if symbol not in SYMBOLS or mode not in MODES:raise ValueError('unknown pair/mode')
    if mode=='E0':return []
    events=[BANKS[symbol[:3]],BANKS[symbol[3:]]]
    if mode=='E2':events+=['US_NFP','US_CPI']+(['AUD_CPI'] if 'AUD' in symbol else [])
    return events

def windows(calendar,event):
    c=calendar['Clocks'][event];h,m=map(int,c['Time'].split(':'))
    dates=pd.DatetimeIndex(calendar['Dates'][event])+pd.Timedelta(days=c['DayOffset'],hours=h,minutes=m)
    return dates-pd.Timedelta(minutes=c['Before']),dates+pd.Timedelta(minutes=c['After'])

def matches(point,dates,mode,calendar):
    dates=pd.DatetimeIndex(dates)
    if dates.tz is not None or ((dates<pd.Timestamp('2020-01-01'))|(dates>=pd.Timestamp('2024-01-01'))).any():raise ValueError('Discovery JST dates only')
    if (dates!=dates.normalize()).any() or (dates.weekday!=point['Weekday']).any():raise ValueError('fixed entry day required')
    entry=dates+pd.Timedelta(minutes=point['AdjustedEntryMinute'])
    exit=dates+pd.Timedelta(days=point['AdjustedExitDayOffset'],minutes=point['AdjustedExitMinute'])
    if ((exit-entry)!=pd.Timedelta(minutes=point['PlannedHoldingMinutes'])).any():raise ValueError('planned schedule inconsistent')
    found=[[] for _ in dates]
    for event in applicable_events(point['Symbol'],mode):
        start,end=windows(calendar,event)
        for i,(a,b) in enumerate(zip(entry,exit)):
            if ((a<=end)&(b>=start)).any():found[i].append(event)
    return found

def filter_replay(point,replay,mode,calendar):
    matched=matches(point,replay.dates,mode,calendar);mask=np.array([bool(x) for x in matched],dtype=bool)
    status=replay.status.copy();status[mask]=-1
    # Retained execution dictionaries and raw values are shared without edits.
    rows=[[dict(Status='FILTERED_EVENT') if mask[i] else row for i,row in enumerate(group)] for group in replay.rows]
    filtered=Replay(replay.dates,status,rows,replay.raw_r.copy())
    ok=replay.status==0;events=applicable_events(point['Symbol'],mode)
    diag=dict(EventMode=mode,ApplicableEvents=events,FilteredOpportunities=int(mask.sum()),RemovedTradeCountByEvent={e:sum(bool(ok[i]) and e in aliases for i,aliases in enumerate(matched)) for e in events},OverlapOpportunityCountByEvent={e:sum(e in aliases for aliases in matched) for e in events},MultiEventOverlapOpportunities=sum(len(x)>1 for x in matched),MultiEventRemovedTrades=sum(bool(ok[i]) and len(x)>1 for i,x in enumerate(matched)),Attribution='OR removes once; event counts include each matched alias and may sum above RemovedTrades')
    return filtered,diag
