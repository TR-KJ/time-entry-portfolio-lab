# LIVE_OPERATION_MANUAL_v1.0

## Step9.2.4 本番運用手順書

作成日：2026-08-21

---

# 1. 目的

本ドキュメントは、Step9.2.4 EAを本番環境で安全運用するための手順を定義する。

対象：

- VPS実口座MT5
- DELL実口座MT5（監視用）
- Step9.2.4 EA
- OANDA MT5環境

目的：

- EA停止事故防止
- MT5更新時の確認
- VPS再起動後の復旧
- EA更新時の安全確認
- 本番環境の再現性確保

---

# 2. 本番環境構成

## VPS

役割：
EA実運用

設定：

- MT5実口座
- Step9.2.4 EA稼働
- アルゴリズム取引 ON
- 自動売買担当


## DELL

役割：
監視・緊急確認用

設定：

- MT5実口座
- Step9.2.4 EA配置
- アルゴリズム取引 OFF

注意：

同一実口座でVPSとDELLを同時にアルゴリズム取引ONにしない。

---

# 3. 通常運用開始手順（月曜日）

## VPS確認

1. VPSへ接続

2. MT5起動確認

3. 口座ログイン確認

4. EAチャート確認

5. アルゴリズム取引確認


正常状態：

VPS
- アルゴリズム取引 ON

DELL
- アルゴリズム取引 OFF

---

# 4. EA起動確認

Expertsログで以下を確認する。

確認項目：

- EA初期化成功
- FixedLot確認
- LotMode確認
- TestMode OFF確認
- Mock日時 OFF確認
- Event Filter設定確認


正常設定：

- FixedLot = 0.01
- LotMode = 0
- TestMode = false
- UseMockJstDateTime = false

---

# 5. EAハッシュ確認

本番投入前にEX5ファイルのSHA256を確認する。

確認対象：

MQL5
Experts
Step9.2.4 EX5

確認目的：

- 古いEX5混入防止
- VPSとDELLの差異防止
- 意図しない更新防止

確認方法：

DELL側で確認したSHA256とVPS側SHA256が一致すること。

---

# 6. SET確認

現在使用するSET：

step9_2_3_live_vps_minilot_verified.set


確認項目：

- FixedLot = 0.01
- LotMode = 0
- MaxAutoLot = 0.01
- TestMode = false
- UseTestTimes = false
- UseMockJstDateTime = false


初期本番運用ではRiskPercentPerTradeを低く設定する。

---

# 7. VPS再起動時の手順

## VPS再起動後

確認順：

1. VPS接続

2. MT5起動確認

3. 口座ログイン確認

4. EAチャート確認

5. アルゴリズム取引確認

6. Expertsログ確認

7. 最初のエントリーまで監視


異常時：

- EA停止
- 保有ポジション確認
- 未決済注文確認
- ログ保存
- 原因確認後復旧

---

# 8. MT5 Build更新時

MT5アップデート後は即本番継続しない。


手順：

MT5 Build更新

↓

デモ確認

↓

0.01実口座確認

↓

問題なし

↓

通常運用復帰


確認項目：

- エントリー動作
- 決済動作
- reconciliation動作
- Magic照合
- 複数注文処理

---

# 9. EA更新時

EX5差替え手順：

旧EA停止

↓

保有ポジション確認

↓

未決済注文確認

↓

新EX5配置

↓

SHA256確認

↓

SET読み込み

↓

Expertsログ確認

↓

デモ確認

↓

0.01実口座確認

↓

本番復帰


注意：

VPS側でMQ5から再コンパイルしない。

基本はDELLで作成したEX5をVPSへコピーする。

---

# 10. Step9.2.4 既知仕様

## unknown retcode 0対応

Build差異により以下が発生する場合がある。

Returned=false

ResultRetcode=0

unknown retcode 0


これは注文失敗とは限らない。


Step9.2.4ではCTradeの戻り値だけで判断せず、実際の口座状態を確認する。

---

# 11. Entry reconciliation

確認フロー：

注文送信

↓

CTrade結果確認

↓

Position確認

↓

Deal確認

↓

reconciliation success


確認済み：

- BUY entry
- SELL entry
- Evidence=POSITION
- Evidence=DEAL_ADD
- 複数Magic同時注文

---

# 12. Exit reconciliation

確認フロー：

決済注文送信

↓

CTrade結果確認

↓

Position消失確認

↓

決済Deal確認

↓

Time exit reconciled success


確認済み：

- PositionClose正常成功
- retcode=0発生時の救済
- pending後の非同期確認
- 複数Magic決済

---

# 13. 初期本番運用方針

開始設定：

RiskPercentPerTrade

0.25〜0.5%


期間：

2〜4週間


確認項目：

- 約定漏れなし
- 決済漏れなし
- ロット計算正常
- VPS安定稼働
- 週次複利更新正常
- 想定外ポジションなし
- EA停止なし


問題なしの場合：

RiskPercentPerTrade

1.0%

へ移行する。

---

# 14. 運用記録

毎週記録：

- 週初残高
- 週末残高
- 利益率
- 最大DD
- 取引件数
- EAログ異常有無
- VPS状態
- MT5 Build番号

---

# 15. 緊急停止基準

以下の場合はアルゴリズム取引をOFFにする。

- EAが想定外注文を出した
- 決済されないポジションが発生した
- VPS接続異常
- MT5更新直後の異常
- EAハッシュ不一致
- ログに原因不明エラーが継続

---

# Version History

## v1.0

2026-08-21

Step9.2.4本番検証完了。

確認済：

- BUY entry reconciliation
- SELL entry reconciliation
- POSITION evidence
- DEAL_ADD evidence
- Time exit reconciliation
- 複数Magic運用


初期本番運用方針：

低リスク複利運用開始

↓

2〜4週間安定確認

↓

RiskPercentPerTrade 1.0%へ移行
