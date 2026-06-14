# DEVELOPMENT_LOG_EA.md

# Time Entry Portfolio Lab EA開発ログ

## 目的

この開発ログでは、時間固定エントリーポートフォリオをMT5 EA化するための開発内容を記録する。

EA化は、まずデモ口座で段階的に実施し、挙動確認後にリアル口座へ移行する。

---

# EA化方針

## 実装方式

PineConnectorではなく、MQL5でEAを直接作成する方針とする。

理由：

```text
TradingViewのシグナル送信型ではなく、
MT5内で時間指定・決済・ロット管理・指標停止・ATRフィルタを完結させる方が安定するため。
```

EAに必要な主な機能：

```text
1. 時間指定エントリー
2. 時間指定決済
3. SL / TP設定
4. 曜日・日付条件
5. 年末年始停止
6. 指標日停止
7. Global H1 ATR P70フィルタ
8. 週次複利・損失額固定ロット計算
9. Magic Numberによるロジック別管理
10. 複数通貨ペア・複数ロジック対応
```

---

# EA開発ステップ

以下の6ステップで進める。

```text
Step 1：1ロジックだけEA化
Step 2：複数ロジック対応
Step 3：Global H1 ATR P70追加
Step 4：指標停止追加
Step 5：週次複利ロット管理追加
Step 6：全28ロジック化
```

最初から全機能を入れず、段階的に確認する。

---

# Step 1 方針

## 目的

Step 1では、勝てるかどうかではなく、EAの基本挙動確認を目的とする。

確認項目：

```text
指定曜日・指定時刻にエントリーするか
指定時刻に決済するか
SL/TPが正しく入るか
Magic Numberでポジション管理できるか
JST時間とMT5サーバー時間のズレを制御できるか
非JPYペアのpip計算が正しくできるか
```

---

# Step 1 対象ロジック

当初候補として 13_UJ_Fix_MidWeek を検討したが、出現回数が少なく、挙動確認に時間がかかる可能性がある。

そのため、Step 1の候補は以下とする。

```text
22_GA_C_2
```

---

## 22_GA_C_2 仕様

| Item | Value |
|---|---|
| Strategy | 22_GA_C_2 |
| Pair | GBPAUD |
| Direction | Long |
| Entry Day | Thursday |
| Entry Time | 16:56 JST |
| Exit Time | Next day 01:15 JST |
| SL | 70 pips |
| TP | 80 pips |
| Spread | entry_adjust方式を前提 |
| Lot | Step 1では固定ロット |
| ATR Filter | Step 1ではなし |
| Event Filter | Step 1ではなし |
| Weekly Compounding | Step 1ではなし |

---

# Step 1 実装方針

Step 1では、あえて機能を絞る。

入れる機能：

```text
GBPAUD Long
木曜16:56 JST エントリー
翌日01:15 JST 決済
SL 70pips
TP 80pips
固定ロット
Magic Number管理
1ポジションのみ
```

入れない機能：

```text
Global H1 ATR P70
指標停止
年末年始停止
週次複利ロット計算
複数ロジック管理
全28ロジック
```

これにより、バグが出た場合に原因を特定しやすくする。

---

# Step 1 確認項目

デモ口座で以下を確認する。

```text
1. EAをGBPAUDチャートに適用できるか
2. 指定時刻に1回だけエントリーするか
3. 同じ日に重複エントリーしないか
4. SL/TPが正しい価格に入るか
5. 翌日01:15 JSTに時間決済されるか
6. TP/SL到達時は時間決済前に正しく終了するか
7. Magic Numberで対象ポジションだけを管理できるか
8. MT5サーバー時間とJSTのズレが正しく処理されているか
9. ログにエントリー判定・スキップ理由・決済理由が出るか
```

---

# 今後の予定

Step 1で基本挙動が確認できたら、次に進む。

```text
Step 2：複数ロジック対応
Step 3：Global H1 ATR P70追加
Step 4：指標停止追加
Step 5：週次複利ロット管理追加
Step 6：全28ロジック化
```

リアル口座への移行は、デモ口座で十分に挙動確認した後に行う。
