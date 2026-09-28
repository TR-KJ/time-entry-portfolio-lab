"""Stage1 full sweep entry point: Colab only, explicit confirmed immutable SHA.

No Validation/Monitor entry point exists. No real-data full sweep was run in
Work. Compressed metric shards retain all five SLs, including failed SLs.
"""
import argparse,csv,gzip,hashlib,importlib.util,json,os,platform,sqlite3,subprocess,sys
from pathlib import Path
import numpy as np
import pandas as pd
from .stage1_config import load_config,search_space,ROOT,CONFIG_SHA
from .stage1_engine import FastEngine,STATUS
from .stage1_data import audit_inputs,load_discovery
from .execution import START,END


def json_safe(x):
    if isinstance(x,dict):return {str(k):json_safe(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [json_safe(v) for v in x]
    if isinstance(x,np.generic):x=x.item()
    if isinstance(x,float) and not np.isfinite(x):return 'INF' if x==np.inf else '-INF' if x==-np.inf else 'UNDEFINED'
    return x

def atomic_json(path,value):
    p=Path(path);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(json_safe(value),ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(c not in '0123456789abcdef' for c in expected_sha):raise ValueError('full Freeze SHA required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=expected_sha:raise ValueError('checkout SHA mismatch')
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT,check=True)
    lock=json.loads((ROOT/'research_inputs/b6/stage1_release_manifest.json').read_text())
    for name,digest in lock.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('implementation hash mismatch: '+name)
    return actual

def require_full_authorization(expected_sha,confirmed):
    if not confirmed:raise PermissionError('Chat confirmation flag required')
    try:colab=importlib.util.find_spec('google.colab') is not None
    except ModuleNotFoundError:colab=False
    if not colab:raise PermissionError('Full sweep is restricted to Google Colab')
    return verify_release(expected_sha)

def open_store(out,identity):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'shards').mkdir(exist_ok=True)
    identity=json_safe(identity);file=out/'identity.json'
    if file.exists():
        if json.loads(file.read_text())!=identity:raise ValueError('resume identity mismatch; choose a fresh output directory')
    else:
        if (out/'stage1.sqlite').exists():raise ValueError('database without identity')
        atomic_json(file,identity)
    db=sqlite3.connect(out/'stage1.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, sha TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS candidates (id TEXT PRIMARY KEY, shard TEXT, symbol TEXT, direction TEXT, weekday INTEGER, entry INTEGER, hold INTEGER, offset INTEGER, exit INTEGER, avg REAL, passes INTEGER, total REAL, dd REAL, wi INTEGER, hi INTEGER)')
    db.execute('CREATE INDEX IF NOT EXISTS by_shard ON candidates(shard)');db.commit();return db

def done(db,out,job):
    row=db.execute('SELECT sha FROM jobs WHERE id=?',(job,)).fetchone()
    if row is None:return False
    p=Path(out)/'shards'/(job+'.npz')
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=row[0]:raise ValueError('checkpoint shard corruption: '+job)
    return True

def job_arrays(engine,symbol,direction,entry,dates,holds,c):
    sls=c['sl_pips'][symbol];prepared=engine.prepare(dates,entry,direction=='L',sls)
    packed={};rows=[]
    for wi,w in enumerate(c['weekdays']):
        mask=dates.weekday==w
        # Reuse first-hit queries across all five weekdays and 283 exits.
        from .stage1_engine import Prepared
        p=Prepared(engine,dates[mask],prepared.entries[mask],prepared.price[mask],prepared.stops[:,mask],prepared.first_hit[:,mask],prepared.sls,prepared.sign)
        batch=p.evaluate(holds);summaries=batch.summary(c['gate'])
        for si,m in enumerate(summaries):
            m['SLHits']=batch.sl_hit[si].sum(axis=0)
            m['TimeExits']=((batch.status==0)&~batch.sl_hit[si]).sum(axis=0)
            m['ExitBarFirstHits']=(batch.sl_hit[si]&(batch.close[si]==batch.exits)).sum(axis=0)
            m['FallbackTrades']=((batch.status==0)&(batch.exits>batch.scheduled)).sum(axis=0)
            m['MissingPathTrades']=((batch.status==0)&(batch.missing>0)).sum(axis=0)
        for key in summaries[0]:packed.setdefault(key,[]).append(np.stack([m[key] for m in summaries]))
        for code,name in enumerate(STATUS):packed.setdefault('Opportunities_'+name,[]).append((batch.status==code).sum(axis=0))
        avg=np.median(np.stack([m['AvgR'] for m in summaries]),axis=0)
        total=np.median(np.stack([m['TotalR'] for m in summaries]),axis=0)
        dd=np.max(np.stack([m['MaxDDR'] for m in summaries]),axis=0)
        passes=np.stack([m['Pass'] for m in summaries]).sum(axis=0)
        for hi in np.flatnonzero(passes>=c['gate']['min_passing_sl']):
            h=int(holds[hi]);x=entry+h;cid=f'B6-{symbol}-{direction}-W{w}-E{entry:04d}-H{h:04d}'
            if not all(np.isfinite(v[hi]) for v in (avg,total,dd)):raise ValueError('nonfinite ranking key')
            rows.append((cid,symbol,direction,int(w),int(entry),h,x//1440,x%1440,float(avg[hi]),int(passes[hi]),float(total[hi]),float(dd[hi]),wi,int(hi)))
    packed={k:np.stack(v) for k,v in packed.items()}
    packed.update(holds=np.asarray(holds),SL=np.asarray(sls),weekdays=np.asarray(c['weekdays']))
    return packed,rows

def save_job(db,out,job,arrays,rows):
    path=Path(out)/'shards'/(job+'.npz');tmp=path.with_suffix('.tmp')
    with tmp.open('wb') as f:np.savez_compressed(f,**arrays)
    os.replace(tmp,path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    with db:
        db.execute('DELETE FROM candidates WHERE shard=?',(job,))
        db.executemany('INSERT INTO candidates VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',[(r[0],job,*r[1:]) for r in rows])
        db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?)',(job,digest))

def finish(db,out,c):
    """External global ordering and direct representative assignment; no chaining."""
    out=Path(out);reps=[];seen=0;counts={k:0 for k in ('REPRESENTATIVE','SUPPRESSED','OUTSIDE_TOP50')}
    query='SELECT * FROM candidates ORDER BY avg DESC,passes DESC,total DESC,dd ASC,symbol ASC,direction ASC,weekday ASC,entry ASC,offset ASC,exit ASC'
    tmp=out/'assignments.csv.gz.tmp'
    with gzip.open(tmp,'wt',newline='') as f:
        writer=csv.writer(f);writer.writerow(['CandidateID','GlobalRank','Status','RepresentativeID','EntryDistance','ExitDistance','HoldingDifference'])
        for row in db.execute(query):
            seen+=1;cid,shard,symbol,direction,w,e,h,offset,x,*rest=row;match=None;dist=None
            for rep in reps:
                if (symbol,direction,w,offset)!=(rep[2],rep[3],rep[4],rep[7]):continue
                de=min(abs(e-rep[5]),1440-abs(e-rep[5]));dx=min(abs(x-rep[8]),1440-abs(x-rep[8]));dh=abs(h-rep[6]);cl=c['clustering']
                if de<=cl['radius_entry_minutes'] and dx<=cl['radius_exit_minutes'] and dh<=cl['max_hold_difference_minutes']:
                    match=rep[0];dist=(de,dx,dh);break
            if match is not None:status='SUPPRESSED'
            elif len(reps)<c['clustering']['max_structures']:reps.append(row);match=cid;dist=(0,0,0);status='REPRESENTATIVE'
            else:status='OUTSIDE_TOP50'
            counts[status]+=1;writer.writerow([cid,seen,status,match or '',*(dist or ('','',''))])
    os.replace(tmp,out/'assignments.csv.gz')
    selected=[]
    for row in reps:
        cid,shard,symbol,direction,w,e,h,offset,x,avg,passes,total,dd,wi,hi=row
        with np.load(out/'shards'/(shard+'.npz'),allow_pickle=False) as z:
            slrows=[dict(SL=int(sl),**{k:z[k][wi,si,hi].item() for k in z.files if z[k].ndim==3}) for si,sl in enumerate(z['SL'])]
        selected.append(dict(CandidateID=cid,Symbol=symbol,Direction=direction,Weekday=w,EntryMinute=e,ExitMinute=x,ExitDayOffset=offset,HoldingMinutes=h,MedianAvgR=avg,PassSLCount=passes,MedianTotalR=total,WorstMaxDDR=dd,SLResults=slrows))
    atomic_json(out/'stage1_selected_structures.json',selected)
    atomic_json(out/'selection_summary.json',dict(PassingStructures=seen,**counts,Stage2Executed=False,ValidationExecuted=False))
    return selected

def full_sweep(data_root,out,expected_sha,confirmed=False):
    code_sha=require_full_authorization(expected_sha,confirmed);c=load_config();out=Path(out)
    if out.resolve().is_relative_to(ROOT):raise ValueError('large research output must be outside the git repository')
    if (np.__version__,pd.__version__)!=('2.3.5','2.2.3'):raise RuntimeError('Use frozen numpy==2.3.5 and pandas==2.2.3')
    manifest,paths,audit=audit_inputs(data_root)
    identity=dict(code_sha=code_sha,config_sha256=CONFIG_SHA,inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in audit],scope='FULL_DISCOVERY_STAGE1',runtime=dict(Python=platform.python_version(),Numpy=np.__version__,Pandas=pd.__version__))
    db=open_store(out,identity);pd.DataFrame(audit).to_csv(out/'input_audit.csv',index=False)
    atomic_json(out/'search_space.json',search_space(c));atomic_json(out/'effective_config.json',c)
    dates=pd.date_range(START,END-pd.Timedelta(days=1),freq='D');dates=dates[dates.weekday<5]
    holds=np.arange(30,1441,5)
    expected_jobs=len(c['symbols'])*2*len(range(0,1440,5))
    for symbol in c['symbols']:
        bars=load_discovery(symbol,manifest,paths);engine=FastEngine(bars,symbol);del bars
        for direction in c['directions']:
            for entry in range(0,1440,5):
                job=f'{symbol}_{direction}_{entry:04d}'
                if done(db,out,job):continue
                arrays,rows=job_arrays(engine,symbol,direction,entry,dates,holds,c)
                save_job(db,out,job,arrays,rows)
                completed=db.execute('SELECT count(*) FROM jobs').fetchone()[0]
                atomic_json(out/'progress.json',dict(CompletedJobs=completed,ExpectedJobs=expected_jobs,State='RUNNING'))
                if entry%60==0:print(f'{symbol} {direction} entry={entry}: {completed}/{expected_jobs} jobs saved',flush=True)
        del engine
    count=db.execute('SELECT count(*) FROM jobs').fetchone()[0]
    if count!=expected_jobs:raise RuntimeError('incomplete sweep; selection barred')
    finish(db,out,c);atomic_json(out/'progress.json',dict(CompletedJobs=count,ExpectedJobs=expected_jobs,State='COMPLETE_STAGE1_ONLY'));db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--describe',action='store_true');p.add_argument('--data-root',type=Path);p.add_argument('--out',type=Path,default=Path('/content/b6_stage1'));p.add_argument('--expected-sha',default='');p.add_argument('--confirm-chat-reviewed-freeze',action='store_true');a=p.parse_args()
    if a.describe:print(json.dumps({'search_space':search_space(),'config':load_config()},ensure_ascii=False,indent=2))
    else:
        if a.data_root is None:p.error('--data-root is required')
        full_sweep(a.data_root,a.out,a.expected_sha,a.confirm_chat_reviewed_freeze)
