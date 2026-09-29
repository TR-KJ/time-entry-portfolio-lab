"""Raw-R reporting for every coarse TP condition, without pruning or ranking."""
import numpy as np
from .stage1_metrics import metrics,YEARS
from .stage1_engine import STATUS
from .stage1_search import json_safe

def summarize(candidate,grid,replay,gate):
    valid=np.broadcast_to((replay.status==0)[:,None],replay.raw_r.T.shape)
    m=metrics(replay.raw_r.T,valid,replay.dates.year,gate)
    results=[];annual=[];diagnostics=[]
    for i,setting in enumerate(grid):
        key={**candidate,**setting};key['RatioAliases']='|'.join(key['RatioAliases'])
        r=replay.raw_r[i];ok=valid[:,i];n=int(m['N'][i])
        row={**key,**{k:m[k][i] for k in ('Wins','Losses','WinRate','TotalR','AvgR','PF','MaxDDR')}}
        row.update(Trades=n,ZeroR=m['ZeroTrades'][i],AvgWinR=float(r[ok&(r>0)].mean()) if m['Wins'][i] else np.nan,AvgLossR=float(r[ok&(r<0)].mean()) if m['Losses'][i] else np.nan)
        reasons=[]
        if n<gate['min_trades']:reasons.append('TOTAL_TRADES')
        if m['Losses'][i]<gate['min_losses']:reasons.append('LOSS_COUNT')
        if not np.isfinite(m['PF'][i]) or m['PF'][i]<gate['min_pf']:reasons.append('PF')
        positive=0
        for y in YEARS:
            ym=replay.dates.year==y;positive+=int(m[f'TotalR_{y}'][i]>0)
            if m[f'N_{y}'][i]<gate['min_annual_trades']:reasons.append(f'ANNUAL_TRADES_{y}')
            annual.append({**key,'Year':y,'Trades':m[f'N_{y}'][i],'Wins':int((ym&ok&(r>0)).sum()),'Losses':m[f'Losses_{y}'][i],**{k:m[f'{k}_{y}'][i] for k in ('TotalR','AvgR','PF','MaxDDR')}})
        if positive<gate['min_positive_years']:reasons.append('POSITIVE_YEARS')
        row.update(Pass=not reasons,FailReasons='|'.join(reasons),PositiveYears=positive)
        if row['Pass']!=bool(m['Pass'][i]):raise AssertionError('gate mismatch')
        trades=[x for x in replay.records(i) if x['Status']=='OK'];diag=dict(key)
        for reason in ('SL','TP','TimeExit'):
            # Frozen reference uses TimeExit for scheduled Open exit.
            count=sum(x['ExitReason']==reason for x in trades);label=reason
            diag[label+'Count']=count;diag[label+'Rate']=count/n if n else np.nan
        if diag['SLCount']+diag['TPCount']+diag['TimeExitCount']!=n:raise AssertionError('unknown ExitReason')
        diag.update(FallbackCount=sum(x['ExitDelayMinutes']>0 for x in trades),MissingPathTrades=sum(x['missing_path_minutes']>0 for x in trades),MissingPathMinutes=sum(x['missing_path_minutes'] for x in trades),ExitBarFirstHits=sum(x['exit_bar_first_hit'] for x in trades))
        diag.update({f'Opportunities_{name}':int((replay.status==j).sum()) for j,name in enumerate(STATUS)})
        results.append(row);diagnostics.append(diag)
    return json_safe(dict(results=results,yearly=annual,diagnostics=diagnostics))
