# B7 Stage0 audit results — BLOCKED_PENDING_PROVENANCE

Technical data/protocol checks completed; **scientific Stage0 clearance is blocked by unverified broker/source equivalence**. This is an audit snapshot Freeze, not a declaration that all Stage0 prerequisites pass. No different broker has been demonstrated. No Stage1 implementation/sweep, candidate selection, Validation/Monitor performance or money/R2 work was performed.

## Verification

|Check|Result|Evidence|
|---|---|---|
|Independent main-based B7 branch|PASS|main1df6b8c…; B6 read-only7ac8f554…; repository_refs/source_manifest|
|Existing EU/GU formal audit reuse|NOT FOUND in searched scope|37 branch tips +8 Drive M1/input/manifest records; none matched; new technical audit performed|
|Actual M1 files inspected|81|input_audit.csv includes selected and excluded alternate exports|
|B7 measured inventory|72 files,9×8|expected_m1_manifest.csv; broker clearance still BLOCKED|
|Existing7 identity|56/56 exact|filename,SHA256,rows,FirstRaw,LastRaw match frozen B6 manifest|
|Selected data integrity|PASS|OHLC,finite,positive,decimal price grid,raw ordering; pair raw/JST duplicates0|
|Helsinki→Tokyo conversion|PASS as prescribed interpretation|ambiguous=infer,nonexistent=shift_forward; original broker timezone not independently certified|
|Actual last timestamp|2026-09-09 06:00 JST for all9|no tail fill; requested Monitor end remains2026-09-10 exclusive|
|EU/GU broker/source equivalence|BLOCKED / UNVERIFIED|CSV lacks broker field; shared directory/schema and uncertain recollection are insufficient proof|
|EU/GU alternate exports|PASS subset equivalence|RECHECK contains all original timestamps with exact OHLC, plus actual additional rows; no files spliced|
|Spread|AGREED|EU1.0,GU1.5 pips; research assumptions,not historical averages|
|Pip|FORMAT CONSISTENT|JPY.01/non-JPY.0001; finite positive prices on fractional-pip decimal grid|
|Calibration algorithm|PASS exact inherited function bodies|calibration_method_identity.json; no PnL input; Discovery-only|
|Existing7 SL grid|7/7 exact match|all five values unchanged; no adjusted grids|
|Synthetic/audit tests|25 PASS|synthetic_tests.txt; B7-specific suite only,not a claim to rerun all B6 stages|
|Bounded actual-data compatibility|36 PASS|9pair×2directions×TP_NONE/30;SL20;one preselected2020-02-04 09:00 anchor,holding30; no PnL table saved|
|Stage1/Validation/Monitor research|NOT RUN|Stage1 absent; future-price arrays never enter calibration/compatibility|
|EA/SET/VPS/live/current-forward|UNCHANGED|only new B7 paths staged; main/B6 refs verified separately after publication|

The initial integrity-check implementation incorrectly assumed the old export was a contiguous prefix. Read-only diagnosis established a sparse timestamp subset with exact overlapping OHLC. The subset check was corrected; no price/PnL-based selection condition changed. A separate smoke-comparison issue compared string timestamps with pandas.Timestamp objects; comparison now normalizes timestamps only and preserves exact numerical comparison. Both checks passed after fixes; no execution convention changed.

## EU/GU files and coverage

Same discovered source root: `ゆうのすけさん2025/再現性100%/EUR:USD/MT5データ` and `GBP:USD/MT5データ`, with historical segments in `1分足`. Broker identity remains unverified. Each has six2015–2025 segments plus2026Jan–Mar and2026Apr–Sep RECHECK, eight selected files. Nine files each including excluded ordinary2026Apr–Sep version. Exact hashes and filenames are in the72-row manifest; all alternatives in input_audit.csv.

### EURUSD

|Selected filename|Rows|First raw|Last raw|
|---|---:|---|---|
|EURUSD_M1_201501020900_201612302359.csv|744037|2015-01-02 09:00:00|2016-12-30 23:59:00|
|EURUSD_M1_201701020000_201812282357.csv|740913|2017-01-02 00:00:00|2018-12-28 23:57:00|
|EURUSD_M1_201901020600_202012310000.csv|743191|2019-01-02 06:00:00|2020-12-31 00:00:00|
|EURUSD_M1_202101040001_202212302354.csv|746018|2021-01-04 00:01:00|2022-12-30 23:54:00|
|EURUSD_M1_202301020702_202412310000.csv|743131|2023-01-02 07:02:00|2024-12-31 00:00:00|
|EURUSD_M1_202501020000_202512310000.csv|369201|2025-01-02 00:00:00|2025-12-31 00:00:00|
|EURUSD_M1_202601020000_202603310000.csv|88752|2026-01-02 00:00:00|2026-03-31 00:00:00|
|EURUSD_M1_202604010000_202609090000_RECHECK.csv|165596|2026-04-01 00:00:00|2026-09-09 00:00:00|

|Period|Rows|First JST|Last JST|
|---|---:|---|---|
|Discovery|1489448|2020-01-01 00:00:00|2023-12-30 06:58:00|
|Validation|740978|2024-01-02 07:00:00|2025-12-31 07:00:00|
|Monitor|254348|2026-01-02 07:00:00|2026-09-09 06:00:00|

### GBPUSD

|Selected filename|Rows|First raw|Last raw|
|---|---:|---|---|
|GBPUSD_M1_201501020900_201612302359.csv|743986|2015-01-02 09:00:00|2016-12-30 23:59:00|
|GBPUSD_M1_201701020001_201812282357.csv|740796|2017-01-02 00:01:00|2018-12-28 23:57:00|
|GBPUSD_M1_201901020600_202012310000.csv|743162|2019-01-02 06:00:00|2020-12-31 00:00:00|
|GBPUSD_M1_202101040002_202212302355.csv|745823|2021-01-04 00:02:00|2022-12-30 23:55:00|
|GBPUSD_M1_202301020702_202412310000.csv|742974|2023-01-02 07:02:00|2024-12-31 00:00:00|
|GBPUSD_M1_202501020000_202512302359.csv|369434|2025-01-02 00:00:00|2025-12-30 23:59:00|
|GBPUSD_M1_202601020001_202603310000.csv|88566|2026-01-02 00:01:00|2026-03-31 00:00:00|
|GBPUSD_M1_202604010000_202609090000_RECHECK.csv|165589|2026-04-01 00:00:00|2026-09-09 00:00:00|

|Period|Rows|First JST|Last JST|
|---|---:|---|---|
|Discovery|1489082|2020-01-01 00:00:00|2023-12-30 06:58:00|
|Validation|741196|2024-01-02 07:00:00|2025-12-31 06:59:00|
|Monitor|254155|2026-01-02 07:01:00|2026-09-09 06:00:00|

Gap diagnostics include weekends/holidays and segment joins. They are descriptive counts, not a verified exchange-session missing-bar classification. The original EU/GU2026Apr–Sep files have a144-day gap: EU18,720/GU18,719 rows. RECHECK has EU165,596/GU165,589; overlap differs in0 OHLC rows. No broker is inferred from that match.

## Price-only five-SL proposals — PROVISIONAL

|Symbol|Eligible days|Daily median pips|SL1|SL2|SL3|SL4|SL5|
|---|---:|---:|---:|---:|---:|---:|---:|
|USDJPY|806|77.5000|10|25|40|60|95|
|EURJPY|808|95.3000|15|30|50|75|115|
|GBPJPY|807|126.6000|20|40|65|100|150|
|AUDJPY|808|82.7000|10|25|40|65|100|
|AUDUSD|807|70.5000|10|20|35|55|85|
|EURAUD|808|119.8500|20|35|60|95|145|
|GBPAUD|805|135.1000|20|40|70|110|160|
|EURUSD|808|74.4500|10|20|35|60|90|
|GBPUSD|808|101.1000|15|30|50|80|120|

All grids use the inherited prespecified Tue–Fri eligible-day median High−Low,2020–2023 only, multipliers.15/.30/.50/.80/1.20,half-up5pips,min10,max300,strictly increasing5pips correction. No clamp/duplicate correction occurred. Exact eligibility and annual counts,quantiles and auxiliary30-minute/4-hour diagnostics are in price_statistics.json. These are price diagnostics,not candidate performance and not formal Stage1 adoption.

## Artifacts

- docs/b7: source_of_truth,research_plan,parameter_decision_register,stage0_validation,sl_calibration_prespec.
- research_inputs/b7: stage0_protocol.json,expected_m1_manifest.csv,sl_grid_proposal.csv; separately identified B6 reference manifest/grid.
- results/b7/stage0: repository_refs,source_manifest,existing_audit_search,input_audit,pair_audit,coverage,alternate_exports,alternate_overlap_diagnostics,price_statistics,calibration_day_diagnostics.csv.gz,calibration_method_identity,sl_grid_proposal,spread_pip_audit,environment,synthetic_tests,bounded_smoke,run_status,provenance_status,artifact_manifest.
- src/research/b7: audit,calibration,isolation,compatibility and unchanged B6 reference fixture. tests/test_b7_audit.py and tests/test_b7_compatibility.py.

No raw M1,complete trade log,credentials or personal absolute path is saved. No new executable module for Stage1 or later exists.

## Stopping conditions / Chat handoff

B01 is unresolved broker/source identity. Therefore complete Stage0 PASS must not be claimed even after publishing the tested snapshot. Require traceable provenance before official data-source clearance. Stage1 remains disabled. Confirm the SL proposals and resolve Pure Time eligibility,5SL robustness,plateau thresholds,family de-duplication/fixed key/weekday transition,undefined metrics,SL/TP rules,calendar/month sample-removal rules,event thresholds and future Validation contract; full list in the Decision Register. No B6 numerical gates are silently inherited.

Validation/Monitor **performance was not opened or computed**. Their raw-file bytes,OHLC validity,timestamps and coverage were read under the specifically authorized data-integrity audit. Consequently do not state that all Validation/Monitor raw data remained unopened. This distinction preserves the audit requirement and research blindness accurately.

Git publication status and final SHA are verified after committing, in the returned handoff, avoiding a self-referential commit hash. Publication of this BLOCKED snapshot does not clear the blocker or authorize Stage1.
