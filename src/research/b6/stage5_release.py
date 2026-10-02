"""Verify Stage5 checkout, exact artifact hashes and acyclic identity binding."""
import subprocess
from .stage5_config import ROOT,sha
from .stage5_input import strict_json
from .stage5_freeze import CANDIDATE_PATH,CONTRACT_PATH

def verify_release(expected_sha):
    if len(expected_sha)!=40 or any(c not in '0123456789abcdef' for c in expected_sha):raise ValueError('exact 40-digit Stage5 Freeze commit required')
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if actual!=expected_sha:raise ValueError('Stage5 checkout SHA mismatch')
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise ValueError('Stage5 checkout must be clean including untracked files')
    lock=strict_json((ROOT/'research_inputs/b6/stage5_release_manifest.json').read_bytes())
    for name,digest in lock.items():
        if sha(ROOT/name)!=digest:raise ValueError('Stage5 release hash mismatch: '+name)
    contract=strict_json((ROOT/CONTRACT_PATH).read_bytes())
    if contract['CandidateFreezeSHA256']!=sha(ROOT/CANDIDATE_PATH):raise ValueError('Candidate Freeze/Validation Contract SHA binding mismatch')
    return actual
