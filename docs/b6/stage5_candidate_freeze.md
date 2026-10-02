# B6 Stage5 Discovery Candidate Freeze

Discovery explorationは終了。Stage4正式runtimeの50候補を、順序・売買条件・EventMode・raw Discovery metricsごと固定した。Stage5で候補の再探索・再ランキング選抜・削除・補充を行っていない。50件すべてE0であり、E1/E2を比較してE0を選んだStage4 decision auditも保存する。

これはresearch candidate Freezeであり、live strategy採用ではない。2024/2025 Validation、2026 Monitor、Portfolio Simulationは未実行。EA/SET/VPS/live/Risk Table/Global R2/Dell Demoは変更しない。

## Freeze chainと正式入力

|段階|Commit|
|---|---|
|Stage1|920b9be5c8f1bcf46a46dbbd4ac06dc19eb295b1|
|Stage2-A|50f83f3904acc3bc3abe54204db7a2ab4964b024|
|Stage2-B|686b4b8b479055e3ff43a21f450b1a7182367ebe|
|Stage3|a2e689332a229d648ed26418f220df96d8ede196|
|Stage4 implementation|22a7b5ff8d49455afc730b446c666b1aa3a2a048|

Stage4 config SHA256: `71ed976b935d99d1a6b76a3d8035418b52b15b0c7c99c974b2dfbf74053c53d6`。
正式input rootは `b6_stage4_archive`（Colab: `/content/drive/MyDrive/b6_stage4_archive`）。Workで同名の正式Drive archiveへアクセスして監査した。Review ZIPやChat値から再構成していない。
Stage4 selected SHA256: `c612f3d083011a640815d7b2c2821c833ec6c6eecbd71f8b35c0b0b36d9c430f`。

`stage5_config.json` に67正式ファイルのexact bytes SHA256を固定した。progress/identity/config、Stage3 audit、calendar/audit、E0 audit、search space、4種CSV、selected/summary/review、checkpoints＋50shardsを含む。
COMPLETE_STAGE4_ONLY、150 variants（各候補E0/E1/E2）、候補50、E0/E1/E2選択数50/0/0、drop0、CandidateFreeze/Validation/Monitor/Portfolio未実行を独立確認した。

固定条件の比較に限って、SHA `7643ff28e2b03829903d9ea3c66118abe4969a61b518a8aa97bdc68e7005c0e8` のStage3正式selected JSONを補助参照する。候補の生成元はStage4正式selectedのみ。Stage3結果やChat値で欠落候補を補完しない。
保存済みE0 full/4年別metricsとStage3正式値が完全一致し、Stage4全候補E0 preflight PASS記録も一致した。WorkではE0を再実行していない。

Stage4の5採用gate・3段tie-breakを保存済みvariant値に適用してselected modeを照合するだけであり、再選択・閾値変更ではない。JSON値はexact比較。CSVシリアライズと年別総和の確認だけ既存1e-12許容差を用い、正式採用gateとFreeze値には丸めやepsilonを入れない。入力不一致は停止し、修復しない。

## 正式Candidate artifact

File: `research_inputs/b6/stage5_candidate_freeze.json`

**Candidate Freeze SHA256: `b98f36d92d1b101fcd53f65fdd900bee35f1a209cbdcdd71d71211dc15d00ae0`**

schema=`b6-stage5-candidate-freeze-v1`、status=`STAGE5_DISCOVERY_CANDIDATE_FREEZE`、CandidateCount=50。
UTF-8、stable key ordering、indent=2、末尾LF、NaN禁止。配列はStage4正式順を保持し、同じ正式入力から常に同じbytesになる。INF/UNDEFINEDは明示文字列、巨大数への置換なし。別内容の既存artifactは上書き拒否、同じbytesの再生成だけ許可する。

exact file SHAを当該ファイル自身へ埋め込むと循環するため、CandidateFreezeSHA256Referenceで後続Validation Contract内のexact digestを参照する。docs・test summary・release manifestにも同じSHAを記録。Candidate→Contractは固定path/schema参照、Contract→Candidateはexact SHA、Contract自身のexact SHAはrelease manifestに保存する。この非循環のidentityをStage6 hard gateにする。

各候補にCandidateID、Symbol、Direction、Weekday、FinalEntryJST/FinalExitJST、FinalExitDayOffset、FinalHoldingMinutes、SL/TP/TPMode、SelectedEventMode、ApplicableEvents、固定spread/pip sizeを保存。内部実行用AdjustedEntryMinute/AdjustedExitMinute/AdjustedExitDayOffset/PlannedHoldingMinutesも保持する。新しいlive Strategy番号は割り当てない。

Discovery `[2020-01-01, 2024-01-01)` JSTのみ。正式metricsはTrades/Wins/Losses/ZeroR/WinRate/TotalR/AvgR/PF/MaxDDR/AvgWinR/AvgLossR。年別2020〜2023はTrades/Wins/Losses/TotalR/AvgR/PF/MaxDDR。Stage4年別にZeroR列はないため新しく推定列を足さず、存在する場合だけ保持する。
**DiscoveryMaxDDRはraw unrounded値を別の必須fieldとして保存**。将来のDD閾値に表示丸め値を使わない。

`results/b6/stage5_freeze/candidate_summary.csv` は正式JSONの表示用view。候補順も同一。JSONと不一致はtest failure。

## Executionとevent provenance

候補artifact内ExecutionContractへfrozen source hashesと規約を保存する。Helsinki→Tokyo naive、exact Entry Open±spread、adjusted Entry基準SL/TP、Entry/Exit足inclusive、同一足SL first、Exit exact〜+4を先に確保、欠損非生成、中間補間なし、raw High/Low、epsilon/追加rounding/slippageなし、overnight可、weekend bridgeなし、Entry 12/25〜1/3停止。0RはTradesに含めWins/Lossesに含めず、metricsはraw R、表示Pips6/R9。PFは正R和/負R絶対和、lossなしpositiveありINF、どちらもなしUNDEFINED。

Stage4 calendar SHA `1882b315f88d2a1b4fd18b2929f12bd269c87c98b5c2bf1a66203baf54865484`、source commit `173be2a114dad6bd183a0a1515581528850f0850` を継承。日付/clock/窓/予定区間inclusive overlapを変更しない。50件E0でもStage4比較・E1/E2 AdoptionPass・selection reason・E0/selected metrics・retention/removal/deltasを保持する。

## Validation Contract（未実行）

File: `research_inputs/b6/stage5_validation_contract.json`

**Validation Contract SHA256: `646344d240323f81d46e6360ac1f5d4e15f2130db6399f7fbbcb013bc1a15c57`**

Stage6の唯一のformal PASS/FAIL contract。結果を見る前に固定した。2024〜2025は他研究等で閲覧経験のある期間なので、**B6 holdout validation / OOS-like**と呼び、pristine unseen OOSとは呼ばない。

|区分|開始inclusive JST|終了exclusive JST|
|---|---|---|
|2024|2024-01-01|2025-01-01|
|2025|2025-01-01|2026-01-01|
|Combined|2024-01-01|2026-01-01|

まず各年Trades≥30かつLosses≥5、Combined Trades≥70をすべて要求する。1つでも不足ならINSUFFICIENT_SAMPLE。これはFAILではなく、formal PASS/FAILの判定を行わない。
十分なsampleだけ、次の5条件をすべて満たせばPASS、満たさなければFAIL。

1. 2024 TotalR > 0
2. 2025 TotalR > 0
3. Combined PF ≥ 1.10
4. Combined AvgR ≥ 0.02
5. Combined MaxDDR ≤ max(10.0, 1.5 × Stage5FrozenDiscoveryMaxDDR)

Discovery DDはこのStage5 raw値だけを使い、Stage6で再計算・差替えしない。raw比較、epsilonなし。単年PF/単年AvgR/WinRate/Recovery/Discovery改善/quarter/月別/有意差等は追加gateにしない。未定義の必須比較はPASS不可。

Stage6出力仕様は2024/2025/Combined別のTrades/Wins/Losses/ZeroR/PF/AvgR/TotalR/MaxDDRと、DiscoveryMaxDDR/ValidationDDLimit/SampleSufficient/SampleFailReasons/ValidationStatus/ValidationFailReasons。Candidate条件・EventMode・calendar・executionは不変。結果による候補追加/削除/再調整・Stage1〜4への戻り探索なし。

Stage5のassess helperは入力済み合成metricsに閾値を適用する純粋関数のみ。Validation engineやM1 loaderは実装していない。テストの2024/2025ラベル付き数値は合成fixtureであり、実候補成績ではない。

## 再生成・テスト

`PYTHONPATH=src/research python -m b6.stage5_freeze --stage4-root <正式archive> --stage3-selected-reference <正式Stage3 selected JSON> --destination <出力先>`。
M1引数はなく、正式Stage4 runtimeと固定条件照合用Stage3 JSONだけを使用する。56 M1については既存manifest識別情報を参照するだけで、price filesを読まない。absolute local archive pathはローカル返却報告に記録し、公開auditにはlogical root名とColab rootを記録する。

同じ正式入力から2回独立生成し、JSON/Contract/audit/CSV全bytes一致、既存artifactとの一致を確認済み。価格読込・研究API・Validation helper呼出しを拒否するguard下でも生成PASS。
全suiteは `python -m b6.stage5_test_suite --stage2a-snapshot <50f83f…clean> --stage2b-snapshot <686b4b…clean> --stage3-snapshot <a2e689…clean> --stage4-snapshot <22a7b5…clean>`。旧releaseのdocs照合先だけ歴史的clean snapshotを使い、assertionは変更しない。その他の旧273テストと新Stage5テストは現treeに対して実行する。

Stage5 release manifestは新規script/artifacts/docs/tests/audit/CSV/test summaryと必要shared dependenciesを固定する。過去Stage1〜4のコード/config/tests/Notebook/results/manifest/Baselineは変更しない。GitHubは指定research branchへfast-forward保存、main merge/force-pushなし。

## 停止と後続

Stage5 commit・remote SHA・local HEAD一致とworking tree cleanを確認して停止。Stage6は別指示が必要であり、今回は2024/2025/Combined Validationを開始しない。
Stage7はStage6通過候補だけ2026-01-01〜2026-09-09をMonitor表示する後続段階。2026でformal validation判定を変更しない。Stage6 PASSもlive採用ではなく、overlap/correlation・robustness・money simulation・incremental portfolio value等の後段研究が必要。

Stage5 Discovery Candidate Freeze完了。2024–2025 Validationは未実行。Chat確認後にStage6へ進む。
