# Edge Decay Sensitivity Analysis：最終結果

**18/20/22/23の正式警告候補4戦略は、7つのユニーク設定すべてで警告側に残った。22と18は全設定EDGE LOST、20と23は全設定EDGE DECAY。指定範囲内の閾値感度という意味で4戦略とも「頑健」。**

既存Primary ResultはSTABLE 21 / EDGE LOST 2 / EDGE DECAY 2 / INSUFFICIENT SAMPLE 3のまま維持。新しい正式閾値を採用せず、EA/VPS/SET/live運用コード・設定も変更していない。

## 研究記録
- Repo: TR-KJ/time-entry-portfolio-lab
- Branch: research/edge-decay-sensitivity-validation
- 計画コミット: b3b9aca221adb78c70a34eefcd5b8e98d4511d7c
- 実装コミット: c9a937b459a5bb4fc4b7fa41985a8a972fba9d42
- 結果コミット: 本文書と確定CSVを追加したコミット。自己参照を避けSHAは最終報告に記載。
- 既存正式結果コミット: 8c45becc49218d7dc971109bf140f71ce3e8099d
- 計画: docs/40_edge_decay_sensitivity_validation_plan.md
- 実行日: 2026-09-12 JST（実行時刻はrun record参照）

## 固定データと手順
Baselineはdaily_stop_baseline_trades.csv、28戦略・16,298 trades。
SHA-256: cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359（実行時一致）。
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ/EJ1イベント重複修正済み。
既存ログのRを集計し、Baselineを再計算していない。

計画コミットが正式結果コミットの直後で、追加ファイルが計画文書1件のみであることをGitHubで確認してからコードを作成した。実装コミットを分離した後、固定データの検証・集計・独立照合を実行した。
既存正式コードを変更せず再利用。中心値の全28分類と全期間主要数値・フラグは、既存正式CSVの全列と文字列表現まで一致した。既存コードと正式CSVのGit blob SHAも照合した。

EntryTime JST基準: Historical 2015–2021、Recent A 2022–2023、Recent B 2024–2025、Recent Combined 2022–2025、2026 Monitorは2026-09-09まで。2026は分類へ入力しない。
Historical 9,756、Recent Combined 5,547、2026 Monitor 995 trades。A+B=Combined。

## 固定OAT設定と分母
PF: 1.00 / 1.05 / 1.10。Ratio: 0.25 / 0.50 / 0.75。Sample: relaxed 20/10、official 30/15、strict 40/20（Combined/A・B）。
各軸で他の条件を中心値に固定。3軸×3点の252行をCSVへ出力した。中心値3表示を重複除外すると7設定×28=196判定。
警告残存率の主分母は7。表示上の9設定分母と各軸3点の回数もCSVに併記した。標本不足は警告に数えず分母に残し、別の件数として明示した。
事前固定ラベルは正式警告候補だけに適用し、7/7=頑健、5–6/7=中程度、0–4/7=不安定。非候補はNA。

## 設定別全体集計
| 設定 | STABLE | EDGE LOST | EDGE DECAY | INSUFFICIENT SAMPLE |
|---|---:|---:|---:|---:|
| PF_1.00 | 21 | 2 | 2 | 3 |
| OFFICIAL | 21 | 2 | 2 | 3 |
| PF_1.10 | 21 | 2 | 2 | 3 |
| RATIO_0.25 | 21 | 2 | 2 | 3 |
| RATIO_0.75 | 21 | 2 | 2 | 3 |
| SAMPLE_RELAXED | 23 | 2 | 2 | 1 |
| SAMPLE_STRICT | 21 | 2 | 2 | 3 |

relaxed sampleのみ14/15が判定可能になりSTABLEへ移る。正式分類は変更しない。16はrelaxedでも不足。

## 全28戦略の感度分類
S=STABLE、L=EDGE LOST、D=EDGE DECAY、I=INSUFFICIENT SAMPLE。
PF列は1.00/1.05/1.10、Ratio列は0.25/0.50/0.75、Sample列はrelaxed/official/strictの順。

| 戦略 | 正式 | PF 3点 | Ratio 3点 | Sample 3点 | 警告/7 | 標本不足/7 | 正式一致/7 |
|---|---|---|---|---|---:|---:|---:|
| 1_EJ_Log1 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 2_EJ_NightBlitz_20 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 3_EJ_NightBlitz_21 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 4_GJ_Port_Log1 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 5_GJ_Port_Log2 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 6_GJ_Old_Mon | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 7_GJ_Mon_Blitz | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 8_AJ_Core1 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 9_AJ_Core2 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 10_AJ_SatA | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 11_AJ_SatB | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 12_UJ_Short_Core | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 13_UJ_Fix_MidWeek | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 14_UJ_Sat_3rd | I | I/I/I | I/I/I | S/I/I | 0 | 6 | 6 |
| 15_UJ_Sat_Aug | I | I/I/I | I/I/I | S/I/I | 0 | 6 | 6 |
| 16_UJ_T10A | I | I/I/I | I/I/I | I/I/I | 0 | 7 | 7 |
| 17_EA_1B_Wed_Short | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 18_EA_2_MonWed_Short | L | L/L/L | L/L/L | L/L/L | 7 | 0 | 7 |
| 19_EA_3_WedThu_Long | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 20_EA_1A_MonTue_Short | D | D/D/D | D/D/D | D/D/D | 7 | 0 | 7 |
| 21_GA_B_3 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 22_GA_C_2 | L | L/L/L | L/L/L | L/L/L | 7 | 0 | 7 |
| 23_GA_F_2 | D | D/D/D | D/D/D | D/D/D | 7 | 0 | 7 |
| 24_GA_D_1 | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 25_AU_China_Demand | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 26_AJ_China_Demand | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 27_EA_China_Demand | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |
| 28_GA_China_Demand | S | S/S/S | S/S/S | S/S/S | 0 | 0 | 7 |

21の正式STABLE戦略は全設定STABLE（警告0/7）。China Demand 4戦略も同じ。10_AJ_SatAはHistorical AvgRが負で、比率はNA。STABLEは優位性が確認されたという意味ではない。
14はRecent A/B/Combined = 11/13/24、15は12/11/23。両者はrelaxedのみSTABLE、他6設定は不足。16は10/9/19で全7設定不足。警告0/7を安全性や優位性の根拠にはしない。

## 18/20/22/23：詳細
| 戦略 | 全設定分類 | 警告残存 | C/H AvgR | H AvgR | A AvgR | B AvgR | C AvgR | 2026 AvgR |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 18_EA_2_MonWed_Short | EDGE LOST | 7/7 (100%) | -0.214079 | 0.067619 | -0.088589 | 0.052981 | -0.014476 | 0.080747 |
| 20_EA_1A_MonTue_Short | EDGE DECAY | 7/7 (100%) | 0.137287 | 0.051965 | 0.029200 | -0.011645 | 0.007134 | -0.022074 |
| 22_GA_C_2 | EDGE LOST | 7/7 (100%) | -0.311805 | 0.143712 | -0.029259 | -0.060362 | -0.044810 | -0.078719 |
| 23_GA_F_2 | EDGE DECAY | 7/7 (100%) | 0.046124 | 0.074290 | -0.046941 | 0.053148 | 0.003427 | 0.013416 |

| 戦略 | H PF | C PF | 2026 PF | H trades | A trades | B trades | C trades | 2026 trades |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 18_EA_2_MonWed_Short | 1.242738 | 0.952395 | 1.408835 | 573 | 152 | 167 | 319 | 61 |
| 20_EA_1A_MonTue_Short | 1.206808 | 1.024160 | 0.892844 | 455 | 120 | 141 | 261 | 54 |
| 22_GA_C_2 | 1.443493 | 0.873060 | 0.764654 | 274 | 79 | 79 | 158 | 29 |
| 23_GA_F_2 | 1.439554 | 1.028037 | 1.144440 | 252 | 77 | 78 | 155 | 27 |

- **22_GA_C_2:** 全7設定でEDGE LOST。Historical PF 1.443493は最大の1.10条件を満たし、標本数はstrictも満たす。A/B双方が負で、C AvgR -0.044810、C PF 0.873060。Ratio軸変更時もLOST優先が維持される。2026もAvgR -0.078719、PF 0.764654だが、分類には利用していない。
- **18_EA_2_MonWed_Short:** 全7設定でEDGE LOST。今回、閾値による分類の不安定さは観察されなかった。B AvgR +0.052981は回復してもH +0.067619未満で、Cは負のまま。2026 +0.080747 / PF 1.408835は回復を示す補助情報だが分類対象外。「固定期間診断が頑健」と「現在も消失が持続している」は別の問いであり、前者から後者は結論しない。
- **20_EA_1A_MonTue_Short:** C/H AvgR 0.137287（約13.73%）で、25%/50%/75%の全条件に該当し全設定DECAY。今回の指定範囲では50%の選択への依存は観察されない。2026は負の補助情報。
- **23_GA_F_2:** C/H AvgR 0.046124（約4.61%）で全設定DECAY。Bと2026が正に戻っても、固定期間の判定は変わらない。20と同じく指定範囲内のratio閾値依存は観察されない。

4戦略とも各軸3/3、表示9/9、ユニーク7/7で警告。今回の残存率で22だけを順位付けすることはできない。全組み合わせ・未指定閾値・未指定期間には一般化しない。

## Phase 2への解釈
**22単独停止仮説を別研究として事前固定し検証へ進む材料として、診断は頑健だった。** PF1.05や50%という中心値だけで警告候補になったわけではない。
ただし、4候補とも7/7なので感度分析単独で22が唯一の候補とは言えない。22のA/B負および2026の負という連続値の経過は、18の回復とは異なる補助材料になる。
次研究を行うならE0_BASELINE（28戦略）vs E1_MINUS_22（22のみ停止）の仮説・評価方法を別途固定する。本研究は停止の改善効果を検証しておらず、即停止の根拠ではない。
新しい正式閾値の採用・既存分類の変更・Phase 2実行は行わない。

## 全28戦略の連続値
各期間のPF/Trades/TotalRを含む完全値はcontinuous_metrics CSVに保存。以下は小数6桁表示で、判定は表示丸め前。

| 戦略 | C/H AvgR | H AvgR | A AvgR | B AvgR | C AvgR | 2026 AvgR |
|---|---:|---:|---:|---:|---:|---:|
| 1_EJ_Log1 | 2.170808 | 0.111975 | 0.297444 | 0.188707 | 0.243076 | 0.026905 |
| 2_EJ_NightBlitz_20 | 1.584828 | 0.093669 | 0.166353 | 0.130026 | 0.148450 | 0.049655 |
| 3_EJ_NightBlitz_21 | 2.336076 | 0.045630 | 0.109092 | 0.104039 | 0.106594 | 0.058920 |
| 4_GJ_Port_Log1 | 1.864534 | 0.030574 | 0.062986 | 0.051027 | 0.057007 | 0.054479 |
| 5_GJ_Port_Log2 | 0.872029 | 0.096152 | 0.115703 | 0.053156 | 0.083848 | -0.033432 |
| 6_GJ_Old_Mon | 4.534162 | 0.073146 | 0.270976 | 0.392333 | 0.331655 | 0.203000 |
| 7_GJ_Mon_Blitz | 4.941058 | 0.016805 | 0.057308 | 0.108507 | 0.083035 | 0.061923 |
| 8_AJ_Core1 | 2.683774 | 0.058337 | 0.160286 | 0.152843 | 0.156564 | 0.077381 |
| 9_AJ_Core2 | 1.087799 | 0.198803 | 0.382749 | 0.049766 | 0.216257 | -0.131833 |
| 10_AJ_SatA | NA | -0.001858 | 0.043343 | 0.017739 | 0.030633 | -0.037600 |
| 11_AJ_SatB | 0.821670 | 0.072659 | 0.082364 | 0.037039 | 0.059701 | -0.101818 |
| 12_UJ_Short_Core | 2.100915 | 0.184569 | 0.475391 | 0.302000 | 0.387763 | -0.094697 |
| 13_UJ_Fix_MidWeek | 1.705068 | 0.074976 | 0.126787 | 0.128892 | 0.127839 | -0.035228 |
| 14_UJ_Sat_3rd | 4.051482 | 0.196796 | 0.815556 | 0.781880 | 0.797315 | 0.105926 |
| 15_UJ_Sat_Aug | 0.605333 | 0.323214 | -0.083333 | 0.500000 | 0.195652 | 1.200000 |
| 16_UJ_T10A | 2.011028 | 0.152492 | 0.279778 | 0.336543 | 0.306667 | 0.068889 |
| 17_EA_1B_Wed_Short | 0.902298 | 0.165701 | 0.189705 | 0.102619 | 0.149512 | -0.017744 |
| 18_EA_2_MonWed_Short | -0.214079 | 0.067619 | -0.088589 | 0.052981 | -0.014476 | 0.080747 |
| 19_EA_3_WedThu_Long | 1.307617 | 0.087798 | 0.145222 | 0.080696 | 0.114807 | -0.019419 |
| 20_EA_1A_MonTue_Short | 0.137287 | 0.051965 | 0.029200 | -0.011645 | 0.007134 | -0.022074 |
| 21_GA_B_3 | 0.809729 | 0.015319 | 0.014412 | 0.010455 | 0.012404 | 0.029273 |
| 22_GA_C_2 | -0.311805 | 0.143712 | -0.029259 | -0.060362 | -0.044810 | -0.078719 |
| 23_GA_F_2 | 0.046124 | 0.074290 | -0.046941 | 0.053148 | 0.003427 | 0.013416 |
| 24_GA_D_1 | 0.812789 | 0.062831 | 0.118615 | -0.015613 | 0.051068 | 0.029218 |
| 25_AU_China_Demand | 0.919707 | 0.053652 | 0.057601 | 0.041040 | 0.049344 | -0.006434 |
| 26_AJ_China_Demand | 1.682314 | 0.092525 | 0.184744 | 0.125900 | 0.155657 | 0.109333 |
| 27_EA_China_Demand | 1.214420 | 0.094467 | 0.069783 | 0.160578 | 0.114722 | -0.034952 |
| 28_GA_China_Demand | 1.797114 | 0.064035 | 0.059907 | 0.171374 | 0.115077 | -0.012571 |

## 検証と再現方法
- 12件の単体テスト合格。固定設定集合、全sample境界、PF厳密不等号、ratio等号、分類優先順位、DECAYに追加条件なし、NA/inf、H<=0比率NA、記述ラベル、Monitor非入力、hash不一致停止を確認。
- 別実装のpandas集計で140期間のTrades/AvgR/PF/TotalR、28比率、252表示分類（196ユニーク分類）、28戦略の残存・一致・不足回数、出力CSV hashを照合し一致（指標atol=rtol=1e-10）。独立監査は正式/感度モジュールをimportしていない。
- 2026 Rを変更する統合確認で全感度分類・戦略要約が不変、Monitor連続値だけが変化することを確認。
- 既存正式CSVの分類を改変すると照合で停止することを確認。
- notebook全コードセルの構文と構造、内蔵ソース一致、ローカル実行で3分析CSVのバイト一致を確認。run recordは実行時刻が異なるため分析CSVのみバイト比較。
- ローカルPython 3.12 / pandas 2.2.3で実行。Colabサーバー上では未実行。アップロード・DriveセルはColab用として提供。
- GitHub最終treeを元treeと比較し、既存ファイルのblob SHA不変と研究用新規ファイルのみの追加を確認する。

```sh
python src/research/edge_decay_sensitivity_analysis.py --baseline /path/to/daily_stop_baseline_trades.csv --primary-csv results/edge_decay/strategy_edge_decay_final_classification.csv --output-dir /content --implementation-commit c9a937b459a5bb4fc4b7fa41985a8a972fba9d42
python -m unittest discover -s tests -p test_edge_decay_sensitivity_analysis.py -v
python tests/verify_edge_decay_sensitivity_results.py --baseline /path/to/daily_stop_baseline_trades.csv --output-dir /content
```

## 作成ファイル
- docs/40_edge_decay_sensitivity_validation_plan.md
- docs/41_edge_decay_sensitivity_final_result.md
- src/research/edge_decay_sensitivity_analysis.py
- tests/test_edge_decay_sensitivity_analysis.py
- tests/verify_edge_decay_sensitivity_results.py
- notebooks/edge_decay_sensitivity_validation.ipynb（本文確定結果、/content出力、任意Driveセル）
- results/edge_decay_sensitivity/edge_decay_sensitivity_classifications.csv（252行）
- results/edge_decay_sensitivity/edge_decay_sensitivity_strategy_summary.csv（28行）
- results/edge_decay_sensitivity/edge_decay_sensitivity_continuous_metrics.csv（28行）
- results/edge_decay_sensitivity/edge_decay_sensitivity_run_record.csv（1行）
