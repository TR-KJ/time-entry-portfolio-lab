# Stage10 Incremental Portfolio / Money Simulation Implementation Freeze

## Latest user instruction supersedes the initial Global R2 comparison

The initial request specified current27 + Global R2, then the user considered Global R2 for existing27 and fixed risk for B6. The **final explicit instruction** is: all existing27 and both B6 candidates use fixed 0.25 / 1.0 / 1.5 / 2.0% per trade. Accordingly Stage10 applies **no Global R2 overlay to any component or configuration**. This is a fixed-risk counterfactual on the current static27 strategy set, not a reproduction of current operational R2 money results. The operational R2 table, EA, SET and deployment state are untouched. No missing R2 assignment is replaced by a fallback or regenerated from M1; the assignment is not an input to this revised study.

Global R2 was identified, not guessed: R2_GLOBAL / R2_MODERATE is a volatility-dependent risk allocation overlay, not a trade stream or entry filter. Q1–Q5=.50/.70/.90/1.10/1.30%, unavailable/insufficient=.90%; Primary daily ATR20 SMA with preceding252-day midrank. Its source paths, commits, exact SHA256 and immutable public source copies are preserved in stage10_portfolio_baseline.json and stage10_provenance. Research source is volatility_phase3; operational specification/code is Phase5 at 5e93a8834e27d4d9ffdbc2980906511f74ddb27a. This record prevents confusion between disabling R2 **in this study by user instruction** and altering live policy.

## Baseline and B6 hard gates

Formal baseline: `daily_stop_baseline_trades.csv`, SHA256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`, 28 strategies / 16,298 trades. Exclude only exact `22_GA_C_2`: 27 strategies / 15,837 trades, of which 9,083 enter in [2020-01-01,2026-09-10). Retain `20_EA_1A_MonTue_Short`. Portfolio Revision #1 records the decision; Phase5 SET independently has exactly22 OFF and other27 ON. The decision document itself says PENDING_VERIFICATION for actual live application; no claim of independent live verification is made. All exact strategy IDs and provenance are in the baseline artifact.

Stage9 Freeze e66c54b65ca4ee2e6f7f730a1adc69a3357cfdcd. Final Candidate SHA256 e154b03d92f3af5d0108ec983fe3843ef374cf64a6e5f5d5feb54a3014108562. Exactly:

- AUDJPY `B6-AUDJPY-L-W0-E0950-H1440`: Monday15:50 → Tuesday15:50 JST, Long, SL20, TP_NONE, E0.
- GBPJPY `B6-GBPJPY-L-W0-E0835-H1415`: Monday13:57 → Tuesday13:31 JST, Long, SL30, TP_NONE, E0.

B6 uses the original Stage8 `stage8_trade_ledger.csv.gz`, SHA256 af0caed1d3002af960042d56e50e290271a3aced5a82ee879997a30d4e418248. Filter only those IDs: AJ339 + GJ338 =677 trades from the3043-row source. Preserve saved raw R, actual entry/close and all Stage9 conditions; no optimization or replay. Work performed hash/schema/identity/schedule/R consistency audits only. Current27+B6 have zero reporting-boundary and Monday06-week crossings in the 2020+ input. Missing/changed inputs, duplicate source rows, condition mismatches or crossings hard-fail; no repair or truncation.

## Fixed matrix and periods

P0_CURRENT = current static27 under fixed risk, Global R2 OFF in this study.
P1_CURRENT_PLUS_AJ = P0 + AJ only.
P2_CURRENT_PLUS_GJ = P0 + GJ only.
P3_CURRENT_PLUS_B6_BOTH = P0 + AJ + GJ.

Exactly four risks .25/1/1.5/2%, two modes, 32 jobs. Each job uses the same per-trade risk for every existing and B6 trade. B6 additions increase gross/concurrent stop-risk intentionally; no equal-total-risk scaling, new risk points, best-risk choice, threshold, score or ranking. P3−P0 is primary; P1/P2 are fixed contribution diagnostics and never cause reselection.

CONTINUOUS_2020 starts500,000 JPY at2020-01-01, ends2026-09-10 exclusive; no capital or DD-peak reset in2024/2026. Reporting periods: Discovery [2020,2024), Validation [2024,2026), Monitor [2026-01-01,2026-09-10), PostDiscovery [2024-01-01,2026-09-10), FullAvailable [2020-01-01,2026-09-10).
POSTDISCOVERY_RESET_2024 independently starts500,000 JPY at2024-01-01; reports Validation, Monitor and PostDiscovery only. This is a **post-selection diagnostic**, not fresh/unseen OOS. No Monitor-only reset. Total period-result rows=128; incremental rows=96; decision-evidence rows=32.

## Money semantics and inherited implementation

Unchanged src/research/edge_decay_phase2_money_simulation.py supplies baseline loading, week_start and period metrics. Stage10 wraps its semantics in a component-aware settlement loop and does not import/call its adoption decision function. Decimal precision40, no internal money rounding. Weekly start=JST Monday06:00; Sunday and Monday pre06 belong to previous week. First weekly base500,000 JPY; all entries inside a week have RiskAmount=WeeklyBase×RiskPct/100. Prior-week closed PnL compounds the next week; no intra-week compounding, floating equity, interest or invented transaction costs.

Existing trade PnL retains historical arithmetic RiskAmount×Pips/SL after savedR integrity check <=1e-8. B6 PnL=RiskAmount×saved rawR, with Pips/SL consistency check <=1e-12. These are source integrity checks, not rounding or selection tolerances. Settlement order=CloseTime→EntryTime→PortfolioComponentKey→source RowId. Existing StrategyNo remains an audit field; B6 has no assigned StrategyNo. Nonpositive weekly or closed balance rejects the run.

EntryTime JST determines reporting membership; CloseTime determines settlement. Crossing any reporting boundary or entry trading-week end rejects input. The inherited period metrics use carried capital and mode-wide DD peaks; period metrics never silently reset peak. Initial capital is included in peak. MaxDDJPY/MaxDDPct are positive. WorstDayPct uses close-day net PnL/day-start balance; WorstWeekPct uses Monday06 close-week PnL/week-start balance; losses are negative. MoneyPF=positive YenPnL / absolute negative YenPnL; no losses=>UNDEFINED. MoneyRoMD=NetProfitJPY/MaxDDJPY; noDD=>UNDEFINED.

Each P1/P2/P3 metric subtracts the corresponding same-risk/mode/period P0. DD delta<0 improves and>0 worsens; more-negative WorstDay/Week delta worsens. FinalCapital interaction=(P3−P0)−[(P1−P0)+(P2−P0)], an audit of compounding non-additivity only.

## Risk load and exposure

Weekly Trades/BaselineTrades/B6Trades and GrossRiskAllocationPct=Trades×RiskPct are saved. Gross allocation is hypothetical full-stop loss allocation, **not actual loss**. Open intervals are half-open [EntryTime,CloseTime); zero-duration trades contribute trade counts but no elapsed exposure. Closings precede openings at tied times. MaxConcurrentRiskPct=simultaneous positions×RiskPct, a stop-risk proxy against that entry-week base, **not broker margin**. AvgConcurrentPositions is elapsed-time weighted across the entire reporting calendar interval including zero-exposure minutes.

Save Max/Avg concurrent positions and MaxConcurrentB6Positions, AJ/GJ both/either-open minutes/Jaccard, weeks both trade and weeks simultaneously open. No either-exposure=>UNDEFINED Jaccard. Each candidate's overlap uses the union of any existing open positions and the union of same-symbol existing positions; multiple existing trades do not double-count overlap minutes. Candidate-specific maximum counts existing positions plus that candidate while it is open.

Money mode is THEORETICAL_UNCAPPED. It is not live EA replication: live uses Monday00 JST equity snapshot, MaxAutoLot, AllowMinLot, volume min/max/step and tick/pip valuation. No actual lot, JPY margin or margin level is fabricated. EA_CONSTRAINED=NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS.

## Colab release and output guards

Notebook: notebooks/b6_stage10_incremental_portfolio.ipynb. PREPARE_ENVIRONMENT, MOUNT_DRIVE, RUN_STAGE10_FULL, CHAT_CONFIRMED_STAGE10_FREEZE and SAVE_OUTPUT_TO_DRIVE default False; STAGE10_FREEZE_SHA is empty. Default run-all displays definitions only, with no IO/simulation. Set sys.dont_write_bytecode=True before b6 import and retain strict clean checkout guard.

Required paths (confirmed synchronized source mapped to MyDrive):
- /content/drive/MyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/daily_stop_baseline_trades.csv
- /content/drive/MyDrive/b6_stage8_archive/stage8_trade_ledger.csv.gz

Frozen repo inputs contain Stage9 identities, baseline, source spec and provenance. No M1 or R2 feature assignment path is used. Formal execution requires Google Colab, both run/Chat flags, exact clean Stage10 commit, Stage9 ancestry, release manifest/config/input hash agreement, and Python3.13.15 / NumPy2.3.5 / pandas2.2.3. A runtime mismatch stops rather than alters semantics.

Output=/content/b6_stage10; Drive archive=/content/drive/MyDrive/b6_stage10_archive. Resume requires identical code/config/input/runtime identity and exact checkpoint hashes. Progress shows completed job count only. All32 jobs and128 period rows must exist before formal outputs/display. identity/effective_config/input audits/progress, eight required gzip CSV tables, summary/review JSON and compact review ZIP are emitted. ZIP excludes raw baseline/B6 ledger and per-trade logs. Drive copy requires matching destination identity and byte verification. Gzip mtime0 and fixed ZIP timestamps make exports deterministic.

## Validation and stop point

Synthetic tests cover manual capital/DD/day/week/PF/RoMD, week rollover/compounding, exact risks/configs/modes, no normalization, raw B6R, legacy money regression, simultaneous exposure/overlap/ties, non-additive interaction, input/config/release/runtime/resume/display guards, fresh-checkout bytecode cleanliness and complete32-job synthetic export/resume. All historical assertions remain unchanged at exact historical snapshots for release checks; current engine tests are retained.

Work audit contains no actual capital/DD/delta calculations. Stage10 full Money Simulation, actual terminal wealth/DD comparison, broker-constrained simulation, risk allocation/RiskPct choice and live adoption are not executed. No EA/SET/VPS/live modification or Strategy29+ numbering. PASS != live adoption. Stop at Implementation Freeze; formal Colab execution follows Chat confirmation.
