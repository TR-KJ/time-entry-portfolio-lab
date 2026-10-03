"""Audit exact formal archive bytes and package PASS inputs; never replay prices."""
import argparse,csv,gzip,hashlib,io,json
from collections import Counter
from decimal import Decimal,InvalidOperation
from pathlib import Path
from .stage6_config import ROOT,sha,load_config as stage6_config
from .stage6_input import load_input as stage5_input,FIELDS
from .stage5_freeze import serialize,write_identical_or_new
from .stage5_input import strict_json

SPEC_PATH=ROOT/'research_inputs/b6/stage7_source_spec.json'
def spec():return strict_json(SPEC_PATH.read_bytes())

def encoded(value):
    if value is None:return ''
    if isinstance(value,(list,dict)):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
    return str(value)

def csv_equal(text,value):
    # pandas writes numeric columns as e.g. 2.0 when the frozen scalar is 2.
    # Compare exact decimal text, with no tolerance, rounding or correction.
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        try:return Decimal(text)==Decimal(str(value))
        except InvalidOperation:return False
    return text==encoded(value)

def same_csv(row,values):
    return set(row)==set(values) and all(csv_equal(row[k],v) for k,v in values.items())

def validate_formal(identity,summary,progress,rows,periods,points,s):
    expected=dict(State='COMPLETE_STAGE6_VALIDATION_ONLY',CandidateCount=50,PeriodRows=150,PASS=17,FAIL=33,INSUFFICIENT_SAMPLE=0,ValidationExecuted=True,MonitorExecuted=False,PortfolioExecuted=False,LiveChanged=False,NoRanking=True)
    for record in (summary,progress):
        for key,value in expected.items():
            if record.get(key)!=value or type(record[key]) is not type(value):raise ValueError('formal completion mismatch: '+key)
    if progress.get('CompletedJobs')!=50 or progress.get('ExpectedJobs')!=50:raise ValueError('incomplete Stage6')
    wanted=dict(code_sha=s['stage6_code_sha'],config_sha256=s['stage6_config_sha256'],stage5_commit=s['stage5_commit'],candidate_sha256=s['candidate_sha256'],contract_sha256=s['contract_sha256'],candidate_count=50,calendar_sha256=s['calendar']['SHA256'],calendar_source_commit=s['calendar']['SourceCommit'],scope='FORMAL_VALIDATION_2024_2025',runtime=s['formal_runtime'])
    for key,value in wanted.items():
        if identity.get(key)!=value:raise ValueError('Stage6 identity mismatch: '+key)
    manifest=list(csv.DictReader((ROOT/s['m1_manifest']['Manifest']).open()))
    if len(identity.get('inputs',[]))!=56 or identity['inputs']!=[{k:r[k] for k in ('Filename','SHA256')} for r in manifest]:raise ValueError('Stage6 56 M1 identity mismatch')
    ids=[r['CandidateID'] for r in rows]
    if len(rows)!=50 or len(set(ids))!=50 or ids!=[p['CandidateID'] for p in points]:raise ValueError('Stage6 candidate order/count/duplicate mismatch')
    if Counter(r['ValidationStatus'] for r in rows)!=Counter(PASS=17,FAIL=33):raise ValueError('Stage6 status counts mismatch')
    if len(periods)!=150 or [(r['CandidateID'],r['Period']) for r in periods]!=[(cid,label) for cid in ids for label in ('2024','2025','Combined')]:raise ValueError('Stage6 period rows mismatch')
    for row,p in zip(rows,points):
        for k in FIELDS:
            if k!='ApplicableEvents' and not csv_equal(row.get(k,''),p[k]):raise ValueError('frozen condition changed: '+k)
        if row['EventMode']!=p['SelectedEventMode']:raise ValueError('event mode changed')
    selected=[(row,p) for row,p in zip(rows,points) if row['ValidationStatus']=='PASS']
    if [r['CandidateID'] for r,p in selected]!=s['expected_pass_ids']:raise ValueError('expected PASS IDs/order mismatch')
    if Counter(p['Symbol'] for r,p in selected)!=Counter({k:v for k,v in s['pair_counts'].items() if v}):raise ValueError('pair composition mismatch')
    candidates=[]
    for row,p in selected:
        if (p['Direction'],p['Weekday'],p['SelectedEventMode'])!=('L',0,'E0'):raise ValueError('unexpected PASS condition')
        # Conditions are exact Stage5 values independently cross-checked against
        # the formal CSV. CSV provenance strings preserve all source precision.
        provenance={k:v for k,v in row.items() if k.startswith(('2024_','2025_','Combined_')) or k in ('ValidationDDLimit','SampleSufficient','SampleFailReasons','ValidationFailReasons')}
        if row['SampleSufficient']!='True' or json.loads(row['ValidationFailReasons'])!=[]:raise ValueError('PASS provenance mismatch')
        candidates.append(dict({k:p[k] for k in FIELDS},DiscoveryMetrics=dict(MaxDDR=p['DiscoveryMaxDDR']),FormalValidationStatus=row['ValidationStatus'],ValidationProvenance=provenance))
    return candidates

def build_outputs(archive):
    root=Path(archive);s=spec()
    if not root.is_dir():raise ValueError('formal Stage6 archive required, not review ZIP')
    hashes={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('formal archive symlink rejected')
        if p.is_file():hashes[p.relative_to(root).as_posix()]=sha(p)
    for name,h in s['formal_file_sha256'].items():
        if hashes.get(name)!=h:raise ValueError('formal exact SHA mismatch: '+name)
    def read(name):return strict_json((root/name).read_bytes())
    def rows(name):
        with gzip.open(root/name,'rt',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
    points,_,_=stage5_input()
    identity,summary,progress=read('identity.json'),read('stage6_summary.json'),read('progress.json')
    validation,periods=rows('stage6_validation_results.csv.gz'),rows('stage6_period_results.csv.gz')
    candidates=validate_formal(identity,summary,progress,validation,periods,points,s)
    ledger=read('checkpoints.json')
    if set(ledger)!={p['CandidateID'] for p in points}:raise ValueError('formal checkpoint IDs mismatch')
    for row,p in zip(validation,points):
        cid=p['CandidateID'];name='shards/'+cid+'.json'
        if hashes.get(name)!=ledger[cid]:raise ValueError('formal shard SHA mismatch')
        shard=read(name)
        if shard['candidate']!=p:raise ValueError('formal shard candidate mutated')
        if not same_csv(row,shard['validation']):raise ValueError('formal shard/result mismatch')
        if not all(same_csv(r,v) for r,v in zip([r for r in periods if r['CandidateID']==cid],shard['periods'],strict=True)):raise ValueError('formal shard/period mismatch')
    audit=dict(Status='PASS',FormalStage6Root=str(root.resolve()),FormalFileSHA256=hashes,SourceStage6CodeSHA=s['stage6_code_sha'],SourceStage6ConfigSHA256=s['stage6_config_sha256'],**summary,CompletedJobs=50,ExpectedJobs=50,SelectedPASSCandidateIDs=[p['CandidateID'] for p in candidates],PairCounts=s['pair_counts'],FrozenConditionsUnchanged=True,NoDropRefillRerank=True,ScientificInput='Formal archive exact bytes; not review ZIP',Stage7MonitorExecuted=False)
    freeze=dict(schema='b6-stage7-monitor-input-v1',status='STAGE7_MONITOR_INPUT_FREEZE',SourceStage6CodeSHA=s['stage6_code_sha'],SourceStage6ConfigSHA256=s['stage6_config_sha256'],SourceStage6ValidationResultsSHA256=hashes['stage6_validation_results.csv.gz'],SourceStage6SummarySHA256=hashes['stage6_summary.json'],Stage5CandidateFreezeSHA256=s['candidate_sha256'],ValidationContractSHA256=s['contract_sha256'],CandidateCount=17,CandidateOrdering=s['ordering'],FormalValidationStatusRequired='PASS',MonitorPeriod=s['monitor_period'],Candidates=candidates)
    stream=io.StringIO(newline='');out=[]
    for p in candidates:
        out.append({**{k:p[k] for k in ('CandidateID','Symbol','FinalEntryJST','FinalExitJST','FinalHoldingMinutes','SL','TP','SelectedEventMode','FormalValidationStatus')},**{k:p['ValidationProvenance'][k] for k in ('Combined_PF','Combined_AvgR','Combined_TotalR','Combined_MaxDDR')}})
    writer=csv.DictWriter(stream,fieldnames=list(out[0]),lineterminator='\n');writer.writeheader();writer.writerows(out)
    # Publish only required PASS provenance. FAIL performance and full period
    # metrics remain in the formal archive; exact hashes above bind that source.
    compact_rows=[dict(row) if row['ValidationStatus']=='PASS' else {k:v for k,v in row.items() if k in FIELDS or k in ('ValidationStatus','EventMode')} for row in validation]
    evidence=dict(Identity=identity,Summary=summary,Progress=progress,ValidationRows=compact_rows,PeriodRows=[{k:row[k] for k in ('CandidateID','Period')} for row in periods])
    return {'research_inputs/b6/stage7_monitor_candidates.json':serialize(freeze),'results/b6/stage7_freeze/stage6_input_audit.json':serialize(audit),'results/b6/stage7_freeze/monitor_candidate_summary.csv':stream.getvalue().encode(),'results/b6/stage7_freeze/stage6_formal_evidence.json':serialize(evidence)}

def generate(archive,destination):
    src,dest=Path(archive).resolve(),Path(destination).resolve()
    if src.is_relative_to(dest) or dest.is_relative_to(src):raise ValueError('destination overlaps formal archive')
    outputs=build_outputs(src)
    for name,data in outputs.items():
        if (dest/name).exists() and (dest/name).read_bytes()!=data:raise ValueError('refuse different existing freeze')
    for name,data in outputs.items():write_identical_or_new(dest/name,data)
    return hashlib.sha256(outputs['research_inputs/b6/stage7_monitor_candidates.json']).hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--destination',required=True);a=p.parse_args();print(generate(a.archive,a.destination))
