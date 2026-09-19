# Phase 5 — No-order reconciliation regression protocol
Protocol fixed before new test implementation. Dedicated trading EA implementation remains 1a69fbfe104ddd41e031273d9318c480a711969c; binary cda4909b26d44f4f0c7f5dc3f4d08709bc56923684b49e2578ca83a87263d540 is not rebuilt by this test work.
Original Plan and timezone addendum remain unchanged. This implements the existing predeployment regression requirement, not a new allocation/acceptance criterion.

## Test mechanism
Generate an include containing exact function/struct text extracted from the frozen dedicated EA. Record SHA256 per function and enforce regeneration equality. Isolated script uses deterministic in-memory terminal history/position/clock adapters via explicit preprocessor aliases. No CTrade, OrderSend, trade.Buy/Sell/PositionClose, GV writes, terminal timer registration or production EA include is allowed.
The script is a component execution test in MetaEditor/MQL, NOT a real broker trade, not a full terminal-runtime reproduction, and not a test of native API adapter correctness. Native history selection semantics are modeled explicitly including HistoryDealSelect clearing the selected list.
Actual OnTick/OnTimer/OnTradeTransaction bodies may be extracted; rename callbacks so only OnStart runs. RunStrategies is a counting stub. Thus callback ordering/guards and pending lifecycle are tested, not real strategy scheduling or order submission.
Mock records are limited to this isolated script. Forward EA TestMode/UseTestTimes/Mock remain false and Algo remains OFF.

## Fixed scenarios
Success-retcode table; BUY/SELL evidence direction; initial/reset pending state; preserve pending across resize/same-size calls; start/deadline; no evidence before deadline; evidence before timeout; timeout clears without marking entered; matching DEAL_ADD; unrelated/duplicate events; wrong symbol/magic/direction/entry kind/order/time/volume; previous-ticket exclusion; position-first reconciliation.
Exit: position gone; matching OUT/OUT_BY; wrong position identifier/order/time/volume/direction/symbol/magic; partial close rejected; pending close lookup; before/at timeout; delayed DEAL_ADD; Tick/Timer repeat does not mark entry twice; disabled guard does not advance handlers.
Static assertions verify extracted text matches frozen source and real TryEntry/close paths contain pending checks before submission. These are static checks, never relabeled full submission runtime.
No requirement to force broker return-code faults or place real orders during this protocol. Natural forward trade/exit and WeeklyBase week rollover remain future acceptance evidence; unresolved predeployment gaps remain explicitly pending.

## Evidence
Prior revised core34/34 screenshot, synthetic280-day parity, USDJPY513-day saved-feed parity, binary hash, SET120-key audit (Approved=false/timeverified=true), compiler/terminal6182, current clock screenshot and supplied standard-library7-file dependency manifest are carried as evidence with provenance, not as a global deployment PASS.
Save compile0/0 and runtime summary plus per-case logs for the new script. No local MQL compiler exists; deliver source only, mark MQL execution pending until Dell evidence.
No VPS/live changes. All original risk/Q/ATR/window/minima fixed. No EA attachment/Algo enable instructed by this protocol.
