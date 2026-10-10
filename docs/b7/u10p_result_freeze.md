# B7 U10-P Result Freeze


## U10-P Result Freeze — 2026-10-11

U10P=COMPLETE_U10P_ONLY_FROZEN; U10PResultFrozen=true; U10PExecutionComplete=true; U10PExecuted=true; U10PExecutionAuthorized=false. Actual Drive b7_u10p_20261010_01 archive and40 jobs/121 trusted files passed COMPLETE/manifest/ZIP/member-order/hash/size/CRC/byte-identity, Producer identity, environment, ancestry and unchanged-source audits. Producer dc12531b559aaa7a821626e4813a2d291125efe4, U10 Result488553634c3923f5ef561a7db777d1b0b2ff5796, U10-P input7bce58b58102be11d8fe2debe4212b47a52cc685d10b044a9f7663e5b0bad11f remain fixed. Independent saved-result recount: PASS_U10P40, DROP0, P0/P1/P2/P3=37/2/1/0, NoReplacement=true. Selected protection: GBPAUD Rank2 P2 and GBPUSD Rank4/Rank7 P1. P0 retention reasons: NO_PROTECTION_MODE_PASS35 and ALL_PROTECTION_MODES_NOT_APPLICABLE2. Applicability patterns TTT37/TFF1/FFF2. U01 failures P1/P2/P3 all0; N/A modes remain ineligible.

P0 barriers40/40, fixed trade universes, all160 mode stream/ID hashes, saved adoption checks and ranked-PASS inventory/selected first mode are consistent. Saved metrics and WinnerToLoser counts were audited/aggregated, never recomputed from trades. No M1 content read, E2 regeneration, MFE/MAE/Giveback computation, protection simulation, performance metrics recomputation or ranking reselection. Tests use synthetic fixtures only. See docs/b7/u10p_result_freeze.md and results/b7/u10p for full exact evidence.

All40 PASS_U10P records are exactly projected through unchanged project_candidate_freeze into research_inputs/b7/candidate_freeze_selected40_input.json. Every fixed input field is retained, plus selected mode/metrics/stream SHA, actual candidate/checkpoint SHA, producer/config/data identity. CandidateFreezeInputPrepared=true; CandidateFreezeExecuted=false; ValidationPerformance=NOT_RUN; MonitorPerformance=NOT_RUN. This is input preparation only. Earlier U10PExecuted=false statements describe implementation history and are superseded by this audited formal result.

P1 reduces WinnerToLoser to0 in the pair diagnostics, yet only GBPUSD2 records pass the frozen adoption rules. This observation does not authorize threshold relaxation, mode preference, P3 deletion, pair-specific changes or replacement. P1 .50R/0R, P2 .75R/.25R, P3 1R/.50R, next-existing-M1 activation, no same-bar rescue, SL-first and frozen TP remain unchanged. Entry/exit/holding/SL/TP/weekday/DOM/month/U09 fine tune/Event E2/protection mode are fixed; no return to Discovery after Validation. Stop pending separate Candidate Freeze instruction; U11 and Monitor remain unexecuted.

## Bound source identities

- ImplementationSHA: `dc12531b559aaa7a821626e4813a2d291125efe4`
- ConditionsFreezeSHA: `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`
- U09SupplementalConditionsFreezeSHA: `1466a2c3e8b3d523233c45d665a6cac21e974393`
- U10SupplementalConditionsFreezeSHA: `e34099b9c807df1f145f96ca92c2443fe552fa36`
- U10ResultFreezeSHA: `488553634c3923f5ef561a7db777d1b0b2ff5796`
- U10PConfigSHA256: `13a086a4f4bb7ec39cd9a6283f1858d72749669ff119eef87006f8f6d99d3d94`
- U10PInputSHA256: `7bce58b58102be11d8fe2debe4212b47a52cc685d10b044a9f7663e5b0bad11f`
- EventCalendarSHA256: `7a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb`
- CalendarSourceCommit: `173be2a114dad6bd183a0a1515581528850f0850`
- M1ManifestSHA256: `6bdead8061fcbe3cf792e9ea0e0dcd8f869057aa5a8fc78c572d23f4ae49d15a`

Archive: `/MyDrive/b7_u10p_20261010_01_archive`; checkpoints: `/MyDrive/b7_u10p_20261010_01_checkpoints`. Producer Python3.13.16 / NumPy2.3.5 / pandas2.2.3. Actual12 archive files and11 ZIP members verified. Full identity binds72 M1 metadata and ordered40 IDs/U10 candidate/checkpoint/object/E2 hashes. Formal preflight records725 tests PASS,16 bounded replays/56 E2 trades/224 mode-trades; all six formal/validation/monitor smoke flags false. Producer descends from U10 Result and U10 Supplemental; frozen U10-P contract matches the pre-existing full prespec.

40 completed jobs and121 trusted files; aggregate SHA256 `c455774a67670b6ed799357e213d3fa10b0616aca880708aa6b4baa784a1af5e`. Archive objects match Drive candidates in exact order; checkpoint audit exact. Source hashes unchanged before/after. No formal run/finalizer API called. Read-only audit verifies recorded producer environment, not the Work runtime; synthetic test environment is separately recorded.

## Counts and selected WinnerToLoser effect

| Pair | Candidates | P0 | P1 | P2 | P3 | P0 WTL | Selected WTL | Reduction | Fraction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AUDJPY | 4 | 4 | 0 | 0 | 0 | 34 | 34 | 0 | 0.0 |
| AUDUSD | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A |
| EURAUD | 7 | 7 | 0 | 0 | 0 | 23 | 23 | 0 | 0.0 |
| EURJPY | 8 | 8 | 0 | 0 | 0 | 83 | 83 | 0 | 0.0 |
| EURUSD | 5 | 5 | 0 | 0 | 0 | 8 | 8 | 0 | 0.0 |
| GBPAUD | 5 | 4 | 0 | 1 | 0 | 13 | 8 | 5 | 0.38461538461538464 |
| GBPJPY | 8 | 8 | 0 | 0 | 0 | 130 | 130 | 0 | 0.0 |
| GBPUSD | 2 | 0 | 2 | 0 | 0 | 14 | 0 | 14 | 1.0 |
| USDJPY | 1 | 1 | 0 | 0 | 0 | 10 | 10 | 0 | 0.0 |

## Selected3 exact persisted metrics

### GBPAUD Rank2 — P2

CandidateID: `B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610`. RankedPASSModes=['P2']; all AdoptionChecks true. WTL 8 → 3; reduction5; fraction0.625.

| Metric | P0 | Selected |
|---|---:|---:|
| MaxDDPips | 443.69999999999254 | 411.7999999999897 |
| MedianAnnualAvgPips | 16.677913968547777 | 17.140957446808653 |
| PFpips | 1.8344978310540216 | 2.0402689442122632 |
| PositiveYearCount | 3 | 3 |
| TotalPips | 2520.100000000034 | 2862.300000000034 |
### GBPUSD Rank4 — P1

CandidateID: `B7S1:GBPUSD:LONG:TUE:E0365:D0:X1120:H0755`. RankedPASSModes=['P1']; all AdoptionChecks true. WTL 7 → 0; reduction7; fraction1.0.

| Metric | P0 | Selected |
|---|---:|---:|
| MaxDDPips | 246.70000000000073 | 246.70000000000073 |
| MedianAnnualAvgPips | 10.708988095237142 | 11.029181184668015 |
| PFpips | 2.050666965586693 | 2.1279321544567473 |
| PositiveYearCount | 4 | 4 |
| TotalPips | 1874.5999999998367 | 1875.2999999998478 |
### GBPUSD Rank7 — P1

CandidateID: `B7S1:GBPUSD:LONG:TUE:E0370:D0:X1180:H0810`. RankedPASSModes=['P1']; all AdoptionChecks true. WTL 7 → 0; reduction7; fraction1.0.

| Metric | P0 | Selected |
|---|---:|---:|
| MaxDDPips | 395.50000000002194 | 369.60000000002094 |
| MedianAnnualAvgPips | 7.769494949494041 | 8.275454545453686 |
| PFpips | 1.5357722377931151 | 1.5777008419229783 |
| PositiveYearCount | 3 | 4 |
| TotalPips | 1452.799999999842 | 1468.399999999855 |

## Applicability and adoption

P0 retained37: NO_PROTECTION_MODE_PASS35; ALL_PROTECTION_MODES_NOT_APPLICABLE2. Applicability P1/P2/P3: TTT37, TFF1, FFF2; each agrees with finite TP <= triggerR×SL structural N/A. U01 failure counts P1/P2/P3=0/0/0, including N/A. N/A remains excluded. P1 PASS exactly GBPUSD Rank4/Rank7; P2 PASS exactly GBPAUD Rank2; P3 PASS0. RankedPASSModes inventory equals the PASS set and selected mode equals its first member (or P0 for empty); no reranking.

False AdoptionChecks on non-PASS modes (overlapping reasons, not additive candidate counts):

| Check | P1 | P2 | P3 |
|---|---:|---:|---:|
| Applicable | 2 | 3 | 3 |
| U01Equivalent | 0 | 0 | 0 |
| TotalPips | 34 | 31 | 29 |
| PFpips | 23 | 28 | 28 |
| MedianAnnualAvgPips | 30 | 24 | 25 |
| PositiveYearCount | 2 | 1 | 1 |
| MaxDDPips | 18 | 8 | 5 |
| ReductionCount | 12 | 33 | 40 |
| ReductionFraction | 8 | 19 | 32 |

## Pair × mode diagnostics

| Pair | Mode | WTL |
|---|---|---:|
| AUDJPY | P0 | 34 |
| AUDJPY | P1 | 0 |
| AUDJPY | P2 | 17 |
| AUDJPY | P3 | 28 |
| EURAUD | P0 | 23 |
| EURAUD | P1 | 0 |
| EURAUD | P2 | 19 |
| EURAUD | P3 | 21 |
| EURJPY | P0 | 83 |
| EURJPY | P1 | 0 |
| EURJPY | P2 | 52 |
| EURJPY | P3 | 73 |
| EURUSD | P0 | 8 |
| EURUSD | P1 | 0 |
| EURUSD | P2 | 8 |
| EURUSD | P3 | 8 |
| GBPAUD | P0 | 13 |
| GBPAUD | P1 | 0 |
| GBPAUD | P2 | 5 |
| GBPAUD | P3 | 9 |
| GBPJPY | P0 | 130 |
| GBPJPY | P1 | 0 |
| GBPJPY | P2 | 96 |
| GBPJPY | P3 | 113 |
| GBPUSD | P0 | 14 |
| GBPUSD | P1 | 0 |
| GBPUSD | P2 | 13 |
| GBPUSD | P3 | 14 |
| USDJPY | P0 | 10 |
| USDJPY | P1 | 0 |
| USDJPY | P2 | 9 |
| USDJPY | P3 | 10 |

## Future Candidate Freeze exact input only

SHA256 `ceacffaaf085cb3470b28548328315dfed9d817e53f368043f54b3583017b328`, Bytes254958. Exactly40 original-order unique PASS records, all fixed fields unchanged, mode counts37/2/1/0 and pair counts preserved (AUDUSD0). Each selected mode metric object and SelectedModeTradeStreamSHA256 is exact; all actual candidate/checkpoint/producer/config/data identities are bound. The containing Git commit identifies this Result Freeze without circular SHA. CandidateFreezeExecuted=false; ValidationPerformance=NOT_RUN; MonitorPerformance=NOT_RUN.

## Actual source artifact hashes

| File | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 198 | `27a0082d884aebb22098db62476ba5ae25c65a3d3388b5f23c395bf627fd8c9b` |
| archive.zip | 4086669 | `bec4573590af7e4d94e664dc8de0871acc0ec7d4e201de9ccdb4179dbc5b625a` |
| artifact_manifest.json | 1095 | `1803365132a91680084ac5b3c4cd4c41d34611659024a959237ad992569d2e9f` |
| candidate_results.json | 34537399 | `6ecb60257a900b2d0fcc6610bdbf55e9719256825695b4d337de993e2b14a3ca` |
| checkpoint_audit.json | 5892 | `519ba7f98066422dbc012d52d27011f94257b365fe8baf8c98d954dd292dc9da` |
| input_identity.json | 53700 | `6a48e0283231ecd781d3d220602018f6d5c3f5a1ec3e6770d9f5025f66014a01` |
| mode_summary.json | 3714 | `f748166740b78d0f33e21bb86800ce8ae91098677bc3d21486b4baad68f3bab5` |
| pair_summary.json | 202 | `62e08fc537c2f2a424d9c80f92251df498ccf2723cb7488a91008e57d12fb828` |
| preflight.json | 54533 | `f7f52a2c053663c16a6d1dbe17d78b8325bd8287844180ab2663f65d8ddd2c06` |
| protection_summary.json | 271 | `63405e91b4ac913a76a7918efaf8ef519d469dff727bce5ad5b61fb07b60606e` |
| review.json | 150 | `8be112ae236b6d26db7e51871dcf272f8266e9697a6b998b99a495bb888747a9` |
| winner_to_loser_summary.json | 873 | `b98b16488678a62d42ea58e3f2d6a99638508b182d232c3f2f0110f6726fc8b4` |

candidate_results and archive.zip remain in Drive, with exact path/hash/size bound; the other10 artifacts are byte-identical copies (review renamed). Source manifest retains original paths. Repository manifest binds all new outputs. Production source, tests, notebooks, prior results/inputs/conditions/calendar are byte-identical to Producer. Prior release memberships and metadata remain fixed; only existing dependent SHA256/Bytes refresh. No main/B6/EA/SET/VPS/live changes.

Tests Total725 / PASS725 / FAIL0 / ERROR0 / SKIP0. Work synthetic-test environment: {'Python': '3.12.14', 'NumPy': '2.3.5', 'pandas': '2.2.3'}. Formal results were not rerun.
