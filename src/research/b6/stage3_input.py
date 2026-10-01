"""Audit actual complete Stage2-B runtime artifacts; never regenerate results."""
import gzip,hashlib,io,json,math
from pathlib import Path
import pandas as pd
from .stage3_config import ROOT,load_config
from .stage2a_config import load_candidates,STRUCTURE_KEYS
from .stage2b_config import load_config as previous_config
from .stage2b_input import INTEGER_FIELDS,NUMERIC_FIELDS,integer,number,validate_metrics,close
from .stage2b_selection import local_grid,setting_key,final_key

INTS=INTEGER_FIELDS|{'SourceCenterSL','SourceCenterTP','NeighborhoodCount','NeighborhoodPassCount'}
NUMS=NUMERIC_FIELDS|{'PointAvgR','CenterDistance','SourceCenterDistance','NeighborhoodPassRate','NeighborhoodMedianAvgR','NeighborhoodMedianTotalR','NeighborhoodWorstMaxDDR'}
NULLS={'TP','TPRatio','ActualTPRatio','SourceCenterTP'}

def normalize(value):
    if isinstance(value,dict):return {k:normalize(v) for k,v in value.items()}
    if isinstance(value,list):return [normalize(v) for v in value]
    return None if value=='UNDEFINED' else value

def parse_table(data,name,spec):
    raw=gzip.decompress(data) if name.endswith('.gz') else data
    frame=pd.read_csv(io.BytesIO(raw),dtype=str,keep_default_na=False)
    if list(frame.columns)!=spec['Columns'] or len(frame)!=spec['Rows']:raise ValueError('Stage2-B rows/schema mismatch: '+name)
    rows=[]
    for record in frame.to_dict('records'):
        row={}
        for k,v in record.items():
            if k in NULLS and v=='':row[k]=None
            elif k in INTS:row[k]=integer(v)
            elif k in NUMS:row[k]=number(v)
            elif k in ('Pass','StabilityPass'):
                if v not in ('True','False'):raise ValueError('boolean field malformed')
                row[k]=v=='True'
            elif k in ('CenterAliases','SourceCenterAliases'):row[k]=json.loads(v)
            else:row[k]=v
        rows.append(row)
    return rows

def key(row):return (row['CandidateID'],*setting_key(row))

def same(a,b):
    if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) and not isinstance(b,bool):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)
    return type(a) is type(b) and a==b

def validate_payload(meta,tables,candidates,candidate_audit,c):
    b=previous_config();identity=meta['identity.json'];summary=meta['stage2b_summary.json'];progress=meta['progress.json']
    expected=dict(code_sha=c['stage2b_freeze_sha'],config_sha256=c['stage2b_config_sha256'],stage2a_code_sha=c['stage2a_freeze_sha'],stage2a_config_sha256=b['stage2a_config_sha256'],candidate_sha256=c['candidate_sha256'],scope='FULL_DISCOVERY_STAGE2B',stage2a_result_sha256=b['stage2a_runtime_sha256'])
    if any(identity.get(k)!=v for k,v in expected.items()):raise ValueError('Stage2-B provenance mismatch')
    if meta['effective_config.json']!=b:raise ValueError('Stage2-B effective config mismatch')
    for k in ('Stage3Executed','ValidationExecuted','MonitorExecuted','Refill'):
        if summary.get(k) is not False:raise ValueError('contaminated Stage2-B provenance')
    if summary.get('State')!='COMPLETE_STAGE2B_ONLY' or progress.get('State')!='COMPLETE_STAGE2B_ONLY':raise ValueError('incomplete Stage2-B')
    expected_inputs=pd.read_csv(ROOT/'research_inputs/b6/expected_m1_manifest.csv',dtype=str)[['Filename','SHA256']].to_dict('records')
    if len(expected_inputs)!=56 or identity.get('inputs')!=expected_inputs:raise ValueError('M1 identity mismatch')
    runtime=identity.get('runtime',{})
    if not runtime.get('Python') or runtime.get('Numpy')!=c['runtime']['numpy'] or runtime.get('Pandas')!=c['runtime']['pandas']:raise ValueError('runtime identity mismatch')
    prior=meta['stage2a_input_audit.json']
    if prior.get('Status')!='PASS' or prior.get('RuntimeResultSHA256')!=b['stage2a_runtime_sha256'] or prior.get('CandidateSHA256')!=candidate_audit['CandidateSHA256']:raise ValueError('Stage2-A audit mismatch')
    original={r['CandidateID']:r for r in candidates};centers=meta['centers.json'];by_center={cid:[] for cid in original}
    seen_centers=set()
    for center in centers:
        cid=center['CandidateID']
        if cid not in original or any(center[k]!=original[cid][k] for k in STRUCTURE_KEYS):raise ValueError('center structure changed')
        if key(center) in seen_centers:raise ValueError('duplicate center')
        seen_centers.add(key(center));by_center[cid].append(center)
        if center['CenterType'] not in ('GROWTH','EFFICIENCY') or not center['CenterAliases'] or set(center['CenterAliases'])-{'GROWTH','EFFICIENCY'}:raise ValueError('center alias invalid')
    expected_rows={}
    for cid,cs in by_center.items():
        if len(cs)>2:raise ValueError('too many centers')
        for g in local_grid(cs,b):expected_rows[(cid,*setting_key(g))]={**original[cid],**g}
    indexes={}
    for name in ('stage2b_all_results.csv.gz','stage2b_yearly_results.csv.gz','stage2b_diagnostics.csv.gz','stability_results.csv.gz'):
        rows=tables[name];yearly='yearly' in name;lookup={}
        for row in rows:
            k=key(row);full=k+(row['Year'],) if yearly else k
            if full in lookup or k not in expected_rows:raise ValueError('duplicate/unknown result setting')
            template=expected_rows[k]
            if any(row[n]!=template[n] for n in (*STRUCTURE_KEYS,'SL','TP','TPMode','CenterAliases')):raise ValueError('result structure/SL/TP mismatch')
            if name!='stage2b_diagnostics.csv.gz':validate_metrics(row)
            lookup[full]=row
        required={k+(y,) for k in expected_rows for y in (2020,2021,2022,2023)} if yearly else set(expected_rows)
        if set(lookup)!=required:raise ValueError('incomplete local result keys')
        indexes[name]=lookup
    allrows=indexes['stage2b_all_results.csv.gz'];annual=indexes['stage2b_yearly_results.csv.gz'];stable=indexes['stability_results.csv.gz'];diag=indexes['stage2b_diagnostics.csv.gz']
    for k,row in allrows.items():
        if not same(row,{n:stable[k][n] for n in row}):raise ValueError('stability point mismatch')
        years=[annual[k+(y,)] for y in (2020,2021,2022,2023)]
        for n in ('Trades','Wins','Losses'):
            if row[n]!=sum(y[n] for y in years):raise ValueError('annual count mismatch')
        close(row['TotalR'],sum(y['TotalR'] for y in years))
        passed=(row['Trades']>=c['gate']['min_trades'] and row['Losses']>=c['gate']['min_losses'] and isinstance(row['PF'],(int,float)) and row['PF']>=c['gate']['min_pf'] and all(y['Trades']>=c['gate']['min_annual_trades'] for y in years) and sum(y['TotalR']>0 for y in years)>=c['gate']['min_positive_years'])
        if row['Pass']!=passed:raise ValueError('P02 gate mismatch')
        d=diag[k]
        if sum(d[n] for n in ('SLCount','TPCount','TimeExitCount'))!=row['Trades'] or d['Opportunities_OK']!=row['Trades']:raise ValueError('diagnostic counts mismatch')
    scopes=tables['stability_by_center.csv.gz'];scope_lookup={}
    for row in scopes:
        k=key(row);sk=k+(row['SourceCenterType'],)
        if k not in stable or sk in scope_lookup:raise ValueError('invalid center-scoped stability')
        scope_lookup[sk]=row
    for k,row in stable.items():
        if not same(row,scope_lookup.get(k+(row['SourceCenterType'],),{})):raise ValueError('chosen stability scope mismatch')
    selected=meta['stage2b_selected_settings.json'];dropped=tables['dropped_structures.csv'];selected_ids=[];dropped_ids=[r['CandidateID'] for r in dropped]
    for row in selected:
        cid=row['CandidateID'];k=key(row)
        if cid not in original or cid in selected_ids or k not in stable:raise ValueError('duplicate/unknown selected candidate')
        selected_ids.append(cid)
        if row.get('Status')!='STAGE2B_SELECTED_SL_TP_FROZEN' or row.get('StabilityPass') is not True or row.get('Pass') is not True:raise ValueError('invalid selected status')
        if row.get('SelectedSL')!=row['SL'] or row.get('SelectedTP')!=row['TP']:raise ValueError('selected SL/TP changed')
        if not same({n:row[n] for n in stable[k]},stable[k]):raise ValueError('selected differs from formal stability result')
        years=[annual[k+(y,)] for y in (2020,2021,2022,2023)]
        if not same(row.get('YearlyMetrics'),years):raise ValueError('selected yearly metrics mismatch')
        eligible=[r for kk,r in stable.items() if kk[0]==cid and r['StabilityPass']]
        if not eligible or key(min(eligible,key=final_key))!=k:raise ValueError('selected differs from frozen Stage2-B final rule')
    if len(set(dropped_ids))!=len(dropped_ids) or set(selected_ids)&set(dropped_ids) or set(selected_ids)|set(dropped_ids)!=set(original):raise ValueError('dropped/selected partition mismatch')
    if len(selected)!=c['selected_candidate_count'] or sum(r['TP'] is None for r in selected)!=c['selected_tp_none_count']:raise ValueError('selected count/type mismatch')
    n=len(allrows)
    for k,v in dict(Candidates=len(original),UniqueCenters=len(centers),ActualUniqueConfigurations=n,SelectedStructures=len(selected),DroppedStructures=len(dropped),P02Pass=sum(r['Pass'] for r in allrows.values()),P02Fail=sum(not r['Pass'] for r in allrows.values()),StabilityPass=sum(r['StabilityPass'] for r in stable.values()),StabilityFail=sum(not r['StabilityPass'] for r in stable.values())).items():
        if summary.get(k)!=v:raise ValueError('summary count mismatch')
    if any(progress.get(k)!=v for k,v in dict(CompletedJobs=len(original),ExpectedJobs=len(original),CompletedConfigurations=n,ExpectedConfigurations=n).items()):raise ValueError('progress incomplete')
    if meta['search_space.json'].get('ActualUniqueConditions')!=n:raise ValueError('search space mismatch')
    return [{**{k:r[k] for k in STRUCTURE_KEYS},'SL':r['SL'],'TP':r['TP'],'TPMode':r['TPMode']} for r in selected],identity

def load_input(result_root,stage1_root,c=None):
    c=load_config() if c is None else c;root=Path(result_root);s1=Path(stage1_root)
    if not root.is_dir():raise ValueError('formal Stage2-B result root required; no reconstruction')
    raw={};hashes={}
    for name,spec in c['stage2b_runtime_manifest'].items():
        p=root/name
        if not p.is_file():raise ValueError('required Stage2-B file missing: '+name)
        raw[name]=p.read_bytes();hashes[name]=hashlib.sha256(raw[name]).hexdigest()
        if hashes[name]!=spec['SHA256']:raise ValueError('Stage2-B input SHA mismatch: '+name)
    if hashes['stage2b_selected_settings.json']!=c['selected_settings_sha256'] or hashes['effective_config.json']!=c['stage2b_config_sha256']:raise ValueError('selected/config SHA mismatch')
    candidates,audit=load_candidates(s1/'stage1_selected_structures.json',s1/'identity.json',s1/'effective_config.json')
    meta={n:normalize(json.loads(data)) for n,data in raw.items() if n.endswith('.json')}
    tables={n:parse_table(data,n,c['stage2b_runtime_manifest'][n]) for n,data in raw.items() if '.csv' in n}
    selected,identity=validate_payload(meta,tables,candidates,audit,c)
    report=dict(Status='PASS',Stage2BFreezeSHA=c['stage2b_freeze_sha'],Stage2AFreezeSHA=c['stage2a_freeze_sha'],Stage1CandidateSHA256=c['candidate_sha256'],SelectedSettingsSHA256=c['selected_settings_sha256'],SelectedCount=len(selected),TPNoneCount=sum(r['TP'] is None for r in selected),FormalInputSHA256=hashes,Rows={n:len(v) for n,v in tables.items()},State=meta['stage2b_summary.json']['State'],Stage3Executed=False,ValidationExecuted=False,MonitorExecuted=False,Stage3SelectionPerformed=False,Runtime=identity['runtime'])
    return selected,report,identity
