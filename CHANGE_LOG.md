# CHANGELOG

## 2026-06-13

### Added
- GitHub repository created.
- Added initial project structure.
- Added README.md.
- Added DEVELOPMENT_LOG.md.
- Added original Gemini backtest code as `src/portfolio_backtest_v1_original.py`.

### Planned
- Fix UJ_Short_Core entry time.
- Fix UJ_Short_Core normal-day SL/TP.
- Add GA, EA, AU, AJ, EURAUD, GBPAUD additional logic.
- Add 2026 event calendar.
- Refactor strategy definitions into config-based structure.

## 2026-06-13

### Added

- Added `src/portfolio_backtest_v1_1_engine_fix.py`.
- Added 2026 event calendar support.
- Added period summary output.
- Added strategy summary output.
- Added exit reason summary output.
- Added CSV outputs for trade log and summaries.

### Changed

- Fixed `UJ_Short_Core` normal-day entry time from `07:53` to `08:04`.
- Fixed `UJ_Short_Core` normal-day SL/TP from `SL20 / TP50` to `SL50 / TPなし`.
- Kept `UJ_Short_Core` goto-day settings as `09:55 Entry / SL20 / TP50`.
- Adopted calendar month-end stop for `UJ_Short_Core`.
- Removed 12A/12B duplicate ablation structure from the main version.
- Kept `UJ_Fix_MidWeek` as Wednesday and Thursday after the 25th.
- Kept `same_bar_policy = sl_first`.
- Kept `spread_mode = entry_adjust`.

### Notes

- This version covers only the current master 16 logic portfolio.
- GA / EA / AU / Aussie-related additional logic will be added in v1.2.
- Legacy IS/OOS and Strict IS/OOS summaries are both included for comparison and future filter testing.
