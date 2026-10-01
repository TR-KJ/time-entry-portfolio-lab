"""One fixed datetime-based +/-5 minute grid around the original anchor."""
import pandas as pd
from .stage2a_config import STRUCTURE_KEYS
from .stage3_config import load_config

def point_key(row):return (row['EntryDeltaMinutes'],row['ExitDeltaMinutes'])

def time_grid(candidate,c=None):
    c=load_config() if c is None else c;g=c['time_grid'];valid=[];invalid=[]
    # A concrete Monday in Discovery; weekday/date arithmetic never wraps strings.
    day=pd.Timestamp('2020-02-03')+pd.Timedelta(days=candidate['Weekday'])
    entry=day+pd.Timedelta(minutes=candidate['EntryMinute']);exit=day+pd.Timedelta(days=candidate['ExitDayOffset'],minutes=candidate['ExitMinute'])
    if int((exit-entry).total_seconds()/60)!=candidate['HoldingMinutes']:raise ValueError('inconsistent Original5mAnchor')
    if any(candidate[k]%5 for k in ('EntryMinute','ExitMinute','HoldingMinutes')):raise ValueError('original five-minute anchor required')
    for e in range(g['entry_delta_min'],g['entry_delta_max']+1,g['step_minutes']):
        for x in range(g['exit_delta_min'],g['exit_delta_max']+1,g['step_minutes']):
            es=entry+pd.Timedelta(minutes=e);xs=exit+pd.Timedelta(minutes=x);hold=int((xs-es).total_seconds()/60);offset=(xs.normalize()-es.normalize()).days
            reasons=[]
            if es.normalize()!=day or es.weekday()!=candidate['Weekday']:reasons.append('ENTRY_DATE_WEEKDAY_CHANGED')
            if offset!=candidate['ExitDayOffset']:reasons.append('EXIT_DAY_OFFSET_CHANGED')
            if not g['holding_min']<=hold<=g['holding_max']:reasons.append('HOLDING_BOUNDS')
            if reasons:invalid.append(dict(CandidateID=candidate['CandidateID'],EntryDeltaMinutes=e,ExitDeltaMinutes=x,Reasons='|'.join(reasons)));continue
            row={k:candidate[k] for k in STRUCTURE_KEYS}
            row.update(AnchorEntryMinute=candidate['EntryMinute'],AnchorExitMinute=candidate['ExitMinute'],AnchorExitDayOffset=candidate['ExitDayOffset'],AnchorHoldingMinutes=candidate['HoldingMinutes'],EntryDeltaMinutes=e,ExitDeltaMinutes=x,AdjustedEntryMinute=es.hour*60+es.minute,AdjustedExitMinute=xs.hour*60+xs.minute,AdjustedExitDayOffset=offset,PlannedHoldingMinutes=hold,AnchorDistance=abs(e)+abs(x),SL=candidate['SL'],TP=candidate['TP'],TPMode='TP_NONE' if candidate['TP'] is None else 'FINITE')
            valid.append(row)
    if len(valid)+len(invalid)!=121 or len({point_key(p) for p in valid})!=len(valid):raise ValueError('invalid fixed grid')
    return valid,invalid

def execution_candidate(point):
    a={k:point[k] for k in STRUCTURE_KEYS};a.update(EntryMinute=point['AdjustedEntryMinute'],ExitMinute=point['AdjustedExitMinute'],ExitDayOffset=point['AdjustedExitDayOffset'],HoldingMinutes=point['PlannedHoldingMinutes']);return a

def fixed_setting(point):
    sl,tp=point['SL'],point['TP']
    return dict(SL=sl,TP=tp,TPMode=point['TPMode'],TPRatio=None if tp is None else tp/sl,ActualTPRatio=None if tp is None else tp/sl,RatioAliases=[])
