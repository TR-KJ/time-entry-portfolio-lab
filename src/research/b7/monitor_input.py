"""Immutable PASS22 input and U11 Result Freeze provenance; no prices."""
from .stage1_contract import ROOT,digest,object_hash,verify_conditions
from .candidate_freeze import read,exact
from .u11_input import input_config as validation_input,FREEZE_SHA,SUPPLEMENT_SHA
from .u11_result_freeze import validate_monitor
RESULT_SHA='08db85612fa76773a3f7e3bbaefd91c84877db22'
PRODUCER_SHA='f763cfd25d79d59a1ba823de5493e8535c575e55'
INPUT=ROOT/'research_inputs/b7/monitor_selected22_input.json'
CONFIG=ROOT/'research_inputs/b7/monitor_config.json'
INPUT_SHA='677aa3a9a18e9b8b46dcf7900ad9d4adbcc8a9bd0bf5e057b22e7e839fd434d2'
INPUT_OBJECT='bd4eca4cf0aa5b0bace249ff61259f290f5c495d6f335fc71651a01b215bf3c9'
PERIOD='[2026-01-01, 2026-09-10) JST'
PAIRS=dict(AUDJPY=4,AUDUSD=0,EURAUD=6,EURJPY=4,EURUSD=0,GBPAUD=3,GBPJPY=5,GBPUSD=0,USDJPY=0)
MODES=dict(P0=21,P1=0,P2=1,P3=0)

def validate(d):
    if object_hash(d)!=INPUT_OBJECT:raise ValueError('exact immutable Monitor object')
    _,v=validation_input()
    validate_monitor(d,v['Candidates'],read(ROOT/'results/b7/u11/pass_inventory.json'),read(ROOT/'results/b7/u11/drive_checkpoint_audit.json')['TrustedFiles'],PRODUCER_SHA)
    if d['PairCounts']!=PAIRS or d['ProtectionModeCounts']!=MODES or d['CandidateIDs']!=[r['CandidateID'] for r in d['Candidates']]:raise ValueError('ordered22/counts')
    if d['CandidateFreezeSHA']!=FREEZE_SHA or d['U11ProducerImplementationSHA']!=PRODUCER_SHA:raise ValueError('source identity')
    if {r['CandidateID']:r['FormalProtectionMode'] for r in d['Candidates'] if r['FormalProtectionMode']!='P0'}!={'B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610':'P2'}:raise ValueError('fixed Protection')
    return d

def input_config():
    verify_conditions();c=read(CONFIG)
    if INPUT.is_symlink() or digest(INPUT)!=INPUT_SHA or INPUT.stat().st_size!=260069:raise ValueError('exact Monitor SHA/Bytes')
    d=validate(read(INPUT))
    expected=dict(U11ResultFreezeSHA=RESULT_SHA,U11ProducerImplementationSHA=PRODUCER_SHA,CandidateFreezeSHA=FREEZE_SHA,MonitorInputSHA256=INPUT_SHA,MonitorInputObjectSHA256=INPUT_OBJECT,MonitorInputBytes=260069,CandidateIDs=d['CandidateIDs'],PairCounts=PAIRS,ProtectionModeCounts=MODES,MonitorPeriod=PERIOD,MonitorStart='2026-01-01 00:00:00',MonitorEnd='2026-09-10 00:00:00',MonitorStatus='OBSERVED_ONLY',NoReplacement=True,ValidationOverrideAllowed=False,PostValidationRetuningAllowed=False,ExpectedJobs=22,ExpectedTrustedFiles=67)
    for k,v in expected.items():
        if not exact(c[k],v):raise ValueError('Monitor config '+k)
    for p,h in c['FrozenSources'].items():
        if digest(ROOT/p)!=h:raise ValueError('frozen source mutation: '+p)
    if digest(INPUT)!=INPUT_SHA:raise ValueError('input mutated')
    return c,d
