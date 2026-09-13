# JPY Regime Dependency Phase 1 — Result

状態: 実データ実行・独立照合完了。EA/VPS/SET/live変更なし。
Branch: research/jpy-regime-dependency-phase1
計画SHA: 11541f39730fcbae7dd7dfb5fc82c95bf7c18652
実装SHA: a57735bf817281bc953107a2e05edd616367686a
結果SHA: この文書を追加したGitコミット（自己参照を避け、最終報告で記載）。

## 結論
Primary・200MA Robustnessとも、事前固定した円安レジーム依存仮説を支持しない。円安期だけ利益があったという群全体の仮説とは整合しない。円高時に利益が失われるという結果でもない。これは依存が存在しないことの証明や将来の保証ではない。
Long pooled AvgR: Primary 円安 +0.094361 / 円高 +0.098400、差 −0.004040 R/trade。等重み差 −0.026011。正差5/10で過半数未満。
Robustness 円安 +0.075584 / 円高 +0.119854、差 −0.044271。等重み差 −0.043047。十分標本で正差2/9。
群全体のPhase 2 Edge Risk Threshold Studyへ進む事前条件を満たさない。今回、閾値探索へは進まない。個別の差は記述に留める。

## 日次仕様とcoverage
監査済みUSDJPY M1の指定8本のみ。Europe/Helsinki→Asia/Tokyo。実データが存在するJST暦日の最後のM1 Close。土曜早朝も1日。翌00:00から利用可、当日entryに当日終値は使わない。126日方式は127 closes、MA200と20日傾きは220 closesが必要。日次3,648行（2015-01-02〜2026-09-09）。末尾の9/9は同日のtradeに使用しない。
Baseline SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359、一致。28戦略16,298件は再計算なし。対象Long 6,333件、Short 3,087件。
| 群・方式 | 円安 | 円高 | Neutral | 履歴不足 |
|---|---:|---:|---:|---:|
| Long Primary | 3319 | 2797 | 0 | 217 |
| Long Robustness | 2619 | 2047 | 1281 | 386 |
| Short Primary | 1640 | 1340 | 0 | 107 |
| Short Robustness | 1267 | 977 | 660 | 183 |
履歴有効coverage: Long Primary 96.57%、Robustness 93.91%。Short Primary 96.53%、Robustness 94.07%。Neutralを円安円高へ再配分していない。

## Long 10戦略
差は円安−円高 AvgR。Robustnessの16は両セル20件条件を満たさず、等重み・過半数から除外。
| 戦略 | Primary差 | Robustness差 | Robustness主要根拠 |
|---|---:|---:|---|
| 1_EJ_Log1 | +0.009435 | -0.138117 | 対象 |
| 2_EJ_NightBlitz_20 | +0.020071 | -0.068612 | 対象 |
| 3_EJ_NightBlitz_21 | +0.011463 | -0.028117 | 対象 |
| 4_GJ_Port_Log1 | +0.029503 | +0.025242 | 対象 |
| 6_GJ_Old_Mon | -0.075879 | +0.052336 | 対象 |
| 7_GJ_Mon_Blitz | -0.041932 | -0.071052 | 対象 |
| 8_AJ_Core1 | -0.029206 | -0.044903 | 対象 |
| 13_UJ_Fix_MidWeek | +0.017493 | -0.007819 | 対象 |
| 16_UJ_T10A | -0.194631 | +0.072469 | LOW_SAMPLE・除外 |
| 26_AJ_China_Demand | -0.006430 | -0.106380 | 対象 |

8_AJ_Core1は両方式で円高時のAvgRが相対的に高い。4_GJ_Port_Log1は両方式で正差だが、これだけで群全体の判定を置き換えない。
各セルのTrades/TotalR/AvgR/PF/WinRate/AvgWinR/AvgLossRおよびLOW_SAMPLEはstrategy CSVに全件保存。

## Short control
Primary pooled差 +0.007458、等重み差 −0.028369で混在。十分標本7戦略中5戦略は円安側が高い。
Robustness pooled差 +0.020514、等重み差 +0.030203、十分標本6戦略中5戦略が円安側で高い。想定した『Shortは円高側で相対的に強い』という一貫した結果ではない。
decision CSVのShort Support列はLongと同じ正差条件を適用した記述値で、Shortの経済的整合性やPrimary仮説支持を意味しない。ControlOnly=True。

## 補助期間・限界
Historical 2015-2021 / RecentA 2022-2023 / RecentB 2024-2025 / Monitor2026を変更せず保存。2022-2026は既閲覧で完全未閲覧holdoutではない。
2026 Robustnessの円高セルはLong/Shortとも0件で比較不能。期間の不足セルはLOW_SAMPLE。群結論はFULLのみ。
共通市場日や同時取引による相関があり、この方向性判定を統計的有意性とは呼ばない。USDJPYは円と米ドル双方の影響を含み、円単独の因果効果を識別しない。

## 検証と成果物
7境界条件テストPASS。全日次の126 index/200MA/20 slopeを独立Decimal計算で一致確認。全対象tradeのno-lookahead、個別・pooled・等重み集計、支持判定を独立照合。代表4日をmanual_audit CSVに保存。
results/jpy_regime_phase1/: strategy_primary.csv、strategy_robustness.csv、group_summary.csv、period_summary.csv、coverage.csv、decision.csv、run_record.csv、verification.csv、manual_audit.csv、regime_assignments_audit_light.csv（全てjpy_regime_phase1_接頭辞）。
完全assignment audit（9,420件）とdaily audit（3,648日）は実行時に/contentへ保存。GitHubには先頭・末尾各戦略の34件auditのみ保存。完全版hashはrun_recordに記録。
notebooks/jpy_regime_phase1.ipynbは実装SHAに固定して取得し、主要結果を本文表示。Drive保存は初期OFF。
