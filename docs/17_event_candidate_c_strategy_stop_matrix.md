# Event Candidate C Strategy Stop Matrix

## 1. Purpose

本ドキュメントは、以下のEAに実装されている `Event Candidate C` について、28戦略ごとの経済イベント停止方式を一覧化したものである。

対象EA:

- `src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

参照仕様:

- `docs/09_event_candidate_c_implementation_spec.md`

本一覧は、仕様書上の方針だけではなく、現在のEAコードで実際に実装されている判定を優先して整理する。

---

## 2. Stop Policy Definitions

### date_all_day

イベント日とEntry予定日が一致する場合、そのStrategyの新規Entryを終日停止する。

表記:

- `終日`

### position_overlap

Strategyの予定保有時間と、イベント発表前後の停止ウィンドウが重なる場合のみ、新規Entryを停止する。

判定対象:

- Entry予定時刻
- Exit予定時刻
- Event発表時刻
- Event発表前の停止時間
- Event発表後の停止時間

表記:

- `重複`

### Not Applicable

そのStrategyでは対象イベントとして扱わない。

表記:

- `—`

---

## 3. Event Candidate C Basic Policy

Candidate Cの基本方針は以下。

| Event | 基本停止方式 |
|---|---|
| US NFP | date_all_day |
| US CPI | date_all_day |
| BOJ | date_all_day |
| FOMC | position_overlap |
| BOE | position_overlap |
| ECB | position_overlap |
| RBA | position_overlap |
| 豪CPI | position_overlap |

ただし、Strategy別の強制終日停止および個別Overrideが優先される。

---

## 4. Strategy Stop Matrix

| No. | Strategy | Symbol | US NFP | US CPI | FOMC | BOJ | BOE | ECB | RBA | 豪CPI |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | 1_EJ_Log1 | EURJPY | — | 特殊※1 | — | — | — | — | — | — |
| 2 | 2_EJ_NightBlitz_20 | EURJPY | 終日 | 終日 | 重複※2 | 終日 | — | 終日 | — | — |
| 3 | 3_EJ_NightBlitz_21 | EURJPY | 終日 | 終日 | 重複※2 | 終日 | — | 終日 | — | — |
| 4 | 4_GJ_Port_Log1 | GBPJPY | — | — | — | — | — | — | — | — |
| 5 | 5_GJ_Port_Log2 | GBPJPY | 終日 | 終日 | 重複 | 終日 | 重複 | — | — | — |
| 6 | 6_GJ_Old_Mon | GBPJPY | 終日 | 終日 | 重複 | 終日 | 重複 | — | — | — |
| 7 | 7_GJ_Mon_Blitz | GBPJPY | 終日 | 終日 | 終日 | 終日 | 終日 | — | — | — |
| 8 | 8_AJ_Core1 | AUDJPY | 終日 | 終日 | 重複 | 終日 | — | — | 重複 | 重複 |
| 9 | 9_AJ_Core2 | AUDJPY | 終日 | 終日 | 重複 | 終日 | — | — | 重複 | 重複 |
| 10 | 10_AJ_SatA | AUDJPY | 終日 | 終日 | 終日 | 終日 | — | — | 終日 | 終日 |
| 11 | 11_AJ_SatB | AUDJPY | 終日 | 終日 | 終日 | 終日 | — | — | 終日 | 終日 |
| 12 | 12_UJ_Short_Core | USDJPY | 終日 | 終日 | 重複 | 終日 | — | — | — | — |
| 13 | 13_UJ_Fix_MidWeek | USDJPY | 終日 | 終日 | 重複 | 終日 | — | — | — | — |
| 14 | 14_UJ_Sat_3rd | USDJPY | 終日 | 終日 | 重複 | 終日 | — | — | — | — |
| 15 | 15_UJ_Sat_Aug | USDJPY | 終日 | 終日 | 重複 | 終日 | — | — | — | — |
| 16 | 16_UJ_T10A | USDJPY | — | — | — | 終日 | — | — | — | — |
| 17 | 17_EA_1B | EURAUD | 終日 | 終日 | 重複 | — | — | 重複 | 重複 | 重複 |
| 18 | 18_EA_2 | EURAUD | 終日 | 終日 | 重複 | — | — | 重複 | 重複 | 重複 |
| 19 | 19_EA_3 | EURAUD | 終日 | 終日 | 重複 | — | — | 重複 | 重複 | 重複 |
| 20 | 20_EA_1A | EURAUD | 終日 | 終日 | 重複 | — | — | 重複 | 重複 | 重複 |
| 21 | 21_GA_B3 | GBPAUD | 終日 | 終日 | 重複 | — | 重複 | — | 重複 | 重複 |
| 22 | 22_GA_C2 | GBPAUD | 終日 | 終日 | 重複 | — | 重複 | — | 重複 | 重複 |
| 23 | 23_GA_F2 | GBPAUD | 終日 | 終日 | 重複 | — | 重複 | — | 重複 | 重複 |
| 24 | 24_GA_D1 | GBPAUD | 終日 | 終日 | 重複 | — | 重複 | — | 重複 | 重複 |
| 25 | 25_AU_China_Demand | AUDUSD | — | — | 重複※3 | — | — | — | 重複 | 重複 |
| 26 | 26_AJ_China_Demand | AUDJPY | — | — | — | 終日 | — | — | 重複 | 重複 |
| 27 | 27_EA_China_Demand | EURAUD | — | — | 重複※3 | — | — | 重複 | 重複 | 重複 |
| 28 | 28_GA_China_Demand | GBPAUD | — | — | 重複※3 | — | 重複 | — | 重複 | 重複 |

---

## 5. Strategy-Specific Notes

### 5.1 1_EJ_Log1

`1_EJ_Log1` は、通常のUS CPI当日終日停止とは異なる特殊ルールを使用する。

停止条件:

- 2月
- 毎月1日
- `US_CPI_WED_2026_DATES` に登録された日

コード上の停止ログ:

- `EJ_LOG1_FEB_STOP`
- `EJ_LOG1_DAY1_STOP`
- `US_CPI_WEEK_WED`

したがって、表ではUS CPIを `特殊` と記載する。

---

### 5.2 2_EJ_NightBlitz_20 / 3_EJ_NightBlitz_21

以下2戦略は、Strategy別の強制終日停止対象に含まれる。

- `2_EJ_NightBlitz_20`
- `3_EJ_NightBlitz_21`

ただし、FOMCについては個別Overrideが設定されており、`position_overlap` 判定を使用する。

実際の停止方式:

| Event | 停止方式 |
|---|---|
| US NFP | 終日 |
| US CPI | 終日 |
| BOJ | 終日 |
| ECB | 終日 |
| FOMC | 重複 |

---

### 5.3 Force Date All Day Strategies

以下のStrategyは、対象イベントについて原則 `date_all_day` を使用する。

- `2_EJ_NightBlitz_20`
- `3_EJ_NightBlitz_21`
- `7_GJ_Mon_Blitz`
- `10_AJ_SatA`
- `11_AJ_SatB`

ただし、`2_EJ_NightBlitz_20` と `3_EJ_NightBlitz_21` のFOMCは、個別Overrideにより `position_overlap` となる。

---

### 5.4 China Demand Strategies and FOMC

以下のStrategyは、FOMC当日だけではなく、翌日早朝のFOMCも確認する。

- `25_AU_China_Demand`
- `27_EA_China_Demand`
- `28_GA_China_Demand`

予定保有時間が翌日FOMCの停止ウィンドウと重なる場合、前日のEntryを停止する。

確認対象:

- Entry予定日のFOMC
- Entry予定日の翌日のFOMC
- Entry予定時刻からExit予定時刻まで
- FOMC停止ウィンドウとの重複

---

## 6. Position Overlap Event Settings

現在のEA input初期値は以下。

| Event | Event Time JST | Pre Minutes | Post Minutes | Stop Window |
|---|---:|---:|---:|---|
| FOMC | 03:00 | 180 | 180 | 00:00〜06:00 |
| BOE | 21:00 | 120 | 120 | 19:00〜23:00 |
| ECB | 21:15 | 120 | 120 | 19:15〜23:15 |
| RBA | 13:30 | 120 | 120 | 11:30〜15:30 |
| 豪CPI | 10:30 | 120 | 120 | 08:30〜12:30 |

該当input:

- `InpFomcEventHourJST`
- `InpFomcEventMinuteJST`
- `InpFomcPreMinutes`
- `InpFomcPostMinutes`
- `InpBoeEventHourJST`
- `InpBoeEventMinuteJST`
- `InpBoePreMinutes`
- `InpBoePostMinutes`
- `InpEcbEventHourJST`
- `InpEcbEventMinuteJST`
- `InpEcbPreMinutes`
- `InpEcbPostMinutes`
- `InpRbaEventHourJST`
- `InpRbaEventMinuteJST`
- `InpRbaPreMinutes`
- `InpRbaPostMinutes`
- `InpAuCpiEventHourJST`
- `InpAuCpiEventMinuteJST`
- `InpAuCpiPreMinutes`
- `InpAuCpiPostMinutes`

---

## 7. Common Year-End Stop

Event Candidate Cでは、全28Strategyに共通して年末年始停止を行う。

停止期間:

- 12月25日から12月31日
- 1月1日から1月3日

ログ名:

- `YEAR_END_STOP`

この停止は、個別経済イベント判定より前に実行される。

---

## 8. Other Non-Event Stop Rules

本一覧は、主として経済イベント停止を整理したものである。

各Strategyには、経済イベント停止とは別に以下の停止条件が存在する。

- 特定月停止
- 特定日停止
- 月初停止
- 月末3営業日停止
- 年末年始停止
- Strategy固有の日付ルール
- Strategy固有の曜日ルール
- China Demand日付ウィンドウ
- Weekend / Market Closed Guard
- Emergency Stop
- ATR Filter

これらは、本一覧の経済イベント停止とは別に判定される。

---

## 9. Log Types

Event Candidate Cでは、主に以下のログが出力される。

### date_all_day

- `EVENT REJECT`
- `CANDIDATE_C_DATE_<EVENT_NAME>`

### position_overlap

- `EVENT OVERLAP STOP`

ログ例:

- `EVENT OVERLAP STOP. Symbol=EURAUD, Event=FOMC`
- `EVENT OVERLAP STOP. Symbol=GBPAUD, Event=BOE`
- `EVENT REJECT. Event=CANDIDATE_C_DATE_US_NFP`
- `EVENT REJECT. Event=CANDIDATE_C_DATE_BOJ`

---

## 10. Important Implementation Notes

### 10.1 Current EA Code Has Priority

仕様書とEAコードに差異がある場合、本ドキュメントでは現在のEAコードを優先する。

### 10.2 Event Inputs Must Be Enabled

各イベント停止は、対応するinputが `true` の場合のみ有効となる。

- `InpStopOnUS_NFP`
- `InpStopOnUS_CPI`
- `InpStopOnFOMC`
- `InpStopOnBOJ`
- `InpStopOnBOE`
- `InpStopOnECB`
- `InpStopOnRBA`
- `InpStopOnAU_CPI`

### 10.3 Candidate C Must Be Enabled

Candidate Cを使用するには、以下の設定が必要。

- `InpUseEventFilter = true`
- `InpUseEventCandidateC = true`

`InpUseEventCandidateC = false` の場合は、旧Event Filter方式が使用される。

---

## 11. Conclusion

現在のEAでは、全Strategyを一律に停止するのではなく、以下を組み合わせてEvent Filterを実行する。

- Strategyごとの対象イベント
- Eventごとの基本停止方式
- Strategy別の強制終日停止
- Strategy別Override
- Entry予定時刻
- Exit予定時刻
- Event停止ウィンドウ
- 当日および翌日イベント

これにより、重要イベントでは終日停止を維持しながら、必要以上にEntry機会を失わないStrategy別ハイブリッド方式を実現している。
