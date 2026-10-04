"""Independent actual-day R2 adapter. Outcomes are absent from the feature API."""
import bisect
import hashlib
import math
import types
from datetime import datetime, timedelta
from .stage11_config import ROOT,INPUT,PHASE5_SHA,SOURCE_HASHES,RISK,require,read
TZ='Europe/Helsinki -> Asia/Tokyo -> naive JST'
SPEC='stage11-r2-actual-day-v1'

def source_audit():
    out={}
    for path,h in SOURCE_HASHES.items():
        record=read(ROOT/INPUT/'stage11_provenance'/ (path.split('/')[-1]+'.json'))
        require(record['SourceCommit']==PHASE5_SHA and record['SourcePath']==path,'R2 source identity mismatch')
        require(len(h)==64 and record['SourceSHA256']==h==hashlib.sha256(record['Content'].encode()).hexdigest(),'R2 source SHA mismatch')
        out[path]=dict(SourceCommit=PHASE5_SHA,SourceSHA256=h)
    return dict(Status='PASS',Sources=out,CalculationExecuted=False)

def reference():
    source_audit()
    record=read(ROOT/INPUT/'stage11_provenance/volatility_phase5_audit.py.json')
    module=types.ModuleType('stage11_frozen_independent_auditor')
    exec(compile(record['Content'],record['SourcePath'],'exec'),module.__dict__)
    return module

def quintile(n):
    require(type(n) is int and 0<=n<=504,'invalid rank numerator')
    return 'Q'+str(1+sum(5*n>=c for c in (504,1008,1512,2016)))

def risk(state):
    require(state in RISK,'unknown R2 state');return RISK[state]

def daily_from_rows(rows,candidate):
    """Canonical naive JST input. Ignore candidate date/future before OHLC checks."""
    require(isinstance(candidate,datetime) and candidate.tzinfo is None,'naive JST entry required')
    days=[];previous=None
    for r in rows:
        t=r['JST']
        if isinstance(t,str):t=datetime.strptime(t,'%Y.%m.%d %H:%M:%S')
        require(t.tzinfo is None,'naive JST M1 required')
        if t.date()>=candidate.date():continue
        require(previous is None or previous<t,'DUPLICATE_OR_UNSORTED_M1');previous=t
        require(t.second==0 and t.microsecond==0,'M1_ALIGNMENT')
        o,h,l,c=[float(r[k]) for k in ('Open','High','Low','Close')]
        require(all(math.isfinite(v) and v>0 for v in (o,h,l,c)) and h>=max(o,l,c) and l<=min(o,h,c),'INVALID_OHLC')
        d=t.replace(hour=0,minute=0,second=0,microsecond=0)
        if not days or days[-1]['day']!=d:days.append(dict(day=d,open=o,high=h,low=l,close=c,last=t,count=1))
        else:
            x=days[-1];x.update(high=max(x['high'],h),low=min(x['low'],l),close=c,last=t,count=x['count']+1)
    return days

def true_ranges(days):
    return [max(x['high']-x['low'],abs(x['high']-days[i-1]['close']),abs(x['low']-days[i-1]['close'])) if i else x['high']-x['low'] for i,x in enumerate(days)]

def feature_daily(days,candidate):
    d=[x for x in days if x['day'].date()<candidate.date()]
    previous=None
    for x in d:
        require(previous is None or previous<x['day'],'DUPLICATE_OR_UNSORTED_DAILY');previous=x['day']
        o,h,l,c=[x[k] for k in ('open','high','low','close')]
        require(all(math.isfinite(v) and v>0 for v in (o,h,l,c)) and h>=max(o,l,c) and l<=min(o,h,c),'INVALID_OHLC')
        require(x['last'].date()==x['day'].date(),'INVALID_DAILY_LAST')
    base=dict(FeatureStatus='FALLBACK',FallbackReason='INSUFFICIENT_VOL_HISTORY',FeatureDailyDate=None,LastM1JST=None,
        ReferenceStart=None,ReferenceEnd=None,ReferenceCount=0,ATR20=None,RankNumerator=None,Percentile=None,
        Quintile='FALLBACK',AppliedRiskPercent=risk('FALLBACK'),DailyCount=len(d))
    if len(d)<272:return base
    tr=true_ranges(d);atr=[math.fsum(tr[i-19:i+1])/20 for i in range(19,len(tr))]
    value=atr[-1];ref=atr[-253:-1]
    require(len(ref)==252 and all(math.isfinite(v) for v in [value,*ref]),'UNAVAILABLE_OR_NONFINITE_FEATURE')
    n=2*sum(v<value for v in ref)+sum(v==value for v in ref);q=quintile(n)
    return dict(base,FeatureStatus='VALID',FallbackReason='',FeatureDailyDate=d[-1]['day'],LastM1JST=d[-1]['last'],
        ReferenceStart=d[-253]['day'],ReferenceEnd=d[-2]['day'],ReferenceCount=252,ATR20=value,RankNumerator=n,
        Percentile=100*n/504,Quintile=q,AppliedRiskPercent=risk(q))

def feature(rows,candidate):return feature_daily(daily_from_rows(rows,candidate),candidate)

def assert_parity(actual,expected):
    require(actual['FeatureStatus']==expected['status'] and actual['FallbackReason']==expected['reason'],'independent status parity')
    require(actual['AppliedRiskPercent']==risk('Q'+str(expected['q']) if expected['q'] else 'FALLBACK'),'independent risk parity')
    require(actual['DailyCount']==expected['days'],'independent day count parity')
    if actual['FeatureStatus']=='VALID':
        for k,v in {'ATR20':'atr','RankNumerator':'rank','Percentile':'percent','FeatureDailyDate':'day','LastM1JST':'last','ReferenceStart':'ref_start','ReferenceEnd':'ref_end'}.items():require(actual[k]==expected[v],'independent parity '+k)
        require(actual['Quintile']=='Q'+str(expected['q']),'independent quintile parity')

class Assigner:
    def __init__(self,daily_by_symbol,source_identity,use_cache=True,parity=True):
        require(bool(source_identity),'source identity required')
        self.days=daily_by_symbol;self.identity=source_identity;self.use_cache=use_cache;self.cache={}
        self.oracle=reference() if parity else None
    def assign(self,symbol,entry):
        require(symbol in self.days and bool(self.days[symbol]),'UNAVAILABLE_FEATURE_SOURCE')
        key=(self.identity,TZ,SPEC,symbol,entry.date().isoformat())
        if self.use_cache and key in self.cache:return dict(self.cache[key])
        days=self.days[symbol];result=feature_daily(days,entry)
        if self.oracle:
            # One OHLC row per actual date preserves all daily statistics and LastM1JST.
            reduced=[dict(JST=x['last'].strftime(self.oracle.FORMAT),Open=x['open'],High=x['high'],Low=x['low'],Close=x['close']) for x in days if x['day'].date()<entry.date()]
            assert_parity(result,self.oracle.feature(reduced,entry))
        if self.use_cache:self.cache[key]=dict(result)
        return result
