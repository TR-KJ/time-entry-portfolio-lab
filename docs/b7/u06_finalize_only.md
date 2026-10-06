# B7 U06 Finalize-Only Implementation

Producer implementation is exactly `14e43b7b1307492a07b8653e8de9263b37cb02a9`. This release adds recovery from completed Drive candidate outputs only. It does not authorize or execute the formal U06 run. U06ExecutionAuthorized=false and U06Executed=false; U06FinalizeOnlyImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW after implementation checks PASS.

## API and immutable producer

`b7.u06_finalize_only.finalize_from_completed_jobs(source, output, reviewed_sha, approval=None, progress=None)` is separate from the normal runner. It requires `CHAT_APPROVED_COLAB_B7_U06_FINALIZE_ONLY`; normal `CHAT_APPROVED_COLAB_B7_U06_ONLY` is rejected. Production requires Colab, a Drive source, and fresh local output outside Drive and separate from the source. The reviewed finalizer SHA must be HEAD in a clean checkout, descended from the pinned producer, with valid finalizer release hashes and frozen successful implementation-test evidence.

No M1 or selected Drive inputs are reopened; only frozen repository metadata/compact input are read for identity validation. The current runtime does not launch the B7 evaluator tests during recovery: it verifies the frozen PASS evidence and release hashes. This prevents even synthetic evaluator calls within a Finalize-Only invocation. Full tests run during implementation, before Freeze.

The original u06_runtime, u06_execution, u06_reference, u06_selection, u06_input, u06_smoke, u06_config, compact input and existing notebook remain byte-identical to the producer. Normal resume retains exact environment including Python patch. Historical condition and Stage1 result artifacts are unchanged.

## Producer identity and environment

The separate finalizer config pins the producer identity excluding its not-yet-known environment: producer SHA, conditions, full prespec/U06 config hashes, Stage1 result commit, selected SHA, compact input SHA, Stage1 source audit SHA, M1 manifest hash and exact72 file metadata identities, and ordered72 CandidateIDs. It also binds the original repository source metadata bytes. Tests compare this pin to the unchanged producer preflight identity builder.

Producer and current Python must be canonical numeric major.minor.patch strings with equal major.minor; patch may differ. The producer Python is taken from the stored identity and retained unchanged. Both NumPy and pandas must exactly match producer and the producer's required2.3.5/2.2.3 versions. Examples:3.13.15→3.13.16 PASS;3.13→3.14 FAIL. The same rule allows a3.12.x producer only with a3.12.x finalizer. The original run has not occurred, so no producer Python patch is invented or certified in advance.

## Read-only source barrier

Trusted source reads are exactly identity.json plus candidate.json, checkpoint.json and DRIVE_COMPLETE.json for each of72 candidate directories:217 files. The fixed CandidateID set/order must exactly match the compact Stage1 representatives. Missing, extra, duplicate IDs/JSON keys, nonterminal states, corruption, symlinks and hash/identity differences stop processing.

Named `.incomplete-*` staging directories are ignored and never opened or counted as completed jobs. They cannot fill a missing candidate. Any other unexpected job directory/file is rejected. Root partial result/review/COMPLETE artifacts are ignored, not read or appended. Each candidate must bind its exact ID/schedule/symbol/rank; each checkpoint must bind the full stored producer identity and its canonical hash plus candidate hash; each Drive marker must bind checkpoint and candidate hashes. Only PASS_U06 or DROP_U06_SL is terminal. No gate, SL, TP or selection is rerun to make that determination.

Trusted hashes are checked during source audit and again before completion. Source is never written. Progress contains only ProcessedJobs/ExpectedJobs. No output directory or individual result is emitted before all72 source audits pass.

## Outputs and completion

Fresh output contains finalize_preflight.json, finalize_identity.json, finalize_environment.json, source_checkpoint_audit.json, candidate_results.json, checkpoint_audit.json, pair_summary.json, review.json, artifact_manifest.json and COMPLETE.json. Original producer identity/environment and current finalizer identity/environment remain separate. Candidate order is the frozen input order; filesystem order cannot affect aggregation.

Stored candidate objects are aggregated without recalculation. Review contains Status=COMPLETE_U06_ONLY, Mode=FINALIZE_ONLY, JobRecomputation=false, completed72 counts and U06_ONLY stop boundary. The manifest is prepared with the final review's exact hash; review is published at the end and COMPLETE is the last write. COMPLETE binds both manifest and review. Failures never reuse or overwrite the output directory; use a new local output on retry. Existing `u06_runtime.archive_completed` can archive a completed result after a separate guarded notebook action.

## Verification and scope

Synthetic72-job tests cover the complete audit, all required mismatch/corruption cases, environment policy, normal resume rejection, no-recomputation traps, public API, source immutability, fresh output, completion-last/interruption, ignored staging/partial results, producer identity equivalence and deterministic filesystem/process replay. Runtime traps cover M1 read/load, Engine, evaluate, select, scalar executor, normal producer preflight and evaluator-test execution.

A separate notebook `b7_u06_finalize_only.ipynb` leaves every RUN flag False. The existing U06 notebook is unchanged. Implementation reports and release hashes are under results/b7/u06_finalize_only. No real U06 Drive checkpoint or candidate results were accessed, no real candidate SL/TP/DROP result was generated, and no U06/U07+/Validation/Monitor run occurred.
