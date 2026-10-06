"""Fixed one-day compatibility smoke, unrelated to the formal 72 schedules."""
import pandas as pd
from .stage1_contract import SYMBOLS,Structure
from .stage1_input import load_discovery
from .u06_execution import Engine,evaluate
from .u06_reference import execute
from .stage1_metrics import summarize,gate
from .u06_selection import zones,winner
BOUNDS=('2020-02-04 09:00','2020-02-04 09:35')

def run_smoke(paths):
    count=0
    for symbol in SYMBOLS:
        bars=load_discovery(paths,symbol,BOUNDS);engine=Engine(bars,symbol)
        for direction in ('LONG','SHORT'):
            s=Structure(symbol,direction,1,540,30);am={};bm={}
            for sl in (10,15,20):
                for tp in (None,5,15,25):
                    a=engine.execute(direction,BOUNDS[0],'2020-02-04 09:30',sl,s.key,tp)
                    b=execute(bars,symbol,direction,BOUNDS[0],'2020-02-04 09:30',sl,s.key,tp)
                    if a!=b or a['Status']!='OK':raise AssertionError('U06 exact trade replay')
                    x,y=summarize([a]),summarize([b])
                    if x!=y or gate(x,True)!=gate(y,True):raise AssertionError('U06 metric replay')
                    if tp is None:am[sl]=x;bm[sl]=y
                    count+=1
            if zones(am)!=zones(bm) or winner(zones(am))!=winner(zones(bm)):raise AssertionError('zone replay')
    return dict(Status='PASS',Cases=count,Bounds=list(BOUNDS),HoldingMinutes=30,SLPips=[10,15,20],TPPips=[None,5,15,25],Comparison='EXACT_ALL_TRADE_FIELDS_METRICS_GATE_ZONES',Formal72Used=False,FullSearch=False,PerformanceSaved=False)
