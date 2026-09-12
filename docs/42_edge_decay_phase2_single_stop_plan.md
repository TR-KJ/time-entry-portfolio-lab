# Edge Decay Phase 2 single-stop family：事前固定計画

固定日: 2026-09-12 JST
Repo: TR-KJ/time-entry-portfolio-lab
Branch: research/edge-decay-phase2-single-stop-validation
起点: dc27b8a0091ecb829a28c22d0627078134f78275
本計画のみを先にGitHubへコミットし、そのSHAと内容を取得確認した後に実装する。

## 目的と固定前提
対象戦略を単独停止した場合、28戦略Baselineよりポートフォリオの利益が増えるかを検証する。EDGE LOST/DECAY診断の再評価ではない。既存正式分類・閾値・正式構成は変更しない。
Baseline: daily_stop_baseline_trades.csv、28戦略、16,298 trades。
SHA-256: cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。
固定ログの対象戦略名と完全一致する行のみ除外する。Baseline再計算、R再計算、残存取引の変更、リスク再配分を行わない。入力hash不一致は停止する。
EA/VPS/SET/live運用コード・設定は変更しない。

## family・順序の事前固定
1. 22_GA_C_2: EDGE LOST、Recent A/B/2026すべてAvgR負。
2. 18_EA_2_MonWed_Short: EDGE LOST、Recent B/2026回復。
3. 20_EA_1A_MonTue_Short: EDGE DECAY、Recent B/2026負。
4. 23_GA_F_2: EDGE DECAY、Recent B/2026回復。
4候補は過去の独立研究で候補化済みであり、今この時点で同一familyとして固定する。
22→18→20→23の順に実行し、各結果文書・CSVをGitHubへ確定コミットしてSHA確認後に次へ進む。
前の採否にかかわらず後続3候補も同じルールで実施する。今回の実行範囲は22のみ。後続は準備状態に留める。
各比較は E0_BASELINE（28戦略）と E1_MINUS_<戦略番号>（対象1本のみ除外した27戦略）の2構成のみ。結果には完全戦略名も記録する。
各E1は常に原Baselineから独立生成し、前の除外を累積しない。

## 期間と集計方法
既存研究と同じEntryTime JSTで期間所属を決める。開始含む・終了含まず。
- IS: 2015-01-01～2022-01-01
- OOS1: 2022-01-01～2026-01-01
- OOS2: 2026-01-01～2026-09-10
- OOS_COMBINED: 2022-01-01～2026-09-10
- ALL: 2015-01-01～2026-09-10
年別は2022/2023/2024/2025/2026（2026-09-09まで）の5期間。2026は部分年で年率換算しない。
2022–2026は過去研究で閲覧済みで、完全未閲覧holdoutではない。新規の独立確認・統計的有意性・将来利益を主張しない。4つの関連比較を報告し、勝者だけの選択報告をしない。

## 指標の定義
Primary: Delta Total R = E1 Total R - E0 Total R。CSVの元R文字列をDecimalで合計し、表示丸め前の値で判定する。
全期間区分にTrades, TotalR, PF, MaxDDR, WorstDayR, WorstWeekRと全指標のDelta（E1−E0）を表示する。
PF = 正R合計 / 負R合計の絶対値。損失0・利益正ならInfinity、両方0ならNA。非有限PF差はNAとして理由を記録し、TotalR判定を変更しない。
MaxDDRは各期間の取引をCloseTime→EntryTime→StrategyNoの順で並べた累積Rについて、初期資産0を含む最大peak-to-trough幅（非負）。含み損を含まない確定損益ベース。期間ごと0から再計算し、OOS合算DDを部分期間DDの和にしない。
WorstDayRは期間選択後のCloseTime JST日付別R合計の最小。WorstWeekRはCloseTime JSTの月曜～日曜週別R合計の最小。取引がある日・週を対象とし、空の取引集合では0。決済が期間境界を越えてもEntryTimeによる所属は変えない。
MaxDDRのDelta負は改善、WorstDayR/WorstWeekRおよびPFのDelta正は改善。Trades減少自体は採用理由にしない。

## 固定採否ルール
ISで停止効果を確認・報告するが、その結果で候補・順序・期間・指標・ルールを変更しない。
正式採否の最優先はOOS1+OOS2合算Delta Total R。
1. OOS合算Delta Total R <= 0: REJECT（不採用）。
2. OOS合算Delta Total R > 0であっても、以下の両方を満たさなければREJECT（年別安定性不通過）。
   - 対象5期間中、Delta Total R >= 0が3期間以上（ゼロを含む）。
   - max(年別Delta Total R) / OOS合算Delta Total R < 0.70。
     「70%以上を単一年が占めない」を厳密に採用し、70%ちょうどは不通過。分母は正の年だけの合計ではなく、負の年を含むOOS純改善。Decimalで max(yearDelta) < 0.70 * combinedDelta を直接比較する。合算<=0の寄与率はNA。
3. 上記2条件と正のOOS合算Deltaを満たす場合のみ ADOPTION_CANDIDATE（採用候補、実運用採用ではない）。
副次指標PF/DD/WorstDay/WorstWeekの変化と悪化項目を必ず併記し、後付けの数値閾値や裁量条件を追加しない。改善だけでTotalRが減る構成を採用しない。採用候補に通過しても自動的なlive採用はしない。
Money Simulationは採用候補通過時だけ後段研究として可能。不採用は進めない。今回はMoney Simulationを実行しない。

## 禁止事項
複数候補の同時停止、全組み合わせ探索、候補追加削除、期間探索、閾値変更、OOS後の再最適化、22の採否に応じた後続実施の変更を禁止する。
誤実装が発見された場合は計画を変更せず誤りと影響を明示して訂正し、旧結果との履歴を保持する。

## 出力・監査
- docs/42_edge_decay_phase2_single_stop_plan.md（本計画）
- src/research/edge_decay_phase2_single_stop.py
- tests/test_edge_decay_phase2_single_stop.py と独立照合スクリプト
- notebooks/edge_decay_phase2_single_stop_validation.ipynb
- docs/43_edge_decay_phase2_22_result.md
- results/edge_decay_phase2_single_stop/edge_decay_phase2_22_{period_results,yearly_results,decision,run_record}.csv
Colab本文に確定E0/E1/Deltaの5期間と年別2022–2026結果を表示する。実行セルは/contentへCSV出力し、任意Drive保存セルを備える。ローカル実行とColabサーバー実行を区別する。
run record: Baseline hash/件数、Branch、検証日時JST、完全対象戦略名、family/順序、計画SHA、実装SHA、固定期間・判定ルール、CSV名/hash、採否、副次確認、Money Simulation状態を記録する。自己参照する結果コミットSHAは最終報告と次段階への引継ぎで記録する。
テストはゼロ・3/5境界・70%境界・負年を含む寄与率、PFのNA/Infinity、初期損失DD、日/週境界、hash不一致、単独除外、期間加法性、元R合計とDelta=-除外戦略Rの一致を確認する。
22の実データを独立集計して全主要指標・判定を照合し、確定後に18を次対象として記録する。データ未取得時は結果を推定せず未実行を明記する。
