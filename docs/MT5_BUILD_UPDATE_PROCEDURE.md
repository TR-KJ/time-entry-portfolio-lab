# MT5_BUILD_UPDATE_PROCEDURE

## MT5 Build更新手順書

作成日：2026-08-21

---

# 1. 目的

MT5 Build更新によるEA挙動変化を安全に確認するための手順。

今回確認した問題：

- Build6093
- Build6116

でCTrade戻り値挙動差異を確認。

---

# 2. 基本方針

MT5更新後、いきなり本番継続しない。

必ず検証する。

Build更新

↓

デモ確認

↓

0.01実口座確認

↓

通常運用

---

# 3. 更新前準備

保存：

- EA EX5
- SHA256
- SET
- GitHub状態


記録：

- 更新前Build番号
- 更新日時

---

# 4. Build更新後確認

確認：

- MT5起動
- 口座ログイン
- EA読込
- Expertsログ


---

# 5. 動作確認

確認項目：

## Entry

- BUY
- SELL
- reconciliation


## Exit

- SL決済
- TP決済
- 時間決済


## Magic

- 複数戦略
- 複数通貨


---

# 6. unknown retcode 0確認

Build差異により、

Returned=false

ResultRetcode=0

unknown retcode 0

が発生する場合がある。


判断：

注文失敗とは限らない。


Step9.2.4では、

Entry：

Position確認

↓

Deal確認

↓

reconciliation success


Exit：

Position消失確認

↓

Deal確認

↓

Time exit reconciled success

で判断する。

---

# 7. 本番復帰条件

以下を満たすこと。

- Entry正常
- Exit正常
- reconciliation正常
- 想定外注文なし
- ログ異常なし


---

# Version History

## v1.0

2026-08-21

Build差異対策記録。
