"""Independent slow scalar executor for bounded reference replay; no B6 selections."""
import pandas as pd
import numpy as np
START=pd.Timestamp('2024-01-01'); END=pd.Timestamp('2026-01-01')

def validate(bars):
    if not isinstance(bars.index,pd.DatetimeIndex) or bars.index.tz is not None or bars.empty:raise ValueError('naive nonempty Validation bars')
    if not bars.index.is_unique or not bars.index.is_monotonic_increasing or bars.index[0]<START or bars.index[-1]>=END:raise ValueError('Validation index/bounds')
    for row in bars[['Open','High','Low','Close']].itertuples(index=False):
        o,h,l,c=map(float,row)
        if not all(np.isfinite(v) for v in (o,h,l,c)) or h<max(o,l,c) or l>min(o,h,c):raise ValueError('OHLC')
from .stage1_contract import SPREAD, PIPS

def execute(bars, symbol, direction, entry, scheduled, sl=None, fixed_key=(), tp=None):
    validate(bars)
    e, x = pd.Timestamp(entry), pd.Timestamp(scheduled)
    if e.tzinfo is not None or x.tzinfo is not None: raise ValueError('naive JST')
    if sl is not None and (not np.isfinite(sl) or sl <= 0): raise ValueError('SL')
    if tp is not None and (not np.isfinite(tp) or tp <= 0): raise ValueError('TP')
    if direction not in ('LONG', 'SHORT'): raise ValueError('direction')
    def skip(s): return {'Status': s}
    if not START <= e < END or not START <= x < END: return skip('PERIOD_BOUNDARY')
    h = (x-e).total_seconds()/60
    if h != int(h) or not 30 <= h <= 1440: return skip('INVALID_HOLD')
    if e.weekday() >= 5: return skip('INVALID_ENTRY_WEEKDAY')
    if (e.month == 12 and e.day >= 25) or (e.month == 1 and e.day <= 3): return skip('YEAR_END_STOP')
    if e not in bars.index: return skip('MISSING_ENTRY')
    chosen = None
    for delay in range(5):
        t = x + pd.Timedelta(minutes=delay)
        if t >= END: return skip('PERIOD_BOUNDARY')
        if t in bars.index: chosen = t; break
    if chosen is None: return skip('MISSING_EXIT')
    if chosen.weekday() == 6 or (chosen.weekday() == 0 and chosen.date() != e.date()): return skip('WEEKEND_BOUNDARY')
    sign = 1 if direction == 'LONG' else -1
    raw = float(bars.at[e, 'Open']); price = raw + sign*SPREAD[symbol]*PIPS[symbol]
    stop = None if sl is None else price-sign*sl*PIPS[symbol]
    target = None if tp is None else price+sign*tp*PIPS[symbol]
    close, fill, reason = chosen, float(bars.at[chosen, 'Open']), 'TimeExit'
    window = bars.loc[e:chosen]
    for t, row in window.iterrows():
        if stop is not None and (row.Low <= stop if sign == 1 else row.High >= stop):
            close, fill, reason = t, stop, 'SL'; break
        if target is not None and (row.High >= target if sign == 1 else row.Low <= target):
            close, fill, reason = t, target, 'TP'; break
    pips = -float(sl) if reason == 'SL' else (float(tp) if reason == 'TP' else sign*(fill-price)/PIPS[symbol])
    return dict(Status='OK', EntryTime=str(e), ScheduledExitTime=str(x), CloseTime=str(close),
                RawEntryOpen=raw, EntryPrice=price, ClosePrice=fill, Pips=pips, ExitReason=reason,
                SL=sl, TP=tp, ExitDelayMinutes=int((chosen-x).total_seconds()/60),
                MissingPathMinutes=int((chosen-e).total_seconds()/60)+1-len(window), FixedKey=list(fixed_key))

from copy import deepcopy
from datetime import datetime,timedelta
from .stage1_contract import object_hash
from .u11_input import FREEZE_SHA

def event_names(symbol):
    bank={'USD':'FOMC','EUR':'ECB','JPY':'BOJ','GBP':'BOE','AUD':'RBA'}
    out={bank[symbol[:3]],bank[symbol[3:]],'US_NFP','US_CPI'}
    if 'AUD' in (symbol[:3],symbol[3:]):out.add('AUD_CPI')
    return sorted(out)

def event_windows(calendar):
    out=[]
    for e in calendar['Events']:
        for day in e['SourceDates']:
            center=datetime.strptime(day+' '+e['FixedJST'],'%Y-%m-%d %H:%M')
            if e['CanonicalEventName']=='FOMC':center+=timedelta(days=1)
            width=timedelta(minutes=e['WindowPlusMinusMinutes'])
            out.append((e['CanonicalEventName'],center-width,center+width))
    return out

def calendar_days(r,days=None):
    ds=list(pd.date_range('2024-01-01','2025-12-31')) if days is None else list(pd.DatetimeIndex(days))
    if len(set(ds))!=len(ds) or any(d.tzinfo is not None or d!=d.normalize() or not START<=d<END for d in ds):raise ValueError('Validation dates')
    if r['FormalEntryMinute']+r['FormalHoldingMinutes']!=1440*r['FormalExitDayOffset']+r['FormalExitMinute']:raise ValueError('schedule')
    out=[]
    for d in sorted(ds):
        bucket='D1' if d.day<11 else ('D2' if d.day<21 else 'D3')
        if d.weekday() in r['FormalWeekdays'] and bucket in r['FormalDOMBuckets'] and d.month in r['FormalMonths']:out.append(d)
    return out

def executable(bars,r,days=None):
    ts=[];skips={}
    for day in calendar_days(r,days):
        e=day+timedelta(minutes=r['FormalEntryMinute']);x=day+timedelta(days=r['FormalExitDayOffset'],minutes=r['FormalExitMinute'])
        key=[r['Symbol'],int(r['Direction']=='SHORT'),day.weekday(),r['FormalEntryMinute'],r['FormalExitDayOffset'],r['FormalExitMinute'],r['FormalHoldingMinutes'],r['CandidateID']]
        t=execute(bars,r['Symbol'],r['Direction'],e,x,r['FormalSL'],key,r['FormalTP'])
        if t['Status']!='OK':skips[t['Status']]=skips.get(t['Status'],0)+1;continue
        t['CandidateID']=r['CandidateID'];t['PlannedEntryTimeJST']=str(e);t['PlannedTimeExitJST']=str(x);t['TradeID']=object_hash([r['CandidateID'],str(e),str(x)]);ts.append(t)
    ts.sort(key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    return ts,skips

def filter_e2(ts,r,calendar):
    names=r['E2EventSet']
    if r['FormalEventMode']!='E2' or names!=event_names(r['Symbol']):raise ValueError('saved E2 set')
    ws=event_windows(calendar);kept=[];removed=[];overlaps={};counts={n:0 for n in names};multi=0
    if len(set(t['TradeID'] for t in ts))!=len(ts):raise ValueError('duplicate trade ID')
    for t in ts:
        e=datetime.fromisoformat(t['PlannedEntryTimeJST']);x=datetime.fromisoformat(t['PlannedTimeExitJST']);found=set()
        for name,lo,hi in ws:
            if name in names and e<=hi and x>=lo:found.add(name)
        found=sorted(found);overlaps[t['TradeID']]=found
        if len(found)==0:kept.append(t)
        else:
            removed.append(t['TradeID'])
            if len(found)>1:multi+=1
            for name in found:counts[name]+=1
    d=dict(E0ExecutableTrades=len(ts),E2Trades=len(kept),RemovedTrades=len(removed),Retention=len(kept)/len(ts) if ts else None,RemovedByEvent=counts,MultiEventOverlapTradeCount=multi,RemovedTradeIDsSHA256=object_hash(removed))
    return kept,d,dict(RemovedTradeIDs=removed,OverlappingEvents=overlaps)

def simulate(bars,r,t,mode):
    if mode not in ['P0','P1','P2','P3']:raise ValueError('fixed mode')
    if len(bars) and (bars.index[0]<START or bars.index[-1]>=END):raise ValueError('Validation only')
    trigger_r={'P0':None,'P1':.5,'P2':.75,'P3':1.}[mode];lock_r={'P0':None,'P1':0.,'P2':.25,'P3':.5}[mode]
    sl=r['FormalSL'];tp=r['FormalTP'];pip=PIPS[r['Symbol']];price=t['EntryPrice'];long=r['Direction']=='LONG';sign=1 if long else -1
    app=mode=='P0' or tp is None or tp>trigger_r*sl
    if not app:raise ValueError('frozen selected Protection structural conflict')
    path=bars.loc[t['EntryTime']:t['CloseTime']]
    if path.empty or str(path.index[0])!=t['EntryTime'] or str(path.index[-1])!=t['CloseTime']:raise ValueError('exact path')
    out=deepcopy(t);trigger=None;activation=None;stop=None;hit=False;hi=None;lo=None
    for when,row in path.iterrows():
        hi=float(row.High) if hi is None else max(hi,float(row.High));lo=float(row.Low) if lo is None else min(lo,float(row.Low))
        if trigger is not None and activation is None:activation=str(when)
        if activation is not None and (row.Low<=stop if long else row.High>=stop):
            out.update(CloseTime=str(when),ClosePrice=stop,Pips=float(lock_r*sl),ExitReason='ProtectionSL');hit=True;break
        if mode!='P0' and app and trigger is None:
            target=price+sign*trigger_r*sl*pip
            if row.High>=target if long else row.Low<=target:
                trigger=str(when);stop=price+sign*lock_r*sl*pip
        # Baseline first-hit close handles original SL/TP, including SL-first ties.
        if str(when)==t['CloseTime']:break
    mfe=max(0.,(hi-price)/pip if long else (price-lo)/pip);mae=max(0.,(price-lo)/pip if long else (hi-price)/pip)
    out.update(Mode=mode,Direction=r['Direction'],FormalSL=sl,FormalTP=tp,PlannedTimeExit=t['PlannedTimeExitJST'],ActualCloseTime=out['CloseTime'],FinalPips=out['Pips'],MFEpips=mfe,MAEpips=mae,GivebackPips=mfe-out['Pips'],WinnerToLoser=mfe>=.5*sl and out['Pips']<0,Applicable=app,NotApplicableReason=None if app else 'NOT_APPLICABLE_TP_AT_OR_BEFORE_TRIGGER',TriggerR=trigger_r,LockR=lock_r,TriggerReached=trigger is not None,TriggerBar=trigger,ActivationBar=activation,ProtectionActivated=activation is not None,ProtectionStop=stop,ProtectionHit=hit)
    for suffix,reach in [('025',.25),('050',.5),('075',.75),('100',1.)]:out['Reach'+suffix+'R']=mfe>=reach*sl
    return out

def metric_block(values):
    values=[float(v) for v in values]
    if not all(np.isfinite(x) for x in values):raise ValueError('nonfinite')
    positive=[x for x in values if x>0];negative=[x for x in values if x<0]
    total=float(np.sum(values));gain=float(np.sum(positive));loss=float(np.sum(negative));n=len(values)
    cumulative=0.;peak=0.;dd=0.
    for v in values:
        cumulative+=v;peak=max(peak,cumulative);dd=max(dd,peak-cumulative)
    state='FINITE' if loss<0 else ('INF' if gain>0 else 'UNDEFINED')
    return dict(Trades=n,Wins=len(positive),Losses=len(negative),ZeroPips=n-len(positive)-len(negative),TotalPips=total,AvgPips=total/n if n else None,PFState=state,PFpips=gain/abs(loss) if loss<0 else None,MaxDDPips=dd)

def summarize(trades):
    ordered=sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    groups={str(y):[] for y in (2024,2025)};months={f'{y}-{m:02d}':[] for y in (2024,2025) for m in range(1,13)}
    for t in ordered:
        y=t['EntryTime'][:4];month=t['EntryTime'][:7]
        if y not in groups or month not in months:raise ValueError('Validation assignment')
        groups[y].append(t['Pips']);months[month].append(t['Pips'])
    return dict(Combined=metric_block([t['Pips'] for t in ordered]),Annual2024=metric_block(groups['2024']),Annual2025=metric_block(groups['2025']),Monthly={k:metric_block(v) for k,v in months.items()})

def checks(metrics,record):
    sample={}
    for year in (2024,2025):sample['Trades'+str(year)]=metrics['Annual'+str(year)]['Trades']>=30
    sample['CombinedTrades']=metrics['Combined']['Trades']>=70
    for year in (2024,2025):sample['Losses'+str(year)]=metrics['Annual'+str(year)]['Losses']>=5
    m=metrics['Combined'];limit=1.50*record['SelectedModeDiscoveryMetrics']['MaxDDPips']
    if all(sample.values()) and (m['PFState']!='FINITE' or m['PFpips'] is None):raise ValueError('sufficient sample PF invariant')
    formal={}
    for y in (2024,2025):formal['TotalPips'+str(y)]=metrics['Annual'+str(y)]['TotalPips']>0
    formal['AvgPips']=m['AvgPips'] is not None and m['AvgPips']>0
    formal['PFpips']=m['PFState']=='FINITE' and m['PFpips'] is not None and m['PFpips']>=1.10
    formal['MaxDDPips']=m['MaxDDPips']<=limit
    status='PASS'
    if not all(sample.values()):status='INSUFFICIENT_SAMPLE'
    elif not all(formal.values()):status='FAIL'
    return sample,formal,status,limit

def diagnostics(trades,metrics,record):
    v=metrics['Combined'];d=record['SelectedModeDiscoveryMetrics'];n=len(trades);wtl=[t for t in trades if t['WinnerToLoser']];g=[t['GivebackPips'] for t in wtl]
    def ratio(a,b):return a/b if a is not None and b is not None and b!=0 else None
    def delta(a,b):return a-b if a is not None and b is not None else None
    return dict(AvgPipsRetention=ratio(v['AvgPips'],d['AvgPips']),DiscoveryPFState=d['PFState'],DiscoveryPFpips=d['PFpips'],ValidationPFState=v['PFState'],ValidationPFpips=v['PFpips'],PFDelta=delta(v['PFpips'],d['PFpips']),PFRatio=ratio(v['PFpips'],d['PFpips']),DiscoveryTotalPips=d['TotalPips'],ValidationTotalPips=v['TotalPips'],TotalPipsDelta=v['TotalPips']-d['TotalPips'],TotalPipsRatio=ratio(v['TotalPips'],d['TotalPips']),DiscoveryMaxDD=d['MaxDDPips'],ValidationMaxDD=v['MaxDDPips'],MaxDDDelta=v['MaxDDPips']-d['MaxDDPips'],MaxDDRatio=ratio(v['MaxDDPips'],d['MaxDDPips']) if d['MaxDDPips']>0 else None,DDThreshold=d['MaxDDPips']*1.5,WinRate=v['Wins']/v['Trades'] if v['Trades'] else None,WinnerToLoserCount=len(wtl),WinnerToLoserFraction=len(wtl)/n if n else None,WinnerToLoserGiveback=dict(Total=float(np.sum(g)),Mean=float(np.mean(g)) if g else None,Median=float(np.median(g)) if g else None),TriggerReachedCount=sum(t['TriggerReached'] for t in trades),ProtectionActivatedCount=sum(t['ProtectionActivated'] for t in trades),ProtectionActivationCount=sum(t['ProtectionActivated'] for t in trades),ProtectionHitCount=sum(t['ProtectionHit'] for t in trades),DiagnosticsOnly=True,RetentionGateAdded=False)

def evaluate_candidate(bars,r,calendar=None,days=None,implementation_sha='SYNTHETIC',approval=None):
    if r['CandidateID'].startswith('B7S1:'):
        import os
        from pathlib import Path
        if approval!='CHAT_APPROVED_COLAB_B7_U11_ONLY' or not os.environ.get('COLAB_RELEASE_TAG') or not Path('/content').is_dir():raise PermissionError('formal Candidate evaluation is Colab-approved only')
    mode=r['FormalProtectionMode']
    triggers={'P0':None,'P1':.5,'P2':.75,'P3':1.}
    if mode not in triggers or mode!='P0' and r['FormalTP'] is not None and r['FormalTP']<=triggers[mode]*r['FormalSL']:raise ValueError('frozen selected mode structurally inapplicable')
    if calendar is None:raise ValueError('explicit immutable calendar for reference')
    e0,skips=executable(bars,r,days);e2,events,detail=filter_e2(e0,r,calendar)
    selected=[simulate(bars,r,t,mode) for t in e2]
    for t in selected:t['FormalProtectionMode']=mode
    selected.sort(key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    if {t['TradeID'] for t in selected}!={t['TradeID'] for t in e2}:raise ValueError('fixed E2 trade universe')
    m=summarize(selected);sample,formal,status,limit=checks(m,r)
    out=dict(deepcopy(r),CandidateFreezeSHA=FREEZE_SHA,U11ImplementationSHA=implementation_sha,ValidationPeriod='[2024-01-01, 2026-01-01) JST',EventMode='E2',ValidationMetrics=m,SampleChecks=sample,SampleSufficient=all(sample.values()),FormalChecks=formal,FormalConditionsPASS=all(formal.values()),ValidationStatus=status,Status=status,DiscoveryBaseline=deepcopy(r['SelectedModeDiscoveryMetrics']),DDThreshold=limit,Diagnostics=diagnostics(selected,m,r),EventDiagnostics=events,ExecutionSkipped=skips,ValidationE2BaselineTradeStreamSHA256=object_hash(e2),E2TradeIDsSHA256=object_hash([t['TradeID'] for t in e2]),ValidationSelectedTradeStreamSHA256=object_hash(selected),ValidationTradeIDsSHA256=object_hash([t['TradeID'] for t in selected]),TradeResults=selected,NoReplacement=True,PostValidationRetuningAllowed=False,RescuePASSAllowed=False)
    audit=dict(CandidateDays=[str(d) for d in calendar_days(r,days)],E0Executable=e0,E2Survivors=e2,Filtering=detail)
    return out,audit
