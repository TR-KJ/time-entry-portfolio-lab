## 2026-06-17：EA Step 5.1 指標停止 仕様整理

### 目的

Step 5では、28ロジック統合EAに「重要経済指標・政策イベントによるエントリー停止」を追加する。

ベースEA：

```text
time_entry_step4_3_1_config_managed_28strategies_atr_p70_log_suppressed.mq5
```

Step 5で作成予定のEA：

```text
time_entry_step5_config_managed_28strategies_event_filter.mq5
```

---

# Step 5 の基本方針

Step 5では、以下は変更しない。

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
ATR P70フィルタ
ATRログ抑制
日またぎExit判定
同日重複エントリー防止
```

追加するもの：

```text
重要指標日・政策イベント日のEntry停止
指標停止ON/OFF input
指標停止ログ
```

---

# 指標停止の対象

現時点では、Python検証側で使っていた重要イベントをEA側にも移植する。

対象候補：

```text
US_NFP
US_CPI
FOMC
BOJ
BOE
RBA
AU_CPI
ECB
```

ただし、初期実装ではすべてを一気に入れず、まずは既存検証で使用頻度が高いものから入れる。

初期候補：

```text
US_NFP
US_CPI
FOMC
BOJ
BOE
RBA
AU_CPI
```

ECBは必要性を確認してから追加してもよい。

---

# 停止単位

Step 5初期版では、時刻単位ではなく **日付単位停止** とする。

つまり、対象イベント日であれば、その日の該当ロジックEntryを停止する。

例：

```text
2026-06-12 が US_CPI の日
→ 対象ロジックはその日のEntryを停止
```

---

# 通貨別の停止対象

初期方針では、イベントごとに停止対象通貨を分ける。

## USD系イベント

対象：

```text
US_NFP
US_CPI
FOMC
```

停止対象候補：

```text
USDJPY
AUDUSD
```

加えて、円クロス・豪ドルクロスへの影響を考慮し、ポートフォリオ全体停止にするかは検討。

初期実装方針：

```text
USイベントは全ロジック停止
```

理由：

```text
NFP / CPI / FOMC は複数通貨へ波及しやすい
既存検証でも重要イベント除外として扱っている
実装を単純にできる
```

---

## JPY系イベント

対象：

```text
BOJ
```

停止対象：

```text
USDJPY
EURJPY
GBPJPY
AUDJPY
```

初期実装方針：

```text
BOJ日はJPY関連ロジック停止
```

---

## GBP系イベント

対象：

```text
BOE
```

停止対象：

```text
GBPJPY
GBPAUD
```

---

## AUD系イベント

対象：

```text
RBA
AU_CPI
```

停止対象：

```text
AUDUSD
AUDJPY
EURAUD
GBPAUD
```

---

## EUR系イベント

対象：

```text
ECB
```

停止対象：

```text
EURJPY
EURAUD
```

ECBは初期実装では保留でもよい。

---

# input案

```text
InpUseEventFilter = true
InpPrintEventFilterLogs = true

InpStopOnUS_NFP = true
InpStopOnUS_CPI = true
InpStopOnFOMC = true
InpStopOnBOJ = true
InpStopOnBOE = true
InpStopOnRBA = true
InpStopOnAU_CPI = true
InpStopOnECB = false
```

---

# 実装方式

Step 5初期版では、EAコード内にイベント日リストをハードコードする。

理由：

```text
MQL5単体で完結する
外部CSV読み込みよりテストが簡単
まずはロジックの正しさを確認しやすい
```

将来的には外部CSV化を検討する。

---

# イベント日リストの形式

MQL5では、日付を `YYYYMMDD` の整数として管理する。

例：

```text
20260612
20260729
```

関数イメージ：

```text
bool IsDateInList(int date_key, int &event_dates[])
```

---

# 追加予定関数

```text
bool IsEventDate(int date_key, int &event_dates[])
bool IsUSHighImpactEventDate(int date_key)
bool IsBOJEventDate(int date_key)
bool IsBOEEventDate(int date_key)
bool IsRBAEventDate(int date_key)
bool IsAUCPIEventDate(int date_key)
bool IsECBEventDate(int date_key)

bool IsSymbolAffectedByEvent(StrategyConfig &cfg, int date_key, string &event_name)
bool PassEventFilter(StrategyConfig &cfg, datetime jst_time)
```

---

# 組み込み位置

Step 4.3.1では、Entry直前の共通フィルタとして以下がある。

```text
PassEntryFilters()
```

Step 5では、ここに指標停止を追加する。

処理順案：

```text
TryEntry()
↓
IsEntryTime()
↓
PassEntryFilters()
   ├ PassGlobalAtrP70Filter()
   └ PassEventFilter()
↓
AlreadyEnteredToday()
↓
HasOpenPosition()
↓
Entry
```

ただし、ログ量を抑えるため、将来的には以下の順も検討する。

```text
IsEntryTime()
↓
AlreadyEnteredToday()
↓
HasOpenPosition()
↓
PassEntryFilters()
```

Step 5初期版では、Step 4.3.1の構造を大きく変えず、PassEntryFilters内に追加する。

---

# 指標停止ログ

`InpPrintEventFilterLogs = true` の場合、対象日に以下を出す。

例：

```text
EVENT REJECT. Strategy=5_GJ_Port_Log2, Symbol=GBPJPY, Event=BOE, Date=20260620
```

イベント対象外の場合は、原則ログを出さない。

---

# 指標停止エラー時の扱い

ハードコード日付リスト方式では、基本的に取得エラーは発生しない。

ただし、日付リストが空の場合などは、停止なしとして扱う。

---

# Step 5.2 実装方針

Step 5.2では、まず小さく実装する。

初期実装対象：

```text
US_NFP
US_CPI
FOMC
BOJ
BOE
RBA
AU_CPI
```

実装後の予定ファイル名：

```text
time_entry_step5_config_managed_28strategies_event_filter.mq5
```

---

# Step 5.2 テスト方針

## Test 1：コンパイル

```text
0 errors
```

---

## Test 2：指標停止OFF確認

設定：

```text
InpUseEventFilter = false
```

期待：

```text
Step 4.3.1と同じ挙動
代表Entry OK
```

---

## Test 3：USイベント停止確認

代表：

```text
5_GJ_Port_Log2
```

Mock日付をUSイベント日に設定。

期待：

```text
EVENT REJECT
Entryしない
```

---

## Test 4：BOJ停止確認

代表：

```text
12_UJ_Short_Core
```

期待：

```text
BOJ日にUSDJPY停止
```

---

## Test 5：RBA / AU_CPI停止確認

代表：

```text
25_AU_China_Demand
または
9_AJ_Core2
```

期待：

```text
AUD関連ロジック停止
```

---

## Test 6：イベント対象外日はEntry確認

Mock日付をイベント対象外日にする。

期待：

```text
EVENT REJECTなし
ATR条件が通ればEntry
```

---

# 未確定事項

以下は、実装前に確認が必要。

```text
イベント日リストをどこから持ってくるか
対象年を何年分入れるか
USイベントを全ロジック停止にするか
ECBを初期実装に含めるか
イベント日だけ停止か、前後日も停止するか
```

---

# Step 5.1 判定

Step 5.1は仕様整理として完了。

次に必要な作業：

```text
Python検証側で使っていたイベント日リストを確認
Step 5.2でEAコードへイベント日リストを実装
```

## 2026-06-17：EA Step 5.1 指標停止 仕様整理 修正版

### 対象

ベースEA：

```text
time_entry_step4_3_1_config_managed_28strategies_atr_p70_log_suppressed.mq5
```

Step 5.2作成EA：

```text
time_entry_step5_config_managed_28strategies_event_filter.mq5
```

---

## 方針修正

当初は「通貨別イベント停止」を想定していたが、提供されたPythonカレンダー生成コードでは、イベント停止が戦略ごとに細かく定義されていた。

そのため、Step 5では以下の方針に変更する。

```text
通貨別イベント停止ではなく、
Python検証コード準拠の戦略別イベント停止として実装する
```

---

## 2026年イベント日リスト

EA内に以下の2026年イベント日を `YYYYMMDD` の整数配列で実装する。

```text
FOMC
US_NFP
US_CPI
BOJ
BOE
ECB
RBA
AU_CPI
US_CPI発表週の水曜日
```

---

## Python準拠の停止ルール

### EJ系

```text
1_EJ_Log1
→ 2月停止
→ 1日停止
→ US_CPI発表週の水曜日停止

2_EJ_NightBlitz_20
3_EJ_NightBlitz_21
→ EVENTS_5_ECB停止
```

`EVENTS_5_ECB`：

```text
FOMC + US_NFP + US_CPI + BOJ + ECB
```

---

### GJ系

```text
4_GJ_Port_Log1
→ 12月停止
→ 1日・2日・29日・30日・31日停止

5_GJ_Port_Log2
→ 18日・19日・27日停止
→ EVENTS_5_BOE停止

6_GJ_Old_Mon
→ 1月・2月停止
→ EVENTS_5_BOE停止

7_GJ_Mon_Blitz
→ EVENTS_5_BOE停止
```

`EVENTS_5_BOE`：

```text
FOMC + US_NFP + US_CPI + BOJ + BOE
```

---

### AJ系

```text
8_AJ_Core1
9_AJ_Core2
10_AJ_SatA
11_AJ_SatB
→ EVENTS_7_AJ停止
```

`EVENTS_7_AJ`：

```text
FOMC + US_NFP + US_CPI + BOJ + ECB + RBA + AU_CPI
```

---

### UJ系

```text
12_UJ_Short_Core
13_UJ_Fix_MidWeek
14_UJ_Sat_3rd
15_UJ_Sat_Aug
→ EVENTS_4停止

16_UJ_T10A
→ BOJ停止
```

`EVENTS_4`：

```text
FOMC + US_NFP + US_CPI + BOJ
```

---

## 初期版で対象外にするロジック

提供されたPythonカレンダー生成コードに停止条件が明示されていないため、初期版では以下はイベント停止対象外とする。

```text
17_EA_1B
18_EA_2
19_EA_3
20_EA_1A
21_GA_B_3
22_GA_C_2
23_GA_F_2
24_GA_D_1
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

必要であれば、後続Stepで個別にイベント停止条件を追加する。

---

## 追加input

```text
InpUseEventFilter = true
InpPrintEventFilterLogs = true
InpSuppressEventLogsOncePerDay = true

InpStopOnUS_NFP = true
InpStopOnUS_CPI = true
InpStopOnFOMC = true
InpStopOnBOJ = true
InpStopOnBOE = true
InpStopOnECB = true
InpStopOnRBA = true
InpStopOnAU_CPI = true
```

---

## 組み込み位置

Step 4.3.1の共通フィルタに追加する。

```text
PassEntryFilters()
├ PassGlobalAtrP70Filter()
└ PassPythonCalendarEventFilter()
```

---

## Step 5.2 テスト方針

### Test 1：コンパイル

```text
0 errors
```

### Test 2：イベントフィルタOFF確認

```text
InpUseEventFilter = false
```

期待：

```text
Step 4.3.1と同等挙動
代表Entry OK
```

### Test 3：EJ停止確認

代表：

```text
1_EJ_Log1
```

Mock日付：

```text
2026-06-10 13:55
```

期待：

```text
EVENT REJECT. Event=US_CPI_WEEK_WED
Entryしない
```

### Test 4：GJ停止確認

代表：

```text
5_GJ_Port_Log2
```

Mock日付：

```text
2026-06-18 09:55
```

期待：

```text
EVENT REJECT. Event=BOE
Entryしない
```

### Test 5：AJ停止確認

代表：

```text
9_AJ_Core2
```

Mock日付：

```text
2026-07-02 17:14
```

期待：

```text
EVENT REJECT. Event=US_NFP
Entryしない
```

### Test 6：UJ停止確認

代表：

```text
12_UJ_Short_Core
```

Mock日付：

```text
2026-06-17 09:55
```

期待：

```text
EVENT REJECT. Event=FOMC
Entryしない
```

### Test 7：イベント対象外日Entry確認

イベント対象外日で、ATR条件が通る場合にEntryすることを確認する。

---

## Step 5.1修正版 判定

Python検証コード準拠の戦略別イベント停止として仕様を修正。

次に実施すること：

```text
Step 5.2：イベントフィルタ実装EAのコンパイル・テスト
```

## 2026-06-17：EA Step 5.2 イベントフィルタ初期版 テスト結果

### 対象EA

```text
time_entry_step5_config_managed_28strategies_event_filter.mq5
```

---

## テスト結果

確認済み：

```text
コンパイルOK
Test 2：イベントOFFで代表Entry/Exit OK
Test 3：EJ_Log1がCPI週水曜で停止 OK
Test 4：GJ_Port_Log2がBOE/日付停止で停止 OK
Test 5：9_AJ_Core2がEVENTS_7_AJで停止 OK
Test 6：UJ系がEVENTS_4または既存停止条件で停止 OK
Test 7：イベント対象外日はEntry OK
```

---

## 注意点

Test 6は `EVENT REJECT` ではなく、既存のDate Ruleによる停止だった。

```text
Date rule reject
```

そのため、UJイベント停止の純粋確認は後続で再確認候補とする。

---

## 確認された課題

一部ロジックで `EVENT REJECT` ログがEntry Window中に繰り返し出力された。

確認：

```text
9_AJ_Core2：EVENT REJECT 1回のみ
5_GJ_Port_Log2：EVENT REJECTが連続出力
1_EJ_Log1：EVENT REJECTが連続出力
12_UJ系：EVENT REJECT / Date rule reject系ログが連続出力
```

---

## 判定

イベント停止ロジック自体は概ねOK。

ただし、ログ連続出力を抑制するため、次に以下を実施する。

```text
Step 5.2.1：EVENT REJECTログ抑制修正版
```

## 2026-06-17：EA Step 5.2.1 EVENT REJECTログ抑制版 正式合格ログ

### 対象EA

```text
time_entry_step5_2_1_config_managed_28strategies_event_filter_log_suppressed.mq5
```

---

## 目的

Step 5.2で確認された `EVENT REJECT` ログの連続出力を抑制するため、ログ抑制版を作成した。

---

## 修正内容

同一日付・同一Strategy・同一Symbol・同一Magic・同一Eventでは、`EVENT REJECT` ログを1回だけ出すように修正。

変更したもの：

```text
EVENT REJECTログの出力回数
```

変更しないもの：

```text
イベント停止判定
Entryする / しない
ATR判定
SL / TP
Direction
Magic Number
時間決済
日またぎExit
同日重複エントリー防止
```

---

## テスト結果

確認済み：

```text
Test 1：コンパイル OK
Test 2：EJログ抑制 OK
Test 3：GJログ抑制 OK
Test 4：AJログ抑制 OK
Test 5：イベント対象外日Entry OK
```

---

## 判定

Step 5.2.1は正式合格。

```text
イベント停止ロジック OK
EVENT REJECTログ抑制 OK
イベント対象外日のEntry OK
売買挙動に問題なし
```

---

## 次にやること

次は、GitHub上の最新ルールセットとEA実装の整合性を確認する。

```text
EA実装と最新ルールセットの整合性チェック
↓
問題なければ Step 5 正式合格
```

## 2026-06-17：EA Step 5.3 strategy_master_list準拠イベントフィルタ仕様整理

### 対象

現在の合格EA：

```text
time_entry_step5_2_1_config_managed_28strategies_event_filter_log_suppressed.mq5
```

Step 5.3で作成予定のEA：

```text
time_entry_step5_3_config_managed_28strategies_master_event_filter.mq5
```

---

## 目的

Step 5.3では、GitHub上の最新ルールセット：

```text
docs/01_strategy_master_list.md
```

に合わせて、28ロジック全体のイベントフィルタ・個別停止条件を整合させる。

Step 5.2.1では、主にクロス円16ロジックのイベント停止を実装したが、最新マスターではEA系・GA系・China系にもイベント停止条件が定義されている。

そのため、Step 5.3で以下を追加・修正する。

---

# Step 5.3 修正対象

## 1. AJ系イベント定義の修正

現在のStep 5.2.1では、AJ系イベントにECBが含まれている可能性がある。

最新マスターでは、AJ系は以下の6イベント。

```text
US CPI
US NFP
FOMC
BOJ
RBA
AUD CPI
```

修正方針：

```text
AJ系8〜11のEVENTS_7_AJからECBを除外
名称も EVENT_RULE_AJ_6_EVENTS などへ整理
```

対象ロジック：

```text
8_AJ_Core1
9_AJ_Core2
10_AJ_SatA
11_AJ_SatB
```

---

## 2. EA系17〜20のイベント停止追加

対象ロジック：

```text
17_EA_1B
18_EA_2
19_EA_3
20_EA_1A
```

EA Common Events：

```text
US CPI
US NFP
FOMC
ECB
RBA
AUD CPI
```

追加停止：

```text
月末最終営業日
月末2営業日前
月末3営業日前
10月全停止
年末年始 12/25〜1/3
```

個別停止：

```text
17_EA_1B：8月停止
18_EA_2：1月・8月停止
19_EA_3：個別停止なし
20_EA_1A：8月停止
```

Step 5.3では、EA系の月末3営業日前停止も実装対象に含める。

---

## 3. GA系21〜24のイベント停止追加

対象ロジック：

```text
21_GA_B_3
22_GA_C_2
23_GA_F_2
24_GA_D_1
```

GA Common Events：

```text
US CPI
US NFP
FOMC
BOE
RBA
AUD CPI
```

追加停止：

```text
年末年始 12/25〜1/3
```

注意：

```text
GAではECB停止は使用しない
FOMCは当日のみ停止
```

---

## 4. China系25〜28のイベント停止追加

対象ロジック：

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

### 25_AU_China_Demand

```text
Pair：AUDUSD
Event Filter：RBA / AUD CPI / FOMC前日・当日
Exclude Month：8月・10月
Date Rule：9〜15日、25日〜月末
```

### 26_AJ_China_Demand

```text
Pair：AUDJPY
Event Filter：BOJ / RBA / AUD CPI
Exclude Month：2月・8月・10月
Date Rule：9〜15日
```

### 27_EA_China_Demand

```text
Pair：EURAUD
Event Filter：RBA / AUD CPI / FOMC前日・当日 / ECB
Exclude Month：8月・10月
Date Rule：9〜15日
```

### 28_GA_China_Demand

```text
Pair：GBPAUD
Event Filter：RBA / AUD CPI / FOMC前日・当日 / BOE
Exclude Month：8月・10月
Date Rule：9〜15日
```

---

# Step 5.3で追加するイベントルール案

```text
EVENT_RULE_NONE
EVENT_RULE_EJ_LOG1
EVENT_RULE_EVENTS_5_ECB
EVENT_RULE_EVENTS_5_BOE
EVENT_RULE_AJ_6_EVENTS
EVENT_RULE_UJ_4_EVENTS
EVENT_RULE_BOJ_ONLY

EVENT_RULE_EA_COMMON
EVENT_RULE_GA_COMMON
EVENT_RULE_AU_CHINA
EVENT_RULE_AJ_CHINA
EVENT_RULE_EA_CHINA
EVENT_RULE_GA_CHINA
```

---

# イベント日リスト

Step 5.3では、引き続き2026年イベント日をEA内にハードコードする。

使用するイベント：

```text
US_CPI_2026
US_NFP_2026
FOMC_2026
BOJ_2026
BOE_2026
ECB_2026
RBA_2026
AU_CPI_2026
```

追加で必要な派生日付：

```text
FOMC前日
US_CPI発表週の水曜日
月末最終営業日
月末2営業日前
月末3営業日前
年末年始 12/25〜1/3
```

---

# FOMC前日・当日停止

Step 5.3では、China系の一部でFOMC前日・当日停止を実装する。

対象：

```text
25_AU_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

判定：

```text
date == FOMC日
または
date == FOMC前日
```

---

# EA系の月末3営業日前停止

Step 5.3で実装する。

対象：

```text
17_EA_1B
18_EA_2
19_EA_3
20_EA_1A
```

停止対象：

```text
月末最終営業日
月末2営業日前
月末3営業日前
```

営業日の定義：

```text
月〜金
土日を除外
祝日は考慮しない
```

初期実装では、土日だけを除いた営業日ベースで判定する。

関数案：

```text
bool IsLastBusinessDay(datetime jst_time)
bool IsNthBusinessDayFromMonthEnd(datetime jst_time, int n)
bool IsMonthEnd3BusinessDays(datetime jst_time)
```

判定イメージ：

```text
月末最終営業日 → n = 1
月末2営業日前 → n = 2
月末3営業日前 → n = 3
```

---

# 年末年始停止

Step 5.3では、最新マスター準拠の年末年始停止も共通的に入れる。

停止期間：

```text
12/25〜1/3
```

対象：

```text
原則全28ロジック
```

---

# Step 5.3で維持するもの

以下は変更しない。

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
時間決済
日またぎExit
同日重複エントリー防止
```

---

# Step 5.3 テスト方針

## Test 1：コンパイル

```text
0 errors
```

---

## Test 2：AJ系ECB除外確認

対象：

```text
9_AJ_Core2
```

テスト内容：

```text
ECB日だけではAJ系が停止しないことを確認
```

ただし、同日がUS CPI / NFP / FOMC / BOJ / RBA / AUD CPIと重なる場合は別日で確認する。

---

## Test 3：EA Common Events停止確認

対象：

```text
17_EA_1B
```

確認：

```text
US CPI / NFP / FOMC / ECB / RBA / AUD CPI のいずれかでEVENT REJECT
```

---

## Test 4：EA月末3営業日前停止確認

対象：

```text
17_EA_1B または 20_EA_1A
```

確認：

```text
月末最終営業日
月末2営業日前
月末3営業日前
でEVENT REJECT
```

---

## Test 5：GA Common Events停止確認

対象：

```text
22_GA_C_2
```

確認：

```text
BOE / RBA / AUD CPI / US CPI / NFP / FOMC でEVENT REJECT
ECBでは停止しない
```

---

## Test 6：China系イベント停止確認

対象：

```text
25_AU_China_Demand
26_AJ_China_Demand
27_EA_China_Demand
28_GA_China_Demand
```

確認：

```text
AU China：RBA / AUD CPI / FOMC前日・当日で停止
AJ China：BOJ / RBA / AUD CPIで停止
EA China：RBA / AUD CPI / FOMC前日・当日 / ECBで停止
GA China：RBA / AUD CPI / FOMC前日・当日 / BOEで停止
```

---

## Test 7：Exclude Month確認

確認：

```text
AU China：8月・10月停止
AJ China：2月・8月・10月停止
EA China：8月・10月停止
GA China：8月・10月停止
```

EA系：

```text
17_EA_1B：8月停止
18_EA_2：1月・8月停止
20_EA_1A：8月停止
```

---

## Test 8：年末年始停止確認

対象：

```text
任意の代表ロジック
```

確認：

```text
12/25〜1/3で停止
```

---

## Test 9：イベント対象外日Entry確認

対象：

```text
5_GJ_Port_Log2
または
25_AU_China_Demand
```

確認：

```text
イベント対象外日ではEVENT REJECTなし
Entry条件を満たせばEntryする
```

---

# Step 5.3 判定基準

以下を確認できればStep 5.3を合格とする。

```text
コンパイルOK
AJ系ECB除外OK
EA Common Events停止OK
EA月末3営業日前停止OK
GA Common Events停止OK
China系イベント停止OK
Exclude Month停止OK
年末年始停止OK
イベント対象外日Entry OK
EVENT REJECTログ抑制OK
```

---

# 次にやること

次はStep 5.3コード作成に進む。

予定ファイル名：

```text
time_entry_step5_3_config_managed_28strategies_master_event_filter.mq5
```

## 2026-06-17：EA Step 5.3 master list準拠イベントフィルタ 正式合格ログ

### 対象EA

```text
time_entry_step5_3_config_managed_28strategies_master_event_filter.mq5
```

---

## 目的

Step 5.3では、GitHub上の最新ルールセット：

```text
docs/01_strategy_master_list.md
```

に合わせて、28ロジック全体のイベントフィルタ・個別停止条件を修正した。

---

## 主な修正内容

```text
AJ系：ECB停止を除外し、6 events for AJに修正
EA系17〜20：EA Common Events追加
GA系21〜24：GA Common Events追加
China系25〜28：各China Events追加
EA系：月末最終営業日・2営業日前・3営業日前停止を追加
年末年始停止 12/25〜1/3 を追加
EVENT REJECTログ抑制を維持
```

---

## テスト結果

確認済み：

```text
コンパイル OK
AJ系ECB除外確認 OK
EA Common Events停止 OK
EA月末3営業日前停止 OK
GA Common Events停止 OK
AU Chinaイベント停止 OK
EA Chinaイベント停止 OK
GA Chinaイベント停止 OK
EA系8月停止 OK
AJ China 2月停止 OK
年末年始停止 OK
イベント対象外日Entry OK
EVENT REJECTログ抑制 OK
```

---

## 補足

```text
26_AJ_China_Demand は、2026年のBOJ / RBA / AU_CPI日と稼働日条件 9〜15日 が重なりにくいため、
純粋なイベント停止テストは保留。

ただし、AJ ChinaのExclude Month停止は確認済み。
また、China系イベント判定ロジックは他China系で確認済み。
```

---

## 判定

Step 5.3は正式合格。

```text
Step 5：master list準拠イベントフィルタ実装 OK
```

---

## 現在の到達点

```text
Step 3.2：28ロジックClean版 正式合格
Step 4.3.1：ATR P70 + ATRログ抑制版 正式合格
Step 5.3：master list準拠イベントフィルタ 正式合格
```

---

## 次にやること

次工程候補：

```text
Step 6：年末年始停止・その他停止条件の最終整理
Step 7：週次複利ロット計算
```
