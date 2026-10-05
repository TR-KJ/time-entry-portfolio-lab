"""Unrounded deterministic Pips metrics; PF state is separate from JSON value."""
import numpy as np
from .stage1_contract import YEARS

def metric_block(pips):
    p = np.asarray(pips, dtype=np.float64)
    if not np.isfinite(p).all(): raise ValueError('nonfinite Pips')
    n = len(p); wins = int(np.count_nonzero(p > 0)); losses = int(np.count_nonzero(p < 0))
    gain = float(np.sum(p[p > 0])); loss = float(np.sum(p[p < 0]))
    state = 'FINITE' if loss < 0 else ('INF' if gain > 0 else 'UNDEFINED')
    pf = gain / abs(loss) if loss < 0 else None
    total = float(np.sum(p))
    curve = np.cumsum(p)
    dd = float(np.max(np.maximum.accumulate(np.r_[0., curve])[1:] - curve)) if n else 0.
    return dict(Trades=n, Wins=wins, Losses=losses, ZeroPips=n-wins-losses, TotalPips=total,
                AvgPips=total/n if n else None, PFpips=pf, PFState=state, MaxDDPips=dd)

def summarize_arrays(pips, entries, closes, years):
    """One structure/variant, hence fixed key is identical across its trades."""
    p = np.asarray(pips); entries = np.asarray(entries); closes = np.asarray(closes); years = np.asarray(years)
    order = np.lexsort((entries, closes)); p = p[order]; years = years[order]
    out = metric_block(p)
    annual = {str(y): metric_block(p[years == y]) for y in YEARS}
    out['Annual'] = annual
    out['PositiveYearCount'] = sum(a['TotalPips'] > 0 for a in annual.values())
    out['NegativeYearCount'] = sum(a['TotalPips'] < 0 for a in annual.values())
    sufficient = all(a['Trades'] >= 30 for a in annual.values())
    avgs = [a['AvgPips'] for a in annual.values()]
    out['MedianAnnualAvgPips'] = float(np.median(avgs)) if sufficient else None
    out['WorstYearAvgPips'] = min(avgs) if all(a is not None for a in avgs) else None
    return out

def summarize(trades):
    # Independent API handles merged trades: fixed key is the final ordering field.
    ts = sorted(trades, key=lambda t: (t['CloseTime'], t['EntryTime'], tuple(t['FixedKey'])))
    p = np.array([t['Pips'] for t in ts]); years = np.array([int(str(t['EntryTime'])[:4]) for t in ts])
    # Already fully ordered: integer positions preserve the fixed-key order on ties.
    pos = np.arange(len(ts))
    return summarize_arrays(p, pos, pos, years)

def gate(m, sl=False):
    return bool(m['Trades'] >= 150 and all(m['Annual'][str(y)]['Trades'] >= 30 for y in YEARS)
                and m['Losses'] >= 10 and m['AvgPips'] is not None and m['AvgPips'] > 0
                and m['PFState'] == 'FINITE' and m['PFpips'] >= (1.05 if sl else 1.10)
                and m['PositiveYearCount'] >= 3)

def point_result(pure, fixed):
    passed = [gate(m, True) for m in fixed]
    return dict(PurePASS=gate(pure), SLPASS=passed, PassingSLCount=sum(passed),
                SLRobustnessPASS=sum(passed) >= 3, FormalPASS=gate(pure) and sum(passed) >= 3)

def ranking_key(record):
    m = record['PureMetrics']
    if not record['FormalPASS'] or not gate(m): raise ValueError('ineligible ranking input')
    return (-m['PositiveYearCount'], -m['MedianAnnualAvgPips'], -m['WorstYearAvgPips'], -m['PFpips'],
            -m['AvgPips'], -m['TotalPips'], m['MaxDDPips'], *record['FixedKey'])
