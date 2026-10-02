# B6 Stage6 2024–2025 Validation 実装Freeze

B6 holdout validation / OOS-like。2024–2025は他研究等で閲覧済みのため、pristine unseen OOSとは呼ばない。Workは実装・合成テスト・M1同一性/期間availability監査まで。正式50候補のValidation成績はWorkで読込・計算・表示しない。Chat確認後のGoogle Colabだけが正式2024–2025結果を開く。

## Stage5 hard gate

|Identity|固定値|
|---|---|
|Stage5 commit|e35225782c84a59dd7546e9ff8d3944705c3709a|
|Candidate SHA256|b98f36d92d1b101fcd53f65fdd900bee35f1a209cbdcdd71d71211dc15d00ae0|
|Contract SHA256|646344d240323f81d46e6360ac1f5d4e15f2130db6399f7fbbcb013bc1a15c57|
|Stage5 config SHA256|5cde19cc5de4a34252124b9e0aded07948ab9b87cdef4b164e1cca08a2bebb10|
|Stage4 selected SHA256|c612f3d083011a640815d7b2c2821c833ec6c6eecbd71f8b35c0b0b36d9c430f|
|Candidate count|50|
|Calendar SHA256|1882b315f88d2a1b4fd18b2929f12bd269c87c98b5c2bf1a66203baf54865484|
|M1 manifest SHA256|8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f|

repoのStage5 Candidate/Contractだけを正式入力にし、Stage3/4 archiveを再利用しない。Stage5 ancestryと当該commit内のartifact bytes、現treeのexact SHA、50件/一意ID/固定条件schema/raw DiscoveryDD/Spread/PipSize/Mode/Calendar/Execution hashesを照合する。repairしない。Stage1〜5のfrozen filesはbyte-identical、Stage5 Validation Contractが唯一の判定規則。

## 期間とデータ境界

2024=[2024-01-01,2025-01-01)、2025=[2025-01-01,2026-01-01)、Combined=[2024-01-01,2026-01-01)、すべてnaive JST。
年別帰属は予定Entry JST年。2026は含めない。2023/2024混在sourceもcanonical JST変換後にsliceする。
既存56 M1のfilename/hash/行数/端点auditとcanonical read関数を再利用する。Helsinki→Tokyo、ambiguous=infer/nonexistent=shift_forward、duplicate拒否、OHLC整合を維持し、Validation-only copy以外をexecutorへ渡さない。2023/2026行が1行でも混ざったexecutor入力は拒否する。補間/broker splicingはしない。
Workでの実データ監査は56 hashと7pairの年別行数・JST端点・期間外0行の確認だけ。replay/metricsを呼べないguard下で実施し、Candidate P&L/判定を作らない。

## Frozen executionの期間adapter

過去engineはDiscovery START/ENDと開始曜日を内部固定している。元ファイルも共有moduleのglobalsも変更しない。Stage6 adapterはStage5が固定する各source SHAを照合し、private moduleへchecked ASTで次だけを適用する。

- execution STARTを2024-01-01、ENDを2026-01-01へ変更。
- private modules間のrelative importをprivate対象へ接続。
- fast engineの曜日epoch literal 2（2020-01-01水曜）をSTART.weekday()へ変更。Validation起点は月曜。
- Stage4 event matchesのperiod guardだけを2024-01-01〜2026-01-01へ変更。

期待する変換箇所数・旧ASTを厳密確認し、それ以外の式を変えない。源ファイルに予期しない変更があれば停止。SL/TP・raw hit・Exit eligibility・fallback・年末停止・event overlapの演算式はfrozen sourceをそのまま再利用する。参照executeとfast Stage2-Aの両方を同じ期間へ適合し、合成データで一致を確認する。

exact Entry Open±spread、adjusted Entry基準SL/TP、Entry/Exit足inclusive、同一足SL first、Exit exact→+1〜+4を先に確保、missing entry/exitは非生成、中間補間なし、raw High/Low、epsilon/追加price rounding/slippageなし、overnight可、weekend bridgeなし、12/25〜1/3 Entry停止を維持。

Stage5正式50件はE0だが、E1/E2もfrozen Stage4 logicで実行可能。mode選択APIは作らない。予定Entry〜予定Exitと固定event窓のinclusive overlapを使い、actual早期決済やfallbackで予定区間を変えない。Calendarは指定source commit173be2…と固定SHAのままで、Web更新やDST訂正はしない。

## 指標と正式判定

年別は予定Entry年。Combinedは2024/2025 tradeをCloseTime→EntryTime→CandidateIDで並べてtrade levelから集計する。各候補は週1回・保有24h以下なので、frozen B6のEntry機会順とClose順は一致する。年別AvgR/PFの平均や年別DDの最大値は使わない。
数値集計はfrozen stage1_metricsを再利用し、必要numeric fieldsのみ採用する。同関数の旧P02診断は破棄し、正式Validation条件に使用・表示しない。raw R、initial peak=0、0R中立、INF/UNDEFINED表現を保持。表示Pips6/R9を正式判定に使わない。

Stage5 Contract JSONとstage5_validation.contract()の完全一致をruntime確認し、stage5_validation.assessをそのまま呼ぶ。新しい閾値を再定義しない。
まず2024/2025各年Trades≥30・Losses≥5、Combined Trades≥70を全て要求。不足はINSUFFICIENT_SAMPLE、FAILではなくformal PASS/FAIL条件を評価しない。全不足reasonを固定順で保存。
十分なsampleだけ次の5条件すべてを満たせばPASS、それ以外FAIL。

1. 2024 TotalR > 0
2. 2025 TotalR > 0
3. Combined PF ≥ 1.10
4. Combined AvgR ≥ 0.02
5. Combined MaxDDR ≤ max(10.0, 1.5 × Stage5FrozenDiscoveryMaxDDR)

Stage5 raw DiscoveryMaxDDRだけを参照し、Discoveryを再計算しない。raw比較・epsilonなし。単年PF/AvgR、WinRate、Recovery、月/quarter、有意差、相関/portfolio等はformal gateへ追加しない。
PASS/FAIL/INSUFFICIENT_SAMPLEを全50件に付け、成績順位やTop Nで選ばない。FAIL後の条件変更・追加/削除/補充・再探索はしない。別条件を試す場合は別研究ID。

## Colab手順と実行guard

Notebook: `notebooks/b6_stage6_validation.ipynb`。
PREPARE_ENVIRONMENT/MOUNT_DRIVE/RUN_STAGE6_FULL/CHAT_CONFIRMED_STAGE6_FREEZE/SAVE_OUTPUT_TO_DRIVEはすべてFalse、STAGE6_FREEZE_SHA=""が既定。
既定run-allはFreeze status、50件、期間、sample、正式5条件、DD式、Candidate/Contract SHAだけ表示。M1読込・正式成績計算なし。

Chat確認済み40桁Stage6 SHAを設定してColabで準備。clean checkout/release hashes/Stage5 ancestry/artifact SHA/config一致を検証し、固定NumPy2.3.5/pandas2.2.3を使用する。Python exact versionもresume identityへ保存。
DATA_ROOT=`/content/drive/MyDrive/ゆうのすけさん2025`。出力=`/content/b6_stage6`。Drive退避=`/content/drive/MyDrive/b6_stage6_archive`。
本番はRUN_STAGE6_FULL=TrueかつCHAT_CONFIRMED_STAGE6_FREEZE=True、Google Colab、exact release SHAの全条件が必要。どちらかflagがFalseなら入力読込より前に拒否/未実行。

candidate checkpointはatomic保存・checksum検証。再開identityはStage6 code/config、Stage5 commit、Candidate/Contract SHA/count、56 M1 hashes、calendar SHA/source、Python/NumPy/pandas。差異は拒否。完了50候補の集合・固定条件・period keys・Stage5判定を検証してから正式集約する。途中表示は完了job数だけ、metrics/status/count別集計は表示しない。

## 出力と停止位置

identity/effective_config/stage5_input_audit/m1_input_audit/search_space/progress、stage6_period_results（150行）/validation_results（50行）/diagnostics CSV、summary/review JSON/ZIP、再開shards/checkpoints。
Period tableは2024/2025/Combined別Trades/Wins/Losses/ZeroR/PF/AvgR/TotalR/MaxDDR。Validation tableは固定条件、DiscoveryDD/limit、各期間metrics、SampleSufficient/reasons、ValidationStatus/reasons。理由はStage5固定codeを全違反保存。
56ファイルinventoryはidentityに1回、review ZIPはmanifest SHA・監査件数・期間coverageのみとし、raw M1/full raw trade logsを保存しない。

50候補全完走後にCOMPLETE_STAGE6_VALIDATION_ONLY、ValidationExecuted=true、MonitorExecuted=false、PortfolioExecuted=false、LiveChanged=false。Notebookは完走後のみ件数・status別表・各期間表・reason/DDを表示。順位付けなし。
Drive保存は既定OFF、完走後明示ONで新規directoryにだけcopyし、既存を上書きしない。

Stage7対象はPASSのみだが、今回Stage7 APIは作らず2026を開かない。INSUFFICIENT_SAMPLE/FAILを自動PASSにしない。PASSはlive採用ではない。

## テスト

Stage6 synthetic: 7pairs×L/S×TP_NONE/finite×同日/overnight、E0/E1/E2、Entry/Exit inclusive、SL-first、fallback0〜4/+5拒否、欠損/中間gap、raw boundary、年末停止、FOMC翌JST日、予定区間、epoch曜日、period leakage、Combined trade-level/連続DD、Stage5境界、resume、default Notebook、未完走表示拒否、release。
合成2024/2025データは検証fixtureであり、正式50候補の実市場成績ではない。
全suite: `PYTHONPATH=src/research python -m b6.stage6_test_suite --stage2a-snapshot <50f83f…clean> --stage2b-snapshot <686b4b…clean> --stage3-snapshot <a2e689…clean> --stage4-snapshot <22a7b5…clean> --stage5-snapshot <e352257…clean>`。
旧releaseのdocs照合だけ歴史的snapshot、元assertion無変更。その他は現在のtreeで実行する。Stage1〜5コード/config/Notebook/tests/results/manifest/Baselineは不変。

WorkではStage6 full Validation未実行。Chat確認後にGoogle Colabで2024–2025 Validationを実行する。
