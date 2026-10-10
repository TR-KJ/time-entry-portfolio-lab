# B7 U10 Implementation Only — Formal Event Mode E2

Status: FROZEN_READY_FOR_CHAT_REVIEW. U10ExecutionAuthorized=false; U10Executed=false. U10PImplementationAuthorized=false; U10PExecuted=false. No formal Candidate E0/E1/E2 metrics, removals or status were generated. This commit adds implementation only, following a separately published conditions-only supplement.

## Frozen identity

U09 Result Freeze: ee4406aa910a8cc13bfe57590ed6ea97faea18f4. U09 Producer:345a0e8ef659bcd601b73a6475c4613a04ff4337. Original Conditions:5dbac7af2d41aa912308868e6ad1a6dbf7cdd107. U09 Supplemental:1466a2c3e8b3d523233c45d665a6cac21e974393. U10 Supplemental:e34099b9c807df1f145f96ca92c2443fe552fa36; supplemental prespec SHA2565dc8c39e2e1bb2ab85c893e8769d601e4cb8d1a295e56bf543c6a6643d92130b.

U10 input research_inputs/b7/u10_selected54_input.json remains SHA256ea64a5145c08db79d6122c24c6ab875c190739b816275ae4bd443510d9571744. Exact ordered54, unique, NoReplacement=true, U09 PASS only, final schedule/SL/TP/Calendar/lineage/source hashes unchanged. Full-object identity rejects every input mutation, with independent U09 shift/hash checks. Anchor schedule is provenance only. Discovery is [2020-01-01,2024-01-01) JST; Validation/Monitor price rows are rejected by execution.

## Calendar source and U10-S01

Source commit173be2a114dad6bd183a0a1515581528850f0850, path src/portfolio_backtest_v1_2_add_aussie_logic.py, blob f087a22554fb920e2c7230b0626e72f654376358, file SHA2564b71f6b7b1cdbe3266cd9b7cefae37811781561016a013a34d7c8c84247ef32d. Eight exact full source arrays, including explicit 2026 concatenations, are frozen in research_inputs/b7/u10_event_calendar.json. SHA256:7a1bdaeab45aa72ad9098386707e452f280d99f37d2c0fb5f4c512805a72d8eb. No network at formal evaluation runtime; no source repair or date supplementation. Tests extract arrays from the exact Git object without executing the original backtest.

AUD_CPI_DATES initial44 + AUD_CPI_2026_DATES4 = final48; Discovery16 exact dates pinned in supplemental prespec. Legacy AU_CPI_DATES is undefined and lookup returns empty; B7 never calls it. Canonical event name AUD_CPI throughout artifacts/diagnostics. No Candidate C matrix, strategy overrides, all-day event rules, synthetic legacy events or historical release-time reconstruction.

| Event | Source date mapping | Fixed JST | ±minutes |
|---|---|---|---:|
| FOMC | next calendar day | 03:00 | 180 |
| US_NFP | same day | 21:30 | 120 |
| US_CPI | same day | 21:30 | 120 |
| BOJ | same day | 12:00 | 180 |
| BOE | same day | 21:00 | 120 |
| ECB | same day | 21:15 | 120 |
| RBA | same day | 13:30 | 120 |
| AUD_CPI | same day | 10:30 | 120 |

Times stay fixed in winter/summer. FOMC source2020-01-29 maps to2020-01-30 03:00, window00:00–06:00 inclusive. Full event arrays retained; events are not pre-deleted solely because their timestamp is outside Discovery when their window can overlap a permitted trade.

## E0/E1/E2

E0 executes fixed U09 Final schedule with frozen SL/TP/Weekday/DOM/Month once. E1 removes constituent central-bank overlaps. E2 adds US_NFP and US_CPI for every pair, plus AUD_CPI only for AUD pairs. Canonical event order is lexical. Unknown symbols fail closed.

| Pair | E1 | E2 extras |
|---|---|---|
| USDJPY | BOJ,FOMC | US_CPI,US_NFP |
| EURJPY | BOJ,ECB | US_CPI,US_NFP |
| GBPJPY | BOE,BOJ | US_CPI,US_NFP |
| AUDJPY | BOJ,RBA | AUD_CPI,US_CPI,US_NFP |
| AUDUSD | FOMC,RBA | AUD_CPI,US_CPI,US_NFP |
| EURAUD | ECB,RBA | AUD_CPI,US_CPI,US_NFP |
| GBPAUD | BOE,RBA | AUD_CPI,US_CPI,US_NFP |
| EURUSD | ECB,FOMC | US_CPI,US_NFP |
| GBPUSD | BOE,FOMC | US_CPI,US_NFP |

Event filtering uses planned Entry through original planned Time Exit, both inclusive. Actual early SL/TP close and fallback TimeExit do not shorten/extend this interval. Multiple events remove one trade once; overlapping names are sorted unique. Missing execution days never become RemovedTrades. Retention=surviving/E0 executable trades; E0 retention1 when nonempty and null when empty. E2 survivors subset E1 subset E0. Remaining prices, Pips, close reasons and all trade fields are unchanged. TradeID hashes CandidateID/planned Entry/planned Exit; stream and ID hashes permit future exact E2 regeneration.

Each mode stores existing stage1 metrics (annual2020–2023, PF state/value, DD, medians and counts), EventSet, RemovedTrades, Retention, RemovedByEvent and MultiEventOverlapTradeCount. DD starts at zero and uses CloseTime→EntryTime→FixedKey. Diagnostic event counts may exceed unique removals. No full formal trade logs are persisted to GitHub. Future PASS-only U10-P projection API retains exact fields, Producer/calendar/job hashes and E2 metrics; no actual U10-P input is created now.

## Formal Gate

Only E2 determines status: Trades>=150; each year>=30; Losses>=10; AvgPips>0; PFState FINITE; PFpips>=1.10; PositiveYearCount>=3. All failed checks retained in canonical order. PASS_U10 or DROP_U10_E2_GATE. No DD cap, retention80%, removed20, improvement requirement, E0/E1 fallback, replacement, calendar/schedule/SLTP changes or mode selection. Unrounded values; INF/UNDEFINED never numeric sentinels.

## Independent verification

Optimized execution reuses unchanged U06 Engine; indexed fixed windows filter E0 once. Scalar reference uses unchanged independent U06 reference execution, its own date/calendar iteration, event selection, timestamp/window construction, inclusive overlap and Gate checks. Only immutable inputs, serialization and existing metrics primitives are shared. Tests compare full trades, planned/actual times, windows, event names, removed/retained IDs, Pips, metrics, annual PF/DD, Gate and status. Edge fixtures cover endpoint inclusivity, overnight, early close, fallback, multiple events, adjacent-period windows, empty streams, nonempty PASS/DROP and deterministic order/hash seeds.

Bounded actual smoke uses prespecified synthetic schedules on AUDUSD/EURJPY and seven fixed2020 event days; LONG/SHORT and finite/none TP. No formal54 schedule is used.16 replays/112 E0 trades exact reference/optimized. Evidence has Formal54Used=false, FormalCandidateStatusProduced=false, FormalU10PerformanceSaved=false, Full54Run=false, ValidationUsed=false, MonitorUsed=false. The 72-file exact identity audit is metadata/integrity only; performance uses bounded Discovery rows only.

## Runner, resume and Finalize-Only

Normal approval CHAT_APPROVED_COLAB_B7_U10_ONLY, Colab only. Fresh separate local/Drive roots.1 Candidate/job,54 jobs; local validation→private Drive staging→copy/hash verification→DRIVE_COMPLETE last→atomic publish. Progress counts only. Exact Python patch/NumPy/pandas and complete runtime identity required for normal resume; mismatch/corruption STOP. All54 completed recovery copies/validates persisted jobs and finalizes without performance recomputation; uses reviewed frozen test/smoke evidence and exact stored data identity instead of rereading prices.

Finalize approval CHAT_APPROVED_COLAB_B7_U10_FINALIZE_ONLY. Explicit caller Producer=reviewed SHA=clean HEAD; no automatic adoption of source SHA. Same Python major.minor (patch differences allowed), NumPy2.3.5/pandas2.2.3 exact. Audit identity +54×candidate/checkpoint/marker=163 trusted files. Ignore partial staging; reject missing/extra/duplicate/corrupt jobs. Source unchanged. Fresh separate local output only, nothing written before54/54 passes. Trap tests prohibit M1 load, Engine/execution, timestamp generation, overlap/refilter, metrics/Gate reevaluation and status policy. Persisted schema/hash checks and summaries only.

Outputs: input_identity,preflight,candidate_results,checkpoint_audit,pair_summary,status_summary,event_summary,mode_summary,review,artifact_manifest,COMPLETE. Finalize additionally saves finalize_preflight/identity/environment and source audit. COMPLETE_U10_ONLY written last after all54. Fresh archive only after COMPLETE, with copy hash/size and ordered ZIP member hash/size/CRC validation; raw M1 excluded.

## Notebook and stopping boundary

notebooks/b7_u10_event_e2.ipynb and b7_u10_finalize_only.ipynb have all RUN flags False. Mount/install/checkout/input audit/calendar audit/M1 audit/tests/bounded smoke/preflight/fresh run/resume/finalize/archive are separate guarded cells. Explicit reviewed SHA required. Review implementation before authorizing a Colab formal run.

All pre-existing production code, tests, notebooks, prior inputs/results, Original and Supplemental conditions remain byte-identical. Existing release memberships are unchanged; dependent status/SoT hashes refreshed only. U10 implementation release binds new code/config/calendar/input/conditions/prior U09 artifacts/tests/notebooks/evidence. See test_results.json for exact Total/PASS/FAIL/ERROR/SKIP. Main/B6/27–28 strategies/Global R2/EA/SET/VPS/live/current forward untouched. No formal U10/U10-P/Profit Protection/Candidate Freeze/Validation/Monitor/Money/Portfolio run.
