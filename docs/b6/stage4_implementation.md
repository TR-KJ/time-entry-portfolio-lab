# B6 Stage4 Event Filter 実装Freeze

Stage3正式selected 50候補の時刻・SL/TPを保持し、Discovery 2020〜2023のE0/E1/E2だけを比較する。Workは監査・実装・テスト・少数日smokeまで。本番はChat確認後のGoogle Colabに限定する。

## 正式入力と監査

Stage3 Freeze `a2e689332a229d648ed26418f220df96d8ede196`、config SHA256 `4c7ca05a7d9ffac826de30ad8f5d3db882b720798e1afddf4bac63ddf2bb279d`。
selected SHA256 `7643ff28e2b03829903d9ea3c66118abe4969a61b518a8aa97bdc68e7005c0e8`。正式selected 50、drop 0、COMPLETE_STAGE3_ONLY、Stage4/EventFilter/Validation/Monitor未実行を再監査した。

`stage4_config.json` は66ファイルのexact bytes SHA256を固定する。最低13ファイルに加え、review JSON/ZIP、checkpoints、50個のshardを含む。ZIP単独では入力を代用しない。Stage2-B/Stage1の正式アーカイブも監査チェーンに使用する。56 M1識別情報は既存manifestと照合し、公開監査結果には複製しない。

保存済みStage3 shardから固定grid、全点、年別、diagnostics、近傍安定性、最終順位を読み取り照合する。価格の再探索やruntimeの修復は行わない。selectedと順位の照合はJSON値の完全一致。CSVとの照合だけ既存の数値シリアライズ許容差1e-12を用いる。全入力のexact bytes hashが前提であり、採用gateやE0再実行一致にこの許容差を用いない。

Stage3のEntryMinute/ExitMinuteは元anchorを表す。Stage4実行には必ずAdjustedEntryMinute/AdjustedExitMinute/AdjustedExitDayOffset/PlannedHoldingMinutesを使い、Final表示と照合する。

## 固定カレンダー

source commit `173be2a114dad6bd183a0a1515581528850f0850` の `src/portfolio_backtest_v1_2_add_aussie_logic.py`。
source SHA256 `4b71f6b7b1cdbe3266cd9b7cefae37811781561016a013a34d7c8c84247ef32d`。
frozen calendar SHA256 `1882b315f88d2a1b4fd18b2929f12bd269c87c98b5c2bf1a66203baf54865484`。

トップレベルの指定8リストと2026リスト、元リスト＋2026リストの代入だけをASTで抽出する。元Pythonを実行・importしない。順序と重複を保持し、日付/DST/実際の発表時刻を調査・修正しない。全日付の保持は出典監査だけであり、取引評価はDiscoveryのみ。

|Event|固定JST|前/後（分）|JST日offset|全日付件数|Discovery source日付件数|
|---|---|---|---|---|---|
|FOMC|03:00|180/180|+1|97|33|
|US_NFP|21:30|120/120|0|144|48|
|US_CPI|21:30|120/120|0|144|48|
|BOJ|12:00|180/180|0|103|33|
|BOE|21:00|120/120|0|106|34|
|ECB|21:15|120/120|0|96|32|
|RBA|13:30|120/120|0|123|44|
|AUD_CPI|10:30|120/120|0|48|16|

FOMC source日は米国発表日。翌JST日の00:00〜06:00をinclusiveに停止する。これは研究上の固定clockであり、歴史的発表時刻の再構築ではない。

## 3 modesと重複判定

E0は除外なし。E1は構成2通貨の中央銀行だけ。USD→FOMC、JPY→BOJ、EUR→ECB、GBP→BOE、AUD→RBA。
E2はE1＋US_NFP＋US_CPI、AUDを含む4pairだけAUD_CPIを追加。Candidate CのStrategy別matrixには依存しない。結果が同じでも3modeを保持する。50×3=150 variants。

予定Entry≤窓End、かつ予定Exit≥窓Startならoverlap。両端inclusive。実際の早期SL/TP決済やExit fallbackは予定区間を変えない。複数窓はORで除外1回。event別countは複数aliasへ計上するため、合計がRemovedTradesを超える場合がある。

E1/E2はfrozen E0 replayの削除maskだけで実装する。残したEntry/Close/Pips/R/ExitReasonを再計算・変更しない。RemovedTradesはE0実成立件数−残存成立件数、RetentionRateは残存成立件数/E0実成立件数。欠損等でE0が生成しなかった機会はRemovedTradesに含めず、FilteredOpportunitiesにのみ含める。

## 指標・採用

既存Stage2-A/Stage3集計をimportし、raw R・初期peak 0のDD・同じ時系列順・0R中立を保持する。フィルター除外は独立status -1でmaskし、欠損や年末停止と誤分類しない。全期間11指標と4年別指標を保存する。

採用gateはRetention≥.80、Removed≥20、DeltaTotalR≥2、DeltaAvgR≥.01、FilterDD≤E0DDの5つだけ。丸め・epsilon・P02再通過・年別改善等を追加しない。未定義比較はFAIL。
両filter PASSならDeltaTotalR降順→FilterDD昇順→E1。両FAILならE0。候補の削除・補充・再調整はしない。E0のAdoptionPass=Falseは「filter採用でない」の意味で、候補落選を意味しない。

## E0必須バリアと再開

Colab本番では、入力・カレンダー・56 M1を監査後、全候補E0を固定実行で再現する。全期間と2020/2021/2022/2023年別の正式Stage3 selected metricsに完全一致するまで、どの候補もE1/E2を計算しない。1候補でも不一致なら例外で停止する。再開時もこのバリアを再実行し、保存済みfilter checkpointで迂回できない。

Workでは全50候補×DiscoveryのE0を実行しない。合成データの一致/不一致停止テストと3候補×固定4日の参照比較を行う。正式全期間E0一致はColab preflight待ちであり、WorkのPASSとは区別する。

再開identityはStage4 code/config、Stage3 Freeze/selected/全66hash、calendar SHA/source commit、Stage1候補SHA、56 M1hash、Python/NumPy/pandasを含む。不一致・破損checkpointを拒否。NumPy2.3.5/pandas2.2.3固定、Pythonは実行環境の正確なversionを保存して再開照合する。正式入力やrepositoryと出力の重複を拒否する。

## Notebookと成果物

`notebooks/b6_stage4_event_filter.ipynb` の準備・mount・本番・Chat確認・Drive保存flagは全False、Freeze SHAは空。既定run-allは固定条件だけ表示し、正式入力・M1読込なし。

Colab入力は `/content/drive/MyDrive/b6_stage3_archive`。監査用Stage2-B=`b6_stage2b_archive`、Stage1=`b6_stage1_20260929`、M1=`ゆうのすけさん2025`。出力 `/content/b6_stage4`、任意保存先 `/content/drive/MyDrive/b6_stage4_archive`。既存保存先を上書きしない。

identity/effective config/Stage3 input audit/calendar/calendar audit/E0 audit/search space/progress、variant/yearly/event diagnostics/selection audit CSV、selected/summary/review JSON/ZIP、再開用shards/checkpointsを保存する。full raw trade log/M1は保存しない。
COMPLETE_STAGE4_ONLY後だけmode件数・採用数・retention/removal/delta分布・selected表を表示する。EventFilterExecuted=true、CandidateFreeze/Validation/Monitor/PortfolioExecuted=false。

## 検証方法

全テストは `python -m b6.stage4_test_suite --stage2a-snapshot <50f83f…のclean checkout> --stage2b-snapshot <686b4b…のclean checkout> --stage3-snapshot <a2e689…のclean checkout>`。`PYTHONPATH=src/research` を指定する。

旧releaseテストのdocs照合先だけ各歴史的snapshotへ向け、元のassertionをそのまま実行する。その他の旧207テストと新Stage4テストは現在の実装に対して実行する。旧コード/config/tests/Notebook/results/manifest不変を新releaseでも検証する。SKIPを増やさない。

限定実データsmokeは正式selectedの先頭3候補、各年2月最初の該当曜日の計4日。日付選択はEvent結果に依存しない。固定scheduleとSL/TPのE0参照実装比較、E1/E2 mask、残存約定一致だけを確認し、正式mode選択・ランキング・成績表は出さない。

WorkではStage4 full sweep未実行。Chat確認後にGoogle Colabで実行する。
