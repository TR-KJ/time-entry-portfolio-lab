# Phase 5 — OANDA timestamp adapter correction (pre-implementation)
Status: PREREGISTERED; must be committed and remote SHA read back before code edits.
Parent evidence commit: ba31b37fa1b6b7833f7d9677f3f414303f7d1a73.
Original Plan: 9930d2f7fdf903fd60a85ba286592a0cf72a0412. Original implementation: 603c33cd6a945d2e18ca95b88a93b9a568537e73.

## Purpose and provenance
User confirms original research M1 came from MetaQuotes MT5 demo (user assertion, exact server identity not independently inspected). Original 56 hashes match. Seven symbols in five 2025 windows support differing original/OANDA raw clocks. Do not infer universal historical policy from broker name.
OANDA official source: https://www.oanda.jp/lab-education/e-learning/mt5basic/mt5chart/jpn_times/ specifies US winter GMT+2 / US summer GMT+3 and NY17:00 rollover.
Only Dell demo input-time conversion is corrected. Original research data, conversions and Phase4 results remain immutable. No profit reoptimization.

## Explicit supersession
This addendum supersedes the original Phase5 Plan's requirement to interpret Dell OANDA raw timestamps as Europe/Helsinki and the Helsinki-specific verification input. It preserves true JST daily boundaries; ATR20 TR SMA; completed actual trading days including Saturday; previous252 midrank excluding evaluated day; Q cuts and risk .50/.70/.90/1.10/1.30; .90 fallback; 27 strategies excluding22; all acceptance rules and observation minimums.
Frozen original Plan is not edited. Deployment restart testing remains excluded; future VPS acceptance requires it separately. VPS/live files and branches untouched.

## Exact adapter contract
Version OANDA_US_DST_V1, supported dates 2007 onward under current US DST legislation (no assertion future law cannot change).
UTC offset +3 between second Sunday of March 07:00 UTC inclusive and first Sunday of November 06:00 UTC exclusive; +2 otherwise.
Raw server→UTC: evaluate candidates raw-2h and raw-3h against that rule. Accept exactly one; reject ambiguous/nonexistent local times. Convert accepted UTC to JST +9h. Never use host OS DST or today's offset for historical rows.
Thus on 2026-03-08 server09:00–09:59 does not exist; on 2026-11-01 server08:00–08:59 is ambiguous. Invalid conversion must not silently produce a usable current clock.
JST→server uses JST-9h then the UTC rule. Reject unsupported pre-2007 dates.
Python independent reference uses America/New_York with server=NY wall time+7h; resolve folds with UTC roundtrip. This differs algorithmically from MQL calendar arithmetic.
Apply the adapter consistently to P5Now/current strategy scheduling, WeeklyBase's JST week key through existing GetJstTime path, historical CopyRates boundaries, each raw M1 row, snapshot audit and initialization/diagnostic logs.
Rename InpPhase5HelsinkiVerified to InpPhase5OandaTimeVerified, defaultfalse in EA and full SET. Keep Approvedfalse, login0, unset server/run. No backward alias that could preserve old mistaken approval. Log version OANDA_US_DST_V1. Require a fresh RunId for the revised package.
Keep demo binary distinct from live. Recompile dedicated source and scripts; previous binaries are not proof for this revision.

## Validation fixed before implementation
- Existing Python suite including risk/fallback/lot/27-strategy/reconciliation-static regression passes; static tests remain distinct from MQL runtime.
- Test US spring/autumn exact boundaries, rejected gap/fold, US/EU mismatch dates, ordinary winter/summer, pre-2007 rejection and JST midnight/weekly boundary.
- Independent oracle checks MQL calendar-rule mirror against zoneinfo 2007–2035 including transitions and roundtrips; not labeled actual MQL execution.
- Expand actual shared-core no-order MQL test script with US timestamps and scheduling/history-boundary roundtrip assertions; execution and compile remain Dell gates.
- Regenerate synthetic fixture ServerTime from fixed JST with the OANDA rule, leaving JST/OHLC and expected daily values unchanged.
- Reprocess seven actual Dell M1 exports using US conversion and independent reference; record as-of 2026-09-16 00:00 JST / last completed daySep15. Same inputs/hashes; source600-day range and first observed day exclusion unchanged. Compare OHLC/ATR/rank/quintile with the preceding diagnostic-US results.
- Actual same-feed MQL/Python parity, all revised compile0/0, binary hashes, clock evidence and final allowlisted SET remain mandatory before any order. No deployment based on local Python pass alone.

## Deliverables
Updated dedicated demoEA/shared core/runtime, Python audit, unit tests, no-order MQL test, US-timestamp synthetic fixture, default-disabled SET, deployment checklist, validation report, revised source ZIP with hashes and clear NOT_COMPILED designation.
Before Dell operation, report addendum and implementation remote SHAs and verification outcomes. Dell operation instructions remain one step per user confirmation.
