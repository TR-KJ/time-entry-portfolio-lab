"""Fixed China4 group hypothesis; reads the accepted log, never backtests."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
import argparse
import hashlib
import io
import numpy as np
import pandas as pd

BASELINE_HASH = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PLAN_COMMIT = '71e8501f23dcd81104147ab3aaa72892762d0bdc'
BRANCH = 'research/china-demand-group-validation'
CHINA4 = ('25_AU_China_Demand', '26_AJ_China_Demand', '27_EA_China_Demand', '28_GA_China_Demand')
PERIODS = {'IS': ('2015-01-01','2022-01-01'), 'OOS1': ('2022-01-01','2026-01-01'), 'OOS2': ('2026-01-01','2026-09-10'), 'OOS_COMBINED': ('2022-01-01','2026-09-10'), 'ALL': ('2015-01-01','2026-09-10')}

def select_period(df, start, end):
    return df.loc[df.EntryTime.ge(pd.Timestamp(start)) & df.EntryTime.lt(pd.Timestamp(end))].copy()

def load_baseline(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_HASH:
        raise ValueError('Baseline SHA-256 mismatch')
    df = pd.read_csv(io.BytesIO(raw), dtype={'R': str})
    df['_ExactR'] = df.R.map(Decimal)
    df['R'] = pd.to_numeric(df.R, errors='raise')
    for col in ('EntryTime', 'CloseTime'):
        df[col] = pd.to_datetime(df[col], errors='raise')
        if df[col].dt.tz is not None or df[col].isna().any():
            raise ValueError('Expected non-null naive JST timestamps')
    assert len(df) == 16298 and df.Strategy.nunique() == 28
    assert sorted(df.StrategyNo.unique()) == list(range(1,29))
    assert not df.duplicated(['StrategyNo', 'EntryTime']).any()
    assert df.CloseTime.ge(df.EntryTime).all()
    assert np.isfinite(df[['R','SL','Pips']].to_numpy()).all()
    assert np.allclose(df.R, df.Pips / df.SL, atol=1e-8, rtol=0)
    assert len(select_period(df, *PERIODS['ALL'])) == len(df)
    for number, name in zip(range(25,29), CHINA4):
        assert set(df.loc[df.StrategyNo.eq(number),'Strategy']) == {name}
    return df

def metrics(df):
    d = df.sort_values(['CloseTime','EntryTime','StrategyNo'], kind='mergesort')
    r = d.R.to_numpy(dtype=float)
    equity = np.r_[0., np.cumsum(r)]
    losses = -r[r < 0].sum()
    daily = d.groupby(d.CloseTime.dt.normalize()).R.sum()
    weekly = d.groupby(d.CloseTime.dt.to_period('W-SUN')).R.sum()
    return {'Trades': len(d), 'TotalR': float(sum(d._ExactR, Decimal(0))),
            'PF': float(r[r>0].sum()/losses) if losses else np.nan,
            'MaxDDR': float((np.maximum.accumulate(equity)-equity).max()),
            'WorstDayR': float(daily.min()) if len(d) else 0.,
            'WorstWeekR': float(weekly.min()) if len(d) else 0.}

def compare(df, label):
    c1 = df.loc[~df.Strategy.isin(CHINA4)].copy()
    removed = df.loc[df.Strategy.isin(CHINA4)]
    assert len(c1) + len(removed) == len(df)
    a, b = metrics(df), metrics(c1)
    exact_delta = sum(c1._ExactR, Decimal(0)) - sum(df._ExactR, Decimal(0))
    assert exact_delta == -sum(removed._ExactR, Decimal(0))
    delta = {k: b[k]-a[k] for k in a}
    delta['TotalR'] = float(exact_delta)
    return [dict(Period=label,Candidate=c,**m) for c,m in [('C0_BASELINE',a),('C1_MINUS_CHINA4',b),('DELTA_C1_MINUS_C0',delta)]], exact_delta

def decide(delta):
    return 'REJECT_C1_KEEP_C0' if delta <= 0 else 'REVIEW_REQUIRED_NOT_ADOPTED'

def run(baseline, output_dir='/content'):
    df = load_baseline(baseline)
    rows, deltas = [], {}
    for label, bounds in PERIODS.items():
        sub = select_period(df,*bounds)
        part, deltas[label] = compare(sub,label)
        rows.extend(part)
    yearly = []
    for year in range(2015,2027):
        part, _ = compare(df.loc[df.EntryTime.dt.year.eq(year)],str(year))
        yearly.extend(part)
    assert deltas['ALL'] == deltas['IS']+deltas['OOS1']+deltas['OOS2']
    assert deltas['OOS_COMBINED'] == deltas['OOS1']+deltas['OOS2']
    assert len(select_period(df,*PERIODS['IS'])) == 9756
    assert len(select_period(df,*PERIODS['OOS2'])) == 995
    # Published C0 anchors, tolerance reflects six-decimal publication rounding.
    expected = {'IS':768.488273, 'OOS_COMBINED':621.779376, 'OOS2':19.818791}
    for label, total in expected.items():
        actual = next(r['TotalR'] for r in rows if r['Period']==label and r['Candidate']=='C0_BASELINE')
        assert abs(actual-total) <= 0.00000051
    provenance = dict(BaselineSHA256=BASELINE_HASH, Branch=BRANCH, PlanCommit=PLAN_COMMIT,
        RunJST=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(), BaselineTrades=len(df),
        BaselineRecalculated=False, LiveChanged=False)
    decision = dict(Candidate='C1_MINUS_CHINA4', DeltaTotalRExact=str(deltas['OOS_COMBINED']),
        Decision=decide(deltas['OOS_COMBINED']), PrimaryRule='OOS combined Delta Total R <= 0: reject; > 0: review, no automatic adoption',
        MoneySimulation='NOT_RUN', **provenance)
    tables = {'period_results':pd.DataFrame(rows), 'yearly_results':pd.DataFrame(yearly),
              'final_decision':pd.DataFrame([decision]), 'run_record':pd.DataFrame([provenance])}
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        file = out / f'china_demand_group_{name}.csv'
        table.to_csv(file,index=False,float_format='%.12f')
        print('\n'+file.name+'\n'+table.to_string(index=False))
    return tables

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output-dir',type=Path,default=Path('/content'))
    args=parser.parse_args()
    run(args.baseline,args.output_dir)
