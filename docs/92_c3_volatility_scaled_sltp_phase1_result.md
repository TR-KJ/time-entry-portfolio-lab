# 92 C3 Volatility-Scaled SL/TP Phase 1 — Result

Date: 2026-09-23 JST  
Branch: `research/c3-volatility-scaled-sltp-phase1`  
Preregistered Plan commit: `9bcf394f9c0426ca9a07641fda8e81ca71a6912d`  
Frozen implementation commit: `758037448297997b010444d882c315d723a2b0ce`  
Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`

## Decision

**`INSUFFICIENT_FEATURE_COVERAGE`**

C3 is not a formal candidate. Primary ATR coverage was 92.5112%, below the preregistered 95% requirement. The primary outcome was also adverse: Total R fell by 141.8587R and the paired week-cluster bootstrap interval was entirely below zero. RV20 robustness was likewise adverse. Do not run C3 Phase 2 and do not change EA, SET, RunId, VPS, risk tables, or live operation.

## Hard reconciliation and inputs

R0 reproduced the frozen baseline before any volatility-scaled result was calculated:

| Scope | Anchors | Replayed | Mismatches | Status |
|---|---:|---:|---:|---|
| All 28 strategies | 16,298 | 16,298 | 0 | PASS |
| Active 27, excluding Strategy 22 | 15,837 | 15,837 | 0 | PASS |

All 56 M1 files passed the frozen manifest audit for filename, SHA-256, row count, and raw date range. Trades used completed JST daily data available before entry. Missing feature history retained the trade with a 1.00 fallback factor.

## Portfolio result

| Variant | Trades | Total R | Delta Total R | Avg R | PF | Win rate | Worst week R | Max DD R |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R0 | 15,837 | 1,360.2534 | — | 0.085891 | 1.4065 | 54.6126% | -14.4558 | 29.2115 |
| ATR20 primary | 15,837 | 1,218.3947 | **-141.8587** | 0.076933 | 1.3589 | 54.5305% | -16.8136 | 36.2711 |
| RV20 robustness | 15,837 | 1,187.2408 | **-173.0126** | 0.074966 | 1.3399 | 54.2716% | -16.6343 | 38.6494 |

For ATR20, average paired delta was -0.008957R per trade. The preregistered 5,000-draw Monday-week cluster bootstrap, seed 20260913, gave a 95% interval of **[-0.013554, -0.004444] R per trade**. For RV20 it was -0.010925R, interval **[-0.015974, -0.005729]**.

## Period stability

| Period | ATR Delta Total R | RV Delta Total R |
|---|---:|---:|
| Historical | -59.5980 | -77.4315 |
| Recent A | -41.1661 | -52.4523 |
| Recent B | -37.6268 | -41.8737 |
| 2026 Monitor | -3.4678 | -1.2551 |
| Recent Combined | -82.2607 | -95.5811 |
| ALL | -141.8587 | -173.0126 |

Every fixed period was negative for both methods. The ATR trade comparison contained 6,611 improved, 6,518 harmed, and 2,708 unchanged trades.

## Feature coverage and scale

| Method | Valid | Fallback | Coverage | Mean scale | Median | Q10 | Q90 | 0.50 cap | 2.00 cap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ATR20 | 14,651 | 1,186 | 92.5112% | 1.0242 | 0.9830 | 0.7503 | 1.3738 | 3 | 327 |
| RV20 | 14,642 | 1,195 | 92.4544% | 1.0256 | 0.9893 | 0.6886 | 1.4553 | 148 | 458 |

The shortfall is concentrated in the initial history needed to build ATR20/RV20 and the preceding 252 completed-day reference window. Those trades remained paired through the frozen 1.00 fallback.

## Gates

| Gate | Result | Evidence |
|---|---|---|
| A | FAIL | ATR ALL Delta Total R was negative |
| B | FAIL | ATR CI lower bound was negative |
| C | FAIL | Historical delta was negative |
| D | FAIL | Recent Combined delta was negative |
| E | FAIL | 0 of 3 eligible recent subperiods were positive |
| F | FAIL | RV ALL and Recent Combined were negative |
| G | FAIL | ATR valid coverage 92.5112% < 95% |
| H | FAIL | Portfolio delta was not positive |

Three strategies had positive exploratory ATR deltas: Strategy 2 (+0.3379R), Strategy 21 (+0.9474R), and Strategy 28 (+1.2912R). Their preregistered concentration diagnostic was 0.5011. These are exploratory only and do not support selective adoption.

## Validation

Five synthetic unit checks passed for prior-252/current exclusion, fallback 1.00, clipping and outward tick rounding, scaled SL/TP with actual-SL R normalization, and TP-absent Time Exit behavior. Independent post-run verification passed 13/13 checks, including paired cardinality, distance reconstruction, TP preservation, aggregate reconstruction, coverage, bootstrap interval, and concentration arithmetic.

The local full paired detail has 31,674 rows, 9,320,666 bytes, SHA-256 `4aa1cbe5c2b07e39d831168b82b4960f68bd55f9e089cbc3d9f69bdef82c1c1a`. It is intentionally excluded from Git because it is a large reproducibility artifact; its hash and size are frozen in the run record.

## Conclusion

The frozen volatility scaling rule reduced Total R, worsened PF and Max DD, and failed every formal gate. C3 stops after Phase 1. Dell Phase 5 remains Global R2 only.
