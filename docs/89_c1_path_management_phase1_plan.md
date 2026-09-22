# 89 C1 Path-Dependent Exit Management Phase 1 — preregistered Plan

Registered 2026-09-22 JST. Branch `research/c1-path-dependent-exit-management-phase1`. This Plan must be committed, pushed, and its remote SHA verified before implementation or outcome calculation. No result-driven changes to rules, thresholds, periods, gates, or significance tests.

## Objective and scope

Test whether one global post-entry stop rule increases Total R over the unchanged 27 active strategies. Ultimate adoption objective is Total Profit / terminal wealth. This phase does not simulate money, change entries, initial SL, TP, scheduled exits, spreads, live deployment, Dell Demo Phase 5, EA, SET, RunId, or VPS. Strategy 22 `22_GA_C_2` is reference only. The 2022–2026 observations have been viewed in prior research and are not a pristine holdout.

## Frozen inputs and hard gate

The sole trade anchor is `daily_stop_baseline_trades.csv`, SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`, 28 strategies and 16,298 trades. Exactly 15,837 anchors from the 27 active strategies must remain after excluding Strategy 22's 461 trades. Candidate entries are never regenerated. Validate identities, strategy metadata, planned entry and scheduled exit, SL, TP, direction, Mode and baseline R before replay.

The source is exactly the 56 files in `results/volatility_phase1/volatility_phase1_input_manifest.csv` (7 symbols × 8), audited again for filename uniqueness, SHA-256, row count, raw first/last timestamp, and OHLC integrity. Use the existing `daily_stop_baseline_revalidation.load_pair` conversion: Europe/Helsinki → Asia/Tokyo → timezone-naive JST. Preserve the GBPAUD 2019 gaps. No broker splice or synthetic bar.

Stage 1 computes C1-R0 only for all 16,298 anchors, then reconciles against the baseline. Compare identity, symbol, direction, Mode, planned entry and exit, actual exit time, reason, and exit delay exactly. Numeric absolute tolerances are entry/open/exit price, SL and TP `1e-9`; pips `1e-6`; R `1e-8`. Require **zero** mismatches, including zero missing bars, before computing R1/R2/R3 outcomes. Report 28-strategy and active 27-strategy counts separately. Halt on any discrepancy; no auto-repair or partial inference.

## Execution and variants

Reuse historical execution conventions: planned JST M1 Open entry; Long fill = Open + fixed spread, Short = Open − fixed spread. Spreads in pips: USDJPY 0.5, EURJPY 1, GBPJPY 2, AUDJPY 1.5, AUDUSD 1.5, EURAUD 1.5, GBPAUD 2. JPY pip = .01, non-JPY = .0001. Ignore CSV spread. Scan M1 High/Low; SL wins a same-bar SL/TP collision. Normal overnight continuation. Time Exit is the exit M1 Open, exact then first available through +4 minutes inclusive; none is a hard failure. Retain all baseline-specific fixes, including UJ12 and event handling encoded in the fixed anchors. Scan the exit M1 bar for SL/TP before Time Exit exactly as the reference does.

One R is the anchor's initial SL distance in pips. All levels are computed from the spread-adjusted entry fill. R0 retains initial SL, TP and Time Exit. R1 `BE50`: completed M1 bar reaches MFE ≥ +0.50R; move SL to 0R from the next M1 bar. R2 `LOCK100`: completed M1 bar reaches MFE ≥ +1.00R; move SL to +0.50R from the next M1 bar. R3 `STAGED`: first +0.50R schedules 0R, then first +1.00R schedules +0.50R. The second stage may be observed in the same bar as the first milestone, but each transition takes effect no earlier than the following M1 bar. A stop can only tighten. Exact threshold touches count. No other milestones, trail, conditions, or parameter search.

At each present M1 bar: apply a stop change scheduled by the previous bar; test current SL; test unchanged TP (SL first on a collision); if still open update favorable/adverse extrema and first milestone timestamps; queue any stop change for the *next present* M1 bar; then apply scheduled Time Exit when applicable. MFE/MAE start at 0R and are updated only on bars that remain open after SL/TP tests. This yields a conservative, specified OHLC path anatomy. On a Time Exit bar, the reference SL/TP scan occurs first; extrema from that bar are descriptive and cannot affect the exit or later decisions. A gap does not interpolate a milestone or retroactively activate a stop.

## Outputs and periods

Record MFE_R, MAE_R and timestamps, first +0.5R and +1.0R timestamps, final baseline R, giveback `MFE_R - baseline_R`, post-milestone loss flags, and each variant's trigger/exit. Pair by fixed `(StrategyNo, EntryTime)`; `TRADE_DELTA_R = variant_R - R0_R`. Primary metric is Total R and Delta Total R, with Avg R and Avg Delta R per trade. Secondary: PF, win rate, AvgWinR, signed AvgLossR, improved/harmed/unchanged counts and conditional mean changes, trigger and exit rates, Worst Day, Worst Week, MaxDD. For daily/weekly safety, group R by JST **entry** date / Monday-start entry week; MaxDD is the largest peak-to-trough drop in cumulative R ordered by actual CloseTime, then StrategyNo and EntryTime, starting at 0. These are unlevered R diagnostics, not money simulation.

Half-open EntryTime periods: Historical `[2015-01-01,2022-01-01)`, Recent A `[2022-01-01,2024-01-01)`, Recent B `[2024-01-01,2026-01-01)`, 2026 Monitor `[2026-01-01,2026-09-10)`, Recent Combined `[2022-01-01,2026-09-10)`, ALL `[2015-01-01,2026-09-10)`. Include Strategy 22 only as a 28-strategy reference.

## Inference and locked gates

For each active global variant, use paired trade deltas grouped by Monday-start JST entry week. Resample occupied calendar weeks with replacement, retaining all paired trades and multiplicity, for 5,000 replicates with NumPy PCG64 seed `20260913` independently reset per variant. Statistic is trade-weighted **Avg Delta R / Trade**: sampled sum of delta divided by sampled number of trades. Use linear-interpolated 2.5/97.5 percentiles for a 95% CI. One-sided positive-tail approximate p = `(1 + number of bootstrap Avg Delta <= 0)/5001`. All three variants form one Holm step-down family, ordered by raw p then R1/R2/R3 for ties. Record raw and adjusted p; these bootstrap-tail p values are approximate, not randomization-test p values.

Global sample sufficiency: ALL, Historical and Recent Combined each need ≥30 paired trades and ≥20 distinct entry weeks. Each of Recent A, Recent B, and 2026 Monitor is eligible for Gate F only if it has ≥30 paired trades and ≥20 weeks. At least two eligible periods are required; insufficient periods do not count as positive. Strategy diagnostics use ≥30 trades and ≥20 weeks for each stated period; otherwise label `INSUFFICIENT_SAMPLE` and make no formal per-strategy selection.

For each R1/R2/R3, `GLOBAL_DYNAMIC_MANAGEMENT_CANDIDATE` requires all:

- A: ALL Delta Total R > 0.
- B: ALL Avg Delta R 95% CI lower > 0.
- C: Holm-adjusted one-sided p < 0.05.
- D: Historical Delta Total R ≥ 0.
- E: Recent Combined Delta Total R > 0.
- F: at least 2 eligible among Recent A, Recent B, 2026 Monitor have Delta Total R > 0.
- G: against R0, none of Worst Day, Worst Week or MaxDD deteriorates beyond its locked allowance: respectively `max(1R, 10% × abs(R0 Worst Day))`, `max(2R, 10% × abs(R0 Worst Week))`, and `max(5R, 10% × R0 MaxDD)`. A more negative Worst Day/Week or larger MaxDD is deterioration. Equality at the allowance passes. These thresholds are portfolio R diagnostics and do not excuse failed profit gates.

Gate priority: `INSUFFICIENT_SAMPLE` if global sample floors fail; `GLOBAL_DYNAMIC_MANAGEMENT_CANDIDATE` iff A–G all pass; `SAFETY_FAIL` if A–F pass and G fails; `UNSTABLE_ACROSS_PERIODS` if A–C pass and D/E/F fails; otherwise `NOT_SUPPORTED`. Interesting individual strategies may be described as `EXPLORATORY_STRATEGY_SIGNAL`, without rule selection or C1 adoption. Do not change thresholds, test family, alpha, or gate definitions after seeing outcomes.

## Validation, publication and next phase

Required tests: source hash/count/time audits, active universe, R0 full reconciliation, same-bar collision, next-bar milestone activation, exact +0.5R/+1.0R boundary, BE/lock transition, missing M1/gap, overnight, TP/SL before milestone, Time Exit and +4-minute fallback, independent extrema and variant calculations, bootstrap CI spot-check, independent Holm, representative manual audit. Implement and push code, verify remote implementation SHA, and only then execute R0. On R0 pass, compute variants, independently validate, and publish result doc, notebook, CSV summaries, validation and publication manifest. Notebook CSVs save to `/content`; Drive save cell defaults OFF. Large trade detail may remain local/Colab with hashes and sizes in manifest. List Plan, implementation and result SHAs, data audits, gates and all requested metrics in final report. If source data are unavailable, report that blocker and do not fabricate metrics or verdict.

Only a formal candidate may enter a separately planned Phase 2 money simulation comparing current 27 + Global Volatility R2 against current 27 + Global Volatility R2 + one global C1 rule. Require higher terminal wealth/Total Profit; DD improvement alone cannot justify adoption. Phase 3 Demo is later and separate. Current Dell Phase 5 remains Global R2 only through completion; no live changes here.
