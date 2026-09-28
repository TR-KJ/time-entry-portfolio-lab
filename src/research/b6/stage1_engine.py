"""Fast Discovery-only SL engine. Range extrema find first raw-price hit exactly.

Tree queries are an acceleration of the inclusive minute walk, not a new fill
model. Neither rounding nor epsilon is used in trigger comparisons.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .execution import START,END,PIPS,SPREAD,validate,execute
from .stage1_metrics import metrics
MINUTE=60_000_000_000
MINUTES=int((END-START).total_seconds()/60)
STATUS=('OK','FILTERED_YEAR_END','PERIOD_BOUNDARY','MISSING_ENTRY','MISSING_EXIT','WEEKEND_BOUNDARY')

class ExtremeTree:
    def __init__(self,values,is_min):
        self.is_min=is_min;self.size=1<<(len(values)-1).bit_length()
        identity=np.inf if is_min else -np.inf
        self.tree=np.full(2*self.size,identity)
        self.tree[self.size:self.size+len(values)]=values
        op=np.minimum if is_min else np.maximum
        width=self.size//2
        while width:
            self.tree[width:2*width]=op(self.tree[2*width:4*width:2],self.tree[2*width+1:4*width:2]);width//=2
    def hit(self,value,threshold):return value<=threshold if self.is_min else value>=threshold
    def first(self,starts,ends,thresholds):
        starts=np.asarray(starts,dtype=np.int64);ends=np.asarray(ends,dtype=np.int64);thresholds=np.asarray(thresholds)
        if starts.shape!=ends.shape or starts.shape!=thresholds.shape:raise ValueError('query shape')
        if np.any(starts<0) or np.any(ends>=self.size) or np.any(ends<starts):raise ValueError('query bounds')
        l=starts+self.size;r=ends+self.size+1
        best=np.full(len(l),self.size,dtype=np.int64);nodes=np.zeros(len(l),dtype=np.int64);width=1
        while np.any(l<r):
            active=l<r
            for mask,ix in ((active&((l&1)==1),l),(active&((r&1)==1),r-1)):
                ids=np.flatnonzero(mask)
                q=ix[ids];left=(q-self.size//width)*width
                keep=self.hit(self.tree[q],thresholds[ids])&(left<best[ids])
                sel=ids[keep];nodes[sel]=q[keep];best[sel]=left[keep]
            l=(l+1)//2;r=r//2;width*=2
        while True:
            ids=np.flatnonzero((nodes>0)&(nodes<self.size))
            if not len(ids):break
            left=nodes[ids]*2
            nodes[ids]=left+(~self.hit(self.tree[left],thresholds[ids]))
        return np.where(nodes>0,nodes-self.size,-1)

@dataclass
class Batch:
    dates: pd.DatetimeIndex
    entries: np.ndarray
    scheduled: np.ndarray
    exits: np.ndarray
    close: np.ndarray
    status: np.ndarray
    pips: np.ndarray
    r: np.ndarray
    sl_hit: np.ndarray
    entry_price: np.ndarray
    close_price: np.ndarray
    missing: np.ndarray
    sls: tuple
    def summary(self,gate):
        return [metrics(self.r[i],self.status==0,self.dates.year,gate) for i in range(len(self.sls))]
    def records(self,sl_index):
        out=[]
        for a,b in np.ndindex(self.status.shape):
            code=int(self.status[a,b]);r={'Status':STATUS[code]}
            if code==0:
                ts=lambda x:str(START+pd.Timedelta(minutes=int(x)))
                hit=bool(self.sl_hit[sl_index,a,b]);close=int(self.close[sl_index,a,b])
                r.update(EntryTime=ts(self.entries[a]),ScheduledExitTime=ts(self.scheduled[a,b]),CloseTime=ts(close),
                         EntryPrice=float(self.entry_price[a]),ClosePrice=float(self.close_price[sl_index,a,b]),
                         SL=float(self.sls[sl_index]),TP=None,Pips=round(float(self.pips[sl_index,a,b]),6),R=round(float(self.r[sl_index,a,b]),9),
                         ExitReason='SL' if hit else 'TimeExit',ExitDelayMinutes=int(self.exits[a,b]-self.scheduled[a,b]),
                         missing_path_minutes=int(self.missing[a,b]),exit_bar_first_hit=hit and close==self.exits[a,b])
            out.append(r)
        return out

class FastEngine:
    def __init__(self,bars,symbol):
        validate(bars)
        if symbol not in PIPS:raise ValueError('unknown symbol')
        idx=(bars.index.as_unit('ns').asi8-START.value)//MINUTE
        if np.any((bars.index.as_unit('ns').asi8-START.value)%MINUTE):raise ValueError('M1 alignment')
        self.symbol=symbol;self.open=np.full(MINUTES,np.nan);self.open[idx]=bars.Open.to_numpy()
        low=np.full(MINUTES,np.inf);high=np.full(MINUTES,-np.inf)
        low[idx]=bars.Low.to_numpy();high[idx]=bars.High.to_numpy()
        self.low_tree=ExtremeTree(low,True);self.high_tree=ExtremeTree(high,False)
        self.present=np.isfinite(self.open)
        self.prefix=np.r_[0,np.cumsum(self.present)]
        # First existing bar at/after minute, sentinel at dataset boundary.
        self.next=np.minimum.accumulate(np.where(self.present,np.arange(MINUTES),MINUTES)[::-1])[::-1]
    def prepare(self,dates,entry_minute,long,sls):
        dates=pd.DatetimeIndex(dates)
        if dates.tz is not None or not dates.equals(dates.normalize()) or not dates.is_unique or not dates.is_monotonic_increasing:raise ValueError('unique sorted naive JST dates required')
        if len(dates) and (dates.min()<START or dates.max()>=END or (dates.weekday>=5).any()):raise ValueError('Discovery weekdays only')
        if not 0<=entry_minute<1440:raise ValueError('entry minute')
        if any(not np.isfinite(s) or s<=0 for s in sls):raise ValueError('SL')
        e=(dates.as_unit('ns').asi8-START.value)//MINUTE+entry_minute
        sign=1 if long else -1;pip=PIPS[self.symbol]
        price=self.open[e]+sign*SPREAD[self.symbol]*pip
        stops=price[None,:]-sign*np.asarray(sls)[:,None]*pip
        tree=self.low_tree if long else self.high_tree
        hit=tree.first(np.tile(e,len(sls)),np.tile(np.minimum(e+1444,MINUTES-1),len(sls)),stops.ravel()).reshape(len(sls),len(e))
        return Prepared(self,dates,e,price,stops,hit,tuple(sls),sign)

@dataclass
class Prepared:
    engine: FastEngine
    dates: pd.DatetimeIndex
    entries: np.ndarray
    price: np.ndarray
    stops: np.ndarray
    first_hit: np.ndarray
    sls: tuple
    sign: int
    def evaluate(self,holds):
        raw_holds=np.asarray(holds)
        holds=np.asarray(holds,dtype=np.int64)
        if not np.array_equal(raw_holds,holds):raise ValueError('whole-minute holds required')
        if len(holds)==0 or np.any(holds<30) or np.any(holds>1440):raise ValueError('holding bounds')
        eng=self.engine;e=self.entries;x=e[:,None]+holds[None,:]
        within=x<MINUTES;safe=np.minimum(x,MINUTES-1)
        chosen=eng.next[safe];found=within&(chosen<MINUTES)&(chosen<=x+4)
        filtered=np.asarray(((self.dates.month==12)&(self.dates.day>=25))|((self.dates.month==1)&(self.dates.day<=3)))
        status=np.zeros(x.shape,dtype=np.int8)
        status[~within]=2
        status[within&(~eng.present[e,None])]=3
        eligible=within&eng.present[e,None]
        status[eligible&~found]=4
        status[eligible&~found&(x+4>=MINUTES)]=2
        # <=24h prohibits Friday->Monday; preserve the reference weekend guard.
        weekday=(chosen//1440+2)%7 # 2020-01-01 Wednesday
        weekend=(weekday==6)|((weekday==0)&(chosen//1440!=e[:,None]//1440))
        status[eligible&found&weekend]=5
        status[filtered,:]=1
        valid=status==0
        hit=(self.first_hit[:,:,None]>=0)&(self.first_hit[:,:,None]<=chosen[None,:,:])&valid[None,:,:]
        close=np.where(hit,self.first_hit[:,:,None],chosen[None,:,:])
        closeprice=np.where(hit,self.stops[:,:,None],eng.open[np.minimum(chosen,MINUTES-1)][None,:,:])
        pips=self.sign*(closeprice-self.price[None,:,None])/PIPS[eng.symbol]
        pips=np.where(hit,-np.asarray(self.sls)[:,None,None],pips)
        r=pips/np.asarray(self.sls)[:,None,None]
        pips=np.where(valid[None,:,:],pips,np.nan);r=np.where(valid[None,:,:],r,np.nan)
        missing=(chosen-e[:,None]+1)-(eng.prefix[np.minimum(chosen+1,MINUTES)]-eng.prefix[e,None])
        return Batch(self.dates,e,x,chosen,close,status,pips,r,hit,self.price,closeprice,missing,self.sls)

def reference_batch(bars,symbol,dates,entry_minute,long,sls,holds):
    """Slow oracle built on unchanged Stage0 executor. Use only bounded fixtures."""
    dates=pd.DatetimeIndex(dates);records=[];rv=[];statuses=[]
    for sl in sls:
        sr=[];sv=[];ss=[]
        for date in dates:
            row=[];values=[];codes=[]
            filtered=(date.month==12 and date.day>=25)or(date.month==1 and date.day<=3)
            for h in holds:
                e=date+pd.Timedelta(minutes=entry_minute);x=e+pd.Timedelta(minutes=int(h))
                # Validate only the relevant day slice, but reject outside-period
                # arrays at entry, before any representative processing.
                validate(bars)
                r={'Status':'FILTERED_YEAR_END'} if filtered else execute(bars,symbol,long,e,x,sl)
                raw=np.nan
                if r['Status']=='OK':raw=-1.0 if r['ExitReason']=='SL' else ((1 if long else -1)*(r['ClosePrice']-r['EntryPrice'])/PIPS[symbol])/sl
                row.append(r);values.append(raw);codes.append(STATUS.index(r['Status']))
            sr.extend(row);sv.append(values);ss.append(codes)
        records.append(sr);rv.append(sv);statuses.append(ss)
    return records,np.asarray(rv),np.asarray(statuses[0],dtype=np.int8)
