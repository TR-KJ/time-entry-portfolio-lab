# Strategy Selection / Portfolio Pruning（戦略選択／ポートフォリオ整理）のOOS2最終結果

状態: OOS2最終ホールドアウト完了／P1不採用／28戦略Baseline維持

実行日時: 2026-09-12 14:44 JST

ブランチ: `research/strategy-selection-validation`

分析プログラム: `src/research/strategy_selection_oos2_analysis.py` v1.0.0

OOS2結果閲覧前の実装コミット:

```text
c6a230142394b61f51978a9e2aaa97537689ab74
```

候補固定コミット:

```text
1c265a7e4bd156b1abb8a99e84626047d378be63
```

## 1. 入力と最終ホールドアウト条件

ISで固定し、OOS1でも変更しなかった次の2候補だけを、OOS2へ一度だけ適用した。

- `P0_BASELINE`: 28戦略、除外なし
- `P1_MINUS_TOP1`: `10_AJ_SatA`だけを除外

入力チェックはすべて合格した。

- ベースライン・トレードログSHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`
- 固定候補CSV SHA-256: `ffbed6dd415ca1ec91240b8e4754e71b66ba8a7973c24e8439f9bfaa85d6277c`
- 開封前OOS1結果CSV SHA-256: `9042c26a797b0db9ac6a70938b5cad8a645af001ecd878faa0f94174025a6aa2`
- 全ベースライン行数: 16,298
- OOS2ベースライン行数: 995
- OOS2期間: JSTのEntryTimeを基準に2026-01-01から2026-09-09まで

OOS2を見る前に、候補ID、除外戦略、判定ルール、期間、しきい値を変更していない。追加候補、追加グループ、組み合わせ探索も行っていない。

## 2. OOS2単独結果

OOS2単独では、`10_AJ_SatA`除外候補のTotal RがBaselineを0.940000R上回った。

| 指標 | `P0_BASELINE` | `P1_MINUS_TOP1` | Delta（P1 - P0） |
|---|---:|---:|---:|
| Trades | 995 | 970 | -25 |
| Total R | 19.818791 | 20.758791 | +0.940000 |
| PF | 1.095529 | 1.101748 | +0.006219 |
| Win Rate | 51.457286% | 51.649485% | +0.192199pt |
| Avg R / trade | 0.019918383 | 0.021400816 | +0.001482433 |
| Avg Win R | 0.443909887 | 0.448662400 | +0.004752513 |
| Avg Loss R | -0.431316156 | -0.435942460 | -0.004626304 |
| Max DD R | 18.954206 | 18.946206 | -0.008000（改善） |
| Worst Day R | -4.579584 | -4.579584 | 0.000000 |
| Worst Week R | -5.397048 | -5.191048 | +0.206000（改善） |
| positive years | 1 | 1 | 0 |
| negative years | 0 | 0 | 0 |
| max losing streak | 11 | 11 | 0 |

## 3. OOS1＋OOS2合算結果

最終判断に用いるOOS合算では、`P1_MINUS_TOP1`のTotal RがBaselineを3.318000R下回った。

| 指標 | `P0_BASELINE` | `P1_MINUS_TOP1` | Delta（P1 - P0） |
|---|---:|---:|---:|
| Trades | 6,542 | 6,378 | -164 |
| Total R | 621.779376 | 618.461376 | -3.318000 |
| PF | 1.432989 | 1.436870 | +0.003881 |
| Win Rate | 54.509324% | 54.656632% | +0.147308pt |
| Avg R / trade | 0.095044234 | 0.096967917 | +0.001923683 |
| Avg Win R | 0.577060127 | 0.583512454 | +0.006452327 |
| Avg Loss R | -0.484486180 | -0.491379048 | -0.006892868 |
| Max DD R | 22.196976 | 21.871599 | -0.325377（改善） |
| Worst Day R | -10.880000 | -10.880000 | 0.000000 |
| Worst Week R | -12.824402 | -12.424402 | +0.400000（改善） |
| positive years | 5 | 5 | 0 |
| negative years | 0 | 0 | 0 |
| max losing streak | 15 | 15 | 0 |

## 4. 年別Total R

| 年 | `P0_BASELINE` | `P1_MINUS_TOP1` | Delta（P1 - P0） |
|---:|---:|---:|---:|
| 2022 | 163.991920 | 162.095920 | -1.896000 |
| 2023 | 160.985032 | 159.847032 | -1.138000 |
| 2024 | 129.794238 | 127.806238 | -1.988000 |
| 2025 | 147.189395 | 147.953395 | +0.764000 |
| 2026～09-09 | 19.818791 | 20.758791 | +0.940000 |
| OOS合計 | 621.779376 | 618.461376 | -3.318000 |

除外によって改善したのは2025年と2026年であり、2022年、2023年、2024年は悪化した。ISでは+0.444000R、OOS1では-4.258000R、OOS2では+0.940000Rとなり、方向は期間ごとに安定しなかった。固定ログ全期間ではP1のDelta Total Rは-2.874000Rである。

## 5. 最終判断

`P1_MINUS_TOP1`は不採用とし、正式構成は`P0_BASELINE`、すなわち28戦略・除外なしを維持する。

理由は次のとおり。

- 最優先指標のOOS合算Total Rが3.318000R減少した。
- ISの小幅な利益改善はOOS1で再現せず、OOS2単独では改善したものの期間安定性がなかった。
- PF、Max DD、Worst Weekには小幅な改善があるが、固定ルールでは利益が減る場合にDD改善だけで採用しない。
- 利益増加条件を満たす非Baseline候補が残らないため、新しい除外構成をWeekly Fixed Risk / Weekly CompoundのMoney Simulationへ進める必要はない。

この結果を受けた候補変更、しきい値変更、別戦略への差替え、追加探索、全組み合わせ探索は行わない。本検証は不採用で完了とする。

## 6. 出力記録

OOS1・OOS2・OOS合算結果CSV:

```text
results/strategy_selection/strategy_selection_oos_results.csv
```

CSV SHA-256:

```text
75ed480de1bc31599a018dbc10595175cccc34087bccba19de524af4dae5fe79
```

最終判断CSV:

```text
results/strategy_selection/strategy_selection_final_decision.csv
```

EA、VPS、SET、live運用コードおよび稼働設定は変更していない。28戦略BaselineをEAへ改めて反映する作業も発生しない。
