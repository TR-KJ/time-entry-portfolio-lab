# B7 U10-P Implementation Only

Status: FROZEN_READY_FOR_CHAT_REVIEW. U10PExecutionAuthorized=false; U10PExecuted=false. Work Implementation Freeze → Chat review → separately approved Colab formal run. No formal40 Candidate performance was generated, including individual trial candidates. Candidate Freeze, Validation, Monitor, Money, Portfolio and Global R2 remain unexecuted.

## Immutable inputs and scope

U10 Result Freeze:488553634c3923f5ef561a7db777d1b0b2ff5796. U10 Producer:ca3affff0c210e4a4cda9aae98ca8a9928db9489. Original Conditions:5dbac7af2d41aa912308868e6ad1a6dbf7cdd107. U09 Supplemental:1466a2c3e8b3d523233c45d665a6cac21e974393. U10 Supplemental:e34099b9c807df1f145f96ca92c2443fe552fa36; prespec SHA2565dc8c39e2e1bb2ab85c893e8769d601e4cb8d1a295e56bf543c6a6643d92130b.

research_inputs/b7/u10p_selected40_input.json SHA2567bce58b58102be11d8fe2debe4212b47a52cc685d10b044a9f7663e5b0bad11f. Full object/file hashes plus independent prior-input/source-checkpoint checks bind every field, order, lineage, E2 metrics/event set, candidate/object/checkpoint/Producer hashes and E2 stream hash. Count40 unique PASS_U10 only, NoReplacement=true, U10PPerformanceEvaluated=false. Pair counts USDJPY1/EURJPY8/GBPJPY8/AUDJPY4/AUDUSD0/EURAUD7/GBPAUD5/EURUSD5/GBPUSD2. No DROP14 resurrection or rank replacement.

Event calendar SHA2567a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb, source commit173be2a114dad6bd183a0a1515581528850f0850. Frozen full_research_prespec.U10-P copied into config/input unchanged. Pair/direction/Entry/Exit/holding/SL/TP/Weekday/DOM/Month/CalendarFreeze/U09 result/E2/calendar/spread/pip/execution remain fixed. Discovery rows only [2020-01-01,2024-01-01) JST; later price rows rejected.

## P0 barrier before diagnostics

Regenerate exact U10 formal E2 survivors with existing execution conventions and frozen calendar. Filter planned Entry–planned TimeExit inclusive before executing surviving trades; no E0/E1 mode evaluation. Reuse unchanged optimized U06 Engine, independently reconstruct scalar reference with U06 scalar executor. Preserve original TradeID and fixed keys, raw/adjusted prices, SL/TP, planned/actual times and missing/fallback fields. Sort CloseTime→EntryTime→FixedKey. Before *any* MFE/MAE/protection evaluation, object_hash(P0 original trade stream) must equal E2TradeStreamSHA256 and summarize(P0) must equal the entire DiscoveryE2Metrics object, including annual/PF state/DD/median/worst-year fields. Either mismatch hard-stops with no protection output. Stream equality also binds original TradeID sequence. Persist barrier hash, metrics equality and P0 ID-sequence hash.

## Diagnostics and protection execution

EntryPrice is spread-adjusted formal entry; High/Low remain raw. LONG MFE=max(0,max(High-EntryPrice)/PipSize); MAE=max(0,max(EntryPrice-Low)/PipSize). SHORT MFE=max(0,max(EntryPrice-Low)/PipSize); MAE=max(0,max(High-EntryPrice)/PipSize). Each mode includes entry bar through its actual closing bar, including full raw High/Low of closing bar as prescribed; later bars excluded. No within-bar order inference, epsilon, interpolation or rounding. GivebackPips=MFEpips-FinalPips (can exceed MFE when final is negative).1R=Candidate FormalSL pips. Reach>=0.25/0.50/0.75/1.00R inclusive. WinnerToLoser iff MFE>=0.50R AND FinalPips<0; zero final is not WTL. WTL fraction=count/Trades, null for empty synthetic streams. Persist per-trade diagnostics and WTL giveback total/mean/median; these are not additional gates.

| Mode | TriggerR | LockR |
|---|---:|---:|
| P0 | none | none |
| P1 | 0.50 | 0.00 |
| P2 | 0.75 | 0.25 |
| P3 | 1.00 | 0.50 |

LONG trigger/stop price=EntryPrice+Rmultiple*FormalSL*PipSize; SHORT subtracts. Raw favorable High/Low confirms trigger. Static protection begins on the next existing M1 bar, never the trigger bar. Missing clock minutes are not interpolated. Trigger-bar SL/TP/time close has no activation. Original SL first then frozen TP; once active, protection is the current SL and wins same-bar TP ties. Fill exactly at stop level, not gap Open; protection Pips equal frozen LockR*SL like existing SL/TP level fills. No trailing or extra trigger/lock variants.

Finite FormalTP<=TriggerR*FormalSL means NOT_APPLICABLE_TP_AT_OR_BEFORE_TRIGGER for that Candidate/mode, excluded from adoption and ranking. None TP remains applicable. N/A mode stores unchanged P0-equivalent trade diagnostics with Applicable=false and no activation; it never blocks P0 fallback. Structurally applicable mode may have individual trades hit TP before activation; retain that TP result. The formal TP never changes. A protective stop can only close at/before baseline original SL/TP/time close, so vector/scalar paths are bounded by original P0 actual close and then shortened to protection close. All modes preserve the same E2 trade universe, planned schedules and IDs; only actual close/result/reason may change, along with consequent diagnostics.

## Metrics, adoption and ranking

Existing unrounded stage1_metrics summarize handles mode-specific actual CloseTime→EntryTime→FixedKey, initial cumulative/peak0 DD, annual2020–2023 and PF state separately. P0 metrics remain exact baseline. P1–P3 require all U01Equivalent checks: Trades>=150, each year>=30, Losses>=10, AvgPips>0, FINITE PF>=1.10, PositiveYearCount>=3. Only U01-PASS modes compare with P0. Both finite numeric PF and non-null MedianAnnualAvgPips are required invariants; contradictions stop, no numeric sentinel or shortened-year median.

DoNotWorsen: TotalPips/PFpips/MedianAnnualAvgPips/PositiveYearCount >=P0, MaxDDPips <=P0. Equality passes, all unrounded. ReductionCount=P0 WTL-Pk WTL (negative allowed); ReductionFraction=count/P0 WTL when P0>0, otherwise null and fraction gate false. Both fraction>=0.20 and count>=5 required. Applicable AND U01 AND all five comparisons AND both reduction gates define adoption. No Giveback/MFE/MAE/WinRate/Avg improvement/activation-count/Sharpe extra gates.

Rank PASS modes by WTL reduction count DESC, DD ASC, PF DESC, TotalPips DESC, P1 before P2 before P3. Select rank1 only; no PASS→P0 with explicit retention reason. Candidate status PASS_U10P always, no Candidate drop; terminal count40. Each mode persists complete metrics, U01 checks, WTL/giveback, reduction, no-worsen/adoption checks, full trade diagnostics and result-stream/ID-sequence hashes. Persist selected mode and ranked PASS inventory. Future Candidate Freeze projection API preserves fixed fields, selected Discovery metrics and provenance/data/config/calendar hashes; no actual Candidate Freeze artifact created now.

## Independent implementation and evidence

u10p_execution uses vector first-hit arrays and raw extrema; u10p_reference independently loops bars, detects trigger/activation/stop, implements its own comparisons and stable priority sorts. Reference never calls optimized protection, trigger detector, comparator or selector. Existing immutable config/calendar, independent earlier scalar execution and metrics primitives are shared. Exact comparisons cover all trade fields, MFE/MAE/Reach/Giveback, trigger/activation/stop/hit, close/Pips/reason/WTL, annual/DD/gates/reduction/adoption/ranking/selection. Seeded artificial paths and nonempty four-year160-trade fixture exercise actual adoption and metrics, separately from formal inputs.

Synthetic cases cover P1/P2/P3 locks, trigger+originalSL reversal, trigger+TP, active stop+TP SL-first, missing next minute, no next bar, TP10/15 structural N/A, TP_NONE, LONG/SHORT raw/spread formulas, nonnegative MFE/MAE, shortened horizon, exact/below R reach, positive/negative/zero final, zero/negative WTL reduction, exact20%/5 trades, every U01 boundary, equality/just-worse comparisons, invariant null/INF rejection, every ranking priority, P0 fallback, barrier traps, U10 stream compatibility, input mutation and discovery isolation.

Bounded actual smoke uses only prespecified separate synthetic schedules on AUDUSD/EURJPY and seven fixed2020 dates, with LONG/SHORT and finite/None TP.72/72 exact M1 integrity audit;16 replays,56 E2 trades,224 mode trades; all exact scalar/vector comparisons PASS. Formal40Used=false, FormalProtectionModeProduced=false, FormalU10PPerformanceSaved=false, Full40Run=false, ValidationUsed=false, MonitorUsed=false. No formal Candidate was trial-run or viewed.

## Runner and recovery

CHAT_APPROVED_COLAB_B7_U10P_ONLY is required, default unapproved and Colab only.1 Candidate/job,40 jobs. Use result-independent fresh local/Drive roots; no overwrites. Each completion: local candidate→hash/checkpoint→validate→private Drive staging→copy/hash validate→DRIVE_COMPLETE last→atomic publish. Intermediate progress counts only. Identity binds reviewed implementation SHA, original/U09/U10 supplemental conditions, full/config/input hashes, U10 Result Freeze, calendar, manifest/all72 M1 identities, ordered40 IDs, source hashes, Python exact patch/NumPy/pandas. Any mismatch rejects normal resume. All40 completed resume uses stored evidence and jobs with no M1 load/evaluation.

Finalize approval CHAT_APPROVED_COLAB_B7_U10P_FINALIZE_ONLY is separate. Explicit Producer SHA=reviewed SHA=clean HEAD; never source-autoadopt. Same Python major.minor, patch differences allowed; NumPy2.3.5 and pandas2.2.3 exact; normal resume stays patch-exact. Read only identity.json +40×candidate/checkpoint/DRIVE_COMPLETE=121 trusted files. Reject missing/extra/duplicate/corrupt/hash/identity/status mismatch; ignore incomplete staging. Fresh separate local output only; no output until all40 audits pass; source unchanged. Only persisted schema/hash validation and stored-field aggregates, no M1/E2/Engine/MFE/MAE/trigger/simulation/metrics/WTL/Gate/ranking/selection recalculation. Trap tests cover those callable entry points and public API; deterministic replay, COMPLETE last and source bytes unchanged tested.

Outputs: input_identity,preflight,candidate_results,checkpoint_audit,pair_summary,protection_summary,mode_summary,winner_to_loser_summary,review,artifact_manifest,COMPLETE. Finalize additionally saves identity/environment/preflight/source audit. COMPLETE_U10P_ONLY written last after40/40. Fresh Drive archive after COMPLETE only; exact SHA/Bytes/ZIP order/member SHA/CRC verified; raw M1 forbidden.

## Review and stopping boundary

notebooks/b7_u10p_profit_protection.ipynb and b7_u10p_finalize_only.ipynb separate mount/install/checkout/input/calendar/M1 audits/tests/smoke/preflight/fresh/resume/finalize/archive; all RUN flags False and approvals blank. Reviewed Freeze SHA must be entered explicitly after Chat review. Producer pin is this implementation's containing commit, not the previous U10 Producer.

All previous code/tests/notebooks/inputs/conditions/Stage1-U10 results remain byte-identical. Dependent release memberships unchanged, hashes refreshed only. main/B6/strategy portfolio/Global R2/EA/SET/VPS/live/forward untouched. Final full B7 test evidence is test_results.json. Stop at Implementation Freeze; formal40 run and Candidate Freeze/Validation/Monitor require separate instructions.
