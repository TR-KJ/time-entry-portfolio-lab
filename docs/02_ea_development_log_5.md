## 2026-06-16：EA Step 3.1 28ロジック統合EA 整理版仕様整理

### 目的

Step 2J.2で、28ロジック統合EAまで到達した。

ただし、現時点のEAは開発・テストを積み上げた検証版であり、今後 `Global H1 ATR P70`、指標停止、週次複利ロット管理を追加する前に、一度コード構造を整理する。

Step 3では、28ロジック統合EAを整理版として作り直し、今後の拡張に耐えやすい土台を作る。

---

# 現在の状態

対象EA：

```text
time_entry_step2j2_config_managed_28strategies.mq5
```

状態：

```text
28ロジック統合済み
コンパイルOK
9_AJ_Core2 停止条件OK
28ロジック全ON起動確認OK
China系4本のentry successは月曜確認予定
9_AJ_Core2のentry successは月曜確認予定
```

---

# Step 3で作る整理版EA

予定ファイル名：

```text
time_entry_step3_config_managed_28strategies_clean.mq5
```

目的：

```text
Step 2J.2の機能を維持したまま、コード構造を整理する
28ロジックの仕様を維持する
次のStep 4 Global H1 ATR P70を追加しやすくする
指標停止・年末年始停止・週次複利ロット管理を後から追加しやすくする
```

---

# Step 3で維持する機能

以下はStep 2J.2から変更しない。

```text
28ロジック構成
通貨ペア
Direction
Entry時刻
Exit時刻
SL
TP
Magic Number
Special Rule
日またぎExit判定
Mock JST日時テスト
TestTime一括テスト
Skipログ制御
Rule Rejectログ制御
Global Variableによる同日重複エントリー防止
```

---

# 28ロジック構成

## Step 2F 既存13ロジック

```text
17_EA_1B_Wed_Short
18_EA_2_MonWed_Short
19_EA_3_WedThu_Long
21_GA_B_3
22_GA_C_2
23_GA_F_2
24_GA_D_1
5_GJ_Port_Log2
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

## Step 2H 追加10ロジック

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

## Step 2I China系4ロジック

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

## Step 2J 追加1ロジック

```text
9_AJ_Core2
```

---

# 対象通貨ペア

Step 3整理版EAで扱う通貨ペア：

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
EURJPY
AUDJPY
AUDUSD
```

MT5の気配値表示には上記7銘柄を表示しておく。

---

# Special Rule一覧

整理版でも以下のSpecial Ruleを維持する。

```text
RULE_NONE
RULE_UJ_SHORT_CORE
RULE_UJ_FIX_MIDWEEK
RULE_UJ_SAT_3RD
RULE_UJ_SAT_AUG
RULE_UJ_T10A
RULE_CHINA_AU_DEMAND
RULE_CHINA_9_15
RULE_AJ_CORE2
```

対応：

```text
RULE_NONE              → 通常曜日・時刻ロジック
RULE_UJ_SHORT_CORE     → 12_UJ_Short_Core
RULE_UJ_FIX_MIDWEEK    → 13_UJ_Fix_MidWeek
RULE_UJ_SAT_3RD        → 14_UJ_Sat_3rd
RULE_UJ_SAT_AUG        → 15_UJ_Sat_Aug
RULE_UJ_T10A           → 16_UJ_T10A
RULE_CHINA_AU_DEMAND   → 25_AU_China_Demand
RULE_CHINA_9_15        → 26/27/28 China Demand
RULE_AJ_CORE2          → 9_AJ_Core2
```

---

# Step 3で整理したいコード構造

Step 3整理版では、以下のように関数の役割を分ける。

```text
1. Utility
2. Time / Date helpers
3. Lot / pip helpers
4. Global Variable helpers
5. Symbol / Position helpers
6. Special Rule判定
7. Strategy parameter取得
8. Entry / Exit判定
9. Strategy設定
10. Order処理
11. Expert events
```

目的：

```text
関数の場所を整理して読みやすくする
今後のATRフィルタ追加位置を明確にする
指標停止フィルタ追加位置を明確にする
週次複利ロット計算追加位置を明確にする
```

---

# Step 4以降の追加予定を見据えた整理

## Global H1 ATR P70

Step 4で追加予定。

追加候補位置：

```text
TryEntry() 内
↓
IsEntryTime() 通過後
↓
AlreadyEnteredToday() の前後
↓
ATRフィルタ判定
↓
発注
```

想定関数：

```text
bool PassGlobalAtrFilter(StrategyConfig &cfg, datetime jst_time)
```

---

## 指標停止・年末年始停止

後続Stepで追加予定。

追加候補位置：

```text
IsStrategyActiveDate() の後
または
TryEntry() 内のEntry直前
```

想定関数：

```text
bool PassEventFilter(StrategyConfig &cfg, datetime jst_time)
bool PassYearEndFilter(datetime jst_time)
```

---

## 週次複利ロット管理

後続Stepで追加予定。

現在：

```text
InpFixedLot = 0.01
```

将来：

```text
GetStrategyLot(cfg)
```

または、

```text
CalculateWeeklyRiskLot(cfg, account_balance)
```

へ差し替える。

---

# Step 3ではまだ実装しないもの

Step 3では、コード整理のみを目的とし、以下はまだ実装しない。

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
本番ロット管理
外部CSV設定
```

---

# Step 3整理版のテスト方針

Step 3.2で整理版コードを作成後、以下を確認する。

## Test 1：コンパイル

```text
0 errors
0 warnings
```

## Test 2：28ロジック全ON起動確認

```text
28ロジック全ONで起動
7通貨ペア認識
28ロジック分の初期化ログ
エラーなし
不要な大量エントリーなし
```

## Test 3：代表Entry確認

代表として以下を確認する。

```text
既存通常ロジック代表：5_GJ_Port_Log2
UJ特殊代表：12_UJ_Short_Core
China代表：25_AU_China_Demand
AJ特殊代表：9_AJ_Core2
```

ただし、China系4本と9_AJ_Core2のentry success確認は、月曜の市場オープン後に行う。

---

# Step 3開始条件

Step 3.2整理版コード作成は、月曜に以下を確認してから進めるのが安全。

```text
China系4本 entry success
9_AJ_Core2 entry success
SL / TP確認
方向確認
手動決済確認
```

ただし、Step 3.1仕様整理はこの時点で完了とする。

---

# Step 3.1 判定

Step 3.1は完了。

次に進む条件：

```text
月曜日に未完了Entry確認
↓
Step 2I / Step 2J 正式合格ログ
↓
Step 3.2 整理版EAコード作成
```

## 2026-06-17：EA Step 2I / Step 2J 正式合格ログ

### 対象EA

```text
time_entry_step2j2_config_managed_28strategies.mq5
```

---

## 目的

Step 2I / Step 2Jで未完了だった実注文確認を行い、28ロジック統合EAを正式合格とする。

対象：

```text
Step 2I：China系4ロジック
Step 2J：9_AJ_Core2
```

---

# Step 2I：China系4ロジック 正式確認

## 対象ロジック

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

## 確認内容

以下を確認した。

```text
China系4本 entry success OK

25_AU：AUDUSD buy 0.01 OK
26_AJ：AUDJPY buy 0.01 OK
27_EA：EURAUD sell 0.01 OK
28_GA：GBPAUD sell 0.01 OK

SL / TP OK
方向 OK
手動決済 OK
```

## 判定

```text
Step 2I 正式合格
```

---

# Step 2J：9_AJ_Core2 正式確認

## 対象ロジック

```text
9_AJ_Core2
```

## 仕様

| Item | Value |
|---|---|
| Pair | AUDJPY |
| Direction | Short |
| Entry | 木曜 17:14 JST |
| Exit | 翌日 01:14 JST |
| SL | 30 pips |
| TP | 80 pips |
| Magic | 90001 |
| Special Rule | RULE_AJ_CORE2 |

## 確認内容

以下を確認した。

```text
9_AJ_Core2 entry success OK
AUDJPY sell 0.01 OK

SL / TP OK
方向 OK
手動決済 OK
Entry直後にTime exitしない OK
```

## 判定

```text
Step 2J 正式合格
```

---

# 28ロジック統合EA 正式合格

## 確認済み

```text
28ロジック統合EA コンパイルOK
28ロジック全ON起動OK
7通貨ペア認識OK
China系4本 entry success OK
9_AJ_Core2 entry success OK
SL / TP OK
方向 OK
手動決済 OK
日またぎ即決済なし OK
```

## 判定

```text
Step 2J.2：28ロジック統合EA 正式合格
```

---

# 現在の到達点

```text
Step 2F：13ロジック統合EA OK
Step 2H：23ロジック統合EA OK
Step 2I：China系4ロジック 正式合格
Step 2J：9_AJ_Core2 正式合格
Step 2J.2：28ロジック統合EA 正式合格
```

---

# 注意点

現時点のEAは、28ロジックの時間エントリー・時間決済・SL/TP・Magic管理を確認するための統合検証版。

まだ本番運用には使用しない。

未実装：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
本番用ロット管理
外部CSV設定
```

---

# 次にやること

次は Step 3.2 として、28ロジック統合EAの整理版コードを作成する。

予定ファイル名：

```text
time_entry_step3_config_managed_28strategies_clean.mq5
```

Step 3.2の目的：

```text
Step 2J.2の機能を維持したままコード構造を整理する
今後のGlobal H1 ATR P70追加に備える
指標停止・年末年始停止・週次複利ロット管理を追加しやすい土台にする
```
