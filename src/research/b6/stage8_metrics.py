"""Trade/opportunity evidence and period diagnostics; no selection or ranking."""
import numpy as np
import pandas as pd
from .stage8_data import START,END,PERIODS
from .stage6_metrics import aggregate

LEDGER_FIELDS=('CandidateID','Symbol','WeekKey','PlannedEntry','ActualEntry','PlannedExit','ActualClose','ExitReason','R','Pips','Period','FallbackMinutes','MissingPathMinutes')
DIAGNOSTIC_FIELDS=('CandidateID','Symbol','WeekKey','PlannedEntry','PlannedExit','Period','Status','Reason','FallbackMinutes','MissingPathMinutes')

def period_for(entry):
    t=pd.Timestamp(entry)
    if t.tz is not None or not START<=t<END:raise ValueError('outside FullAvailable planned Entry')
    return next(name for name,(a,b) in PERIODS.items() if name!='FullAvailable' and a<=t<b)

def evaluate(point,replay,event_diag):
    if len(replay.rows)!=1 or len(replay.dates)!=len(replay.rows[0]) or replay.raw_r.shape!=(1,len(replay.dates)):raise ValueError('replay shape mismatch')
    ledger=[];diagnostics=[]
    for i,(date,row) in enumerate(zip(replay.dates,replay.rows[0])):
        date=pd.Timestamp(date)
        if date.tz is not None or date!=date.normalize() or date.weekday()!=point['Weekday']:raise ValueError('planned Entry date mismatch')
        entry=date+pd.Timedelta(minutes=point['AdjustedEntryMinute']);exit_time=entry+pd.Timedelta(minutes=point['PlannedHoldingMinutes'])
        week=entry.strftime('%Y-%m-%d');period=period_for(entry);ok=row['Status']=='OK'
        if (replay.status[i]==0)!=ok:raise ValueError('replay status mismatch')
        common=dict(CandidateID=point['CandidateID'],Symbol=point['Symbol'],WeekKey=week,PlannedEntry=str(entry),PlannedExit=str(exit_time),Period=period,FallbackMinutes=int(row.get('ExitDelayMinutes',0)),MissingPathMinutes=int(row.get('missing_path_minutes',0)))
        diagnostics.append(dict(common,Status='TRADE' if ok else 'NO_TRADE',Reason=row['Status']))
        if not ok:continue
        actual=pd.Timestamp(row['EntryTime']);close=pd.Timestamp(row['CloseTime'])
        if actual!=entry or pd.Timestamp(row['ScheduledExitTime'])!=exit_time or not START<=entry<=close<END or not START<=exit_time<END:raise ValueError('trade timing/period mismatch')
        raw=float(replay.raw_r[0,i])
        if not np.isfinite(raw):raise ValueError('finite raw R required')
        ledger.append(dict(common,ActualEntry=str(actual),ActualClose=str(close),ExitReason=row['ExitReason'],R=raw,Pips=raw*point['SL']))
    validate_ledger(ledger)
    return dict(candidate=point,ledger=ledger,diagnostics=diagnostics,event_diagnostics=event_diag)

def validate_ledger(records):
    seen=set()
    for r in records:
        key=(r['CandidateID'],r['WeekKey'])
        if key in seen:raise ValueError('duplicate candidate WeekKey')
        seen.add(key);entry=pd.Timestamp(r['PlannedEntry']);actual=pd.Timestamp(r['ActualEntry']);close=pd.Timestamp(r['ActualClose']);exit_time=pd.Timestamp(r['PlannedExit'])
        if any(t.tz is not None for t in (entry,actual,close,exit_time)):raise ValueError('naive JST ledger required')
        if r['WeekKey']!=entry.strftime('%Y-%m-%d') or r['Period']!=period_for(entry) or actual!=entry or not START<=entry<=close<END or not entry<exit_time<END:raise ValueError('ledger temporal identity mismatch')
        if not np.isfinite(float(r['R'])) or not np.isfinite(float(r['Pips'])) or r['FallbackMinutes'] not in range(5) or r['MissingPathMinutes']<0:raise ValueError('invalid ledger values')

def period_records(records,label):
    if label not in PERIODS:raise ValueError('unknown period')
    a,b=PERIODS[label]
    return [r for r in records if a<=pd.Timestamp(r['PlannedEntry'])<b]

def candidate_periods(points,records):
    validate_ledger(records);ids={p['CandidateID'] for p in points}
    if any(r['CandidateID'] not in ids for r in records):raise ValueError('unknown ledger candidate')
    result=[]
    for p in points:
        own=[r for r in records if r['CandidateID']==p['CandidateID']]
        for label in PERIODS:
            rows=[dict(CandidateID=r['CandidateID'],EntryTime=r['ActualEntry'],CloseTime=r['ActualClose'],RawR=r['R']) for r in period_records(own,label)]
            result.append(dict(CandidateID=p['CandidateID'],Period=label,**aggregate(rows)))
    return result
