# China Demand 4戦略一括停止：事前固定検証計画

計画登録日: 2026-09-12 JST
対象: TR-KJ/time-entry-portfolio-lab
使用Branch: research/china-demand-group-validation
起点: research/daily-stop-validation / 8bc5f65d1eb8219c1b2010e4674f6c8220fb68e4
状態: 分析コード作成・C0/C1計算より前に本計画をコミットする。

## 仮説と固定候補
China Demandという事前定義された共通ロジック群の一括停止がTotal Rを増やすかを検証する。成績を見て選んだ4戦略ではなく、利用者が指定したグループ仮説である。
- C0_BASELINE: 28戦略すべて、除外なし。
- C1_MINUS_CHINA4: 25_AU_China_Demand, 26_AJ_China_Demand, 27_EA_China_Demand, 28_GA_China_Demandを戦略名の完全一致で一括除外した24戦略。

ISを見ても候補・構成・閾値・除外数は変更しない。OOS後の再最適化、追加候補探索、全組み合わせ探索、China4の一部だけ除外、別グループ追加は禁止。

## 入力固定
Baseline Trade Log: daily_stop_baseline_trades.csv
SHA-256: cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
28戦略 / 16,298 trades / Daily Stopなし / ATR OFF / Event Candidate C / UJ12前倒しゴトウビ修正済み / EJ1イベント重複修正済み。
Drive保存元: time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/
固定ログは再計算しない。既存Rを使用し、残存トレードの値・順序規則を変えず抽出する。hash不一致、行数・戦略名・期間・数値不整合なら停止。追加日付除外・欠損補完なし。

## 期間・集計定義
JSTのEntryTime基準で、IS 2015-01-01～2021-12-31、OOS1 2022-01-01～2025-12-31、OOS2 2026-01-01～2026-09-09（翌日00:00未満）。
IS、OOS1、OOS2の順で同じ固定候補を計算し、OOS合算と固定ログ全期間も表示。
年別は2015～2026、特に2022、2023、2024、2025、2026を個別表示。2026は途中年である。
Total Rは既存Rの合計。PFは正R合計/負R絶対値合計（損失ゼロなら未定義）。
MaxDDはCloseTime, EntryTime, StrategyNo順、初期累積R=0からの最大下落幅（正値）。Worst Day/WeekはCloseTime JST、週は月曜～日曜。期間に属するトレードの決済まで含める。既存研究と同じ定義を使う。
Deltaは常にC1-C0。MaxDDの負Deltaは改善、Worst Day/Weekの正Deltaは改善。
判定には丸め前のTotal R差を使用し、表示は小数6桁。合算PF/DDは期間指標の足し算でなく該当トレード全体から再集計。

## 事前判定ルール
Primary metricはDelta Total R。利益増加を最優先し、PF/MaxDD/Worst Day/Worst Weekは副次。
OOS1+OOS2合算Delta Total R <= 0ならC1不採用で研究終了、28戦略維持、Money Simulationへ進めない。
>0でも自動採用せず年別安定性とリスク指標を確認し、必要なら最終候補だけMoney Simulationへ進む。数値閾値を事後追加しない。正の場合の定性的判断と根拠は明記する。

## 検証上の位置付け
Strategy Selectionとは独立した仮説であり、その確定結果を書き換えない。ただし同じ歴史データとOOS期間は既存研究ですでに参照されている。今回の候補は計算前固定だが、OOSを完全未閲覧の新しい独立ホールドアウトとは主張しない。
各28戦略のエッジ消失/優位性低下検証は別研究であり今回は実装・探索しない。
EA/VPS/SET/live運用コード・稼働設定は変更しない。

## 出力・検証
Colab本文表示と/content CSVの2系統。任意のDrive保存セルも用意。
確定CSV保存先: results/china_demand_group/
- china_demand_group_period_results.csv
- china_demand_group_yearly_results.csv
- china_demand_group_final_decision.csv
- china_demand_group_run_record.csv
計画: docs/36_china_demand_group_validation_plan.md
最終結果: docs/37_china_demand_group_final_result.md
実装: src/research/china_demand_group_analysis.py
Colab: notebooks/china_demand_group_validation.ipynb
最終文書にBaseline hash、Branch、計画コミット、実行日、CSV名とhash、判定ルール、採否、実行環境と検証結果を記録。
入力hash、C0既存集計一致、C1=Baselineから指定4戦略のみ除外、各期間/年合算整合、Delta Total R=-除外4戦略合計Rを確認する。境界日時、DD初期損失、週集計、判定のゼロ境界も検証。
