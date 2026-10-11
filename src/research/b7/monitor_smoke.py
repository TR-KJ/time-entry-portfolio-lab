"""Synthetic-only Monitor reference smoke. Never reads actual M1 or formal records."""
import pandas as pd
import numpy as np
from copy import deepcopy
from .monitor_engine import Engine
from .monitor_execution import evaluate_candidate
from . import monitor_reference as reference
from .monitor_metrics import metric_block
from .u10_calendar import event_set
from .candidate_freeze import exact

def synthetic_record(symbol='EURJPY',direction='LONG',mode='P0',entry=547,exit=1387,offset=0,tp=None):
    empty=metric_block([])
    return dict(CandidateID=f'B7_MONITOR_SMOKE:{symbol}:{direction}:{mode}:{entry}:{offset}:{exit}:{tp}',Symbol=symbol,Direction=direction,PairRank=0,FormalEntryMinute=entry,FormalExitMinute=exit,FormalExitDayOffset=offset,FormalHoldingMinutes=offset*1440+exit-entry,FormalWeekdays=[0,1,2,3,4],FormalDOMBuckets=['D1','D2','D3'],FormalMonths=list(range(1,13)),FormalSL=10,FormalTP=tp,FormalProtectionMode=mode,FormalEventMode='E2',E2EventSet=event_set(symbol,'E2'),SelectedModeDiscoveryMetrics=deepcopy(empty),ValidationMetrics=dict(Combined=deepcopy(empty),Annual2024=deepcopy(empty),Annual2025=deepcopy(empty),Monthly={f'{y}-{m:02d}':deepcopy(empty) for y in (2024,2025) for m in range(1,13)}),Synthetic=True)

def bars(start='2026-02-03 09:00',n=36):
    return pd.DataFrame({k:np.full(n,100.) for k in ('Open','High','Low','Close')},index=pd.date_range(start,periods=n,freq='min'))

def run_smoke():
    """All fixtures generated here; no path argument or actual-price input accepted."""
    count=0
    for start,n in [('2026-01-01 09:00',36),('2026-01-02 09:00',36),('2026-01-03 09:00',36),('2026-02-03 09:00',36),('2026-02-03 23:45',36),('2026-09-09 23:30',30)]:
        base=bars(start,n);e=base.index[0];x=e+pd.Timedelta(minutes=30)
        for delay in range(6):
            b=base.drop(base.index[30:30+delay])
            pristine=b.copy()
            for direction in ('LONG','SHORT'):
                for hit in ('NONE','SL','TP','BOTH','GAP'):
                    b=pristine.copy()
                    if hit in ('SL','BOTH'):b.iloc[0,b.columns.get_loc('Low')]=99.
                    if hit in ('TP','BOTH'):b.iloc[0,b.columns.get_loc('High')]=101.
                    if hit=='GAP':b=b.drop(b.index[5:10])
                    a=Engine(b,'USDJPY').execute(direction,e,x,20,(),20)
                    z=reference.execute(b,'USDJPY',direction,e,x,20,(),20)
                    if not exact(a,z):raise AssertionError('synthetic raw execution parity')
                    count+=1
    selected=0
    for direction in ('LONG','SHORT'):
        for mode in ('P0','P1','P2','P3'):
            for events in ([],[dict(CanonicalEventName=n,SourceDates=['2026-02-03'],FixedJST='09:30',WindowPlusMinusMinutes=0) for n in ('US_NFP','US_CPI')]):
                r=synthetic_record('USDJPY',direction,mode,540,570);b=bars()
                # Trigger followed by a missing bar: activation is next existing minute.
                b.iloc[0,b.columns.get_loc('High')]=100.08;b.iloc[0,b.columns.get_loc('Low')]=99.92
                b=b.drop(b.index[1:3]);c={'Events':events}
                a,ad=evaluate_candidate(Engine(b,'USDJPY'),r,c,['2026-02-03'],implementation_sha='0'*40)
                z,zd=reference.evaluate_candidate(b,r,c,['2026-02-03'],implementation_sha='0'*40)
                if not exact(a,z) or not exact(ad,zd):raise AssertionError('synthetic selected pipeline parity')
                if a['Status']!='OBSERVED_ONLY' or a['ValidationOverrideAllowed'] is not False:raise AssertionError('observed-only')
                selected+=1
    for values,state in [([], 'UNDEFINED'),([0.], 'UNDEFINED'),([1.], 'INF'),([-1.], 'FINITE'),([-3.,5.,-10.],'FINITE')]:
        a=metric_block(values)
        if a!=reference.metric_block(values) or a['PFState']!=state:raise AssertionError('synthetic metrics parity')
    # Explicit period/weekend and attribution invariants, separate from parity.
    from .monitor_data import validate
    from .monitor_metrics import summarize
    validate(bars('2026-01-01 00:00',1));validate(bars('2026-09-09 23:59',1))
    try:validate(bars('2026-09-10 00:00',1))
    except ValueError:pass
    else:raise AssertionError('end exclusive')
    b=bars('2026-02-06 23:59',1443);b=b.drop(b.index[1440])
    if Engine(b,'USDJPY').execute('LONG',b.index[0],'2026-02-07 23:59')['Status']!='WEEKEND_BOUNDARY':raise AssertionError('weekend reconnect')
    ts=[dict(Pips=p,EntryTime=e,CloseTime=e,FixedKey=[i]) for i,(p,e) in enumerate([(-3.,'2026-01-05 09:00:00'),(5.,'2026-02-03 09:00:00'),(-10.,'2026-09-09 09:00:00')])]
    m=summarize(ts[::-1])
    if m!=reference.summarize(ts) or m['Annual2026']!=m['Combined'] or len(m['Monthly'])!=9 or m['Combined']['MaxDDPips']!=10:raise AssertionError('monthly/annual/order/DD')
    return dict(Status='PASS',RawExecutionComparisons=count,SelectedPipelineComparisons=selected,Formal22Used=False,ActualMonitorRowsUsed=False,FormalMonitorPerformanceSaved=False,Full22Run=False,ValidationStatusChanged=False,Synthetic2026Only=True,PerformanceValuesPublished=False)
