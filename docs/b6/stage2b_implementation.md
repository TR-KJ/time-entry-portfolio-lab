# B6 Stage2-B implementation freeze — 2026-09-29

## Scope and actual input audit
Stage1 fixed exactly50 time structures. Stage2-A completed in Colab with COMPLETE_STAGE2A_ONLY, 50 candidates, 1,500 configurations, 1,281 PASS and219 FAIL. Work can access the exact Drive runtime files and has audited their bytes/provenance/schema/keys/counts/aggregate consistency. No actual Stage2-B center or selected setting is computed in Work.

Stage1 Freeze: `920b9be5c8f1bcf46a46dbbd4ac06dc19eb295b1`.
Stage1 candidate SHA256: `82a71c1ac9ffaa9a121795c6e0186bf77af5185b90bc21f65d7174161c35214f`, exactly50.
Stage2-A Freeze: `50f83f3904acc3bc3abe54204db7a2ab4964b024`.
Stage2-A config SHA256: `bab7eced359ad914e63b6a13dd6c956f86c9b7f695f9b8fc622b2c8f9e4685d6`.
The exact eight runtime file hashes are locked in `stage2b_config.json`, including all/yearly/diagnostic results, summary, identity, effective config, candidate input audit and progress. Their runtime records Python3.13.15, NumPy2.3.5 and pandas2.2.3. Stage2-B records its own Python version and rejects resume across version changes; Python need not equal the preceding stage's version.

Formal input is the full result directory, not a review ZIP. The validator first reads immutable file snapshots into memory and hashes those same bytes before parsing. It validates Stage1 exact candidate input, both prior Freeze/config identities, completion state, 50 IDs and unchanged time structures, exact expected1,500 condition keys,6,000 yearly keys and1,500 diagnostic keys. Duplicate/unknown IDs, SL/TP/mode/ratio changes, missing columns/rows and future years stop. It checks integer counts, metric labels and consistency, annual totals, gate reasons, exit counts/rates and56 expected M1 input hashes. It does not repair or recreate inputs. The small numerical tolerance used to cross-check independently serialized aggregate sums is never used for ranking, thresholds, price comparisons or execution.

## Files
- `stage2b_config.py`: fixed config hash.
- `stage2b_input.py`: exact prior runtime input audit, with no center selection.
- `stage2b_selection.py`: pure center/grid/stability/final selection functions, with no IO or execution imports.
- `stage2b_metrics.py`: adapter to unchanged Stage2-A fast replay and raw-R metrics.
- `stage2b_search.py`: Colab authorization, identity, checkpoints, complete outputs; no Stage3/Validation/Monitor entry points.
- `stage2b_smoke.py`: first3 fixed input candidates,2 predefined SLs,TP_NONE/0.5R/2R,first matching February weekday in each Discovery year. Compatibility only, no actual center selection/ranking/selected artifact.
- `stage2b_test_suite.py`: runs every test, including the original immutable release tests against their historical snapshot.
- `notebooks/b6_stage2b_local_optimization.ipynb`: default no-run; formal input paths and explicit Stage2-B SHA/Chat flags.

## Official N06b
Only P02 PASS coarse settings are eligible. Growth ordering: AvgR descending,TotalR descending,MaxDDR ascending,TP_NONE first,SL ascending,TP ascending,fixed key. Efficiency is TotalR/max(MaxDDR,1); Efficiency descending followed by the same Growth ordering. If both choose the same setting, keep one center with both aliases; do not choose a runner-up. No eligible setting means zero centers.

Each finite center generates at most25 points from SL±10 andTP±10 in5-pip steps. TP_NONE generates at most5 SL points and remains NONE. Bounds are SL10–300 andTP5–900 inclusive. Remove out-of-bounds points without replacement. Never extend the range. Union settings are evaluated once with all center aliases. All unique settings receive raw-R full/yearly metrics and diagnostic output; no gate-driven pruning.

For each evaluated setting, build separate neighborhoods inside each originating center's own grid. Finite: SL/TP±5,at most9 points. NONE: SL±5,at most3 points. Include self and all evaluated valid points, including P02 failures. Do not union two center grids to enlarge a neighborhood. No extra minimum of3 neighbors is imposed by this instruction; a boundary NONE point may have2. Nonfinite/undefined neighborhood AvgR metrics fail stability explicitly rather than being dropped/imputed.

Stability requires point P02 PASS,3×pass-count>=2×neighbor-count, and neighborhood median AvgR>=0.8×point AvgR. Record count/pass-count/rate,median AvgR,median TotalR,worst MaxDDR,pass/reasons and center distances. A duplicated point is eligible if any originating center passes; among passing versions take the version with the best official final key. This interpretation was explicitly confirmed by the user in this task. Preserve every center-scoped record in a separate output.

Distance is L1 on the5-pip grid,SL-only for NONE. A point's ranking distance is the minimum over all its center aliases, even when another alias supplies the stability metrics. Final order: neighborhood median AvgR descending,neighborhood pass-rate descending,point AvgR descending,minimum center distance ascending,MaxDDR ascending,TP_NONE first,SL ascending,TP ascending,fixed key. Fixed key: Symbol,Direction,Weekday,EntryMinute,ExitDayOffset,ExitMinute,HoldingMinutes,CandidateID ascending. For the same point's otherwise equal center-scoped metrics,SourceCenterType lexical order supplies a deterministic diagnostic tie-break.

Select exactly one setting per surviving original time structure. No stable point means STAGE2B_DROPPED_NO_STABLE_POINT; no coarse P02 center means STAGE2B_DROPPED_NO_P02_CENTER. No replacement candidates/refill. Selected SL/TP are frozen for a future Stage3; Stage3 is not implemented here.

## Execution and search-space boundary
Unchanged Stage2-A reference/fast implementation and metrics are imported. Discovery only2020–2023 JST. Adjusted Open±fixed spread,SL/TP from adjusted Entry,raw High/Low,Entry/Exit inclusive,SL-first on ties,Exit exact/+1…+4 secured before scan,missing Entry/Exit no trade even with earlier hits,TimeExit at chosen Open,no epsilon/interpolation/new rounding/slippage,year-end Entry stop12/25–1/3. Intermediate missing-path diagnostics retain the frozen convention through the secured exit. Formal metrics use unrounded R; display Pips6/R9; zero R counts in Trades but not Wins/Losses.

Theoretical maximum:50 per structure,2,500 total. Implementation expected upper bound:2,500. Actual unique count may be lower due to NONE,center deduplication,overlap,bounds or no PASS center. It is calculated from the formal input only during the authorized Colab run and saved separately in search_space.json. Work does not calculate actual centers or actual unique count; no result is inferred from the upper bound.

## Outputs and resume
Default `/content/b6_stage2b` includes identity.json,effective_config.json,stage2a_input_audit.json,search_space.json,progress.json,centers.json,stage2b_all_results.csv.gz,stage2b_yearly_results.csv.gz,stage2b_diagnostics.csv.gz,stability_results.csv.gz (one row per unique point),stability_by_center.csv.gz (each center scope),dropped_structures.csv,stage2b_selected_settings.json,stage2b_summary.json,stage2b_review.json andstage2b_review.zip. List provenance fields use JSON encoding within CSV. Empty outputs retain schema and dropped identities. Final settings include source center/aliases,point and neighborhood metrics,minimum distance and all four yearly rows,along with unchanged time structure and selected SL/TP.

One checkpoint job per original candidate, including candidates with no centers. Atomic JSON shards then atomic checksum ledger; interruption before ledger update recomputes that uncommitted job. Missing/corrupt committed shards stop. Finalization checks every job/grid/condition/year identity and expected total before writing completed status. Selected/stability artifacts are generated after all jobs. Re-running complete checkpoints only regenerates final outputs; it does not extend the range. Only COMPLETE_STAGE2B_ONLY outputs are research results; incomplete tables are not.

Resume identity binds Stage2-B code/config,Stage2-A Freeze/config and all8 result hashes,Stage1 candidate SHA,56 M1 input hashes and exact Python/NumPy/pandas versions. Paths are not scientific identity. Use a fresh output directory on mismatch. Review ZIP omits the local56-file identity inventory and raw M1/trade logs; it contains full result tables and hashed provenance. ZIP is for review,not resume; preserve the whole output directory to resume. Drive backup defaults OFF.

## Testing without modifying old frozen files
Only Plan/Decision Register evolve from the Stage2-A release manifest. Stage1/Stage2-A code,config,notebooks,tests,results and manifests remain unchanged. Their original release tests intentionally assert their historical documents. The full-suite driver binds the ROOT of exactly the two historical release-test modules to a clean checkout of Stage2-A Freeze,while every other test uses the current Stage2-B tree. New release tests also assert all unchanged historical executable/test/notebook bytes and results in the current tree. No tests are skipped and no prior release assertions are weakened.

Prepare a clean detached worktree at `50f83f3904acc3bc3abe54204db7a2ab4964b024`, then run from the current repo with its research package on PYTHONPATH:

```text
PYTHONPATH=src/research python -m b6.stage2b_test_suite --stage2a-snapshot /path/to/clean-stage2a-snapshot
```

This runs the complete test suite, including synthetic center tie-breaks,grid union/bounds,stability boundaries/overlap,final order/drop,strict input audit,shared execution regression,adapter compatibility,resume,default notebook and both historical/current releases. Work additionally runs the bounded real-data smoke without center/final selection. No research full sweep is invoked by these checks.

## Stop point
After fast-forward GitHub save,verify remote SHA=local HEAD and tracked tree clean,then stop. No main merge,force-push,Stage2-B production sweep,Stage3,Event Filter,Validation,Monitor,portfolio or EA/SET/Dell/VPS/live/Global R2 changes.

WorkではStage2-B full sweep未実行。Chat確認後にGoogle Colabで実行する。
