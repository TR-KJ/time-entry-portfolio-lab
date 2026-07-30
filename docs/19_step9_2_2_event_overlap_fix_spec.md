# Step 9.2.2 Event Overlap Fix Spec

## 1. Purpose

Forward Phase 3-A中に確認された以下の仕様補正を、次回EA `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5` の修正対象として確定する。

対象元EA:

- `src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

次回EA候補:

- `src/EA/time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

本修正は、Lot計算・Entry・Exit・既存Event Candidate C・ATR OFF・Weekend Guardの不具合修正ではなく、実運用に向けたイベント停止範囲とゴトウビ認識の仕様補正である。

---

## 2. Confirmed Fix Scope

今回の修正対象は以下4点とする。

1. `12_UJ_Short_Core` 前倒しゴトウビ対応
2. `1_EJ_Log1` のFOMC / US_NFP / BOJ / ECB `position_overlap` 対応
3. `4_GJ_Port_Log1` のFOMC `position_overlap` 対応
4. `16_UJ_T10A` のFOMC `position_overlap` 対応

---

## 3. Fix 1: 12_UJ_Short_Core Forward Gotobi

### 3.1 Background

2026/7/24、`12_UJ_Short_Core` が `NORMAL` モードで08:04 Entryした。

しかし、2026/7/25は土曜日であり、実務上は2026/7/24を25日分の前倒しゴトウビとして扱いたい。

### 3.2 Current Behavior

現行EAでは、`12_UJ_Short_Core` のGOTO判定は以下のみである。

- 20日
- 25日
- 30日

そのため、25日または30日が土日の場合の前倒しゴトウビは未実装である。

### 3.3 Fixed Specification

`12_UJ_Short_Core` のGOTO判定を以下で固定する。

通常GOTO:

- 20日
- 25日
- 30日

前倒しGOTO:

- 25日が土曜日または日曜日の場合、直前金曜日を前倒しGOTOとする
- 30日が土曜日または日曜日の場合、直前金曜日を前倒しGOTOとする

前倒しGOTOにしないもの:

- 20日が土曜日または日曜日の場合、直前金曜日を前倒しGOTOにしない

祝日:

- 祝日は前倒し対象にしない
- 理由は、海外市場が稼働しているため

### 3.4 Final Logic

最終仕様:

- 20 / 25 / 30 は通常GOTO
- 25 / 30 が土日の場合のみ、直前金曜を前倒しGOTO
- 20 が土日の場合は、前倒しGOTOにしない
- 祝日は考慮しない

実運用を考慮し、2026年固定配列ではなくロジック判定で実装する。

---

## 4. Fix 2: 1_EJ_Log1 Event Overlap

### 4.1 Background

2026/7/29、`1_EJ_Log1` が13:55にEntryした。

保有予定時間:

- Entry: 2026/7/29 13:55 JST
- Exit: 2026/7/30 04:55 JST

同期間中に、2026/7/30 03:00 JSTのFOMCが存在する。

FOMC停止ウィンドウ:

- 00:00〜06:00 JST

したがって、予定保有時間とFOMC停止ウィンドウが重なるため、本来は `EVENT OVERLAP STOP` としたい。

### 4.2 Current Behavior

現行EAでは、`1_EJ_Log1` は以下の特殊停止のみを持つ。

- 2月停止
- 毎月1日停止
- `US_CPI_WEEK_WED` 停止

そのため、以下イベントの `position_overlap` 停止対象になっていない。

- FOMC
- US_NFP
- BOJ
- ECB

### 4.3 Fixed Specification

`1_EJ_Log1` について、以下イベントを `position_overlap` 停止対象に追加する。

- FOMC
- US_NFP
- BOJ
- ECB

US CPIについては、現行の `US_CPI_WEEK_WED` 特殊停止を維持する。

つまり、`1_EJ_Log1` については、US CPIを通常の `position_overlap` にはしない。

### 4.4 Event Time and Window

| Event | Event Time JST | Pre Minutes | Post Minutes | Stop Window |
|---|---:|---:|---:|---|
| FOMC | 03:00 | 180 | 180 | 00:00〜06:00 |
| US_NFP | 21:30 | 120 | 120 | 19:30〜23:30 |
| BOJ | 12:00 | 180 | 180 | 09:00〜15:00 |
| ECB | 21:15 | 120 | 120 | 19:15〜23:15 |

---

## 5. Fix 3: 4_GJ_Port_Log1 FOMC Overlap

### 5.1 Background

`4_GJ_Port_Log1` は以下の保有時間で稼働する。

- Symbol: GBPJPY
- Direction: LONG
- Entry: 00:00 JST
- Exit: 08:55 JST

FOMCが日本時間03:00で、停止ウィンドウが00:00〜06:00の場合、`4_GJ_Port_Log1` の予定保有時間はFOMC停止ウィンドウと重なる。

### 5.2 Current Behavior

現行EAでは、`4_GJ_Port_Log1` のCandidate C判定は以下のみである。

- 12月停止
- 毎月1日停止
- 毎月2日停止
- 毎月29日停止
- 毎月30日停止
- 毎月31日停止

FOMCの `position_overlap` 判定は未実装である。

### 5.3 Fixed Specification

`4_GJ_Port_Log1` にFOMC `position_overlap` 停止を追加する。

既存の以下停止は維持する。

- 12月停止
- 毎月1日停止
- 毎月2日停止
- 毎月29日停止
- 毎月30日停止
- 毎月31日停止

FOMC停止条件:

- FOMC日または翌日FOMCを確認する
- Entry予定時刻〜Exit予定時刻と、FOMC停止ウィンドウが重なる場合は停止する
- 停止時は `EVENT OVERLAP STOP` を出す

---

## 6. Fix 4: 16_UJ_T10A FOMC Overlap

### 6.1 Background

`16_UJ_T10A` は以下の保有時間で稼働する。

- Symbol: USDJPY
- Direction: LONG
- Entry: 02:58 JST
- Exit: 09:50 JST

FOMCが日本時間03:00で、停止ウィンドウが00:00〜06:00の場合、`16_UJ_T10A` の予定保有時間はFOMC停止ウィンドウと重なる。

### 6.2 Current Behavior

現行EAでは、`16_UJ_T10A` のイベント停止はBOJのみである。

- BOJ: 終日停止
- FOMC: 未実装

### 6.3 Fixed Specification

`16_UJ_T10A` にFOMC `position_overlap` 停止を追加する。

既存のBOJ終日停止は維持する。

FOMC停止条件:

- FOMC日または翌日FOMCを確認する
- Entry予定時刻〜Exit予定時刻と、FOMC停止ウィンドウが重なる場合は停止する
- 停止時は `EVENT OVERLAP STOP` を出す

---

## 7. Required Input Additions

現行EAには、FOMC / ECB / BOE / RBA / AU_CPI の `position_overlap` 用inputは存在する。

今回、`1_EJ_Log1` のUS_NFP / BOJ `position_overlap` 対応のため、以下inputを追加する。

US_NFP:

- `InpNfpEventHourJST = 21`
- `InpNfpEventMinuteJST = 30`
- `InpNfpPreMinutes = 120`
- `InpNfpPostMinutes = 120`

BOJ:

- `InpBojEventHourJST = 12`
- `InpBojEventMinuteJST = 0`
- `InpBojPreMinutes = 180`
- `InpBojPostMinutes = 180`

---

## 8. Implementation Direction

### 8.1 Event Time Window

`GetCandidateCEventTimeAndWindow` と `GetCandidateCEventTimeAndWindowByDateKey` に、以下イベントを追加する。

- `US_NFP`
- `BOJ`

### 8.2 Event Date Key

`IsCandidateCEventDateKey` に、以下イベントを追加する。

- `US_NFP`
- `BOJ`

### 8.3 Strategy Target

`IsCandidateCStrategyTargetForEvent` に、以下を追加する。

FOMC対象に追加:

- `1_EJ_Log1`
- `4_GJ_Port_Log1`
- `16_UJ_T10A`

US_NFP対象に追加:

- `1_EJ_Log1`

BOJ対象に追加:

- `1_EJ_Log1`

ECB対象に追加:

- `1_EJ_Log1`

### 8.4 Candidate C Flow

以下StrategyのCandidate C判定に、`RejectCandidateCPositionOverlapEventsDuringPlannedPosition` を追加する。

- `1_EJ_Log1`
- `4_GJ_Port_Log1`
- `16_UJ_T10A`

既存の特殊停止は維持し、特殊停止の後または必要な位置で `position_overlap` を確認する。

---

## 9. Expected Test Cases

### 9.1 UJ12 Forward Gotobi

2026/7/24:

- Expected Mode: GOTO
- Expected Entry: 09:55
- Expected SL: 20.0
- Expected TP: 50.0

2026/6/19:

- 6/20土曜の前倒し候補だが、20日より前なのでGOTOにしない
- Expected: Date rule reject before 20th, or NORMAL/GOTO判定前にEntry対象外

### 9.2 1_EJ FOMC Overlap

2026/7/29:

- Entry: 13:55
- Exit: 2026/7/30 04:55
- FOMC: 2026/7/30 03:00
- Expected: `EVENT OVERLAP STOP`

### 9.3 1_EJ NFP Overlap

NFP日が `1_EJ_Log1` の保有時間と重なるケース:

- Expected: `EVENT OVERLAP STOP`

### 9.4 1_EJ BOJ Overlap

BOJ 12:00の停止ウィンドウ 09:00〜15:00 と、`1_EJ_Log1` Entry 13:55が重なるケース:

- Expected: `EVENT OVERLAP STOP`

### 9.5 4_GJ FOMC Overlap

FOMC当日:

- Entry: 00:00
- Exit: 08:55
- FOMC: 03:00
- Expected: `EVENT OVERLAP STOP`

### 9.6 16_UJ FOMC Overlap

FOMC当日:

- Entry: 02:58
- Exit: 09:50
- FOMC: 03:00
- Expected: `EVENT OVERLAP STOP`

---

## 10. Forward Test Interpretation

今回の修正対象は、Forward Phase 3-Aで確認された以下の正常項目を壊さない前提で追加する。

- Weekly Fixed Risk Lot計算
- Entry
- Exit
- Event Candidate Cの既存対象イベント停止
- ATR OFF
- Weekend / Market Closed Guard
- FOMC翌日深夜のposition_overlap判定

本修正により、実運用に近いゴトウビ認識と、重要イベント直撃回避を強化する。

---

## 11. Conclusion

Step 9.2.2では、以下4点を実装する。

1. `12_UJ_Short_Core` の前倒しゴトウビ対応
2. `1_EJ_Log1` のFOMC / US_NFP / BOJ / ECB `position_overlap` 対応
3. `4_GJ_Port_Log1` のFOMC `position_overlap` 対応
4. `16_UJ_T10A` のFOMC `position_overlap` 対応

これにより、Forward Phase 3-Aで発見された実運用上のEvent Filter抜けを補正する。
