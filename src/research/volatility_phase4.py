"""Fixed 27-strategy R2 validation. No production EA changes or inferred inputs."""
from pathlib import Path
from decimal import Decimal as D, localcontext
import argparse, csv, hashlib, json, sys
import pandas as pd
import volatility_phase3 as p3

ROOT = Path(__file__).resolve().parents[2]
PLAN_SHA = '08d594b092cc0555ec3f917118eb5e8c22ca22d5'
BASE_SHA = '144f7be6a97017cb7292c5ed9d9e8f4ef845af63'
BRANCH = 'research/volatility-environment-phase4-deployment-validation'
CANDIDATES = ('R0_FIXED_090', 'R2_MODERATE')
PREFIX = 'volatility_phase4_'

def risk(candidate, quintile):
    if candidate not in CANDIDATES:
        raise ValueError('Unregistered Phase 4 candidate')
    return p3.risk(candidate, quintile)

def scenario(rows):
    expected = {s['StrategyNo']: s['Strategy'] for s in p3.p1.STRATEGIES}
    if set(r['StrategyNo'] for r in rows) != set(expected):
        raise ValueError('Expected all 28 baseline identities')
    if any(r['Strategy'] != expected[r['StrategyNo']] for r in rows):
        raise ValueError('Strategy identity mismatch')
    kept = [r.copy() for r in rows if r['Strategy'] != '22_GA_C_2']
    assert set(r['StrategyNo'] for r in kept) == set(expected) - {22}
    assert all(a == b for a, b in zip(kept, [r for r in rows if r['StrategyNo'] != 22]))
    return kept

def simulate(rows, candidate, method):
    for r in rows:
        risk(candidate, r[method+'Quintile'])
    return p3.simulate(rows, candidate, method)

def decide(summary, validation=None, audit=None):
    conditions = {k: None for k in ['AllProfitPass','Reset3of4Pass','RecentPass','DrawdownPass','WorstDayPass','RobustnessPass']}
    if summary:
        t = {(r['Method'],r['Candidate'],r['Period']):r for r in summary}
        b = t['primary','R0_FIXED_090','ALL']; r = t['primary','R2_MODERATE','ALL']
        delta = {k:t['primary','R2_MODERATE',k]['FinalCapital']-t['primary','R0_FIXED_090',k]['FinalCapital'] for k in p3.PERIODS if k != 'ALL'}
        conditions.update(AllProfitPass=r['FinalCapital']>b['FinalCapital'], Reset3of4Pass=sum(v>=0 for v in delta.values())>=3,
            RecentPass=delta['RecentB']>0 or delta['Monitor2026']>0,
            DrawdownPass=r['MaxDDPct']<=b['MaxDDPct']*D('1.25'), WorstDayPass=r['WorstDayPct']>D('-20'),
            RobustnessPass=t['robustness','R2_MODERATE','ALL']['FinalCapital']>=t['robustness','R0_FIXED_090','ALL']['FinalCapital'])
    conditions.update(DeploymentAuditPass=audit, ValidationPass=validation)
    values=list(conditions.values())
    label='NOT_CANDIDATE' if False in values else ('UNDETERMINED' if None in values else 'DEMO_FORWARD_CANDIDATE')
    return dict(Candidate='R2_MODERATE',**conditions,WorstDaySafetyLimitPct=-20,WorstDayComparison='STRICT_GREATER_THAN',Decision=label,LiveAdopted=False)

def write(out, name, rows):
    p3.money.write_csv(out/(PREFIX+name+'.csv'), rows)

def check_sources():
    manifest=pd.read_csv(ROOT/'results/volatility_phase3/volatility_phase3_source_manifest.csv')
    # Explicit frozen dependency manifest generated from preregistered base.
    frozen=json.loads((Path(__file__).with_name('volatility_phase4_frozen_sources.json')).read_text())
    for path, expected in frozen.items():
        if p3.p1.sha(ROOT/path)!=expected: raise ValueError('Frozen source changed: '+path)
    return frozen

def run(output, implementation_sha, baseline=None, paths=None, phase2_full=None):
    if len(implementation_sha)!=40 or any(c not in '0123456789abcdef' for c in implementation_sha):
        raise ValueError('Remote-verified implementation SHA required')
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    if any(out.glob(PREFIX+'*.csv')): raise ValueError('Use a fresh output directory to avoid stale results')
    frozen=check_sources()
    audit_path=ROOT/'research_inputs/volatility_phase4_deployment_audit.csv'
    audit=pd.read_csv(audit_path).fillna('')
    audit.to_csv(out/(PREFIX+'deployment_feasibility.csv'),index=False)
    # This audit is pending current SET/spec evidence; source capability is not deployment approval.
    audit_pass=None
    summary=[];checks=[];manual=[];rows=[];kept=[]
    missing=[]
    if not baseline or not Path(baseline).is_file(): missing.append('BASELINE_ORIGINAL_CSV')
    if paths is None: missing.append('FROZEN_56_M1_FILES')
    else:
        provided={Path(p).name for p in paths if Path(p).is_file()}
        for names in p3.p1.FROZEN['MANIFEST_NAMES'].values():
            missing.extend(n for n in names if n not in provided)
    with localcontext() as ctx:
        ctx.prec=40
        if not missing:
            # Inherited routine rehashes all M1 inputs and validates full feature regression.
            a=p3.assignments(baseline,paths,phase2_full,out)
            rows=p3.money.load_baseline(baseline)
            if len(a)!=len(rows) or a.TradeID.tolist()!=list(range(len(rows))):
                raise ValueError('Assignment row identity mismatch')
            for r in rows:
                for method in p3.p1.METHODS:r[method+'Quintile']=a.iloc[r['RowId']][method+'Quintile']
            kept=scenario(rows)
            from verify_volatility_phase4 import verify
            for method in p3.p1.METHODS:
                for candidate in CANDIDATES:
                    for period,(start,end) in p3.PERIODS.items():
                        own=[r for r in kept if start<=str(r['EntryTime'])[:10]<end]
                        if not own: raise ValueError('Unexpected empty fixed period')
                        metric,logs,weeks=simulate(own,candidate,method)
                        verify(own,candidate,method,metric,logs)
                        summary.append(dict(Method=method,Candidate=candidate,Period=period,**metric))
                        checks.append(dict(Check='Independent all trade/metric verification',Method=method,Candidate=candidate,Period=period,Status='PASS'))
                        if period=='ALL':
                            write(out,method+'_'+candidate+'_trades',logs)
                            seen=set()
                            for r in logs:
                                q=r[method+'Quintile']
                                if q not in seen or r['TradingWeekStart'] in [w['Week'] for w in weeks[:2]]:
                                    manual.append(dict(Method=method,Candidate=candidate,RowId=r['RowId'],Strategy=r['Strategy'],EntryTime=r['EntryTime'],Quintile=q,WeeklyBase=r['WeeklyBase'],RiskPct=r['RiskPct'],SL=r['SL'],Pips=r['Pips'],YenPnL=r['YenPnL'],Status='INDEPENDENT_MATCH'));seen.add(q)
            for r in summary:
                base=next(b for b in summary if (b['Method'],b['Period'],b['Candidate'])==(r['Method'],r['Period'],'R0_FIXED_090'))
                r['FinalCapitalDeltaVsR0']=r['FinalCapital']-base['FinalCapital']
            write(out,'27strategy_money_summary',[r for r in summary if r['Period']=='ALL'])
            write(out,'period_reset_summary',[r for r in summary if r['Period']!='ALL'])
            write(out,'robustness_summary',[r for r in summary if r['Method']=='robustness'])
            write(out,'manual_audit',manual)
            write(out,'scenario_identity',[dict(RowId=r['RowId'],StrategyNo=r['StrategyNo'],Strategy=r['Strategy']) for r in kept])
        else:
            for name in ['27strategy_money_summary','period_reset_summary','robustness_summary']:
                write(out,name,[dict(Status='NOT_RUN_INPUT_MISSING',MissingInputs=json.dumps(missing),MetricsComputed=False)])
    checks.extend([dict(Check='Frozen source hashes',Status='PASS'),dict(Check='Real input regression',Status='NOT_RUN_INPUT_MISSING' if missing else 'PASS'),
                   dict(Check='Historical broker constrained simulation',Status='NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS'),
                   dict(Check='Current static lot table',Status='NOT_RUN_MISSING_CURRENT_SYMBOL_SPECS'),
                   dict(Check='Current SET corroboration',Status='UNVERIFIED_CURRENT_SET'),
                   dict(Check='Full validation including regeneration and notebook',Status='PENDING')])
    write(out,'verification',checks)
    # Full validation cannot be marked PASS by the money routine itself.
    write(out,'decision',[decide(summary,validation=None,audit=audit_pass)])
    hashes={p.name:p3.p1.sha(p) for p in sorted(out.glob('*.csv'))}
    write(out,'run_record',[dict(Status='NOT_RUN_INPUT_MISSING' if missing else 'MONEY_VERIFIED_AUDIT_AND_FULL_VALIDATION_PENDING',Branch=BRANCH,PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,
        BaseSHA=BASE_SHA,BaselineHash=p3.p1.sha(baseline) if baseline and Path(baseline).is_file() else '',BaselineTrades=len(rows) if rows else '',ScenarioTrades=len(kept) if kept else '',
        RemovedTrades=len(rows)-len(kept) if rows else '',ScenarioStrategies=27 if kept else '',Validation='PENDING',IndependentMoneyVerification='NOT_RUN' if missing else 'PASS',
        BaselineRecalculated=False,LiveChanged=False,HistoricalBrokerStatus='NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS',MissingInputs=json.dumps(missing),
        Python=sys.version.split()[0],Pandas=pd.__version__,Numpy=p3.np.__version__,OutputHashes=json.dumps(hashes,sort_keys=True))])
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',default='/content/volatility_phase4');p.add_argument('--implementation-sha',required=True)
    p.add_argument('--baseline');p.add_argument('--input-paths');p.add_argument('--phase2-full')
    v=p.parse_args();run(v.output_dir,v.implementation_sha,v.baseline,json.loads(Path(v.input_paths).read_text()) if v.input_paths else None,v.phase2_full)
