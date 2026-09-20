# AU China Demand Late-Month Edge Decay Phase 1 — Result

**NOT_SUPPORTED. Phase 2へ進まない。** 固定したRecent CombinedではLATE AvgRはHistoricalより低下していない。この診断は戦略停止を指示せず、将来のedge維持を証明するものでもない。

## Provenance
- Branch: `research/au-china-late-month-edge-decay-phase1`
- Preregistered Plan remote SHA: `b49e7766bc2a710c3afae7685476e0fa47d2fecb`
- Implementation remote SHA (before real-data calculation): `caf3f612fa881b89cd7d83f6c1c430e15c3efcb2`
- Result commit: the commit publishing this document; recorded in the delivery receipt outside this commit to avoid self-reference.
- Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`; matched. 28 strategies / 16,298 trades. Daily Stop OFF / ATR OFF / Event Candidate C; baseline not recalculated.
- Strategy25: 1,022 trades = EARLY 583 + LATE 439. Unique and exhaustive assignments passed.
- Existing baseline uses Pair `AU`, whose canonical symbol is AUDUSD (existing loader alias mapping, lines 40–42). Initial literal AUDUSD check halted the input audit; corrected to the documented AU encoding before outcomes were computed. No research definition changed.
- Main parent `1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5`. Existing docs across remote branches reached 72; new Plan/Result use 73/74.
- Git CLI had no authenticated push credential; authenticated GitHub connector committed and advanced the same research branch. Remote SHA confirmed with git ls-remote before implementation and before calculation.
- 2022–2026は既閲覧済みでpristine holdoutではない。旧Edge Decay helperとHistorical/Recent A/Recent B/Monitor境界は一致。今回のRecent Combinedは指定により2026-09-09まで含み、旧2025年末終了と意図的に異なる。既存helper変更なし。

## Segment × period
AvgR is R/trade; TotalR is sum of recorded R; PF is R-based gross gains / absolute gross losses. End date 2026-09-09 is inclusive. Counts include only actual baseline trades; missing calendar dates are not synthesized.

| Period | Segment | Trades | Weeks | AvgR | TotalR | PF | LOW_SAMPLE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Historical | EARLY_MONTH | 350 | 110 | 0.079793 | 27.927500 | 1.491098 | False |
| Historical | LATE_MONTH | 264 | 90 | 0.018996 | 5.015000 | 1.106526 | False |
| Recent A | EARLY_MONTH | 100 | 31 | 0.069125 | 6.912500 | 1.436120 | False |
| Recent A | LATE_MONTH | 74 | 26 | 0.042027 | 3.110000 | 1.161077 | False |
| Recent B | EARLY_MONTH | 98 | 31 | 0.067117 | 6.577500 | 1.650111 | False |
| Recent B | LATE_MONTH | 75 | 27 | 0.006967 | 0.522500 | 1.043587 | False |
| 2026 Monitor | EARLY_MONTH | 35 | 11 | -0.016714 | -0.585000 | 0.910104 | False |
| 2026 Monitor | LATE_MONTH | 26 | 9 | 0.007404 | 0.192500 | 1.044715 | True |
| Recent Combined | EARLY_MONTH | 233 | 73 | 0.055386 | 12.905000 | 1.397383 | False |
| Recent Combined | LATE_MONTH | 175 | 62 | 0.021857 | 3.825000 | 1.107444 | False |
| ALL | EARLY_MONTH | 583 | 183 | 0.070039 | 40.832500 | 1.457033 | False |
| ALL | LATE_MONTH | 439 | 152 | 0.020137 | 8.840000 | 1.106921 | False |

## Fixed contrasts and bootstrap
Calendar-week cluster bootstrap 5,000 replicates, PCG64 seed 20260913, Monday-based JST weeks, independently resampled periods, jointly sampled EARLY/LATE, trade-weighted means, percentile linear 95% CI. Formal primary cells have sufficient samples: Historical LATE 264 trades/90 weeks and Combined LATE 175/62; EARLY 350/110 and 233/73.

| Comparison | Contrast | Estimate | CILower | CIUpper | CIStatus |
| --- | --- | --- | --- | --- | --- |
| Recent Combined | LATE_DECAY | 0.002861 | -0.078085 | 0.084839 | OK |
| Recent Combined | EARLY_DECAY | -0.024407 | -0.097749 | 0.051974 | OK |
| Recent Combined | RELATIVE_DECAY | 0.027268 | -0.082051 | 0.135638 | OK |
| Recent A | LATE_DECAY | 0.023031 | -0.105722 | 0.148316 | OK |
| Recent A | EARLY_DECAY | -0.010668 | -0.102410 | 0.080395 | OK |
| Recent B | LATE_DECAY | -0.012030 | -0.105058 | 0.082848 | OK |
| Recent B | EARLY_DECAY | -0.012676 | -0.107328 | 0.104511 | OK |
| 2026 Monitor | LATE_DECAY | -0.011592 |  |  | INSUFFICIENT_SAMPLE |
| 2026 Monitor | EARLY_DECAY | -0.096507 |  |  | INSUFFICIENT_SAMPLE |

LATE Historical AvgR 0.018996 → Combined 0.021857. LATE_DECAY +0.002861 is opposite to the proposed decay direction. EARLY_DECAY −0.024407; RELATIVE_DECAY +0.027268 also opposes late-specific deterioration. All primary CIs cross zero.
Recent A is above Historical; Recent B and Monitor are below: **2/3 periods lower**. Recent A/B CIs cross zero. Monitor LATE has only 26 trades/9 weeks (LOW_SAMPLE=true); EARLY 35/11 has LOW_SAMPLE=false but insufficient weeks. Both Monitor CIs are INSUFFICIENT_SAMPLE under the preregistered floor. Bootstrap replicates without a segment are not redrawn or dropped. No inference is made from Monitor CI.

## Formal criteria
|Criterion|Value / reason|Status|
|---|---|---|
|A Historical LATE AvgR >0|0.018996|PASS|
|B LATE_DECAY <0|+0.002861|FAIL|
|C valid LATE_DECAY CI upper <0|upper +0.084839; CIStatus OK|FAIL|
|D RELATIVE_DECAY <0|+0.027268|FAIL|
|E Recent B or Monitor LATE <Historical|both below|PASS|

Overall **NOT_SUPPORTED**. The weak-signal rule also fails because B and D are not negative. No formal Phase2 candidate; no exclusion or money simulation performed. Stopping late-month entries is not a conclusion of this phase.

## All-year descriptive table
2026 is through September 9, not a full year. All years and both segments are shown; yearly figures are descriptive only.

| Year | Segment | Trades | AvgR | TotalR |
| --- | --- | --- | --- | --- |
| 2015 | EARLY_MONTH | 50 | 0.030550 | 1.527500 |
| 2015 | LATE_MONTH | 38 | -0.114079 | -4.335000 |
| 2016 | EARLY_MONTH | 50 | 0.082550 | 4.127500 |
| 2016 | LATE_MONTH | 38 | 0.207763 | 7.895000 |
| 2017 | EARLY_MONTH | 50 | 0.236400 | 11.820000 |
| 2017 | LATE_MONTH | 37 | -0.004932 | -0.182500 |
| 2018 | EARLY_MONTH | 50 | 0.049250 | 2.462500 |
| 2018 | LATE_MONTH | 39 | 0.025833 | 1.007500 |
| 2019 | EARLY_MONTH | 50 | 0.048800 | 2.440000 |
| 2019 | LATE_MONTH | 39 | 0.016731 | 0.652500 |
| 2020 | EARLY_MONTH | 50 | 0.093000 | 4.650000 |
| 2020 | LATE_MONTH | 37 | 0.035405 | 1.310000 |
| 2021 | EARLY_MONTH | 50 | 0.018000 | 0.900000 |
| 2021 | LATE_MONTH | 36 | -0.037014 | -1.332500 |
| 2022 | EARLY_MONTH | 50 | 0.027700 | 1.385000 |
| 2022 | LATE_MONTH | 37 | 0.117500 | 4.347500 |
| 2023 | EARLY_MONTH | 50 | 0.110550 | 5.527500 |
| 2023 | LATE_MONTH | 37 | -0.033446 | -1.237500 |
| 2024 | EARLY_MONTH | 49 | 0.003571 | 0.175000 |
| 2024 | LATE_MONTH | 39 | 0.048077 | 1.875000 |
| 2025 | EARLY_MONTH | 49 | 0.130663 | 6.402500 |
| 2025 | LATE_MONTH | 36 | -0.037569 | -1.352500 |
| 2026 | EARLY_MONTH | 35 | -0.016714 | -0.585000 |
| 2026 | LATE_MONTH | 26 | 0.007404 | 0.192500 |

LATE fluctuates in sign across years (positive in 2016, 2018–2020, 2022, 2024 and 2026; negative in 2015, 2017, 2021, 2023 and 2025); the complete sequence does not show a monotonic recent decline. EARLY is positive in every full year shown, with 2026 negative. Full-period LATE AvgR 0.020137 is lower than EARLY 0.070039, but a lower level is not evidence of a post-2021 late-specific decay. No years or alternate cutoffs were selected for additional testing.

## Validation evidence
- Seven unit tests passed: JST segment boundaries, every period boundary, leap-day week assignment, identity rejection, metrics/zeros, strict classifier branches, paired bootstrap reproducibility/sufficiency, hash rejection.
- Baseline hash, 16,298 count, 28 identities, duplicate check, finite R and R=Pips/SL passed via fixed existing loader.
- All 1,022 Strategy25 rows passed exact name/number, AU→AUDUSD, Long, weekday 10:00 entry, scheduled 15:50 same-day exit, SL40/TP40 and unique EARLY/LATE checks.
- Independent csv/Decimal reaggregation matched AvgR/TotalR/PF and counts for all 12 period cells and 24 year cells (tolerance 1e-10).
- Independent raw-trade cluster expansion checked all 20,000 bootstrap replicates and all available CI endpoints, not only a spot-check. Maximum finite replicate discrepancy 1.95e-16; independent sorted-order interpolation agreed within 2e-14. Monitor missing-segment means correctly remain NaN/insufficient; expected empty-mean warnings do not alter inference.
- Independently checked all assignment date/week/segment fields. Twenty deterministic first/last representatives across 2015/2021/2022/2024/2026 reviewed manually against original rows: EARLY dates 9–15, LATE 25–31; all AU/Long 10:00 and scheduled 15:50. Includes 2021-11-30 Monday key 2021-11-29 and 2026-07-31 key 2026-07-27.
- No protected existing file changes. No EA/SET/VPS/live or Volatility Phase5, Trend Strength, Pre-Entry modifications; no entry/risk changes. Only new study files are published on the research branch; main is not merged.

## Deliverables
- `src/research/au_china_late_month_phase1.py`
- `tests/test_au_china_late_month_phase1.py`
- `tests/verify_au_china_late_month_phase1.py`
- `notebooks/au_china_late_month_phase1.ipynb`
- `docs/73_au_china_late_month_phase1_plan.md` (unchanged preregistration)
- `docs/74_au_china_late_month_phase1_result.md` (this document)
- `results/au_china_late_month_phase1/`: five prescribed aggregate/run-record CSVs, verification JSON, notebook validation JSON, publication manifest.
- Trade assignment and representative raw audits are local/Colab only with SHA-256/size recorded in manifest.

Notebook embeds the exact committed analysis and baseline-validation source, shows the above tables in its body, executes into /content, and offers Drive save default OFF. Local notebook computation is verified; Colab server execution is not claimed. Reproduce with the original hash-matching baseline CSV, Python 3.12 / NumPy 2.3.5 / pandas. See run record for exact versions/seed/SHAs. Detailed trades are not published to GitHub.
