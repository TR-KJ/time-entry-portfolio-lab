# B6 Source of Truth

2026-09-27実確認。新規clean cloneからB6専用branchを作成。開始時の未コミット変更なし、AGENTS.mdなし。
Remote: https://github.com/TR-KJ/time-entry-portfolio-lab.git
作業branch: research/b6-recent-era-time-entry-rediscovery。main merge / force push / 既存branch書換えは禁止。
端末上の一時checkoutで作業し、ユーザーの既存checkoutは変更しない。

|参照branch/用途|実確認commit|引継ぎとの差|
|---|---|---|
|main|1df6b8c5ed0b156ae511ba0dcc957c1af5ba64e5|一致|
|research/c1-path-dependent-exit-management-phase1|9f14c906921e7e4d792a32c02dd439b7e8192b41|一致|
|research/volatility-environment-phase5-demo-forward|5e93a8834e27d4d9ffdbc2980906511f74ddb27a|一致|
|Baseline calendarの固定旧ソース|173be2a114dad6bd183a0a1515581528850f0850|固定を維持|

ファイル別の参照commit・SHA256は `results/b6/stage0/source_manifest.json`。
mainにないC1/A3/Volatilityファイルは上記commitをgit objectから読み、mainの同名推測で補わない。
期待manifestはC1のresearch_inputs/a3_expected_m1_manifest.csvとPhase5のresults/volatility_phase1/volatility_phase1_input_manifest.csv。
両者はbyte同一、SHA256 `8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f`。
B6配下へ期待manifestをbyte同一で保存。実ファイルに合わせて期待値を更新していない。

主executionの正本はmainの `src/research/daily_stop_baseline_revalidation.py`。
load_pairはHelsinki ambiguous=infer / nonexistent=shift_forward、JST重複は例外。
対して旧portfolioソースのloaderはtz_localizeデフォルトとdrop_duplicatesを使用する。
この相違を認識し、B6は監査済みBaseline loader規約に合わせる。旧portfolioを直接importしない（末尾に全戦略実行がある）。
Baselineはmainガードがあり、安全にimportできる。calendarはその関数を呼ぶと旧commitから取得するが、Stage0代表照合ではネットワークcalendar呼出しは行わない。
代表照合のno=999はテスト内部だけのreference fixtureであり、live/B6 Candidate Strategy番号ではない。
元の取引ログのEntry/Exit/SL/TPを使い、日付・イベントの選択処理は済んだ代表anchorのexecutionだけを検証する。

`exit_efficiency_phase1.py`のE100、`c1_path_management_phase1.py`のR0もExit足inclusive・SL first。
C1は診断指標のEPSを持つが、実際のSL/TP hit比較にepsilonを入れていない。
丸めはBaselineがPips6桁/R9桁。A3のRはPipsを丸めた後に割る経路があるため、B6はBaselineの未丸めPipsからR算出を正本にする。
C1保存済みALL28の不一致0記録は今回の検証実績に流用しない。

仕様間の既知差を再確認：docs/19はStrategy4/16へFOMC overlap追加を要求するが、Baseline EVENT_POLICYでは4は全て無し、16のFOMCも無し。
Strategy21はdocs/01で8月停止の記載がある一方、Baseline individual_stopにはその停止がない。
Baselineのhashを保ったまま比較するため、これらをB6で修正しない。master listをBaselineより優先しない。
Strategy12は25/30の週末だけ前金曜へ前倒し（20は前倒しなし）。EJ1はCPI週水曜停止＋FOMC/NFP/BOJ/ECB overlap。
これら個別戦略ルールをB6候補へ継承しない。

Baseline実ファイルSHA256 `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`、28戦略/16,298件を今回照合。
Baseline全取引は探索母集団にしない。2020〜2023の既存代表45件だけを実行照合した。
生M1・完全Baselineログ・個人絶対パス・認証情報はGitHubへ保存しない。
入力パスはCLI --data-root / --baseline、Notebook変数として与える。

GBPAUD既知gap（Discovery外）：2019-01-03 07:45〜2019-01-09 07:00 JST、2019-05-07 13:30〜2019-05-13 06:02 JST。
他ブローカー補完、新規損益依存の除外日追加はしない。
