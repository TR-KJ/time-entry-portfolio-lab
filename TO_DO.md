#スプレッド処理方式を変更して精密検証

ただし、最終工程

現行コードでは、エントリー価格を不利にすることでスプレッドを反映している。

```python
ep = o[s_idx] + spread if is_long else o[s_idx] - spread
```

この方式は、トレードごとにスプレッド分を1回控除する考え方に近い。

今後の改善候補：

- `entry_adjust`方式として明記する
- Bid/Ask方式に変更したバージョンと比較する
- 通貨ペアごとのスプレッド設定を外部CSVで管理する

#戦略ごとの除外テスト結果を反映させるかどうかを決める（検証する）

docs/
├── 01_strategy_master_list.md
├── 02_ea_development_log.md
├── 03_ea_specification.md
├── 04_backtest_policy.md
├── 05_money_management.md
└── 06_operation_checklist.md

01_strategy_master_list.md
全ロジック一覧・仕様表

02_ea_development_log.md
EA開発の時系列ログ

03_ea_specification.md
EAの完成仕様・設計書

04_backtest_policy.md
BT条件・検証ルール

05_money_management.md
固定損失額・週次複利・リスク率

06_operation_checklist.md
デモ/リアル運用前チェックリスト
