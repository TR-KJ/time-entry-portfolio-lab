"""Independent numpy/pandas verifier; never imports the new simulation module."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

PREFIX = 'edge_decay_phase2_money_'
HASH = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'


def verify(baseline, output_dir, legacy_source):
    out = Path(output_dir)
    assert hashlib.sha256(Path(baseline).read_bytes()).hexdigest() == HASH
    d = pd.read_csv(baseline)
    for k in ('EntryTime', 'CloseTime'):
        d[k] = pd.to_datetime(d[k])
    d['RowId'] = np.arange(len(d))
    shifted = d.EntryTime - pd.Timedelta(hours=6)
    d['week'] = shifted.dt.to_period('W-SUN').dt.start_time + pd.Timedelta(hours=6)
    periods = {'IS': ('2015-01-01','2022-01-01'), 'OOS1': ('2022-01-01','2026-01-01'), 'OOS2': ('2026-01-01','2026-09-10'), 'OOS_COMBINED': ('2022-01-01','2026-09-10'), 'ALL': ('2015-01-01','2026-09-10')}
    periods.update({str(y): (f'{y}-01-01',f'{y+1}-01-01' if y<2026 else '2026-09-10') for y in range(2022,2027)})
    got = pd.concat([pd.read_csv(out/(PREFIX+n+'.csv'), dtype={'Period':str}) for n in ('period_results','yearly_results')])
    gotlogs = pd.read_csv(out/(PREFIX+'trade_log.csv'))
    gotweeks = pd.read_csv(out/(PREFIX+'weekly.csv'))
    tree = ast.parse(Path(legacy_source).read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('get_trading_week_start','run_weekly_fixed_risk_sim')]
    ns = dict(pd=pd, np=np, INITIAL_CAPITAL=500000, WEEK_ROLLOVER_HOUR=6)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(legacy_source), 'exec'), ns)
    expected, checks = {}, 0
    def close(actual, desired):
        nonlocal checks
        np.testing.assert_allclose(actual, desired, rtol=2e-10, atol=2e-7, equal_nan=True)
        checks += np.asarray(actual).size
    for risk in (0.25, 1., 1.5, 2.):
        for candidate in ('M0_BASELINE','M1_MINUS_22'):
            x = d.copy() if candidate=='M0_BASELINE' else d[d.Strategy!='22_GA_C_2'].copy()
            wr = (x.Pips/x.SL).groupby(x.week).sum()
            end = 500000*np.cumprod(1+wr.to_numpy()*risk/100)
            bases = pd.Series(np.r_[500000,end[:-1]], index=wr.index)
            x['base'] = x.week.map(bases)
            x['pnl'] = x.base*(risk/100)*(x.Pips/x.SL)
            x = x.sort_values(['CloseTime','EntryTime','StrategyNo','RowId'], kind='stable')
            x['capital'] = 500000+x.pnl.cumsum()
            x['prior'] = x.capital.shift(fill_value=500000)
            x['peak'] = np.maximum.accumulate(np.r_[500000,x.capital])[1:]
            x['dd'] = x.peak-x.capital
            x['ddpct'] = 100*x.dd/x.peak
            x['day'] = x.CloseTime.dt.normalize()
            close_shift = x.CloseTime-pd.Timedelta(hours=6)
            x['closeweek'] = close_shift.dt.to_period('W-SUN').dt.start_time+pd.Timedelta(hours=6)
            daybase = x.groupby('day').prior.first()
            weekbase = x.groupby('closeweek').prior.first()
            z = gotlogs[(gotlogs.RiskPct==risk)&(gotlogs.Candidate==candidate)].set_index('RowId').loc[x.RowId]
            for col, expectedcol in [('YenPnL','pnl'), ('Capital','capital'), ('DrawdownJPY','dd'), ('DrawdownPct','ddpct'), ('WeeklyBase','base')]:
                close(z[col].to_numpy(), x[expectedcol].to_numpy())
            zweek = gotweeks[(gotweeks.RiskPct==risk)&(gotweeks.Candidate==candidate)].sort_values('TradingWeekStart')
            close(zweek.FinalCapital.to_numpy(), end)
            ns['RISK_PER_TRADE_PCT'] = risk/100
            old, _ = ns['run_weekly_fixed_risk_sim'](x, candidate)
            old = old.set_index('RowId').loc[x.RowId]
            close(old.YenPnL.to_numpy(), x.pnl.to_numpy())
            close(old.Equity.iloc[-1], end[-1])
            for period,(start,stop) in periods.items():
                sub = x[x.EntryTime.ge(start)&x.EntryTime.lt(stop)]
                prev = x[x.CloseTime.lt(start)]
                initial = prev.capital.iloc[-1] if len(prev) else 500000
                final = sub.capital.iloc[-1] if len(sub) else initial
                net = final-initial
                loss = -sub.pnl.clip(upper=0).sum()
                exp = dict(Trades=len(sub), StartCapital=initial, FinalCapital=final, NetProfitJPY=net, ReturnPct=100*net/initial, MaxDDJPY=sub.dd.max(), MaxDDPct=sub.ddpct.max(), WorstDayPct=(sub.groupby('day').pnl.sum()/daybase*100).min(), WorstWeekPct=(sub.groupby('closeweek').pnl.sum()/weekbase*100).min(), MoneyRoMD=net/sub.dd.max(), MoneyPF=sub.pnl.clip(lower=0).sum()/loss if loss else np.nan)
                expected[(risk,period,candidate)] = exp
        for period in periods:
            a,b = [expected[risk,period,c] for c in ('M0_BASELINE','M1_MINUS_22')]
            expected[risk,period,'DELTA_M1_MINUS_M0'] = {k:b[k]-a[k] for k in a}
    for (risk,period,candidate), exp in expected.items():
        z = got[(got.RiskPct==risk)&(got.Period==period)&(got.Candidate==candidate)]
        assert len(z)==1
        for k,v in exp.items(): close(z.iloc[0][k],v)
    good = True
    for risk in (0.25,1.,1.5,2.):
        a = expected[risk,'ALL','DELTA_M1_MINUS_M0']['FinalCapital']
        b = expected[risk,'OOS_COMBINED','DELTA_M1_MINUS_M0']['NetProfitJPY']
        good &= (a>0 and b>0) if risk==1.5 else (a>=0 and b>=0)
    decision = pd.read_csv(out/(PREFIX+'decision.csv'))
    assert decision.iloc[0].ArithmeticDecision == ('MONEY_ADOPTION_CANDIDATE' if good else 'REJECT')
    record_path = out/(PREFIX+'run_record.csv')
    record = pd.read_csv(record_path, dtype=str)
    for name,sha in json.loads(record.iloc[0].CSVHashes).items():
        assert hashlib.sha256((out/name).read_bytes()).hexdigest()==sha
    decision['Decision'] = decision.ArithmeticDecision
    decision['Reason'] = decision.Reason.str.replace(';VALIDATION_NOT_PASSED','',regex=False).replace('VALIDATION_NOT_PASSED','ALL_FIXED_CONDITIONS_PASSED')
    decision['VerificationStatus'] = 'PASS'
    decision.to_csv(out/(PREFIX+'decision.csv'),index=False)
    pd.DataFrame([dict(Check='Baseline_hash_count_identities_boundaries',Status='PASS'),dict(Check=f'Independent_numpy_metrics_trade_week_values_{checks}',Status='PASS'),dict(Check='Legacy_v1_1_PnL_and_FinalCapital_all_8_runs',Status='PASS'),dict(Check='All_120_period_risk_candidate_rows_and_decision',Status='PASS'),dict(Check='CSV_hashes',Status='PASS')]).to_csv(out/(PREFIX+'verification.csv'),index=False)
    record['Decision'] = decision.iloc[0].Decision
    record['VerificationStatus'] = 'PASS'
    record['CSVHashes'] = json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob(PREFIX+'*.csv')) if f.name!=record_path.name},sort_keys=True)
    record.to_csv(record_path,index=False)
    print(f'PASS: {checks} values, 120 metric rows, legacy v1.1 all 8 runs, decision and hashes')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True)
    p.add_argument('--output-dir',required=True)
    p.add_argument('--legacy-source',required=True)
    verify(**vars(p.parse_args()))
