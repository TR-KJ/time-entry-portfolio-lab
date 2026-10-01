"""Exactly five raw-value adoption gates and three tie keys; no P02 gate."""
import math

def finite(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def compare(e0,row):
    def delta(k):return row[k]-e0[k] if finite(row[k]) and finite(e0[k]) else 'UNDEFINED'
    return dict(E0Trades=e0['Trades'],FilteredTrades=row['Trades'],RetentionRate=row['Trades']/e0['Trades'] if e0['Trades'] else 'UNDEFINED',RemovedTrades=e0['Trades']-row['Trades'],DeltaTotalR=delta('TotalR'),DeltaAvgR=delta('AvgR'),DeltaMaxDDR=delta('MaxDDR'),E0MaxDDR=e0['MaxDDR'],FilterMaxDDR=row['MaxDDR'])

def adoption(values):
    checks=[('RETENTION',finite(values['RetentionRate']) and values['RetentionRate']>=.80),('REMOVED_TRADES',finite(values['RemovedTrades']) and values['RemovedTrades']>=20),('DELTA_TOTAL_R',finite(values['DeltaTotalR']) and values['DeltaTotalR']>=2.0),('DELTA_AVG_R',finite(values['DeltaAvgR']) and values['DeltaAvgR']>=.01),('MAX_DD',finite(values['FilterMaxDDR']) and finite(values['E0MaxDDR']) and values['FilterMaxDDR']<=values['E0MaxDDR'])]
    reasons=[name for name,passed in checks if not passed]
    return dict(AdoptionPass=not reasons,AdoptionFailReasons='|'.join(reasons))

def choose(rows):
    if [r['EventMode'] for r in rows]!=['E0','E1','E2']:raise ValueError('exactly three ordered modes required')
    eligible=[r for r in rows[1:] if adoption(r)['AdoptionPass']]
    if not eligible:return rows[0],'NO_FILTER_PASSES_FIVE_GATES'
    best=min(eligible,key=lambda r:(-r['DeltaTotalR'],r['FilterMaxDDR'],0 if r['EventMode']=='E1' else 1))
    return best,'FIVE_GATES_THEN_DELTA_TOTAL_DD_E1'
