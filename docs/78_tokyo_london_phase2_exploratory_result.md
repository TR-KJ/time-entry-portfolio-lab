# Tokyo → London Phase 2 Exploratory — Result

UJ・EAはEXPLORATORY_WATCHLIST、GJはNOT_SUPPORTED。EXPLORATORY_SUPPORTEDは0通貨。
3主比較の95%CIは全て0を含み、Holm adjusted pは全て1.0。戦略化・Phase3自動進行・live変更は行わない。

## Provenance / preregistration
- Branch: research/tokyo-london-market-effect-phase2-exploratory
- Phase1 Result/base SHA: 40183638fe476a1776f6b55bbe69683e7ff558ab
- Plan SHA: 38fc59ba0b5f5b330ab0c1e8a057e20870e0efb3
- Implementation SHA: f051a0ec93b5620757d1b9d1637a118739b93032
- Result SHA: このResultとCSVを初めて追加したcommit。自己参照を避け最終報告・publication receiptへremote確認済みSHAを記録。
- Executed UTC: 2026-09-20T15:03:35.720285+00:00
- Plan commit/push→remote SHA一致確認→実装→実装commit/push→remote一致確認→初Phase2 assignment/result計算、の順序を遵守。
- 事前Planからの分析仕様変更なし。

ユーザーがPhase1結果を見た後、UJ Continuation / EA Reversal / GJ recent Continuationを選定した追加探索。
Phase1の全6通貨NOT_SUPPORTEDを維持する。元のSUPPORTEDのみ進行方針を今回の探索に限り変更したことを事前開示済み。
95%CIの水準は緩めていない。WATCHLIST条件も結果前のPlanで固定。3比較Holmは、この履歴依存の選択自体を補正しない。
2022–2026はpristine unseen holdoutではない。

## Main results
AlignedLondonReturnはUJ/GJ=sign(TokyoReturn)×LondonReturn、EA=−sign(TokyoReturn)×LondonReturn。
値はpipsの価格変化で、spread/commission/slippageを控除した取引利益ではない。
| Pair | Hypothesis | Main period | N | Q1 N / mean | Q5 N / mean | Delta Q5-Q1 | 95% CI | p raw | p Holm | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | Continuation | ALL | 2746 | 561 / +0.6260 | 564 / +0.8387 | +0.2126 | [-3.2039, 3.5119] | 0.898020 | 1.000000 | EXPLORATORY_WATCHLIST |
| EURAUD | Reversal | ALL | 2753 | 573 / +0.1571 | 525 / +2.0617 | +1.9046 | [-2.3206, 6.0136] | 0.366127 | 1.000000 | EXPLORATORY_WATCHLIST |
| GBPJPY | Continuation | RecentCombined | 1206 | 243 / +3.1617 | 253 / +6.0387 | +2.8770 | [-5.8215, 10.9595] | 0.491702 | 1.000000 | NOT_SUPPORTED |


## Fixed gates
| Pair | A CI | B Holm | C Q5 positive | D recent | E robustness | Recent check / delta | Robustness delta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | FAIL | FAIL | PASS | PASS | PASS | RecentCombined / +1.9088 | +0.2953 |
| EURAUD | FAIL | FAIL | PASS | PASS | PASS | RecentCombined / +4.9723 | +3.4616 |
| GBPJPY | FAIL | FAIL | PASS | FAIL | PASS | RecentB / -4.9381 | +4.2720 |

A: 主Delta>0かつ95%CI下限>0。B: 主比較Holm p<=.05。C: 主Q5 mean>0。
D: UJ/EAはRecentCombined Delta>0、GJはRecentB Delta>0。E: 主periodのRobustness Delta>0。全て必要sample条件付き。
全PASSでEXPLORATORY_SUPPORTED。主Delta>0かつCDE通過だがA/B不通過ならWATCHLIST。
WATCHLISTは正式支持や自動Phase3進行ではなく、観察候補にとどめるラベル。

## Interpretation
- UJ: 全期間Deltaは+0.213 pipsと小さく、Q5 meanはQ4より低い。近年DeltaとRobustnessは正だが、 magnitudeとともに効果が増えるという明確な証拠は得られなかった。
- EA: 全期間Delta+1.905、RecentCombined+4.972、Robustness+3.462 pips。Q5が強い形の点推定はあるが、主Delta CIは0を含む。Q1〜Q5の単調増加でもなく、探索的継続観察に留まる。
- GJ: RecentCombined Delta+2.877、2026は+14.538 pipsだが、RecentB 2024–2025は−4.938 pips。事前固定の安定性D不通過。2026だけを取り出して採用しない。構造的な方向転換を証明したとは言えない。

## Quintile shape — main period Primary
| Pair | Q1 | Q2 | Q3 | Q4 | Q5 | Spearman(5 means) | positive adjacent /4 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | +0.6260 | -0.5080 | -1.1879 | +2.0513 | +0.8387 | 0.500 | 1 |
| EURAUD | +0.1571 | -0.7186 | +0.5989 | -1.4046 | +2.0617 | 0.300 | 2 |
| GBPJPY | +3.1617 | +0.4489 | -1.3508 | -2.2385 | +6.0387 | 0.000 | 1 |

Spearmanは5群meanの順位相関のみ、p値なし。隣接差・単調性は正式gateにしていない。

## Primary period stability
| Pair | Period | N | Q1 N | Q5 N | Delta | 95% CI | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | Historical | 1543 | 326 | 294 | -1.3068 | [-4.4303, 1.9023] | OK |
| EURAUD | Historical | 1547 | 335 | 282 | -0.3529 | [-6.5733, 5.6609] | OK |
| GBPJPY | Historical | 1547 | 336 | 308 | -0.8998 | [-8.4804, 6.5746] | OK |
| USDJPY | RecentA | 514 | 83 | 134 | +4.6362 | [-4.7541, 13.6707] | OK |
| EURAUD | RecentA | 517 | 93 | 124 | +3.8637 | [-5.9280, 13.3356] | OK |
| GBPJPY | RecentA | 517 | 96 | 120 | +5.7660 | [-6.8909, 18.4361] | OK |
| USDJPY | RecentB | 514 | 97 | 113 | +1.9344 | [-8.2197, 12.4217] | OK |
| EURAUD | RecentB | 513 | 110 | 90 | +6.7204 | [-1.9010, 15.6159] | OK |
| GBPJPY | RecentB | 514 | 101 | 103 | -4.9381 | [-19.5894, 8.7321] | OK |
| USDJPY | Monitor2026 | 175 | 55 | 23 | +2.0394 | [-19.9496, 20.8679] | INSUFFICIENT_SAMPLE |
| EURAUD | Monitor2026 | 176 | 35 | 29 | +3.9218 | [-7.1437, 14.2786] | INSUFFICIENT_SAMPLE |
| GBPJPY | Monitor2026 | 175 | 46 | 30 | +14.5377 | [-3.1840, 32.9803] | OK |
| USDJPY | RecentCombined | 1203 | 235 | 270 | +1.9088 | [-4.2239, 7.9425] | OK |
| EURAUD | RecentCombined | 1206 | 238 | 243 | +4.9723 | [-0.5072, 10.4529] | OK |
| GBPJPY | RecentCombined | 1206 | 243 | 253 | +2.8770 | [-5.8215, 10.9595] | OK |
| USDJPY | ALL | 2746 | 561 | 564 | +0.2126 | [-3.2039, 3.5119] | OK |
| EURAUD | ALL | 2753 | 573 | 525 | +1.9046 | [-2.3206, 6.0136] | OK |
| GBPJPY | ALL | 2753 | 579 | 561 | +0.8468 | [-4.8046, 6.4330] | OK |

UJ 2026 Q5=23日、EA 2026 Q5=29日で最低30日に不足。2026の表示値は記述統計のみ。
全期間の最初252 valid日をrank履歴として除外。HistoricalとALLの解析開始が2015-01-01になるわけではない。
GJの2022以降にはそれ以前の252日履歴を引き継ぎ、periodごとにrankをresetしていない。

## UP / DOWN diagnostics — main period Primary
| Pair | Tokyo | Q1 N | Q1 mean | Q5 N | Q5 mean | side Delta | LOW_SAMPLE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | UP | 273 | +1.3337 | 271 | +0.2461 | -1.0876 | False |
| USDJPY | DOWN | 288 | -0.0448 | 293 | +1.3867 | +1.4315 | False |
| EURAUD | UP | 285 | -0.8670 | 262 | -1.4466 | -0.5795 | False |
| EURAUD | DOWN | 288 | +1.1705 | 263 | +5.5567 | +4.3862 | False |
| GBPJPY | UP | 119 | +6.3563 | 124 | +10.3677 | +4.0114 | False |
| GBPJPY | DOWN | 124 | +0.0960 | 129 | +1.8775 | +1.7816 | False |

各side別のQ5-Q1は点推定のみ。CI/p/正式支持判定なし。上昇側だけ・下落側だけを後付け採用しない。
全period/method/side/Qのmean、median、件数はdirection_summary.csv。

## Coverage (ALL)
| Pair | Method | Candidate | Endpoint valid | Missing | Rank burn-in | Neutral after rank | Eligible |
| --- | --- | --- | --- | --- | --- | --- | --- |
| USDJPY | Primary | 3050 | 3007 | 43 | 252 | 9 | 2746 |
| USDJPY | Robustness | 3050 | 3007 | 43 | 252 | 2 | 2753 |
| EURAUD | Primary | 3050 | 3007 | 43 | 252 | 2 | 2753 |
| EURAUD | Robustness | 3050 | 3007 | 43 | 252 | 6 | 2749 |
| GBPJPY | Primary | 3050 | 3007 | 43 | 252 | 2 | 2753 |
| GBPJPY | Robustness | 3050 | 3007 | 43 | 252 | 2 | 2753 |

Q1〜Q5は直前252 valid日とのmidrank percentile。Q内の日数は等しくなくてよい。
Tokyo==0は参照履歴とQ割当に残し、Aligned解析から除外。London==0は0として含める。
必要endpointの補間なし。Primary/Robustnessはそれぞれ自身のX・rank・方向を使用。

## Validation
- 24 raw CSVのSHA256/行数/raw始終一致、不正OHLC・重複UTCなし。時刻調整0。
- Phase1 daily SHA256 d6a243fa93e4ca19af68caeee84e034acb8dc2382a1c15b510c61ce5ff1f1236一致。
- 元CSV再抽出の3pair X/Y、4 endpoint時刻/価格、valid flagsがPhase1日次CSVと一致。
- 新Phase2 synthetic tests 8/8 PASS。再利用Phase1 timezone/DST/exact timestamp/pip等tests 8/8 PASS。
- 全日rankを別経路sorted-reference/searchsortedで照合。全Q/Delta/coverage/UP-DOWN/全gate/Holm等、独立51,763 checks PASS。
- sample条件とshape/Spearmanを別計算で72 checks PASS。
- 各36 period×pair×methodセルで最初3 bootstrap反復を日次行実複製で照合。
- UJ ALL Primary全5000 bootstrap反復を独立RNG抽出・行複製で再計算しCI/p一致。
- 3pair×2method×5Qの初該当日30例、および2022境界6例の参照252日・rank・Q・Decimal価格差を照合し表を確認。
- ローカル実行ソース、テスト、Notebook、manifest等8ファイルがremote blobと一致。
- 既存base 394ファイルの変更・削除0。main / Volatility Phase5 / Phase1 branch SHA不変。

## Limits / disposition
週bootstrapは観測済みQ割当に条件付ける。252日rankの推定や週を跨ぐ依存・非定常性を完全には反映しない。
GJの2022境界と対象3通貨はPhase1結果を見て選択済み。今回のp値を独立確証研究の証拠と解釈しない。
本Planで探索判定は事前固定済み。結果後のCI緩和・Q境界変更・期間変更・片側採用は行っていない。
Phase1 verdictは不変。Phase3へ進める探索的支持pairなし。UJ/EAはWATCHLISTに記録するだけで、監視automationや新戦略は作っていない。

## Created files
Plan/Result: docs/77_tokyo_london_phase2_exploratory_plan.md / docs/78_tokyo_london_phase2_exploratory_result.md。
Implementation: src/research/tokyo_london_phase2.py。
Tests: tests/test_tokyo_london_phase2.py / tests/verify_tokyo_london_phase2.py。
Input manifest: research_inputs/tokyo_london_phase2_expected_manifest.csv。
Notebook: notebooks/tokyo_london_phase2.ipynb（/content CSV保存、Drive save初期OFF、確定結果snapshot）。
results/tokyo_london_phase2/のpair_summary、quintile_summary、period_summary、shape_summary、direction_summary、coverage、multiple_comparison、input_audit、manual_audit、validation、independent_validation、supplemental_validation、run_record、publication_manifest（共通prefix tokyo_london_phase2_）。
daily_assignmentはlocal/Colabのみ。GitHubにはSHA256/rowsを公開。
Volatility Phase5 / EA / SET / VPS / live / 既存研究成果物は全て変更なし。
