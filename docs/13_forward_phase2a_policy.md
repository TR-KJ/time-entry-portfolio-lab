# Forward Phase 2-A Policy

## 目的

Forward Phase 2-A は、Event Candidate C と ATR OFF を本体EAで動作確認するためのフォワードテストフェーズである。

このフェーズでは、利益・PF・DDを主目的にしない。

主目的は、以下のEA動作確認である。

- Weekend / Market Closed Guard が正しく動作すること
- Event Candidate C が正しく動作すること
- ATR Filter OFF 状態でATR REJECTが出ないこと
- FixedLot 0.01 で安全にEntry / Exitが行われること
- Event停止、通常Entry、Time Exitが想定どおり動くこと

---

## 対象EA

src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

---

## Phase名

Forward Phase 2-A

---

## Phase 2-A の位置づけ

現行フォワード Phase 1-A は、以下の設定でEA動作確認を行っていた。

- FixedLot = 0.01
- ATR Filter = ON
- Event Filter = ON
- Event Candidate C = 未使用
- Weekend / Market Closed Guard = 未実装または未反映

Phase 2-A では、以下を反映する。

- Weekend / Market Closed Guard を使用
- Event Candidate C を使用
- ATR Filter をOFF
- LotModeは引き続き Fixed Lot
- FixedLotは 0.01

Weekly Fixed Risk 1.5% はまだ使用しない。

Weekly Fixed Riskは、Phase 2-AでEvent Candidate CとATR OFFの動作確認が完了した後、次フェーズで確認する。

---

## Phase 2-A 設定

### Lot

LotMode = Fixed Lot  
InpLotMode = 0  
InpFixedLot = 0.01  

### Weekend / Market Closed Guard

InpUseWeekendMarketClosedGuard = true  
InpPrintWeekendGuardLogs = true  
InpSuppressWeekendGuardLogsOncePerDay = true  

### ATR Filter

InpUseGlobalAtrP70Filter = false  
InpPrintAtrFilterLogs = false  

### Event Filter

InpUseEventFilter = true  
InpUseEventCandidateC = true  
InpPrintEventFilterLogs = true  
InpSuppressEventLogsOncePerDay = true  

### Emergency / Test

InpEmergencyStop = false  
InpTestMode = false  
InpUseMockJstDateTime = false  
InpUseTestTimes = false  

### Logs

通常フォワードでは、ログ過多を避けるため以下を推奨する。

InpPrintDebug = true  
InpPrintSkipLogs = false  
InpPrintRuleRejectLogs = true  
InpSuppressRuleRejectLogsOncePerDay = true  
InpPrintEventFilterLogs = true  
InpSuppressEventLogsOncePerDay = true  
InpPrintAtrFilterLogs = false  

---

## Event Candidate C 設定

Phase 2-A では Event Candidate C をONにする。

InpUseEventCandidateC = true

Event Candidate C の基本方針は以下。

US CPI / NFP / BOJ:
date_all_day

FOMC:
position_overlap

RBA / ECB / BOE / AUD CPI:
position_overlap

一部Strategy:
date_all_day維持またはStrategy別特殊ルール維持

---

## FOMC position_overlap 仕様

FOMCは、イベント日だから終日停止するのではなく、予定保有時間がFOMC停止ウィンドウと重なる場合のみ停止する。

初期設定:

FOMC EventTime JST = 03:00  
Pre Minutes = 180  
Post Minutes = 180  

停止ウィンドウ例:

EventTime = 03:00  
Window = 00:00〜06:00  

停止条件:

Entry予定時刻〜Exit予定時刻が、FOMC停止ウィンドウと重なる場合に停止する。

確認済みケース:

3_EJ_NightBlitz_21  
Entry: 2026-07-29 21:56  
Exit : 2026-07-30 05:27  
FOMC: 2026-07-30 03:00  
Result: EVENT OVERLAP STOP

18_EA_2  
Entry: 2026-12-08 09:59  
Exit : 2026-12-09 05:26  
FOMC: 2026-12-09 03:00  
Result: EVENT OVERLAP STOP

27_EA_China_Demand  
Entry: 2026-12-09 10:00  
Exit : 2026-12-09 15:50  
FOMC: 2026-12-09 03:00  
Result: Entry  
Reason: FOMC window 00:00〜06:00 と保有予定時間が重ならないため

---

## Phase 2-A 移行前に確認済みの内容

### Weekend Guard

対象EA:

time_entry_step9_1_weekend_guard_28strategies.mq5

確認結果:

- 土曜日Entry時刻でWeekend Guard停止 OK
- 日曜日Entry時刻でWeekend Guard停止 OK
- 平日はWeekend Guardでは停止しない OK
- Weekend Guard OFF時は旧挙動に戻る OK

判定:

Weekend / Market Closed Guard は合格。

---

### Event Candidate C 前半テスト

対象EA:

time_entry_step9_2_event_candidate_c_28strategies.mq5

確認結果:

- InpUseEventCandidateC=false で現行Event Filter互換 OK
- US CPI date_all_day OK
- NFP date_all_day OK
- BOJ date_all_day OK

判定:

Event Candidate C の date_all_day 系は合格。

---

### Event Candidate C overlap fix

対象EA:

time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

確認結果:

- 3_EJ_NightBlitz_21 の翌日深夜FOMC overlap停止 OK
- 18_EA_2 の翌日深夜FOMC overlap停止 OK
- 27_EA_China_Demand のFOMC non-overlap通過 OK

判定:

FOMC position_overlap 修正は合格。

---

### ATR OFF + Event Candidate C

対象EA:

time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

確認結果:

- ATR OFF + US CPI date_all_day停止 OK
- ATR OFF + イベント対象外日Entry OK
- ATR OFF + 3_EJ FOMC overlap停止 OK
- ATR OFF + 18_EA FOMC overlap停止 OK

判定:

ATR OFF + Event Candidate C の組み合わせ確認は合格。

---

## Phase 2-A で確認したいこと

Phase 2-Aでは、以下を中心にフォワード確認する。

### Entry

- 各Strategyが予定Entry時刻に判定されること
- FixedLot 0.01でEntryすること
- Event対象外日でEntryできること
- Weekend Guardで土日Entryしないこと
- EmergencyStop=falseで通常Entryが可能なこと

### Event Filter

- US CPI / NFP / BOJがdate_all_dayで止まること
- FOMCがposition_overlapで止まること
- FOMC日でも保有予定時間が重ならない場合は止まらないこと
- Event停止ログが過剰に出すぎないこと

### ATR Filter

- ATR REJECTが出ないこと
- InpUseGlobalAtrP70Filter=false が有効であること

### Exit

- Time Exitが予定通り動くこと
- Event Filter / EmergencyStop に関係なく、既存ポジションのTime Exitが維持されること

### Safety

- 土日・市場クローズ中に不要なATR/Event判定へ進まないこと
- 予定外のOrderSendがないこと
- すでに当日Entry済みの場合、already entered todayで二重Entryしないこと

---

## Phase 2-A では評価しないもの

Phase 2-Aは動作確認フェーズのため、以下は主評価対象にしない。

- Profit Factor
- Total Pips
- Max DD
- 勝率
- 週次複利リターン
- Weekly Fixed Risk 1.5%の実運用成績

これらは、Phase 2-AでEA動作が安定した後、Phase 3以降で確認する。

---

## Weekly Fixed Riskについて

検証上の本命候補は以下。

Event Candidate C + ATR OFF + Weekly Fixed Risk 1.5%

次点候補:

Event Candidate C + ATR OFF + Weekly Fixed Risk 1.0%

ただし、Phase 2-AではWeekly Fixed Riskは使用しない。

理由:

- Event Candidate CとATR OFFの動作確認に集中するため
- Lot変動を入れると問題発生時の原因切り分けが難しくなるため
- まずFixedLot 0.01で安全確認するため

Weekly Fixed Riskは、Phase 2-A完了後に別フェーズで確認する。

---

## Phase 2-A 開始条件

以下を満たしたらPhase 2-Aへ移行可能。

- time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5 がコンパイルOK
- Weekend GuardテストOK
- Event Candidate C date_all_dayテストOK
- FOMC position_overlapテストOK
- ATR OFF + Event Candidate C組み合わせテストOK
- GitHub docsにテスト結果を記録済み
- 現行Phase 1-AからPhase 2-Aへ切り替えるタイミングを決める

---

## Phase 2-A 開始時の注意

現行フォワードEAをいきなり上書きしない。

Phase 2-A用EAとして、以下を使用する。

src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

開始前に、MT5側でEA名・input設定・適用チャートを確認する。

特に以下を確認する。

- InpUseGlobalAtrP70Filter = false
- InpUseEventCandidateC = true
- InpUseWeekendMarketClosedGuard = true
- InpLotMode = 0
- InpFixedLot = 0.01
- InpTestMode = false
- InpUseMockJstDateTime = false
- InpUseTestTimes = false
- InpEmergencyStop = false

---

## Phase 2-A 記録項目

Phase 2-A開始後は、以下を記録する。

- 開始日時
- 使用EAファイル名
- input設定
- 稼働口座
- 稼働チャート
- Entryログ
- Event Rejectログ
- Weekend Guardログ
- Time Exitログ
- 想定外Entry
- 想定外Reject
- エラー・警告ログ
- 手動停止・EA再起動の有無

---

## Phase 2-A 終了条件

以下を満たしたら、Phase 2-A完了候補とする。

- 複数日フォワードでEAが安定稼働
- Event Candidate Cの停止が想定通り
- ATR REJECTが出ない
- Weekend Guardが不要な判定を抑制
- Time Exitが正常
- 想定外OrderSendがない
- ログが追跡可能な量に収まる

---

## 次のPhase候補

Phase 2-A完了後、次は以下を検討する。

Forward Phase 3-A:

Event Candidate C + ATR OFF + Weekly Fixed Risk 1.5%

目的:

実運用モデルに近いフォワード確認

次点:

Forward Phase 3-B:

Event Candidate C + ATR OFF + Weekly Fixed Risk 1.0%

目的:

保守的なリスク設定での実運用モデル確認

---

## 現時点の結論

Forward Phase 2-A は以下で進める。

Event Candidate C + ATR OFF + FixedLot 0.01

使用EA:

time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5

目的:

EA動作確認

Phase 2-Aの確認が完了してから、Weekly Fixed Risk 1.5%へ進む。
