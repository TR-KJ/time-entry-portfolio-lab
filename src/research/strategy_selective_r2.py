"""A5 preregistered, 27-strategy selective R2 research. Never alters live files."""
from __future__ import annotations
import argparse, csv, hashlib, json, statistics, sys
from collections import Counter, defaultdict
from decimal import Decimal as D, localcontext
from pathlib import Path
import pandas as pd
import volatility_phase3 as p3
import volatility_phase4 as p4

ROOT = Path(__file__).resolve().parents[2]
PLAN_SHA = '7339f3fa4db3b7d1ebd993f2464a505a3b60b4ed'
BASELINE_SHA = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PHASE2_SHA = '598ed582f84f6435cda5d78b4f433a9cccf144375c8aa169cbd2a69400fbdd2e'
PHASE2_ASSIGNMENTS_SHA = '077be95f9796b3cd00568992316447f7f02116618b8d6b5d9eabbb2c0da14126'
STRONG = frozenset((1,3,4,12,19,23,25,26))
BROAD = frozenset((1,2,3,4,5,6,7,8,12,19,20,21,23,25,26))
VARIANTS = ('R0_FIXED_090','R2_GLOBAL','S1_STRONG_ONLY_R2','S2_BROAD_R2')
METHODS = ('primary','robustness')
PERIODS = p3.PERIODS


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def membership():
    p=ROOT/'results/volatility_phase2/volatility_phase2_monotonicity_summary.csv'
    if sha(p)!=PHASE2_SHA:raise ValueError('Phase 2 membership source hash')
    d=pd.read_csv(p)
    d=d[(d.Period=='FULL')&(d.ScopeType=='Strategy')&(d.Aggregation=='trade_weighted')]
    if len(d)!=56:raise ValueError('Phase 2 membership rows')
    out=[]
    for sid,g in d.groupby('StrategyNo'):
        a=g.set_index('Method'); sid=int(sid)
        if set(a.index)!=set(METHODS):raise ValueError('Method rows')
        pri,rob=a.loc['primary'],a.loc['robustness']
        support=lambda r:r.Support=='ORDERED_POSITIVE_SUPPORTED'
        strong=support(pri) and support(rob)
        broad=(support(pri) or support(rob)) and pri.Support!='LOW_SAMPLE' and rob.Support!='LOW_SAMPLE' and pri.Q5MinusQ1AvgR>0 and rob.Q5MinusQ1AvgR>0
        if sid==22:strong=broad=False
        out.append(dict(StrategyNo=sid,Strategy=pri.Strategy,PrimarySupport=pri.Support,RobustnessSupport=rob.Support,PrimaryQ5MinusQ1=pri.Q5MinusQ1AvgR,RobustnessQ5MinusQ1=rob.Q5MinusQ1AvgR,STRONG=strong,BROAD=broad,Active=sid!=22))
    if {r['StrategyNo'] for r in out if r['STRONG']}!=STRONG or {r['StrategyNo'] for r in out if r['BROAD']}!=BROAD:
        raise ValueError('Frozen A5 membership mismatch')
    return out


def risk(variant, sid, q):
    if variant not in VARIANTS:raise ValueError('Unregistered variant')
    if variant=='R0_FIXED_090':return D('.90')
    eligible=(variant=='R2_GLOBAL' or variant=='S1_STRONG_ONLY_R2' and sid in STRONG or variant=='S2_BROAD_R2' and sid in BROAD)
    return p3.risk('R2_MODERATE' if eligible else 'R0_FIXED_090',q)


def uses_r2(variant,sid):
    return variant=='R2_GLOBAL' or variant=='S1_STRONG_ONLY_R2' and sid in STRONG or variant=='S2_BROAD_R2' and sid in BROAD


def r2_applied(variant, row, method):
    return uses_r2(variant,row['StrategyNo']) and row[method+'Quintile']!=p3.p1.INS


def simulate(rows, variant, method, scale=D(1)):
    p3.validate(rows)
    groups=defaultdict(list)
    for r in rows:
        pct=risk(variant,r['StrategyNo'],r[method+'Quintile'])*scale
        groups[p3.money.week_start(r['EntryTime'])].append((r,pct))
    balance=D(500000); logs=[]; weeks=[]
    for week,items in sorted(groups.items()):
        if balance<=0:raise ValueError('Insolvent weekly base')
        base=balance; total=D(0)
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
    metric=p3.money.metrics(logs,*p3.PERIODS['ALL'])
    vals=[risk(variant,r['StrategyNo'],r[method+'Quintile'])*scale for r in rows]
    metric.update(MeanNominalRiskPct=sum(vals,D(0))/len(vals),MedianNominalRiskPct=D(str(statistics.median(vals))),R2Trades=sum(r2_applied(variant,r,method) for r in rows),R2TradeSharePct=D(100)*sum(r2_applied(variant,r,method) for r in rows)/len(rows))
    return metric,logs,weeks


def write(out,name,rows):
    p3.money.write_csv(out/('strategy_selective_r2_'+name+'.csv'),rows)


def pct(values,p):
    x=sorted(values); i=(len(x)-1)*p; lo=int(i); hi=min(lo+1,len(x)-1)
    return x[lo]+(x[hi]-x[lo])*D(str(i-lo))


def decision(summary, matched, verified):
    table={(r['Method'],r['Variant'],r['Period']):r for r in summary}
    out=[]
    for v in VARIANTS[2:]:
        g=table['primary','R2_GLOBAL','ALL']; s=table['primary',v,'ALL'];r0=table['primary','R0_FIXED_090','ALL']
        diff={p:table['primary',v,p]['FinalCapital']-table['primary','R2_GLOBAL',p]['FinalCapital'] for p in PERIODS if p!='ALL'}
        gates=dict(A=s['FinalCapital']>g['FinalCapital'],B=sum(x>=0 for x in diff.values())>=3,C=diff['RecentB']>0 or diff['Monitor2026']>0,D=table['robustness',v,'ALL']['FinalCapital']>=table['robustness','R2_GLOBAL','ALL']['FinalCapital'],E=s['MaxDDPct']<=r0['MaxDDPct']*D('1.25') and s['WorstDayPct']>D(-20),F=sum(diff[p]>=0 for p in ('RecentA','RecentB','Monitor2026'))>=2)
        excess=s['MeanNominalRiskPct']>g['MeanNominalRiskPct']
        matched_pass=(matched.get(('primary',v),D(0))>=g['FinalCapital']) if excess else True
        if not verified:label='VALIDATION_INCOMPLETE'
        elif not gates['E']:label='SAFETY_FAIL'
        elif not gates['A']:label='GLOBAL_R2_REMAINS_PREFERRED'
        elif not (gates['B'] and gates['C'] and gates['F']):label='UNSTABLE_ACROSS_PERIODS'
        elif not gates['D']:label='ROBUSTNESS_FAIL'
        elif not matched_pass:label='PROFIT_GAIN_RISK_BUDGET_DRIVEN'
        else:label='SELECTIVE_R2_CANDIDATE'
        out.append(dict(Variant=v,PrimaryAllDelta=s['FinalCapital']-g['FinalCapital'],RobustnessAllDelta=table['robustness',v,'ALL']['FinalCapital']-table['robustness','R2_GLOBAL','ALL']['FinalCapital'],RecentBDelta=diff['RecentB'],Monitor2026Delta=diff['Monitor2026'],ResetNonnegativeCount=sum(x>=0 for x in diff.values()),RecentNonnegativeCount=sum(diff[p]>=0 for p in ('RecentA','RecentB','Monitor2026')),MeanRiskExceedsGlobal=excess,MatchedAllPass=matched_pass,**gates,Verdict=label))
    return out


def run(baseline,paths,output,implementation_sha,phase2_full=None):
    if len(implementation_sha)!=40:raise ValueError('Remote implementation SHA required')
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    if list(out.glob('strategy_selective_r2_*.csv')):raise ValueError('Fresh output directory required')
    if sha(baseline)!=BASELINE_SHA:raise ValueError('Baseline hash mismatch')
    members=membership(); p4.check_sources()
    if len(paths)!=56:raise ValueError('Expected 56 M1 paths')
    with localcontext() as ctx:
        ctx.prec=40
        a=p3.assignments(baseline,paths,phase2_full,out)
        if sha(out/'volatility_phase3_trade_assignments.csv')!=PHASE2_ASSIGNMENTS_SHA:raise ValueError('Phase 2 full assignment hash')
        allrows=p3.money.load_baseline(baseline)
        if len(allrows)!=16298 or a.TradeID.tolist()!=list(range(16298)):raise ValueError('Baseline identity/count')
        for r in allrows:
            for m in METHODS:r[m+'Quintile']=a.iloc[r['RowId']][m+'Quintile']
        rows=p4.scenario(allrows)
        if len(rows)!=15837 or len(allrows)-len(rows)!=461:raise ValueError('Primary trade universe')
        write(out,'membership',members)
        summary=[];riskrows=[];contrib=[];matched=[];audit=[];validation=[]
        for method in METHODS:
            allscale={}
            global_mean=sum((risk('R2_GLOBAL',r['StrategyNo'],r[method+'Quintile']) for r in rows),D(0))/len(rows)
            for v in VARIANTS[2:]:
                mean=sum((risk(v,r['StrategyNo'],r[method+'Quintile']) for r in rows),D(0))/len(rows)
                if mean>global_mean:allscale[v]=global_mean/mean
            for v in VARIANTS:
                for period,(start,end) in PERIODS.items():
                    own=[r for r in rows if start<=str(r['EntryTime'])[:10]<end]
                    metric,logs,weeks=simulate(own,v,method)
                    if v in VARIANTS[:2]:
                        check,oldlogs,_=p4.simulate(own,'R0_FIXED_090' if v=='R0_FIXED_090' else 'R2_MODERATE',method)
                        for k in ('FinalCapital','NetProfitJPY','MaxDDPct','WorstDayPct','WorstWeekPct'):
                            if metric[k]!=check[k]:raise ValueError('Phase 4 regression '+k)
                        if any(x['YenPnL']!=y['YenPnL'] for x,y in zip(logs,oldlogs)):raise ValueError('Phase 4 trade regression')
                    # Independent weekly product from assigned nominal risks, without simulator risk function.
                    wk=defaultdict(D)
                    for r in own:
                        rpct=D('.90') if v=='R0_FIXED_090' or not uses_r2(v,r['StrategyNo']) else p3.risk('R2_MODERATE',r[method+'Quintile'])
                        wk[p3.money.week_start(r['EntryTime'])]+=rpct/100*r['Pips']/r['SL']
                    wealth=D(500000)
                    for key in sorted(wk):wealth*=1+wk[key]
                    if abs(wealth-metric['FinalCapital'])>D('.000001'):raise ValueError('Independent Final Wealth mismatch')
                    summary.append(dict(Method=method,Variant=v,Period=period,**metric))
                    validation.append(dict(Check='Phase 4 regression and independent wealth',Method=method,Variant=v,Period=period,Status='PASS'))
                    if period=='ALL':
                        vals=[risk(v,r['StrategyNo'],r[method+'Quintile']) for r in own]
                        if sum(vals,D(0))/len(vals)!=metric['MeanNominalRiskPct']:raise ValueError('Mean risk mismatch')
                        cnt=Counter(str(x) for x in vals); qc=Counter(r[method+'Quintile'] for r in own)
                        riskrows.append(dict(Method=method,Variant=v,MeanRisk=metric['MeanNominalRiskPct'],MedianRisk=metric['MedianNominalRiskPct'],P5=pct(vals,D('.05')),P25=pct(vals,D('.25')),P75=pct(vals,D('.75')),P95=pct(vals,D('.95')),RiskCounts=json.dumps(cnt,sort_keys=True),QuintileCounts=json.dumps(qc,sort_keys=True),R2Trades=metric['R2Trades'],R2TradeSharePct=metric['R2TradeSharePct']))
                        for sid in sorted({r['StrategyNo'] for r in own}):
                            rr=[r for r in logs if r['StrategyNo']==sid];vv=[r['RiskPct'] for r in rr]
                            contrib.append(dict(Method=method,Variant=v,StrategyNo=sid,Strategy=rr[0]['Strategy'],Trades=len(rr),TotalYenPnL=sum((r['YenPnL'] for r in rr),D(0)),MeanRisk=sum(vv,D(0))/len(vv)))
                        seen=set()
                        for r in logs:
                            key=(r['StrategyNo'],r[method+'Quintile'])
                            if key not in seen or r['TradingWeekStart'] in {w['Week'] for w in weeks[:2]}:
                                audit.append(dict(Method=method,Variant=v,RowId=r['RowId'],Strategy=r['Strategy'],EntryTime=r['EntryTime'],Quintile=r[method+'Quintile'],RiskPct=r['RiskPct'],WeeklyBase=r['WeeklyBase'],YenPnL=r['YenPnL'],Status='PASS'));seen.add(key)
                if v in allscale:
                    scale=allscale[v]
                    for period,(start,end) in PERIODS.items():
                        own=[r for r in rows if start<=str(r['EntryTime'])[:10]<end]
                        mm,_,_=simulate(own,v,method,scale)
                        matched.append(dict(Method=method,Variant=v,Period=period,Scale=scale,MeanNominalRiskPct=mm['MeanNominalRiskPct'],FinalCapital=mm['FinalCapital'],NetProfitJPY=mm['NetProfitJPY']))
                    matched_mean=next(x['MeanNominalRiskPct'] for x in matched if x['Method']==method and x['Variant']==v and x['Period']=='ALL')
                    if abs(matched_mean-global_mean)>D('1e-30'):raise ValueError('Risk budget scale mismatch')
        matched_lookup={(r['Method'],r['Variant']):r['FinalCapital'] for r in matched if r['Period']=='ALL'}
        verdict=decision(summary,matched_lookup,True)
        write(out,'all_summary',[r for r in summary if r['Period']=='ALL' and r['Method']=='primary'])
        write(out,'reset_summary',[r for r in summary if r['Period']!='ALL' and r['Method']=='primary'])
        write(out,'robustness_summary',[r for r in summary if r['Method']=='robustness'])
        write(out,'risk_summary',riskrows);write(out,'strategy_contribution',contrib)
        write(out,'risk_budget_matched',matched);write(out,'manual_audit',audit)
        write(out,'validation',validation);write(out,'decision',verdict)
        hashes={p.name:sha(p) for p in sorted(out.glob('strategy_selective_r2_*.csv'))}
        write(out,'run_record',[dict(Status='COMPLETED',PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,BaselineSHA=sha(baseline),BaselineTrades=len(allrows),PrimaryTrades=len(rows),RemovedStrategy22Trades=461,Phase2MembershipSHA=PHASE2_SHA,SourceM1Files=len(paths),Validation='PASS',BaselineRecalculated=False,LiveChanged=False,FreshOOS=False,OutputHashes=json.dumps(hashes,sort_keys=True),Python=sys.version.split()[0],Pandas=pd.__version__)])
    return summary,verdict

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--input-paths',required=True);ap.add_argument('--output-dir',default='/content');ap.add_argument('--implementation-sha',required=True);ap.add_argument('--phase2-full')
    x=ap.parse_args();run(x.baseline,json.loads(Path(x.input_paths).read_text()),x.output_dir,x.implementation_sha,x.phase2_full)
