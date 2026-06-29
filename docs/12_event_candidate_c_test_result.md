# Event Candidate C Test Result

## 対象EA

```text
src/EA/time_entry_step9_2_event_candidate_c_28strategies.mq5
```

---

## 目的

Event Candidate C の実装後、以下が想定どおり動作するか確認する。

```text
1. InpUseEventCandidateC=false で現行Event Filter互換になる
2. US CPI / NFP / BOJ が date_all_day で停止する
3. FOMC が position_overlap で停止する
4. FOMC が position_overlap 非該当なら通過する
5. ATR OFF + Event Candidate C の組み合わせで動作する
```

---

## 前提

Event Candidate C は、現行Event Filterを残したまま、inputで切り替え可能にする方式。

```text
InpUseEventFilter = true
InpUseEventCandidateC = false
→ 現行Event Filter

InpUseEventFilter = true
InpUseEventCandidateC = true
→ Event Candidate C
```

---

## 共通テスト設定

基本設定：

```text
InpUseWeekendMarketClosedGuard = true
InpUseEventFilter = true
InpPrintEventFilterLogs = true
InpPrintDebug = true

InpTestMode = true
InpUseMockJstDateTime = true
InpUseTestTimes = false
```

Event Candidate C単体を確認するため、原則としてATR FilterはOFFにする。

```text
InpUseGlobalAtrP70Filter = false
InpPrintAtrFilterLogs = false
```

---

# Test 1：InpUseEventCandidateC=false / 現行Event Filter互換

## 目的

`InpUseEventCandidateC=false` の場合、Candidate Cではなく現行Event Filter側で判定されることを確認する。

## 条件

```text
InpUseEventFilter = true
InpUseEventCandidateC = false
InpUseGlobalAtrP70Filter = false
InpUseWeekendMarketClosedGuard = true
```

## Strategy 1

```text
1_EJ_Log1
```

## 結果

```text
OK
EVENT REJECT
Reason: CPI week wed
```

## 補足

`1_EJ_Log1` は、US CPI当日停止ではなく、CPI週水曜停止系の現行ルールで停止した。

これはCandidate Cではなく、現行Event Filter側の既存ルールが動作している確認になる。

---

## Strategy 2

```text
5_GJ_Port_Log2
```

## 結果

```text
OK
EVENT REJECT
```

---

## 判定

```text
OK
```

`InpUseEventCandidateC=false` の場合、Candidate Cではなく現行Event Filter側で停止することを確認。

---

# Test 2：US CPI / NFP / BOJ date_all_day

## 目的

Event Candidate C ON時に、以下の重要イベントが `date_all_day` として停止されることを確認する。

```text
US_CPI
US_NFP
BOJ
```

---

## Test 2-A：US CPI date_all_day

### 条件

```text
InpUseEventCandidateC = true
InpUseGlobalAtrP70Filter = false
Strategy = 5_GJ_Port_Log2
Event = US_CPI
```

### 結果

```text
OK
EVENT REJECT
```

### 補足：1_EJ_Log1について

`1_EJ_Log1` では、US CPI当日のrejectログは出なかった。

これは異常ではなく、`1_EJ_Log1` がUS CPI当日停止ではなく、CPI week Wednesday系の特殊ルールを持つため。

記録上は以下の扱いとする。

```text
5_GJ_Port_Log2：
US CPI date_all_day 確認OK

1_EJ_Log1：
US CPI当日停止の確認対象からは除外
CPI week Wednesday特殊ルールとして別扱い
```

---

## Test 2-B：NFP date_all_day

### 条件

```text
InpUseEventCandidateC = true
InpUseGlobalAtrP70Filter = false
Strategy = 5_GJ_Port_Log2
Event = NFP
```

### 結果

```text
OK
EVENT REJECT
```

### 判定

```text
NFP日がCandidate Cのdate_all_dayで停止することを確認。
```

---

## Test 2-C：BOJ date_all_day

### 条件

```text
InpUseEventCandidateC = true
InpUseGlobalAtrP70Filter = false
Strategy = 5_GJ_Port_Log2
Event = BOJ
```

### 結果

```text
OK
EVENT REJECT
```

### 判定

```text
BOJ日がCandidate Cのdate_all_dayで停止することを確認。
```

---

# ここまでの判定

```text
Test 1：OK
Test 2-A：OK
Test 2-B：OK
Test 2-C：OK
```

Event Candidate C の以下は確認済み。

```text
InpUseEventCandidateC=false で現行Event Filter互換
US CPI / NFP / BOJ の date_all_day 停止
```

---

# Test 3：FOMC position_overlap / 重なる場合だけ停止

## 目的

FOMCは、Candidate Cでは `date_all_day` ではなく `position_overlap` として扱う。

つまり、FOMC日だから終日停止するのではなく、予定保有時間がFOMC停止ウィンドウと重なる場合のみ停止する。

---

## FOMC設定

```text
FOMC JST Date = 2026-07-30
InpFomcEventHourJST = 3
InpFomcEventMinuteJST = 0
InpFomcPreMinutes = 180
InpFomcPostMinutes = 180
```

停止ウィンドウ：

```text
2026-07-30 00:00 〜 2026-07-30 06:00
```

---

## 確認したいこと

予定ポジション保有時間が以下に重なる場合、停止する。

```text
Entry予定時刻 〜 Exit予定時刻
と
2026-07-30 00:00 〜 2026-07-30 06:00
```

---

## 使用候補Strategy

FOMC position_overlap確認には、FOMC対象かつ強制date_all_day対象ではないStrategyを使う。

候補：

```text
27_EA_China_Demand
28_GA_China_Demand
13_UJ_Fix_MidWeek
15_UJ_Sat_Aug
```

ただし、Date Ruleに先回りされないよう、Entry曜日・日付条件に注意する。

---

## 期待ログ

予定保有時間がFOMCウィンドウに重なる場合、以下のようなログが出る。

```text
EVENT OVERLAP STOP
Event=FOMC
EventTime=2026.07.30 03:00
WindowPre=180
WindowPost=180
```

その後、汎用ログとして以下が出ても問題なし。

```text
Skip entry: entry filter rejected.
```

---

## 合格条件

```text
EVENT OVERLAP STOP が出る
CANDIDATE_C_DATE_FOMC では止まらない
EventTime が 2026.07.30 03:00 になっている
予定Entry〜ExitがFOMCウィンドウに重なる場合だけ停止する
OrderSendされない
```

---

# Test 4：FOMC position_overlap / 重ならない場合は通過

## 目的

FOMC日でも、予定保有時間がFOMC停止ウィンドウに重ならない場合は、Event Candidate Cでは停止しないことを確認する。

---

## FOMC停止ウィンドウ

```text
2026-07-30 00:00 〜 2026-07-30 06:00
```

---

## 確認したいこと

予定保有時間が上記ウィンドウに重ならない場合、FOMCでは停止しない。

例：

```text
Entry予定時刻：10:00
Exit予定時刻：15:50
```

この場合、

```text
10:00 〜 15:50
```

は、

```text
00:00 〜 06:00
```

と重ならないため、FOMCでは停止しない。

---

## 期待

以下のログが出ないこと。

```text
EVENT OVERLAP STOP
CANDIDATE_C_DATE_FOMC
```

ただし、別理由で止まる可能性はある。

例：

```text
Date rule reject
Skip entry: entry filter rejected
Already entered today
```

これらはFOMC position_overlapの異常ではない。

---

## 合格条件

```text
FOMC日でもEVENT OVERLAP STOPが出ない
CANDIDATE_C_DATE_FOMCも出ない
後続判定へ進む
```

---

# Test 5：ATR OFF + Event Candidate C 組み合わせ確認

## 目的

Forward Phase 2-A予定設定で、ATR FilterがOFFになり、Event Candidate Cのみでイベント停止されることを確認する。

---

## Phase 2-A予定設定

```text
LotMode = Fixed Lot
FixedLot = 0.01

InpUseWeekendMarketClosedGuard = true
InpUseGlobalAtrP70Filter = false
InpUseEventFilter = true
InpUseEventCandidateC = true
```

---

## Test 5-A：イベント日にEvent Candidate Cで停止

### 条件

```text
InpUseGlobalAtrP70Filter = false
InpUseEventCandidateC = true
Event = US_CPI / NFP / BOJ など
Strategy = 5_GJ_Port_Log2
```

### 期待

```text
Event Candidate Cで停止
ATR REJECTは出ない
OrderSendされない
```

### 合格条件

```text
EVENT REJECTが出る
ATR REJECTが出ない
Skip entry: entry filter rejected. が出てもOK
```

---

## Test 5-B：イベント対象外日はATRで止まらない

### 条件

```text
InpUseGlobalAtrP70Filter = false
InpUseEventCandidateC = true
Event対象外の平日
Strategy = 5_GJ_Port_Log2 など
```

### 期待

```text
ATR REJECTが出ない
EVENT REJECTが出ない
Weekend Guardでも止まらない
```

ただし、Date RuleやAlreadyEnteredTodayで止まる可能性はある。

---

## 合格条件

```text
ATR OFFなのでATR REJECTが出ない
イベント対象外ならEVENT REJECTも出ない
後続判定へ進む
```

---

# ログ繰り返しについて

MockJST固定中は、EAのTimer処理により同じ判定が繰り返されるため、ログが複数回出ることがある。

これはTestMode / MockJST中の挙動としては問題なし。

通常フォワードでは以下を推奨する。

```text
InpSuppressWeekendGuardLogsOncePerDay = true
InpSuppressEventLogsOncePerDay = true
InpSuppressRuleRejectLogsOncePerDay = true
InpPrintSkipLogs = false
InpPrintAtrFilterLogs = false
```

---

# 次回再開時の作業

次回は以下から再開する。

```text
Test 3：FOMC position_overlap / 重なる場合だけ停止
Test 4：FOMC position_overlap / 重ならない場合は通過
Test 5：ATR OFF + Event Candidate C 組み合わせ確認
```

特にTest 3 / 4では、使用StrategyのEntry JST / Exit JSTと、Date Rule条件を確認したうえでMockJSTを指定する。

---

# 現時点の結論

Event Candidate Cの前半テストは合格。

```text
現行Event Filter互換：OK
US CPI date_all_day：OK
NFP date_all_day：OK
BOJ date_all_day：OK
```

次はFOMC position_overlapの確認へ進む。

# docs/12_event_candidate_c_test_result.md 追記：FOMC position_overlap テスト結果と修正方針

## 追加テスト対象EA

```text
src/EA/time_entry_step9_2_event_candidate_c_28strategies.mq5
```

---

## Test 4：FOMC position_overlap / 重ならない場合は通過

### Test 4-A

```text
Strategy: 27_EA_China_Demand
MockJST: 2026-12-09 10:00
Entry: 2026-12-09 10:00
Exit: 2026-12-09 15:50
FOMC EventTime: 2026-12-09 03:00
Window: 2026-12-09 00:00〜06:00
```

### 結果

```text
OK
```

### 判定

```text
EVENT OVERLAP STOP は出ない。
CANDIDATE_C_DATE_FOMC も出ない。
FOMC停止ウィンドウと予定保有時間が重ならないため、Event Candidate Cでは停止しない。
```

その後、Entry後に以下のログが出た。

```text
skip entry : already entered today
```

これは、MockJST固定中にOnTimerで同じEntry判定が繰り返され、すでに当日Entry済みとなったため。
異常ではない。

---

### Test 4-B

```text
Strategy: 25_AU_China_Demand
MockJST: 2026-07-30 10:00
Entry: 2026-07-30 10:00
Exit: 2026-07-30 15:50
FOMC EventTime: 2026-07-30 03:00
Window: 2026-07-30 00:00〜06:00
```

### 結果

```text
OK
```

### 判定

```text
EVENT OVERLAP STOP は出ない。
CANDIDATE_C_DATE_FOMC も出ない。
FOMC停止ウィンドウと予定保有時間が重ならないため、Event Candidate Cでは停止しない。
```

その後、Entry後に以下のログが出た。

```text
skip entry : already entered today
```

これはTestMode / MockJST中の正常な繰り返しログとして扱う。

---

## Test 3：FOMC position_overlap / 重なる場合だけ停止

### Test 3-A

```text
Strategy: 3_EJ_NightBlitz_21
MockJST: 2026-07-29 21:56
Entry: 2026-07-29 21:56
Exit: 2026-07-30 05:27
FOMC EventTime: 2026-07-30 03:00
Window: 2026-07-30 00:00〜06:00
```

### 期待

```text
EVENT OVERLAP STOP
```

### 結果

```text
NG
エントリーしてしまった。
```

### 判定

予定保有時間はFOMC停止ウィンドウと重なっている。

```text
Entry〜Exit: 2026-07-29 21:56〜2026-07-30 05:27
FOMC Window: 2026-07-30 00:00〜06:00
```

本来は停止すべきだが、実際にはEntryした。

推定原因：

```text
Event Candidate Cのposition_overlap判定が、Entry日の日付キーを中心にイベントを確認しており、
Entry翌日のFOMC時刻を正しく拾えていない可能性が高い。
```

---

### Test 3-B

```text
Strategy: 18_EA_2
MockJST: 2026-07-29 09:59
Entry: 2026-07-29 09:59
Exit: 2026-07-30 05:26
FOMC EventTime: 2026-07-30 03:00
Window: 2026-07-30 00:00〜06:00
```

### 結果

```text
Entry停止
EVENT REJECT
その後、skip entry : entry filter rejected が繰り返し出る
```

### 判定

Entry自体は停止したが、ログは `EVENT OVERLAP STOP` ではなく `EVENT REJECT`。

また、2026-07-29は月末3営業日前に該当する可能性があり、EA系の月末停止に先回りされた可能性が高い。

そのため、FOMC position_overlapの合格確認としては未確定。

---

### Test 3-C

```text
Strategy: 19_EA_3
MockJST: 2026-07-29 20:56
Entry: 2026-07-29 20:56
Exit: 2026-07-30 10:00
FOMC EventTime: 2026-07-30 03:00
Window: 2026-07-30 00:00〜06:00
```

### 結果

```text
Entry停止
EVENT REJECT
その後、skip entry : entry filter rejected が繰り返し出る
```

### 判定

Test 3-Bと同じく、Entry自体は停止したが、`EVENT OVERLAP STOP` ではない。

月末3営業日前停止など、別のEvent / Ruleで停止した可能性が高いため、FOMC position_overlapの合格確認としては未確定。

---

## ここまでの判定

```text
Test 4-A：OK
Test 4-B：OK
Test 3-A：NG
Test 3-B：停止したが、overlap確認としては未確定
Test 3-C：停止したが、overlap確認としては未確定
```

---

## 発見した課題

```text
FOMC position_overlapで、Entry日翌日のFOMC時刻を拾えていない可能性がある。
```

特に以下のケースで問題が発生した。

```text
Entry: 2026-07-29 21:56
Exit: 2026-07-30 05:27
FOMC: 2026-07-30 03:00
Window: 2026-07-30 00:00〜06:00
```

このケースは予定保有時間とFOMC停止ウィンドウが明確に重なるため、本来は `EVENT OVERLAP STOP` で停止すべき。

---

## 修正方針

新EAを作成する。

```text
src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5
```

修正内容：

```text
1. position_overlap判定で、Entry日だけでなく予定保有期間を確認する
2. Entry日翌日のイベントも確認対象にする
3. Entry予定時刻〜Exit予定時刻 と Event Window の重なりで停止判定する
4. EVENT OVERLAP STOPログで停止理由を明示する
5. 既存のdate_all_day停止、月末停止、年末年始停止は維持する
```

---

## 修正版での再テスト候補

### Retest 3-A

```text
Strategy: 3_EJ_NightBlitz_21
MockJST: 2026-07-29 21:56
Expected: EVENT OVERLAP STOP
```

### Retest 3-B 推奨

月末停止に先回りされにくい日付を使う。

```text
Strategy: 18_EA_2
MockJST: 2026-12-08 09:59
Entry: 2026-12-08 09:59
Exit: 2026-12-09 05:26
FOMC: 2026-12-09 03:00
Window: 2026-12-09 00:00〜06:00
Expected: EVENT OVERLAP STOP
```

### Retest 4-A

```text
Strategy: 27_EA_China_Demand
MockJST: 2026-12-09 10:00
Expected: EVENT OVERLAP STOPなし
```

---

## 次にやること

```text
1. time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5 を作成
2. MetaEditorでコンパイル
3. Retest 3-A / 3-B / 4-A を実施
4. EVENT OVERLAP STOPログが出るか確認
5. 問題なければTest 5：ATR OFF + Event Candidate C確認へ進む
```

---

# Event Candidate C Retest Result

## 対象EA

src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

---

## 修正目的

前回テストで、FOMC position_overlap において、Entry日翌日のFOMC発表時刻を正しく拾えていない可能性が確認された。

特に以下のケースで、本来はFOMCウィンドウと重なるにもかかわらず、Entryしてしまった。

Strategy: 3_EJ_NightBlitz_21  
Entry: 2026-07-29 21:56  
Exit : 2026-07-30 05:27  
FOMC EventTime: 2026-07-30 03:00  
Window: 2026-07-30 00:00〜06:00

このため、position_overlap判定を修正した。

---

## 修正内容

- Entry日だけでなく、予定保有期間中のイベントを確認する
- Entry予定時刻〜Exit予定時刻とEvent Windowの重なりで停止判定する
- 翌日深夜FOMCを拾えるようにする
- EVENT OVERLAP STOPログで停止理由を明示する

---

## Retest 3-A：3_EJ_NightBlitz_21 / FOMC overlap

### 条件

Strategy: 3_EJ_NightBlitz_21  
MockJST: 2026-07-29 21:56  
Entry: 2026-07-29 21:56  
Exit : 2026-07-30 05:27  
FOMC EventTime: 2026-07-30 03:00  
Window: 2026-07-30 00:00〜06:00

### 結果

OK  
EVENT OVERLAP STOP

### 補足

その後、以下のログが繰り返し出る。

skip entry : entry filter rejected

これはMockJST固定中に同じ判定が繰り返され、Event Filterで止まり続けているため。異常ではない。

---

## Retest 3-B：18_EA_2 / FOMC overlap

### 条件

Strategy: 18_EA_2  
MockJST: 2026-12-08 09:59  
Entry: 2026-12-08 09:59  
Exit : 2026-12-09 05:26  
FOMC EventTime: 2026-12-09 03:00  
Window: 2026-12-09 00:00〜06:00

### 結果

OK  
EVENT OVERLAP STOP

### 補足

その後、以下のログが繰り返し出る。

skip entry : entry filter rejected

これはMockJST固定中に同じ判定が繰り返され、Event Filterで止まり続けているため。異常ではない。

---

## Retest 4-A：27_EA_China_Demand / FOMC non-overlap

### 条件

Strategy: 27_EA_China_Demand  
MockJST: 2026-12-09 10:00  
Entry: 2026-12-09 10:00  
Exit : 2026-12-09 15:50  
FOMC EventTime: 2026-12-09 03:00  
Window: 2026-12-09 00:00〜06:00

### 結果

OK  
Entry

### 判定

予定保有時間 10:00〜15:50 は、FOMC停止ウィンドウ 00:00〜06:00 と重ならない。

そのため、FOMC position_overlapでは停止せず、Entryまで進むことを確認。

---

## Retest判定

Retest 3-A：OK  
Retest 3-B：OK  
Retest 4-A：OK

確認できたこと：

- FOMC position_overlapで、翌日深夜FOMCを正しく拾える
- 予定保有時間がFOMCウィンドウと重なる場合はEVENT OVERLAP STOPで停止する
- 予定保有時間がFOMCウィンドウと重ならない場合は停止しない

---

## 結論

Event Candidate C の position_overlap 修正は合格。

time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

を、Event Candidate C実装版の有力候補とする。

次は、ATR OFF + Event Candidate C の組み合わせ確認へ進む。
