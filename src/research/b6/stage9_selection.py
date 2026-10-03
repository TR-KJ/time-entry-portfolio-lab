"""Fixed GBPJPY family policy and raw lexicographic comparison."""
import copy
import math
from .stage9_input import AJ, GBP, SCOPE, OUTSIDE, PERIODS, IDENTITY, require, validate_families

KEYS = [
    {'Field': 'WorstSegmentMaxDDR', 'Order': 'ASC'},
    {'Field': 'RelativeLotMarginProxy', 'Order': 'ASC'},
    {'Field': 'FullAvailableMaxDDR', 'Order': 'ASC'},
    {'Field': 'ValidationAvgR', 'Order': 'DESC'},
    {'Field': 'FullAvailableTotalR', 'Order': 'DESC'},
    {'Field': 'CandidateID', 'Order': 'ASC'},
]
PROXY = dict(Formula='30.0 / SL_pips', Symbol='GBPJPY',
             Assumption='same symbol, equal fixed monetary risk',
             Interpretation='relative lot / margin proxy; lower is less',
             ActualBrokerMargin=False, RiskAllocationDecided=False, LotDecided=False)
BOUNDARY = dict(Stage10Executed=False, PortfolioExecuted=False, MoneySimulationExecuted=False,
                ExistingPortfolioComparisonExecuted=False, GlobalR2ComparisonExecuted=False,
                RiskAllocationDecided=False, RiskPercentageDecided=False, LotDecided=False,
                EAChanged=False, SETChanged=False, VPSChanged=False, LiveChanged=False,
                StrategyNumberingAssigned=False, M1Read=False, ReplayExecuted=False,
                CandidateTradeRecomputed=False, CorrelationRecomputed=False, RetuningExecuted=False)


def raw_number(value):
    require(not isinstance(value, bool), 'boolean is not a raw metric')
    result = float(value)
    require(math.isfinite(result), 'non-finite selection metric')
    return result


def relative_lot_margin_proxy(symbol, sl):
    require(symbol == 'GBPJPY', 'proxy only compares GBPJPY family representatives')
    sl = raw_number(sl)
    require(sl > 0, 'positive raw SL required')
    return 30.0 / sl


def selection_key(row):
    values = [raw_number(row[k['Field']]) for k in KEYS[:-1]]
    return (*values[:3], -values[3], -values[4], row['CandidateID'])


def rank_rows(rows):
    require(len(rows) > 0 and len({r['CandidateID'] for r in rows}) == len(rows), 'unique ranking rows required')
    return [{**r, 'LexicographicRank': i, 'Selected': i == 1}
            for i, r in enumerate(sorted(rows, key=selection_key), 1)]


def selection_rows(pool, metrics):
    scope = validate_families(pool)
    ids = [p['CandidateID'] for p in pool['Candidates']]
    require(len(metrics) == 36 and [(r['CandidateID'], r['Period']) for r in metrics] ==
            [(c, period) for c in ids for period in PERIODS], 'unique complete candidate-period source required')
    lookup = {(r['CandidateID'], r['Period']): r for r in metrics}
    rows = []
    for p in scope:
        periods = {name: lookup[p['CandidateID'], name] for name in PERIODS}
        dd = {name: raw_number(r['MaxDDR']) for name, r in periods.items()}
        require(all(v >= 0 for v in dd.values()), 'negative drawdown')
        full = periods['FullAvailable']
        pf = full['PF']
        if pf not in ('INF', 'UNDEFINED'):
            pf = raw_number(pf)
        rows.append(dict(CandidateID=p['CandidateID'], FinalEntryJST=p['FinalEntryJST'],
            FinalExitJST=p['FinalExitJST'], SL=p['SL'], TP=p['TP'],
            WorstSegmentMaxDDR=max(dd[name] for name in PERIODS[:3]),
            RelativeLotMarginProxy=relative_lot_margin_proxy(p['Symbol'], p['SL']),
            DiscoveryMaxDDR=dd['Discovery'], ValidationMaxDDR=dd['Validation'],
            MonitorMaxDDR=dd['Monitor'], FullAvailableMaxDDR=dd['FullAvailable'],
            ValidationAvgR=raw_number(periods['Validation']['AvgR']),
            FullAvailableAvgR=raw_number(full['AvgR']), FullAvailableTotalR=raw_number(full['TotalR']),
            FullAvailablePF=pf))
    return rank_rows(rows)


def consolidate(pool, metrics):
    rows = selection_rows(pool, metrics)
    selected = rows[0]['CandidateID']
    dispositions = []
    for p in pool['Candidates']:
        cid = p['CandidateID']
        if cid == AJ:
            disposition, reason = 'AUTO_RETAINED_SINGLETON', 'USER_FIXED_SINGLETON'
        elif cid == selected:
            disposition, reason = 'SELECTED_GBPJPY_FAMILY_REPRESENTATIVE', 'FIXED_LEXICOGRAPHIC_RANK_1'
        elif cid in OUTSIDE:
            disposition, reason = 'NOT_IN_REPRESENTATIVE_SELECTION_SCOPE', 'ENTRY_OUTSIDE_13H_NOT_PERFORMANCE_FAIL'
        else:
            disposition, reason = 'NOT_SELECTED_FAMILY_REDUNDANCY', 'ONE_GBP_REPRESENTATIVE_POLICY_NOT_PERFORMANCE_FAIL'
        dispositions.append(dict(CandidateID=cid, Symbol=p['Symbol'],
            Family='AUDJPY_SINGLETON' if cid == AJ else 'GBPJPY_FAMILY',
            Stage8Eligibility=p['DeploymentReviewEligibility'], RepresentativeSelectionScope=cid in SCOPE,
            Stage9Disposition=disposition, ReasonCode=reason))
    by_id = {p['CandidateID']: p for p in pool['Candidates']}
    disp = {r['CandidateID']: r for r in dispositions}
    final = []
    for cid in (AJ, selected):
        point = copy.deepcopy(by_id[cid])
        point.update(Stage8Eligibility=disp[cid]['Stage8Eligibility'], Stage9Family=disp[cid]['Family'],
                     Stage9Disposition=disp[cid]['Stage9Disposition'])
        final.append(point)
    artifact = dict(schema='b6-stage9-final-candidates-v1', State='COMPLETE_STAGE9_FINAL_CANDIDATE_FREEZE',
                    CandidateCount=2, CandidateOrdering='AUDJPY singleton then GBPJPY representative; family order, not ranking',
                    Stage8Identity=IDENTITY, Candidates=final, **BOUNDARY)
    return rows, dispositions, artifact


def family_policy():
    return dict(schema='b6-stage9-family-consolidation-v1', Stage8Identity=IDENTITY,
        PolicyBasis='Explicit user decision based on Stage8 structural evidence; no clustering algorithm',
        Families=[dict(Name='AUDJPY_SINGLETON', Members=[AJ], Disposition='AUTO_RETAINED_SINGLETON'),
                  dict(Name='GBPJPY_FAMILY', Members=list(GBP), RepresentativeCount=1)],
        RepresentativeSelectionScope=list(SCOPE), OutsideSelectionScope=list(OUTSIDE),
        EntryScope='13:00 <= FinalEntryJST < 14:00; Stage8 Pool field, not CandidateID',
        SelectionKeys=KEYS, RelativeLotMarginProxy=PROXY,
        MetricDefinitions=dict(WorstSegmentMaxDDR='max(Discovery.MaxDDR, Validation.MaxDDR, Monitor.MaxDDR)',
            PerformanceSource='stage8_candidate_period_metrics.csv.gz only',
            Validation='[2024-01-01, 2026-01-01)', FullAvailable='[2020-01-01, 2026-09-10)',
            Comparison='raw IEEE-754 binary64 parsed from formal CSV; no rounding, epsilon or tolerance',
            PF='audit only; never a selection key', Correlation='family policy basis only; never a selection key'),
        ResearchHistoryUnchanged=True, FormalValidationChanged=False, MonitorResultsChanged=False,
        Stage8EligibilityChanged=False, AJGBPCompetition=False, ClusteringExecuted=False,
        FinalCandidateCount=2, **BOUNDARY)
