"""U10 persisted schema, identity and summaries; no execution/filter/gate policy."""
from copy import deepcopy
from collections import Counter
from .stage1_contract import ROOT,CONDITIONS_SHA,digest,object_hash
from .u10_input import input_config,CONFIG,CALENDAR,RESULT_SHA,SUPPLEMENT_SHA,SUPPLEMENT_HASH,CALENDAR_COMMIT,SOURCE_PATH,SOURCE_BLOB,SOURCE_SHA
RELEASE=ROOT/'results/b7/u10_implementation/release_manifest.json'
CHECKS=('TotalTrades','Annual2020','Annual2021','Annual2022','Annual2023','TotalLosses','AvgPips','FinitePF','PFpips','PositiveYearCount')

def identity(sha,env):
    c,d=input_config()
    return dict(ImplementationSHA=sha,ConditionsFreezeSHA=CONDITIONS_SHA,U09SupplementalConditionsFreezeSHA='1466a2c3e8b3d523233c45d665a6cac21e974393',U10SupplementalConditionsFreezeSHA=SUPPLEMENT_SHA,SupplementalPrespecSHA256=SUPPLEMENT_HASH,FullPrespecSHA256=digest(ROOT/'research_inputs/b7/full_research_prespec.json'),U10ConfigSHA256=digest(CONFIG),U09ResultFreezeSHA=RESULT_SHA,U09ProducerSHA=c['U09ProducerSHA'],U10InputSHA256=c['InputSHA256'],CalendarSourceCommit=CALENDAR_COMMIT,CalendarSourcePath=SOURCE_PATH,CalendarSourceBlobSHA=SOURCE_BLOB,CalendarSourceSHA256=SOURCE_SHA,EventCalendarSHA256=digest(CALENDAR),FrozenEventContract=c['FrozenEventContract'],M1ManifestSHA256=digest(ROOT/'research_inputs/b7/expected_m1_manifest.csv'),M1ExactIdentity=__import__('json').loads((ROOT/'results/b7/u09/input_identity.json').read_text())['M1ExactIdentity'],U09ArchiveIdentity={k:v for k,v in d.items() if k.startswith('Source')},SourceCandidateHashes=[{k:r[k] for k in ('CandidateID','U09CandidateSHA256','U09CheckpointSHA256')} for r in d['Candidates']],Environment=env,CandidateIDs=d['CandidateIDs'])

def result(record,modes,checks,streams):
    out=deepcopy(record);failed=[k for k in CHECKS if not checks[k]]
    out.update(FormalEventMode='E2',NoReplacement=True,CalendarSourceCommit=CALENDAR_COMMIT,EventCalendarSHA256=digest(CALENDAR),Modes=modes,PostE2GatePASS=not failed,GateChecks=checks,FailedChecks=failed,Status='DROP_U10_E2_GATE' if failed else 'PASS_U10',DropReason='POST_E2_U01_EQUIVALENT_GATE' if failed else None,TradeStreamSHA256={m:object_hash(streams[m]) for m in ('E0','E1','E2')},TradeIDsSHA256={m:object_hash([t['TradeID'] for t in streams[m]]) for m in ('E0','E1','E2')})
    return out

def validate_result(out,record):
    for k,v in record.items():
        if out.get(k)!=v:raise ValueError('fixed schedule/calendar/lineage')
    if out.get('FormalEventMode')!='E2' or out.get('NoReplacement') is not True or out.get('CalendarSourceCommit')!=CALENDAR_COMMIT or out.get('EventCalendarSHA256')!=digest(CALENDAR):raise ValueError('event identity')
    if out.get('Status') not in ('PASS_U10','DROP_U10_E2_GATE') or type(out.get('PostE2GatePASS')) is not bool:raise ValueError('terminal status')
    checks=out['GateChecks']
    if set(checks)!=set(CHECKS) or any(type(v)is not bool for v in checks.values()):raise ValueError('gate schema')
    failed=[k for k in CHECKS if not checks[k]]
    if out['FailedChecks']!=failed or out['PostE2GatePASS']!=(not failed) or (out['Status']=='PASS_U10')!=(not failed) or out['DropReason']!=('POST_E2_U01_EQUIVALENT_GATE' if failed else None):raise ValueError('persisted gate/status consistency')
    if set(out['Modes'])!={'E0','E1','E2'}:raise ValueError('three modes')
    bank={'USD':'FOMC','JPY':'BOJ','EUR':'ECB','GBP':'BOE','AUD':'RBA'};sym=record['Symbol']
    e1=sorted({bank[sym[:3]],bank[sym[3:]]});e2=sorted(set(e1)|{'US_NFP','US_CPI'}|({'AUD_CPI'} if 'AUD' in (sym[:3],sym[3:]) else set()))
    counts=[];base=out['Modes']['E0']['Metrics']['Trades']
    for name,events in [('E0',[]),('E1',e1),('E2',e2)]:
        d=out['Modes'][name];m=d['Metrics'];n=m['Trades'];removed=d['RemovedTrades']
        if d['EventSet']!=events or type(n)is not int or n<0 or removed!=base-n:raise ValueError('mode counts/events')
        if d['Retention']!=(n/base if base else None):raise ValueError('retention schema')
        if m['Wins']+m['Losses']+m['ZeroPips']!=n or set(m['Annual'])!={'2020','2021','2022','2023'} or sum(a['Trades'] for a in m['Annual'].values())!=n:raise ValueError('metric count schema')
        for block in [m,*m['Annual'].values()]:
            if block['PFState'] not in ('FINITE','INF','UNDEFINED') or (block['PFpips'] is not None)!=(block['PFState']=='FINITE'):raise ValueError('PF schema')
        if set(d['RemovedByEvent'])!=set(events) or any(type(v)is not int or v<0 or v>removed for v in d['RemovedByEvent'].values()) or sum(d['RemovedByEvent'].values())<removed:raise ValueError('removed event schema')
        if not 0<=d['MultiEventOverlapTradeCount']<=removed:raise ValueError('multi-event count')
        for h in (out['TradeStreamSHA256'][name],out['TradeIDsSHA256'][name],d['RemovedTradeIDsSHA256']):
            if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('stream hashes')
        counts.append(n)
    if not counts[0]>=counts[1]>=counts[2] or out['Modes']['E0']['RemovedTrades']!=0:raise ValueError('subset count invariant')
    return out

def summaries(results):
    results=sorted(results,key=lambda r:r['CandidateID']);pairs=sorted({r['Symbol'] for r in results});event=[];mode=[]
    for sym in pairs:
        rs=[r for r in results if r['Symbol']==sym];base=sum(r['Modes']['E0']['Metrics']['Trades'] for r in rs)
        for m in ('E0','E1','E2'):
            ds=[r['Modes'][m] for r in rs];n=sum(d['Metrics']['Trades'] for d in ds)
            mode.append(dict(Symbol=sym,Mode=m,E0Trades=base,Trades=n,RemovedTrades=sum(d['RemovedTrades'] for d in ds),Retention=n/base if base else None))
            for e in sorted({e for d in ds for e in d['EventSet']}):event.append(dict(Symbol=sym,Mode=m,Event=e,OverlapTrades=sum(d['RemovedByEvent'].get(e,0) for d in ds)))
    return {'status_summary.json':dict(CandidateCount=len(results),Counts=dict(sorted(Counter(r['Status'] for r in results).items())),FormalEventMode='E2',NoReplacement=True),'event_summary.json':event,'mode_summary.json':mode}

def project_u10p(record,candidate,candidate_sha,checkpoint_sha,producer_sha):
    """Future Result Freeze API only; does not generate a formal input in this task."""
    validate_result(candidate,record)
    if candidate['Status']!='PASS_U10':raise ValueError('PASS only; no replacement')
    return dict(deepcopy(record),FormalEventMode='E2',U10Status='PASS_U10',E2EventSet=candidate['Modes']['E2']['EventSet'],DiscoveryE2Metrics=candidate['Modes']['E2']['Metrics'],U10CandidateSHA256=candidate_sha,U10CandidateObjectSHA256=object_hash(candidate),U10CheckpointSHA256=checkpoint_sha,U10ProducerImplementationSHA=producer_sha,CalendarSourceCommit=CALENDAR_COMMIT,EventCalendarSHA256=digest(CALENDAR),E2TradeStreamSHA256=candidate['TradeStreamSHA256']['E2'])
