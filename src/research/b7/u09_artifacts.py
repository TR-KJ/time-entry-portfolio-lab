"""Persisted U09 schema validation and aggregation only; no policy recomputation."""
from collections import Counter
from .stage1_contract import ROOT,CONDITIONS_SHA,digest
from .u09_input import input_config,INPUT,CONFIG,RESULT_SHA,SUPPLEMENT_SHA,SUPPLEMENT,SUPPLEMENT_HASH
from .u06_finalize_only import read
RELEASE=ROOT/'results/b7/u09_implementation/release_manifest.json'
DECISIONS=('FINE_TUNED','ANCHOR_RETAINED_NO_1M_PLATEAU','ANCHOR_RETAINED_BEST_IS_ANCHOR','ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE','ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT')

def identity(producer_sha,environment):
    _,data=input_config()
    return dict(ImplementationSHA=producer_sha,ConditionsFreezeSHA=CONDITIONS_SHA,U09SupplementalConditionsFreezeSHA=SUPPLEMENT_SHA,SupplementalPrespecSHA256=SUPPLEMENT_HASH,FullPrespecSHA256=digest(ROOT/'research_inputs/b7/full_research_prespec.json'),U09ConfigSHA256=digest(CONFIG),U08ResultFreezeSHA=RESULT_SHA,U09InputSHA256=digest(INPUT),M1ManifestSHA256=digest(ROOT/'research_inputs/b7/expected_m1_manifest.csv'),M1ExactIdentity=read(ROOT/'results/b7/u08/input_identity.json')['M1ExactIdentity'],Environment=environment,CandidateIDs=[r['CandidateID'] for r in data['Candidates']])

def validate_result(out,r):
    for k in ('CandidateID','Symbol','PairRank','FormalSL','FormalTP','AnchorWeekday','FormalWeekdays','SetName','FormalDOMBuckets','OFFBuckets','FormalMonths','OFFMonths','CalendarFreeze'):
        if out.get(k)!=r[k]:raise ValueError('fixed U09 result identity')
    src={k:r[k] for k in ('U08Status','U08CandidateSHA256','U08CheckpointSHA256','U08ProducerImplementationSHA','U07SourceIdentity','U06SourceIdentity')}
    if out.get('U08SourceIdentity')!=src or out.get('AnchorSchedule')!=r['Schedule'] or out.get('Direction')!=r['Schedule']['Direction']:raise ValueError('U08 lineage/anchor')
    if out.get('Status')!='PASS_U09' or out.get('Decision') not in DECISIONS:raise ValueError('terminal non-drop status')
    ps=out['Points'];ns=out['Plateaus'];ids=[p['PointID'] for p in ps]
    expected=[f'{e:+d}/{x:+d}' for e in range(-5,6) for x in range(-5,6)]
    if out['NominalPointCount']!=121 or ids!=expected or [n['CenterPointID'] for n in ns]!=ids:raise ValueError('121 ordered point/center inventory')
    byid=dict(zip(ids,ps))
    for p in ps:
        if p['PointID']!=f"{p['EntryShiftMinutes']:+d}/{p['ExitShiftMinutes']:+d}" or type(p['Valid']) is not bool or type(p['FormalPASS']) is not bool:raise ValueError('point schema')
        if p['Valid']:
            if p['InvalidReason'] is not None or p['Metrics'] is None:raise ValueError('valid metrics')
            if p['FormalPASS'] and p['Metrics']['AvgPips'] is None:raise ValueError('FormalPASS null Avg invariant')
        elif p['InvalidReason'] is None or p['Metrics'] is not None or p['FormalPASS']:raise ValueError('invalid exclusion schema')
    if out['ValidPointCount']!=sum(p['Valid'] for p in ps) or out['InvalidPointCount']!=sum(not p['Valid'] for p in ps):raise ValueError('point counts')
    for n in ns:
        members=n['NeighborhoodMembers']
        if len(members)!=len(set(members)) or any(i not in byid or not byid[i]['Valid'] for i in members) or len(members)!=n['ValidPointCount']:raise ValueError('neighborhood member schema')
        if n['CenterMetrics']!=byid[n['CenterPointID']]['Metrics']:raise ValueError('center metrics projection')
        if n['PlateauPASS'] and (n['AllValidMedianAvgPips'] is None or n['NeighborhoodMedianPFpips'] is None):raise ValueError('ranking defined invariant')
    ranked=out['RankedPlateau'];nb={n['CenterPointID']:n for n in ns}
    if len(ranked)!=len(set(ranked)) or len(ranked)!=out['PlateauCandidateCount'] or set(ranked)!={n['CenterPointID'] for n in ns if n['PlateauPASS']}:raise ValueError('ranked inventory')
    if out['BestCandidate']!=(ranked[0] if ranked else None) or out['AnchorNeighborhood']!=nb['+0/+0'] or out['AnchorBaseline']!=nb['+0/+0']['AllValidMedianAvgPips']:raise ValueError('selection projection')
    chosen=byid[out['BestCandidate'] if out['Decision']=='FINE_TUNED' else '+0/+0']
    if not chosen['Valid']:raise ValueError('final valid')
    for k in ('EntryMinute','ExitMinute','ExitDayOffset','HoldingMinutes'):
        if out['Anchor'+k]!=r['Schedule'][k] or out['Formal'+k]!=chosen[k]:raise ValueError('formal schedule projection')
    for k in ('EntryShiftMinutes','ExitShiftMinutes'):
        if out[k]!=chosen[k]:raise ValueError('final shift')
    return out

def summaries(results):
    return {'decision_summary.json':dict(CandidateCount=len(results),Decisions=dict(sorted(Counter(r['Decision'] for r in results).items())),NoCandidateDrop=True),
            'shift_summary.json':[dict(CandidateID=r['CandidateID'],Decision=r['Decision'],**{k:r[k] for k in ('FormalEntryMinute','FormalExitMinute','FormalExitDayOffset','FormalHoldingMinutes','EntryShiftMinutes','ExitShiftMinutes')}) for r in results]}
