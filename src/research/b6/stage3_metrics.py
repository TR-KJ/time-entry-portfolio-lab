"""One fixed SL/TP per adjusted schedule, using frozen Stage2-A semantics."""
from .stage2a_engine import fast_replay,reference_replay
from .stage2a_metrics import summarize
from .stage3_grid import execution_candidate,fixed_setting

def evaluate_point(engine,point,dates,c,bars=None):
    a=execution_candidate(point);setting=fixed_setting(point)
    replay=fast_replay(engine,a,dates,[setting]) if bars is None else reference_replay(bars,a['Symbol'],a,dates,[setting])
    data=summarize(a,[setting],replay,c['gate'])
    for rows in data.values():
        for row in rows:row.update(point)
    # Keep original anchor fields unambiguous; EntryMinute/ExitMinute are original.
    diag=data['diagnostics'][0]
    data['results'][0].update({k:v for k,v in diag.items() if k not in data['results'][0]})
    return data

def evaluate_candidate(engine,candidate,dates,grid,c):
    result={k:[] for k in ('results','yearly','diagnostics')}
    for point in grid:
        if any(point[k]!=candidate[k] for k in ('CandidateID','Symbol','Direction','Weekday','SL','TP','ExitDayOffset')):raise ValueError('fixed candidate fields changed')
        data=evaluate_point(engine,point,dates,c)
        for k in result:result[k].extend(data[k])
    return result
