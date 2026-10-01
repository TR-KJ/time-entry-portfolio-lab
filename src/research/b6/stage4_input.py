"""Read-only Stage3 provenance, checkpoints, tables and final selection audit."""
import gzip,hashlib,io,json,zipfile
from pathlib import Path
import pandas as pd
from .stage4_config import load_config
from .stage3_config import load_config as previous_config
from .stage3_input import load_input as previous_input,same,normalize
from .stage3_search import prepare_jobs
from .stage3_selection import select_final
from .stage1_search import json_safe

def compare_table(raw,expected,name):
    frame=pd.read_csv(io.BytesIO(raw),dtype=str,keep_default_na=False)
    if len(frame)!=len(expected):raise ValueError('Stage3 table count: '+name)
    if not expected:return
    if set(frame.columns)!=set(expected[0]):raise ValueError('Stage3 table schema: '+name)
    for actual,target in zip(frame.to_dict('records'),expected):
        for k,v in target.items():
            a=actual[k]
            if v is None or v=='UNDEFINED':ok=a in ('','UNDEFINED')
            elif isinstance(v,bool):ok=a==str(v)
            elif isinstance(v,(int,float)):
                try:ok=same(float(a),v)
                except ValueError:ok=False
            elif isinstance(v,(list,dict)):
                try:ok=same(json.loads(a),v)
                except ValueError:ok=False
            else:ok=a==str(v)
            if not ok:raise ValueError('Stage3 table content: '+name+':'+k)

def validate_payload(meta,shards,fixed,c,prior_audit,prior_identity):
    prev=previous_config();identity=meta['identity.json'];summary=meta['stage3_summary.json'];progress=meta['progress.json']
    expected=dict(code_sha=c['stage3_freeze_sha'],config_sha256=c['stage3_config_sha256'],stage2b_code_sha=c['stage2b_freeze_sha'],selected_settings_sha256=prev['selected_settings_sha256'],stage2b_runtime_sha256=prior_audit['FormalInputSHA256'],candidate_sha256=c['candidate_sha256'],scope='FULL_DISCOVERY_STAGE3',inputs=prior_identity['inputs'])
    if any(identity.get(k)!=v for k,v in expected.items()):raise ValueError('Stage3 identity mismatch')
    if meta['effective_config.json']!=prev or meta['stage2b_input_audit.json']!=prior_audit:raise ValueError('Stage3 prior config/audit mismatch')
    rt=identity.get('runtime',{})
    if not rt.get('Python') or rt.get('Numpy')!=c['runtime']['numpy'] or rt.get('Pandas')!=c['runtime']['pandas']:raise ValueError('Stage3 runtime version mismatch')
    if summary.get('State')!='COMPLETE_STAGE3_ONLY' or progress.get('State')!='COMPLETE_STAGE3_ONLY':raise ValueError('Stage3 incomplete')
    if any(summary.get(k) is not False for k in ('Stage4Executed','EventFilterExecuted','ValidationExecuted','MonitorExecuted','Refill')):raise ValueError('Stage3 contaminated provenance')
    jobs,space=prepare_jobs(fixed,prev)
    if meta['search_space.json']!=space or meta['invalid_schedules.json']!=[p for j in jobs for p in j['invalid']]:raise ValueError('Stage3 search space mismatch')
    if set(shards)!={a['CandidateID'] for a in fixed}:raise ValueError('Stage3 checkpoint IDs mismatch')
    tables={k:[] for k in ('results','yearly','diagnostics','stability')};selected=[];dropped=[]
    for job in jobs:
        candidate=job['candidate'];data=shards[candidate['CandidateID']]
        if data['grid']!=job['grid']:raise ValueError('Stage3 grid/SL/TP changed')
        for kind in ('results','yearly','diagnostics'):
            rows=data[kind];expected=[(p,y) for p in job['grid'] for y in ((2020,2021,2022,2023) if kind=='yearly' else (None,))]
            if len(rows)!=len(expected):raise ValueError('incomplete Stage3 shard')
            for row,(point,year) in zip(rows,expected):
                if any(row.get(k)!=v for k,v in point.items()) or row.get('Year')!=year:raise ValueError('Stage3 fixed fields/year mismatch')
            tables[kind].extend(rows)
        result=select_final(candidate,data['results'],data['yearly'],prev)
        tables['stability'].extend(json_safe(result['stability']))
        if result['selected'] is None:dropped.append(result['dropped'])
        else:selected.append(json_safe(result['selected']))
    # Exact JSON values, not a new price run; replay the frozen ranking over saved results.
    if selected!=meta['stage3_selected_settings.json']:raise ValueError('Stage3 selected differs from stability/final ranking')
    ids=[r['CandidateID'] for r in selected];drops=[r['CandidateID'] for r in dropped]
    if len(set(ids))!=len(ids) or set(ids)&set(drops) or set(ids)|set(drops)!=set(shards):raise ValueError('Stage3 selected/dropped partition')
    if len(ids)!=c['selected_candidate_count']:raise ValueError('Stage3 selected count mismatch')
    n=len(tables['results'])
    expected_summary=dict(CandidateCount=len(fixed),SelectedStructures=len(ids),DroppedStructures=len(drops),ActualUniqueConfigurations=n,GatePass=sum(r['Pass'] for r in tables['results']),GateFail=sum(not r['Pass'] for r in tables['results']),StabilityPass=sum(r['StabilityPass'] for r in tables['stability']),StabilityFail=sum(not r['StabilityPass'] for r in tables['stability']))
    if any(summary.get(k)!=v for k,v in expected_summary.items()):raise ValueError('Stage3 summary mismatch')
    if any(progress.get(k)!=v for k,v in dict(CompletedJobs=len(fixed),ExpectedJobs=len(fixed),CompletedConfigurations=n,ExpectedConfigurations=n).items()):raise ValueError('Stage3 progress counts')
    return selected,tables,dropped,identity

def load_input(result_root,stage2b_root,stage1_root,c=None):
    c=load_config() if c is None else c;root=Path(result_root);raw={};hashes={}
    for name,digest in c['stage3_runtime_manifest'].items():
        p=root/name
        if not p.is_file():raise ValueError('formal Stage3 input missing: '+name)
        raw[name]=p.read_bytes();hashes[name]=hashlib.sha256(raw[name]).hexdigest()
        if hashes[name]!=digest:raise ValueError('formal Stage3 SHA mismatch: '+name)
    if hashes['stage3_selected_settings.json']!=c['selected_settings_sha256'] or hashes['effective_config.json']!=c['stage3_config_sha256']:raise ValueError('Stage3 selected/config identity')
    meta={n:json.loads(v) for n,v in raw.items() if n.endswith('.json') and '/' not in n}
    shards={cid:json.loads(raw['shards/'+cid+'.json']) for cid in meta['checkpoints.json']}
    if any(hashes['shards/'+cid+'.json']!=h for cid,h in meta['checkpoints.json'].items()):raise ValueError('Stage3 checkpoint ledger mismatch')
    fixed,prior_audit,prior_identity=previous_input(stage2b_root,stage1_root)
    selected,tables,dropped,identity=validate_payload(meta,shards,fixed,c,prior_audit,prior_identity)
    for kind,suffix in (('results','all_results'),('yearly','yearly_results'),('diagnostics','diagnostics'),('stability','stability')):
        name='stage3_'+suffix+'.csv.gz';compare_table(gzip.decompress(raw[name]),tables[kind],name)
    compare_table(raw['dropped_structures.csv'],dropped,'dropped_structures.csv')
    review=meta['stage3_review.json'];ri={k:v for k,v in identity.items() if k!='inputs'};ri['M1InputCount']=56
    if review['Summary']!=meta['stage3_summary.json'] or review['Identity']!=ri or review['InputAudit']!=prior_audit:raise ValueError('Stage3 review inconsistency')
    with zipfile.ZipFile(io.BytesIO(raw['stage3_review.zip'])) as z:
        expected={'effective_config.json','stage2b_input_audit.json','search_space.json','invalid_schedules.json','progress.json','stage3_all_results.csv.gz','stage3_yearly_results.csv.gz','stage3_diagnostics.csv.gz','stage3_stability.csv.gz','dropped_structures.csv','stage3_selected_settings.json','stage3_summary.json','stage3_review.json'}
        if len(z.namelist())!=len(expected) or set(z.namelist())!=expected:raise ValueError('Stage3 review ZIP membership')
        if any(z.read(n)!=raw[n] for n in expected):raise ValueError('Stage3 review ZIP content mismatch')
    audit=dict(Status='PASS',Stage3FreezeSHA=c['stage3_freeze_sha'],Stage3ConfigSHA256=c['stage3_config_sha256'],SelectedSettingsSHA256=c['selected_settings_sha256'],SelectedCount=len(selected),DroppedCount=len(dropped),FormalInputSHA256=hashes,State='COMPLETE_STAGE3_ONLY',Stage4Executed=False,EventFilterExecuted=False,ValidationExecuted=False,MonitorExecuted=False,FixedSLTP=True,FinalRankingAudit='PASS',Runtime=identity['runtime'])
    return selected,audit,identity
