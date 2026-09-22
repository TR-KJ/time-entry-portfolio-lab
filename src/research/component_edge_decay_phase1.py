"""Preregistered A1 diagnosis. Reads only the frozen baseline; never backtests."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
from pathlib import Path
import numpy as np

BASELINE_SHA = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
PLAN_SHA = '51b31242826a338c86c0f99ecb8d608005af862c'
SEED = 20260913
B = 5000
BRANCH = 'research/component-edge-decay-phase1'
COMPONENTS = {1:('Mon','Wed'),2:('Mon','Wed'),3:('Mon','Wed'),4:('Tue','Wed'),5:('Tue','Thu','Fri'),12:('20','25','30'),13:('Wed','Thu'),18:('Mon','Tue','Wed'),19:('Wed','Thu'),20:('Mon','Tue')}
NAMES = {1:'1_EJ_Log1',2:'2_EJ_NightBlitz_20',3:'3_EJ_NightBlitz_21',4:'4_GJ_Port_Log1',5:'5_GJ_Port_Log2',12:'12_UJ_Short_Core',13:'13_UJ_Fix_MidWeek',18:'18_EA_2_MonWed_Short',19:'19_EA_3_WedThu_Long',20:'20_EA_1A_MonTue_Short'}
PERIODS = {'Historical':('2015-01-01','2022-01-01'),'Recent A':('2022-01-01','2024-01-01'),'Recent B':('2024-01-01','2026-01-01'),'2026 Monitor':('2026-01-01','2026-09-10'),'Recent Combined':('2022-01-01','2026-09-10'),'ALL':('2015-01-01','2026-09-10')}
WEEKDAYS = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')

def nominal_gotobi(day):
    if day.day in (20,25,30): return str(day.day)
    if day.weekday()==4:
        for offset in (1,2):
            future=day+timedelta(days=offset)
            if future.day in (25,30) and future.weekday() in (5,6): return str(future.day)
    return None

def period(day,label):
    a,z=PERIODS[label]; return a<=day.isoformat()<z

def week(day): return (day-timedelta(days=day.weekday())).isoformat()

def load_baseline(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=BASELINE_SHA: raise ValueError('baseline hash mismatch')
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    if len(rows)!=16298: raise ValueError('baseline count mismatch')
    identities={(int(r['StrategyNo']),r['Strategy']) for r in rows}
    if len(identities)!=28 or {n for n,_ in identities}!=set(range(1,29)): raise ValueError('baseline identities mismatch')
    if len({(r['StrategyNo'],r['EntryTime']) for r in rows})!=len(rows): raise ValueError('duplicate trade identity')
    for r in rows:
        r['No']=int(r['StrategyNo']); t=datetime.fromisoformat(r['EntryTime'])
        if t.tzinfo is not None: raise ValueError('expected naive JST')
        r['Day']=t.date(); r['Week']=week(r['Day']); r['Rfloat']=float(r['R'])
        if not np.isfinite(r['Rfloat']) or abs(r['Rfloat']-float(r['Pips'])/float(r['SL']))>1e-8: raise ValueError('invalid R')
        if not period(r['Day'],'ALL'): raise ValueError('outside coverage')
    return rows

def assign(r):
    n=r['No']; day=r['Day']
    if n not in COMPONENTS: return None
    if r['Strategy']!=NAMES[n]: raise ValueError('strategy name mismatch')
    if n==12:
        if r['Mode']=='NORMAL':
            if nominal_gotobi(day) is not None: raise ValueError('NORMAL on gotobi day')
            return None
        if r['Mode']!='GOTO': raise ValueError('unknown UJ12 mode')
        c=nominal_gotobi(day)
        if not c or r['EntryTime'][11:16]!='09:55' or float(r['SL'])!=20 or float(r['TP'])!=50: raise ValueError('invalid UJ12 GOTO')
    else: c=WEEKDAYS[day.weekday()]
    if c not in COMPONENTS[n]: raise ValueError('unmatched component')
    return c

def metrics(rows):
    rs=np.array([r['Rfloat'] for r in rows],dtype=float); n=len(rs)
    gain=float(rs[rs>0].sum()); loss=float(-rs[rs<0].sum())
    return dict(Trades=n,Weeks=len({r['Week'] for r in rows}),TotalR=float(rs.sum()),AvgR=float(rs.mean()) if n else None,PF=gain/loss if loss else (float('inf') if gain else None),WinRate=float(np.count_nonzero(rs>0)/n) if n else None,AvgWinR=float(rs[rs>0].mean()) if gain else None,AvgLossR=float(rs[rs<0].mean()) if loss else None)

def bootstrap_strategy(rows,components):
    byperiod={p:defaultdict(list) for p in ('Historical','Recent Combined')}
    for r in rows:
        for p in byperiod:
            if period(r['Day'],p): byperiod[p][r['Week']].append(r)
    arrays={}
    for p,clusters in byperiod.items():
        keys=sorted(clusters); sums=np.zeros((len(keys),len(components))); counts=np.zeros_like(sums)
        for i,k in enumerate(keys):
            for r in clusters[k]:
                j=components.index(r['Component']); sums[i,j]+=r['Rfloat']; counts[i,j]+=1
        arrays[p]=(sums,counts)
    rng=np.random.Generator(np.random.PCG64(SEED)); sampled={}
    for p,(sums,counts) in arrays.items():
        draws=rng.integers(0,len(sums),size=(B,len(sums)))
        sampled[p]=(sums[draws].sum(axis=1),counts[draws].sum(axis=1))
    output={}
    for j,c in enumerate(components):
        with np.errstate(divide='ignore',invalid='ignore'):
            h_s,h_n=sampled['Historical']; q_s,q_n=sampled['Recent Combined']
            cd=q_s[:,j]/q_n[:,j]-h_s[:,j]/h_n[:,j]
            sd=(q_s.sum(axis=1)-q_s[:,j])/(q_n.sum(axis=1)-q_n[:,j])-(h_s.sum(axis=1)-h_s[:,j])/(h_n.sum(axis=1)-h_n[:,j])
            rd=cd-sd
        output[c]=(cd,rd)
    return output

def holm(pvals):
    order=sorted(range(len(pvals)),key=lambda i:(pvals[i],i)); adjusted=[None]*len(pvals); running=0
    for rank,i in enumerate(order):
        running=max(running,min(1,(len(pvals)-rank)*pvals[i])); adjusted[i]=running
    return adjusted

def analyze(rows):
    targets=defaultdict(list); excluded=Counter()
    for r in rows:
        if r['No'] not in COMPONENTS: continue
        c=assign(r)
        if c is None: excluded[r['No']]+=1; continue
        r['Component']=c; targets[r['No']].append(r)
    summary=[]; yearly=[]; contrasts=[]; coverage=[]; boot={}; keys=[]
    for n,cs in COMPONENTS.items():
        own=targets[n]
        coverage.append(dict(StrategyNo=n,Strategy=NAMES[n],TotalBaseline=sum(r['No']==n for r in rows),Eligible=len(own),ExcludedNormal=excluded[n],ComponentCounts=json.dumps(dict(Counter(r['Component'] for r in own)),sort_keys=True)))
        if not own: raise ValueError('no eligible rows')
        boot[n]=bootstrap_strategy(own,cs)
        for c in cs:
            subset=[r for r in own if r['Component']==c]; keys.append((n,c))
            for p in PERIODS:
                summary.append(dict(StrategyNo=n,Strategy=NAMES[n],Component=c,Period=p,**metrics([r for r in subset if period(r['Day'],p)])))
            for year in range(2015,2027):
                yearly.append(dict(StrategyNo=n,Strategy=NAMES[n],Component=c,Year=year,**metrics([r for r in subset if r['Day'].year==year])))
            h=metrics([r for r in subset if period(r['Day'],'Historical')]);q=metrics([r for r in subset if period(r['Day'],'Recent Combined')])
            sib=[r for r in own if r['Component']!=c];sh=metrics([r for r in sib if period(r['Day'],'Historical')]);sq=metrics([r for r in sib if period(r['Day'],'Recent Combined')])
            cd=q['AvgR']-h['AvgR'] if q['AvgR'] is not None and h['AvgR'] is not None else None
            sd=sq['AvgR']-sh['AvgR'] if sq['AvgR'] is not None and sh['AvgR'] is not None else None
            rd=cd-sd if cd is not None and sd is not None else None
            sufficient=all(m['Trades']>=30 and m['Weeks']>=20 for m in (h,q,sh,sq))
            bc,br=boot[n][c]; valid=bool(np.isfinite(bc).all() and np.isfinite(br).all())
            ci_c=np.quantile(bc,[.025,.975],method='linear') if valid and sufficient else (None,None)
            ci_r=np.quantile(br,[.025,.975],method='linear') if valid and sufficient else (None,None)
            pval=(1+int(np.count_nonzero(br>=0)))/(B+1) if valid and sufficient else 1.0
            contrasts.append(dict(StrategyNo=n,Strategy=NAMES[n],Component=c,HistoricalAvgR=h['AvgR'],RecentCombinedAvgR=q['AvgR'],ComponentDecay=cd,ComponentCI_L=ci_c[0],ComponentCI_U=ci_c[1],SiblingDecay=sd,RelativeDecay=rd,RelativeCI_L=ci_r[0],RelativeCI_U=ci_r[1],RawP=pval,SampleSufficient=sufficient,BootstrapValid=valid,HistoricalTrades=h['Trades'],HistoricalWeeks=h['Weeks'],RecentTrades=q['Trades'],RecentWeeks=q['Weeks'],SiblingHistoricalTrades=sh['Trades'],SiblingHistoricalWeeks=sh['Weeks'],SiblingRecentTrades=sq['Trades'],SiblingRecentWeeks=sq['Weeks']))
    adj=holm([x['RawP'] for x in contrasts]);multiple=[]
    for x,padj in zip(contrasts,adj):
        tests={'A':x['HistoricalAvgR'] is not None and x['HistoricalAvgR']>0,'B':x['RecentCombinedAvgR'] is not None and x['RecentCombinedAvgR']<0,'C':x['ComponentDecay'] is not None and x['ComponentDecay']<0,'D':x['ComponentCI_U'] is not None and x['ComponentCI_U']<0,'E':x['RelativeDecay'] is not None and x['RelativeDecay']<0,'F':padj<.05,'G':x['SampleSufficient'] and x['BootstrapValid']}
        x['AdjustedP']=padj
        for k,v in tests.items(): x[k]='PASS' if v else 'FAIL'
        if all(tests.values()): verdict='COMPONENT_DECAY_CANDIDATE'
        elif not tests['G']: verdict='INSUFFICIENT_SAMPLE'
        elif x['RecentCombinedAvgR'] is not None and x['RecentCombinedAvgR']>0 and tests['C']: verdict='WEAKENED_BUT_STILL_POSITIVE'
        elif tests['C'] and tests['E']: verdict='WEAK_DECAY_SIGNAL'
        else: verdict='NOT_SUPPORTED'
        x['Verdict']=verdict
        multiple.append(dict(StrategyNo=x['StrategyNo'],Component=x['Component'],RawP=x['RawP'],AdjustedP=padj,HolmFamilySize=len(contrasts),HolmPass=tests['F']))
    if len(contrasts)!=23: raise ValueError('formal family mismatch')
    return dict(component_period_summary=summary,contrasts=contrasts,yearly_summary=yearly,multiple_comparison=multiple,coverage=coverage)

def write_csv(path,records):
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)

def run(baseline,out,implementation_sha='UNCOMMITTED'):
    rows=load_baseline(baseline); tables=analyze(rows);out=Path(out);out.mkdir(parents=True,exist_ok=True);hashes={}
    for name,records in tables.items():
        p=out/f'component_edge_decay_phase1_{name}.csv';write_csv(p,records);hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    record=[dict(Branch=BRANCH,PlanSHA=PLAN_SHA,ImplementationSHA=implementation_sha,BaselineSHA256=BASELINE_SHA,BaselineTrades=len(rows),BaselineStrategies=28,TargetStrategies=10,FormalComponents=23,BootstrapReplicates=B,Seed=SEED,Python=__import__('sys').version.split()[0],Numpy=np.__version__,FreshHoldout=False,BaselineRecalculated=False,PortfolioSimulated=False,DriveSaveDefault=False)]
    p=out/'component_edge_decay_phase1_run_record.csv';write_csv(p,record);hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    print(json.dumps({'coverage':tables['coverage'],'candidates':[dict(StrategyNo=x['StrategyNo'],Component=x['Component']) for x in tables['contrasts'] if x['Verdict']=='COMPONENT_DECAY_CANDIDATE'],'hashes':hashes},ensure_ascii=False,indent=2))
    return tables

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--out',default='/content');ap.add_argument('--implementation-sha',default='UNCOMMITTED');a=ap.parse_args();run(a.baseline,a.out,a.implementation_sha)
