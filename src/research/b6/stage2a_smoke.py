"""Bounded compatibility check: first 3 fixed inputs, 2 SLs, 3 TPs, 4 dates.

No performance/ranking artifact; no full-sweep entry point is called.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from .stage2a_config import load_config,load_candidates,tp_grid
from .stage2a_engine import FastEngine,fast_replay,reference_replay
from .stage2a_metrics import summarize
from .stage1_data import audit_inputs,load_discovery
from .stage1_search import atomic_json
from .stage0 import EXPECTED_SHA

def smoke(data_root,candidate_path,identity_path,effective_config_path,out):
    c=load_config();candidates,audit=load_candidates(candidate_path,identity_path,effective_config_path)
    manifest,paths,inputs=audit_inputs(data_root);chosen=candidates[:3];conditions=opportunities=generated=0
    for symbol in dict.fromkeys(a['Symbol'] for a in chosen):
        discovery=load_discovery(symbol,manifest,paths)
        for a in [a for a in chosen if a['Symbol']==symbol]:
            # Fixed first matching weekday in February in each Discovery year.
            dates=pd.DatetimeIndex([pd.Timestamp(y,2,1)+pd.Timedelta(days=(a['Weekday']-pd.Timestamp(y,2,1).weekday())%7) for y in (2020,2021,2022,2023)])
            mask=np.zeros(len(discovery),dtype=bool)
            for d in dates:mask|=(discovery.index>=d)&(discovery.index<d+pd.Timedelta(days=3))
            bars=discovery.loc[mask].copy();grid=[tp_grid(sl,c)[i] for sl in (c['sl_pips'][symbol][0],c['sl_pips'][symbol][-1]) for i in (0,1,4)]
            fast=fast_replay(FastEngine(bars,symbol),a,dates,grid);slow=reference_replay(bars,symbol,a,dates,grid)
            np.testing.assert_array_equal(fast.status,slow.status);np.testing.assert_array_equal(fast.raw_r,slow.raw_r)
            for i in range(len(grid)):
                for f,s in zip(fast.records(i),slow.records(i)):
                    if any(v!=s[k] for k,v in f.items()):raise AssertionError('reference-fast trade mismatch')
                    generated+=int(f['Status']=='OK');opportunities+=1
            if summarize(a,grid,fast,c['gate'])!=summarize(a,grid,slow,c['gate']):raise AssertionError('reference-fast metric mismatch')
            conditions+=len(grid)
        del discovery
    report=dict(Status='PASS',Purpose='compatibility_only_no_candidate_performance',CandidateCount=3,Conditions=conditions,OpportunityComparisons=opportunities,GeneratedTradeComparisons=generated,MatchedM1Inputs=len(inputs),ExpectedManifestSHA256=EXPECTED_SHA,CandidateInputSHA256=c['candidate_sha256'],Stage1FreezeSHA=c['stage1_freeze_sha'],CandidateInputCount=audit['CandidateCount'],FullSweepExecuted=False,RankingProduced=False)
    atomic_json(out,report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',required=True);p.add_argument('--stage1-root',required=True,type=Path);p.add_argument('--out',required=True);a=p.parse_args()
    print(json.dumps(smoke(a.data_root,a.stage1_root/'stage1_selected_structures.json',a.stage1_root/'identity.json',a.stage1_root/'effective_config.json',a.out),indent=2))
