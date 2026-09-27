"""Explicit Stage 0 only: identity audit, isolated price calibration, representative replay."""
from __future__ import annotations
import argparse,hashlib,json,os,sys,importlib.util,ast
from collections import Counter,defaultdict
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
import pandas as pd
import numpy as np
from .execution import discovery_view,execute
ROOT=Path(__file__).resolve().parents[3]
EXPECTED_SHA='8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f'
BASELINE_SHA='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def reference():
    path=ROOT/'src/research/daily_stop_baseline_revalidation.py'
    if sha(path)!='08b9717a3a94a0066e7ef7ebfa0f4802cbc84ae0570c3b875d96729877f4e216':raise ValueError('reference changed')
    spec=importlib.util.spec_from_file_location('b6_frozen_reference',path)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

def resolve(root,ref):
    p=ROOT/'research_inputs/b6/expected_m1_manifest.csv'
    if sha(p)!=EXPECTED_SHA:raise ValueError('expected manifest changed')
    m=pd.read_csv(p)
    if len(m)!=56 or Counter(m.Symbol)!={s:8 for s in ref.MANIFEST_NAMES}:raise ValueError('manifest counts')
    for s,names in ref.MANIFEST_NAMES.items():
        if list(m[m.Symbol==s].Filename)!=names:raise ValueError('manifest order')
    hits=defaultdict(list);want=set(m.Filename)
    for base,dirs,files in os.walk(root):
        for name in files:
            if name in want or name=='daily_stop_baseline_trades.csv':hits[name].append(Path(base)/name)
    bad=[dict(Filename=n,Matches=len(hits[n])) for n in m.Filename if len(hits[n])!=1]
    if bad:raise ValueError('missing/ambiguous exact names: '+json.dumps(bad))
    return m,hits

def audit_pair(rows,hits,ref):
    audit=[];frames=[]
    for x in rows.itertuples():
        path=hits[x.Filename][0];h=sha(path);df=ref.read_mt5_file(path)
        first=str(df.RawDatetime.iloc[0]);last=str(df.RawDatetime.iloc[-1])
        invalid=int(((df.High<df[['Open','Low','Close']].max(axis=1))|(df.Low>df[['Open','High','Close']].min(axis=1))).sum())
        finite=bool(np.isfinite(df[['Open','High','Low','Close']].to_numpy()).all())
        ok=h==x.SHA256 and len(df)==x.Rows and first==x.FirstRaw and last==x.LastRaw and invalid==0 and finite
        audit.append(dict(Symbol=x.Symbol,Filename=x.Filename,SHA256=h,Rows=len(df),FirstRaw=first,LastRaw=last,RawDuplicates=int(df.RawDatetime.duplicated().sum()),InvalidOHLC=invalid,FiniteOHLC=finite,Status='PASS' if ok else 'FAIL'))
        frames.append(df)
    full=pd.concat(frames,ignore_index=True);del frames
    localized=full.RawDatetime.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward')
    full.index=pd.DatetimeIndex(localized.dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
    duplicates=int(full.index.duplicated().sum())
    info=dict(Symbol=rows.Symbol.iloc[0],JSTFirst=str(full.index.min()),JSTLast=str(full.index.max()),JSTDuplicates=duplicates,Rows=len(full))
    if duplicates or any(x['Status']!='PASS' for x in audit):return audit,info,None
    full=full.sort_index(); isolated=discovery_view(full)
    del full
    return audit,info,isolated

def round5(x):return int((Decimal(str(x))/Decimal(5)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))*5

def calibrate(bars,symbol):
    from .execution import validate,PIPS
    validate(bars); accepted=[];days=[];blocks={30:[],240:[]};pip=PIPS[symbol]
    for d in pd.date_range('2020-01-01','2023-12-31'):
        g=bars.loc[(bars.index>=d)&(bars.index<d+pd.Timedelta(days=1))]
        stop=(d.month==12 and d.day>=25) or (d.month==1 and d.day<=3)
        if d.weekday() not in (1,2,3,4):reason='NOT_TUE_FRI'
        elif stop:reason='YEAR_END'
        elif len(g)<1380:reason='LOW_COUNT'
        elif g.index[0]>d+pd.Timedelta(minutes=5) or g.index[-1]<d+pd.Timedelta(hours=23,minutes=55):reason='ENDPOINT'
        elif (g.index[1:]-g.index[:-1]).max()>pd.Timedelta(minutes=10):reason='GAP'
        else:reason='ACCEPT'
        days.append(dict(Symbol=symbol,Date=str(d.date()),Year=d.year,Rows=len(g),Status=reason))
        if reason!='ACCEPT':continue
        accepted.append((d.year,float((g.High.max()-g.Low.min())/pip)))
        for width in blocks:
            agg=g.resample(f'{width}min',origin='start_day').agg({'Open':'count','High':'max','Low':'min'})
            good=agg[agg.Open==width];blocks[width].extend(((good.High-good.Low)/pip).tolist())
    a=pd.DataFrame(accepted,columns=['year','range']);counts=a.groupby('year').size().to_dict() if len(a) else {}
    enough=len(a)>=600 and all(counts.get(y,0)>=100 for y in range(2020,2024))
    D=float(a['range'].median()) if len(a) else None;values=[];adjusted=False
    if enough:
        for m in (.15,.30,.50,.80,1.20):
            raw=round5(D*m);v=max(10,min(300,raw),values[-1]+5 if values else 10)
            adjusted|=v!=raw;values.append(v)
        if values[-1]>300:enough=False;values=[]
    summary=dict(Symbol=symbol,Status='PROPOSAL' if enough else 'PENDING_INSUFFICIENT_DATA',EligibleDays=len(a),AnnualDays=counts,
                 DailyMedianPips=D,DailyQ25=float(a['range'].quantile(.25)) if len(a) else None,DailyQ75=float(a['range'].quantile(.75)) if len(a) else None,
                 AnnualMedian=a.groupby('year')['range'].median().to_dict() if len(a) else {},
                 Range30mMedian=float(np.median(blocks[30])) if blocks[30] else None,Range4hMedian=float(np.median(blocks[240])) if blocks[240] else None,
                 Adjusted=adjusted,SL=values)
    return summary,days

def load_representatives(path):
    if path is None:return None
    if sha(path)!=BASELINE_SHA:raise ValueError('baseline hash mismatch')
    # Identity audit may parse metadata over all rows; performance fields outside Discovery are never selected/reported.
    rows=pd.read_csv(path)
    if len(rows)!=16298 or rows.StrategyNo.nunique()!=28:raise ValueError('baseline count')
    rows=rows[(rows.EntryTime>='2020-01-01')&(rows.EntryTime<'2024-01-01')&(rows.ScheduledExitTime<'2024-01-01')].copy()
    rows['overnight']=rows.EntryTime.str[:10]!=rows.ScheduledExitTime.str[:10]
    rows['fallback']=rows.ExitDelayMinutes>0
    rows['no_tp']=rows.TP.isna()
    # Earliest anchor in every existing coverage stratum. No ranking or profit preference.
    rows=rows.sort_values(['EntryTime','StrategyNo']).groupby(['Pair','Direction','ExitReason','overnight','fallback','no_tp'],dropna=False,sort=True).head(1)
    return rows

def compare_representatives(rows,bars,symbol,ref):
    if rows is None:return []
    out=[];pair=ref.SYMBOL_TO_PAIR[symbol]
    for r in rows[rows.Pair==pair].itertuples():
        e=pd.Timestamp(r.EntryTime);x=pd.Timestamp(r.ScheduledExitTime);long=r.Direction=='Long';tp=None if pd.isna(r.TP) else float(r.TP)
        # Existing run_strategy on only this representative day/window; use a no-event fixture Strategy.
        # no=999 avoids historical per-strategy exceptions; empty policy/calendar avoids selection changes.
        s=ref.Strategy(999,'B6_COMPAT_ANCHOR',pair,long,(e.weekday(),),(e.hour,e.minute),(x.hour,x.minute),(x.date()-e.date()).days,float(r.SL),tp)
        ref.EVENT_POLICY[999]={k:'-' for k in ref.EVENTS}
        subset=bars.loc[e:x+pd.Timedelta(minutes=4)].copy()
        existing=ref.run_strategy(s,subset,{k:set() for k in ref.EVENTS},[])
        b6=execute(bars.loc[e.normalize():x.normalize()+pd.Timedelta(days=1)-pd.Timedelta(minutes=1)],symbol,long,e,x,float(r.SL),tp)
        errors=[]
        if len(existing)!=1 or b6['Status']!='OK':errors=['REFERENCE_OR_B6_MISSING']
        else:
            old=existing[0]
            for k in ('EntryTime','ScheduledExitTime','CloseTime','ExitReason','ExitDelayMinutes'):
                if str(old[k])!=str(b6[k]) or str(getattr(r,k))!=str(b6[k]):errors.append(k)
            for k,tol in [('RawEntryOpen',1e-9),('EntryPrice',1e-9),('ClosePrice',1e-9),('Pips',1e-6),('R',1e-8)]:
                if abs(old[k]-b6[k])>tol or abs(float(getattr(r,k))-b6[k])>tol:errors.append(k)
        out.append(dict(Symbol=symbol,StrategyNo=r.StrategyNo,EntryTime=r.EntryTime,Direction=r.Direction,ExitReason=r.ExitReason,Overnight=r.overnight,Fallback=r.fallback,NoTP=r.no_tp,Status='FAIL' if errors else 'PASS',Mismatch='|'.join(errors)))
    return out

def run(root,out,baseline=None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);ref=reference();m,hits=resolve(root,ref)
    if baseline is None and len(hits['daily_stop_baseline_trades.csv'])==1:baseline=hits['daily_stop_baseline_trades.csv'][0]
    reps=load_representatives(baseline)
    audit=[];coverage=[];stats=[];days=[];comparisons=[]
    for symbol in ref.MANIFEST_NAMES:
        a,c,bars=audit_pair(m[m.Symbol==symbol],hits,ref);audit+=a;coverage.append(c)
        pd.DataFrame(audit).to_csv(out/'input_audit.csv',index=False)
        if bars is None:raise ValueError('input audit failed; see input_audit.csv')
        s,d=calibrate(bars,symbol);stats.append(s);days+=d
        comparisons+=compare_representatives(reps,bars,symbol,ref)
        print(symbol,'audited; Discovery days',s['EligibleDays'],'SL proposal',s['SL'],flush=True)
        del bars
    pd.DataFrame(coverage).to_csv(out/'coverage.csv',index=False)
    pd.DataFrame(days).to_csv(out/'calibration_day_diagnostics.csv',index=False)
    (out/'price_statistics.json').write_text(json.dumps(stats,indent=2)+'\n')
    pd.DataFrame([dict(Symbol=s['Symbol'],Status=s['Status'],**{f'SL{i+1}':s['SL'][i] if len(s['SL'])==5 else None for i in range(5)}) for s in stats]).to_csv(out/'sl_grid_proposal.csv',index=False)
    if comparisons:pd.DataFrame(comparisons).to_csv(out/'representative_reconciliation.csv',index=False)
    report=dict(InputAudit='PASS',RepresentativeReplay='NOT_RUN_BASELINE_UNAVAILABLE' if reps is None else ('FAIL' if any(x['Status']=='FAIL' for x in comparisons) else 'PASS'),RepresentativeCount=len(comparisons),BaselineSHA256=sha(baseline) if baseline else None,Stage1='NOT_RUN',Validation='NOT_RUN',Monitor='NOT_RUN',CalibrationPrespecSHA256=sha(ROOT/'docs/b6/sl_calibration_prespec.md'))
    (out/'run_status.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('/content/b6_stage0'));p.add_argument('--baseline',type=Path)
    a=p.parse_args();run(a.data_root,a.out,a.baseline)
