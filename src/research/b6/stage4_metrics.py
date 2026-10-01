"""Frozen raw-R metrics with event-deletion masks; E0 exact preflight barrier."""
from .stage2a_metrics import summarize
from .stage3_grid import execution_candidate,fixed_setting
from .stage3_config import load_config as previous_config
from .stage4_events import MODES,filter_replay
from .stage4_selection import compare,adoption,choose
FULL=('Trades','Wins','Losses','ZeroR','WinRate','TotalR','AvgR','PF','MaxDDR','AvgWinR','AvgLossR')
YEAR=('Trades','Wins','Losses','TotalR','AvgR','PF','MaxDDR')
FIXED=('CandidateID','Symbol','Direction','Weekday','FinalEntryJST','FinalExitJST','FinalExitDayOffset','FinalHoldingMinutes','SL','TP','TPMode','AdjustedEntryMinute','AdjustedExitMinute','AdjustedExitDayOffset','PlannedHoldingMinutes')

def summarize_replay(point,replay):
    data=summarize(execution_candidate(point),[fixed_setting(point)],replay,previous_config()['gate'])
    identity={k:point[k] for k in FIXED}
    return dict(results=[{**identity,**{k:data['results'][0][k] for k in FULL}}],yearly=[{**identity,'Year':r['Year'],**{k:r[k] for k in YEAR}} for r in data['yearly']],execution_diagnostics=data['diagnostics'])

def verify_e0(point,replay):
    data=summarize_replay(point,replay);row=data['results'][0]
    if any(row[k]!=point[k] for k in FULL):raise ValueError('E0 full metrics differ from official Stage3: '+point['CandidateID'])
    years=point['YearlyMetrics']
    if [r['Year'] for r in years]!=[2020,2021,2022,2023] or any(a[k]!=b[k] for a,b in zip(data['yearly'],years) for k in YEAR):raise ValueError('E0 yearly metrics differ from official Stage3: '+point['CandidateID'])
    return dict(CandidateID=point['CandidateID'],FullMetrics='EXACT_PASS',YearlyMetrics='EXACT_PASS')

def evaluate_modes(point,replay,calendar):
    e0=summarize_replay(point,replay)['results'][0];rows=[];annual=[];diagnostics=[]
    for mode in MODES:
        filtered,diag=filter_replay(point,replay,mode,calendar);data=summarize_replay(point,filtered)
        row={**data['results'][0],'EventMode':mode,**compare(e0,data['results'][0])}
        row.update(adoption(row) if mode!='E0' else dict(AdoptionPass=False,AdoptionFailReasons='BASELINE'))
        row['ApplicableEvents']=diag['ApplicableEvents'];rows.append(row)
        annual.extend({**r,'EventMode':mode} for r in data['yearly'])
        diagnostics.append({**{k:point[k] for k in FIXED},**diag,**{k:v for k,v in row.items() if k not in FULL}})
    best,reason=choose(rows)
    selected={**{k:point[k] for k in FIXED},'SelectedEventMode':best['EventMode'],'E0Metrics':{k:e0[k] for k in FULL},'SelectedModeMetrics':{k:best[k] for k in FULL},**{k:v for k,v in best.items() if k not in FULL and k not in FIXED and k!='EventMode'},'SelectionReason':reason,'YearlyMetrics':[r for r in annual if r['EventMode']==best['EventMode']],'Status':'STAGE4_MODE_SELECTED_STAGE5_NOT_EXECUTED'}
    return dict(results=rows,yearly=annual,diagnostics=diagnostics,selection_audit=[dict(r,Selected=r['EventMode']==best['EventMode'],SelectionReason=reason) for r in rows],selected=selected)

def preflight_all(points,replays):
    ids=[p['CandidateID'] for p in points]
    if len(set(ids))!=len(ids) or set(replays)!=set(ids):raise ValueError('E0 preflight candidate set mismatch')
    return [verify_e0(p,replays[p['CandidateID']]) for p in points]
