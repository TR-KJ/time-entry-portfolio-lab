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
