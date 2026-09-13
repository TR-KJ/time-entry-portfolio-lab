"""Independent pandas audit; never imports production sensitivity/primary modules."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

def verify(baseline,output):
    assert hashlib.sha256(Path(baseline).read_bytes()).hexdigest()=='cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
    df=pd.read_csv(baseline,parse_dates=['EntryTime']);out=Path(output)
    cl=pd.read_csv(out/'edge_decay_sensitivity_classifications.csv')
    su=pd.read_csv(out/'edge_decay_sensitivity_strategy_summary.csv',keep_default_na=False)
    co=pd.read_csv(out/'edge_decay_sensitivity_continuous_metrics.csv')
    assert len(df)==16298 and df.Strategy.nunique()==28 and len(cl)==252 and len(su)==len(co)==28
    periods={'Historical':('2015-01-01','2022-01-01'),'RecentA':('2022-01-01','2024-01-01'),
             'RecentB':('2024-01-01','2026-01-01'),'RecentCombined':('2022-01-01','2026-01-01'),
             'Monitor2026':('2026-01-01','2026-09-10')}
    m={}
    for n in range(1,29):
        actual=co.loc[co.StrategyNo.eq(n)].iloc[0]
        for p,(start,end) in periods.items():
            rs=df.loc[df.StrategyNo.eq(n)&df.EntryTime.ge(start)&df.EntryTime.lt(end),'R']
            gain=rs[rs>0].sum();loss=-rs[rs<0].sum()
            d=dict(Trades=len(rs),AvgR=rs.mean(),PF=gain/loss if loss else np.inf if gain else np.nan,TotalR=rs.sum());m[n,p]=d
            for k,v in d.items():assert np.isclose(v,actual[p+'_'+k],atol=1e-10,rtol=1e-10,equal_nan=True),(n,p,k)
        h=m[n,'Historical'];c=m[n,'RecentCombined']
        ratio=c['AvgR']/h['AvgR'] if h['AvgR']>0 else np.nan
        assert np.isclose(ratio,actual.RecentToHistoricalAvgR,atol=1e-10,rtol=1e-10,equal_nan=True)
    for _,r in cl.iterrows():
        h,a,b,c=[m[r.StrategyNo,p] for p in ['Historical','RecentA','RecentB','RecentCombined']]
        short=c['Trades']<r.CombinedMinTrades or min(a['Trades'],b['Trades'])<r.ABMinTrades
        persistent=max(a['AvgR'],b['AvgR'])<h['AvgR']
        lost=h['AvgR']>0 and h['PF']>r.HistoricalPFThreshold and c['AvgR']<=0 and c['PF']<=1 and persistent
        decay=c['AvgR']<=h['AvgR']*r.DecayRatioThreshold and c['PF']<h['PF'] and persistent
        expected='INSUFFICIENT SAMPLE' if short else 'EDGE LOST' if lost else 'EDGE DECAY' if decay else 'STABLE'
        assert expected==r.Classification,(r.Strategy,r.UniqueSetting)
    for _,r in su.iterrows():
        own=cl.loc[cl.StrategyNo.eq(r.StrategyNo)];unique=own.drop_duplicates('UniqueSetting')
        assert len(own)==9 and len(unique)==7
        assert own.groupby('UniqueSetting').Classification.nunique().max()==1
        assert len(own[['Axis','Point']].drop_duplicates())==9
        wc=unique.Classification.isin(['EDGE LOST','EDGE DECAY']).sum()
        assert wc==r.WarningCountUnique and np.isclose(wc/7,r.WarningRateUnique)
        assert own.Classification.isin(['EDGE LOST','EDGE DECAY']).sum()==r.WarningCountDisplayed
        assert np.isclose(r.WarningCountDisplayed/9,r.WarningRateDisplayed)
        assert (unique.Classification=='INSUFFICIENT SAMPLE').sum()==r.InsufficientCountUnique
        assert (unique.Classification==r.PrimaryClassification).sum()==r.PrimaryMatchCountUnique
        for axis in ['PF','RATIO','SAMPLE']:
            assert own.loc[own.Axis.eq(axis)].Classification.isin(['EDGE LOST','EDGE DECAY']).sum()==r[axis+'_WarningCount']
        for _,u in unique.iterrows():assert r[u.UniqueSetting]==u.Classification
        expected_label='NA (non-candidate)' if r.PrimaryClassification not in ['EDGE LOST','EDGE DECAY'] else '頑健' if wc==7 else '中程度' if wc>=5 else '不安定'
        assert r.WarningRetentionLabel==expected_label
    record=pd.read_csv(out/'edge_decay_sensitivity_run_record.csv').iloc[0]
    for filename,digest in json.loads(record.CSVHashes).items():assert hashlib.sha256((out/filename).read_bytes()).hexdigest()==digest
    assert cl.loc[cl.UniqueSetting.eq('OFFICIAL')].groupby('StrategyNo').Classification.first().value_counts().to_dict()=={'STABLE':21,'INSUFFICIENT SAMPLE':3,'EDGE LOST':2,'EDGE DECAY':2}
    assert {p:sum(m[n,p]['Trades'] for n in range(1,29)) for p in ['Historical','RecentCombined','Monitor2026']}=={'Historical':9756,'RecentCombined':5547,'Monitor2026':995}
    print('PASS: independent 140 period metrics, 252 displayed / 196 unique classifications, 28 ratios and summaries, CSV hashes')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args();verify(a.baseline,a.output_dir)
