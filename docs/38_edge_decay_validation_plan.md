# Edge Decay / Edge Deterioration 検証計画（コード作成前固定）

計画日: 2026-09-12 JST
対象Repo: TR-KJ/time-entry-portfolio-lab
Branch: research/edge-decay-validation
起点コミット: 7f36c3da01dcafd4e9cfb4891467349e0ab37eba
China Demand停止研究とは別の独立研究。計画をGitHubへコミットし、そのSHAを確認した後にのみコード作成・分類計算へ進む。

## 固定Baseline
- 28戦略・16,298 trades
- SHA-256 cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359
- Daily Stopなし
- ATR OFF
- Event Candidate C
- UJ12前倒しゴトウビ修正済み
- EJ1イベント重複修正済み
- Baseline Trade Logの再計算なし
- 既存 daily_stop_baseline_trades.csv の記録済みRを使用する。

## 研究目的
2015-2021年には優位性が確認できた戦略の中に、2022年以降、その優位性が持続的に低下・消失している戦略があるかを診断する。最近負けた戦略を止めることや、戦略数削減そのものを目的にしない。

## 期間固定
- Historical Reference: 2015-2021
- Recent A: 2022-2023
- Recent B: 2024-2025
- Recent Combined: 2022-2025
- 2026 Monitor: 2026-09-09まで（判定条件そのものには使わず補助確認のみ）

## 主指標・併記
Avg R / Trade を primary metric とする。
Total R、PF、Win Rate、Avg Win R、Avg Loss R、MaxDD R、Trades、年別 Avg R、年別 Total R、SL/TP/Time Exit率、Max Losing Streakを併記する。

## 分類ルール（変更禁止）
### 1) EDGE LOST候補
Historical 2015-2021で AvgR > 0 かつ PF > 1.05
かつ Recent Combined 2022-2025で AvgR <= 0 かつ PF <= 1.00
かつ Recent A と Recent B の両方で AvgR が Historical AvgR を下回る。

### 2) EDGE DECAY候補
Recent Combined AvgR <= Historical AvgR * 0.50
かつ Recent A AvgR < Historical AvgR
かつ Recent B AvgR < Historical AvgR
かつ Recent PF < Historical PF
※ EDGE LOSTに該当するものはEDGE LOSTを優先。

### 3) STABLE
上記いずれにも該当しない。

### 4) INSUFFICIENT SAMPLE
Recent Combined 2022-2025が30 trades未満、または Recent A / Recent B のどちらかが15 trades未満なら判定保留。赤黄緑には分類しない。

標本不足判定を最優先、その後EDGE LOST、EDGE DECAY、STABLEの順とする。EDGE DECAYには、指定されていないHistoricalの適格条件やRecent AvgR > 0条件を追加しない。全28戦略を同一式で診断する。STABLEはこの固定条件への非該当を意味し、エッジの存在や将来利益の証明ではない。

## 2026の扱い
- 2026は分類判定に使わない。
- 各戦略について2026 AvgR / TotalR / PF / Tradesを補助表示し、EDGE LOST/DECAY仮説を補強または弱める材料としてだけ扱う。
- 2026を見て閾値や分類ルールを変更しない。

## 重要な解釈
- EDGE LOST / EDGE DECAY判定は即EA停止を意味しない。
- 疑わしい戦略が出た場合のみ、Phase 2として別の独立停止仮説検証へ進む。本研究では停止検証・停止・Money Simulationを実行しない。
- 2022-2026は過去研究で既に参照済みのため完全未閲覧holdoutとは扱わない。
- EA/VPS/SET/live運用コードや設定は変更しない。

## 禁止事項
- 結果を見て閾値変更
- 戦略ごとの特殊基準追加
- 3年/4年/5年窓など複数窓を後から探索
- 2026を見て判定ルール修正
- 複数戦略除外の組み合わせ探索
- TP<SLなど別テーマを途中で混ぜる
- スコア重みの後付け調整

## 共通集計定義
前研究と同じEntryTime（ログのJST）を期間・年の所属基準とし、期間内エントリーの決済損益全体を使う。2026は2026-01-01以上2026-09-10未満。各期間は左閉右開。
AvgR = 記録済みR合計 / trades。PF = 正R合計 / 負R合計絶対値。勝率 = R > 0件数 / 全件数（ゼロRも分母に含む）。
Avg Win Rは正Rの平均、Avg Loss Rは負Rの平均（負号付き）。該当取引なしの場合は欠損。
PFは損失なし・利益ありなら+inf、利益損失ともゼロなら未定義（欠損）。未定義指標は条件を満たすものとしない。
MaxDDはCloseTime, EntryTime, StrategyNoの順で、初期累積R=0からの最大下落幅（正値）。Max Losing Streakも同じ順序でR < 0の連続件数、ゼロRは連敗を切る。
Exit率は記録済みExitReasonのSL/TP/Timeの各件数 / 全件数。その他理由があればOther件数・率を表示し、既知理由へ恣意的に振り分けない。
分類は表示丸め前の値を使用する。合算期間の指標はトレードから集計し、年別指標を単純平均しない。履歴欠測等は明示し、閾値は追加しない。

## 出力仕様
- 28戦略一覧を STABLE / EDGE DECAY / EDGE LOST / INSUFFICIENT SAMPLE の4分類で出す。
- Colab本文に人間が読めるサマリー表示。
- 同じ結果を /content にCSV出力。
- strategy_edge_decay_summary.csv
- strategy_edge_decay_yearly.csv
- strategy_edge_decay_final_classification.csv
- 必要なら詳細CSVも追加可（実行記録CSVを含む）。
- 任意のDrive保存セルを用意。
- 確定結果はGitHub results/edge_decay 配下へ保存。
- docs/38_edge_decay_validation_plan.md と docs/39_edge_decay_final_result.md を残す。
- Baseline hash、Branch、検証日、使用期間、分類ルール、CSV名を記録。
- 実装・テストは研究専用コードとし、ノートブックを用意する。

## 検証・記録
計画コミットSHAを確認してから実装する。実装後は分類の優先順位・各閾値の境界・期間境界・2026非依存・指標計算・hash不一致停止をテストする。
固定Baseline hash、16,298 trades、28戦略、期間集計整合を確認する。独立した集計でも主要指標と分類を照合する。
計画・実装・結果のコミットを分離し、それぞれのSHA、作成ファイル、28戦略分類一覧、候補の要約を最終報告する。Colab上で実行したかどうかを正確に記録する。
