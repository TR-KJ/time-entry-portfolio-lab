"""Deterministic Stage4-to-Stage5 packaging, without price replay or selection."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from .stage5_config import ROOT,load_config
from .stage5_input import load_input,strict_json
from .stage5_validation import contract,SCHEMA
from .stage4_config import load_config as previous_config
from .stage4_metrics import FULL,YEAR,FIXED

CANDIDATE_PATH='research_inputs/b6/stage5_candidate_freeze.json'
CONTRACT_PATH='research_inputs/b6/stage5_validation_contract.json'

def serialize(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8')

def sha_bytes(value):return hashlib.sha256(value).hexdigest()

def write_identical_or_new(path,data):
    path=Path(path)
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('refuse overwrite of different frozen artifact: '+str(path))
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data)

def execution_contract():
    prev=previous_config();lock=strict_json((ROOT/'research_inputs/b6/stage4_release_manifest.json').read_bytes())
    paths=['src/research/b6/execution.py','src/research/b6/stage1_engine.py','src/research/b6/stage2a_engine.py','src/research/b6/stage1_metrics.py','src/research/b6/stage2a_metrics.py','src/research/b6/stage3_grid.py','src/research/b6/stage4_events.py','src/research/b6/stage4_metrics.py']
    return dict(FrozenSourceSHA256={p:lock[p] for p in paths},Timezone='Europe/Helsinki -> Asia/Tokyo -> naive JST',DST=dict(Ambiguous='infer',Nonexistent='shift_forward'),DuplicateJST='reject',Entry='Exact planned Entry M1 Open',LongEntry='Open + fixed spread',ShortEntry='Open - fixed spread',SLTPBasis='Spread-adjusted Entry',EntryBarInclusive=True,ExitBarInclusive=True,SameBar='SL_FIRST',ExitFallbackMinutes=[0,1,2,3,4],ExitRequiredBeforePathScan=True,MissingEntry='NO_TRADE',MissingAllExitFallback='NO_TRADE',IntermediateMissingInterpolation=False,HighLow='raw',HitEpsilon=0,AdditionalPriceRounding=False,AdditionalSlippage=False,Overnight=True,WeekendBridge=False,EntryStop=dict(Start='12-25',End='01-03',Inclusive=True),SpreadPips=prev['spread_pips'],PipSize={s:(.01 if s.endswith('JPY') else .0001) for s in prev['spread_pips']},Metrics=dict(Basis='unrounded_R',TradeOrdering='Inherited Stage3/Stage4 opportunity order',Drawdown='Inherited cumulative raw R, initial peak 0',ZeroR='Trades included; Wins/Losses excluded',Missing='No trade',PF='sum(positive raw R)/abs(sum(negative raw R))',NoLossPositivePF='INF',NoLossNoPositivePF='UNDEFINED',DisplayDecimals=prev['display_decimals']))

def build_candidate_freeze(selected,shards,audit,identity,c):
    if len(selected)!=c['expected_candidate_count'] or len({s['CandidateID'] for s in selected})!=len(selected):raise ValueError('all selected candidates required')
    ex=execution_contract();prev=previous_config();candidates=[]
    for s in selected:
        if shards[s['CandidateID']]['selected']!=s:raise ValueError('selected input changed after audit')
        annual=[{'Year':r['Year'],**{k:r[k] for k in YEAR},**({'ZeroR':r['ZeroR']} if 'ZeroR' in r else {})} for r in s['YearlyMetrics']]
        decision={k:s[k] for k in ('SelectedEventMode','ApplicableEvents','E0Metrics','SelectedModeMetrics','RetentionRate','RemovedTrades','DeltaTotalR','DeltaAvgR','DeltaMaxDDR','AdoptionPass','AdoptionFailReasons','SelectionReason')}
        decision.update(E1AdoptionPass=shards[s['CandidateID']]['results'][1]['AdoptionPass'],E2AdoptionPass=shards[s['CandidateID']]['results'][2]['AdoptionPass'],AllModesCompared=['E0','E1','E2'],ModeDecisionSource='Formal Stage4 selected; E0 is a compared outcome, not a skipped Stage4')
        candidates.append({**{k:s[k] for k in FIXED},'SelectedEventMode':s['SelectedEventMode'],'ApplicableEvents':s['ApplicableEvents'],'FixedSpreadPips':ex['SpreadPips'][s['Symbol']],'PipSize':ex['PipSize'][s['Symbol']],'DiscoveryMetrics':s['SelectedModeMetrics'],'DiscoveryYearlyMetrics':annual,'DiscoveryMaxDDR':s['SelectedModeMetrics']['MaxDDR'],'Stage4DecisionAudit':decision})
    # Exact self-hash lives in the dependent contract/manifest, avoiding a hash cycle.
    return dict(schema='b6-stage5-candidate-freeze-v1',status='STAGE5_DISCOVERY_CANDIDATE_FREEZE',created_from_stage4_freeze_sha=c['stage4_freeze_sha'],StageFreezeChain={k:c.get(k,prev.get(k)) for k in ('stage1_freeze_sha','stage2a_freeze_sha','stage2b_freeze_sha','stage3_freeze_sha','stage4_freeze_sha')},Stage4RuntimeInputSHA256=audit['FormalInputSHA256'],Stage4SelectedSettingsSHA256=c['stage4_selected_sha256'],Stage4RuntimeIdentity={k:v for k,v in identity.items() if k!='inputs'},M1InputProvenance=dict(Count=56,Manifest='research_inputs/b6/expected_m1_manifest.csv',ManifestSHA256=sha_bytes((ROOT/'research_inputs/b6/expected_m1_manifest.csv').read_bytes()),PriceFilesRead=False),DiscoveryPeriod=dict(StartInclusive='2020-01-01',EndExclusive='2024-01-01',Timezone='Asia/Tokyo naive'),CandidateCount=len(candidates),CandidateOrdering=c['ordering'],CandidateFreezeSHA256Reference=dict(Algorithm='SHA256',Scope='Exact completed UTF-8 file bytes including final LF',RecordedIn=CONTRACT_PATH,Field='CandidateFreezeSHA256',Reason='No recursive self-hash; exact digest also in docs, test summary and release manifest'),ExecutionContract=ex,EventCalendarProvenance=dict(File='research_inputs/b6/stage4_event_calendar.json',SHA256=prev['calendar_sha256'],SourceCommit=prev['calendar_source_commit'],SourceFile=prev['calendar_source_file'],SourceSHA256=prev['calendar_source_sha256'],Clocks=prev['event_clocks'],Overlap=prev['overlap'],Modes=prev['event_modes'],CurrencyCentralBank=prev['currency_central_bank'],NoCorrections=True),Candidates=candidates,ValidationContractReference=dict(File=CONTRACT_PATH,Schema=SCHEMA,ExactContractSHA256Location='research_inputs/b6/stage5_release_manifest.json'),DiscoveryExplorationEnded=True,ValidationExecuted=False,MonitorExecuted=False,PortfolioExecuted=False,LiveAdoption=False)

def summary_csv(freeze):
    rows=[]
    for p in freeze['Candidates']:
        row={k:p[k] for k in ('CandidateID','Symbol','Direction','Weekday','FinalEntryJST','FinalExitJST','FinalExitDayOffset','FinalHoldingMinutes','SL','TP','TPMode','SelectedEventMode','FixedSpreadPips','PipSize')}
        row.update({k:p['DiscoveryMetrics'][k] for k in FULL});row['DiscoveryMaxDDR']=p['DiscoveryMaxDDR']
        row.update({'TotalR_'+str(r['Year']):r['TotalR'] for r in p['DiscoveryYearlyMetrics']});rows.append(row)
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows);return stream.getvalue().encode('utf-8')

def build_outputs(result_root,stage3_selected_path):
    c=load_config();selected,shards,audit,identity=load_input(result_root,stage3_selected_path,c)
    freeze=build_candidate_freeze(selected,shards,audit,identity,c);candidate_bytes=serialize(freeze);digest=sha_bytes(candidate_bytes);validation=serialize(contract(digest))
    files={CANDIDATE_PATH:candidate_bytes,CONTRACT_PATH:validation,'results/b6/stage5_freeze/stage4_input_audit.json':serialize(audit),'results/b6/stage5_freeze/candidate_summary.csv':summary_csv(freeze)}
    return files,dict(CandidateFreezeSHA256=digest,ValidationContractSHA256=sha_bytes(validation),CandidateCount=len(selected),SelectedModeCounts=audit['SelectedModeCounts'],Stage4SelectedSHA256=c['stage4_selected_sha256'],ValidationExecuted=False,MonitorExecuted=False,PortfolioExecuted=False,PriceReplayPerformed=False)

def generate(result_root,stage3_selected_path,destination):
    files,report=build_outputs(result_root,stage3_selected_path);dest=Path(destination)
    for source in (Path(result_root),Path(stage3_selected_path).parent):
        if dest.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(dest.resolve()):raise ValueError('destination overlaps formal runtime')
    # Validate every target before any writes; never repair a different existing artifact.
    for name,data in files.items():
        p=dest/name
        if p.exists() and p.read_bytes()!=data:raise ValueError('existing freeze differs: '+name)
    for name,data in files.items():write_identical_or_new(dest/name,data)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Freeze audited Stage4 Discovery results; no price inputs or replay')
    p.add_argument('--stage4-root',required=True);p.add_argument('--stage3-selected-reference',required=True);p.add_argument('--destination',required=True);a=p.parse_args()
    print(json.dumps(generate(a.stage4_root,a.stage3_selected_reference,a.destination),ensure_ascii=False,indent=2))
