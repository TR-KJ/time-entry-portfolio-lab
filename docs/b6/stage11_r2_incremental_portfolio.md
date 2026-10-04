# B6 Stage11 B6 × Global R2 Incremental Portfolio Implementation Freeze

Current27 will use R2 as planned future policy. This implementation does not change live operation. GJ is the first/core B6 candidate. AJ is evaluated only conditional on GJ; no AJ-only adoption or portfolio exists.

## Frozen identities

Stage10: `0b8a8507b5021baeded4fcfc5fb3f1ce1644cc7d`.
Stage9: `e66c54b65ca4ee2e6f7f730a1adc69a3357cfdcd`.
Stage9 final candidates: `e154b03d92f3af5d0108ec983fe3843ef374cf64a6e5f5d5feb54a3014108562`.
Stage10 baseline artifact: `2c91a08486fb536ecf0a5a8bdec2afd77c748299919eec12738e951972681215`.
Full baseline ledger: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`.
B6 ledger: `af0caed1d3002af960042d56e50e290271a3aced5a82ee879997a30d4e418248`.

R2_GLOBAL / R2_MODERATE is a VOLATILITY_DEPENDENT_PER_TRADE_RISK_OVERLAY. It is not a trade filter, entry filter, strategy selection or ATR P70 filter. All trades, including Q1 and normal-history fallback, remain.

Phase5 source commit `5e93a8834e27d4d9ffdbc2980906511f74ddb27a`:

| Source | SHA256 |
|---|---|
| `docs/63_volatility_phase5_plan.md` | `37d89f9ec2f63cd499d393360b0a7d78488c90ff19e1524ebbcb4e5a922ec75d` |
| `src/EA/phase5_demo/vol_r2_core.mqh` | `28fc8fca8f8ac4bab01101f5812dfe40fb4ba7a0d9c0eff7148692fe2e1754bf` |
| `src/research/volatility_phase5_audit.py` | `68d385daa8bf6239a120c88bd26d151ec91842a212549aa7af9e4f97ebf98702` |

Exact source content is embedded with commit/path/SHA identity. The independent Phase5 Python `feature()` is executed unchanged against synthetic fixtures and, in Colab, per unique symbol/day against daily-equivalent OHLC rows preserving LastM1JST. Its OANDA New York server-clock helper is not used for B6 data: B6's frozen Helsinki conversion applies before the shared JST daily feature contract. Additional hand fixtures independently verify ATR/rank/percentile/quintile/risk.

## Absolute risk and feature contract

| State | Risk percent |
|---|---:|
| Q1 | 0.50 |
| Q2 | 0.70 |
| Q3 | 0.90 |
| Q4 | 1.10 |
| Q5 | 1.30 |
| FALLBACK | 0.90 |

No scale or normalization. Europe/Helsinki → Asia/Tokyo → naive JST, with inherited ambiguous=infer and nonexistent=shift_forward. Actual JST dates use first Open/max High/min Low/last Close. Candidate date and all future dates are excluded. No synthetic calendar days; actual Saturday included. TR starts at High-Low, subsequently max(High-Low, abs(High-previous actual Close), abs(Low-previous actual Close)). ATR20 is the simple math.fsum of last20 actual TR divided by20, never Wilder. Current is last eligible completed daily ATR; references are preceding252 ATR excluding current. Minimum272 actual dates.

n=2×count(ref<current)+count(ref==current), percent=100n/504. Quintile is 1+count(5n≥cut), cut=504/1008/1512/2016; equality goes upward, no epsilon. Normal insufficient history gives INSUFFICIENT_VOL_HISTORY/.90 and retains trade. Invalid/nonfinite OHLC, duplicate/unsorted source, unavailable source and identity failure hard fail. Only symbol/entry/prior prices enter the feature API; no outcome, close or PnL. Same-day cache includes source identity/timezone/spec/symbol/as-of date.

## Input audits and warmup

All56 files match frozen manifest `8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f`.
Across all7 symbols earliest JST2015-01-02 16:00, latest2026-09-09 06:00. Pre2020 actual dates:1549 GBPAUD,1558 each other symbol, exceeding272. Full price history remains available for feature warmup; no2020 truncation, no2024 feature reset. Work inspected hashes, timestamp coverage and trade counts only. No actual assignments opened.

Existing27 identities (22 only excluded,20 retained):

- `1_EJ_Log1`
- `2_EJ_NightBlitz_20`
- `3_EJ_NightBlitz_21`
- `4_GJ_Port_Log1`
- `5_GJ_Port_Log2`
- `6_GJ_Old_Mon`
- `7_GJ_Mon_Blitz`
- `8_AJ_Core1`
- `9_AJ_Core2`
- `10_AJ_SatA`
- `11_AJ_SatB`
- `12_UJ_Short_Core`
- `13_UJ_Fix_MidWeek`
- `14_UJ_Sat_3rd`
- `15_UJ_Sat_Aug`
- `16_UJ_T10A`
- `17_EA_1B_Wed_Short`
- `18_EA_2_MonWed_Short`
- `19_EA_3_WedThu_Long`
- `20_EA_1A_MonTue_Short`
- `21_GA_B_3`
- `23_GA_F_2`
- `24_GA_D_1`
- `25_AU_China_Demand`
- `26_AJ_China_Demand`
- `27_EA_China_Demand`
- `28_GA_China_Demand`

GJ: B6-GBPJPY-L-W0-E0835-H1415, Monday13:57 → Tuesday13:31, Long SL30 TP_NONE E0,338 trades.
AJ: B6-AUDJPY-L-W0-E0950-H1440, Monday15:50 → Tuesday15:50, Long SL20 TP_NONE E0,339 trades.
Existing27 after2020:9083. Exact immutable ledgers, no trade deletion by R2.

## Matrix and money semantics

| Configuration | Composition | Trades |
|---|---|---:|
| R0_CURRENT_R2 | Current27 R2 | 9083 |
| R1_CURRENT_R2_PLUS_GJ | Current27 + GJ, same R2 | 9421 |
| R2_CURRENT_R2_PLUS_GJ_AJ | Current27 + GJ + AJ, same R2 | 9760 |

GJ incremental=R1−R0; AJ conditional incremental=R2−R1; Total B6 incremental=R2−R0. No extra combination.

500,000 JPY initial capital. Monday06 JST week-start closed Balance stays fixed through the week. Each RiskAmount=WeeklyBase×AppliedRiskPercent/100. Different trades can have different amounts; profits compound only next week. Existing PnL preserves Stage10 amount×Pips/SL arithmetic after savedR integrity; B6 uses frozen rawR. Settlement CloseTime/EntryTime/PortfolioComponentKey/RowId. Report attribution, DD initial peak500k, peak carryover, day/week denominators and undefined metrics match Stage10. No display-rounded R.

THEORETICAL_UNCAPPED; EAConstrainedStatus=NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS. Research Monday06 closed Balance differs from live Monday00 JST first sizing-request Equity, tick value, lot caps and volume limits. Stop-risk proxies are not broker margin or actual lots.

CONTINUOUS_2020 starts2020-01-01, ends before2026-09-10; no capital/DD reset at2024/2026. Reports Discovery, Validation, Monitor, PostDiscovery, FullAvailable. POSTDISCOVERY_RESET_2024 starts2024-01-01 with500k, same end, reports Validation/Monitor/PostDiscovery; capital only resets, feature history does not. This is a post-selection diagnostic, not fresh OOS.

Six money jobs,24 period rows,24 incremental rows. One9760-row assignment set shared across all jobs. Weekly gross allocation=sum AppliedRiskPercent; concurrency=sum simultaneously open AppliedRiskPercent, half-open intervals. Overlap is elapsed union/intersection, including GJ/AJ weeks and each B6 vs any/same-symbol Current27. Period risk mean/median/min/max and full72-row distribution (3groups×4periods×6bins) are available after completion.

## Colab and outputs

Notebook: `notebooks/b6_stage11_r2_incremental_portfolio.ipynb`.
PREPARE_ENVIRONMENT, MOUNT_DRIVE, RUN_STAGE11_FULL, CHAT_CONFIRMED_STAGE11_FREEZE, SAVE_OUTPUT_TO_DRIVE allFalse; STAGE11_FREEZE_SHA empty. Default run-all prints only frozen definitions. Bytecode disabled before b6 import; clean checkout required without exemptions.

Baseline `/content/drive/MyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/daily_stop_baseline_trades.csv`.
B6 `/content/drive/MyDrive/b6_stage8_archive/stage8_trade_ledger.csv.gz`.
M1 `/content/drive/MyDrive/ゆうのすけさん2025`.
Output `/content/b6_stage11`; archive `/content/drive/MyDrive/b6_stage11_archive`.

Formal run requires Google Colab, exact Freeze SHA, clean checkout, release/config/source/input hashes, all56 M1 hashes, Python3.13.15/NumPy2.3.5/pandas2.2.3, full+Chat flags. No Python-version substitution is performed. Input and assignment preflight precede money. Resume requires exact code/config/runtime/input/source/assignment-checkpoint identities and shard hashes. Partial runs expose progress only; completion and all output hashes gate display/archive.

Required identity/config/source/M1/trade/assignment audits, assignments and B6 assignment tables, R2 distribution,24 period results,24 increments,weekly/risk_load/concurrency/b6_overlap/diagnostics,summary/review JSON and compact review ZIP are written. ZIP contains no raw M1 or baseline ledger; the9760-row assignment evidence is included. State=COMPLETE_STAGE11_R2_INCREMENTAL_PORTFOLIO_ONLY. R2AssignmentsGenerated/GlobalR2Applied true only in formal completion; R2TradeFilter/AJOnlyConfigurationExists/RiskAllocationDecided/LiveChanged/StrategyNumberingAssigned false.

Stage10 completed archive metadata/output hashes audited, with GlobalR2Applied/RiskAllocationDecided/LiveChanged false. No Stage10 performance is used as scientific input or for specification selection. Historical Phase3 assignment hash is reference-only because exact bytes are unavailable.

## Freeze boundary

No threshold, score, ranking, automatic deployment decision or risk choice. Chat review may subsequently consider both B6 R2, GJ-only R2, or a separate later GJ fixed/AJ lower fixed study. Stage11 does not run that fallback study. No live/EA/SET/VPS changes or Strategy29+ numbering.

Work: implementation/source/hash/coverage/count audits and synthetic tests only. Stage11 actual R2 assignments and Money Simulation, FinalCapital/DD comparison and adoption decisions remain unexecuted. Frozen Stage1–10/Phase5 source/config/results unchanged; only this Stage's records and appended research documentation are new.

## Verification record

Repository suite:712 PASS (historical638 + Stage11 new74), FAIL0/ERROR0/SKIP0. Separately, frozen Phase5 `test*phase5*.py`:36 PASS, unchanged at its source commit. Combined748 PASS. Local Python3.12.14; formal Colab Python3.13.15 is required by the runtime guard and was not executed in Work. Run repository tests with `PYTHONPATH=.:src/research PYTHONDONTWRITEBYTECODE=1 python -m b6.stage11_test_suite` and the exact historical snapshot arguments declared in that runner. Phase5 tests run in a clean checkout of5e93a8834e27d4d9ffdbc2980906511f74ddb27a using `python -m unittest discover -s tests -p "test*phase5*.py"`.
