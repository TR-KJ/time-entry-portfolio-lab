# 07_forward_test_weekend_guard_note.md

# フォワード運用中の週末ログ・Weekend Guard整理メモ

## 対象EA

```text
time_entry_step8_3_1_config_managed_28strategies_forward_test_ready_skiplog_compile_fixed.mq5
```

---

## 確認日

```text
2026-06-27
```

---

## 確認内容

フォワード運用中、2026-06-27 土曜日のログを確認した。

日付変更直後に、複数ロジックで以下のような `Date rule reject` が出ていた。

```text
13_UJ_Fix_MidWeek：Date rule reject: not Wed/Thu
14_UJ_Sat_3rd：Date rule reject: not 3rd
15_UJ_Sat_Aug：Date rule reject: not August
16_UJ_T10A：Date rule reject: not 10th
25_AU_China_Demand：Date rule reject: not weekday
26_AJ_China_Demand：Date rule reject: not weekday
27_EA_China_Demand：Date rule reject: not weekday
28_GA_China_Demand：Date rule reject: not weekday
9_AJ_Core2：Date rule reject: not Thursday
```

また、同日 08:04 JST に以下を確認した。

```text
12_UJ_Short_Core：ATR REJECT
Symbol=USDJPY
JST=2026.06.27 08:04
```

---

## 判定

`Date rule reject` の内容自体は正常。

各ロジックが「その日はEntry対象日ではない」と判定しているだけであり、売買事故ではない。

また、`12_UJ_Short_Core` についても、ATR REJECTによりEntryは発生していない。

```text
発注なし
ポジションなし
売買事故なし
```

---

## 気になる点

土曜日 08:04 JST は、通常のFX市場としてはクローズ中。

そのため、本来は `12_UJ_Short_Core` がATR判定まで進む前に、共通の週末・市場クローズ判定で停止する方が自然。

現状は以下のような順序で判定されている可能性がある。

```text
Entry時刻確認
↓
Date Rule
↓
Event Filter
↓
ATR Filter
↓
OrderSend
```

そのため、土曜日でもEntry時刻に到達したロジックがATR判定まで進むことがある。

---

## 修正方針

この問題は `12_UJ_Short_Core` 専用ではなく、全戦略共通で対応した方がよい。

理由：

```text
12番だけが特別に危険というより、
今回たまたま12_UJ_Short_Coreが土曜日08:04のEntry候補時刻に到達しただけ。

他の戦略でも、土日や市場クローズ中にEntry時刻へ到達すれば、
同様にDate Rule / Event / ATR判定まで進む可能性がある。
```

したがって、次回修正では全28戦略共通の `Weekend / Market Closed Guard` を追加する。

---

## 理想の判定順

修正後の理想順：

```text
TryEntry()
↓
Enabled確認
↓
Symbol確認
↓
Entry時刻確認
↓
Weekend / Market Closed Guard
↓
EmergencyStop確認
↓
Date Rule
↓
Event Filter
↓
ATR Filter
↓
AlreadyEnteredToday
↓
HasOpenPosition
↓
OrderSend
```

土日・市場クローズ中は、ATR判定より前に停止する。

---

## 想定ログ

修正後は、土曜日・日曜日など市場クローズ中にEntry時刻へ到達した場合、以下のようなログで止める。

```text
Skip entry: weekend / market closed. Strategy=12_UJ_Short_Core, JST=2026.06.27 08:04
```

このログは12番専用ではなく、全戦略共通で使用する。

---

## Date rule rejectログについて

日付変更直後に複数戦略の `Date rule reject` が出ること自体は異常ではない。

ただし、フォワード運用ログとしてはやや見づらいため、今後の改善候補とする。

改善案：

```text
Date rule reject はEntry Window内だけ出す
または
日付変更直後の一括Date rule rejectログは出さない
```

---

## 次回修正候補

```text
Step 9.5：Forward Log / Weekend Guard 整理版
```

修正候補：

```text
1. 全戦略共通のWeekend / Market Closed Guardを追加
2. 土日・市場クローズ日はATR判定より前に止める
3. Date rule rejectログをEntry Window内中心に整理
4. Weekend Guardログも同一日付・同一Strategyでは1回だけに抑制
```

---

## 現時点の運用判断

今回のログは、即停止が必要なものではない。

```text
EAは稼働中
Entry / Exitは概ね正常
売買事故なし
土曜日のATR REJECTは判定順改善候補
```

したがって、現在のフォワードテストは継続可能。

ただし、次回EA修正では、全戦略共通のWeekend Guard追加を優先検討する。
