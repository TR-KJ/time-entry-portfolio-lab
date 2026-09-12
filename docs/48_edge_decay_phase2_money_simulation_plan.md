# Edge Decay Phase 2 Money Simulation：事前固定計画

2026-09-12 JST。独立研究。コード作成・M0/M1資金比較前に本書だけをGitHubへコミットし、branch refとcommit内容を確認してから実装する。

## 出典・優先順位
起点はsingle-stop family確定SHA `832417d32401ba350d6c0422ecc28c2fc23540f7`。専用branch `research/edge-decay-phase2-money-simulation`。
- `src/portfolio_money_management_sim_v1_1.py`、`DEVELOPMENT_LOG_3.md`、`results/money_sim_v1_1_weekly_fixed_risk/*`：50万円、月曜06:00 JST、週初Balance×Risk、週内固定、翌週複利、2015年からの継続資金曲線・継続DD。
- `src/money_risk_compare_global_atr_p70_v1.py`、同名results：50万円、正式比較Risk 1.0/1.5/2.0%。ATR研究のリスク候補のみ再利用し、ATRフィルタは導入しない。
- `docs/16_forward_phase3a_weekly_fixed_risk_policy.md`：1.5%をバックテスト上の本命と記録。今回の代表判定Riskは1.5%。0.25%はlive VPSの保守的動作検証用の参照であり、研究代表値とは別。
- `src/EA/time_entry_step9_2_4_trade_result_reconcile_28strategies.mq5` とその参照元step9_2_1：liveは月曜00:00 JST週キー、初回要求時Equity取得・週内GV固定、MaxAutoLot=1.00、AllowMinLot=true。研究v1.1と同一仕様とは扱わない。

## 固定入力・候補・期間
Baseline 28戦略、16,298 trades、SHA-256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`。Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ/EJ1重複修正済み。固定ログ再計算なし。hash不一致は実行停止。
M0_BASELINE=全28戦略、M1_MINUS_22=完全名 `22_GA_C_2` のみ除外。別候補・複数除外・組合せ探索禁止。既存診断・Phase 2採否・EA/VPS/SET/liveコード設定を変更しない。
IS=2015-01-01〜2021-12-31、OOS1=2022-01-01〜2025-12-31、OOS2=2026-01-01〜2026-09-09、OOS_COMBINED、ALL、年別2022〜2026を表示。Phase 2と同じEntryTime JST所属。資金曲線はCloseTimeで確定損益を反映する。期間境界を跨ぐ取引があれば停止し、勝手に所属を変えない。2022〜2026は既閲覧、完全未閲覧holdoutではない。
既知：22除外はOOS +9.362857140R、全期間 -30.014285732R、OOS Worst Weekが0.301428571R悪化。これだけでlive採用しない。

## 資金仕様
初期資金500,000 JPY。Risk候補は0.25%, 1.0%, 1.5%, 2.0%の4点に固定、追加禁止。0.5%は過去の上記正式比較にないので追加しない。
主研究はv1.1の理論Money Simulation（lot capなし）。Weekly Fixed Risk=週内の各取引RiskAmount固定、Weekly Compound=翌週Base更新。同一方式であり、非複利の別モードを発明しない。
週キーはEntryTime JSTに対し月曜06:00、これより前は前週。最初の週Base=初期資金。各週の開始BalanceにRiskを掛け、週内の同時保有も各取引同額。取引ごとの複利更新なし。次週は前週全確定PnL反映後のBalance。無取引週は残高不変。浮動損益・入出金・利息なし。
v1.1はentry週の損益を全て週末に加えるため、週境界を越えて未決済なら未来損益を参照し得る。今回の入力でCloseTime < entry週開始+7日を必須検証し、不成立なら実行停止・制約として報告する。将来情報を用いて黙って計算しない。
資金曲線は2015年から各M0/M1を独立に継続し、IS/OOSで50万円へリセットしない（v1.1優先）。OOS開始残高が異なることを明記する。正規化OOS再スタートや別ルールによる救済研究は今回行わない。
Rはv1.1同様Pips/SLから計算（SLは各行、UJ12可変SLを保持）。保存Rとの微小なCSV丸め差を記録し、Phase 2のR列を上書きしない。通貨額は内部丸めなし、表示のみ丸める。Baseまたは確定残高<=0なら破綻として停止し採用不可。

## Lot・実運用制約の区別
理論式：RiskAmount=WeeklyBase×Risk、LossPerLot=SL_pips×PipValueJPYPerLot、RawLot=RiskAmount/LossPerLot、Lot=RawLot、PnL=Lot×PipValueJPYPerLot×Pips=RiskAmount×Pips/SL。v1.1はこの最後の式を使い、lot step/最小/最大/MaxAutoLot/AllowMinLotを適用しない。理論modeは無制約、pip valueが約分されるため架空の固定換算レートや数値Lotを作らない。
EA側の再現仕様を別記：RawLotがsymbol minimum未満でAllowMinLot=falseなら0、trueなら継続。MaxAutoLot>0なら先にcap。NormalizeLotはsymbol min/maxにclip→floor(lot/step)×step→小数2桁。symbol min/max/stepはMT5の銘柄属性であり一律0.01等を仮定しない。pip valueはEAのtick value/tick size/pip sizeから口座通貨で算出。
固定BaselineはPipSizeはあるが、各時点のJPY pip value、symbol min/max/step、週初の浮動Equityがない。よって実運用制約付きの数値比較は今回の固定入力だけでは正確に再現できない。実行状態をNOT_RUN_MISSING_HISTORICAL_BROKER_INPUTSとして必ず出力し、理論結果を実運用制約付き結果と呼ばない。再現用lot helperと人工値のテストは用意するが、過去値を捏造して集計しない。主判定は理論modeのみ。これは将来のlive採用承認を意味しない。

## 指標と事前採否
最優先：最終利益額 / Final Capital。代表Risk=1.5%。以下全てでMONEY_ADOPTION_CANDIDATE、満たさなければREJECT：
1. 1.5%のALL FinalCapital(M1)>M0（同じ50万円からの最終純利益改善と等価）。
2. 1.5%の継続OOS_COMBINED NetProfitJPY(M1)>M0。
3. 他の事前固定Risk 0.25/1.0/2.0%でもALL FinalCapital差および継続OOS_COMBINED NetProfit差がともに>=0（一貫性）。
4. hash/入力/資金健全性・独立照合が通過。
比較は丸め前。主条件の等号は不通過。他Riskでのみ良くても代表値を変更しない。継続曲線のALL利益減少をOOSのR改善またはDD改善で救済しない。Phase 2既存判定はそのまま残し、この独立Money判定と区別する。
期間別にStartCapital、FinalCapital、NetProfitJPY、ReturnPct、Trades、MaxDDJPY、MaxDDPct、WorstDayPct、WorstWeekPct、MoneyRoMD、MoneyPFをM0/M1/差分で表示。
CloseTime→EntryTime→StrategyNo→元行番号の決定順。DDは初期資金を含む継続ピークから計算（v1.1の初回損失を見落とすcummax初期値だけを修正、記録する）。期間MaxDDは継続DDの期間内最大。MoneyRoMD=期間純利益/期間最大継続DD円。MoneyPF=利益円合計/損失円絶対値、損失なしはNA。
WorstDayPct=JST決済日PnL/その日開始Balance×100、WorstWeekPct=月曜06:00 JST週のPnL/週初Balance×100、期間内最小。期間で日/週が分割される場合は当該期間のPnLのみを同じ日/週初Balanceで割る。損失は負表示、DDは正表示。差分は全てM1−M0、DD差は負が改善、Worst差は負が悪化。年別は部分年を年率換算しない。

## 実装・出力・検証順序
A既存調査→B本書のみコミット/SHA検証→C実装/実装コミット→D入力hash確認→E同条件比較→Fテスト/独立照合→G結果確定コミット。計画を結果後に改訂しない。
出力先 `results/edge_decay_phase2_money_simulation`：period_results.csv（5期間）、yearly_results.csv、weekly.csv、trade_log.csv、decision.csv、run_record.csv、verification.csv、constraint_status.csv（全てedge_decay_phase2_money_接頭辞）。
notebooks/edge_decay_phase2_money_simulation.ipynb：本文確定サマリー、実行時/content CSV、任意Drive保存（初期false）、コードSHA固定取得、Baseline upload/hash確認。
docs/49_edge_decay_phase2_money_simulation_result.md：主要値・判定・制約・検証・作成ファイル。
run record：Baseline hash/count、branch、計画/実装SHA、JST実行日時、初期資金、全Riskと代表値、週仕様、Lot仕様、期間/採否ルール、CSV名/hash、Colab/local実行区別、制約mode未実行理由。
検証：hash fail closed、候補完全名除外、週境界、同時保有、SL別リスク、初回損失DD、週跨ぎ/期間跨ぎ停止、破綻、採否等号/一貫性、EA lot clamp/step/min/cap。独立実装で全期間/Risk主要値と週次複利積を照合。旧v1.1の関数を副作用なしで抽出し、MoneyPnL/最終資金一致を照合。CSVとnotebook再実行の整合を確認する。
Phase 2閾値Sensitivity再実行なし、結果を見たRisk追加なし。正式live構成は28戦略のまま。
