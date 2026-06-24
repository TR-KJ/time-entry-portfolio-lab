# 04_mt5_forward_test_setup_checklist.md

# MT5フォワードテスト設置手順・稼働前チェックリスト

## 対象EA

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

## 目的

このドキュメントは、28ロジック統合EAをWindowsパソコンでデモ口座フォワードテストするための設置手順と、稼働前チェックリストを整理するもの。

対象環境：

```text
Windows PC
DELL Inspiron
OANDA MT5 デモ口座
28ロジック統合EA
固定0.01lot 初回フォワード
```

---

# 1. フォワードテスト開始前の基本方針

初回フォワードテストでは、利益確認よりも、EAの実運用挙動確認を優先する。

確認優先順位：

```text
1. EAが正常起動するか
2. 28ロジックが読み込まれるか
3. Entry時刻が正しいか
4. 方向が正しいか
5. Lotが正しいか
6. SL / TPが正しく入るか
7. Time exitが正しく動くか
8. Event Filterが効くか
9. ATR Filterが効くか
10. ログが見やすいか
```

初回は固定0.01lotで開始する。

```text
InpLotMode = 0
InpFixedLot = 0.01
```

---

# 2. Windows PC側の準備

## 2.1 電源接続

DELL Inspironは、フォワードテスト中はACアダプター接続で使用する。

確認：

```text
ACアダプター接続
バッテリー残量に依存しない
本体・ACアダプターに異常な発熱や焦げ臭さがない
```

注意：

```text
充電中にACアダプターが温かくなるのは通常あり得る
異常に熱い、焦げ臭い、変形、異音がある場合は使用停止
```

---

## 2.2 スリープ無効化

EA稼働中にPCがスリープすると、MT5も停止する。

Windows設定：

```text
設定
↓
システム
↓
電源とバッテリー
↓
画面とスリープ
```

推奨：

```text
電源接続時、画面をオフにする：任意
電源接続時、デバイスをスリープ状態にする：なし
```

重要：

```text
スリープは必ず「なし」
画面オフはOK
```

---

## 2.3 電源モード

可能であれば、電源モードは安定重視にする。

推奨：

```text
電源モード：最適なパフォーマンス
または
バランス
```

避けたい設定：

```text
省電力優先
バッテリー節約モード
```

---

## 2.4 Windows Update対策

フォワード中に自動再起動されるとMT5が停止する。

確認：

```text
設定
↓
Windows Update
```

推奨：

```text
更新プログラムを確認
必要な更新は週末に実施
再起動が必要な場合は、相場停止中に行う
アクティブ時間を設定する
```

注意：

```text
完全に更新を止めるより、週末に計画的に更新する
平日稼働中の再起動を避ける
```

---

## 2.5 ネット接続

確認：

```text
Wi-Fiが安定している
可能なら有線LAN
テザリング運用時は通信切れに注意
```

フォワード中に確認するもの：

```text
MT5右下の通信状態
価格が更新されているか
気配値が動いているか
```

---

# 3. MT5側の準備

## 3.1 OANDA MT5にログイン

確認：

```text
OANDA MT5を起動
デモ口座にログイン
右下に通信量表示がある
赤い停止マークが出ていない
気配値が更新されている
```

ログイン確認：

```text
ナビゲーター
↓
口座
↓
デモ口座IDが表示されている
```

---

## 3.2 自動売買をON

MT5上部の自動売買ボタンをONにする。

確認：

```text
自動売買ボタンがON
赤ではなくON状態
EAのニコちゃん/アイコンが有効状態
```

EA側の許可：

```text
EAをチャートに入れる
↓
全般
↓
アルゴリズム取引を許可
```

---

## 3.3 対象通貨ペアを気配値表示に出す

28ロジックで使う7通貨ペアを気配値表示に出す。

対象：

```text
USDJPY
EURJPY
GBPJPY
AUDJPY
AUDUSD
EURAUD
GBPAUD
```

手順：

```text
気配値表示
↓
右クリック
↓
銘柄
↓
対象通貨ペアを表示
```

確認：

```text
7通貨ペアすべて表示
Bid / Askが動いている
スプレッドが異常に広くない
```

---

# 4. EAファイル設置手順

## 4.1 EAファイルをExpertsへ保存

保存先：

```text
MT5
↓
ファイル
↓
データフォルダを開く
↓
MQL5
↓
Experts
```

配置するEA：

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

---

## 4.2 MetaEditorでコンパイル

手順：

```text
MT5でF4
または
MetaEditorを開く
↓
Experts内のEAを開く
↓
F7でコンパイル
```

期待：

```text
0 errors
```

警告が出た場合：

```text
errors が0なら一旦可
ただし、warning内容は記録する
```

---

# 5. EAをチャートに設置

## 5.1 チャートは1枚でOK

このEAは内部で複数通貨ペアを扱うため、基本は1枚のチャートに設置する。

推奨：

```text
USDJPY M1
または
GBPJPY M1
```

注意：

```text
同じEAを複数チャートに入れない
二重稼働・二重Entryの原因になる
```

---

## 5.2 EA投入

手順：

```text
ナビゲーター
↓
エキスパートアドバイザ
↓
対象EAをチャートへドラッグ
```

---

# 6. フォワードテスト用input初期値

詳細は以下を参照。

```text
docs/03_forward_test_input_defaults.md
```

初回推奨の主要設定：

```text
InpEmergencyStop = false

InpLotMode = 0
InpFixedLot = 0.01

InpUseGlobalAtrP70Filter = true
InpUseEventFilter = true

InpTestMode = false
InpUseTestTimes = false
InpUseMockJstDateTime = false

InpPrintDebug = true
InpPrintSkipLogs = false
InpPrintRuleRejectLogs = true
InpPrintLotLogs = true
InpPrintAtrFilterLogs = false
InpPrintEventFilterLogs = true
```

重要：

```text
TestMode=false
UseMockJstDateTime=false
UseTestTimes=false
EmergencyStop=false
```

この4つは必ず確認する。

---

# 7. EA起動直後の確認

EA起動後、エキスパートタブを見る。

確認ログ：

```text
EA initialized
28 strategies loaded
LOT MODE CHECK. Mode=Fixed Lot
EmergencyStop=false
UseGlobalAtrP70Filter=true
UseEventFilter=true
```

確認すること：

```text
28ロジック分の初期化ログが出る
7通貨ペアが認識される
エラーが出ない
不要な大量ログが出ない
```

出てはいけないもの：

```text
SymbolSelect failed
Invalid symbol point
ATR ERROR
OrderSend failed
trade disabled
market closed
```

---

# 8. 稼働前チェックリスト

## Windows / PC

```text
□ ACアダプター接続
□ スリープなし
□ Windows Updateの再起動予定なし
□ ネット接続安定
□ PC時刻が大きくズレていない
□ 本体・ACアダプターに異常なし
```

## MT5

```text
□ OANDAデモ口座にログイン
□ 右下の通信状態OK
□ 自動売買ON
□ EAのアルゴリズム取引許可ON
□ 対象7通貨ペアが気配値表示にある
□ 価格が更新されている
```

## EA input

```text
□ InpEmergencyStop=false
□ InpLotMode=0
□ InpFixedLot=0.01
□ InpUseGlobalAtrP70Filter=true
□ InpUseEventFilter=true
□ InpTestMode=false
□ InpUseMockJstDateTime=false
□ InpUseTestTimes=false
□ InpPrintSkipLogs=false
```

## GitHub / 記録

```text
□ 使用EAファイルをGitHubへ保存
□ docsの開発ログを更新
□ フォワード開始日を記録
□ デモ口座番号を記録
□ 初期証拠金を記録
```

---

# 9. フォワード開始後に毎日見るもの

毎日1回は確認する。

```text
MT5が起動しているか
自動売買ONか
通信状態OKか
不要なエラーが出ていないか
予定Entryがあったか
Entry方向が正しいか
Lotが0.01か
SL / TPが正しいか
Time exit successが出たか
EVENT REJECTが妥当か
ATR REJECTが妥当か
```

---

# 10. 週末メンテナンス

週末に行うこと：

```text
MT5を確認
Windows Update確認
必要なら再起動
再起動後にMT5を起動
EAが稼働しているか確認
GitHubへログ記録
```

週明け前に確認：

```text
MT5起動
OANDAデモ口座ログイン
自動売買ON
EA稼働
7通貨ペア表示
EmergencyStop=false
```

---

# 11. 緊急停止方法

新規Entryを止めたい場合：

```text
EA設定
↓
InpEmergencyStop = true
```

効果：

```text
新規Entry停止
既存ポジションのTime exitは維持
```

完全停止したい場合：

```text
自動売買OFF
または
EAをチャートから削除
```

注意：

```text
自動売買OFFやEA削除をすると、Time exitも動かなくなる
既存ポジションは手動管理が必要
```

---

# 12. 注意事項

初回フォワードテストでは、成績よりも挙動確認を優先する。

特に見るもの：

```text
Entry時刻
Direction
Lot
SL / TP
Time exit
Event Filter
ATR Filter
ログの見やすさ
```

数週間は固定0.01lotで稼働し、EAの実挙動を確認する。

週次複利ロットは、フォワード挙動が安定してから検討する。

---

# 13. 次にやること

次工程：

```text
Step 9.3：フォワードテスト記録フォーマット作成
```
