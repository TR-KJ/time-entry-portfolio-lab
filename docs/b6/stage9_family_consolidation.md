# Stage9 Candidate Family Consolidation & Final Candidate Freeze

Stage9 is a deterministic post-validation selection, completed in Work from the formal Stage8 Google Drive archive. It is not new validation, a pristine holdout, or live adoption. The source is the completed Stage8 runtime at `68d84078c2edc3108c0e3d6ca78d64d9b3d91ab5`. Stage8's nine-candidate pool and all 17 research PASS / OBSERVED records remain unchanged. The eight AUDJPY 07:01 candidates excluded for `WEEKLY_OPEN_EXECUTION_MODEL_RISK` are not reinstated.

## Formal input and hard gates

`stage9_source_spec.json` locks all 45 archive files by exact bytes SHA256, including identity/config, saved audits, progress/summary, candidate-period metrics, ledger, pairwise data, diagnostics, 20 matrices, checkpoints, nine shards, and review ZIP. `stage8_input_audit.json` records the synchronized formal root and all hashes. Review ZIP is inventoried only and is never scientific input. Source inaccessible, incomplete, mismatched or modified means stop without repair or recomputation.

The required state is `COMPLETE_STAGE8_OVERLAP_CORRELATION_ONLY`: source17, ineligible8, eligible9 (AUDJPY1 / GBPJPY8), 36 pairs, four periods, 144 pairwise rows and 36 candidate-period rows. OverlapCorrelationExecuted=true; FamilyConsolidationExecuted, PortfolioExecuted and LiveChanged=false; NoRanking, NoSelection and NoRetuning=true. Identity/config/pool/eligibility SHA, exact candidate order and conditions, saved M1 metadata, checkpoint hashes and matrix shape/order are audited. No M1 price file is read. Ledger and pairwise results are inventoried, never recalculated.

The only candidate performance source is the archive's `stage8_candidate_period_metrics.csv.gz`. `stage8_formal_evidence.json` is a machine-extracted, unrounded string copy of its 36 rows, linked to the gzip SHA, plus pair-row identities without correlation values. It permits portable regression verification; the formal freeze builder still requires the original hash-locked archive. Chat numbers and hand-built performance tables are not sources.

## Fixed family policy

The user explicitly fixes two families; no clustering algorithm or threshold is introduced.

- AUDJPY_SINGLETON: `B6-AUDJPY-L-W0-E0950-H1440`, 15:50 entry, automatically retained. It never competes with GBPJPY.
- GBPJPY_FAMILY: all eight Stage8 GBPJPY candidates, in Stage8 relative order. Exactly one representative is selected.

Representative scope uses Stage8 `FinalEntryJST`, not the ID's E-number: `13:00 <= FinalEntryJST < 14:00`. The six IDs/times are `E0835-H1415` 13:57, `E0835-H1325` 13:50, `E0835-H1370` 13:58, `E0800-H1360` 13:22, `E0795-H1405` 13:13, `E0800-H1440` 13:22 (each prefixed `B6-GBPJPY-L-W0-`).

`E0765-H1440` 12:45 and `E0870-H1290` 14:29 / SL20 remain research-valid family members with `NOT_IN_REPRESENTATIVE_SELECTION_SCOPE`. The five nonselected scope candidates have `NOT_SELECTED_FAMILY_REDUNDANCY`. Neither disposition is performance FAIL. Full IDs, scopes, reasons and unchanged eligibility for all nine appear in `candidate_disposition.csv` and `stage9_family_consolidation.json`.

## Exact selection rule

Lexicographic order, using raw values without rounding, epsilon or tolerance:

1. WorstSegmentMaxDDR ASC = max(Discovery.MaxDDR, Validation.MaxDDR, Monitor.MaxDDR).
2. RelativeLotMarginProxy ASC = 30.0 / SL_pips.
3. FullAvailableMaxDDR ASC.
4. ValidationAvgR DESC.
5. FullAvailableTotalR DESC.
6. CandidateID ASC.

Raw CSV numeric strings are parsed to the original binary64 values; no display-rounding is applied. Proxy is computed from raw SL. SL30=1.0; SL35=30/35. It compares relative lot/margin load for the same GBPJPY symbol at equal fixed monetary risk. It is **not actual broker margin**, a lot decision or a risk allocation. Actual money/capital impact belongs to Stage10.

Validation is [2024-01-01,2026-01-01); FullAvailable is [2020-01-01,2026-09-10). FullAvailable AvgR/TotalR/DD/PF are retained in the audit. PF, WinRate, Monitor PF/TotalR, Sharpe, recovery/profit-DD scores, correlation/Jaccard and external broker/market information are not ranking keys. Correlation only supports the user-fixed family policy.

## Result

`B6-GBPJPY-L-W0-E0835-H1415` wins on the first key alone: WorstSegmentMaxDDR=11.07333333333348, strictly below each of the other five. Its proxy=1.0; FullAvailableMaxDDR=11.07333333333348; ValidationAvgR=0.11323432343233049; FullAvailableTotalR=148.63333333332955. Later keys are not needed to decide this run. The complete six-row raw audit is `gbpjpy_representative_selection.csv`.

Final order is family order, not inter-symbol ranking:

| CandidateID | Entry JST | Exit JST | Exit day offset | SL pips | TP | EventMode |
|---|---|---|---:|---:|---|---|
| B6-AUDJPY-L-W0-E0950-H1440 | 15:50 | 15:50 | 1 | 20 | TP_NONE | E0 |
| B6-GBPJPY-L-W0-E0835-H1415 | 13:57 | 13:31 | 1 | 30 | TP_NONE | E0 |

Both remain Long / Monday / Formal PASS / Monitor OBSERVED / Stage8 ELIGIBLE. All original Stage8 fields are copied exactly, with only Stage9 family/disposition and Stage8Eligibility alias added. There is no condition, SL/TP, EventMode, spread or execution change.

## Serialization and handoff

JSON is UTF-8, sorted keys, final LF, no NaN. INF/UNDEFINED are strings if needed. CSV preserves raw numeric precision and final LF; `UNDEFINED` in TP means the source null/TP_NONE, not a missing condition. Candidate order is stable. Two independent original-archive builds produced identical bytes for every generated artifact. `stage9_config.json` binds source hashes, family, audit and exact final-candidate SHA256; Stage10 must hard-gate that final SHA. `stage9_release_manifest.json` binds code/tests/docs/results and all required frozen dependencies, excluding itself. `verify_release` requires the exact clean checkout and Stage8 ancestry.

The formal state is `COMPLETE_STAGE9_FINAL_CANDIDATE_FREEZE`, FamilyConsolidationExecuted=true, FinalCandidateFreezeExecuted=true, FinalCandidateCount=2. Stage10 Portfolio / Money Simulation, existing 27/28 comparison, Global R2 comparison, risk allocation / risk percentage / lot decisions, EA / SET / VPS / live changes and Strategy29+ numbering are not executed. PASS != live adoption. Stop at GitHub Freeze; Stage10 needs separate instruction.

## Tests and reproducibility

Stage9 tests cover wrong source SHA/state/counts, duplicate or missing rows, exact families/scope, all six synthetic tie-breaks, adjacent floating-point raw comparisons, forbidden ranking inputs, proxy semantics, exact final conditions, deterministic artifacts, release integrity and prohibited engine imports. Historical tests and assertions remain unchanged. Historical release/preparation assertions use the exact clean Stage2A through Stage8 snapshots; all remaining tests run current code. The measured run is saved in `results/b6/stage9_freeze/test_summary.json`.

Run with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/research python -m b6.stage9_test_suite`, supplying `--stage2a-snapshot` through `--stage8-snapshot` paths. Rebuild the nine generated freeze artifacts with `python -m b6.stage9_freeze --archive <formal-archive> --output-root <review-directory>` and byte-compare against the release. This never replays M1. Historical engine unit tests use synthetic fixtures only; no formal research run is launched by Stage9.
