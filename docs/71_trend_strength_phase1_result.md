# Trend Strength Phase 1 — 結果

**総合判定: NOT_SUPPORTED（Primary ADX14 / Robustness ER20とも不支持）。事前条件によるPhase 2進行は支持されない。**
これは依存不存在の証明ではなく、固定したHIGH−LOW診断で支持条件を満たさなかったという結果である。

## 実行系譜と変更境界
- Branch: research/trend-strength-phase1
- 基点: 0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc（Volatility Phase 2）
- 計画SHA: 50e7d70cf1eb1fe892c144a0721dbf490e07b656
- 実装SHA: d297143d0d173632fad0fe7f1372292a4bcc5981
- 計画のみremote固定・読み返し後に実装。実装remote SHA読み返し後に実データ研究計算。
- 結果SHA: このResult/CSV/Notebookを追加したコミット（自己参照を避け本文へのSHA埋め込みはしない）。
- 既存ファイルの変更はなし。専用Trend研究ファイルのみ新規追加。
- Volatility Phase 5 Dell Demo Forward、EA/VPS/SET/liveコード・設定は変更なし。
- Baseline再計算なし、Entry除外0件、Risk変更なし、Volatility交差分析/統合なし。

## 固定入力・仕様
28戦略16,298 trades、Baseline SHA256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359` 一致。
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。
live停止済み22_GA_C_2を含む固定28戦略。全StrategyNo/Strategy/Pair/Direction一致。
監査済みM1の56/56ファイルが既存Volatility Phase1 input manifestのSHA256と一致。
MT5 Europe/Helsinki→Asia/Tokyo→timezone-naive JST。各実バーのあるJST暦日にOHLCを生成、Closeは最終M1 Close。
土曜早朝も1 completed trading day。翌日00:00から使用可、Entry当日の部分足は禁止。

PrimaryはWilder ADX14。raw i=1..14平均をsmooth seed、DX i=14..27平均を最初のADX（i=27）、以後(13*前値+現在値)/14。
DMの同値は両方0、TR/DIのゼロ分母は0。RobustnessはER20=abs(Ct−Ct−20)/20変化の絶対値合計、分母0はER=0。
評価日を除く過去252完了日のmidrank。(2*less+equal)<168 LOW、168以上336未満 NORMAL、336以上 HIGH。
不足はINSUFFICIENT_TREND_HISTORY。ADX初分類index279、ER272。指標・window・cutの変更なし。

## Portfolio Primary / Robustness
主指標AvgR/Trade。WinRateは%、AvgLossRは負値。LOW/NORMAL/HIGH順。

| Method | Regime | Trades | TotalR | AvgR | PF | WinRate | AvgWinR | AvgLossR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | LOW | 5129 | +435.454622 | +0.084900 | +1.430496 | +55.488399 | +0.508423 | -0.445407 |
| primary | NORMAL | 4881 | +452.669482 | +0.092741 | +1.450706 | +55.070682 | +0.542048 | -0.459660 |
| primary | HIGH | 5033 | +426.634780 | +0.084767 | +1.374851 | +53.586330 | +0.580193 | -0.488684 |
| robustness | LOW | 5037 | +394.290454 | +0.078279 | +1.374451 | +54.059956 | +0.531500 | -0.456232 |
| robustness | NORMAL | 4886 | +452.465945 | +0.092605 | +1.462239 | +55.259926 | +0.530119 | -0.449635 |
| robustness | HIGH | 5150 | +464.176428 | +0.090131 | +1.409792 | +54.737864 | +0.566474 | -0.488449 |

HIGH−LOW差と正式判定:

| Method | PooledDelta | CILow | CIHigh | EqualWeightedDelta | EligibleStrategies | SameSignStrategies | Support |
| --- | --- | --- | --- | --- | --- | --- | --- |
| primary | -0.000133 | -0.033329 | +0.034280 | +0.014636 | 26 | 11 | NOT_SUPPORTED |
| robustness | +0.011853 | -0.022186 | +0.046414 | +0.005706 | 25 | 16 | NOT_SUPPORTED |

ADXはpooled差−0.000133と等重み差+0.014636で方向が一致せず、符号一致11/26で過半数未達、CIも0を含む。
ERは差+0.011853、等重み差+0.005706、符号一致16/25で方向条件は満たすが、CIが0を含むため不支持。
ADX pooledはHIGH < LOW < NORMAL、ER pooledはLOW < HIGH < NORMALで、単調な高Trend優位は示されない。

等重みLOW/NORMAL/HIGH:

| Method | Regime | AvgR | HighMinusLowAvgR | EligibleStrategies | RegimeOrder |
| --- | --- | --- | --- | --- | --- |
| primary | LOW | +0.092216 | +0.014636 | 26 | LOW < NORMAL < HIGH |
| primary | NORMAL | +0.094266 | +0.014636 | 26 | LOW < NORMAL < HIGH |
| primary | HIGH | +0.106852 | +0.014636 | 26 | LOW < NORMAL < HIGH |
| robustness | LOW | +0.081699 | +0.005706 | 25 | LOW < HIGH < NORMAL |
| robustness | NORMAL | +0.094844 | +0.005706 | 25 | LOW < HIGH < NORMAL |
| robustness | HIGH | +0.087405 | +0.005706 | 25 | LOW < HIGH < NORMAL |

ADX等重み対象26戦略（14_UJ_Sat_3rd / 16_UJ_T10Aを除く）、ER対象25戦略（14 / 15_UJ_Sat_Aug / 16を除く）。
いずれもLOWとHIGH双方20以上。NORMALは記述のみ。pooledは全28戦略の有効分類tradeを含む。

## Coverage

| Method | Assigned | Insufficient | CoveragePct |
| --- | --- | --- | --- |
| primary | 15043 | 1255 | +92.299669 |
| robustness | 15073 | 1225 | +92.483740 |

履歴不足も16,298件のassignmentに保持。日次特徴量計算のwarm-upと252日reference不足によるもので、再計算や後埋めは行わない。

## 補助group
全4群とも両方式不支持。groupにより対象を絞らない。

| Method | Group | PooledDelta | CILow | CIHigh | EqualWeightedDelta | EligibleStrategies | SameSignStrategies | Support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | JPY | -0.005674 | -0.052386 | +0.042938 | +0.021113 | 15 | 5 | NOT_SUPPORTED |
| primary | AUD_nonJPY | +0.007523 | -0.036693 | +0.053305 | +0.005804 | 11 | 5 | NOT_SUPPORTED |
| primary | Long | -0.000490 | -0.041031 | +0.040444 | -0.007427 | 14 | 6 | NOT_SUPPORTED |
| primary | Short | +0.000354 | -0.053663 | +0.057024 | +0.040377 | 12 | 7 | NOT_SUPPORTED |
| robustness | JPY | +0.020338 | -0.028359 | +0.070027 | +0.012722 | 14 | 9 | NOT_SUPPORTED |
| robustness | AUD_nonJPY | -0.000675 | -0.047027 | +0.045245 | -0.003222 | 11 | 4 | NOT_SUPPORTED |
| robustness | Long | +0.017227 | -0.022696 | +0.057571 | +0.004532 | 14 | 9 | NOT_SUPPORTED |
| robustness | Short | +0.003892 | -0.054512 | +0.058532 | +0.007201 | 11 | 7 | NOT_SUPPORTED |

## 全28戦略
各行のLOW/NORMAL/HIGHはAvgR、Nは各cell件数。十分標本戦略について、両方式ともCIが0を除外する個別戦略は0件。全件数値を開示し、LOW_SAMPLEもCSVに保持。

### ADX14

| Strategy | N_L | N_N | N_H | LOW | NORMAL | HIGH | Delta | CILow | CIHigh | Eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1_EJ_Log1 | 265 | 252 | 272 | +0.132259 | +0.156559 | +0.166665 | +0.034406 | -0.090969 | +0.153694 | True |
| 2_EJ_NightBlitz_20 | 328 | 312 | 311 | +0.099851 | +0.124274 | +0.103830 | +0.003979 | -0.123038 | +0.129779 | True |
| 3_EJ_NightBlitz_21 | 327 | 312 | 312 | +0.044644 | +0.089731 | +0.073419 | +0.028775 | -0.043313 | +0.105117 | True |
| 4_GJ_Port_Log1 | 296 | 295 | 283 | +0.024324 | +0.074720 | +0.023650 | -0.000674 | -0.048290 | +0.046323 | True |
| 5_GJ_Port_Log2 | 409 | 360 | 390 | +0.122127 | +0.069478 | +0.055595 | -0.066532 | -0.185480 | +0.054102 | True |
| 6_GJ_Old_Mon | 150 | 155 | 148 | +0.280853 | +0.183458 | +0.079351 | -0.201502 | -0.464901 | +0.063517 | True |
| 7_GJ_Mon_Blitz | 184 | 181 | 178 | +0.082429 | +0.058058 | +0.019235 | -0.063194 | -0.141877 | +0.014385 | True |
| 8_AJ_Core1 | 179 | 186 | 178 | +0.093695 | +0.092081 | +0.109238 | +0.015542 | -0.117519 | +0.149804 | True |
| 9_AJ_Core2 | 99 | 103 | 114 | +0.155320 | +0.239806 | +0.218070 | +0.062750 | -0.244387 | +0.366239 | True |
| 10_AJ_SatA | 130 | 130 | 113 | +0.000523 | -0.013354 | +0.022124 | +0.021601 | -0.064613 | +0.107024 | True |
| 11_AJ_SatB | 131 | 130 | 113 | +0.055461 | +0.059217 | +0.045776 | -0.009685 | -0.175134 | +0.154829 | True |
| 12_UJ_Short_Core | 153 | 186 | 161 | +0.196843 | +0.279527 | +0.251491 | +0.054648 | -0.129693 | +0.245914 | True |
| 13_UJ_Fix_MidWeek | 65 | 71 | 71 | +0.071239 | +0.084700 | +0.085278 | +0.014039 | -0.070859 | +0.102697 | True |
| 14_UJ_Sat_3rd | 25 | 22 | 19 | +0.422044 | +0.408485 | +0.339883 | -0.082161 | -0.597838 | +0.424193 | False |
| 15_UJ_Sat_Aug | 28 | 17 | 20 | +0.223214 | +0.162941 | +0.627750 | +0.404536 | -0.440348 | +0.946665 | True |
| 16_UJ_T10A | 26 | 14 | 14 | +0.237009 | +0.286667 | +0.149683 | -0.087326 | -0.576680 | +0.472340 | False |
| 17_EA_1B_Wed_Short | 109 | 100 | 115 | +0.133604 | +0.172086 | +0.174311 | +0.040706 | -0.163151 | +0.239040 | True |
| 18_EA_2_MonWed_Short | 282 | 280 | 317 | +0.019657 | +0.078294 | +0.046085 | +0.026428 | -0.093692 | +0.153095 | True |
| 19_EA_3_WedThu_Long | 219 | 208 | 218 | +0.035550 | +0.058429 | +0.162161 | +0.126611 | -0.003207 | +0.253368 | True |
| 20_EA_1A_MonTue_Short | 226 | 240 | 244 | +0.029044 | +0.049067 | +0.020967 | -0.008077 | -0.135230 | +0.120978 | True |
| 21_GA_B_3 | 187 | 165 | 189 | +0.016279 | +0.015562 | -0.011724 | -0.028003 | -0.078992 | +0.023701 | True |
| 22_GA_C_2 | 155 | 125 | 150 | +0.152553 | -0.031634 | +0.050733 | -0.101820 | -0.289000 | +0.086485 | True |
| 23_GA_F_2 | 147 | 117 | 138 | +0.042661 | +0.036477 | +0.040185 | -0.002475 | -0.109803 | +0.101912 | True |
| 24_GA_D_1 | 147 | 117 | 138 | +0.049554 | +0.048500 | +0.101981 | +0.052427 | -0.081574 | +0.189234 | True |
| 25_AU_China_Demand | 326 | 321 | 296 | +0.054333 | +0.058964 | +0.051757 | -0.002576 | -0.076649 | +0.074145 | True |
| 26_AJ_China_Demand | 144 | 158 | 174 | +0.123194 | +0.076329 | +0.141201 | +0.018006 | -0.101597 | +0.145141 | True |
| 27_EA_China_Demand | 173 | 173 | 192 | +0.074451 | +0.086628 | +0.121024 | +0.046573 | -0.068100 | +0.157023 | True |
| 28_GA_China_Demand | 219 | 151 | 165 | +0.083951 | +0.141015 | -0.001996 | -0.085947 | -0.196051 | +0.020869 | True |

### ER20

| Strategy | N_L | N_N | N_H | LOW | NORMAL | HIGH | Delta | CILow | CIHigh | Eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1_EJ_Log1 | 273 | 237 | 280 | +0.083579 | +0.187233 | +0.186439 | +0.102859 | -0.031436 | +0.236734 | True |
| 2_EJ_NightBlitz_20 | 330 | 284 | 339 | +0.060875 | +0.142723 | +0.124641 | +0.063766 | -0.054120 | +0.187277 | True |
| 3_EJ_NightBlitz_21 | 329 | 284 | 340 | +0.022800 | +0.092319 | +0.092212 | +0.069411 | -0.004965 | +0.142035 | True |
| 4_GJ_Port_Log1 | 288 | 302 | 287 | +0.044346 | +0.051342 | +0.026829 | -0.017516 | -0.067644 | +0.033595 | True |
| 5_GJ_Port_Log2 | 382 | 392 | 387 | +0.099887 | +0.091125 | +0.063615 | -0.036272 | -0.162726 | +0.094114 | True |
| 6_GJ_Old_Mon | 142 | 154 | 158 | +0.178563 | +0.310870 | +0.051127 | -0.127437 | -0.377859 | +0.135864 | True |
| 7_GJ_Mon_Blitz | 181 | 179 | 184 | +0.059949 | +0.064783 | +0.035656 | -0.024293 | -0.106266 | +0.056516 | True |
| 8_AJ_Core1 | 192 | 170 | 182 | +0.050513 | +0.145513 | +0.100549 | +0.050036 | -0.079828 | +0.183715 | True |
| 9_AJ_Core2 | 114 | 92 | 110 | +0.180292 | +0.241159 | +0.201788 | +0.021495 | -0.299460 | +0.337999 | True |
| 10_AJ_SatA | 109 | 139 | 126 | -0.008642 | +0.013683 | -0.002413 | +0.006230 | -0.074200 | +0.085100 | True |
| 11_AJ_SatB | 109 | 140 | 126 | -0.009108 | +0.115299 | +0.035411 | +0.044519 | -0.115822 | +0.199803 | True |
| 12_UJ_Short_Core | 147 | 172 | 184 | +0.230041 | +0.242465 | +0.257016 | +0.026975 | -0.196996 | +0.240099 | True |
| 13_UJ_Fix_MidWeek | 56 | 76 | 75 | +0.064474 | +0.105609 | +0.067495 | +0.003021 | -0.099771 | +0.098257 | True |
| 14_UJ_Sat_3rd | 24 | 25 | 17 | +0.479630 | +0.376533 | +0.298301 | -0.181329 | -0.686789 | +0.322324 | False |
| 15_UJ_Sat_Aug | 16 | 27 | 22 | +0.295312 | +0.056296 | +0.696818 | +0.401506 | -0.454629 | +0.902760 | False |
| 16_UJ_T10A | 25 | 14 | 15 | +0.160622 | +0.328254 | +0.244000 | +0.083378 | -0.350529 | +0.584185 | False |
| 17_EA_1B_Wed_Short | 112 | 105 | 108 | +0.197436 | +0.118667 | +0.154378 | -0.043058 | -0.271231 | +0.167772 | True |
| 18_EA_2_MonWed_Short | 304 | 263 | 315 | +0.057021 | +0.052666 | +0.035249 | -0.021773 | -0.138045 | +0.094128 | True |
| 19_EA_3_WedThu_Long | 227 | 213 | 207 | +0.094508 | +0.048247 | +0.111004 | +0.016496 | -0.117508 | +0.151632 | True |
| 20_EA_1A_MonTue_Short | 234 | 210 | 268 | +0.033171 | -0.021571 | +0.075410 | +0.042240 | -0.080198 | +0.162004 | True |
| 21_GA_B_3 | 178 | 170 | 194 | -0.008036 | -0.006281 | +0.029653 | +0.037689 | -0.013100 | +0.088555 | True |
| 22_GA_C_2 | 142 | 149 | 140 | +0.199256 | -0.034573 | +0.022561 | -0.176694 | -0.372865 | +0.017580 | True |
| 23_GA_F_2 | 148 | 124 | 131 | +0.029775 | +0.037581 | +0.064046 | +0.034271 | -0.067415 | +0.133086 | True |
| 24_GA_D_1 | 148 | 124 | 131 | +0.022065 | +0.087679 | +0.090797 | +0.068733 | -0.058772 | +0.196366 | True |
| 25_AU_China_Demand | 317 | 339 | 287 | +0.048778 | +0.064617 | +0.050845 | +0.002067 | -0.068158 | +0.074129 | True |
| 26_AJ_China_Demand | 144 | 153 | 179 | +0.127562 | +0.091547 | +0.122868 | -0.004694 | -0.144212 | +0.129162 | True |
| 27_EA_China_Demand | 181 | 180 | 177 | +0.049761 | +0.130306 | +0.105320 | +0.055560 | -0.065893 | +0.175151 | True |
| 28_GA_China_Demand | 185 | 169 | 181 | +0.133600 | -0.001901 | +0.082622 | -0.050978 | -0.158289 | +0.057247 | True |

## 補助期間
2022–2026は既閲覧で完全未閲覧holdoutではない。追加窓探索なし。以下はpooledの記述値であり、期間別の正式支持判定を行わない。

| Period | Method | LOW | NORMAL | HIGH | Delta |
| --- | --- | --- | --- | --- | --- |
| Historical | primary | +0.068652 | +0.082641 | +0.092641 | +0.023989 |
| Historical | robustness | +0.074879 | +0.087231 | +0.080526 | +0.005648 |
| RecentA | primary | +0.161132 | +0.125911 | +0.050875 | -0.110257 |
| RecentA | robustness | +0.127419 | +0.086730 | +0.134926 | +0.007507 |
| RecentB | primary | +0.074531 | +0.123045 | +0.103395 | +0.028864 |
| RecentB | robustness | +0.061318 | +0.142068 | +0.095564 | +0.034246 |
| Monitor2026 | primary | -0.022875 | +0.024779 | +0.049307 | +0.072182 |
| Monitor2026 | robustness | -0.009184 | +0.012981 | +0.043283 | +0.052468 |

ADXではRecentAの差が負、他3期間は正で、方向は期間によって異なる。ERの補助期間差は正だが、FULLのCI条件を満たさない。
これを理由に期間や閾値を変更しない。NORMALが高い形状は記述するが別検定を追加しない。

## 検証
16 unit tests PASS（ADX/ER手計算・独立実装、ゼロ分母、初有効index、252参照・等号、JST冬夏・土曜、月曜、00:00、future M1改変/prefix不変、sample/CI正式条件、Baseline不一致拒否）。
各symbolの全日次ADX/ERを独立scalar実装と照合。ADX独立側はsmooth sumsとDIの共通分母消去を使用し、本体のsmooth means/DI計算から分離。
23代表日を元M1 OHLC/Close、指標、reference、代表trade Entry確定時刻で照合。
全日次OHLC/日付/LastM1/AvailableAt/M1Countは既存Volatility Phase1 make_dailyと完全一致。
独立Decimal集計・等重み・符号判定・週別集計CIを照合。

| Check | Status | Rows |
| --- | --- | --- |
| Independent Decimal metrics, differences, equal weights, eligibility, support, coverage all periods | PASS | 1140 |
| All trades retained; all trade-date availability assertions | PASS | 16298 |
| Independent weekly sums and linear CI | PASS | 66 |
| Regime ordering, exact rank labels, combined decisions | PASS | 1140 |
| All daily ADX and ER scalar reference; representative M1 audits | PASS | 23 |
| Volatility daily generation exact regression and frozen M1 hashes | PASS | 56 |

## 解釈とPhase 2
事前固定したPortfolio BOTH_SUPPORTED条件を満たさないため、**このPhase 1を根拠にPhase 2へ進む価値・条件は確認されなかった**。
HIGH/LOWどちらかの優位、独立情報、因果、将来filter有効性を主張しない。不支持は依存不存在の証明ではない。
Volatility Phase1〜4で高VolほどAvgRが高いことは既存結果。本研究はTrend単独診断で、Volatilityとの相関や独立情報を評価していない。
将来のPhase2を行うなら別の根拠と別事前登録が必要。既定方針は五分位段階関係とVolatilityを揃えた追加情報の検証。
後段Economic Valueの比較方針 R2 vs R2 + Trend Strengthを維持するが、今回実行・採用しない。
CIは5000回、seed20260913、611暦週cluster、全method/strategy共通週重み、95%linear quantile。
多重比較未調整、週を跨ぐ依存・非定常性を完全には扱わず、完全未閲覧holdoutでもない。

## 作成ファイル
- docs/70_trend_strength_phase1_plan.md / docs/71_trend_strength_phase1_result.md
- src/research/trend_strength_phase1.py / trend_strength_phase1_frozen_inputs.json
- tests/test_trend_strength_phase1.py / verify_trend_strength_phase1.py
- notebooks/trend_strength_phase1.ipynb（本文にPortfolio/全28戦略主要結果、実行セル、/content保存、Drive保存初期OFF）
- results/trend_strength_phase1/ の以下CSV（prefix: trend_strength_phase1_）:
  strategy_primary, strategy_robustness, group_summary, period_summary, regime_coverage, run_record,
  decision, combined_decision, manual_audit, input_manifest, assignment_audit_light, verification。
- 詳細trade_assignments/daily_auditはローカルのみ。GitHubには追加しない。

実行環境・日時・input/output SHA256はrun_recordとinput_manifest参照。本文はローカル実行結果でありColab実行出力ではない。

## GitHub軽量化の記録
自動承認レビューの200,000バイト上限により一括アップロードが拒否されたため、個別に確認可能な研究成果物として保存した。period_summaryは全912行と全主要指標を保持し、重複するStrategy名/Symbol/Direction/EligibleIDs等の説明列と期間別では未使用のCI/Support列を省略した。省略前後の共通列は全行完全照合PASS。完全版はローカルに保持。run_recordのOutputHashesは計算時の完全版を指し、公開版のhashと完全版との差はpublication_manifestで明記する。分析結果・判定・精度・事前計画の変更はない。

取引時刻・損益を含む軽量assignment auditも自動承認レビューで拒否されたため、公開assignment_audit_lightはsymbol/日次指標/分類のみ（取引ID・戦略ID・EntryTime・Rなし）、公開manual_auditは代表trade時刻列なしとした。完全な取引単位監査はローカルのみ。公開範囲を縮小し、研究計算・判定は変更していない。
