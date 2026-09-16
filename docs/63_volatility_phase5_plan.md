# Volatility Environment Phase 5 — Dell Demo Forward Validation

Status: PREREGISTERED PLAN; no Phase 5 EA implementation or Dell deployment at registration.
Repository: TR-KJ/time-entry-portfolio-lab
Branch: research/volatility-environment-phase5-demo-forward
Base commit: 7795c23f8bb1bf8bc362cb49bec4a9f36e554581
Registration date: 2026-09-16 JST
This document freezes implementation requirements, diagnostics, acceptance and observation rules before code changes. The commit containing only this document is the Plan SHA; verify remote ref, commit parent/diff and this content before implementation. Record that SHA in subsequent validation and start manifests without editing this original plan.

## 1. Purpose and Phase 4 provenance

Verify that fixed R2 operates as designed, safely and reproducibly on Dell OANDA DEMO. This is an implementation/operational acceptance test, not an OOS profitability study. Profit, PF and DD are descriptive only and cannot determine PASS or rescue a failure.

User-fixed Phase 4 formal handoff: DEMO_FORWARD_CANDIDATE; all eight conditions PASS; 27 strategies / 15,837 trades, excluding only 22_GA_C_2. Phase 4 Plan SHA: 08d594b092cc0555ec3f917118eb5e8c22ca22d5. Existing implementation/audit SHA: 7795c23f8bb1bf8bc362cb49bec4a9f36e554581. Branch: research/volatility-environment-phase4-deployment-validation.

Evidence distinction: remote Phase 4 branch resolved to 7795c23 on inspection. That commit's research_inputs/volatility_phase4_deployment_audit.csv still says UNDETERMINED, and docs/62_volatility_phase4_result.md and results/volatility_phase4 are absent from its tree. Formal completion and additional audit evidence are therefore USER-CONFIRMED HANDOFF, not independently verified committed final results. Preserve this distinction; do not rewrite Phase 4 files or claim this SHA contains final PASS evidence. Record any later supplied final artifacts and their hashes separately without changing R2 or criteria.

Source review at the base includes docs/61_volatility_phase4_plan.md, src/research/volatility_phase1.py, volatility_phase2.py, volatility_phase4.py, and Step9.2.4 plus its included Step9.2.1 source. Root/nested AGENTS.md was not present in the inspected complete tree.

## 2. Frozen model and implementation contract

R0 reference Risk=0.90%. R2 Q1=0.50%, Q2=0.70%, Q3=0.90%, Q4=1.10%, Q5=1.30%; insufficient/unavailable feature=0.90%.
No modification of allocations, ATR definition, 252-day reference, cuts, strategy schedules, SL/TP rules or Event Candidate C selection.
R2 is risk allocation, NOT an entry filter. InpUseGlobalAtrP70Filter remains false; broker native D1/iATR is not a substitute.

At each eligible entry time use the target symbol's completed M1 history to reproduce frozen Primary feature:
- Convert broker historical timestamps using verified Europe/Helsinki rules to JST, including historical DST; do not apply today's fixed offset to the entire history. Verify Dell server clock/timezone against dated evidence before start; unresolved mapping blocks deployment.
- Group actual M1 bars by JST calendar date. First Open, max High, min Low, last Close. Include actual Saturday bars; no weekend filling or synthetic zero days.
- Only dates strictly before candidate JST date qualify; AvailableAt=daily date+1 calendar day, LastM1+60 seconds <= candidate. Exclude current partial day and all future observations.
- TR=max(High-Low,abs(High-previous actual Close),abs(Low-previous actual Close)); inherited first daily TR=High-Low. ATR20 is simple mean of 20 actual daily TR, not Wilder smoothing.
- Evaluate most recent eligible daily ATR20 against preceding 252 ATR20 values excluding the evaluated day. Require evaluated value and all 252 references finite; at least 272 actual daily OHLC records under inherited initial TR handling. Load additional history and validate coverage rather than equating 272 calendar days to trading days.
- Integer midrank numerator n=2*count(reference<value)+count(reference==value); percentile=100*n/504. Exact comparisons, no epsilon added to ties or cuts. Q index is determined by comparing 5*n against 504,1008,1512,2016 with equality entering the upper bin. Q1=[0,20), Q2=[20,40), Q3=[40,60), Q4=[60,80), Q5=[80,100].
- Preserve double-precision calculation parity; numeric tolerance for auditing cannot excuse different n/quintile. Investigate floating-point rank discrepancies against identical source data before deployment.
- Symbol/day caches are permitted only when keyed by source/timezone/spec version and as-of day. Never reuse yesterday's cached feature when a newer completed source day is available but not loaded. Rebuild when invalidated; record history synchronization and request boundaries.
- Missing or unsynchronized history, invalid OHLC/nonfinite values, duplicate timestamps, insufficient features, unknown timezone or stale cache yield status and explicit fallback reason, Risk=.90. No future filling, alternate lookback or trade exclusion to improve outcomes. Unknown broker time conversion also blocks initial deployment.
- Ordinary missing SL/pip-value/base or invalid volume remain lot/order STOP conditions; they are not cured by volatility fallback.

AppliedRiskPercent is a local candidate/attempt value, never a mutation of MQL input. Route it through the existing common GetStrategyLot path for both Buy/Sell:
RiskAmount=WeeklyBase*AppliedRiskPercent/100;
RawLot=RiskAmount/(GetStrategySLPips(cfg,JST)*GetPipValuePerLot(symbol)).
Preserve dynamic UJ12 SL and existing pip size/tick value/tick size formula. Validate all inputs as finite and positive.
Preserve raw-lot-below-min stop when AllowMinLot=false, cap before existing NormalizeLot, broker max/min/step and floor rounding. Log raw, capped and normalized lot separately. Final lot must not exceed MaxAutoLot or broker max, and must be a valid step; zero means no order. Incompatible cap/spec configuration blocks initialization, rather than silently rounding up.
Phase 5 intended specifications are min=.01/max=10/step=.01 and MaxAutoLot=1.00; confirm Dell independently. Different specs require a documented compatibility review before start, never substitute live evidence.

WeeklyBase behavior remains Monday00:00 JST week key, first legitimate sizing request snapshots Equity (existing nonpositive Equity fallback to Balance), reuses within week. It is NOT research Monday06 Balance.
Use a demo-specific GV namespace containing a short Phase5 identifier, account login, server identity/hash and week key; remain within MT5 name limits. Do not read/write/delete legacy live GV names. A diagnostic-only filtered candidate must not create WeeklyBase early: log existing base or NOT_REQUESTED. At actual sizing record creation/reuse, Equity/Balance snapshot, week key and GV name.
MT5再起動テストは対象外。VPS導入前に別途必須。This includes restart persistence and WeeklyBase/GV restoration in a future separate Deployment/Acceptance Test. No restart is required for Dell acceptance.

## 3. Dedicated EA, configuration and safety

New source/binary stem: time_entry_step9_2_4_trade_result_reconcile_27strategies_vol_r2_demo.
New source under src/EA/; binary .ex5 only after an actual successful MetaEditor compile.
Existing Step9.2.4, Step9.2.1 and live binary files must remain byte-identical. If dependency copies are required, place them under src/EA/phase5_demo/ with distinct names and record dependency hashes. Avoid macro overrides that accidentally change reconciliation call paths.

Demo guard at initialization AND before order submission: account trade mode must be DEMO and account/server must match the pre-start allowlist. Default account identity unconfigured -> cannot trade. Account switch must not authorize real trading or cross-account WeeklyBase. Phase5 acceptance requires OANDA demo evidence; runtime allowlist supplements the DEMO flag.
Required configuration: LotMode=1; WeeklyBaseUseEquity=true; RiskPercentPerTrade=.90 fallback/reference; MaxAutoLot=1.00; AllowMinLotWhenBelowMinimum=false; TestMode=false; UseTestTimes=false; UseMockJstDateTime=false; UJ12 force modes=false; GlobalAtrP70Filter=false; EventFilter=true; EventCandidateC=true; EmergencyStop=false at approved observation start; existing weekend guard enabled.
Exactly 22 disabled and other 27 enabled; preserve strategy identities/magics and all unrelated input values. Validate the complete configuration, not just a fragment applied on unsafe source defaults.
R2 allocation enabled and diagnostic input InpPrintVolR2Diagnostics=true in Phase5 SET. Existing TradeResult and WeeklyBase diagnostics remain enabled.
Name SET: step9_2_4_dell_demo_vol_r2_phase5.set. Repository template must be marked NOT_DEPLOYABLE until complete account identity, actual input parse, compile and checks are verified.
No VPS live EA/SET/branch merge or deployment. Do not overwrite existing live filenames.
Maintain prohibition on simultaneous VPS live and Dell live Algo ON. Dell demo is a separate account and permitted only after checking other Dell EAs/charts, open positions and pending orders for symbol/magic collisions. One operator-confirmed deployment operation at a time.
No automatic real-money deployment follows a PASS.

## 4. Candidate definition, diagnostics and observation schema

A distinct candidate is an enabled strategy whose normal date/time entry window is reached, keyed by RunId + strategy number + symbol + planned entry JST. Deduplicate OnTick/OnTimer repetitions; retries have AttemptId and never count as extra samples.
Keep a candidate inventory for filtered/skipped windows so unintended skips can be investigated. R2 evaluation for diagnostic-only candidates must not change guard ordering, entry eligibility or WeeklyBase snapshot timing. Missing dependent quantities use explicit NOT_REQUESTED/NOT_AVAILABLE, not invented zero.
Log once per candidate plus every sizing/order attempt and reconciliation transition. Reuse the decision context within an attempt, never recompute between lot calculation and order.
Experts logs must preserve existing TradeResult diagnostics and link via CandidateId/AttemptId plus magic/symbol/time, order/deal/position identifiers and result/retcode.

CSV/log schema, one candidate/attempt row plus linked lifecycle events:
SchemaVersion,RunId,CandidateId,AttemptId,EventType,StrategyNo,StrategyName,Magic,Symbol,
EntryCandidateJST,PlannedEntryJST,ObservedAtJST,ServerTime,ServerTimezoneRule,
VolFeatureStatus,FeatureDailyDate,AvailableAtJST,LastM1JST,HistoryStart,HistoryEnd,M1Count,DailyCount,
ReferenceStart,ReferenceEnd,ReferenceCount,ATR20,RankNumerator,Percentile,Quintile,AppliedRiskPercent,FallbackReason,
WeekKey,GVName,WeeklyBaseAction,WeeklyBase,EquitySnapshot,BalanceSnapshot,AccountCurrency,
SLPips,PipSize,TickSize,TickValue,PipValuePerLot,RiskAmount,RawLot,CappedLot,RoundedLot,FinalLot,
VolumeMin,VolumeMax,VolumeStep,MaxAutoLot,MaxAutoLotCap,MinLotStop,LotStopReason,
FilterDecision,SkipReason,OrderAttempt,OrderTicket,DealTicket,PositionId,Retcode,ReconciliationStatus,
SourceCommit,SourceSHA256,BinarySHA256,SETSHA256,MT5Build,AccountAlias,EvidencePath.
Record numeric fields with sufficient precision (17 significant digits where applicable). Preserve full raw Experts logs, source M1 exports/snapshot hashes and independent audit output. Protect account credentials; commit only alias/masked identity, keep exact allowlist manifest privately.
CSV audit schema adds IndependentATR20,IndependentRankNumerator,IndependentQuintile,IndependentRisk,IndependentLot,CheckA through CheckG,AuditStatus,DiscrepancyReason.

## 5. Observation minimum and deterministic sample selection

Hybrid duration AND count rule: at least 14 elapsed calendar days from signed start manifest; at least 10 distinct candidates with valid Primary features, spanning at least 2 different naturally occurring quintiles and at least 2 symbols; at least one actual demo entry and its subsequent exit/reconciliation lifecycle. Fallback candidates are recorded/audited but do not count toward the 10 valid-feature candidates.
At least one real Monday00 JST week transition; observe valid sizing requests on both sides, within-week WeeklyBase reuse on at least two requests and correct new-week first-request snapshot. A calendar boundary alone is insufficient.
Audit all candidates and attempts within the evaluation interval; choose the first ten qualifying candidates chronologically for the explicit minimum audit table. Do not select favorable trades. Log all later observations as well.
The first eligibility assessment is at day14; if conditions are missing, INSUFFICIENT_OBSERVATIONS and natural observation continues, with weekly evidence assessments. No maximum duration that converts missing evidence into PASS. Freeze each assessment cutoff before calculating its verdict. No TestTimes/Mock/forced regime for the natural-forward cohort.
All five quintiles/fallback/cap/minimum cases are required in predeployment tests; natural-forward requirement is at least two quintiles, not all five. Unobserved natural cases are disclosed. A later controlled demo procedure needs separate preregistration and cannot be counted retroactively as natural observations.

Frequency basis: results/edge_decay_phase2_single_stop/edge_decay_phase2_22_period_results.csv at base has E1_MINUS_22=966 trades for OOS2. docs/43_edge_decay_phase2_22_result.md defines OOS2 as 2026-01-01 through 2026-09-09 (252 calendar days): 966/36=26.83 trades per calendar week, or about 53.67 per 14 days. This is saved baseline-trade aggregation, not a raw trade-log reanalysis or prediction. The full original log is not tracked in the inspected branch. N=10 is a conservative operational minimum relative to that evidence; frequency does not guarantee feature/quintile coverage. Do not later change N based on observed PnL or inconvenient coverage.

## 6. Acceptance A–G and immutable verdict

A Quintile: independently reconstruct the SAME Dell M1 snapshots with a separately written Python reference (not calling EA implementation or its translated helper) and compare daily OHLC, ATR20, integer n, percentile, quintile and as-of boundaries. ATR absolute tolerance 1e-10 price units plus relative tolerance 1e-10; percentile absolute tolerance 1e-10 percentage points; n, dates, counts and quintile EXACT. Research feed may provide context but cannot replace same-feed parity.
B Risk: every observed valid Q uses exact fixed table; each fallback uses .90 with a valid reason. All Q1–Q5 and fallback mapping covered by predeployment tests.
C Lot: independently calculate from captured request-time base, dynamic SL and broker tick/spec values; WeeklyBase/RiskAmount tolerance absolute 1e-6 account-currency units plus relative 1e-10; raw lot absolute 1e-10 plus relative 1e-10; final volume exact in integer step units. Cap/min-stop booleans and zero-order decisions exact. No use of later tick values.
D Orders: at least one real demo entry and completed exit reconciled to account history; no duplicate entry, wrong magic/symbol, unexplained missing/extra order, lost reconciliation or unintended skip. Normal documented broker rejections are not automatically code failures, but must be correctly handled and do not substitute for the required successful lifecycle. Inventory candidate/guard decisions.
E WeeklyBase: within-week reuse and first legitimate request in new week match the frozen behavior. No restart test.
F Safety: demo/account allowlist only, all prohibited test modes OFF, 22 OFF/27 ON, no conflicting EA, no VPS live changes, dedicated artifacts and GV namespace.
G Logs: each candidate, sizing and order lifecycle is reconstructible and auditable, including fallback/stop reasons and linking identifiers.

Priority:
1. DEMO_FORWARD_FAIL if any confirmed implementation or safety violation of A–G occurs, regardless of sample count or profit.
2. DEMO_FORWARD_PASS only if deployment validations passed, observation minima met and ALL A–G evidenced PASS, with no unresolved discrepancies.
3. INSUFFICIENT_OBSERVATIONS otherwise, including absent logs/source evidence or unobserved required lifecycle/week transition. Missing evidence is not evidence of correctness.
Observed code defects cannot be deleted as exclusions. Preserve failed run; after fixing code, new source/binary/SET hashes and new start manifest define a fresh validation run under these same criteria. Changes to methodology require a separately versioned future plan, never retrospective alteration.
P&L/PF/DD cannot cause PASS/FAIL or shorten/extend observation by themselves.

## 7. Validation before deployment

Required and evidence-linked:
- Unit tests: JST daily OHLC incl Saturdays, empty days, month/year changes, historical DST, first TR, SMA20; exact ties and boundaries including 0/100.
- No-lookahead: current/future M1 mutations cannot alter prior candidate feature; midnight and LastM1+60 eligibility.
- Fallback: 271/272 daily history boundary, nonfinite/duplicate/invalid prices, unsynchronized history, stale cache and unavailable symbol.
- Risk Q1–Q5/fallback exact mapping; allocation does not filter entries.
- Lot regression: both directions; dynamic UJ12 SL; invalid base/SL/tick inputs, cap, raw below/equal/above min and step boundaries. Baseline .90 path matches existing Step9.2.4 for compatible specs.
- Config tests: 22 disabled/27 enabled, unsafe defaults rejected, wrong/real account rejected, no test/mock modes, legacy GV untouched.
- Step9.2.4 reconciliation regression covering existing success, pending, timeout, delayed deal, duplicate prevention, exit confirmation and OnTick/OnTimer interaction; compare unchanged inherited source and existing documented scenarios in docs/26. Add executable tests where absent; do not claim source text checks equal runtime regression.
- Independent same-data feature/risk/lot verifier and static source review; compiled MQL fixture runner where needed to exercise actual implementation, not only Python emulation.
- Actual MetaEditor compile: log compiler/MT5 build, zero errors, review all warnings, complete include manifest, source and binary SHA256. Compile unavailable => NOT_RUN, deployment blocked. No fabricated .ex5 or compile success.
- Document test commands, versions, counts/failures and limitations. Confirm remote Plan SHA preceded all EA edits; verify inherited/live files unchanged.

## 8. Planned files and start gate

docs/63_volatility_phase5_plan.md (this immutable document)
docs/64_volatility_phase5_dell_demo_deployment_checklist.md
docs/65_volatility_phase5_acceptance_checklist.md
docs/66_volatility_phase5_result.md (only actual observations, not hypothetical PASS)
src/EA/time_entry_step9_2_4_trade_result_reconcile_27strategies_vol_r2_demo.mq5
src/EA/phase5_demo/ (dedicated include/fixture files if needed)
configs/phase5/step9_2_4_dell_demo_vol_r2_phase5.set
src/research/volatility_phase5_audit.py
tests/test_volatility_phase5.py and dedicated MQL validation harness
research_inputs/phase5/forward_observation_schema.csv
research_inputs/phase5/start_manifest.template.json
results/volatility_phase5/ (validation, masked manifests, observation/audit records)
Optional notebooks/volatility_phase5_audit.ipynb; raw account logs remain private with hashes and evidence references.

Before first forward order, freeze a separate actual start manifest: verified Plan SHA, implementation remote SHA, source/include hashes, compiled binary name/hash/compiler build, complete SET name/hash/parsed values, MT5 build, Dell/OANDA demo account/server/currency and mode evidence, seven symbol specs, timezone evidence, non-overlap check, week/GV namespace, validation report, start JST and operator confirmation. User-confirmed versus independently parsed evidence must be labeled.
Live reference only: step9_2_4_live_vps_weekly090_1500k_minus22_20260914.set; time_entry_step9_2_4_trade_result_reconcile_28strategies.ex5; MT5 build6180; inputs/specs in user handoff. None proves Dell configuration. Dell build/account/binary/SET/current funds/start date remain PENDING until measured.
Sequence: source inspection -> plan-only commit -> remote ref/parent/diff/content verification -> first Work report with Plan SHA and criteria -> dedicated implementation/tests/artifacts -> actual compile/start gates -> one Dell operation -> user confirmation -> next operation -> forward observation. Do not instruct or perform Dell operations during the first report.
