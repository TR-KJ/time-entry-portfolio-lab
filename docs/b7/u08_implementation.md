# B7 U08 Implementation Freeze — DOM / Month LOMO / Calendar

Implementation only. Formal U08 56-job execution is not authorized or executed. Formal DOM, Month, DROP and Calendar results for the56 candidates are not generated or viewed. U09+, Candidate Freeze, Validation and Monitor are not executed.

## Frozen identities and input

- U07 Result Freeze: `21140269596584575677421934399122614f6cd6`.
- Conditions Freeze: `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`.
- U07 Producer: `9adeef8514fb76efec70a2cc46ce85e306ea0597`.
- U06 Result Freeze: `c526dc1bb49d168376e5cb4858174524c0a63f7a`.
- Stage1 Result Freeze: `72b8244c69d165fae4a3c806a1cdb5d6fcfa1a38`.
- Input: `research_inputs/b7/u08_selected56_input.json`.
- Input SHA256: `7c49b9cd0374b57f4da78eb784aa646050cba507b0ff037e303085a61deb7616`.

Exactly56 PASS_U07 candidates, no replacement. `u08_input.py` audits the entire fixed input hash, ordered unique IDs, NoReplacement, U07 status/producer, original schedules and FormalSL/TP, frozen weekday/Anchor/canonical SetName projections, U06 source identity, candidate/checkpoint hashes, and Archive/manifest/result identity. It reads existing frozen result metadata, not new performance. Frozen inputs and previous conditions/results are unchanged.

FormalWeekdays and all symbol/direction/entry/exit/offset/holding/SL/TP fields are fixed. AnchorWeekday and canonical SetName are retained as provenance. U08 never calls U07 selection or U06 SL/TP selection. Calendar membership and annual attribution use planned Entry JST date, not CloseTime/exit date/raw broker date.

## Explicit comparison supplement

The user's2026-10-08 supplement is recorded in `u08_config.json`, without rewriting the original full conditions or metrics code.

PF strict improvement is true only when both baseline and candidate have PFState=FINITE and candidate PFpips > baseline PFpips. Any INF/UNDEFINED participation is false. Finite zero is compared normally; no numeric sentinel is created. DOM/Month PF<1 OFF conditions likewise require FINITE.

MedianAnnualAvgPips strict improvement requires both values non-null and candidate > baseline. Either null means false. `stage1_metrics.py` remains unchanged: all four annual sample gates are required to produce this median. Missing/undersampled years are never dropped from a median. This is an adoption comparison definition, not a new sample gate or a Month final U01 gate.

All adoption comparisons additionally require AvgPips strictly greater, PositiveYearCount no smaller, and MaxDDPips no larger. Equality fails strict improvement; there is no absolute improvement floor.

## Execution and metrics architecture

`u08_reference.py` independently enumerates fixed weekdays and calls the unchanged U06 scalar executor. `u08_execution.py` uses the unchanged U06 vectorized Engine/evaluate path. Only formal fixed weekdays generate baseline trades; no weekday optimization occurs.

`u08_calendar.py` supplies independent scalar Entry-date filtering and vectorized masks over owned trade records. Both feed the existing deterministic metric implementation and the shared frozen policy in `u08_selection.py`. This separates execution, calendar filtering, metrics and policy; expected policy outcomes are tested independently with explicit metric fixtures. Records are never replaced by means of bucket/month metrics.

The inherited execution remains Helsinki→JST, exact entry M1 Open with directional spread, exact exit M1 Open or+1…+4 only, exit availability before path evaluation, entry/exit bar inclusive, same-bar SL first, raw High/Low, no epsilon/interpolation, missing trades omitted, overnight subject to existing constraints, no Monday reconnect, no period crossing, Dec25–Jan3 entry stop, holding30…1440. Existing Stage1/U06/U07 production files are byte-identical.

The engine rejects rows outside `[2020-01-01,2024-01-01)` JST. Calendar views also reject non-Discovery trades and duplicate entries. Filtered streams are recomputed with CloseTime→EntryTime→fixed-key ordering, unrounded Pips, initial cumulative/peak0, and Entry-year attribution.

## DOM

D1=days1–10; D2=11–20; D3=21–EOM, including28/29/30/31. DOM0 means all buckets ON.

Initial individual diagnostics include all metrics, annual metrics, positive/negative year counts, overall/yearly fractions and sample/OFF checks. Minimum sample uses exact integer comparisons: bucket Trades×5 >= DOM0 Trades, overall and each of2020–2023. Fractions are diagnostics only; zero denominators are represented as null rather than used in decisions.

OFF candidates require sample PASS, TotalPips<0, AvgPips<0, FINITE PF<1, and NegativeYearCount>=3. Freeze these candidates once from DOM0. Rank by NegativeYearCount DESC, AvgPips ASC, PF ASC, TotalPips ASC, D1/D2/D3.

Only DOM0, rank1 OFF DOM1, and rank1+rank2 OFF DOM2 can be evaluated. DOM1 must improve DOM0 under every comparison. If rejected, stop at DOM0; no substitute bucket and no DOM2. DOM2 is evaluated only after DOM1 adoption and must further improve adopted DOM1; rejection retains DOM1. Never more than2 OFF buckets; one active bucket is allowed. No new OFF candidates after filtering.

After adoption, the final DOM stream must pass the unchanged U01Equivalent gate: Trades>=150, all annual Trades>=30, Losses>=10, Avg>0, finite PF>=1.10, positive years>=3. Failure produces DROP_U08_DOM_FINAL_GATE. No preceding-state fallback, Month evaluation or replacement.

## Month and Calendar

Only DOM PASS proceeds. M0 is all12 months with formal DOM fixed. Individual diagnostics use Entry JST month1…12. Sample requires combined Trades>=16 and every annual Trades>=3. Initial OFF requires sample PASS, TotalPips<0, finite PF<1, NegativeYearCount>=3; no additional Avg predicate.

All12 LOMO cases are computed from M0, each excluding only its own month with fixed DOM. A formal OFF candidate must satisfy both its initial OFF conditions and every M0→LOMO comparison. Candidate lists never expand after exclusion. Rank using M0 individual diagnostics: NegativeYearCount DESC, Avg ASC, PF ASC, Total ASC, MonthNumber ASC; LOMO improvement magnitude is not a ranking key.

No formal OFF means M0. Otherwise rank1 OFF is M1, reusing that exact LOMO result; a contradictory comparison raises STOP. M2 considers only rank1+rank2, must further improve M1, and otherwise retains M1. Rank3 is never substituted. Maximum2 OFF months; no subset search.

There is no additional Month final U01 gate. PASS_U08 freezes CalendarFreeze={FormalWeekdays, FormalDOMBuckets, OFFBuckets, FormalMonths, OFFMonths}. The only other terminal status is DROP_U08_DOM_FINAL_GATE. U09/Event results cannot change this calendar.

## Artifacts and future U09 projection

Each candidate stores fixed identity/schedule/SL/TP/weekday/Anchor/SetName and U07 source identity; DOM0,3 diagnostics/sample checks/initial candidates/ranking, attempted DOM states/comparisons/adoption/final gate; and, for DOM PASS, M0,12 diagnostics,12 LOMO comparisons, initial/formal candidates/ranking, attempted M states/comparisons and final CalendarFreeze. DROP stores no Month or CalendarFreeze.

Formal completion can write input_identity, preflight, candidate_results, checkpoint_audit, pair_summary, dom_summary, month_summary, calendar_summary, review, artifact_manifest and COMPLETE. Summaries project completed artifacts; they do not rerun policy. Raw M1 is not archived.

A later authorized U08 Result Freeze can project PASS_U08 into U09 input with CandidateID/Symbol/PairRank/Direction, fixed schedule, FormalSL/TP, FormalWeekdays, FormalDOM buckets/OFF buckets, FormalMonths/OFFMonths, U08 status, source candidate/checkpoint hashes and producer identity. This implementation creates no U09 input artifact or performance.

## 56-job runner and durability

One fixed input candidate is one job: baseline trades→DOM→DOM gate→Month if PASS→Calendar→terminal artifact. Import does not start execution. `CHAT_APPROVED_COLAB_B7_U08_ONLY` is required, default unapproved, with Colab and mounted Drive/local-path guards.

User chooses a result-independent run-id through fresh local/Drive root paths. Existing roots reject fresh runs. Reviewed clean SHA, conditions/config/input/release hashes, exact72 M1 metadata/bytes, dependency versions, all tests and bounded replay are mandatory preflight barriers.

Each job writes candidate then hashed local checkpoint, synchronously copies into private Drive staging, verifies hashes/identity, writes DRIVE_COMPLETE last and publishes before proceeding. Incomplete staging is not treated as complete. Completed corrupt/mismatched named jobs reject. Progress contains counts only; all56 local and Drive outputs must agree before COMPLETE_U08_ONLY.

Normal resume requires exact implementation SHA, conditions/full-prespec/U08 config/U07 Result Freeze/U08 input/manifest/all72 data identities/ordered56 IDs and environment including Python patch. Completed Drive jobs restore to local staging without recomputation; missing jobs alone calculate. The all-completed resume route is trap-tested against M1/evaluator calls.

Archive is created only from COMPLETE outputs in a fresh destination. Source member hashes/Bytes and ZIP member contents/CRC are verified; completion is published last. No overwrite, raw M1 copy or force-push workflow is introduced.

## Finalize-Only

`u08_finalize_only.py` and a dedicated notebook are included in the same freeze. Approval is separately `CHAT_APPROVED_COLAB_B7_U08_FINALIZE_ONLY`. Caller must explicitly supply the Chat-reviewed Producer SHA; it must equal reviewed SHA and clean checkout HEAD. Never infer this pin from source. This avoids embedding a commit's own SHA inside itself.

Read-only source consists of identity.json and56 completed job directories with candidate.json/checkpoint.json/DRIVE_COMPLETE.json:169 trusted files. Identity, ordered IDs, source/fixed fields, all hashes, completion and terminal schemas must match. Missing/extra/duplicate/corrupt jobs reject; private partial staging is not opened as a source. Only after56/56 PASS can output begin, in a fresh separate local directory. Source bytes are rechecked; COMPLETE is last.

Only Finalize-Only permits Python patch differences within the same major.minor. NumPy2.3.5 and pandas2.2.3 must match exactly. Normal resume remains exact including Python patch. Recovery verifies frozen test evidence rather than running evaluator tests/smoke.

Trap tests forbid M1/read_mt5/load_discovery, Engine/evaluate, DOM/Month/LOMO/selection and calendar metric recomputation. Recovery only validates completed schemas and projects summaries. Review records Mode=FINALIZE_ONLY, JobRecomputation=false, COMPLETE_U08_ONLY. Replays and normal/recovery aggregation are deterministic.

## Verification and notebooks

`test_results.json` stores actual full-suite counts and names; existing prior-stage tests remain unchanged. New tests cover bucket/calendar boundaries, exact20%, all OFF/comparison boundaries including finite-only PF and null median, ranking/sequential/no-fallback behavior, DOM gate, Month sample/all12 LOMO/no new final gate, fixed-input mutations, nonempty reference/optimized PASS, Discovery/duplicate protection, inherited execution cases,56-job corruption/identity/environment/approval checks, no recomputation, source immutability, fresh roots, completion order, archive, process determinism and notebook defaults.

Bounded actual smoke was fixed before reading its outcomes: USDJPY/EURUSD; six dates2020-01-07,01-14,01-21,02-04,02-11,02-25;09:00 JST entry/30-minute holding, fixed Tuesday, LONG/SHORT, SL15, TP_NONE/10. This spans all3 DOM buckets and2 months with48 trade cases and8 fixed-schedule replays. It compares exact trades, filters, metrics, DOM selection and all12 Month LOMO cases. The tiny formal pipeline correctly drops at the DOM sample gate; Month diagnostics are additionally tested standalone on that same fixed smoke stream, without altering the formal pipeline. Synthetic data separately exercises nonempty PASS and adoption branches. Formal56Used=false, PerformanceSaved=false, FullSearch=false; no formal candidate calendar is produced.

Both notebooks have all RUN flags False and blank approvals/SHA pins. Normal notebook separates mount/install/checkout/input/M1/tests/smoke/preflight/formal/resume/finalize/archive. The dedicated recovery notebook has no M1/evaluator-test/smoke cells. Synthetic Colab tests use the corrected narrowly scoped mapper, preserving real `/content/<repo>` paths.

Status: U07ResultFrozen=true; U08ConditionsFrozen=true; U08ImplementationAuthorized=true; U08ImplementationStatus=FROZEN_READY_FOR_CHAT_REVIEW; U08ExecutionAuthorized=false; U08Executed=false; U09ImplementationAuthorized=false. Stop for Chat review; formal Colab execution needs separate authorization.
