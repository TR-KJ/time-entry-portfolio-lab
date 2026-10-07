# B7 U06 Result Freeze

Status: COMPLETE_U06_ONLY_FROZEN; U06ResultFrozen=true; U06ExecutionComplete=true. NoReplacement=true. U07ImplementationAuthorized=false; U07Executed=false.

Run ID:b7_u06_20261007_01. Actual archive:`/MyDrive/b7_u06_20261007_01_archive`; actual checkpoint root:`/MyDrive/b7_u06_20261007_01_checkpoints`. All archive files, all ZIP members and all72 actual Drive jobs were read and verified. No performance recomputation occurred.

## Identity and integrity

Producer:`14e43b7b1307492a07b8653e8de9263b37cb02a9`. Conditions:`5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. Stage1 Result:`72b8244c69d165fae4a3c806a1cdb5d6fcfa1a38`. Finalize-Only implementation reference:`0271f6c1f51c7fc5addc138f1fe66e0a9089c040`; the audited archive carries the producer's normal-finalization schema. Environment:Python3.13.16, NumPy2.3.5, pandas2.2.3. Exact config/full-prespec/selected/compact/source-audit/M1 manifest and72 M1 metadata identities/CandidateIDs matched frozen producer identity. Preflight records PASS,176 tests PASS and216 smoke cases PASS.

COMPLETE binds actual manifest and review SHA256. Every original manifest Path/SHA256/Bytes matched. ZIP contains exactly the expected non-ZIP archive files; every member hash, size and CRC passed. All72 job directories were present with no extras or duplicates. Each candidate, checkpoint and DRIVE_COMPLETE hash/identity/status passed; the archived candidate objects and checkpoint_audit exactly match those Drive jobs. The separately saved drive_checkpoint_audit binds all217 trusted source files.

## Independent recounts

| Pair | PASS | DROP |
|---|---:|---:|
| AUDJPY | 8 | 0 |
| AUDUSD | 7 | 1 |
| EURAUD | 8 | 0 |
| EURJPY | 8 | 0 |
| EURUSD | 8 | 0 |
| GBPAUD | 6 | 2 |
| GBPJPY | 8 | 0 |
| GBPUSD | 2 | 6 |
| USDJPY | 1 | 7 |

Formal SL distribution: {'55': 1, '60': 3, '65': 12, '75': 9, '80': 9, '95': 8, '105': 1, '110': 10, '125': 1, '130': 1, '165': 1}
TP_NONE=43; finite TP=13. Finite TP distribution: {'55': 1, '65': 2, '120': 1, '140': 4, '165': 3, '240': 2}

Per-pair SL/TP counts and finite TP/R groups are stored in u06_result_summary.json and were independently recomputed from candidate_results.json. All user-reported counts and groups match. These are observations only: no TP/R anchors, SL grids, gates, retention, ranking, later-stage rules or data change. Sixteen drops are not replaced; U07 input remains56.

## Frozen U07 input

`research_inputs/b7/u07_selected56_input.json`: SHA256 `fbb78686e8a767bb8fbaa903e9b89eee99d9c856b2182d29f1953bb51273fe39`, Bytes 34529. Contains exactly the56 PASS CandidateIDs, symbols, Stage1 PairRank, fixed schedules, FormalSL, FormalTP (null=TP_NONE), terminal U06 status and exact source candidate/checkpoint hashes. The top-level identity also binds the full candidate_results hash and producer identity. `u07_input.reference.json` binds this input. This is input preparation only, not U07 execution or final Candidate Freeze.

## Archive storage

Full candidate_results.json embeds SL/TP diagnostics and remains in Drive with exact SHA256/Bytes; archive.zip also remains there. Small review, completion, manifest, preflight, identity and audit artifacts are copied byte-for-byte to GitHub. Original review.json is named u06_review.json in GitHub; the copied original artifact_manifest retains its original Drive paths. u06_archive_manifest.json binds the entire original archive.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 197 | `959643113ea9f82beb6634b3c90a3df022bccf9f670cb59f893a5e04011a5306` |
| archive.zip | 696369 | `85ca1279b9479be6ec4d483586e8bd1ce503978ff438be5bdd2359a946b12b58` |
| artifact_manifest.json | 726 | `a520d8d1c46c9d88d6b3d28763a82f899dd9dd29ce32b9af8c632560c7ad2117` |
| candidate_results.json | 6023664 | `ebbf6d65d5c00419cf88cf2379543be0389bf31d272b9d970bce5c7ff5ea4123` |
| checkpoint_audit.json | 10568 | `9056e7cfbd95dd7ed4b47f23cd0100a9891cf7591af5078cba10c47b5d8e7c3a` |
| input_identity.json | 20481 | `c5a50dd802f5f79b2a100a8afa79eb5c676486b5f7a873efa9b30cc939a1f78d` |
| pair_summary.json | 282 | `8f279cfe220a254639b56480b230f3e6ff6fe9e62c26b9ebca25c2f33d37fbf6` |
| preflight.json | 20997 | `995e57f633428f811b87d7cfd8a444c55cf4bffb188f6968f1b7cb0104bd15e1` |
| review.json | 164 | `2feca228d135e94c46081c0cf859a4d3da657a924e11ace2164c06fa8171a854` |

## Scope and checks

207 existing tests PASS,0 FAIL,0 SKIP. Consistency checks and byte-identity audit cover existing code/tests/notebooks, research inputs/conditions and Stage1 results. Only result artifacts, status, Source of Truth and release-manifest metadata change. Prior implementation commits remain immutable; existing release manifest membership is preserved while changed documentation/status hashes are refreshed.

U07–U10/U10-P, Candidate Freeze, Validation and Monitor are NOT_RUN. No EA/SET/VPS/live change; no main merge or force push. A separate U07 Implementation Only instruction is required.
