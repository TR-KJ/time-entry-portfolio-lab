# Step 9.2.2 Event Overlap Fix Patch Guide

このドキュメントは、`src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5` から、次回EA候補 `src/EA/time_entry_step9_2_2_event_overlap_fix_28strategies.mq5` を作成するための差分メモである。

最初に既存EAをコピーする。

- From: `src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
- To: `src/EA/time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

その後、以下の修正を反映する。

---

## 1. Header

ファイル冒頭の表示名を任意で変更する。

```mql5
//| time_entry_step9_2_2_event_overlap_fix_28strategies.mq5                 |
//| Time Entry Portfolio Lab                                         |
//| Step 9.2.2: Event overlap fix for 28 strategies                  |
```

---

## 2. Add US_NFP / BOJ position_overlap inputs

既存のEvent Candidate C time-window settingsに、以下を追加する。

追加位置候補:

- `InpFomcPostMinutes` の直後

```mql5
input int             InpNfpEventHourJST = 21;
input int             InpNfpEventMinuteJST = 30;
input int             InpNfpPreMinutes = 120;
input int             InpNfpPostMinutes = 120;
input int             InpBojEventHourJST = 12;
input int             InpBojEventMinuteJST = 0;
input int             InpBojPreMinutes = 180;
input int             InpBojPostMinutes = 180;
```

---

## 3. Replace UJ12 Gotobi logic

既存の以下関数を置き換える。

- `bool IsUJGotoDay(int day)`
- `int GetUJ12TradeMode(datetime jst_time)`

置き換え後:

```mql5
bool IsUJGotoDay(int day)
{
   return day == 20 || day == 25 || day == 30;
}

bool IsUJForwardGotobiDate(datetime jst_time)
{
   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(dt.day_of_week != 5)
   {
      return false;
   }

   datetime next_day = jst_time + 86400;
   datetime next_next_day = jst_time + 86400 * 2;

   MqlDateTime nd;
   MqlDateTime nnd;
   TimeToStruct(next_day, nd);
   TimeToStruct(next_next_day, nnd);

   if(nd.day == 25 || nd.day == 30)
   {
      return true;
   }

   if(nnd.day == 25 || nnd.day == 30)
   {
      return true;
   }

   return false;
}

int GetUJ12TradeMode(datetime jst_time)
{
   if(InpUJ12ForceGotoMode && InpUJ12ForceNormalMode) return UJ_MODE_INVALID;
   if(InpUJ12ForceGotoMode) return UJ_MODE_GOTO;
   if(InpUJ12ForceNormalMode) return UJ_MODE_NORMAL;

   MqlDateTime dt;
   TimeToStruct(jst_time, dt);

   if(IsUJGotoDay(dt.day)) return UJ_MODE_GOTO;
   if(IsUJForwardGotobiDate(jst_time)) return UJ_MODE_GOTO;

   return UJ_MODE_NORMAL;
}
```

仕様:

- 20 / 25 / 30 は通常GOTO
- 25 / 30 が土日の場合のみ、直前金曜を前倒しGOTO
- 20 が土日の場合は、前倒しGOTOにしない
- 祝日は考慮しない

---

## 4. Add US_NFP / BOJ to GetCandidateCEventTimeAndWindow

`GetCandidateCEventTimeAndWindow` 内に以下を追加する。

追加位置候補:

- FOMCブロックの直後

```mql5
   if(normalized_event == "US_NFP")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpNfpEventHourJST, InpNfpEventMinuteJST);
      pre_minutes = InpNfpPreMinutes;
      post_minutes = InpNfpPostMinutes;
      return true;
   }

   if(normalized_event == "BOJ")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpBojEventHourJST, InpBojEventMinuteJST);
      pre_minutes = InpBojPreMinutes;
      post_minutes = InpBojPostMinutes;
      return true;
   }
```

---

## 5. Add US_NFP / BOJ to IsCandidateCEventDateKey

`IsCandidateCEventDateKey` 内に以下を追加する。

追加位置候補:

- FOMCブロックの直後

```mql5
   if(normalized_event == "US_NFP")
   {
      return IsDateInList(date_key, US_NFP_2026_DATES);
   }

   if(normalized_event == "BOJ")
   {
      return IsDateInList(date_key, BOJ_2026_DATES);
   }
```

---

## 6. Update IsCandidateCStrategyTargetForEvent

### 6.1 FOMC target additions

FOMCブロックに以下を追加する。

```mql5
      if(cfg.strategy_code == "1_EJ_Log1") return true;
      if(cfg.strategy_code == "4_GJ_Port_Log1") return true;
      if(cfg.strategy_code == "16_UJ_T10A") return true;
```

### 6.2 US_NFP target block

FOMCブロックの後などに、以下を追加する。

```mql5
   if(normalized_event == "US_NFP")
   {
      if(cfg.strategy_code == "1_EJ_Log1") return true;
      return false;
   }
```

### 6.3 BOJ target block

```mql5
   if(normalized_event == "BOJ")
   {
      if(cfg.strategy_code == "1_EJ_Log1") return true;
      return false;
   }
```

### 6.4 ECB target addition

ECBブロックに以下を追加する。

```mql5
      if(cfg.strategy_code == "1_EJ_Log1") return true;
```

---

## 7. Update IsCandidateCPositionOverlapOverride

既存の `IsCandidateCPositionOverlapOverride` に、`1_EJ_Log1` のUS_NFP / BOJを追加する。

置き換え候補:

```mql5
bool IsCandidateCPositionOverlapOverride(StrategyConfig &cfg, string event_name)
{
   string normalized_event = NormalizeCandidateCEventName(event_name);

   if(normalized_event == "FOMC")
   {
      if(cfg.strategy_code == "2_EJ_NightBlitz_20") return true;
      if(cfg.strategy_code == "3_EJ_NightBlitz_21") return true;
      if(cfg.strategy_code == "1_EJ_Log1") return true;
      if(cfg.strategy_code == "4_GJ_Port_Log1") return true;
      if(cfg.strategy_code == "16_UJ_T10A") return true;
   }

   if(cfg.strategy_code == "1_EJ_Log1")
   {
      if(normalized_event == "US_NFP") return true;
      if(normalized_event == "BOJ") return true;
   }

   return false;
}
```

---

## 8. Add US_NFP / BOJ to GetCandidateCEventTimeAndWindowByDateKey

`GetCandidateCEventTimeAndWindowByDateKey` 内に以下を追加する。

追加位置候補:

- FOMCブロックの直後

```mql5
   if(normalized_event == "US_NFP")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpNfpEventHourJST, InpNfpEventMinuteJST);
      pre_minutes = InpNfpPreMinutes;
      post_minutes = InpNfpPostMinutes;
      return true;
   }

   if(normalized_event == "BOJ")
   {
      event_time_jst = BuildJstDateTimeFromDateKey(event_date_key, InpBojEventHourJST, InpBojEventMinuteJST);
      pre_minutes = InpBojPreMinutes;
      post_minutes = InpBojPostMinutes;
      return true;
   }
```

---

## 9. Update RejectCandidateCPositionOverlapEventsDuringPlannedPosition

既存関数を以下に置き換える。

```mql5
bool RejectCandidateCPositionOverlapEventsDuringPlannedPosition(StrategyConfig &cfg, datetime jst_time)
{
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "FOMC")) return true;
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "US_NFP")) return true;
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "BOJ")) return true;
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "RBA")) return true;
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "ECB")) return true;
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "BOE")) return true;
   if(RejectCandidateCPositionOverlapEventIfMatched(cfg, jst_time, "AU_CPI")) return true;
   return false;
}
```

---

## 10. Update PassEventCandidateCFilter blocks

### 10.1 1_EJ_Log1

既存の `1_EJ_Log1` ブロックに、`US_CPI_WEEK_WED` 判定の後、`return true` の前に以下を追加する。

```mql5
      if(RejectCandidateCPositionOverlapEventsDuringPlannedPosition(cfg, jst_time)) return false;
```

期待する最終イメージ:

```mql5
   if(cfg.strategy_code == "1_EJ_Log1")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 2)
      {
         PrintEventDecisionLog(cfg, jst_time, "EJ_LOG1_FEB_STOP");
         return false;
      }

      if(dt.day == 1)
      {
         PrintEventDecisionLog(cfg, jst_time, "EJ_LOG1_DAY1_STOP");
         return false;
      }

      if(IsCpiWednesdayDate(date_key))
      {
         PrintEventDecisionLog(cfg, jst_time, "US_CPI_WEEK_WED");
         return false;
      }

      if(RejectCandidateCPositionOverlapEventsDuringPlannedPosition(cfg, jst_time)) return false;

      return true;
   }
```

### 10.2 4_GJ_Port_Log1

既存の `4_GJ_Port_Log1` ブロックに、月停止・日付停止の後、`return true` の前に以下を追加する。

```mql5
      if(RejectCandidateCPositionOverlapEventsDuringPlannedPosition(cfg, jst_time)) return false;
```

期待する最終イメージ:

```mql5
   if(cfg.strategy_code == "4_GJ_Port_Log1")
   {
      MqlDateTime dt;
      TimeToStruct(jst_time, dt);

      if(dt.mon == 12)
      {
         PrintEventDecisionLog(cfg, jst_time, "GJ_PORT_LOG1_DEC_STOP");
         return false;
      }

      if(dt.day == 1 || dt.day == 2 || dt.day == 29 || dt.day == 30 || dt.day == 31)
      {
         PrintEventDecisionLog(cfg, jst_time, "GJ_PORT_LOG1_DAY_STOP");
         return false;
      }

      if(RejectCandidateCPositionOverlapEventsDuringPlannedPosition(cfg, jst_time)) return false;

      return true;
   }
```

### 10.3 16_UJ_T10A

既存の `16_UJ_T10A` ブロックに、BOJ終日停止の前に以下を追加する。

```mql5
      if(RejectCandidateCPositionOverlapEventsDuringPlannedPosition(cfg, jst_time)) return false;
```

期待する最終イメージ:

```mql5
   if(cfg.strategy_code == "16_UJ_T10A")
   {
      if(RejectCandidateCPositionOverlapEventsDuringPlannedPosition(cfg, jst_time)) return false;

      if(InpStopOnBOJ && IsDateInList(date_key, BOJ_2026_DATES))
      {
         PrintEventDecisionLog(cfg, jst_time, "BOJ");
         return false;
      }

      return true;
   }
```

---

## 11. Compile/Test Notes

作成後、以下をMetaEditorで確認する。

- Compile OK
- `12_UJ_Short_Core` 2026/7/24 09:55 GOTO Entry判定
- `12_UJ_Short_Core` 2026/6/19 は20日前なのでEntry対象外
- `1_EJ_Log1` 2026/7/29 FOMC overlap stop
- `4_GJ_Port_Log1` FOMC overlap stop
- `16_UJ_T10A` FOMC overlap stop
- 既存のEvent Candidate C対象Strategyが壊れていないこと
