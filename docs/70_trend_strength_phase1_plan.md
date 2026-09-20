# Trend Strength Phase 1 — 事前登録計画
状態: 実装前固定・Trend結果未計算。Branch: research/trend-strength-phase1。
基点: Volatility Phase 2 remote 0f8d134a41fe84fb1e79cdf43a91b7c2f77f67dc。
既存別branchの最大docs番号69を確認し、Plan 70 / Result 71を予約。

## 目的と変更境界
方向でなくトレンドの強さ・一方向性により28戦略のAvg R/Tradeが変わるかを純粋診断する。HIGH優位/LOW優位を仮定しない。
固定28戦略・16,298 trades、Baseline byte SHA256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359。
Daily Stopなし、ATR OFF、Event Candidate C、UJ12前倒しゴトウビ・EJ1イベント重複修正済み。Trade Log再計算禁止。
liveで停止済み22_GA_C_2を比較可能性のため含む。全tradeをassignment/coverageに残し履歴不足のみregime集計から区別する。
Volatility Phase 5 Dell Demo Forwardには一切変更しない。EA/VPS/SET/live運用コード・設定変更なし。
Entry filter/ON-OFF・Risk変更・Volatility R2との統合・Volatilityとの掛け合わせ分析なし。

## 既存調査と入力固定
基点とPhase5 remote 5e93a8834e27d4d9ffdbc2980906511f74ddb27aのsrc/tests/notebooksにADX実装は見つからなかった。Wilder式を下記で一意固定。
Volatility Phase1 make_daily/load_m1/to_jst/rank_regime/暦週bootstrap仕様を採用。
src/research/volatility_phase1_frozen_inputs.json（基点固定）の28 StrategyNo/Strategy/Pair/Longを全件照合する。
UJ=USDJPY,EJ=EURJPY,GJ=GBPJPY,AJ=AUDJPY,AU=AUDUSD,EA=EURAUD,GA=GBPAUD。
同JSONのMANIFEST_NAMESの7symbol×8=56 M1ファイルのみ。既存results/volatility_phase1/volatility_phase1_input_manifest.csvの全SHA256一致を必須にする。
欠落・同名複数・重複timestamp・非finite/非正価格・OHLC不正時は中止、補間禁止。
Baseline既存保存先: MyDrive/time-entry-portfolio-lab/daily_stop/baseline_cc32f32e3df5/daily_stop_baseline_trades.csv。
入力未取得ならNOT_RUN_INPUT_MISSING、数値を作らず未完了と記録。別データ・再計算trade・日次代理で代用しない。

## 日次と確定時刻
MT5 M1開始時刻をEurope/Helsinki (ambiguous=infer, nonexistent=shift_forward) → Asia/Tokyo → timezone-naive JST。
実バーのあるJST暦日単位にfirst Open/max High/min Low/last Close。土曜早朝も1 completed trading day。
バーなし日は生成しない。M1Count/LastM1を記録。観測ギャップを埋めない。
DailyDate dのAvailableAt=d+1暦日00:00。EntryのJST日付より前の直近DailyDateを採用。
AvailableAt<=EntryTimeかつLastM1+1分<=EntryTimeを必須とする。00:00 entryは前日使用可。
当日の部分足を使用しない。評価日自身をpercentile referenceに含めない。

## ADX14 Primary（float64、0起点）
i>=1でup=High[i]-High[i-1], down=Low[i-1]-Low[i]。
plusDM=up if up>down and up>0 else 0; minusDM=down if down>up and down>0 else 0。同値は両方0。
TR[i]=max(High-Low,abs(High-Close[i-1]),abs(Low-Close[i-1]))。
i=0のTR/DMは計算に使わずNaN。
14本のi=1..14を単純平均してi=14のWilder平均TR/plusDM/minusDMをseed。
i>14: smooth[i]=(13*smooth[i-1]+raw[i])/14。
DIplus/minus=100*smoothDM/smoothTR。smoothTR=0なら両DI=0。
DX=100*abs(DIplus-DIminus)/(DIplus+DIminus)。DI合計0ならDX=0。
最初のADXはi=27でDX[14..27]の14本平均。以後ADX[i]=(13*ADX[i-1]+DX[i])/14。
ADX以前はNaN。既存実装不在につきこのseedを固定し、別ライブラリのseedへ結果後変更しない。

## ER20 Robustness
ER20[i]=abs(Close[i]-Close[i-20])/sum(j=i-19..i,abs(Close[j]-Close[j-1]))。
20変化/21Closeを使う。初有効index=20。denominator=0ならER=0。
評価日はPrimary同様の直近完了実データ日。

## 252日midrankと等号境界
各方式x[i]のreferenceは直前252 completed trading days x[i-252:i]。評価値と252本全てfiniteが必要。
足りなければINSUFFICIENT_TREND_HISTORY。NaNを飛ばした252値収集、後埋め、共通coverageへの制限禁止。
p=(less+0.5*equal)/252。float64の等値、事前丸めなし。
正確な1/3,2/3でLOW:p<1/3、NORMAL:1/3<=p<2/3、HIGH:p>=2/3。
整数numerator=2*less+equalで、<168 LOW、168以上336未満 NORMAL、336以上 HIGH。
初分類indexはADX279、ER272。ADX14/ER20/reference252/cutは結果後変更禁止。
25/75cut、ADX固定値20/25、別length、戦略別閾値、別trend indicatorの追加禁止。

## 期間・集計・sample
FULL:2015-01-01<=EntryTime<2026-09-10。
補助:Historical [2015,2022),RecentA [2022,2024),RecentB [2024,2026),Monitor2026 [2026-01-01,2026-09-10)。
2022-2026は既閲覧で完全未閲覧holdoutではない。追加期間/窓探索禁止。
各Strategy×Regimeとgroup pooledでTrades,TotalR,AvgR,PF,WinRate%,AvgWinR,AvgLossR（負値）を表示。
R>0勝ち,R<0負け,R=0も分母に含む。PF=正R合計/負R絶対合計。損失0利益ありinf、両方0 NaN。
空cellはTrades=0/TotalR=0/他NaN。HIGH-LOW AvgRとLOW→NORMAL→HIGH値および順序を表示（同値明記）。
cell<20はLOW_SAMPLE=true。個別主要比較eligible=LOWとHIGH双方20以上、NORMALは記述のみ。
Group:Portfolio全28,Long,Short,JPY（USDJPY/EURJPY/GBPJPY/AUDJPY）,AUD_nonJPY（AUDUSD/EURAUD/GBPAUD）。
pooledは全有効trade。各groupのstrategy-equal-weightedはeligible同一戦略集合の各regime AvgR平均。
NORMAL空cell時は等重みNORMAL NaN、集合を変えない。等重みはAvgR/差と対象IDs/数を表示しPF等の平均を作らない。
各期間でeligibilityを再評価。group結果から後付けで対象を絞らない。

## 正式診断条件とCI
FULL Portfolioが正式判定。各methodについて以下全条件でSUPPORTED:
A) pooled HIGH-LOW差の95%週cluster CIが厳密に0を除外。
B) strategy-equal-weighted HIGH-LOW差がpooled差と同符号。
C) eligible strategyの厳密過半数がpooled差と同符号（ゼロは不一致）。
比較不能（eligible0、LOW/HIGH空、CI不能）はUNDETERMINED。それ以外NOT_SUPPORTED。
両method SUPPORTEDかつ同符号=BOTH_SUPPORTED、逆符号=CONFLICTING、片方のみ=PRIMARY_ONLY/ROBUSTNESS_ONLY、
両方不支持=NOT_SUPPORTED、支持なしで比較不能を含む=UNDETERMINED。
CIは正式条件Aに含む。両方式に同一条件を適用。単なる点推定の符号だけを支持とは呼ばない。
補助groupも同条件で探索的表示。個別はeligibleかつCIが0を除外ならCLEAR、その両方式同符号を頑健候補と記述するのみ。
多重比較未調整。NORMALだけが異なる非単調依存はこのHIGH-LOW判定では検出できず、不支持は依存不存在を意味しない。

CI: JST EntryTimeの月曜起点暦週、2014-12-29〜2026-09-07の空週を含む全週。
全戦略/symbolを同じ週clusterとして復元抽出。NumPy default_rng(20260913)、5000反復、各反復元週数の整数抽出。
全method/group/strategyに同じ重み行列。各反復HIGH/LOW R合計と件数から差再計算。
片方0件は無効、4750以上有効を要求。2.5/97.5% linear quantile。等重み/補助期間CIなし。
週を跨ぐ依存・非定常性を完全には扱わない。因果証明・将来filter有効性証明ではない。

## Volatilityとの関係と次段階
既存Volatility Environment Phase1〜4で高VolほどAvgRが高いことを確認済み。
Trend StrengthとVolatilityは相関し得る。Trend単独依存が見つかっても独立情報とは結論しない。
Phase2への正式進行条件をPortfolio BOTH_SUPPORTEDと固定（片方式のみ/逆方向/不支持/判定不能なら進行支持なし）。
Phase2では別事前登録のもと五分位の段階関係とVolatilityを揃えた条件で追加情報を検証する。Phase1では交差分析なし。
後段Economic ValueのBaselineは固定0.9%でなくVolatility R2とし、R2 vs R2 + Trend Strengthを比較する方針を記録。
今回はPhase2やEconomic Valueを実行しない。

## 検証と成果物・実行ゲート
PlanのみGitHub commit→remote SHA確認→研究コード作成。実装SHAも実データ結果計算前にremote固定する。
Baseline hash/16298/28 IDs mapping、56 M1 hash、JST OHLC/last Close/冬夏/土曜/月曜/00:00、
future M1変更・prefix invarianceのno-lookahead、ADX/ER手計算と独立ループ、reference除外/252/等号境界をテスト。
独立集計は別ルートで全period strategy/groupの件数/TotalR/AvgR/PF/WinRate/勝敗平均/差/等重み/eligibility/符号判定を照合。
CIも週別独立合計から照合。代表auditはsymbolごとの初有効ADX/ER分類日および2022-01-03/2026-09-08以後最初のtrade。
代表日OHLCをM1から別集計し指標/reference/entry確定時刻を照合。
既存Volatility daily生成と日付/OHLC/LastM1/M1Count/AvailableAtが一致する回帰検証を行う。
必須CSV prefix trend_strength_phase1_: strategy_primary,strategy_robustness,group_summary,period_summary,regime_coverage,run_record。
追加decision,combined_decision,verification,manual_audit,input_manifest,assignment_audit_lightを保存可。
詳細trade_assignments/daily_auditはlocalまたはColab /contentのみ。GitHubは軽量auditのみ。
src/research/trend_strength_phase1.py、専用frozen入力、tests、notebooks/trend_strength_phase1.ipynb、
docs/71_trend_strength_phase1_result.md、results/trend_strength_phase1/を新規作成する。
Notebook本文にPortfolio/全28Strategy主要結果、/content保存、Drive保存セル初期OFF。
run recordはPlan/実装SHA、input/output hash、coverage、テスト、BaselineRecalculated=false、LiveChanged=false。
Result commitをremote確認しBranch/Plan/実装/結果SHAを最終報告。計画外の分析を追加しない。
