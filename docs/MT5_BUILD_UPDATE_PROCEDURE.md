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

---

# 8. LiveUpdateによる自動Build更新

MT5にはLiveUpdate機能があり、新しいBuildが配信された場合、更新ファイルがバックグラウンドで自動ダウンロードされる。

通常のMT5設定画面には、以下のような運用設定はない。

- 自動更新をOFFにする
- 手動更新のみに固定する
- 特定Buildに固定する

そのため、本番VPSでは「MT5を再起動する」という操作を、単なる再起動ではなく「Build更新が適用される可能性がある操作」として扱う。

---

## 更新の基本的な流れ

例：

LiveUpdate

↓

new version build XXXX is available

↓

更新ファイルを自動ダウンロード

↓

downloaded successfully

↓

MT5再起動

↓

新Buildで起動


更新ファイルがダウンロード済みでも、MT5を再起動していない端末では旧Buildのまま稼働している場合がある。

そのため、同じOANDA MT5環境でも、VPSとDELLでBuild番号が異なることがある。

---

## MT5再起動前の確認

本番VPSのMT5を再起動する前に、Journal（操作履歴）を確認する。

特に以下のLiveUpdateログを確認する。

- new version build XXXX is available
- downloaded successfully

これらが存在する場合、次回MT5起動時にBuildが変更される可能性がある。

再起動前に現在のBuild番号を記録する。

例：

2026-08-22
VPS MT5 Build 6116
LiveUpdate Build 6140 downloaded successfully

---

## MT5再起動後の確認

再起動後、必ず以下を確認する。

1. MT5の「ヘルプ → バージョン情報」を開く
2. Build番号を確認する
3. 再起動前のBuild番号と比較する
4. Journalの起動ログを確認する

起動ログ例：

OANDA MetaTrader 5 x64 build 6140 started for OANDA Corporation


Buildが変更されていた場合は、通常のMT5再起動ではなく「MT5 Build更新」として扱う。

---

## Build変更時の運用ルール

Buildが変更された場合は、以下を重点確認する。

- EA初期化正常
- Input設定正常
- Lot計算正常
- WeeklyBase正常
- Entry正常
- Exit正常
- CTrade戻り値
- ResultRetcode
- reconciliation動作
- 想定外注文なし

特に、最初の実エントリーと最初の時間決済ログを確認する。

---

## 本番運用中のBuild記録

最低でも週1回、週初にVPSのMT5 Build番号を記録する。

例：

2026-08-24
VPS Build 6140

先週とBuild番号が異なる場合、その週はBuild変更後の確認期間として扱い、Entry / Exit / Lot / WeeklyBaseログを重点的に確認する。

---

## DELLとVPSのBuild差異

DELLデモとVPS実口座は、それぞれ独立したMT5環境として扱う。

LiveUpdateファイルが両方にダウンロードされていても、MT5の再起動タイミングが異なれば、異なるBuildで稼働する場合がある。

そのため、

DELL Build正常

＝

VPS Buildでも同じ挙動

とは判断しない。

Build番号は必ず端末ごとに確認する。

---

# 9. 2026-08 Build更新実例

2026-08-22、以下を確認。

VPS：

- Build 6116からBuild 6140へ更新
- LiveUpdateによりBuild 6140を自動ダウンロード
- MT5再起動後にBuild 6140で起動

DELLデモ：

- Build 6140更新ファイルはダウンロード済み
- MT5再起動前のためBuild 6090のまま稼働

この実例から、本番VPSでは「再起動時にBuildが変更される可能性」を常に考慮する。

また、Build変更前後でEA挙動が変化する可能性があるため、Build番号とEAログをセットで記録する。

2026-08-24時点：

VPS Build 6140では、以前Build 6116で発生していた

Returned=false
ResultRetcode=0
unknown retcode 0

ではなく、

Returned=true
ResultRetcode=10009

による通常Entry成功を複数回確認。

ただし、Build変更との因果関係は現時点では確定していないため、「Build 6140で修正された」とは断定せず、継続監視する。
