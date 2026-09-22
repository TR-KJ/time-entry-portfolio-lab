"""Independent post-run checks against original CSV and published aggregate tables."""
import argparse,csv,hashlib,json,math,sys
from collections import defaultdict,Counter
from datetime import date,timedelta
from decimal import Decimal
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from component_edge_decay_phase1 import BASELINE_SHA,COMPONENTS,NAMES,nominal_gotobi,holm,PERIODS

def read(path): return list(csv.DictReader(open(path,newline='',encoding='utf-8')))
def close(a,b): return math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-9)
def verify(baseline,out):
    raw=Path(baseline).read_bytes();assert hashlib.sha256(raw).hexdigest()==BASELINE_SHA
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()));assert len(rows)==16298
    source=defaultdict(list);excluded=Counter()
    for r in rows:
        n=int(r['StrategyNo'])
        if n not in COMPONENTS: continue
        assert r['Strategy']==NAMES[n]
        d=date.fromisoformat(r['EntryTime'][:10]);wd=('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[d.weekday()]
        if n==12:
            if r['Mode']=='NORMAL': excluded[n]+=1;continue
            assert r['Mode']=='GOTO';c=nominal_gotobi(d);assert c is not None
        else:c=wd
        assert c in COMPONENTS[n]
        source[(n,c)].append(r)
    coverage=read(Path(out)/'component_edge_decay_phase1_coverage.csv')
    for item in coverage:
        n=int(item['StrategyNo']);assert int(item['Eligible'])==sum(len(source[(n,c)]) for c in COMPONENTS[n]);assert int(item['ExcludedNormal'])==excluded[n]
    checked=0
    for item in read(Path(out)/'component_edge_decay_phase1_component_period_summary.csv'):
        n=int(item['StrategyNo']);c=item['Component'];p=item['Period'];a,z=PERIODS[p]
        group=[r for r in source[(n,c)] if a<=r['EntryTime'][:10]<z]
        vals=[Decimal(r['R']) for r in group];total=sum(vals,Decimal(0));positive=sum((v for v in vals if v>0),Decimal(0));negative=-sum((v for v in vals if v<0),Decimal(0))
        assert int(item['Trades'])==len(group)
        assert close(item['TotalR'],total)
        if group: assert close(item['AvgR'],total/len(group))
        if negative: assert close(item['PF'],positive/negative)
        checked+=1
    contrasts=read(Path(out)/'component_edge_decay_phase1_contrasts.csv');assert len(contrasts)==23
    ps=[float(x['RawP']) for x in contrasts];adjusted=holm(ps)
    for x,p in zip(contrasts,adjusted):assert close(x['AdjustedP'],p)
    audit=[]
    for n in COMPONENTS:
        for c in COMPONENTS[n]:
            group=sorted(source[(n,c)],key=lambda r:r['EntryTime'])
            assert group
            audit.extend((dict(StrategyNo=n,Component=c,Position=position,EntryTime=r['EntryTime'],Mode=r['Mode']) for position,r in [('earliest',group[0]),('latest',group[-1])]))
    result=dict(BaselineSHA256=BASELINE_SHA,Rows=len(rows),TargetStrategies=len(COMPONENTS),FormalComponents=len(contrasts),PeriodCellsChecked=checked,HolmChecked=len(contrasts),RepresentativeTrades=audit)
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--baseline',required=True);a.add_argument('--out',required=True);v=a.parse_args();verify(v.baseline,v.out)
