# 03_forward_test_input_defaults.md

# デモ口座フォワードテスト用 input 初期値整理

## 対象EA

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

## 目的

このドキュメントは、28ロジック統合EAをデモ口座でフォワードテスト開始する際の、推奨input初期値を整理するためのもの。

目的：

```text
運用開始時の設定ミスを防ぐ
固定ロットで安全にフォワード確認する
イベント停止・ATRフィルタ・時間エントリーの実挙動を確認する
ログを見やすく保つ
```

---

# 1. フォワードテスト開始時の基本方針

初回フォワードテストでは、週次複利ロットではなく、固定0.01lotで開始する。

理由：

```text
まずはEAが予定どおりEntryするか確認する
停止すべき日に止まるか確認する
イベントフィルタ・ATRフィルタの実挙動を確認する
ロット変動要因を一旦なくす
```

初回方針：

```text
デモ口座
固定0.01lot
全28ロジックON
ATR P70フィルタON
Event Filter ON
EmergencyStop OFF
TestMode OFF
Mock日時 OFF
```

---

# 2. 稼働モード設定

## 緊急停止

```text
InpEmergencyStop = false
```

意味：

```text
false → 通常稼働
true  → 新規Entryを全停止
```

注意：

```text
EmergencyStop = true でも、既存ポジションのTime exitは維持される
```

---

# 3. ロット設定

## 初回フォワード推奨

```text
InpLotMode = 0
InpFixedLot = 0.01
```

意味：

```text
InpLotMode = 0 → 固定ロット
InpFixedLot = 0.01 → 0.01lot固定
```

初回はこの設定で開始する。

---

## 週次複利モードは後で使用

週次複利を使う場合：

```text
InpLotMode = 1
InpRiskPercentPerTrade = 0.50
InpMaxAutoLot = 1.00
InpWeeklyBaseUseEquity = true
InpAllowMinLotWhenBelowMinimum = true
```

ただし、初回フォワードでは使わない。

---

# 4. ATR P70フィルタ設定

```text
InpUseGlobalAtrP70Filter = true
InpAtrTimeframe = PERIOD_H1
InpAtrPeriod = 14
InpAtrP70LookbackBars = 500
InpAtrPercentile = 70.0
InpAtrUseClosedBar = true
```

意味：

```text
H1確定足のATRを使用
過去500本のATR P70以上の場合のみEntry許可
```

ログ：

```text
InpPrintAtrFilterLogs = false
```

初回フォワードではログ量を抑えるため、通常はfalse推奨。

---

# 5. イベントフィルタ設定

```text
InpUseEventFilter = true
InpPrintEventFilterLogs = true
InpSuppressEventLogsOncePerDay = true
```

意味：

```text
重要イベント日はEntry停止
EVENT REJECTログは同条件で1回のみ表示
```

イベントフィルタはONでフォワードテストする。

---

# 6. Test / Mock設定

フォワードテスト時は、テストモード系を必ずOFFにする。

```text
InpTestMode = false
InpUseTestTimes = false
InpUseMockJstDateTime = false
```

重要：

```text
InpUseMockJstDateTime = true のままにしない
InpUseTestTimes = true のままにしない
```

---

# 7. ログ設定

初回フォワード推奨：

```text
InpPrintDebug = true
InpPrintSkipLogs = false
InpPrintRuleRejectLogs = true
InpSuppressRuleRejectLogsOncePerDay = true
InpSuppressSkipLogsOncePerDay = true
InpPrintLotLogs = true
```

理由：

```text
Entry / Exit / Lot / Event停止は確認したい
Skip系ログは多すぎるため抑制する
Rule Rejectは停止理由確認のためON
```

---

# 8. Enable設定

初回フォワードでは、原則として28ロジック全ON。

```text
InpEnable_1_EJ_Log1 = true
InpEnable_2_EJ_NightBlitz_20 = true
InpEnable_3_EJ_NightBlitz_21 = true
InpEnable_4_GJ_Port_Log1 = true
InpEnable_5_GJ_Log2 = true
InpEnable_6_GJ_Old_Mon = true
InpEnable_7_GJ_Mon_Blitz = true
InpEnable_8_AJ_Core1 = true
InpEnable_9_AJ_Core2 = true
InpEnable_10_AJ_SatA = true
InpEnable_11_AJ_SatB = true
InpEnable_12_UJ_Short_Core = true
InpEnable_13_UJ_Fix_MidWeek = true
InpEnable_14_UJ_Sat_3rd = true
InpEnable_15_UJ_Sat_Aug = true
InpEnable_16_UJ_T10A = true
InpEnable_17_EA_1B = true
InpEnable_18_EA_2 = true
InpEnable_19_EA_3 = true
InpEnable_20_EA_1A = true
InpEnable_21_GA_B3 = true
InpEnable_22_GA_C2 = true
InpEnable_23_GA_F2 = true
InpEnable_24_GA_D1 = true
InpEnable_25_AU_China_Demand = true
InpEnable_26_AJ_China_Demand = true
InpEnable_27_EA_China_Demand = true
InpEnable_28_GA_China_Demand = true
```

---

# 9. 推奨input初期値まとめ

```text
InpEmergencyStop = false

InpLotMode = 0
InpFixedLot = 0.01
InpRiskPercentPerTrade = 0.50
InpMaxAutoLot = 1.00
InpWeeklyBaseUseEquity = true
InpAllowMinLotWhenBelowMinimum = true

InpUseGlobalAtrP70Filter = true
InpAtrTimeframe = PERIOD_H1
InpAtrPeriod = 14
InpAtrP70LookbackBars = 500
InpAtrPercentile = 70.0
InpAtrUseClosedBar = true
InpPrintAtrFilterLogs = false

InpUseEventFilter = true
InpPrintEventFilterLogs = true
InpSuppressEventLogsOncePerDay = true

InpTestMode = false
InpUseTestTimes = false
InpUseMockJstDateTime = false

InpPrintDebug = true
InpPrintSkipLogs = false
InpPrintRuleRejectLogs = true
InpSuppressRuleRejectLogsOncePerDay = true
InpSuppressSkipLogsOncePerDay = true
InpPrintLotLogs = true
```

---

# 10. 稼働前チェックリスト

EAをチャートに入れる前に確認する。

```text
OANDAデモ口座にログインしている
自動売買ボタンがON
EAの自動売買許可がON
対象7通貨ペアが気配値表示にある
VPSまたはPCがスリープしない
TestMode=false
UseMockJstDateTime=false
UseTestTimes=false
EmergencyStop=false
LotMode=0
FixedLot=0.01
EventFilter=true
ATR Filter=true
```

対象通貨ペア：

```text
USDJPY
EURJPY
GBPJPY
AUDJPY
AUDUSD
EURAUD
GBPAUD
```

---

# 11. フォワードテスト中に見るもの

毎日確認するもの：

```text
Entry予定ロジックが予定どおり動いたか
停止すべき日にEVENT REJECTが出たか
ATR REJECTで止まった日があるか
SL / TPが正しく入っているか
Time exit success が出たか
不要な大量ログが出ていないか
```

---

# 12. 注意事項

初回フォワードは、成績を見るより先に、EAの実運用挙動を見る。

確認優先順位：

```text
1. エントリー時刻
2. 方向
3. Lot
4. SL / TP
5. Time exit
6. Event Filter
7. ATR Filter
8. ログの見やすさ
```

利益・損失評価は、最低でも数週間分の稼働ログを見てから行う。

---

# 13. 次にやること

次工程：

```text
Step 9.2：MT5設置手順・稼働前チェックリスト作成
Step 9.3：フォワードテスト記録フォーマット作成
```
