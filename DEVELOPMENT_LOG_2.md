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

## 2026-06-14：v1.2 Q1分析結果を保存

### 対象

以下のv1.2コードを実行し、クロス円16ロジックにオージー系12ロジックを追加した28ロジック構成でバックテストを実施した。

```text
src/portfolio_backtest_v1_2_add_aussie_logic.py
```

追加内容：

```text
EA：EUR/AUD Rev.4 4ロジック
GA：GBP/AUD 4ロジック
中国実需系 4ロジック
```

---

### 重要修正

v1.2作成時に、JPYペアと非JPYペアでpip換算が異なる問題を修正した。

```text
JPYペア：pip_size = 0.01
非JPYペア：pip_size = 0.0001
```

また、スプレッドは価格値ではなくpips指定に統一した。

```text
spread_pips → spread_price = spread_pips * pip_size
```

これにより、EURAUD / GBPAUD / AUDUSD のSL/TP・損益計算が正しくなるように修正した。

---

### v1.2 全体結果

v1.2の主要結果は以下。

```text
Full 2015/01〜2026/03
Trades：15,265
WinRate：54.48%
PF：1.368
TotalPips：+86,558.7
MaxDD：2,201.7
RoMD：39.31
```

2026 Q1では、クロス円のみのv1.1.1より改善した。

```text
v1.1.1 Q1：+377.2 pips / PF 1.116 / MaxDD 506.3 / RoMD 0.75
v1.2 Q1：+1,358.8 pips / PF 1.237 / MaxDD 600.0 / RoMD 2.26
```

---

### v1.2 Q1分析結果の保存先

Q1分析結果は以下へ保存した。

```text
results/q1_2026_analysis_v2_with_aussie/
```

保存CSV：

```text
Q1_2026_Total_Summary.csv
Q1_2026_Strategy_Summary.csv
Q1_2026_Monthly_Summary.csv
Q1_2026_Daily_Summary.csv
Q1_2026_Exclusion_Test.csv
Q1_2026_Drawdown_Timeline.csv
Q1_2026_Drawdown_Window_Trades.csv
Q1_2026_Group_Summary.csv
Q1_2026_Pair_Summary.csv
Q1_2026_Direction_Summary.csv
Q1_2026_Pair_Direction_Summary.csv
```

---

### 所感

オージー系追加により、2026 Q1の成績は大きく改善した。

特にGAと中国実需系がQ1の補完として機能した。

一方で、2026年2月には集中DDが残っている。

```text
2026年2月：PF 0.870 / Total -276.6 pips / MaxDD 600.0
```

このため、次はロジック単体の停止ではなく、同時被弾を抑えるフィルタ検証へ進む。

---

### 次にやること

次はフィルタ検証 v1 に進む。

優先候補：

```text
1. 同日トレード数制限
2. 同一方向JPYエクスポージャー制限
3. 同一方向AUDエクスポージャー制限
4. 前日値幅フィルタ
5. 直近24時間値幅フィルタ
```

まずは、2026年2月のような複数ロジック同時被弾を抑えるため、同時リスク制限系から検証する。

## 2026-06-14：フィルタ検証 v1 実行

### 対象

`Portfolio_Integration_Results_v1_2_add_aussie_logic.csv` を使用し、後処理で以下のフィルタを検証した。

- 同日トレード数制限
- 同一JPY方向エクスポージャー制限
- 同一AUD方向エクスポージャー制限
- 上記の組み合わせ

### 主な結果

Base結果：

| Period | Trades | PF | TotalPips | MaxDD | RoMD |
|---|---:|---:|---:|---:|---:|
| Full | 15,265 | 1.368 | 86,558.7 | 2,201.7 | 39.31 |
| OOS | 1,541 | 1.403 | 9,885.6 | 872.8 | 11.33 |
| Q1 | 348 | 1.237 | 1,358.8 | 600.0 | 2.26 |

OOS重視の暫定候補：

```text
MaxJPYSameDir_3


