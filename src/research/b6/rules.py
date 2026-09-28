"""Approved Stage1 selection helpers; later-stage grid helpers only (no execution)."""
from statistics import median
from math import isfinite
from .stage0 import round5

def structure_count(config):
    h=config['holding_minutes']
    return len(config['symbols'])*2*5*len(range(0,1440,config['entry_step_minutes']))*len(range(h['min'],h['max']+1,h['step']))

def single_pass(m):
    return (m['N']>=150 and all(m['annual_N'].get(y,0)>=30 for y in range(2020,2024))
            and m['losses']>=10 and isfinite(m['PF']) and m['PF']>=1.1 and m['AvgR']>0
            and sum(m['annual_TotalR'].get(y,0)>0 for y in range(2020,2024))>=3)

def rank_key(c):
    values=c['sl_metrics']
    if len(values)!=5:raise ValueError('five SL results required')
    if any(not isfinite(m[k]) for m in values for k in ('AvgR','TotalR','MaxDDR')):raise ValueError('nonfinite metric')
    return (-median(m['AvgR'] for m in values),-sum(single_pass(m) for m in values),
            -median(m['TotalR'] for m in values),max(m['MaxDDR'] for m in values),
            c['symbol'],0 if c['direction']=='L' else 1,c['weekday'],c['entry'],(c['entry']+c['hold'])//1440,(c['entry']+c['hold'])%1440)

def circular(a,b):return min(abs(a-b),1440-abs(a-b))

def near(a,b):
    xa=a['entry']+a['hold'];xb=b['entry']+b['hold']
    return (all(a[k]==b[k] for k in ('symbol','direction','weekday')) and xa//1440==xb//1440
            and circular(a['entry'],b['entry'])<=30 and circular(xa%1440,xb%1440)<=30 and abs(a['hold']-b['hold'])<=30)

def shortlist(candidates,limit=50):
    ids=[c['id'] for c in candidates]
    if len(set(ids))!=len(ids):raise ValueError('duplicate candidate id')
    eligible=sorted((c for c in candidates if sum(single_pass(m) for m in c['sl_metrics'])>=3),key=rank_key)
    selected=[];assignment={}
    for c in eligible:
        rep=next((r for r in selected if near(c,r)),None)
        if rep is not None:assignment[c['id']]=rep['id']
        elif len(selected)<limit:selected.append(c);assignment[c['id']]=c['id']
        else:assignment[c['id']]='OUTSIDE_TOP50'
    return selected,assignment

def tp_grid(sl):return [None]+sorted({max(5,round5(sl*m)) for m in (.5,1,1.5,2,3)})

def local_grid(sl,tp):
    ss=[s for s in range(sl-10,sl+11,5) if 10<=s<=300]
    tt=[None] if tp is None else [t for t in range(tp-10,tp+11,5) if 5<=t<=900]
    return [(s,t) for s in ss for t in tt]

def time_grid(entry,hold):
    return [(e,x-e) for e in range(max(0,entry-5),min(1439,entry+5)+1)
            for x in range(entry+hold-5,entry+hold+6) if 30<=x-e<=1440]
