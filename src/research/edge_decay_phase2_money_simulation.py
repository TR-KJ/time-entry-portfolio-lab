"""Preregistered theoretical weekly fixed-risk / compound study; no live changes."""
import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_HALF_UP
from pathlib import Path
from zoneinfo import ZoneInfo

D = Decimal
INITIAL = D('500000')
RISKS = (D('0.25'), D('1.0'), D('1.5'), D('2.0'))
PRIMARY = D('1.5')
TARGET = '22_GA_C_2'
BASELINE_HASH = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PLAN_SHA = 'a9dde1fec22ff33b1df5460bebf173fe7cd85941'
BRANCH = 'research/edge-decay-phase2-money-simulation'
PREFIX = 'edge_decay_phase2_money_'
PERIODS = {'IS': ('2015-01-01', '2022-01-01'), 'OOS1': ('2022-01-01', '2026-01-01'), 'OOS2': ('2026-01-01', '2026-09-10'), 'OOS_COMBINED': ('2022-01-01', '2026-09-10'), 'ALL': ('2015-01-01', '2026-09-10')}
YEARS = {str(y): (f'{y}-01-01', f'{y+1}-01-01' if y < 2026 else '2026-09-10') for y in range(2022, 2027)}
RULE = 'Primary 1.5%: ALL FinalCapital delta > 0 AND continuous OOS NetProfitJPY delta > 0; other fixed risks: both deltas >= 0; validation passes; no live adoption'
WEEK_SPEC = 'JST Monday 06:00; entry week; week-start Balance fixed within week; prior closed PnL compounds next week; continuous since 2015'
LOT_SPEC = 'THEORETICAL_UNCAPPED: Lot=RawLot; PnL=RiskAmount*Pips/SL; pip value cancels; no broker min/max/step/MaxAutoLot'
CONSTRAINT_STATUS = 'NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS'


def week_start(t):
    monday = t.replace(hour=6, minute=0, second=0, microsecond=0) - timedelta(days=t.weekday())
    return monday if t >= monday else monday - timedelta(days=7)


def validate_rows(rows):
    for r in rows:
        if r['SL'] <= 0 or not all(r[k].is_finite() for k in ('SL', 'Pips', 'R')):
            raise ValueError('Invalid SL/Pips/R')
        if r['EntryTime'].tzinfo or r['CloseTime'].tzinfo:
            raise ValueError('Expected naive JST timestamps')
        if not r['EntryTime'] <= r['CloseTime'] < week_start(r['EntryTime']) + timedelta(days=7):
            raise ValueError('Close before entry or crossing trading-week boundary')
        for start, end in list(PERIODS.values()) + list(YEARS.values()):
            a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
            if (a <= r['EntryTime'] < b) != (a <= r['CloseTime'] < b):
                raise ValueError('Trade crosses a reporting-period boundary')
        if abs(r['Pips']/r['SL'] - r['R']) > D('0.00000001'):
            raise ValueError('Saved R integrity mismatch')


def load_baseline(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_HASH:
        raise ValueError('Baseline SHA-256 mismatch')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    for i, r in enumerate(rows):
        r['RowId'] = i
        r['StrategyNo'] = int(r['StrategyNo'])
        for k in ('EntryTime', 'CloseTime'):
            r[k] = datetime.fromisoformat(r[k])
        for k in ('Pips', 'SL', 'R'):
            r[k] = D(r[k])
    ids = {(r['StrategyNo'], r['Strategy']) for r in rows}
    if len(rows) != 16298 or len(ids) != 28 or sorted(n for n, _ in ids) != list(range(1, 29)) or (22, TARGET) not in ids:
        raise ValueError('Baseline identities/count mismatch')
    if len({(r['StrategyNo'], r['EntryTime']) for r in rows}) != len(rows):
        raise ValueError('Duplicate entries')
    counts = [sum(a <= str(r['EntryTime'])[:10] < b for r in rows) for a, b in list(PERIODS.values())[:3]]
    if counts != [9756, 5547, 995]:
        raise ValueError('Period counts mismatch')
    validate_rows(rows)
    return rows


def ea_lot(risk_amount, sl, pip_value, minimum, maximum, step, max_auto=D('1'), allow_min=True):
    """EA formula for supplied historical inputs only; never assumes broker values."""
    if min(risk_amount, sl, pip_value, minimum, maximum) <= 0 or minimum > maximum or step < 0:
        raise ValueError('Invalid broker/risk inputs')
    raw = risk_amount / (sl * pip_value)
    if raw < minimum and not allow_min:
        return raw, D(0)
    lot = min(raw, max_auto) if max_auto > 0 else raw
    lot = min(maximum, max(minimum, lot))
    if step > 0:
        lot = (lot/step).to_integral_value(rounding=ROUND_FLOOR)*step
    return raw, lot.quantize(D('.01'), rounding=ROUND_HALF_UP)


def simulate(rows, risk, candidate):
    if risk not in RISKS or candidate not in ('M0_BASELINE', 'M1_MINUS_22'):
        raise ValueError('Unregistered risk/candidate')
    validate_rows(rows)
    selected = [r for r in rows if candidate == 'M0_BASELINE' or r['Strategy'] != TARGET]
    groups = defaultdict(list)
    for r in selected:
        groups[week_start(r['EntryTime'])].append(r)
    balance, logs, weekly = INITIAL, [], []
    for week, group in sorted(groups.items()):
        if balance <= 0:
            raise ValueError('Insolvent weekly base; adoption prohibited')
        base, amount = balance, balance*risk/100
        pnl = D(0)
        for r in sorted(group, key=lambda r: (r['EntryTime'], r['CloseTime'], r['StrategyNo'], r['RowId'])):
            value = amount*r['Pips']/r['SL']
            pnl += value
            logs.append({k: r[k] for k in ('RowId', 'StrategyNo', 'Strategy', 'Pair', 'EntryTime', 'CloseTime', 'SL', 'Pips', 'R')} | dict(Candidate=candidate, RiskPct=risk, TradingWeekStart=week, WeeklyBase=base, RiskAmount=amount, RCalculated=r['Pips']/r['SL'], YenPnL=value))
        balance += pnl
        weekly.append(dict(Candidate=candidate, RiskPct=risk, TradingWeekStart=week, StartCapital=base, RiskAmount=amount, Trades=len(group), NetProfitJPY=pnl, ReturnPct=pnl/base*100, FinalCapital=balance))
    equity, peak = INITIAL, INITIAL
    for r in sorted(logs, key=lambda r: (r['CloseTime'], r['EntryTime'], r['StrategyNo'], r['RowId'])):
        equity += r['YenPnL']
        if equity <= 0:
            raise ValueError('Insolvent closed balance; adoption prohibited')
        peak = max(peak, equity)
        r.update(Capital=equity, PeakCapital=peak, DrawdownJPY=peak-equity, DrawdownPct=(peak-equity)/peak*100)
    logs.sort(key=lambda r: (r['CloseTime'], r['EntryTime'], r['StrategyNo'], r['RowId']))
    return logs, weekly


def metrics(logs, start, end):
    a, b = datetime.fromisoformat(start), datetime.fromisoformat(end)
    sub = [r for r in logs if a <= r['EntryTime'] < b]
    before = [r for r in logs if r['CloseTime'] < a]
    initial = before[-1]['Capital'] if before else INITIAL
    final = sub[-1]['Capital'] if sub else initial
    daily, weekly, day_bases, week_bases = defaultdict(Decimal), defaultdict(Decimal), {}, {}
    prior = INITIAL
    for r in logs:
        day, week = r['CloseTime'].date(), week_start(r['CloseTime'])
        day_bases.setdefault(day, prior)
        week_bases.setdefault(week, prior)
        prior = r['Capital']
    for r in sub:
        daily[r['CloseTime'].date()] += r['YenPnL']
        weekly[week_start(r['CloseTime'])] += r['YenPnL']
    dd = max((r['DrawdownJPY'] for r in sub), default=D(0))
    gain = sum((max(r['YenPnL'], D(0)) for r in sub), D(0))
    loss = -sum((min(r['YenPnL'], D(0)) for r in sub), D(0))
    return dict(Trades=len(sub), StartCapital=initial, FinalCapital=final, NetProfitJPY=final-initial, ReturnPct=(final-initial)/initial*100, MaxDDJPY=dd, MaxDDPct=max((r['DrawdownPct'] for r in sub), default=D(0)), WorstDayPct=min((v/day_bases[k]*100 for k,v in daily.items()), default=D(0)), WorstWeekPct=min((v/week_bases[k]*100 for k,v in weekly.items()), default=D(0)), MoneyRoMD=(final-initial)/dd if dd else None, MoneyPF=gain/loss if loss else None)


def decide(deltas, verified=True):
    if set(deltas) != set(RISKS):
        raise ValueError('Exactly four fixed risks required')
    reasons = []
    for risk in RISKS:
        for metric, value in deltas[risk].items():
            if not value.is_finite():
                raise ValueError('Nonfinite decision metric')
            if value <= 0 if risk == PRIMARY else value < 0:
                reasons.append(f'{risk}%:{metric}:NOT_POSITIVE' if risk == PRIMARY else f'{risk}%:{metric}:NEGATIVE')
    if not verified:
        reasons.append('VALIDATION_NOT_PASSED')
    return dict(Decision='REJECT' if reasons else 'MONEY_ADOPTION_CANDIDATE', Reason=';'.join(reasons) or 'ALL_FIXED_CONDITIONS_PASSED', PrimaryRiskPct=PRIMARY, Rule=RULE, LiveAdopted=False)


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def run(baseline, output_dir, implementation_sha, execution='LOCAL'):
    if len(implementation_sha) != 40 or any(c not in '0123456789abcdef' for c in implementation_sha):
        raise ValueError('Confirmed implementation SHA required')
    with localcontext() as ctx:
        ctx.prec = 40
        rows = load_baseline(baseline)
        tables = {'period_results': [], 'yearly_results': [], 'weekly': [], 'trade_log': []}
        deltas = {}
        for risk in RISKS:
            simulations = {}
            for candidate in ('M0_BASELINE', 'M1_MINUS_22'):
                log, weekly = simulate(rows, risk, candidate)
                simulations[candidate] = log
                tables['trade_log'].extend(log)
                tables['weekly'].extend(weekly)
            for table, periods in (('period_results', PERIODS), ('yearly_results', YEARS)):
                for period, bounds in periods.items():
                    a, b = [metrics(log, *bounds) for log in simulations.values()]
                    delta = {k: b[k]-a[k] if a[k] is not None and b[k] is not None else None for k in a}
                    for candidate, result in zip(('M0_BASELINE', 'M1_MINUS_22', 'DELTA_M1_MINUS_M0'), (a, b, delta)):
                        tables[table].append(dict(RiskPct=risk, Period=period, Candidate=candidate, **result))
                    if period == 'ALL':
                        deltas.setdefault(risk, {})['ALL_FinalCapital'] = delta['FinalCapital']
                    elif period == 'OOS_COMBINED':
                        deltas.setdefault(risk, {})['OOS_NetProfitJPY'] = delta['NetProfitJPY']
        # Independent verification is a required separate gate; provisional arithmetic result retained.
        tables['decision'] = [decide(deltas, verified=False) | dict(ArithmeticDecision=decide(deltas)['Decision'], VerificationStatus='PENDING')]
        tables['constraint_status'] = [dict(Mode='THEORETICAL_UNCAPPED', Status='RUN', MainDecision=True, Description=LOT_SPEC), dict(Mode='EA_CONSTRAINED', Status=CONSTRAINT_STATUS, MainDecision=False, Description='Missing historical JPY pip value, symbol volume min/max/step, weekly floating equity; MaxAutoLot=1 and AllowMinLot=true documented only')]
        tables['verification'] = [dict(Check='Baseline_hash_count_identities_boundaries', Status='PASS'), dict(Check='Independent_full_metrics_and_legacy_v1_1', Status='PENDING')]
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        hashes = {}
        for name, values in tables.items():
            file = out/(PREFIX+name+'.csv')
            write_csv(file, values)
            hashes[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
        record = dict(BaselineSHA256=BASELINE_HASH, BaselineTrades=len(rows), BaselineStrategies=28, Branch=BRANCH, PlanSHA=PLAN_SHA, ImplementationSHA=implementation_sha, RunJST=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(), InitialCapitalJPY=INITIAL, RiskPcts=json.dumps([str(x) for x in RISKS]), PrimaryRiskPct=PRIMARY, WeeklyBaseSpec=WEEK_SPEC, LotSpec=LOT_SPEC, DecisionRule=RULE, Periods=json.dumps(PERIODS), PeriodBasis='EntryTime_JST; continuous capital; boundary-crossing rejected', Execution=execution, ConstrainedStatus=CONSTRAINT_STATUS, SavedRMaxRoundingDifference=max(abs(r['R']-r['Pips']/r['SL']) for r in rows), BaselineRecalculated=False, FreshHoldout=False, LiveChanged=False, Decision=tables['decision'][0]['Decision'], VerificationStatus='PENDING', CSVHashes=json.dumps(hashes, sort_keys=True), RunRecordCSV=PREFIX+'run_record.csv')
        write_csv(out/(PREFIX+'run_record.csv'), [record])
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', required=True)
    p.add_argument('--output-dir', required=True)
    p.add_argument('--implementation-sha', required=True)
    run(**vars(p.parse_args()))
