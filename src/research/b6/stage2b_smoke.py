"""Bounded Discovery compatibility only; never selects real Stage2-B centers."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from .stage2b_config import load_config
from .stage2a_config import load_candidates,load_config as stage2a_config,tp_grid
from .stage2a_engine import FastEngine,fast_replay,reference_replay
from .stage2a_metrics import summarize
from .stage2b_metrics import evaluate_candidate
from .stage1_data import audit_inputs,load_discovery
from .stage1_search import atomic_json
from .stage0 import EXPECTED_SHA

def smoke(data_root,stage1_root,out):
    root=Path(stage1_root);c=load_config();a=stage2a_config()
    candidates,_=load_candidates(root/'stage1_selected_structures.json',root/'identity.json',root/'effective_config.json')
    manifest,paths,audit=audit_inputs(data_root);chosen=candidates[:3];conditions=opportunities=0
    for symbol in dict.fromkeys(x['Symbol'] for x in chosen):
        discovery=load_discovery(symbol,manifest,paths)
        for candidate in [x for x in chosen if x['Symbol']==symbol]:
            dates=pd.DatetimeIndex([pd.Timestamp(y,2,1)+pd.Timedelta(days=(candidate['Weekday']-pd.Timestamp(y,2,1).weekday())%7) for y in (2020,2021,2022,2023)])
            mask=np.zeros(len(discovery),dtype=bool)
            for d in dates:mask|=(discovery.index>=d)&(discovery.index<d+pd.Timedelta(days=3))
            bars=discovery.loc[mask].copy();grid=[tp_grid(sl,a)[i] for sl in (a['sl_pips'][symbol][0],a['sl_pips'][symbol][-1]) for i in (0,1,4)]
            engine=FastEngine(bars,symbol);fast=fast_replay(engine,candidate,dates,grid);ref=reference_replay(bars,symbol,candidate,dates,grid)
            np.testing.assert_array_equal(fast.status,ref.status);np.testing.assert_array_equal(fast.raw_r,ref.raw_r)
            for i in range(len(grid)):
                for f,s in zip(fast.records(i),ref.records(i)):
                    if any(v!=s[k] for k,v in f.items()):raise AssertionError('execution mismatch')
                    opportunities+=1
            current=evaluate_candidate(engine,candidate,dates,grid,c)
            if current!=summarize(candidate,grid,fast,a['gate']) or current!=summarize(candidate,grid,ref,a['gate']):raise AssertionError('Stage2-B adapter metric mismatch')
            conditions+=len(grid)
        del discovery
    report=dict(Status='PASS',Purpose='compatibility_only',Candidates=3,Conditions=conditions,OpportunityComparisons=opportunities,Matched=opportunities,AuditedM1Inputs=len(audit),ExpectedM1ManifestSHA256=EXPECTED_SHA,Stage1CandidateSHA256=c['candidate_sha256'],ActualStage2BCentersSelected=False,ActualStage2BSelectedSettingsProduced=False,PerformanceOrRankingPublished=False,FullSweepExecuted=False)
    atomic_json(out,report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',required=True);p.add_argument('--stage1-root',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(smoke(a.data_root,a.stage1_root,a.out))
