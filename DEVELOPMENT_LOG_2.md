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
