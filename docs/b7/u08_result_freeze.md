# B7 U08 Result Freeze

Status: COMPLETE_U08_ONLY_FROZEN. U08ResultFrozen=true; U08ExecutionComplete=true; U08Executed=true; U08ExecutionAuthorized=false. U09ImplementationAuthorized=false; U09Executed=false; NoReplacement=true.

## Identity and audit

Run:b7_u08_20261008_01. Archive:`/MyDrive/b7_u08_20261008_01_archive`. Checkpoint:`/MyDrive/b7_u08_20261008_01_checkpoints`. Producer:`0b33aa5ff6ff769b11212e9b8593242fb71c680c`. U07 Result Freeze:`21140269596584575677421934399122614f6cd6`. Conditions:`5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`. U08 input SHA256:`7c49b9cd0374b57f4da78eb784aa646050cba507b0ff037e303085a61deb7616`.

Producer environment:Python3.13.16,NumPy2.3.5,pandas2.2.3. Exact identity covers config,full prespec,U08 input,M1 manifest,all72 M1 metadata records and ordered56 CandidateIDs. This audit reads saved artifacts only, without M1 content reads or candidate/performance/selection recomputation. Archive preflight records397 tests PASS; bounded actual smoke48 trade cases,8 full fixed-schedule replays,D1/D2/D3,months1/2,12 LOMO cases per replay. Formal56Used/FormalCalendarProduced/PerformanceSaved/FullSearch=false.

COMPLETE manifest/review hashes PASS. Every manifest Path/SHA256/Bytes PASS. ZIP exact inventory and all member hash/size/CRC comparisons PASS. All56 actual Drive jobs and169 trusted files PASS: no missing/extra/duplicate jobs, exact CandidateID/identity/IdentitySHA256/candidate/checkpoint/DRIVE_COMPLETE hashes and terminal schema. Archive candidates and checkpoint audit match Drive exactly. Source unchanged after audit. Trusted-file aggregate SHA256:`9307720d565a1272b44d020ba3c20e5e43325871ac0cbc7cc3797d63ffe57e4a`.

## Independent recounts

| Pair | PASS_U08 | DROP |
|---|---:|---:|
| AUDJPY | 8 | 0 |
| AUDUSD | 7 | 0 |
| EURAUD | 8 | 0 |
| EURJPY | 8 | 0 |
| EURUSD | 6 | 2 |
| GBPAUD | 6 | 0 |
| GBPJPY | 8 | 0 |
| GBPUSD | 2 | 0 |
| USDJPY | 1 | 0 |

Total56:PASS54,DROP2. DOM0=54,DOM1=2,DOM2=0; DOM Final Gate PASS54. All54 PASS have DOM0,active[D1,D2,D3],OFFBuckets=[]. No surviving DOM filter.

### DROP details

- `B7S1:EURUSD:SHORT:TUE:E1375:D1:X1270:H1335`; EURUSD rank5; DOM1 with D1 OFF; final Trades=137; failed checks:TotalTrades. Annual Trades2020–2023:[34, 34, 34, 35]. All gate checks and stored metrics are preserved in u08_result_summary.json.
- `B7S1:EURUSD:LONG:TUE:E0365:D0:X1195:H0830`; EURUSD rank8; DOM1 with D1 OFF; final Trades=136; failed checks:TotalTrades. Annual Trades2020–2023:[34, 34, 33, 35]. All gate checks and stored metrics are preserved in u08_result_summary.json.

Both DOM1 Sequential Adoption comparisons passed all five checks, but the adopted DOM failed U01Equivalent final sample gate. No DOM0 fallback; neither candidate entered Month/Calendar or U09; no replacement.

### Month

Evaluated54. M0=17,M1=27,M2=10. OFF count0=17,1=27,2=10. Thus37/54 adopt a month filter, with47 total month-stops. Month OFF frequency Jan–Dec:24,6,7,0,0,2,6,0,1,0,1,0.

OFFMonths lists below retain source ranking/adoption order; none are numerically resorted.

| OFFMonths | Count |
|---|---:|
| [] | 17 |
| [1] | 17 |
| [1, 3] | 5 |
| [6] | 1 |
| [9] | 1 |
| [2] | 6 |
| [7, 1] | 2 |
| [11, 7] | 1 |
| [7, 3] | 1 |
| [7] | 2 |
| [3, 6] | 1 |

| Pair | OFFMonths × count |
|---|---|
| AUDJPY | [] ×2; [1] ×6 |
| AUDUSD | [1, 3] ×2; [1] ×5 |
| EURAUD | [1] ×3; [1, 3] ×3; [] ×1; [6] ×1 |
| EURJPY | [] ×2; [9] ×1; [2] ×5 |
| EURUSD | [7, 1] ×2; [11, 7] ×1; [7, 3] ×1; [] ×1; [7] ×1 |
| GBPAUD | [] ×3; [1] ×3 |
| GBPJPY | [] ×8 |
| GBPUSD | [3, 6] ×1; [7] ×1 |
| USDJPY | [2] ×1 |

GBPJPY8 all have no month OFF; AUDUSD7 all have month OFF; EURUSD loses2 candidates. January OFF24 and other observations authorize no sample/gate/ranking/pair-specific rule changes, fallback, third OFF month, return to U07/SL/TP, or replacement.

## Calendar and comparison boundaries

PASS54 CalendarFreeze exactly contains FormalWeekdays,FormalDOMBuckets,OFFBuckets,FormalMonths,OFFMonths. FormalWeekdays equals U07; FormalDOMBuckets=[D1,D2,D3],OFFBuckets=[]; FormalMonths is the exact active-month complement and OFFMonths keeps source order. No return to Weekday/DOM/Month after U09/U10/U10-P.

There is a DOM final U01Equivalent gate and no Month final U01 gate. All54 DOM passes remain PASS_U08 after Month; no new gate was applied in this Freeze. Exact Producer config hash binds PF strict improvement to both states FINITE and candidate>baseline; INF/UNDEFINED comparisons are false, PF<1 OFF requires FINITE (zero allowed). Median strict improvement requires both non-null and candidate>baseline; null comparisons are false. No alternative three-year median/sample gate was created.

## U09 exact input projection

`research_inputs/b7/u09_selected54_input.json`: SHA256 `8faa886c3d1a72e8020688b8931481d81d1df637d63b0b368e0171b8d1dce2ca`, Bytes 99948. Exact ordered54 PASS only, NoReplacement=true, excluding EURUSD ranks5/8. Fields retain CandidateID,Symbol,PairRank,Schedule and explicit Direction/EntryMinute/ExitMinute/ExitDayOffset/HoldingMinutes,FormalSL/TP,AnchorWeekday,FormalWeekdays,canonical SetName,FormalDOMBuckets/OFFBuckets/FormalMonths/OFFMonths,CalendarFreeze,U08Status,U07/U06 source identities,candidate/checkpoint hashes,Producer SHA; top-level source Archive ZIP/manifest/result/identity hashes bind origin.

U09 may change only Entry/Exit±5 minutes in1-minute increments under the existing frozen contract. Pair/direction/SL/TP/weekday/DOM/month remain fixed; no Calendar return. This task performs no U09 implementation or performance evaluation.

## Storage and immutable hashes

candidate_results.json and archive.zip stay in Drive with path/SHA256/Bytes frozen. Ten small formal artifacts are copied byte-identically; review.json is named u08_review.json. Original artifact_manifest retains Archive-relative names; github_artifact_manifest binds repository copies.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| COMPLETE.json | 197 | `1bc84ac298001a0d52b939380a410b83ab3d68c80ff024f3df20c89f66ae46fb` |
| archive.zip | 376441 | `a435b887892e0f8107234dd4d1b9a5a64987bf98a33737b548ae2e79a0564e75` |
| artifact_manifest.json | 1081 | `33227a1ca651e76818d8865478e79627589f4487d29269054f438abf250c348d` |
| calendar_summary.json | 12690 | `211fb8d1a12ad0dd36f561f0fb7f343100fc43ddb50429bf70308602b0fe64b3` |
| candidate_results.json | 2301721 | `d46fa97f66e4ee642c057eecb212d1762ff6a947d550c3f13faf5070115d4d6f` |
| checkpoint_audit.json | 8230 | `a9fa293e76955149b1fec5c946206456a89380d514536912bcbcbc25745add18` |
| dom_summary.json | 58 | `ad84c3c2537e594a54726e3d8c7c8c88bca43df014dc787f0181c173bb4be385` |
| input_identity.json | 19597 | `f9e4de991db104f6a92ea0a64d9f4a7282e259ef4baede0772bfa48209205cc0` |
| month_summary.json | 159 | `2835f8a39efebdb3ae5d2864d06e4b3d6eee755ad986560776d679005b050dda` |
| pair_summary.json | 246 | `4079996ab0fc289012181bfbed975dc79e8f05f00cb6146d0a71e7dbcf47ee71` |
| preflight.json | 20380 | `b3568b75ac23abf979e5f292d6f2fe73044cf585d7f4a0731f8b3e5ccc422394` |
| review.json | 175 | `a2e722c4ebede183272f64bb840b29f53bfeff6c43b40344d59754de6f801a31` |

## Tests and stopping boundary

397 existing B7 tests PASS,0 failures/errors,0 skips (Work Python3.12.14/NumPy2.3.5/pandas2.2.3). Independent result consistency checks PASS. Production code,tests,notebooks,earlier inputs,conditions,Stage1/U06/U07 results are byte-identical to Producer; existing release memberships are unchanged, with dependent docs/status hashes refreshed.

U09 fine tune/plateau/anchor retention,U10,U10-P,Candidate Freeze,Validation,Monitor are NOT_RUN. Main/B6/EA/SET/VPS/live unchanged. Stop after U08 Result Freeze and U09 input projection; further implementation needs a separate instruction.
