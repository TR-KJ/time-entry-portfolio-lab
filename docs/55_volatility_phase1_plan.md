# Volatility Environment Phase 1 — 事前登録計画
状態: 実装前固定・結果未計算。Branch: research/volatility-environment-phase1
基点: 1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5。既存別branchで53/54使用済みのため55/56を使用。

## 目的・固定境界
各戦略の期待値は自身のsymbolのLOW/NORMAL/HIGH volatility regimeで変わるか。方向を仮定しない。
固定28戦略16,298 trades、SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359。
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1重複修正済み。
Baseline CSVを再計算しない。22_GA_C_2も含める。2026-09-14週からのlive停止判断とは分離。
EA/VPS/SET/liveコード・設定に変更なし。Entry除外0件。履歴不足もassignmentとcoverageに残す。
今回の結果でlive ON/OFF・ATR filter採用を決めない。

## 既存仕様調査と入力固定
mainのsrc/filter_test_v2_range_atr.pyはH1 ATR14=TR.rolling(14).mean()、P70等によるEntry filter。
「ATR70」はATR length 70ではなくH1 ATR14のP70基準。今回とは別研究、結果融合禁止。
既存実装優先という依頼に従いPrimaryはD1 ATR20の単純平均（SMA of TR）に固定する。
Wilder推奨は認識しているが、既存方式優先を適用する。WilderをPrimaryまたは第三分析として追加しない。
Wilder20の手計算代表例は計算方式の相違を確認するunit testだけに使い、実tradeには適用しない。

監査済みM1の唯一のmanifestは基点コミットのsrc/research/daily_stop_baseline_revalidation.pyのMANIFEST_NAMES（7 symbol×8本）。
同ファイルのSTRATEGIESに定義された28 IDs、StrategyNo、Pair、Directionを全件照合して固定する。
Mapping: UJ=USDJPY, EJ=EURJPY, GJ=GBPJPY, AJ=AUDJPY, AU=AUDUSD, EA=EURAUD, GA=GBPAUD。
manifestはこの不変SHAのソースから定数のみ取得可。取引生成・event calendarロード関数は呼ばない。
入力各ファイルのSHA-256、行数、期間を保存。欠落/複数同名/重複timestamp/不正OHLC/非正価格は中止、補間なし。
Baseline保存記録: MyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/daily_stop_baseline_trades.csv。
既存daily仕様はresearch/jpy-regime-dependency-phase1の53 Plan、commit b2459dcd8034a7fe88ec1fb185018ce0a868cb36に準拠。

## 時刻・daily・no-lookahead
MT5 timestamp（M1開始時刻）をEurope/Helsinki（ambiguous=infer, nonexistent=shift_forward）→Asia/Tokyo→timezone-naive JST。
JST暦日の実M1のfirst Open、max High、min Low、last Close。土曜早朝も実データがあれば1 completed trading day。
バーのない暦日は生成・前方補完しない。途中欠損がある日は観測された実バーのみ。既知ギャップの後埋めなし。
DailyDate=dのAvailableAt=d+1暦日00:00。最終M1 CloseはLastM1+1分に確定。
EntryにはDailyDate < EntryのJST日付、AvailableAt<=Entry、LastM1+1分<=Entryを満たす直近日を使う。
00:00 entryは前日使用可。当日途中の最終データを当日entryに使わない。休日entryは直近完了実データ日。
daily auditにOHLC、LastM1、AvailableAt、M1Count、index、参照始終日を残す。

## 指標・percentileの一意定義
TR[i]=max(H[i]-L[i], abs(H[i]-C[i-1]), abs(L[i]-C[i-1]))。最初のTRはH-L。
Primary ATR20[i]=mean(TR[i-19:i+1])、最初の有効index=19（0起点）。
Robustness r[i]=ln(C[i]/C[i-1])。RV20[i]=sample std(r[i-19:i+1], ddof=1)*sqrt(252)、最初の有効index=20。
20/252はバーがあるJST日の本数。252年率化は記述的で通常のFX営業日数への補正は行わない。
各方式xの評価値x[i]を、それ以前252本 x[i-252:i] と比較する。評価値を参照窓に含めない。
252本全てと評価値がfiniteでなければINSUFFICIENT_VOL_HISTORY。途中のNaNを飛ばし252個を拾わない。
percentile=(count(reference<value)+0.5*count(reference==value))/252。float64で比較、事前丸めなし。
境界はexact rational 1/3, 2/3。2*less+equal <168ならLOW、<336ならNORMAL、それ以外HIGH。
ATR分類の初有効index=271、RV分類の初有効index=272。後埋め禁止。共通coverageへの後付け制限なし。
ATR20/252/33.33・66.67/RV20の変更・別窓・別cut・戦略別threshold禁止。

## 指標・期間・集計
FULL: 2015-01-01 <= EntryTime < 2026-09-10。
補助はHistorical 2015-2021、RecentA 2022-2023、RecentB 2024-2025、Monitor2026のみ。2022-2026は既閲覧、fresh holdoutではない。
Strategy×RegimeをPrimary表示: Trades, TotalR, AvgR, PF, WinRate（%）, AvgWinR, AvgLossR（負値）。
R>0勝ち、R<0負け、R=0も分母に含む。PF=正R合計/負R絶対合計。損失0利益ありinf、両方0はNaN。
空セル: Trades=0 TotalR=0 他NaN。HIGH-LOW AvgR差、3regimeの最大-最小差（3セル全て非空時）、LOW→NORMAL→HIGHの推移を表示。
cell<20でLOW_SAMPLE=true。主要比較のEligibleはLOW/HIGH双方>=20のみ、NORMALは記述的。
Group: Portfolio全28、JPY（USDJPY/EURJPY/GBPJPY/AUDJPY）、AUD_nonJPY（AUDUSD/EURAUD/GBPAUD）、Long、Short。
各groupにtrade-weighted pooled全有効trade、strategy-equal-weightedを併記。
等重みはLOW/HIGH双方>=20の同一戦略集合の各AvgRを平均、対象IDs/数を明記。NORMALで空cellがあれば等重みNORMALをNaNとし集合を変えない。
等重みPF・TotalR等をpooledと混同しない（AvgRのみ）。各期間でsample条件を再評価。groupから対象を後付けで絞らない。

## 診断判定（事前固定）
記述統計とstrategy sign consistencyが中心。CIは補助的な不確実性評価で因果/独立holdout/将来filterの証明ではない。
「ゼロから明確に離れる」は下記95%週cluster bootstrap CIが0を含まないこと、と一意に定義する。
FULL・各method・各groupで:
A: pooled HIGH-LOW差の95%CIが厳密に0を除外し、等重みHIGH-LOW差がpooledと同符号。
B: Eligible strategyの厳密過半数でHIGH-LOW差がpooledと同符号。ゼロ差は一致に数えない。
AかつBでSUPPORTED。比較不可（eligible0/LOW HIGH片方なし/CI計算不能）はUNDETERMINED、その他NOT_SUPPORTED。
Primaryのみ/Robustnessのみ/両方同方向支持（頑健に支持）/両方支持だが逆方向（CONFLICTING）/不支持/判定不能を区別。
Portfolioは補助的な全体診断。個別戦略はeligibleかつCIが0を除外ならCLEAR_PRIMARYまたはCLEAR_ROBUSTNESS。
両方式で同符号clearなら頑健な個別候補。全28戦略を表示、多重比較未調整の探索的診断と明記。
groupも同条件で補助診断（多重比較未調整）。28個の検定を確証的な発見とは呼ばない。

CI実装固定: JST EntryTimeの月曜00:00起点の暦週をcluster。FULL開始週〜終了週を空週込みで並べる。
週全体を復元抽出し同一週内の全戦略・symbolのtradeを一緒に再標本化（単純trade bootstrap禁止）。
5000回、NumPy default_rng seed=20260913、各反復で元の週数を抽出。全method/group/strategyに同じ週抽出重みを使う。
HIGHとLOWのR合計/件数から差を再計算。どちらか0件の反復は無効、>=4750有効反復を要求。
CI=有効差の2.5/97.5 percentile、linear補間。等重みやperiodのCIは算出しない。
暦週を跨ぐ自己相関・非定常性は完全には扱えない。この限界と未調整多重比較を結果に記載。
NORMALのみ異なる非単調依存は表に記述するがHIGH-LOW判定では検出できない。不支持を依存不存在と解釈しない。
Phase2候補は両方式同方向clearの戦略、または両方式同方向SUPPORTEDの群を探索候補として列挙するだけ。採用や対象限定研究はPhase1確定後の別事前登録。

## 検証・成果物・実行順序
PlanのみGitHubコミット→remote SHA読み返し→実装。実装commit SHAも実行前固定してrecordへ。
Baseline byte hash・16298・全28 IDs/Pair/Direction、JST冬夏/00:00/土曜/月曜、daily last Close/OHLC、
当日以後M1改変不変、参照252/index/等値境界、ATR20 SMA手計算とWilder20との差の代表例、log RV ddof=1、
不足履歴、LOW_SAMPLE/ゼロ/空集合、bootstrap週内共有をテスト。
独立集計は別ルート（csv/Decimalまたはmath.fsum）で全period strategy/groupの件数/R/AvgR/PF/差・等重み・符号判定を照合。
代表auditは各symbolの初有効ATR日・初有効RV日と、2022-01-03/2026-09-08以降最初のtrade（存在時）。OHLCをM1から別集計しATR/TR/RV/referenceを再計算。
Notebook本文に28戦略、group、判定、coverageを表示し/contentへCSV。Drive保存は初期OFFの独立セル。
必須CSV prefix volatility_phase1_: strategy_primary, strategy_robustness, group_summary, period_summary, regime_coverage, run_record。
追加decision、verification、manual_audit、input_manifest、daily_audit、assignment_audit_lightを許可。
全trade assignmentとdaily詳細はlocal/Colabのみ。GitHubはresults/volatility_phase1/軽量版。
実装src/research/volatility_phase1.py、Notebook notebooks/volatility_phase1.ipynb、tests、Result docs/56_volatility_phase1_result.md。
run record: Plan/Implementation SHA、input/output hashes、coverage、実行時刻、テスト、BaselineRecalculated=false、LiveChanged=false。
入力未取得時はNOT_RUN_INPUT_MISSINGとし、結果数値は作らず実行可能成果物を保存。追加探索はしない。
