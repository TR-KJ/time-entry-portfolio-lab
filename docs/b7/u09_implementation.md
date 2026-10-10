# B7 U09 Implementation Only — 1-minute Entry / Exit Fine Tune

Status: FROZEN_READY_FOR_CHAT_REVIEW. Implementation and synthetic/bounded-smoke validation only. U09ExecutionAuthorized=false; U09Executed=false. No formal54 Best shift, FineTune or Anchor-retain results are generated, opened or saved. U10/U10-P/Candidate Freeze/Validation/Monitor are NOT_RUN.

## Immutable prerequisites

- Original Conditions Freeze: `5dbac7af2d41aa912308868e6ad1a6dbf7cdd107`.
- U09 Supplemental Conditions Freeze: `1466a2c3e8b3d523233c45d665a6cac21e974393`.
- Supplemental prespec SHA256: `cefa5aed9fc820c8bbf4dd4a57622263cd2443bc8509f8016f62bb20e76a92f3`.
- U08 Result Freeze: `382f351c169da48e1fe4eadf31fc858bbd57eed0`.
- U08 Producer: `0b33aa5ff6ff769b11212e9b8593242fb71c680c`.
- U09 selected54 input SHA256: `8faa886c3d1a72e8020688b8931481d81d1df637d63b0b368e0171b8d1dce2ca`.

`u09_input.py` audits the exact ordered PASS54 projection against frozen U08 identity,169-file checkpoint hash records,Calendar summary,Archive hashes and original U08 input. DROP EURUSD ranks5/8 cannot re-enter. NoReplacement=true. The supplemental prespec and doc hashes are pinned separately; original conditions files are unchanged.

## Schedule and execution

The Original Five-Minute Anchor is the input schedule. Stage1 CandidateID remains lineage identity. The only variable fields are Entry and Exit. Each integer shift pair in [-5,+5]² occurs once, including0/0:121 nominal points, maximum6,534 across54 jobs. Datetime arithmetic shifts planned Entry/Exit once and recomputes holding and exit-day offset. Entry date/weekday change, exit-day-offset change, holding outside30–1440 or execution-invalid schedules are excluded, never Formal FAIL. Minute-of-day modulo is not used to repair invalid dates. No ±6, re-anchor or extension.

Calendar membership uses planned Entry JST date and fixed FormalWeekdays/DOM/Months. OFFMonths order and every CalendarFreeze field,Symbol,Direction,FormalSL/TP,AnchorWeekday,SetName and source identities are retained. Trade execution directly reuses unchanged U06 optimized and scalar kernels: exact Entry Open, frozen spread/pip size, exact Exit then +1…+4 fallback only, exit availability before inclusive raw High/Low path, same-bar SL first,no epsilon/interpolation,weekend reconnect prohibition,period boundaries and Dec25–Jan3 Entry stop. Missing trades remain absent, never zero Pips. Only [2020-01-01,2024-01-01) JST reaches either evaluator. Metrics are recalculated from unrounded trade records with unchanged annual attribution and deterministic DD order.

Point fixed key follows U04 field order using shifted schedule values: Symbol,direction LONG before SHORT,AnchorWeekday,EntryMinute,ExitDayOffset,ExitMinute,HoldingMinutes,original CandidateID. During trade aggregation the weekday component is the actual planned Entry weekday, as in previous multi-weekday stages. The schedule fields uniquely identify a point within one original anchor; filesystem/DataFrame/completion order is never a tie-break.

## Point Gate, Plateau and supplemental semantics

Point Formal PASS is unchanged U01Equivalent:Trades≥150,each of2020–2023≥30,Losses≥10,AvgPips>0,FINITE PF≥1.10,PositiveYearCount≥3. No absolute DD cap.

Every center reads its ±1×±1 neighborhood from the cached point map. No execution is repeated for neighborhoods. Outside ±5 and schedule-invalid points are excluded. Formal FAIL valid points remain included. Plateau requires center Formal PASS,at least4 valid points,`PASSCount*3 >= ValidCount*2`,and all-valid Median Avg≥center Avg×0.80. All boundaries use internal values. Neighborhoods do not require neighbors to be Plateau PASS.

U09-S01: PF median includes schedule-valid FINITE non-null PF values, whether Formal PASS or FAIL. INF/UNDEFINED/null are excluded without sentinels or state ordering. Even finite populations use arithmetic mean of the central values. Empty finite population for a ranking-eligible center stops with invariant error.

U09-S02: a valid null Avg remains valid,counts in the PASS denominator,and fails Point Gate. Any null in the all-valid neighborhood makes its Avg median undefined and Plateau false,with `UNDEFINED_VALID_NEIGHBOR_AVG`. Nulls are not removed,filled or replaced. Formal PASS center with null Avg is an invariant error. Anchor baseline uses the same all-valid/null semantics without a new minimum-valid-count gate.

Only Plateau PASS centers rank by Neighborhood Median Avg DESC,finite Neighborhood Median PF DESC,Center MedianAnnualAvg DESC,L1 ASC,then fixed key. L1=abs(EntryShift)+abs(ExitShift),relative to the original anchor only.

## Adoption and terminal result

Baseline is Anchor Neighborhood Median Avg,not Anchor center Avg. Required improvement is `max(0.05, AnchorBaseline*0.025)`; unrounded exact boundary qualifies. Negative/zero baseline retains the0.05 floor without absolute-value conversion.

Decision precedence is fixed:

1. No Plateau → ANCHOR_RETAINED_NO_1M_PLATEAU.
2. Best is0/0 → ANCHOR_RETAINED_BEST_IS_ANCHOR.
3. Best non-anchor and baseline undefined → ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE.
4. Insufficient improvement → ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT.
5. Otherwise → FINE_TUNED.

No rank2 fallback. All terminal candidates are PASS_U09; U09 never drops a candidate. Retain means exact original schedule and0/0 shifts. Result artifact stores original lineage/source/Calendar,AnchorSchedule and explicit AnchorEntry/Exit/Offset/Holding,all point metrics and invalid reasons,all Plateau diagnostics and membership,ranked IDs,BestCandidate,AnchorNeighborhood,baseline/required/actual improvement,decision,and FormalEntry/Exit/Offset/Holding with shifts. PF state remains separate from nullable numeric value.

## Independent verification

`u09_reference.py` independently implements datetime schedule/invalid logic,scalar trade/calendar evaluation,Point Gate,neighborhood median/count/ratio,ranking,baseline and adoption. The optimized path uses the U06 Engine plus vector calendar date filtering. Only deterministic metric primitives and output serialization are shared; the reference does not call optimized schedule or selection policy. Synthetic tests include full121-point replay,nonempty four-year streams,all adoption reasons,all supplemental edge cases,ranking priorities,execution compatibility and calendar/isolation checks.

Actual smoke is fixed in config before evaluation:USDJPY/EURUSD,LONG/SHORT,SL15,TP_NONE/10,Entry09:00,Holding35;2020 Jan7/14/21 and Feb4/11/25;Entry/Exit shifts-1/0/+1 only. Eight fixed-schedule replays,72 point cases,432 trades match exactly through execution,metrics,Plateau and decision. Formal54Used=false;FormalScheduleProduced=false;PerformanceSaved=false;FullSearch=false. The actual tiny stream does not establish formal Gate eligibility; synthetic four-year tests exercise positive Plateau/adoption paths. No per-case actual performance or decisions are saved in smoke evidence.

## Runner, durability and recovery

One fixed input candidate per job,54 jobs. Import performs no formal execution. The runner requires Colab and `CHAT_APPROVED_COLAB_B7_U09_ONLY`,explicit reviewed clean HEAD,release integrity,input/supplement audits,pinned dependencies,all tests,72 exact M1 audits and bounded smoke. Preflight asserts both prerequisite commits are ancestors.

Identity binds Producer Implementation SHA,Original Conditions SHA,Supplemental Freeze SHA and prespec hash,full prespec/config,U08 Result Freeze,input hash,M1 manifest/all72 metadata,ordered54 IDs,and exact Python patch/NumPy/pandas. Fresh roots must not exist; resume requires exact identity. Completed Drive jobs are hash/schema-validated and reused without candidate performance recomputation. Normal preflight still performs required tests/M1 audit/bounded synthetic-schedule smoke; this is distinct from Finalize-Only recovery.

Each local job writes candidate then checkpoint;Drive copying uses private staging,hash verification and DRIVE_COMPLETE written last before publishing. Interrupted staging is never a completed job. All54 local and Drive objects must agree before final outputs. Intermediate progress exposes counts only. COMPLETE_U09_ONLY is written last. Archive uses fresh destination,whitelisted JSON artifacts,no raw M1,verified copy hashes/sizes,ZIP exact inventory/size/hash/CRC and final completion marker.

Finalize-Only requires separate `CHAT_APPROVED_COLAB_B7_U09_FINALIZE_ONLY`. Caller explicitly pins Producer=reviewed SHA=clean checkout HEAD; source may not choose its Producer. It accepts Python patch changes within the same major.minor and requires exact NumPy2.3.5/pandas2.2.3. Normal resume retains exact patch policy.

Trusted source is identity.json plus54 candidate/checkpoint/DRIVE_COMPLETE triples (163 files). Missing/extra/duplicate/corrupt/hash or identity mismatch stops. No outputs are written before54/54 audit. Source is read-only; fresh separate local output required. Only persisted schema consistency and aggregation are performed: no M1/read_mt5/load_discovery/Engine/evaluate/grid generation/Plateau/ranking/Anchor comparison/selection. Trap tests enforce this. Finalizer outputs input/preflight,finalize metadata,source audit,candidate results,checkpoint audit,pair/decision/shift summaries,review,manifest,and COMPLETE last. Replay is deterministic and source bytes remain unchanged.

## Notebook and future projection

`b7_u09_1m_finetune.ipynb` and `b7_u09_finalize_only.ipynb` have all RUN flags False and blank approval/reviewed SHA values. Mount/install/checkout/input/M1/tests/smoke/preflight/formal/resume/finalize/archive are separate guarded cells. Synthetic path mapping does not redirect real Colab repository files.

Future U09 Result Freeze can project54 results into U10:CandidateID,Symbol,PairRank,Direction,FormalSL/TP,CalendarFreeze,FormalEntryMinute/ExitMinute/ExitDayOffset/HoldingMinutes,EntryShift/ExitShift,Decision,candidate/checkpoint hashes and Producer identity. This implementation generates no actual U10 input. U10/Event/U10-P/Candidate Freeze/Validation/Monitor and EA/SET/VPS/live changes remain outside scope.
