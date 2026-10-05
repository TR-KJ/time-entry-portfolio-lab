"""Exact named-file integrity barrier and owned Discovery-only price loading."""
from pathlib import Path
from datetime import datetime
import csv
import numpy as np
import pandas as pd
from .stage1_contract import ROOT, SYMBOLS, PRESPEC, digest
from .execution import START, END, discovery_view, validate

MANIFEST = 'research_inputs/b7/expected_m1_manifest.csv'

def manifest_rows():
    expected=PRESPEC['InheritedEnvironmentAndExecution']['Frozen72FileManifest']['SHA256']
    if digest(ROOT/MANIFEST)!=expected:raise ValueError('manifest identity')
    with (ROOT/MANIFEST).open() as f:rows=list(csv.DictReader(f))
    if len(rows)!=72 or len({r['Filename'] for r in rows})!=72:raise ValueError('72 unique files required')
    return rows

def resolve_exact(data_root):
    """Locate only exact frozen filenames; no alternative version or source substitution."""
    names={r['Filename'] for r in manifest_rows()}; found={}
    for p in Path(data_root).rglob('*.csv'):
        if p.name not in names:continue
        if p.name in found:raise ValueError('ambiguous duplicate exact filename')
        found[p.name]=p
    if set(found)!=names:raise ValueError('missing exact frozen files')
    return found

def raw_identity(path):
    before=digest(path)
    with Path(path).open('r',encoding='utf-8-sig',newline='') as f:
        header=next(f).rstrip('\r\n').split('\t')
        normalized=[c.strip().strip('<>').upper() for c in header]
        if not all(c in normalized for c in ('DATE','TIME','OPEN','HIGH','LOW','CLOSE')):raise ValueError('MT5 header')
        di,ti=normalized.index('DATE'),normalized.index('TIME');first=last=None;count=0
        for line in f:
            if not line.strip():continue
            if first is None:first=line
            last=line;count+=1
    if count==0:raise ValueError('empty file')
    def stamp(line):
        parts=line.rstrip('\r\n').split('\t')
        return str(pd.Timestamp(parts[di].replace('.','-')+' '+parts[ti]))
    if digest(path)!=before:raise ValueError('input mutated during audit')
    return dict(Filename=Path(path).name,SHA256=before,Rows=count,FirstRaw=stamp(first),LastRaw=stamp(last))

def audit_inputs(paths):
    rows=manifest_rows()
    if set(paths)!={r['Filename'] for r in rows}:raise ValueError('exact 72 file mapping required')
    out=[]
    for expected in rows:
        p=Path(paths[expected['Filename']])
        if p.name!=expected['Filename']:raise ValueError('filename substitution')
        got=raw_identity(p)
        for k in ('Filename','SHA256','Rows','FirstRaw','LastRaw'):
            if str(got[k])!=str(expected[k]):raise ValueError('M1 identity mismatch: '+expected['Filename']+' '+k)
        out.append(dict(Symbol=expected['Symbol'],**got))
    return out

def read_mt5(path):
    df=pd.read_csv(path,sep='\t')
    cols={str(c).strip().strip('<>').upper():c for c in df.columns}
    for c in ('DATE','TIME','OPEN','HIGH','LOW','CLOSE'):
        if c not in cols:raise ValueError('MT5 header')
    raw=pd.to_datetime(df[cols['DATE']].astype(str).str.strip()+' '+df[cols['TIME']].astype(str).str.strip(),errors='coerce')
    if raw.isna().any():raise ValueError('timestamp parse')
    idx=pd.DatetimeIndex(raw.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward').dt.tz_convert('Asia/Tokyo').dt.tz_localize(None))
    bars=pd.DataFrame({c.title():pd.to_numeric(df[cols[c]],errors='coerce').to_numpy() for c in ('OPEN','HIGH','LOW','CLOSE')},index=idx)
    if not idx.is_unique:raise ValueError('JST duplicate')
    if not np.isfinite(bars.to_numpy()).all():raise ValueError('nonfinite input')
    if not idx.is_monotonic_increasing:raise ValueError('unsorted source')
    return bars

def load_discovery(paths,symbol,bounds=None):
    """Integrity stage can see file bytes, but evaluator receives only a new Discovery copy.

    Optional bounds are only for the prespecified one-day implementation smoke.
    """
    if symbol not in SYMBOLS:raise ValueError('symbol')
    lo,hi=(START,END) if bounds is None else tuple(pd.Timestamp(t) for t in bounds)
    if not START<=lo<hi<=END:raise ValueError('non-Discovery bounds')
    frames=[]
    for row in manifest_rows():
        if row['Symbol']!=symbol:continue
        # Helsinki to JST is +6/+7 hours: use a conservative one-day source margin.
        if pd.Timestamp(row['LastRaw'])<lo-pd.Timedelta(days=1) or pd.Timestamp(row['FirstRaw'])>=hi:continue
        path=Path(paths[row['Filename']])
        if digest(path)!=row['SHA256']:raise ValueError('load identity mismatch')
        full=read_mt5(path)
        frame=discovery_view(full)
        frame=frame.loc[(frame.index>=lo)&(frame.index<hi)].copy()
        del full
        if len(frame):frames.append(frame)
        if digest(path)!=row['SHA256']:raise ValueError('file changed during load')
    if not frames:raise ValueError('no Discovery input')
    bars=pd.concat(frames).sort_index()
    validate(bars)
    return bars
