# JPY Regime Dependency Phase 1 — 事前登録計画
状態: 実装前固定。結果未計算。Branch: research/jpy-regime-dependency-phase1

## 目的と境界
円絡みLongのAvg R/TradeはUSDJPY上昇レジームで高く、低下レジームで低下するかを診断する。
因果証明・将来のエッジ消失保証・有意性検定による判定ではない。今回の結果でlive ON/OFFしない。
EA/VPS/SET/liveコード・設定は変更しない。22_GA_C_2の停止は別件。
Baselineは28戦略16,298 trades、SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359。
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1重複修正済み。ログ再計算禁止。

## 固定対象
Long: 1_EJ_Log1, 2_EJ_NightBlitz_20, 3_EJ_NightBlitz_21, 4_GJ_Port_Log1, 6_GJ_Old_Mon, 7_GJ_Mon_Blitz, 8_AJ_Core1, 13_UJ_Fix_MidWeek, 16_UJ_T10A, 26_AJ_China_Demand。
Short control: 5_GJ_Port_Log2, 9_AJ_Core2, 10_AJ_SatA, 11_AJ_SatB, 12_UJ_Short_Core, 14_UJ_Sat_3rd, 15_UJ_Sat_Aug。
番号・名称・Pair・Directionを照合する。追加削除禁止。研究上USDJPYも円絡みLongに含む。

## 入力調査と日次仕様
docs/29_daily_stop_baseline_result.mdは完全ログをMyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/に保存と記録。
GitHub mainのファイル一覧に正式USDJPY D1系列なし。src/filter_test_v2_range_atr.pyの既存日次はレンジ用。
本研究はsrc/research/daily_stop_baseline_revalidation.pyの監査済みUSDJPY M1 manifest 8本と時刻変換のみ踏襲し、取引生成関数は実行しない。
MT5 RawDatetimeをEurope/Helsinki（ambiguous=infer, nonexistent=shift_forward）としてAsia/Tokyoへ変換。
入力は以下の8本のみ（再帰探索は同名が一意の場合のみ）。外部追加データ禁止、各ファイルSHA-256を実行記録へ保存。
"USDJPY_M1_201501020900_201612302359.csv", "USDJPY_M1_201701020001_201812282357.csv", "USDJPY_M1_201901020600_202012310000.csv", "USDJPY_M1_202101040002_202212302355.csv", "USDJPY_M1_202301020700_202412310000.csv", "USDJPY_M1_202501010000_202512302358.csv", "USDJPY_M1_202601020001_202603310000.csv", "USDJPY_M1_202604010000_202609090000_RECHECK.csv"

JST暦日で実バーがある日ごとに、最後のM1バーCloseをdaily closeとする。土曜早朝も実データがあれば1取引日として数える。休日の合成・補間・前方補完はしない。
M1時刻はバー開始、Closeは1分後に確定。日次系列はそのJST日が終わる翌00:00まで使用しない。
tradeには DailyDate < EntryTimeのJST日付、かつ最終M1時刻+1分 <= EntryTimeを満たす直近の日を割り当てる。00:00 entryには直前日が使用可能。
ファイル末尾の当日途中データを当日entryに使用しない。重複時刻・不正価格・不正OHLCは中止。
日次末尾時刻、日次確定時刻、entry、参照indexをaudit保存。月曜は直近完了の実データ日を使用。

## レジーム
Primary: C[i]/C[i-126]-1。127 closesが必要。>0 JPY_WEAK、<0 JPY_STRONG、==0 NEUTRAL_ZERO。
Robustness: MA200[i]=mean(C[i-199:i+1])、MA200[i-20]=mean(C[i-219:i-19])。220 closesが必要。
C[i]>MA200[i]かつMA200[i]>MA200[i-20]ならJPY_WEAK_TREND。
両方<ならJPY_STRONG_TREND。その他（等号含む）はNEUTRAL_MIXED。
各方式で履歴不足はINSUFFICIENT_REGIME_HISTORY。個別に除外・件数表示。後埋め禁止。
浮動小数の等号誤判定を避けるためCloseとMA比較は十進数または正確な十進合計で行う。

## 期間と指標
FULL: 2015-01-01 <= JST EntryTime < 2026-09-10。
補助期間をHistorical 2015-2021 / RecentA 2022-2023 / RecentB 2024-2025 / Monitor2026 2026-01-01〜2026-09-09に固定。
2022-2026は既閲覧で完全未閲覧holdoutではない。期間追加移動禁止。
各戦略・Long/Short pooled: Trades, TotalR, AvgR（主）, PF, WinRate, AvgWinR, AvgLossR。
WinはR>0、LossはR<0、ゼロRはtrade数に含む。AvgLossRは負値。PFは正R合計/負R絶対合計。損失ゼロ・利益ありはInfinity、両方ゼロは未定義。空セルはTrades=0, TotalR=0, その他未定義。
差はAvgR weak minus strong。TotalR差は件数依存の補助。

## 集計・最低標本・判定
Trade-weighted pooledは対象全trade。個別regimeセル<20件はLOW_SAMPLE、表示はするが主要根拠にしない。
Strategy-equal-weightedは比較する弱・強両セル各20件以上の同一戦略集合のAvgRを等重み平均。採用戦略数とIDsを表示。戦略PFの平均を群PFとは呼ばない。Neutralは補助で取扱変更なし。
各方式FULLの支持条件は全て必要:
1 pooled AvgR weak > strong
2 equal-weighted AvgR weak > strong
3 両セル20件以上の戦略の厳密過半数が差>0（ゼロ差は非支持）。
十分標本戦略ゼロ、比較不能の場合は判定不能であり不支持と区別。
PrimaryとRobustness別判定。両支持なら「JPYレジーム依存仮説は頑健に支持」、片方のみ/両方不支持も区別。これは方向性診断で統計的有意性を意味しない。
Shortは同じ表・差を算出し逆方向か補助確認。Long支持条件には入れない。期間表は補助のみ。

## 禁止と次段階
60/90/180日追加、±X%探索、MA100/150/250、slope変更、戦略別定義変更、複合条件探索禁止。
Phase 1が依存を支持した場合のみPhase 2 Edge Risk Threshold Studyを別研究・別事前登録として検討。今回実装しない。

## 出力・検証・順序
docs/53_jpy_regime_phase1_plan.mdをGitHubへコミットしremote SHAを読み返し確認してから実装。
src/research/jpy_regime_phase1.py、tests/test_jpy_regime_phase1.py、独立検証、notebooks/jpy_regime_phase1.ipynb。
CSV prefix jpy_regime_phase1_: strategy_primary, strategy_robustness, group_summary, period_summary, regime_assignments_audit, run_record。必要に応じcoverage、decision、verification、daily auditを追加。
Colab本文に主要結果と10戦略表を表示。/contentへ全CSV。Drive保存セルは初期OFF。GitHub結果はresults/jpy_regime_phase1/、結果文書はdocs/54_jpy_regime_phase1_result.md。
Baseline hash/件数/28 IDs/固定17対象の名前方向Pair、no-lookahead（当日未来バー変更でも判定不変）、126 index、MA200と20 index、冬夏timezone、土曜/月曜/00:00、LOW_SAMPLE・空集合・ゼロ・Neutralをテスト。
独立集計で件数と十進R合計・差・支持判定を照合。代表日は先頭Primary有効日、先頭Robustness有効日、2022-01-03直前完了日、2026-09-08直前完了日（該当範囲のみ）を固定し参照closeと計算を監査。
run recordに計画/実装SHA、入力・出力hash、coverage、除外件数、実行時刻、テスト情報、BaselineRecalculated=false, LiveChanged=falseを記録。
実データ未取得なら結果を捏造せずNOT_RUN_INPUT_MISSINGと記録し、実行可能な成果物まで保存する。
