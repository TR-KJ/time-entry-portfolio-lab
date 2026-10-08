# B7 Source of Truth

Repository: TR-KJ/time-entry-portfolio-lab. Independent local clone; no user checkout modified. Branch: `research/b7-pips-first-recent-era-time-entry-rediscovery`, based on main `1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5`. B6 read-only source: `research/b6-recent-era-time-entry-rediscovery` at `7ac8f554970fbc19d758f52151dd948e3a67d9fa`. GitHub API and fetched Git objects were used, not an inferred branch snapshot. No AGENTS.md in the audited B6 tree. `repository_refs.json` records 37 remote branches plus origin/HEAD alias. Source file identities and scoped inventories are in `source_manifest.json`.

## Reference scope and permitted reuse

B6 source_of_truth,plan,decision register,Stage0–11 documents, source/test/notebook and frozen-input/result trees were inventoried. The infrastructure audit examines historical execution,calibration,data isolation,PF labels,hash/freeze methodology,event/Validation policies and later money/R2 boundaries. Existing28→27 excludes22 as an operational decision; B7 does not alter or reproduce that selection. The reference inventory is not a B7 candidate input. B6 final candidates, frozen selections and performance are not loaded into B7 audit/calibration functions, and no B7 discovery ranking is implemented.

Main `src/research/daily_stop_baseline_revalidation.py` SHA256 `08b9717a3a94a0066e7ef7ebfa0f4802cbc84ae0570c3b875d96729877f4e216` is the execution/MT5-parser reference. It has a main guard. Old portfolio modules with execution side effects are not imported. Baseline's frozen calendar source is commit `173be2a114dad6bd183a0a1515581528850f0850`; no event data is downloaded or corrected in Stage0. B6 Candidate C matrix and per-strategy exceptions are not B7 event policy.

B6 Stage0 `round5` and `calibrate` function bodies are copied exactly into B7 calibration; no result-driven multiplier change. `discovery_view`/`validate` bodies are likewise inherited. Nine-symbol pip constants are used. `reference/b6_execution.py` is byte-identical to B6; private synthetic/reference adapters add only EU/GU symbol constants and the user-fixed spreads. This is compatibility evidence, not a Stage1 executor or Pure Time implementation.

B6 expected M1 manifest is byte-identical to the C1/A3 and Phase5 inventory, SHA256 `8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f`; its 56 expected identities are kept separately. B7's72-row inventory is measured, not a guessed expansion. Phase5/R2 sources at `5e93a8834e27d4d9ffdbc2980906511f74ddb27a` are audit-only; their OANDA New York server-clock context does **not** establish the historical M1 broker and does not replace B6 Helsinki conversion. B7 does not run money/R2.

## Research Data Collection and provenance limitations

Read-only synchronized Google Drive location: `ゆうのすけさん2025/再現性100%/<currency:currency>/MT5データ/` and its `1分足/` subfolder. Exact source folders are recorded without personal absolute paths in `input_audit.csv`. All9 pair exports share the MT5 tab-separated schema; this does not prove broker equivalence. B01 reassessment (2026-10-05) accepts the user-supplied concrete Sep9 acquisition record: the data-export MT5 was Dell Inspiron OANDA DEMO and the eight named 2026Apr–Sep RECHECKs were acquired in that workflow. Their exact-file modification sequence corroborates the record. This supersedes the earlier vague Forex/FXCM recollection for that scope. User research decision: apply the same provenance standard to all nine pairs. Adopt the audited, SHA256-frozen 72 M1 files as the formal Research Data Collection; historical broker identity is not independently certified for every file of the existing seven pairs either. This is acceptance with known limitations, not new broker certification. See b01_provenance_review.md and provenance_evidence.json.

Search for existing EU/GU audit evidence covered all37 fetched branch tips in docs/research_inputs/results/src/research plus8 identifiable Drive M1/input/manifest records. No EURUSD/GBPUSD matching formal audit was located. This is a bounded search finding, not proof no deleted/inaccessible historical record exists. Hence EU/GU undergo a new technical audit; no previous formal audit PASS is reused by filename/coverage alone.

81 actual M1 CSVs were inspected in the source tree;72 are inventory-selected (9×8),9 alternate exports remain excluded. EU/GU ordinary2026Apr–Sep exports contain a144-day gap. All original timestamps/OHLC are an exact subset of their respective RECHECK exports; RECHECK has additional actual rows. Select the complete RECHECK file **without merging,interpolation or cross-source filling**. Both versions' hashes/rows/endpoints and subset diagnostics are retained. Initial code incorrectly required a contiguous prefix; diagnosis showed exact timestamp subsets instead. This was an integrity-check correction before accepting data, not a rule changed after PnL. No PnL was computed.

**B01 = CLEAR_WITH_LIMITATION; Stage0 = PASS_WITH_PROVENANCE_LIMITATION; DataIntegrity = PASS; BrokerIdentity = HISTORICAL_NOT_FULLY_CERTIFIED.** The audited, SHA256-frozen 72 M1 files are the formal B7 **Research Data Collection**. This adopts the same research provenance standard for EU/GU and the existing seven pairs; it does not independently certify broker identity.

Known limitations and binding restrictions:

- Historical segment broker names are not fully independently certified for all nine pairs.
- Concrete records support the eight 2026 Apr–Sep RECHECKs acquired through Dell Inspiron OANDA DEMO MT5; this evidence is not automatically extended to historical/Q1 or GA.
- No explicit evidence of different-broker mixing has been confirmed.
- After seeing results, source replacement, data reacquisition and filling are prohibited. The exact 72 files and manifest stay frozen.

**Stage1MayStart = true AFTER_STAGE1_CONDITIONS_FREEZE.** Research conditions are now fully frozen under the subsequent full conditions Freeze. This is still not implementation/execution authorization: execution authorization remains false; the subsequent implementation-only instruction authorizes implementation, not the formal sweep. Provenance research judgment and limitations are unchanged.

## Reproduction and audit limitations

Use Python3.12.14 / NumPy2.3.5 / pandas2.2.3 as recorded in environment.json (the actual interpreter version is authoritative). Stage0 only:

```sh
PYTHONPATH=src/research PYTHONDONTWRITEBYTECODE=1 python -m b7.stage0_audit --data-root "$B7_DATA_ROOT"
PYTHONPATH=src/research PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p 'test_b7*.py' -v
```

`B7_DATA_ROOT` is the existing `再現性100%` directory. Inputs read in place. Review aggregate gaps carefully: counts include weekends and holidays; no exchange-session calendar is used to classify every gap as missing expected trading data. The price precision tolerance is a formatting diagnostic only, never an execution hit epsilon. Full-nine/all-segment broker attribution remains unresolved; the eight2026 RECHECKs now have scoped OANDA acquisition support. Timestamp interpretability under Helsinki does not prove the export's original timezone. Candidate PnL/Validation/Monitor are never produced by the audit CLI.

The original projectless directory refused shell writes even after a filesystem grant. A fresh isolated temporary clone was used; no pre-existing checkout was changed. This does not affect scientific identity, which uses Git/file hashes, not personal paths. Audit artifacts are published only under B7 paths.

The row-level calibration diagnostics are gzip-compressed to keep publication compact; they contain dates/counts/status only, not M1 prices. GitHub publication uses the connected GitHub API when local Git transport authentication is unavailable.

## P01/P02/U01–U05 formal conditions Freeze

The user has formally frozen P01/P02/U01–U05 as AGREED/FROZEN. `stage1_conditions_freeze.md` preserves the full agreed specification; `research_inputs/b7/stage1_prespec.json` records the official SL grids, numeric semantics, Pure Time/SL gates, Plateau, family/fixed-key and PF semantics. Original proposal/calibration artifacts remain historical snapshots; their numeric values are unchanged and are now formally adopted.

The partial Freeze above is preserved as historical evidence. The subsequent full Freeze formally adopts U06–U12 and U10-P without changing P01/P02/U01–U05. Current authoritative artifacts are `full_research_conditions_freeze.md` and `research_inputs/b7/full_research_prespec.json`; both reference the prior immutable artifacts and hashes.

Stage1ConditionsFrozen = true; Stage1ImplementationAuthorized = true under the separate implementation-only instruction; Stage1ExecutionAuthorized = false; Stage1MayStartNow = false. No new performance result is opened. The current full protocol supersedes historical pending/authorization fields, not underlying provenance evidence. The current run_status.json is authoritative for authorization. B01/Stage0 and all source limitations remain unchanged.

## Stage1 Implementation Only release

The explicit subsequent user instruction authorizes Stage1 engine/tests/bounded compatibility smoke/notebook/runtime infrastructure only. See stage1_implementation.md and results/b7/stage1_implementation. Status is FROZEN_READY_FOR_CHAT_REVIEW after checks. Formal execution still requires a separate Chat confirmation and Colab barriers; the historical full-prespec authorization fields record their original Freeze, while run_status.json and stage1_runtime_config.json record the current implementation-only authorization. No research conditions or old Freeze artifacts changed.

## Completed90-job Finalize-Only implementation

The user reports that the Colab full sweep completed90 jobs and a validated checkpoint backup was saved before finalization finished. This subsequent Work implements recovery only; the real backup and candidate results have not been accessed. See stage1_finalize_only.md. Original producer is abe588cf14c225f1cc8f9f991700fbe815618cc2 with Python3.13.15. The new dedicated finalizer allows Python3.13 patch differences only, while normal resume remains byte-identical and exact-identity only. Stage1FinalizeOnlyImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; Stage1FinalizeOnlyExecutionAuthorized=false. Research conditions, B01 and Stage0 remain unchanged.

## Stage1 Result Freeze — 2026-10-06

The actual Drive archive `/MyDrive/b7_stage1_finalize_20261006` passed COMPLETE, manifest, ZIP-member, identity and selection consistency checks. Stage1 is `COMPLETE_STAGE1_ONLY_FROZEN`; Stage1ResultFrozen=true and Stage1ExecutionComplete=true. The verified archive records completion of 90 source jobs, 7,335,360 structures, 44,012,160 variants, 12,638 families and 72 selected representatives (8 per pair). Full authoritative selected JSON remains hash-fixed in Drive; see `research_inputs/b7/stage1_selected_top8.reference.json` and `docs/b7/stage1_result_freeze.md`. Earlier pending/user-reported entries are historical and superseded by this actual-archive audit. No research conditions, code, tests or data changed. U06 onward and Validation/Monitor remain unexecuted and unauthorized by this task.

## U06 Implementation Freeze

U06 SL/TP implementation, reference/optimized replay, input extraction, notebook and synchronous per-candidate Drive checkpoints are frozen for Chat review. The explicit user endpoint supplement fixes nearest5-pip half-up at both ±20% endpoints; SL alone retains its3-point minimum extension. See `docs/b7/u06_implementation.md` and `research_inputs/b7/u06_config.json`. The full selected input and original checkpoint hashes yielded72 exact representatives with verified official five-SL metrics in `research_inputs/b7/u06_selected72_input.json`. This is Stage1 result extraction, not new U06 performance. U06ConditionsFrozen=true; U06ImplementationAuthorized=true; U06ImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; U06ExecutionAuthorized=false; U06Executed=false. U07+, Candidate Freeze, Validation/Monitor remain unexecuted. Original research-condition and Stage1 result commits/files remain unchanged.

## U06 Finalize-Only Implementation Freeze

A separate completed-Drive-checkpoint finalizer pins Producer `14e43b7b1307492a07b8653e8de9263b37cb02a9`. It audits exactly72 frozen CandidateIDs and217 trusted source files, accepts only matching Python major.minor with exact NumPy/pandas, and never loads M1 or recalculates a candidate. Existing U06 runner/evaluator/selection/config/input remain byte-identical; ordinary resume remains exact-environment. See `docs/b7/u06_finalize_only.md`. U06FinalizeOnlyImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; U06FinalizeOnlyExecutionAuthorized=false; U06ExecutionAuthorized=false; U06Executed=false. Tests use synthetic outputs only. No actual U06 checkpoint or formal SL/TP results were accessed.

## U06 Result Freeze — 2026-10-07

Actual Drive archive `/MyDrive/b7_u06_20261007_01_archive` and all72 jobs under `/MyDrive/b7_u06_20261007_01_checkpoints` passed COMPLETE, manifest, every ZIP-member, exact producer identity and checkpoint hash audits. Stage1 input72 yielded PASS_U0656 and DROP_U06_SL16; NoReplacement=true. U06 is COMPLETE_U06_ONLY_FROZEN, U06ResultFrozen=true and U06ExecutionComplete=true. Formal run producer is14e43b7b1307492a07b8653e8de9263b37cb02a9 under Python3.13.16/NumPy2.3.5/pandas2.2.3. Earlier unexecuted U06 statements describe implementation-only history and are superseded by this verified result. `research_inputs/b7/u07_selected56_input.json` freezes only the56 PASS schedules and Formal SL/TP with exact source hashes; it does not execute or authorize U07. See `docs/b7/u06_result_freeze.md`. Research conditions, Stage1 results and evaluator/selection code remain unchanged. U07+, Candidate Freeze, Validation/Monitor remain NOT_RUN.

## U07 Implementation Freeze — explicit Best tie supplement

U07 Weekday ON/OFF and Finalize-Only are implemented for Chat review. Exact U06 Result Freeze `c526dc1bb49d168376e5cb4858174524c0a63f7a` supplies56 PASS candidates with input SHA256 `fbb78686e8a767bb8fbaa903e9b89eee99d9c856b2182d29f1953bb51273fe39`. Anchor is frozen Schedule.Weekday; no replacement. The explicit user supplement fixes Best ranking to MedianAnnualAvgPips DESC, PositiveYearCount DESC, W3 > W2 > W1 > W0. Existing Plateau/final selection rules and original conditions artifacts remain unchanged. See `docs/b7/u07_implementation.md` and `research_inputs/b7/u07_config.json`. U07ConditionsFrozen=true; U07ImplementationAuthorized=true; U07ImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; U07ExecutionAuthorized=false; U07Executed=false. FormalWeekdays/Drop results are not produced or viewed; U08+, Candidate Freeze, Validation/Monitor remain NOT_RUN. This replaces only the earlier U07 implementation-authorization status. U06 results,56-input bytes and Stage1/U06 code remain unchanged.

## U07 Result Freeze — 2026-10-08

Actual Drive `/MyDrive/b7_u07_20261007_01_archive` and all56 jobs under `/MyDrive/b7_u07_20261007_01_checkpoints` passed COMPLETE/manifest/ZIP and exact producer/environment/data-metadata/job-hash audits. Producer is9adeef8514fb76efec70a2cc46ce85e306ea0597, Python3.13.16/NumPy2.3.5/pandas2.2.3. U07 is COMPLETE_U07_ONLY_FROZEN; U07ResultFrozen=true; U07ExecutionComplete=true. PASS_U07=56, DROP=0; Anchor CORE56/56;55 anchor-only and one EURAUD rank4 Mon/Tue/Wed. Canonical SetName is a deduplicated label, not the active weekday count. All280 diagnostics and224 non-anchor diagnostics are frozen observations only; no research-rule change follows. `research_inputs/b7/u08_selected56_input.json` is the exact PASS56 projection with fixed schedules/SL/TP/Anchor/FormalWeekdays and source hashes. See `docs/b7/u07_result_freeze.md`. Earlier U07-unexecuted statements describe implementation history and are superseded by this audited result. U07ExecutionAuthorized=false; U08ImplementationAuthorized=false; U08+ and Candidate Freeze/Validation/Monitor remain NOT_RUN. No performance recalculation or weekday reselection occurred.
