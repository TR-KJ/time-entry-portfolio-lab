# B6 Stage1 実装Freeze

2026-09-28。起点 `abb3d0f86120286153352b0d260a081d595be6d4`。
これはコード・設定のFreezeであり、Candidateを発見・選定したという報告ではない。

## 構成
- `stage1_config.json`：Chat正式条件。実行時SHA256 lock、条件のCLI上書きなし。
- `execution.py`：変更なしのStage0 reference executor。
- `stage1_engine.py`：Stage1日付filter付きreference adapterとNumPy min/max tree高速版。
- `stage1_metrics.py`：丸め前Rの年別/合算指標、P02 gate。欠損maskと0R取引を区別。
- `stage1_data.py`：56入力のbyte hash・行数・raw端点監査、混在CSVの監査層からDiscovery copyだけを返す。
- `stage1_search.py`：全探索、圧縮shard、再開、SQLite ranking、直接近接整理、最大50構造保存。
- `stage1_smoke.py`：事前固定した4日付×2Entry×3保有×5SL×両方向×7ペアだけの実装確認。
- `b6_stage1_discovery.ipynb`：Colab用、既定全探索OFF。Validation/Monitor呼出しなし。

Stage0のreferenceコード・較正結果・manifestは上書きしない。旧Stage0 artifact manifestは当時のスナップショットであり、更新済みPlan/rulesの現行hash確認には新stage1_release_manifestを使う。

## 高速化の意味
1. Discovery全分を一意のJST分indexへ置く。欠損OpenはNaN、木の欠損Low/Highは+INF/-INF。
2. first present indexでExit exact〜+4を確保する。確保失敗ならSLが先にあっても非生成。
3. Entry Open±Spreadをreferenceと同じ式で計算。各5SLのraw stop価格について、Entry〜最大Exit+4の最初のhitを木の範囲検索で取得。
4. 各予定保有時間で、hit<=確保Exitの場合だけSLを採用。Entry足/Exit足も含む。到達なしならExit Open。
5. hit価格比較に丸め・epsilon・FMA・slippage等を追加しない。木は既存High/Lowのmin/maxを選ぶだけで、価格を加工しない。
6. Stage1はTPなし。SL/TP同一足優先規約は変更なしreferenceと既存fixtureで保持する。Stage2のfast TP実装は今回作らない。

entry/date/SL当たり1回のhit検索を283保有時間へ使い回す。保有時間とExit fallbackは依然各候補で判定する。SLなしのOpen差計算への置換ではない。

## 指標と例外
trade表示Pips6桁/R9桁、指標は丸め前R。PFは正R合計/負R絶対値合計。0RはNに入るがWin/Lossへ入らない。
PFは利益のみならINF、全ゼロ/空ならUNDEFINED。最低loss10がなければ通過しない。NaNのAvgRがある構造は3/5 gateを満たさずランキングへ流れない。
候補は同一曜日・最大24hなので自己重複せず、Entry順とClose順は一致する。最初から負けた場合もpeak=0からDDを測る。
年間指標はJST Entry年。欠損を数値上の0R取引にしない（集計のneutral値0とvalid maskを併用）。
停止診断の優先順は年末年始filter→期間外→Entry欠損→Exit欠損/境界→週末→OK。既存executionのExit先確保を維持。

## 保存形式・再開
全指標shardの軸は `[weekday_index, SL_index, holding_index]`。`weekdays`、`SL`、`holds`を各shardへ同梱。
年度suffixは2020/2021/2022/2023。Opportunities_*はSLに依存せず `[weekday_index,holding_index]`。
3/5通過した時間構造をSQLiteへ保存し、採用rankingの全キーで外部sortする。
assignments CSVはGlobalRank、代表/抑制/50枠外、RepresentativeID、Entry/Exit循環距離、保有差を保持。
最大50代表を選んだ後も残る通過構造の抑制/枠外理由を記録する。連鎖併合や落選後の補充は行わない。
選定JSONは5SL全部の指標を含む。Stage1失格構造の全指標もshardから再読込できる。

4,032 jobそれぞれの圧縮shardを書き終えてからSQLite transactionを確定する。途中停止で孤立した未完了shardは再計算して置換し、完了shardはhash照合する。
code SHA、config hash、全56input hash、Python/numpy/pandas版が違う出力先への再開は拒否。
全探索は固定numpy2.3.5/pandas2.2.3。Notebookで準備し、既に古い版が読み込まれていれば再起動を要求する。
データ本体や個人絶対パスは出力identityへ書かない。CSV/SQLite/NPZ出力は/content。Driveへの自動保存はOFF。
圧縮前メトリクス配列は全体でGB単位になる。圧縮後サイズ・全探索時間の実測はなく、軽量smokeから完走時間を保証しない。

## 起動境界
`python -m b6.stage1_search --describe` は表示だけ。
全探索にはColab検出、Chat確認フラグ、expected SHAとHEAD一致、tracked dirtyなし、release manifestの全hash一致が必要。
Stage1 NotebookのFREEZE_SHAは返却された40桁SHAを利用者が転記する。Notebook自身のcommit SHAをファイル内へ埋め込む循環を避けるため、値は空欄のままにしている。
Chat承認前のRUN_FULL_SWEEP/CHAT_CONFIRMED_FREEZEはFalse。全job完了後だけselectionを実行する。
Stage2以降へ自動で進まない。2024〜2025/2026の候補実行APIを持たない。

## テスト範囲
全 `tests/test_*.py`（既存回帰を含む）を実行。`verify_*.py`は別研究の保存成果物を引数に取る監査CLIであり、自動テストsuiteではない。B6作業で他研究を再実行しない。
合成fixtureは全7ペア、Long/Short、same-day/overnight、狭/広SL、Entry/Exit足hit、raw境界、fallback0〜4/+5拒否、途中欠損、missing Entry/Exit、年末年始、期間外拒否を含む。
SQL順序と純Pythonのranking一致、非連鎖近接整理、5SL保持、empty selection、resume identity/hash、Colab外full拒否、Notebook既定run-allを検証。
公開smoke監査は既存manifestの参照hashと56/56一致件数だけを保存し、重複する個別入力メタデータCSVは追加公開しない。
実データsmokeは2020-02-04、2021-02-02、2022-02-01、2023-02-07、Entry09:00/23:45、保有30/60/1440分で固定。候補損益・ランキングは保存/表示せず、明細・rawR・年別指標の一致判定だけを保存する。

**WorkではStage1全探索は未実行。Stage1 full sweepはChat確認後、Google Colabで実行する。**
