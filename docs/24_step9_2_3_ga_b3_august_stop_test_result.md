# Step9.2.3 GA_B3 August Stop Test Result

## 1. 概要

Step9.2.2の全挙動を維持したまま、`21_GA_B3` に対して「8月は新規エントリー停止」の条件を追加した。

対象EA：

`src/EA/time_entry_step9_2_3_ga_b3_august_stop_28strategies.mq5`

Commit SHA：

`57ed096762b2d854941e67b4939a86337e73fea3`

---

## 2. 変更内容

対象戦略：

- No.21
- Strategy ID：`GA_B_3`
- Strategy Code：`21_GA_B3`
- Pair：`GBPAUD`
- Direction：Long
- Weekday：Mon
- Entry JST：21:02
- Exit JST：10:00
- Exit Offset：+1 day
- SL：220
- TP：100

追加条件：

- JSTの月が8月の場合、新規エントリーを停止する

停止ログ：

`GA_B3_AUG_STOP`

---

## 3. 変更対象外

以下は変更していない。

- Step9.2.2の既存ロジック
- RBA overlapロジック
- Event Candidate C
- 17_EA_1B
- 18_EA_2
- 20_EA_1A
- その他の27戦略

EA系の8月停止については既存実装を維持している。

### 既存の8月停止対象

- `17_EA_1B_Wed_Short`
- `18_EA_2_MonWed_Short`
- `20_EA_1A_MonTue_Short`

GA系で8月停止を追加したのは `21_GA_B3` のみ。

---

## 4. 8月停止テスト

### テスト条件

Mock JST：

`2026/08/10 21:02`

有効戦略：

`21_GA_B3` のみ

### 確認ログ

```text
[Step6.3 Stops 21_GA_B_3] EVENT REJECT. Symbol=GBPAUD, Event=GA_B3_AUG_STOP, Date=20260810

[Step6.3 Stops 21_GA_B_3] Skip entry: entry filter rejected.
```

### 結果

PASS

8月の `21_GA_B3` は注文処理へ進まず、正常に新規エントリーが停止した。

---

## 5. 8月以外の通過テスト

### テスト条件

Mock JST：

`2026/09/14 21:02`

有効戦略：

`21_GA_B3` のみ

### 確認ログ

```text
[Step7 Lot 21_GA_B_3] LOT FIXED. Symbol=GBPAUD, Lot=0.01

[Step6.3 Stops 21_GA_B_3] BUY entry success. Symbol=GBPAUD, Lot=0.01, Ask=1.91270, SL=1.89070, TP=1.92270
```

### 結果

PASS

9月では `GA_B3_AUG_STOP` は発生せず、正常にエントリーした。

---

## 6. Strategy Master List更新

`docs/01_strategy_master_list.md`

の `21_GA_B3` の Individual Stop を以下に更新。

`8月`

これにより、

- Strategy Master List
- Step9.2.3実装
- DELL実機テスト

の3点が一致した。

---

## 7. 通常運用設定

Step9.2.3には新しいinput項目を追加していないため、Step9.2.2で使用していたSETファイルをそのまま利用可能。

### デモ

EA：

`time_entry_step9_2_3_ga_b3_august_stop_28strategies`

SET：

`step9_2_2_forward_verified.set`

### 実口座

EA：

`time_entry_step9_2_3_ga_b3_august_stop_28strategies`

SET：

`step9_2_2_live_dell_minilot_verified.set`

---

## 8. 実口座 初期化確認

実口座MT5でStep9.2.3をコンパイル。

結果：

`0 errors, 0 warnings`

確認した主要設定：

```text
EmergencyStop=false
FixedLot=0.01
LotMode=0
MaxAutoLot=0.01

JST Offset Hours=6

TestMode=false
UseTestTimes=false
UseMockJstDateTime=false

UseGlobalAtrP70Filter=false

UseEventFilter=true
UseEventCandidateC=true
SuppressEventLogsOncePerDay=true
```

Lot Mode確認：

```text
LOT MODE CHECK. Mode=Fixed Lot, FixedLot=0.01
```

28戦略すべて `Enabled=true` を確認。

---

## 9. 現在の運用状態

### DELL デモ口座

- EA：Step9.2.3
- 通常フォワード設定
- Mock：OFF
- TestMode：OFF
- Algo Trading：ON

### DELL 実口座

- EA：Step9.2.3
- Fixed Lot：0.01
- Mock：OFF
- TestMode：OFF
- Event Filter：ON
- Candidate C：ON
- ATR Filter：OFF
- Algo Trading：ON

---

## 10. 判定

Step9.2.3の `21_GA_B3` 8月停止修正は正常に完了。

確認済み：

- 8月停止：PASS
- 8月以外通過：PASS
- コンパイル：PASS
- 実口座初期化：PASS
- Master List反映：完了
- デモStep9.2.3切替：完了
- 実口座Step9.2.3切替：完了

以上により、Step9.2.3を現行運用版とする。
