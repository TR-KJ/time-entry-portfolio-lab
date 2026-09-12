# Strategy Selection / Portfolio Pruning（戦略選択／ポートフォリオ整理）のIS結果

状態: IS完了／候補固定済み／OOS未閲覧

IS実行日: 2026-09-11 JST

ブランチ: `research/strategy-selection-validation`

分析プログラム: `src/research/strategy_selection_analysis.py` v1.0.0

分析元コミット:

```text
c95a6b78eb8bd6f11e8f958a60aa91095069134d
```

候補固定コミット:

```text
1c265a7e4bd156b1abb8a99e84626047d378be63
```

## 1. 入力の採用確認

プログラムは採用済みのDaily Stopなしベースライン・トレードログを読み込み、結果計算前に固定入力に関するすべてのチェックへ合格した。

- ベースライン・トレードログSHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`
- グループ所属表SHA-256: `aad041b8cbc03611cbe535060c4887f30f9341c5d0f0010158f1d923e830756d`
- 全ベースライン行数確認: 16,298
- 戦略数確認: 28
- IS行数: 9,756
- IS期間: JSTのEntryTimeを基準に2015-01-01から2021-12-31
- ISベースラインTotal R: 768.488273R
- OOS1/OOS2: 計算・表示ともに未実施

M1データは読み込まず、ベースライン・トレードログも再計算していない。

## 2. 単体健康診断とLeave-One-Out結果

ISにおいて、明確な負の限界貢献について事前定義した2条件を両方満たした戦略は1つだけだった。

| 順位 | 戦略 | 単体Total R | プラス年数 | マイナス年数 | LOO Delta Total R | 安定した負の貢献 |
|---:|---|---:|---:|---:|---:|---|
| 1 | `10_AJ_SatA` | -0.444000 | 2 | 5 | +0.444000 | はい |

他のすべての戦略はISの単体Total Rがプラスだったため、利益目的の個別停止候補には該当しなかった。

## 3. リスク指標の観察

`10_AJ_SatA`を除外するとISのTotal RとPFは増加したが、すべてのリスク指標が改善したわけではない。

| 指標 | ベースライン | `10_AJ_SatA`除外 | Delta |
|---|---:|---:|---:|
| Total R | 768.488273 | 768.932273 | +0.444000 |
| PF | 1.372171 | 1.377253 | +0.005082 |
| Max DD R | 27.540956 | 27.854956 | +0.314000（悪化） |
| Worst Day R | -12.000000 | -12.000000 | 0.000000 |
| Worst Week R | -14.455836 | -14.563836 | -0.108000（悪化） |

固定済みの主判断基準はTotal Rであるため、この混合したリスク結果だけを理由に候補から外さない。ただし、採用が確定したわけでもなく、引き続きOOSでの確認が必要である。

## 4. 事前定義グループ仮説

8つのグループはいずれも、除外するとISのTotal Rが減少した。`P3_MINUS_GROUP`に該当するグループはなかった。

| グループ | 戦略数 | グループTotal R | 除外時Delta Total R |
|---|---:|---:|---:|
| `TP_LT_SL` | 5 | +72.977280 | -72.977279 |
| `CHINA_DEMAND` | 4 | +116.723611 | -116.723611 |
| `TP_NONE` | 3 | +169.724000 | -169.724000 |
| `OVERNIGHT` | 11 | +347.675387 | -347.675386 |
| `SHORT` | 13 | +383.654108 | -383.654108 |
| `LONG` | 15 | +384.834165 | -384.834165 |
| `AUD_RELATED` | 16 | +410.429665 | -410.429664 |
| `JPY_RELATED` | 17 | +465.009876 | -465.009875 |

グループTotal Rと符号を反転したDeltaの間にある100万分の1R未満の差は、CSV表示時の丸めだけによるもの。丸め前の照合チェックには合格している。

## 5. 固定済み候補ポートフォリオ

1回限りのOOS確認へ進めるのは、次のポートフォリオだけである。

| 候補ID | 除外 | ISトレード数 | IS Total R | Delta Total R | IS Max DD R |
|---|---|---:|---:|---:|---:|
| `P0_BASELINE` | なし | 9,756 | 768.488273 | 0.000000 | 27.540956 |
| `P1_MINUS_TOP1` | `10_AJ_SatA` | 9,517 | 768.932273 | +0.444000 | 27.854956 |

事前定義した他の候補枠は作成しない。

- `P2_MINUS_STABLE_TOP2`: 安定した負の候補が1戦略しかない。
- `P3_MINUS_GROUP`: 除外によってTotal Rが改善するグループがない。
- `P4_PAIR_CHECK`: 明確な負の候補が1戦略しかない。

しきい値は緩和せず、追加の組み合わせ探索も行っていない。

## 6. 出力ファイル

- `results/strategy_selection/strategy_selection_group_membership.csv`
- `results/strategy_selection/strategy_selection_health_is.csv`
- `results/strategy_selection/strategy_selection_leave_one_out_is.csv`
- `results/strategy_selection/strategy_selection_group_hypotheses_is.csv`
- `results/strategy_selection/strategy_selection_candidates_frozen.csv`

候補CSVには`OOSViewed=False`を記録している。候補固定コミットを記録する前にOOS1を実行してはならない。OOS1を確認した後は、候補やルールを変更してはならない。OOS2は最終ホールドアウトとして残し、最後に確認する。

EA、VPS、SET、live運用コードおよび稼働設定は変更していない。
