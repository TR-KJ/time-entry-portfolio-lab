"""Colab-only structural evidence; all candidate jobs precede pairwise output."""
import importlib.util,json,os,platform,subprocess,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from .stage8_config import ROOT,CONFIG_SHA,sha,load_config
from .stage8_input import load_input,assert_frozen_candidate
from .stage8_data import audit_inputs,load_analysis,availability,START,END,PERIODS
from .stage8_engine import make_engine,replay_candidate
from .stage8_metrics import evaluate,validate_ledger,candidate_periods,LEDGER_FIELDS,DIAGNOSTIC_FIELDS
from .stage8_pairwise import all_pairs,matrices
from .stage2a_search import open_store,save_job,read_job
from .stage2b_search import csv_write
from .stage1_search import atomic_json

STATE='COMPLETE_STAGE8_OVERLAP_CORRELATION_ONLY'

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(c not in '0123456789abcdef' for c in expected_sha):raise ValueError('40-digit Stage8 SHA required')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=expected_sha:raise ValueError('Stage8 checkout SHA mismatch')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('clean Stage8 checkout required')
    for n,h in json.loads((ROOT/'research_inputs/b6/stage8_release_manifest.json').read_text()).items():
        if sha(ROOT/n)!=h:raise ValueError('Stage8 release hash mismatch: '+n)
    load_input();return expected_sha

def require_authorization(expected_sha,run_full,confirmed):
    if run_full is not True or confirmed is not True:raise PermissionError('RUN_STAGE8_FULL and Chat confirmation both required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage8 full structural analysis is Google Colab only')
    return verify_release(expected_sha)

def validate_job(job,p):
    assert_frozen_candidate(job['candidate'],p);validate_ledger(job['ledger'])
    diagnostics=job['diagnostics'];ids=[r['WeekKey'] for r in diagnostics]
    expected_dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D');expected_dates=expected_dates[expected_dates.weekday==p['Weekday']]
    if ids!=list(expected_dates.strftime('%Y-%m-%d')):raise ValueError('incomplete/duplicate opportunity checkpoint')
    trade_weeks={r['WeekKey'] for r in diagnostics if r['Status']=='TRADE'}
    if trade_weeks!={r['WeekKey'] for r in job['ledger']}:raise ValueError('trade/no-trade checkpoint mismatch')
    for r in diagnostics+job['ledger']:
        entry=pd.Timestamp(r['WeekKey'])+pd.Timedelta(minutes=p['AdjustedEntryMinute']);exit_time=entry+pd.Timedelta(minutes=p['PlannedHoldingMinutes'])
        if r['CandidateID']!=p['CandidateID'] or r['Symbol']!=p['Symbol'] or pd.Timestamp(r['PlannedEntry'])!=entry or pd.Timestamp(r['PlannedExit'])!=exit_time:raise ValueError('checkpoint schedule identity changed')
    if any(r['Status'] not in ('TRADE','NO_TRADE') for r in diagnostics):raise ValueError('checkpoint availability state invalid')

def finish(out,ledger,points,c):
    out=Path(out)
    if len(points)!=c['candidate_count'] or set(ledger)!={p['CandidateID'] for p in points}:raise ValueError('all 9 candidate jobs required before metrics')
    trades=[];diagnostics=[]
    for p in points:
        job=read_job(out,ledger,p['CandidateID']);validate_job(job,p);trades.extend(job['ledger']);diagnostics.extend(job['diagnostics'])
    trades.sort(key=lambda r:(r['ActualClose'],r['ActualEntry'],r['CandidateID']))
    periods=candidate_periods(points,trades);pairs=all_pairs(points,trades)
    if len(periods)!=c['expected_candidate_period_rows'] or len(pairs)!=c['expected_pairwise_rows']:raise ValueError('all 36 candidate-period / 144 pairwise rows required')
    frames=matrices(points,pairs)
    for name,rows,fields in [('stage8_trade_ledger.csv.gz',trades,LEDGER_FIELDS),('stage8_diagnostics.csv.gz',diagnostics,DIAGNOSTIC_FIELDS),('stage8_candidate_period_metrics.csv.gz',periods,list(periods[0])),('stage8_pairwise_metrics.csv.gz',pairs,list(pairs[0]))]:csv_write(out,name,rows,fields)
    matrix_files=[]
    for name,frame in frames.items():
        relative='matrix_'+name+'.csv';tmp=out/(relative+'.tmp');frame.to_csv(tmp);os.replace(tmp,out/relative);matrix_files.append(relative)
    summary=dict(State=STATE,SourceCandidateCount=17,DeploymentIneligible=8,DeploymentEligible=9,EligibleAUDJPY=1,EligibleGBPJPY=8,PairCount=c['expected_pair_count'],PeriodCount=4,PairwiseRows=len(pairs),CandidatePeriodRows=len(periods),TradeLedgerRows=len(trades),AnalysisLabel=c['analysis_label'],OverlapCorrelationExecuted=True,FamilyConsolidationExecuted=False,PortfolioExecuted=False,LiveChanged=False,NoRanking=True,NoSelection=True,NoRetuning=True,Strategy29PlusAssigned=False)
    atomic_json(out/'stage8_summary.json',summary)
    identity=json.loads((out/'identity.json').read_text());review_identity={k:v for k,v in identity.items() if k!='inputs'};review_identity['M1InputCount']=len(identity['inputs'])
    atomic_json(out/'stage8_review.json',dict(Summary=summary,Identity=review_identity,Next='Chat review of raw period-specific evidence only. Stage9 family consolidation and Stage10 portfolio not executed. No threshold or representative selection.'))
    atomic_json(out/'progress.json',dict(summary,CompletedJobs=len(points),ExpectedJobs=len(points)))
    names=['effective_config.json','stage7_input_audit.json','m1_input_audit.json','deployment_eligibility_audit.json','stage8_deployment_eligibility.json','stage8_candidate_pool.json','progress.json','stage8_candidate_period_metrics.csv.gz','stage8_pairwise_metrics.csv.gz','stage8_diagnostics.csv.gz','stage8_summary.json','stage8_review.json']+matrix_files
    if (out/'stage8_trade_ledger.csv.gz').stat().st_size<=5_000_000:names.append('stage8_trade_ledger.csv.gz')
    tmp=out/'stage8_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:z.write(out/n,n)
    os.replace(tmp,out/'stage8_review.zip');return summary

def full_analysis(data_root,out,expected_sha,run_full=False,confirmed=False):
    code=require_authorization(expected_sha,run_full,confirmed);c=load_config();points,calendar,input_audit=load_input()
    out=Path(out)
    if any(out.resolve().is_relative_to(p.resolve()) or p.resolve().is_relative_to(out.resolve()) for p in (ROOT,Path(data_root))):raise ValueError('output overlaps input/repository')
    runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__)
    if runtime!=c['formal_runtime']:raise ValueError('frozen Python/NumPy/pandas runtime required')
    manifest,paths,audit=audit_inputs(data_root);inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit]
    if len(inputs)!=56:raise ValueError('56 M1 identities required')
    identity=dict(code_sha=code,config_sha256=CONFIG_SHA,eligibility_sha256=c['eligibility_sha256'],candidate_pool_sha256=c['candidate_pool_sha256'],stage7_code_sha=c['stage7_code_sha'],candidate_count=len(points),candidate_ids=[p['CandidateID'] for p in points],inputs=inputs,calendar_sha256=c['calendar']['SHA256'],runtime=runtime,scope='POST_VALIDATION_STRUCTURAL_ANALYSIS')
    ledger=open_store(out,identity)
    if set(ledger)-set(identity['candidate_ids']):raise ValueError('unknown checkpoint CandidateIDs')
    for name,value in [('effective_config.json',c),('stage7_input_audit.json',input_audit),('deployment_eligibility_audit.json',json.loads((ROOT/c['eligibility_audit_file']).read_text()))]:atomic_json(out/name,value)
    for key,name in [('eligibility_file','stage8_deployment_eligibility.json'),('candidate_pool_file','stage8_candidate_pool.json')]:
        # Preserve exact frozen artifact bytes (including their recorded SHA).
        tmp=out/(name+'.tmp');tmp.write_bytes((ROOT/c[key]).read_bytes());os.replace(tmp,out/name)
    atomic_json(out/'progress.json',dict(State='RUNNING_STAGE8',CompletedJobs=len(ledger),ExpectedJobs=len(points)))
    coverage=[];dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(p['Symbol'] for p in points):
        bars=load_analysis(symbol,manifest,paths);coverage.append(availability(bars,symbol))
        pending=[p for p in points if p['Symbol']==symbol and read_job(out,ledger,p['CandidateID']) is None]
        engine=make_engine(bars,symbol) if pending else None;del bars
        for p in pending:
            replay,diag=replay_candidate(p,dates[dates.weekday==p['Weekday']],calendar,engine=engine)
            save_job(out,ledger,p['CandidateID'],evaluate(p,replay,diag))
            atomic_json(out/'progress.json',dict(State='RUNNING_STAGE8',CompletedJobs=len(ledger),ExpectedJobs=len(points)))
            print(f'Stage8 completed jobs: {len(ledger)}/{len(points)}',flush=True)
        del engine
    atomic_json(out/'m1_input_audit.json',dict(Status='PASS',FileCount=56,ManifestSHA256=c['m1_manifest']['ManifestSHA256'],Inputs=inputs,CanonicalCoverage=coverage,OutsideAnalysisRowsPassedToExecutor=0))
    return finish(out,ledger,points,c)
