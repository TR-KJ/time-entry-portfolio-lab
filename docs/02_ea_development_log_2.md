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
