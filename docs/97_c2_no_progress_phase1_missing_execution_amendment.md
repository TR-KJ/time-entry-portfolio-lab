# 97 C2 Phase 1 — missing-execution Plan amendment v2

User-authorized amendment, registered before the resumed formal calculation. Parent stopped-result commit: `5d5f0b17412b713b44a1f651c7a9bd1037eeaa22`. Branch remains `research/c2-no-progress-time-decay-phase1`.

The original Plan `95`, implementation `38a829530d3e73be34e746a604681a0050174c0b`, stopped Result `96`, original notebook and `results/c2_no_progress_phase1/` remain unchanged. They document the first run's VALIDATION_FAIL. This amendment is explicitly informed by its two identified missing execution windows, before any formal NP profit aggregation. It is not an untouched original preregistration.

## Only policy change

When a trade is still open, prior completed-M1 MFE is below +0.25 initial-SL R, and no executable M1 Open exists at the nominal checkpoint or +1 through +4 minutes, retain the complete R0 outcome: original close timestamp, reason, price, pips and R. Record `MISSING_EXECUTION_KEEP_BASELINE`, `Triggered=False`, and paired delta 0R. Retain the trade in every applicable portfolio, period and strategy denominator. No imputation, synthetic bar, extended delay or deletion.

Apply this missing-execution policy consistently to NP50 and NP75. NP50 remains 50% planned duration and strictly MFE < +0.25R; NP75 remains 75% and the same threshold, robustness only. All other execution ordering, fills, MFE boundary treatment, planned-duration rounding, 56-file source manifest, baseline hash, active universe, periods, bootstrap (5,000, seed 20260913), trigger sample requirements, formal A–H, safety thresholds and verdict priority from Plan 95 remain unchanged. A missing-execution case is audited but no longer by itself a VALIDATION_FAIL. Other validation failures still stop the study.

The known cases are Strategy19 entry 2021-06-17 20:56 JST (NP50 checkpoint 2021-06-18 03:28) and Strategy20 entry 2025-01-07 10:01 JST (checkpoint 2025-01-07 13:00). The audit must independently reproduce exactly these two NP50 missing executions and zero NP75 missing executions on the frozen inputs. An unexpected change in this set is investigated as a reproducibility failure, not silently waived. Known missing intrawindow bars remain an input limitation; this amendment does not infer their path.

## Predeclared sensitivity analysis

Primary inference uses all 15,837 active anchors with zero NP50 delta for the two missing executions. Separately remove the union of missing-execution anchor identities (the known two) from BOTH R0 and each NP variant, leaving 15,835 anchors in ALL. Recompute fixed-period paired totals, mean deltas, 95% week-cluster CIs, safety measures and the A–H/verdict diagnostic. Show whether the primary and sensitivity conclusions agree. The exclusion comparison is descriptive only and cannot replace the primary, rescue a failed gate or select strategies. For NP75 remove the same two anchors for a comparable sensitivity universe, even though NP75 has no missing executions.

## Freeze, run and validation

Commit/push this amendment and verify remote Plan SHA before code edits. Create a separate v2 driver, tests/verifier, notebook and output directory. Commit/push tested implementation and verify remote SHA before full input audit/R0 replay/NP outcomes. Repeat baseline SHA, 56-file hash/row/bounds audit, ALL28 and ACTIVE27 zero-mismatch R0 gate. Test missing fallback as full R0 identity and zero delta, distinct classification, retained denominators and excluded-both-sides sensitivity. Independently verify representative M1 decisions, both missing cases, every paired delta, recovery classification, aggregate totals, week bootstrap and gates for primary and sensitivity.

Publish new Result `98`, `results/c2_no_progress_phase1_v2/` and a separate v2 notebook. Keep full trade detail local with byte count/SHA. Notebook includes source audit, reconciliation, missing policy/counts, primary/period/trigger/recovery/NP75/strategy tables, sensitivity, gates and verdict; Colab output `/content`, Drive save OFF. No Phase 2 money simulation now, and no EA/SET/RunId/VPS/risk/live/Dell Phase 5 changes.
