# Volatility Environment Phase 4 — R2 Deployment Validation
Status: PREREGISTERED BEFORE PHASE 4 IMPLEMENTATION OR MONEY RESULTS.
Branch: research/volatility-environment-phase4-deployment-validation
Base: Phase 3 result 144f7be6a97017cb7292c5ed9d9e8f4ef845af63.
Docs 61 Plan / 62 Result. This plan is immutable after remote SHA/content verification.

## Scope and fixed inputs
Independent retrospective deployment study, not fresh OOS or further optimization.
No EA/VPS/SET/live source/config changes, no live adoption, no new R3 or rescue allocation.
Baseline 28 strategies / 16298 trades; SHA256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359.
Daily Stop none; ATR filter OFF; Event Candidate C; UJ12 advanced gotobi and EJ1 overlap fixes inherited.
Generate the 27-strategy scenario by removing only exact Strategy 22_GA_C_2 (StrategyNo 22) from original rows.
Never regenerate or overwrite the trade log. Validate remaining identities, row identity and count; report removed count and scenario hash.
Only R0_FIXED_090 (.90/.90/.90/.90/.90%) and R2_MODERATE (.50/.70/.90/1.10/1.30%).
INSUFFICIENT_VOL_HISTORY uses .90% for both. No exclusions for missing features.

## Frozen features
Use unchanged Phase 1/2/3 sources at base SHA and Phase 2 manifest hashes.
Primary JST daily ATR20 = simple mean of 20 TR; robustness 20 log-return sample std ddof=1 times sqrt252.
Actual M1 bars converted Europe/Helsinki to JST; daily actual-bar OHLC, including Saturday when present, no filling.
Daily d available following calendar midnight, and LastM1+1 minute must be <= EntryTime.
Evaluation daily value compared with previous 252 completed trading days excluding evaluation day, all finite, exact midrank.
Q1=[0,20), Q2=[20,40), Q3=[40,60), Q4=[60,80), Q5=[80,100]; inherit integer numerator mapping.
No ATR, percentile cuts, window, or history-policy changes.
Rehash 56 original M1 files; regenerate feature assignments using frozen code and regress against Phase 2/3.
Full Phase 2 assignment file, if supplied, must match its published hash; otherwise inherited complete strategy/period/quintile regression plus saved audit applies.
Missing baseline/M1 => NOT_RUN_INPUT_MISSING; no inference of performance from aggregate Phase 3 results.

## A — Historical Deployment Validation
THEORETICAL_UNCAPPED; initial 500000 JPY. Reuse Money v1.1 and Phase 3 Decimal40 simulator.
JST Monday06:00 entry-week base Balance fixed within week, next week compounded from completed PnL.
PnL = WeeklyBase * RiskPct/100 * Pips/SL. No lot rounding or invented pip conversion.
Same close ordering, initial peak, closed-balance DD, day-start Balance / week-start Balance denominators as docs/59.
ALL [2015-01-01,2026-09-10), continuously without resetting capital or peak.
Independent 500000 resets: Historical [2015-01-01,2022-01-01), RecentA [2022-01-01,2024-01-01),
RecentB [2024-01-01,2026-01-01), Monitor2026 [2026-01-01,2026-09-10).
Retain pre-period feature history. Stop on cross-week/reset boundaries, invalid SL/Pips/R, or insolvency.
Execute both methods, both candidates, all five windows (20 metric rows).
Primary metrics: FinalCapital/NetProfitJPY first, MaxDDPct, WorstDayPct, WorstWeekPct, MoneyRoMD,
actual mean nominal risk, reset/robustness capital differences, 27-strategy trades.
28-to-27 table may contextualize Phase 3 but selection is exclusively within 27 strategies.

## B — Live Deployment Feasibility Audit: evidence already inspected
Source under src/EA/time_entry_step9_2_4_trade_result_reconcile_28strategies.mq5,
including inherited time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5.
docs/52 confirms separate live stop decision; user reports effective 2026-09-14 week and risk .90%, 1500000 JPY.
Current step9_2_4_live_vps_weekly090_1500k... SET is NOT PRESENT in inspected repo.
No tracked .set file or complete current timestamped symbol-spec snapshot found.
Do not substitute defaults or old diagnostic settings for current live values.

Source findings:
- Step9.2.4 WeekStartDateKey/GetWeeklyBaseAmount (lines 211-321): Monday00:00 JST calendar date key;
  first call creates terminal GlobalVariable using current selected Equity/Balance; subsequent calls reuse it.
  This is NOT the research A Monday06:00 Balance convention. No exact week-start equity snapshot can be inferred.
- Inherited GetCurrentBaseAmount selects Equity when InpWeeklyBaseUseEquity=true, Balance otherwise,
  and Step9.2.4 falls back to Balance for nonpositive base.
- LotMode 0 fixed; 1 weekly compound. Risk amount=WeeklyBase*InpRiskPercentPerTrade/100.
- RawLot=risk amount/(GetStrategySLPips * pip value per lot);
  pip value=tick value*(pip size/tick size), obtained at runtime.
- RawLot<symbol min with AllowMinLot=false => LOT STOP. Positive MaxAutoLot caps before NormalizeLot.
- NormalizeLot clamps min/max, floors to step, then NormalizeDouble(...,2).
  Cap below min may be raised back to min; sub-.01 step may be altered by two-decimal normalization.
  These must be checked against actual specs, not asserted safe.
- Old docs/26 diagnostic values LotMode=1, Equity=true, MaxAutoLot=.10, AllowMinLot=false
  are historical evidence ONLY. Current values remain UNVERIFIED_CURRENT_SET.
- .90% current risk is user-stated, not corroborated by a current SET.
- GlobalVariable name includes week key but not account/build; reuse/collision and restart behavior need demo tests.

Audit all 27 strategies' common lot path and strategy/date-dependent SL; preserve existing strategy eligibility.
Proposed future implementation uses a per-entry local applied-risk value in common lot calculation;
MQL input itself is not mutated. Log VolRegime, VolPercentile, AppliedRiskPercent, FallbackReason,
feature as-of/source timestamps, strategy/symbol, weekly key/base, raw/rounded/capped lot.
No production implementation in Phase 4.
Broker native D1/iATR cannot be assumed equivalent to JST daily SMA20 TR.
Future EA must reconstruct completed JST OHLC from M1 with exact time conversion and source availability.
For each of USDJPY/EURJPY/GBPJPY/AUDJPY/AUDUSD/EURAUD/GBPAUD maintain 253 finite feature days:
ATR20 requires at least 272 actual daily OHLC observations under inherited first-TR handling;
RV20 requires 273 daily closes. Provision extra history; count valid feature values rather than calendar days.
Verify exact requirement against frozen source before declaring audit pass.
Restart/warm-up: rebuild or validate versioned cache; never use partial/current/future days or stale cache.
Unavailable feature => .90 fallback with reason, retaining ordinary invalid lot/SL/pip-value/order guards.
Full parity/restart/order behavior belongs to separate Phase 5, not claimed tested here.
Current SET/spec absence means audit UNDETERMINED, not pass by absence of detected problems.

## Broker constraints
Historical pip values, historical symbol specs and true weekly floating Equity are not present.
Historical constrained simulation: NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS.
Do not describe A as broker-constrained or live-equivalent.
Optional static 1500000-JPY 27x5 lot table only with dated current complete symbol specs and confirmed cap/min policy.
Use strategy/date-specific SL and label representative/current static feasibility, never historical performance.
If specs absent, omit current_lot_feasibility.csv and report NOT_RUN_MISSING_CURRENT_SYMBOL_SPECS.

## Immutable decision (all unrounded)
DEMO_FORWARD_CANDIDATE requires ALL:
1 Primary ALL FinalCapital > R0.
2 Primary reset FinalCapital >= R0 in >=3/4 periods.
3 Primary RecentB OR Monitor2026 FinalCapital > R0.
4 Primary ALL MaxDDPct <= R0*1.25.
5 Primary ALL WorstDayPct > -20 exactly; equality or below fails.
  This limit is chosen AFTER observing Phase 3 R2 -15.6%, as an operational loss-risk guard,
  not an optimized or independent statistical threshold. Never change after Phase 4 results.
6 Robustness ALL FinalCapital difference >=0.
7 Audit has no fatal implementation incompatibility, with sufficient evidence of current SET/specs.
8 Validation and independent verification pass.
Known failing condition => NOT_CANDIDATE; missing/invalid evidence => UNDETERMINED, never PASS.
No failure rescue via allocation/cuts/strategies/windows/threshold changes.
Passing is demo candidacy only, never live adoption.

## Validation
Baseline byte hash and identities/count; exact 22 exclusion and no other mutation.
Frozen-source/M1 hashes; Phase 2/3 assignment regression and no-lookahead/future mutation tests.
R0/R2 mapping all quintiles/history fallback; reject unregistered candidates.
Monday05:59/06 rollover, fixed within-week base, next-week compound, period reset, boundary/insolvency guards.
Independent NumPy/pandas vectorized week-product/cumsum verifies every trade base/PnL/balance/DD and 20 metrics;
no production risk/week/money helpers in verifier. rtol=1e-10; money atol=1e-6, ratio/pct atol=1e-10.
Independent decision signs and safety-limit equality tests.
Representative manual mapping: each method/quintile incl fallback, first two weeks, variable SL.
Static lot mapping manual audit only if real specs provided.
Repeat deterministic CSV byte regeneration and execute notebook cells locally with path substitution;
Drive initially OFF; do not claim Colab runtime execution if only local.
Synthetic tests alone do not satisfy real-data validation.
Research source changes only; verify no inherited EA/SET/live changes.

## Sequence and output
Review -> plan-only GitHub commit -> remote ref SHA/content/diff verification -> implementation.
Then implementation commit, A/B execution, independent tests, result/CSV/notebook commit and remote verification.
results/volatility_phase4/volatility_phase4_27strategy_money_summary.csv,
volatility_phase4_period_reset_summary.csv, volatility_phase4_robustness_summary.csv,
volatility_phase4_deployment_feasibility.csv, volatility_phase4_decision.csv,
volatility_phase4_run_record.csv; optional current lot table only when inputs exist.
Allow verification/audit/input manifests; full trade logs local or /content only.
Notebook notebooks/volatility_phase4.ipynb: primary, resets, robustness, audit; /content saving and optional Drive cell OFF.
If inputs remain missing, save explicit pending result and missing-input statuses without fabricated metric rows.
Record Plan/Implementation SHA, input/output hashes, environment and incomplete checks; result SHA externally avoids self-reference.

## Separate Phase 5
Only on Phase 4 passage consider Dell OANDA demo forward as separate research/operational trial.
Keep live VPS 27 strategies unchanged. Test implementation correctness, regimes, applied risk, rounding/logs,
restart/warm-up and actual demo orders. Before starting freeze period, acceptance rules, EA build and SET separately.
