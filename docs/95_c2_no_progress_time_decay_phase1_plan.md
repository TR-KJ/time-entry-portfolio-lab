# 95 C2 No-Progress / Time-Decay Exit Phase 1 — frozen Plan

Registered before implementation and C2 outcomes on 2026-09-26 JST. Branch `research/c2-no-progress-time-decay-phase1`, parent C4 result `e6b5c80db7a53c914de71ef167aec8fc0744d69d`. Publish this Plan and verify its remote SHA before coding; publish and verify tested implementation before R0 and NP calculations.

## Question and scope

Does exiting only trades that never achieved +0.25 initial-SL R by 50% of planned holding time improve common portfolio Total R? Primary is NP50; NP75 is the only robustness variant. Do not regenerate candidates, optimize thresholds/checkpoints, adopt strategy-specific settings, run money simulations, or change EA, SET, RunId, VPS, risk table, live configuration or Dell Phase 5 (Global R2 only). Phase 2 requires a separate plan and an eligible candidate. Total Profit / terminal wealth remains the ultimate objective; safety alone cannot justify lower profit. Previously viewed 2022–2026 is not a pristine unseen holdout.

## Frozen inputs and R0 gate

Baseline `daily_stop_baseline_trades.csv` SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`: 28 strategies / 16,298 trades; formal universe excludes Strategy22 only, leaving 27 / 15,837. Strategy22 remains reference/audit only. Audit all 56 files against `results/volatility_phase1/volatility_phase1_input_manifest.csv` by unique filename, SHA-256, rows and raw first/last timestamp. Use existing loader Europe/Helsinki → Asia/Tokyo → naive JST, existing source concatenation, no broker splicing or synthetic gap filling, and known GBPAUD 2019 gap unchanged.

Reuse C1 R0 replay, reconciliation, metrics and paired bootstrap and A3 baseline validation/audit/checkpoint helpers. Reconstruct all 16,298 R0 trades from M1 and reconcile identity, entry/exit time, reason, prices, pips and R under inherited tolerances (prices 1e-9, pips 1e-6, R 1e-8). Require zero mismatches in both ALL28 and ACTIVE27; otherwise stop before NP outcomes.

## Execution and checkpoint ordering

1R is each anchor's initial SL distance. Planned entry and scheduled exit are immutable absolute JST timestamps; actual SL/TP exit never enters planned duration. Compute integer planned minutes; NP50 checkpoint = entry + floor(minutes * 1/2) minutes; NP75 = entry + floor(minutes * 3/4). Require positive duration and checkpoint after entry, including overnight.

Preserve fills: Long = entry Open + fixed spread; Short = entry Open − fixed spread. Spreads in pips: USDJPY .5, EURJPY 1, GBPJPY 2, AUDJPY 1.5, AUDUSD 1.5, EURAUD 1.5, GBPAUD 2. JPY pip .01, others .0001; ignore CSV spread. Preserve Strategy1/12 fixes and all SL/TP. Prior-bar SL/TP scan uses raw float prices and SL-first for simultaneous hits. No second spread on exit.

If R0 closed strictly before checkpoint, copy R0 without assessment. Otherwise MFE = max(0, max prior completed High − entry fill)/SL distance for Long, or max(0, entry fill − min prior completed Low)/SL distance for Short. Include entry bar when completed and every present M1 with timestamp < nominal checkpoint. Do not use checkpoint High/Low or current unrealized R. Decide progress by comparing the favorable extreme directly to entry ± .25*SL distance, inclusive at equality, avoiding subtraction/division roundoff at the exact boundary. Report numeric MFE too. Any prior +.25R achievement means copy R0, even after giveback.

If no progress, resolve checkpoint Open exact, then +1 through +4 minutes. Freeze MFE at nominal checkpoint; do not extend lookback during fallback. Existing SL/TP strictly before executable Open remains effective: if R0 closed before resolved time, copy R0. At executable Open, NP exit takes precedence over that bar's future High/Low, even when R0's historical scan labels exit at the same timestamp. This prevents lookahead. Inherited R0 scheduled-bar SL/TP precedence remains for unchanged trades.

If no executable checkpoint within +4 minutes for an otherwise open no-progress trade, emit missing-checkpoint coverage and stop formal analysis; never drop it or extend fallback. Publish nominal/executable checkpoint, delay and assessment/trigger classification. Missing intrawindow M1 bars are not filled or inferred.

## Metrics and periods

Primary paired delta = NP50 R − R0 R per formal anchor. Publish total/average R, delta, PF, win rate, average win/loss R, trigger count/rate/weeks, improved/harmed/unchanged (delta >1e-9 / <−1e-9 / otherwise), average gain/damage conditional on improvement/harm, SL/TP/original TimeExit/NP exit rates. Worst Day and Worst Week use entry-date and Monday-start entry-week totals, matching C1. MaxDD is positive peak-to-trough cumulative realized R ordered by CloseTime, StrategyNo, EntryTime, starting at zero; it is not monetary or mark-to-market drawdown.

Fixed EntryTime periods: Historical [2015-01-01,2022-01-01), Recent A [2022-01-01,2024-01-01), Recent B [2024-01-01,2026-01-01), 2026 Monitor [2026-01-01,2026-09-10), Recent Combined [2022-01-01,2026-09-10), ALL [2015-01-01,2026-09-10).

Paired calendar-week cluster bootstrap, occupied Monday-start JST entry weeks; keep all trades of a sampled week together. 5,000 replicates, NumPy PCG64 seed 20260913 restarted per period/variant; mean delta = sampled delta sums / sampled trade counts; linear 2.5/97.5 percentiles. No Holm correction for one formal primary. NP75 CI and strategy results are descriptive.

## Trigger and recovery diagnostics

For actual triggers show count/weeks, baseline/NP AvgR/TotalR, delta and improved/harmed/unchanged. Recovery flags overlap: final baseline R >0, >=.50, later TP, later SL, TimeExit positive/negative/zero. NEVER_RECOVERED means final baseline R<=0 (final-outcome proxy, not absence of temporary positive excursion); RECOVERED_POSITIVE means final R>0. Rates divide by triggers only; undefined when none. No recovery-based gate.

All 27 strategies: total count, trigger count/rate/weeks, baseline/NP trigger AvgR, total/mean delta, recovery and TP rates. Strategy eligibility requires >=30 triggers across >=20 entry weeks. Positive eligible strategy delta is EXPLORATORY_STRATEGY_SIGNAL only, never selective adoption. C1 milestone/giveback comparison remains descriptive.

## Formal gates and labels

Candidate requires all A–H plus zero missing executions and passing validation:

- A: ALL NP50 TotalR > R0 TotalR.
- B: ALL paired AvgDeltaR CI lower >0.
- C: Historical NP50 DeltaTotalR >=0.
- D: Recent Combined NP50 DeltaTotalR >0.
- E: Recent A/B/2026 eligibility = >=30 NP50 triggers across >=20 entry weeks. Require at least two eligible periods and at least two eligible positive DeltaTotalR periods. Ineligible = INSUFFICIENT_SAMPLE.
- F: NP75 ALL DeltaTotalR >=0 AND Recent Combined DeltaTotalR >=0 (both required).
- G: ALL NP50 >=200 triggered trades and >=100 trigger entry weeks.
- H: for ALL and every fixed period, NP50 worst-day loss magnitude, worst-week loss magnitude and MaxDDR each <=1.10 times its R0 counterpart, with 1e-9 tolerance. Loss magnitude = max(0,-WorstR); if baseline magnitude zero, allow no deterioration. No tradeoff across measures or periods.

Label priority: INSUFFICIENT_TRIGGER_SAMPLE if G fails; NO_PROGRESS_EXIT_CANDIDATE if all pass; NOT_SUPPORTED if A or B fails; UNSTABLE_ACROSS_PERIODS if C/D/E fails after A/B/G pass; ROBUSTNESS_FAIL if F fails after A–E/G pass; SAFETY_FAIL if H alone fails. Data/coverage/validation failures stop with VALIDATION_FAIL. Phase2Eligible true only for NO_PROGRESS_EXIT_CANDIDATE; no Phase 2 run now.

## Validation and publication

Before outcomes test planned duration, 50/75 rounding, overnight, Long/Short MFE/spread, exact threshold, giveback, completed-bar lookback, checkpoint Open precedence, earlier SL/TP, same-bar SL-first, +4 fallback and absent checkpoint, trigger/recovery classification, paired/bootstrap formulas. Independently recompute representative trades directly from M1 including both directions, trigger/nontrigger, fallback if present and all strategies; check every stored paired delta/trigger/recovery, portfolio/period totals, source hashes and bootstrap CI.

Commit Plan first, implementation/tests/notebook second, then results/verification/result doc/publication manifest. Large trade detail stays local with published bytes/SHA-256. Notebook displays audit, R0, coverage, portfolio, periods, CI, triggered/recovery/NP75/strategy, A–H, verdict and eligibility. Colab outputs `/content`; Drive save defaults OFF. Stop unsupported C2 without threshold/checkpoint expansion.
