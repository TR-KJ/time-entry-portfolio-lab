"""Colab-only fixed Candidate Validation; aggregate/display only at completion."""
import importlib.util,json,os,platform,subprocess,zipfile
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from .stage6_config import ROOT,CONFIG_SHA,sha,load_config
from .stage6_input import load_input,assert_frozen_candidate
from .stage6_data import audit_inputs,load_validation,availability,START,END
from .stage6_engine import make_engine,replay_candidate
from .stage6_metrics import evaluate,PERIODS
from .stage5_validation import assess
from .stage2a_search import open_store,save_job,read_job
from .stage2b_search import csv_write
from .stage1_search import atomic_json

STATE='COMPLETE_STAGE6_VALIDATION_ONLY'

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(c not in '0123456789abcdef' for c in expected_sha):raise ValueError('40-digit Stage6 SHA required')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=expected_sha:raise ValueError('Stage6 checkout SHA mismatch')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean Stage6 checkout required')
    for n,h in json.loads((ROOT/'research_inputs/b6/stage6_release_manifest.json').read_text()).items():
        if sha(ROOT/n)!=h:raise ValueError('Stage6 release hash mismatch: '+n)
    load_input();return expected_sha

def require_authorization(expected_sha,run_full,confirmed):
    if run_full is not True or confirmed is not True:raise PermissionError('RUN_STAGE6_FULL and Chat confirmation both required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage6 full Validation is Google Colab only')
    return verify_release(expected_sha)

def space(points):return dict(CandidateCount=len(points),Periods=list(PERIODS),PeriodRows=len(points)*3,ValidationRows=len(points),NoRanking=True,NoRetuning=True,NoDropOrRefill=True)

def finish(out,ledger,points,c):
    out=Path(out)
    if set(ledger)!={p['CandidateID'] for p in points} or len(points)!=c['candidate_count']:raise ValueError('all frozen Candidate jobs required before aggregation')
    periods=[];validation=[];diagnostics=[]
    for p in points:
        job=read_job(out,ledger,p['CandidateID']);assert_frozen_candidate(job['candidate'],p)
        if [r['Period'] for r in job['periods']]!=list(PERIODS) or any(r['CandidateID']!=p['CandidateID'] for r in job['periods']):raise ValueError('period checkpoint mismatch')
        expected=assess(*job['periods'],p['DiscoveryMaxDDR'])
        if any(job['validation'].get(k)!=v for k,v in expected.items()):raise ValueError('assessment checkpoint mismatch')
        if any(job['validation'].get(k)!=p[k] for k in ('CandidateID','Symbol','Direction','Weekday','FinalEntryJST','FinalExitJST','FinalExitDayOffset','FinalHoldingMinutes','SL','TP','SelectedEventMode','FixedSpreadPips','PipSize')):raise ValueError('fixed checkpoint conditions changed')
        periods.extend(job['periods']);validation.append(job['validation']);diagnostics.append(job['diagnostics'])
    counts=Counter(r['ValidationStatus'] for r in validation)
    if set(counts)-{'PASS','FAIL','INSUFFICIENT_SAMPLE'}:raise ValueError('invalid ValidationStatus')
    for name,rows in [('stage6_period_results.csv.gz',periods),('stage6_validation_results.csv.gz',validation),('stage6_diagnostics.csv.gz',diagnostics)]:csv_write(out,name,rows,list(rows[0]))
    summary=dict(State=STATE,Label=c['label'],CandidateCount=len(points),PeriodRows=len(periods),PASS=counts['PASS'],FAIL=counts['FAIL'],INSUFFICIENT_SAMPLE=counts['INSUFFICIENT_SAMPLE'],Periods=c['periods'],ValidationExecuted=True,MonitorExecuted=False,PortfolioExecuted=False,LiveChanged=False,NoRanking=True)
    atomic_json(out/'stage6_summary.json',summary);atomic_json(out/'progress.json',dict(summary,CompletedJobs=len(points),ExpectedJobs=len(points)))
    identity=json.loads((out/'identity.json').read_text());review_identity={k:v for k,v in identity.items() if k!='inputs'};review_identity['M1InputCount']=len(identity['inputs'])
    atomic_json(out/'stage6_review.json',dict(Summary=summary,Identity=review_identity,InputAudit=json.loads((out/'stage5_input_audit.json').read_text()),M1Audit=json.loads((out/'m1_input_audit.json').read_text()),Next='Chat review. Stage7/2026 Monitor and Portfolio not executed. PASS is not live adoption.'))
    names=['effective_config.json','stage5_input_audit.json','m1_input_audit.json','search_space.json','progress.json','stage6_period_results.csv.gz','stage6_validation_results.csv.gz','stage6_diagnostics.csv.gz','stage6_summary.json','stage6_review.json']
    tmp=out/'stage6_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(out/n,n)
    os.replace(tmp,out/'stage6_review.zip');return summary

def full_validation(data_root,out,expected_sha,run_full=False,confirmed=False):
    code=require_authorization(expected_sha,run_full,confirmed);c=load_config();points,calendar,input_audit=load_input()
    out=Path(out)
    if any(out.resolve().is_relative_to(p.resolve()) or p.resolve().is_relative_to(out.resolve()) for p in (ROOT,Path(data_root))):raise ValueError('output overlaps input/repository')
    if np.__version__!=c['runtime']['numpy'] or pd.__version__!=c['runtime']['pandas']:raise ValueError('frozen numpy/pandas required')
    manifest,paths,audit=audit_inputs(data_root);inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit]
    if len(inputs)!=56:raise ValueError('56 M1 identities required')
    identity=dict(code_sha=code,config_sha256=CONFIG_SHA,stage5_commit=c['stage5_commit'],candidate_sha256=c['candidate_sha256'],contract_sha256=c['contract_sha256'],candidate_count=len(points),inputs=inputs,calendar_sha256=c['calendar']['SHA256'],calendar_source_commit=c['calendar']['SourceCommit'],scope='FORMAL_VALIDATION_2024_2025',runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__))
    ledger=open_store(out,identity)
    if set(ledger)-{p['CandidateID'] for p in points}:raise ValueError('unknown checkpoint CandidateIDs')
    for n,d in [('effective_config.json',c),('stage5_input_audit.json',input_audit),('search_space.json',space(points))]:atomic_json(out/n,d)
    atomic_json(out/'progress.json',dict(State='RUNNING_STAGE6',CompletedJobs=len(ledger),ExpectedJobs=len(points)))
    coverage=[];dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(p['Symbol'] for p in points):
        # Recheck canonical boundaries even when every job for this pair is cached.
        bars=load_validation(symbol,manifest,paths);coverage.append(availability(bars,symbol))
        pending=[p for p in points if p['Symbol']==symbol and read_job(out,ledger,p['CandidateID']) is None]
        engine=make_engine(bars,symbol) if pending else None;del bars
        for p in pending:
            replay,diag=replay_candidate(p,dates[dates.weekday==p['Weekday']],calendar,engine=engine)
            save_job(out,ledger,p['CandidateID'],evaluate(p,replay,diag))
            atomic_json(out/'progress.json',dict(State='RUNNING_STAGE6',CompletedJobs=len(ledger),ExpectedJobs=len(points)))
            print(f'Stage6 completed jobs: {len(ledger)}/{len(points)}',flush=True)
        del engine
    atomic_json(out/'m1_input_audit.json',dict(Status='PASS',FileCount=56,ManifestSHA256=c['m1_manifest']['ManifestSHA256'],CanonicalCoverage=coverage,OutsideValidationRowsPassedToExecutor=0,MonitorExecuted=False))
    return finish(out,ledger,points,c)
