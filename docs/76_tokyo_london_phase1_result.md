# Tokyo → London Market Effect Phase 1 — Result

全6通貨 NOT_SUPPORTED。事前登録したA（CIが0を除外）とB（Holm調整後有意）の両方を全通貨が満たさず、Phase 2候補は0通貨。
本研究の固定window・線形関係に対する結論であり、あらゆる非線形効果や将来の関係が存在しないという証明ではない。閾値や片側条件を追加探索していない。

## Provenance
- Branch: research/tokyo-london-market-effect-phase1
- Base SHA: 1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5
- Plan SHA: 9a51295b5e5868bb2f7ba909206a8fc0588dafdb（GitHub commit後remote ref一致確認、実装前）
- Implementation SHA: c81425b969e7e53d6153c02852dfa6c1d45f363c（remote ref一致確認、実データ統計計算前）
- Result SHA: このResult文書・CSVを最初に追加したcommitのSHA。自己参照を避け本文には埋め込まず、最終報告でremote確認済みSHAを提示。
- 実行UTC: 2026-09-20T14:35:38.960205+00:00
- Planからの分析仕様逸脱: なし。実装後の時刻・pair・閾値・検定変更なし。
- 実行ソース・テスト・Notebook・入力manifestのGit blobがImplementation SHA上の6成果物と一致。

## ALL Primary
| Pair | N | beta | 95% CI | p raw | p Holm | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| USDJPY | 3007 | 0.033938 | [-0.011079, 0.077138] | 0.131174 | 0.655869 | NOT_SUPPORTED |
| EURJPY | 3007 | -0.012742 | [-0.071834, 0.048693] | 0.683063 | 1.000000 | NOT_SUPPORTED |
| GBPJPY | 3007 | -0.051960 | [-0.151236, 0.060408] | 0.471506 | 1.000000 | NOT_SUPPORTED |
| AUDJPY | 3006 | -0.012556 | [-0.049183, 0.023642] | 0.501700 | 1.000000 | NOT_SUPPORTED |
| EURAUD | 3007 | -0.029324 | [-0.085157, 0.021230] | 0.297740 | 1.000000 | NOT_SUPPORTED |
| GBPAUD | 3001 | -0.059379 | [-0.124347, 0.005595] | 0.076985 | 0.461908 | NOT_SUPPORTED |


## Period / Robustness stability
| Pair | Historical | Recent Combined | Recent A | Recent B | 2026 | Robustness beta |
| --- | --- | --- | --- | --- | --- | --- |
| USDJPY | + | + | + | + | + | +0.026579 |
| EURJPY | − | + | + | − | + | -0.016393 |
| GBPJPY | − | + | + | + | + | -0.043336 |
| AUDJPY | − | + | + | + | + | -0.019254 |
| EURAUD | − | − | + | − | − | -0.034835 |
| GBPAUD | − | + | + | − | − | -0.073884 |

全72 pair×method×periodセルは最低80日・20観測週およびbootstrap有効反復条件を満たす。
2026 Monitorは全pair/methodで176日・37週。2022–2026はpristine unseen holdoutではない。

## A〜E gates
| Pair | A CI | B Holm | C Historical/Recent | D 2 of 3 | E Robustness |
| --- | --- | --- | --- | --- | --- |
| USDJPY | FAIL | FAIL | PASS | PASS | PASS |
| EURJPY | FAIL | FAIL | FAIL | FAIL | PASS |
| GBPJPY | FAIL | FAIL | FAIL | FAIL | PASS |
| AUDJPY | FAIL | FAIL | FAIL | FAIL | PASS |
| EURAUD | FAIL | FAIL | PASS | PASS | PASS |
| GBPAUD | FAIL | FAIL | FAIL | PASS | PASS |

A: ALL CI非ゼロ、B: ALL Holm p<=.05、C: HistoricalとRecentCombined同符号、D: Recent A/B/2026の2期間以上同符号、E: Robustness ALL同符号。

## Direction diagnostics (ALL Primary)
| Pair | Tokyo | N | London mean pips | median pips | Reversal % | Continuation % | London neutral % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | UP | 1500 | 0.683 | 0.800 | 47.60 | 52.07 | 0.33 |
| USDJPY | DOWN | 1498 | -0.259 | 0.650 | 51.27 | 48.66 | 0.07 |
| EURJPY | UP | 1562 | 0.238 | 1.400 | 47.25 | 52.69 | 0.06 |
| EURJPY | DOWN | 1438 | 0.558 | 1.050 | 51.88 | 48.12 | 0.00 |
| GBPJPY | UP | 1543 | 1.663 | 2.000 | 46.99 | 52.75 | 0.26 |
| GBPJPY | DOWN | 1462 | 0.495 | 2.000 | 52.12 | 47.74 | 0.14 |
| AUDJPY | UP | 1579 | -0.262 | 0.500 | 48.32 | 51.36 | 0.32 |
| AUDJPY | DOWN | 1421 | -0.060 | 1.000 | 51.86 | 48.06 | 0.07 |
| EURAUD | UP | 1457 | 0.510 | 0.200 | 49.49 | 50.38 | 0.14 |
| EURAUD | DOWN | 1548 | 1.004 | 1.050 | 51.03 | 48.84 | 0.13 |
| GBPAUD | UP | 1438 | 1.624 | 0.750 | 49.44 | 50.49 | 0.07 |
| GBPAUD | DOWN | 1559 | 1.156 | 0.700 | 50.93 | 48.81 | 0.26 |

Tokyo==0別件数: USDJPY=9, EURJPY=7, GBPJPY=2, AUDJPY=6, EURAUD=2, GBPAUD=4。
割合の分母は各UP/DOWN全日。London==0はneutralとして分母に残す。上昇側・下落側の後付け採用はしない。

## Family (scale-free, pair equal weight)
| Family | Primary mean r | Robustness mean r | Use |
| --- | --- | --- | --- |
| JPY | -0.010488 | -0.016314 | DESCRIPTIVE_ONLY |
| AUD-cross | -0.051987 | -0.069550 | DESCRIPTIVE_ONLY |
| All-6 | -0.024321 | -0.034060 | DESCRIPTIVE_ONLY |

raw pipsをpoolしない。Familyに正式支持判定を付けず、個別gateにも用いない。

## Data / coverage
候補平日は各pair/methodで3050日。既存56本manifest中の対象48本すべてでSHA256・行数・raw始終時刻一致。
時刻調整0件、重複UTCなし。不足endpointを補間しない。
| Pair | Primary valid / excluded | Robustness valid / excluded |
| --- | --- | --- |
| USDJPY | 3007 / 43 | 3007 / 43 |
| EURJPY | 3007 / 43 | 3007 / 43 |
| GBPJPY | 3007 / 43 | 3007 / 43 |
| AUDJPY | 3006 / 44 | 3006 / 44 |
| EURAUD | 3007 / 43 | 3007 / 43 |
| GBPAUD | 3001 / 49 | 3001 / 49 |

日付は2015-01-01〜2026-09-09 inclusive。9/9は元データがMT500:00までで必要endpointがなく除外。
期間別coverage・endpoint別除外数はcoverage.csv。複数欠損理由は重複計上し得る。
日次assignmentとexclusionsはlocal/Colab保存、GitHubへはpublication_manifestのhash/件数を公開する。

## Validation
- 合成unit tests: 8/8 PASS（DST開始/終了、Helsinki/UTC/JST/London、exact timestamp、欠損の独立coverage、未来バー改変不変、pip、OLS、Holm、bootstrap CI、gate分母）。
- 72セルの独立OLS照合、および各セル3反復を週内日次行の実複製で照合: PASS。
- 合成データ5000反復の全CI/p照合: PASS。
- 実USDJPY ALL Primaryの5000反復を独立lstsqで再計算しCI/p一致: PASS。
- 別経路math.fsum回帰、全gate、Holm、方向表、coverage、元CSV行/Decimal audit: 932 checks PASS。
- 6pair×夏冬×UP/DOWN=24代表日、96 endpointを元CSVから再読込。Open・時刻・pipsをDecimal再計算し表を確認済み。
- 373既存baseファイルのblob無変更。mainとVolatility Phase5 branch SHAも開始時から不変。

## Limits / next phase
週clusterは週を跨ぐ依存と構造変化を完全には扱わない。中心化bootstrap p値は近似検定で、percentile CIとの双対性は仮定しない。
Robustness XとYはLondon08の同一Openを境界として共有する。因果関係や実行可能な売買利益の証明ではない。
Phase 2候補: **なし**。Q assignment、percentile、AlignedLondonReturn、Q1〜Q5/Q5−Q1は計算も閲覧もしていない。
**Phase 2 formal gateはPENDING**。将来Phase 2を行う場合も、実データのassignment/resultを一切計算・閲覧する前に別PlanでHard Gate/補助条件/多重比較/非対称性を事前固定する。
今回の不支持を理由にPhase 1の基準を緩めたり、未支持pairをPhase 2へ進めたりしない。

## Files / protection
新規Plan/Result: docs/75_tokyo_london_phase1_plan.md、docs/76_tokyo_london_phase1_result.md。
新規実装: src/research/tokyo_london_phase1.py。
新規検証: tests/test_tokyo_london_phase1.py、tests/verify_tokyo_london_phase1.py。
新規入力固定: research_inputs/tokyo_london_phase1_expected_manifest.csv。
Notebook: notebooks/tokyo_london_phase1.ipynb（/content保存、Drive保存default OFF、今回の結果snapshotを併記）。
CSV: results/tokyo_london_phase1/のpair_summary、period_summary、direction_summary、family_summary、coverage、multiple_comparison、run_record、input_audit、validation、independent_validation、manual_audit、bootstrap_spot_check、completion_validation、publication_manifest（共通prefix tokyo_london_phase1_）。
Volatility Phase5 / EA / VPS / SET / live / 既存研究成果物は変更なし。取引作成・最適化・Money Simulation・Portfolio追加なし。
