# 01_strategy_master_list.md

# 時間固定エントリー戦略 全ロジック一覧

## 目的

このドキュメントは、時間固定エントリー・時間固定決済ポートフォリオで使用する各ロジックの条件を一覧化するためのマスターリストである。

今後、Pythonコードの条件確認、バックテスト結果の比較、フィルタ検証、実運用チェックに使用する。

---

# 1. クロス円マスター16ロジック

## EURJPY

| No | Strategy ID | Pair | Direction | Weekday | Entry JST | Exit JST | Exit Offset | SL | TP | Event Filter | Individual Stop |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 1 | 1_EJ_Log1 | EURJPY | Long | Mon, Wed | 13:55 | 04:55 | +1 day | 70 | 250 | CPI Wednesday | February, day 1, year-end |
| 2 | 2_EJ_NightBlitz_20 | EURJPY | Long | Mon, Wed | 20:56 | 04:45 | +1 day | 45 | 70 | 5 events with ECB | year-end |
| 3 | 3_EJ_NightBlitz_21 | EURJPY | Long | Mon, Wed | 21:56 | 05:27 | +1 day | 75 | 70 | 5 events with ECB | year-end |

---

## GBPJPY

| No | Strategy ID | Pair | Direction | Weekday | Entry JST | Exit JST | Exit Offset | SL | TP | Event Filter | Individual Stop |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 4 | 4_GJ_Port_Log1 | GBPJPY | Long | Tue, Wed | 00:00 | 08:55 | same day | 130 | 90 | none | December, day 1/2/29/30/31, year-end |
| 5 | 5_GJ_Port_Log2 | GBPJPY | Short | Tue, Thu, Fri | 09:55 | 23:55 | same day | 90 | none | 5 events with BOE | day 18/19/27, year-end |
| 6 | 6_GJ_Old_Mon | GBPJPY | Long | Mon | 15:45 | 22:50 | same day | 50 | 210 | 5 events with BOE | January, February, year-end |
| 7 | 7_GJ_Mon_Blitz | GBPJPY | Long | Mon | 18:02 | 23:02 | same day | 130 | 250 | 5 events with BOE | year-end |

---

## AUDJPY

| No | Strategy ID | Pair | Direction | Weekday | Entry JST | Exit JST | Exit Offset | SL | TP | Event Filter | Individual Stop |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 8 | 8_AJ_Core1 | AUDJPY | Long | Mon | 08:01 | 22:46 | same day | 70 | 110 | 6 events for AJ | year-end |
| 9 | 9_AJ_Core2 | AUDJPY | Short | Thu | 17:14 | 01:14 | +1 day | 30 | 80 | 6 events for AJ | June, September, day 1/20/26〜month-end, year-end |
| 10 | 10_AJ_SatA | AUDJPY | Short | Fri | 10:58 | 13:51 | same day | 50 | 25 | 6 events for AJ | year-end |
| 11 | 11_AJ_SatB | AUDJPY | Short | Fri | 18:57 | 01:43 | +1 day | 55 | 95 | 6 events for AJ | year-end |

---

## USDJPY

| No | Strategy ID | Pair | Direction | Weekday / Date Rule | Entry JST | Exit JST | Exit Offset | SL | TP | Event Filter | Individual Stop |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 12 | 12_UJ_Short_Core | USDJPY | Short | 20日〜月末、21/22/水曜/8月/カレンダー末日は停止 | Goto: 09:55 / Normal: 08:04 | 14:56 | same day | Goto: 20 / Normal: 50 | Goto: 50 / Normal: none | 4 events | year-end |
| 13 | 13_UJ_Fix_MidWeek | USDJPY | Long | 25日以降の水曜・木曜 | 18:04 | 22:03 | same day | 95 | 95 | 4 events | year-end |
| 14 | 14_UJ_Sat_3rd | USDJPY | Short | 毎月3日 | 20:01 | 03:08 | +1 day | 45 | 70 | 4 events | year-end |
| 15 | 15_UJ_Sat_Aug | USDJPY | Short | 8月1日〜10日 | 19:00 | 23:30 | same day | 20 | 35 | 4 events | year-end |
| 16 | 16_UJ_T10A | USDJPY | Long | 毎月10日、水曜は停止 | 02:58 | 09:50 | same day | 45 | 110 | BOJ only | year-end |

---

# 2. イベントフィルター定義

## 4 events

対象：

- US CPI
- US NFP
- FOMC
- BOJ

主な対象：

- USDJPY
- 一部クロス円ロジック

---

## 5 events with ECB

対象：

- US CPI
- US NFP
- FOMC
- BOJ
- ECB

主な対象：

- EURJPY

---

## 5 events with BOE

対象：

- US CPI
- US NFP
- FOMC
- BOJ
- BOE

主な対象：

- GBPJPY

---

## 6 events for AJ

対象：

- US CPI
- US NFP
- FOMC
- BOJ
- RBA
- AUD CPI

主な対象：

- AUDJPY

---

# 3. 検証エンジン仕様

## 時刻

すべてJST基準。

MT5データは `Europe/Helsinki` として読み込み、`Asia/Tokyo` に変換する。

---

## スプレッド処理

現行方式：

```text
spread_mode = entry_adjust
```

Long：

```text
Entry = Open + spread
```

Short：

```text
Entry = Open - spread
```

---

## SL/TP同一足判定

1分足の同一足内でSLとTPの両方に到達した場合、SLを優先する。

```text
same_bar_policy = sl_first
```

---

# 4. 今後追加予定のロジック

次バージョン `v1.2_add_aussie_logic.py` で、以下を追加予定。

| Group | Pair | Description |
|---|---|---|
| GA | GBPAUD | GBP/AUD追加ロジック |
| EA | EURAUD | EUR/AUD追加ロジック |
| AU China Demand | AUDUSD | 中国実需狙い |
| AJ China Demand | AUDJPY | 中国実需狙い |
| EA China Demand | EURAUD | 中国実需狙い |
| GA China Demand | GBPAUD | 中国実需狙い |

# 5. v1.2 追加予定：オージー系ロジック

## 目的

v1.2では、現行クロス円16ロジックに加えて、以下のオージー系ロジックを追加する。

```text
EA：EUR/AUD Rev.4 4ロジック
GA：GBP/AUD 4ロジック
中国実需系：4ロジック

合計：12ロジック追加
```

v1.2追加後は、クロス円16ロジック + オージー系12ロジックの合計28ロジックでポートフォリオ検証を行う。

---

# 5.1 EA：EUR/AUD Rev.4 4ロジック

## EA共通仕様

| Item | Value |
|---|---|
| Pair | EURAUD |
| Timezone | JST |
| Common Event Stop | RBA / AUD CPI / NFP / US CPI / FOMC / ECB |
| FOMC Stop | FOMC当日のみ停止 |
| Month-End Stop | 月末最終営業日・月末2営業日前・月末3営業日前 |
| Seasonal Stop | 10月全停止 |
| Year-End Stop | 12/25〜1/3停止 |
| Spread Requirement | 平常時スプレッド1.5pips以下推奨 |

---

## EAロジック一覧

| No | Strategy ID | Pair | Direction | Weekday | Entry JST | Exit JST | Exit Offset | SL | TP | Individual Stop | Event Filter |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 17 | EA_1B_Wed_Short | EURAUD | Short | Wed | 09:59 | 20:58 | same day | 70 | 175 | 8月 | EA Common Events |
| 18 | EA_2_MonWed_Short | EURAUD | Short | Mon, Tue, Wed | 09:59 | 05:26 | +1 day | 90 | 180 | 1月・8月 | EA Common Events |
| 19 | EA_3_WedThu_Long | EURAUD | Long | Wed, Thu | 20:56 | 10:00 | +1 day | 90 | none | none | EA Common Events |
| 20 | EA_1A_MonTue_Short | EURAUD | Short | Mon, Tue | 10:01 | 16:00 | same day | 50 | 125 | 8月 | EA Common Events |

---

# 5.2 GA：GBP/AUD 4ロジック

## GA共通仕様

| Item | Value |
|---|---|
| Pair | GBPAUD |
| Timezone | JST |
| Common Event Stop | BOE / RBA / AUD CPI / NFP / US CPI / FOMC |
| FOMC Stop | FOMC当日のみ停止 |
| Year-End Stop | 12/25〜1/3停止 |
| ECB Stop | なし |

---

## GAロジック一覧

| No | Strategy ID | Pair | Direction | Weekday | Entry JST | Exit JST | Exit Offset | SL | TP | Individual Stop | Event Filter |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 21 | GA_B_3 | GBPAUD | Long | Mon | 21:02 | 10:00 | +1 day | 220 | 100 | none | GA Common Events |
| 22 | GA_C_2 | GBPAUD | Long | Thu | 16:56 | 01:15 | +1 day | 70 | 80 | none | GA Common Events |
| 23 | GA_F_2 | GBPAUD | Short | Fri | 19:42 | 22:45 | same day | 90 | 200 | none | GA Common Events |
| 24 | GA_D_1 | GBPAUD | Long | Fri | 22:44 | 03:08 | +1 day | 90 | 200 | none | GA Common Events |

---

# 5.3 中国実需系 4ロジック

## 中国実需系 共通仕様

| Item | Value |
|---|---|
| Timezone | JST |
| Base Weekday | Mon-Fri |
| Main Date Rule | 毎月9日〜15日 |
| FOMC Stop | FOMC前日・当日停止 |
| Year-End Stop | 12/25〜1/3停止 |

---

## 中国実需系ロジック一覧

| No | Strategy ID | Pair | Direction | Weekday | Date Rule | Entry JST | Exit JST | Exit Offset | SL | TP | Exclude Month | Event Filter |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|
| 25 | AU_China_Demand | AUDUSD | Long | Mon-Fri | 9〜15日、25日〜月末 | 10:00 | 15:50 | same day | 40 | 40 | 8月・10月 | RBA / AUD CPI / FOMC前日・当日 |
| 26 | AJ_China_Demand | AUDJPY | Long | Mon-Fri | 9〜15日 | 10:00 | 15:50 | same day | 45 | 80 | 2月・8月・10月 | BOJ / RBA / AUD CPI |
| 27 | EA_China_Demand | EURAUD | Short | Mon-Fri | 9〜15日 | 10:00 | 15:50 | same day | 60 | 60 | 8月・10月 | RBA / AUD CPI / FOMC前日・当日 / ECB |
| 28 | GA_China_Demand | GBPAUD | Short | Mon-Fri | 9〜15日 | 10:00 | 16:10 | same day | 75 | 70 | 8月・10月 | RBA / AUD CPI / FOMC前日・当日 / BOE |

---

# 5.4 v1.2 イベントフィルター定義

## EA Common Events

対象：

- US CPI
- NFP
- FOMC
- ECB
- RBA
- AUD CPI

追加停止：

- 月末最終営業日
- 月末2営業日前
- 月末3営業日前
- 10月全停止
- 年末年始 12/25〜1/3

備考：

```text
EA Rev.4ではFOMCは当日のみ停止。
FOMC前日は停止しない。
```

---

## GA Common Events

対象：

- US CPI
- NFP
- FOMC
- BOE
- RBA
- AUD CPI

追加停止：

- 年末年始 12/25〜1/3

備考：

```text
GAではECB停止は使用しない。
FOMCは当日のみ停止。
```

---

## AU China Events

対象：

- RBA
- AUD CPI
- FOMC前日
- FOMC当日

追加停止：

- 8月全停止
- 10月全停止
- 年末年始 12/25〜1/3

備考：

```text
AUDUSDのみ、毎月9日〜15日に加えて25日〜月末も稼働する。
```

---

## AJ China Events

対象：

- BOJ
- RBA
- AUD CPI

追加停止：

- 2月全停止
- 8月全停止
- 10月全停止
- 年末年始 12/25〜1/3

---

## EA China Events

対象：

- RBA
- AUD CPI
- FOMC前日
- FOMC当日
- ECB

追加停止：

- 8月全停止
- 10月全停止
- 年末年始 12/25〜1/3

---

## GA China Events

対象：

- RBA
- AUD CPI
- FOMC前日
- FOMC当日
- BOE

追加停止：

- 8月全停止
- 10月全停止
- 年末年始 12/25〜1/3

---

# 5.5 v1.2 実装メモ

## 追加するデータ

v1.2では、既存のクロス円データに加えて、以下の1分足データを読み込む。

```text
euraud_m1
gbpaud_m1
audusd_m1
```

既存の `audjpy_m1` は、AJ中国実需系でも再利用する。

---

## 追加するイベント関数

v1.2では、以下のイベント判定を追加する。

```text
is_month_end_3_biz_days()
is_fomc_prev_or_today()
filter_ea_rev4()
filter_ga()
filter_au_china()
filter_aj_china()
filter_ea_china()
filter_ga_china()
```

---

## v1.2での出力予定

ファイル名：

```text
src/portfolio_backtest_v1_2_add_aussie_logic.py
```

結果保存先：

```text
results/v1_2_add_aussie_logic/
```

出力CSV：

```text
Portfolio_Integration_Results_v1_2_add_aussie_logic.csv
Portfolio_Period_Summary_v1_2_add_aussie_logic.csv
Portfolio_Strategy_Summary_v1_2_add_aussie_logic.csv
Portfolio_ExitReason_Summary_v1_2_add_aussie_logic.csv
```

---

# 5.6 v1.2後の分析予定

v1.2実行後、以下を確認する。

```text
1. v1.1.1クロス円16ロジックとの比較
2. オージー系12ロジック単体の成績
3. 2026 Q1でオージー系がDDを補完したか
4. AUD方向の偏りが増えすぎていないか
5. JPY方向とAUD方向の同時リスク
6. フィルタ検証に進むべき対象
```

v1.2のQ1分析結果を見た後、フィルタ検証へ進む。
