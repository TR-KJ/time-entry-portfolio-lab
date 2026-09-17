# Phase 5 — Timestamp source reconciliation
Status: PREDEPLOYMENT_HOLD; forward NOT_STARTED; final decision NOT_EVALUATED.
Evidence review: 2026-09-17. This document records findings and a proposed resolution, not authorization to deploy or an amendment to the frozen Plan.

## Fixed references
Plan 9930d2f7fdf903fd60a85ba286592a0cf72a0412.
Implementation 603c33cd6a945d2e18ca95b88a93b9a568537e73.
Phase 4 user-confirmed decision DEMO_FORWARD_CANDIDATE is preserved as supplied; this audit does not recalculate or invalidate its historical results.
No EA, SET, Plan or VPS live changes in this evidence commit.

## Evidence chain
1. Located all 56 original M1 inputs on the user's Google Drive. SHA256 matched every entry in results/volatility_phase1/volatility_phase1_input_manifest.csv at the implementation SHA (56/56).
2. Both src/research/daily_stop_baseline_revalidation.py and src/research/volatility_phase1.py localize original raw timestamps with Europe/Helsinki before converting to JST. Phase 1 Plan explicitly fixes this. Phase 5 copied that timezone into P5ServerToJst, including current entry scheduling, and requires InpPhase5HelsinkiVerified.
3. OANDA official MT5 documentation specifies GMT+2 in US winter and GMT+3 in US summer, with NY17:00 day rollover:
https://www.oanda.jp/lab-education/e-learning/mt5basic/mt5chart/jpn_times/
4. Earlier seven-file Dell audit: 4,450,335 rows matching user counts; no duplicate timestamps, invalid OHLC or minute alignment errors. Session gaps are not certified as absent. Applying Helsinki versus the diagnostic US rule to the SAME Dell feed changed 16 symbol-days' quintiles across 1,694 comparable valid symbol-days. This comparison concerns Dell data, not the original Phase 4 trades.
5. Original 2025 raw M1 versus Dell raw M1: compared intrabar CLOSE-OPEN correlation at offsets -120,-60,0,+60,+120 minutes, using five date windows and all seven symbols. All 35 windows selected the predicted offset: 0 in common winter/summer, Dell timestamp +60 minutes in US/EU mismatch weeks. Best correlations range 0.863281–0.983713. These are price alignment diagnostics, not a model performance test or proof of broker identity.
Windows (start inclusive/end exclusive): winter 2025-02-03/02-22; spring mismatch 03-10/03-29; summer 04-01/04-26; autumn mismatch 10-27/11-01; winter again 11-03/11-22.
The common-price alignment strongly supports different timestamp conventions in the two feeds. Original broker/server provenance remains to be confirmed by user or source metadata. This limited 2025 comparison does not certify every historical source segment.

## Interpretation
The previous finding does NOT establish that original Helsinki-based research timestamps were wrong. Original data and Dell data appear to use different raw clocks. Correct source-specific conversion can preserve true JST calendar-day boundaries, ATR20, the 252-day window, no-lookahead and fixed R2 allocations/cuts. Different feeds may still have different OHLC and features; exact cross-broker prices are not an acceptance requirement. Independent EA parity must use the identical Dell feed.

## Proposed resolution (not implemented)
Confirm original feed provenance. Then preregister a separate timestamp-adapter correction addendum without overwriting the historical Plan: original research retains verified source conversion; Dell OANDA adapter uses its US-DST clock. Explain explicitly the change to Plan wording and to current-entry clock/history boundary conversion, rename the misleading Helsinki verification input, and retain all existing R2 statistical definitions.
Verify dated US/EU mismatch cases, server↔UTC↔JST round trips, current entry time, historical CopyRates boundaries, daily OHLC, no-lookahead, and identical-Dell-feed Python/MQL parity before deployment. Broker clock evidence remains required. Do not set HelsinkiVerified=true as a workaround.
No change to risk mapping, Q cuts, ATR or 252 window; no trading or restart acceptance test in this audit.

## Existing Dell setup evidence
User-reported dedicated EA/core/snapshot compile: 0 errors/0 warnings, binary hashes still pending.
Screenshot core: Passed=24 Failed=0 NO_ORDERS=true.
Synthetic MQL snapshot: 280 days, ATR20 3.0125000000000002, rank numerator 311, Q4, risk1.1; exported daily CSV independently matched 280 rows with ATR tolerance.
MT5 build6182; OANDA-Japan MT5 Demo/Hedge confirmed by screenshot; exact private account allowlist not published.
User reports old EA detached from only chart, Algo OFF. Setup restart for Unlimited bars completed; this was not the excluded restart acceptance test.
Real-feed MQL parity, final binary/SET hashes, order reconciliation and forward observations remain outstanding.
