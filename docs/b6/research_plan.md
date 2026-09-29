# B6 Recent-Era Time-Entry Rediscovery — Stage2-A実装Freeze

状態：STAGE2-A IMPLEMENTATION FREEZE（2026-09-29指示）。Stage1はColab完了済み。WorkではStage2-A全探索を実行せず、Chatが保存内容とSHAを確認した後にGoogle Colabで実行する。Stage5 Candidate Freezeとは別。
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
機械設定は `research_inputs/b6/stage2a_config.json`、詳細は `stage2a_implementation.md`。Stage2-B中心選定と正式rankingは実装しない。

### Stage 2-B（範囲固定・N06b保留）
最大2中心、SL±10pips/TP±10pips、5pips刻み、TPなし中心はSLのみ、範囲の追加なし、という範囲は維持する。
**どの2中心を選ぶかというN06bの正式ルールは、Stage2-A結果をChatで確認してから固定する。**
従来の参考順位・細部安定点案を今回の実行規則へ昇格しない。Stage2-Aは中心選定成果物を生成せず、Stage2-Bを起動しない。

### Stage 3（正式採用、今回未実装・未実行）
選ばれたSL/TP固定、元5分anchorのEntry/Exit各±5分を1分刻み（最大121組）。追加最適化である。
Entryは元JST暦日内、Exit offsetは加減算から再計算し、予定保有30〜1440分を維持。
各点の3×3近傍（中心含む、範囲内の有効点のみ）で2/3以上が通過し、近傍Median AvgR>=点AvgR×0.8を要求。
安定性条件を満たした点の中で近傍Median AvgR最大→元anchorとのEntry/Exit L1距離最小→Entry/Exit固定時刻キー昇順。
旧案にあった「単体順位」を同値処理へ挿入しない。範囲を増やさず、終了後にSL/TPを再最適化しない。

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

## Stage2-A実装Freezeの停止位置
Workではunit/synthetic/regression/reference-fast/限定実データsmoke/Notebook既定動作/release整合性だけを検証。
新NotebookはRUN_STAGE2A_FULL=False、CHAT_CONFIRMED_STAGE2A_FREEZE=False、Drive保存OFF。
全探索にはColab、Chat確認済みStage2-A SHA、clean checkout、release hash、固定入力/runtime identityが必要。
出力は `/content/b6_stage2a`。候補ごとのcheckpoint hashとcode/config/candidate/56入力/runtime identityを検証して再開。
GitHubへfast-forward保存しremote SHA=local HEADを確認して停止。Stage2-A本番、Stage2-B以降、Validation/Monitor/portfolio/live変更は行わない。
WorkではStage2-A full sweep未実行。Chat確認後にGoogle Colabで実行する。
