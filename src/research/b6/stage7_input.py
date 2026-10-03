"""Hash-locked Monitor input; no formal archive or price access at run time."""
import json,subprocess
from collections import Counter
from .stage7_config import ROOT,sha,load_config
from .stage6_input import load_input as stage5_input,assert_frozen_candidate
from .stage7_freeze import validate_formal,spec

def load_input():
    c=load_config()
    subprocess.run(['git','merge-base','--is-ancestor',c['stage6_code_sha'],'HEAD'],cwd=ROOT,check=True)
    for name,h in c['input_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('Stage7 input exact SHA mismatch: '+name)
    if sha(ROOT/'research_inputs/b6/stage6_config.json')!=c['stage6_config_sha256']:raise ValueError('Stage6 config changed')
    points,calendar,_=stage5_input()
    evidence=json.loads((ROOT/c['evidence_file']).read_text())
    expected=validate_formal(evidence['Identity'],evidence['Summary'],evidence['Progress'],evidence['ValidationRows'],evidence['PeriodRows'],points,spec())
    f=json.loads((ROOT/c['monitor_candidate_file']).read_text());candidates=f['Candidates']
    if f['status']!='STAGE7_MONITOR_INPUT_FREEZE' or f['CandidateCount']!=17 or candidates!=expected:raise ValueError('Monitor candidate freeze changed')
    for key,value in dict(SourceStage6CodeSHA=c['stage6_code_sha'],SourceStage6ConfigSHA256=c['stage6_config_sha256'],SourceStage6ValidationResultsSHA256=c['formal_file_sha256']['stage6_validation_results.csv.gz'],SourceStage6SummarySHA256=c['formal_file_sha256']['stage6_summary.json'],Stage5CandidateFreezeSHA256=c['candidate_sha256'],ValidationContractSHA256=c['contract_sha256'],FormalValidationStatusRequired='PASS',MonitorPeriod=c['monitor_period'],CandidateOrdering=c['ordering']).items():
        if f.get(key)!=value:raise ValueError('Monitor provenance mismatch: '+key)
    audit=json.loads((ROOT/c['input_audit_file']).read_text())
    if any(audit['FormalFileSHA256'].get(k)!=v for k,v in c['formal_file_sha256'].items()):raise ValueError('formal audit SHA map mismatch')
    if audit['SelectedPASSCandidateIDs']!=[p['CandidateID'] for p in candidates]:raise ValueError('audit order mismatch')
    return candidates,calendar,audit
