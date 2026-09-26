# 96 C2 No-Progress / Time-Decay Exit Phase 1 — execution-coverage stop

**Verdict: VALIDATION_FAIL. Phase2Eligible: False. NP50 profit effect is NOT_EVALUATED.**

Run date: 2026-09-26 JST. Branch: `research/c2-no-progress-time-decay-phase1`.
Plan SHA: `1b211146d4aa7610df9663693e586890d4dba4fe`.
Frozen implementation SHA: `38a829530d3e73be34e746a604681a0050174c0b`.
Both were pushed and their remote SHA verified before proceeding to the next stage.
Result SHA is the commit containing this document, recorded in the final handoff (avoids a self-referential hash).

The fixed rule is NP50: at 50% of planned duration, exit at M1 Open only if prior completed-M1 MFE never reached +0.25 initial-SL R. NP75 is robustness. No checkpoint or threshold search was conducted. The 2022–2026 observations are previously viewed, not a pristine unseen holdout.

## Input and R0 verification

Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`.

- 28 strategies / 16,298 fixed trades; active 27 / 15,837 after excluding Strategy22's 461 trades.
- All 56 M1 source hashes, row counts and raw first/last timestamps matched the frozen manifest.
- R0 reconstructed from M1: ALL28 16,298/16,298, ACTIVE27 15,837/15,837; **zero mismatches** in identity, timestamps, reasons, prices, pips and R.
- Formal R0 Total R: **1,360.253363762R**, consistent with the reconciled fixed baseline.
- Europe/Helsinki → Asia/Tokyo → naive JST conversion and source selection unchanged. No broker splicing or synthetic bars.

The source hashes passing means the same audited files were used; it does not imply that every newly introduced checkpoint exists in those files.

## Frozen stopping condition encountered

The published Plan requires stopping formal analysis if an otherwise open no-progress trade lacks an executable checkpoint Open at the exact minute or +1 through +4 minutes. **Two formal NP50 trades meet this stopping condition.** The missing fraction is 2/15,837 (0.01262866%). The Plan specifies zero tolerance for missing executions; no trade was dropped, assigned a substitute fill or moved to a later checkpoint.

| Strategy | Entry JST | Planned minutes | NP50 checkpoint JST | Prior MFE R | Previous M1 JST | Next M1 JST | Delay |
|---|---|---:|---|---:|---|---|---:|
| 19 / EURAUD Long | 2021-06-17 20:56 | 784 | 2021-06-18 03:28 | 0.154444444 | 2021-06-18 03:24 | 2021-06-18 04:32 | +64 min |
| 20 / EURAUD Short | 2025-01-07 10:01 | 359 | 2025-01-07 13:00 | 0.174000000 | 2025-01-07 11:02 | 2025-01-07 14:03 | +63 min |

Both remained open under baseline at the checkpoint, had not reached +0.25R on available completed bars, and had no prior SL/TP hit. The independent diagnostic parses the original raw files directly, verifies their hashes, converts timestamps and recalculates the checkpoint, entry fill, MFE and missing +4-minute window. The absence is in the supplied source data; its upstream cause is not determined. Missing bars may also obscure unobserved path movement, so no missing-path inference is made.

Affected files:

- `EURAUD_M1_202101040002_202212302354.csv`, SHA-256 `83a444c425953805d57b8b854966e136982159f2e5aa034b044d42a0c4abd726`.
- `EURAUD_M1_202501010000_202512310000.csv`, SHA-256 `f76a558640c5950395b3a5cda30ed34cf21d148877e9485cbcc723e70ac0ea31`.

## Scope of computed and uncomputed results

NP50 and NP75 per-trade replay reached the execution-coverage check. NP50 has 2 missing executions; NP75 has 0. Formal outcome aggregation was not entered, and no complete trade-detail result was published.

| Required item | Status |
|---|---|
| R0 Total R | 1,360.253363762R; reconciled baseline |
| NP50 trigger count / rate / weeks | NOT_EVALUATED |
| NP50 Total R, Delta Total R, Avg Delta R, empirical 95% CI | NOT_EVALUATED |
| Historical / Recent Combined / Recent A / Recent B / 2026 effects | NOT_EVALUATED |
| NP75 performance robustness | NOT_EVALUATED; 0 missing execution bars only |
| Recovery / later TP rates | NOT_EVALUATED |
| Improved / harmed / unchanged counts | NOT_EVALUATED |
| Worst Day / Worst Week / MaxDD comparison | NOT_EVALUATED |
| Strategy-level profit signals | NOT_EVALUATED |
| Formal gates A–H | NOT_EVALUATED because the validation prerequisite failed |

The corresponding requested summary CSVs are explicit NOT_EVALUATED status records, not numerical result tables. Do not interpret this as NOT_SUPPORTED, zero effect, zero triggers, or a negative empirical finding.

## Validation and interpretation

13/13 synthetic tests passed, covering planned-duration rounding (50% and 75%), overnight handling, Long/Short MFE, spread, exact +0.25R equality, giveback, checkpoint-bar exclusion, Open precedence, earlier SL/TP, same-bar SL-first, +4 fallback/missing bars, recovery, paired delta and a separate synthetic bootstrap calculation. The post-run source-gap diagnostic passed 6/6 checks. Full empirical paired-delta and bootstrap verification was not run, because no formal outcome table exists.

C1 intervened after favorable milestones (+0.5R and +1.0R); C2 asks about trades that never reached +0.25R by a planned checkpoint. That distinction is preserved. This C2 run cannot answer whether waiting has positive or negative value and provides no strategy-specific adoption signal.

## Decision and artifacts

**No formal candidate. No Phase 2 or money simulation.** The current frozen study stops here. Any attempt to resolve the source gaps or change the missing-execution policy requires an explicit, separately documented data/Plan revision before a new formal run; this report does not authorize retuning or selective exclusion.

Dell Volatility Phase 5 remains Global R2 only. EA / SET / RunId / VPS / risk / Demo / live were not changed.

Artifacts: Plan `docs/95_c2_no_progress_time_decay_phase1_plan.md`; this result; frozen implementation `src/research/c2_no_progress_phase1.py`; 13-test suite `tests/test_c2_no_progress_phase1.py`; full-result verifier `tests/verify_c2_no_progress_phase1.py` (not run on this stopped study); post-run gap verifier `tests/verify_c2_checkpoint_coverage.py`; `notebooks/c2_no_progress_phase1.ipynb`; published CSVs under `results/c2_no_progress_phase1/`. Publication manifest records every published CSV's bytes and SHA-256 and states that no complete trade detail was produced.
