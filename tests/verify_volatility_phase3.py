"""Independent vectorized float64 verifier; no production risk/week/money helpers."""
import numpy as np
import pandas as pd
MAP={'R0_FIXED_090':[.9]*5,'R1_MILD':[.7,.8,.9,1,1.1],'R2_MODERATE':[.5,.7,.9,1.1,1.3],'F1_Q1_OFF':[0,.9,.9,.9,.9]}
def verify(rows,candidate,method,metric,logs):
    t=pd.DataFrame(rows)
    for c in ['Pips','SL']:t[c]=t[c].astype(float)
    q=t[method+'Quintile'];t['risk']=q.map(dict(zip(['Q1','Q2','Q3','Q4','Q5'],MAP[candidate]))).fillna(.9)
    nominal=t.risk.mean();skip=int(t.risk.eq(0).sum());t=t[t.risk>0].copy()
    t['EntryTime']=pd.to_datetime(t.EntryTime);t['CloseTime']=pd.to_datetime(t.CloseTime)
    shifted=t.EntryTime-pd.Timedelta(hours=6)
    t['week']=shifted.dt.normalize()-pd.to_timedelta(shifted.dt.weekday,unit='D')+pd.Timedelta(hours=6)
    t['u']=t.risk/100*t.Pips/t.SL
    factors=1+t.groupby('week').u.sum().sort_index()
    bases=500000*factors.cumprod().shift(fill_value=1)
    t['base']=t.week.map(bases);t['pnl']=t.base*t.u
    t=t.sort_values(['CloseTime','EntryTime','StrategyNo','RowId'])
    t['capital']=500000+t.pnl.cumsum();t['peak']=np.maximum.accumulate(np.r_[500000,t.capital])[1:]
    t['dd']=t.peak-t.capital;t['ddpct']=t.dd/t.peak*100
    close_shift=t.CloseTime-pd.Timedelta(hours=6)
    t['closeweek']=close_shift.dt.normalize()-pd.to_timedelta(close_shift.dt.weekday,unit='D')+pd.Timedelta(hours=6)
    t['day']=t.CloseTime.dt.normalize();t['before']=t.capital-t.pnl
    day=t.groupby('day').agg(pnl=('pnl','sum'),base=('before','first'))
    week=t.groupby('closeweek').agg(pnl=('pnl','sum'),base=('before','first'))
    final=t.capital.iloc[-1] if len(t) else 500000;net=final-500000;dd=t.dd.max() if len(t) else 0
    expected=dict(Trades=len(t),SkippedTrades=skip,StartCapital=500000,FinalCapital=final,NetProfitJPY=net,ReturnPct=net/500000*100,MaxDDJPY=dd,MaxDDPct=t.ddpct.max() if len(t) else 0,WorstDayPct=(day.pnl/day.base*100).min() if len(t) else 0,WorstWeekPct=(week.pnl/week.base*100).min() if len(t) else 0,MoneyRoMD=net/dd if dd else None,MoneyPF=t.pnl.clip(lower=0).sum()/-t.pnl.clip(upper=0).sum() if (t.pnl<0).any() else None,MeanNominalRiskPct=nominal,MeanExecutedRiskPct=t.risk.mean() if len(t) else 0,MeanNominalRiskDeltaVsR0=nominal-.9)
    for key,value in expected.items():
        if value is None:assert metric[key] is None,key
        else:np.testing.assert_allclose(float(metric[key]),value,rtol=1e-10,atol=1e-6 if key in ['StartCapital','FinalCapital','NetProfitJPY','MaxDDJPY'] else 1e-10,err_msg=key)
    assert t.RowId.tolist()==[r['RowId'] for r in logs]
    for col,key in [('base','WeeklyBase'),('pnl','YenPnL'),('capital','Capital'),('dd','DrawdownJPY'),('ddpct','DrawdownPct')]:
        np.testing.assert_allclose(t[col],[float(r[key]) for r in logs],rtol=1e-10,atol=1e-6 if col!='ddpct' else 1e-10,err_msg=col)
