"""Independent v2 primary/sensitivity and M1 verification; no C2 replay imports."""
import argparse
import csv
import hashlib
import math
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from daily_stop_baseline_revalidation import PIP_SIZE, SPREAD_PIPS, SYMBOL_TO_PAIR, load_pair
from exit_efficiency_phase1 import BASELINE_SHA, PERIODS, write

PREFIX='c2_no_progress_phase1_'


def main():
    ap=argparse.ArgumentParser()
    for k in ('out','baseline','m1-root','manifest'): ap.add_argument('--'+k,required=True)
    a=ap.parse_args(); out=Path(a.out)
    def read(name): return list(csv.DictReader((out/(PREFIX+name+'.csv')).open()))
    checks=[]
    def check(name,condition,detail=''):
        checks.append(dict(Check=name,Status='PASS' if condition else 'FAIL',Detail=detail))
    def eq(x,y): return math.isclose(float(x),float(y),rel_tol=0,abs_tol=1e-8)
    full=read('trade_detail_local'); rows=[r for r in full if r['Formal']=='True']
    anchors=list(csv.DictReader(Path(a.baseline).open()))
    check('baseline_hash',hashlib.sha256(Path(a.baseline).read_bytes()).hexdigest()==BASELINE_SHA)
    check('reference_and_formal_counts',len(full)==32596 and len(rows)==31674)
    check('universe',set(int(r['StrategyNo']) for r in rows)==set(range(1,29))-{22})
    check('pair_uniqueness',len({(r['StrategyNo'],r['EntryTime'],r['Variant']) for r in full})==len(full))
    base={(r['StrategyNo'],r['EntryTime']):r for r in anchors}
    check('r0_matches_anchor',all(eq(r['R0R'],base[r['StrategyNo'],r['EntryTime']]['R']) and r['R0CloseTime']==base[r['StrategyNo'],r['EntryTime']]['CloseTime'] and r['R0ExitReason']==base[r['StrategyNo'],r['EntryTime']]['ExitReason'] for r in full))
    check('every_paired_delta',all(eq(r['DeltaR'],float(r['NPR'])-float(r['R0R'])) for r in full))
    check('untriggered_unchanged',all(r['NPR']==r['R0R'] and r['NPCloseTime']==r['R0CloseTime'] and r['NPExitReason']==r['R0ExitReason'] for r in full if r['Triggered']=='False'))
    check('trigger_classification',all((r['Triggered']=='True')==(r['Assessment']=='NO_PROGRESS_EXIT')==(r['NPExitReason'] in ('NP50','NP75')) for r in full))
    def flags(r):
        v=float(r['R0R']); why=r['R0ExitReason']
        return dict(RECOVERED_POSITIVE=v>0,RECOVERED_HALF_R=v>=.5,NEVER_RECOVERED=v<=0,
                    LATER_HIT_TP=why=='TP',LATER_HIT_SL=why=='SL',TIME_EXIT_POSITIVE=why=='TimeExit' and v>0,
                    TIME_EXIT_NEGATIVE=why=='TimeExit' and v<0,TIME_EXIT_ZERO=why=='TimeExit' and v==0)
    check('all_recovery_flags',all(r['Recovery_'+k]==str(v) for r in full if r['Triggered']=='True' for k,v in flags(r).items()))
    missing=[r for r in full if r['Assessment']=='MISSING_EXECUTION_KEEP_BASELINE']
    excluded={(r['StrategyNo'],r['EntryTime']) for r in missing}
    check('known_missing_identity', {(r['StrategyNo'],r['EntryTime'],r['Variant']) for r in missing}=={
        ('19','2021-06-17 20:56:00','NP50'),('20','2025-01-07 10:01:00','NP50')})
    check('missing_full_baseline_and_zero_delta', all(r['Triggered']=='False' and eq(r['DeltaR'],0) and
        r['R0R']==r['NPR'] and r['R0CloseTime']==r['NPCloseTime'] and r['R0ClosePrice']==r['NPClosePrice'] and
        r['R0ExitReason']==r['NPExitReason'] for r in missing))
    for p in read('period_summary')+read('sensitivity_period_summary'):
        lo,hi=PERIODS[p['Period']]
        rr=[r for r in rows if r['Variant']==p['Variant'] and lo<=r['EntryTime'][:10]<hi]
        if p.get('Analysis')=='EXCLUDE_BOTH_SIDES_DESCRIPTIVE_ONLY':
            rr=[r for r in rr if (r['StrategyNo'],r['EntryTime']) not in excluded]
        trigger=[r for r in rr if r['Triggered']=='True']
        scope='sensitivity_' if p.get('Analysis') else 'primary_'
        check(scope+'totals_'+p['Variant']+'_'+p['Period'],len(rr)==int(p['Trades']) and len(trigger)==int(p['TriggerCount']) and
              eq(sum(float(r['R0R']) for r in rr),p['R0TotalR']) and eq(sum(float(r['NPR']) for r in rr),p['NPTotalR']) and
              eq(sum(float(r['DeltaR']) for r in rr),p['DeltaTotalR']))
        weekly=defaultdict(list)
        for r in rr: weekly[r['Week']].append(float(r['DeltaR']))
        blocks=[weekly[k] for k in sorted(weekly)]; n=len(blocks)
        totals=np.array([math.fsum(b) for b in blocks]); counts=np.array([len(b) for b in blocks])
        rng=np.random.Generator(np.random.PCG64(20260913)); dist=[]
        for _ in range(5000):
            draw=rng.integers(n,size=n)
            dist.append(math.fsum(totals[draw])/sum(counts[draw]))
        bounds=np.quantile(dist,[.025,.975])
        check(scope+'bootstrap_'+p['Variant']+'_'+p['Period'],eq(bounds[0],p['CILower']) and eq(bounds[1],p['CIUpper']))
        for tag,value,timekey in [('R0','R0R','R0CloseTime'),('NP','NPR','NPCloseTime')]:
            day=defaultdict(float); wk=defaultdict(float)
            balance=peak=dd=0.
            for r in sorted(rr,key=lambda r:(r[timekey],int(r['StrategyNo']),r['EntryTime'])):
                v=float(r[value]); day[r['EntryTime'][:10]]+=v; wk[r['Week']]+=v
                balance+=v; peak=max(peak,balance); dd=max(dd,peak-balance)
            check(scope+'safety_metrics_'+tag+'_'+p['Variant']+'_'+p['Period'],eq(min(day.values()),p[tag+'WorstDayR']) and eq(min(wk.values()),p[tag+'WorstWeekR']) and eq(dd,p[tag+'MaxDDR']))
    for rec in read('recovery_summary'):
        lo,hi=PERIODS[rec['Period']]
        selected=[r for r in rows if r['Variant']==rec['Variant'] and lo<=r['EntryTime'][:10]<hi and r['Triggered']=='True']
        assert int(rec['Count'])==sum(flags(r)[rec['Category']] for r in selected)
    check('recovery_aggregate_counts',True)
    ps={(p['Variant'],p['Period']):p for p in read('period_summary')}
    primary=ps['NP50','ALL']
    recent=[ps['NP50',k] for k in ('Recent A','Recent B','2026 Monitor')]
    expected_gates=dict(A=float(primary['DeltaTotalR'])>0,B=float(primary['CILower'])>0,
        C=float(ps['NP50','Historical']['DeltaTotalR'])>=0,
        D=float(ps['NP50','Recent Combined']['DeltaTotalR'])>0,
        E=sum(int(p['TriggerCount'])>=30 and int(p['TriggerWeeks'])>=20 and float(p['DeltaTotalR'])>0 for p in recent)>=2,
        F=all(float(ps['NP75',k]['DeltaTotalR'])>=0 for k in ('ALL','Recent Combined')),
        G=int(primary['TriggerCount'])>=200 and int(primary['TriggerWeeks'])>=100,
        H=all((float(p['NP'+m]) if m=='MaxDDR' else max(0,-float(p['NP'+m])))<=
              1.1*(float(p['R0'+m]) if m=='MaxDDR' else max(0,-float(p['R0'+m])))+1e-9
              for (v,_),p in ps.items() if v=='NP50' for m in ('WorstDayR','WorstWeekR','MaxDDR')))
    check('formal_gates_independent',all(str(expected_gates[g['Gate']])==g['Pass'] for g in read('formal_gates')))
    check('phase2_eligibility',read('run_record')[0]['Phase2Eligible']==str(all(expected_gates.values())))

    sens={(p['Variant'],p['Period']):p for p in read('sensitivity_period_summary')}
    all_s=sens['NP50','ALL']; recent_s=[sens['NP50',k] for k in ('Recent A','Recent B','2026 Monitor')]
    sg=dict(A=float(all_s['DeltaTotalR'])>0,B=float(all_s['CILower'])>0,
        C=float(sens['NP50','Historical']['DeltaTotalR'])>=0,D=float(sens['NP50','Recent Combined']['DeltaTotalR'])>0,
        E=sum(int(p['TriggerCount'])>=30 and int(p['TriggerWeeks'])>=20 and float(p['DeltaTotalR'])>0 for p in recent_s)>=2,
        F=all(float(sens['NP75',k]['DeltaTotalR'])>=0 for k in ('ALL','Recent Combined')),
        G=int(all_s['TriggerCount'])>=200 and int(all_s['TriggerWeeks'])>=100,
        H=all((float(p['NP'+m]) if m=='MaxDDR' else max(0,-float(p['NP'+m])))<=
              1.1*(float(p['R0'+m]) if m=='MaxDDR' else max(0,-float(p['R0'+m])))+1e-9
              for (v,_),p in sens.items() if v=='NP50' for m in ('WorstDayR','WorstWeekR','MaxDDR')))
    check('sensitivity_gates',all(str(sg[g['Gate']])==g['Pass'] for g in read('sensitivity_gates')))
    def label(g):
        if not g['G']: return 'INSUFFICIENT_TRIGGER_SAMPLE'
        if all(g.values()): return 'NO_PROGRESS_EXIT_CANDIDATE'
        if not g['A'] or not g['B']: return 'NOT_SUPPORTED'
        if not all(g[k] for k in 'CDE'): return 'UNSTABLE_ACROSS_PERIODS'
        if not g['F']: return 'ROBUSTNESS_FAIL'
        return 'SAFETY_FAIL'
    record=read('run_record')[0]
    check('primary_verdict',record['Verdict']==label(expected_gates))
    check('sensitivity_verdict',record['SensitivityVerdict']==label(sg))
    check('sensitivity_universe',all(int(sens[v,'ALL']['Trades'])==15835 for v in ('NP50','NP75')))

    manifest=list(csv.DictReader(Path(a.manifest).open())); found=defaultdict(list)
    wanted={x['Filename'] for x in manifest}
    for p in Path(a.m1_root).rglob('*.csv'):
        if p.name in wanted: found[p.name].append(p)
    assert set(found)==wanted and all(len(v)==1 for v in found.values())
    check('independent_m1_hashes',all(hashlib.file_digest(found[r['Filename']][0].open('rb'),'sha256').hexdigest()==r['SHA256'] for r in manifest), '56 files')
    paths=defaultdict(list)
    for r in manifest: paths[r['Symbol']].append(found[r['Filename']][0])
    # Deterministic representatives of every strategy, variant and assessment;
    # include every delayed checkpoint, and both directions where available.
    selected={}; groups=defaultdict(list)
    for r in full: groups[r['StrategyNo'],r['Variant'],r['Assessment']].append(r)
    for group in groups.values():
        for r in (group[0],group[-1]): selected[r['StrategyNo'],r['EntryTime'],r['Variant']]=r
    for r in full:
        if r['CheckpointDelay'] and int(r['CheckpointDelay'])>0: selected[r['StrategyNo'],r['EntryTime'],r['Variant']]=r
    manual=[]
    for symbol,pair in SYMBOL_TO_PAIR.items():
        data=load_pair(paths[symbol],symbol)
        for r in selected.values():
            if r['Pair']!=pair: continue
            anchor=base[r['StrategyNo'],r['EntryTime']]
            e=datetime.fromisoformat(r['EntryTime']); s=datetime.fromisoformat(r['ScheduledExitTime'])
            minutes=(s-e).total_seconds()/60
            cp=e+timedelta(minutes=int(minutes*(.5 if r['Variant']=='NP50' else .75)))
            assert str(cp)==r['CheckpointTime']
            sign=1 if r['Direction']=='Long' else -1
            fill=float(data.loc[e,'Open'])+sign*SPREAD_PIPS[pair]*PIP_SIZE[pair]
            unit=float(r['SL'])*PIP_SIZE[pair]
            prior=data.loc[e:cp-timedelta(minutes=1)]
            if datetime.fromisoformat(r['R0CloseTime'])<cp:
                triggered=False; mf=None; assessment='CLOSED_BEFORE_CHECKPOINT'; price=float(r['R0ClosePrice']); exit_time=r['R0CloseTime']
            else:
                extreme=float(prior.High.max() if sign==1 else prior.Low.min())
                mf=max(0.,sign*(extreme-fill)/unit)
                assert eq(mf,r['CheckpointMFE_R'])
                reached=extreme>=fill+unit/4 if sign==1 else extreme<=fill-unit/4
                candidates=[cp+timedelta(minutes=i) for i in range(5) if cp+timedelta(minutes=i) in data.index]
                actual=candidates[0] if candidates else None
                triggered=not reached and actual is not None and datetime.fromisoformat(r['R0CloseTime'])>=actual
                assessment='PROGRESS_REACHED' if reached else ('MISSING_EXECUTION_KEEP_BASELINE' if actual is None else ('NO_PROGRESS_EXIT' if triggered else 'CLOSED_BEFORE_EXECUTION'))
                price=float(data.loc[actual,'Open']) if triggered else float(r['R0ClosePrice'])
                exit_time=str(actual) if triggered else r['R0CloseTime']
            expected=round(sign*(price-fill)/unit,9) if triggered else float(r['R0R'])
            ok=eq(expected,r['NPR']) and str(triggered)==r['Triggered'] and assessment==r['Assessment'] and exit_time==r['NPCloseTime'] and eq(fill,r['EntryPrice'])
            manual.append(dict(StrategyNo=r['StrategyNo'],EntryTime=r['EntryTime'],Variant=r['Variant'],Direction=r['Direction'],
                               Checkpoint=str(cp),IndependentMFE=mf,IndependentR=expected,Status='PASS' if ok else 'FAIL'))
        del data
    check('representative_m1_replay',all(r['Status']=='PASS' for r in manual),str(len(manual))+' representatives')
    write(out/(PREFIX+'manual_audit.csv'),manual)
    write(out/(PREFIX+'independent_verification.csv'),checks)
    failed=[c for c in checks if c['Status']!='PASS']
    print(f'{len(checks)-len(failed)}/{len(checks)} independent checks PASS; {len(manual)} representative trades')
    if failed: raise AssertionError(failed)


if __name__=='__main__': main()
