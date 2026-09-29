"""Stage2-B reporting adapter; shared frozen Stage2-A raw-R metrics unchanged."""
from .stage2a_metrics import summarize
from .stage2a_engine import fast_replay

def evaluate_candidate(engine,candidate,dates,grid,config):
    if not grid:return dict(results=[],yearly=[],diagnostics=[])
    replay=fast_replay(engine,candidate,dates,grid)
    return summarize(candidate,grid,replay,config['gate'])
