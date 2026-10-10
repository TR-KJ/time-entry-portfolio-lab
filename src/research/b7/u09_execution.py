"""One execution per valid point; unchanged U06 optimized price kernel."""
import pandas as pd
import numpy as np
from .execution import START,END
from .u06_execution import Engine
from .stage1_metrics import summarize
from .u09_schedule import grid
from .u09_selection import point,assemble

def calendar_days(record,days=None):
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D') if days is None else pd.DatetimeIndex(days)
    if dates.tz is not None or dates.has_duplicates or any((dates<START)|(dates>=END)) or any(dates!=dates.normalize()):raise ValueError('unique Discovery JST dates')
    dates=dates.sort_values();buckets=np.where(dates.day<=10,'D1',np.where(dates.day<=20,'D2','D3'))
    return dates[np.isin(dates.weekday,record['FormalWeekdays']) & np.isin(buckets,record['FormalDOMBuckets']) & np.isin(dates.month,record['FormalMonths'])]

def evaluate_point(engine,record,p,dates):
    trades=[]
    for d in dates:
        e=d+pd.Timedelta(minutes=p['EntryMinute']);x=d+pd.Timedelta(days=p['ExitDayOffset'],minutes=p['ExitMinute'])
        key=list(p['FixedKey']);key[2]=d.weekday()
        t=engine.execute(record['Schedule']['Direction'],e,x,record['FormalSL'],key,record['FormalTP'])
        if t['Status']=='OK':trades.append(t)
    return summarize(trades),trades

def evaluate_candidate(engine,record,days=None):return evaluate_points(engine,record,grid(record),days)

def evaluate_points(engine,record,schedules,days=None):
    """Bounded test/smoke entry; formal runner always uses the full fixed grid."""
    if engine.symbol!=record['Symbol']:raise ValueError('engine symbol')
    dates=calendar_days(record,days);points=[];logs={};seen=set()
    for p in schedules:
        if p['PointID'] in seen:raise ValueError('duplicate point evaluation')
        seen.add(p['PointID'])
        if p['Valid']:m,t=evaluate_point(engine,record,p,dates);logs[p['PointID']]=t
        else:m=None
        points.append(point(p,m))
    return assemble(record,points),logs
