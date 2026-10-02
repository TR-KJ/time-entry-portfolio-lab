"""Trade-level period aggregation, chronological DD and frozen Stage5 assessment."""
import numpy as np
import pandas as pd
from .stage1_metrics import metrics as frozen_metrics
from .stage1_search import json_safe
from .stage5_validation import assess
from .stage6_input import FIELDS
from .stage6_data import START,END
# The legacy helper's P02 result is discarded; only numeric aggregation is reused.
_UNUSED_GATE=dict(min_trades=0,min_losses=0,min_pf=0,min_annual_trades=0,min_positive_years=0)
PERIODS=('2024','2025','Combined')

def aggregate(records):
    ordered=sorted(records,key=lambda r:(r['CloseTime'],r['EntryTime'],r['CandidateID']))
    raw=np.asarray([r['RawR'] for r in ordered],dtype=float);years=np.asarray([pd.Timestamp(r['EntryTime']).year for r in ordered])
    m=frozen_metrics(raw[:,None],np.ones((len(raw),1),dtype=bool),years,_UNUSED_GATE)
    result=dict(Trades=int(m['N'][0]),Wins=int(m['Wins'][0]),Losses=int(m['Losses'][0]),ZeroR=int(m['ZeroTrades'][0]),**{k:float(m[k][0]) for k in ('PF','AvgR','TotalR','MaxDDR','WinRate')},AvgWinR=float(raw[raw>0].mean()) if (raw>0).any() else np.nan,AvgLossR=float(raw[raw<0].mean()) if (raw<0).any() else np.nan)
    return json_safe(result)

def evaluate(point,replay,event_diag):
    if len(replay.dates)!=len(replay.rows[0]) or replay.raw_r.shape!=(1,len(replay.dates)):raise ValueError('replay shape mismatch')
    if ((replay.dates<START)|(replay.dates>=END)).any():raise ValueError('outside Validation Entry dates')
    records=[]
    for i,row in enumerate(replay.rows[0]):
        if (replay.status[i]==0)!=(row['Status']=='OK'):raise ValueError('replay status mismatch')
        if row['Status']!='OK':continue
        entry=pd.Timestamp(row['EntryTime']);close=pd.Timestamp(row['CloseTime']);planned=pd.Timestamp(row['ScheduledExitTime'])
        if not START<=entry<=close<END or not START<=planned<END or entry.normalize()!=replay.dates[i]:raise ValueError('trade/period leakage or Entry-date mismatch')
        records.append(dict(row,RawR=float(replay.raw_r[0,i]),CandidateID=point['CandidateID']))
    selected={label:[r for r in records if label=='Combined' or pd.Timestamp(r['EntryTime']).year==int(label)] for label in PERIODS}
    rows=[dict(CandidateID=point['CandidateID'],Period=label,**aggregate(selected[label])) for label in PERIODS]
    a,b,combined=rows;judgment=assess(a,b,combined,point['DiscoveryMaxDDR'])
    result={k:point[k] for k in FIELDS if k!='ApplicableEvents'};result['EventMode']=point['SelectedEventMode'];result.update(judgment)
    for row in rows:
        result.update({row['Period']+'_'+k:row[k] for k in ('Trades','Wins','Losses','ZeroR','TotalR','PF','AvgR','MaxDDR')})
    diag=dict(CandidateID=point['CandidateID'],**event_diag,Trades=len(records),SLCount=sum(r['ExitReason']=='SL' for r in records),TPCount=sum(r['ExitReason']=='TP' for r in records),TimeExitCount=sum(r['ExitReason']=='TimeExit' for r in records),FallbackCount=sum(r['ExitDelayMinutes']>0 for r in records),MissingPathMinutes=sum(r['missing_path_minutes'] for r in records),MissingPathTrades=sum(r['missing_path_minutes']>0 for r in records),MissingEntryOpportunities=sum(r['Status']=='MISSING_ENTRY' for r in replay.rows[0]),MissingExitOpportunities=sum(r['Status']=='MISSING_EXIT' for r in replay.rows[0]),FilteredEventOpportunities=sum(r['Status']=='FILTERED_EVENT' for r in replay.rows[0]))
    return dict(candidate=point,periods=rows,validation=result,diagnostics=diag)
