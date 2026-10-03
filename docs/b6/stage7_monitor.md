# B6 Stage7 — 2026 Reference Monitor implementation freeze

Stage6 formal runtime is complete: 50 candidates, 150 period rows, PASS 17 / FAIL 33 / INSUFFICIENT_SAMPLE 0. Source code `a1f9e0266801d3d0b4cd383f8fea909fdbc0a678`; config SHA256 `fa68b843ce900a83fa9828a7415cce9256d45982e1fee3de9d21980cbb418e4c`. Formal Validation was executed in Google Colab. Its outputs remain immutable; Work does not rerun them.

## Scientific input and provenance

The exact formal archive is `/Users/tomitaryou/Library/CloudStorage/GoogleDrive-ry103ta.i@gmail.com/マイドライブ/b6_stage6_archive`. The ten expected SHA256 values in `research_inputs/b6/stage7_source_spec.json` were independently checked against the archive bytes. `results/b6/stage7_freeze/stage6_input_audit.json` records every archive file hash, including identity, checkpoints, all 50 shards and the review ZIP. The ZIP was hashed as an archive inventory item; it was not used as scientific input.

The formal CSV status filter `ValidationStatus == PASS` defines the 17 candidates. All 50 CSV conditions and shard payloads were cross-checked against the unchanged Stage5 freeze. The 17 retained records preserve formal CSV order, with AUDJPY 9 / GBPJPY 8 / EURJPY 0, all Long (`L`), Monday (`0`), E0. There is no drop, refill, rerank or condition adjustment. CSV numeric formatting such as `2` versus `2.0` is compared as exact decimal values, without tolerance or rounding. Formal metric text is retained verbatim as provenance.

- Monitor input: `research_inputs/b6/stage7_monitor_candidates.json`
- Exact SHA256: `c973c541726efba057b2c07a19cc99ffd2b5a2d457328d1e9df8e813d5e96b86`
- Ordered input summary: `results/b6/stage7_freeze/monitor_candidate_summary.csv`
- Audited identity, summary, progress, frozen-condition rows and PASS-only metric provenance (FAIL metrics and full period metrics excluded): `results/b6/stage7_freeze/stage6_formal_evidence.json`
- Stage5 Candidate SHA256: `b98f36d92d1b101fcd53f65fdd900bee35f1a209cbdcdd71d71211dc15d00ae0`
- Validation Contract SHA256: `646344d240323f81d46e6360ac1f5d4e15f2130db6399f7fbbcb013bc1a15c57`

`python -m b6.stage7_freeze --archive <formal archive> --destination <repository>` deterministically regenerates identical inputs or rejects a differing existing file. It never accesses M1 prices or replays candidates. Missing archive, incomplete execution, wrong identity/hash, duplicate ID, changed conditions, count or expected-ID discrepancies are fatal; no repair is performed. The runtime uses only the exact repo-frozen Monitor input and its provenance, so the Drive Stage6 archive is not required in the Stage7 Colab run.

## Fixed Monitor scope

Window: `[2026-01-01 00:00, 2026-09-10 00:00)` JST. Canonical conversion is Europe/Helsinki → Asia/Tokyo → naive JST, before slicing. All seven pairs end at **2026-09-09 06:00 JST** in the exact 56 audited M1 inputs. The per-pair first/last timestamps, Monitor rows and source rows outside the window are in `results/b6/stage7_freeze/m1_availability_audit.json`. No candidate prices were replayed during this audit.

This is a partial year reference observation, not new Formal Validation. No Monitor PASS/FAIL, minimum sample, PF/AvgR/TotalR/DD threshold, ranking, Top N, retuning, EventMode reselection or Stage6 FAIL revival exists. Every input retains `FormalValidationStatus=PASS`; `MonitorState=OBSERVED` is neutral, even for negative TotalR or zero trades. Partial 2026 totals do not create a formal comparison with full-year 2024/2025. PASS does not mean live adoption.

The private checked AST adapter changes only frozen period constants, weekday epoch, relative imports and event period guards. Shared Stage1–6 source and globals remain unchanged. All existing execution semantics remain: exact Entry M1 Open with fixed spread, spread-adjusted SL/TP basis, Entry/Exit inclusive, SL first, Exit secured before path scan, exact then +1/+2/+3/+4 fallback, missing Entry/Exit means no trade, no interpolation, no extra rounding/slippage/epsilon, raw High/Low, overnight allowed, no weekend bridge, entry stop December 25–January 3. No prices are added after the data end. The frozen event calendar SHA is `1882b315f88d2a1b4fd18b2929f12bd269c87c98b5c2bf1a66203baf54865484` from `173be2a114dad6bd183a0a1515581528850f0850`; no web updates.

Metrics use chronological raw R and initial DD peak 0. Zero R counts as a trade but not a win/loss; PF without loss and with positive return is `INF`, with no positive/loss is `UNDEFINED`. The reused frozen numerical aggregator's legacy discovery gate output is discarded, never used for Monitor decisions. Diagnostics include planned opportunities, trade/exit/fallback/missing-path/event counts and actual data coverage.

## Colab and output

Notebook: `notebooks/b6_stage7_monitor.ipynb`. All five flags default False and `STAGE7_FREEZE_SHA=""`. Default run-all prints fixed input metadata only, with no M1 reading or Monitor calculation. Preparation sets `sys.dont_write_bytecode=True` before importing b6; strict clean-checkout guard remains intact.

- DATA_ROOT: `/content/drive/MyDrive/ゆうのすけさん2025`
- OUTPUT_ROOT: `/content/b6_stage7`
- Drive archive: `/content/drive/MyDrive/b6_stage7_archive`
- NumPy `2.3.5`, pandas `2.2.3`; Python version recorded and required to match on resume.

Full Monitor requires Google Colab, Chat confirmation, both full-run flags, exact 40-digit release SHA, clean checkout, manifest/config/candidate/provenance/calendar/M1 identities and frozen library versions. Resume requires exact code/config/candidate/source-result IDs, candidate order/count, 56 M1 hashes, calendar and Python/NumPy/pandas versions. Output must be outside repo and M1 inputs, and Drive copy never overwrites an existing archive.

Only completed-job counts appear before all 17 jobs finish. Completion state is `COMPLETE_STAGE7_MONITOR_ONLY`. Output consists of identity, config, input audits, atomic shards/checkpoints, progress, 17 Monitor result rows, diagnostics, summary, review and compact review ZIP. After completion the Notebook shows the 17 rows and separate per-pair tables in frozen order, never Monitor PASS/FAIL counts. Review ZIP excludes raw M1 and large trade logs.

## Verification and stop point

The Stage7 suite retains the historical Stage1–6 assertions unchanged at clean frozen snapshots; current Stage7 tests cover source hard gates, frozen conditions, period isolation, seven-pair Long/Short synthetic replay, TP_NONE/finite TP, E0/E1/E2, SL-first/raw boundaries, fallback/missing bars/overnight/FOMC, metrics, neutral status, resume, Notebook defaults and clean preparation.

`python -m b6.stage7_test_suite --stage2a-snapshot <path> --stage2b-snapshot <path> --stage3-snapshot <path> --stage4-snapshot <path> --stage5-snapshot <path> --stage6-snapshot <path>` runs the full suite. Use `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src/research`; preparation regressions explicitly remove inherited bytecode suppression in fresh subprocesses. Exact counts are in `results/b6/stage7_freeze/test_summary.json`.

Implementation Freeze stops after GitHub remote SHA equals local HEAD and tracked/untracked status is clean. Work does not run the 2026 Monitor, Portfolio, overlap/correlation, existing 27/28 comparisons, live changes or Strategy 29+ numbering.

WorkではStage7 full Monitor未実行。Chat確認後にGoogle Colabで2026 Monitorを実行する。
