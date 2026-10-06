# B7 Completed90-job Finalize-Only Implementation

Scope: implementation, tests and synthetic checkpoint fixtures only. The user reports a90/90-job Colab backup produced by implementation `abe588cf14c225f1cc8f9f991700fbe815618cc2`, under Python3.13.15 / NumPy2.3.5 / pandas2.2.3. This work has not accessed, finalized or opened candidate results from that backup. Research conditions remain frozen at `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`.

Current status: Stage1ConditionsFrozen=true; Stage1ImplementationAuthorized=true; Stage1ExecutionAuthorized=false; Stage1FinalizeOnlyImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; Stage1FinalizeOnlyExecutionAuthorized=false.

## Separate API and trust boundary

`b7.stage1_finalize_only.finalize_from_completed_jobs(source, output, reviewed_sha, approval=None, progress=None)` is separate from the normal runner. It requires the exact dedicated string `CHAT_APPROVED_COLAB_STAGE1_FINALIZE_ONLY`, Colab and the reviewed clean finalizer checkout. The normal `CHAT_APPROVED_COLAB_STAGE1_ONLY` is rejected here.

The existing `stage1_runtime.py` including `run_formal`, normal preflight, checkpoint validator and exact resume comparison is byte-identical to the original implementation. Engine, metrics, family, CandidateID and normal runtime config are also unchanged. Normal resume still rejects Python3.13.15→3.13.16, as well as code/config/data/environment changes.

Official source inputs are only `identity.json` and the90 directories' `checkpoint.json`, `summary.json`, `formal_pass.jsonl`, `point_map.npz`. Root partial Plateau/Family/Top8/review/manifest/COMPLETE artifacts are not read at all. They can contain invalid JSON without affecting the new result. There is no append-to-partial mode.

The stored original identity must equal the complete pinned identity in `stage1_finalize_only_config.json`: original implementation and conditions commits, both prespec hashes, original runtime config hash, M1 manifest hash, exact72 identities, spread/pip/SL, execution identity, Discovery bounds,90 job definitions, U01/U02/U05, ranking/U03/U04, and original environment. The pinned identity was generated from the original producer's identity builder and frozen repository manifest, not from user performance results. No current environment is substituted into the source jobs.

Source audit requires exactly90 regular job directories, JOB_COMPLETE, checkpoint identity and identity SHA, all3 output hashes, expected/evaluated81,504 structures and489,024 variants/job, zero errors,288×283 maps, valid dtypes, matching formal-map/JSONL/summary counts, unique reversible IDs, fixed structure fields and stored metric/map consistency. This is schema/integrity validation, not U01/U02 recalculation. Trusted hashes are checked again before and after processing; source mutation aborts completion.

## Current environment and preflight

Original environment is exactly Python3.13.15, NumPy2.3.5, pandas2.2.3. Finalizer Python may be3.13.x only;3.12.x,3.14.x and prerelease/noncanonical version strings are rejected. NumPy and pandas must match exactly. This exception is not applied to normal resume.

Current preflight requires exact reviewed finalizer commit, clean checkout, original implementation ancestry, frozen-condition hashes, finalizer release hashes, allowed environment and all B7 tests PASS. Tests use synthetic data; no72-file M1 reread or bounded actual-data replay is requested by this path. Current Work testing uses Python3.12.14 with explicit synthetic environment injection for the3.13 patch-policy tests. Real Colab/Python3.13 finalization is NOT_RUN and is intentionally blocked in this Work environment.

## No recomputation; unchanged selection semantics

No Engine, load_discovery, evaluate_job, regenerate, M1 parser, actual-data smoke or Gate function is called by the finalization processing path. Tests patch these calls to raise. Existing tests run as a separate preflight check and may exercise the engine on synthetic fixtures; they do not recalculate the user's jobs.

U03 reuses the unchanged frozen Plateau function. Point arrays are decompressed once per job and cached in memory, instead of repeatedly indexing compressed NPZ members for each neighbor. Job processing order is the original symbol/LONG-before-SHORT/Monday-before-Friday order. Formal records use the frozen fixed-key order.

Ranking uses stored finite formal metrics in exactly the original lexicographic order, without calling the original ranking helper's redundant U01 gate recheck. The dedicated family kernel retains the exact original direct-representative spatial bucket algorithm and output schema. Synthetic tests compare Plateau,Family andTop8 output bytes against the original finalizer on the same nonempty fixture. No thresholds, gates, family distances, minimum counts or Top8 policy change.

## Fresh output and completion

Output must not already exist and cannot equal, contain or be inside the source. The source is never written. A failure leaves only incomplete fresh output; it emits no final COMPLETE marker and does not reuse that directory automatically. Use another new directory after resolving the failure.

Outputs:

- `plateau_diagnostics.jsonl`
- `family_suppression.jsonl`
- `selected_top8.json`
- `review.json`
- `progress.json`
- `artifact_manifest.json`
- `COMPLETE.json`
- `finalize_identity.json`
- `finalize_environment.json`
- `source_checkpoint_audit.json`
- `finalize_preflight.json`

Identity separates original producer SHA/environment from finalizer SHA/environment. Review includes SourceJobCount90, both identities/environments,7,335,360 structures,44,012,160 variants, completed ranking/Plateau/family/Top8 flags and ExecutionStopsAt=STAGE1_ONLY. Progress exposes only phase/job counts, not candidate IDs,times or metrics.

After processing and source revalidation, the manifest is prepared with the exact final review hash. The final review and COMPLETE marker are written only at the end. COMPLETE binds manifest and review SHA256. The existing complete-only archive helper can archive this fresh output; no source jobs or M1 files are copied into the finalize result.

## Restore and notebook

`restore_completed_jobs(source, destination)` validates the source, copies only the361 trusted files into private temporary staging, revalidates all90 jobs and source hashes, then places RESTORE_COMPLETE and atomically renames the staging directory. An existing destination is rejected. Interrupted staging is not considered restored and is never reused. Source Drive backup is unchanged; partial finalize artifacts are not copied.

The notebook adds `RUN_RESTORE_CHECKPOINT`, `RUN_FINALIZE_PREFLIGHT`, `RUN_FINALIZE_ONLY`, `RUN_FINALIZE_ARCHIVE`, all False. FINALIZER_IMPLEMENTATION_SHA is independently supplied after review; FINALIZE_APPROVAL is empty by default. CHECKPOINT_BACKUP defaults to the user-named Drive backup; CHECKPOINT_SOURCE and FINALIZE_OUTPUT are separate local paths. Do not turn on RUN_FORMAL/RUN_RESUME for Finalize-Only. Finalize-only setup does not resolve DATA_ROOT or read M1.

## Future per-job Drive mirroring

Not implemented in this change, to keep the normal runner byte-identical. A separate future design should complete and validate each local job, copy into a unique Drive staging directory, verify destination hashes, publish a completion marker, and only then proceed to the next job. Synchronous mirroring adds Drive latency but bounds runtime-loss exposure to the unfinished job. This is a design note, not an available automatic backup feature.

## Tests and release evidence

`results/b7/stage1_finalize_only/test_results.json` records the final counts, environment and test IDs. Tests cover nonempty90-job fixtures, original-kernel equivalence, process/hash-seed replay, shuffled job/filesystem order, ignored invalid partial outputs, source immutability, no-calculation traps, restore interruption, fresh output, exact normal resume rejection, patch-only environment rules and corruption of identity/checkpoints/each output/counts/shapes.

All fixtures are generated from synthetic metrics in temporary directories and removed after testing. No user backup, formal candidate, Plateau/Family/Top8 result, U06+, Validation or Monitor is read or executed. Main/B6 and EA/SET/VPS/live are unchanged. Production Finalize-Only requires a separate Chat approval after reviewing this new Implementation Freeze.
