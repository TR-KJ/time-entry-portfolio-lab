# Strategy Selection / Portfolio Pruning IS Result

Status: IS COMPLETE / CANDIDATES FROZEN / OOS NOT VIEWED

IS execution date: 2026-09-11 JST

Branch: `research/strategy-selection-validation`

Analysis: `src/research/strategy_selection_analysis.py` v1.0.0

Source analysis commit:

```text
c95a6b78eb8bd6f11e8f958a60aa91095069134d
```

Candidate freeze commit:

```text
1c265a7e4bd156b1abb8a99e84626047d378be63
```

## 1. Input acceptance

The program read the accepted no-Daily-Stop Baseline Trade Log and passed all
frozen-input checks before calculating results.

- Baseline Trade Log SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`
- Group membership SHA-256: `aad041b8cbc03611cbe535060c4887f30f9341c5d0f0010158f1d923e830756d`
- Full Baseline rows verified: 16,298
- Strategy count verified: 28
- IS rows: 9,756
- IS period: 2015-01-01 through 2021-12-31, based on EntryTime JST
- IS Baseline Total R: 768.488273R
- OOS1/OOS2: not calculated or displayed

No M1 data was read and the Baseline Trade Log was not recalculated.

## 2. Individual health and Leave-One-Out result

Only one strategy met both predeclared conditions for a clear negative marginal
contribution in IS.

| Rank | Strategy | Standalone Total R | Positive years | Negative years | LOO Delta Total R | Stable negative |
|---:|---|---:|---:|---:|---:|---|
| 1 | `10_AJ_SatA` | -0.444000 | 2 | 5 | +0.444000 | Yes |

All other strategies had positive standalone Total R in IS and therefore did
not qualify as individual stop candidates for the profit objective.

## 3. Risk-metric observation

Removing `10_AJ_SatA` increased IS Total R and PF, but did not improve every
risk metric.

| Metric | Baseline | Minus `10_AJ_SatA` | Delta |
|---|---:|---:|---:|
| Total R | 768.488273 | 768.932273 | +0.444000 |
| PF | 1.372171 | 1.377253 | +0.005082 |
| Max DD R | 27.540956 | 27.854956 | +0.314000 (worse) |
| Worst Day R | -12.000000 | -12.000000 | 0.000000 |
| Worst Week R | -14.455836 | -14.563836 | -0.108000 (worse) |

This mixed risk result does not remove the candidate because the frozen primary
criterion is Total R. It also does not establish adoption; OOS confirmation is
still required.

## 4. Predeclared group hypotheses

All eight group exclusions reduced IS Total R. None qualified for `P3_MINUS_GROUP`.

| Group | Members | Group Total R | Exclusion Delta Total R |
|---|---:|---:|---:|
| `TP_LT_SL` | 5 | +72.977280 | -72.977279 |
| `CHINA_DEMAND` | 4 | +116.723611 | -116.723611 |
| `TP_NONE` | 3 | +169.724000 | -169.724000 |
| `OVERNIGHT` | 11 | +347.675387 | -347.675386 |
| `SHORT` | 13 | +383.654108 | -383.654108 |
| `LONG` | 15 | +384.834165 | -384.834165 |
| `AUD_RELATED` | 16 | +410.429665 | -410.429664 |
| `JPY_RELATED` | 17 | +465.009876 | -465.009875 |

The sub-micro-R differences between Group Total R and its sign-reversed Delta
are CSV display rounding only; the unrounded reconciliation check passed.

## 5. Frozen Candidate portfolios

Only the following portfolios advance to the one-time OOS confirmation.

| Candidate ID | Exclusion | IS Trades | IS Total R | Delta Total R | IS Max DD R |
|---|---|---:|---:|---:|---:|
| `P0_BASELINE` | none | 9,756 | 768.488273 | 0.000000 | 27.540956 |
| `P1_MINUS_TOP1` | `10_AJ_SatA` | 9,517 | 768.932273 | +0.444000 | 27.854956 |

The other predeclared candidate slots are not created:

- `P2_MINUS_STABLE_TOP2`: only one stable negative candidate exists.
- `P3_MINUS_GROUP`: no group exclusion improves Total R.
- `P4_PAIR_CHECK`: only one clear negative candidate exists.

No thresholds were relaxed and no additional combinations were searched.

## 6. Output files

- `results/strategy_selection/strategy_selection_group_membership.csv`
- `results/strategy_selection/strategy_selection_health_is.csv`
- `results/strategy_selection/strategy_selection_leave_one_out_is.csv`
- `results/strategy_selection/strategy_selection_group_hypotheses_is.csv`
- `results/strategy_selection/strategy_selection_candidates_frozen.csv`

The candidate CSV records `OOSViewed=False`. Do not run OOS1 until the candidate
freeze commit is recorded. After OOS1 is viewed, candidates and rules must not be
changed. OOS2 remains the final holdout and must be checked last.

EA, VPS, SET, live-operation code and live settings remain unchanged.
