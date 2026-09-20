# AU China Demand Late-Month Edge Decay Phase 1 — preregistered plan

Registration date: 2026-09-20 JST. Branch: `research/au-china-late-month-edge-decay-phase1`.
Parent: main `1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5`.
This document alone must be committed and pushed, and its remote commit SHA verified, BEFORE any new analysis code is written or outcomes calculated. Plan is immutable thereafter. No result-driven changes of periods, thresholds, comparators or metrics.

## Purpose and scope
Diagnose whether Strategy25 LATE_MONTH Avg R/Trade deteriorated after 2021 and more than its EARLY_MONTH internal control. This phase cannot conclude that trades should be stopped. No portfolio exclusion simulation or money simulation in Phase 1.

## Frozen input and identity
Use existing `daily_stop_baseline_trades.csv` only, never regenerate trades or backtest M1.
SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`.
Exactly 16,298 trades / 28 unique strategy identities; Daily Stop OFF, ATR OFF, Event Candidate C, UJ12 Gotobi and EJ1 overlap fixes incorporated. Source found at Desktop/Daily Stop検証; SHA checked before registration without aggregating outcomes. Existing manifest: `results/daily_stop/baseline_run_record.csv`.
Although live has stopped 22_GA_C_2, use the fixed 28-strategy log for research comparability.
Extract only StrategyNo 25, exact name `25_AU_China_Demand`, Pair AUDUSD, Long. Audit unique (StrategyNo, EntryTime), finite R, R=Pips/SL tolerance 1e-8, SL40/TP40, weekday entry 10:00 JST and scheduled exit 15:50 same JST date. Actual close can occur earlier for SL/TP or follow baseline execution delay rules. Audit schema and all identities before calculating results; unexpected identity/time/calendar rules stop execution.
Baseline EntryTime is timezone-naive JST per existing loader `src/research/edge_decay_analysis.py`. Explicitly interpret in Asia/Tokyo; never treat it as UTC. Timezone-aware timestamps are rejected as an unexpected baseline schema.

## Segments (entry JST calendar day)
EARLY_MONTH: 9–15 inclusive. LATE_MONTH: >=25. Every Strategy25 trade must belong to exactly one; any other day is an identity/audit error and halts the run.
No individual dates, revised >=26/27 thresholds, month-end business-day definitions or subdivisions within 9–15.

## Fixed inclusive periods
|Period|Start|End|
|---|---|---|
|Historical|2015-01-01|2021-12-31|
|Recent A|2022-01-01|2023-12-31|
|Recent B|2024-01-01|2025-12-31|
|2026 Monitor|2026-01-01|2026-09-09|
|Recent Combined|2022-01-01|2026-09-09|
|ALL|2015-01-01|2026-09-09|
Use half-open intervals ending the next calendar day. Historical, Recent A/B and Monitor match existing Edge Decay helper; **Recent Combined intentionally differs**: old helper ends 2025-12-31, this user-specified study includes 2026 Monitor. Do not modify/reuse its combined-period constant. 2022–2026 has already been viewed in prior research and is NOT a pristine holdout. No additional periods, rolling windows or start-year searches.

## Metrics
Primary: Avg R/Trade = sum(recorded R)/trade count. Auxiliary: Trades, Total R, PF=sum(positive R)/abs(sum(negative R)), WinRate=count(R>0)/N, AvgWinR and signed AvgLossR. R=0 belongs in N but neither wins nor losses. PF is infinity if gains exist without losses, undefined if both zero; empty means are undefined. Show all 12 segment×period cells, including counts and LOW_SAMPLE=(N<30). Yearly AvgR/TotalR/Trades and same auxiliary metrics for BOTH segments for every year 2015–2026 in one table; 2026 ends September 9. No year selection.

## Primary contrasts
LATE_DECAY = AvgR(LATE, Recent Combined) − AvgR(LATE, Historical).
EARLY_DECAY = AvgR(EARLY, Recent Combined) − AvgR(EARLY, Historical).
RELATIVE_DECAY = LATE_DECAY − EARLY_DECAY.
Negative LATE_DECAY indicates weakened late edge; negative relative contrast indicates greater late deterioration.

## Bootstrap fixed before implementation
Calendar week is Monday 00:00–next Monday 00:00 JST, keyed by Monday's date (not week number alone). Assign periods first; boundary weeks contribute only trades within each period. Resampling population consists of occupied Strategy25 weeks (at least one EARLY or LATE trade); empty weeks do not affect trade-weighted means and are excluded.
Use NumPy Generator(PCG64), seed=20260913, 5,000 replicates. Chronologically sort cluster keys. For each replicate independently sample with replacement exactly the original number of occupied weeks from Historical, then Recent Combined; keep all EARLY and LATE trades and their multiplicity within each sampled week. Compute each segment's sum R / number of trades, not unweighted means of weekly means. Derive all three contrasts from the same paired segment samples, preserving within-week correlation. Historical and Recent samples are independent even if a boundary week has the same Monday key. CI: 2.5th and 97.5th percentiles, NumPy linear interpolation, two-sided 95%, no adjustment for multiple comparisons (single formal contrast C; others descriptive).
After primary replicates, reset PCG64 to the same seed for each robustness comparison in order Recent A, Recent B, 2026 Monitor: independently resample Historical and that recent period in the identical paired-segment procedure. Report each segment's difference versus Historical and CI, plus late lower-than-Historical count out of three. No alternative seeds or CI methods as inferential searches.
Minimum sufficient sample per segment contributing to a contrast: >=30 trades AND >=20 distinct occupied calendar weeks containing that segment, in EACH compared period. Otherwise CI status INSUFFICIENT_SAMPLE; show point estimates and counts, no supported inference. Relative contrast requires sufficiency for all four cells. Any replicate missing a required segment makes that contrast CI INSUFFICIENT_SAMPLE (no redrawing, dropping, imputing or changing denominator).

## Locked formal classification
A: Historical LATE AvgR > 0.
B: LATE_DECAY < 0.
C: LATE_DECAY CI valid and its upper endpoint strictly <0.
D: RELATIVE_DECAY <0.
E: Recent B OR 2026 Monitor LATE AvgR < Historical LATE AvgR (at least one).
All A–E PASS => LATE_MONTH_DECAY_SUPPORTED.
Otherwise, B and D PASS but C not PASS => WEAK_DECAY_SIGNAL (flag any insufficient sample explicitly).
All other combinations => NOT_SUPPORTED. Equality fails strict comparisons; missing quantities fail the respective criterion. Show each A–E PASS/FAIL and C's sample status.

## Validation (before accepting results)
Hash/count/identity/rules checks; unique exhaustive segment assignment using JST; boundary tests for day 8/9/15/16/24/25 and every fixed period edge, leap/year/week boundaries; invalid inputs rejected; independent Decimal/csv reaggregation of AvgR, PF, TotalR and counts; bootstrap independent trade-level cluster-expansion spot-check of replicates and all CI endpoints against aggregate cluster implementation using identical fixed draws. Synthetic tests for week pairing, insufficiency, zeros, strict formal rules. Deterministic representative manual audit: earliest and latest trade for each segment in years 2015, 2021, 2022, 2024, 2026 (if any); compare assignment to original log, not cherry-picked outcomes. Validate period definitions against existing helper and explicitly document combined-period exception. No modification of that helper.

## Deliverables and provenance
New study-only module/tests; `docs/74_au_china_late_month_phase1_result.md`; notebook showing segment×period table, three contrasts and 95% CI, all-year table. CSV prefix `au_china_late_month_phase1_` with segment_period_summary, yearly_summary, contrasts, bootstrap_ci, run_record. Include sample weeks, sufficiency, A–E, seed/replicates, baseline hash, Plan remote SHA, implementation SHA, runtime versions and validation evidence. Commit implementation before real-data calculation. Publish results in a separate commit; verify remote SHAs for Plan, implementation and results. Publication manifest lists file hashes, sizes and locations; result commit SHA reported externally to avoid circular self-hashing.
Assignments and representative raw-trade audits stay local/Colab with a manifest (conservative publication choice); aggregated CSVs and code/docs/notebook on GitHub. Notebook outputs CSVs to /content and has optional Drive save default OFF. Include reproducible execution and clear indication if Colab itself was not run.

## Phase 2 conditional policy (NOT executed)
Only LATE_MONTH_DECAY_SUPPORTED qualifies as a formal Phase 2 candidate. WEAK_DECAY_SIGNAL does not proceed; any future exception needs a new preregistered study.
If supported, a later phase compares Baseline 28-strategy portfolio against the same fixed log excluding ONLY Strategy25 LATE_MONTH trades. Increasing Total Profit / terminal wealth is primary; reduced DD alone cannot justify worsening profit. Any money simulation or integration with Volatility R2 / current 27-strategy live composition requires a separate later phase.

## Protected scope
No changes to Volatility Phase5 Dell Demo Forward, VPS, live, EA/SET, Trend Strength or Pre-Entry artifacts. No entry/risk on-off changes, strategy26/27/28 mixing, TP/SL/timing modifications, external China/news/macro data, weekday/month/season splits, volatility cross-analysis, M1 reruns or portfolio exclusion simulation. No merge into main is required for publication.
