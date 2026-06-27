# Weekend / Market Closed Guard 追加仕様

## 目的

フォワード運用中、土曜日・日曜日など市場クローズ中にも、Entry時刻に到達したStrategyが `Date Rule` / `Event Filter` / `ATR Filter` 判定まで進む可能性が確認された。

発注事故は発生していないが、ログ整理と安全性向上のため、全28戦略共通の `Weekend / Market Closed Guard` を追加する。

---

## 対象EA

```text
src/EA/time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

---

## 現行フォワード状態

現在のフォワードテストは動作確認フェーズ。

```text
Forward Phase 1-A
```

現行設定：

```text
LotMode = Fixed Lot
FixedLot = 0.01
ATR Filter = ON
Event Filter = ON
EmergencyStop = false
TestMode = false
MockJST = false
UseTestTimes = false
```

現時点では、EAは概ね正常に動作している。

ただし、フォワード実施期間はまだ約3日間のため、既存稼働EAを即差し替えるのではなく、別ファイルで修正版を作成し、TestMode / MockJSTで確認してからPhase移行する。

---

## 修正方針

全28戦略共通で、土日・市場クローズ中のEntryを止める。

このGuardは特定Strategy専用ではなく、全Strategy共通の安全装置とする。

---

## 追加するinput候補

```mq5
input bool InpUseWeekendMarketClosedGuard = true;
input bool InpPrintWeekendGuardLogs = true;
input bool InpSuppressWeekendGuardLogsOncePerDay = true;
```

ただし、初回実装時は既存挙動との切替確認をしやすくするため、以下でもよい。

```mq5
input bool InpUseWeekendMarketClosedGuard = false;
```

実運用Phase 2-Aへ進む段階で `true` にする。

---

## 判定順

理想の判定順は以下。

```text
TryEntry()
↓
Enabled確認
↓
Symbol確認
↓
Entry時刻確認
↓
Weekend / Market Closed Guard
↓
EmergencyStop確認
↓
Entry Filters
   ├─ ATR Filter
   └─ Event Filter
↓
AlreadyEnteredToday
↓
HasOpenPosition
↓
OrderSend
```

重要：

```text
Weekend / Market Closed Guard は ATR Filter / Event Filter より前に置く。
```

理由：

```text
市場クローズ中にATR判定・Event判定まで進ませないため。
```

---

## 判定ロジック

### 初期仕様

まずはJST基準で以下を市場クローズ扱いにする。

```text
土曜日
日曜日
```

MQL5上の `MqlDateTime.day_of_week` を使う。

```text
0 = Sunday
6 = Saturday
```

判定：

```text
day_of_week == 0 → stop
day_of_week == 6 → stop
```

---

## 関数案

### IsWeekendMarketClosedJST

```mq5
bool IsWeekendMarketClosedJST(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.day_of_week == 0)
   {
      return true;
   }

   if(dt.day_of_week == 6)
   {
      return true;
   }

   return false;
}
```

---

### PassWeekendMarketClosedGuard

```mq5
bool PassWeekendMarketClosedGuard(StrategyConfig &cfg, datetime jst_time)
{
   if(!InpUseWeekendMarketClosedGuard)
   {
      return true;
   }

   if(IsWeekendMarketClosedJST(jst_time))
   {
      PrintWeekendGuardLog(cfg, jst_time, "Skip entry: weekend / market closed.");
      return false;
   }

   return true;
}
```

---

## ログ仕様

ログ例：

```text
[Step9 WeekendGuard 12_UJ_Short_Core] Skip entry: weekend / market closed. Symbol=USDJPY, JST=2026.06.27 08:04
```

ログは、同一Strategy・同一日付では1回だけに抑制する。

---

## ログ抑制仕様

Runtime配列で抑制する。

候補：

```mq5
string printed_weekend_guard_log_keys[];
int printed_weekend_guard_log_count = 0;
```

ログキー候補：

```text
strategy_code | symbol | magic | date_key | WEEKEND_GUARD
```

---

## TryEntryへの追加位置

現行の `TryEntry()` に、Entry時刻確認後、EmergencyStop前に追加する。

イメージ：

```mq5
void TryEntry(StrategyConfig &cfg, datetime jst_time)
{
   if(!cfg.enabled) return;
   if(!EnsureSymbolReady(cfg.symbol, cfg.strategy_name)) return;
   if(!IsEntryTime(cfg, jst_time)) return;

   if(!PassWeekendMarketClosedGuard(cfg, jst_time))
   {
      return;
   }

   if(InpEmergencyStop)
   {
      PrintEmergencyStopSkip(cfg, jst_time);
      return;
   }

   if(!PassEntryFilters(cfg, jst_time))
   {
      PrintSkip(cfg.strategy_name, "Skip entry: entry filter rejected.");
      return;
   }

   if(AlreadyEnteredToday(cfg, jst_time)) return;
   if(HasOpenPosition(cfg.symbol, cfg.magic)) return;

   if(cfg.direction == DIR_LONG) SendBuyOrder(cfg, jst_time);
   if(cfg.direction == DIR_SHORT) SendSellOrder(cfg, jst_time);
}
```

---

## TestMode / MockJST確認項目

### Test 1：土曜日は停止

設定例：

```text
InpUseMockJstDateTime = true
MockJST = 2026-06-27 土曜日
```

期待：

```text
Entry時刻に到達しても発注しない
ATR Filterまで進まない
Event Filterまで進まない
Weekend Guardログが出る
```

---

### Test 2：日曜日は停止

設定例：

```text
InpUseMockJstDateTime = true
MockJST = 2026-06-28 日曜日
```

期待：

```text
Entry時刻に到達しても発注しない
Weekend Guardログが出る
```

---

### Test 3：平日は通過

設定例：

```text
InpUseMockJstDateTime = true
MockJST = 平日のEntry時刻
```

期待：

```text
Weekend Guardでは止まらない
後続のEmergencyStop / Event / ATR / Entry処理へ進む
```

---

### Test 4：InpUseWeekendMarketClosedGuard=false

期待：

```text
Weekend Guard追加前と同じ挙動
```

---

### Test 5：ログ抑制

期待：

```text
同一Strategy・同一日付ではWeekend Guardログが1回だけ出る
```

---

## Phase 2-Aとの関係

Phase 2-Aは以下で進める。

```text
Forward Phase 2-A
Event Candidate C + ATR OFF + FixedLot 0.01
```

ただし、Weekend GuardはPhase 2-Aの前提となる共通安全装置として先に追加する。

Phase 2-A予定設定：

```text
LotMode = Fixed Lot
FixedLot = 0.01
InpUseGlobalAtrP70Filter = false
InpUseEventFilter = true
InpUseEventCandidateC = true
InpUseWeekendMarketClosedGuard = true
```

---

## 実装時の注意点

```text
現行EAを直接上書きしない
別名EAとして作成する
まずWeekend Guardのみ追加する
Event Candidate Cは次Stepで追加する
ATR OFFはinput変更のみで確認する
```

---

## 推奨ファイル名

現行EA：

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

Weekend Guard追加版候補：

```text
time_entry_step9_1_weekend_guard_28strategies.mq5
```

または、既存Step番号を維持する場合：

```text
time_entry_step8_3_2_weekend_guard_28strategies.mq5
```

推奨：

```text
time_entry_step8_3_2_weekend_guard_28strategies.mq5
```

理由：

```text
Step 8.3系のフォワード準備EAの小修正として扱えるため。
```

---

## 現時点の判断

Weekend / Market Closed Guard追加は、全戦略共通の安全装置であり、Event Candidate CやATR OFFより先に追加して問題ない。

ただし、現行フォワード中EAはまだ約3日間の動作確認段階のため、即差し替えはしない。

まずは別名EAとして作成し、TestMode / MockJSTで確認する。

確認後、Phase 2-Aへ移行する。
