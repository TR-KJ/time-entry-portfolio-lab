"""Colab-only Reference Monitor; publish results only after all 17 jobs."""
import importlib.util,json,os,platform,subprocess,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from .stage7_config import ROOT,CONFIG_SHA,sha,load_config
from .stage7_input import load_input,assert_frozen_candidate
from .stage7_data import audit_inputs,load_monitor,availability,START,END
from .stage7_engine import make_engine,replay_candidate
from .stage7_metrics import evaluate,fixed_columns,METRICS
from .stage2a_search import open_store,save_job,read_job
from .stage2b_search import csv_write
from .stage1_search import atomic_json

STATE='COMPLETE_STAGE7_MONITOR_ONLY'

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(c not in '0123456789abcdef' for c in expected_sha):raise ValueError('40-digit Stage7 SHA required')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=expected_sha:raise ValueError('Stage7 checkout SHA mismatch')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean Stage7 checkout required')
    for n,h in json.loads((ROOT/'research_inputs/b6/stage7_release_manifest.json').read_text()).items():
        if sha(ROOT/n)!=h:raise ValueError('Stage7 release hash mismatch: '+n)
    load_input();return expected_sha

def require_authorization(expected_sha,run_full,confirmed):
    if run_full is not True or confirmed is not True:raise PermissionError('RUN_STAGE7_FULL and Chat confirmation both required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage7 full Monitor is Google Colab only')
    return verify_release(expected_sha)

def finish(out,ledger,points,c):
    out=Path(out)
    if set(ledger)!={p['CandidateID'] for p in points} or len(points)!=c['candidate_count']:raise ValueError('all frozen Monitor jobs required')
    results=[];diagnostics=[]
    for p in points:
        job=read_job(out,ledger,p['CandidateID']);assert_frozen_candidate(job['candidate'],p)
        expected=fixed_columns(p);result=job['monitor'];diag=job['diagnostics']
        if set(result)!=set(expected)|{'Monitor'+k for k in METRICS} or any(result.get(k)!=v for k,v in expected.items()):raise ValueError('checkpoint condition/status/provenance mismatch')
        if diag['CandidateID']!=p['CandidateID'] or diag['Trades']!=result['MonitorTrades']:raise ValueError('checkpoint diagnostics mismatch')
        results.append(result);diagnostics.append(diag)
    for name,rows in [('stage7_monitor_results.csv.gz',results),('stage7_diagnostics.csv.gz',diagnostics)]:csv_write(out,name,rows,list(rows[0]))
    audit=json.loads((out/'m1_input_audit.json').read_text())
    summary=dict(State=STATE,CandidateCount=len(points),FormalValidationPASSCount=len(points),MonitoredCount=len(points),MonitorPeriod=c['monitor_period'],ActualDataEnd={r['Symbol']:r['LastAvailableJST'] for r in audit['CanonicalCoverage']},MonitorExecuted=True,FormalValidationChanged=False,PortfolioExecuted=False,LiveChanged=False,NoMonitorPassFail=True,NoRanking=True,NoRetuning=True,PartialYear=True)
    atomic_json(out/'stage7_summary.json',summary)
    identity=json.loads((out/'identity.json').read_text());review_identity={k:v for k,v in identity.items() if k!='inputs'};review_identity['M1InputCount']=len(identity['inputs'])
    atomic_json(out/'stage7_review.json',dict(Summary=summary,Identity=review_identity,Stage6InputAudit=json.loads((out/'stage6_input_audit.json').read_text()),M1Audit=audit,Next='Chat review only. No Portfolio/live. Partial-year reference observations; no Monitor PASS/FAIL or retuning.'))
    atomic_json(out/'progress.json',dict(summary,CompletedJobs=len(points),ExpectedJobs=len(points)))
    names=['effective_config.json','stage6_input_audit.json','m1_input_audit.json','progress.json','stage7_monitor_results.csv.gz','stage7_diagnostics.csv.gz','stage7_summary.json','stage7_review.json']
    tmp=out/'stage7_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(out/n,n)
    os.replace(tmp,out/'stage7_review.zip');return summary

def full_monitor(data_root,out,expected_sha,run_full=False,confirmed=False):
    code=require_authorization(expected_sha,run_full,confirmed);c=load_config();points,calendar,input_audit=load_input()
    out=Path(out)
    if any(out.resolve().is_relative_to(p.resolve()) or p.resolve().is_relative_to(out.resolve()) for p in (ROOT,Path(data_root))):raise ValueError('output overlaps input/repository')
    if np.__version__!=c['runtime']['numpy'] or pd.__version__!=c['runtime']['pandas']:raise ValueError('frozen numpy/pandas required')
    manifest,paths,audit=audit_inputs(data_root);inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit]
    if len(inputs)!=56:raise ValueError('56 M1 identities required')
    identity=dict(code_sha=code,config_sha256=CONFIG_SHA,monitor_candidate_sha256=c['monitor_candidate_sha256'],stage6_code_sha=c['stage6_code_sha'],stage6_validation_results_sha256=c['formal_file_sha256']['stage6_validation_results.csv.gz'],candidate_count=len(points),candidate_ids=[p['CandidateID'] for p in points],inputs=inputs,calendar_sha256=c['calendar']['SHA256'],runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__),scope='REFERENCE_MONITOR_2026_PARTIAL')
    ledger=open_store(out,identity)
    if set(ledger)-set(identity['candidate_ids']):raise ValueError('unknown checkpoint CandidateIDs')
    atomic_json(out/'effective_config.json',c);atomic_json(out/'stage6_input_audit.json',input_audit)
    atomic_json(out/'progress.json',dict(State='RUNNING_STAGE7',CompletedJobs=len(ledger),ExpectedJobs=len(points)))
    coverage=[];dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(p['Symbol'] for p in points):
        bars=load_monitor(symbol,manifest,paths);pair_audit=availability(bars,symbol);coverage.append(pair_audit)
        pending=[p for p in points if p['Symbol']==symbol and read_job(out,ledger,p['CandidateID']) is None]
        engine=make_engine(bars,symbol) if pending else None;del bars
        for p in pending:
            replay,diag=replay_candidate(p,dates[dates.weekday==p['Weekday']],calendar,engine=engine)
            save_job(out,ledger,p['CandidateID'],evaluate(p,replay,diag,pair_audit))
            atomic_json(out/'progress.json',dict(State='RUNNING_STAGE7',CompletedJobs=len(ledger),ExpectedJobs=len(points)))
            print(f'Stage7 completed jobs: {len(ledger)}/{len(points)}',flush=True)
        del engine
    atomic_json(out/'m1_input_audit.json',dict(Status='PASS',FileCount=56,ManifestSHA256=c['m1_manifest']['ManifestSHA256'],Inputs=inputs,CanonicalCoverage=coverage,OutsideMonitorRowsPassedToExecutor=0))
    return finish(out,ledger,points,c)
