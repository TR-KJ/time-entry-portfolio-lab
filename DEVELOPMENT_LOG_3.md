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

## 2026-06-14：H1 ATR P70フィルタ深掘り

### 対象

MoneyFilterCompare v1 で最有力となった以下のフィルタを深掘りした。

```text
V2_H1_ATR14_Pips_LTE_P70
```

意味：

```text
H1 ATR(14) が、Strict IS期間の同ペア分布で70パーセンタイル以下の時だけエントリー
```

つまり、通貨ペアごとに過去のH1 ATR水準を見て、そのペアにとって上位30%に入るような高ボラ局面ではエントリーを見送るフィルタ。

---

### 使用コード

```text
src/money_filter_deep_dive_v1.py
```

### 保存先

```text
results/money_filter_deep_dive_v1/
```

### 主な出力CSV

```text
DeepDive_H1_ATR_P70_Money_Period_Summary.csv
DeepDive_H1_ATR_P70_Pips_Period_Summary.csv
DeepDive_H1_ATR_P70_Strategy_Exclusion_Impact.csv
DeepDive_H1_ATR_P70_Q1_Daily_Impact.csv
DeepDive_H1_ATR_P70_ATR_Ratio_Bucket_Summary.csv
```

---

## 結果概要

### MoneySimベース

損失額固定型・週次複利・1トレードリスク2%で比較した。

| Dataset | Period | Trades | MaxDDPct | MoneyRoMD | PF_Yen |
|---|---|---:|---:|---:|---:|
| Base | Full | 15,265 | 42.95% | 6.32 | 1.325 |
| Accepted H1 ATR P70 | Full | 10,557 | 42.18% | 11.99 | 1.430 |
| Base | OOS | 1,541 | 25.76% | 5.82 | 1.315 |
| Accepted H1 ATR P70 | OOS | 946 | 16.74% | 8.97 | 1.451 |
| Base | Q1 | 348 | 15.12% | 1.75 | 1.194 |
| Accepted H1 ATR P70 | Q1 | 182 | 8.23% | 3.25 | 1.466 |

### 判断

H1 ATR P70フィルタは、実運用前提ではかなり有効。

特にOOSと2026 Q1で、MaxDDPctとMoneyRoMDが大きく改善した。

```text
OOS MaxDDPct：25.76% → 16.74%
Q1 MaxDDPct：15.12% → 8.23%
Q1 MoneyRoMD：1.75 → 3.25
```

---

## 重要な気づき

### 高ATR側も長期ではプラス

Pipsベースでは、除外された高ATRトレード全体もプラスだった。

| Dataset | Full TotalPips | Full PF | Full RoMD |
|---|---:|---:|---:|
| Accepted | +44,270.6 | 1.309 | 26.44 |
| Rejected | +42,288.1 | 1.459 | 31.61 |

つまり、H1 ATR P70は「悪いトレードだけを除外するフィルタ」ではない。

正しい解釈は以下。

```text
高ボラ時の大きな資金変動を抑えて、
週次複利運用の耐久性を上げる防御型フィルタ
```

---

## 2026 Q1での効果

Q1では、除外側がかなり弱かった。

| Dataset | Q1 Trades | Q1 TotalPips | Q1 MaxDD | Q1 RoMD |
|---|---:|---:|---:|---:|
| Accepted | 182 | +1,161.0 | 349.8 | 3.32 |
| Rejected | 166 | +197.8 | 745.9 | 0.27 |

特に、以下の日はH1 ATR P70による除外がDD抑制に大きく効いた。

| Date | All Pips | Accepted | Rejected | Improvement |
|---|---:|---:|---:|---:|
| 2026-02-02 | -228.6 | 0.0 | -228.6 | +228.6 |
| 2026-03-23 | -211.1 | -7.9 | -203.2 | +203.2 |
| 2026-01-26 | -184.5 | -0.4 | -184.1 | +184.1 |
| 2026-02-12 | -181.0 | 0.0 | -181.0 | +181.0 |

一方で、以下のように高ATRで大きく勝っていた日も除外している。

| Date | All Pips | Accepted | Rejected | Improvement |
|---|---:|---:|---:|---:|
| 2026-03-09 | +402.2 | 0.0 | +402.2 | -402.2 |
| 2026-02-10 | +173.1 | -82.2 | +255.3 | -255.3 |
| 2026-03-10 | +230.6 | +69.4 | +161.2 | -161.2 |

そのため、H1 ATR P70は防御力が高いが、爆益日も捨てるフィルタである。

---

## ロジック別の示唆

全ロジック共通でH1 ATR P70をかけると、強い高ATRトレードも除外してしまう。

除外側が大きくプラスだったロジック例：

| Strategy | Rejected Pips | Accepted Pips | Comment |
|---|---:|---:|---|
| 24_GA_D_1 | +1,855.9 | +366.4 | 高ATR側がかなり強い |
| 8_AJ_Core1 | +2,054.1 | +880.0 | 高ATR側も強い |
| 13_UJ_Fix_MidWeek | +1,061.9 | +650.7 | 高ATR側が良い |
| 22_GA_C_2 | +1,071.2 | +1,498.4 | 両方良い |
| 26_AJ_China_Demand | +1,188.9 | +1,273.0 | 両方良い |

一方で、Accepted側が弱いものもある。

```text
10_AJ_SatA
Accepted：-91.0 pips
Rejected：+319.7 pips
```

このため、全ロジック共通のH1 ATR P70は有効だが、かなり粗い可能性がある。

---

## ATR Ratio Bucketの示唆

ATR比率別に見ると、VeryHighも長期では強い。

| ATR Bucket | Trades | PF | TotalPips | RoMD |
|---|---:|---:|---:|---:|
| VeryLow | 4,526 | 1.195 | +10,817.9 | 6.79 |
| Low | 4,380 | 1.447 | +26,553.0 | 28.84 |
| NearThreshold | 1,651 | 1.245 | +6,899.7 | 5.36 |
| OverSlightly | 2,129 | 1.458 | +16,482.1 | 18.41 |
| High | 1,420 | 1.303 | +8,442.6 | 6.69 |
| VeryHigh | 1,159 | 1.613 | +17,363.4 | 14.39 |

よって、

```text
ATRが高い = 悪い
```

ではない。

正しくは、

```text
ATRが高い局面は、勝つ時も大きいが、DDも大きくなりやすい
```

と解釈する。

---

## 現時点の判断

```text
H1 ATR P70は採用候補としてかなり有力
ただし全ロジック共通フィルタとしては粗い
```

実運用候補としては以下の位置づけ。

```text
防御型：H1 ATR P70 全体適用
成長型：Base
改良型：ロジック別ATRフィルタ
```

---

## 次にやること

次は、ロジック別ATRフィルタ探索に進む。

作成予定コード：

```text
src/money_filter_logic_atr_select_v1.py
```

目的：

```text
H1 ATR P70を全ロジック共通でかけるのではなく、
各ロジックごとに、
フィルタなし / P70 / P75 / P80 / P85 / P90 / P95
の中から、MoneySim基準で最適候補を探す。
```

見る指標：

```text
Full MoneyRoMD
OOS MoneyRoMD
Q1 MoneyRoMD
MaxDDPct
NetProfitYen
Worst WeekReturnPct
RejectedRate
```

狙い：

```text
H1 ATR P70を全体適用するよりも、
防御力と成長力のバランスが良いロジック別ATRフィルタを探す。
```
