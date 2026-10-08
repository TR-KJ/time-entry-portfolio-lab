# B7 U07 Result Freeze

Status: COMPLETE_U07_ONLY_FROZEN; U07ResultFrozen=true; U07ExecutionComplete=true; NoReplacement=true. U07ExecutionAuthorized=false; U08ImplementationAuthorized=false; U08Executed=false.

Run ID:b7_u07_20261007_01. Actual Archive:`/MyDrive/b7_u07_20261007_01_archive`. Actual checkpoint root:`/MyDrive/b7_u07_20261007_01_checkpoints`. This Freeze audits completed outputs and projects U08 input; it does not recalculate performance or execute U08.

## Identity and integrity

Producer:`9adeef8514fb76efec70a2cc46ce85e306ea0597`. Original U07 Implementation:`6dadb449d94787eeb899099e0ff6d9d4be0e6100`. U06 Result:`c526dc1bb49d168376e5cb4858174524c0a63f7a`. Conditions:`5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. U07 input SHA256:`fbb78686e8a767bb8fbaa903e9b89eee99d9c856b2182d29f1953bb51273fe39`. Environment:Python3.13.16, NumPy2.3.5, pandas2.2.3. Config/full-prespec/input/manifest/full72 M1 metadata/ordered56 CandidateIDs match frozen expected identity exactly. Archive preflight records291 tests PASS,40 trade cases/8 full synthetic-schedule bounded replays PASS with Formal56Used=false, FormalWeekdaysProduced=false, PerformanceSaved=false.

COMPLETE manifest/review hashes match actual files. Every manifest Path/SHA256/Bytes matches. ZIP exact inventory, every member hash/size/CRC match original archive files. Actual56 job directories have no extras/missing/duplicates. CandidateID, complete identity/IdentitySHA256, candidate/checkpoint and DRIVE_COMPLETE hashes and terminal schema pass. Archive candidate_results and checkpoint_audit equal actual Drive objects. The trusted-file audit binds169 files and their aggregate hash. No M1 contents are reread by this result audit.

## Independent observations

| Pair | PASS | DROP |
|---|---:|---:|
| AUDJPY | 8 | 0 |
| AUDUSD | 7 | 0 |
| EURAUD | 8 | 0 |
| EURJPY | 8 | 0 |
| EURUSD | 8 | 0 |
| GBPAUD | 6 | 0 |
| GBPJPY | 8 | 0 |
| GBPUSD | 2 | 0 |
| USDJPY | 1 | 0 |

ActiveWeekdayCount:1=55,2=0,3=1,4=0,5=0. Actual sets:Mon42,Tue9,Wed1,Thu1,Fri2,Mon/Tue/Wed1. Final membership frequencies:Mon43,Tue10,Wed2,Thu1,Fri2.

Canonical SetName:W0=18,W1=12,W2=26,W3=0. Equal W sets are deduplicated and retain the highest-priority canonical label. W2 can therefore have one actual active weekday. Per-candidate SetName, FormalWeekdays and ActiveWeekdayCount are stored separately in u07_result_summary.json.

Expanded candidate:`B7S1:EURAUD:SHORT:MON:E1135:D1:X0365:H0670`, EURAUD PairRank4, Anchor MON, FormalWeekdays MON/TUE/WED, canonical W1. Diagnostics:MON/TUE/WED CORE,THU SUPPORT,FRI NON_SUPPORT. The other55 candidates exactly retain Anchor only. All56 Anchors are CORE.

All280 diagnostics:CORE85,SUPPORT14,NON_SUPPORT181. Non-anchor224:CORE29,SUPPORT14,NON_SUPPORT181. Non-anchor CORE/SUPPORT43 exist despite55 anchor-only selections; anchor-only does not mean every other weekday failed its individual gate.

| Weekday | CORE | SUPPORT | NON_SUPPORT |
|---|---:|---:|---:|
| Mon | 43 | 0 | 13 |
| Tue | 24 | 5 | 27 |
| Wed | 10 | 6 | 40 |
| Thu | 5 | 2 | 49 |
| Fri | 3 | 1 | 52 |

Monday has the most CORE diagnostics; CORE counts decline across later weekdays in this sample. These are result observations only. No CORE/SUPPORT/Anchor/set/80%/Best/U08 rule, subset search, candidate population, source data or U06 parameter changes are authorized by these observations.

## U08 exact input projection

`research_inputs/b7/u08_selected56_input.json`: SHA256 `7c49b9cd0374b57f4da78eb784aa646050cba507b0ff037e303085a61deb7616`, Bytes 59686. All56 PASS candidates, ordered as the frozen U07 input, with CandidateID/Symbol/PairRank, fixed Direction/EntryMinute/ExitMinute/ExitDayOffset/HoldingMinutes/Schedule, FormalSL/TP, AnchorWeekday, FormalWeekdays, canonical SetName, U07Status, U06 source identity, U07 candidate/checkpoint hashes, Producer SHA and top-level Archive ZIP/manifest/result/identity hashes. No replacement, no weekday reselection or performance evaluation. U08 must retain pair/direction/times/holding/SL/TP/FormalWeekdays and cannot return to weekday selection from DOM/Month results.

## Storage and fixed hashes

candidate_results.json and archive.zip remain in Drive with exact SHA256/Bytes. Small completion, manifest, review, identity, preflight, pair and checkpoint artifacts are copied byte-for-byte to GitHub. review.json is stored as u07_review.json; the copied original artifact_manifest retains original Archive paths. u07_archive_manifest binds every original file.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 197 | `35ba74e94dbb6cab3f0e5230b697f6e979a3dac91e884cb99db3628c9a61f7e8` |
| archive.zip | 101366 | `e42560677151bdf13fe839e6973574c119e01e26756ef5c141dd79ac5d28bba9` |
| artifact_manifest.json | 724 | `592d960f2b5537316848e1906d2b4f147bd938e3b54cc233501911b296e5ff0e` |
| candidate_results.json | 530151 | `5f277a27ef3b5ecb200277823c65800ada96231afcb9a7964e885d9476401ed7` |
| checkpoint_audit.json | 8230 | `1c8f84a41e1ab04b30089b7327abf7c72998b087b9a20ad2e3c7a82a7b88d2f1` |
| input_identity.json | 19597 | `c104b08d13061f5e76a390df133dfe72e451af422171fc6ebfa973411aa1ad7a` |
| pair_summary.json | 218 | `b37ba91db2529096e6a9254906dc942277be3981b8e3efbb003b75effe97a45f` |
| preflight.json | 20177 | `c1f45e4768f335ed7a62342c18ae2def0e71b5bf27e2b133b6ba88a9ed3ac5d2` |
| review.json | 147 | `6911cf9fd6ed92809fe6c4cf34f6da17536619f0aac5bb398d40ff3d0b212b66` |

## Checks and stopping boundary

291 existing tests PASS,0 FAIL/ERROR,0 SKIP on Work Python3.12.14. All requested independent recounts agree with the actual source and user-reported observations. Code/tests/notebooks, prior inputs/conditions and Stage1/U06 result bytes are unchanged. Existing release manifest memberships are preserved; only documentation/status dependency hashes are refreshed.

U08 DOM/Month/LOMO/Calendar,U09,U10,U10-P,Candidate Freeze,Validation,Monitor are NOT_RUN. No main/B6/EA/SET/VPS/live changes. Stop after Result Freeze and U08 input preparation; U08 Implementation Only needs a separate instruction.
