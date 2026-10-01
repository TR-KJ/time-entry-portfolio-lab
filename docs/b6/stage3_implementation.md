# B6 Stage3 implementation freeze

2026-10-01. Stage3 changes Entry/Exit schedules only, with Stage2-B SL/TP, symbol, direction, weekday and original planned ExitDayOffset fixed. Work performs input audit, implementation and tests, then GitHub Freeze. No Stage3 research sweep or later stage runs in Work.

## Actual Stage2-B input
The formal Drive result directory is `/content/drive/MyDrive/b6_stage2b_archive` in Colab, corresponding to the local Drive folder named `b6_stage2b_archive`. Work audited the actual runtime files, not only the user's review summary or ZIP. COMPLETE_STAGE2B_ONLY,1,042 conditions,95 centers,50 selected structures,0 drops and50 TP_NONE settings were verified across the official artifacts. Stage3/Validation/Monitor execution flags are false.

Stage2-B Freeze: `686b4b8b479055e3ff43a21f450b1a7182367ebe`.
Stage2-B config SHA256: `60ae03111ed6bf283df47acf62a6713a8ee53459a48d52a84a70553dd9070bf3`.
Selected settings SHA256: `476bad8f65b896d9c76a52dcf22f7c68381e22c0235523253fbdaa7ad1010a5b`.
Stage2-A Freeze: `50f83f3904acc3bc3abe54204db7a2ab4964b024`.
Stage1 Freeze: `920b9be5c8f1bcf46a46dbbd4ac06dc19eb295b1`.
Stage1 candidate SHA256: `82a71c1ac9ffaa9a121795c6e0186bf77af5185b90bc21f65d7174161c35214f`.

`stage3_config.json` locks all14 formal input file hashes and the observed CSV schemas/counts: progress,identity,effective config,summary,selected settings,centers,all results,yearly results,diagnostics,unique stability,center-scoped stability,dropped structures,search space andprior Stage2-A input audit. Raw bytes are hashed and parsed from the same in-memory snapshot. Files are neither repaired nor regenerated. Selected settings are not copied to GitHub. All scientific file bytes must match exactly at Colab runtime.

The validator checks previous Freeze/config/result identities,56 M1 identities,completion counts,contamination flags,original candidate structures,center-generated SL/TP result keys,annual metrics and P02 status,diagnostic counts,selected-to-stability/center-scope/yearly agreement,prior final ordering,and the selected/dropped partition. Checking the completed Stage2-B ordering is an input audit,not a new Stage3 selection. Selected SL/TP must agree with SelectedSL/SelectedTP and the formal result. Numeric comparison tolerance in cross-file serialization audit is never used for execution,thresholds or ranking. Malformed/missing/hash-mismatched input stops; no review-ZIP fallback.

## Modules
- `stage3_config.py`: immutable config hash.
- `stage3_input.py`: formal prior result audit and normalized fixed input structures.
- `stage3_grid.py`: datetime schedule generation around Original5mAnchor; invalid-point reasons; frozen execution adapter.
- `stage3_metrics.py`: unchanged Stage2-A reference/fast replay and raw-R reporting for each adjusted schedule.
- `stage3_selection.py`: evaluated valid3×3 neighbors,stability and exactly the authorized three-layer final order.
- `stage3_search.py`: Colab/Chat/SHA/release authorization,all valid points,atomic checkpoints,resume and final artifacts.
- `stage3_smoke.py`: first3 formal inputs,only entry/exit deltas -1/0/+1,first matching February weekday in each Discovery year; no formal selection/ranking.
- `stage3_test_suite.py`: complete suite with immutable historical release assertions bound to clean historical snapshots.

## Fixed time grid
Anchor Entry/Exit/day offset come from the unchanged Stage1 structure retained in Stage2-B. A concrete JST schedule date with the candidate's weekday is used for datetime arithmetic. Each entry/exit delta is independently -5…+5 inclusive,one-minute step. No reanchoring,rolling second search or range extension.

Exclude a point if adjusted Entry leaves the original date/weekday,adjusted planned ExitDayOffset changes,or adjusted planned holding falls outside30…1440 minutes. Do not wrap an invalid schedule to another day or replace excluded points. Original anchor consistency and five-minute alignment are checked before generating minute schedules. SL/TP are read-only fixed inputs,including TP_NONE. The engine receives adjusted EntryMinute/ExitMinute/HoldingMinutes; CandidateID stays the original structure ID.

Theoretical maximum is121 per selected candidate; the audited count50 gives6,050. Implementation expected upper bound is also6,050. Actual full-run valid count is not calculated in Work. The authorized runner saves TheoreticalMax,CandidateCount,RawGridPoints,InvalidSchedulePoints,ActualUniqueConfigurations and per-candidate counts separately. Invalid schedule details are retained. All valid points are evaluated before any stability selection; P02 cannot prune computation.

## Execution and metrics
Stage1/Stage2-A/Stage2-B execution files remain byte-identical. Discovery only2020–2023 JST,exact M1 Entry Open±fixed spread,SL/TP from adjusted Entry without new price rounding,raw High/Low,no epsilon,Entry and selected Exit bars included,SL-first on a same-bar tie. Secure planned Exit or first available+1…+4 before scanning; if all missing,do not salvage a trade from an earlier trigger. TimeExit uses selected Open. No intermediate interpolation,broker splicing,slippage addition or weekend bridging. Entry stopDecember25–January3 remains unchanged.

Formal metrics use unrounded R; displayPips6/R9. Zero R counts as a trade but neither win nor loss. P02:total trades>=150,each Discovery year>=30,losses>=10,PF>=1.10,at least3 of4 annual TotalR positive. Shared metrics preserve empty/undefined/INF conventions,MaxDDR from zero equity,and signed AvgLossR. Missing-path diagnostics retain the frozen convention through the secured exit bar.

Result schedule columns distinguish original `EntryMinute/ExitMinute/HoldingMinutes` and explicit Anchor fields from `AdjustedEntryMinute/AdjustedExitMinute/AdjustedExitDayOffset/PlannedHoldingMinutes`. The adjusted schedule is used for execution. Final selected artifacts also expose FinalEntryJST/FinalExitJST strings,FinalExitDayOffset andFinalHoldingMinutes. All-results rows include exit and missing/fallback diagnostics in addition to the separate diagnostic table.

## Stability and final selection
For point(e,x),include evaluated valid points at(e±1,x±1) within the original grid,including self. Out-of-grid and invalid schedules are omitted,not zero-filled. Record NeighborhoodCount even on boundaries. Do not add a minimum-neighbor-count rule.

A stable point must itself pass P02,have3×NeighborhoodPassCount>=2×NeighborhoodCount,and satisfy NeighborhoodMedianAvgR>=0.8×PointAvgR. Undefined neighborhood metrics fail explicitly rather than being silently removed/imputed. Record median TotalR,worst MaxDDR andpass-rate as diagnostics.

Final order is only:
1. NeighborhoodMedianAvgR descending.
2. abs(EntryDeltaMinutes)+abs(ExitDeltaMinutes) ascending.
3. AdjustedEntryMinute,AdjustedExitDayOffset,AdjustedExitMinute,EntryDeltaMinutes,ExitDeltaMinutes,CandidateID ascending.

PointAvgR,TotalR,PF,DD,WinRate,NeighborhoodPassRate andStage2-B scores are never ranking tie-breaks. At most one time point survives per input candidate. No stable point produces STAGE3_DROPPED_NO_STABLE_TIME,with no refill or return to previous SL/TP/center candidates. Selected time andSL/TP are frozen for a future Event Filter step. No Stage4 implementation or execution is included.

## Outputs and recovery
Default `/content/b6_stage3`:identity.json,effective_config.json,stage2b_input_audit.json,search_space.json,invalid_schedules.json,progress.json,stage3_all_results.csv.gz,stage3_yearly_results.csv.gz,stage3_diagnostics.csv.gz,stage3_stability.csv.gz,dropped_structures.csv,stage3_selected_settings.json,stage3_summary.json,stage3_review.json andstage3_review.zip,plus checksum ledger and candidate shards. Raw M1/full trade logs are not stored. Review ZIP contains compact result/provenance tables and excludes the local56-file identity inventory. The entire output directory is required for resume; review ZIP alone is insufficient.

One job per selected input candidate. Atomic shard write precedes atomic checksum ledger update; interruption before ledger commit recomputes only that uncommitted candidate. Committed missing/corrupt shards stop. Finalization checks every ordered time/year key and fixed schedule/SL/TP field; it requires all jobs before formal selection. Resume binds Stage3 code/config,Stage2-B Freeze,selected SHA,all14 prior input hashes,Stage1 candidate SHA,56 M1 hashes,andPython/NumPy/pandas versions. NumPy2.3.5/pandas2.2.3 are fixed; Python must be identical within a resumed run. A mismatch requires a fresh directory.

Notebook flags PREPARE_ENVIRONMENT,MOUNT_DRIVE,RUN_STAGE3_FULL,CHAT_CONFIRMED_STAGE3_FREEZE,SAVE_OUTPUT_TO_DRIVE defaultFalse andSTAGE3_FREEZE_SHA defaults empty. Default run-all displays rules/count expectations only:no input reading,price loading or metrics. Full run requires Google Colab,confirmed flag,40-digit exact Stage3 SHA,clean tracked checkout,release hashes andformal input identity. Only after COMPLETE_STAGE3_ONLY does it display actual counts,P02/stability counts,selected/dropped structures,delta distributions,anchor-unchanged count andselected settings,with Stage4/Validation/Monitor unexecuted. Drive backup is opt-in.

## Complete test suite with unchanged prior freezes
Only the evolving Plan/Decision Register are updated. Prior code/config/tests/notebooks/results/manifests are not edited. Historical release tests still assert their historical documentation,so the full-suite driver binds the ROOT of the two older release modules to a clean Stage2-A snapshot andthe Stage2-B release module to a clean Stage2-B snapshot. All other tests use the current tree. Current Stage3 release tests additionally verify prior frozen bytes/results. No assertions are weakened or tests skipped.

Prepare clean detached snapshots at the Stage2-A andStage2-B SHAs,then run:

```text
PYTHONPATH=src/research python -m b6.stage3_test_suite --stage2a-snapshot /path/to/stage2a-snapshot --stage2b-snapshot /path/to/stage2b-snapshot
```

Unit/synthetic/regression tests include one-minute7-pair Long/Short NONE/finite execution,midnight/offset/holding boundaries,entry/exit/raw/fallback cases,stability thresholds,forbidden ranking keys,SL/TP invariance,input contamination/duplicates/hash mismatches,resume corruption,default Notebook andrelease integrity. The bounded actual-data smoke is compatibility only,no Stage3 research selection.

## Stop point
Fast-forward GitHub save only,no main merge or force push. Verify remote SHA=local HEAD andclean tracked tree,then stop. Stage3 full research sweep,Stage4 Event Filter,Validation,Monitor,portfolio andlive/EA/SET/Dell/VPS/Global R2 changes are not performed.

WorkではStage3 full sweep未実行。Chat確認後にGoogle Colabで実行する。
