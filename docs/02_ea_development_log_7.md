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
