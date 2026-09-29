# B6 Stage2-A implementation freeze — 2026-09-29

## Scope and input identity
Stage1 completed in user-run Colab: 4,032/4,032 jobs, COMPLETE_STAGE1_ONLY, 689,738 passing structures, exactly 50 representatives. Work verified candidate bytes/count/unique IDs, effective config, identity code/config SHA and progress locally. No candidate performance or rankings are published by the smoke test.

Stage1 immutable commit: `920b9be5c8f1bcf46a46dbbd4ac06dc19eb295b1`.
Candidate SHA256: `82a71c1ac9ffaa9a121795c6e0186bf77af5185b90bc21f65d7174161c35214f`.
Stage1 effective config SHA256: `93cc9a92c6473cf770f98b72511de076375411db1c27ae1568f976f96212b37e`.
Exact bytes are read from Drive; no guessed/reconstructed copy is committed. Paths are operational parameters, not scientific identity. Count, hashes, Stage1 identity, canonical unique CandidateIDs and structural bounds are hard gates before M1 loading. Performance fields in the Stage1 input are ignored; the 50 identities and time structures remain unchanged and output follows original input order.

## Implementation map
- `stage2a_config.py`: immutable config hash, candidate gates, Decimal ROUND_HALF_UP grid, per-SL deduplication, expected count 1,500.
- `stage2a_engine.py`: independent reference replay through unchanged Stage0 execution; dedicated fast TP extension through unchanged Stage1 exit eligibility/SL first hits and first TP hit. TP wins only when strictly earlier than SL; ties are SL.
- `stage2a_metrics.py`: raw-R metrics and P02 reasons for every condition, including failed conditions and zero-trade conditions.
- `stage2a_search.py`: explicit Colab/Chat/SHA/release guard, 56-input audit, candidate checkpoints, resume identity, complete output and review bundle.
- `stage2a_smoke.py`: bounded compatibility-only first three input candidates, two extreme fixed SL values, TP_NONE/0.5R/2R, first matching weekday in February in each Discovery year. No candidate scores or rankings saved.
- `notebooks/b6_stage2a_tp_discovery.ipynb`: all action flags default False; default execution displays frozen config only.

## Grid and semantics
All seven fixed five-SL grids are identical to Stage1. Each SL has TP_NONE and ratios 0.5/1/1.5/2/3. Decimal half-up to multiples of five pips, minimum five pips; SL25 × 0.5 becomes TP15 (actual ratio 0.6). Original ratio, actual ratio and aliases are retained. Deduplication occurs only within that SL; NONE is always retained. Fixed grids have exactly six unique conditions per SL, thirty per candidate, total 1,500; any discrepancy stops execution.

Discovery only: 2020-01-01 inclusive through 2024-01-01 exclusive in canonical JST. The audit loader may read mixed-period source bytes to verify identity and canonical timezone, but copies/slices Discovery before returning price arrays to either executor. No future-performance API is provided.

Unchanged historical execution: adjusted Entry Open ± fixed spread; SL and TP from adjusted Entry; raw High/Low; entry and chosen exit bars included; no epsilon, interpolation, new price rounding or slippage. First available scheduled exit through +4 minutes is secured before any path replay, even if an earlier SL/TP exists. Missing Entry or all five Exit choices means no trade. Time exit uses chosen Open. Year-end Entry stop December 25–January 3, overnight allowed, no weekend bridging. Intermediate path diagnostics cover Entry through secured Exit, including bars after an early close, matching Stage1 semantics.

## Metrics and outputs
Formal metrics use unrounded R. Trade display is Pips6/R9. Zero R counts as a trade, neither win nor loss. PF is positive sum / absolute negative sum; INF/UNDEFINED are text labels, not substituted large numbers. MaxDDR starts at zero equity; weekly structures holding at most 24 hours are non-overlapping, so Entry order and Close order agree.

Gate: at least150 total trades, at least30 each Discovery year, at least10 losses, PF>=1.10, positive TotalR in at least3/4 years. It labels Pass/Fail with all reasons; it never prunes work. AvgLossR is signed negative mean. Ratios are fractions, not percentages. No formal rank or Stage2-B center file is generated. N06b remains deferred until Chat reviews Stage2-A results.

Default `/content/b6_stage2a` includes identity.json, effective_config.json, candidate_input_audit.json, search_space.json, progress.json, checkpoints.json and per-candidate JSON shards; stage2a_all_results.csv.gz, stage2a_yearly_results.csv.gz (6,000 rows), stage2a_diagnostics.csv.gz, stage2a_summary.json, stage2a_review.json and stage2a_review.zip. Full and yearly schemas cover all requested metrics, schedule identity, SL/TP/mode/ratios; diagnostics include exit counts/rates, fallback and missing opportunities/path counts. Full trade logs/raw M1 are not retained.

Review ZIP contains all three compact result tables, review provenance and summary/config/search/progress. Local identity retains 56 filename/hash pairs for resume, while review JSON retains their count and aggregate identity digest rather than duplicating that local inventory. Candidate IDs are retained in candidate audit/results. Resume needs the entire output folder; ZIP alone is for review, not resume.

## Safety and recovery
Code SHA, fixed config SHA, candidate SHA, Stage1 provenance, all56 M1 hashes and Python/NumPy/pandas versions must match on resume. NumPy2.3.5 and pandas2.2.3 are frozen. Python version is recorded and must remain identical within a resumed run. Each candidate job is atomic JSON followed by an atomic checksum ledger. A crash before ledger update recomputes only that uncommitted job; committed corrupt/missing shards stop. Finalization requires every expected candidate and ordered SL/TP key, all1,500 conditions, all6,000 yearly records. Partial tables must not be interpreted before COMPLETE_STAGE2A_ONLY. Resume reruns finalization after a final-output interruption.

Tracked Stage1 executable files/config/notebook/release manifest and baseline remain byte-identical. Plan/register now describe Stage2-A. The Stage1 release regression checks its immutable commit for all historical files and additionally checks current bytes for Stage1 executables; only evolving Plan/register and that regression file are archival-only. Stage2-A has a separate release manifest covering its own code plus shared dependencies, docs, tests and notebook.

## Stop point
Only unit/synthetic/regression/reference-fast/limited actual-data smoke/notebook-default/release checks run in Work. No Stage2-A production sweep, Stage2-B/3, Event Filter, Validation, Monitor, portfolio simulation or live/EA changes.

WorkではStage2-A full sweep未実行。Chat確認後にGoogle Colabで実行する。
