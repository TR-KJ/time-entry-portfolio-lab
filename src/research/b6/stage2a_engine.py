"""SL+TP extension using frozen Stage1 exit eligibility and independent first hits."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .execution import execute,validate,PIPS,START
from .stage1_engine import FastEngine,MINUTES,STATUS

@dataclass
class Replay:
    dates: pd.DatetimeIndex
    status: np.ndarray
    rows: list
    raw_r: np.ndarray
    def records(self,index):return self.rows[index]

def fast_replay(engine,candidate,dates,grid):
    dates=pd.DatetimeIndex(dates);long=candidate['Direction']=='L';sign=1 if long else -1
    if len(dates) and (dates.weekday!=candidate['Weekday']).any():raise ValueError('fixed Entry weekday')
    sls=tuple(dict.fromkeys(x['SL'] for x in grid));hold=candidate['HoldingMinutes']
    prepared=engine.prepare(dates,candidate['EntryMinute'],long,sls);base=prepared.evaluate([hold])
    allrows=[];raws=[];valid=base.status[:,0]==0
    for setting in grid:
        si=sls.index(setting['SL']);sl=setting['SL'];tp=setting['TP']
        rows=base.records(si);r=base.r[si,:,0].copy()
        if tp is not None:
            target=prepared.price+sign*tp*PIPS[engine.symbol]
            tree=engine.high_tree if long else engine.low_tree
            first_tp=tree.first(prepared.entries,np.minimum(prepared.entries+hold+4,MINUTES-1),target)
            slhit=base.sl_hit[si,:,0]
            # STRICTLY earlier TP only. Ties go to SL, on Entry and Exit bars too.
            tpwin=valid&(first_tp>=0)&(first_tp<=base.exits[:,0])&(~slhit|(first_tp<base.close[si,:,0]))
            for i in np.flatnonzero(tpwin):
                rows[i].update(CloseTime=str(START+pd.Timedelta(minutes=int(first_tp[i]))),ClosePrice=float(target[i]),Pips=round(float(tp),6),R=round(float(tp/sl),9),ExitReason='TP',exit_bar_first_hit=bool(first_tp[i]==base.exits[i,0]))
            r[tpwin]=tp/sl
        for i,row in enumerate(rows):
            if row['Status']=='OK':row.update(TP=tp,RawR=float(r[i]))
        allrows.append(rows);raws.append(r)
    return Replay(dates,base.status[:,0],allrows,np.asarray(raws))

def reference_replay(bars,symbol,candidate,dates,grid):
    validate(bars);dates=pd.DatetimeIndex(dates)
    if len(dates) and (dates.weekday!=candidate['Weekday']).any():raise ValueError('fixed Entry weekday')
    out=[];raws=[];statuses=[]
    for setting in grid:
        rows=[];rs=[];ss=[];sl=setting['SL'];tp=setting['TP']
        for d in dates:
            e=d+pd.Timedelta(minutes=candidate['EntryMinute']);x=e+pd.Timedelta(minutes=candidate['HoldingMinutes'])
            holiday=(d.month==12 and d.day>=25)or(d.month==1 and d.day<=3)
            row={'Status':'FILTERED_YEAR_END'} if holiday else execute(bars,symbol,candidate['Direction']=='L',e,x,sl,tp)
            raw=np.nan
            if row['Status']=='OK':
                if row['ExitReason']=='SL':raw=-1.
                elif row['ExitReason']=='TP':raw=tp/sl
                else:raw=((1 if candidate['Direction']=='L' else -1)*(row['ClosePrice']-row['EntryPrice'])/PIPS[symbol])/sl
                row['RawR']=float(raw)
            rows.append(row);rs.append(raw);ss.append(STATUS.index(row['Status']))
        out.append(rows);raws.append(rs);statuses.append(ss)
    return Replay(dates,np.asarray(statuses[0]),out,np.asarray(raws))
