# 90 C1 Path-Dependent Exit Management Phase 1 — Result

Run date: 2026-09-22 JST. Branch: `research/c1-path-dependent-exit-management-phase1`. Frozen Plan commit: `c749bdd848dc0f8e4eb8ec7d572cabbee874ed0a`; final implementation/verification commit: `8ce7b79109f4361cfa71ec068ea0ae2a8bc479d7`. The 2022–2026 observations are previously viewed, not a pristine unseen holdout.

## Source audit and R0 hard gate

Fixed Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`. The 28-strategy file contains 16,298 unique anchors. Excluding only Strategy 22 (`22_GA_C_2`, 461 trades) yields 27 active strategies and 15,837 paired trades. The 28-strategy reference R0 Total R is 1,390.267649494; active R0 is 1,360.253363762.

All 56 audited M1 source files matched the inherited manifest's SHA-256, row count and first/last raw timestamp: 30,371,276 M1 rows and 1,866,361,150 bytes. The manifest's Git blob is `dcaf2e8e0792bc7c336da7ad834f6e53ae0b8b07`. M1 was converted Europe/Helsinki → Asia/Tokyo → naive JST. Known GBPAUD history gaps were preserved. No broker splicing.

R0 reconstructed every fixed trade from M1 before any dynamic calculation. Reconciliation: **16,298/16,298, zero mismatches** across all 28; **15,837/15,837, zero mismatches** across active 27. Identity, timestamps, exit reason, prices, pips and R passed the Plan's fixed tolerances. During development, a tolerance on raw SL/TP comparisons initially produced 12 exit discrepancies; it was removed to match the reference engine, then the complete audit and R0 gate were rerun with zero mismatches. No discrepancy was waived.

## Primary portfolio comparison — active 27

| Variant | Total R | Delta Total R | Avg Delta R/trade | 95% CI for Avg Delta R | raw p | Holm p |
|---|---:|---:|---:|---:|---:|---:|
| R0 baseline | 1,360.253364 | 0 | 0 | — | — | — |
| R1 BE50 | 1,188.606517 | -171.646846 | -0.010838 | [-0.015669, -0.006169] | 1.000 | 1.000 |
| R2 LOCK100 | 1,238.438623 | -121.814741 | -0.007692 | [-0.010590, -0.005057] | 1.000 | 1.000 |
| R3 STAGED | 1,116.523846 | -243.729518 | -0.015390 | [-0.020408, -0.010492] | 1.000 | 1.000 |

CI and p use the preregistered 5,000-draw Monday-start calendar-week cluster bootstrap, seed `20260913`, with paired trade-weighted mean delta. The three one-sided bootstrap-tail p values form one Holm family. They are approximate diagnostic p values. All three observed deltas and both CI bounds are negative.

## Fixed-period stability — Delta Total R

| Period | Trades | BE50 | LOCK100 | STAGED |
|---|---:|---:|---:|---:|
| Historical 2015–2021 | 9,482 | -90.374878 | -52.114521 | -111.866201 |
| Recent A 2022–2023 | 2,688 | -43.085047 | -42.868762 | -76.028139 |
| Recent B 2024–2025 | 2,701 | -30.403828 | -18.867352 | -43.394312 |
| 2026 Monitor through Sep 9 | 966 | -7.783093 | -7.964105 | -12.440865 |
| Recent Combined | 6,355 | -81.271968 | -69.700220 | -131.863316 |
| ALL | 15,837 | -171.646846 | -121.814741 | -243.729518 |

Each variant loses R in every fixed subperiod. No period was chosen after observing the result.

## Benefit, damage and path anatomy

| Variant | Trigger rate | Improved | Harmed | Unchanged | Avg benefit / improved | Avg damage / harmed |
|---|---:|---:|---:|---:|---:|---:|
| BE50 | 37.84% | 809 | 999 | 14,029 | +0.499450R | -0.576279R |
| LOCK100 | 12.99% | 294 | 432 | 15,111 | +0.541572R | -0.650548R |
| STAGED | 37.84% | 971 | 1,241 | 13,625 | +0.498077R | -0.586110R |

Across active baseline trades, 5,992 reached +0.5R and 2,057 reached +1.0R while still open under the fixed OHLC processing order. Of these, 809 ended below 0R after reaching +0.5R, and 295 ended below +0.5R after reaching +1.0R. Mean MFE was 0.515350R; mean maximum giveback was 0.429459R. The variants saved some giveback, but the harmed trades were more numerous and suffered larger average damage. The anatomy is descriptive and did not change any gate.

Strategy diagnostics show positive ALL Delta Total R for 4/27 strategies under BE50, 1/27 under LOCK100, and 2/27 under STAGED. Largest BE50 positive diagnostic was `5_GJ_Port_Log2` (+4.878889R); largest negative was `1_EJ_Log1` (-36.250000R). LOCK100's sole positive was `8_AJ_Core1` (+0.450000R); its largest negative was `2_EJ_NightBlitz_20` (-22.782222R). STAGED's largest positive was `20_EA_1A_MonTue_Short` (+5.532000R); largest negative was `1_EJ_Log1` (-43.240000R). These are `EXPLORATORY_STRATEGY_SIGNAL` observations only; no strategy-specific rule is selected.

## Safety diagnostics and formal gates

| Variant | Worst Day R | Worst Week R | MaxDD R | A | B | C | D | E | F | G | Label |
|---|---:|---:|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| R0 | -12.116818 | -14.455836 | 29.211511 | — | — | — | — | — | — | — | baseline |
| BE50 | -10.493424 | -11.709963 | 28.308003 | F | F | F | F | F | F | P | NOT_SUPPORTED |
| LOCK100 | -11.493424 | -14.455836 | 29.243987 | F | F | F | F | F | F | P | NOT_SUPPORTED |
| STAGED | -10.493424 | -11.709963 | 28.340479 | F | F | F | F | F | F | P | NOT_SUPPORTED |

A = ALL profit gain; B = CI lower > 0; C = Holm p < .05; D = nonnegative Historical delta; E = positive Recent Combined delta; F = positive delta in at least two sufficiently sampled Recent A/B/2026 periods; G = fixed safety allowance. All sample floors were met. Safety Gate G passes, but safety improvements cannot justify lost Total R.

Independent verification passed **38/38 checks**: direct baseline R total, portfolio versus strategy totals, Historical + Recent Combined versus ALL deltas, 15,837-trade paired counts, Holm arithmetic, and 21 representative symbol × variant replays using a separate scalar implementation. Synthetic tests passed for same-bar SL first, exact +0.5R/+1.0R boundaries, next-bar stop activation, BE and lock exits, missing bar/+4-minute fallback, overnight continuation, and TP/SL before milestone. The source audit, R0 zero-mismatch Gate, and independent verification records are published alongside the summary CSVs. Detailed 15,837-trade path anatomy is distributed as a local artifact with SHA-256 in the publication manifest.

## Verdict and deployment scope

**No `GLOBAL_DYNAMIC_MANAGEMENT_CANDIDATE`. Phase 2 money simulation is not authorized by this Plan.** Keep the current 27-strategy exits; do not retune milestones or select rules by strategy inside C1. Any different threshold or strategy-selective design requires a separate preregistered study.

The ongoing Dell OANDA Demo Phase 5 remains Global Volatility R2 only. No P5 EA, SET, RunId, VPS or live change was made.
