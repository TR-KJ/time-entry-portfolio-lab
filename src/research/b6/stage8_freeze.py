"""Exact Stage7 archive audit and user-decided eligibility; no price replay."""
import argparse,csv,gzip,io,json
from collections import Counter
from pathlib import Path
from .stage7_config import ROOT,sha,load_config as stage7_config
from .stage7_input import load_input as stage7_input
from .stage7_metrics import fixed_columns
from .stage7_freeze import same_csv
from .stage6_input import FIELDS
from .stage5_freeze import serialize,write_identical_or_new
from .stage5_input import strict_json

SPEC=ROOT/'research_inputs/b6/stage8_source_spec.json'
def spec():return strict_json(SPEC.read_bytes())

def validate_formal(identity,summary,progress,points,s):
    for record in (summary,progress):
        for k,v in s['expected_stage7_summary'].items():
            if record.get(k)!=v or type(record[k]) is not type(v):raise ValueError('Stage7 completion mismatch: '+k)
    if progress.get('CompletedJobs')!=17 or progress.get('ExpectedJobs')!=17:raise ValueError('incomplete Stage7 jobs')
    c=stage7_config()
    expected=dict(code_sha=s['stage7_code_sha'],config_sha256=s['stage7_config_sha256'],monitor_candidate_sha256=s['stage7_candidate_sha256'],stage6_code_sha=c['stage6_code_sha'],stage6_validation_results_sha256=c['formal_file_sha256']['stage6_validation_results.csv.gz'],candidate_count=17,candidate_ids=[p['CandidateID'] for p in points],calendar_sha256=s['calendar']['SHA256'],runtime=s['formal_runtime'],scope='REFERENCE_MONITOR_2026_PARTIAL')
    for k,v in expected.items():
        if identity.get(k)!=v:raise ValueError('Stage7 runtime identity mismatch: '+k)
    with (ROOT/s['m1_manifest']['Manifest']).open() as f:inputs=[{k:r[k] for k in ('Filename','SHA256')} for r in csv.DictReader(f)]
    if len(inputs)!=56 or identity.get('inputs')!=inputs:raise ValueError('Stage7 M1 identity mismatch')
    if summary.get('MonitorPeriod')!=c['monitor_period']:raise ValueError('Stage7 period changed')
    if summary.get('ActualDataEnd')!={'GBPJPY':'2026-09-09 06:00:00','AUDJPY':'2026-09-09 06:00:00'}:raise ValueError('Stage7 actual data end mismatch')

def derive(points,states,s):
    """No Monitor metric is read. Only exact IDs, conditions and status are used."""
    ids=[p['CandidateID'] for p in points]
    if len(points)!=17 or len(set(ids))!=17 or [r['CandidateID'] for r in states]!=ids:raise ValueError('source17 order/identity required')
    excluded=set(s['excluded_ids']);eligible=set(s['eligible_ids'])
    if len(excluded)!=8 or len(eligible)!=9 or excluded&eligible or excluded|eligible!=set(ids):raise ValueError('exact eligibility partition required')
    decisions=[];pool=[]
    for p,row in zip(points,states):
        if p['FormalValidationStatus']!='PASS' or row['FormalValidationStatus']!='PASS' or row['MonitorState']!='OBSERVED':raise ValueError('research status mutation')
        cid=p['CandidateID'];remove=cid in excluded
        if remove and (p['Symbol'],p['FinalEntryJST'],p['Weekday'])!=('AUDJPY','07:01',0):raise ValueError('excluded AUDJPY Monday 07:01 required')
        status='INELIGIBLE_EXECUTION_RISK' if remove else 'ELIGIBLE'
        decisions.append(dict(CandidateID=cid,FormalValidationStatus='PASS',MonitorState='OBSERVED',Symbol=p['Symbol'],FinalEntryJST=p['FinalEntryJST'],DeploymentReviewEligibility=status,EligibilityReasonCode=s['reason_code'] if remove else 'ELIGIBLE_FOR_STAGE8_DEPLOYMENT_REVIEW',EligibilityReasonText=s['reason_text'] if remove else 'Eligible for Stage8 deployment review only; not live adoption.'))
        if not remove:
            pool.append(dict({k:p[k] for k in FIELDS},DiscoveryMetrics=dict(MaxDDR=p['DiscoveryMaxDDR']),Entry=p['FinalEntryJST'],Exit=p['FinalExitJST'],ExitDayOffset=p['FinalExitDayOffset'],Holding=p['FinalHoldingMinutes'],EventMode=p['SelectedEventMode'],Spread=p['FixedSpreadPips'],FormalValidationStatus='PASS',MonitorState='OBSERVED',DeploymentReviewEligibility='ELIGIBLE'))
    if [p['CandidateID'] for p in pool]!=s['eligible_ids']:raise ValueError('pool order changed')
    if [p['CandidateID'] for p in decisions if p['DeploymentReviewEligibility']=='INELIGIBLE_EXECUTION_RISK']!=s['excluded_ids']:raise ValueError('exclusion order changed')
    if Counter(p['Symbol'] for p in pool)!=Counter(AUDJPY=1,GBPJPY=8) or any(p['SelectedEventMode']!='E0' for p in pool):raise ValueError('pool composition/event mismatch')
    aj=next(p for p in pool if p['Symbol']=='AUDJPY')
    if aj['CandidateID']!='B6-AUDJPY-L-W0-E0950-H1440' or aj['FinalEntryJST']!='15:50':raise ValueError('AUDJPY 15:50 singleton required')
    metadata=dict(SourceStage7CodeSHA=s['stage7_code_sha'],SourceStage7ConfigSHA256=s['stage7_config_sha256'],SourceStage7CandidateSHA256=s['stage7_candidate_sha256'],SourceStage7SummarySHA256=s['formal_file_sha256']['stage7_summary.json'],ResearchCandidateCount=17,ResearchHistoryUnchanged=True,FormalValidationChanged=False,MonitorResultsChanged=False,EligibilityUsesMonitorMetrics=False)
    eligibility=dict(schema='b6-stage8-deployment-eligibility-v1',status='STAGE8_DEPLOYMENT_ELIGIBILITY_FREEZE',**metadata,DeploymentIneligible=8,DeploymentEligible=9,DecisionSource='Explicit user execution-model-risk decision; no external spread measurement or performance criterion',Candidates=decisions)
    artifact=dict(schema='b6-stage8-candidate-pool-v1',status='STAGE8_DEPLOYMENT_REVIEW_POOL_FREEZE',**metadata,CandidateCount=9,CandidateOrdering=s['ordering'],PairCounts=s['pair_counts'],Candidates=pool)
    return eligibility,artifact

def build_outputs(archive):
    root=Path(archive);s=spec()
    if not root.is_dir():raise ValueError('formal Stage7 archive required, not review ZIP')
    hashes={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('formal source symlink rejected')
        if p.is_file():hashes[p.relative_to(root).as_posix()]=sha(p)
    if hashes!=s['formal_file_sha256']:raise ValueError('Stage7 formal exact SHA inventory mismatch')
    if hashes.get('effective_config.json')!=s['stage7_config_sha256']:raise ValueError('Stage7 formal config mismatch')
    def read(n):return strict_json((root/n).read_bytes())
    def csv_rows(n):
        with gzip.open(root/n,'rt',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
    points,_,source_audit=stage7_input();identity=read('identity.json');summary=read('stage7_summary.json');progress=read('progress.json')
    validate_formal(identity,summary,progress,points,s)
    if read('stage6_input_audit.json')!=source_audit:raise ValueError('Stage6 provenance changed')
    rows=csv_rows('stage7_monitor_results.csv.gz');diagnostics=csv_rows('stage7_diagnostics.csv.gz');ledger=read('checkpoints.json')
    ids=[p['CandidateID'] for p in points]
    if len(rows)!=17 or [r['CandidateID'] for r in rows]!=ids or [r['CandidateID'] for r in diagnostics]!=ids or set(ledger)!=set(ids):raise ValueError('Stage7 formal rows/checkpoints mismatch')
    for row,diag,p in zip(rows,diagnostics,points):
        cid=p['CandidateID'];name='shards/'+cid+'.json'
        if hashes.get(name)!=ledger[cid]:raise ValueError('Stage7 shard hash mismatch')
        job=read(name)
        if job['candidate']!=p or not same_csv(row,job['monitor']) or not same_csv(diag,job['diagnostics']):raise ValueError('Stage7 checkpoint/result inconsistency')
        fixed=fixed_columns(p)
        if not same_csv({k:row[k] for k in fixed},fixed):raise ValueError('Stage7 fixed conditions/status changed')
    m1=read('m1_input_audit.json')
    if m1['FileCount']!=56 or m1['Inputs']!=identity['inputs'] or m1['ManifestSHA256']!=s['m1_manifest']['ManifestSHA256']:raise ValueError('Stage7 M1 audit mismatch')
    if {r['Symbol']:r['LastAvailableJST'] for r in m1['CanonicalCoverage']}!=summary['ActualDataEnd']:raise ValueError('Stage7 actual coverage mismatch')
    states=[{k:r[k] for k in ('CandidateID','FormalValidationStatus','MonitorState')} for r in rows]
    eligibility,pool=derive(points,states,s)
    audit=dict(Status='PASS',FormalStage7Root=str(root.resolve()),FormalFileSHA256=hashes,FormalIdentity=identity,FormalSummary=summary,FormalProgress=progress,ResearchStates=states,ResearchCandidateCount=17,ObservedCount=17,FormalValidationChanged=False,MonitorResultsChanged=False,AllShardsAudited=True,ScientificInput='Exact formal archive; review ZIP inventory only',OverlapCorrelationExecuted=False,PortfolioExecuted=False)
    decision_audit=dict(ResearchCandidateCount=17,DeploymentIneligible=8,DeploymentEligible=9,ExcludedCandidateIDs=s['excluded_ids'],EligibleCandidateIDs=s['eligible_ids'],PairCounts=s['pair_counts'],ReasonCode=s['reason_code'],EligibilityUsesMonitorMetrics=False,ExternalSpreadMeasurementUsed=False,ResearchHistoryUnchanged=True,NoRanking=True,NoRetuning=True,LiveAdoption=False)
    return {'research_inputs/b6/stage8_deployment_eligibility.json':serialize(eligibility),'research_inputs/b6/stage8_candidate_pool.json':serialize(pool),'results/b6/stage8_freeze/stage7_input_audit.json':serialize(audit),'results/b6/stage8_freeze/deployment_eligibility_audit.json':serialize(decision_audit)}

def generate(archive,destination):
    src,dest=Path(archive).resolve(),Path(destination).resolve()
    if src.is_relative_to(dest) or dest.is_relative_to(src):raise ValueError('output overlaps formal archive')
    outputs=build_outputs(src)
    for name,data in outputs.items():
        if (dest/name).exists() and (dest/name).read_bytes()!=data:raise ValueError('refuse overwrite of different freeze')
    for name,data in outputs.items():write_identical_or_new(dest/name,data)
    return {name:sha(dest/name) for name in outputs}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--destination',required=True);a=p.parse_args();print(json.dumps(generate(a.archive,a.destination),indent=2))
