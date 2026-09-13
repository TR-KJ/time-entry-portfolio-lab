# 2026 Deployment Reset Money Simulation：確定結果

**D1_MINUS_22とD3_MINUS_20が事前条件を通過し、Deployment Reset候補 / Shadow Forward候補となった。** D2_MINUS_18・D4_MINUS_23は対象外。
これは既閲覧2026データの回顧比較であり、新規OOSではない。live採用・EA停止決定ではない。正式28戦略およびEA/VPS/SET/liveコード・設定、既存Edge Decay正式分類・Sensitivity・Phase2 single-stop結果は変更していない。

## 固定手順と入力
Branch: research/deployment-reset-2026-validation
既存Money仕様の参照元commit: abd9b87b498e0cccdcf2d33ed71736aa32e491fb
計画SHA: [524b93bdcfc3cccf739c85cf8826f236e511fa47](https://github.com/TR-KJ/time-entry-portfolio-lab/commit/524b93bdcfc3cccf739c85cf8826f236e511fa47)
実装SHA: [b2822c6053f2e831295a5457a586fc9dbcd6b5b5](https://github.com/TR-KJ/time-entry-portfolio-lab/commit/b2822c6053f2e831295a5457a586fc9dbcd6b5b5)
結果SHA: この結果文書を追加する確定commit（自己参照を避け、最終報告に完全SHAを記載）。

計画文書だけをGitHubへコミットし、内容・branch ref・計画1ファイルのみの差分を確認してからコードを作成した。実装3ファイルもGitHubへ固定し、親が計画SHAであることを確認してから実データを比較した。
Baseline: 28戦略・16,298 trades。SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359 は実行時一致。Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1重複修正済み。固定ログの再計算・再構築なし。

2026-01-01 00:00 JST以上、2026-09-10 00:00 JST未満のEntryTimeで抽出したD0は995 trades。D1は22_GA_C_2のみ除外し966、D2は18_EA_2_MonWed_Shortのみ除外し934、D3は20_EA_1A_MonTue_Shortのみ除外し941、D4は23_GA_F_2のみ除外し968 trades。

## 採用した固定Money仕様
全20条件で2026-01-01の資金・DDピークを500,000円にReset。2015–2025のPnL・DDピーク・資金差は持ち込んでいない。
Risk=0.25/1.0/1.5/2.0%。代表1.5%は研究値、0.25%はlive検証参照値。
EntryTime JST月曜06:00を週境界とする。週初Balance×Riskを各取引で週内固定し、翌週に前週確定損益を反映して複利更新する。初週は部分週でも50万円をBaseとする。
直前の無変更エンジンに2026・当該構成の行だけを渡して実行した。PnL=WeeklyBase×(RiskPct/100)×Pips/SL、SLは各行の実値。Decimal精度40、通貨額の内部丸めなし、表示時のみ丸める。保存Rは変更していない。
理論Money Simulation、lot上限なし、pip valueは約分。lot step/min/max/MaxAutoLot/AllowMinLot等のbroker制約は適用しない。
実運用制約付き比較: **NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS**。過去JPY pip value・volume min/max/step・週初浮動Equityが不足し、架空値による比較はしていない。

DDは50万円を含む決済Balanceのピークから計算。決済順はCloseTime→EntryTime→StrategyNo→元行番号。MaxDDは正、Worst損失は負表示。
WorstDay=JST決済日PnL/日初Balance、WorstWeek=月曜06:00週PnL/週初Balanceの各最小（%）。MoneyRoMD=純利益/最大DD円。期間末まで未決済・週境界跨ぎはないことを検証した。

## 5構成×4Risk

| 構成 | Risk | Trades | Final Capital（円） | 純利益（円） | D0差額（円） |
|---|---:|---:|---:|---:|---:|
| D0_BASELINE | 0.25% | 995 | 524,211.02 | 24,211.02 | +0.00 |
| D1_MINUS_22 | 0.25% | 966 | 527,240.19 | 27,240.19 | +3,029.17 |
| D2_MINUS_18 | 0.25% | 934 | 518,030.60 | 18,030.60 | -6,180.42 |
| D3_MINUS_20 | 0.25% | 941 | 525,907.31 | 25,907.31 | +1,696.29 |
| D4_MINUS_23 | 0.25% | 968 | 523,750.06 | 23,750.06 | -460.96 |
| D0_BASELINE | 1.0% | 995 | 588,769.85 | 88,769.85 | +0.00 |
| D1_MINUS_22 | 1.0% | 966 | 602,808.97 | 102,808.97 | +14,039.11 |
| D2_MINUS_18 | 1.0% | 934 | 564,284.15 | 64,284.15 | -24,485.71 |
| D3_MINUS_20 | 1.0% | 941 | 598,067.16 | 98,067.16 | +9,297.30 |
| D4_MINUS_23 | 1.0% | 968 | 586,868.64 | 86,868.64 | -1,901.21 |
| D0_BASELINE | 1.5% | 995 | 623,594.14 | 123,594.14 | +0.00 |
| D1_MINUS_22 | 1.5% | 966 | 646,281.23 | 146,281.23 | +22,687.09 |
| D2_MINUS_18 | 1.5% | 934 | 587,725.77 | 87,725.77 | -35,868.37 |
| D3_MINUS_20 | 1.5% | 941 | 640,012.00 | 140,012.00 | +16,417.87 |
| D4_MINUS_23 | 1.5% | 968 | 620,737.01 | 120,737.01 | -2,857.13 |
| D0_BASELINE | 2.0% | 995 | 650,709.19 | 150,709.19 | +0.00 |
| D1_MINUS_22 | 2.0% | 966 | 682,750.56 | 182,750.56 | +32,041.36 |
| D2_MINUS_18 | 2.0% | 934 | 604,646.50 | 104,646.50 | -46,062.70 |
| D3_MINUS_20 | 2.0% | 941 | 675,745.27 | 175,745.27 | +25,036.08 |
| D4_MINUS_23 | 2.0% | 968 | 646,947.50 | 146,947.50 | -3,761.69 |

## 代表1.5%の副次指標

| 構成 | MaxDD % | Worst Day % | Worst Week % | Money RoMD | 最大DD円 |
|---|---:|---:|---:|---:|---:|
| D0_BASELINE | 25.500831 | -7.138401 | -8.095572 | 0.647954 | 190,745.22 |
| D1_MINUS_22 | 20.115026 | -7.138401 | -7.933407 | 1.017912 | 143,707.19 |
| D2_MINUS_18 | 25.685114 | -6.320926 | -6.989372 | 0.478965 | 183,156.86 |
| D3_MINUS_20 | 24.188005 | -7.077285 | -8.227572 | 0.763759 | 183,319.56 |
| D4_MINUS_23 | 25.199998 | -7.138401 | -7.985572 | 0.640978 | 188,363.81 |

| 構成 | 1.5% Reset改善 | 他3Risk頑健性 | Shadow Forward候補 |
|---|---|---|---|
| D1_MINUS_22 | 可 | 通過 | 候補 |
| D2_MINUS_18 | 不可 | 不通過 | 対象外 |
| D3_MINUS_20 | 可 | 通過 | 候補 |
| D4_MINUS_23 | 不可 | 不通過 | 対象外 |

## 判定と解釈
代表1.5%のFinal Capital差>0、他3Riskの差>=0、入力・テスト・独立照合PASSを必須とし、丸め前で判定した。DD改善による利益減少の救済はない。

22除外は1.5%でFinal Capitalが623,594.14円から646,281.23円となり、純利益は123,594.14円から146,281.23円へ増加。D0差+22,687.09円。MaxDDは25.500831%から20.115026%へ5.385805ポイント改善し、Worst Weekも0.162166ポイント改善。Worst Dayは表示精度では同じ。
20除外は1.5%でD0差+16,417.87円、MaxDDは1.312826ポイント改善。一方、Worst Weekは-8.095572%から-8.227572%へ0.132000ポイント悪化。事前固定条件は利益額優先で、Worst Week非悪化を追加条件にはしていないため候補に残る。
18除外は日次/週次の最悪損失率が改善しても、利益差-35,868.37円で対象外。23除外もDDが改善しても利益差-2,857.13円で対象外。
全Riskの記述的Final Capital順位はD1>D3>D0>D4>D2。順位をlive採用に置き換えない。22と20の両方をShadow Forward候補とし、複数同時除外は検証していない。
2015継続Moneyで22除外が不採用だったことと今回の改善は、開始資金と評価期間が異なるため両立する。今回もエッジ消失の証明や将来の利益保証ではない。旧研究の診断・判定は保持する。結果後の候補・Risk・閾値・期間変更、月次/四半期の窓探索は行っていない。

## 検証と再実行
- 単体テスト15件通過（Reset、初期DD、週境界、行別SL、単独除外、期間/週跨ぎ停止、破綻、hash不一致、未登録条件、主判定等号、頑健性、PENDING）。
- 独立numpy/pandas実装で138,678値を照合。決済曲線・週初資金・週次複利積・全20主要行・16差分行・5詳細行・4判定が一致。
- 既存v1.1の関数を副作用なく抽出し、全20条件の取引PnLとFinal Capitalが一致。
- 事前固定した照合許容誤差は相対1e-10、絶対1e-7。取引件数・行IDは完全一致。
- NotebookのSHA固定コード取得・分析・独立監査セルをローカル再実行し、実行日時等を含むrun record以外の8本CSVがバイト一致。環境制約によりHTTPS取得と書き込み可能な実行プロセスが分かれるため、実際に固定SHAから取得・hash検証した応答を保存し、取得セルに同一応答を渡して再実行した。Colabサーバー上では未実行。
- GitHub保存treeで参照元の既存359ファイルがすべて不変であることを確認した。追加ファイルは研究専用のみ。

## 作成ファイル
- docs/50_deployment_reset_2026_plan.md
- docs/51_deployment_reset_2026_result.md
- src/research/deployment_reset_2026_money_simulation.py
- tests/test_deployment_reset_2026.py
- tests/verify_deployment_reset_2026.py
- notebooks/deployment_reset_2026_money_simulation.ipynb
- results/deployment_reset_2026/deployment_reset_2026_summary.csv
- results/deployment_reset_2026/deployment_reset_2026_risk_comparison.csv
- results/deployment_reset_2026/deployment_reset_2026_detailed_metrics.csv
- results/deployment_reset_2026/deployment_reset_2026_run_record.csv
- results/deployment_reset_2026/deployment_reset_2026_decision.csv
- results/deployment_reset_2026/deployment_reset_2026_verification.csv
- results/deployment_reset_2026/deployment_reset_2026_constraint_status.csv
- 監査用weekly.csv / trade_log.csv（deployment_reset_2026_接頭辞）はローカル成果物およびColab /contentに出力。元取引明細を大量重複させないためGitHubにはこの2本を含めない。Run recordにその保存範囲とhashを記録する。

Colab本文に確定20条件と代表1.5%詳細を埋め込み、再実行時もテーブル表示・/content CSV出力する。Drive保存セルは初期OFF。
