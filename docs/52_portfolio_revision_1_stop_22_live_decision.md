# Portfolio Revision #1：22_GA_C_2 live停止の運用決定（2026-09-14週）

## 決定と適用状態

| 項目 | 記録 |
|---|---|
| Decision ID | Portfolio Revision #1 / STOP-22-2026-09-14 |
| Decision date | 2026-09-13（JST） |
| Effective live week | 2026-09-14（月）の週から（JST） |
| 意思決定者 | 運用者（ユーザー）の明示指示 |
| Decision status | DECIDED / PRE_IMPLEMENTATION_RECORD（決定済み・実装前記録） |
| Live application status | PENDING_VERIFICATION（本記録では適用・停止を未確認） |
| Live change | `22_GA_C_2` をlive portfolioで停止し、正式運用構成を28戦略から27戦略へ変更する意思決定 |
| 継続戦略 | `20_EA_1A_MonTue_Short` は継続。22以外の27戦略を維持 |
| 記録branch | `operations/stop-22-ga-c2-2026-09-14` |

**これは実装前の意思決定記録であり、実際のlive停止完了を報告する文書ではない。** 今回のGitHub作業は本書の追加のみとし、EA/VPS/SET/liveコード・設定を変更しない。実際の適用日時・操作・確認証跡は、適用後に別途記録する。

22＋20同時除外は未検証の組み合わせであり採用しない。個別除外の改善を組み合わせの改善と解釈しない。

## 根拠と反対材料

以下は既存の確定研究結果に基づく。研究の分類・採否・評価基準を今回変更したり、再計算したりしない。

1. [Edge Decay正式診断](39_edge_decay_final_result.md)：22は **EDGE LOST**。Recent A/BともAvg Rが負で、2026も負だった。ただし診断分類そのものはエッジ消失の永久的証明ではない。
2. [Sensitivity確定結果](41_edge_decay_sensitivity_final_result.md)：22はユニーク設定 **7/7** で警告側（全設定EDGE LOST）に残った。指定された閾値範囲内で頑健であり、未検証の期間・設定へ一般化しない。
3. [Phase 2 single-stop・22確定結果](43_edge_decay_phase2_22_result.md)：OOS合算 Delta Total R **+9.362857140R**、非負年 **5/5**（すべて正）、単一年最大寄与 **34.406469%**（2024年）で **ADOPTION_CANDIDATE**。一方、OOS Worst Week Rは約0.301429R悪化しており、全指標が改善したわけではない。
4. [2015年継続Money確定結果](49_edge_decay_phase2_money_simulation_result.md)：22除外は **REJECT（不採用）**。ALL Delta Total R **-30.014285732R**、4 Riskすべてで最終資産・継続OOS純利益が減少した。過去に22が資金形成へ寄与した事実と、この反対材料を保持する。
5. [2026 Deployment Reset確定結果](51_deployment_reset_2026_result.md)：22除外は **0.25 / 1.0 / 1.5 / 2.0%の4 RiskすべてでFinal Capital改善**。代表1.5%では623,594.14円から646,281.23円へ **+22,687.09円**、MaxDDは25.500831%から20.115026%へ **約5.385805ポイント改善**。2026-01-01に各構成の資金とDDピークを500,000円へResetした比較であり、2015年からの継続Moneyとは評価期間・開始資金が異なる。
6. **2026は既閲覧で、完全未閲覧holdoutではない。** Phase 2のOOSという期間名も完全未閲覧を意味せず、2022–2026は過去研究で参照済み。2026は9月9日までの途中年であり、今回の材料は未来の成績や停止効果を保証しない。

20については、[Phase 2・20確定結果](45_edge_decay_phase2_20_result.md)でOOS合算Delta Total R -0.670000000R・非負年2/5により不採用だった。Deployment Resetでは候補となったが結果は混在している。今回の決定対象は22単独とし、20は継続する。

## 判断の位置づけ

本決定は、**「現時点で得られた情報に基づくPortfolio Revision」**である。近年の診断、単独停止比較、2026の同額Reset比較を運用者が総合し、2026-09-14週から22を停止すると決定した。Shadow Forwardの追加結果を待つことを今回の適用前提とはしない。Shadow Forward完了・未来データでの確認済みを意味するものではない。

22のエッジ消失を永久に証明したものではなく、**永久停止ではない**。将来の再評価・再採用を妨げない。再採用等の判断を行う場合は、その時点の情報・根拠・決定日・適用日を別の運用決定として記録する。本書では新しい自動再採用条件や閾値を設定しない。

既存研究文書の「正式28戦略を維持」「live変更なし」は各研究完了時点の事実として保持する。本書はそれらを改稿せず、後続の運用意思決定として追加する。正式構成の変更決定と実環境への適用確認を区別する。

## 固定データと参照履歴

- Repository: `TR-KJ/time-entry-portfolio-lab`
- 起点branch: `research/deployment-reset-2026-validation`
- 起点commit: `d61848b589036e9ab045db0e063392b4666459c8`
- 起点選択理由：Edge Decay、Sensitivity、Phase 2 single-stop、継続Money、Deployment Resetの確定文書・結果が揃い、docsの続番が51まで存在するため。研究branchを変更せず、そこから運用決定専用branchを作成する。
- Baseline: `daily_stop_baseline_trades.csv`、28戦略・16,298 trades
- Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`
- 研究Baseline条件：Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。
- このhashは既存研究が実行時に一致を確認した固定入力の識別子。本作業でBaselineを再計算・再構築・再hash検証したとは扱わない。
- 関連計画：[Edge Decay](38_edge_decay_validation_plan.md)、[Sensitivity](40_edge_decay_sensitivity_validation_plan.md)、[Phase 2 single-stop](42_edge_decay_phase2_single_stop_plan.md)、[継続Money](48_edge_decay_phase2_money_simulation_plan.md)、[Deployment Reset](50_deployment_reset_2026_plan.md)。
- Moneyは理論・lot上限なし。代表1.5%は研究値、0.25%はlive検証参照値であり、本決定によるlive Risk変更ではない。実運用制約付き比較は `NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS` のまま。

## live適用後の別記録

現時点では **PENDING_VERIFICATION**。以下は未記入の確認様式であり、実施済みの証跡ではない。

適用後にdocsの次の空き続番で独立した確認文書を追加し、本書への相対リンクと本決定commit SHAを記載する。本書の決定時点の内容は保持し、事後の状態を遡って「確認済み」に書き換えない。

| 確認項目 | 適用後に記録する内容 |
|---|---|
| 決定との対応 | Decision ID、本書への相対リンク、決定commit SHA |
| 適用日時・実施者 | 実際の日時（JST）、実施者 |
| 対象環境 | 確認対象のEA/VPS/SETを識別できる情報（秘密情報は含めない） |
| 22停止の設定確認 | 実際に22が無効化されていること、確認日時、設定・画面等の証跡参照 |
| 27戦略・20継続の確認 | 22以外が維持され、20が有効であることの証跡 |
| 適用後の動作確認 | 観測期間、ログ等の参照、22の新規エントリーが停止していることの確認結果 |
| 未確認・例外 | 取引機会未到来等の未確認事項、想定との差異、必要な対応 |
| 最終確認状態 | VERIFIED / PARTIAL / FAILED等と、その根拠 |

取引が発生していない事実だけで停止設定を証明せず、設定確認と観測された動作を分けて記録する。今回の文書追加は、その後続確認やlive操作を実施したことを意味しない。
