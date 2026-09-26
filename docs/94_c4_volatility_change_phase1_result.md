# 94 C4 Volatility Change / Compression–Expansion Phase 1 — Result

Date: 2026-09-26 JST  
Branch: `research/c4-volatility-change-phase1`  
Plan commit: `954c051ce51c12b7301de82f2ae4613a14f155d3`  
Frozen implementation commit: `48cf2d4898fa2ce6674c4929f2a7bffab21e8a2b`  
Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`

## Decision

**`NOT_SUPPORTED`**

Expansion had a positive raw and Strategy × Global R2 quintile adjusted point estimate, and RV robustness had the same direction. The primary 95% interval included zero, however, and none of Recent A, Recent B, or 2026 Monitor met the preregistered period-level informative-strata threshold. C4 is not a formal candidate. Do not run Phase 2 and do not alter Global R2 or live operation.

## Input and validation gates

- Frozen baseline: 28 strategies / 16,298 trades; formal universe excludes only Strategy 22, leaving 27 / 15,837.
- M1 audit: all 56 files passed filename, SHA-256, row count, and raw start/end checks.
- Existing R2 assignment: 257 stored trade audit rows and 1,400 Strategy × period × method × quintile aggregate rows reproduced from frozen Phase 2 sources.
- Feature calculations use completed JST D1 only, with the current day excluded from each prior-252 reference.
- Five synthetic tests passed. Independent reconstruction passed 20/20 checks, including both 5/20 ratios, state boundaries, raw summaries, fixed effects, equal weighting, coverage, and both bootstraps.

## Coverage and state counts

| Method | Valid | Coverage | Compression | Neutral | Expansion |
|---|---:|---:|---:|---:|---:|
| ATR5/ATR20 | 14,651 | 92.5112% | 5,049 | 4,869 | 4,733 |
| RV5/RV20 | 14,642 | 92.4544% | 5,025 | 4,702 | 4,915 |

Both methods pass the preregistered 90% gate. ATR shortages were 1,021 prior-reference shortages, 78 unavailable current values, and 87 nonfinite reference windows. RV shortages were 1,012, 87, and 96 respectively. Source-missing and calculation-error counts were zero.

## Raw portfolio diagnostic

| Method | State | Trades | Total R | Avg R | PF |
|---|---|---:|---:|---:|---:|
| ATR | Compression | 5,049 | 412.6538 | 0.081730 | 1.4213 |
| ATR | Neutral | 4,869 | 384.3343 | 0.078935 | 1.3854 |
| ATR | Expansion | 4,733 | 489.0598 | 0.103330 | 1.4666 |
| RV | Compression | 5,025 | 402.1609 | 0.080032 | 1.4003 |
| RV | Neutral | 4,702 | 409.6249 | 0.087117 | 1.4274 |
| RV | Expansion | 4,915 | 472.8455 | 0.096205 | 1.4460 |

ATR raw Expansion − Compression was **+0.021600R/trade**. RV raw delta was **+0.016173R/trade**.

## R2-adjusted formal result

| Method | FE adjusted effect | 95% CI | Equal-weight effect | Contributing strata | Informative strata | Represented strategies |
|---|---:|---:|---:|---:|---:|---:|
| ATR primary | **+0.028815** | **[-0.007267, +0.065149]** | +0.030417 | 135 | 95 | 23 |
| RV robustness | +0.017080 | [-0.019994, +0.052982] | +0.029031 | 134 | 98 | 23 |

The positive point estimate remains after controlling for Strategy and Global R2 quintile, but uncertainty is too wide to exclude zero. Equal-weight estimates agree in sign, so the effect is not solely driven by high-frequency strata.

## Period stability

| Period | ATR adjusted | ATR 95% CI | Informative strata / strategies | Formal subperiod eligibility | RV adjusted |
|---|---:|---:|---:|---|---:|
| Historical | +0.021896 | [-0.024184, +0.068047] | 48 / 16 | Eligible | -0.003328 |
| Recent A | +0.029390 | [-0.058789, +0.119468] | 1 / 1 | Insufficient sample | +0.043261 |
| Recent B | +0.036090 | [-0.062456, +0.135457] | 1 / 1 | Insufficient sample | +0.065687 |
| 2026 Monitor | +0.063836 | [-0.047385, +0.172435] | 0 / 0 | Insufficient sample | -0.028109 |
| Recent Combined | +0.031845 | [-0.024428, +0.092775] | 26 / 12 | Eligible | +0.032944 |

Historical and Recent Combined match the positive ALL direction. Gate E fails because the three smaller recent periods do not meet the frozen minimum of 10 informative strata and 5 represented strategies; none enters its numerator or denominator.

## R2 quintile diagnostic

ATR raw Expansion − Compression by R2 level was Q1 +0.0165, Q2 -0.0028, Q3 -0.0359, Q4 -0.0361, and Q5 +0.1415R/trade. RV was Q1 +0.0312, Q2 -0.0340, Q3 -0.0367, Q4 +0.0227, and Q5 +0.0825. This is heterogeneous and does not authorize Q-specific C4 application.

## Strategy diagnostic

ATR raw deltas were positive for 18 of 27 active strategies and negative for 9. Larger positive diagnostics included Strategy 16 (+0.4404R/trade, small sample), Strategy 9 (+0.2135), Strategy 12 (+0.1335), Strategy 19 (+0.1271), and Strategy 11 (+0.1238). Larger negative diagnostics included Strategy 14 (-0.4103, small sample) and Strategy 6 (-0.1795). These are exploratory signals only; there is no strategy-selective adoption.

## Formal gates

| Gate | Result | Evidence |
|---|---|---|
| A | PASS | ATR raw and adjusted effects are both positive |
| B | **FAIL** | ATR adjusted 95% CI includes zero |
| C | PASS | ATR FE and equal-weight effects are both positive |
| D | PASS | Historical and Recent Combined match ALL sign |
| E | **FAIL** | Fewer than two eligible recent subperiods |
| F | PASS | RV ALL adjusted effect is positive |
| G | PASS | ATR and RV coverage exceed 90%; no source/calculation errors |
| H | PASS | 95 informative strata and 23 represented strategies |

## Operational conclusion

C4 stops after Phase 1. No threshold, period, slope, ROC, Q-specific, or strategy-specific follow-up was searched. Phase 2 money simulation was not run. Dell Phase 5 continues with Global R2 only. EA, SET, RunId, VPS, Global R2 risk table, Demo, and live operation are unchanged.

The local trade assignment contains 15,837 rows, 3,756,484 bytes, SHA-256 `49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021`. It is excluded from Git; its size and hash are frozen in the run record.
