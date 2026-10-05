# B7 Master Protocol — pre-implementation conditions Freeze

B7 Pips-First Recent-Era Time-Entry Rediscovery is an independent research line based on main. This snapshot freezes all user-agreed research conditions before results; it is **not Stage1 implementation/execution authorization**. Safety, correctness, reproducibility and rules before results take precedence. Never use B6 candidate identities, pair/weekday/time outcomes or performance to design or select B7 candidates.

## Data and boundaries

Nine planned symbols: USDJPY/UJ, EURJPY/EJ, GBPJPY/GJ, AUDJPY/AJ, AUDUSD/AU, EURAUD/EA, GBPAUD/GA, EURUSD/EU, GBPUSD/GU.
Canonical time is naive JST after Europe/Helsinki localization with ambiguous=infer, nonexistent=shift_forward, then Asia/Tokyo conversion. Reject JST duplicates; do not repair them by dropping rows.

- Discovery: [2020-01-01, 2024-01-01).
- Validation: [2024-01-01, 2026-01-01).
- Monitor: [2026-01-01, 2026-09-10).

All-period bytes/OHLC/timestamps may be read **only in the integrity audit layer**. Copy only Discovery OHLC across the calibration/research boundary, reject future rows at its API, and do not retain a full-data parent array. Coverage is actual availability, not proof of uninterrupted market coverage. Never synthesize missing tails or join another broker. Different broker/source confirmed means STOP. The existing B01 decision is CLEAR_WITH_LIMITATION and Stage0 is PASS_WITH_PROVENANCE_LIMITATION; the frozen 72-file Research Data Collection is accepted with the known historical certification limitations in source_of_truth.md. EU/GU have no automatically assumed pre-existing formal audit.

Raw M1 is read in place; no raw data, complete baseline ledger, credentials or personal absolute paths are committed. File identity is filename + SHA256 + rows + raw endpoints, not filename alone. Expected B7 inventory is generated from audited actual files; the B6 manifest is a separately identified seven-pair reference only.

## Price and execution contract — AGREED

|Pair|Fixed spread pips|Pip size|
|---|---:|---:|
|USDJPY|0.5|0.01|
|EURJPY|1.0|0.01|
|GBPJPY|2.0|0.01|
|AUDJPY|1.5|0.01|
|AUDUSD|1.5|0.0001|
|EURAUD|1.5|0.0001|
|GBPAUD|2.0|0.0001|
|EURUSD|1.0|0.0001|
|GBPUSD|1.5|0.0001|

EU1.0/GU1.5 are pre-fixed research assumptions, **not estimated historical average spreads**. CSV SPREAD does not override them. GU2.0 is not an accepted setting.
Entry exact M1 Open; Long=Open+spread, Short=Open−spread. Exit M1 Open, exact then first +1…+4 minute fallback, never +5. Secure exit availability before any SL/TP path scan; an earlier SL cannot rescue a missing exit. Entry and selected Exit bars inclusive; same-bar SL/TP is SL first. Compare raw High/Low without epsilon or price rounding. No interpolation or intermediate-gap filling. Missing trade stays missing, not zero pips. Overnight allowed; no reconnection to Monday after a weekend, no period boundary crossing. Entry stop Dec25–Jan3. Planned holding 30…1440 minutes. Any B7-specific execution change must be documented and await Chat **before implementation**.

B7 Stage0 contains isolation/audit/calibration functions and a byte-identical B6 execution fixture for compatibility tests; it contains no B7 Stage1 runner. Pure Time's future no-SL implementation must retain the same entry/exit availability and period guards. B6's old SL-required executor is not silently relabeled as a Pure Time engine.

## Formal research sequence — AGREED/FROZEN

1. Stage1 five-minute coarse exploration over pair × Long/Short × Entry weekday (Mon–Fri) × 288 Entry minutes × 283 planned holdings (30…1440, five-minute step). 7,335,360 time structures and 44,012,160 variants (Pure Time + five SL), before availability/gates. These are not independent hypotheses or trade counts. **No sweep in Stage0.**
2. Evaluate Pure Time (no SL/no TP) as the primary Pips edge and five fixed SL/no TP as robustness, never select by best SL alone. Five SLs derive only from the separate price calibration prespec. P01 now formally adopts the exact nine grids in stage1_prespec.json; no additional SL or result-driven recalibration.
3. Rank within each pair, never globally across pairs: PositiveYearCount DESC, MedianAnnualAvgPips DESC, WorstYearAvgPips DESC, PFpips DESC, Overall AvgPips DESC, TotalPips DESC, MaxDDPips ASC, fixed key. Stable four-year behavior is the goal; the explicit U01/U02 gate requires at least3/4 positive years (Annual TotalPips >0).
4. Plateau/neighborhood stability avoids isolated peaks. U03/U04 now freeze the 3x3 neighborhood, valid minimum4, PASS ratio2/3, all-valid median threshold0.80, direct non-transitive family suppression and deterministic fixed key; see stage1_conditions_freeze.md. After de-duplication: at most eight Time Families per pair (72 total), zero minimum; three pass means three, zero means zero. No B6 top50 or R-first ranking is adopted. Numeric gates/distances in U01–U04 are now explicit B7 user decisions, not inherited defaults.
The full sequence, including the Stage1 described above, is:

1. Stage0 Source/Data/Protocol
2. Stage1 5m Pure Pips + 5SL robustness
3. SL local Plateau / Freeze
4. TP search / Freeze
5. Weekday
6. DOM
7. Month Seasonality / LOMO
8. Calendar Freeze
9. 1m Fine Tune
10. E2 Event Policy + E0/E1/E2 diagnostics
11. MFE/Giveback + Profit Protection
12. Candidate Freeze
13. Validation 2024–2025
14. Monitor 2026
15. B6 structural comparison
16. Money/R/Portfolio/Global R2

U06 adopts formal SL/TP only after Stage1; local zones, fixed rankings and TP_NONE preference are in the full prespec. U07 uses only four nested weekday sets, not31 subsets. U08 uses sequential DOM0/1/2 and M0/1/2 with frozen bad-bucket/month candidates, not7 or4095 exhaustive subsets. Calendar is frozen before U09; no1m plateau retains the five-minute anchor rather than dropping the candidate. U10 fixes E2 before results; E0/E1/E2 are diagnostics, never a performance mode selection. U10-P follows E2, fixes only P0/P1/P2/P3 protection and cannot retune earlier conditions.

## Pips metrics and undefined values

Trades/Wins/Losses/ZeroPips, AvgPips/TotalPips/PFpips/MaxDDPips, annual AvgPips/TotalPips/PFpips, PositiveYearCount/MedianAnnualAvgPips/WorstYearAvgPips are planned. Missing executions are not trades; zero Pips is a trade but neither win nor loss. PFpips=positive pips sum/abs(negative pips sum). Profit-only=INF label, empty/all-zero=UNDEFINED label, loss-only=0. No large numeric sentinel. P02/U05 are now AGREED/FROZEN: unrounded Pips, planned Entry JST year, cumulative/peak0 DD with CloseTime/EntryTime/fixed-key ordering. INF/UNDEFINED cannot pass the mandatory loss/sample gates. All four Discovery years need >=30 trades; do not omit deficient years from the ranking median. See the complete frozen specification.

## Freeze and later stages

Candidate Freeze and its selection use Discovery2020–2023 only. Validation2024–2025 is not a selection dataset: do not change time,SL,TP,weekday,DOM,month,Event or Protection after seeing it. FAIL stays FAIL. Monitor2026 is OBSERVED only; no reversal of Validation status. Previously studied periods are not claimed pristine unseen OOS.
Only **after B7 Validation** compare B6/B7 pair,direction,weekday,Entry,Exit,holding,SL,TP and overlap for independent convergence. Money/R/fixed risk/Existing27/B6/B7/B6+B7/Portfolio/Global R2 are later separate work. PASS≠live adoption. No Strategy number allocation.

## Current stopping point

All conditions P01/P02/U01–U12 + U10-P are AGREED/FROZEN. Full authoritative protocol: full_research_conditions_freeze.md and research_inputs/b7/full_research_prespec.json. U11 freezes Validation PASS/FAIL/INSUFFICIENT_SAMPLE and PASS-only Monitor. U12 separates future Work implementation from Colab formal sweep with frozen environment/input/resume/output/COMPLETE_STAGE1_ONLY barriers.

Stage1ConditionsFrozen = true; Stage1ImplementationAuthorized = false; Stage1ExecutionAuthorized = false. No executor/notebook implementation, performance sweep, Candidate ranking, Top8, later-stage execution or new performance result access occurred. Next implementation requires a separate user instruction. B01 and Stage0 unchanged; main/B6/EA/SET/VPS/live unchanged.
