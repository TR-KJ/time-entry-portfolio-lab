# 98 C2 No-Progress / Time-Decay Exit Phase 1 v2 — Result

**Verdict: NOT_SUPPORTED. Phase2Eligible: False.**

Branch: `research/c2-no-progress-time-decay-phase1`. Original stopped Result `96`, original Plan `95`, its implementation/notebook and `results/c2_no_progress_phase1/` are preserved without changes. This v2 follows the user-authorized missing-execution amendment, registered before resumed outcome aggregation.

- Amendment Plan SHA: `3e99c78855ba09b6be1a95fb13318b35d551d473` (remote verified before coding).
- Implementation SHA: `eb3557fa1dffbec3a1999bd6306bd4ff63a4600a` (remote verified before calculations).
- Original stopped Result SHA: `5d5f0b17412b713b44a1f651c7a9bd1037eeaa22`.
- Result SHA is the commit containing this document, reported in the final handoff.
- Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`.

## Missing policy and source verification

NP50 remains 50% planned duration and MFE < +0.25 initial-SL R using only completed M1 bars before the checkpoint. NP75 remains robustness at 75%, with the same threshold. If no execution Open exists exact through +4 minutes, retain the complete baseline outcome and classify `MISSING_EXECUTION_KEEP_BASELINE`. Such observations remain in the primary denominator, Triggered=False and delta 0R.

The same two EURAUD NP50 cases were reproduced; NP75 has zero missing executions. No data fill, broker splice, later checkpoint or trade deletion was used for the primary. This amendment addresses missing execution bars, not uncertainty about price paths inside source gaps. It is explicitly informed by the first run's coverage finding and is not an untouched original preregistration.

All 56 M1 hashes, row counts and raw timestamp bounds passed again. R0 independently reconstructed ALL28 16,298/16,298 and ACTIVE27 15,837/15,837 with **zero mismatches**. Strategy22's 461 trades remain reference-only. The source timezone conversion remains Europe/Helsinki → Asia/Tokyo → naive JST.

|Strategy|Entry JST|Checkpoint JST|Prior MFE R|R0 R|NP R|Delta R|Classification|
|---|---|---|---|---|---|---|---|
|19|2021-06-17 20:56:00|2021-06-18 03:28:00|0.154444|-0.054444|-0.054444|0.000000|MISSING_EXECUTION_KEEP_BASELINE|
|20|2025-01-07 10:01:00|2025-01-07 13:00:00|0.174000|0.228000|0.228000|0.000000|MISSING_EXECUTION_KEEP_BASELINE|

## Primary portfolio comparison

|Variant|Trades|R0 Total R|NP Total R|Delta Total R|Avg delta / trade|CI lower|CI upper|
|---|---|---|---|---|---|---|---|
|NP50|15837|1,360.253364|1,091.810162|-268.443202|-0.016950|-0.020946|-0.012940|
|NP75|15837|1,360.253364|1,218.867887|-141.385477|-0.008928|-0.011244|-0.006545|

Paired calendar-week bootstrap: 5,000 replicates, PCG64 seed 20260913, linear 95% percentile interval for mean delta per trade; all trades in a selected Monday-start JST entry week resampled together. NP50 is the only formal primary; no Holm correction. NP75 is descriptive robustness.

|NP50 triggers|Trigger rate|Trigger weeks|Improved|Harmed|Unchanged|Avg gain / improved|Avg delta / harmed|
|---|---|---|---|---|---|---|---|
|6927|0.437393|599|3187|3725|8925|0.219687|-0.260023|

|R0 PF|NP50 PF|R0 win rate|NP50 win rate|R0 avg win|NP50 avg win|R0 avg loss|NP50 avg loss|
|---|---|---|---|---|---|---|---|
|1.406454|1.349639|0.546126|0.494601|0.544212|0.538042|-0.467472|-0.391362|

|R0 SL rate|NP50 SL rate|R0 TP rate|NP50 TP rate|R0 scheduled time rate|NP50 scheduled time rate|NP50 early exit rate|
|---|---|---|---|---|---|---|
|0.116626|0.084170|0.053798|0.051588|0.829576|0.426849|0.437393|

## Fixed periods — NP50

|Period|Trades|Triggers|Trigger weeks|Delta Total R|Avg delta R|CI lower|CI upper|Eligible for period sample gate|
|---|---|---|---|---|---|---|---|---|
|Historical|9482|4294|358|-177.428912|-0.018712|-0.024228|-0.013340|True|
|Recent A|2688|969|102|-40.317889|-0.014999|-0.023589|-0.007131|True|
|Recent B|2701|1153|103|-49.085247|-0.018173|-0.027393|-0.008815|True|
|2026 Monitor|966|511|36|-1.611153|-0.001668|-0.020326|0.014899|True|
|Recent Combined|6355|2633|241|-91.014289|-0.014322|-0.020397|-0.008413|True|
|ALL|15837|6927|599|-268.443202|-0.016950|-0.020946|-0.012940|True|

2022–2026 is previously viewed and is not a pristine unseen holdout. Period eligibility requires 30 triggers and 20 trigger entry weeks; ALL trigger eligibility requires 200 triggers and 100 weeks.

## Triggered trade results and recovery

|Triggered trades|Trigger weeks|R0 trigger Avg R|NP50 trigger Avg R|R0 trigger Total R|NP50 trigger Total R|Delta Total R|Improved|Harmed|Unchanged|
|---|---|---|---|---|---|---|---|---|---|
|6927|599|-0.137175|-0.175928|-950.211266|-1,218.654467|-268.443202|3187|3725|15|

|Recovery flag|Trades|Fraction of triggers|
|---|---|---|
|RECOVERED_POSITIVE|2577|0.372023|
|RECOVERED_HALF_R|328|0.047351|
|NEVER_RECOVERED|4350|0.627977|
|LATER_HIT_TP|35|0.005053|
|LATER_HIT_SL|514|0.074202|
|TIME_EXIT_POSITIVE|2542|0.366970|
|TIME_EXIT_NEGATIVE|3817|0.551032|
|TIME_EXIT_ZERO|19|0.002743|

Recovery flags overlap. RECOVERED_POSITIVE means final baseline R>0; RECOVERED_HALF_R means final R>=.50. NEVER_RECOVERED means final R<=0, not absence of a temporary positive excursion. These are interpretation diagnostics and do not enter formal gates.

## NP75 robustness

|Period|Trades|Triggers|Trigger weeks|Delta Total R|Avg delta R|CI lower|CI upper|Eligible for period sample gate|
|---|---|---|---|---|---|---|---|---|
|Historical|9482|3499|356|-85.090886|-0.008974|-0.011985|-0.005977|True|
|Recent A|2688|766|100|-18.673919|-0.006947|-0.011997|-0.001816|True|
|Recent B|2701|926|102|-38.186101|-0.014138|-0.019826|-0.008714|True|
|2026 Monitor|966|435|36|0.565429|0.000585|-0.008839|0.009992|True|
|Recent Combined|6355|2127|238|-56.294591|-0.008858|-0.012492|-0.005372|True|
|ALL|15837|5626|594|-141.385477|-0.008928|-0.011244|-0.006545|True|

## Two-anchor exclusion sensitivity — descriptive only

The same two missing-NP50 anchor identities are removed from both sides of both variants (ALL 15,835 trades). This comparison cannot replace the primary or rescue a failed gate.

|Variant|Trades|R0 Total R|NP Total R|Delta Total R|Avg delta / trade|CI lower|CI upper|
|---|---|---|---|---|---|---|---|
|NP50|15835|1,360.079808|1,091.636607|-268.443202|-0.016953|-0.020951|-0.012942|
|NP75|15835|1,360.079808|1,218.890554|-141.189255|-0.008916|-0.011241|-0.006536|

Sensitivity verdict: **NOT_SUPPORTED**; agreement with primary: **True**. Full period estimates and CIs are in the sensitivity CSV.

|Gate|Sensitivity pass|Diagnostic verdict|
|---|---|---|
|A|False|NOT_SUPPORTED|
|B|False|NOT_SUPPORTED|
|C|False|NOT_SUPPORTED|
|D|False|NOT_SUPPORTED|
|E|False|NOT_SUPPORTED|
|F|False|NOT_SUPPORTED|
|G|True|NOT_SUPPORTED|
|H|True|NOT_SUPPORTED|

## Safety and formal gates

|Period|R0 worst day|NP50 worst day|R0 worst week|NP50 worst week|R0 MaxDD R|NP50 MaxDD R|Period safety pass|
|---|---|---|---|---|---|---|---|
|Historical|-12.116818|-11.529565|-14.455836|-14.322280|29.211511|26.700795|True|
|Recent A|-11.493424|-10.792105|-13.125830|-11.669801|21.641262|20.287215|True|
|Recent B|-5.102508|-4.794816|-6.911786|-6.437088|16.014834|13.231050|True|
|2026 Monitor|-5.912815|-4.701172|-5.288938|-4.949964|14.122778|11.763561|True|
|Recent Combined|-11.493424|-10.792105|-13.125830|-11.669801|21.641262|20.287215|True|
|ALL|-12.116818|-11.529565|-14.455836|-14.322280|29.211511|26.700795|True|

Worst Day/Week use entry dates and entry weeks, consistent with the original Plan. MaxDD is cumulative realized R ordered by exit, strategy and entry, not monetary/mark-to-market drawdown. Gate H requires no metric to worsen more than 10% in any fixed period.

|Gate|Pass|Verdict|
|---|---|---|
|A|False|NOT_SUPPORTED|
|B|False|NOT_SUPPORTED|
|C|False|NOT_SUPPORTED|
|D|False|NOT_SUPPORTED|
|E|False|NOT_SUPPORTED|
|F|False|NOT_SUPPORTED|
|G|True|NOT_SUPPORTED|
|H|True|NOT_SUPPORTED|

A: positive ALL total-R delta; B: mean-delta CI lower>0; C: Historical delta>=0; D: Recent Combined delta>0; E: at least two eligible recent subperiods with positive delta; F: NP75 ALL and Recent Combined deltas>=0; G: trigger sample floor; H: fixed safety thresholds. Profit improvement is primary; safety cannot justify a loss of Total R.

## Strategy and C1 interpretation

NP50 positive Total-R delta in 1/27 strategies; 1 satisfy the 30-trigger / 20-week floor and are labeled EXPLORATORY_STRATEGY_SIGNAL. No strategy-specific adoption. Largest negative and positive diagnostics:

|Strategy|Name|Triggers|Weeks|Delta Total R|Recovery rate|Later TP rate|Label|
|---|---|---|---|---|---|---|---|
|1|1_EJ_Log1|236|208|-26.298571|0.394068|0.000000|NO_EXPLORATORY_SIGNAL|
|5|5_GJ_Port_Log2|492|350|-24.464444|0.359756|0.000000|NO_EXPLORATORY_SIGNAL|
|3|3_EJ_NightBlitz_21|485|377|-19.210667|0.354639|0.004124|NO_EXPLORATORY_SIGNAL|
|12|12_UJ_Short_Core|141|102|-0.760000|0.319149|0.000000|NO_EXPLORATORY_SIGNAL|
|14|14_UJ_Sat_3rd|20|20|-0.153333|0.250000|0.000000|NO_EXPLORATORY_SIGNAL|
|24|24_GA_D_1|193|193|1.316667|0.284974|0.000000|EXPLORATORY_STRATEGY_SIGNAL|

C1 modified exits after +0.5R/+1.0R favorable milestones; C2 modifies only still-open trades that never reached +0.25R by the fixed checkpoint. Prior progress followed by giveback stays on the baseline in C2. No C1 result was used to retune C2.

## Validation and files

16/16 synthetic tests passed. Independent verification: **116/116 PASS**, including both primary/sensitivity totals and empirical bootstrap CIs, every paired delta/recovery flag, source hashes, gates and verdicts. **345 representative M1 replays** passed, covering all strategy/variant/assessment groups and all delayed checkpoints, including both missing cases. Original stopped files were checked unchanged.

Full reference trade-detail rows: 32,596 (16,298 anchors × 2 variants); formal detail rows: 31,674. Local detail bytes: 10013795; SHA-256 `15ba2e311ceb0ece9901a6c1317e090c6665bb93cb0c90e0c0ca1870aa872cc6`. Detail is local only at `/private/tmp/c2_no_progress_phase1_v2_20260926/c2_no_progress_phase1_trade_detail_local.csv`; aggregate/audit files are published with a manifest.

New files: Plan `docs/97_c2_no_progress_phase1_missing_execution_amendment.md`; Result `docs/98_c2_no_progress_phase1_v2_result.md`; driver `src/research/c2_no_progress_phase1_v2.py`; tests `tests/test_c2_no_progress_phase1_v2.py`; verifier `tests/verify_c2_no_progress_phase1_v2.py`; notebook `notebooks/c2_no_progress_phase1_v2.ipynb`; CSVs in `results/c2_no_progress_phase1_v2/`. Notebook saves to `/content` and Drive save defaults OFF.

**Final verdict: NOT_SUPPORTED; Phase2Eligible=False.** No Phase 2 or money simulation was run. No checkpoint or threshold search follows this result. Dell Volatility Phase 5 remains Global R2 only; EA / SET / RunId / VPS / risk / Demo / live are unchanged.
