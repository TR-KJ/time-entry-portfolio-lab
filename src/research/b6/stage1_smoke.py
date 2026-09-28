"""Fixed, bounded Discovery implementation check; never search, rank or select.

Report comparison counts only, never candidate performance or top candidates.
"""
import argparse,hashlib,json,time,platform
from pathlib import Path
import numpy as np
import pandas as pd
from .stage1_config import load_config
from .stage0 import EXPECTED_SHA
from .stage1_data import audit_inputs,load_discovery
from .stage1_engine import FastEngine,reference_batch
from .stage1_metrics import metrics
from .stage1_search import atomic_json
DATES=pd.DatetimeIndex(['2020-02-04','2021-02-02','2022-02-01','2023-02-07'])
ENTRIES=(540,1425);HOLDS=(30,60,1440)

def run_smoke(root,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);c=load_config()
    manifest,paths,audit=audit_inputs(root)
    atomic_json(out/'smoke_input_identity.json',dict(Status='PASS',ExpectedFiles=56,MatchedFiles=len(audit),ExpectedManifest='research_inputs/b6/expected_m1_manifest.csv',ExpectedManifestSHA256=EXPECTED_SHA))
    reports=[];compared=0
    for symbol in c['symbols']:
        full=load_discovery(symbol,manifest,paths)
        # Only four predetermined 2-day windows cross the smoke execution boundary.
        mask=np.zeros(len(full),dtype=bool)
        for d in DATES:mask|=(full.index>=d)&(full.index<d+pd.Timedelta(days=3))
        bars=full.loc[mask].copy();del full
        began=time.perf_counter();eng=FastEngine(bars,symbol);build_s=time.perf_counter()-began
        fast_s=ref_s=0.;count=ok=0
        for long in (True,False):
            for entry in ENTRIES:
                began=time.perf_counter();batch=eng.prepare(DATES,entry,long,c['sl_pips'][symbol]).evaluate(HOLDS);fast_s+=time.perf_counter()-began
                began=time.perf_counter();old,rs,status=reference_batch(bars,symbol,DATES,entry,long,c['sl_pips'][symbol],HOLDS);ref_s+=time.perf_counter()-began
                np.testing.assert_array_equal(batch.status,status)
                np.testing.assert_array_equal(batch.r,rs)
                fast_metrics=batch.summary(c['gate'])
                for si in range(5):
                    for fast,slow in zip(batch.records(si),old[si]):
                        for key,value in fast.items():
                            if value!=slow[key]:raise AssertionError((symbol,key,'reference-fast mismatch'))
                        count+=1;ok+=fast['Status']=='OK'
                    ref_metrics=metrics(rs[si],status==0,DATES.year,c['gate'])
                    for key,value in fast_metrics[si].items():np.testing.assert_array_equal(value,ref_metrics[key])
        compared+=count
        reports.append(dict(Symbol=symbol,Status='PASS',OpportunitySLComparisons=count,ActualTradeSLComparisons=ok,BuildSeconds=round(build_s,4),FastSeconds=round(fast_s,4),ReferenceSeconds=round(ref_s,4)))
        print(symbol,'bounded compatibility PASS',count,'comparisons',flush=True);del eng,bars
    report=dict(Status='PASS',Scope='BOUNDED_IMPLEMENTATION_CHECK_NOT_DISCOVERY_RESULT',Dates=[str(d.date()) for d in DATES],EntryMinutes=ENTRIES,HoldingMinutes=HOLDS,
                OpportunitySLComparisons=compared,Symbols=reports,PerformanceMetricsPublished=False,CandidateRankingExecuted=False,FullSweepExecuted=False,ValidationExecuted=False,MonitorExecuted=False,
                Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__)
    atomic_json(out/'real_data_smoke.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('/content/b6_stage1_smoke'));a=p.parse_args();run_smoke(a.data_root,a.out)
