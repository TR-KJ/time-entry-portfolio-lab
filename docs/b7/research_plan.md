# B7 Master Protocol — pre-implementation conditions Freeze

B7 Pips-First Recent-Era Time-Entry Rediscovery is an independent research line based on main. This snapshot fixes the user's agreed design and records unresolved choices; it is **not Stage1 implementation/execution authorization**. Safety, correctness, reproducibility and rules before results take precedence. Never use B6 candidate identities, pair/weekday/time outcomes or performance to design or select B7 candidates.

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

## Discovery sequence — AGREED design, unresolved thresholds

1. Stage1 five-minute coarse exploration over pair × Long/Short × Entry weekday (Mon–Fri) × 288 Entry minutes × 283 planned holdings (30…1440, five-minute step). 7,335,360 time structures and 44,012,160 variants (Pure Time + five SL), before availability/gates. These are not independent hypotheses or trade counts. **No sweep in Stage0.**
2. Evaluate Pure Time (no SL/no TP) as the primary Pips edge and five fixed SL/no TP as robustness, never select by best SL alone. Five SLs derive only from the separate price calibration prespec. P01 now formally adopts the exact nine grids in stage1_prespec.json; no additional SL or result-driven recalibration.
3. Rank within each pair, never globally across pairs: PositiveYearCount DESC, MedianAnnualAvgPips DESC, WorstYearAvgPips DESC, PFpips DESC, Overall AvgPips DESC, TotalPips DESC, MaxDDPips ASC, fixed key. Stable four-year behavior is the goal; the explicit U01/U02 gate requires at least3/4 positive years (Annual TotalPips >0).
4. Plateau/neighborhood stability avoids isolated peaks. U03/U04 now freeze the 3x3 neighborhood, valid minimum4, PASS ratio2/3, all-valid median threshold0.80, direct non-transitive family suppression and deterministic fixed key; see stage1_conditions_freeze.md. After de-duplication: at most eight Time Families per pair (72 total), zero minimum; three pass means three, zero means zero. No B6 top50 or R-first ranking is adopted. Numeric gates/distances in U01–U04 are now explicit B7 user decisions, not inherited defaults.
5. SL robustness/selection → TP search/selection → Weekday ON/OFF → Day-of-month → Month Seasonality → Calendar Freeze → one-minute fine tune → Event Filter → Candidate Freeze. No one-minute optimization before SL/TP/calendar decisions.
6. Weekday: up to31 nonempty Mon–Fri subsets, broad operating structure favored; only repeatedly destructive weekdays off. U04 permits cross-weekday family suppression with anchor/supporting weekdays and original metrics retained; later Weekday ON/OFF selection criteria remain UNDECIDED under U07.
7. DOM: 1–10,11–20,21–month-end, up to7 nonempty subsets. Limited damaging-bucket removal, not cherry-picking the best bucket.
8. Months: individual diagnostics for12 months plus Leave One Month Out (Jan omitted…Dec omitted). No4095-subset exhaustive search; risk-removal of repeatedly damaging months only, at most2 months off as the agreed policy. Minimum samples/pass rules and two-month combination protocol require Chat.
9. Fine tune after Calendar Freeze: original5m anchor Entry±5/Exit±5 minutes at1-minute step; no rescue of Stage1 failures, no reanchor, no return to SL/TP/calendar. Plateau required; exact criteria remain unresolved.
10. Event modes: E0 NONE; E1 constituent central banks (USD/FOMC,JPY/BOJ,EUR/ECB,GBP/BOE,AUD/RBA); E2 E1+US NFP+US CPI, plus AUD CPI only for AUD pairs. EU E1=ECB/FOMC; GU E1=BOE/FOMC. No Candidate C strategy-specific matrix. Adoption thresholds and exact calendar/window source freeze remain pending.

## Pips metrics and undefined values

Trades/Wins/Losses/ZeroPips, AvgPips/TotalPips/PFpips/MaxDDPips, annual AvgPips/TotalPips/PFpips, PositiveYearCount/MedianAnnualAvgPips/WorstYearAvgPips are planned. Missing executions are not trades; zero Pips is a trade but neither win nor loss. PFpips=positive pips sum/abs(negative pips sum). Profit-only=INF label, empty/all-zero=UNDEFINED label, loss-only=0. No large numeric sentinel. P02/U05 are now AGREED/FROZEN: unrounded Pips, planned Entry JST year, cumulative/peak0 DD with CloseTime/EntryTime/fixed-key ordering. INF/UNDEFINED cannot pass the mandatory loss/sample gates. All four Discovery years need >=30 trades; do not omit deficient years from the ranking median. See the complete frozen specification.

## Freeze and later stages

Candidate Freeze and its selection use Discovery2020–2023 only. Validation2024–2025 is not a selection dataset: do not change time,SL,TP,weekday,DOM,month or Event after seeing it. FAIL stays FAIL. Monitor2026 is OBSERVED only; no reversal of Validation status. Previously studied periods are not claimed pristine unseen OOS.
Only **after B7 Validation** compare B6/B7 pair,direction,weekday,Entry,Exit,holding,SL,TP and overlap for independent convergence. Money/R/fixed risk/Existing27/B6/B7/B6+B7/Portfolio/Global R2 are later separate work. PASS≠live adoption. No Strategy number allocation.

## Current stopping point

P01/P02/U01–U05 conditions documentation/config Freeze only. U06–U12 remain UNDECIDED, including U12 runtime/resume/artifact/Colab contract. No Stage1 executor/notebook, sweep, performance, ranking or Top8 work is authorized or performed. B01 = CLEAR_WITH_LIMITATION; Stage0 = PASS_WITH_PROVENANCE_LIMITATION unchanged. Do not merge main, edit B6, force-push, or modify existing EA/SET/VPS/forward/live.
