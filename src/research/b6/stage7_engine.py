"""Replay one already-frozen candidate with private Monitor period modules."""
import pandas as pd
from .stage7_adapter import modules
from .stage7_data import validate_prices,START,END
from .stage6_input import validate_candidate
from .stage7_config import load_config
from .stage3_grid import execution_candidate,fixed_setting

def make_engine(bars,symbol):
    validate_prices(bars);return modules()['stage1_engine'].FastEngine(bars,symbol)

def replay_candidate(point,dates,calendar,engine=None,bars=None):
    c=load_config();validate_candidate(point,c['execution_contract'],c['calendar']);dates=pd.DatetimeIndex(dates)
    if dates.tz is not None or not dates.is_unique or not dates.is_monotonic_increasing or not dates.equals(dates.normalize()) or ((dates<START)|(dates>=END)).any() or (dates.weekday!=point['Weekday']).any():raise ValueError('Monitor scheduled Entry dates only')
    a=dict(CandidateID=point['CandidateID'],Symbol=point['Symbol'],Direction=point['Direction'],Weekday=point['Weekday'],EntryMinute=point['AdjustedEntryMinute'],ExitMinute=point['AdjustedExitMinute'],ExitDayOffset=point['AdjustedExitDayOffset'],HoldingMinutes=point['PlannedHoldingMinutes'])
    setting=[fixed_setting(point)];m=modules()['stage2a_engine']
    if bars is not None:
        validate_prices(bars);base=m.reference_replay(bars,a['Symbol'],a,dates,setting)
    else:
        if engine is None or engine.symbol!=a['Symbol']:raise ValueError('matching Monitor engine required')
        if not isinstance(engine,modules()['stage1_engine'].FastEngine):raise ValueError('only period-isolated Monitor engine allowed')
        base=m.fast_replay(engine,a,dates,setting)
    filtered,diag=modules()['stage4_events'].filter_replay(point,base,point['SelectedEventMode'],calendar)
    return filtered,diag
