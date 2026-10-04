# B7 Decision Register

This register derives B7 decisions from the user's current Stage0 instruction, not B6 candidate results. Null fields are intentionally unresolved; no automatic defaults may promote them to AGREED.

|ID|Status|Item / decision|
|---|---|---|
|A01|AGREED|Independent Pips-first B7; Stage0 only; existing operation/B6 unchanged; no Strategy numbering|
|A02|AGREED|Nine specified pairs, Discovery2020–2023 / Validation2024–2025 / partial Monitor2026, half-open JST intervals|
|A03|AGREED|Spread UJ.5 EJ1 GJ2 AJ1.5 AU1.5 EA1.5 GA2 EU1 GU1.5; EU/GU research assumptions|
|A04|AGREED|JPY pip.01/non-JPY.0001 subject to actual format audit; inherited Helsinki→JST and historical execution contract|
|A05|AGREED|5-minute Entry and holding30…1440, Long/Short, Entry weekday; Pure Time primary plus5SL/noTP robustness|
|A06|AGREED|Price-only B6 calibration methodology, existing7 exact-grid audit; exact resulting B7 grids formally adopted under P01|
|A07|AGREED|Per-pair stable-year Pips lexicographic ranking, no cross-pair ranking; maximum8 de-duplicated families/pair, no minimum|
|A08|AGREED|Plateau philosophy; no isolated-peak preference; formal thresholds frozen in U03|
|A09|AGREED|SL→TP→Weekday→DOM→Month→Calendar Freeze→1m→Event→Candidate Freeze|
|A10|AGREED|Weekday max31 subsets; broad operation and limited damaging-weekday removal|
|A11|AGREED|DOM1–10/11–20/21–EOM, max7 subsets; limited removal|
|A12|AGREED|12-month diagnostics + LOMO; prohibit4095; maximum2 off-month policy; minimum/pass rules pending|
|A13|AGREED|Fine tune original Entry/Exit±5min,1min increments; no reanchor/rescue/return to SLTP/calendar|
|A14|AGREED|E0/E1/E2 structure; EU ECB/FOMC,GU BOE/FOMC; no strategy-specific Candidate C matrix|
|A15|AGREED|Immutable Candidate Freeze before Validation; no retuning; Monitor OBSERVED only; compare B6 only after Validation|
|A16|AGREED|Money/R/R2/Portfolio later, PASS not live adoption; no EA/SET/VPS/live/current-forward changes|
|P01|AGREED/FROZEN|Exact nine official five-SL grids adopted; Discovery price-only calibration unchanged; no additional or result-driven SL. See stage1_conditions_freeze.md and stage1_prespec.json.|
|P02|AGREED/FROZEN|Unrounded Pips for all gates/ranking/PF/DD; planned Entry JST year; DD starts cumulative/peak 0; CloseTime JST, EntryTime JST, fixed key order. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U01|AGREED/FROZEN|Pure Time: trades >=150, each year >=30, losses >=10, AvgPips >0, PF >=1.10, positive years >=3/4; no absolute DD cap. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U02|AGREED/FROZEN|Each SL x TP_NONE: same sample/AvgPips/positive-year gates, PF >=1.05; at least3/5 PASS; Pure Time primary, no best-SL selection. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U03|AGREED/FROZEN|Entry/Exit offsets -5/0/+5, center included; valid >=4, formal PASS ratio >=2/3, all-valid median AvgPips >=0.80 x center; invalid schedules excluded. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U04|AGREED/FROZEN|Same symbol/direction/offset; circular Entry/Exit distance <=30 and holding difference <=30; cross-weekday suppression; direct representative only, no chaining; fixed key and weekday provenance frozen. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U05|AGREED/FROZEN|Finite/INF/UNDEFINED/zero semantics; no sentinels; losses >=10 excludes INF; all four annual sample gates required for ranking median. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U06|UNDECIDED|SL selection rule;TP finite grid,rounding,bounds,TP_NONE; any SL/TP local refinement scope; no B6 numeric default|
|U07|UNDECIDED|Mapping weekday-specific Stage1 structures to later Mon–Fri ON/OFF; sample/replication/removal thresholds and tie-breaks|
|U08|UNDECIDED|DOM minimum samples/removal/tie-break rules;month LOMO criteria and how two-month exclusions are assessed|
|U09|UNDECIDED|1m neighborhood/pass/selection rule and day/weekday/offset invalid-boundary handling|
|U10|UNDECIDED|Event calendar source/version,windows,clock/overlap freeze,minimum retained/removed samples and Pips adoption thresholds|
|U11|UNDECIDED|B7 Validation minimum sample,annual/combined pass gates,DD comparison and insufficient-sample labels,freeze before opening results|
|U12|UNDECIDED|Stage1 runtime/dependencies,output/resume/hash contract and authorized execution environment|
|B01|CLEAR_WITH_LIMITATION|User research decision: adopt the audited SHA256-frozen 72-file Research Data Collection under a symmetric all-nine-pair standard. Historical broker names are not fully independently certified; eight recent RECHECKs have scoped OANDA support; no explicit different-broker mixing evidence. No result-driven source replacement/reacquisition/filling. Stage1 only AFTER_STAGE1_CONDITIONS_FREEZE; see source_of_truth.md.|
|I01|IMPLEMENTATION_DETAIL|All-period integrity audit isolated from Discovery price-only copy; period validators reject future rows|
|I02|IMPLEMENTATION_DETAIL|Audit MT5 headers,hash before/after read,OHLC/finite,ordering,duplicates,gaps,fractional-pip grid; no raw price output|
|I03|IMPLEMENTATION_DETAIL|EU/GU original vsRECHECK verified by timestamp subset and identical overlapping OHLC; no merging/filling. Selected file's entire actual bytes are hashed|
|I04|IMPLEMENTATION_DETAIL|Independent main-based checkout; original B6 fixture copied byte-identically, private test constants addEU/GU only; no B7 Stage1 executor|
|I05|IMPLEMENTATION_DETAIL|No matching EU/GU formal audit located in scoped repo/Drive search; do not claim no record could exist anywhere|

## Conditions Freeze and remaining decisions

P01/P02/U01–U05 are AGREED/FROZEN by the explicit user instruction; old IDs are retained. The full authoritative conditions are in stage1_conditions_freeze.md and research_inputs/b7/stage1_prespec.json. No values were selected from new performance results.

U06–U12 remain UNDECIDED, with their table entries unchanged. Later-stage thresholds must be frozen before their corresponding results; do not backfill after discovery. U12 runtime/resume/artifact/Colab execution contract still requires its own Freeze. This partial conditions Freeze does not authorize Stage1 executor/notebook implementation, full sweep, ranking execution or Top8 selection.
