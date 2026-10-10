"""Exact immutable U09 result projection; no performance reads or evaluation."""
from .stage1_contract import ROOT,digest,object_hash,verify_conditions
from .u06_finalize_only import read
RESULT_SHA='ee4406aa910a8cc13bfe57590ed6ea97faea18f4'
PRODUCER_SHA='345a0e8ef659bcd601b73a6475c4613a04ff4337'
SUPPLEMENT_SHA='e34099b9c807df1f145f96ca92c2443fe552fa36'
SUPPLEMENT_HASH='5dc8c39e2e1bb2ab85c893e8769d601e4cb8d1a295e56bf543c6a6643d92130b'
INPUT_SHA='ea64a5145c08db79d6122c24c6ab875c190739b816275ae4bd443510d9571744'
INPUT_OBJECT='a84b767e690021d855105986c155e6ac4a4746eb1338e9bd4f036d8b523fb19d'
CALENDAR_SHA='7a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb'
CALENDAR_COMMIT='173be2a114dad6bd183a0a1515581528850f0850'
SOURCE_PATH='src/portfolio_backtest_v1_2_add_aussie_logic.py'
SOURCE_BLOB='f087a22554fb920e2c7230b0626e72f654376358'
SOURCE_SHA='4b71f6b7b1cdbe3266cd9b7cefae37811781561016a013a34d7c8c84247ef32d'
INPUT=ROOT/'research_inputs/b7/u10_selected54_input.json'
CONFIG=ROOT/'research_inputs/b7/u10_config.json'
CALENDAR=ROOT/'research_inputs/b7/u10_event_calendar.json'
SUPPLEMENT=ROOT/'research_inputs/b7/u10_supplemental_prespec.json'

def validate(data):
    if object_hash(data)!=INPUT_OBJECT:raise ValueError('exact frozen U10 projection')
    rs=data['Candidates'];ids=[r['CandidateID'] for r in rs]
    if data['CandidateCount']!=54 or len(rs)!=54 or len(set(ids))!=54 or ids!=data['CandidateIDs']:raise ValueError('ordered unique54')
    if data['FormalEventMode']!='E2' or data['NoReplacement'] is not True or data['ModeChosenBeforeResults'] is not True or data['U10PerformanceEvaluated'] is not False:raise ValueError('fixed E2 input')
    if data['CalendarSourceCommit']!=CALENDAR_COMMIT:raise ValueError('calendar commit')
    audit=read(ROOT/'results/b7/u09/drive_checkpoint_audit.json');hashes={x['Path']:x['SHA256'] for x in audit['TrustedFiles']}
    shifts=read(ROOT/'results/b7/u09/shift_summary.json')
    if ids!=[x['CandidateID'] for x in shifts]:raise ValueError('U09 order')
    for r,s in zip(rs,shifts):
        if r['U09Status']!='PASS_U09' or r['U09ProducerImplementationSHA']!=PRODUCER_SHA or r['U09Decision']!=s['Decision']:raise ValueError('U09 source')
        for k in ('FormalEntryMinute','FormalExitMinute','FormalExitDayOffset','FormalHoldingMinutes','EntryShiftMinutes','ExitShiftMinutes'):
            if r[k]!=s[k]:raise ValueError('U09 formal schedule')
        for k,n in [('U09CandidateSHA256','candidate.json'),('U09CheckpointSHA256','checkpoint.json')]:
            if r[k]!=hashes[f"jobs/{r['CandidateID']}/{n}"]:raise ValueError('U09 job hash')
    return data

def input_config():
    verify_conditions();c=read(CONFIG)
    if c['U09ResultFreezeSHA']!=RESULT_SHA or c['U10SupplementalFreezeSHA']!=SUPPLEMENT_SHA or c['SupplementalPrespecSHA256']!=SUPPLEMENT_HASH or digest(SUPPLEMENT)!=SUPPLEMENT_HASH:raise ValueError('freeze identity')
    if c['InputSHA256']!=INPUT_SHA or digest(INPUT)!=INPUT_SHA or c['InputObjectSHA256']!=INPUT_OBJECT:raise ValueError('input SHA')
    if c['EventCalendarSHA256']!=CALENDAR_SHA or digest(CALENDAR)!=CALENDAR_SHA or c['CalendarSourceCommit']!=CALENDAR_COMMIT:raise ValueError('calendar identity')
    if c['FrozenEventContract']!=read(ROOT/'research_inputs/b7/full_research_prespec.json')['U10']:raise ValueError('frozen event contract')
    for p,h in c['FrozenSources'].items():
        if digest(ROOT/p)!=h:raise ValueError('frozen source hash')
    return c,validate(read(INPUT))
