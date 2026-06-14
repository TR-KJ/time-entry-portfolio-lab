# DEVELOPMENT_LOG_3.md

# Time Entry Portfolio Lab 開発ログ 3

## 目的

この開発ログでは、時間固定エントリーポートフォリオを、単純なpips評価から実運用前提の資金管理評価へ移行した後の検証内容を記録する。

---

# 2026-06-14：実運用前提の変更

## 運用前提

これまでの検証は主に以下の指標で評価していた。

```text
TotalPips
PF
MaxDD pips
RoMD = TotalPips / MaxDD
```

しかし、実運用では固定ロットではなく、以下の運用方式を前提にすることにした。

```text
損失額固定型
週ごとの複利運用
```

具体的な条件は以下。

| Item | Value |
|---|---:|
| 初期資金 | 500,000円 |
| 1トレードあたりリスク | 2% |
| 複利更新 | 月曜朝 |
| コード上の複利更新時刻 | 月曜06:00 JST |
| 同時保有時の扱い | 各トレード同じ週の固定リスク額 |

---

# MoneySim v1 作成

## 作成ファイル

```text
src/portfolio_money_management_sim_v1.py
```

## 目的

v1.2のトレード履歴を使って、損失額固定型・週次複利運用の資金曲線を作成する。

## 計算ロジック

```text
週初残高 × 2% = その週の1トレードあたり許容損失額
YenPnL = WeekRiskAmount × (Pips / SL)
```

例：

```text
週初残高：500,000円
1トレードリスク：2%
許容損失額：10,000円

SL 50pipsのロジックで +100pips
R = 100 / 50 = 2.0
損益 = 10,000円 × 2.0 = +20,000円
```

## v1で出力した主なCSV

```text
MoneySim_v1_Combined_PeriodSummary.csv
MoneySim_v1_Combined_Weekly.csv
Base_v1_2_MoneySim_TradeLog.csv
Base_v1_2_MoneySim_Weekly.csv
```

## v1で判明した問題

`MoneySim_v1_Combined_PeriodSummary.csv` を確認したところ、Q1の `MaxDDPct` が不自然な値になっていた。

原因：

```text
Q1やOOSなどの期間を切り出した際に、
期間内だけで50万円から資金曲線を再計算するような扱いになっていた。
```

本来は以下で評価すべき。

```text
2015年から継続運用
↓
2026年Q1時点の実際の残高
↓
その継続資金曲線上でのQ1 MaxDDPctを見る
```

---

# MoneySim v1.1 修正版 作成

## 作成ファイル

```text
src/portfolio_money_management_sim_v1_1.py
```

## 修正内容

v1.1では以下を修正した。

```text
1. Q1 / OOSのMaxDDPctを期間内だけで再計算しない
2. 2015年から継続した資金曲線上で期間内DDを評価する
3. 期間開始時点残高 / 期間終了時点残高 / 期間リターンを出す
4. Base / Filter v1 / Filter v2 のCSVが存在するものだけ自動で読み込む
```

## 保存先

GitHubの保存先は以下。

```text
results/money_sim_v1_1_weekly_fixed_risk/
```

主な保存CSV：

```text
MoneySim_v1_1_Combined_PeriodSummary.csv
MoneySim_v1_1_Combined_YearlySummary.csv
Base_v1_2_MoneySim_v1_1_Weekly.csv
Filter_v1_Best_MoneySim_v1_1_Weekly.csv
Filter_v2_Best_MoneySim_v1_1_Weekly.csv
```

---

# MoneySim v1.1 結果

## 比較対象

以下の3つを比較した。

```text
Base_v1_2
Filter_v1_Best
Filter_v2_Best
```

それぞれの意味：

```text
Base_v1_2
= v1.2 Add Aussie Logic のフィルタなし

Filter_v1_Best
= 同日トレード数制限 / JPY・AUD方向エクスポージャー制限系のBest候補

Filter_v2_Best
= 値幅・ATR系フィルタのBest候補
```

---

## 主要比較

| Dataset | Full RoMD | OOS RoMD | Q1 RoMD | Full MaxDDPct | OOS MaxDDPct | Q1 MaxDDPct |
|---|---:|---:|---:|---:|---:|---:|
| Base_v1_2 | 6.32 | 5.82 | 1.75 | 42.95% | 25.76% | 15.12% |
| Filter_v1_Best | 6.13 | 5.55 | 1.17 | 41.47% | 21.67% | 15.34% |
| Filter_v2_Best | 7.43 | 6.19 | 1.97 | 42.11% | 22.29% | 14.97% |

---

# 判断

## Base_v1_2

Baseは最終残高・成長力が最大。

ただし、DDも重い。

```text
成長力重視ならBaseが最強
ただしMaxDDPctは重い
```

---

## Filter_v1_Best

Filter v1は、同日トレード数制限やJPY/AUD方向制限によってDDを少し下げた。

ただし、成長力とRoMDが弱く、現時点では優先度は低め。

```text
Filter_v1_Bestは現時点では本命ではない
```

---

## Filter_v2_Best

Filter v2は、成長を少し抑える代わりに、Full / OOS / Q1すべてでRoMDがBaseより改善した。

```text
Filter_v2_Bestは現時点の暫定本命候補
```

特に重要な点：

```text
Full RoMD：6.32 → 7.43
OOS RoMD：5.82 → 6.19
Q1 RoMD：1.75 → 1.97
Q1 MaxDDPct：15.12% → 14.97%
```

---

# 注意点

2%リスクの週次複利は、シミュレーション上では非常に大きく増える。

長期運用では最終残高が非現実的な水準まで増幅されるため、金額そのものは絶対値として見すぎない。

今後は以下を重視する。

```text
MaxDDPct
Money RoMD
週次損失
OOS成績
Q1など直近不調期での耐久性
```

---

# 現時点の結論

```text
成長力重視：Base_v1_2
リスク効率重視：Filter_v2_Best
Filter_v1_Best：現時点では優先度低め
```

今後の検証では、pipsベースではなく、損失額固定型・週次複利ベースで評価する。

---

# 次にやること

次は以下のコードを作成する。

```text
src/money_filter_compare_v1.py
```

目的：

```text
Filter v1 / Filter v2 の全候補を、
pips RoMDではなく、
円ベース・週次複利・MaxDDPct・Money RoMDで再ランキングする。
```

比較対象候補：

```text
Base
MaxJPYSameDir_3
MaxTrades_7
Range24hPips_LTE_P85
H1_ATR14_Pips_LTE_P70
その他Filter v1 / v2候補
```

見る指標：

```text
FinalEquity
NetProfitYen
MaxDDYen
MaxDDPct
Money RoMD
OOS Money RoMD
Q1 Money RoMD
Worst WeekReturnPct
```

この結果をもとに、実運用向けの本命フィルタを選定する。
