"""Persisted U11 decision and Monitor projection audits; no price/performance APIs."""
from copy import deepcopy
from .stage1_contract import object_hash

def audit_saved_decision(result):
    m=result['ValidationMetrics'];a=m['Annual2024'];b=m['Annual2025'];v=m['Combined']
    sample=dict(Trades2024=a['Trades']>=30,Trades2025=b['Trades']>=30,CombinedTrades=v['Trades']>=70,Losses2024=a['Losses']>=5,Losses2025=b['Losses']>=5)
    limit=result['SelectedModeDiscoveryMetrics']['MaxDDPips']*1.5
    formal=dict(TotalPips2024=a['TotalPips']>0,TotalPips2025=b['TotalPips']>0,AvgPips=v['AvgPips'] is not None and v['AvgPips']>0,PFpips=v['PFState']=='FINITE' and v['PFpips'] is not None and v['PFpips']>=1.1,MaxDDPips=v['MaxDDPips']<=limit)
    sufficient=all(sample.values())
    if sufficient and (v['PFState']!='FINITE' or v['PFpips'] is None):raise ValueError('sample/PF contradiction')
    status='INSUFFICIENT_SAMPLE' if not sufficient else ('PASS' if all(formal.values()) else 'FAIL')
    if sample!=result['SampleChecks'] or formal!=result['FormalChecks'] or sufficient!=result['SampleSufficient'] or all(formal.values())!=result['FormalConditionsPASS'] or status!=result['ValidationStatus'] or status!=result['Status'] or limit!=result['DDThreshold']:raise ValueError('saved decision inconsistency')
    return dict(SampleChecks=sample,FormalChecks=formal,Status=status,DDThreshold=limit)

def validate_monitor(data,records,pass_inventory,trusted_files,producer_sha):
    """Check ordered eligibility, exact frozen strategy, source hashes and no-run flags."""
    ids=[r['CandidateID'] for r in pass_inventory]
    expected=[r for r in records if r['CandidateID'] in set(ids)]
    if len(ids)!=22 or len(set(ids))!=22 or ids!=[r['CandidateID'] for r in expected]:raise ValueError('original-order PASS22 only')
    if any(r['Status']!='PASS' or r['FailedChecks'] for r in pass_inventory):raise ValueError('PASS inventory')
    if data['Scope']!='B7_MONITOR_FORMAL_INPUT' or data['CandidateCount']!=22 or data['CandidateIDs']!=ids or len(data['Candidates'])!=22:raise ValueError('Monitor inventory')
    if data['MonitorPerformanceEvaluated'] is not False or data['ValidationOverrideAllowed'] is not False or data['NoReplacement'] is not True or data['MonitorStatus']!='OBSERVED_ONLY' or data['MonitorPeriod']!='[2026-01-01, 2026-09-10) JST':raise ValueError('Monitor scope')
    if data['U11ProducerImplementationSHA']!=producer_sha:raise ValueError('Producer pin')
    trusted={x['Path']:x['SHA256'] for x in trusted_files}
    if data['SourceTrustedFilesSHA256']!=object_hash(trusted_files):raise ValueError('trusted aggregate')
    for original,out,row in zip(expected,data['Candidates'],pass_inventory):
        if any(out.get(k)!=v for k,v in original.items()) or out['CandidateID']!=row['CandidateID']:raise ValueError('immutable strategy record')
        stem='jobs/'+original['CandidateID']+'/'
        if out['U11ValidationStatus']!='PASS' or out['U11ProducerImplementationSHA']!=producer_sha or out['U11CandidateSHA256']!=trusted[stem+'candidate.json'] or out['U11CheckpointSHA256']!=trusted[stem+'checkpoint.json']:raise ValueError('source identity')
        m=out['ValidationMetrics'];v=m['Combined']
        values=[m['Annual2024']['TotalPips'],m['Annual2025']['TotalPips'],v['AvgPips'],v['PFpips'],v['MaxDDPips']]
        if values!=[row[k] for k in ('TotalPips2024','TotalPips2025','AvgPips','PFpips','ValidationDD')]:raise ValueError('saved metrics projection')
    for sym,n in data['PairCounts'].items():
        if n!=sum(r['Symbol']==sym for r in expected):raise ValueError('pair count')
    if data['ProtectionModeCounts']!={m:sum(r['FormalProtectionMode']==m for r in expected) for m in ('P0','P1','P2','P3')}:raise ValueError('protection count')
    return deepcopy(data)
