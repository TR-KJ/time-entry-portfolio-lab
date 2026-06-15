# Time Entry Portfolio Lab EA開発ログ 2

## 2026-06-15：EA Step 2A 複数ロジック対応 仕様設計

### 背景

Step 1では、EA化の土台確認として以下を実施した。

```text
Step 1A：22_GA_C_2 単体EA
Step 1B：5_GJ_Port_Log2 単体EA
Step 1C：22_GA_C_2 + 5_GJ_Port_Log2 の2戦略統合EA
```

Step 1Cにより、1つのEA内で以下が可能であることを確認した。

```text
複数戦略管理
複数通貨ペア管理
Long / Short 管理
TPあり / TPなし 管理
Magic Number別管理
Global Variableによる同日重複エントリー防止
時間エントリー
時間決済
```

ただし、Step 1Cのコードは、2戦略を個別関数でベタ書きしているため、全28ロジックへ拡張するには管理が難しい。

そのため、Step 2では、複数ロジックを扱いやすい構造へ整理する。

---

## Step 2A の目的

Step 2Aでは、コード作成前に、複数ロジック対応EAの基本設計を決める。

目的：

```text
全28ロジック化に向けて、ロジック定義を管理しやすい構造にする
個別関数ベタ書きを減らす
エントリー判定・決済判定・注文処理を共通化する
Magic Number、Symbol、Direction、SL、TP、時刻条件を一元管理する
後続のATRフィルタ、指標停止、週次複利を追加しやすくする
```

---

## Step 2 の開発方針

Step 2は以下の流れで進める。

```text
Step 2A：複数ロジック対応の仕様設計
Step 2B：2戦略を設定管理型にリファクタリング
Step 2C：5〜8ロジック程度まで増やせる形にする
```

Step 2では、まだ以下は実装しない。

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

これらはStep 3以降で追加する。

---

## Step 2B で扱う対象ロジック

Step 2Bでは、まずStep 1Cと同じ2戦略を対象にする。

```text
22_GA_C_2
5_GJ_Port_Log2
```

理由：

```text
Step 1Cで動作確認済み
Long / Short が含まれる
TPあり / TPなし が含まれる
非JPYペア / JPYペア が含まれる
翌日決済 / 当日決済 が含まれる
```

この2戦略で設定管理型の構造を作り、Step 1Cと同じ動作になるか確認する。

---

## ロジック定義項目

各ロジックは、以下の情報を持つ。

| Field | Meaning |
|---|---|
| Enabled | ロジック有効/無効 |
| StrategyName | 戦略名 |
| Symbol | 通貨ペア |
| MagicNumber | Magic Number |
| Direction | Long / Short |
| EntryWeekdayMode | 単一曜日 / 複数曜日 / 日付条件など |
| EntryWeekdays | エントリー対象曜日 |
| EntryHourJST | エントリー時刻 時 |
| EntryMinuteJST | エントリー時刻 分 |
| ExitMode | 当日決済 / 翌日決済 / 曜日指定決済 |
| ExitWeekday | 決済曜日 |
| ExitDayOffset | 決済日オフセット |
| ExitHourJST | 決済時刻 時 |
| ExitMinuteJST | 決済時刻 分 |
| SLPips | SL pips |
| TPPips | TP pips。0以下ならTPなし |
| OneEntryPerDay | 同日1回のみ |
| Comment | 注文コメント |

---

## Step 2B の最小仕様

Step 2Bでは、設定管理型にするが、まずは対象を2戦略に限定する。

対象：

```text
22_GA_C_2
5_GJ_Port_Log2
```

共通仕様：

```text
固定ロット 0.01
JST Offset input
Entry Window input
Slippage input
PrintDebug input
Magic Number別管理
Global Variableで同日重複エントリー防止
```

テスト用仕様：

```text
InpTestMode = true / false
InpTestModeIgnoreEntryWeekday = true / false
InpTestModeIgnoreExitWeekday = true / false
```

---

## 22_GA_C_2 設定

| Field | Value |
|---|---|
| Enabled | true |
| StrategyName | 22_GA_C_2 |
| Symbol | GBPAUD |
| MagicNumber | 22002 |
| Direction | Long |
| EntryWeekdays | Thursday |
| EntryHourJST | 16 |
| EntryMinuteJST | 56 |
| ExitMode | Weekday指定 |
| ExitWeekday | Friday |
| ExitHourJST | 1 |
| ExitMinuteJST | 15 |
| SLPips | 70 |
| TPPips | 80 |
| Comment | 22_GA_C_2_step2 |

---

## 5_GJ_Port_Log2 設定

| Field | Value |
|---|---|
| Enabled | true |
| StrategyName | 5_GJ_Port_Log2 |
| Symbol | GBPJPY |
| MagicNumber | 50002 |
| Direction | Short |
| EntryWeekdays | Tuesday, Thursday, Friday |
| EntryHourJST | 9 |
| EntryMinuteJST | 55 |
| ExitMode | SameDay |
| ExitHourJST | 23 |
| ExitMinuteJST | 55 |
| SLPips | 90 |
| TPPips | 0 |
| Comment | 5_GJ_Port_Log2_step2 |

---

## Step 2B で確認すること

Step 2Bでは、Step 1Cと同じ2戦略を、設定管理型コードで動作確認する。

確認項目：

```text
EAが起動する
GBPAUD / GBPJPY の両方を認識する
22_GA_C_2 がBuyエントリーする
22_GA_C_2 にSL/TPが入る
22_GA_C_2 が時間決済する
5_GJ_Port_Log2 がSellエントリーする
5_GJ_Port_Log2 にSLが入る
5_GJ_Port_Log2 はTPなしで発注される
5_GJ_Port_Log2 が時間決済する
Magic Numberがロジック別に分かれる
Global Variableがロジック別に作成される
同日重複エントリーを防止する
```

---

## Step 2C の予定

Step 2Bが成功したら、Step 2Cでロジック数を増やす。

候補：

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

ただし、Step 2Cでどのロジックを追加するかは、Step 2B完了後に再確認する。

---

## Step 3 以降の予定

Step 2で複数ロジック管理構造が安定したら、次に進む。

```text
Step 3：Global H1 ATR P70フィルタ追加
Step 4：指標停止・年末年始停止追加
Step 5：週次複利・損失額固定ロット計算追加
Step 6：全28ロジック対応
```

最終的には、以下の運用候補をEA化する。

```text
Global H1 ATR P70 + 1.0% risk
```

攻める場合の候補：

```text
Global H1 ATR P70 + 1.5% risk
```

## 2026-06-15：EA Step 2B 設定管理型2戦略EAテスト完了

### 対象EA

```text
time_entry_step2b_config_managed_2strategies.mq5
```

### 対象ロジック

Step 2Bでは、以下の2戦略を設定管理型EAとして実装・テストした。

```text
22_GA_C_2
5_GJ_Port_Log2
```

---

## Step 2B の目的

Step 1Cでは、2戦略を1つのEAに統合したが、コードは戦略ごとの個別関数ベタ書きだった。

Step 2Bでは、今後の多ロジック化に向けて、以下のような設定管理型へ移行した。

```text
StrategyName
StrategyCode
Symbol
MagicNumber
Direction
Entry曜日
Entry時刻
Exit方式
Exit時刻
SL
TP
有効/無効
Comment
```

これにより、エントリー判定・決済判定・注文処理・Magic管理・Global Variable管理を共通化する方針とした。

---

## 実装した主な構造

### StrategyConfig

各ロジックを以下のような構造体で管理。

```text
enabled
strategy_name
strategy_code
symbol
magic
direction
trade_sunday〜trade_saturday
entry_hour
entry_minute
exit_mode
exit_weekday
exit_hour
exit_minute
sl_pips
tp_pips
one_entry_per_day
comment
```

### 共通化した処理

```text
JST時刻変換
pip size判定
lot正規化
SymbolSelect
Entry時刻判定
Exit時刻判定
Long / Short注文
SL / TP設定
TPなし発注
Magic Number別ポジション管理
Global Variableによる同日重複エントリー防止
時間決済
```

---

## 22_GA_C_2 設定

| Field | Value |
|---|---|
| StrategyName | 22_GA_C_2 |
| Symbol | GBPAUD |
| Direction | Long |
| Entry | 木曜 16:56 JST |
| Exit | 金曜 01:15 JST |
| SL | 70 pips |
| TP | 80 pips |
| Magic Number | 22002 |
| Comment | 22_GA_C_2_step2b |

---

## 5_GJ_Port_Log2 設定

| Field | Value |
|---|---|
| StrategyName | 5_GJ_Port_Log2 |
| Symbol | GBPJPY |
| Direction | Short |
| Entry | 火・木・金 09:55 JST |
| Exit | 当日 23:55 JST |
| SL | 90 pips |
| TP | なし |
| Magic Number | 50002 |
| Comment | 5_GJ_Port_Log2_step2b |

---

## テスト用設定

任意の時刻でテストできるよう、以下のinputを使用。

```text
InpTestMode = true
InpTestModeIgnoreEntryWeekday = true
InpTestModeIgnoreExitWeekday = true
InpUseTestTimes = true
```

これにより、両戦略のEntry / Exit時刻を一括でテスト用時刻に上書きできるようにした。

---

## コンパイル結果

```text
0 errors, 0 warnings
```

コンパイルは正常に完了。

---

## テスト結果

Step 2BのテストはOK。

確認できた内容：

```text
EAが正常に起動する
GBPAUD / GBPJPY の両方を認識する
22_GA_C_2 がBuyエントリーする
22_GA_C_2 にSL/TPが入る
22_GA_C_2 が時間決済する
5_GJ_Port_Log2 がSellエントリーする
5_GJ_Port_Log2 にSLが入る
5_GJ_Port_Log2 はTPなしで発注される
5_GJ_Port_Log2 が時間決済する
Magic Numberがロジック別に分かれる
Global Variableがロジック別に作成される
同日重複エントリーを防止する
```

エキスパートログで以下のような出力を確認。

```text
[Step2B 22_GA_C_2] BUY entry success...
[Step2B 5_GJ_Port_Log2] SELL entry success...
[Step2B 22_GA_C_2] Time exit success...
[Step2B 5_GJ_Port_Log2] Time exit success...
```

---

## Step 2B 判定

Step 2Bは合格。

Step 1Cの2戦略ベタ書きEAから、設定管理型EAへの移行に成功した。

これにより、今後の複数ロジック追加に向けた土台ができた。

---

## 注意点

Step 2Bはまだ検証用EAであり、本番運用には使用しない。

未実装の機能：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

また、同じ日に再テストする場合は、Global Variableが残るため、必要に応じてF3から以下のような変数を削除する。

```text
TE_STEP2B_22_GA_C2_GBPAUD_22002_日付
TE_STEP2B_5_GJ_Log2_GBPJPY_50002_日付
```

---

## 次にやること

次は Step 2C として、5〜8ロジック程度まで拡張する。

候補：

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

Step 2Cの目的：

```text
設定管理型EAでロジック数を増やしても安定して動くか確認する
GA / EA / GJ の複数ペアを扱う
Long / Short を複数混在させる
TPあり / TPなしを混在させる
当日決済 / 翌日決済を混在させる
Magic Number管理をさらに確認する
```

Step 2Cでも、まだ以下は実装しない。

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```
