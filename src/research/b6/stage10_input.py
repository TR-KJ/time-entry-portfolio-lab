"""Frozen saved trade ledgers only. No price data or volatility assignments."""
import csv
import gzip
import io
import importlib.util
from datetime import datetime, timedelta
from decimal import Decimal as D, localcontext
from .stage10_config import (ROOT,INPUT,IMMUTABLE,FINAL_SHA,BASELINE_SHA,LEDGER_SHA,
    AJ,GJ,EXCLUDED,PERIODS,CONFIGS,require,sha,read)

# Load unchanged historical money helpers without importing any price engine.
_spec=importlib.util.spec_from_file_location('b6_stage10_legacy_money',ROOT/'src/research/edge_decay_phase2_money_simulation.py')
legacy=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(legacy)


def validate_rows(rows):
    seen=set()
    for r in rows:
        key=(r['PortfolioComponentKey'],r['RowId'])
        require(key not in seen,'duplicate component/source row');seen.add(key)
        require(r['SL']>0 and all(r[k].is_finite() for k in ('SL','Pips','R')),'invalid raw SL/Pips/R')
        e,c=r['EntryTime'],r['CloseTime']
        require(e.tzinfo is None and c.tzinfo is None,'naive JST required')
        require(e<=c<legacy.week_start(e)+timedelta(days=7),'trading-week crossing or invalid close')
        for a,b in PERIODS.values():
            start,end=datetime.fromisoformat(a),datetime.fromisoformat(b)
            require((start<=e<end)==(start<=c<end),'reporting-period crossing')
        tolerance=D('1e-8') if r['Source']=='BASELINE' else D('1e-12')
        require(abs(r['Pips']/r['SL']-r['R'])<=tolerance,'saved R integrity mismatch')


def frozen_candidates():
    for name,h in IMMUTABLE.items():require(sha(ROOT/name)==h,'Stage9 identity mismatch: '+name)
    artifact=read(ROOT/INPUT/'stage9_final_candidates.json')
    points=artifact['Candidates']
    require(artifact['CandidateCount']==2 and [p['CandidateID'] for p in points]==[AJ,GJ],'exact final two required')
    return points


def load_inputs(baseline_path,b6_ledger_path):
    points=frozen_candidates();by={p['CandidateID']:p for p in points}
    require(sha(baseline_path)==BASELINE_SHA and sha(b6_ledger_path)==LEDGER_SHA,'trade ledger hash mismatch')
    with localcontext() as ctx:
        ctx.prec=40
        original=legacy.load_baseline(baseline_path)
        baseline_artifact=read(ROOT/INPUT/'stage10_portfolio_baseline.json')
        ids=sorted({r['Strategy'] for r in original if r['Strategy']!=EXCLUDED},key=lambda s:int(s.split('_')[0]))
        require(ids==baseline_artifact['CurrentStrategyIDs'] and len(ids)==27,'current 27 identities mismatch')
        require('20_EA_1A_MonTue_Short' in ids,'Strategy20 must remain')
        current=[dict(r,Source='BASELINE',Symbol={'EJ':'EURJPY','GJ':'GBPJPY','AJ':'AUDJPY','UJ':'USDJPY','EA':'EURAUD','GA':'GBPAUD','AU':'AUDUSD'}[r['Pair']],PortfolioComponentKey='BASELINE:'+r['Strategy']) for r in original if r['Strategy']!=EXCLUDED]
        require(len(original)==16298 and len(current)==15837,'baseline trade count mismatch')
        raw=list(csv.DictReader(io.StringIO(gzip.decompress(__import__('pathlib').Path(b6_ledger_path).read_bytes()).decode('utf-8'))))
        require(len(raw)==3043,'Stage8 ledger rows mismatch')
        selected=[];seen=set()
        for i,r in enumerate(raw):
            if r['CandidateID'] not in by:continue
            p=by[r['CandidateID']];e=datetime.fromisoformat(r['ActualEntry']);c=datetime.fromisoformat(r['ActualClose'])
            planned=datetime.fromisoformat(r['PlannedEntry']);end=datetime.fromisoformat(r['PlannedExit'])
            require(r['Symbol']==p['Symbol'] and e==planned and e.weekday()==p['Weekday'] and e.strftime('%H:%M')==p['Entry'],'B6 entry conditions changed')
            require(end.strftime('%H:%M')==p['Exit'] and (end.date()-e.date()).days==p['ExitDayOffset'] and (end-e).total_seconds()==p['Holding']*60,'B6 exit conditions changed')
            require(c<=end+timedelta(minutes=4),'B6 close outside frozen fallback')
            key=(r['CandidateID'],r['WeekKey']);require(key not in seen,'duplicate B6 trade');seen.add(key)
            selected.append(dict(Source='B6',PortfolioComponentKey=r['CandidateID'],CandidateID=r['CandidateID'],
                RowId=i,StrategyNo=None,Strategy=r['CandidateID'],Symbol=p['Symbol'],Pair=p['Symbol'],
                EntryTime=e,CloseTime=c,SL=D(str(p['SL'])),Pips=D(r['Pips']),R=D(r['R'])))
        counts={cid:sum(r['CandidateID']==cid for r in selected) for cid in by}
        require(counts=={AJ:339,GJ:338},'final B6 trade count mismatch')
        rows=[r for r in current+selected if datetime(2020,1,1)<=r['EntryTime']<datetime(2026,9,10)]
        validate_rows(rows)
        audit=dict(Status='PASS',BaselineSHA256=BASELINE_SHA,B6LedgerSHA256=LEDGER_SHA,
            BaselineTrades=16298,CurrentTrades=15837,Current2020Trades=sum(r['Source']=='BASELINE' for r in rows),
            B6Trades=counts,Stage8LedgerRows=3043,ReportingBoundaryCrossings=0,TradingWeekCrossings=0,
            SavedRIntegrity='PASS',M1Read=False,ReplayExecuted=False,GlobalR2Applied=False,
            PortfolioSimulationExecuted=False)
        return rows,audit


def portfolio(rows,name):
    require(name in CONFIGS,'unregistered portfolio')
    out=[r for r in rows if r['Source']=='BASELINE' or r['PortfolioComponentKey'] in CONFIGS[name]]
    validate_rows(out)
    return out
