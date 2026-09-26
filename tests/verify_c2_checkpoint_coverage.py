"""Post-run independent diagnosis of the frozen execution-coverage stop.

No C2 replay imports, result estimation, exclusions, or replacement fills.
"""
import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'research'))
from exit_efficiency_phase1 import BASELINE_SHA, write

PREFIX='c2_no_progress_phase1_'


def main():
    parser=argparse.ArgumentParser()
    for k in ('baseline','manifest','m1-root','out'): parser.add_argument('--'+k,required=True)
    args=parser.parse_args(); out=Path(args.out)
    baseline=Path(args.baseline)
    assert hashlib.sha256(baseline.read_bytes()).hexdigest()==BASELINE_SHA
    anchors={(r['StrategyNo'],r['EntryTime']):r for r in csv.DictReader(baseline.open())}
    missing=list(csv.DictReader((out/(PREFIX+'missing_checkpoint_local.csv')).open()))
    audit=list(csv.DictReader((out/(PREFIX+'m1_audit.csv')).open()))
    manifest=list(csv.DictReader(Path(args.manifest).open()))
    checks=[dict(Check='baseline_hash',Status='PASS',Detail=BASELINE_SHA)]
    assert len(audit)==len(manifest)==56
    for actual,expected in zip(audit,manifest):
        assert actual['Status']=='PASS'
        assert all(actual[k]==expected[k] for k in ('Symbol','Filename','SHA256','Rows','FirstRaw','LastRaw'))
    checks.append(dict(Check='56_source_audit_records',Status='PASS',Detail='Hashes, row counts and raw bounds match frozen manifest'))
    recon=list(csv.DictReader((out/(PREFIX+'r0_reconciliation.csv')).open()))
    assert [r['AnchorTrades'] for r in recon]==['16298','15837']
    assert all(r['Status']=='PASS' and r['MismatchCount']=='0' for r in recon)
    checks.append(dict(Check='r0_reconciliation_records',Status='PASS',Detail='ALL28 and ACTIVE27 zero mismatches'))
    details=[]
    for m in missing:
        a=anchors[m['StrategyNo'],m['EntryTime']]
        assert a['Pair']=='EA' and m['Variant']=='NP50'
        entry=datetime.fromisoformat(a['EntryTime']); scheduled=datetime.fromisoformat(a['ScheduledExitTime'])
        duration=int((scheduled-entry).total_seconds()/60)
        target=entry+timedelta(minutes=duration//2)
        # Select the raw file by its recorded date range, then parse independently.
        raw_target=pd.Timestamp(target,tz='Asia/Tokyo').tz_convert('Europe/Helsinki').tz_localize(None)
        records=[r for r in manifest if r['Symbol']=='EURAUD' and pd.Timestamp(r['FirstRaw'])<=raw_target<=pd.Timestamp(r['LastRaw'])]
        assert len(records)==1
        record=records[0]; paths=list(Path(args.m1_root).rglob(record['Filename'])); assert len(paths)==1
        path=paths[0]
        assert hashlib.file_digest(path.open('rb'),'sha256').hexdigest()==record['SHA256']
        frame=pd.read_csv(path,sep='\t')
        frame.columns=[c.strip('<>').title() for c in frame.columns]
        raw=pd.to_datetime(frame.Date+' '+frame.Time)
        times=raw.dt.tz_localize('Europe/Helsinki',ambiguous='infer',nonexistent='shift_forward').dt.tz_convert('Asia/Tokyo').dt.tz_localize(None)
        frame.index=times
        before=frame[frame.index<target].iloc[-1]
        after=frame[frame.index>target].iloc[0]
        prior=frame[(frame.index>=entry)&(frame.index<target)]
        assert not prior.empty
        long=a['Direction']=='Long'; sign=1 if long else -1
        fill=float(frame.loc[entry,'Open'])+sign*.00015
        unit=float(a['SL'])*.0001
        extreme=float(prior.High.max() if long else prior.Low.min())
        mfe=max(0.,sign*(extreme-fill)/unit)
        reached=extreme>=fill+unit/4 if long else extreme<=fill-unit/4
        stop=fill-sign*unit
        stop_hits=(prior.Low<=stop) if long else (prior.High>=stop)
        tp=fill+sign*float(a['TP'])*.0001 if a['TP'] else None
        tp_hits=False if tp is None else bool(((prior.High>=tp) if long else (prior.Low<=tp)).any())
        present=[str(target+timedelta(minutes=i)) for i in range(5) if target+timedelta(minutes=i) in frame.index]
        valid=not reached and not stop_hits.any() and not tp_hits and not present and datetime.fromisoformat(a['CloseTime'])>target
        assert valid
        detail=dict(StrategyNo=a['StrategyNo'],Strategy=a['Strategy'],Pair=a['Pair'],Direction=a['Direction'],
                    EntryTime=str(entry),ScheduledExitTime=str(scheduled),PlannedMinutes=duration,
                    Variant=m['Variant'],CheckpointTime=str(target),CheckpointRawHelsinki=str(raw_target),
                    FallbackWindowEnd=str(target+timedelta(minutes=4)),PreviousM1=str(before.name),NextM1=str(after.name),
                    NextM1DelayMinutes=int((after.name-target).total_seconds()/60),EntryPrice=fill,
                    CheckpointMFE_R=mfe,PriorProgressReached=reached,PriorSLHit=bool(stop_hits.any()),PriorTPHit=tp_hits,
                    AvailableCheckpointBars=len(present),SourceFilename=record['Filename'],SourceSHA256=record['SHA256'],
                    Status='CONFIRMED_MISSING_EXECUTION')
        details.append(detail)
        checks.append(dict(Check='independent_missing_'+a['StrategyNo']+'_'+str(target),Status='PASS',
                           Detail='Open, MFE<.25, no SL/TP before checkpoint, no M1 in exact through +4min'))
    for name in ('portfolio_summary','period_summary','trade_delta_summary','np75_robustness'):
        path=out/(PREFIX+name+'.csv')
        if path.exists():
            records=list(csv.DictReader(path.open()))
            assert all(r.get('Status')=='NOT_EVALUATED' and not r.get('DeltaTotalR') and not r.get('AvgDeltaR') for r in records)
    checks.append(dict(Check='no_formal_outcomes_published',Status='PASS',Detail='Formal metrics intentionally not evaluated after execution gate failure'))
    write(out/(PREFIX+'checkpoint_gap_audit.csv'),details)
    write(out/(PREFIX+'independent_verification.csv'),checks)
    print(json.dumps(details,indent=2)); print(f'{len(checks)}/{len(checks)} diagnostic checks PASS')


if __name__=='__main__': main()
