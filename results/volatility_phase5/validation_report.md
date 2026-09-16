# Phase5 predeployment validation report

Status: IMPLEMENTED_NOT_COMPILED_NOT_DEPLOYABLE. Forward status: NOT_STARTED.
Plan SHA: 9930d2f7fdf903fd60a85ba286592a0cf72a0412.

## Completed local checks
- Python unittest: 22 tests PASS, including 505 midrank values, 1,000 deterministic lot regression cases, DST transition/ambiguous hours, daily aggregation/Saturdays/gaps, 271/272 warmup, no-lookahead mutations, fallback/risk mapping, invalid lots, full 120-input SET, 22 disabled/27 enabled, verdict priority.
- Static comparison: 14 Step9.2.4 reconciliation/dynamic-SL functions unchanged, full SetupStrategies unchanged. This does NOT establish actual MT5 runtime regression.
- Original Step9.2.1/Step9.2.4 Git blob hashes match the remote base exactly. Plan blob also matches. Dedicated dependency copy contains only safe input defaults, clock/GV namespace routing and renamed initializer; no strategy/event table edits.
- Source review: demo account checks at init, callbacks and active order submissions; account/server-specific GV names bounded to 63 chars; raw/min/cap lot guards; independent tick-input audit; candidate ID based on actual magic (array order differs from strategy number); persistent position-to-candidate linkage for exit/deal events; no premature WeeklyBase creation by filtered candidates.
- No tracked live EA, Plan or Phase4 file changes. No live binary generated or deployed.

## Unexecuted mandatory gates
- MetaEditor compile: NOT_RUN (this Mac environment has no MT5/MetaEditor). No ex5 is supplied.
- Actual MQL core script: NOT_RUN. src/EA/phase5_demo/test_vol_r2_core.mq5 contains 24 assertions and never sends orders.
- Actual MQL/Python same-snapshot parity: NOT_RUN. audit_vol_r2_snapshot.mq5 and synthetic_m1_fixture.csv/expected.json are prepared; real Dell feed parity still required. Numeric tolerance may not excuse a different rank numerator/quintile.
- Full MT5 reconciliation scenario regression (delayed fills/pending/timeouts/duplicate prevention/exit): NOT_RUN; existing implementation retained and source-checked only.
- Dell account/server, timezone, source history completeness, symbol specs, compile build, final SET and binary hashes: PENDING.
- History-load latency/disk use: NOT_MEASURED. First eligible candidate may load 600 calendar days of M1. Same symbol/day synchronized unchanged-count history reuses its immutable snapshot. A candidate whose window expires during work cannot place a late order. Any resulting missed entry must be investigated, not silently excluded.
- Natural-forward A–G, 14 days, 10 candidates, 2 quintiles/2 symbols, real entry/exit and weekly rollover: NOT_STARTED.

## Important review limits
The independent Python reference uses math.fsum; MQL uses a compensated window sum. Real-data and frozen research pandas parity must be measured, especially ties. Never add an epsilon to ranks to make a failing comparison pass.
Europe/Helsinki ambiguous/nonexistent local timestamps fall back rather than infer a fold; ordinary DST boundaries have unit fixtures. Initial broker timezone must be independently confirmed before Approved=true.
The 600-day request drops its first observed day to avoid partial leading-day OHLC. The independent audit uses exactly the resulting exported snapshot, including raw server/JST timestamps. This may change the first TR only far before the required recent 253 ATR values when adequate extra history exists; near warmup boundary validate explicitly against frozen research before release.
Runtime logs join source/binary/SET metadata using the frozen RunId manifest. Full original TradeResult logs remain necessary to review all pending/timeout paths; the numeric audit deliberately does not grant a forward verdict.
Complete production event settings must be compared to actual Dell values before deployment. Existing 2026 calendar coverage must be reviewed before any 2027 extension.
No restart test is required for Dell. VPS restart/WeeklyBase restoration remains a separate future gate.

## API references reviewed
- [CopyRates](https://www.mql5.com/en/docs/series/copyrates): partial history availability and synchronized series must be checked.
- [Account properties](https://www.mql5.com/en/docs/constants/environment_state/accountinformation): DEMO trade mode and account identity guard.
- [FileOpen](https://www.mql5.com/en/docs/files/fileopen): terminal-local evidence exports.

Python: 3.12.14; platform: macOS-26.5.2-arm64-arm-64bit
