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
