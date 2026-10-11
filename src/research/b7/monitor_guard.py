"""Formal evaluation authorization, immutable input and exact run identity barrier."""
import os,re
from pathlib import Path
from .stage1_contract import object_hash
APPROVAL='CHAT_APPROVED_COLAB_B7_MONITOR_ONLY'

def guard(record,reviewed_sha,approval,run_identity):
    if not record['CandidateID'].startswith('B7S1:'):return
    if approval!=APPROVAL or not os.environ.get('COLAB_RELEASE_TAG') or not Path('/content').is_dir():raise PermissionError('formal Monitor is Colab-approved only')
    from . import stage1_runtime as shared
    from .monitor_input import input_config,RESULT_SHA
    from .monitor_artifacts import identity
    if not re.fullmatch('[0-9a-f]{40}',reviewed_sha) or shared.git('rev-parse','HEAD')!=reviewed_sha or shared.git('status','--porcelain'):raise PermissionError('exact reviewed clean implementation required')
    shared.git('merge-base','--is-ancestor',RESULT_SHA,reviewed_sha)
    _,d=input_config()
    records={r['CandidateID']:r for r in d['Candidates']}
    if record['CandidateID'] not in records or object_hash(record)!=object_hash(records[record['CandidateID']]):raise PermissionError('exact PASS22 immutable record required')
    env=shared.environment()
    if env['NumPy']!='2.3.5' or env['pandas']!='2.2.3' or run_identity!=identity(reviewed_sha,env):raise PermissionError('exact formal run identity required')
