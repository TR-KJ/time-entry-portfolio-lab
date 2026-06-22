## 2026-06-17：EA Step 4.1 Global H1 ATR P70 実装仕様整理

### 目的

Step 3.2で、28ロジック統合EA Clean版が正式合格した。

対象EA：

```text
time_entry_step3_config_managed_28strategies_clean.mq5
```

Step 4では、このClean版EAに `Global H1 ATR P70` フィルタを追加する。

ただし、いきなり28ロジックEAへ組み込まず、まずは仕様を整理し、次に単体テストEAでATR取得・P70判定がMT5上で正しく動くか確認する。

---

# Step 4 全体方針

Step 4は以下の順で進める。

```text
Step 4.1：Global H1 ATR P70 のEA実装仕様整理
Step 4.2：ATR取得ロジックの単体テストEA作成
Step 4.2 Test：MT5上でATR値・P70値・判定ログを確認
Step 4.3：28ロジックClean版へATRフィルタ追加
```

---

# Global H1 ATR P70 の意味

現時点の前提：

```text
Global H1 ATR P70
=
各通貨ペアのH1 ATRを使い、
過去一定期間のATR分布に対して現在ATRがP70以上かどうかを判定するフィルタ
```

P70は、ATR値の70パーセンタイルを意味する。

イメージ：

```text
現在のH1 ATR >= 過去ATRのP70
→ ボラティリティが高い状態

現在のH1 ATR < 過去ATRのP70
→ ボラティリティが低い状態
```

---

# EAでの基本判定

Step 4では、以下の判定を基本とする。

```text
現在H1 ATR >= H1 ATR P70
```

上記を満たす場合のみ、エントリー許可とする。

判定：

```text
true  → Entry許可
false → Entry停止
```

---

# ATR対象

ATRを取得する対象は、各ロジックの `cfg.symbol` とする。

例：

```text
5_GJ_Port_Log2      → GBPJPY のH1 ATR
25_AU_China_Demand → AUDUSD のH1 ATR
9_AJ_Core2         → AUDJPY のH1 ATR
```

現時点では、ポートフォリオ全体共通の単一ATRではなく、**各ロジックの通貨ペアごとのH1 ATR** を見る方針。

---

# 時間足

ATR時間足はH1固定とする。

```text
PERIOD_H1
```

---

# ATR期間

Python検証側の定義に合わせる必要があるため、最終確認が必要。

EA側の暫定input案：

```text
InpAtrPeriod = 14
```

現時点ではATR期間14を仮置きする。

注意：

```text
Python検証コード側でGlobal H1 ATR P70に使ったATR期間と必ず一致させる。
不一致の場合、EAとバックテストのフィルタ判定がズレる。
```

---

# P70算出期間

P70算出に使う過去ATR本数も、Python検証側の定義に合わせる必要がある。

EA側の暫定input案：

```text
InpAtrP70LookbackBars = 500
```

注意：

```text
Python検証側のP70算出期間と必ず一致させる。
```

未確定の場合は、Step 4.2でinput化してテストできるようにする。

---

# 確定足・未確定足の扱い

EAでは、H1の未確定足ATRを使うと、時間中に値が変動する。

そのため、初期実装では **確定済みH1足** を使う。

方針：

```text
現在ATR：H1の1本前の確定足ATR
P70計算：H1の確定足ATR群
```

MQL5上の想定：

```text
CopyBuffer(..., start_pos = 1, count = lookback)
```

これにより、現在進行中のH1足を除外する。

---

# P70計算方法

P70は、ATR配列を昇順ソートして70%位置の値を取る。

暫定仕様：

```text
ATR配列を昇順ソート
index = floor((N - 1) * 0.70)
p70 = sorted[index]
```

注意：

```text
Python側のpercentile計算方法と完全一致しない可能性がある。
Step 4.2では、EA上のP70値をログで確認する。
必要ならPython側に合わせて計算方法を調整する。
```

---

# ATR単位

ATR値は価格単位で取得される。

例：

```text
USDJPY：0.120
GBPJPY：0.250
AUDUSD：0.00080
```

ログ表示では見やすくするため、pips換算も併記する。

想定ログ：

```text
Symbol=GBPJPY
ATR_H1=0.250
ATR_H1_Pips=25.0
P70=0.220
P70_Pips=22.0
Pass=true
```

---

# Step 4.2 単体テストEA

Step 4.2では、売買しないテストEAを作成する。

予定ファイル名：

```text
time_entry_step4_2_atr_p70_test.mq5
```

目的：

```text
H1 ATRを取得できるか
P70を計算できるか
現在ATR >= P70 の判定ができるか
pips換算表示が正しいか
各対象通貨ペアで動くか
```

---

# Step 4.2 テストEAのinput案

```text
InpTestSymbol = "GBPJPY"
InpAtrTimeframe = PERIOD_H1
InpAtrPeriod = 14
InpAtrP70LookbackBars = 500
InpUseClosedBar = true
InpPrintEveryTimer = true
InpTimerSeconds = 10
```

MQL5では `ENUM_TIMEFRAMES` input を使う可能性あり。

---

# Step 4.2 ログ出力案

単体テストEAでは、エキスパートログに以下を出す。

```text
ATR P70 Test initialized.
Symbol=GBPJPY
Timeframe=H1
ATR Period=14
Lookback=500
UseClosedBar=true
BarsAvailable=xxxx
CurrentATR=...
CurrentATR_Pips=...
P70=...
P70_Pips=...
PassATR=true/false
```

エラー時：

```text
ATR handle create failed
CopyBuffer failed
Not enough ATR bars
Invalid ATR value
```

---

# Step 4.2 テスト対象通貨ペア

最初は代表で以下を確認する。

```text
GBPJPY
AUDJPY
AUDUSD
EURAUD
GBPAUD
USDJPY
EURJPY
```

最低限、以下3つは確認する。

```text
GBPJPY：JPYクロス代表
AUDUSD：ドルスト代表
EURAUD：クロス通貨代表
```

---

# Step 4.3 28ロジックClean版への組み込み方針

Step 4.2でATR取得・P70判定が確認できたら、Step 4.3でClean版EAへ組み込む。

対象EA：

```text
time_entry_step3_config_managed_28strategies_clean.mq5
```

追加後の予定ファイル名：

```text
time_entry_step4_3_config_managed_28strategies_atr_p70.mq5
```

組み込み位置：

```text
TryEntry()
↓
IsEntryTime() 通過後
↓
PassEntryFilters()
↓
ATR P70判定
↓
AlreadyEnteredToday()
↓
HasOpenPosition()
↓
発注
```

Clean版ではすでに以下の拡張ポイントを用意済み。

```text
bool PassEntryFilters(StrategyConfig &cfg, datetime jst_time)
```

Step 4.3では、この中にATRフィルタを追加する。

---

# Step 4.3 input案

```text
InpUseGlobalAtrP70Filter = true
InpAtrPeriod = 14
InpAtrP70LookbackBars = 500
InpAtrUseClosedBar = true
InpPrintAtrFilterLogs = true
```

---

# ATRフィルタOFF運用

検証・トラブル対応のため、ATRフィルタはON/OFF可能にする。

```text
InpUseGlobalAtrP70Filter = false
→ ATRフィルタ無効
→ Step 3 Clean版と同じ挙動
```

これにより、ATR追加後に問題が出た場合でも、原因切り分けがしやすくなる。

---

# Step 4ではまだ実装しないもの

```text
指標停止
年末年始停止
週次複利ロット計算
本番用ロット管理
外部CSV設定
```

Step 4は、Global H1 ATR P70フィルタの実装と検証に集中する。

---

# 未確定事項

以下は、Python検証コード側と照合して確定する必要がある。

```text
ATR期間
P70算出期間
P70計算方法
現在ATRに使う足が確定足か未確定足か
判定条件が ATR >= P70 で正しいか
通貨ペアごとのATRでよいか
```

現時点のEA実装方針は以下。

```text
ATR期間：14 暫定
P70算出期間：500 暫定
現在ATR：H1確定足
判定：現在ATR >= P70
対象：各ロジックのcfg.symbol
```

---

# Step 4.1 判定

Step 4.1は仕様整理として完了。

次に進む内容：

```text
Step 4.2：ATR取得ロジックの単体テストEA作成
```

予定ファイル名：

```text
time_entry_step4_2_atr_p70_test.mq5
```

## 2026-06-17：EA Step 4.2 ATR P70単体テストEA 正式合格ログ

### 対象EA

```text
time_entry_step4_2_atr_p70_test.mq5
```

---

## 目的

Step 4.2では、28ロジック統合EAへ `Global H1 ATR P70` フィルタを組み込む前に、単体テストEAで以下を確認した。

```text
H1 ATRを取得できるか
過去ATRからP70を計算できるか
ATR値をpips換算できるか
CurrentATR >= P70 の判定ができるか
28ロジックEAで使用する全通貨ペアで動作するか
```

このEAは売買せず、エキスパートログにATR関連情報を出力するテスト専用EA。

---

## テスト設定

基本設定：

```text
InpAtrTimeframe = PERIOD_H1
InpAtrPeriod = 14
InpAtrP70LookbackBars = 500
InpPercentile = 70.0
InpUseClosedBar = true
InpPrintOnInit = true
InpPrintEveryTimer = true
InpTimerSeconds = 10
```

判定条件：

```text
CurrentATR >= P70
```

判定結果：

```text
true  → ATRフィルタ通過想定
false → ATRフィルタ停止想定
```

---

## 確認したログ項目

各通貨ペアで以下が表示されることを確認した。

```text
ATR P70 Test initialized
Symbol
Timeframe=H1
ATR Period=14
P70 Lookback=500
UseClosedBar=true
BarsAvailable
CopiedBars=500
CurrentATR
CurrentATR_Pips
P70
P70_Pips
PassATR_CurrentATR_GTE_P70=true/false
```

---

## テスト対象通貨ペア

28ロジックEAで使用する全7通貨ペアを確認した。

```text
GBPJPY：OK
AUDUSD：OK
EURAUD：OK
USDJPY：OK
EURJPY：OK
AUDJPY：OK
GBPAUD：OK
```

---

## 確認結果

全7通貨ペアで以下を確認した。

```text
H1 ATR取得 OK
過去500本取得 OK
P70計算 OK
pips換算 OK
CurrentATR >= P70 判定 OK
CopyBufferエラーなし
Not enough ATR barsなし
Invalid ATR valueなし
```

---

## Step 4.2 判定

Step 4.2は正式合格。

```text
ATR取得ロジック単体テスト OK
P70計算 OK
全対象通貨ペア OK
```

---

## 注意点

現時点では、Python検証側との完全一致はまだ未確認。

今後確認が必要な項目：

```text
ATR期間がPython側と一致しているか
P70算出期間がPython側と一致しているか
P70計算方法がPython側と一致しているか
確定足ベースでよいか
判定条件が CurrentATR >= P70 でよいか
```

現時点のEA側暫定仕様：

```text
ATR期間：14
P70算出期間：500
使用足：H1確定足
判定：CurrentATR >= P70
対象：各ロジックの通貨ペア
```

---

## 次にやること

次は Step 4.3 として、28ロジックClean版EAへATR P70フィルタを組み込む。

予定ファイル名：

```text
time_entry_step4_3_config_managed_28strategies_atr_p70.mq5
```

推奨フロー：

```text
Step 4.3仕様整理
ATRフィルタOFFでStep 3 Clean版と同じ挙動確認
ATRフィルタONで代表ロジックのPass/Reject確認
28ロジック全ON起動確認
```

## 2026-06-17：EA Step 4.3 28ロジックClean版へのATR P70フィルタ追加 仕様整理

### 目的

Step 4.3では、Step 3.2で正式合格した28ロジック統合EA Clean版に、Step 4.2で単体テスト済みの `Global H1 ATR P70` フィルタを組み込む。

ベースEA：

```text
time_entry_step3_config_managed_28strategies_clean.mq5
```

Step 4.3で作成するEA：

```text
time_entry_step4_3_config_managed_28strategies_atr_p70.mq5
```

---

# Step 4.3 の基本方針

Step 4.3では、28ロジックの既存仕様は変更しない。

維持するもの：

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
Global Variableによる同日重複エントリー防止
```

追加するもの：

```text
Global H1 ATR P70 フィルタ
ATRフィルタON/OFF input
ATR判定ログ
```

---

# ATRフィルタの意味

各ロジックの通貨ペアごとに、H1 ATRを取得し、過去ATRのP70以上かどうかを判定する。

判定：

```text
Current H1 ATR >= H1 ATR P70
```

結果：

```text
true  → Entry許可
false → Entry停止
```

---

# ATR対象

ATR対象は、各ロジックの `cfg.symbol` とする。

例：

```text
5_GJ_Port_Log2      → GBPJPY
25_AU_China_Demand → AUDUSD
9_AJ_Core2         → AUDJPY
```

ポートフォリオ全体共通の単一ATRではなく、ロジックごとの通貨ペアATRを見る。

---

# ATR仕様

Step 4.2単体テストEAで確認済みの仕様を採用する。

```text
Timeframe：H1
ATR Period：14
P70 Lookback：500
Percentile：70.0
UseClosedBar：true
判定：CurrentATR >= P70
```

使用足：

```text
現在ATR：H1の1本前の確定足ATR
P70計算：H1の確定足ATR 500本
```

MQL5想定：

```text
CopyBuffer(..., start_pos = 1, count = 500)
```

---

# 追加input案

Step 4.3では以下のinputを追加する。

```text
input bool   InpUseGlobalAtrP70Filter = true;
input int    InpAtrPeriod = 14;
input int    InpAtrP70LookbackBars = 500;
input double InpAtrPercentile = 70.0;
input bool   InpAtrUseClosedBar = true;
input bool   InpPrintAtrFilterLogs = true;
```

---

# ATRフィルタOFF時の挙動

```text
InpUseGlobalAtrP70Filter = false
```

の場合、ATRフィルタは完全に無効化する。

この場合、Step 3 Clean版と同じ挙動になる。

目的：

```text
ATR追加後の原因切り分けをしやすくする
Step 3 Clean版との差分確認をしやすくする
ATRフィルタ以外の動作確認をしやすくする
```

---

# ATRフィルタON時の挙動

```text
InpUseGlobalAtrP70Filter = true
```

の場合、Entry直前にATR判定を行う。

判定OK：

```text
CurrentATR >= P70
→ Entry続行
```

判定NG：

```text
CurrentATR < P70
→ Entry停止
```

---

# 組み込み位置

Step 3 Clean版では、すでに以下の拡張ポイントを用意している。

```text
bool PassEntryFilters(StrategyConfig &cfg, datetime jst_time)
```

Step 4.3では、この中にATR P70判定を追加する。

処理順：

```text
TryEntry()
↓
IsEntryTime()
↓
PassEntryFilters()
   └ PassGlobalAtrP70Filter()
↓
AlreadyEnteredToday()
↓
HasOpenPosition()
↓
SendBuyOrder / SendSellOrder
```

---

# PassEntryFilters の役割

Step 4.3時点では、PassEntryFilters内でATRフィルタのみを実行する。

想定：

```text
bool PassEntryFilters(StrategyConfig &cfg, datetime jst_time)
{
   if(!PassGlobalAtrP70Filter(cfg, jst_time))
   {
      return false;
   }

   return true;
}
```

将来的には以下もここに追加予定。

```text
指標停止
年末年始停止
その他ポートフォリオ共通フィルタ
```

---

# 追加予定関数

Step 4.3で追加する主な関数：

```text
bool CreateAtrHandle(string symbol, int &handle)
bool GetCurrentAtr(string symbol, int handle, double &current_atr)
bool GetAtrP70(string symbol, int handle, double &p70_value, int &copied_bars)
bool CalculatePercentile(double &values[], int count, double percentile, double &result)
bool PassGlobalAtrP70Filter(StrategyConfig &cfg, datetime jst_time)
double ToPips(string symbol, double price_value)
```

ただし、MQL5ではハンドル管理をシンプルにするため、初期版では判定時に `iATR()` ハンドルを作成し、使用後に `IndicatorRelease()` する方針でもよい。

理由：

```text
Step 4.3初期版は安全性と読みやすさを優先
まずは動作確認を優先
高速化は必要になってから検討
```

---

# ATRログ方針

`InpPrintAtrFilterLogs = true` の場合、Entry判定時にATRログを出す。

Pass時：

```text
ATR PASS. Symbol=GBPJPY, ATR_Pips=28.4, P70_Pips=24.1
```

Reject時：

```text
ATR REJECT. Symbol=GBPJPY, ATR_Pips=18.7, P70_Pips=24.1
```

エラー時：

```text
ATR filter error. Symbol=GBPJPY, reason=...
```

---

# ATR取得エラー時の扱い

初期方針では、ATR取得に失敗した場合は **Entry停止** とする。

理由：

```text
ATRフィルタONなのにATRが取得できない状態でEntryするのは危険
安全側に倒す
```

つまり、

```text
ATR取得失敗
P70計算失敗
CopiedBars不足
Invalid ATR value
```

の場合は `false` を返し、Entryしない。

ただし、`InpUseGlobalAtrP70Filter = false` の場合は、ATR取得自体を行わない。

---

# テスト方針

## Test 1：コンパイル

```text
0 errors
0 warnings
```

---

## Test 2：ATRフィルタOFFでStep 3 Clean版相当確認

設定：

```text
InpUseGlobalAtrP70Filter = false
```

確認：

```text
通常代表 5_GJ_Port_Log2 Entry/Exit OK
UJ代表 12_UJ_Short_Core Entry OK
China代表 25_AU_China_Demand Entry OK
AJ代表 9_AJ_Core2 Entry OK
```

目的：

```text
ATRフィルタOFFならStep 3 Clean版と同じように動くことを確認
```

---

## Test 3：ATRフィルタONで代表ロジック確認

設定：

```text
InpUseGlobalAtrP70Filter = true
InpPrintAtrFilterLogs = true
```

代表：

```text
5_GJ_Port_Log2
25_AU_China_Demand
9_AJ_Core2
```

確認：

```text
ATR PASS / ATR REJECT ログが出る
Pass時はEntryする
Reject時はEntryしない
```

注意：

```text
現在相場のATR状態によってPass/Rejectは変わる
PassになるかRejectになるかは固定ではない
```

---

## Test 4：28ロジック全ON起動確認

設定：

```text
28ロジック全ON
InpUseGlobalAtrP70Filter = true
InpPrintAtrFilterLogs = false
```

確認：

```text
EA起動OK
7通貨ペア認識OK
28ロジック初期化ログOK
エラーなし
不要な大量エントリーなし
```

---

# 重要な注意点

Step 4.3時点では、Python検証側との完全一致はまだ未確認。

今後確認が必要：

```text
ATR期間がPython側と一致しているか
P70算出期間がPython側と一致しているか
P70計算方法がPython側と一致しているか
確定足ベースでよいか
判定条件 CurrentATR >= P70 でよいか
```

ただし、Step 4.2でMT5上のATR取得・P70計算自体は全7通貨ペアで確認済み。

---

# Step 4.3ではまだ実装しないもの

```text
指標停止
年末年始停止
週次複利ロット計算
本番用ロット管理
外部CSV設定
ATRハンドルの高度なキャッシュ管理
```

Step 4.3では、まずATR P70フィルタの組み込みと動作確認に集中する。

---

# Step 4.3 判定基準

以下が確認できれば、Step 4.3を合格とする。

```text
コンパイルOK
ATRフィルタOFFでStep 3 Clean版相当の代表Entry確認OK
ATRフィルタONでATR PASS / REJECTログ確認OK
Pass時のEntry OK
Reject時のEntry停止 OK
28ロジック全ON起動確認OK
```

---

# 次にやること

次は、Step 4.3コード作成に進む。

予定ファイル名：

```text
time_entry_step4_3_config_managed_28strategies_atr_p70.mq5
```
