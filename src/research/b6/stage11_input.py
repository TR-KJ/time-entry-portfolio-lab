"""Exact input/coverage audit separated from authorized feature generation."""
from pathlib import Path
from datetime import datetime
from collections import Counter
from .stage11_config import ROOT,INPUT,CONFIGS,AJ,GJ,MANIFEST_SHA,require,read,sha
from .stage10_input import load_inputs as historical_inputs,validate_rows,legacy

def load_inputs(baseline_path,b6_ledger_path):
    rows,audit=historical_inputs(baseline_path,b6_ledger_path)
    require(sum(r['Source']=='BASELINE' for r in rows)==9083,'current27 2020 count changed')
    counts={name:len(portfolio(rows,name)) for name in CONFIGS}
    require(list(counts.values())==[9083,9421,9760],'R2 must not filter trades')
    audit.update(Stage11PortfolioCounts=counts,R2AssignmentsGenerated=False,MoneySimulationExecuted=False)
    return rows,audit

def portfolio(rows,name):
    require(name in CONFIGS,'unregistered Stage11 portfolio')
    out=[r for r in rows if r['Source']=='BASELINE' or r['PortfolioComponentKey'] in CONFIGS[name]]
    validate_rows(out);return out

def audit_m1(root,coverage=True):
    from .stage1_data import audit_inputs
    require(sha(ROOT/INPUT/'expected_m1_manifest.csv')==MANIFEST_SHA,'M1 manifest mismatch')
    manifest,paths,files=audit_inputs(root)
    require(len(files)==56,'56 M1 files required')
    result=dict(Status='PASS',ManifestSHA256=MANIFEST_SHA,Files=files,FileCount=56,R2AssignmentsGenerated=False,MoneySimulationExecuted=False)
    if coverage:
        import pandas as pd
        stats=[]
        for symbol in dict.fromkeys(manifest.Symbol):
            frames=[]
            for row in manifest[manifest.Symbol==symbol].itertuples():
                f=pd.read_csv(paths[row.Filename],sep='\t',usecols=[0,1],dtype=str)
                frames.append(pd.to_datetime(f.iloc[:,0]+' '+f.iloc[:,1],format='%Y.%m.%d %H:%M:%S'))
            raw=pd.concat(frames,ignore_index=True)
            jst=raw.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward').dt.tz_convert('Asia/Tokyo').dt.tz_localize(None)
            require(jst.is_unique and jst.is_monotonic_increasing,'DUPLICATE_OR_UNSORTED_M1')
            dates=jst.dt.normalize().drop_duplicates()
            stats.append(dict(Symbol=symbol,FirstJST=str(jst.min()),LastJST=str(jst.max()),Rows=len(jst),ActualDates=len(dates),
                ActualDatesBefore2020=int((dates<pd.Timestamp('2020-01-01')).sum()),ActualDatesBefore2024=int((dates<pd.Timestamp('2024-01-01')).sum()),
                WarmupRequiredActualDates=272,FeaturesCalculated=False))
        result['Coverage']=stats
    return manifest,paths,result

def load_daily(symbol,manifest,paths):
    """Full history (including warmup), only called by authorized formal runner."""
    import numpy as np
    import pandas as pd
    from .stage0 import reference
    ref=reference();frames=[ref.read_mt5_file(paths[x.Filename]) for x in manifest[manifest.Symbol==symbol].itertuples()]
    require(bool(frames),'UNAVAILABLE_FEATURE_SOURCE')
    f=pd.concat(frames,ignore_index=True)
    raw=f.RawDatetime.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward')
    f.index=pd.DatetimeIndex(raw.dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
    require(f.index.is_unique and f.index.is_monotonic_increasing,'DUPLICATE_OR_UNSORTED_M1')
    require(not (f.index.as_unit('ns').asi8%60_000_000_000).any(),'M1_ALIGNMENT')
    a=f[['Open','High','Low','Close']]
    require(np.isfinite(a.to_numpy()).all() and (a>0).all().all() and (a.High>=a[['Open','Low','Close']].max(axis=1)).all() and (a.Low<=a[['Open','High','Close']].min(axis=1)).all(),'INVALID_OHLC')
    f=f.assign(Last=f.index,Count=1)
    daily=f.groupby(f.index.normalize(),sort=False).agg({'Open':'first','High':'max','Low':'min','Close':'last','Last':'last','Count':'sum'})
    return [dict(day=t.to_pydatetime(),open=float(r.Open),high=float(r.High),low=float(r.Low),close=float(r.Close),last=r.Last.to_pydatetime(),count=int(r.Count)) for t,r in daily.iterrows()]

def stage10_archive_audit(path):
    path=Path(path)
    if not path.exists():return dict(Status='NOT_AVAILABLE',ScientificInput=False,PerformanceUsed=False)
    summary=read(path/'stage10_summary.json');review=read(path/'stage10_review.json')
    require(summary['State']=='COMPLETE_STAGE10_INCREMENTAL_PORTFOLIO_ONLY','Stage10 incomplete archive')
    for k in ('GlobalR2Applied','RiskAllocationDecided','LiveChanged'):require(summary[k] is False,'Stage10 state changed: '+k)
    require(review['Summary']==summary and read(path/'progress.json')==summary,'Stage10 summary mismatch')
    for name,h in review['OutputSHA256'].items():
        require(Path(name).name==name and sha(path/name)==h,'Stage10 archive hash mismatch')
    return dict(Status='PASS',State=summary['State'],GlobalR2Applied=False,RiskAllocationDecided=False,LiveChanged=False,
        ScientificInput=False,PerformanceUsed=False,MetadataSHA256={n:sha(path/n) for n in ('identity.json','effective_config.json','stage10_summary.json','stage10_review.json','progress.json')},OutputSHA256=review['OutputSHA256'])
