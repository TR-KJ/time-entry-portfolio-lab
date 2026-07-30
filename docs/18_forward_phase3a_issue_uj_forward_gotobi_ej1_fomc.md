# Forward Phase 3-A Issue: UJ Forward Gotobi and EJ1 Event Overlap

## 1. Purpose

Forward Phase 3-Aのフォワードテスト中に確認された、以下2点の挙動について整理し、次回EA修正仕様として記録する。

対象EA:

- `src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

確認された課題:

1. `12_UJ_Short_Core` に前倒しゴトウビ判定がない
2. `1_EJ_Log1` が一部重要イベントの `position_overlap` 停止対象になっていない

本件は、EAコードの暴走やLot計算不具合ではなく、実運用に向けた仕様追加・仕様補正として扱う。

---

## 2. Issue 1: 12_UJ_Short_Core Forward Gotobi

### 2.1 Observed Forward Log

2026/7/24、`12_UJ_Short_Core` が以下のログでEntryした。

- Date: 2026/7/24
- Strategy: `12_UJ_Short_Core`
- Symbol: `USDJPY`
- Mode: `NORMAL`
- Entry Time: 08:04 JST
- Direction: SELL
- SL: 50.0 pips
- TP: None

Log:

- `LOT CALC. Symbol=USDJPY, WeeklyBase=2960288.00, RiskPercent=1.00, RiskAmount=29602.88, SL=50.0, PipValuePerLot=1000.0000, RawLot=0.5921, Lot=0.59`
- `SELL entry success. Symbol=USDJPY, Mode=NORMAL, Lot=0.59, Bid=163.842, SL=164.342, TP=None`

### 2.2 Current Behavior

現行EAでは、`12_UJ_Short_Core` のGOTO判定は以下のみである。

- 20日
- 25日
- 30日

そのため、2026/7/24は、翌7/25が土曜日で実務上は前倒しゴトウビに該当するが、現行EAではGOTOとして認識されず、`NORMAL` モードでEntryした。

### 2.3 Expected Behavior

2026/7/24は、7/25土曜日の前倒しゴトウビとして扱いたい。

期待される動作:

- 2026/7/24
- `12_UJ_Short_Core`
- Mode: `GOTO`
- Entry Time: 09:55 JST
- SL: 20.0 pips
- TP: 50.0 pips

### 2.4 Fixed Specification

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

理由:

- `12_UJ_Short_Core` は20日より前はEntry対象外であるため
- 20日の前倒しを採用すると、19日または18日など、20日より前の日にEntryすることになり、Strategyの基本稼働条件と矛盾するため

祝日:

- 祝日は前倒し対象にしない
- 理由は、海外市場が稼働しているため

### 2.5 Final Gotobi Logic

最終仕様:

- 20 / 25 / 30 は通常GOTO
- 25 / 30 が土日の場合のみ、直前金曜を前倒しGOTO
- 20 が土日の場合は、前倒しGOTOにしない
- 祝日は考慮しない

### 2.6 Implementation Direction

実運用を考慮し、2026年固定配列ではなく、ロジック判定で実装する。

判定イメージ:

- 今日が20日、25日、30日ならGOTO
- 今日が金曜日の場合、翌日または翌々日を確認
- 翌日または翌々日が25日または30日ならGOTO
- 翌日または翌々日が20日の場合はGOTOにしない
- 祝日は判定しない

---

## 3. Issue 2: 1_EJ_Log1 Event Overlap

### 3.1 Observed Forward Log

2026/7/29、`1_EJ_Log1` が以下のログでEntryした。

- Date: 2026/7/29
- Strategy: `1_EJ_Log1`
- Symbol: `EURJPY`
- Entry Time: 13:55 JST
- Direction: BUY
- Exit Time: 2026/7/30 04:55 JST
- FOMC: 2026/7/30 03:00 JST
- FOMC Stop Window: 00:00〜06:00 JST

Log:

- `LOT CALC. Symbol=EURJPY, WeeklyBase=2965632.00, RiskPercent=1.00, RiskAmount=29656.32, SL=70.0, PipValuePerLot=1000.0000, RawLot=0.4237, Lot=0.42`
- `BUY entry success. Symbol=EURJPY, Lot=0.42, Ask=186.353, SL=185.653, TP=188.853`

### 3.2 Current Behavior

現行EAでは、`1_EJ_Log1` は以下の特殊停止のみを持つ。

- 2月停止
- 毎月1日停止
- `US_CPI_WEEK_WED` 停止

そのため、`1_EJ_Log1` は現行コードでは、以下イベントの `position_overlap` 停止対象になっていない。

- FOMC
- US_NFP
- BOJ
- ECB

結果として、2026/7/29 13:55 Entry、2026/7/30 04:55 Exitの保有時間が、2026/7/30 03:00 FOMCの停止ウィンドウと重なっていたが、Entry停止されなかった。

### 3.3 Expected Behavior

`1_EJ_Log1` について、以下イベントは `position_overlap` で停止したい。

- FOMC
- US_NFP
- BOJ
- ECB

一方、US CPIについては現行の特殊停止を維持する。

### 3.4 Fixed Specification

`1_EJ_Log1` のEvent Candidate C判定を以下で固定する。

- FOMC: position_overlap
- US_NFP: position_overlap
- BOJ: position_overlap
- ECB: position_overlap
- US CPI: 現行の `US_CPI_WEEK_WED` 特殊停止を維持

つまり、`1_EJ_Log1` については、US CPIを通常の `position_overlap` にはしない。

### 3.5 Event Time and Window

`1_EJ_Log1` の `position_overlap` 判定に使用するイベント時刻と停止ウィンドウは以下とする。

| Event | Event Time JST | Pre Minutes | Post Minutes | Stop Window |
|---|---:|---:|---:|---|
| FOMC | 03:00 | 180 | 180 | 00:00〜06:00 |
| US_NFP | 21:30 | 120 | 120 | 19:30〜23:30 |
| BOJ | 12:00 | 180 | 180 | 09:00〜15:00 |
| ECB | 21:15 | 120 | 120 | 19:15〜23:15 |

### 3.6 Required Input Additions

現行EAには、FOMC / ECB の `position_overlap` 用inputは存在するが、US_NFP / BOJ の `position_overlap` 用inputが存在しない。

そのため、以下inputを追加する。

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

既存FOMC:

- `InpFomcEventHourJST = 3`
- `InpFomcEventMinuteJST = 0`
- `InpFomcPreMinutes = 180`
- `InpFomcPostMinutes = 180`

既存ECB:

- `InpEcbEventHourJST = 21`
- `InpEcbEventMinuteJST = 15`
- `InpEcbPreMinutes = 120`
- `InpEcbPostMinutes = 120`

### 3.7 Expected Example

2026/7/29の `1_EJ_Log1` は、以下の条件によりEntry停止されるべきである。

- Entry: 2026/7/29 13:55 JST
- Exit: 2026/7/30 04:55 JST
- Event: FOMC
- Event Time: 2026/7/30 03:00 JST
- Stop Window: 2026/7/30 00:00〜06:00 JST
- Entry予定時刻〜Exit予定時刻がStop Windowと重なる

Expected Result:

- `EVENT OVERLAP STOP`
- Entryなし

---

## 4. Confirmed Final Fix Scope

今回の修正対象は以下2点とする。

### Fix 1

`12_UJ_Short_Core` に前倒しゴトウビ判定を追加する。

仕様:

- 20 / 25 / 30 は通常GOTO
- 25 / 30 が土日の場合のみ、直前金曜を前倒しGOTO
- 20 が土日の場合は、前倒しGOTOにしない
- 祝日は考慮しない

### Fix 2

`1_EJ_Log1` に以下イベントの `position_overlap` 停止を追加する。

- FOMC
- US_NFP
- BOJ
- ECB

US CPIは現行の `US_CPI_WEEK_WED` 特殊停止を維持する。

追加Event Time:

- NFP: 21:30 JST / 前後120分
- BOJ: 12:00 JST / 前後180分

---

## 5. Proposed Next EA Version

次回EAファイル名候補:

- `time_entry_step9_2_2_uj_forward_gotobi_ej1_event_overlap_fix_28strategies.mq5`

修正内容:

1. `12_UJ_Short_Core` 前倒しゴトウビ対応
2. `1_EJ_Log1` FOMC / NFP / BOJ / ECB `position_overlap` 対応
3. US_NFP / BOJ の `position_overlap` 用input追加
4. 既存のEvent Candidate C、ATR OFF、Weekly Fixed Risk機能は維持

---

## 6. Forward Test Interpretation

今回確認された2件は、EAの暴走やLot計算不具合ではない。

Forward Phase 3-Aで確認済みの正常項目:

- Weekly Fixed Risk Lot計算
- Entry
- Exit
- Event Candidate Cの既存対象イベント停止
- ATR OFF
- Weekend / Market Closed Guard

今回の2件は、以下として扱う。

- 実運用に向けた仕様補正
- Event Candidate Cの対象拡張
- UJ12のゴトウビ判定補正

したがって、Forward Phase 3-Aは継続可能だが、次回EAで本修正を反映する。

---

## 7. Conclusion

Forward Phase 3-A中に確認された以下2点について、次回EA修正対象として確定する。

1. `12_UJ_Short_Core` の前倒しゴトウビ対応
2. `1_EJ_Log1` のFOMC / NFP / BOJ / ECB `position_overlap` 対応

本修正により、実運用に近いゴトウビ認識と、`1_EJ_Log1` の重要イベント直撃回避を実現する。
