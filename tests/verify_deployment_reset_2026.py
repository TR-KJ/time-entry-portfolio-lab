"""Independent pandas/numpy and original-v1.1 reconciliation. No simulation import."""
import argparse
import ast
import csv
import hashlib
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

PREFIX='deployment_reset_2026_'
HASH='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
TARGETS={'D0_BASELINE':None,'D1_MINUS_22':'22_GA_C_2','D2_MINUS_18':'18_EA_2_MonWed_Short','D3_MINUS_20':'20_EA_1A_MonTue_Short','D4_MINUS_23':'23_GA_F_2'}


def read(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))


def write(path,rows):
    with Path(path).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def verify(baseline,output_dir,legacy_source):
    out=Path(output_dir)
    assert hashlib.sha256(Path(baseline).read_bytes()).hexdigest()==HASH
    d=pd.read_csv(baseline)
    assert len(d)==16298 and d.Strategy.nunique()==28
    for col in ('EntryTime','CloseTime'):d[col]=pd.to_datetime(d[col])
    d['RowId']=np.arange(len(d))
    entry=d.EntryTime.ge('2026-01-01')&d.EntryTime.lt('2026-09-10')
    closed=d.CloseTime.ge('2026-01-01')&d.CloseTime.lt('2026-09-10')
    assert (entry==closed).all()
    d=d[entry].copy();assert len(d)==995
    shifted=d.EntryTime-pd.Timedelta(hours=6)
    d['week']=shifted.dt.to_period('W-SUN').dt.start_time+pd.Timedelta(hours=6)
    assert (d.CloseTime<d.week+pd.Timedelta(days=7)).all()
    got=pd.read_csv(out/(PREFIX+'summary.csv'))
    comparisons=pd.read_csv(out/(PREFIX+'risk_comparison.csv'))
    details=pd.read_csv(out/(PREFIX+'detailed_metrics.csv'))
    logs=pd.read_csv(out/(PREFIX+'trade_log.csv'))
    weeks=pd.read_csv(out/(PREFIX+'weekly.csv'))
    assert len(got)==20 and len(comparisons)==16 and len(details)==5
    assert not got.duplicated(['Candidate','RiskPct']).any()
    tree=ast.parse(Path(legacy_source).read_text())
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('get_trading_week_start','run_weekly_fixed_risk_sim')]
    assert len(funcs)==2
    ns=dict(pd=pd,np=np,INITIAL_CAPITAL=500000,WEEK_ROLLOVER_HOUR=6)
    exec(compile(ast.Module(body=funcs,type_ignores=[]),str(legacy_source),'exec'),ns)
    count=0
    def close(a,b):
        nonlocal count
        np.testing.assert_allclose(a,b,rtol=1e-10,atol=1e-7,equal_nan=True)
        count+=np.asarray(a).size
    expected={}
    for risk in (0.25,1.,1.5,2.):
        for c,target in TARGETS.items():
            x=d[d.Strategy!=target].copy()
            wr=(x.Pips/x.SL).groupby(x.week).sum()
            end=500000*np.cumprod(1+wr.to_numpy()*risk/100)
            bases=pd.Series(np.r_[500000,end[:-1]],index=wr.index)
            x['base']=x.week.map(bases)
            x['pnl']=x.base*(risk/100)*(x.Pips/x.SL)
            x=x.sort_values(['CloseTime','EntryTime','StrategyNo','RowId'],kind='stable')
            x['capital']=500000+x.pnl.cumsum()
            x['prior']=x.capital.shift(fill_value=500000)
            x['peak']=np.maximum.accumulate(np.r_[500000,x.capital])[1:]
            x['dd']=x.peak-x.capital
            x['ddpct']=100*x.dd/x.peak
            x['day']=x.CloseTime.dt.normalize()
            assert (x.capital>0).all() and (x.base>0).all()
            z=logs[(logs.RiskPct==risk)&(logs.Candidate==c)]
            assert len(z)==len(x) and z.RowId.tolist()==x.RowId.tolist()
            for a,b in [('YenPnL','pnl'),('Capital','capital'),('PeakCapital','peak'),('DrawdownJPY','dd'),('DrawdownPct','ddpct'),('WeeklyBase','base')]:
                close(z[a].to_numpy(),x[b].to_numpy())
            zw=weeks[(weeks.RiskPct==risk)&(weeks.Candidate==c)].sort_values('TradingWeekStart')
            assert len(zw)==len(wr)
            close(zw.FinalCapital,end);close(zw.StartCapital,bases)
            close(zw.NetProfitJPY,end-bases.to_numpy())
            close(zw.Trades,x.groupby('week').size())
            close(zw.ReturnPct,wr*risk)
            ns['RISK_PER_TRADE_PCT']=risk/100
            old,_=ns['run_weekly_fixed_risk_sim'](x,c)
            old=old.set_index('RowId').loc[x.RowId]
            close(old.YenPnL,x.pnl);close(old.Equity.iloc[-1],end[-1])
            final=x.capital.iloc[-1];net=final-500000
            loss=-x.pnl.clip(upper=0).sum()
            exp=dict(Trades=len(x),StartCapital=500000,FinalCapital=final,NetProfitJPY=net,ReturnPct=net/500000*100,
                     MaxDDJPY=x.dd.max(),MaxDDPct=x.ddpct.max(),
                     WorstDayPct=(x.groupby('day').pnl.sum()/x.groupby('day').prior.first()*100).min(),
                     WorstWeekPct=(x.groupby('week').pnl.sum()/x.groupby('week').prior.first()*100).min(),
                     MoneyRoMD=net/x.dd.max(),MoneyPF=x.pnl.clip(lower=0).sum()/loss if loss else np.nan)
            expected[risk,c]=exp
            z=got[(got.RiskPct==risk)&(got.Candidate==c)];assert len(z)==1
            assert z.iloc[0].Trades==len(x)
            for k,v in exp.items():close(z.iloc[0][k],v)
        for c in TARGETS:
            a,b=expected[risk,'D0_BASELINE'],expected[risk,c]
            diff={k:b[k]-a[k] for k in a}
            z=got[(got.RiskPct==risk)&(got.Candidate==c)].iloc[0]
            close(z.DeltaFinalCapital,diff['FinalCapital']);close(z.DeltaNetProfitJPY,diff['NetProfitJPY'])
            if c!='D0_BASELINE':
                z=comparisons[(comparisons.RiskPct==risk)&(comparisons.Candidate==c)];assert len(z)==1
                for k,v in diff.items():close(z.iloc[0]['Delta'+k],v)
            if risk==1.5:
                z=details[details.Candidate==c];assert len(z)==1
                for k,v in b.items():close(z.iloc[0][k],v)
                for k,v in diff.items():close(z.iloc[0]['Delta'+k],v)
    record_path=out/(PREFIX+'run_record.csv')
    record=read(record_path)
    for name,sha in json.loads(record[0]['CSVHashes']).items():
        assert hashlib.sha256((out/name).read_bytes()).hexdigest()==sha
    assert json.loads(record[0]['Candidates'])==TARGETS
    assert record[0]['InitialCapitalJPY']=='500000'
    assert record[0]['PlanSHA']=='524b93bdcfc3cccf739c85cf8826f236e511fa47'
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_deployment_reset_2026.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful() and result.testsRun==15
    decision=read(out/(PREFIX+'decision.csv'))
    assert len(decision)==4
    for row in decision:
        c=row['Candidate']
        ds={r:expected[r,c]['FinalCapital']-expected[r,'D0_BASELINE']['FinalCapital'] for r in (0.25,1.,1.5,2.)}
        primary=ds[1.5]>0;robust=all(ds[r]>=0 for r in (0.25,1.,2.))
        want='DEPLOYMENT_RESET_CANDIDATE' if primary and robust else 'NOT_CANDIDATE'
        assert row['ArithmeticDecision']==want
        assert row['ResetImprovement1_5']==str(primary) and row['OtherRiskRobustness']==str(robust)
        row.update(Decision=want,ShadowForwardCandidate=str(primary and robust),VerificationStatus='PASS')
    write(out/(PREFIX+'decision.csv'),decision)
    checks=[dict(Check='Baseline_hash_count_identities_boundaries_and_reset',Status='PASS'),
            dict(Check=f'Independent_numeric_values_{count}',Status='PASS'),
            dict(Check='Legacy_v1_1_all_20_runs_PnL_and_FinalCapital',Status='PASS'),
            dict(Check='20_summary_16_comparison_5_detail_rows_and_4_decisions',Status='PASS'),
            dict(Check='Unit_tests_15',Status='PASS'),dict(Check='CSV_hashes',Status='PASS')]
    write(out/(PREFIX+'verification.csv'),checks)
    record[0]['VerificationStatus']='PASS'
    record[0]['CSVHashes']=json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob(PREFIX+'*.csv')) if p!=record_path},sort_keys=True)
    write(record_path,record)
    print(f'PASS: {count} independent values; 20 v1.1 reconciliations; 15 unit tests; 4 decisions')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True)
    p.add_argument('--output-dir',required=True)
    p.add_argument('--legacy-source',required=True)
    verify(**vars(p.parse_args()))
