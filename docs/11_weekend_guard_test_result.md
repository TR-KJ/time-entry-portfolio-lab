# Weekend Guard Test Result

## 対象EA

```text
src/EA/time_entry_step9_1_weekend_guard_28strategies.mq5
```

---

## 目的

Weekend / Market Closed Guard が想定どおり動作するか確認する。

確認対象：

```text
土曜日はWeekend Guardで停止する
日曜日はWeekend Guardで停止する
平日はWeekend Guardでは停止しない
Weekend Guard OFF時は旧挙動に戻る
```

---

## 前提

Weekend Guardは、土曜日・日曜日など市場クローズ中に、Entry時刻へ到達したStrategyがATR Filter / Event Filterまで進まないようにするための共通安全装置。

判定位置：

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

---

## テスト時の主な設定

```text
InpUseWeekendMarketClosedGuard = true
InpPrintWeekendGuardLogs = true
InpUseMockJstDateTime = true
InpTestMode = true
```

ログ確認のため、テスト中は以下を一時的に使用した。

```text
InpPrintDebug = true
InpPrintSkipLogs = true
InpPrintRuleRejectLogs = true
InpPrintAtrFilterLogs = true
InpPrintEventFilterLogs = true
```

---

## Test 1：Saturday / Weekend Guard ON

### 条件

```text
MockJST: 2026-06-27 08:04
Strategy: 12_UJ_Short_Core
InpUseWeekendMarketClosedGuard = true
```

### 期待

```text
Weekend Guardで停止
ATR Filter / Event Filterへ進まない
OrderSendされない
```

### 結果

```text
OK
```

Weekend Guardで停止することを確認。

---

## Test 2：Sunday / Weekend Guard ON

### 条件

```text
MockJST: 2026-06-28 08:04
Strategy: 12_UJ_Short_Core
InpUseWeekendMarketClosedGuard = true
```

### 期待

```text
Weekend Guardで停止
ATR Filter / Event Filterへ進まない
OrderSendされない
```

### 確認ログ例

```text
[Step9 WeekendGuard 12_UJ_Short_Core] Skip entry: weekend / market closed. Symbol=USDJPY, JST=2026.06.28 08:04
```

### 結果

```text
OK
```

Weekend Guardで停止することを確認。

---

## Test 3：Weekday / Weekend Guard ON

### 条件

```text
MockJST: 2026-06-26 08:04
Strategy: 12_UJ_Short_Core
InpUseWeekendMarketClosedGuard = true
```

### 期待

```text
Weekend Guardでは停止しない
後続のEntry Filterへ進む
```

### 確認ログ

```text
Skip entry: entry filter rejected.
```

### 結果

```text
OK
```

Weekend Guardでは停止せず、後続のEntry Filterへ進むことを確認。

補足：

```text
Skip entry: entry filter rejected. は、Weekend Guard通過後にATR FilterまたはEvent Filterで停止したことを示す汎用ログ。
Weekend Guardの異常ではない。
```

---

## Test 4：Saturday / Weekend Guard OFF

### 条件

```text
MockJST: 2026-06-27 08:04
Strategy: 12_UJ_Short_Core
InpUseWeekendMarketClosedGuard = false
```

### 期待

```text
Weekend Guardログは出ない
旧挙動どおり後続のEntry Filterへ進む
```

### 確認ログ

```text
Skip entry: entry filter rejected.
```

### 結果

```text
OK
```

Weekend Guard OFF時に、Weekend Guardで止まらず後続Entry Filterへ進むことを確認。

---

## ログが繰り返し出る件

Test中、以下のログが繰り返し出ることを確認した。

```text
Skip entry: entry filter rejected.
```

または、

```text
[Step9 WeekendGuard 12_UJ_Short_Core] Skip entry: weekend / market closed. Symbol=USDJPY, JST=2026.06.28 08:04
```

これは、MockJSTで日時を固定し、EAの `OnTimer()` により同じEntry判定が繰り返されるため。

テスト中の挙動としては問題なし。

本番・通常フォワードでは、ログ抑制を有効にする。

```text
InpSuppressWeekendGuardLogsOncePerDay = true
InpPrintSkipLogs = false
```

必要に応じて、以下も通常時は抑制する。

```text
InpPrintAtrFilterLogs = false
InpPrintEventFilterLogs = true
InpSuppressEventLogsOncePerDay = true
InpSuppressRuleRejectLogsOncePerDay = true
```

---

## 判定

```text
Weekend / Market Closed Guard は想定どおり動作。
```

確認できたこと：

```text
土曜日はWeekend Guardで停止
日曜日はWeekend Guardで停止
平日はWeekend Guardでは停止しない
Weekend Guard OFF時は旧挙動に戻る
```

特に重要な点：

```text
土日ではATR Filter / Event Filterより前に停止する。
```

---

## 結論

Weekend Guardは合格。

次の作業として、Event Candidate C 実装へ進む。

```text
Next Step:
Event Candidate C implementation
```
