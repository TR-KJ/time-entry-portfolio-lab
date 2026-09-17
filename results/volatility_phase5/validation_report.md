# Phase 5 OANDA timestamp revision — validation

Timezone addendum remote SHA: 9953aa01409db80779984e62acea61f2bfe4a1e6. Original Plan remains 9930d2f7fdf903fd60a85ba286592a0cf72a0412.
Status: REVISED_SOURCE_NOT_COMPILED_NOT_DEPLOYABLE.

- Python unittest: 30 PASS, including calendar-rule mirror vs independent America/New_York zoneinfo over 2007–2035, exact gap/fold rejection, US/EU mismatch dates, JST midnight/weekly/history boundaries, risk/fallback/lot/config/no-lookahead and existing static reconciliation regression.
- 21,286 UTC test instants (29 years × (12 monthly anchors + 722 transition-neighborhood minutes)); this is a Python mirror check, not actual MQL execution.
- Shared MQL no-order script expanded from24 to34 assertions; revised compile/run PENDING on Dell.
- Frozen P5Risk/P5Quintile/P5Calculate/P5Size bodies byte-identical to prior revision. Dedicated strategy dependency and both original live source files unchanged. Original Plan unchanged.
- Synthetic fixture keeps JST/OHLC and expected280 days/ATR3.0125/n311/Q4/risk1.1; only raw ServerTime changed to OANDA.
- Snapshot script reserves array capacity in8192-bar blocks and rejects allocation failure for large real-feed audit; CSV calculation semantics unchanged.
- Full SET still120 inputs,27 enabled/22 disabled, approvalfalse, login0; renamed OANDA time-verification input defaultsfalse. All real account settings remain unset.

Old Dell compile0/0 and core24/24/synthetic parity relate to old source only. Revised compile, core34/34, synthetic rerun, same-Dell-feed MQL parity and binary hashes remain PENDING. Actual order/reconciliation acceptance and forward observations are not run. No VPS/live change. No deployment approval.

Seven actual exports: all4,450,335 raw timestamps agree between calendar mirror and independent zoneinfo. InputSHA256 matches all previously received exports. Each symbol has513 completed days after the frozen600-day request/drop-first-day policy. Revised independent reference and pandas agree on finalATR/rank; all dailyOHLC/TR/ATR/count rows agree with the prior diagnosticUS result (absolute tolerance1e-12). This does not certify MQL real-feed parity. Latest conditional Q: UJ5,EJ4,GJ4,AJ3,AU1,EA1,GA1, asof2026-09-16 00:00 JST.
