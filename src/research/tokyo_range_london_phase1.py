"""B1 preregistered Tokyo range event study; no trading simulation."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PLAN_SHA = '84b959d715472c81627cbb42579911c7c2805b58'
PAIRS = ['USDJPY','EURJPY','GBPJPY','AUDJPY','AUDUSD','EURAUD','GBPAUD']
HYPOTHESES = ['BREAKOUT_CONTINUATION','SWEEP_REVERSAL']
PERIODS = {
 'Historical': ('2015-01-01','2021-12-31'),
 'RecentA': ('2022-01-01','2023-12-31'),
 'RecentB': ('2024-01-01','2025-12-31'),
 'Monitor2026': ('2026-01-01','2026-09-09'),
 'RecentCombined': ('2022-01-01','2026-09-09'),
 'ALL': ('2015-01-01','2026-09-09'),
}
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT/'research_inputs/a3_expected_m1_manifest.csv'
PREFIX = 'tokyo_range_london_phase1_'
SEED, B = 20260913, 5000
MANIFEST_SHA256 = '8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f'


def sha256(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
 return h.hexdigest()


def pip_size(pair):
 if pair not in PAIRS: raise ValueError(pair)
 return .01 if pair.endswith('JPY') else .0001


def localize_mt5(raw):
 return pd.DatetimeIndex(raw).tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward').tz_convert('UTC')


def discover(root, expected):
 names=set(expected.Filename)
 hits={n:[] for n in names}
 for p in Path(root).rglob('*.csv'):
  if p.name in names: hits[p.name].append(p)
 bad={n:len(v) for n,v in hits.items() if len(v)!=1}
 if bad: raise ValueError('missing or duplicate source names: '+str(bad))
 return {n:v[0] for n,v in hits.items()}


def candidate_dates():
 return pd.bdate_range('2015-01-01','2026-09-09')


def london_endpoints(dates):
 # Local midnight plus wall-clock time, then IANA localization handles DST.
 naive=pd.DatetimeIndex(dates)
 return {h:(naive+pd.Timedelta(hours=h)).tz_localize('Europe/London').tz_convert('UTC') for h in (8,9,11)}


def classify(up,down,open09,high,low):
 if up and down: return 'BOTH_SIDES'
 if not up and not down: return 'NO_BREAK'
 if up: return 'UP_BREAKOUT' if open09>high else 'UP_SWEEP'
 return 'DOWN_BREAKOUT' if open09<low else 'DOWN_SWEEP'


def aligned(event, outcome):
 return outcome * {'UP_BREAKOUT':1,'DOWN_BREAKOUT':-1,'UP_SWEEP':-1,'DOWN_SWEEP':1}[event]


def read_pair(pair, expected, paths):
 audits=[]; pieces=[]; previous_utc_max=None
 for row in expected[expected.Symbol.eq(pair)].itertuples(index=False):
  path=paths[row.Filename]
  digest=sha256(path)
  if digest!=row.SHA256: raise ValueError(f'hash mismatch: {path}')
  d=pd.read_csv(path,sep='\t')
  d.columns=[str(c).strip('<>').upper() for c in d.columns]
  required={'DATE','TIME','OPEN','HIGH','LOW','CLOSE'}
  if not required.issubset(d.columns): raise ValueError(f'columns: {path}')
  raw=pd.to_datetime(d.DATE.astype(str)+' '+d.TIME.astype(str),format='%Y.%m.%d %H:%M:%S')
  if len(d)!=row.Rows or str(raw.iloc[0])!=row.FirstRaw or str(raw.iloc[-1])!=row.LastRaw:
   raise ValueError(f'row/bounds mismatch: {path}')
  o,h,l,c=(d[x].to_numpy(dtype=float) for x in ('OPEN','HIGH','LOW','CLOSE'))
  if not np.isfinite(np.column_stack((o,h,l,c))).all() or np.any(np.minimum.reduce((o,h,l,c))<=0):
   raise ValueError(f'nonpositive/nonfinite price: {path}')
  if np.any(h<np.maximum.reduce((o,l,c))) or np.any(l>np.minimum.reduce((o,h,c))):
   raise ValueError(f'invalid OHLC: {path}')
  utc=localize_mt5(raw)
  ns=utc.asi8
  if np.any(np.diff(ns)<=0) or (previous_utc_max is not None and ns[0]<=previous_utc_max):
   raise ValueError(f'duplicate or nonmonotone UTC: {path}')
  previous_utc_max=int(ns[-1])
  jst=utc.tz_convert('Asia/Tokyo')
  lon=utc.tz_convert('Europe/London')
  jhour=jst.hour*60+jst.minute
  lhour=lon.hour*60+lon.minute
  keep=((jhour>=540)&(jhour<900))|((lhour>=480)&(lhour<540))|((lhour==540)|(lhour==660))
  x=pd.DataFrame({'UTC':utc[keep],'JDate':jst[keep].tz_localize(None).normalize(),
      'LDate':lon[keep].tz_localize(None).normalize(),'JMinute':jhour[keep],
      'LMinute':lhour[keep],'Open':o[keep],'High':h[keep],'Low':l[keep],
      'Filename':path.name,'SourceRow':np.flatnonzero(keep)+2})
  pieces.append(x)
  adjusted=int(np.count_nonzero(utc.tz_convert('Europe/Helsinki').tz_localize(None).asi8!=raw.array.asi8))
  audits.append({'Pair':pair,'Filename':path.name,'SHA256':digest,'Rows':len(d),
                 'FirstRaw':str(raw.iloc[0]),'LastRaw':str(raw.iloc[-1]),
                 'AdjustedTimestampCount':adjusted,'HashMatch':True})
 bars=pd.concat(pieces,ignore_index=True).sort_values('UTC')
 return bars,pd.DataFrame(audits)


def daily_events(pair,bars):
 dates=candidate_dates(); endpoint=london_endpoints(dates)
 tok=bars[(bars.JMinute>=540)&(bars.JMinute<900)]
 t=tok.groupby('JDate').agg(TokyoBars=('UTC','nunique'),TokyoHigh=('High','max'),TokyoLow=('Low','min'))
 ev=bars[(bars.LMinute>=480)&(bars.LMinute<540)]
 e=ev.groupby('LDate').agg(EventBars=('UTC','nunique'),EventHigh=('High','max'),EventLow=('Low','min'))
 opens=bars[bars.LMinute.isin([540,660])].set_index('UTC').Open
 if opens.index.has_duplicates: raise ValueError('duplicate London endpoint')
 df=pd.DataFrame({'Date':dates}).join(t,on='Date').join(e,on='Date')
 df['Open09']=opens.reindex(endpoint[9]).to_numpy()
 df['Open11']=opens.reindex(endpoint[11]).to_numpy()
 df['TokyoBars']=df.TokyoBars.fillna(0).astype(int)
 df['EventBars']=df.EventBars.fillna(0).astype(int)
 df['Pair']=pair
 df['TokyoRangePips']=(df.TokyoHigh-df.TokyoLow)/pip_size(pair)
 df['OutcomePips']=(df.Open11-df.Open09)/pip_size(pair)
 df['HighBreak']=df.EventHigh>df.TokyoHigh
 df['LowBreak']=df.EventLow<df.TokyoLow
 df['Status']='OK'
 # Priority is fixed in Plan. London 08 always follows Tokyo 15, but check explicitly.
 order=endpoint[8].asi8 <= (dates+pd.Timedelta(hours=15)).tz_localize('Asia/Tokyo').tz_convert('UTC').asi8
 rules=[('MISSING_LONDON_11_OPEN',df.Open11.isna()),('MISSING_LONDON_09_OPEN',df.Open09.isna()),
        ('INSUFFICIENT_LONDON_EVENT_DATA',df.EventBars.ne(60)),('WINDOW_ORDER_INVALID',order),
        ('DEGENERATE_TOKYO_RANGE',df.TokyoRangePips.le(0)),('INSUFFICIENT_TOKYO_RANGE_DATA',df.TokyoBars.ne(360))]
 for label,mask in rules: df.loc[mask,'Status']=label
 df['Event']='EXCLUDED'
 ok=df.Status.eq('OK')
 df.loc[ok,'Event']=[classify(u,d,o,h,l) for u,d,o,h,l in zip(df.loc[ok,'HighBreak'],df.loc[ok,'LowBreak'],df.loc[ok,'Open09'],df.loc[ok,'TokyoHigh'],df.loc[ok,'TokyoLow'])]
 df['Hypothesis']=df.Event.map({'UP_BREAKOUT':HYPOTHESES[0],'DOWN_BREAKOUT':HYPOTHESES[0],
                                'UP_SWEEP':HYPOTHESES[1],'DOWN_SWEEP':HYPOTHESES[1]})
 df['AlignedPips']=np.nan
 target=df.Hypothesis.notna()
 df.loc[target,'AlignedPips']=[aligned(x,y) for x,y in zip(df.loc[target,'Event'],df.loc[target,'OutcomePips'])]
 assert not df.duplicated(['Pair','Date']).any()
 return df


def weeks(start,end):
 a=pd.Timestamp(start); z=pd.Timestamp(end)
 first=a-pd.Timedelta(days=a.weekday())
 last=z-pd.Timedelta(days=z.weekday())
 return first, ((last-first).days//7)+1


def week_draws(start,end):
 first,k=weeks(start,end)
 rng=np.random.default_rng(SEED)
 return first,rng.integers(0,k,size=(B,k),dtype=np.int32)


def bootstrap(values,dates,first,draws):
 if len(values)==0: return (np.nan,np.nan,np.nan,0,np.array([]))
 k=draws.shape[1]
 ix=((pd.DatetimeIndex(dates)-first).days//7).to_numpy()
 sums=np.bincount(ix,weights=np.asarray(values,float),minlength=k)
 count=np.bincount(ix,minlength=k)
 bs=sums[draws].sum(axis=1)
 bc=count[draws].sum(axis=1)
 means=np.divide(bs,bc,out=np.full(B,np.nan),where=bc>0)
 valid=means[np.isfinite(means)]
 if len(valid)<4750: return (np.nan,np.nan,np.nan,len(valid),valid)
 estimate=float(np.mean(values))
 lo,hi=np.quantile(valid,[.025,.975],method='linear')
 p=(1+np.count_nonzero(abs(valid-estimate)>=abs(estimate)))/(1+len(valid))
 return float(lo),float(hi),float(p),len(valid),valid


def holm(p):
 p=np.asarray(p,float); safe=np.where(np.isfinite(p),p,1.)
 order=np.argsort(safe,kind='stable'); m=len(p)
 adj=np.minimum(1,np.maximum.accumulate((m-np.arange(m))*safe[order]))
 out=np.empty(m);out[order]=adj
 return out


def summary_stats(g):
 x=g.AlignedPips.to_numpy(float); n=len(x)
 return {'N':n,'Weeks':g.Date.dt.to_period('W-SUN').nunique(),
         'MeanAlignedPips':float(np.mean(x)) if n else np.nan,
         'MedianAlignedPips':float(np.median(x)) if n else np.nan,
         'SDAlignedPips':float(np.std(x,ddof=1)) if n>1 else np.nan,
         'TotalAlignedPips':float(np.sum(x)),
         'PositiveRate':float(np.mean(x>0)) if n else np.nan,
         'NegativeRate':float(np.mean(x<0)) if n else np.nan,
         'ZeroRate':float(np.mean(x==0)) if n else np.nan}


def summarize(daily):
 periods=[]; dirs=[]; counts=[]; coverage=[]
 for period,(start,end) in PERIODS.items():
  first,draws=week_draws(start,end)
  for pair in PAIRS:
   d=daily[daily.Pair.eq(pair)&daily.Date.between(start,end)]
   cov=Counter(d.Status)
   coverage.append({'Period':period,'Pair':pair,'CandidateDays':len(d),**dict(cov)})
   for event in ['UP_BREAKOUT','DOWN_BREAKOUT','UP_SWEEP','DOWN_SWEEP','BOTH_SIDES','NO_BREAK']:
    z=d[d.Event.eq(event)]
    counts.append({'Period':period,'Pair':pair,'Event':event,'N':len(z),
                   'RawOutcomeMeanPips':float(z.OutcomePips.mean()) if len(z) else np.nan})
   for hyp in HYPOTHESES:
    g=d[d.Hypothesis.eq(hyp)]
    stat=summary_stats(g)
    lo,hi,p,nboot,_=bootstrap(g.AlignedPips.to_numpy(float),g.Date,first,draws)
    threshold=(40,20) if period in ('ALL','Historical','RecentCombined') else (20,10)
    status='OK' if stat['N']>=threshold[0] and stat['Weeks']>=threshold[1] else 'INSUFFICIENT_SAMPLE'
    if status=='OK' and nboot<4750: status='BOOTSTRAP_INSUFFICIENT'
    periods.append({'Period':period,'Pair':pair,'Hypothesis':hyp,**stat,
                    'CILow':lo,'CIHigh':hi,'RawP':p,'ValidBootstraps':nboot,'Status':status})
    for event in (['UP_BREAKOUT','DOWN_BREAKOUT'] if hyp==HYPOTHESES[0] else ['UP_SWEEP','DOWN_SWEEP']):
     z=g[g.Event.eq(event)]
     dlo,dhi,_,dnboot,_=bootstrap(z.AlignedPips.to_numpy(float),z.Date,first,draws)
     dirs.append({'Period':period,'Pair':pair,'Event':event,'N':len(z),
                  'MeanAlignedPips':float(z.AlignedPips.mean()) if len(z) else np.nan,
                  'MedianAlignedPips':float(z.AlignedPips.median()) if len(z) else np.nan,
                  'PositiveRate':float((z.AlignedPips>0).mean()) if len(z) else np.nan,
                  'CILow':dlo,'CIHigh':dhi,'ValidBootstraps':dnboot})
 period_df=pd.DataFrame(periods)
 all_df=period_df[period_df.Period.eq('ALL')].copy()
 all_df['HolmAdjustedP']=holm(all_df.RawP.to_numpy())
 pair_rows=[]
 for row in all_df.itertuples(index=False):
  sub=period_df[period_df.Pair.eq(row.Pair)&period_df.Hypothesis.eq(row.Hypothesis)].set_index('Period')
  def positive(per):
   z=sub.loc[per]
   return z.Status=='OK' and z.MeanAlignedPips>0
  short=['RecentA','RecentB','Monitor2026']
  g=(row.N>=40 and row.Weeks>=20 and row.ValidBootstraps>=4750 and
     all(sub.loc[p].Status=='OK' for p in ['Historical','RecentCombined']) and
     sum(sub.loc[p].Status=='OK' for p in short)>=2)
  gates={'A':row.MeanAlignedPips>0,'B':row.CILow>0,'C':row.HolmAdjustedP<.05,
         'D':positive('Historical'),'E':positive('RecentCombined'),
         'F':sum(positive(p) for p in short)>=2,'G':g}
  verdict=(row.Hypothesis+'_SUPPORTED') if all(gates.values()) else (
   'BOOTSTRAP_INSUFFICIENT' if not g and row.N>=40 and row.Weeks>=20 and row.ValidBootstraps<4750 and
   all(sub.loc[p].Status=='OK' for p in ['Historical','RecentCombined']) and
   sum(sub.loc[p].Status=='OK' for p in short)>=2 else
   'INSUFFICIENT_SAMPLE' if not g else 'NOT_SUPPORTED')
  pair_rows.append({**row._asdict(),**{k:'PASS' if v else 'FAIL' for k,v in gates.items()},'Verdict':verdict})
 pair_df=pd.DataFrame(pair_rows)
 family=[]
 for hyp in HYPOTHESES:
  z=pair_df[pair_df.Hypothesis.eq(hyp)].set_index('Pair')
  for name,members in [('JPY',PAIRS[:4]),('AUD_non_JPY',PAIRS[4:]),('All_7',PAIRS)]:
   t=z.loc[members]; eligible=t.SDAlignedPips.gt(0)&t.G.eq('PASS')
   vals=(t.MeanAlignedPips/t.SDAlignedPips)[eligible]
   family.append({'Family':name,'Hypothesis':hyp,'FixedMembers':'|'.join(members),
                  'Contributors':int(eligible.sum()),'EqualWeightStandardizedMean':float(vals.mean()) if len(vals) else np.nan,
                  'Status':'DESCRIPTIVE_ONLY' if eligible.all() else 'INCOMPLETE'})
 return {'pair_hypothesis_summary':pair_df,'period_summary':period_df,
         'direction_summary':pd.DataFrame(dirs),'event_counts':pd.DataFrame(counts),
         'coverage':pd.DataFrame(coverage),'family_summary':pd.DataFrame(family),
         'multiple_comparison':pair_df[['Pair','Hypothesis','RawP','HolmAdjustedP','CILow','CIHigh','C']]}



def manual_audit(pair,bars,daily):
 rows=[]
 valid=daily[daily.Status.eq('OK')].sort_values('Date')
 ep=london_endpoints(valid.Date)
 valid=valid.copy()
 valid['London08UTC']=ep[8]
 for season in ('winter','summer'):
  z=valid[valid.London08UTC.map(lambda x: bool(x.tz_convert('Europe/London').dst().total_seconds())) == (season=='summer')]
  for kind in ('BREAKOUT','SWEEP'):
   q=z[z.Event.str.endswith(kind)]
   if q.empty:
    rows.append({'Pair':pair,'Season':season,'Kind':kind,'Status':'MISSING_STRATUM'})
    continue
   row=q.iloc[0]
   tb=bars[bars.JDate.eq(row.Date)&bars.JMinute.between(540,899)]
   eb=bars[bars.LDate.eq(row.Date)&bars.LMinute.between(480,539)]
   endpoints=london_endpoints(pd.DatetimeIndex([row.Date]))
   b09=bars[bars.UTC.eq(endpoints[9][0])]
   b11=bars[bars.UTC.eq(endpoints[11][0])]
   if len(tb)!=360 or len(eb)!=60 or len(b09)!=1 or len(b11)!=1: raise ValueError('manual audit coverage')
   independent_high=float(tb.High.max()); independent_low=float(tb.Low.min())
   event=classify(bool((eb.High>independent_high).any()),bool((eb.Low<independent_low).any()),float(b09.Open.iloc[0]),independent_high,independent_low)
   independent_outcome=(float(b11.Open.iloc[0])-float(b09.Open.iloc[0]))/pip_size(pair)
   if event!=row.Event or not np.isclose(independent_outcome,row.OutcomePips,rtol=0,atol=1e-8): raise ValueError('manual audit mismatch')
   rows.append({'Pair':pair,'Season':season,'Kind':kind,'Date':str(row.Date.date()),'Event':event,
    'TokyoHigh':independent_high,'TokyoLow':independent_low,'EventHigh':float(eb.High.max()),'EventLow':float(eb.Low.min()),
    'London09Open':float(b09.Open.iloc[0]),'London11Open':float(b11.Open.iloc[0]),
    'IndependentOutcomePips':independent_outcome,'AlignedPips':float(row.AlignedPips),
    'London09File':b09.Filename.iloc[0],'London09SourceRow':int(b09.SourceRow.iloc[0]),
    'London11File':b11.Filename.iloc[0],'London11SourceRow':int(b11.SourceRow.iloc[0]),'Status':'PASS'})
 return pd.DataFrame(rows)


def run(data_root,out,implementation_sha):
 if len(implementation_sha)!=40: raise ValueError('full implementation SHA required')
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if sha256(MANIFEST)!=MANIFEST_SHA256: raise ValueError('frozen manifest hash mismatch')
 expected=pd.read_csv(MANIFEST)
 if len(expected)!=56 or set(expected.Symbol)!=set(PAIRS) or any(expected.groupby('Symbol').size()!=8):
  raise ValueError('expected manifest is not seven by eight')
 paths=discover(data_root,expected)
 daily=[];audits=[];manual=[]
 for pair in PAIRS:
  print('Auditing',pair,flush=True)
  bars,a=read_pair(pair,expected,paths)
  events=daily_events(pair,bars)
  daily.append(events);audits.append(a);manual.append(manual_audit(pair,bars,events))
 daily=pd.concat(daily,ignore_index=True);audit=pd.concat(audits,ignore_index=True)
 assert not daily.duplicated(['Pair','Date']).any()
 tables=summarize(daily)
 tables['input_audit']=audit
 tables['manual_audit']=pd.concat(manual,ignore_index=True)
 tables['validation']=pd.DataFrame([{'Check':'SourceHashes','Pass':audit.HashMatch.all()},
                                    {'Check':'EventUniqueness','Pass':not daily.duplicated(['Pair','Date']).any()},
                                    {'Check':'SevenSymbols','Pass':set(daily.Pair)==set(PAIRS)}])
 for name,table in tables.items(): table.to_csv(out/(PREFIX+name+'.csv'),index=False)
 daily.to_csv(out/(PREFIX+'daily_assignment.csv'),index=False)
 record={'PlanSHA':PLAN_SHA,'ImplementationSHA':implementation_sha,'ExecutedUTC':datetime.now(timezone.utc).isoformat(),
         'Python':platform.python_version(),'Numpy':np.__version__,'Pandas':pd.__version__,
         'Seed':SEED,'Bootstraps':B,'SourceFiles':len(audit),'SourceHashMatch':audit.HashMatch.all(),
         'Phase2Computed':False,'LiveChanged':False,'Status':'COMPUTED_PENDING_INDEPENDENT_AUDIT'}
 pd.DataFrame([record]).to_csv(out/(PREFIX+'run_record.csv'),index=False)
 publication=[]
 for p in sorted(out.glob(PREFIX+'*.csv')):
  if p.name.endswith('publication_manifest.csv'): continue
  publication.append({'Filename':p.name,'SHA256':sha256(p),'Bytes':p.stat().st_size,
                      'Rows':sum(1 for _ in open(p))-1,
                      'Publication':'LOCAL_ONLY' if p.name.endswith('daily_assignment.csv') else 'GITHUB'})
 pd.DataFrame(publication).to_csv(out/(PREFIX+'publication_manifest.csv'),index=False)
 return tables


if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--data-root',required=True);ap.add_argument('--out',default='/content')
 ap.add_argument('--implementation-sha',required=True)
 args=ap.parse_args();run(args.data_root,args.out,args.implementation_sha)
