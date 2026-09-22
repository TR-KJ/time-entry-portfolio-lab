# A5 Strategy-Selective Volatility R2 — Preregistered Plan
Status: PREREGISTERED BEFORE A5 CODE OR OUTCOME COMPUTATION.
Branch: research/strategy-selective-volatility-r2
Base: A3 implementation 039e3b443e86699d57b52e7ad4dc320fe707d43e.
Docs 87 Plan / 88 Result (Result and performance CSVs remain local; not published).
This Plan is immutable after remote SHA/content verification.

## Objective and scope
Compare exactly four prespecified variants on the existing 27 active strategies. Primary benchmark is R2_GLOBAL, not fixed .90. Optimize Total Profit / Final Wealth; lower DD without increased profit is insufficient. No EA, SET, VPS, live, Phase 5, risk-table, feature, source-trade, or money-engine changes. Phase 5 continues Global R2. Historical retrospective study; 2022–2026 is not pristine unseen holdout.

## Frozen sources and universe
Baseline original 28 strategies / 16,298 trades, SHA256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359. Exclude only 22_GA_C_2 / 461 trades, leaving 27 strategies / 15,837 trades. Preserve original row identities; do not recalculate trades.
Membership source: results/volatility_phase2/volatility_phase2_monotonicity_summary.csv SHA256 598ed582f84f6435cda5d78b4f433a9cccf144375c8aa169cbd2a69400fbdd2e, FULL/Strategy/trade_weighted rows. Phase 2 strategy-quintiles SHA256 4dd39e76acd489cad7630f9bbd010ccd41536246bfa2fdb9e7a70e0e6ef65639. Phase 2 run record declares full assignment SHA256 077be95f9796b3cd00568992316447f7f02116618b8d6b5d9eabbb2c0da14126. Rehash frozen 56 M1 files and inherited feature source before calculation.
Support means literal ORDERED_POSITIVE_SUPPORTED in Phase 2's FULL strategy-level Support column, not a new A5 test. Insufficient means either method LOW_SAMPLE. Opposite direction means either method's Q5MinusQ1AvgR <= 0. BROAD requires at least one method supported, neither LOW_SAMPLE, and both method Q5MinusQ1AvgR > 0. Exclude 22 regardless of Phase 2 label.

STRONG (both methods supported; 8): 1_EJ_Log1; 3_EJ_NightBlitz_21; 4_GJ_Port_Log1; 12_UJ_Short_Core; 19_EA_3_WedThu_Long; 23_GA_F_2; 25_AU_China_Demand; 26_AJ_China_Demand.
BROAD (rule above; 15): 1_EJ_Log1; 2_EJ_NightBlitz_20; 3_EJ_NightBlitz_21; 4_GJ_Port_Log1; 5_GJ_Port_Log2; 6_GJ_Old_Mon; 7_GJ_Mon_Blitz; 8_AJ_Core1; 12_UJ_Short_Core; 19_EA_3_WedThu_Long; 20_EA_1A_MonTue_Short; 21_GA_B_3; 23_GA_F_2; 25_AU_China_Demand; 26_AJ_China_Demand.
No membership changes after outcomes.

## Four variants and features
R0_FIXED_090: .90% every trade, reference.
R2_GLOBAL: Q1 .50%, Q2 .70%, Q3 .90%, Q4 1.10%, Q5 1.30% for every strategy, primary benchmark.
S1_STRONG_ONLY_R2: R2 for STRONG, otherwise .90%.
S2_BROAD_R2: R2 for BROAD, otherwise .90%.
Insufficient history gets .90% for every variant. No further variants or individual strategy adjustments.
Primary feature: inherited JST daily D1 ATR20, 20 TR simple mean, evaluated against prior 252 completed trading days excluding evaluation day, exact midrank quintile. Robustness: inherited 20 log-return sample-standard-deviation realized volatility times sqrt(252). Reuse Phase 1/2/3/4 frozen code and assignment checks; no new indicator, percentile cut, or lookahead.

## Money simulation and periods
Reuse Phase 4 / Phase 3 Decimal40 theoretical uncapped simulator, initial 500,000 JPY, Monday 06:00 JST entry-week start Balance fixed inside week, next-week compounding, PnL=WeeklyBase×RiskPct/100×Pips/SL. Closed-balance DD and inherited day/week denominators. This differs from live EA's Monday 00:00 equity snapshot; no live change.
ALL continuous [2015-01-01, 2026-09-10). Four independent 500,000-JPY resets: Historical [2015-01-01,2022-01-01); RecentA [2022-01-01,2024-01-01); RecentB [2024-01-01,2026-01-01); Monitor2026 [2026-01-01,2026-09-10). Run primary and robustness for all four variants in all five windows.

## Metrics and formal comparisons
For each variant/method/period report Final Wealth, Total Profit, MaxDD %, Worst Day %, Worst Week %, Return/MaxDD, trades, mean/median and percentiles of nominal risk, risk distribution, R2 trade count/share, and quintile counts. Also strategy mean risk/contribution. Formal contrasts are S1−R2_GLOBAL and S2−R2_GLOBAL; R0 is reference. Use unrounded Decimal comparisons.

## Prespecified gates and labels
A: Primary ALL Final Wealth strictly greater than Global.
B: Primary reset Final Wealth >= Global in at least 3/4.
C: Primary RecentB or Monitor2026 strictly greater than Global; display both.
D: Robustness ALL Final Wealth >= Global.
E: Phase 4 safety unchanged: primary ALL MaxDDPct <= R0_FIXED_090 primary ALL MaxDDPct × 1.25; primary ALL WorstDayPct strictly > -20. This is research safety, not live approval.
F: Among RecentA, RecentB, Monitor2026 reset differences, at least 2/3 >= 0. This fixed rule prevents a gain concentrated in Historical alone.
Validation must pass. If A–F fail, no formal candidate. Label priority: SAFETY_FAIL if E fails; GLOBAL_R2_REMAINS_PREFERRED if A fails; UNSTABLE_ACROSS_PERIODS if B/C/F fails; ROBUSTNESS_FAIL if D fails; VALIDATION_INCOMPLETE if validation incomplete. If all A–F pass and selective mean nominal risk > Global, also require the diagnostic risk-budget-matched primary ALL Final Wealth >= Global for SELECTIVE_R2_CANDIDATE; otherwise PROFIT_GAIN_RISK_BUDGET_DRIVEN. If all pass, SELECTIVE_R2_CANDIDATE. Missing inputs/metrics => NOT_RUN_INPUT_MISSING, never infer pass. Matched diagnostic is interpretive only, not a deployable fifth risk table.

## Risk-budget diagnostic
For each selective variant and method separately, on the fixed ALL 27-strategy trade universe compute k = mean(Global nominal risk) / mean(Selective nominal risk), unrounded. Only if selective mean > Global, multiply every selective trade's nominal risk (including fixed/fallback) by constant k. Run same Phase 4 simulator and ALL plus resets with the same fixed k; never recompute k by period. Compare matched ALL wealth to Global. Scale does not alter membership, official R2 table, formal variant family, or deployment proposal. Also show medians, p5/p25/p75/p95, strategy means, R2 counts/shares to identify risk-budget effects.

## Validation and publication
Check baseline hash/28 identities, exclusion only 22/count 461, 27 count 15,837, Phase 2 source hash and exact membership, 56 M1 hashes, inherited Phase 2 assignments, R2 quintile/fallback map, Phase 4 R0 and Global regression, Monday 06 rollover, weekly base/reset tests, independent all-trade Final Wealth and risk mean verification, risk scale, representative week audits, no protected-file diffs. Stop on missing/invalid inputs rather than fabricate.
Sequence: commit/push this Plan; verify remote SHA and file; only then code. Commit/push implementation and verify remote SHA before real A5 outcomes. Run independent verification. Save Result 88, notebook, CSVs and publication manifest locally only, honoring user's prior 掲載不要. Notebook displays membership, definitions, ALL/resets, robustness, risks, matched diagnostic, contributions, gates and verdict; /content exports, Drive save default OFF. Record Plan/implementation SHA, source/output hashes, and note Result SHA is none when unpublished.
