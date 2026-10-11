"""Selected Validation-only metrics and frozen U11 sample/formal policy."""
import numpy as np


def metric_block(values):
    p=np.asarray(values,dtype=np.float64)
    if not np.isfinite(p).all():raise ValueError('nonfinite Pips')
    n=len(p);wins=int(np.count_nonzero(p>0));losses=int(np.count_nonzero(p<0))
    gain=float(np.sum(p[p>0]));loss=float(np.sum(p[p<0]));total=float(np.sum(p))
    state='FINITE' if loss<0 else ('INF' if gain>0 else 'UNDEFINED')
    curve=np.cumsum(p);dd=float(np.max(np.maximum.accumulate(np.r_[0.,curve])[1:]-curve)) if n else 0.
    return dict(Trades=n,Wins=wins,Losses=losses,ZeroPips=n-wins-losses,TotalPips=total,AvgPips=total/n if n else None,PFState=state,PFpips=gain/abs(loss) if loss<0 else None,MaxDDPips=dd)


def summarize(trades):
    ts=sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    if any(not '2024-01-01 00:00:00'<=t['EntryTime']<'2026-01-01 00:00:00' for t in ts):raise ValueError('Validation entry assignment')
    def block(prefix):return metric_block([t['Pips'] for t in ts if t['EntryTime'].startswith(prefix)])
    return dict(Combined=metric_block([t['Pips'] for t in ts]),Annual2024=block('2024'),Annual2025=block('2025'),Monthly={f'{y}-{m:02d}':block(f'{y}-{m:02d}') for y in (2024,2025) for m in range(1,13)})


def checks(metrics,record):
    m=metrics['Combined'];a=metrics['Annual2024'];b=metrics['Annual2025'];dd=record['SelectedModeDiscoveryMetrics']['MaxDDPips']*1.50
    sample=dict(Trades2024=a['Trades']>=30,Trades2025=b['Trades']>=30,CombinedTrades=m['Trades']>=70,Losses2024=a['Losses']>=5,Losses2025=b['Losses']>=5)
    if all(sample.values()) and (m['PFState']!='FINITE' or m['PFpips'] is None):raise ValueError('sufficient sample must have finite PF')
    formal=dict(TotalPips2024=a['TotalPips']>0,TotalPips2025=b['TotalPips']>0,AvgPips=m['AvgPips'] is not None and m['AvgPips']>0,PFpips=m['PFState']=='FINITE' and m['PFpips'] is not None and m['PFpips']>=1.10,MaxDDPips=m['MaxDDPips']<=dd)
    status='INSUFFICIENT_SAMPLE' if not all(sample.values()) else ('PASS' if all(formal.values()) else 'FAIL')
    return sample,formal,status,dd


def diagnostics(trades,metrics,record):
    v=metrics['Combined'];d=record['SelectedModeDiscoveryMetrics'];n=len(trades);wtl=[t for t in trades if t['WinnerToLoser']];g=[t['GivebackPips'] for t in wtl]
    def ratio(a,b):return a/b if a is not None and b is not None and b!=0 else None
    def delta(a,b):return a-b if a is not None and b is not None else None
    return dict(AvgPipsRetention=ratio(v['AvgPips'],d['AvgPips']),DiscoveryPFState=d['PFState'],DiscoveryPFpips=d['PFpips'],ValidationPFState=v['PFState'],ValidationPFpips=v['PFpips'],PFDelta=delta(v['PFpips'],d['PFpips']),PFRatio=ratio(v['PFpips'],d['PFpips']),DiscoveryTotalPips=d['TotalPips'],ValidationTotalPips=v['TotalPips'],TotalPipsDelta=v['TotalPips']-d['TotalPips'],TotalPipsRatio=ratio(v['TotalPips'],d['TotalPips']),DiscoveryMaxDD=d['MaxDDPips'],ValidationMaxDD=v['MaxDDPips'],MaxDDDelta=v['MaxDDPips']-d['MaxDDPips'],MaxDDRatio=ratio(v['MaxDDPips'],d['MaxDDPips']) if d['MaxDDPips']>0 else None,DDThreshold=d['MaxDDPips']*1.5,WinRate=v['Wins']/v['Trades'] if v['Trades'] else None,WinnerToLoserCount=len(wtl),WinnerToLoserFraction=len(wtl)/n if n else None,WinnerToLoserGiveback=dict(Total=float(np.sum(g)),Mean=float(np.mean(g)) if g else None,Median=float(np.median(g)) if g else None),TriggerReachedCount=sum(t['TriggerReached'] for t in trades),ProtectionActivatedCount=sum(t['ProtectionActivated'] for t in trades),ProtectionActivationCount=sum(t['ProtectionActivated'] for t in trades),ProtectionHitCount=sum(t['ProtectionHit'] for t in trades),DiagnosticsOnly=True,RetentionGateAdded=False)
