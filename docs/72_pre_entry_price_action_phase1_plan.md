# Pre-Entry Price Action Phase 1 — preregistered plan
Status: fixed before implementation or feature/result computation. Date: 2026-09-20.
Branch: research/pre-entry-price-action-phase1.
Base: research/trend-strength-phase1 at 896ba7888a2ef6473d8a56db426d6312cf990219.
New documents: 72 plan / 73 result. Existing Trend artifacts are immutable.

## Purpose and boundaries
Diagnose whether pre-entry location within the recent price range predicts Avg R/Trade for the fixed strategy universe. Direction is not predetermined: positive WITH_SIDE minus AGAINST_SIDE suggests momentum dependence; negative suggests pullback/mean-reversion dependence. An unclear contrast is not support, and does not prove absence of dependence.
Phase 1 is diagnostic only. No entry filter, Entry ON/OFF, risk adjustment, ATR/ADX/ER/return/candle/MA feature additions, strategy-specific thresholds/windows, Volatility crossing or R2 integration. Do not change Volatility Phase 5 Dell Demo Forward, VPS live, EA, SET, or existing Trend artifacts.
Do not change 60m to 30/90/120m, 180m to another robustness window, bucket boundaries, groups, or periods after results.

## Fixed inputs and existing implementation inspection
28 strategies, 16,298 trades. Baseline SHA-256:
cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
Daily Stop OFF / ATR OFF / Event Candidate C; UJ12 Gotobi and EJ1 event overlap fixes already applied. Never regenerate the Baseline Trade Log. Include stopped live strategy 22_GA_C_2 for comparability.
Freeze all StrategyNo/Strategy/Pair/Long identities, SYMBOL_TO_PAIR, MANIFEST_NAMES and all 56 M1_SHA256 entries from src/research/trend_strength_phase1_frozen_inputs.json at the base commit. Copy to a dedicated frozen-input file without editing the original.
UJ=USDJPY, EJ=EURJPY, GJ=GBPJPY, AJ=AUDJPY, AU=AUDUSD, EA=EURAUD, GA=GBPAUD.
Existing src/research/trend_strength_phase1.py and volatility_phase1.py provide audited load_baseline/load_m1/to_jst and calendar-week resampling conventions. src/filter_test_v2_range_atr.py uses pre-entry range endpoints, but no helper implementing this study's exact windows and coverage was found. Use the audited loaders unchanged; write a dedicated assignment function.
MT5 timestamp denotes M1 OPEN time. Convert Europe/Helsinki (ambiguous=infer, nonexistent=shift_forward) to Asia/Tokyo then timezone-naive JST, exactly as existing loaders.
Exactly one file per frozen filename; verify byte SHA-256 before loading. Reject duplicate timestamps, non-minute-aligned bars or entries, invalid identities/period, nonfinite/nonpositive prices, invalid OHLC. No interpolation, forward/back fill, duplicate dropping, proxy data, or baseline regeneration.
Baseline known prior location: MyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/daily_stop_baseline_trades.csv. Raw Baseline/M1 are not present in the checked repository.
If input access is missing, record NOT_RUN_INPUT_MISSING, leave numerical conclusions unavailable, and do not present missing inputs as NOT_SUPPORTED.

## Features and exact availability
For each entry E and W=60 (primary) or W=180 (robustness), use existing M1 bars with open timestamps t satisfying E-W minutes <= t < E and t+1 minute <= E.
All entries and bars must be minute-aligned. Never use any Open/High/Low/Close from the Entry bar, later bars, or a partial bar.
H=max(window.High), L=min(window.Low), Cpre=Close of the last available completed M1 in this window.
Long: PDRP=(Cpre-L)/(H-L). Short: PDRP=(H-Cpre)/(H-L).
W=60 requires at least 48 unique bars; W=180 requires at least 144.
The last bar OPEN timestamp must satisfy E-5min <= t_last <= E-1min (inclusive); its close is completed at t_last+1min. This explicitly fixes the interpretation of "within the previous five minutes".
Insufficient count or stale/missing last bar => INSUFFICIENT_PREENTRY_HISTORY, with reason/count/freshness recorded.
After coverage passes, H==L => FLAT_PREENTRY_WINDOW. Exclude both reasons from formal bucket statistics but retain every trade in assignments and coverage. Coverage takes precedence over flat. Record raw H/L/C where available.
Finite nonflat PDRP must be in [0,1], otherwise fail; never silently clip or force 0.5.
AGAINST_SIDE: 0 <= x < 1/3.
MIDDLE: 1/3 <= x < 2/3.
WITH_SIDE: 2/3 <= x <= 1.
Compute float64 x without prior rounding; compare with float64 1/3 and 2/3. Exact boundary equality belongs to the upper bucket. Test boundaries with exact supplied feature values and synthetic prices.
Weekends, Monday opens, missing bars and closures count as unavailable expected minutes, not compressed market time. Never widen the window. Do not restrict one method to the other method's coverage.

## Rationale
A dimensionless 0–1 position is comparable across currency price scales/pips. No ATR normalization directly mixes the already observed volatility effect into feature construction. Long and Short share one directional scale. EA implementation is possible from prior M1 High/Low/Close. Restrict the question to range position; no multiple-feature search. This does not establish independence from volatility.

## Periods, metrics and groups
ALL: 2015-01-01 <= EntryTime < 2026-09-10.
Historical: [2015-01-01,2022-01-01).
Recent A: [2022-01-01,2024-01-01).
Recent B: [2024-01-01,2026-01-01).
2026 Monitor: [2026-01-01,2026-09-10).
2022–2026 has already been viewed and is NOT a pristine holdout. No additional period search.
Strategy × bucket and pooled groups: Trades, TotalR, AvgR (primary metric), PF, WinRate%, AvgWinR, AvgLossR (negative), LOW_SAMPLE.
Win R>0; loss R<0; zero R is included in denominator. PF=sum positive R / abs(sum negative R); no losses with positive profit => inf, both zero => NaN. Empty: Trades=0, TotalR=0, other metrics NaN.
Contrast = WITH_SIDE AvgR - AGAINST_SIDE AvgR; always show all three buckets.
Cell n<20 => LOW_SAMPLE=true but still displayed. Individual sign comparisons require both outer buckets >=20. MIDDLE need not have 20.
Groups fixed: (1) all-28 trade-weighted pooled Portfolio; (2) strategy-equal-weighted; (3) Long; (4) Short; (5) JPY: USDJPY/EURJPY/GBPJPY/AUDJPY; (6) AUD non-JPY: AUDUSD/EURAUD/GBPAUD.
Show pooled and equal-weighted AvgR/contrast for Portfolio and each subgroup. Equal-weighted uses only that period/method/group's eligible strategies, with the same eligible IDs in each bucket. Empty MIDDLE for any eligible strategy => equal-weighted MIDDLE NaN; no changing the eligible set. PF and other ratio metrics are not averaged across strategies; show them only for actual pooled trades.
Sign agreement: strict majority of eligible strategies with same nonzero sign as pooled. Exact zero is disagreement. Never select a group after seeing results.

## CI and inference
Use calendar-week cluster bootstrap, 5,000 replicates, NumPy default_rng seed=20260913. JST EntryTime assigns Monday-start calendar weeks. ALL uses every week from 2014-12-29 through 2026-09-07, including empty weeks. Each draw samples the original number of weeks with replacement; one shared draw matrix across all strategies/symbols/groups/methods preserves contemporaneous dependence.
Within each draw recompute outer-bucket total R/count and WITH-AGAINST difference. Replicate with either count zero is invalid. Require >=4,750 valid replicates, otherwise CI unavailable. 95% CI = 2.5/97.5 percentiles, linear interpolation.
ALL strategy and pooled-group contrasts must have CIs. Also compute ALL strategy-equal-weighted contrast CI from replicate per-strategy contrasts over the original fixed eligible set; invalidate a replicate if any eligible strategy has an empty outer cell. Do not inherit pooled CI for equal-weighted.
Period contrasts are descriptive: provide bootstrap CIs using that period's complete Monday-start week grid (including boundary partial weeks), same seed/repetition rules and shared draws within period. Eligibility remains fixed from original sample within period.
CI coverage is unadjusted for multiple comparisons. Individual/group/period findings are supplementary; only ALL Portfolio is formal. Weekly clustering cannot fully handle multiweek dependence/nonstationarity and does not establish causal or economic value.

## Frozen formal support and overall verdict
For each method, support requires ALL of:
A. ALL Portfolio pooled WITH-AGAINST 95% CI strictly excludes zero.
B. Eligible strategy-equal-weighted contrast has the same nonzero sign as pooled.
C. More than half of eligible strategies have the same sign as pooled.
Primary passing => PRIMARY_SUPPORTED; robustness evaluated by identical criteria.
Unavailable CI, zero eligible strategies, missing outer bucket or nonfinite contrast is not support; record its reason separately.
Overall:
* Primary supported + robustness supported + same direction => BOTH_SUPPORTED.
* Primary supported + robustness unsupported + same nonzero pooled direction => PRIMARY_SUPPORTED_ROBUSTNESS_ALIGNED.
* Primary supported + robustness opposite pooled direction (regardless of robustness support) => UNSTABLE.
* Primary unsupported => NOT_SUPPORTED; robustness-only support is auxiliary.
* Primary supported with robustness exactly zero or unavailable => UNSTABLE, reason ROBUSTNESS_UNALIGNED_OR_UNAVAILABLE; not a Phase 2 candidate.
A dataset never run/invalid is NOT_RUN_INPUT_MISSING/FAILED_VALIDATION, not a statistical verdict.
Eligible individual strategy whose CI excludes zero may be called a descriptive clear contrast; no selection/filtering from this result.

## Subsequent research and economic value
Only BOTH_SUPPORTED or PRIMARY_SUPPORTED_ROBUSTNESS_ALIGNED makes Phase 2 a candidate, not authorization to run it now.
Phase 2 would preregister fixed fifths [0,.2),[.2,.4),[.4,.6),[.6,.8),[.8,1] for PDRP60 shape and check incremental information after controlling/matching volatility. Do not do either in Phase 1.
Trend Strength Phase 1 ended NOT_SUPPORTED. Volatility R2 is the current leading baseline. If Pre-Entry is supported through later stages, Economic Value compares Volatility R2 versus Volatility R2 + Pre-Entry, not fixed 0.9%. The user's objective includes increasing Total Profit; lower DD alone with worse profit is not an adoption rationale.

## Validation and publication gates
1. Inspect existing loaders/timezones/helpers (done above).
2. Publish this Plan alone on the new branch; record its commit and independently read remote branch SHA. No new research code before that check.
3. Implement dedicated module/frozen input, tests, independent verifier and notebook. Publish implementation commit and confirm remote SHA before real-data outcome computation.
4. Validate Baseline hash, 16,298 rows, all 28 identities/mappings, all 56 M1 hashes. Unit tests: no lookahead by changing Entry/future bars, truncation invariance, Long/Short inversion, exact 1/3 and 2/3 and endpoints, 60/180 exact boundaries, coverage 47/48 and 143/144, freshness 5/6min, flat/insufficient precedence, missing bars, weekend/Monday and overnight, timezone winter/summer. No thresholds/windows chosen from outcomes.
5. Independently reconstruct feature assignments for ALL trades via timestamp masks/direct max/min/last close, separately from the main indexed-window implementation.
6. Representative manual audit rows selected without R: earliest trade per symbol/direction, earliest Monday per symbol/direction, earliest window crossing JST midnight per symbol/direction, earliest insufficient/flat where present, earliest trade per strategy/bucket/method. Deduplicate deterministically; keep explicit audit values/count/endpoints.
7. Independent aggregation from assignments for all published cells, contrasts, eligible sets, signs and support; independent CI spot checks for both Portfolio methods, all pooled groups and strategies 1/14/28, rebuilding weekly sums/counts and resampling from the fixed seed. Check equal-weighted separately.
8. Save CSV/notebook/Result. Notebook body displays Portfolio primary/robustness, equal-weighted, fixed groups, all 28 strategies and major individual findings. Notebook CSV destination /content, Drive save default OFF.
Required CSV names: pre_entry_phase1_strategy_primary.csv, pre_entry_phase1_strategy_robustness.csv, pre_entry_phase1_group_summary.csv, pre_entry_phase1_period_summary.csv, pre_entry_phase1_coverage.csv, pre_entry_phase1_run_record.csv.
Additional decision, verification, input_manifest, manual_audit, assignment_audit_light, publication_manifest allowed. Full trade assignments stay local/Colab; GitHub receives lightweight audits and manifest hashes/sizes/publication distinction.
Run record: Plan/implementation SHA, source/input/output hashes, software versions, coverage/insufficient/flat counts, validation, BaselineRecalculated=false, LiveChanged=false. Do not hardcode successful tests/audits.
Final report includes Branch, Plan/implementation/result SHA, both definitions, coverage reasons, three Portfolio AvgRs, contrasts/CIs, equal-weighted differences, sign agreement counts, fixed groups, individual findings, overall verdict, Phase 2 eligibility and complete created files. Explicitly confirm no Phase5/EA/VPS/SET/live/Trend modifications.
