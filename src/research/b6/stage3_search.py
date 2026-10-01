"""Colab-only fixed-SL/TP time fine-tuning; no later-stage API."""
import importlib.util,json,os,platform,subprocess,zipfile
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from .stage3_config import ROOT,CONFIG_SHA,load_config,sha
from .stage3_input import load_input
from .stage3_grid import time_grid,point_key
from .stage3_metrics import evaluate_candidate
from .stage3_selection import select_final
from .stage2a_engine import FastEngine
from .stage2a_search import open_store,save_job,read_job
from .stage2b_search import csv_write
from .stage2b_input import SCHEMAS
from .stage1_search import atomic_json
from .stage1_data import audit_inputs,load_discovery
from .execution import START,END

GRID_COLUMNS=['AnchorEntryMinute','AnchorExitMinute','AnchorExitDayOffset','AnchorHoldingMinutes','EntryDeltaMinutes','ExitDeltaMinutes','AdjustedEntryMinute','AdjustedExitMinute','AdjustedExitDayOffset','PlannedHoldingMinutes','AnchorDistance']
STABILITY_COLUMNS=['NeighborhoodCount','NeighborhoodPassCount','NeighborhoodPassRate','NeighborhoodMedianAvgR','NeighborhoodMedianTotalR','NeighborhoodWorstMaxDDR','PointAvgR','StabilityPass','StabilityFailReason']

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(x not in '0123456789abcdef' for x in expected_sha):raise ValueError('40-digit Stage3 Freeze SHA required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=expected_sha:raise ValueError('checkout SHA mismatch')
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT,check=True)
    for name,digest in json.loads((ROOT/'research_inputs/b6/stage3_release_manifest.json').read_text()).items():
        if sha(ROOT/name)!=digest:raise ValueError('release hash mismatch: '+name)
    return actual

def require_full_authorization(expected_sha,confirmed):
    if not confirmed:raise PermissionError('Chat confirmation required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage3 full sweep is Google Colab only')
    return verify_release(expected_sha)

def prepare_jobs(candidates,c):
    jobs=[]
    for candidate in candidates:
        grid,invalid=time_grid(candidate,c);jobs.append(dict(candidate=candidate,grid=grid,invalid=invalid))
    valid=sum(len(j['grid']) for j in jobs);invalid=sum(len(j['invalid']) for j in jobs);raw=len(candidates)*121
    if valid+invalid!=raw:raise ValueError('time space accounting mismatch')
    space=dict(TheoreticalMax=raw,ImplementationExpectedMax=raw,CandidateCount=len(candidates),RawGridPoints=raw,InvalidSchedulePoints=invalid,ActualUniqueConfigurations=valid,PerCandidate=[dict(CandidateID=j['candidate']['CandidateID'],RawGridPoints=121,InvalidSchedulePoints=len(j['invalid']),ActualUniqueConfigurations=len(j['grid'])) for j in jobs],NoExpansion=True)
    return jobs,space

def finish(out,ledger,jobs,c,space):
    out=Path(out)
    if set(ledger)!={j['candidate']['CandidateID'] for j in jobs}:raise ValueError('incomplete/unexpected candidate checkpoints')
    tables={k:[] for k in ('results','yearly','diagnostics','stability')};selected=[];dropped=[]
    for job in jobs:
        candidate=job['candidate'];data=read_job(out,ledger,candidate['CandidateID']);grid=job['grid']
        if data.get('grid')!=grid:raise ValueError('checkpoint time grid mismatch')
        expected_lookup={point_key(p):p for p in grid}
        for kind in ('results','yearly','diagnostics'):
            rows=data[kind];expected=[(*point_key(p),y) for p in grid for y in ((2020,2021,2022,2023) if kind=='yearly' else (None,))]
            if [(*point_key(r),r.get('Year')) for r in rows]!=expected:raise ValueError('checkpoint time/year keys mismatch')
            if any(any(r[k]!=v for k,v in expected_lookup[point_key(r)].items()) for r in rows):raise ValueError('checkpoint fixed fields mismatch')
            tables[kind].extend(rows)
        result=select_final(candidate,data['results'],data['yearly'],c);tables['stability'].extend(result['stability'])
        if result['selected'] is None:dropped.append(result['dropped'])
        else:selected.append(result['selected'])
    actual=len(tables['results'])
    if actual!=space['ActualUniqueConfigurations'] or len(selected)+len(dropped)!=len(jobs):raise ValueError('completion count mismatch')
    for kind,suffix in (('results','all_results'),('yearly','yearly_results'),('diagnostics','diagnostics')):
        columns=list(dict.fromkeys(SCHEMAS['stage2a_'+suffix+'.csv.gz']+GRID_COLUMNS+(SCHEMAS['stage2a_diagnostics.csv.gz'] if kind=='results' else [])))
        csv_write(out,'stage3_'+suffix+'.csv.gz',tables[kind],columns)
    csv_write(out,'stage3_stability.csv.gz',tables['stability'],SCHEMAS['stage2a_all_results.csv.gz']+GRID_COLUMNS+STABILITY_COLUMNS)
    csv_write(out,'dropped_structures.csv',dropped,['CandidateID','Reason'])
    atomic_json(out/'stage3_selected_settings.json',selected)
    summary=dict(State='COMPLETE_STAGE3_ONLY',CandidateCount=len(jobs),ActualUniqueConfigurations=actual,GatePass=sum(r['Pass'] for r in tables['results']),GateFail=sum(not r['Pass'] for r in tables['results']),StabilityPass=sum(r['StabilityPass'] for r in tables['stability']),StabilityFail=sum(not r['StabilityPass'] for r in tables['stability']),SelectedStructures=len(selected),DroppedStructures=len(dropped),EntryDeltaDistribution=dict(sorted(Counter(r['EntryDeltaMinutes'] for r in selected).items())),ExitDeltaDistribution=dict(sorted(Counter(r['ExitDeltaMinutes'] for r in selected).items())),AnchorUnchangedCount=sum(r['AnchorDistance']==0 for r in selected),Stage4Executed=False,EventFilterExecuted=False,ValidationExecuted=False,MonitorExecuted=False,Refill=False)
    atomic_json(out/'stage3_summary.json',summary);atomic_json(out/'progress.json',dict(State=summary['State'],CompletedJobs=len(jobs),ExpectedJobs=len(jobs),CompletedConfigurations=actual,ExpectedConfigurations=actual))
    identity=json.loads((out/'identity.json').read_text());review_identity={k:v for k,v in identity.items() if k!='inputs'};review_identity['M1InputCount']=len(identity['inputs'])
    atomic_json(out/'stage3_review.json',dict(Summary=summary,Identity=review_identity,InputAudit=json.loads((out/'stage2b_input_audit.json').read_text()),Next='Chat review. Selected time and SL/TP frozen. Event Filter / Validation / Monitor not executed.'))
    names=['effective_config.json','stage2b_input_audit.json','search_space.json','invalid_schedules.json','progress.json','stage3_all_results.csv.gz','stage3_yearly_results.csv.gz','stage3_diagnostics.csv.gz','stage3_stability.csv.gz','dropped_structures.csv','stage3_selected_settings.json','stage3_summary.json','stage3_review.json']
    tmp=out/'stage3_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:z.write(out/name,name)
    os.replace(tmp,out/'stage3_review.zip');return summary

def full_sweep(data_root,out,stage2b_root,stage1_root,expected_sha,confirmed=False):
    code_sha=require_full_authorization(expected_sha,confirmed);c=load_config()
    candidates,input_audit,prior_identity=load_input(stage2b_root,stage1_root)
    out=Path(out)
    if out.resolve().is_relative_to(ROOT):raise ValueError('output must be outside repository')
    if np.__version__!=c['runtime']['numpy'] or pd.__version__!=c['runtime']['pandas']:raise RuntimeError('frozen numpy/pandas required')
    manifest,paths,audit=audit_inputs(data_root);inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit]
    if len(inputs)!=56 or inputs!=prior_identity['inputs']:raise ValueError('Stage2-B/M1 identity mismatch')
    identity=dict(code_sha=code_sha,config_sha256=CONFIG_SHA,stage2b_code_sha=c['stage2b_freeze_sha'],selected_settings_sha256=c['selected_settings_sha256'],stage2b_runtime_sha256=input_audit['FormalInputSHA256'],candidate_sha256=c['candidate_sha256'],inputs=inputs,scope='FULL_DISCOVERY_STAGE3',runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__))
    ledger=open_store(out,identity);jobs,space=prepare_jobs(candidates,c)
    if set(ledger)-{a['CandidateID'] for a in candidates}:raise ValueError('unexpected checkpoint IDs')
    atomic_json(out/'effective_config.json',c);atomic_json(out/'stage2b_input_audit.json',input_audit);atomic_json(out/'search_space.json',space);atomic_json(out/'invalid_schedules.json',[p for j in jobs for p in j['invalid']])
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(a['Symbol'] for a in candidates):
        pending=[j for j in jobs if j['candidate']['Symbol']==symbol and read_job(out,ledger,j['candidate']['CandidateID']) is None]
        if not pending:continue
        bars=load_discovery(symbol,manifest,paths);engine=FastEngine(bars,symbol);del bars
        for job in pending:
            candidate=job['candidate'];data=evaluate_candidate(engine,candidate,dates[dates.weekday==candidate['Weekday']],job['grid'],c);data['grid']=job['grid'];save_job(out,ledger,candidate['CandidateID'],data)
            completed=sum(len(j['grid']) for j in jobs if j['candidate']['CandidateID'] in ledger)
            atomic_json(out/'progress.json',dict(State='RUNNING',CompletedJobs=len(ledger),ExpectedJobs=len(jobs),CompletedConfigurations=completed,ExpectedConfigurations=space['ActualUniqueConfigurations']))
            print(f'Stage3 checkpoints: {len(ledger)}/{len(jobs)}; time points {completed}/{space["ActualUniqueConfigurations"]}',flush=True)
        del engine
    return finish(out,ledger,jobs,c,space)
