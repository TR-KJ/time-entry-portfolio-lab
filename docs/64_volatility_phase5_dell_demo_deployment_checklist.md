# Phase 5 — Dell OANDA demo 導入チェックリスト

状態: SOURCE_IMPLEMENTED / NOT_COMPILED / NOT_DEPLOYABLE。現時点でex5は提供しない。
Plan: 9930d2f7fdf903fd60a85ba286592a0cf72a0412（docs/63）。この文書はPlanの変更ではない。

## 配置前のゲート

- [ ] GitHubの実装SHA・全依存source SHA256とPlan SHAを記録する。
- [ ] MetaEditorで専用EAを実コンパイル。エラー0、全warningレビュー。compiler/MT5 build・compile log・生成ex5 SHA256を記録する。
- [ ] test_vol_r2_core.mq5をコンパイルし、注文を出さないscriptとして実行。全24チェックPASSのExpertsログを保存する。
- [ ] MQLと独立Pythonで同一M1 fixtureのdaily OHLC/ATR20/n/Qを比較する。PythonテストのみをEA実行の証拠にしない。
- [ ] Step9.2.4の成功・遅延deal・pending・timeout・重複防止・exitの実行回帰を確認する。静的関数一致は代替ではない。
- [ ] 診断/履歴取得の時間とディスク消費を測定し、予定Entry窓を妨げないことを確認する。600暦日M1を要求するため端末の履歴上限/同期に注意。未同期は0.90 fallbackとなるが有効feature観測件数には数えない。
- [ ] DLL等の追加依存なし。Trade/Trade.mqhは実コンパイル環境の標準ライブラリのhash/buildを記録する。

## Dell実値を固定する

- [ ] Dell/OANDAのDEMO表示、正確なlogin・server・口座通貨を確認。GitHubにはalias/マスク情報だけを保存し、認証情報は保存しない。
- [ ] MT5 build、Dell時刻、broker server時刻、Europe/Helsinkiの過去DST対応を確認する。live build6180やlive数量仕様をDell実値の代用にしない。
- [ ] USDJPY/EURJPY/GBPJPY/AUDJPY/AUDUSD/EURAUD/GBPAUDのmin=.01/max=10/step=.01を確認する。異なる場合は初期化拒否。Planに従った事前互換性レビューが必要。
- [ ] 既存DellのEA/chartとsymbol/magicを照合し、競合がないことを確認。専用EA自身は既存同magicポジション/注文があると初期化を拒否する。他chart上EAの将来発注まで自動検出したとは扱わない。
- [ ] VPS liveとDell liveの同時Algo ON禁止を維持。Dell demoは別口座。VPS liveは一切操作しない。
- [ ] SET全120項目をparseしてテンプレートと比較し、差分を記録する。22=false/他27=true、Risk=.90、LotMode=1、Equity=true、MaxAutoLot=1、min繰上げ=false、ATR70=false、Event/C=true、Test/Mock/force=false。
- [ ] InpPhase5RunIdは新規の英数字/underscore 1–24文字。過去RunIdを再利用しない。InpPhase5DemoLogin/serverを実値で設定。InpPhase5HelsinkiVerifiedは証拠確認後だけtrue。全配置前ゲートを通過するまでInpPhase5Approved=false。
- [ ] 最終SET hash/filename、binary hash/filename、source/依存hash、実装SHA、開始JST、運用者確認をstart manifestへ固定する。

## 配置ファイル

専用mq5とその隣のphase5_demoフォルダを同じ配置関係でコンパイルする。
EA: time_entry_step9_2_4_trade_result_reconcile_27strategies_vol_r2_demo.mq5
依存: phase5_demo/step921_demo_dependency.mqh、vol_r2_core.mqh、vol_r2_runtime.mqh。
旧liveファイルへのコピー・上書きは不要。専用SETは configs/phase5/step9_2_4_dell_demo_vol_r2_phase5.set。
テンプレートは口座/RunId未設定・Approved=falseのため取引できない。

## 操作の進め方

案内は一度に1操作だけ。各操作のユーザー確認を受けて次へ進む。
最初はDellのMetaEditorを開くところまで。コンパイル前にEAをchartへ配置しない。
実コンパイル・試験・実値固定が済んでから配置操作を案内する。
フォワード開始後はExpertsログ全体とP5_*.csvを毎日退避しSHA256を保存する。
同一symbol/JST日の有効featureは同期状態とbar数が不変なら同じ保存済みM1 snapshotを共有する。
履歴拡張・日替りは無効化。historical price correctionが疑われる場合は旧snapshotを保持して比較する。
既存snapshotファイルを上書きしない。保存エラー時は発注停止。履歴が全く取得できない場合は理由付き0.90 fallbackを記録する。

MT5再起動テストは対象外。VPS導入前の別Deployment/Acceptance Testで必須。
今回の初期化チェックは開始時に既存ポジションがないことを要求する。稼働中ポジションを持ったEAの再attach/restartを手順として要求しない。
