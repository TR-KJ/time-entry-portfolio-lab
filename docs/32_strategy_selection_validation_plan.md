# Strategy Selection / Portfolio Pruning 検証計画

Status: FROZEN — 実装・集計・OOS開封前

検証ルール固定日: 2026-09-11 JST

使用ブランチ: `research/strategy-selection-validation`

## 1. 目的と非目的

本検証の目的は、現在の28戦略の中に、停止することでポートフォリオに残る利益（Total R）が増える戦略があるかを確認することである。

戦略数を減らすこと自体、見た目を単純化すること、PFまたはDDだけを改善することは目的としない。利益額の増加を最優先とし、戦略除外が再現性のある改善を示さない場合は28戦略のBaselineを維持する。

## 2. 固定Baselineと母集団

Daily Stop検証で固定したBaseline Trade Logだけを母集団として使用する。

- 戦略数: 28
- Trades: 16,298
- SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`
- Daily Stop: なし
- ATR: OFF
- Event filter: Candidate C
- UJ12前倒しゴトウビ修正: 反映済み
- EJ1イベント重複修正: 反映済み

Baseline Trade Logは再計算しない。M1データからのバックテスト再実行、約定結果の再生成、決済条件の変更は行わず、固定ログから対象戦略の行を除外するシミュレーションだけを行う。Baselineと各候補の差は、同一母集団に対する除外だけで生じなければならない。

## 3. 検証期間と開封順序

期間区分はDaily Stop検証から変更しない。

- IS: 2015-01-01から2021-12-31
- OOS1: 2022-01-01から2025-12-31
- OOS2: 2026-01-01から2026-09-09（両端を含む）

停止候補の判定ルール、順位、Candidate portfolioおよび閾値はISだけで決定・固定する。OOS1を確認した後に、候補の追加・削除・入替え、閾値変更、グループ追加、追加探索をしてはならない。OOS2は最終holdoutとし、すべての候補と判定ルールを固定した後、最後に一度だけ確認する。

OOS1またはOOS2を誤って先に集計・閲覧した場合は、その事実を記録し、未開封OOSとして扱わない。

## 4. 検証単位

### 4.1 単体健康診断

最初に28戦略を個別に集計する。単体成績は候補抽出の材料であり、それだけで停止を決定しない。

### 4.2 Leave-One-Out

次に、Baselineから1戦略だけを除外した28通りをISで集計する。各結果は同じBaselineと比較する。

Total Rは戦略別Rの単純合計であるため、ある戦略の除外によるDelta Total Rは、その戦略の単体Total Rの符号を反転した値と一致しなければならない。この一致を検算に使う。DD、Worst Day、Worst WeekおよびPFはポートフォリオ時系列から再集計するため、単体値だけからは判断しない。

### 4.3 探索禁止

28戦略の全組み合わせ探索、総当たり、遺伝的探索、ランダム探索、OOSを含むランキングは行わない。

## 5. 事前定義グループ仮説

`TP < SL` は停止条件ではなく、検証前に定めた構造仮説の一つとする。設定上のTP/SL比だけで期待値は決まらず、時間決済もあるため、該当しただけでは停止しない。

検証可能なグループは次に限定する。

- 設定上 `TP < SL` の戦略群
- TPなしの戦略群
- JPY関連戦略群
- AUD関連戦略群
- Long戦略群
- Short戦略群
- overnight戦略群
- China Demand戦略群

各戦略の所属は、固定Baselineに対応する既存の戦略定義・設定値・タグから機械的に決める。重複所属を許す。成績を見て所属を変更してはならず、初回集計前に戦略名と所属を `results/strategy_selection/strategy_selection_group_membership.csv` へ固定する。上記以外のグループ、後付けの名称、任意の通貨ペア集合は今回検証しない。

## 6. 指標

最優先の主指標は `Total R` とする。

単体健康診断、Baseline、グループおよびCandidate portfolioでは、少なくとも次を併記する。

- Trades
- Total R
- PF
- Win Rate
- Avg R / trade
- Avg Win R
- Avg Loss R
- Max DD R
- Worst Day R（JST日単位）
- Worst Week R（JST、月曜開始）
- 年別Total R
- positive years / negative years（Total Rが0の年はneutral）
- max losing streak
- exit reason率（TP / SL / time / その他。固定ログ上の決済理由に従う）

Leave-One-Outでは、Baseline比として少なくとも次を表示する。

- Delta Total R
- Delta Max DD R
- Delta PF
- Delta Worst Day R
- Delta Worst Week R

Deltaは原則 `candidate - Baseline` とする。Max DD Rは損失深度を正の絶対値で表し、Delta Max DD Rが負なら改善である。Worst Day RとWorst Week Rは負値で表し、Deltaが正なら改善である。符号規約は全CSVで統一する。

## 7. 個別停止候補ルール

個別戦略がISで次の両方を満たす場合に限り、「明確な負の限界貢献候補」とする。

1. 単体Total Rが0未満
2. Leave-One-OutのDelta Total Rが0より大きい

これは同じ算術条件の相互検算でもある。候補はDelta Total Rの降順、同値の場合は戦略IDの昇順で順位を固定する。

「安定して負の限界貢献」と呼ぶには、上記に加えてISの7暦年のうちnegative yearsがpositive yearsを上回ることを必要とする。年ごとの符号が混在する戦略を、直近だけ・特定年だけを理由に除外しない。

単体で弱い、PFが低い、勝率が低い、または `TP < SL` であることだけでは停止候補にしない。単体Total Rがプラスの戦略は、除外するとTotal Rが減るため利益目的の個別停止候補にしない。DD等の分散効果がある場合は維持判断をさらに補強する。単体Total Rがマイナスでも、OOSで利益増加が再現しなければ採用しない。

## 8. Candidate portfolioの固定

IS集計後、OOS開封前に次のCandidate portfolioだけを固定する。該当候補が存在しない枠は作らない。

- `P0_BASELINE`: 28戦略、除外なし
- `P1_MINUS_TOP1`: 明確な負の限界貢献候補の第1位を1戦略だけ除外
- `P2_MINUS_STABLE_TOP2`: 安定して負の限界貢献を満たす上位2戦略を除外
- `P3_MINUS_GROUP`: 事前定義グループのうち、ISでグループ合計Total Rが最も小さく、かつそのグループ除外でDelta Total Rが正となる1グループだけを除外
- `P4_PAIR_CHECK`: Leave-One-Outで明確な負の限界貢献候補となった上位2戦略の同時除外。これは `P2` と同一なら別候補を作らない

最大でもBaselineを含む5候補とする。候補ID、除外戦略、選定根拠、IS値を `results/strategy_selection/strategy_selection_candidates_frozen.csv` に記録し、そのファイルをOOS実行前にコミットする。

候補枠を埋めるために条件を緩めない。ISで利益改善候補がなければBaselineだけで終了し、「除外候補なし」と結論する。

## 9. 組み合わせ効果の制限

組み合わせ効果の確認は、Leave-One-Outで明確な負の限界貢献候補となった上位2戦略の同時除外だけに限定する。3戦略以上の組み合わせ、順位外候補との組み合わせ、全組み合わせ探索は禁止する。

グループ候補と個別候補を組み合わせた追加ポートフォリオも作らない。

## 10. OOS評価とMoney Simulation

固定した全Candidate portfolioを同じ条件でOOS1に一度だけ適用し、その後OOS2を一度だけ確認する。OOS結果を見てCandidate portfolioを作り直さない。

Money Simulationへ進めるのは、OOS1およびOOS2の確認後に残った最終候補だけとする。方式は次の2つに限定する。

- Weekly Fixed Risk
- Weekly Compound

最終判断では、Baselineに対する利益額の増加を第一条件とする。Max DD、Worst Day、Worst Week等の改善は副次評価である。利益額がBaselineより減る候補は、DDが改善しても採用しない。結果が小さい、期間間で不安定、またはOOSで再現しない場合はBaselineを維持する。

## 11. GBPAUD 2019既知欠損

GBPAUD 2019の既知欠損はDaily Stop検証と同じ扱いとする。

- 欠損を補完しない
- 新しい除外日を設定しない
- 固定Baseline Trade Logをそのまま使用する
- 欠損を理由に特定戦略の結果だけを補正しない

## 12. 再現性と出力記録

すべての結果に、少なくとも次を記録する。

- Baseline Trade Log SHA-256
- 使用ブランチ
- 検証実行日時（JST）
- 検証期間
- 出力CSV名
- 候補・順位・同値処理を含む判定ルール
- 使用したスクリプトのパスとコミットSHA（実装後）
- グループ所属表のファイル名
- OOS開封前に候補を固定したコミットSHA

予定する出力CSV名は次のとおりとする。

- `results/strategy_selection/strategy_selection_group_membership.csv`
- `results/strategy_selection/strategy_selection_health_is.csv`
- `results/strategy_selection/strategy_selection_leave_one_out_is.csv`
- `results/strategy_selection/strategy_selection_group_hypotheses_is.csv`
- `results/strategy_selection/strategy_selection_candidates_frozen.csv`
- `results/strategy_selection/strategy_selection_oos_results.csv`
- `results/strategy_selection/strategy_selection_money_simulation.csv`
- `results/strategy_selection/strategy_selection_final_decision.csv`

実装上やむを得ず名前を変更する場合は、OOS開封前に本書を更新し理由を記録する。OOS開封後の変更は禁止する。

## 13. 採否と運用コード

研究完了時は、各候補および検証全体について `ADOPT` または `REJECT` を明示し、Baselineを維持する場合も明記する。

戦略除外をEAへ反映するかは、IS・OOS1・OOS2・Money Simulationの完了後に別途判断する。本計画書の作成および今後の研究コード実装は、EA、VPS、SET、live運用コードまたは稼働設定を変更する許可を意味しない。

本計画書を固定するコミットでは研究ルール文書と参照リンクだけを変更し、検証コードは作成しない。
