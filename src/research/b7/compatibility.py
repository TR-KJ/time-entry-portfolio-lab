"""Stage0 frozen-reference checks only. Never generates candidates."""
import importlib.util,sys
from pathlib import Path
from .stage0_audit import ROOT,digest

def references():
    import types
    p=ROOT/'src/research/daily_stop_baseline_revalidation.py'
    if digest(p)!='08b9717a3a94a0066e7ef7ebfa0f4802cbc84ae0570c3b875d96729877f4e216':raise ValueError('baseline identity')
    spec=importlib.util.spec_from_file_location('b7_test_baseline',p);ref=importlib.util.module_from_spec(spec);sys.modules[spec.name]=ref;spec.loader.exec_module(ref)
    p=ROOT/'src/research/b7/reference/b6_execution.py'
    spec=importlib.util.spec_from_file_location('b7_test_b6',p);ex=importlib.util.module_from_spec(spec);sys.modules[spec.name]=ex;spec.loader.exec_module(ex)
    # Private test adapters: original sources remain byte-identical. Only symbol constants extended.
    for symbol,pair,spread in [('EURUSD','EU',1.0),('GBPUSD','GU',1.5)]:
        ex.PIPS[symbol]=.0001;ex.SPREAD[symbol]=spread
        ref.PIP_SIZE[pair]=.0001;ref.SPREAD_PIPS[pair]=spread;ref.SYMBOL_TO_PAIR[symbol]=pair
    ref.EVENT_POLICY[999]={k:'-' for k in ref.EVENTS}
    return ref,ex

def bounded_smoke(data_root):
    """One prespecified 2020-Feb-04 anchor,30-minute hold,SL20,TP None/30; no result selection."""
    import json
    import pandas as pd
    from .stage0_audit import SYMBOLS,save
    from .execution import discovery_view
    ref,ex=references();manifest=pd.read_csv(ROOT/'research_inputs/b7/expected_m1_manifest.csv')
    checks=[]
    for symbol in SYMBOLS:
        records=manifest[(manifest.Symbol==symbol)&(manifest.FirstRaw<'2020-02-04')&(manifest.LastRaw>'2020-02-04')]
        if len(records)!=1:raise ValueError('smoke input ambiguity')
        row=records.iloc[0];paths=list(Path(data_root).rglob(row.Filename))
        if len(paths)!=1 or digest(paths[0])!=row.SHA256:raise ValueError('smoke identity mismatch')
        full=ref.read_mt5_file(paths[0]);raw=full.RawDatetime.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward')
        full.index=pd.DatetimeIndex(raw.dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
        bars=discovery_view(full);del full
        e=pd.Timestamp('2020-02-04 09:00');x=e+pd.Timedelta(minutes=30)
        bars=bars.loc[e:x+pd.Timedelta(minutes=4)].copy()
        for long in (True,False):
            for tp in (None,30):
                r=ex.execute(bars,symbol,long,e,x,20,tp)
                s=ref.Strategy(999,'B7_COMPATIBILITY_FIXTURE',ref.SYMBOL_TO_PAIR[symbol],long,(1,),(9,0),(9,30),0,20,tp)
                old=ref.run_strategy(s,bars,{k:set() for k in ref.EVENTS},[])
                keys=('EntryTime','ScheduledExitTime','CloseTime','EntryPrice','ClosePrice','Pips','R','ExitReason','ExitDelayMinutes')
                ok=r['Status']=='OK' and len(old)==1 and all((str(r[k])==str(old[0][k]) if k.endswith('Time') else r[k]==old[0][k]) for k in keys)
                checks.append({'Symbol':symbol,'Direction':'Long' if long else 'Short','TPMode':'NONE' if tp is None else 'FIXED30','Status':'PASS' if ok else 'FAIL'})
                if not ok:raise ValueError('bounded compatibility mismatch')
    save('bounded_smoke.json',{'Anchor':'2020-02-04 09:00 JST','HoldingMinutes':30,'SLPips':20,'Cases':checks,'PnL_or_ranking_saved':False,'CandidateSelection':False,'ValidationMonitorPerformance':False})
    print('Bounded compatibility cases:',len(checks),'PASS; no performance output')
