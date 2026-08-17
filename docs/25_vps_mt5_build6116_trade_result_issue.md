# VPS MT5 Build 6116 約定結果判定問題

## 1. 概要

2026-08-17、VPS実口座でStep9.2.3の最小ロット運用を開始したところ、注文自体は正常約定しているにもかかわらず、EA側では以下のように失敗判定される現象を確認した。

```text
CTrade::OrderSend ... [unknown retcode 0]
BUY entry failed. Retcode=0, unknown retcode 0
```

一方、MT5の操作ログでは、

```text
accepted
placed for execution
order ... done
deal ... done
failed ... [Done]
```

となっており、実際のポジションは正常に生成されていた。

---

## 2. VPSでの再現

VPS実口座環境：

- OANDA Japan 実口座
- MT5 Build 6116
- Step9.2.3
- 固定ロット 0.01
- Test / Mock OFF
- VPSアルゴリズム取引 ON

以下の3戦略で同様の現象を確認した。

- `8_AJ_Core1` / AUDJPY / 08:01
- `1_EJ_Log1` / EURJPY / 13:55
- `7_GJ_Mon_Blitz` / GBPJPY / 18:02

いずれも実際には正常約定しているが、EA側では `BUY entry failed / Retcode=0` となった。

---

## 3. ファイル比較

### Step9.2.3 MQ5

DELL / VPSとも同一。

```text
SHA256
0AA277012745D7D10B7A7C406E8D941B9E9AA42DE3056A6A36DBD5FFCBDEDD3B
```

### Step9.2.1 MQ5

DELL / VPSとも同一。

```text
SHA256
B9AF1145F257AAFA0B72358330F4F3F846DA959D530CEC58FCCBE82CBDB15031
```

### Trade.mqh

DELL / VPSとも同一。

```text
SHA256
96E6781624534377FE7971CBA52CCA3D62D1B030BC10D5E4EBF3ED8C541399ED
```

---

## 4. EX5比較

### DELL実口座版

MT5 Build 6093で使用していたStep9.2.3 EX5。

```text
SHA256
778049B4D58424406643054813CB3F8D6C1658095651B9ECCA7B87D11C21C019A
```

### VPS版

VPS Build 6116でコンパイルしたStep9.2.3 EX5。

```text
SHA256
ECD40682080ED39DC1773E18188CBA370A584DAEB2925E459E8B046F61B5C238
```

---

## 5. DELL製EX5をVPSで試験

コンパイル環境の影響を切り分けるため、DELL Build 6093で作成したEX5をVPSへコピー。

VPS側でもSHA256が以下に一致することを確認した。

```text
778049B4D58424406643054813CB3F8D6C1658095651B9ECCA7B87D11C21C019A
```

VPS上では再コンパイルせず、そのEX5をそのまま使用した。

18:02の `7_GJ_Mon_Blitz` で試験した結果、再び、

```text
unknown retcode 0
BUY entry failed
```

となった。

実際のGBPJPY 0.01ロット注文は正常約定していた。

これにより、VPS側でコンパイルしたEX5固有の問題ではないことを確認した。

---

## 6. DELL Build 6093との比較

VPS実口座をOFFにし、同じOANDA実口座をDELL Build 6093で稼働。

20:56の `2_EJ_NightBlitz_20` を0.01ロットで実行。

結果：

```text
LOT FIXED. Symbol=EURJPY, Lot=0.01
BUY entry success. Symbol=EURJPY, Lot=0.01, Ask=184.596, SL=184.146, TP=185.296
```

操作ログも、

```text
accepted
placed for execution
order ... done
deal ... done
```

となり正常。

`failed ... [Done]` は発生しなかった。

---

## 7. 現時点の切り分け結果

以下は同一であることを確認済み。

- OANDA実口座
- Step9.2.3ソース
- Step9.2.1ソース
- Trade.mqh
- DELL製Step9.2.3 EX5

比較結果：

```text
DELL
MT5 Build 6093
→ 正常
→ BUY entry success

VPS
MT5 Build 6116
→ 実際には正常約定
→ EA側のみ Retcode=0 / BUY entry failed
```

AJ / EJ / GJの複数通貨で再現しているため、特定通貨固有の問題ではない。

現時点では、VPS上のMT5 Build 6116ランタイム、またはBuild 6116とVPS環境の組み合わせを主な原因候補とする。

Build 6116単体の不具合とはまだ断定しない。

---

## 8. 追加確認

21:02の `21_GA_B3` では、

```text
EVENT REJECT. Symbol=GBPAUD, Event=GA_B3_AUG_STOP
```

を確認。

Step9.2.3で追加したGA_B3の8月停止は正常に機能している。

---

## 9. 次の対応

次版を `Step9.2.4` とする。

Step9.2.4では、注文結果判定を堅牢化する。

予定：

- `trade.Buy / Sell` の戻り値を記録
- `ResultRetcode`
- `ResultRetcodeDescription`
- `ResultOrder`
- `ResultDeal`
- `GetLastError`
- Symbol / Magic / Lot
- 実ポジション・実約定の確認
- 必要に応じて `OnTradeTransaction` を利用
- CTrade側が異常値でも、実約定を確認できた場合のみ成功扱い
- 実約定確認後に `MarkEnteredToday()` を実行
- 実約定を確認できない場合は従来どおり注文失敗扱い

今後の流れ：

```text
Step9.2.4 診断＋堅牢化
↓
デモ検証
↓
VPS実口座 0.01ロット再検証
↓
複数回の正常動作確認
↓
VPS本格運用
```

最小検証EAおよびOANDA / MetaQuotesへの問い合わせは現時点では必須とせず、Step9.2.4でも不可解な挙動が残る場合に検討する。
