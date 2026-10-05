"""Prespecified bounded compatibility replay only; emits no candidate performance."""
import time
import pandas as pd
from .stage1_contract import SYMBOLS, SL, Structure
from .stage1_input import load_discovery
from .stage1 import Engine
from .stage1_reference import execute
from .stage1_metrics import summarize, gate

BOUNDS=('2020-02-04 09:00','2020-02-04 09:35')

def run_smoke(paths):
    started=time.perf_counter();cases=[]
    for symbol in SYMBOLS:
        bars=load_discovery(paths,symbol,BOUNDS);engine=Engine(bars,symbol)
        for direction in ('LONG','SHORT'):
            s=Structure(symbol,direction,1,540,30)
            for sl in [None]+SL[symbol]:
                a=engine.execute(direction,BOUNDS[0],'2020-02-04 09:30',sl,s.key)
                b=execute(bars,symbol,direction,BOUNDS[0],'2020-02-04 09:30',sl,s.key)
                if a!=b or a['Status']!='OK':raise AssertionError('bounded optimized/reference mismatch')
                am,bm=summarize([a]),summarize([b])
                if am!=bm or gate(am,sl is not None)!=gate(bm,sl is not None):raise AssertionError('bounded metric mismatch')
                cases.append(dict(Symbol=symbol,Direction=direction,Variant='PURE' if sl is None else 'SL'+str(sl),ExactReplay='PASS'))
    return dict(Status='PASS',Anchor='2020-02-04 09:00 JST',HoldingMinutes=30,Cases=cases,CaseCount=len(cases),
                Compared=['TradeCount','EntryTime','CloseTime','Pips','ExitReason','AllTradeFields','Metrics','Gate'],
                Comparison='EXACT; no numeric tolerance',ElapsedSeconds=time.perf_counter()-started,
                CandidatePerformanceSaved=False,Ranking=False,FullSweep=False)
