# 市場環境依存研究ロードマップ

次に何を検証するかをGitHubだけで確認できるようにするための研究候補メモ。以下は未実施の研究案であり、正式な事前登録・検証結果・live適用の決定ではない。

## 優先順位と4テーマ

### 1. Volatility Environment（ボラティリティ環境）

- **仮説:** 戦略エッジは低・中・高ボラ環境で変化する可能性がある。
- **Phase 1 Primary案:** 各戦略の通貨ペアについて、Entry以前の確定D1バーからATR20を計算し、過去252 completed trading daysのATR20分布に対するpercentileでLOW / NORMAL / HIGHに分類する（3分位を候補とし、境界・同順位の扱い等は開始時に事前固定）。
- **Robustness案:** 20日 realized volatility。Primaryの代替探索には使わず、計算定義を事前固定して頑健性を確認する。
- **次段階:** 依存が確認された場合のみ、Phase 2でEdge Risk threshold studyを別途事前登録する。

### 2. Pre-Entry Price Action（Entry直前の値動き特性）

- **仮説:** エントリー直前の市場活性度が時間指定戦略の期待値に影響する。
- **Phase 1案:** Entry直前180分のRange（High − Low）を、同ペア・同時間帯の過去分布と比較し、QUIET / NORMAL / ACTIVEに分類する。参照期間と分類境界は研究開始時に事前固定する。
- **将来候補:** Entry時点で利用可能な情報なので、依存が支持された後のEAフィルター化候補となる。

### 3. Trend Strength（トレンド強度）

- **仮説:** 相場の方向ではなく、トレンド強度・レンジ環境がエッジに影響する。
- **Primary案:** Entry以前の確定D1バーによるADX14でRange / Intermediate / Trendに分類する。具体的閾値は本研究開始時に事前固定する。

### 4. Interest-Rate Differential（金利差）

- **仮説:** 円との金利差の水準・拡大縮小が、円絡み戦略のエッジに影響する。
- **Primary候補:** 各通貨圏の政策金利 − 日本政策金利。特にspread widening / narrowingを候補とし、変化の参照期間・分類定義を事前固定する。
- **必要データ:** 外部historical policy-rate data。Entry時点で公表・利用可能だった情報を使う。データ収集・整備が必要なため優先順位は最後とする。

## 共通研究原則

- 固定Baselineは**28戦略・16,298 trades**。Baseline Trade LogのSHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`。
- Baseline Trade Logを下流分析で再計算しない。固定ログに市場環境ラベルを付けて分析する。
- まずPhase 1でエッジ依存を診断し、支持されたテーマだけPhase 2 threshold studyへ進む。Phase 2は別途事前登録する。
- 結果を見てlookback / threshold / periodを追加最適化しない。分類・評価指標・支持判定・欠損処理は研究開始前に固定する。
- 指標と参照分布にはEntry時点で利用可能な確定データだけを使う。未確定バーや将来データを混ぜない。
- live変更は別研究・別意思決定。本ロードマップではEA / VPS / SET / live設定を変更しない。

## EA実装可能性

| テーマ | 将来の実装可能性 |
| --- | --- |
| Volatility | 実装可能。Entry時点以前の確定バーからATR / realized volatilityを計算できる。 |
| Pre-Entry Price Action | 実装可能。Entry直前N分のRange / Return等をM1 / M5から計算できる。 |
| Trend Strength | 実装可能。確定バーのADX等を利用できる。 |
| Interest-Rate Differential | 実装可能性はあるが、外部データの供給・更新が必要で実装難度は高め。 |

実装可能性は採用判断とは別。研究で支持されても、EAフィルター化とlive適用は別途検証・判断する。

## ATR70フィルターとの違い

- 過去に検証した「ATR70を基準にEntry可否を判断するATR filter」は、特定閾値によるEntry filterの採否検証。
- 今回のATR20 percentile regime分析は別研究。まずATR20を市場環境の診断変数としてLOW / NORMAL / HIGHに分類し、エッジ依存があるかを見る。
- **Phase 1ではEntryを止めない。** 固定Baselineの全トレードを維持して依存を診断する。
