# Edge Decay Classification Sensitivity Analysis：事前固定計画

計画日: 2026-09-12 JST
Repo: TR-KJ/time-entry-portfolio-lab
Branch: research/edge-decay-sensitivity-validation
起点・Primary Resultコミット: 8c45becc49218d7dc971109bf140f71ce3e8099d
正式計画: docs/38_edge_decay_validation_plan.md
正式結果: docs/39_edge_decay_final_result.md
この計画のみをGitHubへコミットし、SHAと変更ファイルを確認してから分析コードを作成する。

## 目的と固定前提
既存診断の閾値依存性を確認する独立追加研究。最適な閾値の探索ではない。
Primary ResultはSTABLE 21、EDGE LOST 2（18_EA_2_MonWed_Short、22_GA_C_2）、EDGE DECAY 2（20_EA_1A_MonTue_Short、23_GA_F_2）、INSUFFICIENT SAMPLE 3（14_UJ_Sat_3rd、15_UJ_Sat_Aug、16_UJ_T10A）として固定し、変更・上書きしない。
Baselineは既存daily_stop_baseline_trades.csv、28戦略・16,298 trades。
SHA-256: cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
Daily Stopなし、ATR OFF、Event Candidate C。UJ12前倒しゴトウビ、EJ1イベント重複修正済み。
Trade Log再計算なし。記録済みRの期間集計のみ。既存コード・正式結果ファイルも変更しない。
EA/VPS/SET/live運用コード・設定は変更しない。全28戦略の正式構成を維持する。

## 期間・集計
EntryTime JSTを所属基準とする左閉右開期間:
Historical [2015-01-01,2022-01-01)、Recent A [2022-01-01,2024-01-01)、
Recent B [2024-01-01,2026-01-01)、Recent Combined [2022-01-01,2026-01-01)、
2026 Monitor [2026-01-01,2026-09-10)。
Monitorは補助表示のみで分類関数へ入力しない。2022–2026は既に閲覧済みで完全未閲覧holdoutではない。
AvgR = 記録済みR合計 / Trades。PF = 正R合計 / 負R合計絶対値。
損失なし・利益ありのPFは+inf、利益損失ともゼロならNA。未定義の指標は条件を満たさない。
表示丸め前のDecimal値を使用し、Combinedは年別平均の単純平均ではなく全該当トレードから集計する。

## 分類式
H=Historical、A=Recent A、B=Recent B、C=Recent Combined。
1. C Trades < Combined minimum、またはA/BいずれかのTrades < A/B minimumならINSUFFICIENT SAMPLEを最優先。
2. EDGE LOST: H AvgR > 0、H PF > PF threshold、C AvgR <= 0、C PF <= 1.00、A AvgR < H AvgR、B AvgR < H AvgRをすべて満たす。
3. EDGE DECAY: C AvgR <= H AvgR × ratio threshold、A AvgR < H AvgR、B AvgR < H AvgR、C PF < H PFをすべて満たす。LOST優先。
4. その他はSTABLE。
EDGE DECAYにHistorical適格条件やC AvgR > 0条件を追加しない。PF thresholdの変更はLOST条件だけに効く。
STABLEは劣化条件に該当しないという意味で、優位性の存在を証明しない。H AvgRが負の10_AJ_SatAも同一式を適用する。

## One-at-a-timeの固定設定
中心値: PF threshold=1.05、ratio threshold=0.50、Combined minimum=30、A/B minimum=15。
各軸の他条件は中心値に固定する。
- PF軸: 1.00 / 1.05 / 1.10
- Decay ratio軸: 0.25 / 0.50 / 0.75
- Recent sample軸: relaxed（Combined 20、A/B 10）/ official（30、15）/ strict（40、20）
sample軸はCombinedとA/Bを上記の組として動かす。独立した別軸にしない。

分類CSVは28戦略×3軸×3点=252行とし、各行に軸・設定・実効閾値・正式分類・感度分類を記録する。
中心値は3軸に重複して表示されるため、警告残存回数の主集計では中心値1回＋非中心6回=7個のユニーク設定を分母とする。
UniqueSettingはOFFICIAL、PF_1.00、PF_1.10、RATIO_0.25、RATIO_0.75、SAMPLE_RELAXED、SAMPLE_STRICT。
全組み合わせ探索を行わない。

## 残存率と事前固定の記述ラベル
警告側 = EDGE LOSTまたはEDGE DECAY。
全28戦略についてWarningCountUnique / 7、WarningRateUnique、各軸のWarningCount / 3、
参考として表示9行のWarningCountDisplayed / 9を出す。正式値を重複した9行の比率を主指標にしない。
INSUFFICIENT SAMPLEは警告に数えず分母には残す。別途InsufficientCountUniqueを出し、標本不足を改善や安全の根拠と解釈しない。
警告残存ラベルは正式警告候補4戦略だけに適用:
- 頑健: 7/7
- 中程度: 5/7または6/7
- 不安定: 0/7～4/7
正式非警告戦略のラベルはNA（非候補）とし、全戦略で残存回数と分類の一致回数を併記する。
これらは指定範囲内の閾値感度を記述するだけで、確率・統計的有意性・将来の収益性を意味しない。

## 連続値
全28戦略でH、A、B、C、2026それぞれのAvgR、PF、Trades（補助的にTotalR）を保存。
C AvgR / H AvgRはH AvgR > 0の場合のみ計算し、ゼロ以下または未定義は明示的NA。
期間集計と中心値分類を既存正式CSVと照合する。正式分類との不一致は停止して調査し、正式結果を上書きしない。

## 重点解釈
18/20/22/23の全設定での分類推移を示す。
22がどの程度警告側に残るかを確認する。18の回復と分類の閾値依存性を区別し、
回復しているから分類も不安定だと仮定しない。20/23のDECAY判定のratio依存性を確認する。
22単独停止Phase 2の別研究へ進む根拠には使えるが、本研究では停止検証も停止も実施しない。
Sensitivity結果から新しい正式閾値を採用しない。Primary Resultを置き換えない。

## 禁止事項
全組み合わせ探索、最良閾値探し、戦略別特殊閾値、追加期間探索、2026再分類、
結果を見た感度値・記述ラベル基準の追加や変更、除外組み合わせ探索、TP<SL等の別テーマ混入は禁止。

## 出力と実装順序
1. このdocs/40_edge_decay_sensitivity_validation_plan.mdのみをGitHubへコミットし、SHA確認。
2. 研究専用src/research/edge_decay_sensitivity_analysis.py、テスト、Colab notebookを作成し、実装コミットを分離。
3. 固定BaselineのSHA-256、16,298 trades、28戦略を確認。不一致は停止。
4. テストと独立照合を実行。
5. results/edge_decay_sensitivityへ下記確定CSV、docs/41_edge_decay_sensitivity_final_result.mdを結果コミットとして保存。
- edge_decay_sensitivity_classifications.csv
- edge_decay_sensitivity_strategy_summary.csv
- edge_decay_sensitivity_continuous_metrics.csv
- edge_decay_sensitivity_run_record.csv
Colabは本文の確定サマリーと実行時の全28戦略表示、/contentへの4 CSV出力、任意Drive保存セルを持つ。
Colab実行とローカル実行を区別して記録する。run recordにBaseline hash、計画/実装SHA、日時、期間、設定、7設定分母、CSV hash、既存結果照合を記録する。
結果コミットSHAは自己参照を避け、最終報告で明示する。

## 検証計画
既存正式コードを変更せず期間集計を再利用し、既存正式CSVとの一致を確認。
分類優先順位、PFの厳密不等号、ratioの等号、全sample境界、NA/inf、H<=0比率NA、
Monitor非依存、7設定と9表示の重複除外、28×9行、禁止設定なし、hash不一致停止をテストする。
別実装による全28×7分類・全期間主要指標の独立照合（浮動小数の指標許容差atol=rtol=1e-10）を行う。
notebook構造・コード構文と内蔵コードの実行結果を確認する。
GitHubの最終差分で新規研究ファイルのみの追加であること、既存正式結果とlive関連のblob SHA不変を確認する。
