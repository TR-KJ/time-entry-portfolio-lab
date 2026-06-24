# 06_forward_test_operation_guide.md

# フォワードテスト運用ガイド

## 対象

このドキュメントは、28ロジック統合EAのデモ口座フォワードテスト中に使用する運用メモである。

対象EA：

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

対象記録表：

```text
トレード記録表0530_forward_test版.xlsx
```

対象環境：

```text
Windows PC
DELL Inspiron
OANDA MT5 デモ口座
固定0.01lot 初回フォワード
```

---

# 1. フォワードテスト中の基本方針

初回フォワードテストでは、利益・損失の評価よりも、EAの実運用挙動確認を優先する。

確認優先順位：

```text
1. Entry時刻
2. Direction
3. Lot
4. SL / TP
5. Time exit
6. Event Filter
7. ATR Filter
8. Date Rule
9. ログの見やすさ
10. 想定外Entry / 想定外停止の有無
```

初回フォワード設定：

```text
InpLotMode = 0
InpFixedLot = 0.01
InpUseGlobalAtrP70Filter = true
InpUseEventFilter = true
InpEmergencyStop = false
InpTestMode = false
InpUseMockJstDateTime = false
InpUseTestTimes = false
```

---

# 2. トレード記録表の使い方

使用ファイル：

```text
トレード記録表0530_forward_test版.xlsx
```

主に使用するシート：

```text
Forward_Settings
Forward_Trade_Log
Forward_Daily_Check
Forward_Filter_Log
Forward_Weekly_Summary
Forward_MT5_Import
Forward_Dashboard
List_Data
```

---

# 3. Forward_Settings の記入方法

`Forward_Settings` は、フォワードテスト開始時のEA設定を記録するシート。

記録するもの：

```text
EA Version
Account Type
Account ID
Initial Balance
Lot Mode
Fixed Lot
ATR Filter
Event Filter
EmergencyStop
TestMode
MockJST
TestTimes
Operating PC
Start Date
Notes
```

初回推奨値：

```text
EA Version = time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
Account Type = Demo
Lot Mode = Fixed Lot
Fixed Lot = 0.01
ATR Filter = ON
Event Filter = ON
EmergencyStop = false
TestMode = false
MockJST = false
TestTimes = false
Operating PC = DELL Inspiron
```

---

# 4. Forward_Daily_Check の記入方法

`Forward_Daily_Check` は、毎日の稼働確認用。

毎日1回、できれば朝または夜に確認する。

記録項目：

```text
Date
MT5 Running
Auto Trading ON
Connection OK
EA Running
Error Log
Notes
```

記入例：

| Date | MT5 Running | Auto Trading ON | Connection OK | EA Running | Error Log | Notes |
|---|---|---|---|---|---|---|
| 2026-06-24 | OK | OK | OK | OK | none | Date rule rejectのみ。異常なし |

確認すること：

```text
MT5が起動している
OANDAデモ口座にログインしている
自動売買がON
EAがチャート上で稼働している
7通貨ペアの気配値が動いている
エキスパートタブに重大エラーがない
```

重大エラー例：

```text
trade disabled
market closed
invalid volume
invalid stops
OrderSend failed
ATR ERROR
SymbolSelect failed
```

---

# 5. Forward_Trade_Log の記入方法

`Forward_Trade_Log` は、実際にEntry / Exitしたトレードを記録するシート。

MT5口座履歴から分かる情報と、EAログから補足する情報を合わせて記録する。

主な記録項目：

```text
Date
Strategy
Symbol
Direction
Scheduled Entry JST
Actual Entry JST
Lot
SL
TP
Entry Price
Exit JST
Exit Price
Exit Type
P/L
Result
Notes
```

Entryが発生したら記録するもの：

```text
Strategy
Symbol
Direction
Actual Entry JST
Lot
SL
TP
Entry Price
```

Exit後に追記するもの：

```text
Exit JST
Exit Price
Exit Type
P/L
Notes
```

Exit Type の例：

```text
Time exit
SL
TP
Manual
Unknown
```

確認ポイント：

```text
予定時刻どおりEntryしたか
Directionが正しいか
Lotが0.01か
SLが入っているか
TPが仕様どおりか
Time exit successが出たか
```

---

# 6. Forward_Filter_Log の記入方法

`Forward_Filter_Log` は、Entryしなかった理由を記録するシート。

対象：

```text
EVENT REJECT
ATR REJECT
Date rule reject
EmergencyStop
Market closed
その他停止
```

記録項目：

```text
Date
Strategy
Symbol
Scheduled Entry JST
Filter Type
Reason
Log
Expected Stop
Result
Notes
```

記入例：

| Date | Strategy | Symbol | Filter Type | Reason | Result | Notes |
|---|---|---|---|---|---|---|
| 2026-06-24 | 12_UJ_Short_Core | USDJPY | DateRule | Wednesday stop | OK | 水曜停止なので正常 |
| 2026-06-24 | 25_AU_China_Demand | AUDUSD | DateRule | outside AU China date window | OK | 24日は対象外なので正常 |

Filter Type の候補：

```text
Event
ATR
DateRule
EmergencyStop
MarketClosed
Other
```

---

# 7. MT5口座履歴から分かるもの

MT5の口座履歴で確認しやすいもの：

```text
約定時刻
銘柄
売買方向
Lot
約定価格
決済時刻
決済価格
損益
手数料
スワップ
コメント
```

MT5口座履歴だけでは分かりにくいもの：

```text
予定Entry時刻との差
どのStrategyか
Event Filterで止まった理由
ATR Filterで止まった理由
Date Ruleで止まった理由
Time exitなのか、SL/TPなのかの整理
想定外停止の原因
```

そのため、MT5口座履歴とEAエキスパートログを合わせて確認する。

---

# 8. MT5口座履歴のエクスポート方法

## 手順

MT5下部のターミナルから：

```text
口座履歴
↓
右クリック
↓
期間を指定
↓
レポート
↓
HTML または Open XML で保存
```

環境によって表示名は少し異なる。

候補：

```text
レポート
詳細レポート
Open XML
HTML
保存
```

保存したファイルはExcelで開けることが多い。

---

# 9. MT5口座履歴をExcelへ移す方法

## 方法A：Excelで開いてコピー

```text
MT5からHTML / XMLレポートを保存
↓
Excelで開く
↓
必要な行をコピー
↓
トレード記録表の Forward_MT5_Import に貼り付け
```

その後、必要な情報を `Forward_Trade_Log` に転記する。

---

## 方法B：ブラウザ表示からコピー

```text
MT5でレポートを出力
↓
ブラウザで開く
↓
表部分をコピー
↓
Forward_MT5_Import に貼り付け
```

貼り付け後、列が崩れる場合は、Excelの「区切り位置」や貼り付けオプションで調整する。

---

# 10. Forward_MT5_Import の使い方

`Forward_MT5_Import` は、MT5口座履歴を一時的に貼り付けるためのシート。

使い方：

```text
MT5口座履歴を出力
↓
Forward_MT5_Import に貼り付け
↓
Entry / Exit / 損益を確認
↓
Forward_Trade_Log に必要項目を転記
```

注意：

```text
Forward_MT5_Import は生データ置き場
Forward_Trade_Log が整理済みの正式記録
```

---

# 11. Strategy名の確認方法

MT5口座履歴のコメント欄にEAコメントが残る場合、Strategy名の判別に使う。

確認するもの：

```text
Comment
Magic Number
Symbol
Entry Time
Direction
```

Strategyが不明な場合は、以下で照合する。

```text
docs/01_strategy_master_list.md
List_Dataシート
Entry時刻
Symbol
Direction
Magic Number
```

---

# 12. PC再起動後のやることリスト

PC再起動後は、何もしなくてよいとは考えない。  
必ず以下を確認する。

## Windows

```text
□ ACアダプター接続
□ Windowsにログイン済み
□ スリープ設定が「なし」
□ 休止状態が「なし」
□ ネット接続OK
```

## MT5

```text
□ MT5が起動している
□ OANDAデモ口座にログインしている
□ 右下の通信状態OK
□ 気配値が動いている
□ 自動売買ON
```

## EA

```text
□ EAがチャートに残っている
□ EAが稼働している
□ 対象EA名が正しい
□ 28ロジック初期化ログが出ている
□ LOT MODE CHECKログが出ている
```

対象EA：

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

## input確認

特に以下は必ず確認する。

```text
□ InpEmergencyStop = false
□ InpTestMode = false
□ InpUseMockJstDateTime = false
□ InpUseTestTimes = false
□ InpLotMode = 0
□ InpFixedLot = 0.01
□ InpUseGlobalAtrP70Filter = true
□ InpUseEventFilter = true
```

---

# 13. PC再起動後に見るログ

エキスパートタブで以下を確認する。

```text
EA initialized
LOT MODE CHECK. Mode=Fixed Lot
EmergencyStop=false
UseGlobalAtrP70Filter=true
UseEventFilter=true
```

異常ログがないか確認する。

異常ログ例：

```text
trade disabled
market closed
invalid volume
invalid stops
SymbolSelect failed
ATR ERROR
OrderSend failed
```

---

# 14. Windows Update後の復旧手順

Windows Update後は、PCが再起動されている可能性がある。

復旧手順：

```text
Windowsにログイン
↓
MT5を起動
↓
OANDAデモ口座ログイン確認
↓
自動売買ON確認
↓
EAがチャートに残っているか確認
↓
EA input確認
↓
エキスパートタブで初期化ログ確認
↓
Forward_Daily_Checkに記録
```

記録例：

| Date | MT5 Running | Auto Trading ON | Connection OK | EA Running | Error Log | Notes |
|---|---|---|---|---|---|---|
| 2026-06-27 | OK | OK | OK | OK | none | Windows Update後に再起動。EA復旧確認済み |

---

# 15. 緊急停止時の記録

緊急停止した場合：

```text
InpEmergencyStop = true
```

効果：

```text
新規Entry停止
既存ポジションのTime exitは維持
```

記録するもの：

```text
日時
理由
保有ポジション有無
手動決済したか
復旧日時
```

記録例：

| Date | Time | Action | Reason | Position | Notes |
|---|---:|---|---|---|---|
| 2026-06-24 | 18:30 | EmergencyStop=true | 想定外ログ確認 | none | 新規Entry停止 |
| 2026-06-24 | 19:10 | EmergencyStop=false | 原因確認完了 | none | 稼働再開 |

---

# 16. 週次メンテナンス

週末に行うこと：

```text
MT5稼働確認
Windows Update確認
必要なら再起動
再起動後にMT5・EA稼働確認
Forward_Weekly_Summary記入
GitHubへ記録保存
```

週明け前に確認：

```text
OANDAデモ口座ログイン
自動売買ON
EA稼働
7通貨ペア表示
EmergencyStop=false
TestMode=false
Mock=false
TestTimes=false
```

---

# 17. GitHub保存ルール

この運用記録は、GitHubのdocsに保存する。

関連docs：

```text
docs/03_forward_test_input_defaults.md
docs/04_mt5_forward_test_setup_checklist.md
docs/05_forward_test_record_format.md
docs/06_forward_test_operation_guide.md
```

トレード記録表は、必要に応じて以下に保存する。

```text
results/forward_test/
```

ファイル名例：

```text
trade_record_forward_test_YYYYMMDD.xlsx
```

---

# 18. 判断基準

## すぐ停止するケース

```text
想定外の大量Entry
Lotが想定より大きい
SLが入っていない
同じロジックが重複Entry
trade disabledやOrderSend failedが続く
```

対応：

```text
InpEmergencyStop = true
必要なら手動決済
ログ保存
原因確認
```

## 様子見でよいケース

```text
Date rule reject
EVENT REJECT
ATR REJECT
Entry対象外日にEntryしない
```

ただし、記録は残す。

---

# 19. 次にやること

フォワードテスト開始後、以下を継続する。

```text
1. Forward_Daily_Checkを毎日記入
2. Entry/ExitがあればForward_Trade_Logに記録
3. 停止ログがあればForward_Filter_Logに記録
4. 週末にForward_Weekly_Summaryを記録
5. 必要に応じてEvent Filter / ATR Filterを精査
```
