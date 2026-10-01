"""Three fixed selected inputs x four predeclared February dates; no selection."""
import argparse
import numpy as np
import pandas as pd
from .stage4_config import load_config
from .stage4_input import load_input
from .stage4_calendar import audit_calendar
from .stage4_events import filter_replay
from .stage4_metrics import summarize_replay
from .stage3_grid import execution_candidate,fixed_setting
from .stage2a_engine import FastEngine,fast_replay,reference_replay
from .stage1_data import audit_inputs,load_discovery
from .stage1_search import atomic_json
from .stage0 import EXPECTED_SHA

def smoke(data_root,stage3_root,stage2b_root,stage1_root,out):
    c=load_config();selected,_,identity=load_input(stage3_root,stage2b_root,stage1_root);chosen=selected[:3];cal,_=audit_calendar(c)
    manifest,paths,audit=audit_inputs(data_root)
    if [{k:r[k] for k in ('Filename','SHA256')} for r in audit]!=identity['inputs']:raise ValueError('smoke M1 identity mismatch')
    compared=retained=overlaps=0
    for symbol in dict.fromkeys(p['Symbol'] for p in chosen):
        discovery=load_discovery(symbol,manifest,paths)
        for p in [x for x in chosen if x['Symbol']==symbol]:
            dates=pd.DatetimeIndex([pd.Timestamp(y,2,1)+pd.Timedelta(days=(p['Weekday']-pd.Timestamp(y,2,1).weekday())%7) for y in (2020,2021,2022,2023)])
            mask=np.zeros(len(discovery),dtype=bool)
            for d in dates:mask|=(discovery.index>=d)&(discovery.index<d+pd.Timedelta(days=3))
            bars=discovery.loc[mask].copy();engine=FastEngine(bars,symbol);a=execution_candidate(p);setting=[fixed_setting(p)]
            f=fast_replay(engine,a,dates,setting);s=reference_replay(bars,symbol,a,dates,setting)
            np.testing.assert_array_equal(f.status,s.status);np.testing.assert_array_equal(f.raw_r,s.raw_r)
            for fr,sr in zip(f.records(0),s.records(0)):
                if any(v!=sr[k] for k,v in fr.items()):raise AssertionError('E0 execution mismatch')
                compared+=1
            if summarize_replay(p,f)!=summarize_replay(p,s):raise AssertionError('E0 limited metrics mismatch')
            for mode in ('E1','E2'):
                ff,diag=filter_replay(p,f,mode,cal);ss,sd=filter_replay(p,s,mode,cal)
                if diag!=sd:raise AssertionError('filter diagnostics mismatch')
                overlaps+=diag['FilteredOpportunities']
                np.testing.assert_array_equal(ff.status,ss.status)
                for i in np.flatnonzero(ff.status==0):
                    if ff.rows[0][i]!=f.rows[0][i] or any(v!=ss.rows[0][i][k] for k,v in ff.rows[0][i].items()):raise AssertionError('retained execution changed')
                    retained+=1
            del engine,bars
        del discovery
    result=dict(Status='PASS',Purpose='COMPATIBILITY_ONLY',Candidates=3,DatesPerCandidate=4,E0OpportunityComparisons=compared,RetainedTradeComparisons=retained,FilteredOpportunityModeComparisons=overlaps,AuditedM1Inputs=len(audit),ExpectedM1ManifestSHA256=EXPECTED_SHA,Stage3SelectedSHA256=c['selected_settings_sha256'],Stage4FullSweepExecuted=False,FormalEventModeSelectionPerformed=False,E0FullDiscoveryOfficialEquivalence='PENDING_COLAB_GLOBAL_PREFLIGHT',RankingPublished=False)
    atomic_json(out,result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('data-root','stage3-root','stage2b-root','stage1-root','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(smoke(a.data_root,a.stage3_root,a.stage2b_root,a.stage1_root,a.out))
