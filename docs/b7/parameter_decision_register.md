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
|A09|AGREED|Formal 16-stage sequence in full_research_prespec.json; E2 diagnostics → MFE/Giveback/Protection → Candidate Freeze included|
|A10|AGREED|U07 supersedes earlier max31 subset proposal: at most4 nested W sets; arbitrary31-subset search prohibited|
|A11|AGREED|U08 supersedes earlier max7 subset proposal: sequential DOM0/1/2 only; exhaustive7 prohibited|
|A12|AGREED|Twelve-month diagnostics + LOMO; M0/1/2 only, at most2 OFF months; U08 sample/adoption rules frozen; prohibit4095|
|A13|AGREED|Fine tune original Entry/Exit±5min,1min increments; no reanchor/rescue/return to SLTP/calendar|
|A14|AGREED|E2 pre-adopted under U10; E0/E1/E2 diagnostic only; frozen calendar infrastructure, no B6 Candidate C matrix|
|A15|AGREED|Immutable Candidate Freeze before Validation; no retuning; Monitor OBSERVED only; compare B6 only after Validation|
|A16|AGREED|Money/R/R2/Portfolio later, PASS not live adoption; no EA/SET/VPS/live/current-forward changes|
|P01|AGREED/FROZEN|Exact nine official five-SL grids adopted; Discovery price-only calibration unchanged; no additional or result-driven SL. See stage1_conditions_freeze.md and stage1_prespec.json.|
|P02|AGREED/FROZEN|Unrounded Pips for all gates/ranking/PF/DD; planned Entry JST year; DD starts cumulative/peak 0; CloseTime JST, EntryTime JST, fixed key order. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U01|AGREED/FROZEN|Pure Time: trades >=150, each year >=30, losses >=10, AvgPips >0, PF >=1.10, positive years >=3/4; no absolute DD cap. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U02|AGREED/FROZEN|Each SL x TP_NONE: same sample/AvgPips/positive-year gates, PF >=1.05; at least3/5 PASS; Pure Time primary, no best-SL selection. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U03|AGREED/FROZEN|Entry/Exit offsets -5/0/+5, center included; valid >=4, formal PASS ratio >=2/3, all-valid median AvgPips >=0.80 x center; invalid schedules excluded. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U04|AGREED/FROZEN|Same symbol/direction/offset; circular Entry/Exit distance <=30 and holding difference <=30; cross-weekday suppression; direct representative only, no chaining; fixed key and weekday provenance frozen. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U05|AGREED/FROZEN|Finite/INF/UNDEFINED/zero semantics; no sentinels; losses >=10 excludes INF; all four annual sample gates required for ranking median. See stage1_conditions_freeze.md and stage1_prespec.json.|
|U06|AGREED/FROZEN|Formal SL: U02 PASS anchors, ±20% local5pips, maximal >=3-point zones, zone median >=0.80 Pure Time, frozen zone ranking/lower median. Then TP_NONE/0.5/1/1.5/2/3R, adjacent passing anchors/local zones; finite TP must beat TP_NONE by max0.10pips/5% with no positive-year/worst-year degradation. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U07|AGREED/FROZEN|Anchor remains CORE; only deduplicated W0/W1/W2/W3 nested sets. Formal gate, Best median80% plateau plus no positive-year loss; widest set, W3>W2>W1>W0 tie. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U08|AGREED/FROZEN|Initial DOM/month bad-bucket/month candidates frozen; sequential DOM0/1/2 and M0/1/2 improvement checks, max2 exclusions; sample gates and LOMO fixed; Calendar Freeze. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U09|AGREED/FROZEN|Original anchor ±5min each at1min; valid 3x3 plateau, frozen neighborhood ranking; change only for max0.05pips/2.5% improvement; no plateau retains anchor. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U10|AGREED/FROZEN|E2 pre-adopted, frozen B6 calendar commit/times/windows; inclusive planned interval overlap; E0/E1/E2 diagnostic only; post-E2 formal gate, no fallback. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U10-P|AGREED/FROZEN|After E2: MFE/MAE/Giveback, WinnerToLoser >=0.5R then loss; only P0-P3, next-bar activation, fixed TP; non-degradation plus >=20% and >=5trade reduction, frozen tie order. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U11|AGREED/FROZEN|Frozen Candidate Validation2024-2025: annual30/combined70 trades, annual5 losses; both years positive, Avg>0, PF>=1.10, DD<=1.50Discovery. PASS/FAIL/INSUFFICIENT_SAMPLE; Monitor PASS-only OBSERVED_ONLY. See full_research_conditions_freeze.md and full_research_prespec.json.|
|U12|AGREED/FROZEN|Work implementation Freeze → Chat confirmation → Colab; environment/input/barrier identity,90jobs, deterministic resume,3 output levels, COMPLETE_STAGE1_ONLY; current request authorizes docs/config only. See full_research_conditions_freeze.md and full_research_prespec.json.|
|B01|CLEAR_WITH_LIMITATION|User research decision: adopt the audited SHA256-frozen 72-file Research Data Collection under a symmetric all-nine-pair standard. Historical broker names are not fully independently certified; eight recent RECHECKs have scoped OANDA support; no explicit different-broker mixing evidence. No result-driven source replacement/reacquisition/filling. Stage1 only AFTER_STAGE1_CONDITIONS_FREEZE; see source_of_truth.md.|
|I01|IMPLEMENTATION_DETAIL|All-period integrity audit isolated from Discovery price-only copy; period validators reject future rows|
|I02|IMPLEMENTATION_DETAIL|Audit MT5 headers,hash before/after read,OHLC/finite,ordering,duplicates,gaps,fractional-pip grid; no raw price output|
|I03|IMPLEMENTATION_DETAIL|EU/GU original vsRECHECK verified by timestamp subset and identical overlapping OHLC; no merging/filling. Selected file's entire actual bytes are hashed|
|I04|IMPLEMENTATION_DETAIL|Independent main-based checkout; original B6 fixture copied byte-identically, private test constants addEU/GU only; no B7 Stage1 executor|
|I05|IMPLEMENTATION_DETAIL|No matching EU/GU formal audit located in scoped repo/Drive search; do not claim no record could exist anywhere|

## Full conditions Freeze and current authorization

P01/P02/U01–U12 + U10-P are all AGREED/FROZEN. P01/P02/U01–U05 and B01 rows remain unchanged. The authoritative full documents are full_research_conditions_freeze.md and research_inputs/b7/full_research_prespec.json. Historical partial Freeze artifacts remain byte-identical and are referenced with SHA256.

Stage1ConditionsFrozen = true. Stage1ImplementationAuthorized = false; Stage1ExecutionAuthorized = false. This request authorizes documentation/config only. The next separate user instruction may authorize implementation; formal full sweep requires Work implementation Freeze → Chat confirmation → Google Colab. No new performance results were opened. No candidate scarcity relaxation, zero-pair rescue, result-driven threshold change or return from Validation to Discovery.

## Subsequent Stage1 implementation-only authorization

The separate user instruction authorizes Stage1 engine, tests, fixed bounded compatibility smoke, notebook and runtime/release infrastructure. Research decision rows above remain frozen. Stage1ImplementationAuthorized=true; Stage1ExecutionAuthorized=false. Implementation details, deterministic ID encoding and test evidence are in stage1_implementation.md and stage1_runtime_config.json. The prior conditions-only authorization paragraph records the earlier Freeze phase.
