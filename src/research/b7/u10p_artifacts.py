"""Persisted U10-P identity/schema/projection; no evaluator/metrics/selection imports."""
from copy import deepcopy
from collections import Counter
from .stage1_contract import ROOT,digest,object_hash
from .u10_artifacts import identity as prior_identity
from .u10p_input import input_config,CONFIG,INPUT,RESULT_SHA,PRODUCER_SHA
RELEASE=ROOT/'results/b7/u10p_implementation/release_manifest.json'
MODES=('P0','P1','P2','P3')

def identity(sha,env):
    cfg,data=input_config();out=prior_identity(sha,env)
    out.update(U10ResultFreezeSHA=RESULT_SHA,U10ProducerImplementationSHA=PRODUCER_SHA,U10PInputSHA256=digest(INPUT),U10PConfigSHA256=digest(CONFIG),FrozenU10PContract=cfg['FrozenU10PContract'],U10ArchiveIdentity={k:v for k,v in data.items() if k.startswith('Source')},CandidateIDs=data['CandidateIDs'],U10SourceCandidateHashes=[{k:r[k] for k in ('CandidateID','U10CandidateSHA256','U10CandidateObjectSHA256','U10CheckpointSHA256','E2TradeStreamSHA256')} for r in data['Candidates']])
    return out

def validate_result(out,record):
    if any(out.get(k)!=v for k,v in record.items()):raise ValueError('immutable input fields')
    if out.get('Status')!='PASS_U10P' or out.get('NoReplacement') is not True or out.get('FormalProtectionMode') not in MODES:raise ValueError('terminal status')
    b=out['P0Barrier']
    if b['Status']!='PASS' or b['E2TradeStreamSHA256']!=record['E2TradeStreamSHA256'] or b['MetricsExact'] is not True:raise ValueError('P0 barrier')
    modes=out['Modes']
    if set(modes)!=set(MODES) or modes['P0']['Metrics']!=record['DiscoveryE2Metrics']:raise ValueError('modes/P0 metrics')
    baseids=[t['TradeID'] for t in modes['P0']['TradeResults']]
    if len(baseids)!=len(set(baseids)) or object_hash(baseids)!=b['P0TradeIDsSHA256']:raise ValueError('P0 IDs')
    for name,d in modes.items():
        ts=d['TradeResults'];ids=[t['TradeID'] for t in ts]
        if d['Mode']!=name or len(ids)!=len(set(ids)) or set(ids)!=set(baseids) or d['Metrics']['Trades']!=len(ids):raise ValueError('fixed trade universe')
        if object_hash(ts)!=d['TradeStreamSHA256'] or object_hash(ids)!=d['TradeIDsSHA256']:raise ValueError('mode streams')
        if any(t['Mode']!=name or t['ActualCloseTime']!=t['CloseTime'] or t['FinalPips']!=t['Pips'] or t['FormalSL']!=record['FormalSL'] or t['FormalTP']!=record['FormalTP'] for t in ts):raise ValueError('trade schema')
        if any(type(d[k])is not bool for k in ['Applicable','U01GatePASS','AdoptionPASS']):raise ValueError('mode bool schema')
        if name!='P0':
            if not d['AdoptionChecks'] or any(type(v)is not bool for v in d['AdoptionChecks'].values()) or d['AdoptionPASS']!=all(d['AdoptionChecks'].values()):raise ValueError('persisted adoption schema')
            if d['AdoptionPASS'] and (not d['Applicable'] or not d['U01GatePASS']):raise ValueError('ineligible persisted PASS')
    ranked=out['RankedPASSModes']
    if len(ranked)!=len(set(ranked)) or set(ranked)!={m for m in MODES[1:] if modes[m]['AdoptionPASS']}:raise ValueError('ranked PASS inventory')
    if out['FormalProtectionMode']!=(ranked[0] if ranked else 'P0'):raise ValueError('persisted selected mode')
    return out

def summaries(results):
    pairs=sorted({r['Symbol'] for r in results});counts=dict(Counter(r['FormalProtectionMode'] for r in results));rows=[];wtl=[]
    for sym in pairs:
        rs=[r for r in results if r['Symbol']==sym]
        for name in MODES:
            ds=[r['Modes'][name] for r in rs]
            rows.append(dict(Symbol=sym,Mode=name,Candidates=len(rs),Applicable=sum(d['Applicable'] for d in ds),AdoptionPASS=sum(d['AdoptionPASS'] for d in ds),Trades=sum(d['Metrics']['Trades'] for d in ds),WinnerToLoserCount=sum(d['WinnerToLoserCount'] for d in ds)))
        base=sum(r['Modes']['P0']['WinnerToLoserCount'] for r in rs);chosen=sum(r['Modes'][r['FormalProtectionMode']]['WinnerToLoserCount'] for r in rs)
        wtl.append(dict(Symbol=sym,BaselineP0Count=base,SelectedModeCount=chosen,ReductionCount=base-chosen,ReductionFraction=(base-chosen)/base if base else None))
    return {'protection_summary.json':dict(CandidateCount=len(results),Counts={m:counts.get(m,0) for m in MODES},PairModes={s:dict(Counter(r['FormalProtectionMode'] for r in results if r['Symbol']==s)) for s in pairs},NoCandidateDrop=True,NoReplacement=True),'mode_summary.json':rows,'winner_to_loser_summary.json':wtl}

def project_candidate_freeze(record,candidate,candidate_sha,checkpoint_sha,producer_sha,data_hash,config_hash):
    validate_result(candidate,record);mode=candidate['FormalProtectionMode']
    return dict(deepcopy(record),FormalProtectionMode=mode,SelectedModeDiscoveryMetrics=deepcopy(candidate['Modes'][mode]['Metrics']),U10PStatus='PASS_U10P',U10PCandidateSHA256=candidate_sha,U10PCheckpointSHA256=checkpoint_sha,U10PProducerImplementationSHA=producer_sha,DataManifestSHA256=data_hash,U10PConfigSHA256=config_hash,SelectedModeTradeStreamSHA256=candidate['Modes'][mode]['TradeStreamSHA256'])
