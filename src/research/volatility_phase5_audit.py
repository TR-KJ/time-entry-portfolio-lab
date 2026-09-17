"""Independent same-feed Phase5 auditor. Never grants deployment or forward PASS.

Usage: python volatility_phase5_audit.py --experts Experts.log --evidence MQL5-Files-copy --out audit-directory
Stdlib only. MQL fixture comparisons and natural-forward acceptance are separate gates.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RISK={1:.5,2:.7,3:.9,4:1.1,5:1.3,0:.9}
FORMAT='%Y.%m.%d %H:%M:%S'
def dt(s): return datetime.strptime(s,FORMAT)
def jst_from_server(t):
    # OANDA server wall clock = New York wall clock + 7 hours.
    # Independent zoneinfo oracle; MQL uses explicit UTC transition arithmetic.
    z=ZoneInfo('America/New_York'); candidates=[]
    ny=t-timedelta(hours=7)
    for fold in (0,1):
        a=ny.replace(tzinfo=z,fold=fold)
        u=a.astimezone(ZoneInfo('UTC'))
        if u.year<2007: continue
        if u.astimezone(z).replace(tzinfo=None)==ny and u not in candidates: candidates.append(u)
    if len(candidates)!=1: raise ValueError('AMBIGUOUS_SERVER_TIME')
    return candidates[0].astimezone(ZoneInfo('Asia/Tokyo')).replace(tzinfo=None)

def server_from_jst(t):
    u=t.replace(tzinfo=ZoneInfo('Asia/Tokyo')).astimezone(ZoneInfo('UTC'))
    if u.year<2007: raise ValueError('UNSUPPORTED_SERVER_TIME')
    return u.astimezone(ZoneInfo('America/New_York')).replace(tzinfo=None)+timedelta(hours=7)

def daily_from_rows(rows,candidate):
    days={}; previous=None
    for row in rows:
        t=dt(row['JST'])
        if t.date()>=candidate.date() or t+timedelta(minutes=1)>candidate: continue
        if 'ServerTime' in row and jst_from_server(dt(row['ServerTime']))!=t: raise ValueError('TIMEZONE_MISMATCH')
        if previous is not None and t<=previous: raise ValueError('DUPLICATE_OR_UNSORTED_M1')
        previous=t
        o,h,l,c=(float(row[k]) for k in ('Open','High','Low','Close'))
        if not all(math.isfinite(x) and x>0 for x in (o,h,l,c)) or h<max(o,c,l) or l>min(o,c,h): raise ValueError('INVALID_OHLC')
        key=t.replace(hour=0,minute=0,second=0)
        if key not in days: days[key]={'day':key,'open':o,'high':h,'low':l,'close':c,'last':t,'count':1}
        else:
            d=days[key];d.update(high=max(d['high'],h),low=min(d['low'],l),close=c,last=t,count=d['count']+1)
    return list(days.values())

def feature(rows,candidate):
    d=daily_from_rows(rows,candidate); tr=[]; atr=[]
    for i,x in enumerate(d):
        prev=d[i-1]['close'] if i else x['close']
        # First-row high-low agrees because close is inside OHLC.
        tr.append(max(x['high']-x['low'],abs(x['high']-prev),abs(x['low']-prev)))
        atr.append(math.fsum(tr[-20:])/20 if len(tr)>=20 else None)
    if len(d)<272: return {'status':'FALLBACK','reason':'INSUFFICIENT_VOL_HISTORY','q':0,'risk':.9,'days':len(d)}
    value=atr[-1]; ref=atr[-253:-1]
    rank=2*sum(v<value for v in ref)+sum(v==value for v in ref)
    percent=100*rank/504
    q=1+sum(percent>=cut for cut in (20,40,60,80))
    return {'status':'VALID','reason':'','q':q,'risk':RISK[q],'days':len(d),'atr':value,'rank':rank,
            'percent':percent,'day':d[-1]['day'],'last':d[-1]['last'],'available':d[-1]['day']+timedelta(days=1),
            'ref_start':d[-253]['day'],'ref_end':d[-2]['day']}

def lot(base,risk,sl,pipvalue,minimum=.01,maximum=10.,step=.01,cap=1.):
    out={'amount':0.,'raw':0.,'capped':0.,'lot':0.,'cap':False,'min_stop':False,'reason':''}
    if not all(math.isfinite(x) and x>0 for x in (base,risk,sl,pipvalue)):
        return dict(out,reason='INVALID_BASE_RISK_SL_PIPVALUE')
    if (minimum,maximum,step,cap)!=(.01,10.,.01,1.):return dict(out,reason='UNAPPROVED_VOLUME_SPEC')
    out['amount']=base*risk/100;out['raw']=out['amount']/(sl*pipvalue)
    if not all(math.isfinite(out[k]) and out[k]>0 for k in ('amount','raw')):return dict(out,reason='NONFINITE_LOT')
    if out['raw']<minimum:return dict(out,min_stop=True,reason='BELOW_MINIMUM')
    out['cap']=out['raw']>cap;out['capped']=min(out['raw'],cap)
    # Replicates the approved existing double floor behavior (no rounding-up epsilon).
    out['lot']=round(math.floor(min(maximum,max(minimum,out['capped']))/step)*step,2)
    if not minimum<=out['lot']<=min(cap,maximum):return dict(out,lot=0.,reason='INVALID_FINAL_LOT')
    return out

def parse_experts(text):
    out=[]
    for line in text.splitlines():
        if '[P5] SchemaVersion=' not in line:continue
        fields=line.split('[P5] ',1)[1].split('|'); row={}
        for f in fields:
            if '=' not in f:raise ValueError('Malformed diagnostic field')
            k,v=f.split('=',1)
            if k in row:raise ValueError('Duplicate diagnostic field: '+k)
            row[k]=v
        for k in ('SchemaVersion','RunId','CandidateId','AttemptId','EventType','StrategyName','Magic','Symbol'):
            if not row.get(k):raise ValueError('Missing '+k)
        out.append(row)
    return out

def close(actual,expected,atol):
    return math.isfinite(float(actual)) and math.isclose(float(actual),expected,rel_tol=1e-10,abs_tol=atol)

def audit(events,evidence):
    groups={}; output=[]
    for e in events:groups.setdefault((e['RunId'],e['CandidateId']),[]).append(e)
    for (run,cid),evs in groups.items():
        errors=[]; pending=[]; f=None
        fs=[e for e in evs if e['EventType']=='FEATURE']; histories=[e for e in evs if e['EventType']=='HISTORY']
        if len(fs)!=1:pending.append('EXPECTED_ONE_FEATURE')
        else:
            e=fs[0]
            if e['VolFeatureStatus']=='FALLBACK' and float(e['AppliedRiskPercent'])!=.9:errors.append('FALLBACK_RISK')
            if not histories:pending.append('MISSING_SOURCE_EVIDENCE')
            else:
                filename=histories[-1].get('EvidencePath','')
                if Path(filename).name!=filename or filename in ('','EXPORT_FAILED'):pending.append('MISSING_SNAPSHOT')
                elif not (evidence/filename).is_file():pending.append('MISSING_SNAPSHOT')
                else:
                    try:
                        with (evidence/filename).open() as h:f=feature(list(csv.DictReader(h)),dt(e['EntryCandidateJST']))
                        if f['status']!=e['VolFeatureStatus']:errors.append('FEATURE_STATUS')
                        if f['q']!=int(e['Quintile']):errors.append('QUINTILE')
                        if f['risk']!=float(e['AppliedRiskPercent']):errors.append('RISK')
                        if f['status']=='VALID':
                            for actual,key,atol in [('ATR20','atr',1e-10),('Percentile','percent',1e-10)]:
                                if not close(e[actual],f[key],atol):errors.append(actual)
                            if int(e['RankNumerator'])!=f['rank']:errors.append('RANK_NUMERATOR')
                            for actual,key in [('FeatureDailyDate','day'),('LastM1JST','last'),('AvailableAtJST','available'),('ReferenceStart','ref_start'),('ReferenceEnd','ref_end')]:
                                if dt(e[actual])!=f[key]:errors.append(actual)
                            if int(e['ReferenceCount'])!=252 or int(e['DailyCount'])!=f['days']:errors.append('COUNTS')
                        elif f['reason']!=e['FallbackReason']:errors.append('FALLBACK_REASON')
                    except (ValueError,KeyError) as ex:
                        if e['VolFeatureStatus']!='FALLBACK' or e.get('FallbackReason')!=str(ex):errors.append(str(ex))
        for e in evs:
            if e['EventType']!='SIZING':continue
            try:
                values=[float(e[k]) for k in ('WeeklyBase','AppliedRiskPercent','SLPips','PipValuePerLot','VolumeMin','VolumeMax','VolumeStep','MaxAutoLot')]
                r=lot(*values)
                if fs and float(e['AppliedRiskPercent'])!=float(fs[0]['AppliedRiskPercent']):errors.append('SIZING_RISK_CHANGED')
                for actual,key,tol in [('RiskAmount','amount',1e-6),('RawLot','raw',1e-10),('CappedLot','capped',1e-10)]:
                    if not close(e[actual],r[key],tol):errors.append(actual)
                if float(e['FinalLot'])!=r['lot']:errors.append('FINAL_LOT')
                if e['MaxAutoLotCap']!=str(r['cap']).lower() or e['MinLotStop']!=str(r['min_stop']).lower():errors.append('LOT_FLAGS')
                if e['LotStopReason']!=r['reason']:errors.append('LOT_REASON')
                ts,tv,pip=(float(e[k]) for k in ('TickSize','TickValue','PipSize'))
                if ts>0 and not close(e['PipValuePerLot'],tv*pip/ts,1e-10):errors.append('PIP_VALUE')
            except (ValueError,KeyError) as ex:pending.append('INCOMPLETE_SIZING:'+str(ex))
        output.append({'RunId':run,'CandidateId':cid,'AuditStatus':'FAIL' if errors else 'PENDING' if pending else 'NUMERIC_MATCH',
                       'Errors':';'.join(errors),'MissingEvidence':';'.join(pending),'IndependentFeature':f})
    return output

def assess(record):
    """Evaluate evidence-completed checklist, never infer a PASS from numerical matching alone."""
    checks=record.get('checks',{})
    if any(v.get('status')=='FAIL' for v in checks.values()):return 'DEMO_FORWARD_FAIL'
    required=set('ABCDEFG')
    if set(checks)!=required or any(v.get('status')!='PASS' or not v.get('evidence') for v in checks.values()):return 'INSUFFICIENT_OBSERVATIONS'
    if record.get('deployment_validation')!='PASS':return 'INSUFFICIENT_OBSERVATIONS'
    try:
        start=datetime.fromisoformat(record['start']);cutoff=datetime.fromisoformat(record['cutoff'])
        if start.tzinfo is None or cutoff.tzinfo is None:return 'INSUFFICIENT_OBSERVATIONS'
        if (cutoff-start).total_seconds()<14*86400:return 'INSUFFICIENT_OBSERVATIONS'
        rows=record['qualifying_candidates'];ids=[r['id'] for r in rows]
        if len(set(ids))<10 or len(set(ids))!=len(ids):return 'INSUFFICIENT_OBSERVATIONS'
        if any(r['quintile'] not in range(1,6) for r in rows):return 'INSUFFICIENT_OBSERVATIONS'
        if any(r.get('numeric_audit')!='NUMERIC_MATCH' or not start<=datetime.fromisoformat(r['entry_jst'])<=cutoff for r in rows):return 'INSUFFICIENT_OBSERVATIONS'
        if len({r['quintile'] for r in rows})<2 or len({r['symbol'] for r in rows})<2:return 'INSUFFICIENT_OBSERVATIONS'
        if not all(record.get(k) is True for k in ('actual_entry_exit_reconciled','week_rollover_observed','within_week_reuse_observed','all_candidates_audited')):return 'INSUFFICIENT_OBSERVATIONS'
    except (KeyError,TypeError,ValueError):return 'INSUFFICIENT_OBSERVATIONS'
    return 'DEMO_FORWARD_PASS'

def main():
    p=argparse.ArgumentParser();p.add_argument('--experts',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();raw=a.experts.read_bytes();text=raw.decode('utf-16') if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else raw.decode('utf-8-sig')
    events=parse_experts(text);checks=audit(events,a.evidence);a.out.mkdir(parents=True,exist_ok=False)
    sources={}
    for event in events:
        name=event.get('EvidencePath','')
        if name and Path(name).name==name and (a.evidence/name).is_file():sources[name]=hashlib.sha256((a.evidence/name).read_bytes()).hexdigest()
    (a.out/'numeric_audit.json').write_text(json.dumps({'Status':'NOT_A_FORWARD_VERDICT','ExpertsSHA256':hashlib.sha256(raw).hexdigest(),'SnapshotSHA256':sources,'Candidates':checks},default=str,indent=2))
    if events:
        with (a.out/'events.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=sorted(set().union(*(e.keys() for e in events))));w.writeheader();w.writerows(events)
    print(json.dumps({'candidates':len(checks),'numeric_failures':sum(x['AuditStatus']=='FAIL' for x in checks),'forward_verdict':'NOT_EVALUATED'}))
if __name__=='__main__':main()
