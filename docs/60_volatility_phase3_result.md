# Volatility Environment Phase 3 — Risk Allocation Economic Value：結果

## 結論

**R1_MILD / R2_MODERATEはEconomic Value Candidate。両方ともRobustness-consistent。F1_Q1_OFFはNOT_CANDIDATE。**
PrimaryではR1/R2ともALL最終資金がR0を上回り、4期間Resetすべてで改善し、MaxDD安全柵を通過した。
固定候補内ではR2の最終資金が最大。R1はR2よりPrimary MaxDDとWorst Dayが小さい。
DD改善だけで利益減少を救済しない事前ルールによりF1は不採用候補。F1の2026だけの改善でも全期間利益の減少を救済しない。

これは2015〜2026閲覧済みデータを用いたretrospective economic-impact analysisで、新規OOS・将来利益の証明ではない。
50万円から2015年以降の週次複利・lot無制限による理論値であり、巨額のFinal Capitalを実口座で実現可能な金額と解釈しない。
実運用の流動性・lot上限・historical broker条件は再現していない。EA/VPS/SET/liveは変更せず、live採用なし。
22_GA_C_2を含む固定28戦略で比較。2026-09-14週の22停止live判断を遡及変更しない。

## GitHub固定記録

Branch: research/volatility-environment-phase3-risk-allocation
- Phase 2基点: 0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc
- Plan SHA: a7f55489a36ebe353f74e4571222ae16ae0615cd
- Implementation SHA: ddbf4611053bb4cbdf2112e8bedb18461a357d01
- 結果SHA: この文書・CSV・Notebookを含む結果commit（自己参照回避のため最終報告に記載）。
Plan-onlyの差分とremote本文一致を確認後にコードを作成。実装remote ref確認後に初回実データ計算。
結果後のRisk配分・cut・strategy・候補・期間・判定ルールの変更なし。

## 固定候補

| 候補 | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---:|---:|---:|---:|---:|
| R0_FIXED_090 | 0.90% | 0.90% | 0.90% | 0.90% | 0.90% |
| R1_MILD | 0.70% | 0.80% | 0.90% | 1.00% | 1.10% |
| R2_MODERATE | 0.50% | 0.70% | 0.90% | 1.10% | 1.30% |
| F1_Q1_OFF | 未取引 | 0.90% | 0.90% | 0.90% | 0.90% |

INSUFFICIENT_VOL_HISTORYはすべて0.90%。Baseline原本は変更せず、F1 skipはscenario layerで資産曲線・Tradesから除外。
Primary=Phase 2 ATR20 quintile、Robustness=RV20 quintile。Phase 1/2のJST日次、過去252営業日midrank、no-lookahead定義を変更せず再利用。

## Primary ALL（2015〜2026-09-09、継続複利）

| 候補 | Final Capital 円 | Net Profit 円 | MaxDD % | Worst Day % | Worst Week % | Money RoMD |
| --- | --- | --- | --- | --- | --- | --- |
| R0_FIXED_090 | 63,209,432,310 | 63,208,932,310 | 22.4891 | -10.8000 | -13.0103 | 5.633387 |
| R1_MILD | 94,599,475,810 | 94,598,975,810 | 18.1699 | -13.2000 | -13.0103 | 7.187580 |
| R2_MODERATE | 137,039,711,613 | 137,039,211,613 | 20.1704 | -15.6000 | -13.0103 | 8.638825 |
| F1_Q1_OFF | 11,064,768,073 | 11,064,268,073 | 17.9380 | -10.8000 | -13.0103 | 10.695500 |

金額は円単位表示のみ丸め、比較とCSVは丸め前。Net Profit=Final Capital−500,000円。
R0 MaxDD×1.25の安全柵は28.111402%。R1=18.169910%、R2=20.170391%で通過。
R1/R2はWorst DayがR0より悪化（−13.2% / −15.6%対−10.8%）している。これは事前の正式不採用条件ではないが、次段階で明示的に検討する事項。
MaxDD%は減ってもMaxDD円は資金拡大に伴い増える。CSVにはMaxDDJPYも保存。

## Robustness ALL

| 候補 | Final Capital 円 | Net Profit 円 | MaxDD % | Worst Day % | Worst Week % | Money RoMD |
| --- | --- | --- | --- | --- | --- | --- |
| R0_FIXED_090 | 63,209,432,310 | 63,208,932,310 | 22.4891 | -10.8000 | -13.0103 | 5.633387 |
| R1_MILD | 92,184,598,174 | 92,184,098,174 | 22.1761 | -12.9000 | -13.0103 | 6.303828 |
| R2_MODERATE | 130,567,854,851 | 130,567,354,851 | 23.6516 | -15.0000 | -13.0103 | 7.119933 |
| F1_Q1_OFF | 13,471,229,846 | 13,470,729,846 | 19.6583 | -10.8000 | -13.0103 | 12.341307 |

R1/R2のALL Final Capital差はそれぞれ+28,975,165,864円 / +67,358,422,541円。双方非負のため整合。
Robustnessで配分を変更していない。RobustnessのMaxDDはR1=22.1761%、R2=23.6516%で、Primaryとの差も残す。

## Primary 4期間Reset

各期間を独立に500,000円から開始。期間前のfeature履歴は保持。

| 候補 | 期間 | Final Capital 円 | R0差 円 |
| --- | --- | --- | --- |
| R0_FIXED_090 | Historical | 328,319,119 | 0 |
| R0_FIXED_090 | RecentA | 7,939,790 | 0 |
| R0_FIXED_090 | RecentB | 5,217,244 | 0 |
| R0_FIXED_090 | Monitor2026 | 580,959 | 0 |
| R1_MILD | Historical | 355,439,194 | 27,120,075 |
| R1_MILD | RecentA | 9,370,807 | 1,431,017 |
| R1_MILD | RecentB | 5,799,253 | 582,010 |
| R1_MILD | Monitor2026 | 612,187 | 31,228 |
| R2_MODERATE | Historical | 378,734,072 | 50,414,953 |
| R2_MODERATE | RecentA | 10,965,996 | 3,026,205 |
| R2_MODERATE | RecentB | 6,402,331 | 1,185,087 |
| R2_MODERATE | Monitor2026 | 644,223 | 63,263 |
| F1_Q1_OFF | Historical | 100,247,176 | -228,071,943 |
| F1_Q1_OFF | RecentA | 6,097,887 | -1,841,903 |
| F1_Q1_OFF | RecentB | 3,489,376 | -1,727,867 |
| F1_Q1_OFF | Monitor2026 | 648,415 | 67,456 |


## Robustness 4期間Reset（副次表示）

| 候補 | 期間 | Final Capital 円 | R0差 円 |
| --- | --- | --- | --- |
| R0_FIXED_090 | Historical | 328,319,119 | 0 |
| R0_FIXED_090 | RecentA | 7,939,790 | 0 |
| R0_FIXED_090 | RecentB | 5,217,244 | 0 |
| R0_FIXED_090 | Monitor2026 | 580,959 | 0 |
| R1_MILD | Historical | 389,069,228 | 60,750,109 |
| R1_MILD | RecentA | 9,055,477 | 1,115,687 |
| R1_MILD | RecentB | 5,475,719 | 258,475 |
| R1_MILD | Monitor2026 | 597,295 | 16,336 |
| R2_MODERATE | Historical | 454,359,437 | 126,040,318 |
| R2_MODERATE | RecentA | 10,249,027 | 2,309,237 |
| R2_MODERATE | RecentB | 5,714,127 | 496,883 |
| R2_MODERATE | Monitor2026 | 613,358 | 32,399 |
| F1_Q1_OFF | Historical | 129,573,084 | -198,746,035 |
| F1_Q1_OFF | RecentA | 6,204,499 | -1,735,291 |
| F1_Q1_OFF | RecentB | 3,186,142 | -2,031,101 |
| F1_Q1_OFF | Monitor2026 | 657,401 | 76,442 |


## 実際のRisk予算・取引数

| 方式 | 候補 | 取引数 | skip数 | 全Baseline平均Risk % | R0差 percentage points | 実行取引平均Risk % |
| --- | --- | --- | --- | --- | --- | --- |
| primary | R0_FIXED_090 | 16298 | 0 | 0.900000 | 0.000000 | 0.900000 |
| primary | R1_MILD | 16298 | 0 | 0.875034 | -0.024966 | 0.875034 |
| primary | R2_MODERATE | 16298 | 0 | 0.850067 | -0.049933 | 0.850067 |
| primary | F1_Q1_OFF | 11513 | 4785 | 0.635765 | -0.264235 | 0.900000 |
| robustness | R0_FIXED_090 | 16298 | 0 | 0.900000 | 0.000000 | 0.900000 |
| robustness | R1_MILD | 16298 | 0 | 0.883354 | -0.016646 | 0.883354 |
| robustness | R2_MODERATE | 16298 | 0 | 0.866708 | -0.033292 | 0.866708 |
| robustness | F1_Q1_OFF | 12199 | 4099 | 0.673647 | -0.226353 | 0.900000 |

R1/R2の五分位単純平均は0.90%でも実際のtrade比率は均等ではない。今回のPrimary実平均は0.875034% / 0.850067%で、R0より低い。
平均nominal riskは同時保有riskや資金加重exposureそのものではない。正規化や別risk探索は行っていない。
F1の全Baseline分母ではskipをRisk=0として平均するが、損益・資産曲線にゼロPnL取引を挿入していない。

## 事前判定

| Candidate | AllProfitPass | Reset3of4Pass | RecentPass | DrawdownPass | ValidationPass | ResetNonnegativeCount | RobustnessConsistent | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R1_MILD | True | True | True | True | True | 4 | True | ECONOMIC_VALUE_CANDIDATE |
| R2_MODERATE | True | True | True | True | True | 4 | True | ECONOMIC_VALUE_CANDIDATE |
| F1_Q1_OFF | False | False | True | True | True | 1 | False | NOT_CANDIDATE |

(a) ALL資金>R0、(b) 4Resetの3以上で>=R0、(c) RecentB/Monitor2026どちらか>R0、(d) MaxDD<=1.25×R0、(e)検証PASSの全条件。
R1/R2は5条件すべて通過しResetは4/4改善。F1はALL利益と3/4期間条件を満たさない。

## 計算と検証

月曜06:00 JSTの週初Balanceを週内固定し、取引固有Riskだけ変える。PnL=WeeklyBase×Risk%×Pips/SL。
前週確定PnLを翌週Baseへ反映。同一週同時保有でもBase共通。決済順CloseTime→EntryTime→StrategyNo→元行番号。
初期資金を含む継続ピークでclosed-balance DDを計算。ALLは期間途中resetなし。
週跨ぎ・Reset期間跨ぎ・破綻は検査し、違反なし。WorstDayはJST決済日の開始残高、WorstWeekは月曜06:00週初残高を分母とする。

| Check | Status | Detail |
| --- | --- | --- |
| Baseline hash / 16298 trades / 28 identities | PASS | cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359 |
| Original M1 byte hashes | PASS | 56 |
| Phase 2 full assignment hash and all quintile labels | PASS | 16298 x 2 methods |
| Phase 2 full/period/strategy quintile counts and R reproduction | PASS | all cells |
| Feature no-lookahead and 23 representative daily audits | PASS | unchanged Phase 1/2 routines |
| Unit tests including inherited future data mutation | PASS | 27 |
| Independent NumPy/pandas all trade/metric verification | PASS | 40 scenarios |
| Original v1.1 R0 all trade PnL/weekly base regression | PASS | 16298 |
| Independent serialized decision signs | PASS | 3 candidates |
| Notebook code-cell local execution | PASS | path substitution only; Drive OFF; Colab runtime not executed |
| Deterministic CSV byte regeneration | PASS | 26 |
| Run record regeneration excluding timestamp | PASS | all other fields equal |

Baseline byte SHA-256: cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359。
主計算Decimal40桁に対しNumPy/pandasの週次積・cumsumで独立照合。rtol=1e-10、金額atol=1e-6円、%/比率atol=1e-10。
保存RとPips/SLの微差はrun_recordに記録し、Baseline列を書き換えていない。
Notebookの実行セルをローカル入力pathに置換して再実行しCSV byte一致。Google Colab環境そのものでは実行していない。
制約付きmode: NOT_RUN_MISSING_HISTORICAL_BROKER_INPUTS。

## 次段階

利益額を最優先する今回の固定候補比較ではR2を次段階の主検討対象、R1を比較対象として残す。
**future validationの期間・評価条件と、実装前のrisk/lot上限・週更新・JST日次feature仕様を別途固定する段階**を推奨する。
今回の結果だけでlive移行しない。R2のWorst Day悪化も将来検証で確認する。中間Risk案や新候補をこの研究に追加しない。

## 作成ファイル

- docs/59_volatility_phase3_plan.md / docs/60_volatility_phase3_result.md
- src/research/volatility_phase3.py
- tests/test_volatility_phase3.py / tests/verify_volatility_phase3.py
- notebooks/volatility_phase3.ipynb
- results/volatility_phase3/: 必須6 CSV、verification、money_audit_summary、feature_manual_audit、input_manifest、source_manifest、validation_summary、constraint_status、artifact_manifest。
完全版trade/weekly/assignmentsおよび500件の取引単位manual auditはlocalまたはColab /contentのみ。GitHubはmoney_audit_summaryに候補別監査件数・状態だけ保存。run_recordのOutputHashesはローカル実行出力のhash、artifact_manifestはGitHub公開CSVのhash。NotebookのDrive保存セルは初期OFF。
