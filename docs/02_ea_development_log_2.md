## 2026-06-15：EA Step 2D.1 12_UJ_Short_Core 疑似JST日付テスト完了

### 対象EA

```text
time_entry_step2d1_uj_short_core_mock_date_test.mq5
```

### 対象ロジック

```text
12_UJ_Short_Core
```

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Lot | 0.01固定 |
| Magic Number | 12001 |
| ATR Filter | なし |
| Event Filter | なし |
| Weekly Compounding | なし |

---

## Step 2D.1 の目的

Step 2Dでは、`12_UJ_Short_Core` のゴトー日モード・通常日モードの強制テストを行い、注文仕様の切り替えを確認した。

Step 2D.1では、さらに一歩進めて、実際の日付を待たずにEA内部だけ疑似JST日時を使い、`12_UJ_Short_Core` の日付条件そのものを検証した。

確認対象は以下。

```text
20日 → ゴトー日モード
25日 → ゴトー日モード
30日 → ゴトー日モード
通常稼働日 → 通常日モード
21日 → 停止
22日 → 停止
水曜日 → 停止
8月 → 停止
カレンダー月末 → 停止
20日未満 → 停止
```

---

## 追加したテスト機能

以下のinputを追加した。

```text
InpUseMockJstDateTime
InpMockYear
InpMockMonth
InpMockDay
InpMockHour
InpMockMinute
```

これにより、実際のMT5サーバー時刻ではなく、EA内部で任意のJST日時を使って日付条件判定を行えるようにした。

例：

```text
InpUseMockJstDateTime = true
InpMockYear = 2026
InpMockMonth = 2
InpMockDay = 20
InpMockHour = 9
InpMockMinute = 55
```

この場合、EA内部では以下として判定される。

```text
2026-02-20 09:55 JST
```

---

## 共通テスト設定

各テストでは、基本的に以下の設定で実施した。

```text
InpTestMode = true
InpTestModeIgnoreDateRules = false
InpUseTestTimes = false
InpUseMockJstDateTime = true
InpForceGotoMode = false
InpForceNormalMode = false
```

`InpUseTestTimes = false` としたため、テスト時刻は本来のEntry時刻に合わせた。

```text
ゴトー日モード：09:55 JST
通常日モード：08:04 JST
```

---

## ゴトー日判定仕様

`12_UJ_Short_Core` のゴトー日判定は、バックテスト再現性を優先し、初期版では以下のみとした。

```text
20日
25日
30日
```

重要仕様：

```text
前倒しゴトー日は未実装
```

メモ：

```text
12_UJ_Short_Core のゴトー日判定は、バックテスト再現性を優先し、初期版ではカレンダー日付の20日・25日・30日のみとする。
前倒しゴトー日は未実装。
必要であれば、後続バージョンで InpUseForwardGotoDay を追加し、別途検証する。
```

---

## テスト結果一覧

| No | Test | Mock DateTime JST | 期待結果 | 結果 |
|---:|---|---|---|---|
| 1 | 20日ゴトー日 | 2026-02-20 09:55 | GOTOでEntry | OK |
| 2 | 25日ゴトー日 | 2026-06-25 09:55 | GOTOでEntry | OK |
| 3 | 30日ゴトー日 | 2026-07-30 09:55 | GOTOでEntry | OK |
| 4 | 通常日 | 2026-06-23 08:04 | NORMALでEntry | OK |
| 5 | 21日停止 | 2026-06-21 09:55 | Entryしない | OK |
| 6 | 22日停止 | 2026-06-22 09:55 | Entryしない | OK |
| 7 | 水曜停止 | 2026-06-24 08:04 | Entryしない | OK |
| 8 | 8月停止 | 2026-08-25 09:55 | Entryしない | OK |
| 9 | 月末停止 | 2026-07-31 08:04 | Entryしない | OK |
| 10 | 20日未満停止 | 2026-06-19 08:04 | Entryしない | OK |

---

## 確認できた内容

### エントリーする条件

以下は、想定どおりエントリーした。

```text
20日ゴトー日
25日ゴトー日
30日ゴトー日
通常稼働日
```

ログ例：

```text
SELL entry success. Mode=GOTO
SELL entry success. Mode=NORMAL
```

確認できたこと：

```text
20日・25日・30日はGOTOモードになる
通常稼働日はNORMALモードになる
GOTOモードではSL20 / TP50になる
NORMALモードではSL50 / TPなしになる
```

---

### 停止する条件

以下は、想定どおりエントリーしなかった。

```text
21日
22日
水曜日
8月
カレンダー月末
20日未満
```

ログ例：

```text
Date rule reject: 21st stop
Date rule reject: 22nd stop
Date rule reject: Wednesday stop
Date rule reject: August stop
Date rule reject: calendar month end stop
Date rule reject: before 20th
```

確認できたこと：

```text
停止条件が想定どおり機能している
ゴトー日判定より停止条件が優先される
カレンダー月末停止が機能している
8月全停止が機能している
水曜停止が機能している
```

---

## 決済について

Step 2D.1は日付条件テストが主目的のため、エントリーしたポジションは手動決済で対応した。

時間決済は、Step 2Dの強制モードテストで確認済み。

```text
Step 2D：Time exit success 確認済み
Step 2D.1：日付条件確認のため、エントリー後は手動決済
```

---

## Step 2D.1 判定

Step 2D.1は合格。

確認できた項目：

```text
20日ゴトー日判定
25日ゴトー日判定
30日ゴトー日判定
通常日判定
21日停止
22日停止
水曜日停止
8月停止
カレンダー月末停止
20日未満停止
GOTO / NORMAL モード切り替え
GOTO時のSL/TP設定
NORMAL時のSL/TP設定
```

これにより、`12_UJ_Short_Core` の主要な日付条件はEA上で再現できていると判断。

---

## 注意点

同じMock日付で再テストする場合、Global Variableに同日エントリー済み記録が残る。

再テスト時は、MT5で以下を実施する。

```text
F3
↓
グローバル変数
↓
TE_STEP2D1_12_UJ_SHORT_CORE_USDJPY_12001_日付
↓
削除
```

例：

```text
TE_STEP2D1_12_UJ_SHORT_CORE_USDJPY_12001_20260220
```

---

## 次にやること

次は、以下のどちらかに進む。

```text
Step 2D.2：12_UJ_Short_Core を設定管理型EAへ統合
Step 2E：UJ 5ロジック対応
```

推奨順：

```text
Step 2D.2
↓
Step 2E
```

理由：

```text
まず12_UJ_Short_Coreを既存の設定管理型EAへ統合し、特殊日付ロジックを既存構造に組み込めるか確認する。
その後、13_UJ_Fix_MidWeek、14_UJ_Sat_3rd、15_UJ_Sat_Aug、16_UJ_T10Aを追加する方が安全。
```

Step 2D.2で確認したいこと：

```text
設定管理型EAの中で12_UJ_Short_Coreが動く
GOTO / NORMAL分岐が維持される
日付条件が維持される
Magic Numberが12001で管理される
既存8ロジックと共存できる構造にできる
```

## 2026-06-15：EA Step 2D.2 12_UJ_Short_Core 設定管理型EA統合テスト完了

### 対象EA

```text
time_entry_step2d2_config_managed_9strategies_with_uj.mq5
```

### 対象ロジック

Step 2D.2では、Step 2Cの設定管理型8戦略EAに、以下のUJ特殊日付ロジックを追加した。

```text
12_UJ_Short_Core
```

これにより、管理対象は以下の9戦略となった。

```text
22_GA_C_2
5_GJ_Port_Log2
21_GA_B_3
23_GA_F_2
24_GA_D_1
17_EA_1B_Wed_Short
18_EA_2_MonWed_Short
19_EA_3_WedThu_Long
12_UJ_Short_Core
```

---

## Step 2D.2 の目的

Step 2D.1では、`12_UJ_Short_Core` 単体で疑似JST日付テストを行い、日付条件が正しく動くことを確認した。

Step 2D.2では、`12_UJ_Short_Core` を既存の設定管理型EAへ統合し、以下を確認した。

```text
設定管理型EAの中で12_UJ_Short_Coreが動作するか
UJ特殊日付条件が既存構造と共存できるか
GOTO / NORMAL 分岐が維持されるか
SL / TP 分岐が維持されるか
Magic Number 12001で管理できるか
既存8ロジックと同じEA内で共存できるか
```

---

## 追加した特殊ルール

`StrategyConfig` に以下の項目を追加し、通常ロジックと特殊日付ロジックを区別できるようにした。

```text
special_rule
```

ルール定義：

```text
RULE_NONE
RULE_UJ_SHORT_CORE
```

`12_UJ_Short_Core` には以下を設定。

```text
special_rule = RULE_UJ_SHORT_CORE
```

---

## 12_UJ_Short_Core 設定

| Field | Value |
|---|---|
| StrategyName | 12_UJ_Short_Core |
| Symbol | USDJPY |
| Direction | Short |
| Magic Number | 12001 |
| Special Rule | RULE_UJ_SHORT_CORE |
| Lot | 0.01固定 |
| Comment | 12_UJ_Short_Core_step2d2 |

---

## 12_UJ_Short_Core 日付条件

### 稼働日

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

---

## ゴトー日判定

ゴトー日は以下のみ。

```text
20日
25日
30日
```

重要仕様：

```text
前倒しゴトー日は未実装
```

メモ：

```text
12_UJ_Short_Core のゴトー日判定は、バックテスト再現性を優先し、初期版ではカレンダー日付の20日・25日・30日のみとする。
前倒しゴトー日は未実装。
必要であれば、後続バージョンで InpUseForwardGotoDay を追加し、別途検証する。
```

---

## モード別仕様

### GOTOモード

| Item | Value |
|---|---|
| Entry | 09:55 JST |
| Exit | 14:56 JST |
| Direction | Short |
| SL | 20 pips |
| TP | 50 pips |

---

### NORMALモード

| Item | Value |
|---|---|
| Entry | 08:04 JST |
| Exit | 14:56 JST |
| Direction | Short |
| SL | 50 pips |
| TP | なし |

---

## 追加したテスト用input

UJ専用テスト用として、以下を追加した。

```text
InpUJIgnoreDateRules
InpUJUseTestTimes
InpUJForceGotoMode
InpUJForceNormalMode
```

また、疑似JST日時テスト用として以下を利用。

```text
InpUseMockJstDateTime
InpMockYear
InpMockMonth
InpMockDay
InpMockHour
InpMockMinute
```

---

## テスト内容

### A. UJ GOTO 強制テスト

設定：

```text
InpTestMode = true
InpUseMockJstDateTime = false
InpUJIgnoreDateRules = true
InpUJUseTestTimes = true
InpUJForceGotoMode = true
InpUJForceNormalMode = false
```

結果：

```text
SELL entry success. Symbol=USDJPY, Mode=GOTO
```

確認できた内容：

```text
USDJPY Short 0.01 が建つ
GOTOモードとして発注される
SL 20pips が設定される
TP 50pips が設定される
```

判定：

```text
OK
```

---

### B. UJ NORMAL 強制テスト

設定：

```text
InpTestMode = true
InpUseMockJstDateTime = false
InpUJIgnoreDateRules = true
InpUJUseTestTimes = true
InpUJForceGotoMode = false
InpUJForceNormalMode = true
```

結果：

```text
SELL entry success. Symbol=USDJPY, Mode=NORMAL
```

確認できた内容：

```text
USDJPY Short 0.01 が建つ
NORMALモードとして発注される
SL 50pips が設定される
TPなしで発注される
```

判定：

```text
OK
```

---

### C. UJ Mock日付テスト

設定：

```text
InpTestMode = true
InpUseMockJstDateTime = true
InpUJIgnoreDateRules = false
InpUJUseTestTimes = false
InpUJForceGotoMode = false
InpUJForceNormalMode = false
```

代表テストとして、Mock JST日付を設定して確認。

例：

```text
InpMockYear = 2026
InpMockMonth = 2
InpMockDay = 20
InpMockHour = 9
InpMockMinute = 55
```

結果：

```text
SELL entry success. Symbol=USDJPY, Mode=GOTO
```

確認できた内容：

```text
設定管理型EA内でも、Mock日付によるUJ日付判定が機能する
20日がGOTOモードとして認識される
```

判定：

```text
OK
```

補足：

```text
日付条件そのものはStep 2D.1で10パターン確認済みのため、Step 2D.2では代表テスト1件でOKと判断。
```

---

## Step 2D.2 テスト結果

以下すべてOK。

```text
A. UJ GOTO 強制テスト
B. UJ NORMAL 強制テスト
C. UJ Mock日付テスト
```

---

## Step 2D.2 判定

Step 2D.2は合格。

確認できた項目：

```text
12_UJ_Short_Core を設定管理型EAへ統合できた
既存8ロジックと同じEA構造に追加できた
USDJPYを追加銘柄として扱える
UJ特殊日付条件を special_rule で管理できる
GOTO / NORMAL 分岐が維持される
GOTO時のSL20 / TP50 が維持される
NORMAL時のSL50 / TPなし が維持される
Magic Number 12001で管理できる
Mock日付テストが統合EA内でも機能する
```

---

## 注意点

Step 2D.2はまだ検証用EAであり、本番運用には使用しない。

未実装の機能：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

また、同じ日に再テストする場合は、Global Variableが残るため、必要に応じてF3から以下のような変数を削除する。

```text
TE_STEP2D2_12_UJ_Short_Core_USDJPY_12001_日付
```

---

## 次にやること

次は Step 2E として、UJ系ロジックを拡張する。

対象候補：

```text
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

Step 2Eの目的：

```text
UJ系5ロジックを設定管理型EAへ追加する
日付条件系ロジックを複数扱えるようにする
12_UJ_Short_Core以外のUJ特殊条件を確認する
USDJPY内で複数Magic Numberを使い分ける
```

推奨方針：

```text
Step 2E.1：UJ 5ロジック仕様整理
Step 2E.2：UJ 5ロジック単体/統合テスト版コード作成
Step 2E.3：Mock日付テストで各UJロジックを確認
```

## 2026-06-15：EA Step 2E.1 UJ 5ロジック仕様整理

### 目的

Step 2Eでは、USDJPY系の以下5ロジックを設定管理型EAへ追加する。

```text
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

Step 2D.2では、すでに `12_UJ_Short_Core` を設定管理型EAへ統合し、特殊日付条件・GOTO/NORMAL分岐が動作することを確認済み。

Step 2Eでは、残りのUJ系ロジックを追加し、USDJPY内で複数の特殊日付ロジックを扱える構造へ拡張する。

---

# UJ 5ロジック一覧

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic |
|---:|---|---|---|---|---|---:|---:|---:|
| 12 | 12_UJ_Short_Core | USDJPY | Short | 条件分岐 | 14:56 JST | 条件分岐 | 条件分岐 | 12001 |
| 13 | 13_UJ_Fix_MidWeek | USDJPY | Long | 18:04 JST | 22:03 JST | 95 | 95 | 13001 |
| 14 | 14_UJ_Sat_3rd | USDJPY | Short | 20:01 JST | 翌日 03:08 JST | 45 | 70 | 14001 |
| 15 | 15_UJ_Sat_Aug | USDJPY | Short | 19:00 JST | 23:30 JST | 20 | 35 | 15001 |
| 16 | 16_UJ_T10A | USDJPY | Long | 02:58 JST | 09:50 JST | 45 | 110 | 16001 |

---

# 12_UJ_Short_Core

## 基本仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Magic Number | 12001 |
| Lot | 0.01固定 |
| Special Rule | RULE_UJ_SHORT_CORE |

---

## 稼働日条件

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

---

## ゴトー日判定

```text
20日
25日
30日
```

重要仕様：

```text
前倒しゴトー日は未実装
```

メモ：

```text
12_UJ_Short_Core のゴトー日判定は、バックテスト再現性を優先し、初期版ではカレンダー日付の20日・25日・30日のみとする。
前倒しゴトー日は未実装。
必要であれば、後続バージョンで InpUseForwardGotoDay を追加し、別途検証する。
```

---

## GOTOモード

| Item | Value |
|---|---|
| Entry | 09:55 JST |
| Exit | 14:56 JST |
| SL | 20 pips |
| TP | 50 pips |

---

## NORMALモード

| Item | Value |
|---|---|
| Entry | 08:04 JST |
| Exit | 14:56 JST |
| SL | 50 pips |
| TP | なし |

---

# 13_UJ_Fix_MidWeek

## 基本仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Long |
| Magic Number | 13001 |
| Lot | 0.01固定 |
| Entry | 18:04 JST |
| Exit | 22:03 JST |
| SL | 95 pips |
| TP | 95 pips |

---

## 稼働日条件

```text
毎月25日以降
水曜日・木曜日のみ
```

EA条件：

```text
day >= 25
weekday == Wednesday or Thursday
```

曜日番号メモ：

```text
Sunday = 0
Monday = 1
Tuesday = 2
Wednesday = 3
Thursday = 4
Friday = 5
Saturday = 6
```

---

## 停止条件

現時点のStep 2Eでは、指標停止はまだ実装しない。

本来のバックテストでは、UJ共通の重要イベントフィルター対象。

```text
US CPI
US NFP
FOMC
BOJ
年末年始
```

ただし、EA開発ステップ上は、指標停止は後続Stepで追加する。

```text
Step 4：指標停止・年末年始停止追加
```

---

# 14_UJ_Sat_3rd

## 基本仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Magic Number | 14001 |
| Lot | 0.01固定 |
| Entry | 20:01 JST |
| Exit | 翌日 03:08 JST |
| SL | 45 pips |
| TP | 70 pips |

---

## 稼働日条件

```text
毎月3日のみ
```

EA条件：

```text
day == 3
```

---

## 停止条件

現時点のStep 2Eでは、指標停止はまだ実装しない。

本来のバックテストでは、UJ共通の重要イベントフィルター対象。

```text
US CPI
US NFP
FOMC
BOJ
年末年始
```

---

# 15_UJ_Sat_Aug

## 基本仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Magic Number | 15001 |
| Lot | 0.01固定 |
| Entry | 19:00 JST |
| Exit | 23:30 JST |
| SL | 20 pips |
| TP | 35 pips |

---

## 稼働日条件

```text
8月1日〜10日のみ
```

EA条件：

```text
month == 8
day <= 10
```

---

## 停止条件

現時点のStep 2Eでは、指標停止はまだ実装しない。

本来のバックテストでは、UJ共通の重要イベントフィルター対象。

```text
US CPI
US NFP
FOMC
BOJ
年末年始
```

---

# 16_UJ_T10A

## 基本仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Long |
| Magic Number | 16001 |
| Lot | 0.01固定 |
| Entry | 02:58 JST |
| Exit | 09:50 JST |
| SL | 45 pips |
| TP | 110 pips |

---

## 稼働日条件

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

## 停止条件

現時点のStep 2Eでは、指標停止はまだ実装しない。

本来のバックテストでは、16_UJ_T10A は以下の停止条件。

```text
年末年始
BOJ
```

ただし、EA開発ステップ上は、指標停止は後続Stepで追加する。

```text
Step 4：指標停止・年末年始停止追加
```

---

# Step 2E 実装方針

## 追加するSpecial Rule

Step 2D.2では、以下を追加済み。

```text
RULE_UJ_SHORT_CORE
```

Step 2Eでは、UJ系ロジック用に以下の特殊ルールを追加する。

```text
RULE_UJ_FIX_MIDWEEK
RULE_UJ_SAT_3RD
RULE_UJ_SAT_AUG
RULE_UJ_T10A
```

想定：

```text
RULE_UJ_SHORT_CORE    → 12_UJ_Short_Core
RULE_UJ_FIX_MIDWEEK  → 13_UJ_Fix_MidWeek
RULE_UJ_SAT_3RD      → 14_UJ_Sat_3rd
RULE_UJ_SAT_AUG      → 15_UJ_Sat_Aug
RULE_UJ_T10A         → 16_UJ_T10A
```

---

# Step 2E テスト方針

Step 2Eでは、まずUJだけONにしてテストする。

```text
既存8ロジックはOFF
UJ 5ロジックのみON
```

---

## テスト方法

Step 2D.1と同じく、疑似JST日時を使って日付条件を確認する。

共通設定：

```text
InpTestMode = true
InpUseMockJstDateTime = true
InpUseTestTimes = false
```

エントリーさせるテストでは、Mock時刻を本来のEntry時刻に合わせる。

---

# UJ 5ロジック Mock日付テスト一覧

| No | Strategy | Mock DateTime JST | 期待結果 |
|---:|---|---|---|
| 12-1 | 12_UJ_Short_Core GOTO | 2026-02-20 09:55 | USDJPY Short / Mode=GOTO |
| 12-2 | 12_UJ_Short_Core NORMAL | 2026-06-23 08:04 | USDJPY Short / Mode=NORMAL |
| 13-1 | 13_UJ_Fix_MidWeek 水曜 | 2026-06-25 18:04 | USDJPY Long |
| 13-2 | 13_UJ_Fix_MidWeek 25日未満停止 | 2026-06-24 18:04 | Entryしない |
| 14-1 | 14_UJ_Sat_3rd | 2026-06-03 20:01 | USDJPY Short |
| 14-2 | 14_UJ_Sat_3rd 3日以外停止 | 2026-06-04 20:01 | Entryしない |
| 15-1 | 15_UJ_Sat_Aug | 2026-08-05 19:00 | USDJPY Short |
| 15-2 | 15_UJ_Sat_Aug 8月以外停止 | 2026-07-05 19:00 | Entryしない |
| 15-3 | 15_UJ_Sat_Aug 11日以降停止 | 2026-08-11 19:00 | Entryしない |
| 16-1 | 16_UJ_T10A | 2026-07-10 02:58 | USDJPY Long |
| 16-2 | 16_UJ_T10A 10日以外停止 | 2026-07-11 02:58 | Entryしない |
| 16-3 | 16_UJ_T10A 水曜停止 | 2026-06-10 02:58 | Entryしない |

---

## 注意：13_UJ_Fix_MidWeek のテスト日

`13_UJ_Fix_MidWeek` は「25日以降の水・木」条件。

テスト日には、25日以降かつ水曜または木曜の日付を使う。

例：

```text
2026-06-25 18:04
```

この日付は木曜日想定。

---

## 注意：16_UJ_T10A の水曜停止

`16_UJ_T10A` は10日でも水曜日なら停止。

水曜停止テストでは、10日かつ水曜日の日付を使う。

例：

```text
2026-06-10 02:58
```

期待結果：

```text
Entryしない
```

---

# Step 2E 判定基準

以下が確認できれば、Step 2Eは合格。

```text
12_UJ_Short_Core GOTOがEntryする
12_UJ_Short_Core NORMALがEntryする
13_UJ_Fix_MidWeekが条件日にEntryする
13_UJ_Fix_MidWeekが25日未満で停止する
14_UJ_Sat_3rdが3日にEntryする
14_UJ_Sat_3rdが3日以外で停止する
15_UJ_Sat_Augが8月1〜10日にEntryする
15_UJ_Sat_Augが8月以外で停止する
15_UJ_Sat_Augが8月11日以降で停止する
16_UJ_T10Aが10日・水曜以外でEntryする
16_UJ_T10Aが10日以外で停止する
16_UJ_T10Aが水曜の10日で停止する
```

---

# Step 2Eではまだ実装しないもの

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

これらは後続Stepで追加する。

## 2026-06-15：EA Step 2E UJ 5ロジック対応テスト完了

### 対象EA

```text
time_entry_step2e2_uj_5logic_test.mq5
time_entry_step2e2_uj_5logic_test_fix1.mq5
```

### 対象ロジック

Step 2Eでは、USDJPY系の以下5ロジックを対象にした。

```text
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
16_UJ_T10A
```

---

## Step 2E の目的

Step 2Dでは、`12_UJ_Short_Core` の特殊日付条件とGOTO/NORMAL分岐を確認した。

Step 2Eでは、USDJPY系の5ロジックをまとめてEA化し、以下を確認した。

```text
USDJPY内で複数ロジックを管理できるか
Magic Numberをロジック別に分けられるか
複数の日付条件ロジックを扱えるか
Long / Shortを混在できるか
TPあり / TPなしを混在できるか
日またぎ決済を正しく扱えるか
```

---

## UJ 5ロジック仕様

| No | Strategy | Pair | Direction | Entry | Exit | SL | TP | Magic |
|---:|---|---|---|---|---|---:|---:|---:|
| 12 | 12_UJ_Short_Core | USDJPY | Short | 条件分岐 | 14:56 JST | 条件分岐 | 条件分岐 | 12001 |
| 13 | 13_UJ_Fix_MidWeek | USDJPY | Long | 18:04 JST | 22:03 JST | 95 | 95 | 13001 |
| 14 | 14_UJ_Sat_3rd | USDJPY | Short | 20:01 JST | 翌日 03:08 JST | 45 | 70 | 14001 |
| 15 | 15_UJ_Sat_Aug | USDJPY | Short | 19:00 JST | 23:30 JST | 20 | 35 | 15001 |
| 16 | 16_UJ_T10A | USDJPY | Long | 02:58 JST | 09:50 JST | 45 | 110 | 16001 |

---

## 12_UJ_Short_Core 仕様

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

メモ：

```text
12_UJ_Short_Core のゴトー日判定は、バックテスト再現性を優先し、初期版ではカレンダー日付の20日・25日・30日のみとする。
前倒しゴトー日は未実装。
必要であれば、後続バージョンで InpUseForwardGotoDay を追加し、別途検証する。
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

## 13_UJ_Fix_MidWeek 仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Long |
| Entry | 18:04 JST |
| Exit | 22:03 JST |
| SL | 95 pips |
| TP | 95 pips |
| Magic Number | 13001 |

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

## 14_UJ_Sat_3rd 仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Entry | 20:01 JST |
| Exit | 翌日 03:08 JST |
| SL | 45 pips |
| TP | 70 pips |
| Magic Number | 14001 |

稼働条件：

```text
毎月3日のみ
```

EA条件：

```text
day == 3
```

---

## 15_UJ_Sat_Aug 仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Short |
| Entry | 19:00 JST |
| Exit | 23:30 JST |
| SL | 20 pips |
| TP | 35 pips |
| Magic Number | 15001 |

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

## 16_UJ_T10A 仕様

| Item | Value |
|---|---|
| Pair | USDJPY |
| Direction | Long |
| Entry | 02:58 JST |
| Exit | 09:50 JST |
| SL | 45 pips |
| TP | 110 pips |
| Magic Number | 16001 |

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

## Skipログ制御

Step 2E.2では、エキスパートタブがログで埋まらないよう、以下のinputを追加した。

```text
InpPrintSkipLogs = false
```

これにより、通常時は以下のログを非表示にできる。

```text
Skip entry: already entered today
Skip entry: position already exists
```

必要な場合のみ、`InpPrintSkipLogs = true` にして原因確認できるようにした。

停止理由ログについては、テスト時に確認しやすいよう以下で制御する。

```text
InpPrintRuleRejectLogs = true
```

---

## Step 2E.2 初回テスト

### テスト条件

共通設定：

```text
InpTestMode = true
InpUseMockJstDateTime = true
InpPrintSkipLogs = false
InpPrintRuleRejectLogs = true
```

各テストでは、対象ロジックのみ `true`、他ロジックは `false` にした。

---

## テスト結果一覧

| No | Strategy | Mock DateTime JST | 期待結果 | 結果 |
|---:|---|---|---|---|
| 12-1 | 12_UJ_Short_Core GOTO | 2026-02-20 09:55 | USDJPY Short / Mode=GOTO | OK |
| 12-2 | 12_UJ_Short_Core NORMAL | 2026-06-23 08:04 | USDJPY Short / Mode=NORMAL | OK |
| 13-1 | 13_UJ_Fix_MidWeek | 2026-06-25 18:04 | USDJPY Long | OK |
| 13-2 | 13_UJ_Fix_MidWeek 停止 | 2026-06-24 18:04 | Entryしない | OK |
| 14-1 | 14_UJ_Sat_3rd | 2026-06-03 20:01 | USDJPY Short | OK。ただし即Time exit発生 |
| 14-2 | 14_UJ_Sat_3rd 停止 | 2026-06-04 20:01 | Entryしない | OK |
| 15-1 | 15_UJ_Sat_Aug | 2026-08-05 19:00 | USDJPY Short | OK |
| 15-2 | 15_UJ_Sat_Aug 停止 | 2026-07-05 19:00 | Entryしない | OK |
| 15-3 | 15_UJ_Sat_Aug 停止 | 2026-08-11 19:00 | Entryしない | OK |
| 16-1 | 16_UJ_T10A | 2026-07-10 02:58 | USDJPY Long | OK |
| 16-2 | 16_UJ_T10A 停止 | 2026-07-11 02:58 | Entryしない | OK |
| 16-3 | 16_UJ_T10A 水曜停止 | 2026-06-10 02:58 | Entryしない | OK |

---

## 発見した問題：14_UJ_Sat_3rdの日またぎ決済

`14_UJ_Sat_3rd` は以下の仕様。

```text
Entry：20:01 JST
Exit：翌日 03:08 JST
```

初回コードでは、Exit判定が単純に以下の考え方だった。

```text
現在時刻 >= Exit時刻
```

そのため、Mock時刻が `20:01` のとき、`03:08` はすでに過ぎていると判定され、エントリー直後に `Time exit success` が発生した。

これは日またぎ決済ロジックのバグと判断。

---

## 修正内容：Step 2E.2 FIX1

修正版EA：

```text
time_entry_step2e2_uj_5logic_test_fix1.mq5
```

修正内容：

```text
日またぎExit判定を追加
Entry時刻よりExit時刻が早い場合は、翌日決済として扱う
Entry日の夜には即決済しない
```

追加した考え方：

```text
Entry 20:01
Exit 翌日 03:08

この場合、20:01直後にはExitしない。
翌日03:08以降にExitする。
```

---

## Step 2E.2 FIX1 再テスト

### 再テスト対象

```text
14-1  2026-06-03 20:01  14_UJ_Sat_3rd
```

設定：

```text
InpEnable_12_UJ_Short_Core = false
InpEnable_13_UJ_Fix_MidWeek = false
InpEnable_14_UJ_Sat_3rd = true
InpEnable_15_UJ_Sat_Aug = false
InpEnable_16_UJ_T10A = false
```

Mock日時：

```text
InpMockYear = 2026
InpMockMonth = 6
InpMockDay = 3
InpMockHour = 20
InpMockMinute = 1
```

期待結果：

```text
SELL entry success
取引タブに USDJPY sell 0.01 が残る
Time exit success が即時には出ない
```

結果：

```text
OK
```

---

## Step 2E 判定

Step 2Eは合格。

最終判定：

```text
Step 2E.2 初回：日付条件テストはOK。ただし14_UJ_Sat_3rdの日またぎ決済バグあり
Step 2E.2 FIX1：14_UJ_Sat_3rdの日またぎExit修正OK
```

確認済み：

```text
12_UJ_Short_Core：OK
13_UJ_Fix_MidWeek：OK
14_UJ_Sat_3rd：OK（日またぎExit修正済み）
15_UJ_Sat_Aug：OK
16_UJ_T10A：OK
```

---

## 注意点

Step 2Eはまだ検証用EAであり、本番運用には使用しない。

未実装の機能：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
既存8ロジックとの完全統合
```

また、同じMock日付で再テストする場合は、Global Variableが残るため、必要に応じてF3から以下のような変数を削除する。

```text
TE_STEP2E2_FIX1_12_UJ_Short_Core_USDJPY_12001_日付
TE_STEP2E2_FIX1_13_UJ_Fix_MidWeek_USDJPY_13001_日付
TE_STEP2E2_FIX1_14_UJ_Sat_3rd_USDJPY_14001_日付
TE_STEP2E2_FIX1_15_UJ_Sat_Aug_USDJPY_15001_日付
TE_STEP2E2_FIX1_16_UJ_T10A_USDJPY_16001_日付
```

---

## 次にやること

次は Step 2F として、以下を統合する。

```text
Step 2Cの既存8ロジック
+
Step 2EのUJ 5ロジック
```

合計：

```text
13ロジック
```

Step 2Fの目的：

```text
既存8ロジックとUJ5ロジックを1つの設定管理型EAへ統合する
GBPAUD / GBPJPY / EURAUD / USDJPY を同時に扱う
通常曜日系ロジックと特殊日付系ロジックを共存させる
日またぎExit修正を統合EAにも反映する
Magic Numberを13ロジックで分けて管理する
```

推奨フロー：

```text
Step 2F.1：13ロジック統合仕様整理
Step 2F.2：13ロジック統合EAコード作成
Step 2F.3：既存8ロジック + UJ5ロジックの代表テスト
```
