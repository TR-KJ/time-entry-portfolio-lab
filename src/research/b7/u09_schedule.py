"""Minute schedules retain Stage1 lineage, with U04 fixed-key field order."""
from datetime import datetime,timedelta
SHIFTS=tuple(range(-5,6))

def key(record,p):
    return [record['Symbol'],int(record['Schedule']['Direction']=='SHORT'),record['AnchorWeekday'],p['EntryMinute'],p['ExitDayOffset'],p['ExitMinute'],p['HoldingMinutes'],record['CandidateID']]

def schedule(record,es,xs):
    if type(es) is not int or type(xs) is not int or es not in SHIFTS or xs not in SHIFTS:raise ValueError('frozen +/-5 integer grid')
    s=record['Schedule'];day=datetime(2020,1,6)+timedelta(days=record['AnchorWeekday'])
    e0=day+timedelta(minutes=s['EntryMinute']);x0=day+timedelta(days=s['ExitDayOffset'],minutes=s['ExitMinute'])
    if (x0-e0).total_seconds()/60!=s['HoldingMinutes']:raise ValueError('anchor holding invariant')
    e=e0+timedelta(minutes=es);x=x0+timedelta(minutes=xs);h=int((x-e).total_seconds()/60);off=(x.date()-e.date()).days
    reason=('ENTRY_DATE_CHANGED' if e.date()!=e0.date() else 'ENTRY_WEEKDAY_CHANGED' if e.weekday()!=e0.weekday() else 'EXIT_DAY_OFFSET_CHANGED' if off!=s['ExitDayOffset'] else 'HOLDING_OUT_OF_RANGE' if not 30<=h<=1440 else 'EXECUTION_SCHEDULE_INVALID' if e.weekday()>4 else None)
    p=dict(PointID=f'{es:+d}/{xs:+d}',EntryShiftMinutes=es,ExitShiftMinutes=xs,EntryMinute=e.hour*60+e.minute,ExitMinute=x.hour*60+x.minute,ExitDayOffset=off,HoldingMinutes=h,Valid=reason is None,InvalidReason=reason)
    p['FixedKey']=key(record,p);return p

def grid(record):return [schedule(record,e,x) for e in SHIFTS for x in SHIFTS]
