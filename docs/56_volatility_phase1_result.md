# Volatility Environment Phase 1 — 結果

固定28戦略では、ボラティリティが高い環境ほどAvg R/Tradeが高いという診断を、Primary・Robustnessの両方式が事前基準で支持した。これは探索的な環境依存診断であり、将来のfilter有効性やlive採用を意味しない。

- Branch: `research/volatility-environment-phase1`
- 計画SHA: `cb36e1c7d5403c9be40480cdcfbaf221b32fda00`（remote読戻し済み、Planだけのコミット）
- 実装SHA: `af8ba8f333b6ab654ded8f9ae97ae41bbee11c3c`（表示修正後の最終実装、再実行前remote読戻し済み）
- 結果SHA: この結果文書・CSV・結果表示Notebookを含むコミット。最終報告に完全SHAを記載する。
- Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359` 一致。
- 28戦略・16,298 trades維持。Daily Stopなし、ATR OFF、Event Candidate C、UJ12/EJ1修正済み。ログ再計算なし、Entry除外0、EA/VPS/SET/live変更なし。
- 22_GA_C_2も研究対象に維持。2026-09-14週からの停止運用判断は別件。

## 仕様

Primaryは**D1 ATR20 = TRの20日単純平均（SMA）**。既存 `src/filter_test_v2_range_atr.py` の平滑化実装を優先した。**Wilder ATR20ではない**。計画段階でこの選択を固定し、結果後の方式追加はしていない。Wilderのseed/次値は相違を示す手計算テストのみ。

MT5 Europe/Helsinki → Asia/Tokyo → naive JST。日次OHLCはJST暦日の実M1のfirst/max/min/last。最終実M1 Closeを日次Closeとし、翌00:00以降に利用する。土曜早朝に実バーがあれば1日として数え、空休日は作らない。評価日はEntryのJST日付より前の直近完了日。

評価ATRを含めず、その前252 completed trading daysと比較。midrank=(less+0.5×equal)/252。LOW<1/3、NORMAL<2/3、その他HIGH。20日指標と252日全参照値が揃わなければINSUFFICIENT_VOL_HISTORY。後埋めなし。

Robustnessは20日log returnのsample std（ddof=1）×sqrt(252)、同じ252日・midrank三分位。lookback/cut/期間の追加や変更なし。

監査済み7 symbol×8ファイル、合計30,371,276 M1バーを読んだ。入力hash一覧をinput_manifest.csvに記録。データのないJST日は補完せず、途中欠損日も実観測だけから構成した。各symbolの日次本数はdaily auditに記録している。

## Coverage

| Method | Regime | Trades | CoveragePct |
| --- | --- | --- | --- |
| primary | LOW | 6539 | 40.121% |
| primary | NORMAL | 4115 | 25.248% |
| primary | HIGH | 4428 | 27.169% |
| primary | INSUFFICIENT_VOL_HISTORY | 1216 | 7.461% |
| robustness | LOW | 6117 | 37.532% |
| robustness | NORMAL | 4308 | 26.433% |
| robustness | HIGH | 4648 | 28.519% |
| robustness | INSUFFICIENT_VOL_HISTORY | 1225 | 7.516% |

Primary有効15,082件（92.539%）、不足1,216件。Robustness有効15,073件（92.484%）、不足1,225件。最初の有効tradeはそれぞれ2015-11-16 08:01 JST、2015-11-17 00:00 JST。全16,298件のassignmentを保持し、不足分をレジーム成績と分けて件数表示した。

LOW/HIGH双方20件以上の主要比較対象は両方式とも25戦略。14_UJ_Sat_3rd、15_UJ_Sat_Aug、16_UJ_T10Aは標本不足で主要判定に使わない。NORMALは記述的。

## Portfolio / Group

| Method | Regime | Trades | AvgR | PF |
| --- | --- | --- | --- | --- |
| primary | LOW | 6539 | 0.058280 | 1.315575 |
| primary | NORMAL | 4115 | 0.080507 | 1.379063 |
| primary | HIGH | 4428 | 0.135495 | 1.553178 |
| robustness | LOW | 6117 | 0.053973 | 1.283336 |
| robustness | NORMAL | 4308 | 0.096958 | 1.474436 |
| robustness | HIGH | 4648 | 0.121145 | 1.503244 |

全体のLOW→NORMAL→HIGH AvgRはPrimaryで0.058280→0.080507→0.135495、Robustnessで0.053973→0.096958→0.121145。両方式で単調増加。

| Method | Group | PooledDelta | CILow | CIHigh | EqualWeightedDelta | SameSignStrategies | EligibleStrategies | Support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | Portfolio | +0.077215 | +0.039863 | +0.114764 | +0.070864 | 21 | 25 | SUPPORTED |
| primary | JPY | +0.090683 | +0.039410 | +0.142307 | +0.090230 | 12 | 14 | SUPPORTED |
| primary | AUD_nonJPY | +0.054432 | +0.004341 | +0.106806 | +0.046217 | 9 | 11 | SUPPORTED |
| primary | Long | +0.073558 | +0.027806 | +0.118342 | +0.079546 | 14 | 14 | SUPPORTED |
| primary | Short | +0.082499 | +0.024505 | +0.141577 | +0.059815 | 7 | 11 | SUPPORTED |
| robustness | Portfolio | +0.067172 | +0.030311 | +0.102266 | +0.065674 | 22 | 25 | SUPPORTED |
| robustness | JPY | +0.084725 | +0.037119 | +0.131092 | +0.083761 | 13 | 14 | SUPPORTED |
| robustness | AUD_nonJPY | +0.041872 | -0.007572 | +0.091368 | +0.042656 | 9 | 11 | NOT_SUPPORTED |
| robustness | Long | +0.070974 | +0.027096 | +0.112941 | +0.076067 | 14 | 14 | SUPPORTED |
| robustness | Short | +0.062013 | +0.008386 | +0.118175 | +0.052447 | 8 | 11 | SUPPORTED |

PortfolioはPrimary Δ=+0.077215R（95%CI +0.039863〜+0.114764）、Robustness Δ=+0.067172R（+0.030311〜+0.102266）。等重み差も正で、十分標本戦略の符号一致は21/25と22/25。

JPY、Long、Shortは両方式同方向支持。AUD_nonJPYはPrimaryのみ支持で、RobustnessのCIがゼロを含む。groupで対象を後付け限定していない。

## 全28戦略要約

ΔはHIGH−LOW AvgR。CI判定「両方式」はLOW/HIGH各20件以上かつ両方式の95%CIが0を含まず、同方向という事前定義。CIは多重比較未調整である。

| Strategy | ATR LOW/NORMAL/HIGH件数 | ATR AvgR LOW→NORMAL→HIGH | ATR ΔH−L | RV ΔH−L | CI判定 |
| --- | --- | --- | --- | --- | --- |
| 1_EJ_Log1 | 361/195/235 | 0.1047 → 0.0730 → 0.2885 | +0.1838 | +0.1521 | 両方式 |
| 2_EJ_NightBlitz_20 | 438/222/294 | 0.0818 → 0.1430 → 0.1166 | +0.0348 | +0.0165 | 明確な差なし |
| 3_EJ_NightBlitz_21 | 437/222/295 | 0.0612 → 0.0820 → 0.0662 | +0.0049 | +0.0294 | 明確な差なし |
| 4_GJ_Port_Log1 | 360/249/268 | 0.0215 → 0.0442 → 0.0643 | +0.0429 | +0.0577 | Robustnessのみ |
| 5_GJ_Port_Log2 | 462/339/360 | 0.0448 → 0.0785 → 0.1422 | +0.0975 | +0.0931 | 明確な差なし |
| 6_GJ_Old_Mon | 198/133/124 | 0.0231 → 0.2229 → 0.3903 | +0.3672 | +0.3095 | 両方式 |
| 7_GJ_Mon_Blitz | 228/164/153 | 0.0285 → 0.0723 → 0.0705 | +0.0420 | +0.0574 | 明確な差なし |
| 8_AJ_Core1 | 224/168/153 | 0.0667 → 0.0687 → 0.1731 | +0.1064 | +0.1323 | Robustnessのみ |
| 9_AJ_Core2 | 111/100/105 | 0.1507 → 0.3051 → 0.1686 | +0.0179 | +0.0132 | 明確な差なし |
| 10_AJ_SatA | 141/116/117 | -0.0027 → 0.0297 → -0.0206 | -0.0178 | -0.0430 | 明確な差なし |
| 11_AJ_SatB | 142/116/117 | 0.0650 → 0.0336 → 0.0554 | -0.0095 | +0.0544 | 明確な差なし |
| 12_UJ_Short_Core | 207/145/151 | 0.1599 → 0.1631 → 0.4375 | +0.2776 | +0.2534 | 両方式 |
| 13_UJ_Fix_MidWeek | 88/60/59 | 0.0644 → 0.0529 → 0.1332 | +0.0689 | +0.0011 | 明確な差なし |
| 14_UJ_Sat_3rd | 30/17/19 | 0.4014 → 0.2488 → 0.5118 | +0.1104 | -0.4339 | 標本不足 |
| 15_UJ_Sat_Aug | 14/18/33 | 0.1479 → 0.3008 → 0.4270 | +0.2791 | +0.2964 | 標本不足 |
| 16_UJ_T10A | 22/13/19 | 0.1698 → -0.0426 → 0.4784 | +0.3086 | +0.3081 | 標本不足 |
| 17_EA_1B_Wed_Short | 139/95/91 | 0.1846 → 0.1354 → 0.1399 | -0.0447 | -0.0339 | 明確な差なし |
| 18_EA_2_MonWed_Short | 411/245/227 | 0.0097 → 0.0667 → 0.0987 | +0.0891 | +0.0239 | 明確な差なし |
| 19_EA_3_WedThu_Long | 279/190/178 | 0.0558 → 0.0506 → 0.1658 | +0.1100 | +0.0904 | 明確な差なし |
| 20_EA_1A_MonTue_Short | 351/188/174 | -0.0092 → 0.0349 → 0.1175 | +0.1266 | +0.0877 | 明確な差なし |
| 21_GA_B_3 | 265/130/148 | 0.0064 → -0.0120 → 0.0220 | +0.0156 | +0.0280 | 明確な差なし |
| 22_GA_C_2 | 187/104/140 | 0.0936 → -0.0519 → 0.1014 | +0.0078 | +0.0473 | 明確な差なし |
| 23_GA_F_2 | 172/100/131 | -0.0169 → 0.0570 → 0.1119 | +0.1288 | +0.1486 | 両方式 |
| 24_GA_D_1 | 172/100/131 | 0.0459 → 0.0543 → 0.0970 | +0.0511 | +0.0937 | 明確な差なし |
| 25_AU_China_Demand | 443/233/267 | 0.0481 → 0.0403 → 0.0796 | +0.0315 | +0.0040 | 明確な差なし |
| 26_AJ_China_Demand | 196/135/145 | 0.1184 → 0.0534 → 0.1652 | +0.0469 | +0.0455 | 明確な差なし |
| 27_EA_China_Demand | 229/172/137 | 0.0979 → 0.1227 → 0.0553 | -0.0427 | -0.0659 | 明確な差なし |
| 28_GA_China_Demand | 232/146/157 | 0.0473 → 0.1056 → 0.0826 | +0.0353 | +0.0455 | 明確な差なし |

明確な同方向差が両方式で見られた4戦略は、1_EJ_Log1、6_GJ_Old_Mon、12_UJ_Short_Core、23_GA_F_2。いずれもHIGH側が高い。
4_GJ_Port_Log1と8_AJ_Core1はRobustnessのみ。特に8_AJ_Core1のCI下限は約+0.000014Rで境界に非常に近く、強い証拠とは扱わない。
22_GA_C_2はPrimary +0.007797R、Robustness +0.047302Rだが、いずれもCIが0を含む。この研究から同戦略のlive判断を変更しない。

## 事前固定した補助期間

| Period | Method | HighMinusLowAvgR |
| --- | --- | --- |
| Historical | primary | +0.056816 |
| Historical | robustness | +0.060625 |
| RecentA | primary | +0.093096 |
| RecentA | robustness | +0.080981 |
| RecentB | primary | +0.110512 |
| RecentB | robustness | +0.059208 |
| Monitor2026 | primary | +0.071539 |
| Monitor2026 | robustness | +0.074023 |

全体の差の符号は4期間とも正。ただし期間別は記述のみで追加CIや窓探索はしていない。2022〜2026は既閲覧で完全未閲覧holdoutではない。

## 検証

- 10 unit tests PASS: ATR20 SMA手計算・Wilder20との差、履歴index、252日評価値除外、exact cutとties、RV ddof、冬夏JST、OHLCと土曜、00:00/休日/no-lookahead、空/ゼロ/sample、週cluster、比較不能。
- 全28のStrategyNo/ID/Pair/DirectionとBaseline byte hash、件数を検証。
- 全16,298 assignmentでdaily確定時刻と最終M1 Close確定時刻がEntry以前であることを検証。
- 別Decimal集計で1,140行の全期間strategy/group指標・差・等重み・標本条件・支持判定を照合。coverageも別計算で照合。
- 事前定義した代表日の23日次auditがPASS。M1からOHLCを別集計し、ATR/RV/参照窓を再計算。
- Bootstrapは全method/group/strategyで同じ暦週抽出を共有。seed=20260913、5000回、95%linear CI。全group比較で5000回有効。

初回実装eff8eda7c139d8d0ac0f0d2c8f5fc36bb8505b0aの結果確認後、等重み行にpooled CIが重複表示される箇所のみ修正した。計画・計算定義・閾値・判定基準は変更せず、最終実装SHAで再実行した。

週内の戦略間依存を保つが週を跨ぐ自己相関や非定常性は完全には扱わず、多重比較未調整。HIGH−LOWを主要比較にするためNORMALのみ異なる非単調依存は検出できない。「明確な差なし」は依存不存在の証明ではない。

## Phase 2 / ATR70との関係

別事前登録で深掘りする価値がある候補は上記4戦略と、両方式支持のPortfolio/JPY/Long/Short。候補列挙までとし、対象を選んだ追加計算・threshold探索・Entry除外は実施していない。
旧「ATR70」はH1 ATR14 P70を使ったEntry可否フィルター。今回はD1 ATR20を環境診断変数として使用した別研究であり、結果融合なし。LOWでもpooled AvgRは正で、この診断はLOW停止で利益が改善することを意味しない。

## 成果物

- docs/55_volatility_phase1_plan.md / docs/56_volatility_phase1_result.md
- src/research/volatility_phase1.py / volatility_phase1_frozen_inputs.json
- tests/test_volatility_phase1.py / verify_volatility_phase1.py
- notebooks/volatility_phase1.ipynb（主要結果は本文に保存。Colab用実行セルと初期OFFのDrive保存セル付き）
- results/volatility_phase1/ の必須6 CSV: strategy_primary, strategy_robustness, group_summary, period_summary, regime_coverage, run_record（全てvolatility_phase1_ prefix）
- 同ディレクトリの補助CSV: decision, combined_decision, manual_audit, input_manifest, verification, assignment_audit_light。
- 完全trade_assignments・daily_auditはlocal成果物だけに保存、GitHubに含めない。

実データ実行はローカルPythonで完了。Colabセルは再実行用として用意し、/contentへ同じCSVを保存する。Driveへの結果保存は実行していない。
