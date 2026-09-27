# 99 C6 Portfolio Signal Crowding Phase 1 — preregistered Plan

2026-09-27 JST. Branch `research/c6-portfolio-signal-crowding-phase1`, parent C2 v2 Result `c77fb194dd9c606577b05aaf53f2bb0714d941e0`. Commit/push Plan and verify remote SHA before implementation; commit/push tested implementation and verify remote SHA before crowding outcomes. No outcome-driven changes.

## Fixed inputs and scope

Use fixed `daily_stop_baseline_trades.csv`, SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`, 28 strategies / 16,298 trades. Exclude Strategy22 from both observations AND the signal timeline, giving 27 / 15,837. Reuse inherited loader metadata validation; preserve every trade outcome. No reconstruction of candidate signals or M1, positions, exposure, filters, directions or new volatility features.

Reuse the full active-trade assignment exported by C4: `c4_vol_change_phase1_trade_assignments_local.csv`, bytes 3,756,484, SHA-256 `49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021`. This was validated in C4 against Phase2 reference `0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc`. Require exact hash, all 15,837 one-to-one StrategyNo/EntryTime identities and agreement of Strategy/Symbol/R with baseline. Regress primary-quintile assignments against every applicable active primary row of the saved audit and Strategy×Q count/TotalR references (`research_inputs/c4_reference_*`). Do not recompute R2. Map only the inherited INSUFFICIENT_VOL_HISTORY category to `R2_UNAVAILABLE`, retaining those trades. Valid Q categories Q1–Q5 unchanged. Any unexpected category, duplicate, missing identity or regression mismatch stops C6.

## Signals and windows

Signal = one actual baseline Entry event. Naive JST absolute timestamps. For each anchor t, count all other active events with timestamps in inclusive [t−6h,t] and [t−12h,t]. Subtract exactly its own event; include all same-timestamp peers, all symbols/directions, same-strategy earlier events, and already-closed trades. Simultaneous peers are symmetric; no strategy ordering for features. Count same-timestamp other signals separately. Sort stably by timestamp then identity for reproducibility only. Include weekend/closure elapsed time literally; no trading-hour compression. Never use future events. Features computed once from the complete active timeline; period subsets and leave-one-strategy-out retain these fixed features. This is signal concentration conditional on the 27-strategy portfolio, not a simulated reduced portfolio.

## Estimators

Primary additive OLS: R = intercept + Strategy FE + R2 category FE + beta6*SIGNAL_COUNT_6H. Strategy and Q are separate main effects, not Strategy×Q interaction. Intercept plus reference-coded dummies (sorted category first omitted); raw integer crowding, no bins, clipping or threshold. beta is R per additional other signal. Estimate by Frisch–Waugh–Lovell residualization against FE, algebraically equivalent to OLS. Gram-matrix Moore–Penrose inverse rcond=1e-12 accommodates absent levels in bootstrap. Require residual crowding sum of squares >1e-10*max(1, unadjusted weighted sum of squared crowding); otherwise beta unidentifiable. Sign uses tolerance 1e-12: below −tol negative, above +tol positive, otherwise zero.

Raw direction is the unadjusted OLS slope R~intercept+count, not a selected high/low bucket difference. Publish each observed integer count with N/AvgR/TotalR/PF/WinRate/AvgWinR/AvgLossR, without tail grouping. No strict monotonicity requirement.

Strategy equal-weight robustness averages raw within-strategy R~count slopes over eligible strategies (>=30 trades, >=20 occupied entry weeks, >=3 distinct counts). Also display within-strategy Q-adjusted slopes when identifiable; these do not replace the preregistered raw equal-weight estimator. No strategy-level CIs required; label strategy results exploratory, no adoption.

12h uses the identical additive FE model. Same nonzero sign is required; its CI exclusion of zero is descriptive only. LOSO omits each strategy's observations from the model (27 fits), preserving full-portfolio crowd features. Require every resulting beta identifiable and the same nonzero sign as ALL; zero or reversal fails H.

## Periods, adequacy and bootstrap

EntryTime periods: Historical [2015-01-01,2022-01-01), Recent A [2022-01-01,2024-01-01), Recent B [2024-01-01,2026-01-01), 2026 Monitor [2026-01-01,2026-09-10), Recent Combined [2022-01-01,2026-09-10), ALL [2015-01-01,2026-09-10). 2022–2026 is previously viewed, not a pristine unseen holdout. Compute windows on full timeline before filtering periods.

G requires all 15,837 formal trades, >=10 eligible strategies for 6h equal weight, >=4 distinct 6h counts in ALL, largest count frequency <90%, and at least 2 distinct counts plus identifiable adjusted beta in both Historical and Recent Combined. Also require valid 6h ALL bootstrap CI. Recent subperiod eligible for E: >=200 trades, >=20 occupied entry weeks, >=10 strategies, >=4 distinct 6h counts, largest frequency <90%, and identifiable adjusted beta. Ineligible periods are INSUFFICIENT_SAMPLE; require at least two eligible and at least two eligible with ALL sign.

Calendar-week cluster bootstrap: Monday-start JST Entry week; 5,000 draws, PCG64 seed 20260913 restarted per period/feature; draw occupied weeks with replacement, all their observations with multiplicity. Re-estimate additive FE beta in EVERY replicate. Precomputed week-level cross-products are an exact computational shortcut, not a raw-mean bootstrap. Missing FE levels use pseudoinverse; unidentifiable replicates invalid. Require >=4,750 finite replicates for a CI, otherwise CI undefined. Linear 2.5/97.5 percentiles. Save bootstrap draws locally for independent spot-checks. No Holm correction for the one formal primary.

## Frozen formal gates and labels

- A: ALL raw 6h slope and adjusted beta6 have the same nonzero sign.
- B: ALL adjusted beta6 95%CI strictly excludes zero.
- C: eligible-strategy equal-weight raw 6h slope has ALL beta6 sign.
- D: Historical and Recent Combined beta6 both have ALL sign.
- E: at least two eligible Recent A/B/2026 and at least two have ALL sign.
- F: ALL beta12 has ALL beta6 sign (12h CI descriptive).
- G: adequacy and estimability rules above pass.
- H: all 27 LOSO betas retain ALL nonzero sign.

Label priority: INSUFFICIENT_CROWDING_VARIATION if G fails; SIGNAL_CROWDING_SUPPORTED_NEGATIVE/POSITIVE if A–H all pass; NOT_SUPPORTED if A or B fails; UNSTABLE_ACROSS_PERIODS if D or E fails after A/B/G pass; ROBUSTNESS_FAIL if C, F or H fails after A/B/D/E/G pass. Data or validation failure stops with VALIDATION_FAIL. Phase2Eligible only for a supported label. No Phase 2 now.

## Diagnostics, validation and publication

Publish 6h/12h min/max/mean/median/p05/p25/p75/p95/p99, distinct counts/frequencies, by strategy/period. Simultaneous diagnostic buckets 0,1,2,>=3 (descriptive only), plus symbol metrics and 27 LOSO fits. All 27 strategy diagnostics retained; no selective adoption, windows/threshold searches or risk choices.

Test inclusive 6h/12h boundaries, self exclusion, simultaneous symmetry, Strategy22 exclusion, cross midnight/weekend, identity duplication, unavailable category, additive FE versus independent OLS, rank deficiency, equal-weight eligibility and bootstrap week multiplicity. Independently calculate counts for all anchors via direct timestamp comparisons, regress R2 references, check raw/adjusted/equal/period/LOSO slopes by a separate direct least-squares implementation. Verify saved bootstrap percentiles and direct row-weighted refits for at least the first 32 ALL replicates per feature and first 8 per other period. Audit representative low/medium/high crowd, simultaneous/multi-symbol events without outcome-based selection.

Outputs under `results/c6_signal_crowding_phase1/`; large trade assignments/bootstrap draws local with SHA/bytes. Notebook displays all requested audit/distribution/raw/adjusted/CI/equal/period/12h/batch/strategy/symbol/LOSO/gate/verdict/eligibility tables, CSVs under `/content`, Drive save OFF. Result doc next numbered `100`. Preserve existing studies. No Entry Skip, risk/SL/TP/Time Exit/Global R2 table changes, no money simulation, no EA/SET/RunId/VPS/Demo/live change; Dell Phase 5 remains Global R2 only. If unsupported, stop without new windows or thresholds.
