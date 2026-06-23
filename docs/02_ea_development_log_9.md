## 2026-06-17：EA Step 7.2 週次複利ロット計算EA 正式合格ログ

### 対象EA

```text
time_entry_step7_config_managed_28strategies_weekly_compound_lot.mq5
```

---

## 目的

Step 7.2では、Step 6.3で正式合格した28ロジックEAに、週次複利ロット計算機能を追加した。

追加したロットモード：

```text
InpLotMode = 0
→ 固定ロットモード

InpLotMode = 1
→ 週次複利ロットモード
```

---

## 追加機能

```text
固定ロットモード
週次複利ロット計算
週次基準残高Global Variable保存
RiskPercentベースのロット計算
SL pipsベースの損失額計算
最大ロット制限
最小ロット対応
ロット計算ログ
```

---

## テスト結果

確認済み：

```text
Test 1：コンパイル OK
Test 2：固定ロットモード 0.01 lot Entry OK
Test 3：週次複利ロット LOT CALCログ OK
Test 4：週次基準残高Global Variable作成 OK
Test 5：UJ Short Core GOTO / NORMAL のSL別Lot差 OK
Test 6：最大ロット制限 OK
```

---

## 判定

Step 7.2は正式合格。

```text
週次複利ロット計算 OK
固定ロットモード OK
計算Lotの発注反映 OK
週次基準残高保存 OK
最大ロット制限 OK
売買挙動に問題なし
```

---

## 現在の最新版EA

```text
time_entry_step7_config_managed_28strategies_weekly_compound_lot.mq5
```

---

## 現在の到達点

```text
28ロジック統合
ATR P70フィルタ
イベント停止
年末年始・個別停止
各種ログ抑制
週次複利ロット計算
```

---

## 次にやること

次工程候補：

```text
Step 8：本番前安全装置
```

候補内容：

```text
最大同時ポジション数
日次損失制限
週次損失制限
最大ロット上限の最終確認
ロットモード本番設定確認
緊急停止input
```

## 2026-06-17：EA Step 8.1 本番前最小安全装置 仕様整理

### 対象EA

現在の最新版EA：

```text
time_entry_step7_config_managed_28strategies_weekly_compound_lot.mq5
```

Step 8で作成予定のEA：

```text
time_entry_step8_config_managed_28strategies_forward_test_ready.mq5
```

---

## 目的

Step 8では、デモ口座でフォワードテストを開始する前の最小安全装置を追加する。

今回実装するのは以下のみ。

```text
ロットモード本番設定確認
緊急停止input
```

以下は今回は実装しない。

```text
最大同時ポジション数
日次損失制限
週次損失制限
通貨別リスク上限
ポートフォリオ全体リスク上限
```

理由：

```text
まずEAを完成形に近づけ、デモ口座でフォワードテストを開始する
フォワードテスト中に、イベントフィルター・停止条件・実運用ログを精査する
安全装置を増やしすぎて、停止理由が複雑になることを避ける
```

---

# Step 8で維持するもの

以下はStep 7.2から変更しない。

```text
28ロジック構成
Entry時刻
Exit時刻
Direction
SL
TP
Magic Number
ATR P70フィルタ
イベント停止
年末年始・個別停止
ログ抑制
週次複利ロット計算
固定ロットモード
時間決済
日またぎExit
同日重複エントリー防止
```

---

# 追加するinput

## 1. 緊急停止input

```text
InpEmergencyStop = false
```

挙動：

```text
false → 通常稼働
true  → 新規Entryを全停止
```

注意：

```text
InpEmergencyStop = true でも、既存ポジションの時間決済は維持する
```

理由：

```text
緊急停止中でも、保有中ポジションをEAの時間決済で閉じられるようにする
新規Entryだけを止める
```

---

## 2. ロットモード確認ログ

既存input：

```text
InpLotMode = 0 / 1
InpFixedLot
InpRiskPercentPerTrade
InpMaxAutoLot
InpAllowMinLotWhenBelowMinimum
```

Step 8では、OnInit時に現在のロット設定を明示ログ出力する。

ログ例：

```text
LOT MODE CHECK. Mode=Fixed Lot, FixedLot=0.01
```

または、

```text
LOT MODE CHECK. Mode=Weekly Compound, RiskPercent=0.50, MaxAutoLot=1.00, WeeklyBaseUseEquity=true
```

---

# ロットモード本番設定確認

Step 8では、ロットモード設定をEA起動時に必ずログで確認できるようにする。

目的：

```text
デモ口座フォワードテスト開始時に、固定ロットなのか週次複利なのかを誤認しない
RiskPercentやMaxAutoLotの設定ミスを見つけやすくする
```

---

# 危険設定時の警告ログ

以下の場合は警告ログを出す。

## 1. 週次複利モードでRiskPercentが高すぎる

暫定基準：

```text
InpRiskPercentPerTrade > 2.0
```

ログ：

```text
WARNING. RiskPercentPerTrade is high.
```

## 2. MaxAutoLotが大きすぎる

暫定基準：

```text
InpMaxAutoLot > 1.0
```

ログ：

```text
WARNING. MaxAutoLot is high.
```

## 3. 緊急停止ONで起動している

```text
InpEmergencyStop = true
```

ログ：

```text
EMERGENCY STOP ACTIVE. New entries are blocked.
```

---

# 緊急停止の組み込み位置

新規Entry判定の最初の方に入れる。

処理順：

```text
TryEntry()
↓
cfg.enabled確認
↓
InpEmergencyStop確認
↓
Symbol確認
↓
IsEntryTime()
↓
PassEntryFilters()
↓
AlreadyEnteredToday()
↓
HasOpenPosition()
↓
SendBuyOrder / SendSellOrder
```

緊急停止ONの場合：

```text
TryEntry() でreturn
新規Entryしない
```

ただし、Exit処理は止めない。

```text
TryExit() は通常通り実行
```

---

# Step 8でまだ実装しない安全装置

```text
最大同時ポジション数
日次損失制限
週次損失制限
通貨別リスク上限
ポートフォリオ全体リスク上限
```

これらは、デモ口座フォワードテスト中の挙動を見ながら、必要に応じて後続Stepで追加する。

---

# Step 8.2 作成予定EA

```text
time_entry_step8_config_managed_28strategies_forward_test_ready.mq5
```

ベースEA：

```text
time_entry_step7_config_managed_28strategies_weekly_compound_lot.mq5
```

---

# Step 8.2 テスト方針

## Test 1：コンパイル

```text
0 errors
```

## Test 2：緊急停止OFFで通常Entry確認

設定：

```text
InpEmergencyStop = false
```

期待：

```text
Entry条件を満たせば通常通りEntryする
```

## Test 3：緊急停止ONでEntry停止確認

設定：

```text
InpEmergencyStop = true
```

期待：

```text
Entry条件を満たしても新規Entryしない
EMERGENCY STOP ACTIVEログが出る
```

## Test 4：緊急停止ONでもExitは動く確認

既存ポジションを持った状態で、Exit時刻に到達させる。

期待：

```text
Time exit success
```

## Test 5：ロットモード確認ログ

固定ロットモード：

```text
InpLotMode = 0
```

期待：

```text
LOT MODE CHECK. Mode=Fixed Lot
```

週次複利モード：

```text
InpLotMode = 1
```

期待：

```text
LOT MODE CHECK. Mode=Weekly Compound
```

---

# Step 8.1 判定

Step 8.1は仕様整理として完了。

次に行うこと：

```text
Step 8.2：本番前最小安全装置EAの作成
```
