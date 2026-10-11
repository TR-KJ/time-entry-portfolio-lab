# B7 U11 Validation Implementation Only

U11ImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW. U11ConditionsFrozen=true; U11ImplementationAuthorized=true; U11ExecutionAuthorized=false; U11Executed=false. ValidationPerformance=NOT_RUN; MonitorPerformance=NOT_RUN. Work Implementation Freeze → Chat review → separate explicit Colab execution approval. No formal Candidate, including one trial Candidate, has been evaluated. All actual-price implementation checks use prespecified synthetic schedules only.

## Frozen input and scope

Candidate Freeze ebfe204d3561b064c1b4dc98d2fd417631dcc009; parent U10-P Result Freeze e0c57c8815d7f49c158585218fe5300bda699f95. Original Conditions 5dbac7af2d41aa912308868e6ad1a6dbf7cdd107; U09 supplement 1466a2c3e8b3d523233c45d665a6cac21e974393; U10 supplement e34099b9c807df1f145f96ca92c2443fe552fa36. Existing inputs/results/conditions/production are unchanged.

U11 input `research_inputs/b7/u11_validation_selected40_input.json`: SHA256 0a9db7f5d65191cd88153199470034a78286880920960442b9e300d0fbb18ed4, bytes257887, object SHA256 b0ad97127368ec624f4c29cc3be711d3fa35d04d263da4950fd92355e8b95ec8. Candidate Freeze source SHA256 ceacffaaf085cb3470b28548328315dfed9d817e53f368043f54b3583017b328. Ordered unique40, NoReplacement=true. Counts USDJPY1/EURJPY8/GBPJPY8/AUDJPY4/AUDUSD0/EURAUD7/GBPAUD5/EURUSD5/GBPUSD2. No rank replacement or dropped-candidate resurrection.

Fixed P0/P1/P2/P3 counts37/2/1/0. P2=GBPAUD Rank2 `B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610`; P1=GBPUSD Rank4 `B7S1:GBPUSD:LONG:TUE:E0365:D0:X1120:H0755` and Rank7 `B7S1:GBPUSD:LONG:TUE:E0370:D0:X1180:H0810`. These IDs are audited structurally only.

All six fingerprints remain exact:

| Fingerprint | SHA256 |
|---|---|
| CandidateSet | 0fc2a24c248057bf4b7fa5ba1b9413cbb49725bead885372d8f3104c67d432d5 |
| ProtectionMapping | 7a2097c0de2db8cfa27b5da54867af4ecd0bbf3ac002ec81dd92de3cdd196ee6 |
| ScheduleMapping | f58977252feedd00b32122ed31cf076ff91221e93c2c7b73f02a2e367d340d62 |
| DiscoveryBaseline | 00abcf9491b6b275da0204be5444c0a1973557fbd4c976c4de61ab84b85fb40c |
| SelectedStreamMapping | eb1e8057df483fbb86536c0be62448c38898f27792f605e34bd0665955ac0192 |
| EnvironmentExecution | 37cac03494b06353b47e0a33d289d4d7fca35ffb1628b2090bec9e9f1bad4dee |

The U11 config binds file/object hashes, complete frozen U11 contract, fingerprints, exact environment/execution identity, calendar, manifest and immutable source artifacts. Input validator independently reconstructs the Candidate Freeze projection and checks every field and order. Calendar SHA256 7a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb; calendar source commit173be2a114dad6bd183a0a1515581528850f0850.

## Period and execution

`load_validation` is separate from Discovery. Exact72 filename map and frozen hashes, existing Helsinki→naive JST conversion, raw finite/index/OHLC checks, owned Validation slice, discard full frame, concatenate/sort/copy and validate again. Rehash sources after loading. Engine receives only [2024-01-01,2026-01-01); any2020–2023/2026 price row rejects. Raw-file integrity audit can read all bytes; it does not calculate period performance. No source replacement, acquisition or gap filling.

U11 optimized execution function AST matches U06 exactly; only period globals and Validation input validator differ. Entry uses exact raw Open ± frozen spread/pip. Planned exit must be within Validation; find existing exit at+0..+4 before any SL/TP; +5 is missing. Fallback cannot cross2026. Chosen Sunday or different-day Monday exits reject. Entry Dec25–Jan3 stops. Holding30..1440, missing entry skips, missing path bars never interpolated. Inclusive entry/exit raw High/Low, SL first in same-bar TP tie, fill stop/TP level, unrounded Pips, no epsilon.

Candidate days use frozen weekdays, DOM D1=1–10/D2=11–20/D3=21–end and months, within Validation. Frozen entry/exit/dayoffset/holding/SL/TP untouched. Generate E0 executable trades first; apply saved canonical E2 event set to planned entry→planned TimeExit inclusive, even if actual SL closes early. Remove each trade once, count all matched events and multi-event overlap. E2 retained universe and stable TradeID=object_hash([CandidateID,planned entry,planned exit]) are preserved through protection.

## Fixed protection and diagnostics

Only FormalProtectionMode is evaluated. P0=no protection; P1 trigger0.50R/lock0R; P2 trigger0.75R/lock0.25R; P3 trigger1R/lock0.50R; R=FormalSL. Selected Pk with finite TP<=triggerR×SL hard-stops before execution; no P0 fallback/reselection. Frozen TP unchanged.

Raw favorable High/Low confirms trigger; static lock activates next existing M1 bar, never trigger bar. Trigger-bar SL/TP/time exit means no activation. Once active, protective SL wins TP ties and fills the exact lock level. Missing clock minutes are not interpolated. Selected path ends at actual selected close. Original SL/TP/time baseline bounds the protection path.

MFE/MAE use spread-adjusted entry and raw High/Low from entry through actual selected close inclusive; floors0. LONG favorable High/adverse Low, SHORT favorable Low/adverse High. Giveback=MFE−FinalPips. WTL iff MFE>=0.50R and FinalPips<0; zero is not WTL. Trigger/activation/hit counts, WTL/Giveback, retention, PF/pips/DD changes and win rate are diagnostics only. No extra gates.

Persist all immutable Candidate fields, implementation/Freeze SHA, period, E2 diagnostics, selected trade fields, selected stream SHA, ID-sequence SHA, pre-protection E2 stream SHA and ID hash. Trade fields include raw/adjusted entry, planned/scheduled/actual times, SL/TP/mode, result/reason/fallback/missing fields, MFE/MAE/Giveback/WTL, trigger/activation/stop/hit and FixedKey.

## Metrics and decision

Selected trades only, sorted CloseTime→EntryTime→FixedKey. Combined and annual2024/2025 use Trades/Wins/Losses/ZeroPips/TotalPips/AvgPips/PFState/PFpips/MaxDDPips; monthly24 periods include empty months. EntryTime JST assigns year/month, including overnight trades. Combined DD starts cumulative=peak=0 without annual reset; annual DD is separate. PF loss-present FINITE, positive gain/no loss INF, no gain/loss UNDEFINED, null numeric for nonfinite states; no sentinel. Values and comparisons remain unrounded.

Sample requires each year Trades>=30, combined>=70, each year Losses>=5. Any failure→INSUFFICIENT_SAMPLE first. Formal checks are annual2024 TotalPips>0, annual2025 TotalPips>0, combined AvgPips>0, finite combined PF>=1.10, combined DD<=SelectedModeDiscoveryMetrics.MaxDDPips×1.50. Sufficient sample with nonfinite PF is an invariant contradiction and hard-stops. Sufficient sample plus all five→PASS, otherwise FAIL. Zero Discovery DD requires Validation DD0. Retention/WTL/activation/monthly values never add gates. RescuePASSAllowed=false; PostValidationRetuningAllowed=false.

The persisted validator checks original record exactness, required trade/metric schema, hashes, count arithmetic, sample booleans from saved counts, formal booleans from saved metrics and selected Discovery DD, conjunctions and status precedence. It does not call metrics/evaluator/Gate/status-selection APIs or replay M1. Summary separates sufficient-sample formal failures from insufficient-sample diagnostic false checks. PASS/FAIL/INSUFFICIENT_SAMPLE remain distinct; no ranking.

## Independent implementation and evidence

Optimized code uses vector first-hit arrays. Scalar reference independently executes bars, candidate-day filters, E2 windows, protection, metrics/DD, sample/formal comparisons and status; it imports no optimized execution/metric module or stage1_metrics. Shared immutable config constants are allowed. Exact comparisons cover full candidate and audit objects: candidate days, E0 executable stream/IDs, E2 survivors/matches/removals, baseline and selected execution, all diagnostics, annual/monthly/combined metrics, DD, checks/status and hashes.

Synthetic tests cover period ownership and boundaries, execution equivalence, all fallback delays, holiday/weekend, planned E2 window, unique multi-event exclusion, selected protection modes, next-existing-bar activation, same-bar SL/TP/trigger, structural conflicts, MFE/MAE/WTL and no-rounding boundaries; sample and five-condition boundaries; PF states/invariants; entry-year/month assignment; initial/no-reset DD and selected Discovery baseline; no hidden search, formal Work guards, AUDUSD0; immutable input and checkpoint/finalize/archive failures. All previous B7 tests are included. Exact final totals are in `results/b7/u11_implementation/test_results.json`.

72/72 M1 integrity PASS. Prespecified bounded actual smoke on AUDUSD/EURJPY, Jan8–27 2024 (exclusive end), daysJan9/11/16/23, LONG/SHORT, P0–P3, TP_NONE/20, SL10, fixed schedules547→1387 same day and1387→next-day247.64 replay cases,256 E0 executable trades,176 selected trades, exact scalar/vector results. None shares a full formal Candidate schedule tuple. Formal40Used=false; FormalValidationStatusProduced=false; FormalU11PerformanceSaved=false; Full40Run=false; MonitorUsed=false; ActualValidationRowsUsed=true; SyntheticSchedulesOnly=true. Only counts/audit status are saved; no formal performance.

## Colab runner, resume and Finalize-Only

Formal token `CHAT_APPROVED_COLAB_B7_U11_ONLY`, Colab-only, exact reviewed clean implementation checkout and ancestry. Forty Candidates/forty jobs. Identity includes Candidate Freeze, conditions, config/input/full prespec, fingerprints, source calendar/manifest/all72 identities, ordered IDs, execution identity and environment. Fresh separate local/Drive roots. Per job: local candidate→checkpoint→validation→private Drive staging copy and hash verification→DRIVE_COMPLETE last→atomic publication. Only completed/expected counts exposed while running; complete artifacts require40/40.

Normal resume requires all identity fields and exact Python patch/NumPy/pandas. Completed-only resume reads persisted jobs/evidence without loading M1 or evaluating. Incomplete staging is not a completed source. Existing completed jobs never recalculate.

Finalize token `CHAT_APPROVED_COLAB_B7_U11_FINALIZE_ONLY` is separate. Explicit reviewed Producer pin must match clean checkout, never auto-adopt source SHA. Producer is this Implementation Freeze's containing commit, not the Candidate Freeze parent. Python major.minor exact, patch differences allowed; NumPy2.3.5/pandas2.2.3 exact. Normal resume retains patch-exact policy.

Finalize reads only identity plus40×candidate/checkpoint/DRIVE_COMPLETE=121 trusted files. Require exact40 IDs, immutable Producer identity, all file hashes, terminal status, saved schema/arithmetic. Reject missing/extra/duplicate/corrupt/mismatch; ignore incomplete staging and partial root aggregates. Source unchanged and fresh separate local output. No individual result output until all40 source audits PASS. Trap tests prohibit M1/load_discovery/load_validation/Engine/execution/E2/protection/metrics/Gate/status evaluation and tests execution during finalize. Persisted boolean/status consistency is allowed. Deterministic replay and COMPLETE-last tested.

Outputs input_identity,preflight,candidate_results,checkpoint_audit,status_summary,pair_summary,sample_summary,formal_check_summary,event_summary,diagnostic_summary,review,artifact_manifest,COMPLETE. Finalize adds finalize_preflight,finalize_identity,finalize_environment,source_checkpoint_audit. Review/marker COMPLETE_U11_VALIDATION_ONLY; Finalize Mode=FINALIZE_ONLY and JobRecomputation=false. COMPLETE is written last.

After completion, create fresh Drive archive before viewing individual outcomes. Exact output inventory, SHA256/Bytes, ZIP member order/CRC/bytes/hash and archive marker-last validated; no raw M1. Full trade logs remain in local/Drive/archive. GitHub formal result projection is a later separately authorized Result Freeze. Optional Monitor projection accepts only persisted formal PASS records and preserves strategy identity; it never evaluates Monitor.

## Notebook and immutability boundary

`b7_u11_validation.ipynb` and `b7_u11_finalize_only.ipynb` separate mount/install/checkout/input/calendar/M1 audit/tests/smoke/preflight/formal/resume/finalize/archive cells. All13 RUN flags False, approval and reviewed/Producer SHA blank. Print counts only until archive is verified. Finalize forbids simultaneous formal/resume/M1 audit/tests/smoke/preflight flags.

All prior production/tests/notebooks/inputs/results/conditions remain byte-identical. Candidate Freeze artifacts, including historical release manifest, remain byte-identical. Its historical SoT/status hashes are preserved as historical evidence; current U11 release binds current docs/status. Earlier mutable release manifests keep membership and metadata unchanged; only dependent SHA/Bytes refresh. Main/B6/EA/SET/VPS/live/forward, Monitor, Money, Portfolio and Global R2 untouched. Stop at Implementation Freeze pending Chat review and separate explicit Colab U11 approval.
