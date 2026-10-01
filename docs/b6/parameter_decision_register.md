# B6 decision register — 2026-10-01 Stage4実装Freeze

根拠：ユーザーの「B6 Stage1 実装Freeze 指示」および「B6 Stage2-A 実装Freeze 指示」。「B6 Stage2-B 実装Freeze 指示」でN06bを正式固定。重複点の扱いは本タスクの追加回答で確認済み。
Stage4 source of truthは `stage4_config.json` と `stage4_event_calendar.json`。Stage3 source of truthは `stage3_config.json`。Stage2-B source of truthは `stage2b_config.json`。Stage2-A source of truthは `stage2a_config.json`。Stage1 source of truthは `stage1_config.json`。旧 `proposal.json` は準備時点の記録であり実行設定ではない。

|ID|項目|現在の区分|正式な内容・前回との差|
|---|---|---|---|
|A01|独立M1探索・既存/live変更禁止|合意済み|維持。正式Strategy番号を新規割当てしない|
|A02|Stage順序と期間隔離|合意済み|Discovery2020〜2023、2024〜2025 OOS-like、2026 Monitor|
|A03|Historical execution|合意済み|Entry/Exit足inclusive、SL-first、最大4分fallback、欠損非生成|
|A04|Stage1設計変更|合意済み|Pure Time SLなし旧案から5 Fixed SL/TPなしへChat正式変更。実装ミスではない|
|P01|5分Entry/Exit、保有30〜1440、Entry曜日別|合意済み|overnight可、週末後月曜へ接続しない、複数曜日groupなし|
|P02|SL別最低条件|合意済み|N>=150、各年N>=30、loss>=10、PF>=1.10、3/4年TotalR>0|
|P03|Stage2上限|合意済み|近接整理後最大50時間構造、SL違いで枠を増やさない、不足時に補充しない|
|P04|年末年始停止|合意済み|12/25〜1/3、Entry日の共通停止|
|N01|ペア別SL5値|合意済み|Stage0価格較正表をそのまま正式採用。Stage1でTPなし|
|N02|SL導出|合意済み|Discoveryのみの事前価格較正由来として固定。再較正しない|
|N03a|3/5SL最低条件|合意済み|3/5・4/5・5/5を分けて保存、全5SLを保持|
|N03b|ranking変更|合意済み|全5SL Median AvgR↓、PassSLCount↓、Median TotalR↓、Worst MaxDD↑、固定キー。Recovery Ratioを除去|
|N04|近接整理|合意済み|Entry/Exit循環距離各30分、offset一致、保有差30分、rank順代表へ直接割当て、連鎖禁止|
|N05|Stage2-A|正式固定|50候補×固定5SL×6TP=1,500。TP_NONE＋0.5/1/1.5/2/3R。Decimal half-upで5pips、最低5、同一SL内重複除去。最高SLだけに絞らない|
|N06a|Stage2-B範囲|合意済み|最大2中心、SL/TP±10pipsを5刻み、TPなし中心はSLのみ、範囲追加なし|
|N06b|Stage2-B中心/安定点選定|正式固定|P02 PASSのみ。Growth AvgR最大、Efficiency TotalR/max(DD,1)最大、同一点統合。Center別近傍2/3・Median AvgR>=点×0.8、正式lexicographic順位で1設定。詳細はPlan/Stage2-B config|
|N07|Stage3|正式固定|Stage2-B SL/TP固定。Original5mAnchor各±5分/1分刻み。Entry日・曜日/ExitDayOffset固定、保有30〜1440。有効3×3近傍2/3・Median AvgR>=点×.8、近傍中央値→anchor距離→固定時刻キーのみ。最低近傍数/単体成績tie-break追加なし|
|N08|Stage4|正式固定|NONE/通貨構成中央銀行/＋主要マクロの最大3種。保持80%、除去20件、Delta TotalR+2、Delta AvgR+.01、DD悪化なし。旧案の年別Delta条件は削除|
|N09|Validation|合意済み|年30件/年loss5件/合算70件未達はINSUFFICIENT_SAMPLE。両年黒字・PF1.10・AvgR.02・DD<=max(10,Discovery×1.5)でPASS|
|N10|例外|合意済み|0RはWin/Loss除外、欠損は非生成、INF/未定義PFを最低loss条件なしで通過させない|
|I01|実装数値規約|実装上の明文化|指標・rankingは丸め前R、取引表示Pips6桁/R9桁。両実装が同じ規約、SL hitに丸め/epsilonなし|
|I02|固定キー|実装上の明文化|symbol辞書順→L/S→weekday→Entry分→Exit offset→Exit分。候補IDはこの時間構造を一意化|
|I03|全探索の実行場所|合意済み|Workは実装・テスト・GitHub Freezeのみ。Chat確認後にColabでfull sweep|
|H01|Stage2-B full sweep性能・研究結果|未測定・未実行|Workでは測定/探索しない。限定smokeは実装検証で研究結果ではない。Stage1/2-Aは既にColab完了|

Stage2-A実装・Colab実行は完了。Stage2-BもColab完了済み。Stage3もColab完了済み。今回はStage4の実装Freezeだけを行い、Stage4本番探索・Stage5以降は行わない。Stage1/Stage2-A条件は変更しない。

|追加ID|項目|区分|内容|
|---|---|---|---|
|S2A01|入力固定|正式固定|Stage1 Freeze 920b9be…、候補SHA 82a71c1a…、config SHA 93cc9a92…、正確な50件と一意IDをhard gate。完全値はstage2a_config.json|
|S2A02|全条件保存|正式固定|P02は表示/保存のみ。1,500条件の途中打切り・再選抜なし|
|S2A03|実行意味|継承|SL/TPともEntry基準。Entry/Exit足inclusive、同一足SL first、Exit0〜4確保してからscan、raw比較・epsilonなし|
|S2A04|出力/再開|実装固定|全条件・年別・診断CSV、identity/config/audit/search/progress/summary/review JSON/ZIP。code/config/candidate/56M1/runtime不一致拒否|
|S2A05|実行制限|正式固定|Colab＋Chat確認＋Stage2-A SHA＋release整合性。既定OFF。Workはテスト/限定smokeだけ|
|S2A06|研究期間|正式固定|Discovery2020〜2023だけ。Stage2-A NotebookにValidation/Monitor APIなし|

|追加ID|項目|区分|内容|
|---|---|---|---|
|S2B01|正式入力|固定|Stage2-A完了8ファイルの正確なSHA、50候補、1500/6000/1500行、schema/全キー/metrics/provenanceを照合。Review ZIP代用不可|
|S2B02|重複中心・Grid|固定|A=Bは1中心に両alias。重複点評価1回。±10/5刻み、bounds除外のみ、範囲延長なし|
|S2B03|重複点の安定性|ユーザー追加確認済み|Center別判定、いずれかPASSなら候補、正式順位が高いPASS側の近傍指標。距離は全aliasの最小値|
|S2B04|近傍境界|実装明文化|今回の3条件だけ。最低3点条件を追加しない。非有限近傍指標は安定性不通過、削除補完なし|
|S2B05|選定・落選|固定|安定点から1設定/構造。なしは落選、補充なし。選定SL/TPをStage3へ固定、今回Stage3実装なし|
|S2B06|実行範囲|固定|Workは監査/テスト/限定smokeのみ。実候補Center/selected/actual unique数はColab本番時だけ|
|S2B07|再開|固定|Stage2-B code/config、Stage2-A8hashとFreeze、Stage1候補hash、56M1hash、Python/NumPy/pandas全一致|

## Stage3追加決定
根拠はユーザーの「B6 Stage3 実装Freeze 指示」。Stage2-Bの正式runtimeを再監査した。

|ID|項目|区分|内容|
|---|---|---|---|
|S301|唯一の候補入力|正式固定|Stage2-B selected50、全TP_NONE、drop0。14正式入力ファイルのexact hash固定。Review ZIP不可|
|S302|固定パラメータ|正式固定|Symbol/Direction/Weekday/SL/TP/予定ExitDayOffsetを保持。Stage2-Bへの戻り探索なし|
|S303|時刻生成|正式固定|予定datetimeでEntry/Exit各±5分を1分刻み。一度だけ。Entry日・曜日/offset変更、保有範囲外は除外、補充なし|
|S304|安定性|正式固定|評価済み有効3×3、自身を含む。P02自身PASS・近傍2/3・Median AvgR>=点×0.8。最低近傍数なし|
|S305|最終順位|正式固定|近傍Median AvgR DESC→anchor L1距離 ASC→Entry分/offset/Exit分/deltas/ID ASCのみ。他指標追加禁止|
|S306|出力/再開|実装固定|全有効点・年別・診断・安定性・無効schedule・落選・最終設定。code/config/Stage2-B14hash/selected/候補/56M1/runtime identity一致|
|S307|停止|正式固定|Workは監査・実装・全テスト・限定smoke・GitHub Freezeのみ。Stage3本番はChat確認後Colab。Stage4以降なし|

## Stage4追加決定
根拠はユーザーの「B6 Stage4 Event Filter 実装Freeze 指示」。

|ID|項目|区分|内容|
|---|---|---|---|
|S401|正式入力|固定|Stage3 Freeze a2e689…、selected50/drop0。正式66ファイルexact hash。selected SHA 7643ff28…、full値はconfig。保存済み近傍順位・Stage2-B SL/TP整合を監査|
|S402|候補固定|固定|Stage3 final時刻・weekday・offset・holding・SL/TPを使用。anchorへ戻さない。削除/補充/再調整なし|
|S403|Calendar|固定|173be2a… baseline literal8種＋2026追記をAST抽出。日付/clock/DST訂正なし。FOMC03:00は翌JST日、他offset0|
|S404|Modes|固定|E0なし、E1構成2通貨中央銀行、E2＋US_NFP/US_CPI＋AUD pairのみAUD_CPI。Candidate C matrix禁止。50×3、同じtrade集合でもmode統合なし|
|S405|Overlap|固定|予定区間と窓の両端inclusive、OR。actual SL/TP/fallbackで予定区間を変更しない。残存約定不変|
|S406|Retention/Removed|固定|E0実取引が母数、実取引差が除去件数。欠損非成立はFilteredOpportunitiesだけ。event別重複帰属は別count|
|S407|採用|固定|Retention≥.80、Removed≥20、DeltaTotalR≥2、DeltaAvgR≥.01、FilterDD≤E0DDだけ。raw比較、epsilonなし。P02/年別改善/他条件追加なし|
|S408|選択|固定|両PASSはDeltaTotalR大→DD小→E1。どちらもFAILはE0。未定義比較FAIL、E0必ず保持|
|S409|E0バリア|実装固定|Colabで全候補full/4年別Stage3 metrics完全一致後のみfilter評価。再開も再検証。不一致は停止。Workでは全期間検証未実行|
|S410|再開|固定|Stage4 code/config、Stage3 Freeze/selected/66hash、calendar SHA/source、Stage1候補、56M1、Python/NumPy/pandas全一致|
|S411|停止位置|固定|Workは監査/実装/全tests/限定smoke/Notebook/docs/manifest/GitHub Freeze。COMPLETE_STAGE4_ONLY以降のAPIなし。Stage5/Validation/Monitor/Portfolio/live未実行|
