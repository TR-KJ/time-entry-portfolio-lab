"""M1 integrity/coverage audit and Discovery-only price calibration. No strategy search."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from .execution import PIPS, discovery_view
from .calibration import calibrate
ROOT=Path(__file__).resolve().parents[3]
SYMBOLS=list(PIPS)
SPREAD=dict(zip(SYMBOLS,(.5,1,2,1.5,1.5,1.5,2,1,1.5)))
PERIODS={'Discovery':('2020-01-01','2024-01-01'),'Validation':('2024-01-01','2026-01-01'),'Monitor':('2026-01-01','2026-09-10')}

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def save(name,obj):
    (ROOT/'results/b7/stage0'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def loader():
    p=ROOT/'src/research/daily_stop_baseline_revalidation.py'
    if digest(p)!='08b9717a3a94a0066e7ef7ebfa0f4802cbc84ae0570c3b875d96729877f4e216':raise ValueError('baseline source changed')
    spec=importlib.util.spec_from_file_location('b7_frozen_baseline',p)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m.read_mt5_file

def inspect_file(p,symbol,read):
    before=digest(p); df=read(p)
    raw=df.RawDatetime
    a=df[['Open','High','Low','Close']]
    invalid=int(((a.High<a.max(axis=1))|(a.Low>a.min(axis=1))).sum())
    bad=int((~np.isfinite(a.to_numpy())).sum())
    if bad:raise ValueError('nonfinite OHLC: '+p.name)
    # Decimal formatting audit, not execution comparison. No price rounding here.
    tick=PIPS[symbol]/10
    off=int((np.abs(a.to_numpy()/tick-np.rint(a.to_numpy()/tick))>1e-6).sum())
    step=raw.diff().dt.total_seconds().div(60)
    row=dict(Symbol=symbol,Filename=p.name,SHA256=before,Rows=len(df),FirstRaw=str(raw.iloc[0]),LastRaw=str(raw.iloc[-1]),
             RawDuplicates=int(raw.duplicated().sum()),RawOrdered=bool(raw.is_monotonic_increasing),InvalidOHLC=invalid,
             Nonfinite=bad,Nonpositive=int((a<=0).sum().sum()),OffFractionalPipGrid=off,
             RawGapCountGT1=int((step>1).sum()),MaxRawGapMinutes=float(step.max()),
             SourceFolder='/'.join(p.parts[p.parts.index('再現性100%'): -1]),
             Format='MT5 tab-separated OHLC export; no broker identifier')
    if digest(p)!=before:raise ValueError('file mutated during audit')
    if invalid or bad or row['Nonpositive'] or off or not row['RawOrdered']:raise ValueError('invalid input: '+p.name)
    row['Status']='PASS_FILE_INTEGRITY'
    return row,df

def main(data_root):
    read=loader();out=ROOT/'results/b7/stage0'
    save('run_status.json',{'Stage0':'IN_PROGRESS_NOT_CLEARED','BrokerIdentity':'UNVERIFIED','Stage1':'NOT_IMPLEMENTED_NOT_RUN','ValidationPerformance':'NOT_RUN','MonitorPerformance':'NOT_RUN'})
    paths=sorted(p for p in Path(data_root).rglob('*.csv') if '_M1_' in p.name and p.name.split('_')[0] in SYMBOLS)
    expected=pd.read_csv(ROOT/'research_inputs/b7/b6_reference_manifest.csv')
    if digest(ROOT/'research_inputs/b7/b6_reference_manifest.csv')!='8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f':raise ValueError('B6 identity changed')
    audits=[];inventory=[];coverage=[];pair_audit=[];stats=[];days=[];alternates=[]
    for symbol in SYMBOLS:
        sp=[p for p in paths if p.name.startswith(symbol+'_M1_')]
        if len({p.name for p in sp})!=len(sp):raise ValueError('ambiguous file names')
        names=set(expected.loc[expected.Symbol==symbol,'Filename'])
        frames={};rows={}
        for p in sp:
            row,frame=inspect_file(p,symbol,read);rows[p.name]=row;frames[p.name]=frame;audits.append(row)
            pd.DataFrame(audits).to_csv(out/'input_audit.csv',index=False)
        if symbol in ('EURUSD','GBPUSD'):
            # Select expanded export only after proving exact OHLC/timestamp subset identity.
            recent=[n for n in frames if '_202604' in n]
            if len(recent)!=2 or sum('_RECHECK' in n for n in recent)!=1:raise ValueError('unexpected EU/GU segmentation')
            new=next(n for n in recent if '_RECHECK' in n);old=next(n for n in recent if '_RECHECK' not in n)
            old_frame=frames[old].set_index('RawDatetime');new_frame=frames[new].set_index('RawDatetime')
            overlap=old_frame.index.is_unique and new_frame.index.is_unique and old_frame.index.isin(new_frame.index).all() and old_frame.equals(new_frame.reindex(old_frame.index))
            alternates.append(dict(Symbol=symbol,Selected=new,Excluded=old,ExactTimestampOHLCSubset=overlap,SelectedRows=len(frames[new]),ExcludedRows=len(frames[old]),Reason='SUPERSET_WITH_IDENTICAL_OVERLAP' if overlap else 'UNRESOLVED_CONFLICT'))
            save('alternate_exports.json',alternates)
            if not overlap:raise ValueError('STOP: conflicting alternate exports')
            names=set(frames)-{old}
            if len(names)!=8:raise ValueError('unexpected EU/GU segment count')
        if not names or not names<=frames.keys():raise ValueError('missing selected data')
        order=sorted(names,key=lambda n:rows[n]['FirstRaw'])
        for n in order:
            row=rows[n]
            if symbol not in ('EURUSD','GBPUSD'):
                exp=expected[(expected.Symbol==symbol)&(expected.Filename==n)].iloc[0]
                if any(row[k]!=exp[k] for k in ('SHA256','Rows','FirstRaw','LastRaw')):raise ValueError('STOP: B6 identity mismatch '+n)
            row['Selected']=True
            inventory.append({k:row[k] for k in ('Symbol','Filename','SHA256','Rows','FirstRaw','LastRaw')})
        full=pd.concat([frames[n] for n in order],ignore_index=True);del frames
        localized=full.RawDatetime.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward')
        full.index=pd.DatetimeIndex(localized.dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
        info=dict(Symbol=symbol,Files=len(order),Rows=len(full),FirstJST=str(full.index.min()),LastJST=str(full.index.max()),RawDuplicates=int(full.RawDatetime.duplicated().sum()),JSTDuplicates=int(full.index.duplicated().sum()),JSTOrdered=bool(full.index.is_monotonic_increasing))
        if info['JSTDuplicates'] or not info['JSTOrdered']:raise ValueError('STOP: JST duplicate/ordering')
        delta=full.index.to_series().diff().dt.total_seconds().div(60)
        info.update(GapCountGT1=int((delta>1).sum()),GapCountGT10=int((delta>10).sum()),MaxGapMinutes=float(delta.max()),MissingMinutesInSpan=int((delta[delta>1]-1).sum()))
        pair_audit.append(info)
        for period,(start,end) in PERIODS.items():
            idx=full.index[(full.index>=start)&(full.index<end)]
            coverage.append(dict(Symbol=symbol,Period=period,RequestedStart=start,RequestedEndExclusive=end,Rows=len(idx),FirstJST=str(idx.min()),LastJST=str(idx.max()),ObservedDates=len(idx.normalize().unique()),MissingMinutesInSpan=int(np.sum((idx[1:]-idx[:-1]).total_seconds()/60-1)) if len(idx)>1 else 0))
        # No Validation/Monitor arrays returned to the calibration function.
        bars=discovery_view(full);del full
        summary,diagnostics=calibrate(bars,symbol);del bars
        if symbol not in ('EURUSD','GBPUSD'):
            target=pd.read_csv(ROOT/'research_inputs/b7/b6_sl_reference.csv');target=target[target.Symbol==symbol].iloc[0]
            same=summary['SL']==[int(target[f'SL{i}']) for i in range(1,6)]
            summary['B6GridExactMatch']=same
            if not same:raise ValueError('STOP: B6 SL grid mismatch')
        if summary['Status']!='PROPOSAL':raise ValueError('STOP: insufficient calibration')
        stats.append(summary);days.extend(diagnostics)
        save('price_statistics.json',stats)
        pd.DataFrame(pair_audit).to_csv(out/'pair_audit.csv',index=False)
        pd.DataFrame(coverage).to_csv(out/'coverage.csv',index=False)
        pd.DataFrame(inventory).to_csv(ROOT/'research_inputs/b7/expected_m1_manifest.csv',index=False)
        pd.DataFrame(days).to_csv(out/'calibration_day_diagnostics.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        print(symbol,'integrity/coverage audited; SL proposal',summary['SL'],flush=True)
    pd.DataFrame([dict(r,Selected=r.get('Selected',False)) for r in audits]).to_csv(out/'input_audit.csv',index=False)
    grid=pd.DataFrame([dict(Symbol=s['Symbol'],Status='PROVISIONAL',**{f'SL{i+1}':v for i,v in enumerate(s['SL'])}) for s in stats])
    grid.to_csv(out/'sl_grid_proposal.csv',index=False);grid.to_csv(ROOT/'research_inputs/b7/sl_grid_proposal.csv',index=False)
    save('spread_pip_audit.json',{'spread_pips':SPREAD,'pip_size':PIPS,'EU_GU_spreads':'AGREED research assumptions; not historical measured averages','price_format':'positive finite OHLC on fractional-pip decimal grid; see input_audit.csv','broker_identity':'UNVERIFIED: directory/header similarity alone is not proof'})
    save('run_status.json',{'DataIntegrity':'PASS','BrokerIdentity':'UNVERIFIED','Stage0':'BLOCKED_PENDING_PROVENANCE','Stage1':'NOT_IMPLEMENTED_NOT_RUN','ValidationPerformance':'NOT_RUN','MonitorPerformance':'NOT_RUN','AllPeriodDataIntegrityRead':True,'CalibrationPeriod':'Discovery only','B6CandidateInputsUsed':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);a=p.parse_args()
    try:main(a.data_root)
    except Exception:
        save('run_status.json',{'Stage0':'STOP_AUDIT_FAILURE','PriorOutputTables':'NOT_A_COMPLETED_RUN','BrokerIdentity':'UNVERIFIED','Stage1':'NOT_IMPLEMENTED_NOT_RUN','ValidationPerformance':'NOT_RUN','MonitorPerformance':'NOT_RUN'})
        raise
