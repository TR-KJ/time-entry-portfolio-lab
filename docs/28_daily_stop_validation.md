# Daily Stop Validation Specification

Status: baseline accepted and frozen (2026-09-09 JST)

Accepted result: `docs/29_daily_stop_baseline_result.md`

## 1. Purpose and scope

This research evaluates a portfolio-level Daily Stop without changing the established 28-strategy trading model. The repository remains `TR-KJ/time-entry-portfolio-lab`; work is isolated on branch `research/daily-stop-validation`.

The implementation is deliberately split into two layers:

1. audited M1 data -> fixed 28-strategy Baseline Trade Log (no Daily Stop),
2. the exact same fixed trade log -> Daily Stop analysis.

Daily Stop thresholds must never trigger a new M1 backtest. EA, VPS, SET and live-operation code are outside this branch's scope and must not be modified.

## 2. Fixed evaluation periods

Period assignment uses `EntryTime` in JST.

| Segment | Range |
|---|---|
| IS | 2015-01-01 through 2021-12-31 |
| OOS1 | 2022-01-01 through 2025-12-31 |
| OOS2 | 2026-01-01 through the available audited-data endpoint (2026-09-09) |

These boundaries are fixed before Daily Stop testing and must not be moved after observing results.

## 3. Audited M1 data

All seven pairs passed the full-period OHLC audit. Every series runs from 2015-01-02 16:00 JST through 2026-09-09 06:00 JST.

| Pair | Rows | 2026 rows | Parse NG | Duplicates | OHLC NaN | High NG | Low NG | Gaps >5d | Expected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| USDJPY | 4,340,793 | 254,267 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EURJPY | 4,341,959 | 254,324 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| GBPJPY | 4,340,301 | 254,291 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| AUDJPY | 4,340,508 | 254,261 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| AUDUSD | 4,339,756 | 254,281 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EURAUD | 4,340,975 | 254,307 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| GBPAUD | 4,326,984 | 254,272 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |

The code uses an explicit 56-file manifest (seven pairs x eight files), so obsolete or damaged files left in Drive cannot be picked up accidentally.

### GBPAUD 2019 known gaps

The two expected gaps are:

- 2019-01-03 07:45 -> 2019-01-09 07:00 JST (5d 23:15)
- 2019-05-07 13:30 -> 2019-05-13 06:02 JST (5d 16:32)

The same gaps were reproduced after re-export and also exist in M5. They are not filled from another broker. No new date exclusion is introduced. The baseline retains the historical behavior: if the exact entry bar is absent, no trade is generated; if the scheduled exit and all +1 to +4 minute fallback bars are absent, no trade is generated. Strategy schedules are evaluated for every calendar date in the covered range, including dates with no bars at all, so skipped-entry and skipped-exit diagnostics expose complete-day gaps as well as isolated missing bars.

## 4. Frozen 28-strategy Baseline

The strategy parameters, calendar rules and Candidate C matrix are inherited from the repository's established 28-strategy model. ATR is OFF. Only the following formally adopted corrections are added:

- `12_UJ_Short_Core`: 20/25/30 remain normal GOTO dates; when the 25th or 30th falls on Saturday/Sunday, the immediately preceding Friday is also GOTO. The 20th is never moved forward and holidays are ignored.
- `1_EJ_Log1`: add `position_overlap` stops for FOMC, US NFP, BOJ and ECB. US CPI retains its existing `US_CPI_WEEK_WED` special stop.

This study does not refine historical event timestamps. It keeps Candidate C's fixed research-time assumptions, preventing event-calendar improvements from being mixed with Daily Stop effects.

### Price and execution rules

- Scheduled entry uses the exact JST M1 `Open`.
- Long entry = Open + fixed spread; short entry = Open - fixed spread.
- CSV `<SPREAD>` is ignored.
- Fixed spreads (pips): UJ 0.5, EJ 1.0, GJ 2.0, AJ 1.5, AU 1.5, EA 1.5, GA 2.0.
- Scheduled time exit uses M1 `Open`; if absent, search +1 through +4 minutes. If none exists, do not generate the trade.
- From entry through the selected exit bar, inspect each M1 High/Low in chronological order.
- SL/TP prices are based on the spread-adjusted entry.
- When SL and TP are both touched within the same M1 bar, SL wins (conservative rule).
- Overnight positions continue to their specified next-day exit; there is no midnight liquidation.
- `R = realized Pips / actual SL pips used by that trade`. UJ12 therefore uses its actual NORMAL or GOTO SL denominator.

## 5. Daily Stop rules (analysis layer only)

Daily Stop is applied only after the Baseline Trade Log has been generated, exported and identified by SHA-256.

For a candidate trade with entry time `T`, the available realized daily result is the sum of accepted trades satisfying:

```text
same JST accounting day AND CloseTime < T
```

Rules:

- Only strictly earlier closes are available. `CloseTime == EntryTime` is not used; this prevents future/intra-timestamp ordering information.
- When available realized cumulative R is at or below the tested loss threshold, the candidate is blocked.
- Once the threshold is reached, the stop is latched for the rest of that JST date. Later closes from positions already open cannot restart entries even if cumulative R recovers.
- Close events sharing the same M1 timestamp are aggregated before the threshold is evaluated; their unknowable within-minute order is never used.
- Blocked trades add neither profit nor loss and never affect later cumulative R.
- The state resets at 00:00 JST each day.
- Entry ordering is deterministic: `EntryTime`, then the frozen strategy number.
- Overnight trades contribute only after their actual close and only to the JST day containing that close; they cannot retroactively block earlier entries.
- Baseline, accepted and blocked rows must remain separately auditable.

The predeclared comparison is `none / -1R / -1.5R / -2R / -2.5R / -3R / -4R`. Fine-grained values must not be added after seeing results.

`daily_stop_analysis.py` defaults to `IS_SELECTION`. In that mode it calculates only 2015-2021 and explicitly does not calculate or display OOS1/OOS2. After one robust threshold is chosen from IS and recorded, `FROZEN_REPORT` evaluates that one frozen threshold on FULL, IS, OOS1 and OOS2 without retuning.

The analysis code reads only the accepted Baseline Trade Log and aborts unless its SHA-256 is `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`. It does not read M1 data or recalculate baseline trades. Notebook summaries and detailed decisions, accepted trades, blocked trades, daily ledgers, stop events, metadata and output hashes are written to `/content` as CSV.

## 6. Baseline outputs

The Colab program displays summaries in the notebook and writes the same artifacts to `/content`:

- `/content/daily_stop_baseline_trades.csv`
- `/content/daily_stop_baseline_summary.csv`
- `/content/daily_stop_baseline_yearly_summary.csv`
- `/content/daily_stop_baseline_strategy_summary.csv`
- `/content/daily_stop_baseline_diagnostics.csv`
- `/content/daily_stop_baseline_manifest.csv`
- `/content/daily_stop_baseline_run_metadata.csv`

The metadata contains the trade-log SHA-256, source revision and rule flags. `/content` is temporary; after review, confirmed results may be copied to Drive and committed under `results/daily_stop/`.

## 7. Reproducibility and acceptance checks

A run is accepted only if:

- all 56 manifest files are found exactly once;
- input timestamps parse, OHLC values are numeric, duplicates are absent, and OHLC integrity holds;
- exactly 28 strategy definitions execute;
- `R == Pips / SL` within numeric tolerance and all SL exits equal `-1R`;
- no Daily Stop fields or decisions appear in the baseline engine;
- output row order is deterministic and the SHA-256 is recorded;
- diagnostics and summaries are reviewed before the log is frozen for Daily Stop analysis.
- all three post-filter GBPAUD 2019 gap candidates are present as `MISSING_ENTRY` diagnostics.
