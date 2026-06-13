# DEVELOPMENT_LOG_2.md

# Time Entry Portfolio Lab 開発ログ 2

## 目的

この開発ログでは、EA / GA / AU / オージー絡みロジックの追加、および v1.2 以降のポートフォリオ拡張について記録する。

既存の `DEVELOPMENT_LOG.md` が長くなってきたため、クロス円16ロジックの初期検証以降は本ファイルに分離する。

---

# 2026-06-13：オージー系追加前の整理

## 現在の状態

現行マスター16ロジックについて、以下の検証まで完了。

```text
src/portfolio_backtest_v1_1_engine_fix.py
```

対象：

- USDJPY
- EURJPY
- GBPJPY
- AUDJPY

出力結果：

```text
results/v1_1_engine_fix/
```

Q1分析結果：

```text
results/q1_2026_analysis_v1_cross_jpy/
```

---

## Q1分析の要約

2026年Q1のクロス円16ロジック成績：

```text
Trades：183
WinRate：51.91%
PF：1.091
TotalPips：+297.2
MaxDD：583.7
RoMD：0.51
```

Q1で特に悪化したロジック：

```text
1_EJ_Log1
12_UJ_Short_Core
8_AJ_Core1
9_AJ_Core2
5_GJ_Port_Log2
```

Q1で支えたロジック：

```text
4_GJ_Port_Log1
3_EJ_NightBlitz_21
13_UJ_Fix_MidWeek
2_EJ_NightBlitz_20
7_GJ_Mon_Blitz
```

---

## フィルタ検証の方針

クロス円単体のQ1分析では、特定ロジック・特定日・JPY方向の偏りがDDに影響している可能性が見えた。

ただし、今後EA / GA / AU / オージー絡みロジックを追加するため、クロス円単体だけでフィルタを確定しない。

方針：

```text
1. クロス円16ロジックのQ1分析は完了
2. v1.2でEA / GA / AU / オージー絡みロジックを追加
3. オージー込みで再度Q1分析
4. クロス円単体とオージー込みを比較
5. 最終的なフィルタ検証へ進む
```

---

# v1.2 追加予定

予定ファイル：

```text
src/portfolio_backtest_v1_2_add_aussie_logic.py
```

追加予定グループ：

## 1. EA：EUR/AUD

EUR/AUD Rev.4の複数ロジックを追加予定。

対象：

- 1A_MonTue_Short
- 1B_Wed_Short
- 2_MonWed_Short
- 3_WedThu_Long

## 2. GA：GBP/AUD

GBP/AUD追加ロジックを追加予定。

対象：

- GA_B_3
- GA_C_2
- GA_F_2
- GA_D_1

## 3. 中国実需系

対象：

- AUDUSD Long
- AUDJPY Long
- EURAUD Short
- GBPAUD Short

AUDUSDのみ、毎月9日〜15日に加えて25日〜月末も稼働する。

---

## オージー系で注意するイベント

対象イベント：

```text
RBA
AUD CPI
US NFP
US CPI
FOMC
ECB
BOE
```

FOMCについては、オージー系では前日・当日停止が必要。

---

## 次の作業

次に行うこと：

```text
1. EA / GA / 中国実需系ロジックの条件を一覧表に整理
2. v1.2コードに追加
3. v1.2をColabで実行
4. v1.2のPeriod Summary / Strategy Summaryを保存
5. v1.2でQ1分析コードを再実行
```

## 2026-06-13：v1.1.1 AJイベントフィルター修正

### 目的

v1.1では、AUDJPY用イベントフィルターにECBが含まれていた。

ただし、AUDJPYのロジック思想としてECB停止は不要と判断し、v1.1.1ではAJ用イベントを以下に修正した。

```text
v1.1：7 events for AJ = US CPI / NFP / FOMC / BOJ / ECB / RBA / AUD CPI
v1.1.1：6 events for AJ = US CPI / NFP / FOMC / BOJ / RBA / AUD CPI
```

---

### 影響を受けたロジック

主に影響を受けたのは以下。

```text
9_AJ_Core2
```

v1.1 → v1.1.1の変化：

| Version | Trades | PF | TotalPips | MaxDD |
|---|---:|---:|---:|---:|
| v1.1 | 258 | 1.477 | +1,402.4 | 290.5 |
| v1.1.1 | 301 | 1.571 | +1,924.8 | 237.6 |

差分：

```text
Trades：+43
TotalPips：+522.4
PF：+0.094
MaxDD：-52.9
```

---

### 全体結果

| Version | Trades | PF | TotalPips | MaxDD | RoMD |
|---|---:|---:|---:|---:|---:|
| v1.1 | 8,406 | 1.430 | +54,464.5 | 1,533.4 | 35.52 |
| v1.1.1 | 8,448 | 1.432 | +54,996.5 | 1,542.5 | 35.65 |

v1.1.1ではMaxDDはわずかに増えたが、TotalPipsとRoMDが改善した。

---

### 2026 Q1結果

トレード履歴ベースでは、Q1結果は以下。

| Version | Trades | PF | TotalPips | MaxDD | RoMD |
|---|---:|---:|---:|---:|---:|
| v1.1 | 183 | 1.091 | +297.2 | 583.7 | 0.51 |
| v1.1.1 | 184 | 1.116 | +377.2 | 506.3 | 0.75 |

Q1でも改善。

特に、2026/02/05の `9_AJ_Core2` が+80pipsとなり、ECB停止を外した効果が確認できた。

---

### 注意点：期間集計の終了時刻

`Portfolio_Period_Summary_v1_1_1engine_fix.csv` では、期間終了日が `2026-03-31` となっており、これは内部的に `2026-03-31 00:00:00` と扱われる。

そのため、2026-03-31 05:27のトレードが期間集計から漏れている。

次回修正：

```python
'end': '2026-03-31 23:59:59'
```

Full / Legacy OOS / Strict OOS の終了時刻も同様に修正する。

---

### 採用判断

v1.1.1をクロス円16ロジックの本命版とする。

次回以降の開発は、v1.1.1をベースにする。

次の予定：

```text
v1.2_add_aussie_logic.py
```

EA / GA / AU / オージー絡み中国実需ロジックを追加する。
