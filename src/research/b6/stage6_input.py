"""Exact Stage5 artifact, ancestry, candidate and frozen-rule hard gates."""
import math,subprocess
from .stage6_config import ROOT,sha,load_config
from .stage5_input import strict_json
from .stage5_validation import contract as frozen_contract
from .stage5_freeze import serialize
from .stage4_events import applicable_events

FIELDS=('CandidateID','Symbol','Direction','Weekday','FinalEntryJST','FinalExitJST','FinalExitDayOffset','FinalHoldingMinutes','AdjustedEntryMinute','AdjustedExitMinute','AdjustedExitDayOffset','PlannedHoldingMinutes','SL','TP','TPMode','SelectedEventMode','ApplicableEvents','FixedSpreadPips','PipSize','DiscoveryMaxDDR')

def validate_candidate(p,execution,calendar):
    if any(k not in p for k in FIELDS):raise ValueError('candidate schema missing fields')
    if not isinstance(p['CandidateID'],str) or not p['CandidateID'] or p['Symbol'] not in execution['SpreadPips'] or p['Direction'] not in ('L','S'):raise ValueError('candidate identity invalid')
    if type(p['Weekday']) is not int or p['Weekday'] not in range(5):raise ValueError('weekday invalid')
    def minute(s):
        if not isinstance(s,str) or len(s)!=5 or s[2]!=':':raise ValueError('HH:MM required')
        h,m=int(s[:2]),int(s[3:])
        if not (0<=h<24 and 0<=m<60):raise ValueError('time invalid')
        return h*60+m
    e,x=minute(p['FinalEntryJST']),minute(p['FinalExitJST']);offset=p['FinalExitDayOffset'];hold=p['FinalHoldingMinutes']
    if type(offset) is not int or offset not in (0,1) or type(hold) is not int or not 30<=hold<=1440 or offset*1440+x-e!=hold:raise ValueError('holding/offset mismatch')
    if (e,x,offset,hold)!=(p['AdjustedEntryMinute'],p['AdjustedExitMinute'],p['AdjustedExitDayOffset'],p['PlannedHoldingMinutes']):raise ValueError('final/adjusted schedule mismatch')
    if p['FixedSpreadPips']!=execution['SpreadPips'][p['Symbol']] or p['PipSize']!=execution['PipSize'][p['Symbol']]:raise ValueError('spread/pip mutation')
    for k in ('SL','TP'):
        value=p[k]
        if k=='TP' and value is None:continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError('SL/TP invalid')
    if p['TPMode']!=('TP_NONE' if p['TP'] is None else 'FINITE'):raise ValueError('TP mode mismatch')
    if p['SelectedEventMode'] not in ('E0','E1','E2') or p['ApplicableEvents']!=applicable_events(p['Symbol'],p['SelectedEventMode']):raise ValueError('event mode/aliases invalid')
    dd=p['DiscoveryMaxDDR']
    if isinstance(dd,bool) or not isinstance(dd,(int,float)) or not math.isfinite(dd) or dd<0 or dd!=p['DiscoveryMetrics']['MaxDDR']:raise ValueError('raw frozen DiscoveryDD invalid')

def validate_payload(f,v,c):
    if f.get('status')!='STAGE5_DISCOVERY_CANDIDATE_FREEZE' or f['Stage4SelectedSettingsSHA256']!=c['stage4_selected_sha256']:raise ValueError('Stage5 provenance mismatch')
    if len(f['Candidates'])!=c['candidate_count'] or f['CandidateCount']!=c['candidate_count']:raise ValueError('candidate count mismatch')
    ids=[p['CandidateID'] for p in f['Candidates']]
    if len(set(ids))!=len(ids):raise ValueError('duplicate CandidateID')
    if f['ExecutionContract']!=c['execution_contract'] or f['EventCalendarProvenance']!=c['calendar'] or f['M1InputProvenance']!=c['m1_manifest']:raise ValueError('frozen execution/calendar/M1 identity changed')
    if v!=frozen_contract(c['candidate_sha256']):raise ValueError('Stage5 assessment helper/Contract mismatch')
    for ck,vk in [('periods','Periods'),('sample_sufficiency','SampleSufficiency'),('pass_conditions','PassConditions'),('dd_limit','DDLimit'),('prohibited_extra_gates','ProhibitedExtraGates')]:
        if c[ck]!=v[vk]:raise ValueError('Stage6 rule differs from Stage5 Contract')
    for p in f['Candidates']:validate_candidate(p,f['ExecutionContract'],c['calendar'])
    return f['Candidates']

def load_input(c=None):
    c=load_config() if c is None else c
    subprocess.run(['git','merge-base','--is-ancestor',c['stage5_commit'],'HEAD'],cwd=ROOT,check=True)
    targets={c['candidate_file']:c['candidate_sha256'],c['contract_file']:c['contract_sha256'],'research_inputs/b6/stage5_config.json':c['stage5_config_sha256']}
    raw={}
    for name,digest in targets.items():
        raw[name]=(ROOT/name).read_bytes()
        if sha(ROOT/name)!=digest:raise ValueError('Stage5 exact SHA mismatch: '+name)
        if subprocess.check_output(['git','show',c['stage5_commit']+':'+name],cwd=ROOT)!=raw[name]:raise ValueError('Stage5 commit/artifact mismatch')
    if sha(ROOT/c['calendar']['File'])!=c['calendar']['SHA256'] or sha(ROOT/c['m1_manifest']['Manifest'])!=c['m1_manifest']['ManifestSHA256']:raise ValueError('calendar/manifest exact SHA mismatch')
    for name,h in c['execution_contract']['FrozenSourceSHA256'].items():
        if sha(ROOT/name)!=h:raise ValueError('frozen execution source changed')
    f=strict_json(raw[c['candidate_file']]);v=strict_json(raw[c['contract_file']]);points=validate_payload(f,v,c)
    calendar=strict_json((ROOT/c['calendar']['File']).read_bytes())
    audit=dict(Status='PASS',Stage5Commit=c['stage5_commit'],CandidateFreezeSHA256=c['candidate_sha256'],ValidationContractSHA256=c['contract_sha256'],Stage5ConfigSHA256=c['stage5_config_sha256'],Stage4SelectedSettingsSHA256=c['stage4_selected_sha256'],CandidateCount=len(points),CandidateArtifactUnchanged=True,ContractUnchanged=True,ExecutionSourcesUnchanged=True,CalendarSHA256=c['calendar']['SHA256'],M1ManifestSHA256=c['m1_manifest']['ManifestSHA256'],ValidationExecuted=False,MonitorExecuted=False)
    return points,calendar,audit

def assert_frozen_candidate(point,frozen):
    if serialize(point)!=serialize(frozen):raise ValueError('candidate mutated after exact input audit')
