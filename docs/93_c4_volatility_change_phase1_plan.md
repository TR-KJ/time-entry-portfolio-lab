# 93 C4 Volatility Change / Compression–Expansion Phase 1 — preregistered Plan

Registered 2026-09-26 JST. Branch `research/c4-volatility-change-phase1`, based on C3 Result `212ed52c1ec11b32a64f951406745055014de83b`. Commit and publish this Plan, then verify its remote SHA before implementation or outcome calculation. No outcome-driven change to features, state boundaries, estimator, weights, eligibility, periods, gates, or labels.

## Objective and protected scope

Test whether recent volatility change adds common portfolio information beyond Strategy identity and the existing Global R2 volatility-level quintile. Phase 1 is diagnostic only. Keep all entries, R outcomes, SL, TP, Time Exit, strategy enablement, risk, Global R2 table, event filters, EA, SET, RunId, VPS, Dell Phase 5, and live operation unchanged. The primary objective remains higher Total Profit / terminal wealth, but no money simulation is permitted here. The 2022–2026 periods are previously viewed and are not a pristine holdout.

## Frozen sources and universe

Use only `daily_stop_baseline_trades.csv`, SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`, containing 28 strategies and 16,298 fixed trades. Do not regenerate trades. Formal analyses exclude only Strategy 22's 461 trades, leaving 27 active strategies and 15,837 trades; Strategy 22 is reference-only.

Audit exactly the 56 M1 files in `results/volatility_phase1/volatility_phase1_input_manifest.csv` by unique filename, SHA-256, row count, and raw first/last timestamp. Convert Europe/Helsinki to Asia/Tokyo and then timezone-naive JST. Preserve the known GBPAUD 2019 gaps; no broker splice or synthetic bars.

Freeze feature sources by SHA-256: `volatility_phase1.py` `65ef361509e5bb404be02bfb0d1bdefbc6f59acbe8a557cdee030dd3a69116a1`, `volatility_phase1_frozen_inputs.json` `bfc4b372247bc8def18f4a3768d855285559ffed2782de73737fda4eafb5c61b`, and `volatility_phase2.py` `c6d1b6d3380c70970d8b353b632b6f4f20a9c9aff17c5ff1347dde1d3c605428`. Existing R2 reference commit is `0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc`; its run record freezes the unavailable full-assignment hash `077be95f9796b3cd00568992316447f7f02116618b8d6b5d9eabbb2c0da14126`. Regenerate R2 assignments with the frozen source and require exact agreement for every stored audit row plus exact strategy × period × method × quintile counts, Total R, and Avg R from that commit. Any mismatch stops C4.

## Completed-day features and no lookahead

A trading day is an actual JST calendar date containing M1 bars. D1 Open/High/Low/Close are first/max/min/last M1. `TR=max(High-Low, abs(High-prevClose), abs(Low-prevClose))`. Primary values are simple rolling means: `ATR5=mean(latest 5 TR)` and `ATR20=mean(latest 20 TR)`, with `ATRChange=ATR5/ATR20`. Robustness uses daily log close returns and the inherited sample standard deviation (`ddof=1`) annualized by `sqrt(252)`: `RV5=std(latest 5 returns)*sqrt(252)`, `RV20=std(latest 20 returns)*sqrt(252)`, and `RVChange=RV5/RV20`. Annualization cancels in the ratio but remains in the stored components.

For each entry, assign the most recent completed D1 row strictly before its JST entry date. Require `AvailableAt <= EntryTime` and `LastM1 + 1 minute <= EntryTime`. Current ratio and all 252 preceding completed-day ratios must be finite and positive. Reference indices are `[current_index-252,current_index)`, excluding Current.

The exact midrank numerator is `N=2*count(reference<Current)+count(reference==Current)` out of 504. State boundaries use integer arithmetic: COMPRESSION when `N<168`; NEUTRAL when `168<=N<336`; EXPANSION when `N>=336`. Thus exact one-third is NEUTRAL and exact two-thirds is EXPANSION. Invalid Current is `CURRENT_UNAVAILABLE`; fewer than 252 prior rows is `REFERENCE_LT_252`; invalid/nonpositive references are `REFERENCE_NONFINITE` or `REFERENCE_NONPOSITIVE`. Trades remain in coverage counts but cannot enter state contrasts.

## Existing R2 level assignment

For each trade use the inherited primary ATR20 R2 quintile Q1–Q5 based on the same prior-252 midrank definition and the frozen Phase 2 equality rules. Both ATRChange primary and RVChange robustness are adjusted by the **primary ATR20 R2 quintile**, because the formal question asks for information incremental to the deployed Global R2 level. Trades without a valid primary R2 quintile are excluded from adjusted effects and reported separately. No R2 boundaries are changed.

## Raw diagnostics

For COMPRESSION, NEUTRAL, and EXPANSION show Trades, Total R, Avg R, PF, WinRate, AvgWinR, and AvgLossR for each method and fixed period. Define `RAW_DELTA=AvgR_EXPANSION-AvgR_COMPRESSION`. Neutral is descriptive only; no alternate primary contrast.

## Frozen adjusted estimators

Formal strata are `StrategyNo × primary R2 Quintile`, at most 135 for active strategies. Formal contrasts omit Neutral.

The primary estimator is the coefficient on binary Expansion in an OLS regression containing a fixed intercept for every stratum and using every stratum with at least one Expansion and one Compression trade. It is computed by the mathematically equivalent within-stratum formula:

`d_s = meanR(E,s)-meanR(C,s)`

`w_s = nE_s*nC_s/(nE_s+nC_s)`

`BETA_FE = sum(w_s*d_s)/sum(w_s)`.

This weighting is frozen. Strata without both states contribute zero identification weight. The primary estimate is undefined if no contributing stratum exists.

For equal-weight robustness, an informative stratum requires `nE>=20` and `nC>=20`. Define `BETA_EQUAL=mean(d_s)` across informative strata only. Formal representativeness requires at least 20 informative strata and at least 10 distinct active strategies in ALL. Equal-weight estimates are undefined when no informative stratum exists.

## Fixed periods and period eligibility

Use half-open EntryTime periods: Historical `[2015-01-01,2022-01-01)`, Recent A `[2022-01-01,2024-01-01)`, Recent B `[2024-01-01,2026-01-01)`, 2026 Monitor `[2026-01-01,2026-09-10)`, Recent Combined `[2022-01-01,2026-09-10)`, and ALL `[2015-01-01,2026-09-10)`.

Historical and Recent Combined must each have a defined FE effect for Gate D. A Recent A/B/2026 subperiod is eligible for Gate E when it has at least 10 informative strata, at least 5 represented active strategies, at least 30 Expansion trades, and at least 30 Compression trades. Ineligible subperiods are `INSUFFICIENT_SAMPLE`, excluded from the same-sign numerator and denominator. Gate E requires at least two eligible subperiods and at least two eligible subperiods with the ALL sign.

## Cluster bootstrap

For each method and period, cluster by Monday-start JST entry week. Reinitialize NumPy PCG64 seed `20260913`; for 5,000 replicates sample the period's occupied weeks with replacement, retain all sampled trades with multiplicity, and recompute `BETA_FE` from the sampled Strategy × R2 strata. A replicate without an estimable effect is invalid; require at least 4,750 valid replicates for a CI. Use linear 2.5/97.5 percentiles. Compute equal-weight bootstrap analogously using the frozen `nE>=20,nC>=20` rule within each resample; its CI is descriptive and not a formal gate.

## Coverage and formal gates

Feature coverage is valid state / 15,837 active trades. Gate G requires both ATRChange and RVChange coverage >=90%, zero `SOURCE_MISSING`, and zero `CALCULATION_ERROR`. Structural initial-history shortages are reported separately and are not data errors. Gate H requires the ALL primary ATR method to have at least 20 informative strata and at least 10 represented active strategies.

Let `sign(x)` be +1 or -1; zero/undefined has no sign. `VOLATILITY_CHANGE_SUPPORTED` requires all A–H:

- A: primary ATR RAW_DELTA and BETA_FE have the same nonzero sign.
- B: primary ATR BETA_FE 95% CI excludes zero.
- C: primary ATR BETA_FE and BETA_EQUAL have the same nonzero sign.
- D: Historical and Recent Combined primary ATR BETA_FE are defined and have the ALL sign.
- E: at least two Recent A/B/2026 periods are eligible and at least two have the ALL sign.
- F: RVChange ALL BETA_FE is defined and has the primary ATR ALL sign. RV CI exclusion is descriptive, not required.
- G: frozen coverage and data-quality rule above passes.
- H: frozen ALL informative-strata representativeness rule above passes.

Label priority is: `INSUFFICIENT_FEATURE_COVERAGE` if G fails; `INSUFFICIENT_STRATA_COVERAGE` if H fails; `VOLATILITY_CHANGE_SUPPORTED_EXPANSION` or `VOLATILITY_CHANGE_SUPPORTED_COMPRESSION` if A–H all pass; `ROBUSTNESS_FAIL` if A–E/G/H pass and F fails; `UNSTABLE_ACROSS_PERIODS` if A–C/F/G/H pass and D or E fails; otherwise `NOT_SUPPORTED`. Equality at zero fails sign gates; CI touching zero fails B.

## Diagnostics, validation, and stopping rule

Publish strategy, R2-quintile, stratum, state-distribution, and period diagnostics without selective adoption. Strategy-specific findings are `EXPLORATORY_STRATEGY_SIGNAL` only. Q-specific application is prohibited.

Validate baseline hash/universe/exclusion, all M1 manifest fields, D1 generation, ATR5/20 and ratio, RV5/20 and ratio, prior-252/current exclusion, midrank and exact boundaries, no-lookahead, inherited R2 assignments, stratum membership, independent raw and FE/equal estimators, clustered CI, and representative dates. Large trade assignments may remain local with frozen size/hash.

Only a supported label may proceed to a separately preregistered Phase 2 comparing current 27 + Global R2 against current 27 + Global R2 + C4. Do not select risk multipliers or run money simulation now. If unsupported, stop C4 without period, threshold, ratio, or feature searches. Dell Phase 5 remains Global R2 only; no EA, SET, RunId, VPS, risk table, Demo, or live change.
