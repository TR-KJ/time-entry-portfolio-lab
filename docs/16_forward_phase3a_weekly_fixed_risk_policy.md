# Forward Phase 3-A Weekly Fixed Risk Policy

## 1. Summary

Forward Phase 3-A は、Forward Phase 2-Aで動作確認済みの構成をベースに、Lot ModeをFixed LotからWeekly Fixed Riskへ移行するフェーズである。

本フェーズでは、以下の構成を採用する。

- Event Filter: Candidate C ON
- ATR Filter: OFF
- Lot Mode: Weekly Fixed Risk
- Risk Percent Per Trade: 1.5%
- Weekly Base: Week-start Equity basis

ただし、Phase 3-A開始直後の主目的は利益評価ではなく、Weekly Fixed Risk Lotの計算が想定どおりに行われるかを確認することである。

---

## 2. Background

Forward Phase 2-Aでは、以下を確認済み。

- EA起動
- FixedLot 0.01でのEntry
- Date Rule Reject
- Event Candidate C
- ATR Filter OFF
- 7/2 米国雇用統計時の停止
- Windows notebook常時稼働環境
- 外出先からの監視
- 想定外Entry / 想定外停止がないこと

このため、次の段階としてWeekly Fixed Risk Lotへ移行する。

---

## 3. Phase

- Phase Name: Forward Phase 3-A
- Purpose: Weekly Fixed Risk Lot calculation check and forward operation
- Base EA: time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5
- Status: Planned / Ready to start

---

## 4. Main Objective

Forward Phase 3-Aの開始直後は、利益・PF・DDの評価ではなく、以下の確認を主目的とする。

- Weekly Base Equityが正しく取得されるか
- 週初資金を基準にRisk Amountが計算されるか
- SL幅に応じてLotが正しく計算されるか
- Raw LotとFinal Lotが確認できるか
- MaxAutoLotによる制限が正しく効くか
- MinLot処理が正しく行われるか
- 実際の発注Lotが計算結果と一致するか
- 想定以上のLotで発注されていないか

---

## 5. Phase 3-A Settings

### Lot

- InpLotMode = 1
- InpRiskPercentPerTrade = 1.50
- InpWeeklyBaseUseEquity = true
- InpMaxAutoLot = 1.00
- InpAllowMinLotWhenBelowMinimum = true
- InpPrintLotLogs = true

### Weekend / Market Closed Guard

- InpUseWeekendMarketClosedGuard = true
- InpPrintWeekendGuardLogs = true
- InpSuppressWeekendGuardLogsOncePerDay = true

### ATR Filter

- InpUseGlobalAtrP70Filter = false
- InpPrintAtrFilterLogs = false

### Event Filter

- InpUseEventFilter = true
- InpUseEventCandidateC = true
- InpPrintEventFilterLogs = true
- InpSuppressEventLogsOncePerDay = true

### Emergency / Test

- InpEmergencyStop = false
- InpTestMode = false
- InpUseMockJstDateTime = false
- InpUseTestTimes = false

### Logs

- InpPrintDebug = true
- InpPrintSkipLogs = false
- InpPrintRuleRejectLogs = true
- InpSuppressRuleRejectLogsOncePerDay = true
- InpPrintEventFilterLogs = true
- InpSuppressEventLogsOncePerDay = true
- InpPrintAtrFilterLogs = false
- InpPrintLotLogs = true

---

## 6. Risk Setting

Phase 3-Aの初期設定は以下とする。

- Risk Percent Per Trade: 1.5%
- Weekly Base: Week-start Equity
- Max Auto Lot: 1.00

1.5%はバックテスト上の本命設定である。

ただし、実フォワード移行直後はLot計算確認を優先し、想定外に大きいLotが出る場合は即時停止または設定見直しを行う。

---

## 7. Why Weekly Fixed Risk

これまでの検証では、固定Lotやpips評価だけでなく、実運用に近い以下の前提で評価してきた。

- 損失額固定型
- 週ごとの複利計算
- 週初資金を基準にRisk Amountを算出
- 各TradeのSL幅に応じてLotを調整

この運用モデルにより、pipsベースだけではなく、実際の資金成長・ドローダウン・リスク管理に近い形で評価できる。

---

## 8. Start Conditions

Phase 3-A開始条件は以下。

- Phase 2-A完了
- Phase 2-Aで大きな異常なし
- Event Candidate C稼働確認済み
- ATR OFF稼働確認済み
- 7/2 米国雇用統計停止確認済み
- Windows notebook常時稼働環境確認済み
- 保有ポジションなし、または切替タイミングとして問題ない状態
- 未決済注文なし、または切替タイミングとして問題ない状態
- EA inputをPhase 3-A設定へ変更
- 自動売買ON
- ExpertsログでEA起動確認

---

## 9. Startup Checklist

Phase 3-A開始前に、以下を確認する。

- Current EA: time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5
- Compile OK
- InpLotMode = 1
- InpRiskPercentPerTrade = 1.50
- InpWeeklyBaseUseEquity = true
- InpMaxAutoLot = 1.00
- InpPrintLotLogs = true
- InpUseGlobalAtrP70Filter = false
- InpUseEventFilter = true
- InpUseEventCandidateC = true
- InpUseWeekendMarketClosedGuard = true
- InpEmergencyStop = false
- InpTestMode = false
- InpUseMockJstDateTime = false
- InpUseTestTimes = false
- AutoTrading ON
- MT5 connected
- Windows sleep disabled
- Power connected

---

## 10. First Entries Check

Phase 3-A開始後、最初の数Entryでは以下を必ず確認する。

- Strategy name
- Symbol
- Direction
- Entry time
- SL
- TP
- SL pips
- Weekly Base Equity
- Risk Amount
- Raw Lot
- Final Lot
- MaxAutoLot applied or not
- MinLot applied or not
- Actual order lot
- OrderSend result
- Position opened lot
- Time Exit behavior

特に重要なのは、以下。

- Final Lotが想定以上に大きくなっていないか
- MaxAutoLot制限が必要に応じて効いているか
- SL幅が極端に狭いStrategyでLotが過大になっていないか
- 実際の発注Lotがログ上のFinal Lotと一致しているか

---

## 11. Stop / Review Conditions

以下のいずれかが発生した場合、Phase 3-Aを一時停止し、設定またはコードを確認する。

- 想定より大きいLotで発注された
- MaxAutoLotが効いていない
- MinLot処理が想定と違う
- Risk Amountが想定と違う
- Weekly Base Equityが想定と違う
- SL幅の取得に異常がある
- OrderSend failedが連発する
- 同一Strategyで二重Entryした
- ATR REJECTが出た
- Event対象外日にEVENT REJECTが出た
- TestMode / MockJST関連ログが出た
- Time Exitが動かない
- PC / MT5 / 通信環境に不安定さがある

---

## 12. Monitoring Policy

Phase 3-A開始直後は、以下の方針で監視する。

- 最初の数EntryはLot計算ログを必ず確認する
- iPhone MT5でポジションLotを確認する
- 必要に応じてRemote DesktopでExpertsログを確認する
- 想定外Lotの場合は即停止する
- 週初のWeekly Base更新挙動を確認する
- 週またぎ後のLot計算も確認する

通常運用に移るまでは、InpPrintLotLogs = trueを維持する。

Lot計算に問題がないことを確認できた後、ログ量が多い場合はInpPrintLotLogsをfalseにすることを検討する。

---

## 13. Phase 3-A Judgment Criteria

Phase 3-Aは、以下が確認できれば初期合格とする。

- Weekly Fixed Risk LotでEntryできた
- Weekly Base Equityが正しく取得された
- Risk Amountが正しく計算された
- SL幅に応じたLot計算が行われた
- Final Lotが想定内だった
- 実際の発注LotがFinal Lotと一致した
- MaxAutoLot / MinLot処理が想定どおりだった
- Event Candidate Cが引き続き正常に動作した
- ATR REJECTが出なかった
- Time Exitが正常に動作した
- 想定外Entry / 想定外停止がなかった

---

## 14. Notes

Phase 3-Aは、バックテスト上の本命であるWeekly Fixed Risk 1.5%へ移行するフェーズである。

ただし、移行直後は資金成長よりも、Lot計算とEA挙動の安全確認を優先する。

本フェーズでLot計算に問題がなければ、以降は実運用に近い評価フェーズへ進む。

---

## 15. Conclusion

Forward Phase 3-A を開始する。

Initial configuration:

- Event Candidate C: ON
- ATR Filter: OFF
- Lot Mode: Weekly Fixed Risk
- Risk Percent Per Trade: 1.5%
- Weekly Base: Equity
- Max Auto Lot: 1.00
- Lot Logs: ON

Phase 3-A開始直後は、利益評価ではなくLot計算確認フェーズとして扱う。
