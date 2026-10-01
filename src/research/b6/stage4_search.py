"""Colab-only Stage4. Global E0 barrier precedes every filter and resume."""
import importlib.util,json,os,platform,subprocess,zipfile
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from .stage4_config import ROOT,CONFIG_SHA,load_config,sha
from .stage4_input import load_input
from .stage4_calendar import audit_calendar
from .stage4_events import MODES
from .stage4_metrics import preflight_all,evaluate_modes,FIXED
from .stage4_selection import choose,adoption,finite
from .stage3_grid import execution_candidate,fixed_setting
from .stage2a_engine import FastEngine,fast_replay
from .stage2a_search import open_store,save_job,read_job
from .stage2b_search import csv_write
from .stage1_search import atomic_json
from .stage1_data import audit_inputs,load_discovery
from .execution import START,END

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(x not in '0123456789abcdef' for x in expected_sha):raise ValueError('40-digit Stage4 Freeze SHA required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=expected_sha:raise ValueError('checkout SHA mismatch')
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT,check=True)
    for name,digest in json.loads((ROOT/'research_inputs/b6/stage4_release_manifest.json').read_text()).items():
        if sha(ROOT/name)!=digest:raise ValueError('Stage4 release hash mismatch: '+name)
    return actual

def require_full_authorization(expected_sha,confirmed):
    if not confirmed:raise PermissionError('Chat confirmation required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage4 full research is Google Colab only')
    return verify_release(expected_sha)

def search_space(points):
    return dict(CandidateCount=len(points),VariantsPerCandidate=3,TheoreticalMax=len(points)*3,ActualUniqueConfigurations=len(points)*3,Modes=list(MODES),DeduplicateModes=False,NoRetuning=True,NoRefill=True,NoDrop=True)

def replay_all(points,manifest,paths):
    # At most ~50 x 210 opportunities retained in memory; never persisted as trade logs.
    replays={};dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(p['Symbol'] for p in points):
        bars=load_discovery(symbol,manifest,paths);engine=FastEngine(bars,symbol);del bars
        for p in points:
            if p['Symbol']==symbol:replays[p['CandidateID']]=fast_replay(engine,execution_candidate(p),dates[dates.weekday==p['Weekday']],[fixed_setting(p)])
        del engine
        print('Stage4 E0 preflight replay: '+symbol,flush=True)
    return replays

def run_after_preflight(out,ledger,points,replays,calendar):
    # A failure anywhere prohibits ALL E1/E2 computation and checkpoint consumption.
    audits=preflight_all(points,replays)
    atomic_json(Path(out)/'e0_equivalence_audit.json',dict(Status='PASS',Comparison='EXACT_FULL_AND_FOUR_YEARLY_METRICS',Candidates=audits))
    for p in points:
        cid=p['CandidateID']
        if read_job(out,ledger,cid) is None:
            save_job(out,ledger,cid,evaluate_modes(p,replays[cid],calendar))
        atomic_json(Path(out)/'progress.json',dict(State='RUNNING_STAGE4',CompletedJobs=len(ledger),ExpectedJobs=len(points),CompletedConfigurations=len(ledger)*3))
        print(f'Stage4 checkpoints: {len(ledger)}/{len(points)}',flush=True)

def finish(out,ledger,points):
    out=Path(out);tables={k:[] for k in ('results','yearly','diagnostics','selection_audit')};selected=[]
    if set(ledger)!={p['CandidateID'] for p in points}:raise ValueError('incomplete/unexpected Stage4 checkpoints')
    for p in points:
        data=read_job(out,ledger,p['CandidateID'])
        for kind in tables:
            rows=data[kind];expected=[(mode,y) for mode in MODES for y in ((2020,2021,2022,2023) if kind=='yearly' else (None,))]
            if [(r['EventMode'],r.get('Year')) for r in rows]!=expected:raise ValueError('Stage4 mode/year checkpoint mismatch')
            if any(any(r.get(k)!=p[k] for k in FIXED) for r in rows):raise ValueError('Stage4 fixed strategy changed')
            tables[kind].extend(rows)
        best,reason=choose(data['results']);s=data['selected']
        if s['SelectedEventMode']!=best['EventMode'] or s['SelectionReason']!=reason or any(s.get(k)!=p[k] for k in FIXED):raise ValueError('Stage4 selected checkpoint mismatch')
        for r in data['results'][1:]:
            if any(r[k]!=v for k,v in adoption(r).items()):raise ValueError('Stage4 adoption checkpoint mismatch')
        selected.append(s)
    for kind,suffix in (('results','variant_results'),('yearly','yearly_results'),('diagnostics','event_diagnostics'),('selection_audit','selection_audit')):
        csv_write(out,'stage4_'+suffix+'.csv.gz',tables[kind],list(tables[kind][0]) if tables[kind] else ['CandidateID','EventMode'])
    atomic_json(out/'stage4_selected_settings.json',selected)
    counts=Counter(s['SelectedEventMode'] for s in selected)
    distributions={}
    for k in ('RetentionRate','RemovedTrades','DeltaTotalR','DeltaAvgR','DeltaMaxDDR'):
        vals=[s[k] for s in selected if finite(s[k])]
        distributions[k]=dict(Count=len(vals),UndefinedCount=len(selected)-len(vals),Min=min(vals) if vals else None,Median=float(np.median(vals)) if vals else None,Max=max(vals) if vals else None)
    summary=dict(State='COMPLETE_STAGE4_ONLY',CandidateCount=len(points),VariantCount=len(tables['results']),SelectedModeCounts={m:counts[m] for m in MODES},FilterAdoptionCount=counts['E1']+counts['E2'],E1AdoptionCount=counts['E1'],E2AdoptionCount=counts['E2'],SelectedDistributions=distributions,EventFilterExecuted=True,CandidateFreezeExecuted=False,ValidationExecuted=False,MonitorExecuted=False,PortfolioExecuted=False)
    atomic_json(out/'stage4_summary.json',summary)
    atomic_json(out/'progress.json',dict(summary,CompletedJobs=len(points),ExpectedJobs=len(points),CompletedConfigurations=len(points)*3))
    identity=json.loads((out/'identity.json').read_text());public_identity={k:v for k,v in identity.items() if k!='inputs'};public_identity['M1InputCount']=len(identity['inputs'])
    atomic_json(out/'stage4_review.json',dict(Summary=summary,Identity=public_identity,InputAudit=json.loads((out/'stage3_input_audit.json').read_text()),CalendarAudit=json.loads((out/'event_calendar_audit.json').read_text()),E0Audit=json.loads((out/'e0_equivalence_audit.json').read_text()),Next='Chat review; Stage5 Candidate Freeze / Validation / Monitor / Portfolio not executed.'))
    names=['effective_config.json','stage3_input_audit.json','event_calendar.json','event_calendar_audit.json','e0_equivalence_audit.json','search_space.json','progress.json','stage4_variant_results.csv.gz','stage4_yearly_results.csv.gz','stage4_event_diagnostics.csv.gz','stage4_selection_audit.csv.gz','stage4_selected_settings.json','stage4_summary.json','stage4_review.json']
    tmp=out/'stage4_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(out/n,n)
    os.replace(tmp,out/'stage4_review.zip');return summary

def full_sweep(data_root,out,stage3_root,stage2b_root,stage1_root,expected_sha,confirmed=False):
    code_sha=require_full_authorization(expected_sha,confirmed);c=load_config()
    points,input_audit,prior_identity=load_input(stage3_root,stage2b_root,stage1_root)
    calendar,calendar_audit=audit_calendar(c);out=Path(out)
    protected=[ROOT,Path(data_root),Path(stage3_root),Path(stage2b_root),Path(stage1_root)]
    if any(out.resolve().is_relative_to(p.resolve()) or p.resolve().is_relative_to(out.resolve()) for p in protected):raise ValueError('output overlaps repository or formal input')
    if np.__version__!=c['runtime']['numpy'] or pd.__version__!=c['runtime']['pandas']:raise RuntimeError('frozen numpy/pandas required')
    manifest,paths,audit=audit_inputs(data_root);inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit]
    if len(inputs)!=56 or inputs!=prior_identity['inputs']:raise ValueError('Stage3/M1 identity mismatch')
    identity=dict(code_sha=code_sha,config_sha256=CONFIG_SHA,stage3_code_sha=c['stage3_freeze_sha'],selected_settings_sha256=c['selected_settings_sha256'],stage3_runtime_sha256=input_audit['FormalInputSHA256'],calendar_sha256=c['calendar_sha256'],calendar_source_commit=c['calendar_source_commit'],candidate_sha256=c['candidate_sha256'],inputs=inputs,scope='FULL_DISCOVERY_STAGE4',runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__))
    ledger=open_store(out,identity)
    if set(ledger)-{p['CandidateID'] for p in points}:raise ValueError('unexpected Stage4 checkpoint IDs')
    for name,data in [('effective_config.json',c),('stage3_input_audit.json',input_audit),('event_calendar.json',calendar),('event_calendar_audit.json',calendar_audit),('search_space.json',search_space(points))]:atomic_json(out/name,data)
    atomic_json(out/'progress.json',dict(State='E0_PREFLIGHT_REQUIRED',EventFilterExecuted=False))
    replays=replay_all(points,manifest,paths)
    run_after_preflight(out,ledger,points,replays,calendar)
    return finish(out,ledger,points)
