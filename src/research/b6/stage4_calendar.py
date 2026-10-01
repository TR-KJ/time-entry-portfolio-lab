"""Extract only allowlisted AST list assignments; never execute the baseline."""
import ast,hashlib,json,subprocess
from datetime import date
from .stage2a_config import ROOT,sha
SOURCE_COMMIT='173be2a114dad6bd183a0a1515581528850f0850'
SOURCE_FILE='src/portfolio_backtest_v1_2_add_aussie_logic.py'
CLOCKS={
 'FOMC':dict(Time='03:00',Before=180,After=180,DayOffset=1),
 'US_NFP':dict(Time='21:30',Before=120,After=120,DayOffset=0),
 'US_CPI':dict(Time='21:30',Before=120,After=120,DayOffset=0),
 'BOJ':dict(Time='12:00',Before=180,After=180,DayOffset=0),
 'BOE':dict(Time='21:00',Before=120,After=120,DayOffset=0),
 'ECB':dict(Time='21:15',Before=120,After=120,DayOffset=0),
 'RBA':dict(Time='13:30',Before=120,After=120,DayOffset=0),
 'AUD_CPI':dict(Time='10:30',Before=120,After=120,DayOffset=0)}
PATH=ROOT/'research_inputs/b6/stage4_event_calendar.json'

def extract(source):
    env={};counts={};allowed={e+s for e in CLOCKS for s in ('_DATES','_2026_DATES')}
    for node in ast.parse(source).body:
        if not isinstance(node,ast.Assign):continue
        names=[t.id for t in node.targets if isinstance(t,ast.Name) and t.id in allowed]
        if not names:continue
        if len(names)!=1 or len(node.targets)!=1:raise ValueError('ambiguous calendar assignment')
        name=names[0];value=node.value;counts[name]=counts.get(name,0)+1
        if isinstance(value,ast.List):
            if counts[name]!=1:raise ValueError('calendar literal overwritten')
            dates=ast.literal_eval(value)
        elif isinstance(value,ast.BinOp) and isinstance(value.op,ast.Add) and isinstance(value.left,ast.Name) and isinstance(value.right,ast.Name):
            event=name.removesuffix('_DATES')
            if counts[name]!=2 or value.left.id!=name or value.right.id!=event+'_2026_DATES':raise ValueError('unexpected calendar concatenation')
            dates=env[name]+env[value.right.id]
        else:raise ValueError('nonliteral calendar expression')
        if not isinstance(dates,list) or any(not isinstance(d,str) or date.fromisoformat(d).isoformat()!=d for d in dates):raise ValueError('invalid calendar date')
        env[name]=dates
    if any(counts.get(e+'_DATES')!=2 or counts.get(e+'_2026_DATES')!=1 for e in CLOCKS):raise ValueError('missing base/2026 concatenation')
    return {e:env[e+'_DATES'] for e in CLOCKS}

def artifact(source):
    return dict(SourceCommit=SOURCE_COMMIT,SourceFile=SOURCE_FILE,SourceSHA256=hashlib.sha256(source).hexdigest(),ExtractionRules='Top-level allowlisted literal lists, followed by original list + *_2026_DATES in source order; no execution, sorting, deduplication, correction or matrix.',Dates=extract(source),Clocks=CLOCKS,ClockConvention='Fixed research clocks, Asia/Tokyo; FOMC source US date +1 JST day; other offsets zero. Not reconstructed historical announcement times.')

def pinned_source():
    return subprocess.check_output(['git','show',SOURCE_COMMIT+':'+SOURCE_FILE],cwd=ROOT)

def audit_calendar(c):
    if sha(PATH)!=c['calendar_sha256']:raise ValueError('calendar SHA mismatch')
    data=json.loads(PATH.read_text());expected=artifact(pinned_source())
    if data!=expected or data['SourceSHA256']!=c['calendar_source_sha256']:raise ValueError('pinned calendar integrity mismatch')
    return data,dict(Status='PASS',SourceCommit=SOURCE_COMMIT,SourceFile=SOURCE_FILE,SourceSHA256=data['SourceSHA256'],CalendarSHA256=sha(PATH),Clocks=CLOCKS,DateCounts={e:len(ds) for e,ds in data['Dates'].items()},DiscoverySourceDateCounts={e:sum('2020-01-01'<=d<'2024-01-01' for d in ds) for e,ds in data['Dates'].items()})
