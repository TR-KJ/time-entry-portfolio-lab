# Step9.2.4 注文結果診断・約定照合

## 1. 目的

VPSのMT5 Build 6116で、`trade.Buy / trade.Sell` 後に実際は約定しているにもかかわらず、EA側だけが `false / ResultRetcode=0 / unknown retcode 0` を返す事象へ対応する。

Step9.2.3の28戦略、売買条件、ロット計算、イベントフィルタ、GA_B3の8月停止、決済処理は変更しない。

## 2. 対象ファイル

```text
src/EA/time_entry_step9_2_4_trade_result_reconcile_28strategies.mq5
```

ベース：

```text
src/EA/time_entry_step9_2_3_ga_b3_august_stop_28strategies.mq5
```

## 3. 変更内容

注文送信直後に、以下を1行の診断ログへ出力する。

- `trade.Buy / trade.Sell` の戻り値
- `ResultRetcode`
- `ResultRetcodeDescription`
- `ResultOrder`
- `ResultDeal`
- `GetLastError`
- Symbol / Magic / Direction / RequestedLot

`InpPrintTradeResultDiagnostics=true` が既定値。不要時のみ `false` にできる。

通常の `result=true` かつ成功Retcode（`PLACED / DONE / DONE_PARTIAL`）は、Step9.2.3と同じ成功処理を通る。

それ以外（`result=false`、`ResultRetcode=0`、非成功Retcode等）は、注文直前時刻以降に新しく生成された以下の証拠を照合する。

1. 実ポジション
2. `ResultDeal` または取引履歴内の新しいエントリー約定

照合条件：

- 同一Symbol
- 同一Magic
- 同一方向（BUY / SELL）
- 注文直前時刻以降（時刻精度差として2秒だけ許容）
- 実Lotがブローカーの最小・最大Lot内
- 実Lotが要求Lotを半Lot Stepより大きく超えない
- 約定の場合は `DEAL_ENTRY_IN`

条件に一致するポジションまたは約定を確認できた場合だけ、`entry reconciled success` として `MarkEnteredToday()` を実行する。

確認できない場合は、従来どおり `entry failed` とし、`MarkEnteredToday()` は実行しない。

## 4. ログ例

診断ログ：

```text
[Step9.2.4 Trade Result 1_EJ_Log1] Side=BUY, Returned=false, ResultRetcode=0, ResultRetcodeDescription=unknown retcode 0, ResultOrder=0, ResultDeal=0, GetLastError=0, Symbol=EURJPY, Magic=10001, Direction=1, RequestedLot=0.01
```

実ポジションで救済した場合：

```text
BUY entry reconciled success. Symbol=EURJPY, Magic=10001, RequestedLot=0.01, ActualLot=0.01, Evidence=POSITION, Ticket=...
```

照合できない場合：

```text
BUY entry failed. Symbol=EURJPY, Retcode=0, unknown retcode 0, Reconcile=no_matching_position_or_deal
```

## 5. 検証手順

1. MetaEditorでStep9.2.4をコンパイルし、`0 errors, 0 warnings` を確認する。
2. デモ口座でBUY・SELL各1回を実行し、診断ログと通常の `entry success` を確認する。
3. 存在しないSymbol、異常Lot、取引禁止時間などの失敗では、照合成功にならないことを確認する。
4. VPS Build 6116の実口座で固定Lot `0.01` を1戦略だけ有効にして試験する。
5. `false / ResultRetcode=0` が再現した場合、実ポジションまたは取引履歴と、`Evidence=POSITION` または `Evidence=DEAL` のTicket・Magic・Lot・方向が一致することを確認する。
6. 救済成功後、同日の再エントリーが `already entered today` で抑止されることを確認する。
7. 約定証拠がない失敗では `entry failed` のままであることを確認する。
8. GA_B3の8月停止と既存イベントフィルタの代表ケースを再確認する。

実口座試験では、DELLとVPSを同時にアルゴリズム取引ONにしない。

## 6. 現時点の検証範囲

このリポジトリ作業環境にはMetaEditor / MT5がないため、構文の静的確認とStep9.2.3との差分確認までを実施する。最終的な `0 errors, 0 warnings` とBuild 6116での実約定照合は、上記手順でWindows側にて確認する。
