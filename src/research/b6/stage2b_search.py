"""Colab-only local optimization, fixed range, all evaluations, no Stage3."""
import importlib.util,json,os,platform,subprocess,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from .stage2b_config import ROOT,CONFIG_SHA,load_config,sha
from .stage2b_input import load_input,SCHEMAS,validate_metrics
from .stage2b_selection import select_centers,local_grid,setting_key,final_selection
from .stage2b_metrics import evaluate_candidate
from .stage2a_engine import FastEngine
from .stage2a_search import open_store,save_job,read_job
from .stage1_search import atomic_json
from .stage1_data import audit_inputs,load_discovery
from .execution import START,END

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(x not in '0123456789abcdef' for x in expected_sha):raise ValueError('40-digit Stage2-B Freeze SHA required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=expected_sha:raise ValueError('checkout SHA mismatch')
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT,check=True)
    lock=json.loads((ROOT/'research_inputs/b6/stage2b_release_manifest.json').read_text())
    for name,digest in lock.items():
        if sha(ROOT/name)!=digest:raise ValueError('implementation hash mismatch: '+name)
    return actual

def require_full_authorization(expected_sha,confirmed):
    if not confirmed:raise PermissionError('Chat confirmation required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage2-B full sweep is Google Colab only')
    return verify_release(expected_sha)

def prepare_jobs(candidates,coarse_rows,c):
    groups={a['CandidateID']:[] for a in candidates}
    for row in coarse_rows:
        if row['CandidateID'] not in groups:raise ValueError('unknown Stage1 candidate')
        groups[row['CandidateID']].append(row)
    jobs=[]
    for candidate in candidates:
        centers=select_centers(candidate,groups[candidate['CandidateID']]);grid=local_grid(centers,c)
        jobs.append(dict(candidate=candidate,centers=centers,grid=grid))
    total=sum(len(j['grid']) for j in jobs)
    if total>c['theoretical_max_total']:raise ValueError('total grid bound exceeded')
    return jobs,dict(TheoreticalMax=c['theoretical_max_total'],ImplementationExpectedMax=c['theoretical_max_total'],ActualUniqueConditions=total,Candidates=len(candidates),CandidatesWithCenters=sum(bool(j['centers']) for j in jobs),UniqueCenters=sum(len(j['centers']) for j in jobs),PerCandidate=[dict(CandidateID=j['candidate']['CandidateID'],CenterCount=len(j['centers']),UniqueConditions=len(j['grid'])) for j in jobs],RangeExtension=False)

def csv_write(out,name,rows,columns):
    # Keep parseable JSON in list/dict-valued provenance columns.
    encoded=[{k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows]
    frame=pd.DataFrame(encoded) if encoded else pd.DataFrame(columns=columns)
    p=Path(out)/name;tmp=p.with_suffix(p.suffix+'.tmp')
    frame.to_csv(tmp,index=False,compression='gzip' if name.endswith('.gz') else None);os.replace(tmp,p)

def finish(out,ledger,jobs,c,space):
    out=Path(out);ids={j['candidate']['CandidateID'] for j in jobs}
    if set(ledger)!=ids:raise ValueError('incomplete/unexpected checkpoints')
    tables={k:[] for k in ('results','yearly','diagnostics','stability','neighborhoods')};selected=[];dropped=[];centers=[]
    for job in jobs:
        candidate=job['candidate'];data=read_job(out,ledger,candidate['CandidateID']);grid=job['grid']
        if data.get('centers')!=job['centers'] or data.get('grid')!=grid:raise ValueError('checkpoint center/grid mismatch')
        for kind in ('results','yearly','diagnostics'):
            rows=data[kind];expected=[(x['SL'],x['TP'],y) for x in grid for y in ((2020,2021,2022,2023) if kind=='yearly' else (None,))]
            actual=[(r['SL'],r['TP'],r.get('Year')) for r in rows]
            if actual!=expected or any(any(r[k]!=v for k,v in candidate.items()) for r in rows):raise ValueError('checkpoint setting identity mismatch')
            if kind!='diagnostics':
                for r in rows:validate_metrics({k:None if v=='UNDEFINED' else v for k,v in r.items()})
            tables[kind].extend(rows)
        result=final_selection(candidate,job['centers'],data['results'],data['yearly'],c)
        for k in ('stability','neighborhoods'):tables[k].extend(result[k])
        if result['selected'] is not None:selected.append(result['selected'])
        else:dropped.append(result['dropped'])
        centers.extend(job['centers'])
    actual=len(tables['results'])
    if actual!=space['ActualUniqueConditions'] or len(selected)+len(dropped)!=len(jobs):raise ValueError('completion count mismatch')
    for k,suffix in (('results','all_results'),('yearly','yearly_results'),('diagnostics','diagnostics')):
        csv_write(out,'stage2b_'+suffix+'.csv.gz',tables[k],SCHEMAS['stage2a_'+suffix+'.csv.gz']+['CenterAliases'])
    stability_columns=SCHEMAS['stage2a_all_results.csv.gz']+['PointAvgR','CenterAliases','SourceCenterType','SourceCenterAliases','SourceCenterSL','SourceCenterTP','CenterDistance','SourceCenterDistance','NeighborhoodCount','NeighborhoodPassCount','NeighborhoodPassRate','NeighborhoodMedianAvgR','NeighborhoodMedianTotalR','NeighborhoodWorstMaxDDR','StabilityPass','StabilityFailReasons']
    csv_write(out,'stability_results.csv.gz',tables['stability'],stability_columns)
    csv_write(out,'stability_by_center.csv.gz',tables['neighborhoods'],stability_columns)
    csv_write(out,'dropped_structures.csv',dropped,list(jobs[0]['candidate'])+['Reason'] if jobs else ['CandidateID','Reason'])
    atomic_json(out/'centers.json',centers);atomic_json(out/'stage2b_selected_settings.json',selected)
    summary=dict(State='COMPLETE_STAGE2B_ONLY',Candidates=len(jobs),UniqueCenters=len(centers),TheoreticalMax=c['theoretical_max_total'],ActualUniqueConfigurations=actual,P02Pass=sum(r['Pass'] for r in tables['results']),P02Fail=sum(not r['Pass'] for r in tables['results']),StabilityPass=sum(r['StabilityPass'] for r in tables['stability']),StabilityFail=sum(not r['StabilityPass'] for r in tables['stability']),SelectedStructures=len(selected),DroppedStructures=len(dropped),Stage3Executed=False,ValidationExecuted=False,MonitorExecuted=False,Refill=False)
    atomic_json(out/'stage2b_summary.json',summary)
    atomic_json(out/'progress.json',dict(State=summary['State'],CompletedJobs=len(jobs),ExpectedJobs=len(jobs),CompletedConfigurations=actual,ExpectedConfigurations=actual))
    identity=json.loads((out/'identity.json').read_text());review_identity={k:v for k,v in identity.items() if k!='inputs'};review_identity['M1InputCount']=len(identity['inputs'])
    atomic_json(out/'stage2b_review.json',dict(Summary=summary,Identity=review_identity,InputAudit=json.loads((out/'stage2a_input_audit.json').read_text()),Next='Chat review; SL/TP frozen per selected structure; Stage3 not implemented or executed'))
    names=['identity.json','effective_config.json','stage2a_input_audit.json','search_space.json','progress.json','centers.json','stage2b_all_results.csv.gz','stage2b_yearly_results.csv.gz','stage2b_diagnostics.csv.gz','stability_results.csv.gz','stability_by_center.csv.gz','dropped_structures.csv','stage2b_selected_settings.json','stage2b_summary.json','stage2b_review.json']
    tmp=out/'stage2b_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:
            if name!='identity.json':z.write(out/name,name)
    os.replace(tmp,out/'stage2b_review.zip');return summary

def full_sweep(data_root,out,stage2a_root,stage1_root,expected_sha,confirmed=False):
    code_sha=require_full_authorization(expected_sha,confirmed);c=load_config()
    candidates,coarse_rows,input_audit,prior_identity=load_input(stage2a_root,stage1_root)
    out=Path(out)
    if out.resolve().is_relative_to(ROOT):raise ValueError('output must be outside repository')
    if np.__version__!=c['runtime']['numpy'] or pd.__version__!=c['runtime']['pandas']:raise RuntimeError('frozen numpy/pandas required')
    manifest,paths,audit=audit_inputs(data_root);inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit]
    if len(inputs)!=56 or inputs!=prior_identity['inputs']:raise ValueError('Stage2-A/M1 input mismatch')
    identity=dict(code_sha=code_sha,config_sha256=CONFIG_SHA,stage2a_code_sha=c['stage2a_freeze_sha'],stage2a_config_sha256=c['stage2a_config_sha256'],stage2a_result_sha256=input_audit['RuntimeResultSHA256'],candidate_sha256=c['candidate_sha256'],inputs=inputs,scope='FULL_DISCOVERY_STAGE2B',runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__))
    ledger=open_store(out,identity);jobs,space=prepare_jobs(candidates,coarse_rows,c)
    if set(ledger)-{j['candidate']['CandidateID'] for j in jobs}:raise ValueError('unexpected checkpoint IDs')
    atomic_json(out/'effective_config.json',c);atomic_json(out/'stage2a_input_audit.json',input_audit);atomic_json(out/'search_space.json',space)
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(a['Symbol'] for a in candidates):
        pending=[j for j in jobs if j['candidate']['Symbol']==symbol and read_job(out,ledger,j['candidate']['CandidateID']) is None]
        if not pending:continue
        engine=None
        if any(j['grid'] for j in pending):
            bars=load_discovery(symbol,manifest,paths);engine=FastEngine(bars,symbol);del bars
        for job in pending:
            candidate=job['candidate'];data=evaluate_candidate(engine,candidate,dates[dates.weekday==candidate['Weekday']],job['grid'],c)
            data.update(centers=job['centers'],grid=job['grid']);save_job(out,ledger,candidate['CandidateID'],data)
            completed=sum(len(j['grid']) for j in jobs if j['candidate']['CandidateID'] in ledger)
            atomic_json(out/'progress.json',dict(State='RUNNING',CompletedJobs=len(ledger),ExpectedJobs=len(jobs),CompletedConfigurations=completed,ExpectedConfigurations=space['ActualUniqueConditions']))
            print(f'Stage2-B checkpoints: {len(ledger)}/{len(jobs)}; unique conditions {completed}/{space["ActualUniqueConditions"]}',flush=True)
        del engine
    return finish(out,ledger,jobs,c,space)
