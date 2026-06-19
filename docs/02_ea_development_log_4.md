## 2026-06-15：EA Step 2H.1 EJ/GJ/AJ通常曜日系10ロジック仕様整理

### 目的

Step 2Hでは、Step 2Fで完成した13ロジック統合EAに、通常曜日・通常時刻で管理しやすい10ロジックを追加する。

追加後は以下になる。

```text
Step 2F：13ロジック
Step 2H：+10ロジック
合計：23ロジック
```

---

# Step 2H 追加対象10ロジック

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

※ `9_AJ_Core2` は追加停止条件が多いため、Step 2Jで対応する。

---

# 追加後の対象通貨ペア

Step 2Hで新規追加される通貨ペア：

```text
EURJPY
AUDJPY
```

Step 2Fまでに使用済み：

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
```

Step 2H後にEAで扱う通貨ペア：

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
EURJPY
AUDJPY
```

MT5の気配値表示に上記6銘柄を表示しておく。

---

# 10ロジック仕様一覧

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic |
|---:|---|---|---|---|---|---:|---:|---:|
| 1 | 1_EJ_Log1 | EURJPY | Long | 月・水 13:55 | 翌日 04:55 | 70 | 250 | 10001 |
| 2 | 2_EJ_NightBlitz_20 | EURJPY | Long | 月・水 20:56 | 翌日 04:45 | 45 | 70 | 20001 |
| 3 | 3_EJ_NightBlitz_21 | EURJPY | Long | 月・水 21:56 | 翌日 05:27 | 75 | 70 | 30001 |
| 4 | 4_GJ_Port_Log1 | GBPJPY | Long | 火・水 00:00 | 当日 08:55 | 130 | 90 | 40001 |
| 6 | 6_GJ_Old_Mon | GBPJPY | Long | 月 15:45 | 当日 22:50 | 50 | 210 | 60001 |
| 7 | 7_GJ_Mon_Blitz | GBPJPY | Long | 月 18:02 | 当日 23:02 | 130 | 250 | 70001 |
| 8 | 8_AJ_Core1 | AUDJPY | Long | 月 08:01 | 当日 22:46 | 70 | 110 | 80001 |
| 10 | 10_AJ_SatA | AUDJPY | Short | 金 10:58 | 当日 13:51 | 50 | 25 | 10002 |
| 11 | 11_AJ_SatB | AUDJPY | Short | 金 18:57 | 翌日 01:43 | 55 | 95 | 11001 |
| 20 | 20_EA_1A_MonTue_Short | EURAUD | Short | 月・火 10:01 | 当日 16:00 | 50 | 125 | 20002 |

---

# 個別仕様

## 1_EJ_Log1

```text
Pair：EURJPY
Direction：Long
Entry：月・水 13:55 JST
Exit：翌日 04:55 JST
SL：70 pips
TP：250 pips
Magic：10001
Special Rule：RULE_NONE
```

---

## 2_EJ_NightBlitz_20

```text
Pair：EURJPY
Direction：Long
Entry：月・水 20:56 JST
Exit：翌日 04:45 JST
SL：45 pips
TP：70 pips
Magic：20001
Special Rule：RULE_NONE
```

---

## 3_EJ_NightBlitz_21

```text
Pair：EURJPY
Direction：Long
Entry：月・水 21:56 JST
Exit：翌日 05:27 JST
SL：75 pips
TP：70 pips
Magic：30001
Special Rule：RULE_NONE
```

---

## 4_GJ_Port_Log1

```text
Pair：GBPJPY
Direction：Long
Entry：火・水 00:00 JST
Exit：当日 08:55 JST
SL：130 pips
TP：90 pips
Magic：40001
Special Rule：RULE_NONE
```

---

## 6_GJ_Old_Mon

```text
Pair：GBPJPY
Direction：Long
Entry：月 15:45 JST
Exit：当日 22:50 JST
SL：50 pips
TP：210 pips
Magic：60001
Special Rule：RULE_NONE
```

---

## 7_GJ_Mon_Blitz

```text
Pair：GBPJPY
Direction：Long
Entry：月 18:02 JST
Exit：当日 23:02 JST
SL：130 pips
TP：250 pips
Magic：70001
Special Rule：RULE_NONE
```

---

## 8_AJ_Core1

```text
Pair：AUDJPY
Direction：Long
Entry：月 08:01 JST
Exit：当日 22:46 JST
SL：70 pips
TP：110 pips
Magic：80001
Special Rule：RULE_NONE
```

---

## 10_AJ_SatA

```text
Pair：AUDJPY
Direction：Short
Entry：金 10:58 JST
Exit：当日 13:51 JST
SL：50 pips
TP：25 pips
Magic：10002
Special Rule：RULE_NONE
```

---

## 11_AJ_SatB

```text
Pair：AUDJPY
Direction：Short
Entry：金 18:57 JST
Exit：翌日 01:43 JST
SL：55 pips
TP：95 pips
Magic：11001
Special Rule：RULE_NONE
```

---

## 20_EA_1A_MonTue_Short

```text
Pair：EURAUD
Direction：Short
Entry：月・火 10:01 JST
Exit：当日 16:00 JST
SL：50 pips
TP：125 pips
Magic：20002
Special Rule：RULE_NONE
```

---

# Step 2H実装方針

Step 2Hでは、Step 2Fの13ロジックEAに上記10ロジックを追加する。

```text
StrategyConfig strategies[23]
```

追加10ロジックは全て `RULE_NONE` として扱う。

理由：

```text
曜日条件
Entry時刻
Exit時刻
SL
TP
Magic Number
```

のみで管理可能なため。

---

# 日またぎExit対応

以下のロジックは日またぎExitになるため、Step 2Fの修正版Exit判定をそのまま使う。

```text
1_EJ_Log1
2_EJ_NightBlitz_20
3_EJ_NightBlitz_21
11_AJ_SatB
```

既存ロジック側の日またぎExitも引き続き対象。

```text
18_EA_2_MonWed_Short
19_EA_3_WedThu_Long
21_GA_B_3
22_GA_C_2
24_GA_D_1
14_UJ_Sat_3rd
```

---

# Step 2H.2 テスト方針

## Test 1：追加10ロジックのみON

```text
Step 2F既存13ロジック = false
Step 2H追加10ロジック = true
```

`InpUseTestTimes = true` で一括テストする。

確認：

```text
10ロジックがEntryする
Long / Shortが正しく出る
EURJPY / GBPJPY / AUDJPY / EURAUDが扱える
SL / TPが入る
Time exitが機能する
日またぎExitで即決済されない
```

---

## Test 2：追加10ロジックの代表Mock/時刻テスト

日またぎ代表として以下を確認する。

```text
1_EJ_Log1
11_AJ_SatB
```

期待：

```text
Entry直後にTime exitしない
取引タブにポジションが残る
```

---

## Test 3：23ロジック全ON起動確認

```text
既存13ロジック = true
追加10ロジック = true
```

確認：

```text
23ロジック全ONでEA起動OK
6通貨ペア認識OK
初期化ログOK
エラーなし
```

---

# Step 2Hではまだ実装しないもの

```text
9_AJ_Core2の追加日付停止
China系4ロジック
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック本番版
```

次は `Step 2H.2：23ロジック統合EAコード作成` に進む。

## 2026-06-15：EA Step 2H 23ロジック統合EAテスト完了

### 対象EA

```text
time_entry_step2h2_config_managed_23strategies.mq5
```

### 目的

Step 2Hでは、Step 2Fで完成した13ロジック統合EAに、EJ/GJ/AJ/EAの通常曜日系10ロジックを追加し、合計23ロジックの設定管理型EAとして動作確認した。

---

## 追加した10ロジック

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

---

## Step 2H後の構成

```text
Step 2F：既存13ロジック
Step 2H：追加10ロジック
合計：23ロジック
```

対象通貨ペア：

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
EURJPY
AUDJPY
```

---

## 実装内容

```text
StrategyConfig strategies[23]
通常曜日系10ロジックをRULE_NONEとして追加
EURJPY / AUDJPY を新規対応
日またぎExit修正を維持
Skipログ制御を維持
Magic Number別管理を維持
```

---

## テスト結果

### Test 1：追加10ロジック一括Entry/Exit

設定：

```text
追加10ロジック = true
既存13ロジック = false
InpUseTestTimes = true
InpUseMockJstDateTime = false
```

確認結果：

```text
10ロジックがEntryした
4通貨ペアを扱えた
Long / Shortが正しく建った
SL / TPが入った
Exit時刻でTime exit successが出た
取引タブからポジションが消えた
```

判定：

```text
OK
```

---

### Test 2：日またぎExit代表テスト

対象：

```text
1_EJ_Log1
11_AJ_SatB
```

確認結果：

```text
Entry直後にTime exitしない
取引タブにポジションが残る
手動決済で確認完了
```

判定：

```text
OK
```

---

### Test 3：23ロジック全ON起動確認

確認結果：

```text
23ロジック全ONで起動した
6通貨ペアを認識した
23ロジック分の初期化ログが出た
エラーが出なかった
不要な大量エントリーが発生しなかった
```

判定：

```text
OK
```

---

## Step 2H 判定

Step 2Hは合格。

確認済み：

```text
Step 2F：13ロジック統合EA OK
Step 2H：23ロジック統合EA OK
```

---

## 注意点

Step 2Hはまだ検証用EAであり、本番運用には使用しない。

未実装：

```text
9_AJ_Core2の追加日付停止
China系4ロジック
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック本番版
```

---

## 次にやること

次は Step 2I として、China系4ロジックを整理・追加する。

対象：

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

条件メモ：

```text
25_AU：平日 かつ（9〜15日 または 25日〜月末）
26_AJ：平日 かつ 9〜15日
27_EA：平日 かつ 9〜15日
28_GA：平日 かつ 9〜15日
```

Step 2Iでは、上記の日付範囲条件をSpecial Ruleとして追加する。
