# B7 U06 Implementation Only

This release implements Formal SL local plateau and TP search/selection only. No formal U06 execution, SL/TP selection for the real 72, DROP result, U07+, Candidate Freeze, Validation or Monitor is produced by this Work. Existing Stage1 code, results and original condition artifacts remain unchanged.

## Frozen identities and endpoint supplement

Stage1 Result Freeze: `72b8244c69d165fae4a3c806a1cdb5d6fcfa1a38`. Original conditions: `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. Original Stage1 implementation: `abe588cf14c225f1cc8f9f991700fbe815618cc2`; finalizer: `a585e8a0ec73ed34fa0d5918fe373b4e4940ee01`.

The user's explicit endpoint supplement is normative for this U06 implementation and is recorded separately in u06_config.json; the historical conditions commit is not rewritten. For both SL and TP, calculate Anchor×0.80 and Anchor×1.20 using Decimal, round each independently to the nearest five pips with half-up, include both endpoints and the anchor. Python round() is not used. SL alone extends a fewer-than-three-point grid to Anchor−5, Anchor, Anchor+5; TP never gains that extension. Examples:65→50…80;30→25/30/35;25→20/25/30;10 SL→5/10/15;10 TP→10;15 SL→10/15/20. No other frozen research policy changes.

## Exact Stage1 input

Full selected input SHA256 is `b77baa21fc23da8ddf9ce6ad00bb863384d7b88b9c0b506d49b63bbc04b9370b`, Bytes12,600,180. The extractor reads that full Drive JSON, not the derived representative summary. It requires72 unique representatives,9×8, pair ranks1–8, Top8 and matching representative definitions. It verifies the immutable Stage1 source-audit hash and its361 exact trusted paths; original identity must match the original producer configuration.

For each job containing a selected representative, the extractor verifies checkpoint, summary and formal_pass bytes against the Stage1 audit. Per-job identity is the unchanged Stage1 checkpoint_identity wrapper around the run identity and exact job definition. Point-map hashes are bound through checkpoint and original audit; point maps are not reread because extraction does not use them. Source files remain read-only. Only matching representative records are retained, with Pure metrics exactly equal to the selected family member, all official five SL values and metrics, each U02 flag and PassingSLCount rechecked against Stage1. This is extraction/verification of existing Stage1 results, not U06 performance generation.

`research_inputs/b7/u06_selected72_input.json` is the compact formal input, retaining schedule, rank, annual metrics, five-SL PASS anchors and source hashes. Preflight repeats extraction and compares the entire compact object. No rank9 replacement is possible. Anchor weekday is fixed; supporting weekdays are never merged.

## Evaluators and selection

u06_reference.py is an independent scalar raw-bar replay. u06_execution.py validates and owns a Discovery-only frame once and vectorizes SL/TP first-hit tests. It does not modify Stage1 Engine. Both secure exact/+1…+4 Exit availability before testing stops, scan Entry and chosen Exit bars inclusively, choose SL on equal first-hit bars, use raw High/Low without epsilon, and retain exact spread, weekend, year-end, boundary, missing-trade and holding semantics. Helsinki→JST and Discovery copying reuse the existing Stage1 input path.2024+ evaluator input is rejected. Exit missingness is never a zero-Pips trade. Metrics use unchanged Stage1 summarization/gates and unrounded internal float64 values.

u06_selection.py merges overlapping SL grids, evaluates each distinct SL/TP once, extracts maximal5-pip PASS runs of at least3 points and applies the single Zone median≥Pure×0.80 condition. Zones rank by median Avg, count, worst Avg, median PF, then central value; the winning lower median is Formal SL. No zone means DROP_U06_SL with no TP evaluation and no replacement.

TP anchors are TP_NONE and rounded/deduplicated0.5/1/1.5/2/3R with minimum5. Only finite PASS anchors with a passing finite neighbor enter local search; TP_NONE is never a neighbor. Local ranges use the endpoint supplement without SL's small-anchor extension. The same zone ranking and lower median yield the finite candidate. Adoption requires no degradation in positive-year count or worst-year Avg and median annual improvement≥max(0.10, baseline×0.05); otherwise TP_NONE. JSON FormalTP=null means TP_NONE for PASS_U06; DROP has no TP decision. SL is never revisited. Event/MFE/calendar/1m/Validation are absent.

## Runtime and durability

72 fixed CandidateIDs are72 independent jobs. `run_formal` requires Colab, mounted Drive, exact reviewed clean commit, release/config/input/conditions hashes, exact NumPy2.3.5 and pandas2.2.3, all B7 tests, input audit and bounded smoke. Dedicated approval is `CHAT_APPROVED_COLAB_B7_U06_ONLY`; default is unapproved. No import launches a run.

Each job writes complete local diagnostics and a hash-bound completion marker. Before the next job, synchronous Drive mirroring validates local bytes, copies into private staging, validates destination bytes/identity, publishes DRIVE_COMPLETE last, then renames to the final candidate directory. Incomplete staging is not reusable evidence. An existing malformed published job, mismatch or corruption stops resume. Existing folders are rejected for fresh runs. Drive latency is deliberately paid before the next job to preserve completed work after runtime loss.

Resume requires exact implementation, config/full-prespec, Stage1 result/selected/compact input/source audit, M1 manifest/full file identity, environment including Python patch, and CandidateID. Verified Drive jobs restore into fresh local staging and are reused without recomputation; missing jobs alone compute. U06 finalize-only is NOT_IMPLEMENTED in this release; Python patch differences reject normal resume. This optional feature was not used to weaken identity.

Only after all72 local and Drive results agree and have terminal PASS_U06 or DROP_U06_SL status does finalization produce COMPLETE_U06_ONLY. `candidate_results.json` contains full SL/TP points, gates, zones, choices, comparison, source schedule/rank and status. Additional outputs:input_identity, checkpoint_audit, pair_summary, review, artifact_manifest, COMPLETE. Progress exposes counts only. Archive uses new staging, verifies copied files and each ZIP member, publishes completion last, and includes no raw M1. Interrupted finalization can restart with a new local root restored from exact completed Drive checkpoints.

## Notebook, tests and smoke

notebooks/b7_u06_sl_tp.ipynb separates mount, dependency install, checkout, input audit, tests, bounded smoke, preflight, formal, resume and archive. All ten RUN flags defaultFalse. The user must set a reviewed SHA, dedicated approval and fresh result-independent Drive run-id. There is no automatic start.

Tests cover endpoint examples/half-up, dedup, maximal zones, retention boundaries, ranking priorities, lower median, TP eligibility/adoption/fallback, no-TP-on-DROP, exact reference replay including nonempty synthetic SL zones, source input mismatches, Discovery isolation, local/Drive integrity, interrupted copies, exact resume and72-job synthetic completion/archive. Result reports contain counts and exact-equality outcomes, not candidate performance.

Actual smoke is fixed independently of selected schedules:2020-02-04 09:00–09:35 JST,30-minute holding,9 symbols×2 directions×SL10/15/20×TP_NONE/5/15/25=216 cases. It checks every trade field, metrics, gates and zones exactly. This one-day sample cannot satisfy annual gates and is not a formal optimization. Synthetic four-year replay supplies the nonempty-zone decision equivalence test.

Implementation status is FROZEN_READY_FOR_CHAT_REVIEW only after the recorded tests/input audit/release hashes pass. U06ExecutionAuthorized=false and U06Executed=false. Formal Colab execution requires separate Chat approval after this Implementation Freeze.
