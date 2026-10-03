"""Colab-authorized fixed 32-job simulation, resumable by exact identity only."""
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import os
import platform
import subprocess
import zipfile
from datetime import datetime
from decimal import Decimal as D, localcontext
from pathlib import Path
from .stage10_config import ROOT,INPUT,OUTPUT,STAGE9_SHA,FINAL_SHA,CONFIGS,RISKS,MODES,PERIODS,STATE,load_config,read,sha,require
from .stage10_input import load_inputs,portfolio
from .stage10_money import simulate,deltas
from .stage10_risk_load import exposure


def safe(value):
    if isinstance(value,D):
        require(value.is_finite(),'nonfinite output');return str(value)
    if isinstance(value,datetime):return value.isoformat(sep=' ')
    if value is None:return 'UNDEFINED'
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [safe(v) for v in value]
    return value


def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(safe(value),ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,path)


def pack(v):
    if isinstance(v,D):return {'$decimal':str(v)}
    if isinstance(v,datetime):return {'$datetime':v.isoformat()}
    if isinstance(v,dict):return {k:pack(x) for k,x in v.items()}
    if isinstance(v,list):return [pack(x) for x in v]
    if v is None:return {'$none':True}
    return v


def unpack(v):
    if isinstance(v,dict):
        if set(v)=={'$decimal'}:return D(v['$decimal'])
        if set(v)=={'$datetime'}:return datetime.fromisoformat(v['$datetime'])
        if v=={'$none':True}:return None
        return {k:unpack(x) for k,x in v.items()}
    if isinstance(v,list):return [unpack(x) for x in v]
    return v


def csv_write(path,rows):
    require(bool(rows),'empty output table')
    fields=list(dict.fromkeys(k for row in rows for k in row))
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=fields,lineterminator='\n');writer.writeheader()
    writer.writerows(safe(rows))
    data=gzip.compress(buf.getvalue().encode('utf-8'),mtime=0)
    p=Path(path);tmp=p.with_name(p.name+'.tmp');tmp.write_bytes(data);os.replace(tmp,p)


def verify_release(expected_sha):
    require(len(expected_sha)==40 and all(c in '0123456789abcdef' for c in expected_sha),'exact Stage10 SHA required')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==expected_sha,'Stage10 checkout SHA mismatch')
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'clean Stage10 checkout required')
    subprocess.run(['git','merge-base','--is-ancestor',STAGE9_SHA,expected_sha],cwd=ROOT,check=True)
    for n,h in read(ROOT/INPUT/'stage10_release_manifest.json').items():require(sha(ROOT/n)==h,'release hash mismatch: '+n)
    return load_config()


def require_authorization(code,run_full,confirmed):
    if run_full is not True or confirmed is not True:raise PermissionError('RUN_STAGE10_FULL and Chat confirmation required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('formal Stage10 is Google Colab only')
    c=verify_release(code)
    import numpy as np
    import pandas as pd
    runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__)
    require(runtime==c['FormalRuntime'],'frozen runtime mismatch')
    return c,runtime


def job_specs():
    return [(f'{mi}-{ri}-{ci}',mode,risk,name) for mi,mode in enumerate(MODES)
            for ri,risk in enumerate(RISKS) for ci,name in enumerate(CONFIGS)]


def run_job(rows,mode,risk,name):
    with localcontext() as ctx:
        ctx.prec=40
        own=portfolio(rows,name);logs,weekly,stats=simulate(own,risk,mode)
        tag=dict(MoneyMode=mode,RiskPct=risk,PortfolioConfig=name)
        results=[];concurrency=[];overlap=[]
        for period in MODES[mode][1]:
            con,ov=exposure(own,risk,*PERIODS[period])
            results.append(dict(tag,Period=period,**stats[period],**con))
            concurrency.append(dict(tag,Period=period,**con))
            overlap.extend(dict(tag,Period=period,**r) for r in ov)
        return dict(PeriodResults=results,Weekly=[dict(tag,**r) for r in weekly],Concurrency=concurrency,
            Overlap=overlap,Diagnostics=[dict(tag,Status='COMPLETE',Trades=len(logs),GlobalR2Applied=False,
                BrokerMarginCalculated=False,AdoptionDecision='NOT_MADE',RiskChoice='NOT_MADE')])


def open_store(out,identity):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    p=out/'identity.json'
    if p.exists():require(read(p)==safe(identity),'resume identity mismatch')
    else:
        require(not list(out.iterdir()),'fresh output or valid resume identity required');atomic(p,identity)
    manifest=read(out/'checkpoints.json') if (out/'checkpoints.json').exists() else {}
    require(set(manifest)<={s[0] for s in job_specs()},'unknown checkpoint job')
    for key,h in manifest.items():require(sha(out/'shards'/f'{key}.json')==h,'checkpoint hash mismatch')
    return manifest


def validate_job(job,mode,risk,name):
    expected=list(MODES[mode][1]);rows=job['PeriodResults']
    require([r['Period'] for r in rows]==expected,'incomplete job periods')
    for table in job.values():
        for r in table:require((r['MoneyMode'],r['RiskPct'],r['PortfolioConfig'])==(mode,risk,name),'job identity mismatch')
    require(len(job['Concurrency'])==len(expected) and len(job['Overlap'])==3*len(expected) and len(job['Diagnostics'])==1,'incomplete job outputs')


def finish(out,checkpoints,identity):
    out=Path(out);require(set(checkpoints)=={s[0] for s in job_specs()},'all 32 jobs required before formal results')
    tables={k:[] for k in ('PeriodResults','Weekly','Concurrency','Overlap','Diagnostics')}
    for key,mode,risk,name in job_specs():
        p=out/'shards'/f'{key}.json';require(sha(p)==checkpoints[key],'checkpoint changed')
        job=unpack(read(p));validate_job(job,mode,risk,name)
        for k in tables:tables[k].extend(job[k])
    require(len(tables['PeriodResults'])==128,'128 period rows required')
    lookup={(r['MoneyMode'],r['RiskPct'],r['Period'],r['PortfolioConfig']):r for r in tables['PeriodResults']}
    comparison=[];evidence=[]
    with localcontext() as ctx:
        ctx.prec=40
        for mode in MODES:
            for risk in RISKS:
                for period in MODES[mode][1]:
                    group=[lookup[mode,risk,period,name] for name in CONFIGS]
                    p0,p1,p2,p3=group
                    for r in group:r['AddedTradesVsP0']=r['Trades']-p0['Trades']
                    for row in group[1:]:comparison.append(dict(MoneyMode=mode,RiskPct=risk,Period=period,PortfolioConfig=row['PortfolioConfig'],**deltas(row,p0)))
                    evidence.append(dict(MoneyMode=mode,RiskPct=risk,Period=period,Comparison='P3_MINUS_P0_PRIMARY',
                        **deltas(p3,p0),FinalCapitalInteraction=(p3['FinalCapital']-p0['FinalCapital'])-((p1['FinalCapital']-p0['FinalCapital'])+(p2['FinalCapital']-p0['FinalCapital'])),
                        AdoptionDecision='NOT_MADE',RiskAllocationDecided=False))
    riskload=[{k:r[k] for k in ('MoneyMode','RiskPct','PortfolioConfig','TradingWeekStart','Trades','BaselineTrades','B6Trades','GrossRiskAllocationPct')} for r in tables['Weekly']]
    outputs={'portfolio_period_results':tables['PeriodResults'],'risk_comparison':comparison,'weekly':tables['Weekly'],
        'risk_load':riskload,'concurrency':tables['Concurrency'],'b6_overlap':tables['Overlap'],
        'decision_evidence':evidence,'diagnostics':tables['Diagnostics']}
    for name,rows in outputs.items():csv_write(out/f'stage10_{name}.csv.gz',rows)
    summary=dict(State=STATE,BaselineIdentityResolved=True,CurrentStrategyCount=27,
        GlobalR2Identity='R2_GLOBAL / R2_MODERATE; not applied by latest user instruction',GlobalR2Applied=False,
        FinalB6CandidateCount=2,PortfolioConfigs=4,RiskCount=4,MoneyModes=2,CompletedJobs=32,ExpectedJobs=32,
        PeriodResultRows=128,PortfolioSimulationExecuted=True,BrokerConstrainedExecuted=False,
        EAConstrainedStatus='NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS',RiskAllocationDecided=False,
        LiveChanged=False,StrategyNumberingAssigned=False,NoAdoptionThreshold=True,NoRiskSelection=True)
    hashes={p.name:sha(p) for p in out.glob('stage10_*.csv.gz')}
    atomic(out/'stage10_summary.json',summary)
    atomic(out/'stage10_review.json',dict(Summary=summary,Identity=identity,OutputSHA256=hashes,
        Interpretation='post-selection diagnostic; theoretical uncapped; no live adoption or risk selection'))
    atomic(out/'progress.json',summary)
    names=['identity.json','effective_config.json','stage9_input_audit.json','portfolio_baseline_audit.json',
        'input_trade_ledger_audit.json','progress.json','stage10_summary.json','stage10_review.json',*sorted(hashes)]
    tmp=out/'stage10_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names:
            info=zipfile.ZipInfo(n,date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(out/n).read_bytes())
    os.replace(tmp,out/'stage10_review.zip')
    return summary


def complete_summary(out):
    out=Path(out);summary=read(out/'stage10_summary.json');progress=read(out/'progress.json')
    require(summary==progress and summary['State']==STATE and summary['CompletedJobs']==summary['ExpectedJobs']==32 and summary['PeriodResultRows']==128,'partial formal display rejected')
    review=read(out/'stage10_review.json');require(review['Summary']==summary,'review summary mismatch')
    for n,h in review['OutputSHA256'].items():require(sha(out/n)==h,'output hash mismatch')
    return summary


def full_simulation(baseline_path,b6_ledger_path,out,expected_sha,run_full=False,confirmed=False):
    c,runtime=require_authorization(expected_sha,run_full,confirmed)
    out=Path(out).resolve()
    require(not (out.is_relative_to(ROOT.resolve()) or ROOT.resolve().is_relative_to(out)),'output overlaps repository')
    for p in (Path(baseline_path).resolve(),Path(b6_ledger_path).resolve()):
        require(not p.is_relative_to(out),'output overlaps formal input')
    rows,audit=load_inputs(baseline_path,b6_ledger_path)
    identity=dict(CodeSHA=expected_sha,ConfigSHA256=sha(ROOT/INPUT/'stage10_config.json'),
        BaselineArtifactSHA256=c['BaselineArtifactSHA256'],Stage9FinalCandidateSHA256=FINAL_SHA,
        BaselineLedgerSHA256=audit['BaselineSHA256'],B6LedgerSHA256=audit['B6LedgerSHA256'],
        Runtime=runtime,GlobalR2Applied=False,Scope='FIXED_RISK_INCREMENTAL_PORTFOLIO_32_JOBS')
    checkpoints=open_store(out,identity)
    for name,value in [('effective_config.json',c),('input_trade_ledger_audit.json',audit),
        ('stage9_input_audit.json',read(ROOT/OUTPUT/'stage9_input_audit.json')),
        ('portfolio_baseline_audit.json',read(ROOT/INPUT/'stage10_portfolio_baseline.json'))]:atomic(out/name,value)
    atomic(out/'progress.json',dict(State='RUNNING_STAGE10',CompletedJobs=len(checkpoints),ExpectedJobs=32))
    for key,mode,risk,name in job_specs():
        if key not in checkpoints:
            job=run_job(rows,mode,risk,name);validate_job(job,mode,risk,name)
            file=out/'shards'/f'{key}.json';atomic(file,pack(job));checkpoints[key]=sha(file);atomic(out/'checkpoints.json',checkpoints)
        atomic(out/'progress.json',dict(State='RUNNING_STAGE10',CompletedJobs=len(checkpoints),ExpectedJobs=32))
        print(f'Stage10 completed jobs: {len(checkpoints)}/32',flush=True)
    return finish(out,checkpoints,identity)
