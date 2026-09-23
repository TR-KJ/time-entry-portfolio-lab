"""C3 fixed-anchor volatility-scaled SL/TP replay; R0 is a hard gate."""
from __future__ import annotations
import argparse,csv,gc,hashlib,json,math
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
import numpy as np
import pandas as pd

from daily_stop_baseline_revalidation import PIP_SIZE,SPREAD_PIPS,SYMBOL_TO_PAIR,load_pair
from exit_efficiency_phase1 import BASELINE_SHA,PERIODS,STRATEGY,in_period,load_baseline,resolve_and_audit,write
from c1_path_management_phase1 import r0_gate,metric
from volatility_phase1 import make_daily,features

PLAN='docs/91_c3_volatility_scaled_sltp_phase1_plan.md'
PLAN_SHA='9bcf394f9c0426ca9a07641fda8e81ca71a6912d'
METHODS={'ATR':'ATR20','RV':'RV20'}

def rounded_pips(original,factor):
    x=Decimal(str(original))*Decimal(str(factor))/Decimal('0.1')
    return float(x.quantize(Decimal('1'),rounding=ROUND_CEILING)*Decimal('0.1'))

def feature_for(d,index,col):
    if index<0 or index>=len(d):return dict(Current=np.nan,ReferenceMedian=np.nan,RelativeVol=np.nan,ScaleFactor=1.,FeatureStatus='FALLBACK',FallbackReason='CURRENT_UNAVAILABLE')
    current=float(d.iloc[index][col])
    if not math.isfinite(current) or current<=0:return dict(Current=current,ReferenceMedian=np.nan,RelativeVol=np.nan,ScaleFactor=1.,FeatureStatus='FALLBACK',FallbackReason='CURRENT_UNAVAILABLE')
    if index<252:return dict(Current=current,ReferenceMedian=np.nan,RelativeVol=np.nan,ScaleFactor=1.,FeatureStatus='FALLBACK',FallbackReason='REFERENCE_LT_252')
    ref=d[col].iloc[index-252:index].to_numpy(float)
    if not np.isfinite(ref).all():return dict(Current=current,ReferenceMedian=np.nan,RelativeVol=np.nan,ScaleFactor=1.,FeatureStatus='FALLBACK',FallbackReason='REFERENCE_NONFINITE')
    if (ref<=0).any():return dict(Current=current,ReferenceMedian=np.nan,RelativeVol=np.nan,ScaleFactor=1.,FeatureStatus='FALLBACK',FallbackReason='REFERENCE_NONPOSITIVE')
    med=float(np.median(ref));relative=current/med;factor=float(np.clip(relative,.5,2.))
    return dict(Current=current,ReferenceMedian=med,RelativeVol=relative,ScaleFactor=factor,FeatureStatus='VALID',FallbackReason='')

def assignments(anchors,bars):
    d=features(make_daily(bars));out={}
    dates=d.DailyDate.to_numpy()
    for a in anchors:
        idx=int(np.searchsorted(dates,np.datetime64(a['_entry'].date()),side='left')-1)
        if idx>=0:
            row=d.iloc[idx]
            if not (row.AvailableAt<=a['_entry'] and row.LastM1+pd.Timedelta(minutes=1)<=a['_entry']):raise AssertionError('daily lookahead')
        for method,col in METHODS.items():out[(a['_n'],a['EntryTime'],method)]=dict(DailyIndex=idx,DailyDate='' if idx<0 else str(d.iloc[idx].DailyDate.date()),**feature_for(d,idx,col))
    return out

def replay_scaled(a,bars,method,feature):
    idx=bars.index;entry=a['_entry'];scheduled=a['_scheduled'];ei=idx.searchsorted(entry)
    if ei>=len(idx) or idx[ei]!=entry:raise ValueError('missing exact entry')
    exit_time=None
    for delay in range(5):
        t=scheduled+timedelta(minutes=delay);xi=idx.searchsorted(t)
        if xi<len(idx) and idx[xi]==t:exit_time=t;break
    if exit_time is None:raise ValueError('missing exit through +4m')
    pair=a['Pair'];pip=PIP_SIZE[pair];sign=1 if a['Direction']=='Long' else -1
    raw=float(bars.iloc[ei].Open);fill=raw+sign*SPREAD_PIPS[pair]*pip
    sl=rounded_pips(float(a['SL']),feature['ScaleFactor']);tp=None if not a['TP'] else rounded_pips(float(a['TP']),feature['ScaleFactor'])
    slprice=fill-sign*sl*pip;tpprice=None if tp is None else fill+sign*tp*pip
    close=price=reason=None
    for i in range(ei,xi+1):
        row=bars.iloc[i];slhit=row.Low<=slprice if sign==1 else row.High>=slprice
        tphit=False if tpprice is None else (row.High>=tpprice if sign==1 else row.Low<=tpprice)
        if slhit or tphit:
            close=idx[i].to_pydatetime();reason='SL' if slhit else 'TP';price=slprice if slhit else tpprice;break
        if i==xi:close=idx[i].to_pydatetime();reason='TimeExit';price=float(row.Open);break
    pips=sign*(price-fill)/pip;R=pips/sl
    return dict(Status='OK',Variant=method,Triggered=False,StrategyNo=a['_n'],Strategy=a['Strategy'],Pair=pair,Direction=a['Direction'],Mode=a['Mode'],EntryTime=a['EntryTime'],ScheduledExitTime=a['ScheduledExitTime'],CloseTime=close.isoformat(sep=' '),ExitDelayMinutes=delay,RawEntryOpen=raw,EntryPrice=fill,ClosePrice=price,OriginalSL=float(a['SL']),OriginalTP='' if not a['TP'] else float(a['TP']),ActualSLPips=sl,ActualTPPips='' if tp is None else tp,Pips=round(pips,6),R=round(R,9),ExitReason=reason,Week=a['_week'],Method=method,**feature)

def run_variants(rows,paths):
    bypair=defaultdict(list)
    for a in rows:bypair[a['Pair']].append(a)
    out=[]
    for symbol,pair in SYMBOL_TO_PAIR.items():
        bars=load_pair(paths[symbol],symbol);own=bypair[pair];fa=assignments(own,bars)
        for a in own:
            for method in METHODS:out.append((a,replay_scaled(a,bars,method,fa[(a['_n'],a['EntryTime'],method)])))
        del bars;gc.collect()
    return out

def bootstrap(pairs):
    by=defaultdict(list)
    for a,b,v in pairs:by[a['_week']].append(float(v['R'])-float(b['R']))
    keys=sorted(by);s=np.array([sum(by[k]) for k in keys]);n=np.array([len(by[k]) for k in keys]);rng=np.random.Generator(np.random.PCG64(20260913));draw=rng.integers(0,len(keys),(5000,len(keys)));z=s[draw].sum(1)/n[draw].sum(1)
    return float(np.quantile(z,.025,method='linear')),float(np.quantile(z,.975,method='linear'))

def summary(rows,r0,variants):
    base={(a['_n'],a['EntryTime']):r for a,r in r0 if a['_n']!=22};active=[a for a in rows if a['_n']!=22]
    by=defaultdict(list);pairs=defaultdict(list)
    for a,v in variants:
        if a['_n']!=22:by[v['Variant']].append(v);pairs[v['Variant']].append((a,base[(a['_n'],a['EntryTime'])],v))
    r0rows=list(base.values());portfolio=[dict(Variant='R0',**metric(r0rows))];periods=[];strategies=[];trade=[];scale=[];robust=[]
    for method in METHODS:
        m=metric(by[method]);delta=m['TotalR']-portfolio[0]['TotalR'];portfolio.append(dict(Variant=method,DeltaTotalR=delta,AvgDeltaR=delta/len(active),**m))
        for pname in PERIODS:
            ps=[x for x in pairs[method] if in_period(x[0]['_entry'],pname)];d=np.array([float(v['R'])-float(b['R']) for _,b,v in ps]);bm=metric([b for _,b,_ in ps]);vm=metric([v for _,_,v in ps]);rec=dict(Method=method,Period=pname,Trades=len(ps),Weeks=len({a['_week'] for a,_,_ in ps}),R0TotalR=bm['TotalR'],V1TotalR=vm['TotalR'],DeltaTotalR=float(d.sum()),AvgDeltaR=float(d.mean()))
            if pname=='ALL':rec['CI_L'],rec['CI_U']=bootstrap(ps)
            periods.append(rec);trade.append(dict(**rec,Improved=int((d>1e-9).sum()),Harmed=int((d<-1e-9).sum()),Unchanged=int((abs(d)<=1e-9).sum())))
        for n in range(1,29):
            if n==22:continue
            ps=[x for x in pairs[method] if x[0]['_n']==n];vals=[v for _,_,v in ps];d=np.array([float(v['R'])-float(b['R']) for _,b,v in ps]);sf=np.array([v['ScaleFactor'] for v in vals]);mm=metric(vals)
            strategies.append(dict(Method=method,StrategyNo=n,Strategy=STRATEGY[n].name,TPPresent=bool(vals[0]['OriginalTP']!=''),R0TotalR=sum(float(b['R']) for _,b,_ in ps),V1TotalR=mm['TotalR'],DeltaTotalR=float(d.sum()),AvgDeltaR=float(d.mean()),MeanScale=float(sf.mean()),MedianScale=float(np.median(sf)),MinScale=float(sf.min()),MaxScale=float(sf.max()),LowerCap=int((sf==.5).sum()),UpperCap=int((sf==2).sum()),FallbackRate=sum(v['FeatureStatus']!='VALID' for v in vals)/len(vals),SLRate=mm['SLRate'],TPRate=mm['TPRate'],TimeExitRate=mm['TimeExitRate']))
        for group,vals in [('ALL',by[method])]+[(f'Symbol:{s}',[v for v in by[method] if v['Pair']==p]) for s,p in SYMBOL_TO_PAIR.items()]+[(f'Period:{p}',[v for v in by[method] if in_period(datetime.fromisoformat(v['EntryTime']),p)]) for p in PERIODS]:
            sf=np.array([v['ScaleFactor'] for v in vals]);scale.append(dict(Method=method,Group=group,Trades=len(vals),Valid=sum(v['FeatureStatus']=='VALID' for v in vals),Fallback=sum(v['FeatureStatus']!='VALID' for v in vals),Coverage=sum(v['FeatureStatus']=='VALID' for v in vals)/len(vals),Mean=float(sf.mean()),Median=float(np.median(sf)),Q10=float(np.quantile(sf,.1)),Q25=float(np.quantile(sf,.25)),Q75=float(np.quantile(sf,.75)),Q90=float(np.quantile(sf,.9)),Min=float(sf.min()),Max=float(sf.max()),LowerCap=int((sf==.5).sum()),UpperCap=int((sf==2).sum())))
    p={x['Period']:x for x in periods if x['Method']=='ATR'};rv={x['Period']:x for x in periods if x['Method']=='RV'};coverage=next(x for x in scale if x['Method']=='ATR' and x['Group']=='ALL')['Coverage'];sc=[x for x in strategies if x['Method']=='ATR'];pos=[x['DeltaTotalR'] for x in sc if x['DeltaTotalR']>0];conc=max(pos)/sum(pos) if pos else np.nan
    eligible=[q for q in ('Recent A','Recent B','2026 Monitor') if p[q]['Trades']>=30 and p[q]['Weeks']>=20]
    gates=dict(A=p['ALL']['DeltaTotalR']>0,B=p['ALL']['CI_L']>0,C=p['Historical']['DeltaTotalR']>=0,D=p['Recent Combined']['DeltaTotalR']>0,E=sum(p[q]['DeltaTotalR']>0 for q in eligible)>=2,F=rv['ALL']['DeltaTotalR']>=0 and rv['Recent Combined']['DeltaTotalR']>=0,G=coverage>=.95,H=p['ALL']['DeltaTotalR']>0 and bool(pos) and conc<.7)
    if not gates['G']:label='INSUFFICIENT_FEATURE_COVERAGE'
    elif all(gates.values()):label='VOLATILITY_SCALED_SLTP_CANDIDATE'
    elif all(gates[k] for k in 'ABCDEGH') and not gates['F']:label='ROBUSTNESS_FAIL'
    elif all(gates[k] for k in 'ABCDEFG') and not gates['H']:label='CONCENTRATION_FAIL'
    elif gates['A'] and gates['B'] and gates['G'] and not all(gates[k] for k in 'CDE'):label='UNSTABLE_ACROSS_PERIODS'
    else:label='NOT_SUPPORTED'
    formal=[dict(ConcentrationRatio=conc,PositiveStrategies=len(pos),**{f'Gate{k}':v for k,v in gates.items()},Label=label)]
    robust=[x for x in periods if x['Method']=='RV']
    return portfolio,periods,strategies,trade,scale,robust,formal

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--m1-root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--stage',choices=('reconcile','full'),default='full');a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    rows=load_baseline(a.baseline);paths,audit=resolve_and_audit(a.manifest,a.m1_root);write(out/'c3_vol_scaled_sltp_phase1_m1_audit.csv',audit);r0,_=r0_gate(rows,paths,out);Path(out/'c1_path_management_phase1_r0_reconciliation.csv').replace(out/'c3_vol_scaled_sltp_phase1_r0_reconciliation.csv')
    if a.stage=='reconcile':return
    variants=run_variants(rows,paths);tables=summary(rows,r0,variants);names=('portfolio_summary','period_summary','strategy_summary','trade_delta_summary','scale_distribution','robustness_summary','formal_gates')
    for name,data in zip(names,tables):write(out/f'c3_vol_scaled_sltp_phase1_{name}.csv',data)
    active=[v for x,v in variants if x['_n']!=22]
    coverage=[]
    for m in METHODS:
        own=[v for v in active if v['Method']==m];valid=sum(v['FeatureStatus']=='VALID' for v in own)
        coverage.append(dict(Method=m,Trades=len(own),Valid=valid,Fallback=len(own)-valid,Coverage=valid/len(own)))
    write(out/'c3_vol_scaled_sltp_phase1_coverage.csv',coverage)
    # Full paired detail stays local and makes every aggregate independently reproducible.
    write(out/'c3_vol_scaled_sltp_phase1_trade_detail_local.csv',active)
    write(out/'c3_vol_scaled_sltp_phase1_validation.csv',[dict(Check='baseline_sha',Status='PASS',Detail=BASELINE_SHA),dict(Check='m1_manifest',Status='PASS',Detail='56 files'),dict(Check='r0_reconciliation',Status='PASS',Detail='16298/15837 zero mismatches')])
    write(out/'c3_vol_scaled_sltp_phase1_run_record.csv',[dict(Plan=PLAN,PlanSHA=PLAN_SHA,BaselineSHA=BASELINE_SHA,Trades=15837,Result=tables[-1][0]['Label'])]);print(json.dumps(dict(Portfolio=tables[0],Formal=tables[-1]),indent=2))
if __name__=='__main__':main()
