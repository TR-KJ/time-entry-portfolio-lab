# Tokyo → London Phase 2b Directional Asymmetry Exploratory — Result

## 結論

EAのTokyo DOWN Q5には正の平均（+5.914 pips）があるが、95%CIは0を含み、4セルHolm補正後も有意ではない。EA UPには同じ構造がない。結果前に固定した判定は `WEAK_DIRECTIONAL_STRUCTURE`、Phase 3 dispositionは `RESEARCH_STOP`。UJは `SHADOW_NO_STRUCTURE` / `NO_PHASE3`。Tokyo → London研究はいったん終了する。これらは売買損益や実行可能な戦略を意味しない。

Phase 1の全6通貨 `NOT_SUPPORTED`、Phase 2のEA/UJ `EXPLORATORY_WATCHLIST` とGJ `NOT_SUPPORTED` は変更していない。Phase 2bは既知のPhase 2方向結果を見た後の探索で、Recent Combinedもpristine unseen holdoutではない。

## 事前固定と実行順序

- Branch: `research/tokyo-london-phase2b-directional-asymmetry`
- Phase 1 Result SHA: `40183638fe476a1776f6b55bbe69683e7ff558ab`
- Phase 2 Result / base SHA: `046be86bffebd28dbd21a11e49fb9eb2e1d507ac`
- Plan SHA: `e4021d03b5e5f88a3b91db8d3b2ad8dc3a330b6d`（GitHub remote確認後に実装）
- Implementation SHA: `523d7de59885f71a16c5f224cedf2eda56db26fc`（GitHub remote確認後に最終実データ本計算）
- Result SHA: 出版commitのSHAをGitHub上の本書履歴で確認。
- 初回実データ計算後、独立検証器の日時列parseだけを修正して実装を再commit・remote確認した。その後、最終実装SHAを指定して再計算し、128件の独立検証を通過。Plan、統計定義、判定閾値は変更していない。

## Primary: Recent Combined 2022-01-01〜2026-09-09、Q5

| Pair | Tokyo | N | Weeks | Mean pips | Median | SD | 95% CI | Positive | Total aligned pips | raw p | Holm p | A/B/C/D/E | Cell |
|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---|
| EA | UP | 124 | 100 | -0.623 | +2.100 | 37.262 | -6.953〜+5.785 | 50.8% | -77.2 | 0.8460 | 1.0000 | FAIL/FAIL/FAIL/FAIL/FAIL | CELL_NO_STRUCTURE |
| EA | DOWN | 119 | 96 | +5.914 | +1.800 | 39.176 | -0.206〜+12.259 | 51.3% | +703.8 | 0.0632 | 0.2527 | PASS/FAIL/FAIL/PASS/PASS | CELL_WEAK |
| UJ | UP | 141 | 113 | +1.470 | +4.200 | 41.017 | -4.979〜+7.659 | 57.4% | +207.3 | 0.6385 | 1.0000 | FAIL/FAIL/FAIL/FAIL/PASS | CELL_NO_STRUCTURE |
| UJ | DOWN | 129 | 92 | +3.293 | +3.000 | 43.135 | -3.938〜+10.380 | 54.3% | +424.8 | 0.3697 | 1.0000 | PASS/FAIL/FAIL/FAIL/PASS | CELL_NO_STRUCTURE |

A=mean≥2.0 pips、B=CI下限>0、C=Holm p≤0.05、D=Recent A/Bの同方向mean>0・両期間評価可能、E=同方向Robustness Recent Combined mean>0。各セルN≥40かつcalendar weeks≥20。週cluster bootstrap 5,000回、seed `20260913`。95%CI・pの定義はPlanどおり。Total aligned pipsは価格差の合計であり、取引損益ではない。

## 方向差（UP mean − DOWN mean）

| Pair | Window | Difference pips | 95% CI |
|---|---|---:|---|
| EA | Primary | -6.537 | -15.274〜+2.486 |
| EA | Robustness | -5.051 | -15.230〜+5.257 |
| UJ | Primary | -1.823 | -10.982〜+7.277 |
| UJ | Robustness | +0.844 | -9.464〜+10.611 |

EAはDOWN側の点推定値が高いが、方向差のCIも0を含む。方向差は説明的であり、4セルの正式な多重比較familyには加えていない。片方向だけを後付けで正式採用しない。

## 期間・Window安定性

各セルは固定Q5・固定方向の平均pips。`IS` は `INSUFFICIENT_SAMPLE`（N<40または週<20）。詳細なmedian/SD/CI/rateは `tokyo_london_phase2b_period_cells.csv`。

| Pair | Window | Period | UP: N / weeks / mean | DOWN: N / weeks / mean |
|---|---|---|---|---|
| EA | Primary | Historical | 138 / 106 / -2.187 | 144 / 109 / +5.261 |
| EA | Primary | ALL | 262 / 206 / -1.447 | 263 / 205 / +5.557 |
| EA | Primary | RecentA | 59 / 48 / -3.137 | 65 / 49 / +6.058 |
| EA | Primary | RecentB | 49 / 39 / +0.429 | 41 / 37 / +7.834 |
| EA | Primary | Monitor2026 | 16 / 13 / +5.431 (IS) | 13 / 10 / -0.862 (IS) |
| EA | Primary | RecentCombined | 124 / 100 / -0.623 | 119 / 96 / +5.914 |
| EA | Robustness | Historical | 148 / 117 / +5.798 | 140 / 107 / +5.482 |
| EA | Robustness | ALL | 255 / 211 / +2.705 | 269 / 209 / +4.522 |
| EA | Robustness | RecentA | 54 / 47 / -1.030 | 67 / 55 / +1.881 |
| EA | Robustness | RecentB | 43 / 38 / -3.460 | 47 / 37 / +5.904 |
| EA | Robustness | Monitor2026 | 10 / 9 / +3.620 (IS) | 15 / 10 / +3.020 (IS) |
| EA | Robustness | RecentCombined | 107 / 94 / -1.572 | 129 / 102 / +3.479 |
| UJ | Primary | Historical | 130 / 108 / -1.082 | 164 / 119 / -0.113 |
| UJ | Primary | ALL | 271 / 221 / +0.246 | 293 / 211 / +1.387 |
| UJ | Primary | RecentA | 76 / 56 / -0.209 | 58 / 43 / +5.524 |
| UJ | Primary | RecentB | 55 / 47 / +5.231 | 58 / 40 / -2.871 |
| UJ | Primary | Monitor2026 | 10 / 10 / -6.450 (IS) | 13 / 9 / +20.838 (IS) |
| UJ | Primary | RecentCombined | 141 / 113 / +1.470 | 129 / 92 / +3.293 |
| UJ | Robustness | Historical | 142 / 114 / -1.989 | 146 / 111 / +0.954 |
| UJ | Robustness | ALL | 276 / 222 / -0.120 | 278 / 205 / +0.985 |
| UJ | Robustness | RecentA | 77 / 56 / -5.662 | 63 / 41 / +5.902 |
| UJ | Robustness | RecentB | 47 / 42 / +11.502 | 55 / 43 / -5.360 |
| UJ | Robustness | Monitor2026 | 10 / 10 / +14.490 (IS) | 14 / 10 / +4.100 (IS) |
| UJ | Robustness | RecentCombined | 134 / 108 / +1.862 | 132 / 94 / +1.018 |

EA DOWNはRecent A/Bで正（+6.058 / +7.834）かつRobustness Recent Combinedでも正（+3.479）。それでもPrimary主セルのCI下限は−0.206、Holm p=0.2527で強い構造の基準を満たさない。EA DOWNのALL期間CIが正でも、ALLは補助期間であり主判定を置き換えない。2026 Monitorの4主方向セルはすべてsample不足で、良い点推定があっても昇格なし。

## 検証と保存

- Phase 2日次入力18,300行、SHA256 `ab12358882adf6a165983710599f4524ce2b37f1409a9f9a04ad967cefdbc21d`。raw M1 16本のhash/行数/時刻を一致確認。補間・時刻変更なし。
- 日付・DST・exact endpoint・pip size・252日midrank・Q5・aligned符号・日次一意性・週bootstrap・Holm・判定を検証。Phase1/2/2bのsynthetic suite各8件PASS、独立検証128件PASS、16代表日をさらにDecimal rankとraw endpointで照合。
- 研究branchだけに新規Plan/実装/Notebook/Result/CSVを追加。main、Volatility Phase5 Dell Demo Forward、EA、SET、VPS、live、既存28/27戦略、Phase1/Phase2成果物は変更していない。Phase2bでEntry/Exit、SL/TP、Money Simulation、Portfolio追加は実施していない。
- 公開CSVは `results/tokyo_london_phase2b/`。大きな既存Phase2日次入力はGitHubに重複公開せず、固定hashと行数で参照する。Colab notebookは `/content` 保存、Drive保存初期OFF。
