# Volatility Environment Phase 3 — Risk Allocation Economic Value
Status: PREREGISTERED BEFORE IMPLEMENTATION AND MONEY RESULTS.
Branch: research/volatility-environment-phase3-risk-allocation
Base / Phase 2 result: 0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc.
Docs 59 Plan / 60 Result. Plan is immutable after remote verification.

## Research boundary
Retrospective economic-impact analysis on already viewed 2015–2026 data, NOT fresh OOS. Evaluate whether the observed Volatility–Edge relationship increases final capital and risk efficiency under simple fixed allocations. No optimization. No live adoption or EA/VPS/SET/live source/configuration changes. Old ATR70 filter research is separate. Keep all 28 baseline strategies including 22_GA_C_2; do not revise the separate live stop decision effective 2026-09-14 week.
Baseline: 16,298 trades, SHA256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359. Never regenerate baseline.
Phase 1 BOTH_SUPPORTED, positive LOW AvgR. Phase 2 BOTH_SUPPORTED.
Primary pooled Q1..Q5 AvgR: .044682/.078276/.095623/.103454/.143594.
Robustness: .046312/.077083/.094603/.108096/.128460.

## Fixed candidates (percent, Q1/Q2/Q3/Q4/Q5)
- R0_FIXED_090: .90/.90/.90/.90/.90 (formal comparator)
- R1_MILD: .70/.80/.90/1.00/1.10
- R2_MODERATE: .50/.70/.90/1.10/1.30
- F1_Q1_OFF: skip/.90/.90/.90/.90 (filter control, not priority hypothesis)
All methods/candidates: INSUFFICIENT_VOL_HISTORY trades use .90%; no exclusion.
R1/R2 unweighted quintile mean=.90%; actual trade-weighted mean need not equal .90%.
Report nominal risk mean across ALL baseline trades (F1 skipped rows contribute zero only to this denominator), delta vs R0, plus mean across executed trades.
No risk-budget normalization in this study. No extra candidates, thresholds, strategies, base risks, intermediate allocations, or result-driven changes.

## Frozen feature and inputs
Reuse unchanged Phase 1/2 source at base SHA: volatility_phase1.py, frozen_inputs.json, volatility_phase2.py.
Primary D1 ATR20 = SMA20 of TR. Robustness RV20 = sample std(ddof=1) of 20 log returns * sqrt252.
MT5 Europe/Helsinki -> JST, actual-bar daily OHLC including Saturday if present, no filling.
Daily d available next calendar midnight; require AvailableAt<=Entry and LastM1+1 minute<=Entry.
Reference previous252 completed trading days excluding evaluation day; all 252 plus evaluation finite; exact midrank.
Quintiles Q1=[0,20), Q2=[20,40), Q3=[40,60), Q4=[60,80), Q5=[80,100], using Phase 2 integer numerator mapping unchanged.
Rehash all 56 M1 inputs against Phase 2 manifest and regenerate features/assignments from source. Compare all full assignments against saved Phase 2 output when available and its published run-record hash; otherwise compare complete quintile counts/TotalR/AvgR and saved audit. Missing baseline/M1 => NOT_RUN_INPUT_MISSING, no substitute estimates.
Primary determines formal decision; apply identical allocations to robustness with no tuning.

## Money specification and priorities
Reuse Money Management v1.1 (src/portfolio_money_management_sim_v1_1.py) and clarified settlement/DD definitions in docs/48_edge_decay_phase2_money_simulation_plan.md and src/research/edge_decay_phase2_money_simulation.py.
Initial 500,000 JPY. THEORETICAL_UNCAPPED, no lot min/max/step/MaxAutoLot or invented conversion rates.
Week = JST Monday06:00; before that belongs previous week. First weekly base=500000. WeeklyBase fixed for all entries in week; trade Risk varies by entry quintile. PnL=WeeklyBase*RiskPct/100*Pips/SL. Next weekly base adds completed prior-week PnL. Empty weeks unchanged. No intratrade compounding, floating PnL, deposits, interest or additional costs outside supplied Pips. Internal amounts unrounded.
Require positive finite SL and finite Pips, entry<=close<entry-week-start+7days; stop on boundary violation. Stop on trades crossing any defined reset-period boundary. Nonpositive weekly base or closed balance => insolvency, candidate ineligible; never conceal it or switch simulation rules.
R=Pips/SL; validate saved R difference <=1e-8, record maximum, never overwrite baseline.
F1 skip at scenario layer before money/curve/trade-count construction; no fictitious zero-PnL execution row.
Settlement order CloseTime, EntryTime, StrategyNo, original row ID. Initial capital included in DD peak; ALL peak never reset. DD is closed-balance drawdown, not floating equity DD.
MaxDDPct=max((peak-balance)/peak*100); MaxDDJPY=max(peak-balance).
WorstDayPct=min(JST close-day PnL/day-start Balance*100).
WorstWeekPct=min(Monday06 close-week PnL/week-start Balance*100).
Worst metrics use executed days/weeks as existing money study; empty full simulation returns zero.
MoneyRoMD=NetProfitJPY/MaxDDJPY; no DD => NA.
Historical broker inputs absent => NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS. No constrained simulation fabrication.

## Periods
ALL: EntryTime >=2015-01-01 and <2026-09-10; continuous from 500000 with no capital/peak resets.
Separate supplementary simulations each start 500000 and fresh peak:
Historical [2015-01-01,2022-01-01)
RecentA [2022-01-01,2024-01-01)
RecentB [2024-01-01,2026-01-01)
Monitor2026 [2026-01-01,2026-09-10).
First partial week uses 500000. Features retain pre-period history, never restart feature windows. No additional windows.

## Immutable decision
All comparisons use unrounded values.
Economic Value Candidate requires Primary:
(a) ALL FinalCapital > R0
(b) >=R0 in at least 3/4 reset periods
(c) >R0 in at least one of RecentB or Monitor2026
(d) ALL MaxDDPct <=1.25*R0 MaxDDPct
(e) validation and independent verification PASS.
Report each condition separately. Missing/invalid evidence => UNDETERMINED, never PASS.
DD improvements cannot rescue profit reduction.
Robustness-consistent iff robustness ALL FinalCapital delta >=0; negative is caution and does not alter Primary rule.
Evaluate F1 identically but label filter control and do not prioritize over passing R1/R2. Among R1/R2 report final-capital ordering only; never create compromise allocation.
Passing candidates are research candidates only. Next implementation-specification/future-validation stage requires a separate decision; no live adoption here.

## Validation and reproducibility
Baseline hash/count/identity; frozen source hashes; all M1 hashes; Phase 2 assignment/count/AvgR reproduction; no lookahead plus inherited future-data mutation tests.
Weekly rollover 05:59/06:00, weekly base fixed/next-week compounded, different within-week quintiles, variable SL, initial loss DD, scenario mapping all quintiles/INS, F1 true skips, period reset, cross-week/cross-period failure, insolvency, decision equality boundaries.
Independent NumPy/pandas calculation from trade rows distinct from main Decimal money loop, verify each trade PnL/base/balance/DD and all 40 method/scenario/period metric rows. Float tolerance rtol=1e-10, atol=1e-6 yen or 1e-10 percentage/ratio; candidate decisions use main unrounded values, flag sign disagreement.
Representative audit: first executed trade per method/scenario/quintile (including INS), first two weeks and first skipped F1 rows; show base/risk/Pips/SL/PnL and independent agreement.
Repeat saved CSV regeneration byte comparison (deterministic CSVs); run-record timestamp excluded from byte comparison but metadata/metrics checked. Notebook displays saved results and regeneration cells use same fixed implementation SHA, CSV bytes/hashes verified.

## Sequence and outputs
1 source/spec review -> 2 Plan-only GitHub commit, re-fetch remote SHA/content and diff -> 3 implementation/tests/notebook, implementation commit -> 4 tests and real calculation/independent check -> 5 results commit and remote verification.
results/volatility_phase3/volatility_phase3_{money_summary,period_reset_summary,risk_allocation_summary,robustness_summary,decision,run_record}.csv; additional verification/manual_audit/input_manifest/constraint_status/hash manifest allowed.
Full trade/weekly/daily assignments only local or /content, not GitHub.
notebooks/volatility_phase3.ipynb: R0/R1/R2/F1 ALL, reset comparisons, Primary/Robustness; CSV output /content, Drive cell initially OFF. Docs/60 result includes complete summary.
Record branch, plan/implementation SHA, input/output hashes, environment, checks, baseline preserved, live unchanged, retrospective limitation. Result SHA reported externally to avoid self-reference.
