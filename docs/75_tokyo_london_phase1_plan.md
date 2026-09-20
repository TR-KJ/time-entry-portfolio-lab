# Tokyo → London Market Effect Phase 1 — 事前登録 Plan
状態: 実装前・結果未計算。作成日 2026-09-20。
Branch: research/tokyo-london-market-effect-phase1
Base: main 1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5。
既存別branchの74までを確認し、Plan=75 / Result=76を予約。
本PlanだけをGitHubへcommitしてbranch remote SHAを読み返してから実装する。実装も結果計算前にcommitしSHAを記録。

## 目的と保護境界
既存28戦略と独立した将来29〜34番候補の発見に向け、東京の方向XとLondonの方向Yの再現性を診断する。
6個別Primary（固定順）: USDJPY, EURJPY, GBPJPY, AUDJPY, EURAUD, GBPAUD。
Phase 1は価格変化の関係のみ。売買戦略・損益の証明ではない。
Volatility Phase 5 Dell Demo Forward、VPS、EA、SET、live、既存研究成果物を変更しない。
mainを基点とする新規branchへ新規ファイルのみ追加。他branch更新・mergeなし。
30/50pips等の閾値、時刻探索、SL/TP、Risk、Money Simulation、Portfolio追加、Volatility/ADX/ER等との混合禁止。
結果後のpair追加除外・片側採用・pair別window変更禁止。

## データ固定と監査
既存56本=7 symbol×8ファイルのうち上記6symbol×8=48本を使用。AUDUSDは対象外。
不変参照: 5e93a8834e27d4d9ffdbc2980906511f74ddb27a の
results/volatility_phase1/volatility_phase1_input_manifest.csv（blob dcaf2e8e0792bc7c336da7ad834f6e53ae0b8b07）。
同manifestの48ファイル名、SHA256、Rows、FirstRaw、LastRawを凍結コピーし全件照合。
既存MANIFEST_NAMESとも照合。存在のmanifest監査と、実ファイルbyte hash監査を明確に区別。
不足・同名複数・hash不一致・重複UTC timestamp・非正/非finite価格・不正OHLCなら中止。別ソース置換なし。
既存parserのタブ区切りMT5 DATE/TIME/OPEN/HIGH/LOW/CLOSEを使用。
MT5 naive時刻はEurope/Helsinkiでlocalize(ambiguous=infer, nonexistent=shift_forward)、UTCへ変換。
同じUTC timestampからAsia/TokyoおよびEurope/Londonへ変換。timezone変換規則は既存volatility_phase1.pyに整合。
時刻調整件数を監査し、重複が発生すれば中止。価格補間なし。
必要endpointのみを使うが、全入力OHLCとtimestampの整合は監査する。
最終sourceは2026-09-09 00:00 MT5まで。9/9のwindow不足を埋めず欠損に記録する。

## 日付・価格・coverage
JST暦日dの月〜金、2015-01-01〜2026-09-09 inclusiveを候補日とする。祝日もバーの有無で判定。
同じ日付dについてJST09:00, JST15:00, London08:00, London11:00のexact M1 Openを取得。
Primary X=(JST15 Open-JST09 Open)/pip、Y=(London11 Open-London08 Open)/pip。
Robustness X=(London08 Open-JST09 Open)/pip、Yは同じ。
JPY pip=.01、EURAUD/GBPAUD=.0001。差はfloat64、事前丸めなし、betaはdimensionless。
exact以外のfallbackなし。途中バー欠落はendpointが揃えば除外しない（integrated path指標を使用しない）。
Primaryは4 endpoint全て、Robustnessは09/08/11の3 endpointが必要。独立のcoverage集合、共通集合への後付け限定なし。
欠損日には不足endpointを全て記録（sorted pipe-separated reason）、欠損を0 returnにしない。
pair×date×methodは一意。Tokyo開始<Primary終了<London開始<London終了。
Robustness終了=London開始。共有境界Openは時刻上重複区間を作らないが境界価格を共有する限界を明記。
各pair×period×methodに候補平日数、valid日数、除外日数、理由別件数、観測暦週数を表示。
理由別件数は複数欠損日で重複計上し得るため、総除外日数と区別。

## 固定期間
Historical 2015-01-01〜2021-12-31
RecentA 2022-01-01〜2023-12-31
RecentB 2024-01-01〜2025-12-31
Monitor2026 2026-01-01〜2026-09-09
RecentCombined 2022-01-01〜2026-09-09
ALL 2015-01-01〜2026-09-09
全てinclusive。2022〜2026はpristine unseen holdoutではない。
正式評価には>=80 valid daysかつ>=20観測calendar weeksを要求。
不足はINSUFFICIENT_SAMPLE。記述統計は残すが正式gateで同符号として数えない。
Xの分散0はDEGENERATE_Xとして評価不能。Y分散0はr/R²未定義とし正式評価不能。
0 betaは同符号と数えない。

## 回帰・不確実性・p値
各pair×method×period: 切片ありOLS Y=alpha+beta X。
N、観測週数、alpha、beta、Pearson r、R²、X/Y mean, median, sample std(ddof=1)を保存。
calendar-week cluster pairs bootstrap B=5000、NumPy default_rng(20260913)。
各期間の開始日を含む月曜〜終了日を含む月曜の全暦週（空週込み）をcluster集合とする。
各反復で元の暦週数Kを復元抽出。選ばれた週内の全日を一括して保持しOLSを再推定。
期間ごとにseedをresetし、同じ期間の全pair/methodで同じ抽出重みを共有。
有効bootstrapはfinite betaかつX,Y分散正。>=4750有効反復を要求、未満はBOOTSTRAP_INSUFFICIENT。
CIは有効beta*の2.5/97.5 percentile、linear補間（percentile CI）。
H0 beta=0の両側bootstrap p値は中心化分布を使用:
p=(1+count(abs(beta* - beta_hat)>=abs(beta_hat)))/(1+B_valid)。
これは近似bootstrap検定であり、CIと検定の双対性は仮定しない。A/Bは別条件。
全期間のCI/pを計算可能な範囲で表示するが正式多重検定はALL Primaryの6個のみ。
Holm: 6個のpを昇順（tieは固定pair順）に並べ、
adjusted p_(i)=min(1,max_{j<=i}((6-j+1)*p_(j)))。unadjustedとadjustedを保存。
評価不能pは補正計算用1、元pはNaNのまま、該当gateはFAIL。
alpha=.05、adjusted p<=.05でB PASS。period/robustnessの検定は補助、多重比較調整なし。
週を跨ぐ依存・構造変化を完全には扱えず、因果効果も確証しない。

## pair formal verdict（変更禁止）
A: 評価可能ALL Primaryの95%CIが厳密に0を除外。
B: 同ALL Primary Holm adjusted p<=.05。
C: HistoricalとRecentCombinedが双方評価可能かつ両betaがALL Primary betaと同じ非ゼロ符号。
D: RecentA/RecentB/Monitor2026のうち>=2期間が評価可能、かつ少なくとも2期間のbetaがALLと同じ非ゼロ符号。
   3期間という固定母集団を維持。1/1一致を通過にしない。不足期間はINSUFFICIENT_SAMPLEと明示。
E: Robustness ALLが評価可能で、そのbetaがPrimary ALLと同じ非ゼロ符号。
評価可能はsample、非退化、bootstrap有効反復の条件を全て満たすこと。
A〜E全PASSかつbeta<0: REVERSAL_SUPPORTED、beta>0: CONTINUATION_SUPPORTED。
それ以外: NOT_SUPPORTED（評価不能理由も保存）。不存在の証明とは解釈しない。

## direction diagnostics / Family
各pair×method×periodでX>0(UP)、X<0(DOWN)、X==0(NEUTRAL)の件数を表示。
UP/DOWN: Y mean/median、reversal rate=sign(X)*sign(Y)<0の割合、
continuation rate=>0の割合、Y==0のneutral率。分母は各UP/DOWN群全日、Y==0も含む。
X==0はUP/DOWNから除外し別行で件数/Y統計、reversal/continuation率はNaN。
この表はgateでも片側採用根拠でもない。
Family: JPY=4JPY、AUD-cross=EURAUD/GBPAUD、All-6=参考。
各period/methodで固定構成pairのPearson r（standardized beta）の単純等重み平均。
raw pips pooling禁止。構成pairの一つでも評価不能ならfamily平均NaN/INCOMPLETE。
FamilyはDESCRIPTIVE_ONLY、正式支持判定・Phase2進行条件に使用せず、family CI/pは算出しない。
Familyが弱くてもSUPPORTED pairはPhase2候補。

## Phase 2 conceptual plan — formal Hard Gate PENDING
Phase 2では東京値動きの大きさと効果の強さを検証する。
基本案はQ1〜Q5、Q5−Q1、Recent/Robustness確認だが、正式判定条件はPhase 1完了後、
Phase 2のデータを一切計算・閲覧する前に別Planで事前登録する。
対象案はPhase1 SUPPORTED pairのみ。abs(TokyoReturn)をpair自身の直前252 valid trading daysでmidrank percentile化し、
Q1〜Q5（0–20/20–40/40–60/60–80/80–100）で形状診断。Phase1方向に合わせたAlignedLondonReturn案。
Q5−Q1、recent stability、robustness、monotonicity/Spearmanは基本案に留める。
Hard Gate/補助条件/多重比較/UP-DOWN非対称性を次の別Planで正式固定し、結果を見て決めない。
本Phaseではpercentile、Q assignment、AlignedLondonReturn、Q結果を一切計算・閲覧しない。

## Phase 3以降（実施しない）
Phase1→2通過pairだけ有限Entry/Exitグリッドを別Planで固定し独立time-entry戦略を検討。
29_London_UJ / 30_London_EJ / 31_London_GJ / 32_London_AJ / 33_London_EA / 34_London_GAは名前案のみ。
単独Historical/Recent/OOS-like、Money Simulation、現行Portfolio追加価値は後続別Phase。
最終目的はTotal Profit増大、profitを悪化させるDD改善だけで採用しない。

## Validationと成果物
48 source hashes/rows/raw bounds照合、timezone Helsinki/UTC/JST/London（DST境界含む）、
exact endpoint・欠損除外・pip・pairing uniqueness・no-overlap/no-lookaheadをテスト。
回帰は独立np.linalg.lstsq/中心化集計照合、Holmは独立step-down実装照合。
bootstrap spot-checkは同一抽出週を日次行で実際に複製し回帰し直してCIも照合。
代表manual audit=6pair×London夏/冬×Primary UP/DOWN=24例。
各stratumでALLの最初のvalid dateを固定選択（Y/効果量で選ばない）、存在しなければMISSING_STRATUM。
4 endpointのraw/UTC/JST/London時刻、Open、pip、差を元CSVから独立再読込/Decimal再計算して人が確認できる表にする。
本番結果は独立回帰と全gate再構築で照合。
新規src/research/tokyo_london_phase1.py、tests/test_tokyo_london_phase1.py、notebooks/tokyo_london_phase1.ipynb、
入力manifest、results/tokyo_london_phase1/、docs/76_tokyo_london_phase1_result.md。
CSV prefix tokyo_london_phase1_: pair_summary, period_summary, direction_summary, family_summary,
coverage, multiple_comparison, run_record、input_audit、validation、manual_audit、publication_manifest。
日次assignmentとexclusionsはlocal/Colab保存、GitHubは軽量集計とhash/rows manifest。
Notebookは6pair beta/CI/verdict、robustness、period stability、UP/DOWN、family、coverageを表示。
CSVは/contentへ保存。Drive保存cellはdefault OFF。
run record: Plan/Implementation SHA、実行日時、依存version、input/output hash、seed/B、
Phase2Computed=false、LiveChanged=false、既存ファイル無変更確認。
入力にアクセスできない場合はNOT_RUN_INPUT_MISSING、統計欄は未計算として数値やverdictを捏造しない。
