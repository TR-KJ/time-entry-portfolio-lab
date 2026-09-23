from datetime import datetime

import numpy as np
import pandas as pd

from c3_vol_scaled_sltp_phase1 import feature_for, replay_scaled, rounded_pips


def test_outward_rounding_to_tenth_pip():
    assert rounded_pips(70, 1.234) == 86.4
    assert rounded_pips(60, .5) == 30.0


def test_feature_uses_prior_252_only_and_clips():
    d = pd.DataFrame({'ATR20': np.r_[np.ones(252), 2.5]})
    f = feature_for(d, 252, 'ATR20')
    assert f['ReferenceMedian'] == 1.0
    assert f['RelativeVol'] == 2.5
    assert f['ScaleFactor'] == 2.0
    assert f['FeatureStatus'] == 'VALID'


def test_feature_falls_back_before_full_reference_window():
    d = pd.DataFrame({'RV20': np.ones(252)})
    f = feature_for(d, 251, 'RV20')
    assert f['ScaleFactor'] == 1.0
    assert f['FeatureStatus'] == 'FALLBACK'
    assert f['FallbackReason'] == 'REFERENCE_LT_252'


def anchor(tp='30'):
    return {
        '_n': 1, '_entry': datetime(2025, 1, 2, 9),
        '_scheduled': datetime(2025, 1, 2, 9, 2), '_week': '2024-12-30',
        'Strategy': 'synthetic', 'Pair': 'UJ', 'Direction': 'Long',
        'Mode': 'synthetic', 'EntryTime': '2025-01-02 09:00:00',
        'ScheduledExitTime': '2025-01-02 09:02:00', 'SL': '10', 'TP': tp,
    }


def bars(highs, lows, opens=None):
    index = pd.date_range('2025-01-02 09:00:00', periods=3, freq='min')
    opens = opens or [150., 150., 150.]
    return pd.DataFrame({'Open': opens, 'High': highs, 'Low': lows,
                         'Close': opens}, index=index)


def feature(scale):
    return {'DailyIndex': 300, 'DailyDate': '2025-01-01', 'Current': 2.,
            'ReferenceMedian': 1., 'RelativeVol': scale,
            'ScaleFactor': scale, 'FeatureStatus': 'VALID', 'FallbackReason': ''}


def test_replay_scales_sl_and_tp_and_defines_r_from_actual_sl():
    # USDJPY long fill includes 0.2-pip spread: 150.002. A 15-pip SL is 149.852.
    r = replay_scaled(anchor(), bars([150.01] * 3, [149.90, 149.85, 149.85]), 'ATR', feature(1.5))
    assert r['ActualSLPips'] == 15.0
    assert r['ActualTPPips'] == 45.0
    assert r['ExitReason'] == 'SL'
    assert r['R'] == -1.0


def test_replay_does_not_add_tp_and_uses_scheduled_open():
    r = replay_scaled(anchor(tp=''), bars([150.01] * 3, [149.99] * 3,
                                         [150., 150.01, 150.02]), 'RV', feature(.5))
    assert r['ActualTPPips'] == ''
    assert r['ExitReason'] == 'TimeExit'
    assert r['ClosePrice'] == 150.02

