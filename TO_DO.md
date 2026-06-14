第1候補：V2_H1_ATR14_Pips_LTE_P70

第2候補：V2_H1_ATR14_Pips_LTE_P75

第3候補：V2_Range24hPips_LTE_P70

保留：V2_Range24hPips_LTE_P85

除外寄り：Filter v1系

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
