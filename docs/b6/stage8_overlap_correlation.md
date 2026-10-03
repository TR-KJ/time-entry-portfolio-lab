# B6 Stage8 — Deployment Eligibility and Overlap / Correlation

Stage7 formal runtime completed `COMPLETE_STAGE7_MONITOR_ONLY`, 17/17 observed, Formal Validation unchanged. Stage7 code `805fccbb2dac5dddd4e4ed24d14bedf8887d3b1a`, config SHA256 `fa42a56ebf23135c4d9c11d973016614c5298c72ecab60a309218a395d58b683`, candidate SHA256 `c973c541726efba057b2c07a19cc99ffd2b5a2d457328d1e9df8e813d5e96b86` remain immutable.

## Formal source audit and deployment decision

Formal archive: `/Users/tomitaryou/Library/CloudStorage/GoogleDrive-ry103ta.i@gmail.com/マイドライブ/b6_stage7_archive`. All 28 files are hash-locked in `research_inputs/b6/stage8_source_spec.json`: identity, effective config, audits, checkpoint ledger, 17 candidate shards, progress, results, diagnostics, summary, review and review ZIP. Every shard was matched to its unchanged Stage7 candidate and formal CSV row. The ZIP is inventory only; it is not scientific input. Formal Monitor values are checked for archive consistency but are not copied into the eligibility input and are never used in the decision.

All **17 research candidates remain FormalValidationStatus=PASS and MonitorState=OBSERVED**. Exactly eight AUDJPY Monday 07:01 candidates are deployment-review ineligible under the user's explicit decision, reason `WEEKLY_OPEN_EXECUTION_MODEL_RISK`:

> 月曜07:01のAUDJPYは週明け直後に近く、固定spreadによるHistorical execution modelでは、実運用時のspread拡大・slippage・gapに伴う約定リスクを十分にstressしていない。研究上のPASSは維持し、Deployment Review対象のみから除外する。

This is execution-model risk, not poor performance or a claim about measured live spreads. No external spread measurement or web research was performed. Changing Monitor PF/AvgR/TotalR/DD cannot affect eligibility. Research history is not deleted, Formal Validation is not revoked, and Monitor results are unchanged.

Excluded IDs (relative Stage7 order):

```text
B6-AUDJPY-L-W0-E0425-H1315
B6-AUDJPY-L-W0-E0425-H1255
B6-AUDJPY-L-W0-E0425-H1100
B6-AUDJPY-L-W0-E0425-H1360
B6-AUDJPY-L-W0-E0425-H1195
B6-AUDJPY-L-W0-E0425-H1020
B6-AUDJPY-L-W0-E0425-H1150
B6-AUDJPY-L-W0-E0425-H1430
```

Deployment Review Pool (unchanged relative Stage7 order):

```text
B6-GBPJPY-L-W0-E0835-H1415
B6-GBPJPY-L-W0-E0835-H1325
B6-GBPJPY-L-W0-E0765-H1440
B6-GBPJPY-L-W0-E0870-H1290
B6-GBPJPY-L-W0-E0835-H1370
B6-GBPJPY-L-W0-E0800-H1360
B6-GBPJPY-L-W0-E0795-H1405
B6-AUDJPY-L-W0-E0950-H1440
B6-GBPJPY-L-W0-E0800-H1440
```

AUDJPY=1, GBPJPY=8, EURJPY=0. The AUDJPY 15:50 singleton is retained. `ELIGIBLE` means eligible for Stage8 deployment review only, not live adoption. Candidate timing, SL/TP, spread, pip size and E0 are unchanged.

- Eligibility artifact: `research_inputs/b6/stage8_deployment_eligibility.json`, SHA256 `7e62f0ca36a8160233a7f037c08f1c084cab49f418688718559afefa30adf852`.
- Pool artifact: `research_inputs/b6/stage8_candidate_pool.json`, SHA256 `dfe25f015da9532535fb9aae3e580e59835f68cf6f9c0e2b0fc6b4a215ec6d68`.
- Config: `research_inputs/b6/stage8_config.json`, SHA256 `addcaab2c618df492bd73d7ae2d83d626d8c9513420c939da5f98625bd4704c7`.
- Formal audit: `results/b6/stage8_freeze/stage7_input_audit.json`.
- Decision audit: `results/b6/stage8_freeze/deployment_eligibility_audit.json`.

`python -m b6.stage8_freeze --archive <formal Stage7 archive> --destination <repository>` regenerates identical bytes or refuses different existing outputs. Missing source, changed exact file inventory, wrong identity/state/counts/conditions or inconsistent shards are rejected without repair. The Stage8 Colab run consumes repo-frozen artifacts; it does not require the Stage7 Drive archive again.

## Periods and execution

All windows use naive JST after canonical Europe/Helsinki → Asia/Tokyo conversion:

| Period | Start inclusive | End exclusive |
|---|---|---|
| Discovery | 2020-01-01 | 2024-01-01 |
| Validation | 2024-01-01 | 2026-01-01 |
| Monitor | 2026-01-01 | 2026-09-10 |
| FullAvailable | 2020-01-01 | 2026-09-10 |

FullAvailable is **post-validation structural analysis**, combining Discovery, Validation and partial Monitor. It is not a new Validation. Period attribution uses planned Entry JST date; the four separate rows are retained, with no conclusion from FullAvailable alone. All 56 exact M1 hashes and seven-pair timestamp availability were re-audited. Actual end is **2026-09-09 06:00 JST** for all seven pairs. Availability and out-of-window row counts are in `results/b6/stage8_freeze/m1_availability_audit.json`; no candidate replay was used for that audit.

A private checked AST adapter changes only period constants, weekday epoch, relative module links and event date guards. Stage1–7 source and shared globals remain unchanged. Execution remains exact Entry M1 Open with fixed spread, SL/TP based on spread-adjusted Entry, Entry/Exit inclusive, same-bar SL first, Exit exact then +1/+2/+3/+4 secured before scanning, missing Entry/Exit means no trade, no intermediate interpolation, broker splice, epsilon, extra rounding or slippage, raw High/Low, overnight allowed, no weekend bridge, and Entry stop Dec25–Jan3. Frozen EventMode is E0 for all nine; generic E1/E2 compatibility is tested without reselection. No future bars or data-end extrapolation.

## Raw structural evidence

Nine candidates yield **36 unordered pairs per period, 144 long-form pairwise rows**, including 28 GBPJPY-with-GBPJPY and 8 AUDJPY-with-GBPJPY pairs per period. There is no AUDJPY-with-AUDJPY pair. Pair order is input order `i<j`, never a metric ranking. Candidate diagnostics contain **36 candidate-period rows**.

- **WeekKey:** planned Entry JST calendar date `YYYY-MM-DD`, not ISO week number. All planned opportunities, including missing Entry/Exit and other filtered cases, appear in availability diagnostics as TRADE or NO_TRADE with original reason. The trade ledger contains actual trades only.
- **Pearson / Spearman:** raw R on intersecting actual-trade WeekKeys only. No missing/no-trade zero fill. Spearman uses average ranks for ties. Fewer than two common observations or zero variance in either series yields `UNDEFINED`.
- **Trade Jaccard:** BothTradeWeeks / EitherTradeWeeks, with separate A/B/both/either counts.
- **Loss Jaccard:** BothLossWeeks / EitherLossWeeks; loss is raw R<0. Loss sets include each candidate's own actual-trade weeks. Zero R is not a loss.
- **Sign agreement:** matching positive/zero/negative signs on BothTradeWeeks. Zero is its own category.
- **Planned schedule overlap:** intersection / union of frozen Entry→Exit intervals on the same reference Monday, including exit day offset. Intersection and union minutes are also saved.
- **Actual exposure Jaccard:** sum(intersection minutes) / sum(union minutes) across either-trade weeks. No-trade means empty exposure. Intervals use elapsed time `[ActualEntry, ActualClose)`; identical timestamps have zero duration.
- **Shorter exposure coverage:** summed intersection / sum(min(DurationA,DurationB)) on both-trade weeks.
- All zero denominators yield `UNDEFINED`, not zero or a large substitute.
- Structural differences are absolute. Entry uses minute of day; Exit uses minute of day + 1440×day offset, not shortest clock distance. Holding and SL differences, SameSymbol, SameTPMode and SameEventMode are saved.

The ledger stores CandidateID, Symbol, WeekKey, planned/actual entry and exit, exit reason, raw R, Pips=raw R×frozen SL, base period, fallback minutes and missing-path count. Display-rounded execution R is never used. Candidate-period metrics reuse frozen raw-R aggregation, chronological close order and initial DD peak 0; legacy discovery gate outputs are discarded. They are diagnostics only.

`stage8_pairwise_metrics.csv.gz` is the primary source. Twenty optional-display matrices (five metrics × four periods) are derived from the long form, symmetric in frozen candidate order, with diagonal `UNDEFINED`. No reverse calculation from matrices.

There are **no thresholds, clustering, high/medium/low labels, family decisions, scores, ranking, representative selection, survivor selection or retuning**. Stage9 will review family consolidation, especially GBPJPY8 while retaining the AUDJPY singleton in principle. Stage10 will address incremental portfolio/money simulation. Neither Stage9 nor Stage10 has an execution/selection API here.

## Colab, completion and resume

Notebook: `notebooks/b6_stage8_overlap_correlation.ipynb`. Default PREPARE_ENVIRONMENT, MOUNT_DRIVE, RUN_STAGE8_FULL, CHAT_CONFIRMED_STAGE8_FREEZE and SAVE_OUTPUT_TO_DRIVE are all False; `STAGE8_FREEZE_SHA=""`. Default run-all displays fixed metadata only, with no M1 or pairwise computation. Preparation sets `sys.dont_write_bytecode=True` before b6 import; clean checkout guard remains strict.

- DATA_ROOT: `/content/drive/MyDrive/ゆうのすけさん2025`
- OUTPUT_ROOT: `/content/b6_stage8`
- Drive archive: `/content/drive/MyDrive/b6_stage8_archive`
- Full runtime: Python **3.13.15**, NumPy **2.3.5**, pandas **2.2.3**, matching the frozen formal runtime. Preparation may succeed on another Python version, but full analysis rejects a runtime mismatch before M1 access.

Full execution requires Google Colab, exact release SHA, both full/Chat flags, clean checkout, release/config/eligibility/pool/Stage7 provenance/calendar and 56 M1 identities. Resume requires exact code/config/artifact hashes, candidate IDs/order, M1 identities, calendar and Python/NumPy/pandas. Output is outside repo and price inputs; Drive archive is never overwritten.

Only completed-job counts are shown until all nine replays and all 144 pairwise / 36 candidate-period rows are complete. State is `COMPLETE_STAGE8_OVERLAP_CORRELATION_ONLY`. Outputs include identity, config, audits, exact eligibility/pool copies, checkpoints, trade ledger, opportunity diagnostics, candidate-period metrics, pairwise metrics, matrices, summary, review and ZIP. ZIP excludes raw M1 and includes the ledger only if its compressed size is ≤5 MB; the complete ledger always remains in the archive. Completion stops before Stage9/Portfolio/live.

## Verification and Work boundary

New tests use synthetic prices/trades only for replay and pairwise values. Tests cover exact 17/8/9 eligibility, independence from Monitor performance, formal input guards, hand-computed correlations/Jaccards/exposures, undefined/zero behavior, pair symmetry/order, period boundaries, frozen execution compatibility, no fill, Notebook defaults and partial-display guards, clean preparation, exact resume identity and release integrity. Existing Stage1–7 assertions are not changed; historical release assertions use their clean freeze snapshots.

Run `python -m b6.stage8_test_suite --stage2a-snapshot <path> --stage2b-snapshot <path> --stage3-snapshot <path> --stage4-snapshot <path> --stage5-snapshot <path> --stage6-snapshot <path> --stage7-snapshot <path>` with `PYTHONPATH=src/research PYTHONDONTWRITEBYTECODE=1`. Exact test counts are in `results/b6/stage8_freeze/test_summary.json`. Preparation subprocess regressions remove inherited bytecode suppression to expose the original cache failure.

Work does not execute actual Stage8 overlap/correlation, Stage9 family consolidation, GBP representative selection, Stage10 Portfolio, existing portfolio comparison, live changes or Strategy29+ assignment.

WorkではStage8 full Overlap/Correlation未実行。Deployment Eligibility FreezeとStage8実装のみ完了。Chat確認後にGoogle ColabでStage8を実行する。
