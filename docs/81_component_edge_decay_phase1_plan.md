# 81 Composite Strategy Component Edge Decay Phase 1 — preregistered Plan

Registered 2026-09-22 JST. Branch `research/component-edge-decay-phase1`; parent `39b6d4136c1ae049904fdcf6ef53cbaf70c9e88f`. This Plan alone is committed and its remote SHA verified before study code or outcome calculations. Definitions, periods, tests and thresholds are immutable after registration.

## Purpose and frozen input
Diagnose decay inside existing composite strategies. Phase 1 is descriptive/inferential diagnosis only: no component stop, portfolio or money simulation, EA/SET/VPS/live or Volatility Phase 5 changes. The fixed `daily_stop_baseline_trades.csv` is read without recalculation: SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`, 16,298 trades, 28 strategy identities. Entry timestamps are naive JST interpreted as Asia/Tokyo. Reject hash, count, identity, timestamp, R/Pips/SL or duplicate failures before results. Although live composition differs, use all fixed 28-strategy baseline records. 2022–2026 is previously viewed, not a pristine unseen holdout.

## Locked component universe
| Strategy | Components |
|---|---|
| 1_EJ_Log1 | Mon, Wed |
| 2_EJ_NightBlitz_20 | Mon, Wed |
| 3_EJ_NightBlitz_21 | Mon, Wed |
| 4_GJ_Port_Log1 | Tue, Wed |
| 5_GJ_Port_Log2 | Tue, Thu, Fri |
| 12_UJ_Short_Core | nominal Gotobi 20, 25, 30 |
| 13_UJ_Fix_MidWeek | Wed, Thu |
| 18_EA_2_MonWed_Short | Mon, Tue, Wed |
| 19_EA_3_WedThu_Long | Wed, Thu |
| 20_EA_1A_MonTue_Short | Mon, Tue |

These are 23 formal components in one Holm family (2+2+2+2+3+3+2+3+2+2). Weekday is entry JST weekday. Strategy12 has both GOTO and NORMAL records in the fixed baseline (pre-registration schema audit: GOTO 224, NORMAL 322). Only GOTO records possess the specified nominal 20/25/30 component; NORMAL records are explicitly out of scope, retained in coverage with their count and never silently assigned to a Gotobi component. Every eligible GOTO record and every record of the other nine strategies must map to exactly one component. For Strategy12, actual 20/25/30 is its own nominal date; a Friday one or two days before a weekend 25 or 30 maps to the future nominal 25 or 30. The 20th is never shifted. Reject unmatched or ambiguous GOTO rows. Match Mode, 09:55 entry, SL20/TP50 against baseline and existing `daily_stop_baseline_revalidation.py` and EA forward-Gotobi rules. All Strategy12 NORMAL rows are reported as out-of-scope in coverage. No other strategy or split is added. Strategy25 9–15/>=25 was already NOT_SUPPORTED; 26–28 weekday splits, Strategy16, month/season and post hoc splits are forbidden.

## Locked dates and metrics
Inclusive JST entry dates: Historical 2015-01-01–2021-12-31; Recent A 2022-01-01–2023-12-31; Recent B 2024-01-01–2025-12-31; 2026 Monitor 2026-01-01–2026-09-09; Recent Combined 2022-01-01–2026-09-09; ALL 2015-01-01–2026-09-09. Implement as half-open next-day bounds. No rolling window or changed start. Primary AvgR = sum(recorded R)/trades. Auxiliary: Trades, TotalR, gross-positive-R/absolute-gross-negative-R PF, WinRate(R>0), AvgWinR, signed AvgLossR, occupied Monday-based JST calendar weeks. Zero-R contributes to N only. PF is infinity with positive gains/no losses and undefined if both zero. Show every year 2015–2026 for every component including zero-trade cells; 2026 ends 09-09.

## Predeclared contrasts
For each component c, `COMPONENT_DECAY = AvgR(c,Recent Combined)-AvgR(c,Historical)`. Its sibling is all OTHER eligible components of the same strategy pooled by trades separately within each period; `SIBLING_DECAY = AvgR(siblings,Recent Combined)-AvgR(siblings,Historical)`. Thus three-component sibling means are trade-weighted, never equal-component weighted in formal decisions. `RELATIVE_DECAY = COMPONENT_DECAY-SIBLING_DECAY`; negative means c deteriorated more. Recent A/B/Monitor component AvgR and difference versus Historical are descriptive stability checks only; Recent B or Monitor weakness cannot rescue a failed formal test.

## Resampling, p values and family
Calendar week is Monday 00:00 JST through next Monday; key Monday date, not week number. Assign periods before resampling; boundary weeks contain only their period's records. For each strategy separately, form occupied historical and recent-combined week clusters from eligible trades. Chronological week order. NumPy PCG64 Generator seed 20260913, 5,000 replicates per strategy, reinitialized to the same seed for each strategy. Each replicate samples with replacement the original number of occupied weeks independently within the two periods, retaining all trades and multiplicities of every component in sampled weeks. The same paired strategy draws feed component and sibling means, preserving within-week correlation. Trade-weighted means. No redraw/drop of empty-component replicates: affected CI/p is unavailable and cannot pass. Percentile 2.5/97.5 with NumPy linear interpolation gives unadjusted two-sided 95% CIs for component and relative decay. For each relative-decay hypothesis, one-sided negative-tail bootstrap p = (1 + number of valid bootstrap relative-decay replicates >= 0)/(5001); this is an explicitly approximate bootstrap tail probability. Every one of the 23 relative tests, including insufficient-sample tests, belongs to ONE Holm family; insufficient p=1. Holm step-down adjustment across all 23, ties stable by strategy number/component order. Formal condition F is adjusted p < 0.05. No alternate CI/p method, seed, family, or thresholds after results.

Sample floor: each component Historical and Recent Combined requires >=30 trades and >=20 component-occupied calendar weeks. Relative contrast additionally requires the pooled siblings meet the same floor in both periods. Display counts/weeks for every cell. Any floor failure or undefined replicate => INSUFFICIENT_SAMPLE and candidate barred.

## Formal verdicts
A Historical component AvgR>0; B Recent Combined component AvgR<0; C COMPONENT_DECAY<0; D its valid CI upper<0; E RELATIVE_DECAY<0; F relative Holm-adjusted p<0.05; G all sample floors and valid resampling pass. Strict comparisons: equality fails. Only A–G all PASS yields `COMPONENT_DECAY_CANDIDATE`. Otherwise G FAIL => `INSUFFICIENT_SAMPLE`; G PASS and Recent Combined AvgR>0 with negative component decay => `WEAKENED_BUT_STILL_POSITIVE`; G PASS and component/relative decay negative but a CI/Holm condition fails => `WEAK_DECAY_SIGNAL`; otherwise `NOT_SUPPORTED`. Recent-positive components are never stop candidates. All A–G PASS/FAIL shown even for insufficient rows.

## Verification and publication
Validate fixed hash/28 identities/16,298 count; exact 10 target identities and counts; exhaustive unique eligible assignment and explicit NORMAL exclusion; weekday and nominal-day unit tests including weekday, Saturday/Sunday 25/30 forward-Friday and unshifted 20; every period boundary; independently aggregate AvgR/TotalR/PF; independently spot-check cluster-bootstrap draws/CI and Holm; deterministic representative earliest/latest trade for each strategy/component versus original log. Halt rather than guess on schema or rule mismatch. Commit implementation and verify remote SHA before real-data calculation. Then publish separate Result commit and verify remote SHA. No result-driven changes to this Plan.

Outputs: `docs/82_component_edge_decay_phase1_result.md`; new study-only source/tests; notebook showing all strategy/component periods, contrasts/CIs/adjusted p/verdict and every year, writes CSV to `/content`, Drive save default OFF. Aggregate CSVs `component_edge_decay_phase1_component_period_summary.csv`, `_contrasts.csv`, `_yearly_summary.csv`, `_multiple_comparison.csv`, `_coverage.csv`, `_run_record.csv`; publication manifest with hashes/locations. Trade assignments may remain local/Colab with their hash and size in manifest.

## Future Phase 2, not executed here
Only formal candidates qualify. Exclude one component at a time from the same fixed baseline and compare baseline versus each single-exclusion variant. Total Profit / terminal wealth increase is primary; DD improvement alone with profit loss is not adoption grounds. Money Simulation and integration with live 27 strategies or Volatility R2 require later separate Plans.
