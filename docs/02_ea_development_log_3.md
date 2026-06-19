## 2026-06-15：EA Step 2F.1 13ロジック統合仕様整理

### 目的

Step 2Fでは、これまで個別に確認してきた以下を1つの設定管理型EAへ統合する。

```text
Step 2C：既存8ロジック
Step 2E：UJ 5ロジック
```

合計：

```text
13ロジック
```

Step 2F.1では、コード作成前に、13ロジック統合EAの仕様を整理する。

---

# Step 2F 統合対象

## 既存8ロジック

```text
22_GA_C_2
5_GJ_Port_Log2
21_GA_B_3
23_GA_F_2
24_GA_D_1
17_EA_1B_Wed_Short
18_EA_2_MonWed_Short
19_EA_3_WedThu_Long
```

## UJ 5ロジック

```text
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

---

# 13ロジック一覧

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic |
|---:|---|---|---|---|---|---:|---:|---:|
| 17 | 17_EA_1B_Wed_Short | EURAUD | Short | 水曜 09:59 JST | 当日 20:58 JST | 70 | 175 | 17001 |
| 18 | 18_EA_2_MonWed_Short | EURAUD | Short | 月・火・水 09:59 JST | 翌日 05:26 JST | 90 | 180 | 18002 |
| 19 | 19_EA_3_WedThu_Long | EURAUD | Long | 水・木 20:56 JST | 翌日 10:00 JST | 90 | なし | 19003 |
| 21 | 21_GA_B_3 | GBPAUD | Long | 月曜 21:02 JST | 翌日 10:00 JST | 220 | 100 | 21003 |
| 22 | 22_GA_C_2 | GBPAUD | Long | 木曜 16:56 JST | 金曜 01:15 JST | 70 | 80 | 22002 |
| 23 | 23_GA_F_2 | GBPAUD | Short | 金曜 19:42 JST | 当日 22:45 JST | 90 | 200 | 23002 |
| 24 | 24_GA_D_1 | GBPAUD | Long | 金曜 22:44 JST | 翌日 03:08 JST | 90 | 200 | 24001 |
| 5 | 5_GJ_Port_Log2 | GBPJPY | Short | 火・木・金 09:55 JST | 当日 23:55 JST | 90 | なし | 50002 |
| 12 | 12_UJ_Short_Core | USDJPY | Short | 条件分岐 | 14:56 JST | 条件分岐 | 条件分岐 | 12001 |
| 13 | 13_UJ_Fix_MidWeek | USDJPY | Long | 18:04 JST | 22:03 JST | 95 | 95 | 13001 |
| 14 | 14_UJ_Sat_3rd | USDJPY | Short | 20:01 JST | 翌日 03:08 JST | 45 | 70 | 14001 |
| 15 | 15_UJ_Sat_Aug | USDJPY | Short | 19:00 JST | 当日 23:30 JST | 20 | 35 | 15001 |
| 16 | 16_UJ_T10A | USDJPY | Long | 02:58 JST | 当日 09:50 JST | 45 | 110 | 16001 |

---

# 対象通貨ペア

Step 2Fでは、以下4ペアを扱う。

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
```

MT5の気配値表示には、最低限この4銘柄を表示しておく。

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
```

---

# EAファイル名

Step 2F.2で作成するEAファイル名は以下とする。

```text
time_entry_step2f2_config_managed_13strategies.mq5
```

---

# Step 2Fの目的

Step 2Fでは、以下を確認する。

```text
設定管理型EAで13ロジックを管理できるか
EURAUD / GBPAUD / GBPJPY / USDJPYを同時に扱えるか
Long / Shortが混在しても動作するか
TPあり / TPなしが混在しても動作するか
当日決済 / 翌日決済 / 曜日指定決済が混在しても動作するか
通常曜日ロジックとUJ特殊日付ロジックが共存できるか
日またぎExit修正が統合EAでも機能するか
Magic Numberを13ロジックで分けて管理できるか
Global Variableによる同日重複エントリー防止がロジック別に機能するか
```

---

# 既存8ロジック仕様

## 17_EA_1B_Wed_Short

| Field | Value |
|---|---|
| Pair | EURAUD |
| Direction | Short |
| Entry | 水曜 09:59 JST |
| Exit | 当日 20:58 JST |
| SL | 70 pips |
| TP | 175 pips |
| Magic | 17001 |
| Special Rule | RULE_NONE |

---

## 18_EA_2_MonWed_Short

| Field | Value |
|---|---|
| Pair | EURAUD |
| Direction | Short |
| Entry | 月・火・水 09:59 JST |
| Exit | 翌日 05:26 JST |
| SL | 90 pips |
| TP | 180 pips |
| Magic | 18002 |
| Special Rule | RULE_NONE |

---

## 19_EA_3_WedThu_Long

| Field | Value |
|---|---|
| Pair | EURAUD |
| Direction | Long |
| Entry | 水・木 20:56 JST |
| Exit | 翌日 10:00 JST |
| SL | 90 pips |
| TP | なし |
| Magic | 19003 |
| Special Rule | RULE_NONE |

---

## 21_GA_B_3

| Field | Value |
|---|---|
| Pair | GBPAUD |
| Direction | Long |
| Entry | 月曜 21:02 JST |
| Exit | 翌日 10:00 JST |
| SL | 220 pips |
| TP | 100 pips |
| Magic | 21003 |
| Special Rule | RULE_NONE |

---

## 22_GA_C_2

| Field | Value |
|---|---|
| Pair | GBPAUD |
| Direction | Long |
| Entry | 木曜 16:56 JST |
| Exit | 金曜 01:15 JST |
| SL | 70 pips |
| TP | 80 pips |
| Magic | 22002 |
| Special Rule | RULE_NONE |

---

## 23_GA_F_2

| Field | Value |
|---|---|
| Pair | GBPAUD |
| Direction | Short |
| Entry | 金曜 19:42 JST |
| Exit | 当日 22:45 JST |
| SL | 90 pips |
| TP | 200 pips |
| Magic | 23002 |
| Special Rule | RULE_NONE |

---

## 24_GA_D_1

| Field | Value |
|---|---|
| Pair | GBPAUD |
| Direction | Long |
| Entry | 金曜 22:44 JST |
| Exit | 翌日 03:08 JST |
| SL | 90 pips |
| TP | 200 pips |
| Magic | 24001 |
| Special Rule | RULE_NONE |

---

## 5_GJ_Port_Log2

| Field | Value |
|---|---|
| Pair | GBPJPY |
| Direction | Short |
| Entry | 火・木・金 09:55 JST |
| Exit | 当日 23:55 JST |
| SL | 90 pips |
| TP | なし |
| Magic | 50002 |
| Special Rule | RULE_NONE |

---

# UJ 5ロジック仕様

## 12_UJ_Short_Core

| Field | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Entry | 条件分岐 |
| Exit | 14:56 JST |
| SL | 条件分岐 |
| TP | 条件分岐 |
| Magic | 12001 |
| Special Rule | RULE_UJ_SHORT_CORE |

### 稼働日条件

```text
毎月20日〜月末まで
```

ただし、以下は停止。

```text
21日
22日
水曜日
8月全期間
カレンダー月末
```

### ゴトー日判定

```text
20日
25日
30日
```

重要仕様：

```text
前倒しゴトー日は未実装
```

### GOTOモード

| Item | Value |
|---|---|
| Entry | 09:55 JST |
| Exit | 14:56 JST |
| SL | 20 pips |
| TP | 50 pips |

### NORMALモード

| Item | Value |
|---|---|
| Entry | 08:04 JST |
| Exit | 14:56 JST |
| SL | 50 pips |
| TP | なし |

---

## 13_UJ_Fix_MidWeek

| Field | Value |
|---|---|
| Pair | USDJPY |
| Direction | Long |
| Entry | 18:04 JST |
| Exit | 22:03 JST |
| SL | 95 pips |
| TP | 95 pips |
| Magic | 13001 |
| Special Rule | RULE_UJ_FIX_MIDWEEK |

稼働条件：

```text
毎月25日以降
水曜日・木曜日のみ
```

EA条件：

```text
day >= 25
weekday == Wednesday or Thursday
```

---

## 14_UJ_Sat_3rd

| Field | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Entry | 20:01 JST |
| Exit | 翌日 03:08 JST |
| SL | 45 pips |
| TP | 70 pips |
| Magic | 14001 |
| Special Rule | RULE_UJ_SAT_3RD |

稼働条件：

```text
毎月3日のみ
```

EA条件：

```text
day == 3
```

注意：

```text
Entry 20:01 / Exit 翌日03:08 の日またぎ決済。
Step 2E.2 FIX1で、Entry直後に即Time exitしないよう修正済み。
Step 2Fでもこの日またぎExit修正を必ず反映する。
```

---

## 15_UJ_Sat_Aug

| Field | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Entry | 19:00 JST |
| Exit | 23:30 JST |
| SL | 20 pips |
| TP | 35 pips |
| Magic | 15001 |
| Special Rule | RULE_UJ_SAT_AUG |

稼働条件：

```text
8月1日〜10日のみ
```

EA条件：

```text
month == 8
day <= 10
```

---

## 16_UJ_T10A

| Field | Value |
|---|---|
| Pair | USDJPY |
| Direction | Long |
| Entry | 02:58 JST |
| Exit | 09:50 JST |
| SL | 45 pips |
| TP | 110 pips |
| Magic | 16001 |
| Special Rule | RULE_UJ_T10A |

稼働条件：

```text
毎月10日
ただし水曜日は停止
```

EA条件：

```text
day == 10
weekday != Wednesday
```

---

# Special Rule一覧

Step 2Fでは以下のルールを使う。

```text
RULE_NONE
RULE_UJ_SHORT_CORE
RULE_UJ_FIX_MIDWEEK
RULE_UJ_SAT_3RD
RULE_UJ_SAT_AUG
RULE_UJ_T10A
```

対応：

```text
RULE_NONE             → 通常曜日ロジック
RULE_UJ_SHORT_CORE    → 12_UJ_Short_Core
RULE_UJ_FIX_MIDWEEK  → 13_UJ_Fix_MidWeek
RULE_UJ_SAT_3RD      → 14_UJ_Sat_3rd
RULE_UJ_SAT_AUG      → 15_UJ_Sat_Aug
RULE_UJ_T10A         → 16_UJ_T10A
```

---

# Exit判定

Step 2Fでは、Step 2E.2 FIX1で修正した日またぎExit判定を採用する。

## 通常Exit

```text
Entry時刻よりExit時刻が後の場合：
同日Exitとして扱う
```

例：

```text
Entry 19:00
Exit 23:30
```

## 日またぎExit

```text
Entry時刻よりExit時刻が前の場合：
翌日Exitとして扱う
```

例：

```text
Entry 20:01
Exit 翌日03:08
Entry 22:44
Exit 翌日03:08
Entry 09:59
Exit 翌日05:26
Entry 20:56
Exit 翌日10:00
```

重要：

```text
日またぎロジックでは、Entry日の夜に即Time exitしないこと。
```

---

# ログ方針

Step 2Fでも、ログが多くなりすぎないよう以下を採用する。

```text
InpPrintDebug = true
InpPrintSkipLogs = false
InpPrintRuleRejectLogs = true
```

## Skipログ

通常は非表示。

```text
Skip entry: already entered today
Skip entry: position already exists
```

必要なときのみ、以下で表示する。

```text
InpPrintSkipLogs = true
```

## 日付条件Rejectログ

テスト中は表示。

```text
InpPrintRuleRejectLogs = true
```

本番寄りテストでは、必要に応じて `false` にする。

---

# テスト方針

Step 2F.2でコード作成後、以下の順でテストする。

## Test 1：既存8ロジックだけON

目的：

```text
Step 2C相当の動作が維持されているか確認
```

設定：

```text
既存8ロジック = true
UJ5ロジック = false
```

テスト方法：

```text
InpUseTestTimes = true
任意のEntry/Exit時刻で一括テスト
```

期待：

```text
既存8ロジックがEntryする
時間決済する
```

---

## Test 2：UJ5ロジックだけON

目的：

```text
Step 2E相当の動作が維持されているか確認
```

設定：

```text
既存8ロジック = false
UJ5ロジック = true
```

テスト方法：

```text
InpUseMockJstDateTime = true
各UJロジックのMock日付テスト
```

期待：

```text
UJ5ロジックがStep 2Eと同じ挙動をする
14_UJ_Sat_3rdが即Time exitしない
```

---

## Test 3：13ロジック同時ON

目的：

```text
13ロジックを同じEA内で管理できるか確認
```

設定：

```text
既存8ロジック = true
UJ5ロジック = true
```

注意：

```text
全ロジックを同じMock時刻・同じTestTimeで同時Entryさせる必要はない。
まずはEA起動、各ロジック認識、エラーなしを確認する。
その後、代表ロジックを個別ONにしてEntry確認する。
```

---

# Step 2F.2で作るEA

ファイル名：

```text
time_entry_step2f2_config_managed_13strategies.mq5
```

方針：

```text
Step 2Cの8ロジック構造
+
Step 2E.2 FIX1のUJ5ロジック構造
+
日またぎExit修正
+
Skipログ制御
```

---

# Step 2Fではまだ実装しないもの

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

これらは後続Stepで追加する。

## 2026-06-15：EA Step 2F 13ロジック統合EAテスト完了

### 対象EA

```text
time_entry_step2f2_config_managed_13strategies.mq5
```

### 対象ロジック

Step 2Fでは、既存8ロジックとUJ5ロジックを統合し、合計13ロジックの設定管理型EAを作成・テストした。

```text
既存8ロジック
17_EA_1B_Wed_Short
18_EA_2_MonWed_Short
19_EA_3_WedThu_Long
21_GA_B_3
22_GA_C_2
23_GA_F_2
24_GA_D_1
5_GJ_Port_Log2

UJ5ロジック
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

---

## Step 2F の目的

以下を1つのEA内で共存させることを確認した。

```text
EURAUD / GBPAUD / GBPJPY / USDJPY の複数通貨ペア管理
Long / Short の混在
TPあり / TPなし の混在
通常曜日ロジックとUJ特殊日付ロジックの共存
日またぎExit対応
Magic Number別管理
Global Variableによる同日重複エントリー防止
```

---

## 実装内容

Step 2Cの既存8ロジック構造に、Step 2E.2 FIX1のUJ5ロジックを統合した。

主な反映内容：

```text
StrategyConfig strategies[13]
RULE_NONE
RULE_UJ_SHORT_CORE
RULE_UJ_FIX_MIDWEEK
RULE_UJ_SAT_3RD
RULE_UJ_SAT_AUG
RULE_UJ_T10A
日またぎExit修正
Skipログ制御
Mock JST日時テスト
```

---

## テスト結果

### Test 1：既存8ロジックのみON

設定：

```text
既存8ロジック = true
UJ5ロジック = false
InpUseTestTimes = true
InpUseMockJstDateTime = false
```

結果：

```text
OK
```

確認内容：

```text
既存8ロジックがStep 2C相当で動作
複数通貨ペア管理OK
Entry / Time exit OK
```

---

### Test 2：UJ5ロジックのみON

設定：

```text
既存8ロジック = false
UJ5ロジック = true
InpUseMockJstDateTime = true
InpUseTestTimes = false
```

結果：

```text
OK
```

確認内容：

```text
12_UJ_Short_Core GOTO / NORMAL OK
13_UJ_Fix_MidWeek OK
14_UJ_Sat_3rd OK
15_UJ_Sat_Aug OK
16_UJ_T10A OK
14_UJ_Sat_3rdの日またぎExit修正もOK
```

---

### Test 3：13ロジック全ON

設定：

```text
既存8ロジック = true
UJ5ロジック = true
```

結果：

```text
OK
```

確認内容：

```text
13ロジック全ONでEA起動OK
4通貨ペア認識OK
初期化ログOK
代表エントリーOK
```

補足：

```text
代表エントリー確認時、12_UJ_Short_Coreだけでなく5_GJ_Port_Log2も同時にエントリーした。
これはMock時刻09:55とGJのEntry時刻09:55が一致し、かつ曜日無視設定だったため。
コードミスではなく、テスト設定上の自然な挙動と判断。
```

---

## Step 2F 判定

Step 2Fは合格。

確認済み：

```text
Step 2C：既存8ロジック OK
Step 2E：UJ5ロジック OK
Step 2F：13ロジック統合EA OK
```

---

## 注意点

Step 2Fはまだ検証用EAであり、本番運用には使用しない。

未実装：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

---

## 次にやること

次は Step 2G として、残り15ロジックの仕様整理に進む。

予定：

```text
Step 2G.1：残り15ロジックの仕様整理
Step 2G.2：追加しやすい順にグループ分け
Step 2H：次の5〜8ロジック追加
```

当面は、Global H1 ATR P70・指標停止・週次複利より先に、全ロジックの時間エントリー/時間決済/SLTP/Magic管理を完成させる。

## 2026-06-15：EA Step 2G.1 残り15ロジック仕様整理

### 目的

Step 2Fで13ロジック統合EAが合格したため、次は残り15ロジックの仕様を整理する。

現在EA化済み：

```text
既存8 + UJ5 = 13ロジック
```

残り：

```text
EJ 3ロジック
GJ 3ロジック
AJ 4ロジック
EA 1ロジック
China系 4ロジック

合計15ロジック
```

---

# 残り15ロジック一覧

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic案 |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | 1_EJ_Log1 | EURJPY | Long | 月・水 13:55 | 翌日 04:55 | 70 | 250 | 10001 |
| 2 | 2_EJ_NightBlitz_20 | EURJPY | Long | 月・水 20:56 | 翌日 04:45 | 45 | 70 | 20001 |
| 3 | 3_EJ_NightBlitz_21 | EURJPY | Long | 月・水 21:56 | 翌日 05:27 | 75 | 70 | 30001 |
| 4 | 4_GJ_Port_Log1 | GBPJPY | Long | 火・水 00:00 | 当日 08:55 | 130 | 90 | 40001 |
| 6 | 6_GJ_Old_Mon | GBPJPY | Long | 月 15:45 | 当日 22:50 | 50 | 210 | 60001 |
| 7 | 7_GJ_Mon_Blitz | GBPJPY | Long | 月 18:02 | 当日 23:02 | 130 | 250 | 70001 |
| 8 | 8_AJ_Core1 | AUDJPY | Long | 月 08:01 | 当日 22:46 | 70 | 110 | 80001 |
| 9 | 9_AJ_Core2 | AUDJPY | Short | 木 17:14 | 翌日 01:14 | 30 | 80 | 90001 |
| 10 | 10_AJ_SatA | AUDJPY | Short | 金 10:58 | 当日 13:51 | 50 | 25 | 10002 |
| 11 | 11_AJ_SatB | AUDJPY | Short | 金 18:57 | 翌日 01:43 | 55 | 95 | 11001 |
| 20 | 20_EA_1A_MonTue_Short | EURAUD | Short | 月・火 10:01 | 当日 16:00 | 50 | 125 | 20002 |
| 25 | 25_AU_China_Demand | AUDUSD | Long | 条件日 10:00 | 当日 15:50 | 40 | 40 | 25001 |
| 26 | 26_AJ_China_Demand | AUDJPY | Long | 条件日 10:00 | 当日 15:50 | 45 | 80 | 26001 |
| 27 | 27_EA_China_Demand | EURAUD | Short | 条件日 10:00 | 当日 15:50 | 60 | 60 | 27001 |
| 28 | 28_GA_China_Demand | GBPAUD | Short | 条件日 10:00 | 当日 16:10 | 75 | 70 | 28001 |

---

# 通貨ペア

残り15ロジックで追加・使用する通貨ペア：

```text
EURJPY
GBPJPY
AUDJPY
EURAUD
AUDUSD
GBPAUD
```

Step 2Fまでに使用済みの通貨ペア：

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
```

新規で必要になる通貨ペア：

```text
EURJPY
AUDJPY
AUDUSD
```

---

# 通常曜日系ロジック

以下は、基本的に曜日＋時刻で管理できる。

```text
1_EJ_Log1
2_EJ_NightBlitz_20
3_EJ_NightBlitz_21
4_GJ_Port_Log1
6_GJ_Old_Mon
7_GJ_Mon_Blitz
8_AJ_Core1
10_AJ_SatA
11_AJ_SatB
20_EA_1A_MonTue_Short
```

ただし、指標停止・月停止・日付停止は後続Stepで実装する。

---

# 要注意ロジック

## 9_AJ_Core2

基本仕様：

```text
Pair：AUDJPY
Direction：Short
Entry：木曜 17:14 JST
Exit：翌日 01:14 JST
SL：30
TP：80
```

バックテスト上の追加停止条件：

```text
6月停止
9月停止
1日停止
20日停止
26日以降停止
```

Step 2G時点では、まず曜日・時刻・SLTPのみ整理。  
追加日付停止は後続で実装候補。

---

# China系ロジック

China系は曜日だけでなく、日付範囲条件を持つ。

## 25_AU_China_Demand

```text
Pair：AUDUSD
Direction：Long
Entry：10:00 JST
Exit：15:50 JST
SL：40
TP：40
```

稼働条件：

```text
平日
かつ
9日〜15日 または 25日〜月末
```

---

## 26_AJ_China_Demand

```text
Pair：AUDJPY
Direction：Long
Entry：10:00 JST
Exit：15:50 JST
SL：45
TP：80
```

稼働条件：

```text
平日
かつ
9日〜15日
```

---

## 27_EA_China_Demand

```text
Pair：EURAUD
Direction：Short
Entry：10:00 JST
Exit：15:50 JST
SL：60
TP：60
```

稼働条件：

```text
平日
かつ
9日〜15日
```

---

## 28_GA_China_Demand

```text
Pair：GBPAUD
Direction：Short
Entry：10:00 JST
Exit：16:10 JST
SL：75
TP：70
```

稼働条件：

```text
平日
かつ
9日〜15日
```

---

# Step 2G.2 方針

次は、残り15ロジックを追加しやすい順にグループ分けする。

おすすめ順：

```text
Step 2H：EJ/GJ/AJの通常曜日系 10ロジック追加
Step 2I：China系 4ロジック追加
Step 2J：9_AJ_Core2など追加日付停止の精密化
```

または安全重視なら：

```text
Step 2H：EJ/GJの6ロジック追加
Step 2I：AJの4ロジック追加
Step 2J：China系4ロジック追加
Step 2K：20_EA_1A追加・全28統合
```

---

# Step 2G時点ではまだ実装しないもの

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック本番版
```

まずは全ロジックの以下を完成させる。

```text
時間エントリー
時間決済
SL/TP
Magic Number
通貨ペア管理
同日重複エントリー防止
```
