# Step 9.2.4 — 2026年後半イベントカレンダー/JST監査

更新日: 2026-08-28

Event Candidate Cの停止対象、DATE_ALL_DAY/POSITION_OVERLAP、pre/post時間窓は変更せず、公式日程とJST時刻だけを更新した。DST対象は日付別テーブルを優先し、inputは未登録日付のfallbackとして残す。

## 2026年残り（JST）

| Event | JST date/time |
|---|---|
| FOMC statement | 09/17 03:00, 10/29 03:00, 12/10 04:00 |
| US NFP | 09/04 21:30, 10/02 21:30, 11/06 22:30, 12/04 22:30 |
| US CPI | 09/11 21:30, 10/14 21:30, 11/10 22:30, 12/10 22:30 |
| BOJ | 09/18, 10/30, 12/18 |
| BOE | 09/17 20:00, 11/05 21:00, 12/17 21:00 |
| ECB | 09/10 21:15, 10/29 22:15, 12/17 22:15 |
| RBA | 09/29 13:30, 11/03 12:30, 12/08 12:30 |
| AU CPI（従来の四半期対象） | 10/28 09:30 |

BOJの結果公表時刻は固定されないため、日付停止は従来どおり。1_EJ_Log1のoverlapは既存fallback 12:00 JSTを維持する。

AU CPIは戦略変更を避けるため月次CPIへ拡張せず、従来の四半期CPI対象を維持する。2026年残りは10/28のみを対象とし、JST時刻だけ09:30へ精密化する。

## 1_EJ_Log1 CPI week Wednesday

残りは 09/09, 10/14, 11/11, 12/09。CPI公表日そのものではなく、公表週の水曜日を保持する。

## 実装

- 日付配列を2026-08-28時点の公式日程へ更新。
- DST影響対象は `EVENT_JST_2026` の日付別JST時刻を優先。
- AU CPIの日付配列は従来の四半期対象（1/28、4/29、7/29、10/28）を維持し、月次対象へ拡張しない。
- Step9.2.4のUS NFP/FOMC/ECB overlapも同じテーブルを参照。
- 戦略ロジック、停止対象、停止ポリシー、時間窓は変更しない。

## 一次情報

Federal Reserve FOMC calendar、U.S. BLS NFP/CPI schedules、Bank of Japan meeting schedule、Bank of England MPC dates、ECB Governing Council calendar、RBA board schedule/calendar、ABS CPI future releases。
