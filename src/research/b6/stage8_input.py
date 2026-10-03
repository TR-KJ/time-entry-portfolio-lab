"""Exact Stage8 deployment input, independent of runtime Drive access."""
import json,subprocess
from .stage8_config import ROOT,sha,load_config
from .stage7_input import load_input as stage7_input
from .stage8_freeze import derive,validate_formal,spec
from .stage6_input import assert_frozen_candidate

def load_input():
    c=load_config()
    subprocess.run(['git','merge-base','--is-ancestor',c['stage7_code_sha'],'HEAD'],cwd=ROOT,check=True)
    for name,h in c['input_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('Stage8 exact input SHA mismatch: '+name)
    for name,h in [('research_inputs/b6/stage7_config.json',c['stage7_config_sha256']),('research_inputs/b6/stage7_monitor_candidates.json',c['stage7_candidate_sha256'])]:
        if sha(ROOT/name)!=h or subprocess.check_output(['git','show',c['stage7_code_sha']+':'+name],cwd=ROOT)!=(ROOT/name).read_bytes():raise ValueError('Stage7 frozen commit bytes changed')
    points,calendar,_=stage7_input();audit=json.loads((ROOT/c['input_audit_file']).read_text());s=spec()
    if audit['FormalFileSHA256']!=c['formal_file_sha256']:raise ValueError('Stage7 formal runtime inventory changed')
    validate_formal(audit['FormalIdentity'],audit['FormalSummary'],audit['FormalProgress'],points,s)
    eligibility,pool=derive(points,audit['ResearchStates'],s)
    if json.loads((ROOT/c['eligibility_file']).read_text())!=eligibility or json.loads((ROOT/c['candidate_pool_file']).read_text())!=pool:raise ValueError('deployment freeze changed')
    return pool['Candidates'],calendar,audit
