# Volatility Environment Phase 2 — 正式結果

**全期間の固定28戦略Portfolioは、Primary・Robustnessの両方式で、5分位に沿う正の関係を事前基準で支持した（BOTH_SUPPORTED）。**
pooled Avg R/Tradeは両方式でQ1→Q5の4差すべてが正、Spearman=1.0。等重みでもQ5>Q1かつSpearman>0を満たす。
Phase 1の三分位だけでなく、事前固定した粗い5分位でも上向きの関係が観察された。任意cut探索・取引停止・Risk配分は行っていない。

## 固定記録・実行順序

- Branch: `research/volatility-environment-phase2`
- Phase 1正式結果SHA: `cafbb6ff0bfe81e439b80ed62d50498494814e86`
- 計画SHA: `1acc1fa530610eafcd985d446ba86c4dc415b5d6`（Planのみの差分とremote本文一致を確認後にコード作成）
- 実装SHA: `4f13bff5e40809bb63455fe7214beb2f642508bf`（4ファイルのremote本文一致・branch head確認後に実データ実行）
- 結果SHA: 本文・結果CSV・結果表示Notebookを含むコミット。自己参照を避け、最終報告で完全SHAを提示。
- Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359` 一致。
- 28戦略・16,298 trades。22_GA_C_2を含む。Baseline再計算なし、Entry除外0件、EA/VPS/SET/liveコード・設定変更なし。
- Daily Stopなし、ATR OFF、Event Candidate C、UJ12/EJ1修正済みの固定ログを使用。
- 実データはローカルPythonで実行。Colabセルは再実行用。Driveへの結果保存は実施せず、保存セル初期OFF。

## Portfolio Q1→Q5 Avg R/Trade

| Method | Aggregation | Q1AvgR | Q2AvgR | Q3AvgR | Q4AvgR | Q5AvgR |
| --- | --- | --- | --- | --- | --- | --- |
| primary | trade_weighted | +0.044682 | +0.078276 | +0.095623 | +0.103454 | +0.143594 |
| primary | strategy_equal_weighted | +0.046448 | +0.083528 | +0.096450 | +0.099528 | +0.142691 |
| robustness | trade_weighted | +0.046312 | +0.077083 | +0.094603 | +0.108096 | +0.128460 |
| robustness | strategy_equal_weighted | +0.052778 | +0.076147 | +0.098872 | +0.095127 | +0.131459 |

| Method | Aggregation | Q5MinusQ1AvgR | CILow | CIHigh | Spearman | AdjacentIncreases | Support |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary | trade_weighted | +0.098913 | +0.051353 | +0.146281 | 1.000000 | 4 | ORDERED_POSITIVE_SUPPORTED |
| primary | strategy_equal_weighted | +0.096243 | — | — | 1.000000 | 4 | ORDERED_POSITIVE_SUPPORTED |
| robustness | trade_weighted | +0.082148 | +0.037235 | +0.126370 | 1.000000 | 4 | ORDERED_POSITIVE_SUPPORTED |
| robustness | strategy_equal_weighted | +0.078681 | — | — | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED |

CIはQ5−Q1の95%暦週cluster bootstrap、5,000回、seed=20260913、両Portfolioとも5,000有効反復。
CIは事前計画どおり補助指標で、正式支持条件には入れていない。今回は両pooled CIとも0を含まなかった。
等重み行にpooled CIを転記しない。等重みCIは算出していない。

### 隣接差

| Method | Aggregation | Q2MinusQ1AvgR | Q3MinusQ2AvgR | Q4MinusQ3AvgR | Q5MinusQ4AvgR |
| --- | --- | --- | --- | --- | --- |
| primary | trade_weighted | +0.033594 | +0.017347 | +0.007831 | +0.040141 |
| primary | strategy_equal_weighted | +0.037080 | +0.012922 | +0.003078 | +0.043163 |
| robustness | trade_weighted | +0.030771 | +0.017520 | +0.013493 | +0.020364 |
| robustness | strategy_equal_weighted | +0.023369 | +0.022725 | -0.003745 | +0.036331 |

Primaryの等重みも4/4上昇。Robustness等重みはQ3→Q4に小幅低下があり3/4上昇、Spearman=0.9。
完全単調は正式必要条件にしていない。Robustness等重みの低下も表示した上で固定条件を満たす。

### 各帯の件数と成績

| Method | Quintile | Trades | TotalR | AvgR | PF | WinRate | AvgWinR | AvgLossR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | Q1 | 4785 | +213.803004 | +0.044682 | 1.240719 | 53.375131 | 0.431476 | -0.399544 |
| primary | Q2 | 2626 | +205.551607 | +0.078276 | 1.411741 | 55.255141 | 0.485718 | -0.428520 |
| primary | Q3 | 2510 | +240.013110 | +0.095623 | 1.452481 | 55.697211 | 0.551109 | -0.478302 |
| primary | Q4 | 2195 | +227.080520 | +0.103454 | 1.454122 | 55.170843 | 0.600433 | -0.510248 |
| primary | Q5 | 2966 | +425.901107 | +0.143594 | 1.569182 | 55.124747 | 0.718147 | -0.563032 |
| robustness | Q1 | 4099 | +189.831973 | +0.046312 | 1.239883 | 52.768968 | 0.453622 | -0.411092 |
| robustness | Q2 | 2919 | +225.004107 | +0.077083 | 1.409961 | 56.149366 | 0.472146 | -0.430128 |
| robustness | Q3 | 2660 | +251.644171 | +0.094603 | 1.453750 | 55.827068 | 0.542917 | -0.474007 |
| robustness | Q4 | 2386 | +257.916737 | +0.108096 | 1.493657 | 54.107293 | 0.604476 | -0.478884 |
| robustness | Q5 | 3009 | +386.535840 | +0.128460 | 1.517238 | 55.300764 | 0.681396 | -0.556861 |

5分位は過去252日分布のpercentile帯であり、Baseline取引を等件数に分けたものではない。
そのため各帯のtrade数は20%ずつにはならない。

## 標本条件とcoverage

等重み対象は両方式とも同じ25戦略（1〜13、17〜28）。14_UJ_Sat_3rd、15_UJ_Sat_Aug、16_UJ_T10Aは全5cell各20件条件を満たさず、個別正式判定はLOW_SAMPLE。
pooledではこの3戦略の有効tradeも含め、全28戦略を維持した。
- Primary: 有効15,082件、履歴不足1,216件（Phase 1と一致）。
- Robustness: 有効15,073件、履歴不足1,225件（Phase 1と一致）。
履歴不足はassignment/coverageに保持。後埋め・共通coverageへの後付け制限なし。

## 事前指定4戦略

| Method | Strategy | Q1AvgR | Q2AvgR | Q3AvgR | Q4AvgR | Q5AvgR | Q5MinusQ1AvgR | Spearman | AdjacentIncreases | Support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 1_EJ_Log1 | +0.087121 | +0.105743 | +0.137864 | +0.136167 | +0.321781 | +0.234660 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED |
| primary | 6_GJ_Old_Mon | -0.036993 | +0.222457 | +0.309561 | +0.353944 | +0.265566 | +0.302560 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED |
| primary | 12_UJ_Short_Core | +0.103367 | +0.239759 | +0.101407 | +0.421181 | +0.424265 | +0.320898 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED |
| primary | 23_GA_F_2 | -0.046382 | +0.046332 | +0.064291 | +0.132081 | +0.083605 | +0.129987 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED |
| robustness | 1_EJ_Log1 | +0.040020 | +0.196679 | +0.108655 | +0.165445 | +0.288889 | +0.248869 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED |
| robustness | 6_GJ_Old_Mon | +0.045265 | +0.104471 | +0.311077 | +0.288351 | +0.255185 | +0.209920 | 0.600000 | 2 | NOT_SUPPORTED |
| robustness | 12_UJ_Short_Core | +0.067864 | +0.180378 | +0.428067 | +0.061089 | +0.570452 | +0.502587 | 0.400000 | 3 | ORDERED_POSITIVE_SUPPORTED |
| robustness | 23_GA_F_2 | -0.004088 | +0.006994 | -0.033387 | +0.111272 | +0.136171 | +0.140259 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED |

1_EJ_Log1、12_UJ_Short_Core、23_GA_F_2は両方式で支持。
6_GJ_Old_MonはPrimaryのみ支持。Robustnessは隣接増加2/4で事前条件未達、Q5−Q1 CIも[-0.116934,+0.550089]。
Phase 1で両方式明確だったことを理由にPhase 2でも支持と扱わない。
12_UJ_Short_CoreのRobustnessはQ3→Q4の大きな低下を含み、Spearman=0.4。固定3/4条件は満たすが滑らかな単調増加ではない。
個別専用定義・thresholdは作成していない。

## 補助群

| Method | Scope | Q1AvgR | Q2AvgR | Q3AvgR | Q4AvgR | Q5AvgR | Q5MinusQ1AvgR | Spearman | AdjacentIncreases | CombinedConclusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | JPY | +0.052798 | +0.105962 | +0.105699 | +0.133011 | +0.165911 | +0.113114 | 0.900000 | 3 | BOTH_SUPPORTED |
| primary | AUD_nonJPY | +0.034480 | +0.041849 | +0.082238 | +0.054465 | +0.111026 | +0.076546 | 0.900000 | 3 | PRIMARY_ONLY |
| primary | Long | +0.044092 | +0.086756 | +0.084413 | +0.088413 | +0.138588 | +0.094497 | 0.900000 | 3 | BOTH_SUPPORTED |
| primary | Short | +0.045587 | +0.066566 | +0.108627 | +0.124973 | +0.150962 | +0.105375 | 1.000000 | 4 | PRIMARY_ONLY |
| robustness | JPY | +0.046094 | +0.095165 | +0.126805 | +0.146247 | +0.145601 | +0.099507 | 0.900000 | 3 | BOTH_SUPPORTED |
| robustness | AUD_nonJPY | +0.046603 | +0.053407 | +0.051468 | +0.045996 | +0.105925 | +0.059322 | 0.300000 | 2 | PRIMARY_ONLY |
| robustness | Long | +0.032766 | +0.094371 | +0.075120 | +0.103374 | +0.132953 | +0.100187 | 0.900000 | 3 | BOTH_SUPPORTED |
| robustness | Short | +0.066851 | +0.052211 | +0.118634 | +0.114859 | +0.122197 | +0.055347 | 0.800000 | 2 | PRIMARY_ONLY |

JPY・Longは両方式支持。AUD_nonJPY・ShortはPrimaryのみ支持。
RobustnessのAUD_nonJPYはpooled隣接増加2/4・等重みSpearman=0、Shortもpooled2/4で条件未達。
Phase 1のShort両方式支持をPhase 2に持ち越さず、新しい固定判定を適用した。

## 全28戦略の正式判定

十分標本25戦略のうち、Primaryは14/25、Robustnessは10/25でPhase 2の順序条件を満たした。両方式支持は8戦略。
以下は未調整の個別診断であり、確証的な独立発見や将来の運用優位を意味しない。

| Method | Strategy | Q1AvgR | Q2AvgR | Q3AvgR | Q4AvgR | Q5AvgR | Q5MinusQ1AvgR | Spearman | AdjacentIncreases | Support | CombinedConclusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 1_EJ_Log1 | +0.087121 | +0.105743 | +0.137864 | +0.136167 | +0.321781 | +0.234660 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 2_EJ_NightBlitz_20 | +0.056943 | +0.136635 | +0.223470 | +0.059220 | +0.131308 | +0.074365 | 0.200000 | 3 | ORDERED_POSITIVE_SUPPORTED | PRIMARY_ONLY |
| primary | 3_EJ_NightBlitz_21 | +0.056170 | +0.062667 | +0.110316 | +0.013263 | +0.108263 | +0.052093 | 0.200000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 4_GJ_Port_Log1 | +0.021499 | +0.030173 | +0.030038 | +0.054272 | +0.076634 | +0.055135 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 5_GJ_Port_Log2 | +0.038450 | +0.053895 | +0.107597 | +0.140556 | +0.113604 | +0.075154 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED | PRIMARY_ONLY |
| primary | 6_GJ_Old_Mon | -0.036993 | +0.222457 | +0.309561 | +0.353944 | +0.265566 | +0.302560 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | PRIMARY_ONLY |
| primary | 7_GJ_Mon_Blitz | +0.009960 | +0.037289 | +0.094623 | +0.090659 | +0.070612 | +0.060652 | 0.600000 | 2 | NOT_SUPPORTED | ROBUSTNESS_ONLY |
| primary | 8_AJ_Core1 | +0.040051 | +0.110179 | +0.018336 | +0.212438 | +0.163494 | +0.123442 | 0.600000 | 2 | NOT_SUPPORTED | ROBUSTNESS_ONLY |
| primary | 9_AJ_Core2 | +0.108312 | +0.367308 | +0.207556 | +0.199938 | +0.197606 | +0.089293 | 0.000000 | 1 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 10_AJ_SatA | -0.020782 | +0.035000 | +0.016282 | -0.005172 | -0.013158 | +0.007624 | 0.000000 | 1 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 11_AJ_SatB | +0.046860 | +0.050428 | +0.045091 | +0.025737 | +0.088589 | +0.041729 | 0.100000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 12_UJ_Short_Core | +0.103367 | +0.239759 | +0.101407 | +0.421181 | +0.424265 | +0.320898 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 13_UJ_Fix_MidWeek | +0.060289 | +0.077796 | +0.068960 | +0.046316 | +0.145483 | +0.085195 | 0.300000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 14_UJ_Sat_3rd | +0.360808 | +0.536296 | +0.086000 | +0.359394 | +0.618990 | +0.258182 | 0.200000 | 3 | LOW_SAMPLE | UNDETERMINED |
| primary | 15_UJ_Sat_Aug | +0.077857 | +0.203846 | +0.079000 | +0.706538 | +0.382045 | +0.304188 | 0.800000 | 2 | LOW_SAMPLE | UNDETERMINED |
| primary | 16_UJ_T10A | +0.145238 | +0.292346 | -0.178222 | +0.428642 | +0.460926 | +0.315688 | 0.700000 | 3 | LOW_SAMPLE | UNDETERMINED |
| primary | 17_EA_1B_Wed_Short | +0.194844 | +0.006767 | +0.224738 | +0.006925 | +0.291203 | +0.096359 | 0.500000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 18_EA_2_MonWed_Short | +0.030765 | -0.084802 | +0.131294 | +0.034537 | +0.130908 | +0.100143 | 0.600000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 19_EA_3_WedThu_Long | +0.068081 | +0.010626 | +0.078032 | +0.136602 | +0.159104 | +0.091023 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 20_EA_1A_MonTue_Short | -0.027792 | +0.015883 | +0.062519 | -0.010136 | +0.193910 | +0.221701 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | PRIMARY_ONLY |
| primary | 21_GA_B_3 | +0.004626 | +0.012050 | -0.024010 | -0.001831 | +0.032055 | +0.027429 | 0.200000 | 3 | ORDERED_POSITIVE_SUPPORTED | PRIMARY_ONLY |
| primary | 22_GA_C_2 | +0.028560 | +0.155978 | +0.013181 | -0.046417 | +0.110752 | +0.082192 | -0.200000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 23_GA_F_2 | -0.046382 | +0.046332 | +0.064291 | +0.132081 | +0.083605 | +0.129987 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 24_GA_D_1 | +0.051514 | +0.093240 | -0.004425 | +0.094949 | +0.079858 | +0.028344 | 0.300000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 25_AU_China_Demand | +0.030488 | +0.120792 | +0.029562 | +0.035642 | +0.091480 | +0.060992 | 0.200000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 26_AJ_China_Demand | +0.129373 | +0.050046 | +0.080918 | +0.100185 | +0.185217 | +0.055845 | 0.400000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| primary | 27_EA_China_Demand | +0.108937 | +0.075935 | +0.135245 | +0.069232 | +0.068500 | -0.040437 | -0.700000 | 1 | NOT_SUPPORTED | NOT_SUPPORTED |
| primary | 28_GA_China_Demand | +0.016933 | +0.056025 | +0.148811 | +0.187910 | +0.046630 | +0.029698 | 0.400000 | 3 | ORDERED_POSITIVE_SUPPORTED | PRIMARY_ONLY |
| robustness | 1_EJ_Log1 | +0.040020 | +0.196679 | +0.108655 | +0.165445 | +0.288889 | +0.248869 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 2_EJ_NightBlitz_20 | +0.030532 | +0.170561 | +0.088417 | +0.209084 | +0.089271 | +0.058739 | 0.500000 | 2 | NOT_SUPPORTED | PRIMARY_ONLY |
| robustness | 3_EJ_NightBlitz_21 | +0.019389 | +0.107148 | +0.053358 | +0.078989 | +0.101398 | +0.082009 | 0.400000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 4_GJ_Port_Log1 | -0.004496 | +0.042360 | +0.055190 | +0.076180 | +0.059960 | +0.064456 | 0.900000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 5_GJ_Port_Log2 | +0.038468 | +0.001309 | +0.126469 | +0.215198 | +0.062801 | +0.024332 | 0.600000 | 2 | NOT_SUPPORTED | PRIMARY_ONLY |
| robustness | 6_GJ_Old_Mon | +0.045265 | +0.104471 | +0.311077 | +0.288351 | +0.255185 | +0.209920 | 0.600000 | 2 | NOT_SUPPORTED | PRIMARY_ONLY |
| robustness | 7_GJ_Mon_Blitz | +0.024432 | +0.030623 | +0.087283 | +0.064167 | +0.080420 | +0.055988 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | ROBUSTNESS_ONLY |
| robustness | 8_AJ_Core1 | +0.045619 | +0.069722 | +0.077518 | +0.148114 | +0.164133 | +0.118514 | 1.000000 | 4 | ORDERED_POSITIVE_SUPPORTED | ROBUSTNESS_ONLY |
| robustness | 9_AJ_Core2 | +0.182108 | +0.117193 | +0.339379 | +0.426606 | +0.030996 | -0.151112 | -0.100000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 10_AJ_SatA | -0.011614 | +0.037710 | +0.063611 | -0.058676 | -0.018081 | -0.006467 | -0.500000 | 3 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 11_AJ_SatB | +0.008029 | +0.086772 | +0.047247 | +0.079718 | +0.051990 | +0.043962 | 0.300000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 12_UJ_Short_Core | +0.067864 | +0.180378 | +0.428067 | +0.061089 | +0.570452 | +0.502587 | 0.400000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 13_UJ_Fix_MidWeek | +0.058070 | +0.116902 | +0.115489 | +0.001754 | +0.105500 | +0.047430 | -0.200000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 14_UJ_Sat_3rd | +0.549372 | +0.295556 | +0.416049 | +0.449074 | +0.088687 | -0.460685 | -0.600000 | 2 | LOW_SAMPLE | UNDETERMINED |
| robustness | 15_UJ_Sat_Aug | +0.286875 | -0.083333 | -0.060417 | +0.515000 | +0.467586 | +0.180711 | 0.600000 | 2 | LOW_SAMPLE | UNDETERMINED |
| robustness | 16_UJ_T10A | +0.114000 | +0.180556 | +0.177333 | +0.304444 | +0.331624 | +0.217624 | 0.900000 | 3 | LOW_SAMPLE | UNDETERMINED |
| robustness | 17_EA_1B_Wed_Short | +0.242310 | +0.143695 | +0.063995 | +0.024156 | +0.242468 | +0.000157 | 0.000000 | 1 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 18_EA_2_MonWed_Short | +0.065749 | +0.017206 | +0.038081 | -0.032048 | +0.117937 | +0.052189 | 0.100000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 19_EA_3_WedThu_Long | -0.006776 | +0.146902 | +0.012768 | +0.079607 | +0.184675 | +0.191451 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 20_EA_1A_MonTue_Short | -0.011061 | -0.013606 | +0.083655 | +0.161200 | +0.013864 | +0.024925 | 0.600000 | 2 | NOT_SUPPORTED | PRIMARY_ONLY |
| robustness | 21_GA_B_3 | -0.002661 | -0.006172 | +0.006522 | -0.009691 | +0.044448 | +0.047110 | 0.300000 | 2 | NOT_SUPPORTED | PRIMARY_ONLY |
| robustness | 22_GA_C_2 | +0.068709 | +0.063053 | +0.018337 | +0.018493 | +0.121827 | +0.053118 | 0.100000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 23_GA_F_2 | -0.004088 | +0.006994 | -0.033387 | +0.111272 | +0.136171 | +0.140259 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 24_GA_D_1 | +0.052008 | +0.029544 | +0.037186 | +0.001129 | +0.170471 | +0.118463 | 0.100000 | 2 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 25_AU_China_Demand | +0.031746 | +0.064633 | +0.065159 | +0.058767 | +0.071993 | +0.040247 | 0.700000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 26_AJ_China_Demand | +0.131241 | +0.046405 | +0.059057 | +0.113461 | +0.184906 | +0.053666 | 0.400000 | 3 | ORDERED_POSITIVE_SUPPORTED | BOTH_SUPPORTED |
| robustness | 27_EA_China_Demand | +0.126002 | +0.116939 | +0.099746 | +0.024203 | +0.074434 | -0.051568 | -0.900000 | 1 | NOT_SUPPORTED | NOT_SUPPORTED |
| robustness | 28_GA_China_Demand | +0.082580 | +0.026256 | +0.118927 | +0.071610 | +0.080356 | -0.002224 | -0.100000 | 2 | NOT_SUPPORTED | PRIMARY_ONLY |


## 事前固定の補助期間

| Period | Method | Q1AvgR | Q2AvgR | Q3AvgR | Q4AvgR | Q5AvgR | Q5MinusQ1AvgR | Spearman | AdjacentIncreases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Historical | primary | +0.052787 | +0.063239 | +0.098095 | +0.082072 | +0.139434 | +0.086647 | 0.900000 | 3 |
| Historical | robustness | +0.049563 | +0.064785 | +0.091597 | +0.085066 | +0.129018 | +0.079456 | 0.900000 | 3 |
| RecentA | primary | +0.048478 | +0.126378 | +0.127671 | +0.169234 | +0.139531 | +0.091052 | 0.900000 | 3 |
| RecentA | robustness | +0.047958 | +0.125717 | +0.121601 | +0.192790 | +0.124892 | +0.076934 | 0.500000 | 2 |
| RecentB | primary | +0.049685 | +0.095938 | +0.087594 | +0.122299 | +0.179790 | +0.130105 | 0.900000 | 3 |
| RecentB | robustness | +0.067669 | +0.073587 | +0.096771 | +0.126598 | +0.156449 | +0.088779 | 1.000000 | 4 |
| Monitor2026 | primary | -0.028508 | +0.077795 | -0.058579 | +0.032075 | +0.092031 | +0.120539 | 0.500000 | 3 |
| Monitor2026 | robustness | -0.046688 | +0.075788 | +0.020206 | +0.023154 | +0.052571 | +0.099259 | 0.400000 | 3 |

全補助期間でpooled Q5−Q1は両方式とも正。ただし期間ごとに完全単調ではなく、全期間の滑らかさが各期間で再現するとは限らない。
期間別の等重み対象数はHistorical両方式24、RecentA両方式2、RecentB Primary3/Robustness6、2026は0。
Robustness等重みQ5−Q1はRecentA -0.039004、RecentB -0.000109。2026等重みは比較不能。
標本規則のため短い期間では対象戦略が少なくなる。これらはDESCRIPTIVE_ONLYで、全期間の正式判定を上書きしない。
2022–2026は既閲覧で、完全未閲覧holdoutではない。追加窓・追加cutの探索なし。

## 仕様・検証

Primary=D1 TR SMA20、Robustness=20日log return sample std(ddof=1)×sqrt(252)。
JST実M1日次OHLC、翌00:00以降の参照、評価日を除いた過去252 completed trading days、midrankをPhase 1の不変コードから再利用。
土曜早朝も実バーがあれば1日、空日・欠損は補間しない。
5分位は[0,20)/[20,40)/[40,60)/[60,80)/[80,100]。整数分子n=2*less+equalを5*nと504/1008/1512/2016で比較。

- 監査済みM1 56本・30,371,276バー、全byte hashがPhase 1 manifestと一致。
- Phase 1コード/固定入力JSONのSHA-256不変をテスト・実行時とも確認。
- 20 unit tests PASS（Phase 1の10件＋Phase 2の10件）。0/20/40/60/80/100と近傍、全505個のmidrank分子、標本19/20、固定等重み集合、3/4と2/4、同順位、空集合、未来M1改変不変、bootstrapを検証。
- Notebook全コードセルの構文確認。結果スナップショットはローカル実行由来と明記し、Colabで実行した出力を偽装していない。
- 代表23日でM1からOHLC・ATR/RV・参照窓・5分位を手順独立照合。257件の軽量trade auditを保存。

| Check | Status | Rows |
| --- | --- | --- |
| Independent CSV Decimal metrics/equal weights/all periods | PASS | 1900 |
| Independent ranks/adjacent/eligibility/combined decisions | PASS | 380 |
| Independent weekly sums and linear CI | PASS | 66 |
| All assignments/quintiles/no-lookahead/retained trades | PASS | 16298 |
| Coverage including insufficient history | PASS | 1980 |


### Phase 1回帰照合

同じfeatureからPhase 1の三分位を再現し、正式CSVの丸め前値・CI・判定・coverageを絶対許容1e-10で照合。

| Check | Status | Rows |
| --- | --- | --- |
| Phase1 regression strategy_primary | PASS | 84 |
| Phase1 regression strategy_robustness | PASS | 84 |
| Phase1 regression group_summary | PASS | 60 |
| Phase1 regression period_summary | PASS | 912 |
| Phase1 regression decision | PASS | 10 |
| Phase1 regression combined_decision | PASS | 5 |
| Phase1 regression regime_coverage | PASS | 1320 |
| Phase1 stored feature/assignment audit | PASS | 177 |


## 解釈とPhase 3分岐

**両方式のPortfolioが事前条件を満たしたため、Phase 3を別研究として検討する価値がある。**
Phase 3の候補はVolatility-based Risk AllocationとEntry Filterの利益額比較。
Phase 1 LOW、今回全期間Q1ともpooled AvgRが正なので、Risk Allocationを優先仮説として扱う。
ただし、それが実際に利益額やリスク調整後成績を改善するかは未検証。Phase 2では採用しない。

今回の支持は診断基準上の支持であり、因果・将来filter有効性・未閲覧検証の証明ではない。
粗い5分位でも上向きの関係が残ったことは、Phase 1の三分位境界だけに依存した説明を弱める材料だが、他の相場要因や時期・戦略構成の影響を排除するものではない。
CIは週内依存を保持する一方、週を跨ぐ自己相関や非定常性を完全には扱わず、個別・群の多重比較も未調整。
旧ATR70研究との結果融合なし。Q4以上等の閾値採用、Entry ON/OFF Money Simulation、Risk%最適化、追加cut・窓探索は実施しなかった。

## 作成ファイル

- docs/57_volatility_phase2_plan.md / docs/58_volatility_phase2_result.md
- src/research/volatility_phase2.py
- tests/test_volatility_phase2.py / tests/verify_volatility_phase2.py
- notebooks/volatility_phase2.ipynb
- results/volatility_phase2/ 必須6 CSV: volatility_phase2_portfolio_quintiles.csv、volatility_phase2_strategy_quintiles.csv、volatility_phase2_group_quintiles.csv、volatility_phase2_period_quintiles.csv、volatility_phase2_monotonicity_summary.csv、volatility_phase2_run_record.csv
- 同ディレクトリ補助6 CSV: volatility_phase2_coverage.csv、volatility_phase2_input_manifest.csv、volatility_phase2_verification.csv、volatility_phase2_manual_audit.csv、volatility_phase2_assignment_audit_light.csv、volatility_phase2_phase1_regression.csv
- 完全版volatility_phase2_trade_assignments.csv / volatility_phase2_daily_audit.csvはlocalのみ。GitHubに含めない。
