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

## 2026-06-16：EA Step 2I.1 China系4ロジック仕様整理

### 目的

Step 2Iでは、Step 2Hで完成した23ロジック統合EAに、China系4ロジックを追加する。

追加対象：

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

Step 2I追加後は以下になる。

```text
Step 2H：23ロジック
Step 2I：+4ロジック
合計：27ロジック
```

---

# China系4ロジック一覧

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic |
|---:|---|---|---|---|---|---:|---:|---:|
| 25 | 25_AU_China_Demand | AUDUSD | Long | 条件日 10:00 JST | 当日 15:50 JST | 40 | 40 | 25001 |
| 26 | 26_AJ_China_Demand | AUDJPY | Long | 条件日 10:00 JST | 当日 15:50 JST | 45 | 80 | 26001 |
| 27 | 27_EA_China_Demand | EURAUD | Short | 条件日 10:00 JST | 当日 15:50 JST | 60 | 60 | 27001 |
| 28 | 28_GA_China_Demand | GBPAUD | Short | 条件日 10:00 JST | 当日 16:10 JST | 75 | 70 | 28001 |

---

# 追加通貨ペア

Step 2Iで新規追加される通貨ペア：

```text
AUDUSD
```

Step 2I後にEAで扱う通貨ペア：

```text
EURAUD
GBPAUD
GBPJPY
USDJPY
EURJPY
AUDJPY
AUDUSD
```

MT5の気配値表示には、上記7銘柄を表示しておく。

---

# 25_AU_China_Demand

```text
Pair：AUDUSD
Direction：Long
Entry：10:00 JST
Exit：15:50 JST
SL：40 pips
TP：40 pips
Magic：25001
```

稼働条件：

```text
平日 かつ（9〜15日 または 25日〜月末）
```

コード条件イメージ：

```text
weekday is Monday〜Friday
AND
(
  day >= 9 AND day <= 15
  OR
  day >= 25
)
```

Special Rule：

```text
RULE_CHINA_AU_DEMAND
```

---

# 26_AJ_China_Demand

```text
Pair：AUDJPY
Direction：Long
Entry：10:00 JST
Exit：15:50 JST
SL：45 pips
TP：80 pips
Magic：26001
```

稼働条件：

```text
平日 かつ 9〜15日
```

コード条件イメージ：

```text
weekday is Monday〜Friday
AND
day >= 9 AND day <= 15
```

Special Rule：

```text
RULE_CHINA_9_15
```

---

# 27_EA_China_Demand

```text
Pair：EURAUD
Direction：Short
Entry：10:00 JST
Exit：15:50 JST
SL：60 pips
TP：60 pips
Magic：27001
```

稼働条件：

```text
平日 かつ 9〜15日
```

コード条件イメージ：

```text
weekday is Monday〜Friday
AND
day >= 9 AND day <= 15
```

Special Rule：

```text
RULE_CHINA_9_15
```

---

# 28_GA_China_Demand

```text
Pair：GBPAUD
Direction：Short
Entry：10:00 JST
Exit：16:10 JST
SL：75 pips
TP：70 pips
Magic：28001
```

稼働条件：

```text
平日 かつ 9〜15日
```

コード条件イメージ：

```text
weekday is Monday〜Friday
AND
day >= 9 AND day <= 15
```

Special Rule：

```text
RULE_CHINA_9_15
```

---

# Special Rule追加方針

Step 2Iでは、以下のSpecial Ruleを追加する。

```text
RULE_CHINA_AU_DEMAND
RULE_CHINA_9_15
```

対応：

```text
RULE_CHINA_AU_DEMAND
→ 25_AU_China_Demand

RULE_CHINA_9_15
→ 26_AJ_China_Demand
→ 27_EA_China_Demand
→ 28_GA_China_Demand
```

---

# Step 2I.2 実装方針

Step 2Hの23ロジックEAに、China系4ロジックを追加する。

```text
StrategyConfig strategies[27]
```

追加4ロジックは、曜日条件だけではなく日付範囲条件を持つため、`RULE_NONE` ではなくSpecial Ruleで管理する。

---

# Step 2I.2 テスト方針

## Test 1：China系4ロジックのみON

```text
既存23ロジック = false
China系4ロジック = true
```

Mock JST日時を使って、条件日エントリーを確認する。

---

## Test 2：25_AU条件確認

25_AUは条件が2ブロックあるため、以下を確認する。

```text
9〜15日でEntryする
25日〜月末でEntryする
16〜24日はEntryしない
土日はEntryしない
```

---

## Test 3：26/27/28 条件確認

26/27/28は共通で以下を確認する。

```text
9〜15日でEntryする
16日以降はEntryしない
土日はEntryしない
```

---

## Test 4：27ロジック全ON起動確認

```text
既存23ロジック = true
China系4ロジック = true
```

確認：

```text
27ロジック全ONでEA起動OK
7通貨ペア認識OK
初期化ログOK
エラーなし
不要な大量エントリーなし
```

---

# Step 2Iではまだ実装しないもの

```text
9_AJ_Core2の追加日付停止
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック本番版
```

次は `Step 2I.2：China系4ロジック追加コード作成` に進む。

## 2026-06-16：EA Step 2I China系4ロジック 仮合格ログ

### 対象EA

```text
time_entry_step2i2_config_managed_27strategies.mq5
```

### 対象ロジック

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

---

## Step 2I の目的

Step 2Hで完成した23ロジック統合EAに、China系4ロジックを追加し、27ロジック統合EAとして動作確認する。

---

## 追加した4ロジック

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic |
|---:|---|---|---|---|---|---:|---:|---:|
| 25 | 25_AU_China_Demand | AUDUSD | Long | 10:00 JST | 15:50 JST | 40 | 40 | 25001 |
| 26 | 26_AJ_China_Demand | AUDJPY | Long | 10:00 JST | 15:50 JST | 45 | 80 | 26001 |
| 27 | 27_EA_China_Demand | EURAUD | Short | 10:00 JST | 15:50 JST | 60 | 60 | 27001 |
| 28 | 28_GA_China_Demand | GBPAUD | Short | 10:00 JST | 16:10 JST | 75 | 70 | 28001 |

---

## China系条件

```text
25_AU：平日 かつ（9〜15日 または 25日〜月末）
26_AJ：平日 かつ 9〜15日
27_EA：平日 かつ 9〜15日
28_GA：平日 かつ 9〜15日
```

---

## テスト結果

### Test 1：China系4ロジックのみON

結果：

```text
条件OK → 発注処理まで到達
ただし土曜日で market closed のため、entry success は未確認
```

判定：

```text
条件判定は概ねOK
実注文確認は月曜日に持ち越し
```

---

### 停止条件テスト

確認済み：

```text
25_AUの16〜24日停止
25_AUの土日停止
26/27/28の16日以降停止
26/27/28の土日停止
```

結果：

```text
OK
```

---

### Test 4：27ロジック全ON起動確認

確認済み：

```text
27ロジック全ONで起動した
7通貨ペアを認識した
27ロジック分の初期化ログが出た
エラーが出なかった
不要な大量エントリーが発生しなかった
```

結果：

```text
OK
```

---

## Step 2I 判定

Step 2Iは **仮合格** とする。

理由：

```text
China系4ロジックの条件判定はOK
停止条件テストもOK
27ロジック全ON起動確認もOK
ただし、土曜日のため China系4本の entry success は未確認
```

---

## 未完了タスク

月曜日に以下を必ず確認する。

```text
25_AU：AUDUSD buy 0.01 が建つ
26_AJ：AUDJPY buy 0.01 が建つ
27_EA：EURAUD sell 0.01 が建つ
28_GA：GBPAUD sell 0.01 が建つ

SL / TP が入る
方向が正しい
手動決済できる
エキスパートログに entry success が出る
```

---

## 次にやること

China系4本の実注文テストは月曜日に持ち越し。

開発は先に進め、次は以下を実施する。

```text
Step 2J.1：9_AJ_Core2 仕様整理
Step 2J.2：9_AJ_Core2追加コード作成
```

## 2026-06-16：EA Step 2J.1 9_AJ_Core2仕様整理

### 目的

Step 2Jでは、残り1ロジックである `9_AJ_Core2` を27ロジック統合EAへ追加し、28ロジック統合EAを作成する。

現在の状態：

```text
Step 2I：27ロジック統合EAまで作成
残り：9_AJ_Core2
```

---

# 9_AJ_Core2 基本仕様

| Item | Value |
|---|---|
| Strategy | 9_AJ_Core2 |
| Pair | AUDJPY |
| Direction | Short |
| Entry | 木曜 17:14 JST |
| Exit | 翌日 01:14 JST |
| SL | 30 pips |
| TP | 80 pips |
| Magic | 90001 |

---

## 通常条件

```text
木曜日 17:14 JST に Short
翌日 01:14 JST に時間決済
```

日またぎ決済：

```text
Entry：木曜 17:14
Exit：金曜 01:14
```

Step 2F以降で実装済みの日またぎExit判定を使用する。

---

# 追加停止条件

`9_AJ_Core2` は通常曜日ロジックではなく、以下の追加停止条件を持つ。

```text
6月停止
9月停止
1日停止
20日停止
26日以降停止
```

EA条件としては以下。

```text
month != 6
month != 9
day != 1
day != 20
day < 26
```

つまり稼働可能日は、

```text
6月・9月ではない
かつ
1日・20日ではない
かつ
25日以前
かつ
木曜日
```

---

# Special Rule

`9_AJ_Core2` は追加日付停止を持つため、`RULE_NONE` ではなく専用Special Ruleで管理する。

追加予定：

```text
RULE_AJ_CORE2
```

対応：

```text
RULE_AJ_CORE2 → 9_AJ_Core2
```

---

# Step 2J.2 実装方針

Step 2Iの27ロジックEAに `9_AJ_Core2` を追加する。

```text
StrategyConfig strategies[28]
```

追加内容：

```text
InpEnable_9_AJ_Core2
RULE_AJ_CORE2
IsAJCore2ActiveDate()
SetStrategyで9_AJ_Core2を追加
```

---

# Step 2J.2 テスト方針

## Test 1：9_AJ_Core2 Entry確認

Mock JSTで木曜条件を作る。

例：

```text
2026-07-02 17:14
```

期待：

```text
AUDJPY sell 0.01 が建つ
SL30 / TP80 が入る
Entry直後にTime exitしない
```

---

## Test 2：停止条件確認

以下を確認する。

```text
6月停止
9月停止
1日停止
20日停止
26日以降停止
木曜以外停止
```

---

## Test 3：28ロジック全ON起動確認

確認項目：

```text
28ロジック全ONで起動する
7通貨ペアを認識する
28ロジック分の初期化ログが出る
エラーが出ない
不要な大量エントリーが発生しない
```

---

# 注意点

China系4ロジックの実注文テストは月曜日に未完了。

Step 2Jを進めるが、以下は必ず残タスクとして扱う。

```text
China系4本の entry success 確認
25_AU / 26_AJ / 27_EA / 28_GA のSL/TP確認
```

---

# Step 2Jではまだ実装しないもの

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
本番用ロット管理
```

まずは28ロジックの時間エントリー、時間決済、SL/TP、Magic管理を完成させる。
