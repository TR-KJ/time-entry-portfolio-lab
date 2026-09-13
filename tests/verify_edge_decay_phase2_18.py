"""Independent pandas/numpy audit; does not import the research module."""
import argparse
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import numpy as np
import pandas as pd

def verify(baseline, output_dir):
    raw=Path(baseline).read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
    d=pd.read_csv(baseline,dtype={'R':str})
    d['exact']=d.R.map(Decimal);d['R']=d.R.astype(float)
    d['EntryTime']=pd.to_datetime(d.EntryTime);d['CloseTime']=pd.to_datetime(d.CloseTime)
    out=Path(output_dir);prefix='edge_decay_phase2_18_'
    periods={'IS':('2015-01-01','2022-01-01'),'OOS1':('2022-01-01','2026-01-01'),'OOS2':('2026-01-01','2026-09-10'),'OOS_COMBINED':('2022-01-01','2026-09-10'),'ALL':('2015-01-01','2026-09-10')}
    periods.update({str(y):(f'{y}-01-01',f'{y+1}-01-01' if y<2026 else '2026-09-10') for y in range(2022,2027)})
    actual=pd.concat([pd.read_csv(out/(prefix+n+'.csv'),dtype=str) for n in ('period_results','yearly_results')])
    annual={}
    for label,(start,end) in periods.items():
        sub=d[d.EntryTime.ge(start)&d.EntryTime.lt(end)]
        expected=[]
        for frame in (sub,sub[sub.Strategy!='18_EA_2_MonWed_Short']):
            frame=frame.sort_values(['CloseTime','EntryTime','StrategyNo'],kind='stable')
            r=frame.R.to_numpy();eq=np.r_[0.,r.cumsum()]
            expected.append(dict(Trades=len(frame),TotalR=sum(frame.exact,Decimal(0)),PF=r[r>0].sum()/-r[r<0].sum(),MaxDDR=(np.maximum.accumulate(eq)-eq).max(),WorstDayR=frame.groupby(frame.CloseTime.dt.date).R.sum().min(),WorstWeekR=frame.groupby(frame.CloseTime.dt.to_period('W-SUN')).R.sum().min()))
        delta={k:expected[1][k]-expected[0][k] for k in expected[0]};expected.append(delta)
        assert delta['TotalR']==-sum(sub.loc[sub.Strategy=='18_EA_2_MonWed_Short','exact'],Decimal(0))
        if label.isdigit():annual[int(label)]=delta['TotalR']
        for name,exp in zip(('E0_BASELINE','E1_MINUS_18','DELTA_E1_MINUS_E0'),expected):
            got=actual[(actual.Period==label)&(actual.Candidate==name)].iloc[0]
            for k,v in exp.items():
                if k=='TotalR': assert Decimal(got[k])==v,(label,name,k)
                else: assert np.isclose(float(got[k]),float(v),atol=1e-10,rtol=1e-10),(label,name,k,got[k],v)
    total=sum(annual.values(),Decimal(0));count=sum(x>=0 for x in annual.values())
    passed=total>0 and count>=3 and max(annual.values())<Decimal('.70')*total
    dec=pd.read_csv(out/(prefix+'decision.csv')).iloc[0]
    assert dec.Decision==('ADOPTION_CANDIDATE' if passed else 'REJECT')
    record=pd.read_csv(out/(prefix+'run_record.csv')).iloc[0]
    for name,sha in json.loads(record.CSVHashes).items():assert hashlib.sha256((out/name).read_bytes()).hexdigest()==sha
    print('PASS: 30 metric rows / 210 values, exact removal identity, annual decision and CSV hashes')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output-dir',required=True)
    verify(**vars(p.parse_args()))
