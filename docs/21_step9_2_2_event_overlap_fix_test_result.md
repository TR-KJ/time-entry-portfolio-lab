# Step 9.2.2 Event Overlap Fix Test Result

## Document Purpose

本ドキュメントは、`time_entry_step9_2_2_event_overlap_fix_28strategies.mq5` に対して実施した修正確認テストの結果を記録する。

対象EA:

- `src/EA/time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

関連仕様:

- `docs/19_step9_2_2_event_overlap_fix_spec.md`
- `docs/20_step9_2_2_event_overlap_fix_patch.md`

---

## Test Summary

Step 9.2.2 では、以下4点の修正を確認した。

1. `12_UJ_Short_Core` の前倒しゴトウビ対応
2. `1_EJ_Log1` のFOMC `position_overlap` 停止
3. `4_GJ_Port_Log1` のFOMC `position_overlap` 停止
4. `16_UJ_T10A` のFOMC `position_overlap` 停止

全テストはMockJSTを使用して実施した。

---

## Common Test Settings

テスト時の基本設定は以下とする。

| Item | Setting |
|---|---|
| EA | `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5` |
| `InpTestMode` | `true` |
| `InpUseMockJstDateTime` | `true` |
| `InpUseTestTimes` | `false` |
| `InpUseGlobalAtrP70Filter` | `false` |
| `InpUseEventFilter` | Test 1は一時的に`false`、Test 2〜4は`true` |
| `InpUseEventCandidateC` | `true` |
| `InpPrintDebug` | `true` |
| `InpPrintEventFilterLogs` | `true` |
| `InpSuppressEventLogsOncePerDay` | `false` |
| `InpPrintSkipLogs` | `true` |
| `InpSuppressSkipLogsOncePerDay` | `false` |
| `InpLotMode` | `0` |
| `InpFixedLot` | `0.01` |

テスト中は、対象StrategyのみをONにし、他Strategyは原則OFFにして確認した。

---

## Test 1: 12_UJ_Short_Core Forward Gotobi

### Purpose

`12_UJ_Short_Core` について、25日または30日が土日の場合、直前金曜日を前倒しゴトウビとして扱うか確認する。

### Test Condition

| Item | Value |
|---|---|
| Strategy | `12_UJ_Short_Core` |
| Symbol | `USDJPY` |
| MockJST | `2026/07/24 09:55` |
| Reason | 翌日 `2026/07/25` が土曜日のため、前倒しゴトウビ対象 |
| Expected Mode | `GOTO` |
| Expected Entry Time | `09:55` |
| Expected SL | `20.0 pips` |
| Expected TP | `50.0 pips` |

### Expected Result

- `Mode=GOTO`
- `SELL entry success`
- SLが20pips相当
- TPが50pips相当
- `Mode=NORMAL` にならないこと

### Actual Result

初回テストでは同日エントリー済みGlobalVariableが残っていたためEntryしなかった。

原因:

- `TE_STEP4_3_12_UJ_Short_Core_USDJPY_12001_20260724` 相当の同日エントリー済み扱い

対応:

- MT5のグローバル変数から該当エントリー済み記録を削除
- 再テストを実施

再テスト結果:

- `Mode=GOTO` を確認
- `SELL entry success` を確認

### Result

`OK`

---

## Test 2: 1_EJ_Log1 FOMC Position Overlap

### Purpose

`1_EJ_Log1` について、予定保有時間がFOMC停止ウィンドウと重なる場合に、`position_overlap` によりEntry停止されるか確認する。

### Test Condition

| Item | Value |
|---|---|
| Strategy | `1_EJ_Log1` |
| Symbol | `EURJPY` |
| MockJST | `2026/07/29 13:55` |
| Planned Entry | `2026/07/29 13:55` |
| Planned Exit | `2026/07/30 04:55` |
| Event | `FOMC` |
| Event Time JST | `2026/07/30 03:00` |
| Stop Window | `2026/07/30 00:00` 〜 `2026/07/30 06:00` |
| WindowPre | `180` |
| WindowPost | `180` |

### Expected Result

- `EVENT OVERLAP STOP`
- `Event=FOMC`
- `BUY entry success` が出ないこと
- Entryなし

### Actual Result

- `EVENT OVERLAP STOP` を確認
- `BUY entry success` なし
- Entry停止を確認

### Result

`OK`

---

## Test 3: 4_GJ_Port_Log1 FOMC Position Overlap

### Purpose

`4_GJ_Port_Log1` について、予定保有時間がFOMC停止ウィンドウと重なる場合に、`position_overlap` によりEntry停止されるか確認する。

### Initial Note

当初、`2026/07/30 00:00` でテスト予定だったが、`2026/07/30` は木曜日であり、`4_GJ_Port_Log1` の通常Entry曜日ではないため、テスト日として不適切と判断した。

`4_GJ_Port_Log1` は火曜・水曜が対象であるため、FOMC日かつEntry曜日に合う日として `2026/01/28 00:00` に変更して確認した。

### Test Condition

| Item | Value |
|---|---|
| Strategy | `4_GJ_Port_Log1` |
| Symbol | `GBPJPY` |
| MockJST | `2026/01/28 00:00` |
| Planned Entry | `2026/01/28 00:00` |
| Planned Exit | `2026/01/28 08:55` |
| Event | `FOMC` |
| Event Time JST | `2026/01/28 03:00` |
| Stop Window | `2026/01/28 00:00` 〜 `2026/01/28 06:00` |
| WindowPre | `180` |
| WindowPost | `180` |

### Expected Result

- `EVENT OVERLAP STOP`
- `Event=FOMC`
- `BUY entry success` が出ないこと
- Entryなし

### Actual Result

- `EVENT OVERLAP STOP` を確認
- `BUY entry success` なし
- Entry停止を確認

### Result

`OK`

---

## Test 4: 16_UJ_T10A FOMC Position Overlap

### Purpose

`16_UJ_T10A` について、予定保有時間がFOMC停止ウィンドウと重なる場合に、`position_overlap` によりEntry停止されるか確認する。

### Test Condition

| Item | Value |
|---|---|
| Strategy | `16_UJ_T10A` |
| Symbol | `USDJPY` |
| MockJST | `2026/07/30 02:58` |
| Planned Entry | `2026/07/30 02:58` |
| Planned Exit | `2026/07/30 09:50` |
| Event | `FOMC` |
| Event Time JST | `2026/07/30 03:00` |
| Stop Window | `2026/07/30 00:00` 〜 `2026/07/30 06:00` |
| WindowPre | `180` |
| WindowPost | `180` |

### Expected Result

- `EVENT OVERLAP STOP`
- `Event=FOMC`
- `BUY entry success` が出ないこと
- Entryなし

### Actual Result

- `EVENT OVERLAP STOP` を確認
- `BUY entry success` なし
- Entry停止を確認

### Result

`OK`

---

## Final Result

| Test | Target | Expected | Result |
|---:|---|---|---|
| 1 | `12_UJ_Short_Core` | Forward Gotobi Mode=`GOTO` | `OK` |
| 2 | `1_EJ_Log1` | FOMC `position_overlap` stop | `OK` |
| 3 | `4_GJ_Port_Log1` | FOMC `position_overlap` stop | `OK` |
| 4 | `16_UJ_T10A` | FOMC `position_overlap` stop | `OK` |

---

## Conclusion

`time_entry_step9_2_2_event_overlap_fix_28strategies.mq5` の修正確認テストは合格とする。

確認済み内容:

- `12_UJ_Short_Core` の前倒しゴトウビ判定が機能する
- `1_EJ_Log1` のFOMC `position_overlap` 停止が機能する
- `4_GJ_Port_Log1` のFOMC `position_overlap` 停止が機能する
- `16_UJ_T10A` のFOMC `position_overlap` 停止が機能する
- 対象Strategyで、期待されるイベント停止時にEntryが発生しないことを確認した

Step 9.2.2 は、Forward Phase 3-A の次回入替候補として使用可能と判断する。

---

## Forward Replacement Note

Step 9.2.2 へ入れ替える場合は、以下を確認してから実施する。

1. 既存保有ポジションがないこと
2. 未決済注文がないこと
3. 現行EAをチャートから削除すること
4. `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5` をセットすること
5. Phase 3-A用inputを再設定すること
6. `InpLotMode = 1`
7. `InpRiskPercentPerTrade = 1.00`
8. `InpWeeklyBaseUseEquity = true`
9. `InpUseGlobalAtrP70Filter = false`
10. `InpUseEventFilter = true`
11. `InpUseEventCandidateC = true`
12. `InpUseWeekendMarketClosedGuard = true`
13. 起動後、Expertsログで初期化ログと設定値を確認すること
