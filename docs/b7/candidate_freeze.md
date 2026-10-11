# B7 Candidate Freeze

## Candidate Freeze — 2026-10-11

Candidate set frozen before any U11 performance is opened.

CandidateFreeze=COMPLETE_CANDIDATE_FREEZE_FROZEN; CandidateFreezeExecuted=true; CandidateFreezeResultFrozen=true; U11InputPrepared=true. All40 formal PASS_U10P Candidates are the immutable set. No ranking, replacement, removal, addition, event regeneration or mode reselection. AUDUSD0 remains0. P0/P1/P2/P3=37/2/1/0; P1 GBPUSD Rank4/Rank7 and P2 GBPAUD Rank2 only. Every candidate is a formal U11 subject, with no retrospective reference-only exclusions or preferential treatment.

Source is research_inputs/b7/candidate_freeze_selected40_input.json at U10-P Result Freeze e0c57c8815d7f49c158585218fe5300bda699f95, SHA256 ceacffaaf085cb3470b28548328315dfed9d817e53f368043f54b3583017b328, Bytes254958. It is unchanged. Its CandidateFreezeExecuted=false describes the historical projection snapshot. Current completion is recorded separately in Candidate Freeze artifacts and run_status.json; the source flag is not mutated.

The containing Candidate Freeze commit is the formal Git identity and future Validation Source of Truth. U11 implementation must bind that actual commit as its exact source/ancestor. research_inputs/b7/u11_validation_selected40_input.json preserves the Candidates array with recursive typed exact equality and exact order. Its frozen U11 object is an exact copy of full_research_prespec.json U11. There is no future/self-referential commit SHA. Inventory and contract hashes, source SHA, ordered candidate/object/mapping/baseline fingerprints, producer and calendar lineage are bound.

All original fields, schedule/SL/TP/weekday/DOM/month/U09/Event E2/Protection, provenance, spread/pip size and execution semantics remain fixed. SelectedModeDiscoveryMetrics is the Discovery baseline; specifically its MaxDDPips supplies the future Validation DD comparison. Never fall back to P0 or another stage. SelectedModeTradeStreamSHA256 is bound for all40. No stream uniqueness gate is added.

Validation period [2024-01-01, 2026-01-01) JST remains blind. RetentionGateAdded=false; RescuePASSAllowed=false; PostValidationRetuningAllowed=false. No partial/winner-only ranking or pair replenishment; future U11 must evaluate all40. Later different hypotheses require a Separate Research ID. Monitor [2026-01-01, 2026-09-10) JST is OBSERVED_ONLY for formal Validation PASS only, with no Validation override.

Chronology: Stage1 → U06 → U07 → U08 → U09 → U10 → U10-P → Candidate Freeze → U11 Validation → Monitor. No actual M1 content or Validation/Monitor performance was read/generated in Candidate Freeze. Structural/identity/mutation tests only are added; existing synthetic tests remain unchanged. U11ImplementationAuthorized=false; U11ExecutionAuthorized=false; U11Executed=false; ValidationPerformance=NOT_RUN; MonitorPerformance=NOT_RUN. Stop pending Separate B7 U11 Validation Implementation Only instruction. See docs/b7/candidate_freeze.md and results/b7/candidate_freeze.

## Immutable set and provenance

Source: `research_inputs/b7/candidate_freeze_selected40_input.json`; SHA256 `ceacffaaf085cb3470b28548328315dfed9d817e53f368043f54b3583017b328`; Bytes254958. Producer `dc12531b559aaa7a821626e4813a2d291125efe4`. U10-P input SHA256 `7bce58b58102be11d8fe2debe4212b47a52cc685d10b044a9f7663e5b0bad11f`. Event Calendar SHA256 `7a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb`; CalendarSourceCommit `173be2a114dad6bd183a0a1515581528850f0850`. All40 U10PStatus=PASS_U10P and FormalEventMode=E2. Source/array order retained, unique40, no missing/extra/duplicates.

| Pair | Count |
|---|---:|
| AUDJPY | 4 |
| AUDUSD | 0 |
| EURAUD | 7 |
| EURJPY | 8 |
| EURUSD | 5 |
| GBPAUD | 5 |
| GBPJPY | 8 |
| GBPUSD | 2 |
| USDJPY | 1 |

| CandidateID | Protection |
|---|---|
| `B7S1:GBPAUD:SHORT:MON:E1200:D1:X0370:H0610` | P2 |
| `B7S1:GBPUSD:LONG:TUE:E0365:D0:X1120:H0755` | P1 |
| `B7S1:GBPUSD:LONG:TUE:E0370:D0:X1180:H0810` | P1 |

Other37 P0; P3 zero. Immutable fields: CandidateID, Symbol, Direction, PairRank, AnchorWeekday, FormalEntryMinute, FormalExitDayOffset, FormalExitMinute, FormalHoldingMinutes, FormalSL, FormalTP, FormalWeekdays, FormalDOMBuckets, OFFBuckets, FormalMonths, OFFMonths, CalendarFreeze, EntryShiftMinutes, ExitShiftMinutes, U09Decision, FormalEventMode, E2EventSet, EventCalendarSHA256, CalendarSourceCommit, FormalProtectionMode. Every additional original source field is also retained exactly. Spread/pip sizes and execution rules remain bound through unchanged full prespec InheritedEnvironmentAndExecution and the SHA-pinned Stage0 protocol.

Provenance fields retained recursively: U06SourceIdentity, U07SourceIdentity, U08SourceIdentity, U09CandidateSHA256, U09CheckpointSHA256, U09ProducerImplementationSHA, U10CandidateSHA256, U10CandidateObjectSHA256, U10CheckpointSHA256, U10ProducerImplementationSHA, U10PCandidateSHA256, U10PCheckpointSHA256, U10PProducerImplementationSHA, U10PConfigSHA256, DataManifestSHA256, EventCalendarSHA256, CalendarSourceCommit, E2TradeStreamSHA256, SelectedModeTradeStreamSHA256. Selected Discovery metrics include full annual2020–2023 schema; floats remain unrounded. Only schema/identity auditing occurred.

## Fingerprints

- CandidateSetSHA256: `0fc2a24c248057bf4b7fa5ba1b9413cbb49725bead885372d8f3104c67d432d5`
- ProtectionMappingSHA256: `7a2097c0de2db8cfa27b5da54867af4ecd0bbf3ac002ec81dd92de3cdd196ee6`
- ScheduleMappingSHA256: `f58977252feedd00b32122ed31cf076ff91221e93c2c7b73f02a2e367d340d62`
- DiscoveryBaselineSHA256: `00abcf9491b6b275da0204be5444c0a1973557fbd4c976c4de61ab84b85fb40c`
- SelectedStreamMappingSHA256: `eb1e8057df483fbb86536c0be62448c38898f27792f605e34bd0665955ac0192`
- EnvironmentExecutionSHA256: `37cac03494b06353b47e0a33d289d4d7fca35ffb1628b2090bec9e9f1bad4dee`

40 individual CandidateObjectSHA256 values are stored in inventory, separately from U10P candidate-file hashes. Protection map and full fixed-field schedule map use CandidateID keys; ordered candidate-set hash additionally preserves array order. Existing stage1_contract.object_hash canonicalization is used.

## Exact U11 contract bind

The following object is copied exactly into u11_contract.json and FrozenU11Contract; it is not an evaluator and no Candidate validation status is assigned.

```json
{
  "ValidationPeriod": "[2024-01-01, 2026-01-01) JST",
  "ImmutableCandidateFreezeRequired": true,
  "SampleAllRequired": {
    "Trades2024Min": 30,
    "Trades2025Min": 30,
    "CombinedTradesMin": 70,
    "Losses2024Min": 5,
    "Losses2025Min": 5
  },
  "FormalPASSAllRequired": [
    "2024 TotalPips > 0",
    "2025 TotalPips > 0",
    "Combined AvgPips > 0",
    "Combined PFpips >= 1.10",
    "Validation MaxDDPips <= Discovery MaxDDPips * 1.50"
  ],
  "RetentionGateAdded": false,
  "DiagnosticsOnly": [
    "Discovery-to-Validation AvgPips retention",
    "PF change",
    "TotalPips change",
    "MaxDD change",
    "WinRate",
    "annual/monthly metrics",
    "WinnerToLoser/Giveback",
    "E2 removed trades",
    "Protection activation count",
    "Other predefined diagnostics"
  ],
  "Statuses": {
    "PASS": "Sufficient sample and all formal conditions PASS",
    "FAIL": "Sufficient sample and one or more formal conditions FAIL",
    "INSUFFICIENT_SAMPLE": "Any sample condition not met"
  },
  "RescuePASSAllowed": false,
  "PostValidationRetuningAllowed": false,
  "FutureDifferentHypothesis": "Separate Research ID, not B7",
  "Monitor": {
    "Eligible": "Formal Validation PASS only",
    "Period": "[2026-01-01, 2026-09-10) JST",
    "Status": "OBSERVED_ONLY",
    "OverrideValidationAllowed": false
  }
}
```

Discovery DD baseline: SelectedModeDiscoveryMetrics.MaxDDPips. Retention and predefined diagnostics cannot change formal status. Sample and PASS conditions are bound only, not tested on actual2024/2025 data.

## U11 input only

Path: `research_inputs/b7/u11_validation_selected40_input.json`. SHA256 `0a9db7f5d65191cd88153199470034a78286880920960442b9e300d0fbb18ed4`; Bytes257887; object SHA256 `b0ad97127368ec624f4c29cc3be711d3fa35d04d263da4950fd92355e8b95ec8`. Candidates exact typed recursive equality and exact order. No candidate field added/removed/modified; no rounding. CandidateCount40, pair/mode counts exact, all selected mode baselines/streams and provenance retained. ValidationPerformanceEvaluated=false; MonitorPerformanceEvaluated=false; CandidateSetImmutable=true; RescuePASSAllowed=false; PostValidationRetuningAllowed=false.

## Verification and boundary

Dedicated structural tests cover source hash, missing/extra/duplicate/order, all field retention, unrounded baseline equality, SHA schema, contract/flags, exact mapping, deterministic replay, source unchanged, and mutation rejection. A fresh-process trap permits only candidate_freeze/stage1_contract modules and six pinned JSON/docs paths; any other B7 loader/Engine/event/protection/metrics/WTL/MFE/MAE/Gate/status execution or data read fails. Existing725 tests retain synthetic performance fixtures; no actual M1 content or Validation performance is produced. Final all-B7 totals are in test_results.json.

Prior code/tests/notebooks, all existing inputs, conditions, calendar, Stage1/U06/U07/U08/U09/U10/U10-P Result artifacts remain byte-identical. Only new Candidate Freeze module/tests, artifacts/U11 input/docs/status and dependent release-manifest SHA256/Bytes refresh are changed. Prior manifest memberships and non-file metadata remain fixed. No main/B6/live/EA/SET/VPS/forward/portfolio/Global R2 changes.
