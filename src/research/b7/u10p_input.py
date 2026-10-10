"""Frozen PASS40 input validation; no performance computation."""
from .stage1_contract import ROOT,digest,object_hash,verify_conditions
from .u06_finalize_only import read
from .u10_input import CALENDAR,CALENDAR_SHA,CALENDAR_COMMIT,SUPPLEMENT_SHA,SUPPLEMENT_HASH
RESULT_SHA='488553634c3923f5ef561a7db777d1b0b2ff5796'
PRODUCER_SHA='ca3affff0c210e4a4cda9aae98ca8a9928db9489'
INPUT_SHA='7bce58b58102be11d8fe2debe4212b47a52cc685d10b044a9f7663e5b0bad11f'
INPUT_OBJECT='16105209109bf8d064d2161215254889553ef245d4546c8ec671ad7e5e36948f'
INPUT=ROOT/'research_inputs/b7/u10p_selected40_input.json'
CONFIG=ROOT/'research_inputs/b7/u10p_config.json'

def validate(data):
    if object_hash(data)!=INPUT_OBJECT:raise ValueError('exact frozen PASS40 input')
    rs=data['Candidates'];ids=[r['CandidateID'] for r in rs]
    if len(rs)!=40 or len(set(ids))!=40 or ids!=data['CandidateIDs'] or data['CandidateCount']!=40:raise ValueError('ordered40')
    if data['NoReplacement'] is not True or data['U10PPerformanceEvaluated'] is not False:raise ValueError('input scope')
    if data['FrozenU10PContract']!=read(ROOT/'research_inputs/b7/full_research_prespec.json')['U10-P']:raise ValueError('frozen contract')
    prior={r['CandidateID']:r for r in read(ROOT/'research_inputs/b7/u10_selected54_input.json')['Candidates']}
    hashes={f['Path']:f['SHA256'] for f in read(ROOT/'results/b7/u10/drive_checkpoint_audit.json')['TrustedFiles']}
    counts={s:sum(r['Symbol']==s for r in rs) for s in ('USDJPY','EURJPY','GBPJPY','AUDJPY','AUDUSD','EURAUD','GBPAUD','EURUSD','GBPUSD')}
    if list(counts.values())!=[1,8,8,4,0,7,5,5,2]:raise ValueError('pair counts')
    for r in rs:
        if r['U10Status']!='PASS_U10' or r['FormalEventMode']!='E2' or r['U10ProducerImplementationSHA']!=PRODUCER_SHA:raise ValueError('source status')
        if any(r.get(k)!=v for k,v in prior[r['CandidateID']].items()):raise ValueError('prior fields')
        for k,n in [('U10CandidateSHA256','candidate.json'),('U10CheckpointSHA256','checkpoint.json')]:
            if r[k]!=hashes['jobs/'+r['CandidateID']+'/'+n]:raise ValueError('source hashes')
        if r['EventCalendarSHA256']!=CALENDAR_SHA or r['CalendarSourceCommit']!=CALENDAR_COMMIT:raise ValueError('event identity')
    return data

def input_config():
    verify_conditions();c=read(CONFIG)
    if c['U10ResultFreezeSHA']!=RESULT_SHA or c['U10ProducerSHA']!=PRODUCER_SHA or c['InputSHA256']!=INPUT_SHA or digest(INPUT)!=INPUT_SHA or c['InputObjectSHA256']!=INPUT_OBJECT:raise ValueError('input identity')
    if digest(CALENDAR)!=CALENDAR_SHA or c['EventCalendarSHA256']!=CALENDAR_SHA:raise ValueError('calendar')
    if c['FrozenU10PContract']!=read(ROOT/'research_inputs/b7/full_research_prespec.json')['U10-P']:raise ValueError('conditions')
    for p,h in c['FrozenSources'].items():
        if digest(ROOT/p)!=h:raise ValueError('frozen source changed: '+p)
    return c,validate(read(INPUT))
