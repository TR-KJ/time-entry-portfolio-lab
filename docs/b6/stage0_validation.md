# B6 Stage 0 実施結果

2026-09-27。準備検証と数値提案まで実施。Stage1/2/3/4/5/6/7は未実行。
新候補の2020〜2023 PF/R/rankingも、2024〜2025/2026成績も計算していない。

## 実データ
|項目|結果|証跡・範囲|
|---|---|---|
|repo/branch/source照合|PASS|source_manifest.json。main/C1/Phase5は引継ぎSHAと一致|
|期待manifest同一性|PASS|2参照元のhash一致、56件・7ペア各8件・名前と順序確認|
|実ファイル同一性|PASS|56/56 hash・行数・raw first/last一致、input_audit.csv|
|OHLC/重複|PASS|全56ファイルOHLC不整合・非有限値なし、全7ペアJST重複0|
|期間隔離|PASS|監査から返す価格配列を2020〜2023へcopy、executor境界拒否＋合成fixture|
|取得終端|PASS|全7ペア2026-09-09 06:00:00 JST。候補成績は未計算|
|Baseline同一性|PASS|指定SHA256一致、28戦略・16,298件|
|既存代表取引照合|PASS|Discovery代表45件、凍結Baselineログ＋既存run_strategy対比、不一致0|
|SL価格較正|PASS|事前規約で7ペア×5値、適格805〜808日、各年200〜203日|
|全28全期間再現|未実行|今回は代表照合のみ。過去C1の0 mismatchを代用しない|
|全探索・高速化性能|未実行|Stage1開始前の後続実装・検証が必要|
|Stage1以降/Validation/Monitor|未実行|依頼の停止位置を維持|

代表選択はDiscoveryログをPair×Direction×ExitReason×overnight×fallback×TPなし有無で区分し、EntryTime/StrategyNoで先頭を選択。
45件は7ペア、Long/Short（既存戦略に存在する方向のみ）、SL/TP/TimeExit、日跨ぎ、TPなしを含む。
実データfallbackはEURAUDの2022-09-05 09:59 Entry代表を含む。+1〜+4すべてのケースは合成テストで補完。
元戦略のフィルター再選定は実施しない。既存anchorのexecution互換性の検証である。

## 合成テスト
22テストメソッドPASS（16 execution/隔離等＋6提案ルール）。複数のparameter caseを各メソッド内で検証。
7ペア×Long/Short×TPあり/なしのreference比較、境界価格、Entry足hit、同一足SL優先、Exit足初hit、TimeExit Open、全fallback遅延、+5拒否、欠損Exitの早期SL救済禁止、Entry欠損、途中欠損、日跨ぎ、保有限界、週末接続禁止、期間外配列拒否・copy、fallback境界、重複/順序/OHLC/timezone、冬夏時刻変換、epsilonなし、再現性を検証。
純粋な提案ルールには合成指標だけを渡し、3/5SL、5SL中央値、順序非依存の近接整理、offset/保有差、PF例外、有限局所grid、組合せ数を検証。

実行記録：`results/b6/stage0/synthetic_tests.txt`、環境：`environment.json`。
Notebookコードセルは既定RUN_STAGE0=Falseで順次実行し、データ処理・探索が起動しないことを確認。
Colab実機での実行は未実行。ローカルのPythonでセル構文・既定run-allのみ検証した。

## SL提案
日次High−Low中央値D（JST火〜金、データ充足日、2020〜2023のみ）。倍率15/30/50/80/120%、5pips half-up。
詳細・除外ルールは集計前保存のsl_calibration_prespec.md。hashはrun_status.json。

|Symbol|D pips|30分中央値|4時間中央値|SL1|SL2|SL3|SL4|SL5|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|USDJPY|77.50|9.30|28.70|10|25|40|60|95|
|EURJPY|95.30|11.90|35.80|15|30|50|75|115|
|GBPJPY|126.60|16.30|48.30|20|40|65|100|150|
|AUDJPY|82.70|10.70|32.50|10|25|40|65|100|
|AUDUSD|70.50|8.60|26.90|10|20|35|55|85|
|EURAUD|119.85|15.80|47.70|20|35|60|95|145|
|GBPAUD|135.10|18.40|54.40|20|40|70|110|160|

全ペアでclamp/重複補正なし。日次と短時間では値幅が異なり、日次中央値が唯一の正解ではない。
USDJPYの年別中央値は2020約56.10→2021約55.15→2022約111.30→2023約113.35と変化する。
これはDiscovery内の価格診断であり、成績を見てSLを再調整する理由に使わない。年度別較正・時間帯別SLへ拡張しない。
実測値であっても探索条件として未採用。採否はdecision register参照。

## 保存・再現
追加ファイルだけをB6専用branchへ保存する。変更一覧・hashは成果物manifest、commit/remote確認は返却報告。
CLI例（入力パスは各環境で設定）：

```sh
PYTHONPATH=src/research python -m unittest discover -s tests -p 'test_b6*.py' -v
PYTHONPATH=src/research python -m b6.stage0 --data-root "$B6_DATA_ROOT" --baseline "$B6_BASELINE" --out /content/b6_stage0
```

既存EA、凍結研究、live等のtrackedファイル変更なし。M1/完全trade logを新規保存していない。
`calibration_day_diagnostics.csv`は価格なしの日次充足診断で、取引ログではない。
今回のコミットは準備Plan・Stage0・数値提案の保存。正式な探索条件FreezeおよびStage5 Candidate Freezeではない。
