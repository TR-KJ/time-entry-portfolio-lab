"""Observation only: raw chronological R, no Monitor selection or thresholds."""
import numpy as np
import pandas as pd
from .stage6_metrics import aggregate
from .stage7_data import START,END

METRICS=('Trades','Wins','Losses','ZeroR','PF','AvgR','TotalR','MaxDDR','WinRate','AvgWinR','AvgLossR')
def fixed_columns(p):
    if p.get('FormalValidationStatus')!='PASS':raise ValueError('only formal PASS inputs')
    return dict(**{k:p[k] for k in ('CandidateID','Symbol','Direction','Weekday','SL','TP')},Entry=p['FinalEntryJST'],Exit=p['FinalExitJST'],ExitDayOffset=p['FinalExitDayOffset'],HoldingMinutes=p['FinalHoldingMinutes'],EventMode=p['SelectedEventMode'],FormalValidationStatus=p['FormalValidationStatus'],**{'ValidationCombined'+k:p['ValidationProvenance']['Combined_'+k] for k in ('PF','AvgR','TotalR','MaxDDR')},MonitorState='OBSERVED')

def evaluate(point,replay,event_diag,coverage):
    if len(replay.dates)!=len(replay.rows[0]) or replay.raw_r.shape!=(1,len(replay.dates)):raise ValueError('replay shape mismatch')
    if ((replay.dates<START)|(replay.dates>=END)).any():raise ValueError('outside Monitor Entry dates')
    records=[]
    for i,row in enumerate(replay.rows[0]):
        if (replay.status[i]==0)!=(row['Status']=='OK'):raise ValueError('replay status mismatch')
        if row['Status']!='OK':continue
        entry=pd.Timestamp(row['EntryTime']);close=pd.Timestamp(row['CloseTime']);planned=pd.Timestamp(row['ScheduledExitTime'])
        if not START<=entry<=close<END or not START<=planned<END or entry.normalize()!=replay.dates[i]:raise ValueError('trade/period leakage')
        raw=float(replay.raw_r[0,i])
        if not np.isfinite(raw):raise ValueError('finite raw R required')
        records.append(dict(row,RawR=raw,CandidateID=point['CandidateID']))
    result=dict(fixed_columns(point),**{'Monitor'+k:v for k,v in aggregate(records).items()})
    diag=dict(CandidateID=point['CandidateID'],**event_diag,PlannedOpportunities=len(replay.dates),Trades=len(records),SLCount=sum(r['ExitReason']=='SL' for r in records),TPCount=sum(r['ExitReason']=='TP' for r in records),TimeExitCount=sum(r['ExitReason']=='TimeExit' for r in records),FallbackCount=sum(r['ExitDelayMinutes']>0 for r in records),MissingPathMinutes=sum(r['missing_path_minutes'] for r in records),MissingPathTrades=sum(r['missing_path_minutes']>0 for r in records),MissingEntryOpportunities=sum(r['Status']=='MISSING_ENTRY' for r in replay.rows[0]),MissingExitOpportunities=sum(r['Status']=='MISSING_EXIT' for r in replay.rows[0]),FilteredEventOpportunities=sum(r['Status']=='FILTERED_EVENT' for r in replay.rows[0]),ActualDataFirstJST=coverage['FirstAvailableJST'],ActualDataLastJST=coverage['LastAvailableJST'])
    return dict(candidate=point,monitor=result,diagnostics=diag)
