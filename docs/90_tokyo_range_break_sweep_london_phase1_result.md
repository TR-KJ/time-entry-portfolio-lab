# B1 Tokyo Range Break / Sweep → London Phase 1 — Result

Branch: `research/tokyo-range-break-sweep-london-phase1`. Plan SHA `84b959d715472c81627cbb42579911c7c2805b58`; implementation SHA `f132d8df2b84ca20c46c087720ae60aa96d1cfe8`. All outcomes were calculated after remote verification of both commits.

## Conclusion

None of the 14 preregistered pair × hypothesis tests passed the formal A–G gate. No B1 pair × hypothesis advances to Phase 2. In accordance with the preregistered decision, B1 stops here; the next separate research theme is B2 London Opening Range Breakout / Fade. This is absence of formal support under the fixed test, not proof that the market effect is zero. No trading strategy or portfolio simulation was performed.

## Input and coverage

All 56 audited M1 source files (7 pairs × 8) matched filename, byte SHA256, row count and raw first/last timestamp. The frozen A3 manifest was byte identical to the original Volatility Phase 1 input manifest, SHA256 `8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f`. No source substitution or gap filling. Known GBPAUD 2019 gaps were treated under the same full coverage rule. Each pair had 3,050 weekday candidates.

| Pair | Valid | Tokyo incomplete | London event incomplete | 11:00 Open missing |
| --- | --- | --- | --- | --- |
| USDJPY | 2939 | 102 | 8 | 1 |
| EURJPY | 2971 | 70 | 8 | 1 |
| GBPJPY | 2956 | 84 | 9 | 1 |
| AUDJPY | 2973 | 69 | 7 | 1 |
| AUDUSD | 2945 | 94 | 10 | 1 |
| EURAUD | 2967 | 74 | 8 | 1 |
| GBPAUD | 2962 | 81 | 6 | 1 |


## All period event counts

| Pair | UP breakout | DOWN breakout | UP sweep | DOWN sweep | Both | No break |
| --- | --- | --- | --- | --- | --- | --- |
| USDJPY | 612 | 501 | 348 | 316 | 26 | 1136 |
| EURJPY | 717 | 575 | 420 | 398 | 89 | 772 |
| GBPJPY | 709 | 664 | 408 | 383 | 119 | 673 |
| AUDJPY | 567 | 466 | 384 | 298 | 13 | 1245 |
| AUDUSD | 570 | 506 | 364 | 356 | 18 | 1131 |
| EURAUD | 579 | 575 | 344 | 418 | 24 | 1027 |
| GBPAUD | 556 | 668 | 338 | 416 | 47 | 937 |


## Formal primary results — ALL

Aligned return is measured in pips from exact London 09:00 Open to exact 11:00 Open. The 95% CI is a 5,000 draw calendar week cluster percentile interval. Raw p uses the preregistered centered two sided bootstrap; adjusted p uses Holm across all 14 tests. All adjusted p values equal 1.000.

| Pair | Test | N | Weeks | Mean | 95% CI | Raw p | Holm p | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | Breakout | 1113 | 555 | 0.986 | [-0.180, 2.117] | 0.098 | 1.000 | NOT_SUPPORTED |
| USDJPY | Sweep | 664 | 433 | 0.144 | [-1.130, 1.410] | 0.829 | 1.000 | NOT_SUPPORTED |
| EURJPY | Breakout | 1292 | 579 | 1.221 | [-0.168, 2.543] | 0.076 | 1.000 | NOT_SUPPORTED |
| EURJPY | Sweep | 818 | 475 | -0.186 | [-1.842, 1.461] | 0.829 | 1.000 | NOT_SUPPORTED |
| GBPJPY | Breakout | 1373 | 575 | 0.219 | [-1.566, 2.005] | 0.812 | 1.000 | NOT_SUPPORTED |
| GBPJPY | Sweep | 791 | 465 | 0.882 | [-1.285, 2.988] | 0.421 | 1.000 | NOT_SUPPORTED |
| AUDJPY | Breakout | 1033 | 526 | 0.542 | [-0.627, 1.740] | 0.372 | 1.000 | NOT_SUPPORTED |
| AUDJPY | Sweep | 682 | 431 | -0.264 | [-1.520, 1.117] | 0.688 | 1.000 | NOT_SUPPORTED |
| AUDUSD | Breakout | 1076 | 534 | 0.620 | [-0.144, 1.392] | 0.110 | 1.000 | NOT_SUPPORTED |
| AUDUSD | Sweep | 720 | 441 | 0.239 | [-0.606, 1.105] | 0.603 | 1.000 | NOT_SUPPORTED |
| EURAUD | Breakout | 1154 | 551 | -0.477 | [-1.999, 1.096] | 0.538 | 1.000 | NOT_SUPPORTED |
| EURAUD | Sweep | 762 | 471 | 0.643 | [-1.010, 2.363] | 0.459 | 1.000 | NOT_SUPPORTED |
| GBPAUD | Breakout | 1224 | 551 | 1.178 | [-0.748, 3.095] | 0.231 | 1.000 | NOT_SUPPORTED |
| GBPAUD | Sweep | 754 | 478 | 1.615 | [-1.095, 4.308] | 0.245 | 1.000 | NOT_SUPPORTED |


## Period means and sample stability

| Pair | Test | Historical mean (N) | Recent combined mean (N) | Recent A mean (N) | Recent B mean (N) | 2026 mean (N) |
| --- | --- | --- | --- | --- | --- | --- |
| USDJPY | Breakout | 0.516 (654) | 1.655 (459) | 0.622 (197) | 2.740 (195) | 1.536 (67) |
| USDJPY | Sweep | 0.571 (412) | -0.556 (252) | 1.990 (101) | -1.618 (109) | -3.919 (42) |
| EURJPY | Breakout | 0.720 (757) | 1.929 (535) | 1.568 (241) | 1.036 (225) | 6.096 (69) |
| EURJPY | Sweep | -1.202 (500) | 1.410 (318) | 4.804 (140) | -1.889 (135) | 0.721 (43) |
| GBPJPY | Breakout | 0.045 (833) | 0.487 (540) | -3.488 (236) | 3.188 (226) | 4.685 (78) |
| GBPJPY | Sweep | 2.191 (465) | -0.987 (326) | -2.890 (135) | 1.773 (138) | -3.323 (53) |
| AUDJPY | Breakout | 1.100 (610) | -0.262 (423) | -0.388 (191) | -0.644 (177) | 1.402 (55) |
| AUDJPY | Sweep | -0.363 (415) | -0.110 (267) | 0.781 (129) | 0.208 (104) | -4.459 (34) |
| AUDUSD | Breakout | 0.564 (659) | 0.708 (417) | 1.185 (195) | 0.206 (175) | 0.598 (47) |
| AUDUSD | Sweep | 0.439 (427) | -0.053 (293) | 0.208 (132) | -0.209 (119) | -0.431 (42) |
| EURAUD | Breakout | -0.923 (712) | 0.242 (442) | 2.988 (208) | -2.893 (181) | 0.170 (53) |
| EURAUD | Sweep | 0.305 (462) | 1.162 (300) | 4.534 (141) | 0.112 (118) | -7.410 (41) |
| GBPAUD | Breakout | 0.421 (759) | 2.413 (465) | 4.611 (227) | -0.073 (181) | 1.556 (57) |
| GBPAUD | Sweep | 1.521 (469) | 1.770 (285) | 1.453 (121) | 1.906 (126) | 2.329 (38) |


2022–2026 is not a pristine unseen holdout. All 14 cells met the preregistered minimum sample requirements for ALL, Historical, Recent Combined and at least two of the three shorter periods.

## Formal A–G gates

A: ALL mean > 0. B: ALL CI lower > 0. C: Holm p < .05. D/E: eligible Historical / Recent Combined mean > 0. F: at least two eligible positive subperiods. G: sufficient sample and bootstrap. P=PASS, F=FAIL.

| Pair | Test | A | B | C | D | E | F | G |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | Breakout | P | F | F | P | P | P | P |
| USDJPY | Sweep | P | F | F | P | F | F | P |
| EURJPY | Breakout | P | F | F | P | P | P | P |
| EURJPY | Sweep | F | F | F | F | P | P | P |
| GBPJPY | Breakout | P | F | F | P | P | P | P |
| GBPJPY | Sweep | P | F | F | P | F | F | P |
| AUDJPY | Breakout | P | F | F | P | F | F | P |
| AUDJPY | Sweep | F | F | F | F | F | P | P |
| AUDUSD | Breakout | P | F | F | P | P | P | P |
| AUDUSD | Sweep | P | F | F | P | F | F | P |
| EURAUD | Breakout | F | F | F | F | P | P | P |
| EURAUD | Sweep | P | F | F | P | P | P | P |
| GBPAUD | Breakout | P | F | F | P | P | P | P |
| GBPAUD | Sweep | P | F | F | P | P | P | P |


## Direction diagnostic — ALL

UP and DOWN rows are diagnostic only; no one sided formal selection. Positive rate includes zero returns in the denominator.

| Pair | Direction event | N | Mean | Median | Positive rate | 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| USDJPY | UP_BREAKOUT | 612 | 1.293 | 1.100 | 0.542 | [-0.304, 2.797] |
| USDJPY | DOWN_BREAKOUT | 501 | 0.611 | -0.800 | 0.471 | [-1.088, 2.357] |
| USDJPY | UP_SWEEP | 348 | -0.198 | -0.100 | 0.497 | [-1.919, 1.594] |
| USDJPY | DOWN_SWEEP | 316 | 0.520 | 0.950 | 0.519 | [-1.319, 2.322] |
| EURJPY | UP_BREAKOUT | 717 | 1.403 | 0.800 | 0.517 | [-0.342, 3.068] |
| EURJPY | DOWN_BREAKOUT | 575 | 0.993 | -0.700 | 0.482 | [-1.137, 3.155] |
| EURJPY | UP_SWEEP | 420 | 0.034 | -0.250 | 0.490 | [-2.326, 2.468] |
| EURJPY | DOWN_SWEEP | 398 | -0.418 | 0.350 | 0.508 | [-2.615, 1.842] |
| GBPJPY | UP_BREAKOUT | 709 | 1.457 | 2.000 | 0.539 | [-1.244, 4.182] |
| GBPJPY | DOWN_BREAKOUT | 664 | -1.104 | -2.400 | 0.461 | [-3.733, 1.516] |
| GBPJPY | UP_SWEEP | 408 | -0.533 | -2.400 | 0.461 | [-3.548, 2.467] |
| GBPJPY | DOWN_SWEEP | 383 | 2.388 | 2.500 | 0.554 | [-0.963, 5.699] |
| AUDJPY | UP_BREAKOUT | 567 | 0.659 | 1.100 | 0.536 | [-0.926, 2.195] |
| AUDJPY | DOWN_BREAKOUT | 466 | 0.400 | -0.350 | 0.489 | [-1.382, 2.145] |
| AUDJPY | UP_SWEEP | 384 | 0.311 | -0.850 | 0.471 | [-1.559, 2.363] |
| AUDJPY | DOWN_SWEEP | 298 | -1.005 | -0.300 | 0.477 | [-2.791, 0.795] |
| AUDUSD | UP_BREAKOUT | 570 | 0.519 | 0.700 | 0.519 | [-0.504, 1.558] |
| AUDUSD | DOWN_BREAKOUT | 506 | 0.733 | -0.200 | 0.490 | [-0.305, 1.828] |
| AUDUSD | UP_SWEEP | 364 | 0.798 | 0.850 | 0.519 | [-0.364, 1.965] |
| AUDUSD | DOWN_SWEEP | 356 | -0.333 | -0.450 | 0.492 | [-1.524, 0.885] |
| EURAUD | UP_BREAKOUT | 579 | -0.263 | -0.500 | 0.485 | [-2.352, 1.874] |
| EURAUD | DOWN_BREAKOUT | 575 | -0.692 | 0.000 | 0.499 | [-2.874, 1.514] |
| EURAUD | UP_SWEEP | 344 | 0.733 | 0.950 | 0.509 | [-1.543, 3.088] |
| EURAUD | DOWN_SWEEP | 418 | 0.568 | 0.200 | 0.502 | [-1.741, 3.003] |
| GBPAUD | UP_BREAKOUT | 556 | 4.571 | 3.500 | 0.550 | [1.791, 7.393] |
| GBPAUD | DOWN_BREAKOUT | 668 | -1.646 | -0.350 | 0.490 | [-4.200, 0.946] |
| GBPAUD | UP_SWEEP | 338 | -0.757 | -1.500 | 0.482 | [-4.373, 2.935] |
| GBPAUD | DOWN_SWEEP | 416 | 3.542 | 1.750 | 0.524 | [-0.208, 7.198] |


## Equal pair weight family diagnostic

The effect is each pair’s ALL aligned mean divided by its own ALL aligned SD, then averaged equally. This is descriptive and does not change pair verdicts.

| Family | Test | Contributors | Equal weight standardized mean | Status |
| --- | --- | --- | --- | --- |
| JPY | Breakout | 4 | 0.033 | DESCRIPTIVE_ONLY |
| AUD_non_JPY | Breakout | 3 | 0.021 | DESCRIPTIVE_ONLY |
| All_7 | Breakout | 7 | 0.028 | DESCRIPTIVE_ONLY |
| JPY | Sweep | 4 | 0.003 | DESCRIPTIVE_ONLY |
| AUD_non_JPY | Sweep | 3 | 0.031 | DESCRIPTIVE_ONLY |
| All_7 | Sweep | 7 | 0.015 | DESCRIPTIVE_ONLY |


## Validation and boundaries

Five synthetic unit tests passed, covering six classes, equality, no lookahead, pip sizes, London DST, endpoints, bootstrap row replication and Holm. An independent verifier checked 21,350 pair days, all 84 period cells, aligned returns, event classification and Holm; one ALL bootstrap CI was rebuilt by explicit week row replication. Representative source reconstruction passed 28 of 28 fixed pair × season × breakout/sweep cases. The run record status is VERIFIED. No M1 price imputation, broker splicing, threshold exploration or Phase 2 feature computation occurred.

## Publication and operational boundary

Aggregate CSVs, audit and validation tables, run record and publication manifest are in `results/tokyo_range_london_phase1/`. The 21,350 row daily assignment stays local; its SHA256 and row count are in the publication manifest. The notebook saves CSVs to `/content` when run in Colab and has Drive save OFF. Phase 2 candidates: none. Volatility Phase 5 Dell Demo Forward remains on Global R2; EA, SET, VPS and live were not changed.
