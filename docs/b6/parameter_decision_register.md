# B6 decision register — 2026-09-28正式決定

根拠：ユーザーの「B6 Stage1 実装Freeze 指示」。2026-09-27の準備提案から以下へ更新。
Stage1 source of truthは `stage1_config.json`。旧 `proposal.json` は準備時点の記録であり実行設定ではない。

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
|N05|Stage2-A|合意済み|各SLでTPなし＋0.5/1/1.5/2/3R、5pips丸め。最高SLだけに絞らない|
|N06a|Stage2-B範囲|合意済み|最大2中心、SL/TP±10pipsを5刻み、TPなし中心はSLのみ、範囲追加なし|
|N06b|Stage2-B中心選定・細部安定点選定|今回の新提案（前回案を保持）|今回の指示は最大2中心と範囲を承認。細部アルゴリズムはStage2開始前に確定し、今回は未実装|
|N07|Stage3|合意済み|Entry/Exit各±5分1刻み、3×3有効近傍2/3通過・Median AvgR>=点×.8。近傍中央値最大→anchor距離→時刻キー。単体rankingをtie-breakへ挿入しない|
|N08|Stage4|合意済み|NONE/通貨構成中央銀行/＋主要マクロの最大3種。保持80%、除去20件、Delta TotalR+2、Delta AvgR+.01、DD悪化なし。旧案の年別Delta条件は削除|
|N09|Validation|合意済み|年30件/年loss5件/合算70件未達はINSUFFICIENT_SAMPLE。両年黒字・PF1.10・AvgR.02・DD<=max(10,Discovery×1.5)でPASS|
|N10|例外|合意済み|0RはWin/Loss除外、欠損は非生成、INF/未定義PFを最低loss条件なしで通過させない|
|I01|実装数値規約|実装上の明文化|指標・rankingは丸め前R、取引表示Pips6桁/R9桁。両実装が同じ規約、SL hitに丸め/epsilonなし|
|I02|固定キー|実装上の明文化|symbol辞書順→L/S→weekday→Entry分→Exit offset→Exit分。候補IDはこの時間構造を一意化|
|I03|全探索の実行場所|合意済み|Workは実装・テスト・GitHub Freezeのみ。Chat確認後にColabでfull sweep|
|H01|full sweep性能・研究結果|データ不足で保留|Workでは測定/探索しない。限定smokeは実装検証で研究結果ではない|

Stage2以降の実行器・最終Candidate Freezeは今回作らない。Stage1の正式設定を再提案しない。
