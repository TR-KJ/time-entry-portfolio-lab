"""Read-only native MT5 export check. Python results are NOT MQL runtime evidence.
Usage: python tests/audit_phase5_oanda_exports.py --input-dir DIR --out DIR
Requires pandas/numpy for independent vectorized timezone/daily comparison.
"""
from pathlib import Path
import argparse,sys,hashlib,json,math
from datetime import datetime,timedelta
import pandas as pd
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import volatility_phase5_audit as audit

def offset(utc):
    ans=np.full(len(utc),2)
    for y in np.unique(utc.year):
        if y<2007:raise ValueError('unsupported year')
        march=pd.Timestamp(int(y),3,1);nov=pd.Timestamp(int(y),11,1)
        begin=march+pd.Timedelta(days=(6-march.weekday())%7+7,hours=7)
        end=nov+pd.Timedelta(days=(6-nov.weekday())%7,hours=6)
        ans[(utc>=begin)&(utc<end)]=3
    return ans

def run(input_dir,out):
    out.mkdir(parents=True,exist_ok=True);report=[]
    cutoff=pd.Timestamp('2026-09-16')
    for symbol in ['USDJPY','EURJPY','GBPJPY','AUDJPY','AUDUSD','EURAUD','GBPAUD']:
        path=input_dir/f'phase5_{symbol}_M1.csv'
        x=pd.read_csv(path,sep='\t');raw=pd.DatetimeIndex(pd.to_datetime(x['<DATE>']+' '+x['<TIME>'],format=audit.FORMAT))
        us=(raw-pd.Timedelta(hours=7)).tz_localize('America/New_York',ambiguous='raise',nonexistent='raise').tz_convert('Asia/Tokyo').tz_localize(None)
        u2=raw-pd.Timedelta(hours=2);u3=raw-pd.Timedelta(hours=3)
        valid2=offset(u2)==2;valid3=offset(u3)==3
        assert (valid2!=valid3).all()
        mirrored=pd.DatetimeIndex(np.where(valid2,u2.to_numpy(),u3.to_numpy()))+pd.Timedelta(hours=9)
        assert (mirrored==us).all() and not raw.has_duplicates and raw.is_monotonic_increasing
        mask=(us>=cutoff-pd.Timedelta(days=600))&(us<cutoff)
        mask &= us.normalize()!=us[mask][0].normalize()
        own=x.loc[mask].copy();jt=us[mask];rt=raw[mask]
        own.columns=own.columns.str.strip('<>')
        frame=pd.DataFrame(own[['OPEN','HIGH','LOW','CLOSE']].to_numpy(float),index=jt,columns=['Open','High','Low','Close'])
        d=frame.groupby(frame.index.normalize()).agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'),M1Count=('Close','size'))
        prev=d.Close.shift();d['TR']=pd.concat([d.High-d.Low,(d.High-prev).abs(),(d.Low-prev).abs()],axis=1).max(axis=1)
        d['ATR20']=d.TR.rolling(20,min_periods=20).mean()
        labels=jt.strftime(audit.FORMAT)
        def rows():
            for t,values in zip(labels,frame.to_numpy()):
                yield dict(JST=t,**dict(zip(['Open','High','Low','Close'],values)))
        f=audit.feature(rows(),cutoff.to_pydatetime())
        atr=d.ATR20.iloc[-1];ref=d.ATR20.iloc[-253:-1]
        rank=int(2*(ref<atr).sum()+(ref==atr).sum())
        assert math.isclose(f['atr'],atr,abs_tol=1e-12,rel_tol=0) and f['rank']==rank and f['days']==len(d)
        d.to_csv(out/f'{symbol}_expected_daily.csv',index_label='JST',float_format='%.17g')
        if symbol=='USDJPY':
            snap=frame.reset_index(drop=True);snap.insert(0,'JST',labels);snap.insert(0,'ServerTime',rt.strftime(audit.FORMAT))
            snap.to_csv(out/'oanda_us_v1_USDJPY_snapshot.csv',index=False,float_format='%.17g')
        result=dict(Symbol=symbol,InputSHA256=hashlib.sha256(path.read_bytes()).hexdigest(),InputRows=len(x),TimestampMirrorMatches=len(raw),SnapshotRows=len(frame),DailyRows=len(d),Feature=f,IndependentPandasRank=rank,Status='PYTHON_MATCH_MQL_PENDING')
        report.append(result);print(symbol,f['q'],f['rank'],len(frame),flush=True)
    (out/'oanda_export_validation.json').write_text(json.dumps(dict(Adapter='OANDA_US_DST_V1',CutoffJST=str(cutoff),MQLRealFeedParity='NOT_RUN',Results=report),default=str,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);v=p.parse_args();run(v.input_dir,v.out)
