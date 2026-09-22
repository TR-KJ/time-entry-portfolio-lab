"""Independent checks of published C1 aggregates and representative M1 trades."""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'research'))
from daily_stop_baseline_revalidation import PIP_SIZE, SPREAD_PIPS, SYMBOL_TO_PAIR, load_pair
from exit_efficiency_phase1 import load_baseline, resolve_and_audit
from c1_path_management_phase1 import replay


def independent_trade(a, bars, variant):
    """Separate scalar implementation; all prices stay in raw price units."""
    start, scheduled = a['_entry'], a['_scheduled']
    end = next((scheduled + timedelta(minutes=k) for k in range(5)
                if scheduled + timedelta(minutes=k) in bars.index), None)
    if end is None:
        raise ValueError('missing exit')
    pair = a['Pair']
    is_long = a['Direction'] == 'Long'
    direction = 1 if is_long else -1
    pip = PIP_SIZE[pair]
    risk = float(a['SL']) * pip
    entry = float(bars.at[start, 'Open']) + direction * SPREAD_PIPS[pair] * pip
    target = None if not a['TP'] else entry + direction * float(a['TP']) * pip
    active_stop = entry - direction * risk
    next_stop = None
    reached_half = reached_one = False
    for t, bar in bars.loc[start:end].iterrows():
        if next_stop is not None:
            active_stop = next_stop
            next_stop = None
        stop_hit = (bar.Low <= active_stop) if is_long else (bar.High >= active_stop)
        target_hit = False if target is None else ((bar.High >= target) if is_long else (bar.Low <= target))
        if stop_hit or target_hit:
            if stop_hit:
                r = direction * (active_stop - entry) / risk
                reason = 'SL' if abs(r+1) < 1e-9 else 'DynamicSL'
            else:
                r = direction * (target - entry) / risk
                reason = 'TP'
            return t.strftime('%Y-%m-%d %H:%M:%S'), reason, round(r, 9)
        best = bar.High if is_long else bar.Low
        favorable = direction * (best - entry) / risk
        reached_half |= favorable >= .5 - 1e-10
        reached_one |= favorable >= 1 - 1e-10
        if variant == 'R1_BE50' and reached_half and direction*(active_stop-entry)/risk < 0:
            next_stop = entry
        elif variant == 'R2_LOCK100' and reached_one and direction*(active_stop-entry)/risk < .5:
            next_stop = entry + direction*.5*risk
        elif variant == 'R3_STAGED':
            if reached_one and direction*(active_stop-entry)/risk < .5:
                next_stop = entry + direction*.5*risk
            elif reached_half and direction*(active_stop-entry)/risk < 0:
                next_stop = entry
        if t == end:
            return t.strftime('%Y-%m-%d %H:%M:%S'), 'TimeExit', round(direction*(float(bar.Open)-entry)/risk, 9)
    raise AssertionError('unclosed')


def read(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def verify_aggregates(baseline, out):
    portfolio = read(out/'c1_path_management_phase1_portfolio_summary.csv')
    strategies = read(out/'c1_path_management_phase1_strategy_summary.csv')
    periods = read(out/'c1_path_management_phase1_trade_delta_summary.csv')
    formal = read(out/'c1_path_management_phase1_multiple_comparison.csv')
    anchor = load_baseline(baseline)
    active = [a for a in anchor if a['_n'] != 22]
    byv = {r['Variant']:r for r in portfolio}
    checks = []
    direct_base = sum(float(a['R']) for a in active)
    checks.append(('independent_baseline_total', abs(direct_base-float(byv['R0']['TotalR'])) < 1e-6,
                   f'{direct_base:.9f}'))
    for variant,row in byv.items():
        own = [x for x in strategies if x['Variant'] == variant]
        total = sum(float(x['TotalR']) for x in own)
        checks.append((f'{variant}_strategy_sum', abs(total-float(row['TotalR'])) < 1e-6, f'{total:.9f}'))
        if variant == 'R0':
            continue
        p = {x['Period']:x for x in periods if x['Variant'] == variant}
        d = float(p['Historical']['DeltaTotalR']) + float(p['Recent Combined']['DeltaTotalR'])
        checks.append((f'{variant}_period_sum',abs(d-float(p['ALL']['DeltaTotalR'])) < 1e-6, f'{d:.9f}'))
        counts = sum(int(p['ALL'][k]) for k in ('Improved','Harmed','Unchanged'))
        checks.append((f'{variant}_paired_counts',counts == 15837,str(counts)))
        change = float(row['TotalR'])-float(byv['R0']['TotalR'])
        checks.append((f'{variant}_delta',abs(change-float(p['ALL']['DeltaTotalR'])) < 1e-6,f'{change:.9f}'))
    order = sorted(formal,key=lambda x:(float(x['RawP']),x['Variant']))
    running = 0.0
    for rank,r in enumerate(order):
        running = max(running,min(1,(3-rank)*float(r['RawP'])))
        checks.append((f"{r['Variant']}_holm",abs(running-float(r['HolmAdjustedP'])) < 1e-12,str(running)))
    return checks


def verify_manual(baseline, manifest, root):
    anchors = load_baseline(baseline)
    paths,_ = resolve_and_audit(manifest,root)
    bypair = defaultdict(list)
    for a in anchors:
        if a['_n'] != 22:
            bypair[a['Pair']].append(a)
    checks = []
    variants = ('R1_BE50','R2_LOCK100','R3_STAGED')
    for symbol,pair in SYMBOL_TO_PAIR.items():
        bars = load_pair(paths[symbol],symbol)
        for variant in variants:
            selected = None
            for a in bypair[pair]:
                candidate = replay(a,bars,variant)
                if candidate['Triggered']:
                    selected = a,candidate
                    break
            if selected is None:
                # A TP at or before +1R can make LOCK100 unreachable for a
                # symbol's strategy set; audit an unchanged trade instead.
                a = bypair[pair][0]
                selected = a,replay(a,bars,variant)
            a,computed = selected
            independent = independent_trade(a,bars,variant)
            okay = (independent[0] == computed['CloseTime'] and
                    independent[1] == computed['ExitReason'] and
                    abs(independent[2]-float(computed['R'])) < 1e-8)
            checks.append((f'manual_{symbol}_{variant}',okay,
                           f"{a['EntryTime']} {independent[0]} {independent[1]} {independent[2]}"))
        del bars
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline',required=True)
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--m1-root',required=True)
    ap.add_argument('--out',required=True)
    a = ap.parse_args()
    out = Path(a.out)
    checks = verify_aggregates(a.baseline,out) + verify_manual(a.baseline,a.manifest,a.m1_root)
    path = out/'c1_path_management_phase1_independent_validation.csv'
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['Check','Status','Detail']);w.writeheader()
        w.writerows(dict(Check=name,Status='PASS' if okay else 'FAIL',Detail=detail) for name,okay,detail in checks)
    for name,okay,detail in checks:
        print('PASS' if okay else 'FAIL',name,detail)
    if not all(okay for _,okay,_ in checks):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
