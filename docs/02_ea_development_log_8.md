## 2026-06-17：EA Step 6.1 年末年始停止・その他停止条件 最終整理

### 対象EA

```text
time_entry_step5_3_config_managed_28strategies_master_event_filter.mq5
```

---

## 目的

Step 6では、Step 5.3で実装した `master list準拠イベントフィルタ` を前提に、年末年始停止・月停止・日付停止・月末営業日停止などの停止条件を最終整理する。

Step 5.3でイベントフィルタは正式合格済み。

Step 6では、以下を確認する。

```text
全28ロジックに年末年始停止が効くか
各ロジックの個別停止条件に漏れがないか
EA系の月末3営業日前停止が正しく効くか
China系のExclude Monthが正しく効くか
既存Date RuleとEvent Filterの優先関係に問題がないか
```

---

# Step 6の基本方針

Step 6では、原則として新しい売買ロジックは追加しない。

維持するもの：

```text
28ロジック構成
Entry時刻
Exit時刻
Direction
SL
TP
Magic Number
ATR P70フィルタ
ATRログ抑制
EVENT REJECTログ抑制
イベント停止条件
同日重複エントリー防止
```

確認・整理するもの：

```text
年末年始停止
月停止
日付停止
月末営業日停止
既存Date Rule
その他Individual Stop
```

---

# 年末年始停止

停止期間：

```text
12/25〜1/3
```

対象：

```text
全28ロジック
```

期待動作：

```text
対象期間内はEntryしない
EVENT REJECT または停止ログが出る
```

---

# クロス円16ロジックの停止条件

## EJ系

```text
1_EJ_Log1
- 2月停止
- 1日停止
- US_CPI発表週の水曜日停止
- 年末年始停止

2_EJ_NightBlitz_20
3_EJ_NightBlitz_21
- 5 events with ECB停止
- 年末年始停止
```

---

## GJ系

```text
4_GJ_Port_Log1
- 12月停止
- 1日・2日・29日・30日・31日停止
- 年末年始停止

5_GJ_Port_Log2
- 18日・19日・27日停止
- 5 events with BOE停止
- 年末年始停止

6_GJ_Old_Mon
- 1月・2月停止
- 5 events with BOE停止
- 年末年始停止

7_GJ_Mon_Blitz
- 5 events with BOE停止
- 年末年始停止
```

---

## AJ系

```text
8_AJ_Core1
- 6 events for AJ停止
- 年末年始停止

9_AJ_Core2
- 6月停止
- 9月停止
- 1日停止
- 20日停止
- 26日〜月末停止
- 6 events for AJ停止
- 年末年始停止

10_AJ_SatA
11_AJ_SatB
- 6 events for AJ停止
- 年末年始停止
```

---

## UJ系

```text
12_UJ_Short_Core
- 20日〜月末のみ
- 21日停止
- 22日停止
- 水曜停止
- 8月停止
- カレンダー月末停止
- 4 events停止
- 年末年始停止

13_UJ_Fix_MidWeek
- 25日以降の水曜・木曜のみ
- 4 events停止
- 年末年始停止

14_UJ_Sat_3rd
- 毎月3日のみ
- 4 events停止
- 年末年始停止

15_UJ_Sat_Aug
- 8月1日〜10日のみ
- 4 events停止
- 年末年始停止

16_UJ_T10A
- 毎月10日のみ
- 水曜停止
- BOJのみ停止
- 年末年始停止
```

---

# オージー系12ロジックの停止条件

## EA系 17〜20

対象：

```text
17_EA_1B
18_EA_2
19_EA_3
20_EA_1A
```

共通停止：

```text
EA Common Events
月末最終営業日
月末2営業日前
月末3営業日前
10月全停止
年末年始停止
```

個別停止：

```text
17_EA_1B：8月停止
18_EA_2：1月・8月停止
19_EA_3：個別停止なし
20_EA_1A：8月停止
```

---

## GA系 21〜24

対象：

```text
21_GA_B_3
22_GA_C_2
23_GA_F_2
24_GA_D_1
```

共通停止：

```text
GA Common Events
年末年始停止
```

注意：

```text
ECB停止なし
FOMCは当日のみ停止
```

---

## China系 25〜28

```text
25_AU_China_Demand
- 8月停止
- 10月停止
- RBA / AUD CPI / FOMC前日・当日停止
- 年末年始停止

26_AJ_China_Demand
- 2月停止
- 8月停止
- 10月停止
- BOJ / RBA / AUD CPI停止
- 年末年始停止

27_EA_China_Demand
- 8月停止
- 10月停止
- RBA / AUD CPI / FOMC前日・当日 / ECB停止
- 年末年始停止

28_GA_China_Demand
- 8月停止
- 10月停止
- RBA / AUD CPI / FOMC前日・当日 / BOE停止
- 年末年始停止
```

---

# Step 6 テスト方針

## Test 1：年末年始停止確認

代表ロジック：

```text
5_GJ_Port_Log2
25_AU_China_Demand
9_AJ_Core2
```

Mock例：

```text
2026-12-25
2026-12-31
2026-01-02
```

期待：

```text
Entryしない
停止ログが出る
```

---

## Test 2：EA系 月末3営業日前停止確認

代表ロジック：

```text
20_EA_1A
```

Mock例：

```text
2026-06-26
2026-06-29
2026-06-30
```

期待：

```text
EA_MONTH_END_3_BIZ_DAYS
Entryしない
```

曜日条件と重ならない日を優先して確認する。

---

## Test 3：EA系 月停止確認

代表：

```text
17_EA_1B：8月停止
18_EA_2：1月・8月停止
20_EA_1A：8月停止
```

期待：

```text
Entryしない
停止ログが出る
```

---

## Test 4：China系 Exclude Month確認

代表：

```text
25_AU_China_Demand：8月・10月停止
26_AJ_China_Demand：2月・8月・10月停止
27_EA_China_Demand：8月・10月停止
28_GA_China_Demand：8月・10月停止
```

期待：

```text
Entryしない
停止ログが出る
```

---

## Test 5：AJ Core2 個別停止確認

対象：

```text
9_AJ_Core2
```

確認：

```text
6月停止
9月停止
1日停止
20日停止
26日〜月末停止
```

期待：

```text
Entryしない
停止ログが出る
```

---

## Test 6：イベント対象外日Entry確認

代表：

```text
5_GJ_Port_Log2
25_AU_China_Demand
20_EA_1A
```

期待：

```text
停止ログが出ない
Entry条件を満たせばEntryする
```

---

# Step 6でコード修正が必要か

現時点では、Step 5.3 EAに以下が実装済みであれば、Step 6で新規コード作成は不要。

```text
年末年始停止
EA系月末3営業日前停止
EA/GA/China系イベント停止
China系Exclude Month
AJ/UJ/GJ/EJの個別停止
EVENT REJECTログ抑制
```

ただし、Step 6テストで漏れが見つかった場合のみ、以下を作成する。

```text
time_entry_step6_config_managed_28strategies_final_stops.mq5
```

---

# Step 6.1 判定

Step 6.1は仕様整理として完了。

次に行うこと：

```text
Step 6.2：停止条件の最終確認テスト
```

テスト後、問題がなければStep 6はコード修正なしで正式合格とする。

## 2026-06-17：EA Step 6.3 停止ログ最終整理版 作成ログ

### 対象EA

```text
time_entry_step6_3_config_managed_28strategies_final_stop_logs.mq5
```

---

## 目的

Step 6.2で確認された以下の課題に対応する。

```text
Date rule reject がEntry Window中に連続出力される
一部停止条件でEntryしないがログが出ないケースがある
```

---

## 修正内容

以下を追加した。

```text
InpSuppressRuleRejectLogsOncePerDay = true
```

同一日付・同一Strategy・同一Symbol・同一Magic・同一Reasonでは、`Date rule reject` を1回だけ出すようにする。

また、EVENT REJECTログは、同一EA稼働中に同一条件で1回だけ出るRuntime抑制へ整理した。

---

## 確認対象

```text
9_AJ_Core2 の Date rule reject ログ抑制
17_EA_1B の8月停止ログ
26_AJ_China_Demand の2月停止ログ
20_EA_1A の月末3営業日前停止ログ
イベント対象外日のEntry確認
```

---

## 注意点

今回の修正はログ整理が目的。

売買挙動は変更しない。

```text
Entry条件
Event停止判定
ATR判定
SL / TP
Direction
Magic Number
時間決済
日またぎExit
同日重複エントリー防止
```

上記はStep 5.3版から維持する。

## 2026-06-17：EA Step 6.3 停止ログ最終整理版 正式合格ログ

### 対象EA

```text
time_entry_step6_3_config_managed_28strategies_final_stop_logs.mq5
```

---

## 目的

Step 6.3では、Step 6.2で確認された停止ログ周りの課題を整理した。

対応内容：

```text
Date rule reject の連続出力抑制
一部停止条件でログが出ないケースの補正確認
停止条件ログの最終確認
```

---

## 修正内容

以下を追加・整理した。

```text
InpSuppressRuleRejectLogsOncePerDay = true
```

同一日付・同一Strategy・同一Symbol・同一Magic・同一Reasonでは、`Date rule reject` を1回だけ出す方針とした。

---

## テスト結果

確認済み：

```text
Test 2：Date rule reject June stop ログ抑制 OK
Test 3：Date rule reject after 26th stop ログ抑制 OK
Test 4：17_EA_1B 8月停止ログ OK
Test 5：26_AJ_China_Demand 2月停止ログ OK
Test 6：20_EA_1A 6/29月末営業日停止ログ OK
Test 7：イベント対象外日Entry OK
```

---

## 判定

Step 6.3は正式合格。

```text
停止条件 OK
停止ログ OK
Date rule reject ログ抑制 OK
EVENT REJECT ログ抑制 OK
イベント対象外日のEntry OK
売買挙動に問題なし
```

---

## 現在の最新版EA

```text
time_entry_step6_3_config_managed_28strategies_final_stop_logs.mq5
```

---

## 現在の到達点

```text
Step 3.2：28ロジックClean版 正式合格
Step 4.3.1：ATR P70 + ATRログ抑制版 正式合格
Step 5.3：master list準拠イベントフィルタ 正式合格
Step 6.3：停止ログ最終整理版 正式合格
```

---

## 次にやること

次工程：

```text
Step 7：週次複利ロット計算
```

## 2026-06-17：EA Step 7.1 週次複利ロット計算 仕様整理

### 対象EA

現在の最新版EA：

```text
time_entry_step6_3_config_managed_28strategies_final_stop_logs.mq5
```

Step 7で作成予定のEA：

```text
time_entry_step7_config_managed_28strategies_weekly_compound_lot.mq5
```

---

## 目的

Step 7では、固定ロット `0.01` ではなく、口座残高または基準残高に応じてロットを自動計算する仕組みを追加する。

ただし、完全な本番ロット管理にいきなり進まず、まずは以下を実装する。

```text
週次複利ロット計算
固定損失額ベースのロット計算
最小ロット・最大ロット・ロット刻み対応
テスト用ログ出力
固定ロット運用との切り替え
```

---

# Step 7 の基本方針

Step 7では、以下は変更しない。

```text
28ロジック構成
Entry時刻
Exit時刻
Direction
SL
TP
Magic Number
ATR P70フィルタ
イベント停止
年末年始停止
各種停止条件
ログ抑制
時間決済
日またぎExit
同日重複エントリー防止
```

変更するもの：

```text
注文ロット計算
```

現在：

```text
InpFixedLot = 0.01
```

Step 7後：

```text
固定ロットモード
または
週次複利ロットモード
```

を選べるようにする。

---

# ロット計算モード

追加予定input：

```text
InpLotMode = 0
```

想定：

```text
0 = Fixed Lot
1 = Weekly Compound Risk Lot
```

---

# 固定ロットモード

```text
InpLotMode = 0
```

の場合は、これまで通り固定ロットを使う。

```text
InpFixedLot = 0.01
```

期待挙動：

```text
Step 6.3と同じロットでEntryする
```

---

# 週次複利ロットモード

```text
InpLotMode = 1
```

の場合、週の開始時点の基準残高をもとに、各トレードの想定損失額を決める。

基本式：

```text
RiskAmount = WeeklyBaseEquity × RiskPercent / 100
Lot = RiskAmount / SL損失額
```

---

# 週次基準残高

週次複利では、毎トレードごとに残高を更新するのではなく、週単位で基準残高を固定する。

方針：

```text
月曜日の週開始時点のAccount EquityまたはBalanceを基準にする
その週の間は同じ基準残高を使う
翌週になったら基準残高を更新する
```

追加予定input：

```text
InpWeeklyBaseUseEquity = true
```

```text
true  → AccountInfoDouble(ACCOUNT_EQUITY)
false → AccountInfoDouble(ACCOUNT_BALANCE)
```

初期方針：

```text
Equity基準
```

---

# 週の定義

JST基準で週を判定する。

```text
月曜日開始
日曜日終了
```

週キー：

```text
YYYY + WeekNumber
```

または簡易的に、

```text
その週の月曜日の日付 YYYYMMDD
```

を使う。

推奨：

```text
WeekStartDateKey
```

例：

```text
2026-06-17 → 週開始日 2026-06-15 → 20260615
```

---

# 週次基準残高の保存

EA再起動後も同じ週の基準残高を維持するため、Global Variableに保存する。

Global Variable名案：

```text
TE_STEP7_WEEKLY_BASE_EQUITY_YYYYMMDD
```

例：

```text
TE_STEP7_WEEKLY_BASE_EQUITY_20260615
```

動作：

```text
同じ週のGVがあれば、それを使う
なければ現在のEquity/Balanceで作成する
次週になれば新しいGVを作成する
```

---

# Risk Percent

追加予定input：

```text
InpRiskPercentPerTrade = 0.5
```

意味：

```text
1トレードあたり、週次基準残高の0.5%をリスクにする
```

例：

```text
WeeklyBaseEquity = 1,000,000円
RiskPercent = 0.5%
RiskAmount = 5,000円
```

---

# SLがないロジックの扱い

現在の28ロジックには、TPなしのものはあるが、SLは基本的に全ロジックに設定されている。

Step 7では、SL pips が `0` 以下の場合は安全側でEntry停止とする。

```text
SL pips <= 0
→ Lot計算不可
→ Entry停止
```

ただし、現行仕様では対象なしの想定。

---

# ロット計算に使うSL

各ロジックの実際のSL pipsを使う。

通常ロジック：

```text
cfg.sl_pips
```

UJ Short Core：

```text
GOTO：20 pips
NORMAL：50 pips
```

既存関数：

```text
GetStrategySLPips(cfg, jst_time)
```

を使う。

---

# pips価値の計算

MQL5上では、銘柄ごとに1ロットあたりのtick value / tick sizeを使って、SL pipsあたりの損失額を計算する。

想定式：

```text
pip_size = GetPipSize(symbol)
tick_value = SYMBOL_TRADE_TICK_VALUE
tick_size = SYMBOL_TRADE_TICK_SIZE

pip_value_per_lot = tick_value * (pip_size / tick_size)
loss_per_lot = SL_pips * pip_value_per_lot

lot = risk_amount / loss_per_lot
```

---

# ロット正規化

計算後、ブローカー仕様に合わせて正規化する。

使用情報：

```text
SYMBOL_VOLUME_MIN
SYMBOL_VOLUME_MAX
SYMBOL_VOLUME_STEP
```

既存関数：

```text
NormalizeLot(symbol, lot)
```

を使用する。

---

# 最大ロット制限

安全のため、EA側で最大ロットを制限する。

追加予定input：

```text
InpMaxAutoLot = 1.0
```

動作：

```text
計算ロット > InpMaxAutoLot
→ InpMaxAutoLot に丸める
```

初期値は慎重に設定する。

---

# 最小ロット未満の場合

計算ロットがブローカー最小ロット未満の場合は、初期方針として最小ロットに丸める。

```text
calculated_lot < SYMBOL_VOLUME_MIN
→ SYMBOL_VOLUME_MIN
```

ただし、安全運用では「最小ロット未満ならEntry停止」も検討可能。

初期実装では以下をinput化する。

```text
InpAllowMinLotWhenBelowMinimum = true
```

---

# ロット計算ログ

追加予定input：

```text
InpPrintLotLogs = true
```

Entry直前に以下を表示する。

```text
LOT CALC. Strategy=5_GJ_Port_Log2, Symbol=GBPJPY, WeeklyBase=1000000, Risk%=0.50, RiskAmount=5000, SL=90.0, Lot=0.05
```

固定ロットモードでは以下。

```text
LOT FIXED. Strategy=5_GJ_Port_Log2, Symbol=GBPJPY, Lot=0.01
```

ログが多い場合は、後続で抑制を検討する。

---

# Step 7.2 単体テスト方針

いきなり28ロジックEAへ完全組み込みせず、まずロット計算が妥当か確認する。

ただし、既にEA構造が安定しているため、Step 7では以下の順で進める。

```text
Step 7.1：仕様整理
Step 7.2：ロット計算テストEA または本EA組み込み版作成
Step 7.3：固定ロットモード確認
Step 7.4：週次複利モード確認
```

---

# Step 7.2 作成予定EA

```text
time_entry_step7_config_managed_28strategies_weekly_compound_lot.mq5
```

ベース：

```text
time_entry_step6_3_config_managed_28strategies_final_stop_logs.mq5
```

---

# Step 7 テスト方針

## Test 1：コンパイル

```text
0 errors
```

---

## Test 2：固定ロットモード確認

設定：

```text
InpLotMode = 0
InpFixedLot = 0.01
```

期待：

```text
Step 6.3と同じく 0.01 lot でEntryする
```

---

## Test 3：週次複利ロットログ確認

設定：

```text
InpLotMode = 1
InpRiskPercentPerTrade = 0.5
InpPrintLotLogs = true
```

期待：

```text
LOT CALC ログが出る
WeeklyBaseEquity が表示される
RiskAmount が表示される
SL pips が表示される
Lot が表示される
```

---

## Test 4：ロットが発注に反映されるか確認

代表：

```text
5_GJ_Port_Log2
```

期待：

```text
計算されたLotでGBPJPY sellが建つ
```

---

## Test 5：UJ Short Core GOTO / NORMAL のSL別ロット確認

対象：

```text
12_UJ_Short_Core
```

確認：

```text
GOTO：SL20 pipsでLot計算
NORMAL：SL50 pipsでLot計算
```

期待：

```text
SL20の方がロット大きめ
SL50の方がロット小さめ
```

---

# Step 7ではまだ実装しないもの

```text
日次損失制限
週次損失制限
通貨別リスク上限
同時ポジション合計リスク制限
ポートフォリオ全体VaR管理
```

これらは、週次複利ロット計算が安定してから検討する。

---

# Step 7.1 判定

Step 7.1は仕様整理として完了。

次に行うこと：

```text
Step 7.2：週次複利ロット計算EAの作成
```
