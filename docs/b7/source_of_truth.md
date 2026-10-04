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

**Stage1MayStart = true AFTER_STAGE1_CONDITIONS_FREEZE.** Stage1 conditions are not yet frozen; Stage1 must not start now. All existing condition-freeze requirements in the Decision Register remain unchanged. This update changes only the provenance research judgment.

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

This is a partial pre-implementation conditions Freeze. U06–U12 remain UNDECIDED; U12 runtime/resume/artifact/Colab contract has not been frozen. Stage1MayStartNow remains false. This request authorizes documentation/config only, with no new performance reads or execution. B01 and Stage0 status and all provenance limitations remain unchanged.
