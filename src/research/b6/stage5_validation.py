"""Pure contract/schema helper using supplied synthetic metrics; no data loader."""
import math
SCHEMA='b6-stage5-validation-contract-v1'
OUTPUT_METRICS=['Trades','Wins','Losses','ZeroR','PF','AvgR','TotalR','MaxDDR']

def contract(candidate_sha):
    return dict(schema=SCHEMA,status='VALIDATION_CONTRACT_FROZEN_NOT_EXECUTED',CandidateFreezeFile='research_inputs/b6/stage5_candidate_freeze.json',CandidateFreezeSHA256=candidate_sha,Timezone='Asia/Tokyo naive',Label='B6 holdout validation / OOS-like',Limitation='2024-2025 have been viewed in other research; not pristine unseen OOS',Periods={'2024':dict(StartInclusive='2024-01-01',EndExclusive='2025-01-01'),'2025':dict(StartInclusive='2025-01-01',EndExclusive='2026-01-01'),'Combined':dict(StartInclusive='2024-01-01',EndExclusive='2026-01-01')},SampleSufficiency=dict(AnnualMinTrades=30,AnnualMinLosses=5,CombinedMinTrades=70,AllRequired=True,InsufficientStatus='INSUFFICIENT_SAMPLE',InsufficientIsFail=False,SkipFormalPassFailIfInsufficient=True),PassConditions=[dict(Field='2024.TotalR',Operator='>',Value=0),dict(Field='2025.TotalR',Operator='>',Value=0),dict(Field='Combined.PF',Operator='>=',Value=1.10),dict(Field='Combined.AvgR',Operator='>=',Value=.02),dict(Field='Combined.MaxDDR',Operator='<=',Value='max(10.0, 1.5 * Stage5FrozenDiscoveryMaxDDR)')],DDLimit=dict(FloorR=10.0,DiscoveryMultiplier=1.5,DiscoverySource='Candidate.DiscoveryMaxDDR raw unrounded value only',DiscoveryRecalculationAllowed=False),Statuses=['PASS','FAIL','INSUFFICIENT_SAMPLE'],Comparison='Raw unrounded R, no epsilon; undefined required comparison cannot PASS',MetricsSemantics=dict(ZeroR='Included in Trades; neither Wins nor Losses',PF='positive R sum / abs(negative R sum)',PFNoLossPositive='INF',PFNoLossNoPositive='UNDEFINED',MissingTrade='Not generated',PipsDisplayDecimals=6,RDisplayDecimals=9),ProhibitedExtraGates=['annual PF','annual AvgR','WinRate','Recovery','Discovery improvement','quarter or month profitability','statistical significance','event reselection'],CandidateConditionsImmutable=True,ExecutionContractReference='stage5_candidate_freeze.json:ExecutionContract',EventCalendarReference='stage5_candidate_freeze.json:EventCalendarProvenance',OutputRequirements=dict(Periods=['2024','2025','Combined'],Metrics=OUTPUT_METRICS,Audit=['DiscoveryMaxDDR','ValidationDDLimit','SampleSufficient','SampleFailReasons','ValidationStatus','ValidationFailReasons']),Stage6IdentityHardGate=['Stage5 commit SHA equals approved remote/local SHA','exact CandidateFreezeSHA256','exact Validation Contract SHA256 from Stage5 release manifest','Stage4 runtime input hashes and selected SHA','frozen execution/calendar identities'],ValidationExecuted=False,MonitorExecuted=False,LiveAdoption=False)

def number(value):
    if value=='INF':return math.inf
    if value=='UNDEFINED':return math.nan
    if isinstance(value,bool) or not isinstance(value,(int,float)):raise ValueError('numeric metric or INF/UNDEFINED required')
    return value

def dd_limit(discovery_dd):
    if isinstance(discovery_dd,bool) or not isinstance(discovery_dd,(int,float)) or not math.isfinite(discovery_dd) or discovery_dd<0:raise ValueError('raw frozen DiscoveryMaxDDR required')
    return max(10.0,1.5*discovery_dd)

def assess(year2024,year2025,combined,frozen_discovery_dd):
    """Threshold helper only: callers supply metrics. Stage5 uses synthetic tests only."""
    limit=dd_limit(frozen_discovery_dd);sample=[]
    for label,row in (('2024',year2024),('2025',year2025)):
        for field,minimum in (('Trades',30),('Losses',5)):
            if type(row[field]) is not int or row[field]<0:raise ValueError('nonnegative integer sample counts required')
            if row[field]<minimum:sample.append(label+'_'+field.upper())
    if type(combined['Trades']) is not int or combined['Trades']<0:raise ValueError('nonnegative combined trades required')
    if combined['Trades']<70:sample.append('COMBINED_TRADES')
    out=dict(DiscoveryMaxDDR=frozen_discovery_dd,ValidationDDLimit=limit,SampleSufficient=not sample,SampleFailReasons=sample,ValidationStatus='INSUFFICIENT_SAMPLE' if sample else None,ValidationFailReasons=[])
    if sample:return out
    checks=[('2024_TOTAL_R',number(year2024['TotalR'])>0),('2025_TOTAL_R',number(year2025['TotalR'])>0),('COMBINED_PF',number(combined['PF'])>=1.10),('COMBINED_AVG_R',number(combined['AvgR'])>=.02),('COMBINED_MAX_DD',number(combined['MaxDDR'])<=limit)]
    out['ValidationFailReasons']=[k for k,passed in checks if not passed];out['ValidationStatus']='FAIL' if out['ValidationFailReasons'] else 'PASS'
    return out
