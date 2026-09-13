# 2026 Deployment Reset Money Simulation：事前固定計画

2026-09-13 JST。独立研究。新規コード作成・5構成Money比較前に本書のみをGitHubへコミットし、commit SHA、内容、branch refを確認する。その後にのみ実装する。

## 出典と研究の位置づけ
Repo: TR-KJ/time-entry-portfolio-lab
Branch: research/deployment-reset-2026-validation
起点: 直前22単独除外Money Simulationの確定commit abd9b87b498e0cccdcf2d33ed71736aa32e491fb。
そのcommitの docs/48_edge_decay_phase2_money_simulation_plan.md と src/research/edge_decay_phase2_money_simulation.py を確認済み。既存v1.1由来の週次資金計算、検証、指標関数を変更せず再利用する。
目的は2015年以来の累積元本差を消し、2026-01-01に同額資金で新規開始した場合の2026-09-09までの円成績を比較すること。
2026は既閲覧であり、新規OOS・未閲覧holdoutではない。回顧的Deployment Reset Simulationである。将来予測や即live採用ではなく、今後のShadow Forward候補の資料とする。
旧研究の2015継続運用という問い・結果を上書きしない。18/20/22/23のEdge Decay正式分類・Sensitivity・Phase2 single-stop結果も変更しない。EA/VPS/SET/liveコード・設定は一切変更しない。

## 固定入力・5構成
Baseline 28戦略・16,298 trades、SHA-256:
cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。固定Trade Logを再計算・再構築しない。元ファイルのhash不一致、件数/戦略ID不一致は停止。
- D0_BASELINE: 28戦略
- D1_MINUS_22: 22_GA_C_2 のみ除外
- D2_MINUS_18: 18_EA_2_MonWed_Short のみ除外
- D3_MINUS_20: 20_EA_1A_MonTue_Short のみ除外
- D4_MINUS_23: 23_GA_F_2 のみ除外
完全名を照合する。追加候補・複数除外・組合せ探索は禁止。

## 期間とReset
EntryTime JSTで2026-01-01 00:00以上、2026-09-10 00:00未満を抽出する（9月9日全日を含む）。資金曲線はCloseTimeで確定損益を反映する。
元ログの期間境界跨ぎを検証し、entry/closeが本期間の内外で異なる取引は停止。entry週の月曜06:00+7日以降に決済する週跨ぎも既存仕様どおり停止。勝手な所属変更や未来損益参照をしない。
全構成・全Riskで初期資金とDDピークを500,000 JPYにReset。最初の部分週も500,000円から開始し、2015–2025のPnL・ピーク・資金差を持ち込まない。過去年のデータは入力整合検証にのみ使い、Money計算へ投入しない。

## 固定Money仕様
初期資金500,000円。Riskは0.25%, 1.0%, 1.5%, 2.0%の4点のみ。代表Riskは1.5%（研究代表値）、0.25%は保守的live検証参照値として区別する。
EntryTime JST月曜06:00を週境界とし、その前は前週。週初Balance×Riskを週内の各取引のリスク額として固定する。同時保有も各取引同額。翌週に前週の全確定PnLを反映して複利更新。無取引週は残高不変。浮動損益・入出金・利息なし。週内取引ごとの複利や新しい非複利modeを作らない。
既存v1.1同様、lot上限なしの理論Money Simulation。
PnL = WeeklyBase × (RiskPct / 100) × Pips / SL
各行の実際のSLを使い、UJ12可変SLを保持する。保存R列は上書きせず、Pips/SLとの微小なCSV丸め差を記録する。内部通貨丸めなし（既存Decimal精度40）、表示時のみ丸める。週初資金または確定残高<=0は停止・候補認定不可。
pip valueは式上約分される。lot step/min/max/MaxAutoLot/AllowMinLot等のbroker制約は主研究に適用しない。historical JPY pip value、volume min/max/step、週初浮動Equityが不足する実運用制約付き比較は NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS と明記する。架空のbroker値は用いない。

## 指標・判定（結果後変更禁止）
1. Primary metricは2026-09-09終了時点のFinal Capital / Net Profit。利益額増加を最優先する。
2. D1–D4についてD0との差（候補−D0）を全Riskで表示する。
3. 代表1.5%のFinal Capital差>0を「2026 Reset改善」の必須条件とする。等号は改善ではない。
4. 他の固定Risk 0.25/1.0/2.0%のFinal Capital差が全て>=0であることを頑健性条件とする。
5. hash・入力・資金健全性・テスト・独立照合が通過し、3と4を満たしたときのみ DEPLOYMENT_RESET_CANDIDATE / Shadow Forward候補とする。未検証はPENDING、条件不通過はNOT_CANDIDATE。検証失敗は確定判定不可。
6. Secondary metricsはMaxDD %, Worst Day %, Worst Week %, Money RoMD, Trades, Net Profit（加えて既存MaxDD円/Return/PFを記録可）。DD改善でFinal Capital減少を救済しない。
7. 既閲覧2026結果を見て候補追加・閾値変更・Risk追加・期間変更をしない。
8. 既存研究の正式分類・Sensitivity・single-stop結果は保持する。
9. 5構成間ランキングは記述表示のみ。最良構成のlive採用はしない。
10. 月次/四半期推移は出す場合も記述補助のみで採否に用いず、追加の窓探索をしない。今回は期間全体と監査用週次/取引記録を基本とする。
比較は丸め前。1.5%改善フラグと他Risk頑健性フラグを分けて表示する。複数候補が通過すればすべてを候補として扱い、後付けの選別条件を追加しない。

指標定義は直前研究を再利用する。決済順序=CloseTime→EntryTime→StrategyNo→元行番号。DDはReset初期資金を含む確定Balanceピークから計算し、正表示。MaxDD円とMaxDD%はそれぞれ期間内最大。
MoneyRoMD=期間純利益/最大DD円（DDなしはNA）。MoneyPF=利益円合計/損失円絶対値（損失なしはNA）。
WorstDayPct=JST決済日PnL/当日開始Balance×100の最小、WorstWeekPct=月曜06:00 JST週PnL/当週開始Balance×100の最小。損失は負表示。初週の分母はReset資金。無取引期間は残高不変。DD差は負が改善、Worst差は負が悪化。年率換算しない。

## 実装順序・出力
A既存仕様確認→B本書のみGitHub commit/SHA・内容確認→C実装・実装commit確認→D固定Baseline hash確認→E2026のみで5×4比較→Fテスト・独立照合→G確定CSV/notebook/最終文書commit確認。
docs/50_deployment_reset_2026_plan.md（本書、固定後変更なし）
docs/51_deployment_reset_2026_result.md（最終結果）
notebooks/deployment_reset_2026_money_simulation.ipynb
src/research/deployment_reset_2026_money_simulation.py、研究専用test/独立照合コード。
results/deployment_reset_2026/に:
- deployment_reset_2026_summary.csv（5×4、主要結果）
- deployment_reset_2026_risk_comparison.csv（4候補×4Risk、D0差分）
- deployment_reset_2026_detailed_metrics.csv（代表1.5%、5構成詳細/差分）
- deployment_reset_2026_run_record.csv
- deployment_reset_2026_decision.csv
- deployment_reset_2026_verification.csv
- deployment_reset_2026_constraint_status.csv
監査用weekly/trade_log CSVは必要に応じて追加、判定条件追加には使わない。
Colab本文に5×4結果・代表1.5%詳細を表示し、/contentへCSVを出力。任意Drive保存セルは初期OFF。実装SHAを固定してコード取得、Baseline upload/hash照合、独立照合まで実行可能とする。ローカル実行かColabサーバー実行か区別する。
Run record: Baseline hash/count、source commit、Branch、計画SHA、実装SHA、実行日JST、5構成、初期資金、全Risk/代表値、期間、WeeklyBase/Lot仕様、判定ルール、CSV名/hash、検証状態、Baseline再計算なし・新規OOSではない・live変更なし。結果SHAは自己参照を避け確定commitとして最終報告に記載する。

## 検証
hash不一致で停止、完全名除外、期間Reset（前年PnL/ピーク非持込）、月曜06:00境界・年初部分週、同時保有・行別SL・初回損失DD、週/期間跨ぎ停止、資金破綻、未登録候補/Risk停止、主判定等号・他Risk非負・未検証判定をテストする。
独立したfloat/pandas等による全20構成Riskの主要指標、週次複利積、決済資金曲線を照合する。旧v1.1のPnL/Final Capitalとも照合する。数値照合許容誤差は相対1e-10・絶対1e-7（円・%・比率）、Tradesは完全一致。これは検算許容誤差であり利益差の採否に許容幅を設けるものではない。
Notebook分析・監査セルをローカル再実行し、実行日時等を除く分析/判定CSV一致を確認する。全既存ファイル不変をGitHub tree差分で確認する。
