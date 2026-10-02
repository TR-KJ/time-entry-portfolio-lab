"""Audit saved Stage4 results only. No M1 reads, execution or optimization."""
import csv,gzip,hashlib,io,json,math,statistics,zipfile
from collections import Counter
from pathlib import Path
from .stage5_config import ROOT,load_config
from .stage4_config import load_config as stage4_config
from .stage4_metrics import FULL,YEAR,FIXED
from .stage4_events import MODES,applicable_events
from .stage4_selection import adoption,compare,choose
from .stage4_input import compare_table

def strict_json(raw):
    def reject(x):raise ValueError('nonfinite JSON token: '+x)
    return json.loads(raw,parse_constant=reject)

def check_metrics(row,yearly=False):
    keys=YEAR if yearly else FULL
    if any(k not in row for k in keys):raise ValueError('missing formal metric')
    for k in ('Trades','Wins','Losses'):
        if type(row[k]) is not int or row[k]<0:raise ValueError('invalid trade counts')
    zero=row['Trades']-row['Wins']-row['Losses']
    if zero<0 or ('ZeroR' in row and row['ZeroR']!=zero):raise ValueError('0R semantics mismatch')
    for k in keys:
        v=row[k]
        if isinstance(v,bool) or not (isinstance(v,(int,float)) and math.isfinite(v) or isinstance(v,str) and v in ('INF','UNDEFINED')):raise ValueError('invalid formal metric value')
    if not isinstance(row['MaxDDR'],(int,float)) or not math.isfinite(row['MaxDDR']) or row['MaxDDR']<0:raise ValueError('invalid raw MaxDDR')
    if row['Losses']==0 and row['PF']!=('INF' if row['Wins'] else 'UNDEFINED'):raise ValueError('PF infinity/undefined semantics mismatch')

def validate_payload(meta,shards,stage3,c):
    prev=stage4_config();identity=meta['identity.json'];summary=meta['stage4_summary.json'];progress=meta['progress.json'];selected=meta['stage4_selected_settings.json']
    expected=dict(code_sha=c['stage4_freeze_sha'],config_sha256=c['stage4_config_sha256'],stage3_code_sha=c['stage3_freeze_sha'],selected_settings_sha256=c['stage3_selected_sha256'],stage3_runtime_sha256=prev['stage3_runtime_manifest'],calendar_sha256=prev['calendar_sha256'],calendar_source_commit=prev['calendar_source_commit'],candidate_sha256=prev['candidate_sha256'],scope='FULL_DISCOVERY_STAGE4')
    if any(identity.get(k)!=v for k,v in expected.items()):raise ValueError('Stage4 provenance mismatch')
    if meta['effective_config.json']!=prev:raise ValueError('Stage4 effective config mismatch')
    with (ROOT/'research_inputs/b6/expected_m1_manifest.csv').open() as f:expected_inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in csv.DictReader(f)]
    if len(expected_inputs)!=56 or identity.get('inputs')!=expected_inputs:raise ValueError('Stage4 M1 provenance mismatch')
    runtime=identity.get('runtime',{})
    if not runtime.get('Python') or runtime.get('Numpy')!=prev['runtime']['numpy'] or runtime.get('Pandas')!=prev['runtime']['pandas']:raise ValueError('Stage4 runtime identity mismatch')
    if meta['stage3_input_audit.json']!=strict_json((ROOT/'results/b6/stage4_freeze/stage3_input_audit.json').read_bytes()):raise ValueError('Stage3 audited provenance mismatch')
    if meta['event_calendar.json']!=strict_json((ROOT/'research_inputs/b6/stage4_event_calendar.json').read_bytes()) or meta['event_calendar_audit.json']!=strict_json((ROOT/'results/b6/stage4_freeze/event_calendar_audit.json').read_bytes()):raise ValueError('calendar changed')
    for obj in (summary,progress):
        if obj.get('State')!='COMPLETE_STAGE4_ONLY' or obj.get('EventFilterExecuted') is not True:raise ValueError('incomplete Stage4')
        if any(obj.get(k) is not False for k in ('CandidateFreezeExecuted','ValidationExecuted','MonitorExecuted','PortfolioExecuted')):raise ValueError('later-stage provenance contamination')
    ids=[r['CandidateID'] for r in selected];prior_ids=[r['CandidateID'] for r in stage3]
    if len(ids)!=c['expected_candidate_count'] or len(set(ids))!=len(ids):raise ValueError('selected count/duplicate CandidateID')
    if ids!=prior_ids or len(set(prior_ids))!=len(prior_ids) or set(shards)!=set(ids):raise ValueError('candidate set/order changed; refill/drop forbidden')
    e0audit=dict(Status='PASS',Comparison='EXACT_FULL_AND_FOUR_YEARLY_METRICS',Candidates=[dict(CandidateID=cid,FullMetrics='EXACT_PASS',YearlyMetrics='EXACT_PASS') for cid in ids])
    if meta['e0_equivalence_audit.json']!=e0audit:raise ValueError('Stage4 E0 preflight missing/inconsistent')
    tables={k:[] for k in ('results','yearly','diagnostics','selection_audit')}
    for s,p in zip(selected,stage3):
        cid=s['CandidateID'];data=shards[cid]
        if any(s.get(k)!=p[k] for k in FIXED):raise ValueError('Stage3 fixed conditions changed')
        if s!=data['selected']:raise ValueError('selected/shard mismatch')
        for kind in tables:
            rows=data[kind];keys=[(m,y) for m in MODES for y in ((2020,2021,2022,2023) if kind=='yearly' else (None,))]
            if [(r['EventMode'],r.get('Year')) for r in rows]!=keys:raise ValueError('incomplete/duplicate variant or year')
            if any(any(r.get(k)!=p[k] for k in FIXED) for r in rows):raise ValueError('variant fixed conditions changed')
            tables[kind].extend(rows)
        rows=data['results'];e0=rows[0]
        if any(e0[k]!=p[k] for k in FULL):raise ValueError('E0/Stage3 full metrics changed')
        years0=[r for r in data['yearly'] if r['EventMode']=='E0']
        if [r['Year'] for r in p['YearlyMetrics']]!=[2020,2021,2022,2023] or any(a[k]!=b[k] for a,b in zip(years0,p['YearlyMetrics']) for k in YEAR):raise ValueError('E0/Stage3 yearly metrics changed')
        best,reason=choose(rows)
        if s['SelectedEventMode']!=best['EventMode'] or s['SelectionReason']!=reason:raise ValueError('formal Stage4 mode selection mismatch')
        for row,d,sa in zip(rows,data['diagnostics'],data['selection_audit']):
            mode=row['EventMode'];check_metrics(row)
            expected_compare=compare(e0,row)
            if any(row[k]!=v for k,v in expected_compare.items()):raise ValueError('Stage4 deltas/retention mismatch')
            passed=adoption(row) if mode!='E0' else dict(AdoptionPass=False,AdoptionFailReasons='BASELINE')
            if any(row[k]!=v for k,v in passed.items()) or row['ApplicableEvents']!=applicable_events(p['Symbol'],mode):raise ValueError('Stage4 adoption/events mismatch')
            if sa!=dict(row,Selected=mode==best['EventMode'],SelectionReason=reason):raise ValueError('selection audit mismatch')
            if any(d.get(k)!=v for k,v in row.items() if k not in FULL):raise ValueError('event diagnostics mismatch')
            if row['RemovedTrades']<0 or row['FilteredTrades']>row['E0Trades'] or d['FilteredOpportunities']<row['RemovedTrades']:raise ValueError('subset counts inconsistent')
            events=row['ApplicableEvents']
            for name in ('RemovedTradeCountByEvent','OverlapOpportunityCountByEvent'):
                if set(d[name])!=set(events) or any(type(n) is not int or n<0 for n in d[name].values()):raise ValueError('event attribution invalid')
            if any(d['RemovedTradeCountByEvent'][e]>d['OverlapOpportunityCountByEvent'][e] for e in events):raise ValueError('event attribution impossible')
            years=[r for r in data['yearly'] if r['EventMode']==mode]
            for y in years:check_metrics(y,True)
            if any(sum(y[k] for y in years)!=row[k] for k in ('Trades','Wins','Losses')) or not math.isclose(sum(y['TotalR'] for y in years),row['TotalR'],rel_tol=1e-12,abs_tol=1e-12):raise ValueError('annual/full reconciliation mismatch')
        expected_selected={**{k:p[k] for k in FIXED},'SelectedEventMode':best['EventMode'],'E0Metrics':{k:e0[k] for k in FULL},'SelectedModeMetrics':{k:best[k] for k in FULL},**{k:v for k,v in best.items() if k not in FULL and k not in FIXED and k!='EventMode'},'SelectionReason':reason,'YearlyMetrics':[r for r in data['yearly'] if r['EventMode']==best['EventMode']],'Status':'STAGE4_MODE_SELECTED_STAGE5_NOT_EXECUTED'}
        if s!=expected_selected:raise ValueError('selected conditions/metrics/yearly changed')
    counts={m:sum(s['SelectedEventMode']==m for s in selected) for m in MODES}
    if counts!=c['expected_selected_modes']:raise ValueError('formal runtime differs from expected Chat counts; stop without repair')
    if len(tables['results'])!=c['expected_variant_count']:raise ValueError('variant count mismatch')
    expected_counts=dict(CandidateCount=len(ids),VariantCount=len(ids)*3,SelectedModeCounts=counts,FilterAdoptionCount=counts['E1']+counts['E2'],E1AdoptionCount=counts['E1'],E2AdoptionCount=counts['E2'])
    if any(summary.get(k)!=v for k,v in expected_counts.items()):raise ValueError('summary counts mismatch')
    if progress!=dict(summary,CompletedJobs=len(ids),ExpectedJobs=len(ids),CompletedConfigurations=len(ids)*3):raise ValueError('completion accounting mismatch')
    distributions={k:dict(Count=len(selected),UndefinedCount=0,Min=min(s[k] for s in selected),Median=statistics.median(s[k] for s in selected),Max=max(s[k] for s in selected)) for k in ('RetentionRate','RemovedTrades','DeltaTotalR','DeltaAvgR','DeltaMaxDDR')}
    if summary['SelectedDistributions']!=distributions:raise ValueError('selected distribution mismatch')
    space=dict(CandidateCount=len(ids),VariantsPerCandidate=3,TheoreticalMax=len(ids)*3,ActualUniqueConfigurations=len(ids)*3,Modes=list(MODES),DeduplicateModes=False,NoRetuning=True,NoRefill=True,NoDrop=True)
    if meta['search_space.json']!=space:raise ValueError('Stage4 search space mismatch')
    return selected,tables,identity

def load_input(result_root,stage3_selected_path,c=None):
    c=load_config() if c is None else c;root=Path(result_root)
    if not root.is_dir():raise ValueError('formal Stage4 runtime unavailable; no reconstruction from review ZIP or Chat')
    raw={};hashes={}
    for name,digest in c['stage4_runtime_sha256'].items():
        p=root/name
        if not p.is_file():raise ValueError('formal Stage4 file missing: '+name)
        raw[name]=p.read_bytes();hashes[name]=hashlib.sha256(raw[name]).hexdigest()
        if hashes[name]!=digest:raise ValueError('formal Stage4 SHA mismatch: '+name)
    if hashes['stage4_selected_settings.json']!=c['stage4_selected_sha256'] or hashes['effective_config.json']!=c['stage4_config_sha256']:raise ValueError('selected/config exact SHA mismatch')
    prior=Path(stage3_selected_path).read_bytes()
    if hashlib.sha256(prior).hexdigest()!=c['stage3_selected_sha256']:raise ValueError('Stage3 reference SHA mismatch')
    meta={n:strict_json(v) for n,v in raw.items() if n.endswith('.json') and '/' not in n};ledger=meta['checkpoints.json']
    if any(hashes.get('shards/'+cid+'.json')!=h for cid,h in ledger.items()):raise ValueError('Stage4 shard ledger mismatch')
    shards={cid:strict_json(raw['shards/'+cid+'.json']) for cid in ledger}
    selected,tables,identity=validate_payload(meta,shards,strict_json(prior),c)
    schemas={}
    for kind,suffix in (('results','variant_results'),('yearly','yearly_results'),('diagnostics','event_diagnostics'),('selection_audit','selection_audit')):
        name='stage4_'+suffix+'.csv.gz';decoded=gzip.decompress(raw[name]);compare_table(decoded,tables[kind],name)
        columns=next(csv.reader(io.StringIO(decoded.decode())))
        if columns!=list(tables[kind][0]):raise ValueError('Stage4 CSV column order mismatch')
        schemas[name]=dict(Rows=len(tables[kind]),Columns=columns)
    review=meta['stage4_review.json'];ri={k:v for k,v in identity.items() if k!='inputs'};ri['M1InputCount']=56
    if any(review.get(k)!=v for k,v in dict(Summary=meta['stage4_summary.json'],Identity=ri,InputAudit=meta['stage3_input_audit.json'],CalendarAudit=meta['event_calendar_audit.json'],E0Audit=meta['e0_equivalence_audit.json']).items()):raise ValueError('Stage4 review inconsistent')
    names={'effective_config.json','stage3_input_audit.json','event_calendar.json','event_calendar_audit.json','e0_equivalence_audit.json','search_space.json','progress.json','stage4_variant_results.csv.gz','stage4_yearly_results.csv.gz','stage4_event_diagnostics.csv.gz','stage4_selection_audit.csv.gz','stage4_selected_settings.json','stage4_summary.json','stage4_review.json'}
    with zipfile.ZipFile(io.BytesIO(raw['stage4_review.zip'])) as z:
        if len(z.namelist())!=len(names) or set(z.namelist())!=names or any(z.read(n)!=raw[n] for n in names):raise ValueError('review ZIP content mismatch')
    audit=dict(Status='PASS',FormalResultRoot=root.name,ColabResultRoot='/content/drive/MyDrive/b6_stage4_archive',Stage4FreezeSHA=c['stage4_freeze_sha'],Stage4ConfigSHA256=c['stage4_config_sha256'],Stage3FreezeSHA=c['stage3_freeze_sha'],Stage3SelectedSHA256=c['stage3_selected_sha256'],FormalInputSHA256=hashes,SelectedSettingsSHA256=c['stage4_selected_sha256'],Schemas=schemas,CandidateCount=len(selected),VariantCount=len(tables['results']),SelectedModeCounts=meta['stage4_summary.json']['SelectedModeCounts'],CandidateDrop=0,State='COMPLETE_STAGE4_ONLY',SelectionConsistency='PASS',Stage3ConditionsUnchanged=True,E0OfficialEquivalence='STAGE4_RECORDED_PASS_AND_SAVED_METRICS_EXACT_MATCH',PriceReplayPerformed=False,ValidationExecuted=False,MonitorExecuted=False,PortfolioExecuted=False,Runtime=identity['runtime'],M1InputCount=len(identity['inputs']))
    return selected,shards,audit,identity
