# China Demand 4戦略一括停止：最終結果

**C1_MINUS_CHINA4は不採用。C0_BASELINEの28戦略・除外なしを維持する。**

実行日: 2026-09-12 JST（CSVに詳細時刻を記録）
Branch: `research/china-demand-group-validation`
起点: `8bc5f65d1eb8219c1b2010e4674f6c8220fb68e4`
コード作成・比較計算前の計画コミット: `71e8501f23dcd81104147ab3aaa72892762d0bdc`
Baseline: `daily_stop_baseline_trades.csv` / 28戦略 / 16,298 trades
SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。

## 固定仮説と採否

C0は28戦略すべて。C1は25_AU_China_Demand、26_AJ_China_Demand、27_EA_China_Demand、28_GA_China_Demandを戦略名の完全一致で一括除外した24戦略。事前定義された共通ロジック群であり、今回成績を見て選んだ4戦略ではない。

Primary metricはDelta Total R（C1-C0）。事前ルール「OOS1+OOS2合算Delta Total R <= 0なら不採用」を適用した。丸め前の差は **-91.242555548R**。副次指標改善だけでは利益減少を許容しないため、Money Simulationへ進めず本研究を終了する。

候補・構成・閾値・除外数の変更、追加候補、全組み合わせ、部分除外、別グループ、OOS後再最適化は実施していない。エッジ消失/優位性低下研究は今回実装・探索していない。EA/VPS/SET/live運用は変更していない。

## 期間別結果

EntryTime JST基準。IS 2015–2021、OOS1 2022–2025、OOS2 2026-01-01～09-09。ALLは固定ログ全期間。

| Period | Candidate | Trades | TotalR | PF | MaxDDR | WorstDayR | WorstWeekR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IS | C0_BASELINE | 9756 | 768.488273 | 1.372171 | 27.540956 | -12.000000 | -14.455836 |
| IS | C1_MINUS_CHINA4 | 8137 | 651.764662 | 1.370203 | 21.862874 | -8.000000 | -8.566213 |
| IS | DELTA_C1_MINUS_C0 | -1619 | -116.723611 | -0.001967 | -5.678082 | 4.000000 | 5.889623 |
| OOS1 | C0_BASELINE | 5547 | 601.960585 | 1.489975 | 22.196976 | -10.880000 | -12.824402 |
| OOS1 | C1_MINUS_CHINA4 | 4628 | 511.942196 | 1.474721 | 25.567099 | -7.000000 | -9.980679 |
| OOS1 | DELTA_C1_MINUS_C0 | -919 | -90.018389 | -0.015254 | 3.370123 | 3.880000 | 2.843722 |
| OOS2 | C0_BASELINE | 995 | 19.818791 | 1.095529 | 18.954206 | -4.579584 | -5.397048 |
| OOS2 | C1_MINUS_CHINA4 | 834 | 18.594625 | 1.105966 | 16.391484 | -4.579584 | -4.796081 |
| OOS2 | DELTA_C1_MINUS_C0 | -161 | -1.224167 | 0.010437 | -2.562722 | 0.000000 | 0.600967 |
| OOS_COMBINED | C0_BASELINE | 6542 | 621.779376 | 1.432989 | 22.196976 | -10.880000 | -12.824402 |
| OOS_COMBINED | C1_MINUS_CHINA4 | 5462 | 530.536821 | 1.423115 | 25.567099 | -7.000000 | -9.980679 |
| OOS_COMBINED | DELTA_C1_MINUS_C0 | -1080 | -91.242556 | -0.009874 | 3.370123 | 3.880000 | 2.843722 |
| ALL | C0_BASELINE | 16298 | 1390.267649 | 1.397117 | 27.540956 | -12.000000 | -14.455836 |
| ALL | C1_MINUS_CHINA4 | 13599 | 1182.301483 | 1.392212 | 25.567099 | -8.000000 | -9.980679 |
| ALL | DELTA_C1_MINUS_C0 | -2699 | -207.966167 | -0.004905 | -1.973857 | 4.000000 | 4.475156 |

MaxDDは正の損失幅でありDeltaが正なら悪化。Worst Day/WeekはDeltaが正なら改善。OOS合算は1,080 trades減少。PFは低下し、MaxDDも悪化した。Worst Day/Week改善を含めても採用条件を満たさない。

## 年別Delta

| Period | Candidate | Trades | TotalR | PF | MaxDDR | WorstDayR | WorstWeekR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | DELTA_C1_MINUS_C0 | -231 | -7.011389 | 0.028820 | -7.193405 | 4.000000 | 5.889623 |
| 2016 | DELTA_C1_MINUS_C0 | -232 | -28.432722 | 0.017898 | -1.315133 | 3.368352 | 4.687939 |
| 2017 | DELTA_C1_MINUS_C0 | -231 | -33.243833 | -0.096583 | -3.149091 | 0.318989 | -0.187500 |
| 2018 | DELTA_C1_MINUS_C0 | -232 | -16.364444 | -0.001815 | 1.522333 | 0.000000 | 0.000000 |
| 2019 | DELTA_C1_MINUS_C0 | -231 | -7.423056 | -0.000965 | -10.099222 | 1.216159 | 6.589050 |
| 2020 | DELTA_C1_MINUS_C0 | -231 | -24.700333 | -0.016315 | -1.425200 | 4.000000 | 2.659673 |
| 2021 | DELTA_C1_MINUS_C0 | -231 | 0.452167 | 0.054553 | -2.959109 | 0.724549 | 1.150524 |
| 2022 | DELTA_C1_MINUS_C0 | -232 | -13.259944 | 0.034428 | 0.000000 | 1.402654 | 2.376381 |
| 2023 | DELTA_C1_MINUS_C0 | -231 | -26.173778 | -0.016250 | 3.370123 | 3.880000 | 2.843722 |
| 2024 | DELTA_C1_MINUS_C0 | -229 | -15.332667 | -0.012830 | -0.552500 | 0.000000 | -0.353056 |
| 2025 | DELTA_C1_MINUS_C0 | -227 | -35.252000 | -0.073337 | -0.205278 | 0.000000 | 0.552751 |
| 2026 | DELTA_C1_MINUS_C0 | -161 | -1.224167 | 0.010437 | -2.562722 | 0.000000 | 0.600967 |

2022～2026各年で利益が減少。2026は09-09までの途中年で通年換算なし。年別C0/C1実数と全副次指標はyearly_results.csvに収録。

## 集計・検証

固定ログを再計算せず既存Rを使用。Total Rと採否はCSV記載RをDecimalで合計し、表示丸め前に判定。PFは正R合計/負R絶対値合計。DDはCloseTime, EntryTime, StrategyNo順、初期R=0。日損益はCloseTime JST、週は月曜～日曜。OOS合算PF/DD等は合算トレードから再集計。期間所属トレードは決済まで含める。

- 指定hash、16,298行、28戦略、指定4名称と番号一致、重複・日時・R整合を確認。
- C0のIS/OOS合算/OOS2 Total Rが既存公表値と小数6桁精度で一致。
- C1は指定4戦略のみ除外、期間合算が一致。
- 標準csv読み取りとDecimalによる独立集計でもOOS差-91.242555548Rと各年差が一致。
- 4テスト合格: 期間境界、初期損失DD・週境界、採否ゼロ境界、hash不一致停止。

ローカルPython 3.12 / pandas 2.2.3で実行。Colabサーバー上での実行はしていない。ノートブックに同一コードと今回の確定結果を収録し、実行セルはColab本文表示と/content/*.csv保存を行う。任意のDrive保存セルを含む。ローカル実行時は一時出力先を指定し、確定CSVをGitHubへ記録した。

同じOOS期間は過去研究で参照済みで、完全未閲覧の新規ホールドアウトとは主張しない。今回の仮説事前固定と計画先行コミットを記録する。

## 作成ファイル・CSV hash

- docs/36_china_demand_group_validation_plan.md
- docs/37_china_demand_group_final_result.md
- src/research/china_demand_group_analysis.py
- tests/test_china_demand_group_analysis.py
- notebooks/china_demand_group_validation.ipynb

- `results/china_demand_group/china_demand_group_final_decision.csv`
  SHA-256: `755e6265d8f963ff9ad2895676f54ac7a1855773dabcc6d56b04fd0a18b05309`
- `results/china_demand_group/china_demand_group_period_results.csv`
  SHA-256: `a76ab1a65f9bfdd6853324d39f51f6480652743dc7acd2bbb4b7b24cea8bf7a1`
- `results/china_demand_group/china_demand_group_run_record.csv`
  SHA-256: `da74a3726de0a8a5062ca1a8972c6341a23e0a0e7c937fabda0a582e64518789`
- `results/china_demand_group/china_demand_group_yearly_results.csv`
  SHA-256: `c8d2224e3d69cc4067e081669782b04061a29f9e8d688f12da884116a41a1274`
