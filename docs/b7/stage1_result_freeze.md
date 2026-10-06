# B7 Stage1 Result Freeze

Status: COMPLETE_STAGE1_ONLY_FROZEN. Stage1ConditionsFrozen=true; Stage1ImplementationStatus=FROZEN; Stage1ResultFrozen=true; Stage1ExecutionComplete=true.

Source of Truth: actual Google Drive archive `/MyDrive/b7_stage1_finalize_20261006`. All 12 files were read and hashed; every manifest entry matched SHA256 and Bytes. COMPLETE binds the exact manifest and review. ZIP contains exactly 11 distinct expected members; each member was streamed, CRC checked by the ZIP reader, and its SHA256/Bytes matched the corresponding archive file.

## Identities

Conditions: `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. Original implementation: `abe588cf14c225f1cc8f9f991700fbe815618cc2`. Finalizer: `a585e8a0ec73ed34fa0d5918fe373b4e4940ee01`. Original Python3.13.15 / NumPy2.3.5 / pandas2.2.3; finalizer Python3.13.16 / NumPy2.3.5 / pandas2.2.3. All identity, environment, preflight and review fields agree; JobRecomputation=false. Original identity object hash agrees with the frozen original identity specification.

## Source audit boundary

The saved finalizer audit is PASS, binds exactly identity.json plus four trusted files for each of the 90 prescribed jobs, with no missing, extra or duplicate trusted paths. Its hash list agrees with finalize_identity. The reviewed finalizer validates zero errors, complete jobs, exact counts, map shapes and hashes before emitting PASS. This Result Freeze verified that saved evidence; it did not independently reread the original job checkpoint files, M1 or trades, and did not repeat finalization. The Colab preflight records 108 tests PASS.

## Recounted results

{"AnchorWeekday": {"FRI": 2, "MON": 58, "THU": 1, "TUE": 9, "WED": 2}, "Direction": {"LONG": 57, "SHORT": 15}, "EvaluatedStructures": 7335360, "EvaluatedVariants": 44012160, "Families": 12638, "FamilyCounts": {"AUDJPY": 1697, "AUDUSD": 1074, "EURAUD": 1647, "EURJPY": 1783, "EURUSD": 1333, "GBPAUD": 1055, "GBPJPY": 1593, "GBPUSD": 705, "USDJPY": 1751}, "PairSelected": {"AUDJPY": 8, "AUDUSD": 8, "EURAUD": 8, "EURJPY": 8, "EURUSD": 8, "GBPAUD": 8, "GBPJPY": 8, "GBPUSD": 8, "USDJPY": 8}, "PlateauPassRecords": 647576, "PlateauRecords": 739598, "PositiveYearCount": {"4": 72}, "SelectedCount": 72, "SourceJobCount": 90}

Selected has 72 distinct Representative CandidateIDs, exact pair ranks 1–8, Top8=true, matching anchor/member/suppression schemas, and equals the Top8 records streamed from the full family file. Direction/weekday/positive-year distributions were recomputed from each representative’s own metrics, not all family members. Every Plateau and Family JSONL record parsed successfully. These observations record Stage1 only and do not justify changing any later-stage conditions.

## Storage and later-stage input identity

The full selected_top8.json is 12,600,180 bytes because it embeds all family members. It is frozen in Drive by exact SHA256/Bytes in `research_inputs/b7/stage1_selected_top8.reference.json`. The smaller `stage1_selected_representatives.json` is a derived 72-row summary, not a replacement for the full selected input. Plateau, Family and ZIP also remain in Drive. Small completion, identity, audit, preflight, progress and review artifacts are copied byte-for-byte to GitHub. The copied original manifest retains original Drive filenames; review.json is stored as stage1_review.json in GitHub. The separate archive manifest records all 12 original paths, hashes and sizes.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 200 | `f4761d74ce7853ac8cf164d22ca3b62d318c697d3d7575a5f187164795ec6fb8` |
| archive.zip | 194226727 | `517d119f24c0fe1f7b7a593dcbcff9e27f30b3d04379370c92aab73f85e0f034` |
| artifact_manifest.json | 1118 | `4172d2f83b46c13c00cd0fe42ae2ef4bf3325934cec31102c2df8a944cd3af52` |
| family_suppression.jsonl | 930147538 | `81934f1aa4e5afa21e691b547e52ccdb9c714502e134b4edc6601a6a9450f87d` |
| finalize_environment.json | 54 | `6d276f4d31930552310ab35d0c59b61d3bd570dc9449f45dd1c68d62199ce2a9` |
| finalize_identity.json | 658 | `62249da352daea7dfa9da43e7e2eedaac1106ed272e9e7df2ca012e11af7a1b4` |
| finalize_preflight.json | 381 | `878b57b2cc4cc4e6eadcd74588c9a30fa08a6ec0624a369e5a8ab55886f19e86` |
| plateau_diagnostics.jsonl | 850965540 | `8203cbefa6502cb7b5d6ff159dd8462ab8b3e9a67f8b77cf3a463553e673f3c3` |
| progress.json | 93 | `1df34694c48d8d65f5de493c8b83fd82872b86c6ea2e502a8336ed1b701b9504` |
| review.json | 621 | `67488aa0ead706b2a51ed5651841c7f494851e3d2d897dc1bcabf6598ff603d4` |
| selected_top8.json | 12600180 | `b77baa21fc23da8ddf9ce6ad00bb863384d7b88b9c0b506d49b63bbc04b9370b` |
| source_checkpoint_audit.json | 44997 | `3db47c30905893b8af730a3b18c01e90aeb15b5f508fffaa439cbc380bf909b2` |

## Scope and checks

108 B7 tests PASS in Work (Python3.12.14, synthetic data). All source code, tests, notebook, research conditions/configuration and M1 manifest remain byte-identical to the Finalize-Only freeze. Only result documentation, archived evidence, derived summary/input reference and status/manifests change. Existing release manifest membership stays fixed; hashes of updated documentation/status are refreshed to keep checkout integrity checks consistent. Historical implementation freeze commits remain immutable.

Top8 remains eight per pair. No gate, ranking, family, Plateau, spread, SL grid, source, pair, weekday or execution semantics changed. U06+, Candidate Freeze, Validation and Monitor are NOT_RUN. No EA/SET/VPS/live changes. Result Freeze does not authorize another execution. Stop here.
