"""Preregistered retrospective risk allocation; immutable baseline and live code."""
from pathlib import Path
from decimal import Decimal, localcontext
from collections import defaultdict
import sys, json, argparse
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
import volatility_phase1 as p1
import volatility_phase2 as p2
import edge_decay_phase2_money_simulation as money
D=Decimal
PLAN_SHA='a7f55489a36ebe353f74e4571222ae16ae0615cd'
PHASE2_SHA='0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc'
BRANCH='research/volatility-environment-phase3-risk-allocation'
RISKS={'R0_FIXED_090':('.90',)*5,'R1_MILD':('.70','.80','.90','1.00','1.10'),'R2_MODERATE':('.50','.70','.90','1.10','1.30'),'F1_Q1_OFF':('0','.90','.90','.90','.90')}
PERIODS={'ALL':('2015-01-01','2026-09-10'),**{k:v for k,v in p1.PERIODS.items() if k!='FULL'}}
ROOT=Path(__file__).resolve().parents[2]

def risk(candidate,q):
    if candidate not in RISKS: raise ValueError('Unregistered candidate')
    if q==p1.INS:return D('.90')
    if q not in p2.QUINTILES:raise ValueError('Invalid quintile')
    return D(RISKS[candidate][p2.QUINTILES.index(q)])

def validate(rows):
    money.validate_rows(rows)
    for r in rows:
        for start,end in PERIODS.values():
            if (start<=str(r['EntryTime'])[:10]<end)!=(start<=str(r['CloseTime'])[:10]<end):raise ValueError('Reset boundary crossing')

def simulate(rows,candidate,method):
    validate(rows)
    groups=defaultdict(list); skipped=[]
    for row in rows:
        q=row[method+'Quintile'];pct=risk(candidate,q)
        if not pct: skipped.append(row);continue
        groups[money.week_start(row['EntryTime'])].append((row,pct))
    balance=D(500000);logs=[];weeks=[]
    for week,items in sorted(groups.items()):
        if balance<=0:raise ValueError('Insolvent base')
        base=balance;total=D(0)
        for r,pct in sorted(items,key=lambda z:(z[0]['EntryTime'],z[0]['CloseTime'],z[0]['StrategyNo'],z[0]['RowId'])):
            pnl=base*pct/100*r['Pips']/r['SL'];total+=pnl
            logs.append(dict(r,WeeklyBase=base,RiskPct=pct,YenPnL=pnl,TradingWeekStart=week))
        balance+=total;weeks.append(dict(Week=week,WeeklyBase=base,PnL=total,FinalCapital=balance))
    balance=peak=D(500000)
    logs.sort(key=lambda r:(r['CloseTime'],r['EntryTime'],r['StrategyNo'],r['RowId']))
    for r in logs:
        balance+=r['YenPnL']
        if balance<=0:raise ValueError('Insolvent closed balance')
        peak=max(peak,balance)
        r.update(Capital=balance,PeakCapital=peak,DrawdownJPY=peak-balance,DrawdownPct=(peak-balance)/peak*100)
    metric=money.metrics(logs,*PERIODS['ALL'])
    metric.update(SkippedTrades=len(skipped),MeanNominalRiskPct=sum((risk(candidate,r[method+'Quintile']) for r in rows),D(0))/len(rows) if rows else D(0),MeanExecutedRiskPct=sum((r['RiskPct'] for r in logs),D(0))/len(logs) if logs else D(0))
    metric['MeanNominalRiskDeltaVsR0']=metric['MeanNominalRiskPct']-D('.90')
    return metric,logs,weeks

def decide(summary,verified):
    lookup={(r['Method'],r['Candidate'],r['Period']):r for r in summary};out=[]
    for c in list(RISKS)[1:]:
        p=lookup['primary',c,'ALL'];b=lookup['primary','R0_FIXED_090','ALL']
        diffs={k:lookup['primary',c,k]['FinalCapital']-lookup['primary','R0_FIXED_090',k]['FinalCapital'] for k in list(PERIODS)[1:]}
        conditions=dict(AllProfitPass=p['FinalCapital']>b['FinalCapital'],Reset3of4Pass=sum(v>=0 for v in diffs.values())>=3,RecentPass=diffs['RecentB']>0 or diffs['Monitor2026']>0,DrawdownPass=p['MaxDDPct']<=D('1.25')*b['MaxDDPct'],ValidationPass=verified)
        rd=lookup['robustness',c,'ALL']['FinalCapital']-lookup['robustness','R0_FIXED_090','ALL']['FinalCapital']
        out.append(dict(Candidate=c,**conditions,ResetNonnegativeCount=sum(v>=0 for v in diffs.values()),PrimaryFinalCapitalDelta=p['FinalCapital']-b['FinalCapital'],RobustnessFinalCapitalDelta=rd,RobustnessConsistent=rd>=0,Decision=('ECONOMIC_VALUE_CANDIDATE' if all(conditions.values()) else 'NOT_CANDIDATE') if verified else 'UNDETERMINED',Role='FILTER_CONTROL' if c.startswith('F') else 'RISK_ALLOCATION',LiveAdopted=False))
    return out

def assignments(baseline,paths,phase2_full,out):
    t=p1.load_baseline(baseline);manifest=pd.read_csv(ROOT/'results/volatility_phase2/volatility_phase2_input_manifest.csv').set_index('Filename')
    for name,expected in p2.SOURCE_HASHES.items():assert p1.sha(Path(p1.__file__).with_name(name))==expected
    selected={}
    for symbol,names in p1.FROZEN['MANIFEST_NAMES'].items():
        selected[symbol]=[]
        for name in names:
            hits=[Path(p) for p in paths if Path(p).name==name]
            if len(hits)!=1:raise ValueError('Missing/duplicate M1 '+name)
            if p1.sha(hits[0])!=manifest.loc[name,'SHA256']:raise ValueError('M1 hash mismatch '+name)
            selected[symbol].append(hits[0])
    arrays=[];audits=[]
    for symbol,files in selected.items():
        bars,_=p1.load_m1(files);daily=p1.features(p1.make_daily(bars));a=p1.assign(t[t.Symbol==symbol],daily)
        audits.extend(dict(Symbol=symbol,**r) for r in p2.manual_quintiles(p1.manual_audit(bars,daily,a),daily))
        arrays.append(p2.add_quintiles(a));print(symbol+' source features and manual audit PASS',flush=True)
    a=pd.concat(arrays).sort_values('TradeID').reset_index(drop=True)
    if phase2_full:
        rr=pd.read_csv(ROOT/'results/volatility_phase2/volatility_phase2_run_record.csv').iloc[0]
        expected=json.loads(rr.OutputHashes)['volatility_phase2_trade_assignments.csv']
        if p1.sha(phase2_full)!=expected:raise ValueError('Phase 2 full assignment hash mismatch')
        old=pd.read_csv(phase2_full)
        for col in ['TradeID','primaryQuintile','robustnessQuintile']:assert a[col].tolist()==old[col].tolist(),col
        for col in ['ATR20','RV20','primaryPercentile','robustnessPercentile']:np.testing.assert_allclose(a[col],old[col],rtol=0,atol=1e-10,equal_nan=True)
    # Full period / strategy / quintile reproduction, not just pooled means.
    expected=pd.concat([pd.read_csv(ROOT/'results/volatility_phase2/volatility_phase2_strategy_quintiles.csv'),pd.read_csv(ROOT/'results/volatility_phase2/volatility_phase2_period_quintiles.csv')])
    for _,r in expected[expected.ScopeType=='Strategy'].iterrows():
        start,end=p1.PERIODS[r.Period];x=a[(a.EntryTime>=start)&(a.EntryTime<end)&(a.StrategyNo==r.StrategyNo)&a[r.Method+'Quintile'].eq(r.Quintile)]
        assert len(x)==r.Trades
        np.testing.assert_allclose([x.R.sum(),x.R.mean()],[r.TotalR,r.AvgR],rtol=0,atol=1e-10,equal_nan=True)
    a.to_csv(out/'volatility_phase3_trade_assignments.csv',index=False)
    pd.DataFrame(audits).to_csv(out/'volatility_phase3_feature_manual_audit.csv',index=False)
    return a

def run(baseline,paths,output,implementation_sha,phase2_full=None):
    if len(implementation_sha)!=40:raise ValueError('Verified implementation SHA required')
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    a=assignments(baseline,paths,phase2_full,out)
    rows=money.load_baseline(baseline)
    for r in rows:
        for m in p1.METHODS:r[m+'Quintile']=a.iloc[r['RowId']][m+'Quintile']
    checks=[];summary=[];audits=[]
    from verify_volatility_phase3 import verify
    with localcontext() as ctx:
        ctx.prec=40
        for m in p1.METHODS:
            for c in RISKS:
                for period,(start,end) in PERIODS.items():
                    own=[r for r in rows if start<=str(r['EntryTime'])[:10]<end]
                    metrics,logs,weeks=simulate(own,c,m)
                    verify(own,c,m,metrics,logs)
                    summary.append(dict(Method=m,Candidate=c,Period=period,**metrics))
                    checks.append(dict(Method=m,Candidate=c,Period=period,Check='Independent all trades and metrics',Status='PASS',Trades=len(logs)))
                    if period=='ALL':
                        money.write_csv(out/f'volatility_phase3_{m}_{c}_trades.csv',logs)
                        money.write_csv(out/f'volatility_phase3_{m}_{c}_weekly.csv',weeks)
                        seen=set()
                        for r in logs:
                            q=r[m+'Quintile']
                            if q not in seen or r['TradingWeekStart'] in [w['Week'] for w in weeks[:2]]:
                                audits.append(dict(Method=m,Candidate=c,RowId=r['RowId'],EntryTime=r['EntryTime'],Quintile=q,WeeklyBase=r['WeeklyBase'],RiskPct=r['RiskPct'],Pips=r['Pips'],SL=r['SL'],YenPnL=r['YenPnL'],Status='PASS'));seen.add(q)
                        if c=='F1_Q1_OFF':
                            for r in [r for r in own if r[m+'Quintile']=='Q1'][:3]:audits.append(dict(Method=m,Candidate=c,RowId=r['RowId'],EntryTime=r['EntryTime'],Quintile='Q1',WeeklyBase='',RiskPct=0,Pips=r['Pips'],SL=r['SL'],YenPnL='',Status='SKIPPED_NOT_IN_CURVE'))
        for r in summary:
            b=next(x for x in summary if (x['Method'],x['Period'],x['Candidate'])==(r['Method'],r['Period'],'R0_FIXED_090'))
            r['FinalCapitalDeltaVsR0']=r['FinalCapital']-b['FinalCapital']
        tables={'money_summary':[r for r in summary if r['Period']=='ALL'], 'period_reset_summary':[r for r in summary if r['Period']!='ALL'],'risk_allocation_summary':[{k:r[k] for k in ['Method','Candidate','Period','Trades','SkippedTrades','MeanNominalRiskPct','MeanExecutedRiskPct','MeanNominalRiskDeltaVsR0']} for r in summary], 'robustness_summary':[r for r in summary if r['Method']=='robustness'],'decision':decide(summary,True),'verification':checks,'manual_audit':audits,'constraint_status':[dict(Status=money.CONSTRAINT_STATUS,Mode='BROKER_CONSTRAINED',LiveChanged=False)]}
        for name,data in tables.items():money.write_csv(out/f'volatility_phase3_{name}.csv',data)
    hashes={p.name:p1.sha(p) for p in sorted(out.glob('volatility_phase3_*.csv')) if not p.name.endswith('run_record.csv')}
    record=dict(Status='COMPLETED',Branch=BRANCH,PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,Phase2SHA=PHASE2_SHA,RunJST=pd.Timestamp.now(tz='Asia/Tokyo').isoformat(),BaselineHash=p1.sha(baseline),BaselineTrades=len(rows),Strategies=28,SourceM1Files=len(paths),Validation='PASS',IndependentVerification='PASS',FreshOOS=False,BaselineRecalculated=False,LiveChanged=False,MaxSavedRDifference=str(max(abs(r['Pips']/r['SL']-r['R']) for r in rows)),Python=sys.version.split()[0],Pandas=pd.__version__,Numpy=np.__version__,OutputHashes=json.dumps(hashes,sort_keys=True))
    money.write_csv(out/'volatility_phase3_run_record.csv',[record]);return tables

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--input-paths',required=True);p.add_argument('--output-dir',default='/content');p.add_argument('--implementation-sha',required=True);p.add_argument('--phase2-full')
    v=p.parse_args();run(v.baseline,json.loads(Path(v.input_paths).read_text()),v.output_dir,v.implementation_sha,v.phase2_full)
