# B7 Stage1 Implementation Freeze

This release implements Stage1 only under the explicit implementation-only user instruction. Research conditions remain at `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. No formal sweep, Candidate ranking result, Top8 selection, U06+ research, Validation or Monitor has been executed. A separate Chat instruction is still required before Colab formal execution.

Current status: Stage1ConditionsFrozen=true; Stage1ImplementationAuthorized=true; Stage1ImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; Stage1ExecutionAuthorized=false. B01=CLEAR_WITH_LIMITATION; Stage0=PASS_WITH_PROVENANCE_LIMITATION unchanged.

## Architecture and exact execution

- `stage1_contract.py`: verifies the full/historical Freeze hashes on import; reads constants from the frozen full prespec; canonical CandidateID/fixed key and90 jobs.
- `stage1_reference.py`: independent scalar chronological bar traversal for bounded replay; no B6 candidate identities, selections or R-first ranking.
- `stage1.py`: owned read-only Discovery NumPy arrays; exact Entry and +0…+4 Exit lookup. It caches each of five SL first-hit positions once per Entry date over the maximum horizon, then evaluates every holding without performance pruning. Pure Time uses secured Exit Open; Fixed5SL is always TP_NONE. All variants use raw prices with no epsilon. Stops return exact negative SL pips. Time-exit Pips are not rounded before metrics. An exit must exist before a stop can count.
- `stage1_metrics.py`: deterministic chronological float64 Pips metrics, all four annual buckets, initial cumulative/peak0 DD, PF states, U01/U02 and lexicographic ranking. Trade order is CloseTime, EntryTime, fixed key. Within one structure/variant its fixed key is constant; merged trade helpers explicitly sort it. No parallel reductions.
- `stage1_family.py`: nonrecursive U03 point-formal-PASS ratio and all-valid median; U04 direct representative suppression with spatial buckets. No chained union, cross-pair ranking or minimum-family refill.
- `stage1_input.py`: exact72-file barrier and independently copied Discovery input; parser matches the inherited Helsinki localization (`infer`, `shift_forward`) then naive JST and duplicate rejection.
- `stage1_runtime.py`: preflight,90-job lifecycle, atomic completed checkpoints, exact resume rejection, output/selection finalization, complete-only manifest/archive.
- `stage1_smoke.py`: fixed one-anchor replay, no candidate performance reporting.

Entry is raw Open±fixed spread. Both Entry and chosen Exit bars are included in stop scanning. Stage1 exposes no TP path; inherited same-bar SL-first behavior remains covered by existing B7/B6-reference compatibility tests. Missing Entry/Exit stays missing. No interpolation, +5 fallback, weekend reconnection or Discovery boundary crossing. Dec25–Jan3 Entry stop is explicit. Friday→Saturday availability follows the inherited executor; no Friday→Monday bridge is introduced.

All288 entries ×283 holdings remain evaluated in each of90 jobs, even where observations are unavailable. Counts are81,504 structures/job,7,335,360 structures and44,012,160 variants overall. No candidate gate skips another variant's calculation. The cache optimizes path lookup only; it does not prune time structures.

## Metrics, IDs and neighborhoods

PF JSON uses PFState=`FINITE`/`INF`/`UNDEFINED`. PFpips is numeric for FINITE and null for INF/UNDEFINED; a state label preserves Infinity without a false finite sentinel. ZeroPips counts as a trade only. All four years participate; insufficient annual sample yields no formal ranking median. Gate comparisons use internal values without epsilon or display rounding.

CandidateID is fully reversible ASCII:

`B7S1:{Symbol}:{LONG|SHORT}:{MON|TUE|WED|THU|FRI}:E{entry:04d}:D{offset}:X{exit:04d}:H{holding:04d}`

Example of encoding only: `B7S1:EURUSD:LONG:MON:E0540:D0:X0570:H0030`. This is not a discovered candidate. Parser verifies redundant offset/exit fields. IDs use no random values or Python hash(). Fixed key is exactly Symbol, LONG-before-SHORT, Monday-before-Friday, Entry minute, Exit offset, Exit minute, holding, CandidateID. Jobs use `{Symbol}_{Direction}_{MON..FRI}`, ordered by symbol lexicographically, direction, weekday. Randomness is used only for an optional result-independent run-folder ID.

U03 neighbors keep Entry date/weekday and Exit offset. Invalid shifted schedules are omitted, but valid formal FAIL points remain in the median population. A valid point with no trades has undefined AvgPips; the full median remains undefined and cannot satisfy the ≥ condition. It is neither zero-filled nor dropped. Formal PASS counts never recursively reference Plateau PASS.

Family output retains representative, anchor/supporting weekdays, every member definition and original Pure metrics, suppressed IDs, direct-distance reason, pair family rank and Top8 flag. All eligible families are recorded; only the first eight per pair are selected, without a minimum.

## Preflight and authorization

The notebook defaults every RUN flag to False. Mount, dependency install, reviewed checkout, input audit, tests, bounded smoke, preflight, formal run, resume and archive are separate controls. `IMPLEMENTATION_SHA` must be set to the exact released SHA reported in Chat; it is intentionally not a self-referential embedded commit. Enabling resume alone does not start a sweep. The notebook disables bytecode writes before importing project modules, so imports do not dirty the reviewed checkout. Direct Python API users must likewise use `-B` or `PYTHONDONTWRITEBYTECODE=1`. A future explicitly approved run records its runtime execution authorization separately from this release's default-false authorization.

Formal runner additionally requires `CHAT_APPROVED_COLAB_STAGE1_ONLY`, a Colab environment, a clean checkout at the reviewed SHA, condition/release hash verification, exact NumPy2.3.5/pandas2.2.3, all B7 tests,72 input identities and bounded exact reference replay. Actual Python is recorded; a difference from3.12.14 never silently skips tests/replay. All barriers repeat on resume. This implementation release is not the separate Chat approval.

Input resolution matches only frozen filenames under an explicit user collection root; duplicates/missing names fail rather than substituting alternatives. Each file verifies SHA256,Rows,FirstRaw,LastRaw and filename before execution. Source files are checked again around loading. Only `[2020-01-01,2024-01-01)` copied arrays reach the evaluator; future arrays are rejected by its validator.

## Checkpoints, schemas and complete-only output

Resume identity contains implementation SHA, full/historical prespec hashes, runtime config hash, manifest hash,72 exact identities, spread/pip/grid, execution identity, Discovery bounds, actual environment,90 job definitions, gates/ranking/U03/U04, and the particular job key. Any difference or output hash corruption rejects reuse.

Each job is calculated in a private scratch directory. Only a fully complete hashed checkpoint is atomically moved into the jobs directory. Interrupted uncheckpointed work is never reused; the unfinished job restarts. Completed jobs remain reusable only on exact identity. Sequential deterministic scheduling is implemented; multiprocessing is not required and no new dependency is introduced.

1. Job summary: expected/evaluated structures and variants, Pure/SL/formal counts, errors, missing diagnostics and runtime identity. Checkpoint binds SHA256 of every job output.
2. Formal point PASS JSONL: structure/ID/fixed key, Pure overall/annual metrics, all5SL metrics and gates. Separate compact288×283 point maps retain every valid point's AvgPips/formal status for unbiased Plateau, including FAIL points. These maps are intermediate calculation artifacts, not top-candidate reports.
3. Plateau JSONL and family JSONL: full neighborhood provenance, suppression/membership/rank/Top8; selected families and review JSON only after all90 jobs are verified.

Full trade ledgers are not retained for44M variants. `regenerate(engine,candidate_id)` returns all six exact variant ledgers for an identified structure using the same frozen execution. Integrated synthetic tests verify exact regeneration against independent reference ledgers.

Progress prints only completion counts/errors/status. Finalization refuses missing/duplicate/unknown jobs, identity mismatches, count mismatches and corrupt artifacts. COMPLETE_STAGE1_ONLY is emitted only after ranking,Plateau,family,Top8 and an artifact manifest; a final completion marker binds manifest/review hashes. Synthetic tests exercise90 artificial empty checkpoint fixtures to validate this lifecycle; they are not a search and are deleted after tests.

Formal computation defaults to `/content/b7_stage1`. Drive saving is complete-only to a new folder, never overwrite. Only manifested output artifacts are copied and zipped; raw M1 is not copied.

## Validation performed in this implementation request

See `results/b7/stage1_implementation/test_results.json`, `input_barrier.json`, `bounded_smoke.json`, `benchmark.json` and `freeze_audit.json` for measured final results. The original Stage0 status test still expected the old BLOCKED/UNVERIFIED state; only its status expectation was updated to the already-approved provenance state plus execution-not-authorized check. Stage0 execution/calibration/audit code and historical B6 fixture remain unchanged.

Actual smoke reuses the pre-existing Stage0 anchor:2020-02-04 09:00 JST,30-minute holding, data bounded through09:34, nine symbols×two directions×(Pure+5SL)=108 cases. Every trade field, unrounded Pips, metric and gate matches exactly; no tolerance or performance table. The input barrier audits all72 files as identity, not performance. Benchmark uses only a fixed flat synthetic one-day input; its timing is not a full-run estimate.

Only B7 tests and their inherited B6 reference checks are claimed. The complete historical B6 test suite is NOT_RUN. No formal job on Discovery data, formal candidate output, U06+ search, Validation,Monitor,Money,Portfolio or R2 is performed. Main/B6 branches and EA/SET/VPS/live remain unchanged.
