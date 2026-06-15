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
