# B7 Decision Register

This register derives B7 decisions from the user's current Stage0 instruction, not B6 candidate results. Null fields are intentionally unresolved; no automatic defaults may promote them to AGREED.

|ID|Status|Item / decision|
|---|---|---|
|A01|AGREED|Independent Pips-first B7; Stage0 only; existing operation/B6 unchanged; no Strategy numbering|
|A02|AGREED|Nine specified pairs, Discovery2020–2023 / Validation2024–2025 / partial Monitor2026, half-open JST intervals|
|A03|AGREED|Spread UJ.5 EJ1 GJ2 AJ1.5 AU1.5 EA1.5 GA2 EU1 GU1.5; EU/GU research assumptions|
|A04|AGREED|JPY pip.01/non-JPY.0001 subject to actual format audit; inherited Helsinki→JST and historical execution contract|
|A05|AGREED|5-minute Entry and holding30…1440, Long/Short, Entry weekday; Pure Time primary plus5SL/noTP robustness|
|A06|AGREED|Price-only B6 calibration methodology, existing7 exact-grid audit; resulting B7 grids remain proposal|
|A07|AGREED|Per-pair stable-year Pips lexicographic ranking, no cross-pair ranking; maximum8 de-duplicated families/pair, no minimum|
|A08|AGREED|Plateau philosophy; no isolated-peak preference, no threshold inferred|
|A09|AGREED|SL→TP→Weekday→DOM→Month→Calendar Freeze→1m→Event→Candidate Freeze|
|A10|AGREED|Weekday max31 subsets; broad operation and limited damaging-weekday removal|
|A11|AGREED|DOM1–10/11–20/21–EOM, max7 subsets; limited removal|
|A12|AGREED|12-month diagnostics + LOMO; prohibit4095; maximum2 off-month policy; minimum/pass rules pending|
|A13|AGREED|Fine tune original Entry/Exit±5min,1min increments; no reanchor/rescue/return to SLTP/calendar|
|A14|AGREED|E0/E1/E2 structure; EU ECB/FOMC,GU BOE/FOMC; no strategy-specific Candidate C matrix|
|A15|AGREED|Immutable Candidate Freeze before Validation; no retuning; Monitor OBSERVED only; compare B6 only after Validation|
|A16|AGREED|Money/R/R2/Portfolio later, PASS not live adoption; no EA/SET/VPS/live/current-forward changes|
|P01|PROVISIONAL|Measured price-only5SL proposals; not formal Stage1 conditions|
|P02|PROVISIONAL|Metrics on unrounded Pips; annual attribution by planned Entry JST year; DD chronological with initial peak0; numerical accumulation/display policy awaits Chat|
|U01|UNDECIDED|Pure Time minimum total/year trades,losses,PF,AvgPips,positive years,DD and annual sample gates|
|U02|UNDECIDED|How5SL robustness passes a family: minimum pass count, per-SL gates and relationship to Pure Time eligibility|
|U03|UNDECIDED|5m plateau neighborhood/radius,self inclusion,boundaries,minimum valid neighbors,pass ratio,metric thresholds,undefined handling|
|U04|UNDECIDED|Time Family identity,nearby suppression distance,weekday membership,offset/holding conditions,non-chaining policy,fixed key|
|U05|UNDECIDED|PF INF/UNDEFINED and zero/empty-year gate/ranking treatment; annual median definition with absent years|
|U06|UNDECIDED|SL selection rule;TP finite grid,rounding,bounds,TP_NONE; any SL/TP local refinement scope; no B6 numeric default|
|U07|UNDECIDED|Mapping weekday-specific Stage1 structures to later Mon–Fri ON/OFF; sample/replication/removal thresholds and tie-breaks|
|U08|UNDECIDED|DOM minimum samples/removal/tie-break rules;month LOMO criteria and how two-month exclusions are assessed|
|U09|UNDECIDED|1m neighborhood/pass/selection rule and day/weekday/offset invalid-boundary handling|
|U10|UNDECIDED|Event calendar source/version,windows,clock/overlap freeze,minimum retained/removed samples and Pips adoption thresholds|
|U11|UNDECIDED|B7 Validation minimum sample,annual/combined pass gates,DD comparison and insufficient-sample labels,freeze before opening results|
|U12|UNDECIDED|Stage1 runtime/dependencies,output/resume/hash contract and authorized execution environment|
|B01|BLOCKED|2026-10-05 reassessment: concrete Sep9 Dell/OANDA DEMO acquisition evidence supports eight2026Apr–Sep RECHECKs, includingEU/GU. Historical2015–2025 and2026Jan–Mar source bridge, especiallyGA, remains insufficient. No different broker/mixed source established. Vague Forex/FXCM recollection is not the blocking rationale; embedded CSV broker metadata is not required. See b01_provenance_review.md.|
|I01|IMPLEMENTATION_DETAIL|All-period integrity audit isolated from Discovery price-only copy; period validators reject future rows|
|I02|IMPLEMENTATION_DETAIL|Audit MT5 headers,hash before/after read,OHLC/finite,ordering,duplicates,gaps,fractional-pip grid; no raw price output|
|I03|IMPLEMENTATION_DETAIL|EU/GU original vsRECHECK verified by timestamp subset and identical overlapping OHLC; no merging/filling. Selected file's entire actual bytes are hashed|
|I04|IMPLEMENTATION_DETAIL|Independent main-based checkout; original B6 fixture copied byte-identically, private test constants addEU/GU only; no B7 Stage1 executor|
|I05|IMPLEMENTATION_DETAIL|No matching EU/GU formal audit located in scoped repo/Drive search; do not claim no record could exist anywhere|

## Chat decisions before Stage1 implementation

Resolve B01 with traceable acquisition provenance; confirm P01 five-SL values and P02 numeric semantics; freeze U01–U05 (eligibility,robustness,plateau,families,fixed key/undefined handling) and the scope dependencies U06–U10, especially weekday-family transition. Record when later-stage threshold freezes must occur **before their corresponding results**; do not backfill after discovery. Freeze the Validation contract before Validation (U11), and Stage1 runtime/release/resume gates (U12). Stage0 publication alone authorizes none of these choices.
