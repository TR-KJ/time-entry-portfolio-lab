# Edge Decay Phase 2 single-stop family：完了・引継ぎ

4候補を事前固定し、22→18→20→23の順に元28戦略Baselineと独立比較した。各結果をGitHubで確定してから次へ進み、候補・期間・指標・判定ルールを変更していない。

| 戦略 | OOS合算Delta Total R | 非負年 | 単一年最大寄与 | 判定 |
|---|---:|---:|---:|---|
| 22_GA_C_2 | +9.362857140 | 5/5 | 34.406469% | 採用候補 |
| 18_EA_2_MonWed_Short | -0.307777785 | 3/5 | NA | 不採用 |
| 20_EA_1A_MonTue_Short | -0.670000000 | 2/5 | NA | 不採用 |
| 23_GA_F_2 | -0.893333329 | 1/5 | NA | 不採用 |

停止効果の候補に残ったのは22だけ。採用候補はlive採用ではなく、後段Money Simulationへ進める資格を意味する。Money Simulationは全候補未実行。18/20/23は進めない。正式構成は28戦略のまま、EA/VPS/SET/live変更なし。
22も全期間Deltaは-30.014285732Rであり、全期間利益の改善ではない。OOS合算Worst Weekは0.301428571R悪化したことも引き継ぐ。

Repo: TR-KJ/time-entry-portfolio-lab
Branch: research/edge-decay-phase2-single-stop-validation
Baseline: 28戦略・16,298 trades、SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359。
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ/EJ1イベント重複修正済み。固定ログ再計算なし。

計画SHA: ead9384028145bb3ac2bf6a093bbfb4b13feb723
共通実装SHA: 8a04ef54021752efc13529417d0e2bdc0644f7f1
22結果SHA: 169a07b9912bf2ba31b3098b267a27275c626d8d
18結果SHA: b3c2ad499125f9eaf1f5442b0aaacb7f072631a9
20結果SHA: e9554e83d3f496c261fabd134e5173c16329ffa8
23結果/本総括SHA: 本ファイル追加コミット。最終報告に記載。

固定ルール：OOS合算Delta Total R>0、年別2022–2026の非負が3/5以上、max年Delta<0.70×OOS純改善の全条件で採用候補。70%等号は不通過。非正合算では寄与率NA。副次PF/DD/Worst Day/Worst Weekで利益減少を救済しない。
IS=2015–2021、OOS1=2022–2025、OOS2=2026–09-09。2022–2026は既閲覧で完全未閲覧holdoutではない。全4候補の独立集計を確認。Colab本文結果はローカル実行、Colabサーバー上では未実行。
複数同時除外・組合せ探索・OOS後最適化は実施していない。既存Edge Decay/Sensitivity正式診断も変更していない。
各戦略の詳細文書はdocs/43,44,45,46、CSVはresults/edge_decay_phase2_single_stop、Colab notebookはnotebooksに保存。
