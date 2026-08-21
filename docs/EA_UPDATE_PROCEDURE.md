# EA_UPDATE_PROCEDURE

## EA更新手順書

作成日：2026-08-21

---

# 1. 目的

Step9.2.4 EA更新時に、安全にEX5を差替えるための手順。

目的：

- 古いEA混入防止
- 設定ミス防止
- VPS事故防止

---

# 2. 基本ルール

EA更新は必ず以下の流れで行う。

開発

↓

GitHub保存

↓

DELLでEX5作成

↓

ハッシュ確認

↓

デモ確認

↓

0.01実口座確認

↓

VPS更新

---

# 3. 更新前確認

確認：

- 保有ポジション
- 未決済注文
- EA停止可能状態


ポジション保有中の場合：

更新影響を確認してから実施する。

---

# 4. EX5作成

作業場所：

DELL MetaEditor


確認：

- 0 errors
- 0 warnings


作成ファイル：

Step9.2.4 EX5

---

# 5. SHA256確認

DELL側EX5のハッシュ取得。

目的：

- 正しいEX5確認
- コピー事故防止
- 古いファイル混入防止

---

# 6. VPSへコピー

手順：

旧EX5確認

↓

新EX5配置

↓

VPS側ハッシュ確認


DELLとVPSのSHA256一致を確認する。

---

# 7. SET確認

使用SET：

step9_2_3_live_vps_minilot_verified.set


確認：

- FixedLot
- LotMode
- Risk設定
- TestMode OFF
- Mock日時 OFF

---

# 8. VPS再セット

手順：

1. EA削除

2. 新EAセット

3. SET読み込み

4. Experts確認


確認：

- 初期化成功
- 異常ログなし

---

# 9. 実運用復帰

順番：

デモ確認

↓

0.01実口座確認

↓

問題なし

↓

通常運用


---

# Version History

## v1.0

2026-08-21

Step9.2.4運用管理用。
