"""Price-only B6 calibration; exact function bodies, no search/PnL input."""
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import numpy as np

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
