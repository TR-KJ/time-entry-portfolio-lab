"""Input audit is separate from the Discovery-only price execution boundary."""
import hashlib
import pandas as pd
from .stage0 import resolve,reference
from .execution import discovery_view,validate,START,END

def audit_inputs(root):
    ref=reference();manifest,hits=resolve(root,ref);paths={};audit=[]
    for row in manifest.itertuples():
        path=hits[row.Filename][0];h=hashlib.sha256();n=0;first=last=None
        with path.open('rb') as f:
            header=f.readline();h.update(header)
            for line in f:
                h.update(line);n+=1
                if first is None:first=line
                last=line
        def endpoint(line):
            if line is None:return ''
            p=line.decode('utf-8-sig').strip().split('\t');return p[0].replace('.','-')+' '+p[1]
        if (h.hexdigest(),n,endpoint(first),endpoint(last))!=(row.SHA256,row.Rows,row.FirstRaw,row.LastRaw):raise ValueError('input identity mismatch: '+row.Filename)
        paths[row.Filename]=path
        audit.append(dict(Symbol=row.Symbol,Filename=row.Filename,SHA256=row.SHA256,Rows=n,FirstRaw=row.FirstRaw,LastRaw=row.LastRaw,Status='PASS'))
    return manifest,paths,audit

def load_discovery(symbol,manifest,paths):
    # The audit layer can parse a mixed 2023/2024 CSV. No full frame is returned
    # to an executor, calibration, metric, selection or ranking function.
    ref=reference();frames=[]
    for row in manifest[manifest.Symbol==symbol].itertuples():
        if pd.Timestamp(row.LastRaw)<START-pd.Timedelta(days=1) or pd.Timestamp(row.FirstRaw)>=END+pd.Timedelta(days=1):continue
        frames.append(ref.read_mt5_file(paths[row.Filename]))
    if not frames:raise ValueError('no Discovery input')
    audit_frame=pd.concat(frames,ignore_index=True)
    raw=audit_frame.RawDatetime.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward')
    audit_frame.index=pd.DatetimeIndex(raw.dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
    if audit_frame.index.duplicated().any():raise ValueError('duplicate canonical JST')
    result=discovery_view(audit_frame.sort_index());del frames,audit_frame
    validate(result);return result
