"""Pinned source arrays and fixed JST windows. No network or legacy resolver."""
from datetime import date
import pandas as pd
import numpy as np
from .stage1_contract import PIPS,object_hash,digest
from .u10_input import CALENDAR,CALENDAR_SHA,CALENDAR_COMMIT,SOURCE_PATH,SOURCE_BLOB,SOURCE_SHA
from .u06_finalize_only import read
EVENTS=('AUD_CPI','BOE','BOJ','ECB','FOMC','RBA','US_CPI','US_NFP')
BANK={'USD':'FOMC','JPY':'BOJ','EUR':'ECB','GBP':'BOE','AUD':'RBA'}
FIXED={'FOMC':('03:00',180),'US_NFP':('21:30',120),'US_CPI':('21:30',120),'BOJ':('12:00',180),'BOE':('21:00',120),'ECB':('21:15',120),'RBA':('13:30',120),'AUD_CPI':('10:30',120)}

def audit_calendar():
    if digest(CALENDAR)!=CALENDAR_SHA:raise ValueError('calendar SHA')
    c=read(CALENDAR)
    if (c['CalendarSourceCommit'],c['SourcePath'],c['SourceBlobSHA'],c['SourceSHA256'])!=(CALENDAR_COMMIT,SOURCE_PATH,SOURCE_BLOB,SOURCE_SHA):raise ValueError('source identity')
    if c['SchemaVersion']!=1 or c['DSTAdjustment'] or c['HistoricalReleaseTimeReconstruction']:raise ValueError('fixed JST schema')
    if [e['CanonicalEventName'] for e in c['Events']]!=list(EVENTS):raise ValueError('eight canonical events')
    for e in c['Events']:
        n=e['CanonicalEventName'];ds=e['SourceDates']
        if e['SourceArray']!=n+'_DATES' or ds!=sorted(set(ds)) or any(date.fromisoformat(d).isoformat()!=d for d in ds):raise ValueError('source dates')
        if e['ExtractedArraySHA256']!=object_hash(ds) or e['TotalSourceDates']!=len(ds):raise ValueError('array identity')
        if (e['FixedJST'],e['WindowPlusMinusMinutes'])!=FIXED[n] or e['SameDay']!=(n!='FOMC'):raise ValueError('fixed time/window/date')
        if e['DiscoveryDates']!=sum('2020-01-01'<=d<'2024-01-01' for d in ds):raise ValueError('Discovery calendar count')
        if n=='AUD_CPI' and (len(ds)!=48 or e['DiscoveryDates']!=16):raise ValueError('U10-S01')
    return c

def event_set(symbol,mode):
    if symbol not in PIPS or len(symbol)!=6 or mode not in ('E0','E1','E2'):raise ValueError('known nine pairs/mode')
    if mode=='E0':return []
    names={BANK[symbol[:3]],BANK[symbol[3:]]}
    if mode=='E2':
        names.update(('US_NFP','US_CPI'))
        if 'AUD' in (symbol[:3],symbol[3:]):names.add('AUD_CPI')
    return sorted(names)

def windows(calendar):
    out=[]
    for e in calendar['Events']:
        for d in e['SourceDates']:
            t=pd.Timestamp(d+' '+e['FixedJST'])+pd.Timedelta(days=int(e['CanonicalEventName']=='FOMC'));w=pd.Timedelta(minutes=e['WindowPlusMinusMinutes'])
            out.append(dict(Event=e['CanonicalEventName'],SourceDate=d,EventTimestampJST=str(t),Start=str(t-w),End=str(t+w)))
    return sorted(out,key=lambda w:(w['Start'],w['End'],w['Event'],w['SourceDate']))

class EventIndex:
    def __init__(self,calendar):
        self.windows=windows(calendar);self.arrays={}
        for name in EVENTS:
            ws=[w for w in self.windows if w['Event']==name]
            self.arrays[name]=(np.array([np.datetime64(w['Start']) for w in ws],dtype='datetime64[ns]'),np.array([np.datetime64(w['End']) for w in ws],dtype='datetime64[ns]'))
    def matching(self,entry,exit,names):
        e,x=np.datetime64(entry),np.datetime64(exit);found=[]
        for n in names:
            starts,ends=self.arrays[n];stop=np.searchsorted(starts,x,side='right')
            if np.any(ends[:stop]>=e):found.append(n)
        return sorted(set(found))
