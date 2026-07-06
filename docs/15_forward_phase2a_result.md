# Forward Phase 2-A Result

## 1. Summary

Forward Phase 2-A は、以下の構成で実施したフォワード動作確認フェーズである。

- EA: time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5
- Lot Mode: Fixed Lot
- Fixed Lot: 0.01
- Event Filter: Candidate C ON
- ATR Filter: OFF
- Weekend / Market Closed Guard: ON

本フェーズの目的は、利益・PF・DDの評価ではなく、EAが想定どおりに稼働するかを確認することである。

約1週間のフォワード稼働において、Entry / Exit / Event停止 / 稼働停止を含め、現時点で大きな異常は確認されていない。

---

## 2. Phase

- Phase Name: Forward Phase 2-A
- Purpose: Event Candidate C + ATR OFF + FixedLot 0.01 の動作確認
- Start Timing: Phase 1-A停止後
- Status: Completed / Passed

---

## 3. Operating Environment

Forward Phase 2-A は、以下の環境で稼働した。

- Windows notebook PC: DELL Inspiron
- Power: Home use with AC adapter connected
- Sleep setting: Disabled
- MT5: Running continuously on Windows notebook
- Monitoring:
  - iPhone MT5
  - Remote Desktop from iPhone
- Network:
  - Home internet while at home
  - Remote monitoring while away from home

外出先からの監視も含め、運用環境として大きな問題は確認されていない。

---

## 4. Phase 2-A Settings

### Lot

- LotMode = Fixed Lot
- InpLotMode = 0
- InpFixedLot = 0.01

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

---

## 5. Confirmed Items

Forward Phase 2-A において、以下を確認した。

### 5.1 EA Startup

EA起動後、Expertsログ上で稼働状態を確認。

- EA起動確認: OK
- TestMode false: OK
- MockJST false: OK
- UseTestTimes false: OK
- 自動売買ON: OK

### 5.2 Fixed Lot Entry

FixedLot 0.01でEntryすることを確認。

- FixedLot 0.01 Entry: OK
- 想定外Lot: なし

### 5.3 Date Rule Reject

各Strategy固有の日付・曜日条件による Date rule reject を確認。

例:

- not Wed/Thu
- not 3rd
- not August
- not 10th
- outside 9-15 window
- not Thursday

これらはStrategyごとの通常ルールによる停止であり、異常ではない。

### 5.4 ATR Filter OFF

ATR Filter OFF状態で稼働。

- InpUseGlobalAtrP70Filter = false
- ATR REJECT: 出力なし
- ATR Filterによる想定外停止: なし

ATR OFF状態であることを確認できたため、Phase 2-A目的に対して問題なし。

### 5.5 Event Candidate C

Event Candidate CをONにした状態で稼働。

- InpUseEventFilter = true
- InpUseEventCandidateC = true

7/2 米国雇用統計時の稼働停止について、問題なく停止したことを確認。

- 2026/7/2 米国雇用統計停止: OK
- Event Filter稼働: OK
- 想定外Event停止: 現時点でなし

### 5.6 Weekend / Market Closed Guard

Weekend / Market Closed GuardはONで稼働。

- InpUseWeekendMarketClosedGuard = true

本フェーズ中、Weekend Guardに起因する重大な問題は確認されていない。

### 5.7 Position Management

Entry後のポジション管理について、外出先からiPhone MT5およびRemote Desktopで確認可能。

- Entry確認: OK
- 稼働状況確認: OK
- 外出先監視: OK
- 稼働停止含む管理: OK

---

## 6. Notes on Sleep / Network Behavior

Phase 2-A中、Windows notebook PCを家で電源接続し、スリープしない設定でEAを稼働した。

確認・整理した挙動は以下。

- PCが稼働中でMT5が接続されていれば、EAは通常通り動作する。
- PCがスリープした場合、MT5およびEAは実質停止する。
- EA管理のTime Exitや条件決済は、PC / MT5 / 通信が稼働している状態でなければ実行されない。
- ただし、すでにブローカーサーバー側に送信済みのSL / TPは、PC停止中でも有効と考える。
- 今後の実運用では、Windows PCのスリープ無効・電源接続・通信安定性が重要。

Phase 2-Aでは、Windows notebookを電源接続し、スリープしない設定で運用する形で問題なく稼働した。

---

## 7. Phase 2-A Judgment

Forward Phase 2-A は、以下の観点から合格と判断する。

- EAが正常に起動した
- FixedLot 0.01でEntryした
- Date rule rejectが正常に出力された
- ATR REJECTが出ていない
- Event Candidate Cが稼働した
- 7/2 米国雇用統計時の停止が問題なく動作した
- Windows notebook常時稼働環境で大きな問題がなかった
- 外出先からの監視も可能だった
- 想定外Entry / 想定外停止 / 二重Entryなどの重大異常は現時点で確認されていない

---

## 8. Conclusion

Forward Phase 2-A は合格。

次フェーズとして、Weekly Fixed Risk Lotによる週次複利計算フェーズへ移行する。

ただし、次フェーズでは利益評価よりも先に、以下の確認を優先する。

- Weekly Base Equityの取得
- Risk Amountの計算
- SL幅に応じたLot計算
- Raw LotとFinal Lotの差
- MaxAutoLot制限の有無
- MinLot処理の有無
- 実際の発注Lot
- 想定以上のLotになっていないか

次フェーズは、Forward Phase 3-Aとして記録する。

---

## 9. Next Phase

Next Phase:

- Forward Phase 3-A
- Event Candidate C + ATR OFF + Weekly Fixed Risk
- Initial target risk: 1.5%
- Main purpose at start: Lot calculation check
