"""Persisted Monitor schema/identity/count aggregation. No performance/Gate API imports."""
from copy import deepcopy
from collections import Counter
import re,math
from datetime import datetime
from .stage1_contract import ROOT,digest,object_hash,CONDITIONS_SHA
from .candidate_freeze import exact
from .monitor_input import input_config,CONFIG,INPUT,FREEZE_SHA,RESULT_SHA,PRODUCER_SHA,PERIOD,PAIRS,MODES
from .u11_artifacts import identity as prior_identity
RELEASE=ROOT/'results/b7/monitor_implementation/release_manifest.json'
def identity(sha,env):
    c,d=input_config();out=prior_identity(PRODUCER_SHA,env)
    out.update(ImplementationSHA=sha,MonitorImplementationSHA=sha,U11ResultFreezeSHA=RESULT_SHA,U11ProducerImplementationSHA=PRODUCER_SHA,MonitorInputSHA256=digest(INPUT),MonitorInputObjectSHA256=object_hash(d),MonitorConfigSHA256=digest(CONFIG),MonitorInputBytes=INPUT.stat().st_size,MonitorPeriod=PERIOD,MonitorStart=c['MonitorStart'],MonitorEnd=c['MonitorEnd'],MonitorStatus='OBSERVED_ONLY',NoReplacement=True,ValidationOverrideAllowed=False,PostValidationRetuningAllowed=False,CandidateIDs=d['CandidateIDs'],CandidateObjectSHA256=[dict(CandidateID=r['CandidateID'],SHA256=object_hash(r)) for r in d['Candidates']],ProtectionMapping={r['CandidateID']:r['FormalProtectionMode'] for r in d['Candidates']},U11SourceTrustedFilesSHA256=d['SourceTrustedFilesSHA256'],U11SourceCandidateResultsSHA256=d['SourceCandidateResultsSHA256'])
    return out

def validate_result(out,record):
    if any(k not in out or not exact(out[k],v) for k,v in record.items()):raise ValueError('immutable Candidate record')
    if out.get('CandidateFreezeSHA')!=FREEZE_SHA or not re.fullmatch('[0-9a-f]{40}',out.get('MonitorImplementationSHA','')):raise ValueError('implementation/Freeze identity')
    if out.get('MonitorPeriod')!=PERIOD or out.get('EventMode')!='E2':raise ValueError('period/event')
    if out.get('NoReplacement') is not True or out.get('PostValidationRetuningAllowed') is not False or out.get('ValidationOverrideAllowed') is not False:raise ValueError('fixed no-rescue flags')
    if out.get('MonitorStatus')!='OBSERVED_ONLY' or out.get('Status')!='OBSERVED_ONLY':raise ValueError('observed-only terminal status')
    if set(out)&{'FormalChecks','SampleChecks','FormalConditionsPASS','SampleSufficient','ValidationStatus','DDThreshold','MonitorPASS','MonitorFAIL'}:raise ValueError('no Monitor Gate fields')
    if out.get('U11ResultFreezeSHA')!=RESULT_SHA or out.get('U11ProducerImplementationSHA')!=PRODUCER_SHA:raise ValueError('source provenance')
    if not exact(out['DiscoveryBaseline'],record['SelectedModeDiscoveryMetrics']) or not exact(out['ValidationBaseline'],record['ValidationMetrics']):raise ValueError('immutable baselines')
    metrics=out['MonitorMetrics'];m=metrics['Combined'];a=metrics['Annual2026']
    if set(metrics)!={'Combined','Annual2026','Monthly'} or set(metrics['Monthly'])!={f'2026-{month:02d}' for month in range(1,10)} or not exact(a,m):raise ValueError('period metric schema')
    for block in [m,a,*metrics['Monthly'].values()]:
        if any(type(block[k]) is not int or block[k]<0 for k in ('Trades','Wins','Losses','ZeroPips')) or block['Wins']+block['Losses']+block['ZeroPips']!=block['Trades']:raise ValueError('metric count schema')
        for k in ('TotalPips','MaxDDPips'):
            if type(block[k]) not in (float,int) or not math.isfinite(block[k]):raise ValueError('numeric metric')
        if block['MaxDDPips']<0:raise ValueError('nonnegative DD')
        if (block['Trades']==0)!=(block['AvgPips'] is None):raise ValueError('Avg null iff no trades')
        if (block['Losses']>0)!=(block['PFState']=='FINITE') or (block['PFState']=='INF' and block['Wins']==0) or (block['PFState']=='UNDEFINED' and block['Wins']!=0):raise ValueError('PF count consistency')
        if block['AvgPips'] is None and block['Trades']!=0 or block['AvgPips'] is not None and (type(block['AvgPips']) not in (float,int) or not math.isfinite(block['AvgPips'])):raise ValueError('Avg schema')
        if block['PFState'] not in ('FINITE','INF','UNDEFINED') or (block['PFpips'] is not None)!=(block['PFState']=='FINITE'):raise ValueError('PF schema')
        if block['PFpips'] is not None and (type(block['PFpips']) not in (float,int) or not math.isfinite(block['PFpips']) or block['PFpips']<0):raise ValueError('finite PF value')
        if block['AvgPips']!=(block['TotalPips']/block['Trades'] if block['Trades'] else None):raise ValueError('persisted Avg arithmetic')
        if not block['Trades'] and (block['TotalPips']!=0 or block['MaxDDPips']!=0):raise ValueError('empty metric arithmetic')
        if block['PFState']=='FINITE' and ((block['Wins']==0)!=(block['PFpips']==0)):raise ValueError('PF zero consistency')
    for k in ('Trades','Wins','Losses','ZeroPips'):
        if sum(v[k] for v in metrics['Monthly'].values())!=m[k]:raise ValueError('monthly count arithmetic')
    ts=out['TradeResults'];ids=[t['TradeID'] for t in ts]
    if len(ts)!=m['Trades'] or len(ids)!=len(set(ids)):raise ValueError('unique selected stream count')
    if object_hash(ts)!=out['MonitorSelectedTradeStreamSHA256'] or object_hash(ids)!=out['MonitorTradeIDsSHA256']:raise ValueError('selected stream hashes')
    if ts!=sorted(ts,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey']))):raise ValueError('deterministic selected order')
    for month,block in metrics['Monthly'].items():
        if block['Trades']!=sum(t['EntryTime'].startswith(month) for t in ts):raise ValueError('persisted month assignment/count')
    for t in ts:
        required={'TradeID','CandidateID','EntryTime','PlannedEntryTimeJST','PlannedTimeExitJST','ScheduledExitTime','ActualCloseTime','CloseTime','Direction','EntryPrice','RawEntryOpen','FormalSL','FormalTP','FormalProtectionMode','ClosePrice','FinalPips','Pips','ExitReason','ExitDelayMinutes','MissingPathMinutes','MFEpips','MAEpips','GivebackPips','WinnerToLoser','TriggerReached','TriggerBar','ActivationBar','ProtectionActivated','ProtectionStop','ProtectionHit','FixedKey'}
        if not required<=set(t):raise ValueError('complete trade schema')
        for k in ('EntryPrice','RawEntryOpen','ClosePrice','FinalPips','Pips','MFEpips','MAEpips','GivebackPips'):
            if type(t[k]) not in (int,float) or not math.isfinite(t[k]):raise ValueError('finite persisted trade number')
        if t['MFEpips']<0 or t['MAEpips']<0:raise ValueError('nonnegative excursions')
        if any(type(t[k]) is not bool for k in ('WinnerToLoser','TriggerReached','ProtectionActivated','ProtectionHit')):raise ValueError('trade flags')
        if type(t['ExitDelayMinutes']) is not int or not 0<=t['ExitDelayMinutes']<=4 or type(t['MissingPathMinutes']) is not int or t['MissingPathMinutes']<0:raise ValueError('execution diagnostics')
        for k in ('EntryTime','CloseTime','ActualCloseTime','PlannedEntryTimeJST','PlannedTimeExitJST'):
            if not '2026-01-01 00:00:00'<=t[k]<'2026-09-10 00:00:00':raise ValueError('Monitor-only persisted trade')
        if t['CandidateID']!=record['CandidateID'] or t['FormalProtectionMode']!=record['FormalProtectionMode'] or t['Mode']!=record['FormalProtectionMode'] or t['FormalSL']!=record['FormalSL'] or t['FormalTP']!=record['FormalTP'] or t['Direction']!=record['Direction']:raise ValueError('trade strategy identity')
        entry=datetime.fromisoformat(t['EntryTime']);planned=datetime.fromisoformat(t['PlannedTimeExitJST']);close=datetime.fromisoformat(t['CloseTime'])
        if any(x.tzinfo is not None or x.second or x.microsecond for x in (entry,planned,close)):raise ValueError('naive exact-minute trade times')
        if t['PlannedEntryTimeJST']!=t['EntryTime'] or t['ScheduledExitTime']!=t['PlannedTimeExitJST'] or close<entry:raise ValueError('planned/actual times')
        bucket='D1' if entry.day<=10 else 'D2' if entry.day<=20 else 'D3'
        key=[record['Symbol'],int(record['Direction']=='SHORT'),entry.weekday(),record['FormalEntryMinute'],record['FormalExitDayOffset'],record['FormalExitMinute'],record['FormalHoldingMinutes'],record['CandidateID']]
        if t['FixedKey']!=key or entry.hour*60+entry.minute!=record['FormalEntryMinute'] or planned.hour*60+planned.minute!=record['FormalExitMinute'] or (planned.date()-entry.date()).days!=record['FormalExitDayOffset'] or (planned-entry).total_seconds()/60!=record['FormalHoldingMinutes'] or entry.weekday() not in record['FormalWeekdays'] or entry.month not in record['FormalMonths'] or bucket not in record['FormalDOMBuckets']:raise ValueError('persisted frozen schedule')
        if t['ActualCloseTime']!=t['CloseTime'] or t['FinalPips']!=t['Pips'] or t['TradeID']!=object_hash([record['CandidateID'],t['PlannedEntryTimeJST'],t['PlannedTimeExitJST']]):raise ValueError('trade identity')
    for h in ('MonitorE2BaselineTradeStreamSHA256','E2TradeIDsSHA256','MonitorSelectedTradeStreamSHA256','MonitorTradeIDsSHA256'):
        if not re.fullmatch('[0-9a-f]{64}',out[h]):raise ValueError('stream SHA format')
    e=out['EventDiagnostics'];n=e['E0ExecutableTrades'];kept=e['E2Trades'];removed=e['RemovedTrades']
    if any(type(e[k]) is not int or e[k]<0 for k in ('E0ExecutableTrades','E2Trades','RemovedTrades','MultiEventOverlapTradeCount')):raise ValueError('event count types')
    if not re.fullmatch('[0-9a-f]{64}',e['RemovedTradeIDsSHA256']):raise ValueError('removed IDs SHA')
    if kept!=len(ts) or n-kept!=removed or e['Retention']!=(kept/n if n else None):raise ValueError('event count/retention')
    if set(e['RemovedByEvent'])!=set(record['E2EventSet']) or any(type(v)is not int or not 0<=v<=removed for v in e['RemovedByEvent'].values()) or sum(e['RemovedByEvent'].values())<removed or not 0<=e['MultiEventOverlapTradeCount']<=removed:raise ValueError('event removal schema')
    if out['Diagnostics']['DiagnosticsOnly'] is not True or out['Diagnostics']['RetentionGateAdded'] is not False:raise ValueError('diagnostics not gates')
    return out

def summaries(results):
    pairs={s:sum(r['Symbol']==s for r in results) for s in PAIRS}
    modes={m:sum(r['FormalProtectionMode']==m for r in results) for m in MODES}
    return {'monitor_summary.json':dict(CandidateCount=len(results),Status='OBSERVED_ONLY',PairCounts=pairs,ProtectionModeCounts=modes,NoReplacement=True,ValidationOverrideAllowed=False),'pair_summary.json':{s:dict(CandidateCount=n,Status='OBSERVED_ONLY') for s,n in pairs.items()},'event_summary.json':dict(DiagnosticsOnly=True,Candidates=[dict(CandidateID=r['CandidateID'],**r['EventDiagnostics']) for r in results]),'diagnostic_summary.json':dict(DiagnosticsOnly=True,Candidates=[dict(CandidateID=r['CandidateID'],**r['Diagnostics']) for r in results])}
