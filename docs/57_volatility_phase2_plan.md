# Volatility Environment Phase 2 — 事前登録計画
状態: 実装前固定。Phase 2実データ集計・コード作成は未実施。
Branch: research/volatility-environment-phase2
基点・Phase 1正式結果SHA: cafbb6ff0bfe81e439b80ed62d50498494814e86
Docs: 57 Plan / 58 Result（mainおよびPhase 1の既存番号を確認済み）。

## 目的・研究境界
「Volatilityが高くなるほど期待値が段階的・概ね単調に上昇する関係があるか、それともPhase 1の三分位切りによる見かけの差か」を、粗い固定5分位で診断する独立研究。
閾値最適化ではない。因果関係、将来filter有効性、利益額最大化の証明ではない。
固定28戦略・16,298 trades（22を含む）、Baseline byte SHA-256:
cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
Baselineを再計算せず、Daily Stopなし、ATR OFF、Event Candidate C、UJ12/EJ1修正済みを継承。
Entry除外0件。EA/VPS/SET/liveコード・設定変更禁止。旧H1 ATR14 P70（ATR70）研究とは別物。

## 固定するPhase 1正式知見
Portfolio Primary LOW +0.058280 / NORMAL +0.080507 / HIGH +0.135495、
HIGH-LOW +0.077215R、95%CI [+0.039863,+0.114764]。
Robustness LOW +0.053973 / NORMAL +0.096958 / HIGH +0.121145、
HIGH-LOW +0.067172R、95%CI [+0.030311,+0.102266]。
strategy-equal-weightedも同方向。十分標本の符号一致Primary 21/25、Robustness 22/25。
両方式個別明確: 1_EJ_Log1、6_GJ_Old_Mon、12_UJ_Short_Core、23_GA_F_2。
LOWでもPortfolio AvgRは正。Phase 1 Entry除外0件。
正式CSVの丸め前値を回帰照合に使い、上記6桁は報告値として固定する。

## 変更しない入力・feature定義
Phase 1の src/research/volatility_phase1.py および frozen_inputs.json を基点SHAのまま再利用する。ファイルSHA-256を記録・検証し変更しない。
監査済みM1 7 symbol×8ファイルはPhase 1 manifestとファイルbyte hashが全件一致することを要求する。
MT5 M1開始timestamp Europe/Helsinki（ambiguous=infer、nonexistent=shift_forward）→Asia/Tokyo→naive JST。
JST実データ日OHLC=first Open/max High/min Low/last Close。土曜早朝も実バーがあれば1 completed trading day。
空日・欠損を補間しない。DailyDate=dは翌暦日00:00から参照可能。
EntryのJST日付より前の直近実データ日を使い、AvailableAt<=Entry、LastM1+1分<=Entryを検証。
TR=max(H-L,abs(H-prevC),abs(L-prevC))、初日TR=H-L。
Primary ATR20=TRの20日単純平均。Robustness=20個log(C/prevC)のsample std(ddof=1)*sqrt(252)。
評価値x[i]の参照はx[i-252:i]で評価日を含めない。252本全てと評価値finiteを要求、NaNを飛ばさない。
midrank p=(less+0.5*equal)/252。float64の厳密比較、丸めなし。
履歴不足はINSUFFICIENT_VOL_HISTORYとして全assignment/coverageへ残す。method間の共通coverageへの追加制限なし。

## 5分位境界（実装前一意固定）
percentile表示は100*p。Q1=[0,20)、Q2=[20,40)、Q3=[40,60)、Q4=[60,80)、Q5=[80,100]。
20/40/60/80の等号は上側、0はQ1、100はQ5。
Phase 1の整数分子 n=2*less+equal（0..504）、p=n/504をそのまま使用する。
5*n <504→Q1、<1008→Q2、<1512→Q3、<2016→Q4、その他Q5。
従ってn=0..100/101..201/202..302/303..403/404..504。
有効なnから20/40/60/80%ちょうどは発生しないが、公開percentile境界関数には上記半開区間仕様を適用し境界テストする。
保存percentileから分子を復元する場合はn=round(p*504)、abs(p-n/504)<=1e-12かつ0<=n<=504を要求。任意percentileや不正値を黙って丸めない。
Phase 1三分位も同じnで<168 LOW、<336 NORMAL、その他HIGHとして回帰照合。

## 分析対象・期間
主対象FULL: 2015-01-01 <= EntryTime < 2026-09-10。
1. 全28 Portfolio trade-weighted pooled Q1〜Q5。
2. strategy-equal-weighted Q1〜Q5。
3. 全28戦略個別Q1〜Q5（結果による表示選別なし）。
4. 上記1/6/12/23は事前サブグループとして詳細表示。独自threshold・別定義・専用cutを作らない。
5. Phase 1と同じ補助group: JPY（UJ/EJ/GJ/AJ）、AUD_nonJPY（AU/EA/GA）、Long、Short。
補助期間はHistorical 2015–2021、RecentA 2022–2023、RecentB 2024–2025、Monitor2026（〜9/9）のみ。
期間別は同じ全28個別・groupを記述表示し、正式全期間判定を上書きしない。追加窓探索禁止。
2022–2026は既閲覧で、完全未閲覧holdoutではない。

## 指標・標本ルール
各pooled/strategy cell: Trades、TotalR、AvgR（主指標）、PF、WinRate%、AvgWinR、AvgLossR（負値）。
R>0勝ち、R<0負け、R=0も件数分母。PF=正R合計/負R絶対合計、損失0利益ありinf、両方0 NaN。
空cellはTrades=0/TotalR=0/その他NaN。strategy×quintile <20ならLOW_SAMPLE=true。
個別正式判定はQ1〜Q5全cell各20件以上が必要。一つでも不足ならLOW_SAMPLE（非支持と混同しない）。
strategy-equal-weightedはmethod×period×groupごとに全5cell各20以上を満たす戦略集合を固定し、5つのAvgRを同一集合で平均する。
対象ID/数を表示。集合0ならAvgR NaNかつUNDETERMINED。pooledは小標本戦略も全有効tradeを含む。
等重みにはAvgRとその差・単調性のみ。TotalR/PF等をpooled統計と混同して作らない。
Q5-Q1、Q2-Q1、Q3-Q2、Q4-Q3、Q5-Q4を表示。
Spearman=quintile番号1..5と5個のAvgRの順位相関（同順位average rank）。
全AvgR同値、欠損ならSpearman NaN。完全同値の有効5cellは関係不支持。
adjacent increaseは厳密に>0のみ。0は増加に含めない。
完全単調増加=4差すべて>0。非減少=4差すべて>=0も補助表示。完全単調は必要条件にしない。

## 正式解釈ルール（結果後変更禁止）
FULL・各methodのPortfolioで下記全条件を満たすとORDERED_POSITIVE_SUPPORTED:
A1 pooled Q5-Q1 >0
A2 pooled Spearman >0
A3 pooled adjacent increases >=3/4
A4 strategy-equal-weighted Q5-Q1 >0
A5 strategy-equal-weighted Spearman >0
等重みのadjacent >=3は追加必要条件にしないが数値表示する。
pooledに空cell、等重み集合0など比較不能ならUNDETERMINED。他はNOT_SUPPORTED。
CIは補助であり上記正式条件には入れない。CIが0を跨ぐ場合も隠さず記載し、統計的有意性や確証的発見と呼ばない。
個別戦略はeligibleかつA1/A2/A3を満たせばORDERED_POSITIVE_SUPPORTED、そうでなければNOT_SUPPORTED。不足はLOW_SAMPLE。
補助groupはPortfolioと同じA1〜A5を適用するが多重比較未調整の記述的診断であり主結論を変更しない。
補助期間はDESCRIPTIVE_ONLY。
両方式支持→BOTH_SUPPORTED（頑健に支持）。
Primaryのみ→PRIMARY_ONLY、Robustnessのみ→ROBUSTNESS_ONLY、両方不支持→NOT_SUPPORTED。
片方/両方判定不能ならUNDETERMINEDとし、判定可能側の結果も併記する。
不支持は関係不存在の証明ではなく、この事前規則を満たさなかったという意味。

## CI（Phase 1と同じ暦週cluster bootstrap）
FULL Q5-Q1のpooled Portfolio、補助group、全28個別に95%CI。
JST EntryTimeの月曜00:00始まり。2014-12-29週〜2026-09-07週を空週込みで並べる。
各反復で元の週数を復元抽出、同じ週内全戦略/通貨のtradeを一緒に再標本化。
NumPy default_rng seed=20260913、5000回、Phase 1 bootstrap_weightsを再利用。
全method/group/strategyに同じ週重み。各反復のQ5とQ1のR合計/件数から差を再計算。
Q1またはQ5が0件の反復は無効。4750以上の有効反復でのみCI、未満はNaN。
2.5/97.5 percentile linear補間。等重み・adjacent・periodのCIは作らない。
週を跨ぐ自己相関・非定常性を完全には扱えない。多重比較未調整。

## 次段階
PortfolioがBOTH_SUPPORTEDの場合のみ、Phase 3を別研究・別事前登録として検討する。
候補は(a) Volatility-based Risk Allocation、(b) Entry Filterのどちらが利益額最大化に適するかの比較。
Phase 1 LOW AvgRが正なのでRisk Allocationを優先仮説とするが、Phase 2結果で採用しない。
その他の判定ではこの分岐によるPhase 3進行条件を満たさない。
10分位/4分位/任意percentile・ATR20/252/RV20変更・Q4以上等threshold採用・Risk%最適化・Entry ON/OFF Money Simulation禁止。

## 検証・実行順序
1. Phase 1コード/正式結果/manifest確認（本計画前に実施）。
2. 本PlanのみGitHubコミット。remoteからSHAと本文・Planのみの差分を読み返して確認。
3. その後にPhase 2コード/Notebook/テストを作成。実データ集計前に実装commitをremote確認する。
4. Baseline hash/件数/全ID、全M1 hashを照合してfeature再計算。Phase 1コードは不変import。
5. 同じfeatureからPhase 1三分位の全期間/補助期間個別・group統計、coverage、HIGH-LOW CIを正式CSVと照合（浮動小数絶対許容1e-10、報告6桁値は5e-7）。
6. 5分位0/20/40/60/80/100・近傍/NaN/範囲外、全整数n=0..504、midrank等値、履歴不足、標本19/20、空/同値/3of4/2of4、共通等重み集合をテスト。
7. no-lookaheadはPhase 1既存テストに加え、未来M1改変時の既存Entry assignment/5分位不変を確認。
8. 独立集計: 主実装のgroupbyに対してcsv/Decimalまたはmath.fsumで件数/TotalR/AvgR/PF/WinRate/平均勝敗/差/等重み/順位/判定を照合。
9. representative manual audit: Phase 1各symbol初有効ATR/RV日、2022-01-03/2026-09-08以降最初tradeの固定選定を継承し、OHLC/TR/ATR/RV/252参照/midrank/quintileを照合。
加えて各method×strategy×quintile最初tradeとstrategy最後tradeを軽量audit表示（結果サイズによる選別禁止）。
10. 結果CSV・Notebook主要表・Result文書を保存し結果commit SHAをremote確認。

入力不足時はNOT_RUN_INPUT_MISSINGとして不足ファイルを記録し、数値・検証PASS・正式判定を捏造しない。
完全版assignment/dailyだけからの未検証置換は正式実行としない。正式実行に必要な元Baseline/M1取得後、同じ固定計画・実装で再開する。

## 成果物
docs/57_volatility_phase2_plan.md、docs/58_volatility_phase2_result.md
src/research/volatility_phase2.py、tests/test_volatility_phase2.py、tests/verify_volatility_phase2.py
notebooks/volatility_phase2.ipynb（Q1→Q5 Portfolio両方式・等重み・差/CI/判定・4戦略・群を本文表示）
必須CSV:
- volatility_phase2_portfolio_quintiles.csv
- volatility_phase2_strategy_quintiles.csv
- volatility_phase2_group_quintiles.csv
- volatility_phase2_period_quintiles.csv
- volatility_phase2_monotonicity_summary.csv
- volatility_phase2_run_record.csv
補助coverage、input_manifest、verification、manual_audit、assignment_audit_light、phase1_regressionを許可。
完全trade assignments/dailyはlocal/Colab /contentのみ。GitHubはresults/volatility_phase2/軽量版。
Colab保存先初期/content、Drive保存セル初期OFF。ローカルは作業環境の明示outputディレクトリに保存。
run record: Plan/Implementation/Phase1 SHA、入力/出力hash、coverage、実行日時、環境、検証結果、BaselineRecalculated=false、EntryTradesRemoved=0、LiveChanged=false。
結果SHAは自己参照回避のため最終報告とremote commit URLで確認する。
