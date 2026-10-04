"""Colab-only R2 assignments then six monetary jobs; no partial result display."""
import importlib.util
import platform
import subprocess
import os
import zipfile
from statistics import median
from pathlib import Path
from decimal import localcontext
from .stage11_config import AJ,GJ,ROOT,INPUT,OUTPUT,STAGE10_SHA,CONFIGS,MODES,PERIODS,COMPARISONS,STATE,MANIFEST_SHA,sha,read,require,load_config
from .stage11_input import load_inputs,portfolio,audit_m1,load_daily,stage10_archive_audit
from .stage11_r2 import source_audit,Assigner
from .stage11_assignment import assign_rows,preflight,assignment_table,distribution
from .stage11_money import simulate,deltas
from .stage11_risk_load import exposure
from .stage10_search import safe,atomic,pack,unpack,csv_write

def verify_release(expected_sha):
    require(len(expected_sha)==40 and all(c in '0123456789abcdef' for c in expected_sha),'exact Stage11 SHA required')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==expected_sha,'Stage11 checkout SHA mismatch')
    require(not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'clean Stage11 checkout required')
    subprocess.run(['git','merge-base','--is-ancestor',STAGE10_SHA,expected_sha],cwd=ROOT,check=True)
    for n,h in read(ROOT/INPUT/'stage11_release_manifest.json').items():require(sha(ROOT/n)==h,'release hash mismatch: '+n)
    source_audit();return load_config()

def require_authorization(code,run_full,confirmed):
    if run_full is not True or confirmed is not True:raise PermissionError('RUN_STAGE11_FULL and Chat confirmation required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('formal Stage11 is Google Colab only')
    c=verify_release(code)
    import numpy as np
    import pandas as pd
    runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__)
    require(runtime==c['FormalRuntime'],'frozen runtime mismatch')
    return c,runtime

def job_specs():return [(f'{mi}-{ci}',mode,name) for mi,mode in enumerate(MODES) for ci,name in enumerate(CONFIGS)]

def run_job(rows,mode,name):
    with localcontext() as ctx:
        ctx.prec=40
        own=portfolio(rows,name);logs,weekly,stats=simulate(own,mode)
        tag=dict(MoneyMode=mode,PortfolioConfig=name)
        results=[];concurrency=[];overlap=[]
        for p in MODES[mode][1]:
            con,ov=exposure(own,*PERIODS[p])
            results.append(dict(tag,Period=p,**stats[p],**con));concurrency.append(dict(tag,Period=p,**con))
            overlap.extend(dict(tag,Period=p,**r) for r in ov)
        return dict(PeriodResults=results,Weekly=[dict(tag,**r) for r in weekly],Concurrency=concurrency,Overlap=overlap,
            Diagnostics=[dict(tag,Status='COMPLETE',Trades=len(logs),GlobalR2Applied=True,R2TradeFilter=False,BrokerMarginCalculated=False,AdoptionDecision='NOT_MADE',RiskChoice='NOT_MADE')])

def validate_job(job,mode,name):
    expected=list(MODES[mode][1])
    require([r['Period'] for r in job['PeriodResults']]==expected,'incomplete periods')
    for table in job.values():
        for r in table:require((r['MoneyMode'],r['PortfolioConfig'])==(mode,name),'job identity mismatch')
    require(len(job['Concurrency'])==len(expected) and len(job['Overlap'])==3*len(expected) and len(job['Diagnostics'])==1,'incomplete outputs')

def incremental(results):
    lookup={(r['MoneyMode'],r['Period'],r['PortfolioConfig']):r for r in results};out=[]
    with localcontext() as ctx:
        ctx.prec=40
        for mode in MODES:
            for p in MODES[mode][1]:
                group=[lookup[mode,p,n] for n in CONFIGS]
                for label,(a,b) in COMPARISONS.items():out.append(dict(MoneyMode=mode,Period=p,Comparison=label,FromConfig=group[b]['PortfolioConfig'],ToConfig=group[a]['PortfolioConfig'],**deltas(group[a],group[b])))
    return out

def finish(out,checkpoints,identity,assigned,assignment_audit):
    out=Path(out)
    require(assignment_audit['Status']=='PASS' and assignment_audit['Assignments']==9760,'all assignments required')
    require(set(checkpoints)=={s[0] for s in job_specs()},'all six money jobs required')
    tables={k:[] for k in ('PeriodResults','Weekly','Concurrency','Overlap','Diagnostics')}
    for key,mode,name in job_specs():
        p=out/'shards'/f'{key}.json';require(sha(p)==checkpoints[key],'checkpoint changed')
        job=unpack(read(p));validate_job(job,mode,name)
        for k in tables:tables[k].extend(job[k])
    comparison=incremental(tables['PeriodResults'])
    require(len(tables['PeriodResults'])==len(comparison)==24,'24 period/incremental rows required')
    keys=('MoneyMode','PortfolioConfig','TradingWeekStart','Trades','BaselineTrades','GJTrades','AJTrades','MeanAppliedRiskPct','MaxAppliedRiskPct','GrossRiskAllocationPct','MaxConcurrentPositions','MaxConcurrentRiskPct')
    outputs={'r2_assignments':assignment_table(assigned),'b6_r2_assignments':assignment_table([r for r in assigned if r['Source']=='B6']),
        'r2_distribution':distribution(assigned),'portfolio_period_results':tables['PeriodResults'],'incremental_comparison':comparison,
        'weekly':tables['Weekly'],'risk_load':[{k:r[k] for k in keys} for r in tables['Weekly']],
        'concurrency':tables['Concurrency'],'b6_overlap':tables['Overlap'],'diagnostics':tables['Diagnostics']}
    for name,rows in outputs.items():csv_write(out/f'stage11_{name}.csv.gz',rows)
    summary=dict(State=STATE,CurrentStrategyCount=27,B6CandidateCount=2,PortfolioConfigs=3,MoneyModes=2,MoneyJobs=6,CompletedJobs=6,
        PeriodResultRows=24,IncrementalRows=24,R2AssignmentsGenerated=True,GlobalR2Applied=True,R2TradeFilter=False,
        AJOnlyConfigurationExists=False,RiskAllocationDecided=False,LiveChanged=False,StrategyNumberingAssigned=False,
        EAConstrainedStatus='NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS',NoAdoptionThreshold=True,NoRiskSelection=True)
    summary['B6AppliedRiskSummary']={}
    for cid in (GJ,AJ):
        own=[r for r in assigned if r['PortfolioComponentKey']==cid];rs=[r['AppliedRiskPercent'] for r in own]
        summary['B6AppliedRiskSummary'][cid]=dict(Trades=len(rs),Mean=sum(rs)/len(rs),Median=median(rs),Min=min(rs),Max=max(rs),QuintileCounts={q:sum(r['Quintile']==q for r in own) for q in ('Q1','Q2','Q3','Q4','Q5','FALLBACK')})
    atomic(out/'stage11_summary.json',summary);atomic(out/'progress.json',summary)
    names=['identity.json','effective_config.json','stage10_input_audit.json','r2_source_audit.json','m1_input_audit.json','trade_input_audit.json','r2_assignment_audit.json','progress.json','stage11_summary.json',*sorted(f'stage11_{n}.csv.gz' for n in outputs)]
    atomic(out/'stage11_review.json',dict(Summary=summary,Identity=identity,OutputSHA256={n:sha(out/n) for n in names},Interpretation='theoretical uncapped; post-selection diagnostic; no adoption or risk decision'))
    tmp=out/'stage11_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for n in names+['stage11_review.json']:
            info=zipfile.ZipInfo(n,date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(out/n).read_bytes())
    os.replace(tmp,out/'stage11_review.zip');return safe(summary)

def complete_summary(out):
    out=Path(out);s=read(out/'stage11_summary.json');r=read(out/'stage11_review.json')
    require(s==read(out/'progress.json')==r['Summary'] and s['State']==STATE and s['CompletedJobs']==6 and s['R2AssignmentsGenerated'] is True,'partial display rejected')
    require(s['PeriodResultRows']==s['IncrementalRows']==24,'incomplete result rows')
    for n,h in r['OutputSHA256'].items():require(Path(n).name==n and sha(out/n)==h,'output hash mismatch')
    require(read(out/'r2_assignment_audit.json')['Assignments']==9760,'incomplete assignments')
    return s

def full_simulation(baseline_path,b6_ledger_path,m1_root,out,expected_sha,run_full=False,confirmed=False,stage10_archive=None):
    c,runtime=require_authorization(expected_sha,run_full,confirmed)
    out=Path(out).resolve()
    for p in (ROOT,Path(baseline_path),Path(b6_ledger_path),Path(m1_root)):
        p=p.resolve();require(not(out.is_relative_to(p) or p.is_relative_to(out)),'output overlaps repository/input')
    rows,trade_audit=load_inputs(baseline_path,b6_ledger_path)
    manifest,paths,m1_audit=audit_m1(m1_root,coverage=False)
    src=source_audit();s10=stage10_archive_audit(stage10_archive or c['Stage10Archive'])
    base=dict(CodeSHA=expected_sha,ConfigSHA256=sha(ROOT/INPUT/'stage11_config.json'),ReleaseManifestSHA256=sha(ROOT/INPUT/'stage11_release_manifest.json'),
        SourceSpecSHA256=sha(ROOT/INPUT/'stage11_source_spec.json'),Runtime=runtime,InputArtifactSHA256=c['InputArtifactSHA256'],
        BaselineSHA256=trade_audit['BaselineSHA256'],B6LedgerSHA256=trade_audit['B6LedgerSHA256'],M1ManifestSHA256=MANIFEST_SHA,Sources=src['Sources'],Stage10ArchiveAudit=s10,Scope='GLOBAL_R2_THREE_PORTFOLIOS_SIX_JOBS')
    out.mkdir(parents=True,exist_ok=True)
    store=out/'assignment_checkpoint.json'
    if (out/'identity.json').exists():
        identity=read(out/'identity.json');require(identity['Base']==safe(base),'resume identity mismatch')
        require(sha(store)==identity['AssignmentCheckpointSHA256'],'assignment checkpoint mismatch')
        assigned=unpack(read(store))
    else:
        require(not list(out.iterdir()),'fresh output or verified resume required')
        print('Stage11 input audit complete; generating assignments',flush=True)
        daily={symbol:load_daily(symbol,manifest,paths) for symbol in dict.fromkeys(manifest.Symbol)}
        assigned=assign_rows(rows,Assigner(daily,MANIFEST_SHA))
        preflight(rows,assigned)
        atomic(store,pack(assigned))
        identity=dict(Base=base,AssignmentCheckpointSHA256=sha(store));atomic(out/'identity.json',identity)
    audit=preflight(rows,assigned)
    for n,v in [('effective_config.json',c),('stage10_input_audit.json',s10),('r2_source_audit.json',src),('m1_input_audit.json',m1_audit),('trade_input_audit.json',trade_audit),('r2_assignment_audit.json',audit)]:atomic(out/n,v)
    checkpoints=read(out/'checkpoints.json') if (out/'checkpoints.json').exists() else {}
    require(set(checkpoints)<={s[0] for s in job_specs()},'unknown checkpoint job')
    for key,h in checkpoints.items():require(sha(out/'shards'/f'{key}.json')==h,'checkpoint hash mismatch')
    for key,mode,name in job_specs():
        if key not in checkpoints:
            job=run_job(assigned,mode,name);validate_job(job,mode,name)
            p=out/'shards'/f'{key}.json';atomic(p,pack(job));checkpoints[key]=sha(p);atomic(out/'checkpoints.json',checkpoints)
        atomic(out/'progress.json',dict(State='RUNNING_STAGE11',AssignmentsComplete=True,CompletedJobs=len(checkpoints),ExpectedJobs=6))
        print(f'Stage11 completed money jobs: {len(checkpoints)}/6',flush=True)
    return finish(out,checkpoints,identity,assigned,audit)
