"""Observed-only selected trade metrics; no eligibility/Gate/status decisions."""
import numpy as np
from .u11_metrics import metric_block

def summarize(trades):
    ts=sorted(trades,key=lambda t:(t['CloseTime'],t['EntryTime'],tuple(t['FixedKey'])))
    if any(not '2026-01-01 00:00:00'<=t['EntryTime']<'2026-09-10 00:00:00' for t in ts):raise ValueError('Monitor entry assignment')
    combined=metric_block([t['Pips'] for t in ts])
    return dict(Combined=combined,Annual2026=dict(combined),Monthly={f'2026-{m:02d}':metric_block([t['Pips'] for t in ts if t['EntryTime'].startswith(f'2026-{m:02d}')]) for m in range(1,10)})

def diagnostics(trades,metrics,record):
    n=len(trades);wtl=[t for t in trades if t['WinnerToLoser']];g=[t['GivebackPips'] for t in trades]
    return dict(DiagnosticsOnly=True,RetentionGateAdded=False,WinRate=metrics['Combined']['Wins']/n if n else None,WinnerToLoserCount=len(wtl),WinnerToLoserFraction=len(wtl)/n if n else None,Giveback=dict(Total=float(np.sum(g)),Mean=float(np.mean(g)) if g else None,Median=float(np.median(g)) if g else None),TriggerReachedCount=sum(t['TriggerReached'] for t in trades),ProtectionActivatedCount=sum(t['ProtectionActivated'] for t in trades),ProtectionActivationCount=sum(t['ProtectionActivated'] for t in trades),ProtectionHitCount=sum(t['ProtectionHit'] for t in trades))
