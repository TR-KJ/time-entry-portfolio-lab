"""Persisted U11 schema/identity/count aggregation. No performance/Gate API imports."""
from copy import deepcopy
from collections import Counter
import re,math
from .stage1_contract import ROOT,digest,object_hash,CONDITIONS_SHA
from .candidate_freeze import exact
from .u11_input import input_config,CONFIG,INPUT,FREEZE_SHA
from .u10p_artifacts import identity as prior_identity
RELEASE=ROOT/'results/b7/u11_implementation/release_manifest.json'
STATUSES=('PASS','FAIL','INSUFFICIENT_SAMPLE')
SAMPLE=('Trades2024','Trades2025','CombinedTrades','Losses2024','Losses2025')
FORMAL=('TotalPips2024','TotalPips2025','AvgPips','PFpips','MaxDDPips')

def identity(sha,env):
    c,d=input_config();out=prior_identity(sha,env)
    out.update(U11ImplementationSHA=sha,CandidateFreezeSHA=FREEZE_SHA,U10PResultFreezeSHA=c['U10PResultFreezeSHA'],U11InputSHA256=digest(INPUT),U11InputObjectSHA256=object_hash(d),U11ConfigSHA256=digest(CONFIG),FrozenU11Contract=c['FrozenU11Contract'],U11ContractSHA256=object_hash(c['FrozenU11Contract']),CandidateFingerprints=c['Fingerprints'],CandidateObjectSHA256=[dict(CandidateID=r['CandidateID'],SHA256=object_hash(r)) for r in d['Candidates']],ValidationStart=c['ValidationStart'],ValidationEnd=c['ValidationEnd'],FrozenEnvironmentAndExecution=c['FrozenEnvironmentAndExecution'],CandidateIDs=d['CandidateIDs'],ProtectionMapping={r['CandidateID']:r['FormalProtectionMode'] for r in d['Candidates']})
    return out

def validate_result(out,record):
    if any(k not in out or not exact(out[k],v) for k,v in record.items()):raise ValueError('immutable Candidate record')
    if out.get('CandidateFreezeSHA')!=FREEZE_SHA or not re.fullmatch('[0-9a-f]{40}',out.get('U11ImplementationSHA','')):raise ValueError('implementation/Freeze identity')
    if out.get('ValidationPeriod')!='[2024-01-01, 2026-01-01) JST' or out.get('EventMode')!='E2':raise ValueError('period/event')
    if out.get('NoReplacement') is not True or out.get('PostValidationRetuningAllowed') is not False or out.get('RescuePASSAllowed') is not False:raise ValueError('fixed no-rescue flags')
    if out.get('ValidationStatus') not in STATUSES or out.get('Status')!=out['ValidationStatus']:raise ValueError('terminal status')
    if not exact(out['DiscoveryBaseline'],record['SelectedModeDiscoveryMetrics']):raise ValueError('selected Discovery baseline')
    metrics=out['ValidationMetrics'];m=metrics['Combined'];a=metrics['Annual2024'];b=metrics['Annual2025']
    if set(metrics)!={'Combined','Annual2024','Annual2025','Monthly'} or set(metrics['Monthly'])!={f'{y}-{month:02d}' for y in (2024,2025) for month in range(1,13)}:raise ValueError('period metric schema')
    for block in [m,a,b,*metrics['Monthly'].values()]:
        if any(type(block[k]) is not int or block[k]<0 for k in ('Trades','Wins','Losses','ZeroPips')) or block['Wins']+block['Losses']+block['ZeroPips']!=block['Trades']:raise ValueError('metric count schema')
        for k in ('TotalPips','MaxDDPips'):
            if type(block[k]) not in (float,int) or not math.isfinite(block[k]):raise ValueError('numeric metric')
        if block['MaxDDPips']<0:raise ValueError('nonnegative DD')
        if (block['Trades']==0)!=(block['AvgPips'] is None):raise ValueError('Avg null iff no trades')
        if (block['Losses']>0)!=(block['PFState']=='FINITE') or (block['PFState']=='INF' and block['Wins']==0) or (block['PFState']=='UNDEFINED' and block['Wins']!=0):raise ValueError('PF count consistency')
        if block['AvgPips'] is None and block['Trades']!=0 or block['AvgPips'] is not None and (type(block['AvgPips']) not in (float,int) or not math.isfinite(block['AvgPips'])):raise ValueError('Avg schema')
        if block['PFState'] not in ('FINITE','INF','UNDEFINED') or (block['PFpips'] is not None)!=(block['PFState']=='FINITE'):raise ValueError('PF schema')
        if block['PFpips'] is not None and (type(block['PFpips']) not in (float,int) or not math.isfinite(block['PFpips']) or block['PFpips']<0):raise ValueError('finite PF value')
    for k in ('Trades','Wins','Losses','ZeroPips'):
        if a[k]+b[k]!=m[k] or any(sum(v[k] for month,v in metrics['Monthly'].items() if month.startswith(y))!=block[k] for y,block in [('2024',a),('2025',b)]):raise ValueError('annual/monthly count arithmetic')
    sample=out['SampleChecks'];formal=out['FormalChecks']
    if set(sample)!=set(SAMPLE) or set(formal)!=set(FORMAL) or any(type(v)is not bool for v in [*sample.values(),*formal.values()]):raise ValueError('persisted check schema')
    # Persisted arithmetic consistency only. Never call metrics, Gate or status selector APIs.
    expected_sample=dict(Trades2024=a['Trades']>=30,Trades2025=b['Trades']>=30,CombinedTrades=m['Trades']>=70,Losses2024=a['Losses']>=5,Losses2025=b['Losses']>=5)
    threshold=record['SelectedModeDiscoveryMetrics']['MaxDDPips']*1.50
    expected_formal=dict(TotalPips2024=a['TotalPips']>0,TotalPips2025=b['TotalPips']>0,AvgPips=m['AvgPips'] is not None and m['AvgPips']>0,PFpips=m['PFState']=='FINITE' and m['PFpips'] is not None and m['PFpips']>=1.10,MaxDDPips=m['MaxDDPips']<=threshold)
    if sample!=expected_sample or formal!=expected_formal or out['DDThreshold']!=threshold:raise ValueError('persisted arithmetic')
    if type(out['SampleSufficient']) is not bool or type(out['FormalConditionsPASS']) is not bool or out['SampleSufficient']!=all(sample.values()) or out['FormalConditionsPASS']!=all(formal.values()):raise ValueError('persisted conjunctions')
    if out['SampleSufficient'] and (m['PFState']!='FINITE' or m['PFpips'] is None):raise ValueError('sufficient finite PF invariant')
    status=out['ValidationStatus']
    if (status=='INSUFFICIENT_SAMPLE')!=(not out['SampleSufficient']) or (status=='PASS')!=(out['SampleSufficient'] and out['FormalConditionsPASS']) or (status=='FAIL')!=(out['SampleSufficient'] and not out['FormalConditionsPASS']):raise ValueError('persisted status precedence')
    ts=out['TradeResults'];ids=[t['TradeID'] for t in ts]
    if len(ts)!=m['Trades'] or len(ids)!=len(set(ids)):raise ValueError('unique selected stream count')
    if object_hash(ts)!=out['ValidationSelectedTradeStreamSHA256'] or object_hash(ids)!=out['ValidationTradeIDsSHA256']:raise ValueError('selected stream hashes')
    if ts!=sorted(ts,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey']))):raise ValueError('deterministic selected order')
    for t in ts:
        required={'TradeID','CandidateID','EntryTime','PlannedEntryTimeJST','PlannedTimeExitJST','ScheduledExitTime','ActualCloseTime','CloseTime','Direction','EntryPrice','RawEntryOpen','FormalSL','FormalTP','FormalProtectionMode','ClosePrice','FinalPips','Pips','ExitReason','ExitDelayMinutes','MissingPathMinutes','MFEpips','MAEpips','GivebackPips','WinnerToLoser','TriggerReached','TriggerBar','ActivationBar','ProtectionActivated','ProtectionStop','ProtectionHit','FixedKey'}
        if not required<=set(t):raise ValueError('complete trade schema')
        for k in ('EntryPrice','RawEntryOpen','ClosePrice','FinalPips','Pips','MFEpips','MAEpips','GivebackPips'):
            if type(t[k]) not in (int,float) or not math.isfinite(t[k]):raise ValueError('finite persisted trade number')
        if t['MFEpips']<0 or t['MAEpips']<0:raise ValueError('nonnegative excursions')
        if any(type(t[k]) is not bool for k in ('WinnerToLoser','TriggerReached','ProtectionActivated','ProtectionHit')):raise ValueError('trade flags')
        if type(t['ExitDelayMinutes']) is not int or not 0<=t['ExitDelayMinutes']<=4 or type(t['MissingPathMinutes']) is not int or t['MissingPathMinutes']<0:raise ValueError('execution diagnostics')
        for k in ('EntryTime','CloseTime','ActualCloseTime','PlannedEntryTimeJST','PlannedTimeExitJST'):
            if not '2024-01-01 00:00:00'<=t[k]<'2026-01-01 00:00:00':raise ValueError('Validation-only persisted trade')
        if t['CandidateID']!=record['CandidateID'] or t['FormalProtectionMode']!=record['FormalProtectionMode'] or t['Mode']!=record['FormalProtectionMode'] or t['FormalSL']!=record['FormalSL'] or t['FormalTP']!=record['FormalTP'] or t['Direction']!=record['Direction']:raise ValueError('trade strategy identity')
        if t['ActualCloseTime']!=t['CloseTime'] or t['FinalPips']!=t['Pips'] or t['TradeID']!=object_hash([record['CandidateID'],t['PlannedEntryTimeJST'],t['PlannedTimeExitJST']]):raise ValueError('trade identity')
    for h in ('ValidationE2BaselineTradeStreamSHA256','E2TradeIDsSHA256','ValidationSelectedTradeStreamSHA256','ValidationTradeIDsSHA256'):
        if not re.fullmatch('[0-9a-f]{64}',out[h]):raise ValueError('stream SHA format')
    e=out['EventDiagnostics'];n=e['E0ExecutableTrades'];kept=e['E2Trades'];removed=e['RemovedTrades']
    if kept!=len(ts) or n-kept!=removed or e['Retention']!=(kept/n if n else None):raise ValueError('event count/retention')
    if set(e['RemovedByEvent'])!=set(record['E2EventSet']) or any(type(v)is not int or not 0<=v<=removed for v in e['RemovedByEvent'].values()) or sum(e['RemovedByEvent'].values())<removed or not 0<=e['MultiEventOverlapTradeCount']<=removed:raise ValueError('event removal schema')
    if out['Diagnostics']['DiagnosticsOnly'] is not True or out['Diagnostics']['RetentionGateAdded'] is not False:raise ValueError('diagnostics not gates')
    return out

def summaries(results):
    pairs=sorted({r['Symbol'] for r in results});counts={s:sum(r['ValidationStatus']==s for r in results) for s in STATUSES}
    event=[]
    for sym in pairs:
        es=[r['EventDiagnostics'] for r in results if r['Symbol']==sym];n=sum(e['E0ExecutableTrades'] for e in es);k=sum(e['E2Trades'] for e in es)
        event.append(dict(Symbol=sym,E0ExecutableTrades=n,E2Trades=k,RemovedTrades=n-k,Retention=k/n if n else None,RemovedByEvent={name:sum(e['RemovedByEvent'].get(name,0) for e in es) for name in sorted({n for e in es for n in e['RemovedByEvent']})},MultiEventOverlapTradeCount=sum(e['MultiEventOverlapTradeCount'] for e in es)))
    return {'status_summary.json':dict(CandidateCount=len(results),Counts=counts,NoReplacement=True),'pair_summary.json':{sym:{s:sum(r['Symbol']==sym and r['ValidationStatus']==s for r in results) for s in STATUSES} for sym in pairs},'sample_summary.json':dict(FailedChecks={k:sum(not r['SampleChecks'][k] for r in results) for k in SAMPLE}),'formal_check_summary.json':dict(SufficientSampleFormalFailureCounts={k:sum(r['SampleSufficient'] and not r['FormalChecks'][k] for r in results) for k in FORMAL},InsufficientSampleDiagnosticFalseCounts={k:sum(not r['SampleSufficient'] and not r['FormalChecks'][k] for r in results) for k in FORMAL},InsufficientCountsAreNotFormalFailureReasons=True),'event_summary.json':dict(Pairs=event,Candidates=[dict(CandidateID=r['CandidateID'],**r['EventDiagnostics']) for r in results]),'diagnostic_summary.json':dict(DiagnosticsOnly=True,Candidates=[dict(CandidateID=r['CandidateID'],**r['Diagnostics']) for r in results])}

def project_monitor(record,candidate,candidate_sha,checkpoint_sha,producer_sha):
    validate_result(candidate,record)
    if candidate['ValidationStatus']!='PASS':raise ValueError('formal Validation PASS only')
    return dict(deepcopy(record),U11ValidationStatus='PASS',U11CandidateSHA256=candidate_sha,U11CheckpointSHA256=checkpoint_sha,U11ProducerImplementationSHA=producer_sha,ValidationSelectedTradeStreamSHA256=candidate['ValidationSelectedTradeStreamSHA256'],ValidationMetrics=deepcopy(candidate['ValidationMetrics']))
