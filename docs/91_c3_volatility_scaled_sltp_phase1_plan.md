# 91 C3 Volatility-Scaled SL/TP Phase 1 — preregistered Plan

Registered 2026-09-23 JST. Branch `research/c3-volatility-scaled-sltp-phase1`, based on C1 Result `9f14c906921e7e4d792a32c02dd439b7e8192b41`. Commit and push this Plan and verify its remote SHA before C3 implementation or outcome calculation. No result-driven changes to features, scale, caps, periods, gates, or labels.

## Objective and protected scope

Test whether one common entry-time volatility scaling principle raises Total R across the current 27 active strategies. Keep fixed entry candidates/times, direction, spread, scheduled Time Exit, original SL/TP ratio, and all baseline-specific fixes. V1 scales both SL and existing TP by one frozen factor; strategies without TP keep no TP and scale SL only. No entry regeneration, strategy-specific rule, coefficient/period/cap search, risk-percent change, money simulation, or live change. Final objective is higher Total Profit/terminal wealth; DD alone cannot justify lower profit. 2022–2026 is previously viewed, not pristine unseen holdout.

## Frozen sources and R0 gate

Use only `daily_stop_baseline_trades.csv`, SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`: 28 strategies/16,298 anchors. Formal universe excludes only Strategy 22's 461 trades, leaving 27/15,837. Candidate entries are never regenerated. Reuse the C1 fixed-anchor loader/replay conventions.

Use exactly the 56 files in `results/volatility_phase1/volatility_phase1_input_manifest.csv`, Git blob `dcaf2e8e0792bc7c336da7ad834f6e53ae0b8b07`; recheck unique filename, SHA-256, rows and raw first/last time. Convert Europe/Helsinki → Asia/Tokyo → naive JST; preserve GBPAUD 2019 gaps; no splice or synthetic bars.

Stage 1 reconstructs R0 and requires zero mismatches for both 16,298 reference and 15,837 active trades before V1/RV calculation. Compare identity, pair, direction, Mode, entry/scheduled/actual exit, reason and delay exactly; absolute tolerances: prices/SL/TP `1e-9`, pips `1e-6`, R `1e-8`. Halt on any mismatch; never waive or auto-correct.

## Frozen daily features and availability

Reuse `volatility_phase1.make_daily`, `features`, and completed-day assignment. A trading day is an actual JST calendar date with M1 bars; D1 Open/High/Low/Close are its first/max/min/last M1. `TR=max(High-Low, abs(High-prevClose), abs(Low-prevClose))`; ATR20 is the simple mean of 20 TR values. RV20 is sample standard deviation (`ddof=1`) of 20 log close returns × sqrt(252). For each entry, use the most recent D1 row strictly before its JST entry date; require `AvailableAt <= EntryTime` and `LastM1 + 1 minute <= EntryTime`.

For method ATR or RV, Current is that assigned completed day's ATR20/RV20. Reference is exactly the preceding 252 completed trading-day feature values, indices `[current_index-252,current_index)`, excluding Current. `RelativeVol=Current/median(reference252)`. A feature is VALID only when Current and all 252 reference values are finite and positive. Otherwise `ScaleFactor=1.00`, `FeatureStatus=FALLBACK`, with reason `CURRENT_UNAVAILABLE`, `REFERENCE_LT_252`, `REFERENCE_NONFINITE`, or `REFERENCE_NONPOSITIVE`. Trades are retained. Formal coverage is active VALID trades / 15,837 and must be **>=95%** for primary ATR. RV coverage is disclosed; robustness cannot pass if its ALL or Recent Combined comparison is incomplete.

## Scaling, tick rounding and execution

Primary V1 uses `clip(RelativeVol,0.50,2.00)` from ATR20. Robustness uses the identical formula with RV20. Factor freezes once at entry. Original distances are multiplied in pips. MT5 price precision in the frozen files implies tick size 0.001 for JPY pairs and 0.00001 otherwise, equal to **0.1 pip**. Round each scaled SL and existing TP distance independently upward to the next tick using integer decimal arithmetic: `ActualDistancePips = ceil(OriginalPips × ScaleFactor / 0.1 - 1e-12) × 0.1`. This never places a protective/target price closer than requested. No TP is created when original TP is absent. The rounded actual SL is V1's 1R; `R=Pips/ActualSLPips`.

Historical execution remains: planned JST M1 Open; Long fill Open + spread, Short Open − spread; fixed spreads UJ .5, EJ 1, GJ 2, AJ 1.5, AU/EA 1.5, GA 2 pips; JPY pip .01, others .0001; CSV spread ignored; scan M1 High/Low; same-bar SL and TP means SL first; normal overnight; Time Exit at scheduled M1 Open exact through +4 minutes. Scan the exit bar for SL/TP before Time Exit. R0 uses original unrounded distances exactly.

## Fixed periods, metrics and inference

Half-open EntryTime periods: Historical `[2015-01-01,2022-01-01)`, Recent A `[2022-01-01,2024-01-01)`, Recent B `[2024-01-01,2026-01-01)`, 2026 Monitor `[2026-01-01,2026-09-10)`, Recent Combined `[2022-01-01,2026-09-10)`, ALL `[2015-01-01,2026-09-10)`. Pair by `(StrategyNo,EntryTime)` and define `TRADE_DELTA_R=V1_R-R0_R`. Primary is Delta Total R; show Total/Avg R, Avg Delta, PF, WinRate, AvgWin/Loss R and exit rates.

For ALL paired active trades, cluster by Monday-start JST entry week. Reinitialize NumPy PCG64 seed `20260913`, resample occupied weeks with replacement for 5,000 draws, preserving trades/multiplicity, and compute sampled sum delta / sampled trade count. Use linear percentile 2.5/97.5% CI. One formal V1 means no Holm correction. Recent subperiod eligibility requires >=30 paired trades and >=20 entry weeks.

Show scale mean, median, Q10/Q25/Q75/Q90, min/max, exact .50/2.00 cap counts, fallback count, and distributions by symbol, period and method. Strategy diagnostics cover all 27 and TP-present versus TP-absent portfolios separately; no selective adoption.

## Locked gates and labels

`VOLATILITY_SCALED_SLTP_CANDIDATE` requires all A–H:

- A: primary ATR ALL Delta Total R > 0.
- B: primary ATR ALL paired Avg Delta R 95% CI lower > 0.
- C: Historical Delta Total R >= 0.
- D: Recent Combined Delta Total R > 0.
- E: at least two eligible among Recent A, Recent B, 2026 Monitor have Delta Total R > 0.
- F: RV robustness ALL Delta Total R >= 0 and Recent Combined Delta Total R >= 0, with complete paired coverage.
- G: primary ATR VALID coverage >=95%.
- H: calculate each active strategy's signed ALL Delta Total R. If total portfolio improvement is positive, `ConcentrationRatio=max(positive strategy Delta)/sum(positive strategy Deltas)` and require it **<0.70**. If no positive contributions or portfolio Delta <=0, H fails. Zero/negative contributions are excluded from the denominator; report their counts.

Label priority: `INSUFFICIENT_FEATURE_COVERAGE` if G fails; candidate if A–H all pass; `ROBUSTNESS_FAIL` if A–E/G/H pass and F fails; `CONCENTRATION_FAIL` if A–G pass and H fails; `UNSTABLE_ACROSS_PERIODS` if A/B/G pass and C/D/E fails; otherwise `NOT_SUPPORTED`. Strategy positives may be `EXPLORATORY_STRATEGY_SIGNAL` only. Equality fails strict gates and passes nonnegative gates.

## Validation, outputs and later phases

Test baseline/M1 hashes, universe/exclusion, zero-mismatch R0, D1/ATR20/RV20 regression, 252-median exclusion and no-lookahead, formula/caps/tick ceiling, TP-absent behavior, fallback 1.00, same-bar SL first, scaled SL/TP first, Time Exit/+4m/overnight, R normalization, bootstrap spot-check, representative independent ATR/RV trades and concentration arithmetic. Commit/push implementation and verify remote SHA before real R0 and outcomes.

Publish Result 92, notebook and requested `c3_vol_scaled_sltp_phase1_*` summaries, coverage, validation, run record and manifest. Large trade detail may remain local with hash/size. Notebook writes CSV to `/content`; Drive save defaults OFF. Only a formal candidate may enter a separately preregistered Phase 2 comparing current 27 + Global R2 with current 27 + Global R2 + C3, using the same risk amount and SL-based lot sizing. Dell Phase 5 remains Global R2 only; no EA, SET, RunId, VPS, risk table or live change.
