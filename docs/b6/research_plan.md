# B6 Recent-Era Time-Entry Rediscovery — Stage6 Validation 実装Freeze

状態：STAGE6 IMPLEMENTATION FREEZE。Stage5候補50件・Validation Contractのexact identityを再確認し、条件不変の2024–2025 Validationコード/tests/Colab Notebookを実装する。Workは本番Validationを実行せず、Chat確認後Colabへ分離する。
根拠：[source_of_truth.md](source_of_truth.md)、数値の分類：[parameter_decision_register.md](parameter_decision_register.md)。

## 目的・禁止範囲（合意済み）
2020〜2023のM1から独立した時間エントリー候補を発掘する。Baselineの取引並べ替えはしない。
既存27/28戦略の時刻・SL/TP・曜日、EA、SET、VPS、live、Dell Demo Phase 5、RunId、Global R2、既存研究を変更しない。
候補IDは `B6-{symbol}-{L|S}-W{0..4}-E{0000..1439}-H{minutes}`。後段条件は別variantキーへ正規化し、正式Strategy番号を割り当てない。
将来は「現行27＋Global R2」と「同構成＋B6」の追加利益・terminal wealthを比較する。Validation通過をlive許可としない。

## Stageと固定順序（合意済み）
|Stage|実施内容|固定対象|
|---|---|---|
|0|source、入力、隔離、約定互換性|既存を変更しない|
|1|ペア×方向×Entry曜日、Entry/Exit 5分刻み、固定SL5種、TPなし|開始前に探索範囲・SL・選定手順|
|2-A|残った時間構造×各SL5種の有限TP比較（TPなし含む）|ペア・方向・曜日・Entry/Exit|
|2-B|有望組合せ周辺のSL/TPを5pips刻みで調整|同上|
|3|SL/TP固定、狭い時刻範囲を1分刻みで追加最適化し最終時刻を選ぶ|ペア・方向・曜日・SL/TP|
|4|限定Event Filterの追加価値|前段の売買条件|
|5|Discoveryのみで最終Candidate・判定規則をFreeze|ID、全条件、入力・コード識別情報|
|6|remote SHA確認後に2024、2025、合算Validation|変更禁止|
|7|通過候補の2026 Monitor|Formal Validation判定を変更しない|

SLなしは任意の参考比較だけで正式6候補目にしない。今回はその参考計算も行わない。
Stage 1でSLを1値に絞らず、時間構造の5結果を後段に渡す。落選時間帯を1分総当たりで救済しない。
Stage 3以後SL/TPへ戻らず、Event Filter後も再調整しない。後段落選時に順位外から補充しない。
曜日はEntry日のJSTで月〜金を個別候補とする。曜日の部分集合探索・追加統合は行わない。
表記上の曜日集約は条件変更とは区別し、候補IDは維持する。

## 期間・execution（合意済み）
Discovery `[2020-01-01,2024-01-01)`、Validation `[2024-01-01,2026-01-01)`、Monitor `[2026-01-01,2026-09-10)`、実際のM1終端は監査出力を使う。
Validationは既閲覧の **B6 holdout validation / OOS-like**。pristine unseen OOSとは呼ばない。
Workで許可する実集計は限定したDiscovery smoke/互換検証だけ。研究としてのTop Candidate/ranking本結果は出さない。全探索はColabへ分離する。
56ファイル全体は入力同一性・品質監査に限って読み、監査関数内でJST変換後にDiscovery配列をcopyして返す。
2023/2024同居ファイルも行時刻で隔離。期間外配列をexecutorへ渡すと例外にする。
予定Exitが期間外ならSL先着でも対象外。fallback探索中に境界を越えた場合も対象外。欠損をゼロ損益にしない。

Helsinki→Tokyo naive、DST ambiguous=infer / nonexistent=shift_forward、重複JSTは拒否。
JPY=.01、非JPY=.0001。固定SpreadはUJ .5 / EJ 1 / GJ 2 / AJ 1.5 / AU 1.5 / EA 1.5 / GA 2 pips。
Entry完全一致Open±Spread、SL/TPは調整Entry基準。Entry足・選択Exit足を含めM1 High/Lowを走査、同一足SL first。
先にExit exactまたは+1〜+4分を確保し、なければ途中SLがあっても取引なし。+5分不採用。
途中欠損は補間しない。SL/TP固定価格約定、raw比較にepsilonや新しい価格丸めを入れない。
到達なしのときだけExit Open決済。午前0時強制決済なし、週末後の月曜価格へ自動接続なし。
取引表示Pipsは小数6桁、Rは丸め前Pips/SLを小数9桁（Baselineに合わせる）。Stage1指標・rankingは丸め前Rを使い、reference/fast双方で同じ順序で集計する。設定pipsの5刻み丸めと約定価格を混同しない。
`missing_path_minutes`、`ExitDelayMinutes`、`exit_bar_first_hit`を記録。Exit足High/Low先行はOpen先行決済と異なる。
互換性は実市場との完全一致や候補間の誤差相殺を保証しない。今回は別約定モデルを実装しない。

## 正式採用条件（2026-09-28）

旧Pure Time-Entry / Time-Exit、SL/TPなし案から **Time Structure Discovery with 5 Fixed SLs / TPなし** へ、Chatで正式に研究設計を変更した。実装ミスではない。事前較正した5SLだけを使用し、Stage1でSL連続最適化を行わない。

正本configは `research_inputs/b6/stage1_config.json`。`proposal.json`とStage0結果は2026-09-27の準備記録であり、現行設定ではない。
### Stage 1
保有30〜1440分、5分刻み、年末年始12/25〜1/3停止（Entry日のみ）を正式採用。
予定保有時間の制限でありSL/TP早期決済を禁止しない。全段階の時刻調整にも同じ予定保有限界。
各SLを別々に評価し、取引>=150、各年>=30、PF_R>=1.10、4年中3年以上TotalR>0を同時に満たすこと。
負け取引>=10を正式採用。DDはStage1の絶対閾値を置かず、下記第4順位にする。
時間構造は5SL中3以上が通過した場合のみ通過。全5SLの値を保持し、5SLの中央値AvgRを主順位とする。
順位は **全5SL Median AvgR降順 → PassSLCount降順 → 全5SL Median TotalR降順 → 全5SL Worst MaxDDR昇順 → symbol, direction(L先), weekday, entry_minute, exit_day_offset, exit_minute昇順**。PF/WinRate/Recovery Ratioを主要rankingに使用しない。3/5・4/5・5/5は個別保存。
PF_pipsとPF_Rは一定SL単体では同値だが、SL間のpipsをプールしてPF/rankingを作らない。
DDはCloseTime, EntryTime, CandidateID順にR累積、初期peak=0。丸め前の内部計算値で比較し、表示丸めで順位を変えない。
各年のプラス判定は同じSLについて行う。SLごとに有利な年を継ぎ足さない。

### 近接整理と50枠
通過時間構造を上記の全順序で走査し、未抑制の先頭を代表として採用。
同一symbol/direction/weekdayかつExit day offsetが同じで、EntryとExitの循環距離 `min(|a-b|,1440-|a-b|)` が双方<=30分、保有差<=30分の未処理候補をその代表へ割り当てる。
連結成分による連鎖併合はしない。代表との直接距離だけなので入力順に依存しない。
offset違い、短時間と24h近辺を循環距離だけで混ぜない。抑制先ID・距離を保存。
全体上位最大50時間構造（ペア別割当なし）。SL/TP違いは枠を増やさない。50未満なら水増ししない。
理由：最良SL一点への依存を下げ、時間帯重複で枠を埋めない。代替の「1SL通過」は多く残すが過適合リスクが高い。

### Stage 2-A（2026-09-29 実装Freeze）
Stage1はColabで4,032/4,032 job、COMPLETE_STAGE1_ONLY、通過689,738構造、代表50件で完了（ユーザー報告。候補bytes・identity・progressはローカルでも確認）。
Stage1 Freeze `920b9be5c8f1bcf46a46dbbd4ac06dc19eb295b1` を変更しない。
正式入力は `stage1_selected_structures.json` の正確な50件。SHA256 `82a71c1ac9ffaa9a121795c6e0186bf77af5185b90bc21f65d7174161c35214f`。
Stage1 effective config SHA256 `93cc9a92c6473cf770f98b72511de076375411db1c27ae1568f976f96212b37e`、identityのcode SHAもhard gate。
再探索・再ranking・再cluster・候補の追加/削除/交換・ペアや曜日の枠補正は禁止。入力順と時間構造を保持する。
各候補の固定5SLについてTP_NONE＋0.5/1/1.5/2/3Rを比較。Decimal half-upで5pips単位へ丸め、最低5pips、同一SL内の有限TPを重複除去しTP_NONEを維持。
SL25×0.5は15pips。7ペア全固定SLで6条件、50×5×6=1,500を事前検算し、不一致なら停止する。
Discovery 2020〜2023だけで1,500条件すべて評価・保存。P02 gateはPass/Failと理由を付けるだけで早期打切りしない。
丸め前Rで全期間・年別の件数/勝敗/PF/AvgR/TotalR/MaxDDR、全期間0R/WinRate/AvgWinR/AvgLossRを計算。SL/TP/TimeExit、fallback、欠損機会・途中欠損を保存。
既存executionは変更しない。参照replayとTP first-hitを加えた専用fast adapterを比較し、同一足はSL優先、Exit確保前の経路救済なし。
Stage2-A単体の機械設定は `research_inputs/b6/stage2a_config.json`、詳細は `stage2a_implementation.md`。Stage2-A単体は中心選定を行わない。今回追加するStage2-Bの正式規則は次節。

### Stage 2-B（2026-09-29 N06b正式固定・実装Freeze）
Stage2-AはColabでCOMPLETE_STAGE2A_ONLY、50候補/1,500条件、PASS1,281・FAIL219で完了。正式8ファイルの実bytes・hash・schema・行数・全設定キー・年別集計・gate・Stage1/2-A provenanceを検証する。Review ZIPを科学的入力にしない。
Stage2-A Freeze `50f83f3904acc3bc3abe54204db7a2ab4964b024`、config SHA `bab7eced359ad914e63b6a13dd6c956f86c9b7f695f9b8fc622b2c8f9e4685d6`。8ファイルの正確なruntime SHAは `stage2b_config.json` に固定。
Stage1の50件・時刻構造、Stage2-A粗Gridは変更しない。候補追加/交換/再cluster/粗探索やり直しなし。

**中心選定：P02 PASS設定のみ。** GrowthはAvgR↓→TotalR↓→MaxDDR↑→TP_NONE優先→SL↑→TP↑→固定キー。
EfficiencyはTotalR/max(MaxDDR,1)↓→AvgR↓→TotalR↓→MaxDDR↑→TP_NONE優先→SL↑→TP↑→固定キー。
両者が同じSL/TPなら1中心に統合し両aliasを記録、次点による2中心目の補充なし。PASSなしなら0中心。

各中心からSL±10、finite TPはTP±10を5pips刻み。TP_NONEはSL軸のみ。SL[10,300]、TP[5,900]外は除外・補充しない。端が良くても範囲延長なし。
重複SL/TPは一度だけ評価しGrowth/Efficiency/両方のaliasを保存。全局所設定を評価しP02は途中pruningに使わない。
理論上限50条件/構造、2,500条件/50構造。実装上限も2,500。actual unique数は本番の入力監査・中心選定後に別表示する。Workでは実候補Centerを選定しないためactual未算出。

**近傍：Centerの局所Grid内で別々に計算。** finiteはSL/TP±5の最大3×3、TP_NONEはSL±5の最大3点。自身を含み、bounds外やそのCenterのGrid外を入れない。
点自身P02 PASS、近傍PASS比率>=2/3、近傍Median AvgR>=点AvgR×0.8を全て要求する。今回指示にない最低3近傍条件は加えない。境界の2点近傍も評価する。
重複点は各Centerで判定し、**いずれかでPASSなら候補、正式順位が高いPASS側の近傍指標を採用**。この解釈は本タスクでユーザー確認済み。全Center別診断も保存する。
距離は5pips格子L1、TP_NONEはSLのみ、aliasの最小距離を使用。

**各構造で最終1設定：** Neighborhood Median AvgR↓→Neighborhood PassRate↓→点AvgR↓→CenterDistance↑→MaxDDR↑→TP_NONE優先→SL↑→TP↑→固定キー。
固定キーはSymbol/Direction/Weekday/EntryMinute/ExitDayOffset/ExitMinute/HoldingMinutes/CandidateID昇順。同一点のCenter別指標まで完全同値ならSourceCenterType辞書順で診断を決定する。
安定点なしはSTAGE2B_DROPPED_NO_STABLE_POINT、中心なしはSTAGE2B_DROPPED_NO_P02_CENTER。50枠を補充しない。
選定SL/TPは固定し再探索へ戻らない。Stage3は次段予定で、今回実装・実行しない。
Reference/Fast・metricsは凍結Stage2-Aをimportして利用し変更しない。Discovery2020〜2023、SL-first・Exit確保優先・raw比較・丸め前Rを継承。
詳細は `stage2b_implementation.md`。新Notebookの全実行/準備/Driveフラグは既定False。

### Stage 3（2026-10-01 正式実装Freeze）
正式入力はStage2-B selected settingsのみ。Driveの `b6_stage2b_archive` を特定し、COMPLETE_STAGE2B_ONLY、1,042条件、selected50・drop0・全TP_NONE、Stage3/Validation/Monitor未実行を正式成果物間で再監査した。
Stage2-B Freeze `686b4b8b479055e3ff43a21f450b1a7182367ebe`、selected SHA `476bad8f65b896d9c76a52dcf22f7c68381e22c0235523253fbdaa7ad1010a5b`。入力14ファイルのexact SHA・CSV schema/行数を `stage3_config.json` に固定。Review ZIP代用・再生成・repairは不可。

Symbol/Direction/Weekday/Stage2-B selected SL/TPを固定。Stage1から継承したEntry/Exit/ExitDayOffsetをOriginal5mAnchorとする。
Entry/Exit予定datetimeそれぞれに-5〜+5分を1分刻みで一度だけ加算。Entry日・曜日を変更する点、ExitDayOffsetが変わる点、調整後保有30〜1440分外は無効。別日へwrap・無効点補充・範囲拡張・再anchorなし。
最大121点/候補、50件で6,050。TheoreticalMax/CandidateCount/RawGridPoints/InvalidSchedulePoints/ActualUniqueConfigurationsを別保存。Stage3 Colab正式runtimeのactualは5,705、無効345を今回再監査済み。
全有効時刻点を評価してP02を表示・保存し、途中pruningなし。Discovery2020〜2023のみ。凍結Stage2-A execution/metricsをimportし、raw比較・SL-first・Exit0〜4先確保・欠損非生成・丸め前Rを維持。

近傍はEntryDelta/ExitDelta各±1の3×3、自身を含む正式Grid内の評価済み有効点のみ。無効/範囲外点を0扱いしない。
点自身P02 PASS、近傍2/3以上P02 PASS、近傍Median AvgR>=点AvgR×0.8を全て要求。最低近傍数を追加しない。NeighborhoodCountを診断保存。
**正式選定はNeighborhood Median AvgR降順 → AnchorDistance昇順 → 固定時刻キーのみ。**
AnchorDistance=abs(EntryDelta)+abs(ExitDelta)。固定キーはAdjusted Entry分→Adjusted ExitDayOffset→Adjusted Exit分→EntryDelta→ExitDelta→CandidateID昇順。
Point AvgR/PF/DD/TotalR/WinRate/Neighborhood PassRate/Stage2-B scoreはtie-breakに入れない。診断のみ。
安定点なしはSTAGE3_DROPPED_NO_STABLE_TIME。他候補で補充せず、SL/TP探索・時刻再最適化へ戻らない。
選定結果は時刻・offset・保有・SL/TPを固定したStage4入力候補。Stage3本番は完了済み。Stage4もColab完了済み。今回はStage5で正式selected全件を固定する。

### Stage 4
候補は最大3種類：E0なし、E1ペア構成通貨の中央銀行発表との予定保有overlap停止、E2=E1＋米NFP/CPI＋AUDを含む場合豪CPIのoverlap停止。
中央銀行対応：USD FOMC、JPY BOJ、EUR ECB、GBP BOE、AUD RBA。E2の米指標は全ペア共通。
Baselineの固定calendar commit 173be2…のliteral日付とbaseline EVENT_CLOCK、FOMC翌日JST規約を継承する仕様。既存Candidate Cの戦略別matrixは流用しない。
全イベントのOR、予定Entry〜Exitと停止窓は両端包含。実現SL/TP時刻でフィルター対象を変えない。日別全停止・イベントの部分集合探索はしない。
E0と比較し、保持率>=80%、除去取引>=20、TotalR改善>=2R、AvgR改善>=0.01R、MaxDDR悪化なしで採用可能。
複数通過ならTotalR差→DD小→E1優先。通過なしならE0。フィルター後のSL/TP・時刻再調整なし。
カレンダーの正確性・網羅性は別の確認事項。固定研究カレンダーは歴史的発表時刻の完全再現ではない。

### Stage 5〜7
最終ID・全パラメータ・年末年始規約・指標/通過閾値・欠損ルール・候補数/落選理由・入力56hash・実行コードhash/依存版・seed（使用時）をDiscoveryだけで固定。
後続の正式FreezeをGitHubへpushしてremote SHA=ローカルHEAD確認後、別指示でValidationへ。
Validationは各年30件以上・合算70件以上・各年負け5件以上を充足判定に使う。欠ければINSUFFICIENT_SAMPLE、勝敗判定を作らない。
充足した場合、各年TotalR>0、合算PF_R>=1.10、合算AvgR>=0.02、合算MaxDDR<=max(10,1.5×凍結Discovery MaxDDR)をすべて満たせばPASS、それ以外FAIL。
2024・2025・合算でN/PF/AvgR/TotalR/DDを別表示。単年PF>=1.10までは要求しない。
これらValidation閾値も正式採用（Validation実行はStage5 Freeze/remote確認後のみ）。閾値は統計的有効性を保証しない。50候補からの選抜、多重試行、既閲覧期間である限界を残す。
Monitorは合格候補のみ。2026の成績でFormal Validationの判定を上書きしない。失敗後の変更は別研究。

### 例外
欠損取引は非生成＋理由、ゼロ損益は件数に含め勝ち/負け両方から除外。年TotalR=0はプラス年に含めない。
利益>0/損失0のPFはINFラベル、両方0はUNDEFINED。最低負け件数で単体不通過にし、巨大な代替数値を順位へ入れない。
空集合・NaN/非有限R・重複IDは失格またはデータ不備として停止。局所探索無効点は除外し、指定範囲を拡張しない。

## Stage1実装・計算・Notebook（2026-09-28の記録）
正式空間は7×2×5×288×283=5,705,280時間構造、SL5種で28,526,400設定。欠損/休場/件数除外前、取引数でも独立仮説数でもない。
TPなしでもSL到達にM1経路が必要。Open差だけの探索には置き換えない。
Referenceは変更しないStage0 `execution.execute` とStage1日付フィルターadapter。Fastは生High/Lowのmin/max木で最初のSL hitを検索し、283 Exitへ共有する。raw比較にepsilon、価格丸め、補間なし。
年度別件数・PF・AvgR・TotalR・DD・loss件数、通過SL数、SL/時間決済/Exit足hit/fallback/途中欠損の診断を保存する。
週1回・最大24h保有で候補内の取引は重ならないため、各候補のEntry順＝Close順。初期peak=0のR累積DDを計算。
全5SLの指標を圧縮shardへ保持し、通過時間構造のみSQLiteで外部sort。代表への直接割当てと抑制理由をgzip CSVへ出力し、上位最大50構造の全5SL結果をJSON保存する。
生M1・完全取引ログをGitHubへ保存しない。Colab出力は `/content/b6_stage1`、Drive保存default OFF。
1 job = symbol/direction/entry（5曜日×283保有×5SL）。合計4,032 job。各jobをatomic保存、SQLite transactionで完了を記録。config/code/input hashが一致する場合だけ再開し、完了shard hashも検証する。
探索本体を起動するにはColab環境、Chat確認フラグ、40桁Freeze SHA、clean tracked checkoutとrelease manifest一致が必要。全job完了前の選定は禁止。
Stage0 Notebookは過去記録として維持。新Stage1 Notebookは既定RUN_FULL_SWEEP=Falseで、設定と探索空間だけを表示する。Validation/Monitor呼出しを含まない。
今回Workでは全unit/synthetic/regression/reference-fast/限定smoke/Notebook軽量確認だけを実行し、Stage1全探索は未実行。
性能は限定benchmarkの記録のみ。全探索の所要時間や圧縮後容量は未測定で保証しない。必要に応じ同じFreeze・同じshardで再開する。

## 採用SL（pips）
|Pair|SL1|SL2|SL3|SL4|SL5|
|---|---:|---:|---:|---:|---:|
|USDJPY|10|25|40|60|95|
|EURJPY|15|30|50|75|115|
|GBPJPY|20|40|65|100|150|
|AUDJPY|10|25|40|65|100|
|AUDUSD|10|20|35|55|85|
|EURAUD|20|35|60|95|145|
|GBPAUD|20|40|70|110|160|

2020〜2023の事前価格較正由来。2024以降の価格分布や候補損益で変更しない。

## Stage2-A実装Freezeの停止位置（履歴）
Workではunit/synthetic/regression/reference-fast/限定実データsmoke/Notebook既定動作/release整合性だけを検証。
新NotebookはRUN_STAGE2A_FULL=False、CHAT_CONFIRMED_STAGE2A_FREEZE=False、Drive保存OFF。
全探索にはColab、Chat確認済みStage2-A SHA、clean checkout、release hash、固定入力/runtime identityが必要。
出力は `/content/b6_stage2a`。候補ごとのcheckpoint hashとcode/config/candidate/56入力/runtime identityを検証して再開。
GitHubへfast-forward保存しremote SHA=local HEADを確認して停止。Stage2-A本番、Stage2-B以降、Validation/Monitor/portfolio/live変更は行わない。
WorkではStage2-A full sweep未実行。Chat確認後にGoogle Colabで実行する。

## Stage2-B実装Freezeの停止位置（履歴）
Workでは入力正式8ファイルの監査、合成/unit/regression/参照互換/限定smoke/Notebook既定動作/release検証だけを実行する。
本番にはColab、Chat確認、Stage2-B Freeze SHA、clean checkout、release manifest一致、正式入力8hash、固定runtime、56M1入力identityを必要とする。
出力 `/content/b6_stage2b` に全局所条件・年別・診断・Center別安定性・落選・最終設定・reviewと再開checkpointを保存する。
旧Stage1/Stage2-Aのコード・Notebook・tests・results・manifestは不変。旧release検証はStage2-A Freeze snapshotで実行し、現Stage2-Bでも旧実行ファイルのhash不変を追加確認する。
Stage2-B full sweepを除く全test suiteの実行手順は実装説明を参照。GitHubへfast-forward保存しremote=local・cleanを確認して停止する。
WorkではStage2-B full sweep未実行。Chat確認後にGoogle Colabで実行する。

## Stage3実装Freezeの停止位置（履歴）
Workは正式入力監査、unit/synthetic/回帰/1分時刻の参照互換/限定smoke/Notebook既定/release検証まで。
新NotebookのPREPARE_ENVIRONMENT/MOUNT_DRIVE/RUN_STAGE3_FULL/CHAT_CONFIRMED_STAGE3_FREEZE/SAVE_OUTPUT_TO_DRIVEは全False、Stage3 SHAは空文字が既定。
本番はColab、Chat確認、40桁Stage3 SHA、clean checkout、release一致、exact Stage2-B入力、56M1/runtime identityを要求する。
出力 `/content/b6_stage3`。全時刻点/年別/診断/安定性/落選/selected/reviewと再開checkpointを保存。後続段階のAPIなし。
旧Stage1/Stage2-A/Stage2-Bコード・config・tests・Notebook・results・manifestは変更せず、過去releaseテストは各Freeze snapshotで元のassertionを検証する。
GitHubへfast-forward保存しremote SHA=local HEAD・cleanを確認して停止する。
WorkではStage3 full sweep未実行。Chat確認後にGoogle Colabで実行する。

## Stage4 Event Filter実装Freeze（履歴）

正式数値・identityは `research_inputs/b6/stage4_config.json`、calendarは `stage4_event_calendar.json`、詳細は [stage4_implementation.md](stage4_implementation.md)。Stage3 selected50/drop0を正式runtimeで確認し、50×3=150 variantsに固定する。時刻/SL/TP/候補集合は変更しない。

E0=filterなし。E1=構成通貨の中央銀行。E2=E1+US_NFP+US_CPI、AUD pairだけAUD_CPI。USD/FOMC、JPY/BOJ、EUR/ECB、GBP/BOE、AUD/RBA。Candidate C matrixは不使用。
指定baseline commitの8literal listと2026追記をASTでexact抽出する。日付/DSTの訂正なし。FOMC03:00±180分はsource日の翌JST日。他clockは実装説明表の固定値。全窓inclusive。
予定Entry〜予定Exitでoverlapを判定し、実際の早期決済/fallbackは判定を変えない。ORで1回削除、event別countは重複帰属可能。Retention=残存実取引/E0実取引、Removed=実取引数差。非成立機会は別診断。
採用は80%以上・20件以上・DeltaTotalR≥2・DeltaAvgR≥.01・DD悪化なしの5条件のみ。P02/年別Delta/他条件なし。両PASSはDeltaTotalR→DD→E1、両FAILはE0。削除/補充/再調整なし。
Colabでは全候補E0の正式Stage3 full/yearly metrics完全一致が全filterに先行する必須バリア。Workでは全期間E0は実行せず、合成・限定smokeを行う。
Notebook全flag既定False、SHA空。COMPLETE_STAGE4_ONLYで停止しStage5 Freeze/Validation/Monitor/Portfolio/liveは未実行。過去freezeの実行ファイルは不変。
GitHubへfast-forward保存しremote SHA=local HEAD・cleanを確認して停止する。
WorkではStage4 full sweep未実行。Chat確認後にGoogle Colabで実行する。

## Stage5 Discovery Candidate Freeze（完了済み）

[stage5_candidate_freeze.md](stage5_candidate_freeze.md) に正式identity・再生成手順・実行境界を記録する。Stage4 selected50件を正式順のまま保持し、候補削除/補充/再ranking選抜なし。全件E0はE1/E2比較後の選択であり、Stage4を省略していない。条件・Discovery full/4年別metrics・raw DiscoveryMaxDDRをexactly固定する。
Candidate Freeze SHA256: `b98f36d92d1b101fcd53f65fdd900bee35f1a209cbdcdd71d71211dc15d00ae0`。
Validation Contract SHA256: `646344d240323f81d46e6360ac1f5d4e15f2130db6399f7fbbcb013bc1a15c57`。

Stage6の正式規則はstage5_validation_contract.jsonだけ。2024/2025各年Trades≥30・Losses≥5、Combined Trades≥70のすべてを満たさなければINSUFFICIENT_SAMPLE（FAILではない）。十分なら各年TotalR>0、Combined PF≥1.10、AvgR≥.02、DD≤max(10,1.5×Stage5 raw DiscoveryDD)の5条件をすべて要求する。単年PF/AvgRなどの追加条件なし。
2024〜2025は既閲覧期間を含むB6 holdout validation / OOS-like。pristine unseen OOSとは呼ばない。Stage5はM1不要の決定的成果物生成のみで、2024+ Candidate performanceを読込/計算/表示しない。
GitHub remote/local SHA一致・cleanを確認して停止。Stage6は別指示。Validation通過もlive採用ではない。
Stage5 Discovery Candidate Freeze完了。2024–2025 Validationは未実行。Chat確認後にStage6へ進む。

## Stage6 2024–2025 Validation実装Freeze

詳細は [stage6_validation.md](stage6_validation.md)、固定実装設定はstage6_config.json。Stage5 Candidate/Contract/commitのexact SHAとancestryがhard gate。全50件の条件、spread/pip、EventMode、calendar、raw DiscoveryDDを変更しない。
ValidationはB6 holdout validation / OOS-like。2024/2025各年とCombinedを別集計、年別帰属は予定Entry JST。canonical JSTで[2024-01-01,2026-01-01)だけをcopyし、executorの2023/2026行は拒否。過去Discovery loader/engineは不変。private period adapterで凍結参照/fast/event実装を再利用する。
Combinedはtrade単位をCloseTime→EntryTime→CandidateIDの時系列で集計し、年別指標の平均は使わない。sample先行・正式5条件はStage5 contractとhelperを再利用、追加gateなし。候補の成績順位付け・絞込・再調整なし。
Notebook全flag既定False、SHA空。正式本番はColab＋Chat確認＋RUN_STAGE6_FULLの両flag、clean release、Stage5 identity一致後だけ。50候補完走前にmetrics/statusを表示せず、COMPLETE_STAGE6_VALIDATION_ONLY後に全件を報告。Stage7/2026/Portfolio/liveは無効。
Workの実データ監査は56hash・期間availabilityだけ。正式2024/2025/Combined Candidate performanceは未実行。GitHub fast-forward、remote=local・clean確認で停止。
WorkではStage6 full Validation未実行。Chat確認後にGoogle Colabで2024–2025 Validationを実行する。

## Stage7 Implementation Freeze — formal Stage6 PASS-only reference Monitor

Stage6 formal Colab runtime at `a1f9e0266801d3d0b4cd383f8fea909fdbc0a678` completed 50 candidates / 150 rows: PASS 17, FAIL 33, INSUFFICIENT_SAMPLE 0. Prior Work non-execution records describe implementation-time state and remain unchanged. Stage7 inputs were independently audited from the formal archive, not reconstructed from Chat or review ZIP. The 17 formal PASS rows retain their order and conditions (AUDJPY 9, GBPJPY 8; Long/Monday/E0).

Stage7 freezes `[2026-01-01, 2026-09-10)` JST as partial-year **Reference Monitor**, with actual M1 end 2026-09-09 06:00 JST. No Monitor PASS/FAIL threshold, ranking, retuning or candidate drop/refill exists. Stage6 statuses are immutable; Stage6 FAIL candidates are not replayed. Portfolio and live remain disabled; PASS ≠ live adoption. Candidate freeze SHA256: `c973c541726efba057b2c07a19cc99ffd2b5a2d457328d1e9df8e813d5e96b86`. See [Stage7 specification](stage7_monitor.md) for hard gates, evidence and tests. Work stops at implementation publication; formal Monitor requires Chat confirmation and Google Colab.

## Stage8 — Deployment Eligibility + post-validation structural analysis

Stage7正式runtimeは17/17 OBSERVEDで完走、Formal Validation PASSは全17件で維持する。ユーザー決定により、AUDJPY Monday 07:01の8件だけを `WEEKLY_OPEN_EXECUTION_MODEL_RISK` としてDeployment Review対象外へ固定。固定spreadモデルが週明けspread/slippage/gapの実行リスクを十分stressしていないためであり、成績や実測spreadに基づく判断ではない。研究候補削除・PASS取消し・Monitor変更なし。

PoolはStage7相対順の9件（AUDJPY 15:50 singleton 1＋GBPJPY8）、SHA256 `dfe25f015da9532535fb9aae3e580e59835f68cf6f9c0e2b0fc6b4a215ec6d68`。Discovery / Validation / partial Monitor / FullAvailableを分け、36 pairs×4＝144 raw overlap/correlation rowsを保存する。FullAvailableはpost-validation structural analysisで、新しいValidationではない。Stage8に閾値・clustering・ranking・代表選定なし。Stage9でfamily consolidation、Stage10でincremental portfolio simulationを別途検討。今回Workは実装・合成tests・入力監査まで。詳細は [Stage8仕様](stage8_overlap_correlation.md)。

## Stage9 — Candidate Family Consolidation & Final Candidate Freeze

Stage8 formal Colab run is complete: nine deployment-eligible candidates, 144 pairwise rows and 36 candidate-period rows. Stage9 audits the synchronized formal archive and freezes the user policy: AUDJPY 15:50 singleton automatically retained; all eight GBPJPY candidates form one family without clustering. Exactly one GBPJPY representative is selected from the six actual FinalEntryJST values in [13:00,14:00).

DD first, relative lot/margin proxy (30.0/SL, same GBPJPY/equal monetary risk; not broker margin) second, then FullAvailable DD, ValidationAvgR DESC, FullAvailable TotalR DESC and CandidateID. No PF or correlation ranking, M1 read/replay, trade or correlation recomputation. The representative is `B6-GBPJPY-L-W0-E0835-H1415`, strictly first on WorstSegmentMaxDDR. Final B6 count=2 in AUDJPY→GBPJPY family order; all conditions and earlier research statuses remain unchanged. Final artifact SHA is the Stage10 hard gate. Stage10 portfolio test is next only under separate instruction; no portfolio/money/live action or numbering occurred. PASS != live adoption. See [Stage9 specification](stage9_family_consolidation.md).
