"""Stage2-A config, exact Stage1 input hard gates, and finite Decimal TP grid."""
import hashlib,json
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from .stage1_config import ROOT
PATH=ROOT/'research_inputs/b6/stage2a_config.json'
CONFIG_SHA='bab7eced359ad914e63b6a13dd6c956f86c9b7f695f9b8fc622b2c8f9e4685d6'
STRUCTURE_KEYS=('CandidateID','Symbol','Direction','Weekday','EntryMinute','ExitMinute','ExitDayOffset','HoldingMinutes')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError('Stage2-A config hash mismatch')
    return json.loads(PATH.read_text())

def tp_grid(sl,c=None):
    c=load_config() if c is None else c
    if Decimal(str(sl))<=0:raise ValueError('positive SL required')
    grid=[dict(SL=sl,TP=None,TPRatio=None,TPMode='TP_NONE',ActualTPRatio=None,RatioAliases=[])]
    seen={}
    for ratio in c['tp_ratios']:
        pips=max(c['tp_min_pips'],int((Decimal(str(sl))*Decimal(ratio)/5).quantize(Decimal('1'),rounding=ROUND_HALF_UP))*5)
        if pips in seen:seen[pips]['RatioAliases'].append(ratio);continue
        row=dict(SL=sl,TP=pips,TPRatio=float(Decimal(ratio)),TPMode='FINITE',ActualTPRatio=pips/sl,RatioAliases=[ratio]);grid.append(row);seen[pips]=row
    return grid

def settings(candidate,c=None):
    c=load_config() if c is None else c
    return [row for sl in c['sl_pips'][candidate['Symbol']] for row in tp_grid(sl,c)]

def validate_structures(rows,c):
    if not isinstance(rows,list) or len(rows)!=c['candidate_count']:raise ValueError('Candidate count must equal 50')
    ids=set();structures=set();out=[]
    for row in rows:
        if not isinstance(row,dict) or any(k not in row for k in STRUCTURE_KEYS):raise ValueError('missing Candidate structure field')
        a={k:row[k] for k in STRUCTURE_KEYS};s=a['Symbol'];e=a['EntryMinute'];x=a['ExitMinute'];h=a['HoldingMinutes'];offset=a['ExitDayOffset']
        if s not in c['sl_pips'] or a['Direction'] not in ('L','S'):raise ValueError('symbol/direction')
        if any(type(a[k]) is not int for k in ('Weekday','EntryMinute','ExitMinute','ExitDayOffset','HoldingMinutes')):raise ValueError('integer structure fields required')
        if not 0<=a['Weekday']<=4 or not 0<=e<1440 or not 0<=x<1440 or offset not in (0,1) or not 30<=h<=1440:raise ValueError('structure bounds')
        if e%5 or x%5 or h%5 or e+h!=offset*1440+x:raise ValueError('structure schedule inconsistent')
        expected=f'B6-{s}-{a["Direction"]}-W{a["Weekday"]}-E{e:04d}-H{h:04d}'
        if a['CandidateID']!=expected or expected in ids:raise ValueError('Candidate ID mismatch/duplicate')
        key=tuple(a[k] for k in STRUCTURE_KEYS[1:])
        if key in structures:raise ValueError('duplicate time structure')
        ids.add(expected);structures.add(key);out.append(a)
    n=sum(len(settings(a,c)) for a in out)
    if n!=c['expected_configurations']:raise ValueError(f'Expected 1500 configurations, got {n}; execution stopped')
    return out

def load_candidates(candidate_path,identity_path,effective_config_path,c=None):
    c=load_config() if c is None else c
    # Verify bytes before parsing/selecting any candidate or opening M1 data.
    if sha(candidate_path)!=c['candidate_sha256']:raise ValueError('Candidate SHA256 mismatch')
    if sha(effective_config_path)!=c['stage1_effective_config_sha256']:raise ValueError('Stage1 effective config SHA256 mismatch')
    identity=json.loads(Path(identity_path).read_text())
    if identity.get('code_sha')!=c['stage1_freeze_sha']:raise ValueError('Stage1 Freeze SHA mismatch')
    if identity.get('config_sha256')!=c['stage1_effective_config_sha256']:raise ValueError('Stage1 identity config mismatch')
    rows=validate_structures(json.loads(Path(candidate_path).read_text()),c)
    # Preserve original order and immutable structure fields; ignore Stage1 scores.
    audit=dict(Status='PASS',CandidateCount=len(rows),CandidateSHA256=c['candidate_sha256'],Stage1FreezeSHA=c['stage1_freeze_sha'],Stage1EffectiveConfigSHA256=c['stage1_effective_config_sha256'],CandidateIDs=[r['CandidateID'] for r in rows],Configurations=sum(len(settings(a,c)) for a in rows))
    return rows,audit
