# DEVELOPMENT_LOG_EA.md

# Time Entry Portfolio Lab EA開発ログ

## 目的

この開発ログでは、時間固定エントリーポートフォリオをMT5 EA化するための開発内容を記録する。

EA化は、まずデモ口座で段階的に実施し、挙動確認後にリアル口座へ移行する。

---

# EA化方針

## 実装方式

PineConnectorではなく、MQL5でEAを直接作成する方針とする。

理由：

```text
TradingViewのシグナル送信型ではなく、
MT5内で時間指定・決済・ロット管理・指標停止・ATRフィルタを完結させる方が安定するため。
```

EAに必要な主な機能：

```text
1. 時間指定エントリー
2. 時間指定決済
3. SL / TP設定
4. 曜日・日付条件
5. 年末年始停止
6. 指標日停止
7. Global H1 ATR P70フィルタ
8. 週次複利・損失額固定ロット計算
9. Magic Numberによるロジック別管理
10. 複数通貨ペア・複数ロジック対応
```

---

# EA開発ステップ

以下の6ステップで進める。

```text
Step 1：1ロジックだけEA化
Step 2：複数ロジック対応
Step 3：Global H1 ATR P70追加
Step 4：指標停止追加
Step 5：週次複利ロット管理追加
Step 6：全28ロジック化
```

最初から全機能を入れず、段階的に確認する。

---

# Step 1 方針

## 目的

Step 1では、勝てるかどうかではなく、EAの基本挙動確認を目的とする。

確認項目：

```text
指定曜日・指定時刻にエントリーするか
指定時刻に決済するか
SL/TPが正しく入るか
Magic Numberでポジション管理できるか
JST時間とMT5サーバー時間のズレを制御できるか
非JPYペアのpip計算が正しくできるか
```

---

# Step 1 対象ロジック

当初候補として 13_UJ_Fix_MidWeek を検討したが、出現回数が少なく、挙動確認に時間がかかる可能性がある。

そのため、Step 1の候補は以下とする。

```text
22_GA_C_2
```

---

## 22_GA_C_2 仕様

| Item | Value |
|---|---|
| Strategy | 22_GA_C_2 |
| Pair | GBPAUD |
| Direction | Long |
| Entry Day | Thursday |
| Entry Time | 16:56 JST |
| Exit Time | Next day 01:15 JST |
| SL | 70 pips |
| TP | 80 pips |
| Spread | entry_adjust方式を前提 |
| Lot | Step 1では固定ロット |
| ATR Filter | Step 1ではなし |
| Event Filter | Step 1ではなし |
| Weekly Compounding | Step 1ではなし |

---

# Step 1 実装方針

Step 1では、あえて機能を絞る。

入れる機能：

```text
GBPAUD Long
木曜16:56 JST エントリー
翌日01:15 JST 決済
SL 70pips
TP 80pips
固定ロット
Magic Number管理
1ポジションのみ
```

入れない機能：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
複数ロジック管理
全28ロジック
```

これにより、バグが出た場合に原因を特定しやすくする。

---

# Step 1 確認項目

デモ口座で以下を確認する。

```text
1. EAをGBPAUDチャートに適用できるか
2. 指定時刻に1回だけエントリーするか
3. 同じ日に重複エントリーしないか
4. SL/TPが正しい価格に入るか
5. 翌日01:15 JSTに時間決済されるか
6. TP/SL到達時は時間決済前に正しく終了するか
7. Magic Numberで対象ポジションだけを管理できるか
8. MT5サーバー時間とJSTのズレが正しく処理されているか
9. ログにエントリー判定・スキップ理由・決済理由が出るか
```

---

# 今後の予定

Step 1で基本挙動が確認できたら、次に進む。

```text
Step 2：複数ロジック対応
Step 3：Global H1 ATR P70追加
Step 4：指標停止追加
Step 5：週次複利ロット管理追加
Step 6：全28ロジック化
```

リアル口座への移行は、デモ口座で十分に挙動確認した後に行う。

## 2026-06-15：EA Step 1A 22_GA_C_2 単体テスト完了

### 対象EA

```text
time_entry_22_GA_C_2_step1a.mq5
```

### 対象ロジック

```text
22_GA_C_2
```

| Item | Value |
|---|---|
| Pair | GBPAUD |
| Direction | Long |
| Entry | 木曜 16:56 JST |
| Exit | 金曜 01:15 JST |
| SL | 70 pips |
| TP | 80 pips |
| Lot | 0.01固定 |
| Magic Number | 22002 |
| JST Offset | MT5サーバー時間 + 6時間 |
| ATR Filter | なし |
| Event Filter | なし |
| Weekly Compounding | なし |

---

### Step 1A の目的

Step 1Aでは、勝ち負けではなく、EAの基本動作確認を目的とした。

確認対象は以下。

```text
指定時刻にエントリーするか
指定時刻に時間決済するか
SL/TPが正しく入るか
同日重複エントリーを防止できるか
Magic Numberで対象ポジションを管理できるか
GBPAUDの非JPYペアでpip計算が機能するか
MT5サーバー時間とJSTのズレをinputで制御できるか
```

---

### 実施内容

MetaEditorで新規EAを作成し、以下のファイル名で保存。

```text
time_entry_22_GA_C_2_step1a.mq5
```

当初、`Scripts` フォルダに保存されていたため、MT5ナビゲーターの「エキスパートアドバイザ」に表示されなかった。

その後、保存先を以下へ変更。

```text
MQL5/Experts/
```

再コンパイル後、MT5ナビゲーターにEAが表示されることを確認。

---

### コンパイル結果

```text
0 errors, 0 warnings
```

コンパイルは正常に完了。

---

### チャート適用

OANDA MT5デモ口座で、以下のチャートにEAを適用。

```text
GBPAUD
```

チャート右上にEA名と自動売買アイコンが表示されることを確認。

---

### 初期化ログ

エキスパートログで以下を確認。

```text
EA initialized.
Symbol=GBPAUD
ExpectedSymbol=GBPAUD
JST Offset Hours=6
MagicNumber=22002
FixedLot=0.01
automated trading is enabled
```

これにより、EAが正常に起動し、自動売買も許可されていることを確認。

---

### エントリーテスト

実際の木曜16:56 JSTを待たず、テスト用にEntry時刻を数分後へ変更し、デモ口座で強制エントリーテストを実施。

結果、指定時刻にGBPAUDのBuyポジションが建つことを確認。

エキスパートログ：

```text
BUY entry success. Lot=0.01, Ask=..., SL=..., TP=...
```

また、エントリー後に以下のログが複数回表示された。

```text
skip entry: already entered today
```

これは、同日重複エントリー防止が正常に機能していることを示す。

---

### 時間決済テスト

エントリー後、Exit時刻を数分後へ変更し、時間決済テストを実施。

結果、指定時刻にポジションが決済されることを確認。

エキスパートログ：

```text
Time exit success
```

---

### Step 1A 判定

Step 1Aは合格。

確認できた項目：

```text
GBPAUDチャートでEAが起動する
自動売買が有効になっている
指定時刻にBuyエントリーする
SL/TPが設定される
同日重複エントリーを防止する
指定時刻に時間決済する
Magic Numberで対象ポジションを管理する
非JPYペアのpip計算が機能している
```

---

### 注意点・今後の改善候補

現在のStep 1Aでは、エントリー時間帯中に `skip entry: already entered today` が複数回ログ出力される。

これは仕様上問題ないが、実運用ではログが多くなるため、今後以下を検討する。

```text
skip系ログを1回だけ表示する
InpPrintDebug=false の時はskip系ログを抑制する
ログ出力レベルを分ける
```

また、Step 1Aでは以下は未実装。

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
複数ロジック管理
全28ロジック対応
```

---

### 次にやること

次は Step 1B として、以下の単体EAを作成する。

```text
5_GJ_Port_Log2
```

仕様：

| Item | Value |
|---|---|
| Pair | GBPJPY |
| Direction | Short |
| Entry | 火・木・金 09:55 JST |
| Exit | 当日 23:55 JST |
| SL | 90 pips |
| TP | なし |
| Lot | 0.01固定 |
| Magic Number | 50002 |
| ATR Filter | なし |
| Event Filter | なし |
| Weekly Compounding | なし |

Step 1Bの目的：

```text
JPYペアのpip計算確認
Shortエントリー確認
TPなしロジック確認
当日時間決済確認
複数曜日エントリー条件確認
```

Step 1Bが完了したら、Step 1Cとして以下に進む。

```text
22_GA_C_2 と 5_GJ_Port_Log2 の2戦略統合EA
```

## 2026-06-15：EA Step 1B 5_GJ_Port_Log2 単体テスト完了

### 対象EA

```text
time_entry_5_GJ_Port_Log2_step1b_testable.mq5
```

### 対象ロジック

```text
5_GJ_Port_Log2
```

| Item | Value |
|---|---|
| Pair | GBPJPY |
| Direction | Short |
| Entry | 火・木・金 09:55 JST |
| Exit | 当日 23:55 JST |
| SL | 90 pips |
| TP | なし |
| Lot | 0.01固定 |
| Magic Number | 50002 |
| JST Offset | MT5サーバー時間 + 6時間 |
| ATR Filter | なし |
| Event Filter | なし |
| Weekly Compounding | なし |

---

### Step 1B の目的

Step 1Bでは、5_GJ_Port_Log2 単体EAの基本動作確認を行った。

主な確認対象は以下。

```text
GBPJPYのJPYペアpip計算
Shortエントリー
TPなし発注
SL設定
当日時間決済
複数曜日エントリー条件
Magic Number管理
同日重複エントリー防止
```

---

### テスト用変更

通常仕様では、5_GJ_Port_Log2 は火・木・金のみエントリー対象。

ただし、テストを任意の日に実施できるよう、以下のinputを追加したテスト版を使用した。

```text
InpTestModeIgnoreWeekday = true
```

これにより、火・木・金以外の日でも、指定したEntry時刻でテストエントリーできるようにした。

---

### コンパイル結果

```text
0 errors, 0 warnings
```

コンパイルは正常に完了。

---

### チャート適用

OANDA MT5デモ口座で、以下のチャートにEAを適用。

```text
GBPJPY
```

チャート右上にEA名と自動売買アイコンが表示されることを確認。

---

### 初期化ログ

エキスパートログで以下を確認。

```text
EA initialized.
Symbol=GBPJPY
ExpectedSymbol=GBPJPY
JST Offset Hours=6
MagicNumber=50002
FixedLot=0.01
Strategy=5_GJ_Port_Log2
Direction=Short
TP=None
TestModeIgnoreWeekday=true
```

EAが正常に起動し、テストモードも有効になっていることを確認。

---

### エントリーテスト

実際のエントリー時刻を待たず、テスト用にEntry時刻を数分後へ変更し、デモ口座で強制エントリーテストを実施。

結果、指定時刻にGBPJPYのSellポジションが建つことを確認。

エキスパートログ：

```text
SELL entry success. Lot=0.01, Bid=..., SL=..., TP=None
```

---

### ポジション確認

MT5下部の「取引」タブで以下を確認。

```text
銘柄：GBPJPY
タイプ：sell
数量：0.01
S/L：設定あり
T/P：なし
```

これにより、以下を確認できた。

```text
GBPJPY Short 0.01 が建った
SL 90pips が設定された
TPなしで発注された
```

---

### 同日重複エントリー防止

テスト中、EAを削除して再度チャートへ入れ直した際、エントリーがスキップされた。

原因は、Global Variableに「同日エントリー済み」の記録が残っていたため。

該当仕様：

```text
Global Variableで同日重複エントリーを防止
EAをチャートから削除してもGlobal Variableは残る
```

再テスト時は、MT5で以下を実施。

```text
F3
↓
グローバル変数
↓
TE_5_GJ_PORT_LOG2_STEP1B_TESTABLE_GBPJPY_50002_日付
↓
削除
```

これにより、同日中でも再テストが可能になった。

---

### 時間決済テスト

エントリー後、Exit時刻を数分後へ変更し、時間決済テストを実施。

結果、指定時刻にポジションが決済されることを確認。

エキスパートログ：

```text
Time exit success
```

---

### Step 1B 判定

Step 1Bは合格。

確認できた項目：

```text
GBPJPYチャートでEAが起動する
指定時刻にSellエントリーする
GBPJPY Short 0.01が建つ
SL 90pipsが設定される
TPなしで発注される
指定時刻に時間決済する
Magic Numberで対象ポジションを管理する
同日重複エントリーを防止する
Global Variable削除で再テスト可能
JPYペアのpip計算が機能している
```

---

### 注意点・今後の改善候補

Step 1Bテスト版では、以下のinputを使用した。

```text
InpTestModeIgnoreWeekday = true
```

本番運用時は必ず以下に戻す。

```text
InpTestModeIgnoreWeekday = false
```

また、テスト後は本来設定に戻す。

```text
InpEntryHourJST = 9
InpEntryMinuteJST = 55
InpExitHourJST = 23
InpExitMinuteJST = 55
InpMagicNumber = 50002
```

---

### 次にやること

次は Step 1C として、以下の2戦略を1つのEAに統合する。

```text
22_GA_C_2
5_GJ_Port_Log2
```

Step 1Cの目的：

```text
複数戦略を同一EA内で管理できるか
複数通貨ペアを扱えるか
Long/Shortを同時に扱えるか
TPあり/TPなしを同時に扱えるか
Magic Numberをロジック別に分けて管理できるか
Global Variableでロジック別に同日重複エントリーを防止できるか
```

Step 1Cでは、まだ以下は実装しない。

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

## 2026-06-15：EA Step 1C 2戦略統合EAテスト完了

### 対象EA

```text
time_entry_step1c_GA_GJ_2strategies.mq5
```

### 対象ロジック

Step 1Cでは、以下の2戦略を1つのEAに統合して動作確認した。

```text
22_GA_C_2
5_GJ_Port_Log2
```

---

## 22_GA_C_2 仕様

| Item | Value |
|---|---|
| Pair | GBPAUD |
| Direction | Long |
| Entry | 木曜 16:56 JST |
| Exit | 金曜 01:15 JST |
| SL | 70 pips |
| TP | 80 pips |
| Lot | 0.01固定 |
| Magic Number | 22002 |
| ATR Filter | なし |
| Event Filter | なし |
| Weekly Compounding | なし |

---

## 5_GJ_Port_Log2 仕様

| Item | Value |
|---|---|
| Pair | GBPJPY |
| Direction | Short |
| Entry | 火・木・金 09:55 JST |
| Exit | 当日 23:55 JST |
| SL | 90 pips |
| TP | なし |
| Lot | 0.01固定 |
| Magic Number | 50002 |
| ATR Filter | なし |
| Event Filter | なし |
| Weekly Compounding | なし |

---

## Step 1C の目的

Step 1Cでは、2戦略を1つのEA内で管理できるかを確認した。

確認対象は以下。

```text
複数戦略を同一EA内で管理できるか
複数通貨ペアを扱えるか
Long / Short を同時に扱えるか
TPあり / TPなし を同時に扱えるか
Magic Numberをロジック別に分けて管理できるか
Global Variableでロジック別に同日重複エントリーを防止できるか
```

---

## テスト用設定

Step 1Cでは、任意の日・任意の時刻にテストできるよう、以下のテスト用inputを使用した。

```text
InpTestMode = true
InpTestModeIgnoreEntryWeekday = true
InpTestModeIgnoreExitWeekday = true
```

これにより、本来の曜日条件・決済曜日条件を一時的に無視して、数分後のEntry / Exit時刻へ変更してテストした。

---

## コンパイル結果

```text
0 errors, 0 warnings
```

コンパイルは正常に完了。

---

## チャート適用

EAは1つのチャートにのみ適用する方針とした。

```text
GBPAUD / GBPJPY の両方にEAを入れると重複管理になるためNG
```

また、MT5の気配値表示に以下の2銘柄を表示しておく必要がある。

```text
GBPAUD
GBPJPY
```

---

## テスト結果

Step 1CのテストはOK。

確認できた内容：

```text
22_GA_C_2 のBuyエントリー成功
22_GA_C_2 のSL/TP設定成功
22_GA_C_2 の時間決済成功

5_GJ_Port_Log2 のSellエントリー成功
5_GJ_Port_Log2 のSL設定成功
5_GJ_Port_Log2 のTPなし発注成功
5_GJ_Port_Log2 の時間決済成功
```

エキスパートログで、以下のようなログを確認。

```text
[Step1C 22_GA_C_2] BUY entry success...
[Step1C 5_GJ_Port_Log2] SELL entry success...
[Step1C 22_GA_C_2] Time exit success...
[Step1C 5_GJ_Port_Log2] Time exit success...
```

---

## Step 1C 判定

Step 1Cは合格。

確認できた項目：

```text
1つのEAで2戦略を管理できる
GBPAUDとGBPJPYの複数通貨ペアを扱える
LongとShortを同一EA内で扱える
TPありとTPなしを同一EA内で扱える
Magic Numberでロジック別に管理できる
Global Variableでロジック別に同日重複エントリーを防止できる
時間エントリーと時間決済が両戦略で機能する
```

---

## 注意点

Step 1Cはまだ検証用EAであり、本番運用には使用しない。

未実装の機能：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
全28ロジック対応
```

また、テスト後に本来仕様へ戻す場合は以下にする。

```text
InpTestMode = false
InpTestModeIgnoreEntryWeekday = false
InpTestModeIgnoreExitWeekday = false
```

---

## 次にやること

次は Step 2 に進む。

Step 2では、Step 1Cのような個別関数ベタ書きから、複数ロジックを管理しやすい構造へ整理する。

予定：

```text
Step 2A：複数ロジック対応の仕様設計
Step 2B：2戦略を設定管理型にリファクタリング
Step 2C：5〜8ロジック程度まで増やせる形にする
```

Step 2以降の記録は、新規ファイル `DEVELOPMENT_LOG_EA_2.md` に記録する。
