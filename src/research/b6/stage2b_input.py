"""Strict audit of exact Stage2-A runtime files, without center selection."""
import gzip,hashlib,io,json,math
from pathlib import Path
from decimal import Decimal,InvalidOperation
import pandas as pd
from .stage2b_config import load_config
from .stage2a_config import ROOT,STRUCTURE_KEYS,load_candidates,load_config as stage2a_config,settings
from .stage1_engine import STATUS

BASE=list(STRUCTURE_KEYS)+['SL','TP','TPRatio','TPMode','ActualTPRatio','RatioAliases']
SCHEMAS={
 'stage2a_all_results.csv.gz':BASE+['Wins','Losses','WinRate','TotalR','AvgR','PF','MaxDDR','Trades','ZeroR','AvgWinR','AvgLossR','Pass','FailReasons','PositiveYears'],
 'stage2a_yearly_results.csv.gz':BASE+['Year','Trades','Wins','Losses','TotalR','AvgR','PF','MaxDDR'],
 'stage2a_diagnostics.csv.gz':BASE+['SLCount','SLRate','TPCount','TPRate','TimeExitCount','TimeExitRate','FallbackCount','MissingPathTrades','MissingPathMinutes','ExitBarFirstHits']+['Opportunities_'+s for s in STATUS]}
INTEGER_FIELDS=set(['Weekday','EntryMinute','ExitMinute','ExitDayOffset','HoldingMinutes','SL','TP','Year','Trades','Wins','Losses','ZeroR','PositiveYears','SLCount','TPCount','TimeExitCount','FallbackCount','MissingPathTrades','MissingPathMinutes','ExitBarFirstHits']+['Opportunities_'+s for s in STATUS])
NUMERIC_FIELDS={'TPRatio','ActualTPRatio','WinRate','TotalR','AvgR','PF','MaxDDR','AvgWinR','AvgLossR','SLRate','TPRate','TimeExitRate'}

def integer(value):
    try:d=Decimal(str(value))
    except InvalidOperation:raise ValueError('invalid integer') from None
    if not d.is_finite() or d!=d.to_integral_value() or d<0:raise ValueError('nonnegative integer required')
    return int(d)

def number(value):
    if value=='UNDEFINED':return None
    if value=='INF':return 'INF'
    x=float(value)
    if not math.isfinite(x):raise ValueError('nonfinite number without canonical label')
    return x

def close(a,b):
    # Serialization/aggregation audit only; never used for fills, hits or ranking.
    if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10):raise ValueError('inconsistent aggregate metrics')

def record_key(row,yearly=False):
    key=(row['CandidateID'],row['SL'],row['TP'])
    return key+(row['Year'],) if yearly else key

def parse_table(raw,name):
    frame=pd.read_csv(io.BytesIO(gzip.decompress(raw)),dtype=str,keep_default_na=False)
    if list(frame.columns)!=SCHEMAS[name]:raise ValueError('Stage2-A schema mismatch: '+name)
    rows=[]
    for original in frame.to_dict('records'):
        row=dict(original)
        for key,value in original.items():
            if key in ('TP','TPRatio','ActualTPRatio') and value=='':row[key]=None
            elif key in INTEGER_FIELDS:row[key]=integer(value)
            elif key in NUMERIC_FIELDS:row[key]=number(value)
            elif key=='Pass':
                if value not in ('True','False'):raise ValueError('invalid Pass boolean')
                row[key]=value=='True'
        rows.append(row)
    return rows

def validate_metrics(row):
    n=row['Trades'];w=row['Wins'];loss=row['Losses']
    if w+loss>n or ('ZeroR' in row and w+loss+row['ZeroR']!=n):raise ValueError('trade counts inconsistent')
    for key in ('TotalR','MaxDDR'):
        if not isinstance(row[key],(int,float)) or not math.isfinite(row[key]):raise ValueError('invalid '+key)
    if row['MaxDDR']<0:raise ValueError('negative drawdown')
    if n:
        if not isinstance(row['AvgR'],(int,float)):raise ValueError('undefined AvgR with trades')
        close(row['AvgR']*n,row['TotalR'])
    elif row['AvgR'] is not None or row['TotalR']!=0 or row['MaxDDR']!=0:raise ValueError('invalid empty metrics')
    pf=row['PF']
    if loss:
        if not isinstance(pf,(int,float)) or not math.isfinite(pf) or pf<0:raise ValueError('invalid PF')
    elif pf!=('INF' if w else None):raise ValueError('invalid zero-loss PF')
    if 'WinRate' in row:
        if n:close(row['WinRate'],w/n)
        elif row['WinRate'] is not None:raise ValueError('invalid empty WinRate')
        for count,k,sign in ((w,'AvgWinR',1),(loss,'AvgLossR',-1)):
            if count and (not isinstance(row[k],(int,float)) or row[k]*sign<=0):raise ValueError('invalid '+k)
            if not count and row[k] is not None:raise ValueError('undefined '+k+' required')
        gain=w*(row['AvgWinR'] or 0);pain=-loss*(row['AvgLossR'] or 0)
        close(gain-pain,row['TotalR'])
        if loss:close(pf,gain/pain)

def validate_tables(tables,candidates,c):
    expected={}
    for candidate in candidates:
        for setting in settings(candidate):
            s={**candidate,**setting};s['RatioAliases']='|'.join(s['RatioAliases']);expected[record_key(s)]=s
    if len(expected)!=c['stage2a_expected_configurations']:raise ValueError('expected 1500 Stage2-A keys')
    indexes={}
    for name,rows in tables.items():
        yearly='yearly' in name;keys={};expected_keys={k+(y,) for k in expected for y in (2020,2021,2022,2023)} if yearly else set(expected)
        if len(rows)!=len(expected_keys):raise ValueError('Stage2-A row count mismatch')
        for row in rows:
            key=record_key(row,yearly)
            if key in keys or key not in expected_keys:raise ValueError('duplicate/unexpected Candidate/SL/TP/year')
            template=expected[record_key(row)]
            if any(row[k]!=template[k] for k in BASE):raise ValueError('Stage2-A condition identity mismatch')
            if yearly or 'all_results' in name:validate_metrics(row)
            keys[key]=row
        if set(keys)!=expected_keys:raise ValueError('missing expected keys')
        indexes[name]=keys
    allrows=indexes['stage2a_all_results.csv.gz'];annual=indexes['stage2a_yearly_results.csv.gz'];diag=indexes['stage2a_diagnostics.csv.gz'];g=c['gate']
    for key,row in allrows.items():
        years=[annual[key+(y,)] for y in (2020,2021,2022,2023)]
        for k in ('Trades','Wins','Losses'):
            if row[k]!=sum(y[k] for y in years):raise ValueError('annual count mismatch')
        close(row['TotalR'],sum(y['TotalR'] for y in years));positive=sum(y['TotalR']>0 for y in years)
        reasons=[]
        if row['Trades']<g['min_trades']:reasons.append('TOTAL_TRADES')
        if row['Losses']<g['min_losses']:reasons.append('LOSS_COUNT')
        if not isinstance(row['PF'],(int,float)) or row['PF']<g['min_pf']:reasons.append('PF')
        for y in years:
            if y['Trades']<g['min_annual_trades']:reasons.append('ANNUAL_TRADES_'+str(y['Year']))
        if positive<g['min_positive_years']:reasons.append('POSITIVE_YEARS')
        if row['PositiveYears']!=positive or row['Pass']!=(not reasons) or row['FailReasons']!='|'.join(reasons):raise ValueError('P02 gate mismatch')
        d=diag[key];n=row['Trades']
        if d['SLCount']+d['TPCount']+d['TimeExitCount']!=n or d['Opportunities_OK']!=n:raise ValueError('exit counts mismatch')
        if row['TP'] is None and d['TPCount']:raise ValueError('TP_NONE has TP exits')
        for label in ('SL','TP','TimeExit'):
            if n:close(d[label+'Rate'],d[label+'Count']/n)
            elif d[label+'Rate'] is not None:raise ValueError('empty exit rate')
        if any(d[k]>n for k in ('FallbackCount','MissingPathTrades','ExitBarFirstHits')) or d['MissingPathMinutes']<d['MissingPathTrades']:raise ValueError('invalid path diagnostics')
    return list(allrows.values())

def load_input(result_root,stage1_root,c=None):
    c=load_config() if c is None else c;root=Path(result_root);s1=Path(stage1_root)
    candidates,candidate_audit=load_candidates(s1/'stage1_selected_structures.json',s1/'identity.json',s1/'effective_config.json')
    raw={}
    for name in c['stage2a_required_files']:
        path=root/name
        if not path.is_file():raise ValueError('required Stage2-A file missing: '+name)
        raw[name]=path.read_bytes()
    hashes={name:hashlib.sha256(data).hexdigest() for name,data in raw.items()}
    if c['stage2a_runtime_sha256'] and hashes!=c['stage2a_runtime_sha256']:raise ValueError('Stage2-A runtime result SHA mismatch')
    meta={name:json.loads(data) for name,data in raw.items() if name.endswith('.json')}
    identity=meta['identity.json'];expected_identity={'code_sha':c['stage2a_freeze_sha'],'config_sha256':c['stage2a_config_sha256'],'candidate_sha256':c['candidate_sha256'],'stage1_code_sha':c['stage1_freeze_sha'],'stage1_config_sha256':c['stage1_effective_config_sha256'],'scope':'FULL_DISCOVERY_STAGE2A'}
    if any(identity.get(k)!=v for k,v in expected_identity.items()):raise ValueError('Stage2-A provenance mismatch')
    if hashes['effective_config.json']!=c['stage2a_config_sha256'] or meta['effective_config.json']!=stage2a_config():raise ValueError('Stage2-A config mismatch')
    runtime=identity.get('runtime',{})
    if not isinstance(runtime.get('Python'),str) or not runtime['Python'] or runtime.get('Numpy')!=c['runtime']['numpy'] or runtime.get('Pandas')!=c['runtime']['pandas']:raise ValueError('Stage2-A runtime identity incomplete')
    manifest=pd.read_csv(ROOT/'research_inputs/b6/expected_m1_manifest.csv',dtype=str)
    expected_inputs=manifest[['Filename','SHA256']].to_dict('records')
    if len(expected_inputs)!=56 or identity.get('inputs')!=expected_inputs:raise ValueError('Stage2-A M1 input identities mismatch')
    if meta['candidate_input_audit.json']!=candidate_audit:raise ValueError('Stage2-A candidate audit mismatch')
    progress=meta['progress.json'];summary=meta['stage2a_summary.json']
    if progress!={'CompletedJobs':50,'ExpectedJobs':50,'CompletedConfigurations':1500,'State':'COMPLETE_STAGE2A_ONLY'}:raise ValueError('Stage2-A incomplete progress')
    for k,v in dict(State='COMPLETE_STAGE2A_ONLY',Candidates=50,Configurations=1500,FormalRanking=False,Stage2BCentersSelected=False,ValidationExecuted=False,MonitorExecuted=False).items():
        if type(summary.get(k)) is not type(v) or summary.get(k)!=v:raise ValueError('Stage2-A summary mismatch')
    tables={name:parse_table(raw[name],name) for name in SCHEMAS};allrows=validate_tables(tables,candidates,c)
    passes=sum(r['Pass'] for r in allrows)
    if summary['PassCount']!=passes or summary['FailCount']!=1500-passes:raise ValueError('Stage2-A summary pass counts mismatch')
    audit=dict(Status='PASS',Stage1FreezeSHA=c['stage1_freeze_sha'],CandidateSHA256=c['candidate_sha256'],CandidateCount=50,Stage2AFreezeSHA=c['stage2a_freeze_sha'],Stage2AConfigSHA256=c['stage2a_config_sha256'],RuntimeResultSHA256=hashes,Runtime=runtime,Rows={name:len(rows) for name,rows in tables.items()},Schemas=SCHEMAS,M1InputCount=56,CentersSelected=False)
    return candidates,allrows,audit,identity
