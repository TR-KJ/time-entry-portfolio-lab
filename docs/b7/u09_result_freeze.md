# B7 U09 Result Freeze

Status: COMPLETE_U09_ONLY_FROZEN. U09ResultFrozen=true; U09ExecutionComplete=true; U09Executed=true; U09ExecutionAuthorized=false. U10ImplementationAuthorized=false; U10Executed=false.

## Identity and actual source audit

Producer: `345a0e8ef659bcd601b73a6475c4613a04ff4337`. Conditions: `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. Supplemental Freeze: `1466a2c3e8b3d523233c45d665a6cac21e974393`; prespec SHA256: `cefa5aed9fc820c8bbf4dd4a57622263cd2443bc8509f8016f62bb20e76a92f3`. U08 Result: `382f351c169da48e1fe4eadf31fc858bbd57eed0`. U09 input SHA256: `8faa886c3d1a72e8020688b8931481d81d1df637d63b0b368e0171b8d1dce2ca`.

Archive: `/MyDrive/b7_u09_20261010_01_archive`. Checkpoints: `/MyDrive/b7_u09_20261010_01_checkpoints`. Producer environment: Python3.13.16 / NumPy2.3.5 / pandas2.2.3.

Actual inventory:11 archive files;10 ZIP members. COMPLETE hashes, exact manifest Paths/SHA256/Bytes, ZIP exact member order and all hashes/bytes/CRC pass. Identity binds config/full prespec/supplement/U08/input/M1 manifest/all72 M1 metadata/ordered54 IDs/environment. Original Conditions, Supplemental and U08 Result are Producer ancestors. Supplemental is a separate conditions-only parent commit before implementation. Formal preflight records502 tests PASS and bounded smoke8 fixed replays/72 points/432 trades, exact reference/optimized comparison; Formal54Used/FormalScheduleProduced/PerformanceSaved/FullSearch=false.

Actual54 completed job directories and163 trusted files pass CandidateID, identity, IdentitySHA256, candidate/checkpoint/DRIVE_COMPLETE hashes and terminal schema; staging is not trusted. Ordered archive results equal all54 Drive candidates and checkpoint_audit. All source hashes unchanged before/after. No M1 content, evaluator, selector or performance recomputation was used. Trusted-file aggregate SHA256: `c6744fd711b3ef9c272ea6628b9b51c67399f1549ccbf18a41b948528f5fbe6e`.

## Independent decisions and schedules

PASS_U09=54; DROP=0; NoReplacement=true. Decisions: FINE_TUNED23; INSUFFICIENT28; BEST_IS_ANCHOR3; NO_1M_PLATEAU0; UNDEFINED_ANCHOR_BASELINE0. All54 have a Plateau PASS candidate and defined anchor baseline. Zero-count decision types remain frozen.

| Pair | Total | Fine | Insufficient | Best Anchor |
|---|---:|---:|---:|---:|
| AUDJPY | 8 | 3 | 5 | 0 |
| AUDUSD | 7 | 2 | 5 | 0 |
| EURAUD | 8 | 6 | 2 | 0 |
| EURJPY | 8 | 3 | 4 | 1 |
| EURUSD | 6 | 4 | 2 | 0 |
| GBPAUD | 6 | 3 | 3 | 0 |
| GBPJPY | 8 | 1 | 6 | 1 |
| GBPUSD | 2 | 1 | 1 | 0 |
| USDJPY | 1 | 0 | 0 | 1 |

Retained31 final Entry/Exit/day offset/holding exactly equal Anchor and shifts0/0. Fine23 final schedule and shifts equal saved rank1 Best point. Each54 has121 unique exact nominal points, anchor0/0, consistent ranked plateau inventory, Best=rank1, AnchorNeighborhood0/0 and matching baseline. No rank2 fallback, re-anchor, second fine tune or range extension.

## Final shifts

| Entry | Exit | Count |
|---:|---:|---:|
| -5 | -3 | 1 |
| -5 | 0 | 1 |
| -5 | 2 | 1 |
| -3 | -1 | 1 |
| -2 | -1 | 1 |
| -2 | 3 | 1 |
| -1 | -1 | 2 |
| 0 | -2 | 1 |
| 1 | 5 | 1 |
| 2 | -5 | 1 |
| 2 | -1 | 1 |
| 3 | -2 | 1 |
| 4 | -3 | 1 |
| 4 | -2 | 2 |
| 4 | 0 | 1 |
| 4 | 1 | 1 |
| 5 | -4 | 1 |
| 5 | -2 | 1 |
| 5 | -1 | 1 |
| 5 | 3 | 2 |

Entry distribution: {'-1': 2, '-2': 2, '-3': 1, '-5': 3, '0': 1, '1': 1, '2': 2, '3': 1, '4': 5, '5': 5}. Exit distribution: {'-1': 6, '-2': 5, '-3': 2, '-4': 1, '-5': 1, '0': 2, '1': 1, '2': 1, '3': 3, '5': 1}.

## Boundary observation

Boundary means Fine Tuned and abs(entry)==5 or abs(exit)==5. Count10/23. No penalty, exclusion or expanded search.

| CandidateID | PairRank | Entry | Exit |
|---|---:|---:|---:|
| `B7S1:AUDJPY:LONG:MON:E0730:D1:X0720:H1430` | 2 | -5 | 0 |
| `B7S1:AUDJPY:LONG:MON:E0765:D1:X0535:H1210` | 4 | 5 | -1 |
| `B7S1:AUDJPY:LONG:MON:E0825:D1:X0815:H1430` | 7 | 5 | 3 |
| `B7S1:AUDUSD:LONG:MON:E0820:D1:X0700:H1320` | 8 | -5 | 2 |
| `B7S1:EURAUD:SHORT:MON:E0755:D1:X0365:H1050` | 1 | 5 | -2 |
| `B7S1:EURAUD:SHORT:MON:E1135:D1:X0365:H0670` | 4 | -5 | -3 |
| `B7S1:EURAUD:LONG:FRI:E0120:D1:X0075:H1395` | 7 | 5 | -4 |
| `B7S1:EURUSD:LONG:MON:E0945:D1:X0750:H1245` | 6 | 5 | 3 |
| `B7S1:GBPAUD:SHORT:WED:E0115:D0:X1370:H1255` | 5 | 1 | 5 |
| `B7S1:GBPAUD:LONG:TUE:E0360:D0:X1420:H1060` | 7 | 2 | -5 |

Pair boundary counts: {'AUDJPY': 3, 'AUDUSD': 1, 'EURAUD': 3, 'EURJPY': 0, 'EURUSD': 1, 'GBPAUD': 2, 'GBPJPY': 0, 'GBPUSD': 0, 'USDJPY': 0}.

## Threshold and margin audit

Saved ActualImprovement equals saved Best neighborhood median Avg minus AnchorBaseline; RequiredImprovement=max(0.05,AnchorBaseline*0.025). Unrounded arithmetic checked for all54. Derived MarginAboveThreshold=Actual-Required is audit-only, never a new gate. Fine23 all margin>=0; insufficient28 have non-anchor Best and Actual<Required; BestAnchor3 retain0/0 without rank2 fallback.

Margin minimum `0.0005241935483263904`; median `0.3739247311827853`; maximum `3.139274981874467`. Smallest two source-exact observations:

- `B7S1:AUDJPY:LONG:MON:E0825:D1:X0815:H1430`: {"ActualImprovement": 0.45752688172036926, "AnchorBaseline": 18.280107526881714, "CandidateID": "B7S1:AUDJPY:LONG:MON:E0825:D1:X0815:H1430", "EntryShiftMinutes": 5, "ExitShiftMinutes": 3, "MarginAboveThreshold": 0.0005241935483263904, "PairRank": 7, "RequiredImprovement": 0.45700268817204287, "Symbol": "AUDJPY"}.
- `B7S1:EURUSD:LONG:TUE:E0365:D0:X1155:H0790`: {"ActualImprovement": 0.20629629629620716, "AnchorBaseline": 8.10370370370384, "CandidateID": "B7S1:EURUSD:LONG:TUE:E0365:D0:X1155:H0790", "EntryShiftMinutes": -1, "ExitShiftMinutes": -1, "MarginAboveThreshold": 0.003703703703611172, "PairRank": 2, "RequiredImprovement": 0.202592592592596, "Symbol": "EURUSD"}.

All23 full-precision records are in improvement_margin_audit.json. Small positive margins remain adopted; no safety buffer, downgrade or new margin threshold.

## Supplemental binding

Producer/config identity binds U09-S01: schedule-valid FINITE non-null PF values only, including Formal FAIL; no INF/UNDEFINED numeric sentinel or state ordering. All saved ranking candidates satisfy the finite-set invariant. U09-S02: valid-null Avg remains valid and in the denominator, Point Gate fails, neighborhood median undefined and Plateau false. Persisted null schema checked without recomputing metrics/neighborhoods/ranking. Neither rule is removed because undefined-baseline observation is zero.

## U10 exact input only

`research_inputs/b7/u10_selected54_input.json`: SHA256 `ea64a5145c08db79d6122c24c6ab875c190739b816275ae4bd443510d9571744`, Bytes 156934. Exact ordered54 PASS projection, NoReplacement=true, all final schedules/shifts/decisions, SL/TP/Weekday/DOM/Month/CalendarFreeze and U08/U07/U06 lineage preserved. Candidate and checkpoint SHA256 and Producer/archive identities are bound. Formal schedule uses U09 Final fields; Anchor fields are provenance only. The containing Git commit identifies this Result Freeze, avoiding a self-referential commit hash in its own file.

FormalEventMode=E2, ModeChosenBeforeResults=true, calendar commit173be2a114dad6bd183a0a1515581528850f0850. Full frozen U10 contract is copied exactly from full_research_prespec.U10 into input. E2=pair-central-bank E1 + US_NFP + US_CPI + AUD_CPI only for AUD. Fixed JST/windows: FOMC03:00±180, NFP/CPI21:30±120, BOJ12:00±180, BOE21:00±120, ECB21:15±120, RBA13:30±120, AUD_CPI10:30±120. No B6 Candidate C matrix or historical release-time reconstruction. Future overlap is planned Entry through planned Time Exit inclusive even with early SL/TP; remove once. Future post-E2 U01 failure drops candidate without E0/E1 fallback. Retention80%, removed20 and E0 improvement are diagnostics, not adoption gates. None of these event computations is run here.

## Fixed archive hashes

Large candidate_results and archive.zip remain in Drive. Nine small artifacts are byte-identical copies (review renamed u09_review); original manifest retains original Archive names. github_artifact_manifest binds repository copies.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 197 | `68228ca851ff58d0bc6d6d158076f1efcd5d3e63cde7b0777dd1246a1c0bbcf3` |
| archive.zip | 2930914 | `e559d35c2382d3cb60fad71e0eb0882daa41383d700938dd9ed69668bf260fff` |
| artifact_manifest.json | 967 | `be4dfc0fdf78cb83bdf633c7502ae4d57f651930b77b154183089c584b32120b` |
| candidate_results.json | 20203743 | `eb0d52ea6869ea4be131ce5fbae968a34a97913b4e2107eacd75211aedb67505` |
| checkpoint_audit.json | 7937 | `71fbde6e9f0393b2365e95acc5be6525b49d5740b02601fdc376750528f17ca4` |
| decision_summary.json | 156 | `e7c782239cf6f8f2e4d8e025ca786afe0f554aa08e46cd2e431a24216029b338` |
| input_identity.json | 19683 | `82d1605ecc03a62439b00cb3af1cca15bd6767c0fb881e79de0d73822e15bc20` |
| pair_summary.json | 218 | `222b832ec5f7580a35961d9ab8e30751568d838ceabfa2a53c36127d814ad7a3` |
| preflight.json | 20379 | `3d8eb80af3ccc020f644b845097e04800c9e5399e042d3387c003a5fdf3bf196` |
| review.json | 147 | `062775e3ded08ad7f12b465738978041fcf402384b4a2d55937b23391ef3074b` |
| shift_summary.json | 13140 | `6dd5551c71465a9f570b61d85e453c859737b6570b6503f16eac4099ee55e06d` |

## Verification and stop

All existing B7 tests are rerun after artifact/status updates; exact evidence is test_results.json. Source/tests/notebooks, original and supplemental conditions, prior results and U09 input remain byte-identical to Producer. Implementation release memberships remain exact, with dependent doc/status hashes refreshed only. U09 implementation Producer is unchanged. No Calendar/SLTP/execution semantics changes.

U10 performance/overlap/removals/retention/E0/E1/E2 metrics/post-E2 gates not evaluated. U10/U10-P/Candidate Freeze/Validation/Monitor NOT_RUN; main/B6/EA/SET/VPS/live unchanged. No further implementation is authorized by this Result Freeze.
