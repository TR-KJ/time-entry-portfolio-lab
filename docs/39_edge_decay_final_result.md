# Edge Decay / Edge Deterioration：最終結果

**STABLE 21戦略、EDGE DECAY候補2戦略、EDGE LOST候補2戦略、INSUFFICIENT SAMPLE 3戦略。分類を理由とするEA停止は実施しない。**

検証日: 2026-09-12 JST（詳細時刻はrun_record CSV）
Repo: TR-KJ/time-entry-portfolio-lab
Branch: research/edge-decay-validation
起点: 7f36c3da01dcafd4e9cfb4891467349e0ab37eba
計画コミット: 402fc221b307985b8eb75abcc84bc3b0888400b5
実装コミット: b9f8127f5a3b59f27883fbe32997791eb920e9e9
結果コミット: 本文書・確定CSV・確定結果入りノートブックを追加したコミット（最終報告にSHA記載）

## 固定データと分類
Baseline: daily_stop_baseline_trades.csv、28戦略、16,298 trades。
SHA-256: cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ修正済み、EJ1イベント重複修正済み。
既存CSVのRを集計。Baseline Trade Log再計算なし。

EntryTime JST基準でHistorical 2015–2021、Recent A 2022–2023、Recent B 2024–2025、Recent Combined 2022–2025、Monitor 2026-01-01～09-09。Monitorは分類条件へ入力しない。

Primary metric: Avg R / Trade。
計画どおり、Combined<30 tradesまたはA/Bのどちらか<15ならINSUFFICIENT SAMPLEを最優先。
EDGE LOST: H AvgR>0、H PF>1.05、Combined AvgR<=0、Combined PF<=1.00、A/B双方のAvgR<H AvgR。
EDGE DECAY: Combined AvgR<=H AvgR×0.50、A/B双方のAvgR<H AvgR、Combined PF<H PF。LOSTを優先。
残りはSTABLE。追加条件・閾値変更なし。表示は小数6桁、判定は丸め前。

## 全28戦略
| 戦略 | 分類 | Historical AvgR | Recent A AvgR | Recent B AvgR | Recent Combined AvgR | 2026 AvgR |
|---|---|---:|---:|---:|---:|---:|
| 1_EJ_Log1 | STABLE | 0.111975 | 0.297444 | 0.188707 | 0.243076 | 0.026905 |
| 2_EJ_NightBlitz_20 | STABLE | 0.093669 | 0.166353 | 0.130026 | 0.148450 | 0.049655 |
| 3_EJ_NightBlitz_21 | STABLE | 0.045630 | 0.109092 | 0.104039 | 0.106594 | 0.058920 |
| 4_GJ_Port_Log1 | STABLE | 0.030574 | 0.062986 | 0.051027 | 0.057007 | 0.054479 |
| 5_GJ_Port_Log2 | STABLE | 0.096152 | 0.115703 | 0.053156 | 0.083848 | -0.033432 |
| 6_GJ_Old_Mon | STABLE | 0.073146 | 0.270976 | 0.392333 | 0.331655 | 0.203000 |
| 7_GJ_Mon_Blitz | STABLE | 0.016805 | 0.057308 | 0.108507 | 0.083035 | 0.061923 |
| 8_AJ_Core1 | STABLE | 0.058337 | 0.160286 | 0.152843 | 0.156564 | 0.077381 |
| 9_AJ_Core2 | STABLE | 0.198803 | 0.382749 | 0.049766 | 0.216257 | -0.131833 |
| 10_AJ_SatA | STABLE | -0.001858 | 0.043343 | 0.017739 | 0.030633 | -0.037600 |
| 11_AJ_SatB | STABLE | 0.072659 | 0.082364 | 0.037039 | 0.059701 | -0.101818 |
| 12_UJ_Short_Core | STABLE | 0.184569 | 0.475391 | 0.302000 | 0.387763 | -0.094697 |
| 13_UJ_Fix_MidWeek | STABLE | 0.074976 | 0.126787 | 0.128892 | 0.127839 | -0.035228 |
| 14_UJ_Sat_3rd | INSUFFICIENT SAMPLE | 0.196796 | 0.815556 | 0.781880 | 0.797315 | 0.105926 |
| 15_UJ_Sat_Aug | INSUFFICIENT SAMPLE | 0.323214 | -0.083333 | 0.500000 | 0.195652 | 1.200000 |
| 16_UJ_T10A | INSUFFICIENT SAMPLE | 0.152492 | 0.279778 | 0.336543 | 0.306667 | 0.068889 |
| 17_EA_1B_Wed_Short | STABLE | 0.165701 | 0.189705 | 0.102619 | 0.149512 | -0.017744 |
| 18_EA_2_MonWed_Short | EDGE LOST | 0.067619 | -0.088589 | 0.052981 | -0.014476 | 0.080747 |
| 19_EA_3_WedThu_Long | STABLE | 0.087798 | 0.145222 | 0.080696 | 0.114807 | -0.019419 |
| 20_EA_1A_MonTue_Short | EDGE DECAY | 0.051965 | 0.029200 | -0.011645 | 0.007134 | -0.022074 |
| 21_GA_B_3 | STABLE | 0.015319 | 0.014412 | 0.010455 | 0.012404 | 0.029273 |
| 22_GA_C_2 | EDGE LOST | 0.143712 | -0.029259 | -0.060362 | -0.044810 | -0.078719 |
| 23_GA_F_2 | EDGE DECAY | 0.074290 | -0.046941 | 0.053148 | 0.003427 | 0.013416 |
| 24_GA_D_1 | STABLE | 0.062831 | 0.118615 | -0.015613 | 0.051068 | 0.029218 |
| 25_AU_China_Demand | STABLE | 0.053652 | 0.057601 | 0.041040 | 0.049344 | -0.006434 |
| 26_AJ_China_Demand | STABLE | 0.092525 | 0.184744 | 0.125900 | 0.155657 | 0.109333 |
| 27_EA_China_Demand | STABLE | 0.094467 | 0.069783 | 0.160578 | 0.114722 | -0.034952 |
| 28_GA_China_Demand | STABLE | 0.064035 | 0.059907 | 0.171374 | 0.115077 | -0.012571 |

STABLEは固定条件への非該当を意味し、エッジや将来利益を保証しない。10_AJ_SatAはHistorical AvgRが負であり「以前の優位性が確認された」とは扱わない（CSVのHistoricalEdgeConfirmed=False）。この点を理由に分類ルールを変更していない。
14/15/16は標本不足につき赤黄緑分類から除外する。

## 候補の詳細・2026補助確認
| 戦略 | Recent trades | Historical PF | Recent PF | Recent TotalR | 2026 trades | 2026 PF | 2026 TotalR |
|---|---:|---:|---:|---:|---:|---:|---:|
| 18_EA_2_MonWed_Short | 319 | 1.242738 | 0.952395 | -4.617778 | 61 | 1.408835 | 4.925556 |
| 20_EA_1A_MonTue_Short | 261 | 1.206808 | 1.024160 | 1.862000 | 54 | 0.892844 | -1.192000 |
| 22_GA_C_2 | 158 | 1.443493 | 0.873060 | -7.080000 | 29 | 0.764654 | -2.282857 |
| 23_GA_F_2 | 155 | 1.439554 | 1.028037 | 0.531111 | 27 | 1.144440 | 0.362222 |

- **18_EA_2_MonWed_Short — EDGE LOST候補**: Recent Aが負、Recent Bは正に回復しているがHistorical AvgR未満。Combinedは-0.014476R/trade、PF 0.952395で固定LOST条件に該当する。2026は+0.080747R/trade、PF 1.408835で、消失の持続という解釈を弱める材料。分類自体は変更しない。
- **22_GA_C_2 — EDGE LOST候補**: Recent A/Bとも負、Combined -0.044810R/trade、PF 0.873060。2026も-0.078719R/trade、PF 0.764654で消失仮説を補強する方向。ただし2026は29 tradesの途中年。
- **20_EA_1A_MonTue_Short — EDGE DECAY候補**: Historical +0.051965からCombined +0.007134R/trade（約13.73%へ低下）、PF 1.206808→1.024160。2026は-0.022074R/trade、PF 0.892844で劣化仮説を補強する方向。
- **23_GA_F_2 — EDGE DECAY候補**: Historical +0.074290からCombined +0.003427R/trade（約4.61%へ低下）、PF 1.439554→1.028037。Recent Bは回復しているがHistorical未満。2026は+0.013416R/trade、PF 1.144440で、最近4年合算より回復し劣化の進行という解釈を弱める一方、Historical水準未満。27 tradesの補助材料のみ。

補強・弱化は方向を説明したもの。新しい分類基準、スコア、2026による再分類は導入していない。

## 標本不足
- 14_UJ_Sat_3rd: Recent A 11 / B 13 / Combined 24 trades。
- 15_UJ_Sat_Aug: Recent A 12 / B 11 / Combined 23 trades。
- 16_UJ_T10A: Recent A 10 / B 9 / Combined 19 trades。
件数条件を満たさないため成績の符号によらず判定保留。

## 検証
- 計画コミットの変更ファイルがdocs/38のみで、起点コミットの直後であることをGitHub上で確認してからコード作成。
- Baseline hash完全一致、16,298行、28戦略、戦略番号1–28、重複なし、日時整合、R整合を確認。
- 11件の単体テスト合格。LOST優先、標本数の30/15境界、50%の等号、PF 1.05の厳密不等号、両期低下条件、PF低下条件、追加適格条件なし、未定義PF・無限PF、期間境界、DD・連敗・退出率、2026非依存、hash不一致停止を確認。
- production moduleをimportしないpandas/numpyによる独立集計で、期間140行＋年別336行＝476行の全指標と全28分類を照合し一致（atol=rtol=1e-10）。
- Historical 9,756、Recent Combined 5,547、Monitor 995 trades。A+B=Combined、合計16,298。
- 公表済みTotalR Historical 768.488273、Recent Combined 601.960585、Monitor 19.818791と小数6桁精度で一致。
- ExitReasonはSL/TP/TimeExitのみ。Other件数ゼロ。率は0–1、AvgLossRは負号付き。
- ノートブック構造確認、全コードセルの構文確認、内蔵解析コードのローカル実行により3本の分析CSVがバイト単位で一致。
- ローカルPython 3.12 / pandas 2.2.3。Colabサーバー上では実行していない。アップロード・Drive連携セルはColabで使用するセルとして用意し、サーバー実行済みとは扱わない。

## 解釈と研究境界
2022–2026は過去研究で既に参照済みで、完全未閲覧holdoutではない。これは事前固定した記述的診断であり、統計的なエッジ消失の証明ではない。
China4停止研究とは独立。China4の4戦略はいずれも本ルールではSTABLE。
EA/VPS/SET/live運用コード・設定は変更していない。28戦略の正式構成を維持。
停止候補の組み合わせ探索、期間探索、TP<SL等の別研究、スコア重み調整、Money Simulationは実施していない。
候補が見つかったため、必要ならPhase 2として停止仮説を別途事前固定し独立検証する。本研究の結果だけで停止へ進めない。

## 作成ファイル
- docs/38_edge_decay_validation_plan.md
- docs/39_edge_decay_final_result.md
- src/research/edge_decay_analysis.py
- tests/test_edge_decay_analysis.py
- tests/verify_edge_decay_results.py
- notebooks/edge_decay_validation.ipynb
- results/edge_decay/strategy_edge_decay_summary.csv（28×5期間、全指標）
- results/edge_decay/strategy_edge_decay_yearly.csv（28×12年、全指標）
- results/edge_decay/strategy_edge_decay_final_classification.csv（28分類、各期主要値、2026補助）
- results/edge_decay/strategy_edge_decay_run_record.csv（hash、Branch、計画SHA、検証時刻、期間、規則文書、CSV名・hash）

実行例:
```sh
python src/research/edge_decay_analysis.py --baseline /path/to/daily_stop_baseline_trades.csv --output-dir /content
python -m unittest discover -s tests -p test_edge_decay_analysis.py -v
python tests/verify_edge_decay_results.py --baseline /path/to/daily_stop_baseline_trades.csv --output-dir /content
```

Colab本文に今回の確定サマリーを収録し、実行時にも全表を表示して/contentへ同一CSVを出力する。任意のDrive保存セルあり。
