import numpy as np
import pandas as pd

from c4_vol_change_phase1 import estimate, ratio_states, state_from_n


def test_exact_tertile_boundaries():
    assert state_from_n(167) == 'COMPRESSION'
    assert state_from_n(168) == 'NEUTRAL'
    assert state_from_n(335) == 'NEUTRAL'
    assert state_from_n(336) == 'EXPANSION'


def test_previous_252_excludes_current_and_uses_midrank():
    values = np.r_[np.arange(1, 253, dtype=float), 253.0]
    nums, pct, states, status = ratio_states(values)
    assert nums[252] == 504
    assert pct[252] == 1.0
    assert states[252] == 'EXPANSION'
    assert status[252] == 'VALID'


def test_equal_value_midrank_and_initial_shortage():
    values = np.ones(253)
    nums, pct, states, status = ratio_states(values)
    assert status[251] == 'REFERENCE_LT_252'
    assert nums[252] == 252
    assert pct[252] == .5
    assert states[252] == 'NEUTRAL'


def test_nonfinite_reference_is_separate_from_current():
    values = np.ones(253); values[10] = np.nan
    *_, status = ratio_states(values)
    assert status[10] == 'CURRENT_UNAVAILABLE'
    assert status[252] == 'REFERENCE_NONFINITE'


def test_fixed_effect_weighting_and_equal_weight_rule():
    rows=[]
    # Stratum 1: delta +1, FE weight 10; stratum 2: delta -1, FE weight 20.
    for no,n,e,c in [(1,20,1.0,0.0),(2,40,0.0,1.0)]:
        rows += [dict(StrategyNo=no,primaryQuintile='Q1',C4State='EXPANSION',R=e)]*n
        rows += [dict(StrategyNo=no,primaryQuintile='Q1',C4State='COMPRESSION',R=c)]*n
    beta,equal,s,ni,ns=estimate(pd.DataFrame(rows))
    assert np.isclose(beta,-1/3)
    assert np.isclose(equal,0.0)
    assert ni==2 and ns==2 and len(s)==2
