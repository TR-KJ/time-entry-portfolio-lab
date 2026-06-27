# Event Candidate C 実装仕様

## 目的

Event Filter検証結果をもとに、本体EAへ `Event Candidate C` を実装するための仕様を整理する。

`Event Candidate C` は、全イベントを一律で終日停止するのではなく、Strategy / Event ごとに以下を分ける方式である。

```text
date_all_day
position_overlap
```

---

## 前提

現行EAは、イベント日をStrategyごとに判定し、該当した場合はEntryを停止する。

現行方式は基本的に以下。

```text
イベント日一致
→ その日のEntryを停止
```

検証結果では、全体を `position_overlap` にするよりも、Strategy / Eventごとに停止方式を分ける `Candidate C` が最有力となった。

---

## 用語

### date_all_day

イベント日に該当する場合、そのStrategyのEntryを終日停止する方式。

```text
Event Date = Entry Date
→ Stop Entry
```

### position_overlap

イベント発表前後の停止ウィンドウと、予定ポジション保有時間が重なる場合のみ停止する方式。

```text
Entry予定時刻 〜 Exit予定時刻
と
EventTime - PreMinutes 〜 EventTime + PostMinutes
が重なる場合のみ停止
```

---

## Candidate C 基本方針

```text
US_NFP / US_CPI / BOJ：
date_all_day 維持

FOMC：
position_overlap

RBA / ECB / BOE：
position_overlap

AUD CPI：
position_overlapで残すが、後で再確認

10_AJ_SatA / 11_AJ_SatB：
date_all_day 維持
```

---

## Strategy別の方針

### date_all_day維持候補

以下は、検証上 `position_overlap` に緩和すると悪化しやすかったため、イベント停止方式は `date_all_day` 維持候補とする。

```text
10_AJ_SatA
11_AJ_SatB
2_EJ_NightBlitz_20
3_EJ_NightBlitz_21
7_GJ_Mon_Blitz
```

ただし、`2_EJ_NightBlitz_20`、`3_EJ_NightBlitz_21`、`7_GJ_Mon_Blitz` については、全イベントを完全固定するのではなく、まずは現行維持寄りとして扱う。

---

### position_overlap候補

以下は、検証上 `position_overlap` にすることで改善が見られたため、緩和候補とする。

```text
17_EA_1B_Wed_Short
20_EA_1A_MonTue_Short
27_EA_China_Demand
28_GA_China_Demand
13_UJ_Fix_MidWeek
15_UJ_Sat_Aug
```

---

## Event別の方針

| Event | Default Policy | Comment |
|---|---|---|
| US_NFP | date_all_day | 重要指標。現行維持寄り |
| US_CPI | date_all_day | 重要指標。現行維持寄り |
| BOJ | date_all_day | JPY系への影響が大きいため現行維持寄り |
| FOMC | position_overlap | 完全OFFではなく、発表時間帯直撃のみ停止候補 |
| RBA | position_overlap | 終日停止は止めすぎの可能性 |
| ECB | position_overlap | 終日停止は止めすぎの可能性 |
| BOE | position_overlap | 終日停止は止めすぎの可能性 |
| AUD CPI | position_overlap | 後で発動状況を再確認 |

---

## 停止方式の優先順位

Strategy別Overrideを優先する。

```text
1. 個別停止・月停止・年末年始停止
2. Strategy別Override
3. Event別Default Policy
4. Event対象外なら通過
```

---

## Candidate C 判定イメージ

### 1. 個別停止

既存の個別停止は維持する。

例：

```text
年末年始停止
月停止
月末3営業日停止
Strategy固有の日付停止
```

これらはEvent Filterとは別に維持する。

---

### 2. Event対象判定

Strategyごとに対象イベントを取得する。

例：

```text
USDJPY系：
US_CPI / US_NFP / FOMC / BOJ

EURAUD系：
US_CPI / US_NFP / FOMC / ECB / RBA / AUD CPI

GBPAUD系：
US_CPI / US_NFP / FOMC / BOE / RBA / AUD CPI
```

---

### 3. Event停止方式の判定

Eventごとに以下を返す。

```text
EVENT_POLICY_NONE
EVENT_POLICY_DATE_ALL_DAY
EVENT_POLICY_POSITION_OVERLAP
```

---

### 4. date_all_day判定

```text
if policy == EVENT_POLICY_DATE_ALL_DAY:
    if entry_date == event_date:
        reject
```

ログ例：

```text
EVENT DATE STOP | Strategy=10_AJ_SatA | Event=US_CPI | Date=2026-xx-xx
```

---

### 5. position_overlap判定

以下が重なれば停止。

```text
Entry予定時刻 〜 Exit予定時刻
EventTime - PreMinutes 〜 EventTime + PostMinutes
```

ログ例：

```text
EVENT OVERLAP STOP | Strategy=27_EA_China_Demand | Event=FOMC | Entry=10:00 | Exit=15:50 | EventTime=03:00 | Window=-180/+180
```

---

## Event Time 仮仕様

現時点では、Python検証と同じ仮置き時刻を使う。

```text
FOMC：日本時間 翌日 3:00 / 4:00想定
US CPI / NFP：21:30 / 22:30想定
BOJ：12:00仮置き
BOE：20:00 / 21:00想定
ECB：21:15 / 22:15想定
RBA：13:30仮置き
AUD CPI：10:30仮置き
```

本体EAへ正式反映する前に、必要に応じて正確なイベント時刻テーブルを作成する。

---

## 停止ウィンドウ仮仕様

Python検証と同じ仮仕様を初期案とする。

| Event | Pre Minutes | Post Minutes |
|---|---:|---:|
| FOMC | 180 | 180 |
| US CPI | 120 | 120 |
| NFP | 120 | 120 |
| BOJ | 180 | 180 |
| BOE | 120 | 120 |
| ECB | 120 | 120 |
| RBA | 120 | 120 |
| AUD CPI | 120 | 120 |

---

## EAに追加したいinput候補

### Candidate C 使用フラグ

```text
InpUseEventCandidateC = true
```

### position_overlap 使用フラグ

```text
InpUseEventPositionOverlap = true
```

### 停止ウィンドウ

```text
InpFomcPreMinutes = 180
InpFomcPostMinutes = 180

InpUsCpiPreMinutes = 120
InpUsCpiPostMinutes = 120

InpNfpPreMinutes = 120
InpNfpPostMinutes = 120

InpBojPreMinutes = 180
InpBojPostMinutes = 180

InpBoePreMinutes = 120
InpBoePostMinutes = 120

InpEcbPreMinutes = 120
InpEcbPostMinutes = 120

InpRbaPreMinutes = 120
InpRbaPostMinutes = 120

InpAuCpiPreMinutes = 120
InpAuCpiPostMinutes = 120
```

ただし、inputが増えすぎる場合は、まず固定値実装でもよい。

---

## 実装関数案

### Event policy enum

```text
#define EVENT_POLICY_NONE 0
#define EVENT_POLICY_DATE_ALL_DAY 1
#define EVENT_POLICY_POSITION_OVERLAP 2
```

---

### Event time struct

```text
struct EventTimeInfo
{
   string event_name;
   datetime event_time_jst;
   int pre_minutes;
   int post_minutes;
};
```

---

### 追加候補関数

```text
int GetCandidateCEventPolicy(StrategyConfig &cfg, string event_name)
bool GetEventTimeJST(string event_name, int date_key, datetime &event_time_jst)
bool DoesPositionOverlapEventWindow(datetime entry_time, datetime exit_time, datetime event_time, int pre_minutes, int post_minutes)
bool PassEventCandidateCFilter(StrategyConfig &cfg, datetime jst_time)
void PrintEventCandidateCLog(...)
```

---

## 既存関数との関係

現行EAには以下の入口がある。

```text
PassEntryFilters
  ├─ PassGlobalAtrP70Filter
  └─ PassPythonCalendarEventFilter
```

Candidate C実装後は、以下の形を候補とする。

```text
PassEntryFilters
  ├─ PassGlobalAtrP70Filter
  └─ PassEventFilter
        ├─ PassPythonCalendarEventFilter        // 現行方式
        └─ PassEventCandidateCFilter            // Candidate C方式
```

または、既存 `PassPythonCalendarEventFilter` 内をCandidate C対応に拡張する。

安全性を考えると、まずは新関数 `PassEventCandidateCFilter` を追加し、inputで切り替える方がよい。

---

## 推奨input切替

```text
InpUseEventFilter = true
InpUseEventCandidateC = true
```

判定：

```text
if !InpUseEventFilter:
    pass

if InpUseEventCandidateC:
    PassEventCandidateCFilter
else:
    PassPythonCalendarEventFilter
```

---

## ログ仕様

現行の `EVENT REJECT` に加えて、以下の区別を付ける。

```text
EVENT DATE STOP
EVENT OVERLAP STOP
EVENT INDIVIDUAL STOP
EVENT MONTH STOP
EVENT YEAR_END_STOP
```

ログ例：

```text
EVENT DATE STOP. Strategy=10_AJ_SatA, Symbol=AUDJPY, Event=US_CPI, Date=20260715

EVENT OVERLAP STOP. Strategy=27_EA_China_Demand, Symbol=EURAUD, Event=FOMC, Entry=20260618 10:00, Exit=20260618 15:50, EventTime=20260618 03:00, WindowPre=180, WindowPost=180
```

---

## TestMode / MockJSTで確認したいこと

### Test 1：現行方式互換

```text
InpUseEventCandidateC = false
```

既存のEvent Filter挙動が変わらないこと。

---

### Test 2：Candidate C ON

```text
InpUseEventCandidateC = true
```

Candidate C側のログが出ること。

---

### Test 3：date_all_day維持

対象：

```text
10_AJ_SatA
11_AJ_SatB
US_CPI
US_NFP
BOJ
```

期待：

```text
該当イベント日は終日停止
EVENT DATE STOPログ
```

---

### Test 4：position_overlapで停止

対象例：

```text
FOMC
EA / GA / China Demand系
```

期待：

```text
Entry予定〜Exit予定がイベントウィンドウと重なる場合のみ停止
EVENT OVERLAP STOPログ
```

---

### Test 5：position_overlapで通過

期待：

```text
イベント日でも、予定ポジション保有時間がイベントウィンドウと重ならなければEntry許可
```

---

### Test 6：個別停止優先

期待：

```text
月停止・年末年始停止・個別停止がある日は、Candidate C判定より先に停止
```

---

### Test 7：ATR OFFとの組み合わせ

```text
InpUseGlobalAtrP70Filter = false
InpUseEventFilter = true
InpUseEventCandidateC = true
```

期待：

```text
ATRで止まらず、Event Candidate Cのみで停止判定される
```

---

## 実装時の注意点

```text
現行Event Filterを壊さない
Candidate Cはinputで切替可能にする
既存の個別停止・月停止・年末年始停止は維持する
ログは date_all_day と position_overlap を分ける
MockJSTで再現確認できるようにする
イベント発表時刻は仮置きから始めてもよいが、後で精密化可能にする
```

---

## 本体EAへ反映する前の確認

```text
1. docs/08_ea_reflection_policy.md と整合しているか
2. Event Candidate Cの対象Strategy/Event一覧に漏れがないか
3. position_overlapの時刻仕様がPython検証と一致しているか
4. ATR OFF input変更と矛盾しないか
5. Weekly Fixed Risk 1.5%運用と同時に使えるか
```

---

## 現時点の結論

Event Candidate Cは、以下の形で実装する。

```text
現行Event Filterを残したまま、
InpUseEventCandidateC でCandidate C方式へ切替可能にする。
```

初期運用候補：

```text
InpUseEventFilter = true
InpUseEventCandidateC = true
InpUseGlobalAtrP70Filter = false
InpLotMode = 1
InpRiskPercentPerTrade = 1.5
```
