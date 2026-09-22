"""Independent check of published B1 tables from daily assignments."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

P='tokyo_range_london_phase1_'
PAIRS=['USDJPY','EURJPY','GBPJPY','AUDJPY','AUDUSD','EURAUD','GBPAUD']
HYP=['BREAKOUT_CONTINUATION','SWEEP_REVERSAL']


def verify(directory):
 root=Path(directory)
 daily=pd.read_csv(root/(P+'daily_assignment.csv'),parse_dates=['Date'])
 period=pd.read_csv(root/(P+'period_summary.csv'))
 pair=pd.read_csv(root/(P+'pair_hypothesis_summary.csv'))
 counts=pd.read_csv(root/(P+'event_counts.csv'))
 assert set(daily.Pair)==set(PAIRS)
 assert not daily.duplicated(['Pair','Date']).any()
 good=daily[daily.Status.eq('OK')]
 assert good.groupby(['Pair','Date']).size().eq(1).all()
 for row in good.itertuples(index=False):
  up=row.EventHigh>row.TokyoHigh; down=row.EventLow<row.TokyoLow
  if up and down: event='BOTH_SIDES'
  elif not up and not down: event='NO_BREAK'
  elif up: event='UP_BREAKOUT' if row.Open09>row.TokyoHigh else 'UP_SWEEP'
  else: event='DOWN_BREAKOUT' if row.Open09<row.TokyoLow else 'DOWN_SWEEP'
  assert event==row.Event
  pip=.01 if row.Pair.endswith('JPY') else .0001
  raw=(row.Open11-row.Open09)/pip
  assert np.isclose(raw,row.OutcomePips,atol=1e-8,rtol=0)
  if event not in ('BOTH_SIDES','NO_BREAK'):
   sign={'UP_BREAKOUT':1,'DOWN_BREAKOUT':-1,'UP_SWEEP':-1,'DOWN_SWEEP':1}[event]
   assert np.isclose(sign*raw,row.AlignedPips,atol=1e-8,rtol=0)
 for r in period.itertuples(index=False):
  start,end={
   'Historical':('2015-01-01','2021-12-31'),'RecentA':('2022-01-01','2023-12-31'),
   'RecentB':('2024-01-01','2025-12-31'),'Monitor2026':('2026-01-01','2026-09-09'),
   'RecentCombined':('2022-01-01','2026-09-09'),'ALL':('2015-01-01','2026-09-09')}[r.Period]
  z=good[good.Pair.eq(r.Pair)&good.Hypothesis.eq(r.Hypothesis)&good.Date.between(start,end)]
  vals=z.AlignedPips.to_numpy(float)
  assert len(vals)==r.N
  assert z.Date.dt.to_period('W-SUN').nunique()==r.Weeks
  if len(vals):
   assert np.isclose(np.mean(vals),r.MeanAlignedPips,atol=1e-8,rtol=0)
   assert np.isclose(np.median(vals),r.MedianAlignedPips,atol=1e-8,rtol=0)
   assert np.isclose(np.sum(vals),r.TotalAlignedPips,atol=1e-8,rtol=0)
 p=pair.RawP.to_numpy(float);safe=np.nan_to_num(p,nan=1.0)
 order=np.argsort(safe,kind='stable');recheck=np.empty(14)
 previous=0
 for rank,index in enumerate(order):
  previous=max(previous,min(1.0,(14-rank)*safe[index]))
  recheck[index]=previous
 np.testing.assert_allclose(recheck,pair.HolmAdjustedP.to_numpy(float))
 # Rebuild the first ALL cell's week bootstrap through explicit row indices.
 cell=pair.iloc[0]
 z=good[good.Pair.eq(cell.Pair)&good.Hypothesis.eq(cell.Hypothesis)]
 start=pd.Timestamp('2015-01-01');end=pd.Timestamp('2026-09-09')
 first=start-pd.Timedelta(days=start.weekday())
 k=((end-pd.Timedelta(days=end.weekday()))-first).days//7+1
 weeks=((z.Date-first).dt.days//7).to_numpy()
 vals=z.AlignedPips.to_numpy(float)
 rng=np.random.default_rng(20260913)
 repl=[]
 for _ in range(5000):
  draw=rng.integers(0,k,k,dtype=np.int32)
  weights=np.bincount(draw,minlength=k)
  actual=np.repeat(np.arange(len(vals)),weights[weeks])
  if len(actual): repl.append(np.mean(vals[actual]))
 lo,hi=np.quantile(repl,[.025,.975],method='linear')
 assert np.isclose(lo,cell.CILow,atol=1e-8,rtol=0)
 assert np.isclose(hi,cell.CIHigh,atol=1e-8,rtol=0)
 return {'DailyRows':len(daily),'EligibleRows':len(good),'PeriodRows':len(period),'PrimaryTests':len(pair),
         'EventCountRows':len(counts),'IndependentHolm':True,'BootstrapSpotCheck':True}

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory');args=a.parse_args()
 print(verify(args.directory))
