# 05_forward_test_record_format.md

# フォワードテスト記録フォーマット

## 対象EA

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

## 目的

このドキュメントは、28ロジック統合EAのデモ口座フォワードテスト結果を記録するためのフォーマットである。

初回フォワードテストでは、利益・損失の評価よりも、EAが仕様どおりに動作しているかを優先して確認する。

確認優先順位：

```text
1. Entry時刻
2. Direction
3. Lot
4. SL / TP
5. Time exit
6. Event Filter
7. ATR Filter
8. ログの見やすさ
9. 想定外Entry / 想定外停止の有無
```

---

# 1. フォワードテスト基本情報

| Item | Value |
|---|---|
| Forward Test Start Date |  |
| MT5 Broker | OANDA Japan |
| Account Type | Demo |
| Account ID |  |
| Initial Balance |  |
| EA Version | time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5 |
| Lot Mode | Fixed Lot |
| Fixed Lot | 0.01 |
| ATR Filter | ON |
| Event Filter | ON |
| EmergencyStop | false |
| TestMode | false |
| MockJST | false |
| TestTimes | false |
| Operating PC | DELL Inspiron |
| VPS / Local PC | Local PC |
| Notes |  |

---

# 2. 初期input確認ログ

フォワード開始時に、以下を確認して記録する。

```text
InpEmergencyStop = false
InpLotMode = 0
InpFixedLot = 0.01
InpUseGlobalAtrP70Filter = true
InpUseEventFilter = true
InpTestMode = false
InpUseMockJstDateTime = false
InpUseTestTimes = false
InpPrintSkipLogs = false
```

確認日：

```text
YYYY-MM-DD
```

確認結果：

```text
OK / NG
```

メモ：

```text

```

---

# 3. 毎日確認チェックリスト

毎日1回、できれば朝または夜に確認する。

| Date | MT5 Running | Auto Trading ON | Connection OK | EA Running | Error Log | Notes |
|---|---|---|---|---|---|---|
|  | OK / NG | OK / NG | OK / NG | OK / NG | none /あり |  |

確認項目：

```text
MT5が起動している
OANDAデモ口座にログインしている
自動売買がON
EAがチャート上で稼働している
7通貨ペアの気配値が動いている
エキスパートタブに重大エラーがない
```

---

# 4. Entry記録フォーマット

Entryが発生したら記録する。

| Date | Strategy | Symbol | Direction | Scheduled Entry JST | Actual Entry JST | Lot | SL | TP | Result | Notes |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
|  |  |  |  |  |  |  |  |  | OK / NG |  |

確認ポイント：

```text
予定時刻どおりEntryしたか
Directionが正しいか
Lotが0.01か
SLが正しいか
TPが正しいか
コメント/Magicに問題がないか
```

---

# 5. Exit記録フォーマット

Time exitまたはSL/TP決済が発生したら記録する。

| Date | Strategy | Symbol | Direction | Entry JST | Exit JST | Exit Type | P/L | Notes |
|---|---|---|---|---:|---:|---|---:|---|
|  |  |  |  |  |  | Time exit / SL / TP / Manual |  |  |

確認ポイント：

```text
Time exit success が出たか
予定Exit時刻に近いか
SL/TP決済の場合、注文条件どおりか
手動決済した場合は理由を残す
```

---

# 6. Event Filter記録フォーマット

イベント停止が発生したら記録する。

| Date | Strategy | Symbol | Event | Scheduled Entry JST | Log | Expected Stop | Result | Notes |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  | EVENT REJECT | Yes / No | OK / NG |  |

確認ポイント：

```text
EVENT REJECT が出たか
対象イベント名が妥当か
本当に停止対象ロジックか
Entryしなかったか
ログが連続出力されていないか
```

---

# 7. ATR Filter記録フォーマット

ATRで停止した場合に記録する。

| Date | Strategy | Symbol | Scheduled Entry JST | ATR Result | ATR Pips | P70 Pips | Result | Notes |
|---|---|---|---:|---|---:|---:|---|---|
|  |  |  |  | ATR REJECT / ATR PASS |  |  | OK / NG |  |

確認ポイント：

```text
ATR REJECTでEntry停止したか
ATR PASSならEntryへ進んだか
ATRログをONにしている場合、ATR_Pips / P70_Pipsが自然か
```

通常運用では `InpPrintAtrFilterLogs = false` 推奨。  
ATR停止の理由を確認したい場合のみ、一時的にtrueへ変更する。

---

# 8. 想定外Entry記録

予定外のEntryがあった場合に記録する。

| Date | Time JST | Strategy | Symbol | Direction | Lot | Situation | Action | Notes |
|---|---:|---|---|---|---:|---|---|---|
|  |  |  |  |  |  |  | EmergencyStop / Manual Close / Continue |  |

確認すること：

```text
MockJSTがtrueになっていないか
TestTimesがtrueになっていないか
同じEAを複数チャートに入れていないか
Global Variableが残っていないか
Strategy Enable設定に誤りがないか
```

---

# 9. 想定外停止記録

Entry予定だったのにEntryしなかった場合に記録する。

| Date | Strategy | Symbol | Scheduled Entry JST | Expected Entry | Actual | Log | Suspected Cause | Notes |
|---|---|---|---:|---|---|---|---|---|
|  |  |  |  | Yes | No |  | Event / ATR / DateRule / MarketClosed / Unknown |  |

確認すること：

```text
EVENT REJECTが出ていないか
ATR REJECTではないか
Date rule rejectではないか
market closedではないか
EmergencyStop=trueになっていないか
Auto TradingがOFFではないか
通信切れではないか
```

---

# 10. 週次サマリー

週末に記録する。

| Week Start | Week End | Entries | Time Exits | SL | TP | Manual Close | Event Reject | ATR Reject | Errors | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
|  |  |  |  |  |  |  |  |  | none /あり |  |

週次確認ポイント：

```text
予定通りのEntry数か
不要なEntryがないか
停止ログが妥当か
MT5停止・通信切れがなかったか
Windows Update再起動がなかったか
ログが見やすいか
```

---

# 11. GitHub記録ルール

フォワードテスト中の記録は、以下のどちらかで管理する。

## 案A：週次MD

```text
results/forward_test/week_YYYYMMDD.md
```

例：

```text
results/forward_test/week_20260622.md
```

## 案B：CSV

```text
results/forward_test/forward_test_log.csv
```

初期はMDで十分。

---

# 12. 週次MDテンプレート

```markdown
# Forward Test Week YYYY-MM-DD

## 基本情報

- EA:
- Account:
- Lot Mode:
- Fixed Lot:
- ATR Filter:
- Event Filter:
- EmergencyStop:

## Daily Check

| Date | MT5 | AutoTrading | Connection | EA | Error | Notes |
|---|---|---|---|---|---|---|
|  | OK | OK | OK | OK | none |  |

## Entries

| Date | Strategy | Symbol | Direction | Entry JST | Lot | SL | TP | Result | Notes |
|---|---|---|---|---:|---:|---:|---:|---|---|
|  |  |  |  |  |  |  |  | OK |  |

## Exits

| Date | Strategy | Symbol | Exit JST | Exit Type | P/L | Notes |
|---|---|---|---:|---|---:|---|
|  |  |  |  | Time exit |  |  |

## Filters

| Date | Strategy | Symbol | Filter | Reason | Result | Notes |
|---|---|---|---|---|---|---|
|  |  |  | Event / ATR / DateRule |  | OK |  |

## Issues

| Date | Issue | Cause | Action | Status |
|---|---|---|---|---|
|  |  |  |  | Open / Closed |

## Weekly Summary

- Entries:
- Time exits:
- SL:
- TP:
- Manual close:
- Event Reject:
- ATR Reject:
- Error:
- Notes:
```

---

# 13. フォワード中の判断基準

## すぐ止めるべきケース

```text
想定外の大量Entry
Lotが想定より大きい
SLが入っていない
同じロジックが重複Entryしている
通信エラーやtrade disabledが続く
```

対応：

```text
InpEmergencyStop = true
必要なら手動決済
ログを保存
原因確認
```

## すぐ止めなくてもよいケース

```text
ATR REJECTでEntryしない
EVENT REJECTでEntryしない
Date rule rejectでEntryしない
スプレッド拡大で一時的に約定しない
```

ただし、記録は残す。

---

# 14. 次にやること

```text
Step 9.4：デモ口座でフォワードテスト開始
```

開始前に、以下を再確認する。

```text
docs/03_forward_test_input_defaults.md
docs/04_mt5_forward_test_setup_checklist.md
docs/05_forward_test_record_format.md
```
