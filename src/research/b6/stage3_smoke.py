"""First three selected inputs, delta -1/0/+1 only, four fixed Discovery days."""
import argparse
import numpy as np
import pandas as pd
from .stage3_config import load_config
from .stage3_input import load_input
from .stage3_grid import time_grid,execution_candidate,fixed_setting
from .stage3_metrics import evaluate_point
from .stage2a_engine import FastEngine,fast_replay,reference_replay
from .stage1_data import audit_inputs,load_discovery
from .stage1_search import atomic_json
from .stage0 import EXPECTED_SHA

def smoke(data_root,stage2b_root,stage1_root,out):
    c=load_config();selected,_,identity=load_input(stage2b_root,stage1_root);chosen=selected[:3]
    manifest,paths,audit=audit_inputs(data_root)
    if [{k:r[k] for k in ('Filename','SHA256')} for r in audit]!=identity['inputs']:raise ValueError('smoke input identity mismatch')
    points=compared=0
    for symbol in dict.fromkeys(a['Symbol'] for a in chosen):
        discovery=load_discovery(symbol,manifest,paths)
        for a in [x for x in chosen if x['Symbol']==symbol]:
            dates=pd.DatetimeIndex([pd.Timestamp(y,2,1)+pd.Timedelta(days=(a['Weekday']-pd.Timestamp(y,2,1).weekday())%7) for y in (2020,2021,2022,2023)])
            mask=np.zeros(len(discovery),dtype=bool)
            for d in dates:mask|=(discovery.index>=d)&(discovery.index<d+pd.Timedelta(days=3))
            bars=discovery.loc[mask].copy();engine=FastEngine(bars,symbol)
            subset=[p for p in time_grid(a,c)[0] if p['EntryDeltaMinutes'] in (-1,0,1) and p['ExitDeltaMinutes'] in (-1,0,1)]
            for p in subset:
                adj=execution_candidate(p);setting=[fixed_setting(p)];f=fast_replay(engine,adj,dates,setting);s=reference_replay(bars,symbol,adj,dates,setting)
                np.testing.assert_array_equal(f.status,s.status);np.testing.assert_array_equal(f.raw_r,s.raw_r)
                for fr,sr in zip(f.records(0),s.records(0)):
                    if any(v!=sr[k] for k,v in fr.items()):raise AssertionError('minute execution mismatch')
                    compared+=1
                if evaluate_point(engine,p,dates,c)!=evaluate_point(None,p,dates,c,bars=bars):raise AssertionError('minute metric mismatch')
                points+=1
        del discovery
    result=dict(Status='PASS',Purpose='COMPATIBILITY_ONLY',Candidates=len(chosen),TimePoints=points,OpportunityComparisons=compared,Matched=compared,AuditedM1Inputs=len(audit),ExpectedM1ManifestSHA256=EXPECTED_SHA,SelectedInputSHA256=c['selected_settings_sha256'],Stage3FullSweepExecuted=False,Stage3FormalSelectionPerformed=False,RankingPublished=False)
    atomic_json(out,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',required=True);p.add_argument('--stage2b-root',required=True);p.add_argument('--stage1-root',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(smoke(a.data_root,a.stage2b_root,a.stage1_root,a.out))
