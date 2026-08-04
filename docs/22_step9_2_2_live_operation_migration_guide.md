# Step 9.2.2 実運用移行手順

## 1. 文書の目的

本ドキュメントは、デモ口座でフォワード検証中の以下のEAを、本番口座で実運用開始するための手順を記録する。

対象EA:

- `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

依存EA:

- `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

Step9.2.2はStep9.2.1を内部で読み込む構成であるため、本番用MT5には両方のファイルを配置する。

ただし、実際にチャートへセットして稼働させるのはStep9.2.2だけとする。

---

## 2. 推奨する実運用開始時期

実運用開始は、2026年8月10日（月）の週を候補とする。

週次基準額を使ったロット計算を行うため、週の途中ではなく、月曜日から開始する方が管理しやすい。

実運用開始までの流れ:

1. 2026年7月31日のBOJイベント停止を確認する
2. 翌週もデモ口座でフォワードを継続する
3. エントリー、決済、イベント停止などに異常がないことを確認する
4. 本番用MT5を別フォルダへインストールする
5. 本番口座へログインする
6. Step9.2.2とStep9.2.1を本番用MT5へ入れてコンパイルする
7. 新しいチャート1枚にStep9.2.2をセットする
8. 保存したEA設定ファイルを読み込む
9. テスト関連設定をすべてOFFへ変更する
10. ロット、リスク率、イベントフィルターを再確認する
11. 保有ポジションと未決済注文がない状態で自動売買をONにする
12. ExpertsログでEAの起動と動作を確認する

---

# 3. 本番用MT5を別フォルダへインストールする

## 3-1. 作業するタイミング

本番用MT5の準備は、次の状態で行う。

- デモ口座に保有ポジションがない
- デモ口座に未決済注文がない
- 間もなくエントリーまたはTime ExitするStrategyがない
- 2026年7月31日のBOJ停止確認が完了している
- デモ用MT5が正常に稼働している

インストール中に、現在稼働中のデモ用MT5を誤って上書きしたり、停止させたりしないように注意する。

---

## 3-2. 現在のMT5をデモ用と分かる名前にする

デスクトップにある現在のMT5ショートカットを右クリックする。

操作:

1. MT5ショートカットを右クリック
2. `名前の変更`を選択
3. `OANDA MT5 DEMO`など、デモ用と分かる名前に変更する

例:

- `OANDA MT5 DEMO`

これはショートカットの表示名を変更するだけであり、EA、チャート、口座設定には影響しない。

---

## 3-3. 現在のデモ用MT5の保存場所を確認する

現在のデモ用MT5を起動する。

操作:

1. MT5上部メニューの`ファイル`を開く
2. `データフォルダを開く`を選択する
3. 開いたデータフォルダの場所を確認する
4. 必要に応じて`origin.txt`を開き、対応するMT5のインストール先を確認する
5. デモ用MT5のインストール先とデータフォルダをメモする

例:

- インストール先  
  `C:\Program Files\OANDA MetaTrader 5`

- データフォルダ  
  `C:\Users\ユーザー名\AppData\Roaming\MetaQuotes\Terminal\xxxxxxxxxxxxxxxx`

新しく作る本番用MT5では、デモ用MT5とは異なるインストール先とデータフォルダを使用する。

確認後、作業中の誤操作を避けるため、デモ用MT5を一度閉じてもよい。

---

## 3-4. OANDAのMT5インストーラーを用意する

OANDAの公式マイページなどから、MT5インストーラーをダウンロードする。

例:

- `oanda5setup.exe`

以前使用したインストーラーがPC内に残っている場合でも、可能であれば最新の公式インストーラーを使用する。

---

## 3-5. インストーラーを起動する

ダウンロードしたMT5インストーラーをダブルクリックする。

Windowsから次の確認が表示された場合:

> このアプリがデバイスに変更を加えることを許可しますか？

`はい`を選択する。

インストール画面が表示されたら、すぐに標準設定で進めず、インストール先を変更できる`設定`などの項目を確認する。

---

## 3-6. 本番用MT5のインストール先を変更する

本番用MT5は、現在のデモ用MT5とは異なるフォルダへインストールする。

推奨例:

- デモ用  
  `C:\Program Files\OANDA MetaTrader 5`

- 本番用  
  `C:\OANDA_MT5_LIVE`

または:

- `C:\Program Files\OANDA MT5 LIVE`

分かりやすさと誤操作防止のため、以下のような短く明確なフォルダ名を推奨する。

`C:\OANDA_MT5_LIVE`

重要事項:

- デモ用MT5と同じインストール先を指定しない
- 既存のMT5フォルダへ上書きしない
- インストール先が変更できない場合は、そのまま進めず一旦中止する
- インストール画面の内容はMT5のバージョンによって多少異なる可能性がある

---

## 3-7. 本番用MT5を起動する

インストール完了後、新しくインストールしたMT5を起動する。

デスクトップに新しいショートカットが作成された場合は、右クリックして名前を変更する。

推奨名称:

- `OANDA MT5 DEMO`
- `OANDA MT5 LIVE`

デモ用と本番用を見た目で区別できる状態にしておく。

---

## 3-8. デモ用と本番用のデータフォルダが分離されているか確認する

本番用MT5を起動した状態で、次の操作を行う。

1. `ファイル`
2. `データフォルダを開く`
3. 開いたフォルダの場所を確認する
4. 必要に応じて`origin.txt`を確認する

本番用MT5のデータフォルダが、デモ用MT5とは別になっていることを確認する。

確認項目:

- デモ用と本番用で、開かれるデータフォルダが異なる
- 本番用のインストール先が`C:\OANDA_MT5_LIVE`などになっている
- デモ用のチャートやEA設定が、本番用MT5へ自動的に表示されていない
- デモ用と本番用のグローバル変数が分離されている

分離する理由:

- デモ口座の同日エントリー済み記録を本番口座へ引き継がないため
- デモ口座の週次基準額を本番口座で誤使用しないため
- デモと本番のExpertsログを分けるため
- デモと本番のEA設定を混同しないため
- デモフォワードを残したまま本番運用できるようにするため

---

## 3-9. 本番口座へログインする

本番用MT5から、本番口座へログインする。

操作例:

1. `ファイル`
2. `取引口座にログイン`
3. 本番口座番号を入力
4. 本番口座用パスワードを入力
5. 本番口座の取引サーバーを選択
6. ログインする

ログイン後、以下を確認する。

- 表示されている口座番号が本番口座である
- デモ口座ではない
- サーバー名が本番口座用である
- 残高が本番口座の金額と一致している
- 通信状態が正常である

この段階では、まだ自動売買をONにしない。

設定確認が終わるまでは、MT5上部の`アルゴリズム取引`をOFFにしておく。

---

# 4. 本番用MT5へEAを配置する前の確認

本番用MT5へEAを入れる前に、以下を確認する。

- GitHubにStep9.2.1が保存されている
- GitHubにStep9.2.2が保存されている
- Windows側のGitHub Desktopが対象リポジトリを開ける
- 本番用MT5がデモ用MT5とは別のデータフォルダを使用している
- 本番用MT5の自動売買がOFFになっている

対象リポジトリ:

`TR-KJ/time-entry-portfolio-lab`

対象ファイル:

- `src/EA/time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
- `src/EA/time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

---

# 5. Step9.2.2とStep9.2.1を本番用MT5へ入れてコンパイルする

## 5-1. GitHub Desktopで最新版を取得する

WindowsでGitHub Desktopを起動する。

対象リポジトリを選択する。

`TR-KJ/time-entry-portfolio-lab`

操作:

1. `Fetch origin`を押す
2. 更新がある場合は`Pull origin`を押す
3. `Pull origin`が表示されなくなるまで更新する
4. Windows側がGitHubの最新版になっていることを確認する

本番用MT5へコピーする直前に、必ず最新版を取得する。

---

## 5-2. GitHubのEAフォルダを開く

GitHub Desktop上部メニューから次の操作を行う。

1. `Repository`
2. `Show in Explorer`

Windowsのエクスプローラーが開いたら、以下へ進む。

`src` → `EA`

対象フォルダ:

`time-entry-portfolio-lab\src\EA`

---

## 5-3. 必要な2つのEAファイルをコピーする

以下の2ファイルを選択する。

1. `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
2. `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

2ファイルを選択した状態で、右クリックして`コピー`を選ぶ。

ショートカットキーを使う場合:

`Ctrl + C`

重要事項:

- Step9.2.2だけをコピーしない
- Step9.2.1も必ず一緒にコピーする
- Step9.2.2はStep9.2.1を内部で読み込むため、両方必要
- ファイル名を変更しない

---

## 5-4. 本番用MT5のデータフォルダを開く

デスクトップから、本番用MT5を起動する。

例:

`OANDA MT5 LIVE`

本番用MT5で次の操作を行う。

1. `ファイル`
2. `データフォルダを開く`

ここで、デモ用MT5ではなく、本番用MT5のデータフォルダが開いていることを確認する。

不安な場合は、開いたフォルダのパスまたは`origin.txt`を再確認する。

---

## 5-5. 本番用MT5のExpertsフォルダへ貼り付ける

本番用MT5のデータフォルダから、以下へ進む。

`MQL5` → `Experts`

`Experts`フォルダ内へ、先ほどコピーした2ファイルを貼り付ける。

ショートカットキー:

`Ctrl + V`

正しい配置:

    MQL5
    └─ Experts
       ├─ time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5
       └─ time_entry_step9_2_2_event_overlap_fix_28strategies.mq5

2ファイルは必ず同じ`Experts`フォルダ内に置く。

サブフォルダを使用する場合も、両方を同じサブフォルダへ入れる。

---

## 5-6. ファイル名と拡張子を確認する

貼り付け後、以下を確認する。

- 2ファイルとも存在している
- ファイル名がGitHub上の名前と一致している
- 拡張子が`.mq5`になっている
- `.mq5.txt`になっていない
- Step9.2.1とStep9.2.2が同じフォルダにある

正しいファイル名:

- `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
- `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

Step9.2.2内のinclude指定と、Step9.2.1のファイル名が1文字でも異なるとコンパイルできない。

---

## 5-7. 本番用MT5からMetaEditorを開く

本番用MT5を前面に表示する。

次のいずれかでMetaEditorを開く。

- キーボードの`F4`
- `ツール` → `MetaQuotes Language Editor`

重要事項:

- 必ず本番用MT5からMetaEditorを開く
- デモ用MT5から開いたMetaEditorと混同しない
- MetaEditor上部やフォルダ構成を確認する

本番用MT5から開いたMetaEditorで、本番側の`MQL5\Experts`を編集する。

---

## 5-8. Step9.2.1をコンパイルする

MetaEditor左側のナビゲーターから以下を開く。

`Experts` → `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

ファイルをダブルクリックして開く。

コンパイル操作:

- キーボードの`F7`
- またはMetaEditor上部の`コンパイル`

画面下部のエラー表示を確認する。

必須条件:

`0 errors`

理想:

`0 errors, 0 warnings`

Step9.2.1が正常にコンパイルできない場合は、Step9.2.2の設定へ進まない。

---

## 5-9. Step9.2.2をコンパイルする

次に、MetaEditor左側のナビゲーターから以下を開く。

`Experts` → `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

ファイルをダブルクリックして開く。

コンパイル操作:

- キーボードの`F7`
- またはMetaEditor上部の`コンパイル`

画面下部を確認する。

必須条件:

`0 errors`

理想:

`0 errors, 0 warnings`

コンパイル成功後、同じフォルダ内に`.ex5`ファイルが生成される。

---

## 5-10. includeエラーが出た場合の確認

以下のようなエラーが出た場合:

`cannot open include file`

または:

`time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5 not found`

次の項目を確認する。

1. Step9.2.1が本番用MT5の`MQL5\Experts`に入っているか
2. Step9.2.1とStep9.2.2が同じフォルダにあるか
3. Step9.2.1のファイル名が変更されていないか
4. 拡張子が`.mq5.txt`になっていないか
5. デモ用MT5のExpertsフォルダへ誤って貼り付けていないか
6. GitHubから2ファイルともコピーしたか
7. 全角文字や余分な空白がファイル名に入っていないか

このエラーは、コード本体よりもファイル配置やファイル名が原因である可能性が高い。

---

## 5-11. 本番用MT5でEA一覧を更新する

コンパイル成功後、本番用MT5へ戻る。

ナビゲーターが表示されていない場合:

`Ctrl + N`

ナビゲーター内の`エキスパートアドバイザ`を右クリックする。

`更新`を選択する。

以下が一覧に表示されることを確認する。

- `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies`
- `time_entry_step9_2_2_event_overlap_fix_28strategies`

実際にチャートへセットするのはStep9.2.2だけである。

---

## 5-12. 新しいチャート1枚にStep9.2.2だけをセットする

本番用MT5で新しいチャートを1枚開く。

例:

- 通貨ペア: `USDJPY`
- 時間足: `M15`

このEAは内部で28Strategyを管理するため、チャートの通貨ペアや時間足に合わせて28枚のチャートを開く必要はない。

ナビゲーターから、以下のEAをチャートへドラッグする。

`time_entry_step9_2_2_event_overlap_fix_28strategies`

チャートへセットしてはいけない組み合わせ:

- Step9.2.1とStep9.2.2を同時にセットする
- Step9.2.2を複数チャートへセットする
- 同一口座で同じEAを複数起動する

Step9.2.1はStep9.2.2の内部で読み込まれる土台であり、独立してチャートへセットしない。

推奨構成:

    本番用MT5
    └─ USDJPY M15チャート 1枚
       └─ Step9.2.2のみ稼働

この時点では、まだ`アルゴリズム取引`をONにしない。

---

# 6. 保存したEA設定を読み込む

デモフォワードで正常稼働している設定を、本番用MT5へ移す。

デモ用MT5で、EAの設定画面を開き、設定を保存する。

推奨ファイル名:

`step9_2_2_forward_verified.set`

保存した`.set`ファイルを、本番用MT5でStep9.2.2をセットする際に読み込む。

操作:

1. Step9.2.2の設定画面を開く
2. `パラメータの入力`タブを開く
3. `読み込み`を押す
4. `step9_2_2_forward_verified.set`を選択する
5. 読み込み後、すべての重要設定を目視確認する

設定ファイルを読み込んだだけで自動売買を開始しない。

---

# 7. テスト関連設定をすべてOFFへ変更する

本番運用では、以下の設定を必ず確認する。

| 設定項目 | 本番設定 |
|---|---:|
| `InpTestMode` | `false` |
| `InpTestModeIgnoreEntryWeekday` | `false` |
| `InpTestModeIgnoreExitWeekday` | `false` |
| `InpUseTestTimes` | `false` |
| `InpUseMockJstDateTime` | `false` |
| `InpUJ12ForceGotoMode` | `false` |
| `InpUJ12ForceNormalMode` | `false` |

特に重要:

- `InpTestMode = false`
- `InpUseMockJstDateTime = false`
- `InpUseTestTimes = false`

MockJSTがONのままだと、実際の日付や時刻ではなく、テスト用日時でEAが動作する可能性がある。

---

# 8. ロットとリスク率を確認する

週次複利1％で運用する場合の設定:

| 設定項目 | 本番設定 |
|---|---:|
| `InpLotMode` | `1` |
| `InpWeeklyBaseUseEquity` | `true` |
| `InpRiskPercentPerTrade` | `1.00` |
| `InpAllowMinLotWhenBelowMinimum` | 運用方針に合わせて確認 |
| `InpMaxAutoLot` | 本番口座に合わせて確認 |
| `InpPrintLotLogs` | `true` |

注意:

`InpMaxAutoLot`が`1.00`の場合、計算上のロットが1.00を超えても、最大1.00ロットに制限される。

実運用開始前に、口座残高と想定SL幅を使い、算出されるロットが想定範囲内か確認する。

---

# 9. フィルター設定を確認する

現在の検証内容をそのまま使用する場合の設定:

| 設定項目 | 本番設定 |
|---|---:|
| `InpUseGlobalAtrP70Filter` | `false` |
| `InpUseEventFilter` | `true` |
| `InpUseEventCandidateC` | `true` |
| `InpStopOnUS_NFP` | `true` |
| `InpStopOnUS_CPI` | `true` |
| `InpStopOnFOMC` | `true` |
| `InpStopOnBOJ` | `true` |
| `InpStopOnBOE` | `true` |
| `InpStopOnECB` | `true` |
| `InpStopOnRBA` | `true` |
| `InpStopOnAU_CPI` | `true` |
| `InpUseWeekendMarketClosedGuard` | `true` |
| `InpEmergencyStop` | `false` |

イベント時刻やJST補正は、デモフォワードで正常稼働している設定を変更せず使用する。

確認項目:

- `InpJstOffsetHours`
- FOMC時刻と前後ウィンドウ
- NFP時刻と前後ウィンドウ
- BOJ時刻と前後ウィンドウ
- BOE時刻と前後ウィンドウ
- ECB時刻と前後ウィンドウ
- RBA時刻と前後ウィンドウ
- AU CPI時刻と前後ウィンドウ

---

# 10. 本番開始前の最終確認

自動売買をONにする前に、以下を確認する。

## 口座

- 本番口座へログインしている
- 口座番号が正しい
- デモ口座ではない
- 残高と有効証拠金が正しい
- 自動売買が許可された口座である

## ポジション・注文

- 保有ポジションがない
- 未決済注文がない
- 手動注文が残っていない

## EA

- チャートにはStep9.2.2だけがセットされている
- Step9.2.1はチャートへセットしていない
- Step9.2.2を複数チャートへセットしていない
- コンパイル結果が`0 errors`
- EA右上の名称がStep9.2.2になっている

## テスト設定

- `InpTestMode = false`
- `InpUseMockJstDateTime = false`
- `InpUseTestTimes = false`
- `InpUJ12ForceGotoMode = false`
- `InpUJ12ForceNormalMode = false`

## リスク設定

- `InpLotMode = 1`
- `InpWeeklyBaseUseEquity = true`
- `InpRiskPercentPerTrade = 1.00`
- `InpMaxAutoLot`を確認済み

## フィルター設定

- ATRフィルターOFF
- Event Candidate C ON
- 各イベント停止ON
- Weekend Guard ON
- Emergency Stop OFF

---

# 11. 自動売買をONにする

すべての確認が完了したら、MT5上部の`アルゴリズム取引`をONにする。

チャート右上のEA表示も確認する。

EAが正常に有効化されていることを確認する。

実運用開始直後は、次の項目を重点的に監視する。

- Expertsログ
- 操作履歴またはJournalログ
- エントリー時刻
- Strategy名
- 通貨ペア
- Magic Number
- ロット
- SL
- TP
- イベント停止ログ
- Time Exit
- 口座履歴

---

# 12. Expertsログで起動を確認する

本番開始後、MT5下部の`エキスパート`タブを確認する。

確認したい内容:

- EAの初期化エラーがない
- Symbol準備エラーがない
- ロット計算エラーがない
- includeまたはファイル読み込みエラーがない
- 異常な注文失敗ログがない
- イベントフィルターが正常に判定している
- Weekend Guardが正常に動作している
- エントリー時に想定ロットが出力される

注文が発生した場合は、Expertsログと口座履歴を突き合わせる。

---

# 13. 推奨する最終構成

## デモ用MT5

- 名称: `OANDA MT5 DEMO`
- デモ口座
- 現在のフォワードを継続
- Step9.2.2を1チャートだけで稼働
- 本番との動作比較に使用

## 本番用MT5

- 名称: `OANDA MT5 LIVE`
- 本番口座
- デモとは別のインストール先
- デモとは別のデータフォルダ
- Step9.2.1とStep9.2.2をExpertsフォルダへ配置
- チャートへセットするのはStep9.2.2だけ
- 週次複利リスク1.00％で運用
- Event Candidate Cを使用
- ATRフィルターは使用しない
- Weekend Guardを使用

---

# 14. 実運用開始後の注意事項

- デモ用MT5と本番用MT5を取り違えない
- 本番口座でテスト用MockJSTを使用しない
- Step9.2.2を複数チャートへ入れない
- Step9.2.1を単独で稼働させない
- EA更新時は、保有ポジションと未決済注文を確認してから行う
- Windows Update後はMT5の再起動状態を確認する
- PCのスリープを無効にする
- ネット接続状態を確認する
- MT5の自動売買ボタンがONであることを確認する
- 2026年以降も使用する場合は、イベント日リストの更新が必要
- ブローカーのサーバー時刻や夏時間変更時はJST補正を確認する
- SL、TP、手動決済の結果は口座履歴でも確認する

---

# 15. 実運用移行チェックリスト

## 本番用MT5準備

- [ ] 本番用MT5を別フォルダへインストールした
- [ ] デモ用MT5と本番用MT5のショートカット名を分けた
- [ ] デモと本番のデータフォルダが別である
- [ ] 本番口座へログインした
- [ ] 本番用MT5の自動売買はOFFのまま準備した

## EA配置・コンパイル

- [ ] GitHub Desktopで最新版をPullした
- [ ] Step9.2.1を本番用Expertsへ配置した
- [ ] Step9.2.2を本番用Expertsへ配置した
- [ ] 2ファイルを同じフォルダへ配置した
- [ ] Step9.2.1が`0 errors`でコンパイルできた
- [ ] Step9.2.2が`0 errors`でコンパイルできた
- [ ] 本番用MT5のEA一覧にStep9.2.2が表示された

## チャート・設定

- [ ] 新しいチャートを1枚開いた
- [ ] Step9.2.2だけをチャートへセットした
- [ ] Step9.2.1をチャートへセットしていない
- [ ] Step9.2.2を複数チャートへセットしていない
- [ ] 保存済み`.set`ファイルを読み込んだ
- [ ] すべての設定を目視確認した

## テスト設定

- [ ] `InpTestMode = false`
- [ ] `InpTestModeIgnoreEntryWeekday = false`
- [ ] `InpTestModeIgnoreExitWeekday = false`
- [ ] `InpUseTestTimes = false`
- [ ] `InpUseMockJstDateTime = false`
- [ ] `InpUJ12ForceGotoMode = false`
- [ ] `InpUJ12ForceNormalMode = false`

## リスク・フィルター

- [ ] `InpLotMode = 1`
- [ ] `InpWeeklyBaseUseEquity = true`
- [ ] `InpRiskPercentPerTrade = 1.00`
- [ ] `InpMaxAutoLot`を確認した
- [ ] `InpUseGlobalAtrP70Filter = false`
- [ ] `InpUseEventFilter = true`
- [ ] `InpUseEventCandidateC = true`
- [ ] 各イベント停止設定がtrue
- [ ] `InpUseWeekendMarketClosedGuard = true`
- [ ] `InpEmergencyStop = false`

## 自動売買開始

- [ ] 本番口座に保有ポジションがない
- [ ] 本番口座に未決済注文がない
- [ ] 口座番号とサーバーを再確認した
- [ ] 月曜日から開始する
- [ ] アルゴリズム取引をONにした
- [ ] Expertsログで起動を確認した
- [ ] 初回エントリー時のロット、SL、TPを確認した

---

## 16. 結論

実運用への移行は、現在のデモ用MT5の設定を直接本番口座へ流用するのではなく、デモ用と本番用のMT5を完全に分離して行う。

推奨方針:

- デモ用MT5はそのままフォワード継続
- 本番用MT5を別フォルダへ新規インストール
- 本番用MT5へStep9.2.1とStep9.2.2を配置
- Step9.2.2だけを1チャートへセット
- テスト関連設定をすべてOFF
- 週次複利リスク1.00％を設定
- Event Candidate CをON
- ATRフィルターをOFF
- 月曜日から実運用を開始
- デモと本番の動作を並行比較する

本番開始後も、当面はデモフォワードを残し、エントリー、イベント停止、ロット計算、決済結果に差異がないか比較する。
