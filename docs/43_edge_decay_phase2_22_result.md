# Edge Decay Phase 2：22_GA_C_2 確定結果

**E1_MINUS_22はADOPTION_CANDIDATE（採用候補）。live採用・停止指示ではない。**
OOS合算Delta Total Rは+9.362857140R。年別5/5期間で正、最大単一年の寄与は2024年の34.406469%で、事前固定した3/5以上・70%未満を満たした。

## 研究記録
- Repo: TR-KJ/time-entry-portfolio-lab
- Branch: research/edge-decay-phase2-single-stop-validation
- 計画コミット: ead9384028145bb3ac2bf6a093bbfb4b13feb723
- 実装コミット: 8a04ef54021752efc13529417d0e2bdc0644f7f1
- 結果コミット: 本文書・確定CSV・結果本文入りnotebookを追加するコミット。SHAは最終報告に記載。
- 検証日: 2026-09-12 JST（正確な実行時刻はrun record）
- 計画: docs/42_edge_decay_phase2_single_stop_plan.md
- family: 22_GA_C_2 → 18_EA_2_MonWed_Short → 20_EA_1A_MonTue_Short → 23_GA_F_2

Baselineは28戦略・16,298 trades、SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359（実行時一致）。Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。固定ログは再計算せず、完全戦略名22_GA_C_2だけを除外した。既存分類・正式Baseline・EA/VPS/SET/liveコードと設定は変更していない。

計画コミットの親が既存感度研究の結果dc27b8a0091ecb829a28c22d0627078134f78275、追加が計画文書1件のみであることをGitHubで確認し、計画をSHA指定で取得してから実装した。実装コミットをGitHubへ固定した後に実データを集計した。

## 採否と解釈
OOS利益正、非負年3/5以上、max年別Delta < 0.70×OOS純改善のすべてを通過。判定は元CSVのRをDecimalで合計し、表示丸め前で実施。
- IS Delta: -39.377142872R。過去ISでは22を外すと利益を失う。ISで候補やルールは変更していない。
- OOS1 Delta: +7.079999996R。
- OOS2 Delta: +2.282857144R。
- OOS合算Delta: +9.362857140R。
- 全期間Delta: -30.014285732R。全期間利益を改善したとは結論しない。
- OOS PF: 1.432989 → 1.460505（改善）。
- OOS MaxDD R: 22.196976 → 21.641262（0.555714R改善）。
- OOS Worst Day R: -10.880000 → -10.880000（不変）。
- OOS Worst Week R: -12.824402 → -13.125830（0.301429R悪化）。副次悪化を隠さず、事前ルールに後付け条件を追加しない。

年別Deltaは2022 +2.277142856、2023 +0.034285713、2024 +3.221428570、2025 +1.547142857、2026 +2.282857144R。2023の改善幅はごく小さいが、固定ルール上は正として数える。
2026は9月9日までの部分年で、年率換算しない。2022–2026は過去研究で閲覧済みで完全未閲覧holdoutではない。停止の将来改善、エッジ消失の証明、統計的有意性は主張しない。診断研究とは目的が異なり、採用候補は後段検証への資格に留まる。
Money Simulationは実施していない。22は後段研究へ進める資格あり。liveは28戦略のまま。

## 5期間 E0/E1/Delta
IS=2015–2021、OOS1=2022–2025、OOS2=2026–09-09。EntryTime JSTで所属、DDはCloseTime→EntryTime→StrategyNo順の確定損益、日/週はCloseTime JST（日曜終了週）で集計。Deltaは全列E1−E0、MaxDDRは負が改善。表示は6桁、確定CSVはDecimal値を保持する。

|Period|Candidate|Trades|TotalR|PF|MaxDDR|WorstDayR|WorstWeekR|
|---|---|---|---|---|---|---|---|
|IS|E0_BASELINE|9756|768.488273|1.372171|27.540956|-12.000000|-14.455836|
|IS|E1_MINUS_22|9482|729.111131|1.368966|29.211511|-12.000000|-14.455836|
|IS|DELTA_E1_MINUS_E0|-274|-39.377143|-0.003205|1.670556|0.000000|0.000000|
|OOS1|E0_BASELINE|5547|601.960585|1.489975|22.196976|-10.880000|-12.824402|
|OOS1|E1_MINUS_22|5389|609.040585|1.519314|21.641262|-10.880000|-13.125830|
|OOS1|DELTA_E1_MINUS_E0|-158|7.080000|0.029339|-0.555714|0.000000|-0.301429|
|OOS2|E0_BASELINE|995|19.818791|1.095529|18.954206|-4.579584|-5.397048|
|OOS2|E1_MINUS_22|966|22.101648|1.111758|14.122778|-4.579584|-5.288938|
|OOS2|DELTA_E1_MINUS_E0|-29|2.282857|0.016229|-4.831429|0.000000|0.108110|
|OOS_COMBINED|E0_BASELINE|6542|621.779376|1.432989|22.196976|-10.880000|-12.824402|
|OOS_COMBINED|E1_MINUS_22|6355|631.142233|1.460505|21.641262|-10.880000|-13.125830|
|OOS_COMBINED|DELTA_E1_MINUS_E0|-187|9.362857|0.027516|-0.555714|0.000000|-0.301429|
|ALL|E0_BASELINE|16298|1390.267649|1.397117|27.540956|-12.000000|-14.455836|
|ALL|E1_MINUS_22|15837|1360.253364|1.406454|29.211511|-12.000000|-14.455836|
|ALL|DELTA_E1_MINUS_E0|-461|-30.014286|0.009337|1.670556|0.000000|0.000000|

## 年別2022–2026 E0/E1/Delta

|Period|Candidate|Trades|TotalR|PF|MaxDDR|WorstDayR|WorstWeekR|
|---|---|---|---|---|---|---|---|
|2022|E0_BASELINE|1383|163.991920|1.460197|13.239666|-7.928654|-8.382382|
|2022|E1_MINUS_22|1344|166.269063|1.489374|12.292269|-7.928654|-8.926668|
|2022|DELTA_E1_MINUS_E0|-39|2.277143|0.029177|-0.947397|0.000000|-0.544286|
|2023|E0_BASELINE|1384|160.985032|1.537135|22.196976|-10.880000|-12.824402|
|2023|E1_MINUS_22|1344|161.019317|1.563911|21.641262|-10.880000|-13.125830|
|2023|DELTA_E1_MINUS_E0|-40|0.034286|0.026775|-0.555714|0.000000|-0.301429|
|2024|E0_BASELINE|1394|129.794238|1.471284|12.974713|-3.693846|-6.500296|
|2024|E1_MINUS_22|1354|133.015667|1.506482|11.927570|-3.693846|-6.453153|
|2024|DELTA_E1_MINUS_E0|-40|3.221429|0.035197|-1.047143|0.000000|0.047143|
|2025|E0_BASELINE|1386|147.189395|1.495443|17.273406|-4.386703|-7.080358|
|2025|E1_MINUS_22|1347|148.736537|1.522151|16.014834|-4.386703|-6.911786|
|2025|DELTA_E1_MINUS_E0|-39|1.547143|0.026708|-1.258571|0.000000|0.168571|
|2026|E0_BASELINE|995|19.818791|1.095529|18.954206|-4.579584|-5.397048|
|2026|E1_MINUS_22|966|22.101648|1.111758|14.122778|-4.579584|-5.288938|
|2026|DELTA_E1_MINUS_E0|-29|2.282857|0.016229|-4.831429|0.000000|0.108110|

## 検証
- 12件の単体テスト合格：0、3/5、70%等号と両側、負年を含む分母、初期損失DD、日/週境界、期間所属、単独除外、PF特殊値、hash不一致、前段階記録必須、5年集合を確認。
- 正式モジュールをimportしないpandas/numpy独立集計で30行×7指標=210値を照合。TotalRはDecimal完全一致、他指標はatol=rtol=1e-10で一致。
- Delta TotalR=-除外戦略R、IS+OOS1+OOS2=ALL、年別合計=OOS合算、採否・CSV hashも確認。
- notebookの全コードセル構文・構造、内蔵研究コード一致、アップロード済み入力からの分析セルのローカル再実行と3分析CSVのバイト一致を確認。ローカル環境にIPythonがないため表示部分だけテキスト表示に置換した。run recordは時刻差を許容する。
- ローカルPythonで実行。Colabサーバー上では未実行。本文に確定結果、実行セルに/content CSV出力、任意Drive保存を用意。

## 次：18への引継ぎ
22の結果コミットSHAをGitHubで確認してから18へ進める準備済み。今回は18/20/23未実行。22の通過を理由に候補や基準を変えず、18→20→23はそれぞれ元28戦略Baselineから独立評価する。採否にかかわらず順次実施し、各結果を確定してから次へ進む。
後続CLIは同じ実装・計画SHAを使い、直前戦略のrun recordとGitHub確定結果SHAを必須とする。CLI自体はオフラインのためSHAの存在を問い合わせない。実行者は渡すSHAでそのrun recordと結果CSVが公開・確定されていることをGitHubで確認する。

```sh
python src/research/edge_decay_phase2_single_stop.py --baseline /path/to/daily_stop_baseline_trades.csv --strategy 18_EA_2_MonWed_Short --implementation-commit 8a04ef54021752efc13529417d0e2bdc0644f7f1 --predecessor-record results/edge_decay_phase2_single_stop/edge_decay_phase2_22_run_record.csv --predecessor-result-sha <22_RESULT_COMMIT_SHA> --output-dir /content
```

18の実行前に出力先を確認し、18の結果文書・CSVを別コミットとして固定する。18を通過/不通過どちらでも20、その後23へ進める。

## 作成ファイル
- docs/42_edge_decay_phase2_single_stop_plan.md
- docs/43_edge_decay_phase2_22_result.md
- src/research/edge_decay_phase2_single_stop.py
- tests/test_edge_decay_phase2_single_stop.py
- tests/verify_edge_decay_phase2_single_stop.py
- notebooks/edge_decay_phase2_single_stop_validation.ipynb
- results/edge_decay_phase2_single_stop/edge_decay_phase2_22_period_results.csv
- results/edge_decay_phase2_single_stop/edge_decay_phase2_22_yearly_results.csv
- results/edge_decay_phase2_single_stop/edge_decay_phase2_22_decision.csv
- results/edge_decay_phase2_single_stop/edge_decay_phase2_22_run_record.csv
