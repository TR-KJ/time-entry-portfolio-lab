# Daily Stop Baseline Revalidation Result

Status: ACCEPTED / FROZEN

Verification date: 2026-09-09 JST

Branch: `research/daily-stop-validation`

Generator: `src/research/daily_stop_baseline_revalidation.py` v1.0.1

## 1. Acceptance decision

The no-Daily-Stop 28-strategy Baseline Trade Log is accepted and frozen for downstream Daily Stop analysis.

The v1.0.1 rerun changed only complete-calendar gap diagnostics. Its Trade Log SHA-256 is identical to the initial run, proving that the diagnostic correction did not alter any generated trade:

```text
cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
```

All later Daily Stop thresholds must use this exact trade log. A different SHA-256 requires a new baseline review and must not be silently substituted.

## 2. Period results

Period assignment uses EntryTime in JST.

| Segment | Trades | Wins | Win rate | Total R | PF | Max DD (R) | Avg R |
|---|---:|---:|---:|---:|---:|---:|---:|
| FULL | 16,298 | 8,887 | 54.528% | 1390.267649 | 1.397117 | 27.540956 | 0.085303 |
| IS | 9,756 | 5,321 | 54.541% | 768.488273 | 1.372171 | 27.540956 | 0.078771 |
| OOS1 | 5,547 | 3,054 | 55.057% | 601.960585 | 1.489975 | 22.196976 | 0.108520 |
| OOS2 | 995 | 512 | 51.457% | 19.818791 | 1.095529 | 18.954206 | 0.019918 |

## 3. Yearly results

| Year | Trades | Wins | Win rate | Total R | PF | Max DD (R) | Avg R |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2015 | 1,378 | 722 | 52.395% | 92.171476 | 1.244601 | 21.007598 | 0.066888 |
| 2016 | 1,405 | 792 | 56.370% | 210.801980 | 1.587640 | 13.124160 | 0.150037 |
| 2017 | 1,389 | 785 | 56.515% | 102.054570 | 1.378209 | 25.011965 | 0.073473 |
| 2018 | 1,385 | 762 | 55.018% | 116.556513 | 1.438216 | 12.213946 | 0.084156 |
| 2019 | 1,391 | 732 | 52.624% | 54.801888 | 1.236708 | 27.540956 | 0.039397 |
| 2020 | 1,411 | 758 | 53.721% | 131.287851 | 1.396600 | 15.515686 | 0.093046 |
| 2021 | 1,397 | 770 | 55.118% | 60.813996 | 1.263305 | 12.260243 | 0.043532 |
| 2022 | 1,383 | 753 | 54.447% | 163.991920 | 1.460197 | 13.239666 | 0.118577 |
| 2023 | 1,384 | 777 | 56.142% | 160.985032 | 1.537135 | 22.196976 | 0.116319 |
| 2024 | 1,394 | 763 | 54.735% | 129.794238 | 1.471284 | 12.974713 | 0.093109 |
| 2025 | 1,386 | 761 | 54.906% | 147.189395 | 1.495443 | 17.273406 | 0.106197 |
| 2026 | 995 | 512 | 51.457% | 19.818791 | 1.095529 | 18.954206 | 0.019918 |

## 4. Data-gap diagnostics

| Diagnostic type | Count |
|---|---:|
| MISSING_ENTRY | 425 |
| MISSING_EXIT | 42 |
| INVALID_WINDOW | 0 |

These rows represent trades not generated under the frozen historical rule. No price interpolation, alternate-broker fill or new date exclusion was applied.

The three known post-filter GBPAUD 2019 gap candidates were all observed as `MISSING_ENTRY`:

| Strategy | Scheduled entry JST | Result |
|---|---|---|
| 21_GA_B_3 | 2019-01-07 21:02 | MISSING_ENTRY |
| 28_GA_China_Demand | 2019-05-09 10:00 | MISSING_ENTRY |
| 22_GA_C_2 | 2019-05-09 16:56 | MISSING_ENTRY |

## 5. Storage

The seven generated CSV artifacts were copied from Colab's temporary `/content` directory to:

```text
/MyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/
```

The copied trade log was hashed again after storage and matched the accepted SHA-256.

GitHub stores the compact accepted summaries and run record under `results/daily_stop/`. The complete trade log remains identified by its SHA-256 and is the sole permitted input to the next analysis layer.

## 6. Next layer boundary

Daily Stop is still OFF in this accepted output. The next program may read the frozen CSV but must not load M1 data or recalculate baseline trades. The predeclared grid is `none / -1R / -1.5R / -2R / -2.5R / -3R / -4R`. Threshold selection is confined to IS; OOS1 and OOS2 remain untouched until the selected threshold is frozen. A triggered stop remains latched until the next 00:00 JST even if an already-open position later recovers daily R.

The completed IS-only run is recorded in `docs/30_daily_stop_is_selection_result.md`. It froze `-4R` solely for one OOS confirmation; this is not yet a production adoption.

The completed frozen OOS run is recorded in `docs/31_daily_stop_oos_result.md`. Daily Stop was not adopted; this no-Daily-Stop Baseline remains the official configuration.
