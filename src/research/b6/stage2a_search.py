"""Colab-only Stage2-A; fixed input order, all conditions, no Stage2-B selector."""
import hashlib,importlib.util,json,os,platform,subprocess,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from .stage2a_config import ROOT,CONFIG_SHA,load_config,load_candidates,settings,sha
from .stage2a_engine import FastEngine,fast_replay
from .stage2a_metrics import summarize
from .stage1_data import audit_inputs,load_discovery
from .stage1_search import atomic_json,json_safe
from .execution import START,END

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(x not in '0123456789abcdef' for x in expected_sha):raise ValueError('40-digit Stage2-A Freeze SHA required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=expected_sha:raise ValueError('checkout SHA mismatch')
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT,check=True)
    lock=json.loads((ROOT/'research_inputs/b6/stage2a_release_manifest.json').read_text())
    for name,digest in lock.items():
        if sha(ROOT/name)!=digest:raise ValueError('implementation hash mismatch: '+name)
    return actual

def require_full_authorization(expected_sha,confirmed):
    if not confirmed:raise PermissionError('Chat confirmation required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Stage2-A full sweep is Google Colab only')
    return verify_release(expected_sha)

def open_store(out,identity):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);p=out/'identity.json'
    if p.exists():
        if json.loads(p.read_text())!=json_safe(identity):raise ValueError('resume identity mismatch; use a fresh directory')
    elif any(out.iterdir()):raise ValueError('output exists without identity; use a fresh directory')
    else:atomic_json(p,identity)
    (out/'shards').mkdir(exist_ok=True)
    ledger=out/'checkpoints.json'
    if not ledger.exists():atomic_json(ledger,{})
    return json.loads(ledger.read_text())

def read_job(out,ledger,cid):
    if cid not in ledger:return None
    p=Path(out)/'shards'/(cid+'.json')
    if not p.exists() or sha(p)!=ledger[cid]:raise ValueError('checkpoint corruption: '+cid)
    return json.loads(p.read_text())

def save_job(out,ledger,cid,data):
    p=Path(out)/'shards'/(cid+'.json');atomic_json(p,data);ledger[cid]=sha(p)
    atomic_json(Path(out)/'checkpoints.json',ledger)

def finish(out,ledger,candidates,c):
    out=Path(out);tables={k:[] for k in ('results','yearly','diagnostics')}
    if set(ledger)!={x['CandidateID'] for x in candidates}:raise ValueError('incomplete/unexpected candidate checkpoints')
    for candidate in candidates:
        job=read_job(out,ledger,candidate['CandidateID']);grid=settings(candidate,c)
        for k in tables:
            rows=job[k];expected=len(grid)*(4 if k=='yearly' else 1)
            if len(rows)!=expected:raise ValueError('incomplete condition rows')
            expected_keys=[(s['SL'],s['TP'],y) for s in grid for y in ((2020,2021,2022,2023) if k=='yearly' else (None,))]
            actual_keys=[(r['SL'],r['TP'],r.get('Year')) for r in rows]
            if actual_keys!=expected_keys or any(any(r[n]!=v for n,v in candidate.items()) for r in rows):raise ValueError('checkpoint condition identity mismatch')
            tables[k].extend(rows)
    if len(tables['results'])!=c['expected_configurations']:raise ValueError('1500 condition completion required')
    for k,name in (('results','all_results'),('yearly','yearly_results'),('diagnostics','diagnostics')):
        p=out/f'stage2a_{name}.csv.gz';tmp=p.with_suffix('.tmp')
        pd.DataFrame(tables[k]).to_csv(tmp,index=False,compression='gzip');os.replace(tmp,p)
    summary=dict(State='COMPLETE_STAGE2A_ONLY',Candidates=len(candidates),Configurations=len(tables['results']),PassCount=sum(r['Pass'] for r in tables['results']),FailCount=sum(not r['Pass'] for r in tables['results']),FormalRanking=False,Stage2BCentersSelected=False,ValidationExecuted=False,MonitorExecuted=False)
    atomic_json(out/'stage2a_summary.json',summary)
    atomic_json(out/'progress.json',dict(CompletedJobs=len(candidates),ExpectedJobs=len(candidates),CompletedConfigurations=len(tables['results']),State=summary['State']))
    identity=json.loads((out/'identity.json').read_text())
    # Review bundle contains counts/digests, never duplicates local M1 file metadata.
    review_identity={k:v for k,v in identity.items() if k!='inputs'}
    review_identity['M1InputCount']=len(identity['inputs'])
    review_identity['M1IdentitySHA256']=hashlib.sha256(json.dumps(identity['inputs'],sort_keys=True).encode()).hexdigest()
    atomic_json(out/'stage2a_review.json',dict(Summary=summary,Identity=review_identity,CandidateInputAudit=json.loads((out/'candidate_input_audit.json').read_text()),Next='Chat reviews Stage2-A before defining N06b; no centers selected'))
    names=['stage2a_review.json','stage2a_summary.json','effective_config.json','search_space.json','progress.json','stage2a_all_results.csv.gz','stage2a_yearly_results.csv.gz','stage2a_diagnostics.csv.gz']
    tmp=out/'stage2a_review.zip.tmp'
    with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:z.write(out/name,name)
    os.replace(tmp,out/'stage2a_review.zip')
    return summary

def full_sweep(data_root,out,candidate_path,identity_path,effective_config_path,expected_sha,confirmed=False):
    code_sha=require_full_authorization(expected_sha,confirmed);c=load_config()
    candidates,candidate_audit=load_candidates(candidate_path,identity_path,effective_config_path)
    out=Path(out)
    if out.resolve().is_relative_to(ROOT):raise ValueError('output must be outside repository')
    if np.__version__!=c['runtime']['numpy'] or pd.__version__!=c['runtime']['pandas']:raise RuntimeError('frozen numpy/pandas versions required')
    manifest,paths,audit=audit_inputs(data_root)
    if len(audit)!=56:raise ValueError('56 audited inputs required')
    identity=dict(code_sha=code_sha,config_sha256=CONFIG_SHA,candidate_sha256=c['candidate_sha256'],stage1_code_sha=c['stage1_freeze_sha'],stage1_config_sha256=c['stage1_effective_config_sha256'],inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit],scope='FULL_DISCOVERY_STAGE2A',runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__))
    ledger=open_store(out,identity)
    if set(ledger)-{a['CandidateID'] for a in candidates}:raise ValueError('unexpected checkpoint IDs')
    atomic_json(out/'effective_config.json',c);atomic_json(out/'candidate_input_audit.json',candidate_audit)
    atomic_json(out/'search_space.json',dict(Candidates=50,Configurations=sum(len(settings(a,c)) for a in candidates),PerPairGrid={s:settings({'Symbol':s},c) for s in c['sl_pips']},FormalRanking=False,EarlyGatePruning=False))
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D')
    for symbol in dict.fromkeys(a['Symbol'] for a in candidates):
        pending=[a for a in candidates if a['Symbol']==symbol and read_job(out,ledger,a['CandidateID']) is None]
        if not pending:continue
        bars=load_discovery(symbol,manifest,paths);engine=FastEngine(bars,symbol);del bars
        for candidate in pending:
            grid=settings(candidate,c);replay=fast_replay(engine,candidate,dates[dates.weekday==candidate['Weekday']],grid)
            data=summarize(candidate,grid,replay,c['gate']);save_job(out,ledger,candidate['CandidateID'],data)
            atomic_json(out/'progress.json',dict(CompletedJobs=len(ledger),ExpectedJobs=50,CompletedConfigurations=len(ledger)*30,State='RUNNING'))
            print(f'Stage2-A checkpoints: {len(ledger)}/50',flush=True)
        del engine
    return finish(out,ledger,candidates,c)
