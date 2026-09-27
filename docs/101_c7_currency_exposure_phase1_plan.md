# 101 C7 Currency-Level Exposure Budget Phase 1 — preregistered Plan

2026-09-27 JST. Branch `research/c7-currency-level-exposure-phase1`; parent C6 Result `cf7decc1a880a0bfa0e3db572753ddf550784515`. Push and verify remote Plan SHA before implementation; push and verify remote tested Implementation SHA before actual exposure/outcome analysis. No outcome-driven revisions.

## Inputs and prior audit

Fixed baseline SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`: 16,298 / 28 strategies. Exclude Strategy22 from observations AND position timeline; retain all 15,837 / 27 active trades and unchanged R. Use actual `CloseTime`, never ScheduledExitTime, for position exit. Inherited metadata loader and C6 identity/R2 validation have passed before this Plan; all baseline exits strictly follow entry (zero zero-duration trades). Reuse A2 boundary semantics, C6 R2 verification, additive FE/weekly moment bootstrap, fixed periods and publication framework where matching.

Frozen full C4 R2 assignment `c4_vol_change_phase1_trade_assignments_local.csv`, 3,756,484 bytes, SHA-256 `49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021`. Exact active identities/Strategy/Symbol/R/TradeID must match. All 248 applicable saved audit rows and 135 primary Strategy/Q reference aggregates must match inherited `research_inputs/c4_reference_*`. Unavailable category remains `R2_UNAVAILABLE` as a distinct FE, with 0.90 exposure weight; observed input count 1,186, reason INSUFFICIENT_VOL_HISTORY. Q1–Q5 weights 0.50/0.70/0.90/1.10/1.30. Unexpected category, missing identity, bad hash, invalid direction or symbol stops analysis. No M1 or new signals.

## Frozen exposure definition

Currencies ordered USD/EUR/GBP/JPY/AUD; symbols USDJPY/EURJPY/GBPJPY/AUDJPY/AUDUSD/EURAUD/GBPAUD. Long: +w base, −w quote; Short reverse. Candidate uses own entry-assigned weight; open positions retain their entry-assigned weights. Relative risk-weight units, NOT monetary notional exposure. Currency net vectors are summed before absolute values; GrossBefore is L1 norm of net currency exposure, NOT the sum of position notionals.

At candidate t, use only active trades with `other_entry < t < other_CloseTime`. Entry-equals-t and exit-equals-t excluded; no arbitrary batch ordering. Primary excludes every same-symbol open position regardless of direction. ExposureBefore is cross-symbol vector; GrossAfter is its L1 norm after adding candidate vector. OpenPositionCount counts that same cross-symbol set. HasOpenPosition = 1(count>0), even when net vector cancels to zero.

NIC=(GrossAfter−GrossBefore)/(2*candidate weight). Reverse triangle inequality proves −1<=NIC<=1. Empty exposure gives +1; +1 does not by itself establish preexisting alignment, and a zero net vector can also arise with open positions. Use integer tenth-weight units (5,7,9,11,13) for vector sums and gross differences, dividing for published units/NIC; equal-unit uses integer1. This avoids accumulated cancellation error; no data-driven clipping. Assert range within 1e-10. Raw sign states: NIC<−1e-10 DIVERSIFYING; |NIC|<=1e-10 NEUTRAL; NIC>1e-10 CONCENTRATING. Formal regression retains continuous original NIC without bins. Record per-currency before/after and absolute change, open identities/count and simultaneous peer count.

Robustness1: cross-symbol equal-unit exposure, candidate and every open position weight1. Robustness2: R2-weighted exposure including same-symbol open trades. Each uses its corresponding GrossBefore/count/HasOpen controls and the same candidate R2 FE, with identical strict timing. Both ALL adjusted betas must have Primary's nonzero sign; robustness CI exclusion descriptive only. No combined third variant. Optional batch diagnostic fixed here: at each timestamp with >1 candidate, add their aggregate vectors to ALL-symbol strict-prior exposure and publish per-currency/gross changes; this is descriptive and never enters models/gates.

## Model, rank and estimators

OLS: R = intercept + additive Strategy FE + additive R2 category FE + GrossBefore + OpenPositionCount + HasOpenPosition + beta*NIC. No interactions, direction controls, signal counts or additional features. beta is R per +1 NIC (−1 to +1 change spans two units).

Pre-Plan synthetic audit: 2,000 random physically constructed cross-symbol states, 4 strategy levels, 5 Q levels, the three controls and NIC produced full rank12/12, condition number33.2873, NIC range within floating epsilon of [−1,1]. Thus all recommended controls are retained. Actual/period/strategy/LOSO design audits publish column count, rank, singular values/condition, residual NIC sum of squares. Redundant nuisance columns (including absent bootstrap FE levels) use Moore–Penrose inverse without changing model span; if NIC is unidentifiable, beta is undefined. No post-result control removal. Nuisance columns RMS-scaled (zero column scale1) for numerical stability; this does not change fitted span or NIC coefficient. Use reference-coded additive FE and FWL cross-products, pinv rcond1e-12; residual NIC SS must exceed 1e-10*max(1, weighted raw NIC SS). Independent full-dummy row least squares validates equivalence. Beta sign tolerance1e-12; zero/undefined never passes sign gates.

Raw Gate A is fixed as AvgR(CONCENTRATING)−AvgR(DIVERSIFYING), not raw continuous slope. Require its nonzero sign equals adjusted beta. Neutral group descriptive; no monotonicity requirement. Publish raw NIC slopes additionally. Strategy diagnostic within-strategy adjusted slope retains R2 FE and all three controls when identifiable. Strategy sample flag >=30 trades, >=20 occupied entry weeks, >=10 negative and >=10 positive NIC, >=3 distinct rounded NIC values and identifiable beta; all 27 remain displayed, labelled EXPLORATORY_STRATEGY_SIGNAL or INSUFFICIENT_SAMPLE. No strategy CI requirement or rule adoption.

## Periods, bootstrap and adequacy

EntryTime JST naive periods: Historical [2015-01-01,2022-01-01); Recent A [2022-01-01,2024-01-01); Recent B [2024-01-01,2026-01-01); 2026 Monitor [2026-01-01,2026-09-10); Recent Combined [2022-01-01,2026-09-10); ALL [2015-01-01,2026-09-10). 2022–2026 was previously viewed and is not pristine unseen holdout. Build exposure once on full active baseline; period filtering and LOSO omit observations only, preserving actual full-portfolio states. LOSO is influence diagnosis, not a reduced-portfolio simulation.

Weekly cluster bootstrap: Monday-start occupied Entry weeks; 5,000 resamples with PCG64 seed20260913 restarted per period/variant. Resample weeks with replacement, retaining all rows with multiplicity; refit FULL formal model every replicate using exact summed week cross-products. Undefined fits invalid; require >=4,750 finite fits for CI; otherwise CI undefined. Linear 2.5/97.5 percentiles. Save every beta locally. Run Primary in all six periods; robustness variants ALL only. Single formal primary; no additional hypothesis selection.

NIC distinct counts use rounding12 decimals only for variation audits; regression values unchanged. Variance uses population ddof0; descriptive SD ddof0. H adequacy: ALL exactly15,837 trades/27strategies, at least200 negative and200 positive, >=3 distinct NIC, variance>=0.01, >=500 trades with cross-symbol open positions representing>=10 strategies, identifiable ALL beta and valid Primary CI. Historical AND Recent Combined each require >=30 negative and30 positive, >=20 occupied weeks, >=3 distinct NIC, variance>=0.01 and identifiable beta. Recent A/B/2026 eligibility: >=200 trades, >=20 occupied weeks, >=10 strategies, >=30 negative and30 positive, >=3 distinct NIC, variance>=0.01, >=100 open-position trades and identifiable beta. Ineligible periods flagged INSUFFICIENT_SAMPLE, not sign failures individually; at least two eligible same-sign periods required for Gate D.

## Gates and verdict priority

- A: raw positive-minus-negative AvgR and Primary beta same nonzero sign.
- B: ALL Primary 95%CI strictly excludes zero.
- C: Historical and Recent Combined betas have ALL nonzero sign.
- D: at least two eligible Recent A/B/2026 periods have ALL nonzero sign.
- E: ALL equal-unit adjusted beta has ALL nonzero sign.
- F: ALL same-symbol-included adjusted beta has ALL nonzero sign.
- G: all 27 LOSO betas identifiable and have ALL nonzero sign (zero fails).
- H: exposure/sample/estimability criteria above.

Priority: H fails => INSUFFICIENT_EXPOSURE_VARIATION; all pass => CURRENCY_EXPOSURE_SUPPORTED_POSITIVE/NEGATIVE; A or B fails => NOT_SUPPORTED; C or D fails after A/B/H pass => UNSTABLE_ACROSS_PERIODS; remaining E/F/G failure => ROBUSTNESS_FAIL. Data/independent validation failure stops publication as successful research and is VALIDATION_FAIL. Phase2Eligible only for supported labels, but Phase2 never run in this task.

## Diagnostics, tests and artifacts

Publish distribution min/max/mean/median/SD/Q10/Q25/Q75/Q90, negative/neutral/positive, distinct, fraction at+1, no-open vs open states; by strategy, symbol and period. Raw sign metrics N/AvgR/TotalR/PF/WinRate/AvgWinR/AvgLossR. Per-currency absolute change diagnostics; simultaneous batch diagnostics; all27 strategy rows; all27 LOSO; period and robustness estimates/CIs; design audits; no selective rules.

Synthetic tests: strict entry/exit boundaries, simultaneous exclusion, same-symbol removal/cross inclusion, Strategy22 removal, identity duplicates, long/short mapping, risk/fallback, vector sums/gross/NIC including positive/negative/neutral/empty/net-zero states, both robustness variants, rank/collinearity/estimability, row OLS and week bootstrap equivalence. Independently rebuild all trade exposure vectors via direct timestamp masks and per-position currency dictionaries (no production reconstruction calls), verify all weights and frozen R2 references, all period/robustness/strategy/LOSO betas via full-dummy row OLS. CI quantile check and direct row-weighted bootstrap checks: first32 ALL draws per variant and first8 each other Primary period. Manual audit selects first chronological example of no-open, JPY increase, EUR increase, diversifying, multiple-open and simultaneous batch states without consulting outcomes; save contributing identities/vectors. Hash public and local artifacts.

Result doc `102_c7_currency_exposure_phase1_result.md`; implementation/tests under existing src/research and tests; notebook `c7_currency_exposure_phase1.ipynb` displays all16 requested sections, CSVs default `/content`, Drive save default OFF. Public summaries under `results/c7_currency_exposure_phase1`; full trade assignments/bootstrap draws local with manifest. Retain original baseline R; no M1 replay, entry skip, risk/SLTP/time-exit/table change, money simulation, new thresholds or features. Dell Phase5 GlobalR2-only and EA/SET/RunId/Demo/VPS/live unchanged. Unsupported C7 ends without extension.
