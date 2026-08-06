# Step9.2.2 VPS移行・最小ロット実運用手順

## 1. 文書の目的

本ドキュメントは、DELL上のOANDA実口座用MT5で正常稼働しているStep9.2.2を、Windows VPSへ安全に移行するための手順を記録する。

移行の段階は次のとおり。

1. DELL・デモ口座でフォワード検証
2. DELL・実口座で固定0.01ロット運用
3. VPSへ環境を構築
4. VPS・実口座で固定0.01ロット運用
5. VPS上で正常稼働を確認
6. 週次複利による本格運用へ移行

本ドキュメントが対象とする段階:

- DELL・実口座・固定0.01ロット
- VPS・実口座・固定0.01ロットへの移行

---

## 2. 対象EA

### 実際にチャートへセットするEA

`time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

### 同じフォルダに必要な依存EA

`time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

Step9.2.2はStep9.2.1を内部でincludeする構成である。

そのため、VPS上のMT5には2ファイルとも配置する。

ただし、チャートへセットするのはStep9.2.2だけとする。

Step9.2.1を別チャートへセットしてはいけない。

---

## 3. 移行前の運用構成

### DELL

- OANDAデモ用MT5
- OANDA実口座用MT5
- 実口座用MT5ではStep9.2.2を固定0.01ロットで運用中

### VPS

- OANDA実口座用MT5を新規インストールする
- DELLに追加のMT5をインストールするわけではない

構成:

- DELL内のMT5: 2つ
- VPS内のMT5: 1つ
- 全環境合計: 3つ

---

## 4. 最重要ルール

同じ実口座で、DELL側とVPS側のEAを同時にONにしない。

禁止状態:

- DELL側アルゴリズム取引: ON
- VPS側アルゴリズム取引: ON

この状態では、同じStrategyがDELLとVPSの両方から重複発注する可能性がある。

EAが使用する同日エントリー済み記録や週次基準額などのMT5グローバル変数は、端末ごとに管理される。

DELL側とVPS側では共有されない。

安全な移行状態:

### VPS準備中

- DELL側: ON
- VPS側: OFF

### 切替時

1. DELL側をOFF
2. DELL側がOFFになったことを確認
3. VPS側をON

### 切替後

- DELL側: OFF
- VPS側: ON

---

# 5. VPS契約後に受け取る情報

VPS契約後、サービス会社から次の情報を確認する。

- VPSのIPアドレス
- Windowsユーザー名
- 初期パスワード
- リモートデスクトップ接続方法
- 管理画面のログイン情報
- VPS再起動方法
- バックアップ機能の有無
- MT5監視機能の有無
- 自動再起動機能の有無
- 障害通知機能の有無

これらの情報は、GitHubへ保存しない。

特に次の情報をGitHubへ書かない。

- VPSのパスワード
- OANDAの取引パスワード
- OANDAの口座番号
- GitHubのパスワード
- 二段階認証コード
- VPS管理画面の認証情報

---

# 6. DELLからVPSへリモート接続する

## 6-1. Windowsのリモートデスクトップを開く

DELLで次の操作を行う。

1. Windowsのスタートメニューを開く
2. `リモート デスクトップ接続`を検索する
3. アプリを起動する

または、キーボードで次を押す。

`Windowsキー + R`

表示された画面へ次を入力する。

`mstsc`

`Enter`を押す。

---

## 6-2. VPSへ接続する

1. `コンピューター`欄へVPSのIPアドレスを入力する
2. `接続`を押す
3. VPSのWindowsユーザー名を入力する
4. VPSのパスワードを入力する
5. 証明書の確認画面が出た場合は、接続先IPを再確認する
6. 問題なければ接続する

接続後、Windowsのデスクトップが表示されればVPSへの接続成功。

---

## 6-3. 初回パスワードを変更する

VPS会社から初期パスワードが発行されている場合は、初回接続後に変更する。

新しいパスワードは次の条件を満たすものにする。

- 他サービスと使い回さない
- 十分に長くする
- 英大文字を含める
- 英小文字を含める
- 数字を含める
- 記号を含める

変更したパスワードをGitHubへ保存しない。

---

# 7. VPSのWindows初期設定

## 7-1. Windows Updateを確認する

VPS上で次を開く。

1. `スタート`
2. `設定`
3. `Windows Update`

更新がある場合は実行する。

再起動が必要な場合は、MT5をインストールする前に再起動を完了させる。

更新後、もう一度Windows Updateを開き、重要な更新が残っていないことを確認する。

---

## 7-2. Windowsのタイムゾーンを確認する

人間がログを確認しやすいように、Windowsのタイムゾーンを日本時間へ設定する。

推奨:

`(UTC+09:00) 大阪、札幌、東京`

ただし、EAの売買時刻はMT5のサーバー時刻と`InpJstOffsetHours`を基準に判定する。

Windowsの時計を日本時間へ変更しただけで、EAの`InpJstOffsetHours`を変更してはいけない。

---

## 7-3. スリープ設定を確認する

VPSがスリープしない設定であることを確認する。

確認項目:

- スリープ: なし
- 休止状態: なし
- 電源停止: なし
- 長時間操作しなくてもWindowsが停止しない

一般的なWindows VPSは常時稼働設定だが、念のため確認する。

---

## 7-4. Windows Updateによる再起動方針

取引時間中に意図せず再起動しないようにする。

推奨方針:

- アクティブ時間を設定する
- 更新は週末に確認する
- 再起動は保有ポジションがない時に行う
- 再起動後は必ずMT5を確認する
- 自動再起動後にMT5が復帰する仕組みを別途確認する

Windows Update自体を永久に無効化する運用は行わない。

---

# 8. OANDA実口座用MT5をVPSへインストールする

## 8-1. OANDA公式サイトからMT5を取得する

VPS上のブラウザを開き、OANDA公式サイトまたはOANDAマイページからWindows版MT5をダウンロードする。

古いインストーラーを流用せず、原則として公式の最新版を使用する。

---

## 8-2. インストーラーを起動する

ダウンロードしたMT5インストーラーをダブルクリックする。

Windowsから次の確認が表示された場合:

`このアプリがデバイスに変更を加えることを許可しますか？`

発行元がOANDAまたはMetaQuotes関連であることを確認し、問題なければ`はい`を選択する。

---

## 8-3. インストール先を設定する

VPSにはOANDA実口座用MT5を1つだけインストールする。

推奨インストール先例:

`C:\OANDA_MT5_LIVE`

または:

`C:\Program Files\OANDA MT5 LIVE`

分かりやすく、短いフォルダ名を推奨する。

---

## 8-4. ショートカット名を変更する

デスクトップに作成されたMT5ショートカットを右クリックする。

推奨名称:

`OANDA MT5 LIVE VPS`

これにより、DELL側のMT5とVPS側のMT5を区別しやすくする。

---

# 9. OANDA実口座へログインする

## 9-1. アルゴリズム取引をOFFにする

MT5上部の`アルゴリズム取引`がOFFになっていることを確認する。

VPS準備中は絶対にONにしない。

---

## 9-2. 実口座へログインする

MT5上部から次を選択する。

1. `ファイル`
2. `取引口座にログイン`

入力する内容:

- OANDAのMT5実口座番号
- MT5実口座用パスワード
- 実口座用サーバー

サーバー例:

`OANDA-Japan MT5 Live`

実際に表示される名称を確認して選択する。

---

## 9-3. ログイン後の確認

次を確認する。

- 口座番号が実口座である
- デモ口座ではない
- サーバー名が実口座用である
- 残高がDELL側の実口座と一致している
- 有効証拠金が一致している
- 保有ポジションが一致している
- 未決済注文が一致している
- 右下の通信状態が正常である

この段階でもアルゴリズム取引はOFFのままにする。

---

# 10. VPSへ移すファイルをDELL側で準備する

## 10-1. GitHub Desktopを最新版にする

DELLでGitHub Desktopを開く。

対象リポジトリ:

`TR-KJ/time-entry-portfolio-lab`

操作:

1. `Fetch origin`
2. 更新がある場合は`Pull origin`
3. 最新状態になるまで更新する

---

## 10-2. EAファイルを確認する

GitHub Desktopで次を選択する。

1. `Repository`
2. `Show in Explorer`
3. `src`
4. `EA`

必要なファイル:

- `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
- `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

---

## 10-3. SETファイルを確認する

VPS最小ロット用として使用するSETファイルを確認する。

推奨ファイル名:

`step9_2_2_live_vps_minlot_verified.set`

まだVPS用SETを作っていない場合は、DELL実口座用の次のSETをコピーして使用する。

`step9_2_2_live_dell_minlot_verified.set`

VPSへ読み込んだ後に内容を再確認し、VPS用の名前で保存する。

---

## 10-4. VPS移行用フォルダを作成する

DELLのデスクトップなどに、次のフォルダを作成する。

`STEP9_2_2_VPS_TRANSFER`

その中へ次の3ファイルをコピーする。

- `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
- `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`
- `step9_2_2_live_dell_minlot_verified.set`

必要に応じて、本ドキュメントも入れる。

---

# 11. DELLからVPSへファイルをコピーする

## 11-1. 推奨方法

リモートデスクトップ接続中に、DELL側のファイルをコピーし、VPS側へ貼り付ける。

操作例:

1. DELL側で`STEP9_2_2_VPS_TRANSFER`を右クリック
2. `コピー`
3. VPSのデスクトップを開く
4. 右クリック
5. `貼り付け`

コピーできない場合は、リモートデスクトップのローカルリソース設定でクリップボードやドライブ共有を確認する。

---

## 11-2. セキュリティ上の注意

VPSへGitHubのパスワードを保存する必要はない。

基本方針:

- GitHubの最新版取得はDELLで行う
- 動作確認済みファイルだけVPSへコピーする
- VPS上で直接EAコードを編集しない
- EAを修正する場合はGitHub側で修正・Commit・Pushする
- VPSへはGitHubから取得した確定版を再配置する

---

# 12. VPSのMT5へEAを配置する

## 12-1. VPS上のMT5データフォルダを開く

VPSのOANDA MT5 LIVEを起動する。

次を選択する。

1. `ファイル`
2. `データフォルダを開く`

開いたフォルダから次へ進む。

`MQL5`

↓

`Experts`

---

## 12-2. EAファイルを貼り付ける

`Experts`フォルダへ次の2ファイルを貼り付ける。

- `time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`
- `time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

2ファイルは必ず同じフォルダに置く。

---

## 12-3. ファイル名を確認する

正しいファイル名:

`time_entry_step9_2_1_event_candidate_c_overlap_fix_28strategies.mq5`

`time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

確認項目:

- 2ファイルとも存在する
- ファイル名がGitHub上の名前と完全一致している
- 拡張子が`.mq5`である
- `.mq5.txt`になっていない
- 2ファイルが同じフォルダにある

Windowsで拡張子が非表示の場合は、エクスプローラーの`表示`から`ファイル名拡張子`をONにする。

ファイルの種類が`MQL5 Source File`なら、基本的に`.mq5`である。

---

# 13. Step9.2.2をコンパイルする

## 13-1. MetaEditorを開く

MT5上部から次を選択する。

`ツール`

↓

`MetaQuotes Language Editor`

または、MT5で`F4`を押す。

---

## 13-2. Step9.2.2を開く

MetaEditor左側のナビゲーターから次へ進む。

`Experts`

↓

`time_entry_step9_2_2_event_overlap_fix_28strategies.mq5`

Step9.2.2をダブルクリックして開く。

---

## 13-3. Step9.2.2をコンパイルする

Step9.2.2を開いた状態で次を実行する。

- `コンパイル`を押す
- または`F7`を押す

確認結果:

- `0 errors`
- 警告が出た場合は内容を確認する

重要:

Step9.2.1だけをコンパイルして完了にしない。

Step9.2.2がStep9.2.1をincludeするため、最終的にStep9.2.2をコンパイルする必要がある。

---

## 13-4. RBA日付を確認する

Step9.2.1を開き、検索機能で次を検索する。

`RBA_2026_DATES`

2026年8月の日付が次になっていることを確認する。

`20260811`

次の誤った日付が残っていないことも確認する。

`20260804`

確認後、Step9.2.2を再度コンパイルする。

---

## 13-5. MT5のナビゲーターを更新する

MT5へ戻る。

ナビゲーターの`エキスパートアドバイザ`を右クリックし、`更新`を押す。

Step9.2.2が一覧に表示されることを確認する。

---

# 14. VPS用チャートを準備する

## 14-1. チャートを1枚だけ開く

任意のOANDA対応通貨ペアのチャートを1枚開く。

例:

`USDJPY`

時間足例:

`M15`

このEAは内部で28Strategyを管理するため、28枚のチャートを開く必要はない。

---

## 14-2. Step9.2.2だけをセットする

ナビゲーターから次をチャートへドラッグする。

`time_entry_step9_2_2_event_overlap_fix_28strategies`

Step9.2.1はチャートへセットしない。

確認事項:

- Step9.2.2をセットしたチャートは1枚だけ
- 他のチャートに同じEAが入っていない
- Step9.2.1がチャートに入っていない

---

# 15. VPS最小ロット用SETを読み込む

## 15-1. EA設定画面を開く

Step9.2.2をチャートへドラッグすると、EA設定画面が開く。

すでにセット済みの場合:

1. 対象チャートをクリック
2. `F7`を押す

---

## 15-2. パラメータを読み込む

1. `パラメータの入力`タブを開く
2. `読み込み`を押す
3. DELLからコピーしたSETファイルを選択する
4. `開く`を押す

読み込むファイル例:

`step9_2_2_live_dell_minlot_verified.set`

---

# 16. VPS最小ロット用インプット最終確認

## 16-1. ロット設定

次を確認する。

- `InpFixedLot = 0.01`
- `InpLotMode = 0`
- `InpMaxAutoLot = 0.01`
- `InpPrintLotLogs = true`
- `InpEmergencyStop = false`

最重要:

- `InpLotMode = 0`
- `InpFixedLot = 0.01`

固定ロットモード中は、1Strategy・1エントリーあたり0.01ロットで動作する。

複数Strategyが同時にポジションを持つ可能性があるため、口座全体の保有ロットが常に0.01になるわけではない。

---

## 16-2. テスト関連設定

次を確認する。

- `InpTestMode = false`
- `InpTestModeIgnoreEntryWeekday = false`
- `InpTestModeIgnoreExitWeekday = false`
- `InpUseTestTimes = false`
- `InpUseMockJstDateTime = false`
- `InpUJ12ForceGotoMode = false`
- `InpUJ12ForceNormalMode = false`

`InpTestMode=false`であれば曜日無視設定は発動しないが、本番用SETでは分かりやすさのため両方falseにする。

---

## 16-3. 時刻関連設定

次を確認する。

- `InpJstOffsetHours = 6`
- `InpSlippagePoints = 30`
- `InpEntryWindowMinutes = 2`

DELL実口座で正常稼働している値から変更しない。

Windowsのタイムゾーンを日本時間に設定しても、`InpJstOffsetHours`を変更しない。

---

## 16-4. ATRフィルター

次を確認する。

- `InpUseGlobalAtrP70Filter = false`

ATR関連の数値は、フィルターOFF中はエントリー判定に使用されない。

---

## 16-5. イベントフィルター

次を確認する。

- `InpUseEventFilter = true`
- `InpUseEventCandidateC = true`
- `InpStopOnUS_NFP = true`
- `InpStopOnUS_CPI = true`
- `InpStopOnFOMC = true`
- `InpStopOnBOJ = true`
- `InpStopOnBOE = true`
- `InpStopOnECB = true`
- `InpStopOnRBA = true`
- `InpStopOnAU_CPI = true`

イベント時刻および停止時間は、DELL実口座で確認済みの値から変更しない。

---

## 16-6. Weekend Guard

次を確認する。

- `InpUseWeekendMarketClosedGuard = true`
- `InpPrintWeekendGuardLogs = true`
- `InpSuppressWeekendGuardLogsOncePerDay = true`

---

## 16-7. ログ設定

VPS最小ロット確認中はログを残す。

推奨:

- `InpPrintDebug = true`
- `InpPrintLotLogs = true`
- `InpPrintEventFilterLogs = true`
- `InpSuppressEventLogsOncePerDay = true`
- `InpPrintRuleRejectLogs = true`
- `InpSuppressRuleRejectLogsOncePerDay = true`
- `InpPrintSkipLogs = false`
- `InpSuppressSkipLogsOncePerDay = true`

---

## 16-8. StrategyのON/OFF

全28StrategyのON/OFFが、DELL実口座用MT5と同じであることを確認する。

意図せずfalseになっているStrategyがないか確認する。

---

# 17. VPS用SETとして保存する

すべてのインプットを確認後、設定画面の`保存`を押す。

推奨ファイル名:

`step9_2_2_live_vps_minlot_verified.set`

保存後、ファイルが存在することを確認する。

この段階では、まだMT5上部のアルゴリズム取引をONにしない。

---

# 18. EA側のアルゴリズム取引許可を確認する

Step9.2.2の設定画面で`共有`タブを開く。

次を確認する。

- `アルゴリズム取引を許可`にチェックが入っている
- DLLの使用許可は、EAが必要としていない限りONにしない
- 外部WebRequest許可は、EAが必要としていない限り設定しない

`OK`を押してEAをチャートへセットする。

MT5上部の`アルゴリズム取引`はまだOFFのままにする。

---

# 19. VPS側の起動ログを確認する

MT5下部の`エキスパート`タブを開く。

確認項目:

- EAの初期化ログが出ている
- 28Strategyの設定一覧が出ている
- 赤いエラーがない
- 対象通貨ペアの準備エラーがない
- `TestMode=false`
- `UseTestTimes=false`
- `UseMockJstDateTime=false`
- Fixed Lotモードである
- Fixed Lotが0.01である
- Event FilterがONである
- Event Candidate CがONである
- ATR FilterがOFFである
- Emergency StopがOFFである

次のようなエラーがないことを確認する。

- `automated trading disabled`
- `trade is not allowed`
- `invalid volume`
- `invalid stops`
- `not enough money`
- `cannot open include file`
- `undeclared identifier`
- `initialization failed`

アルゴリズム取引がOFFの準備段階では、`automated trading disabled`が出る場合がある。

切替後も継続して出る場合は設定を確認する。

---

# 20. VPS再起動後の復帰方法を準備する

## 20-1. VPS会社の監視機能を確認する

VPS会社に次の機能がある場合は設定する。

- MT5稼働監視
- MT5自動再起動
- Windows障害通知
- VPS停止通知
- CPU使用率通知
- メモリ使用率通知
- 自動バックアップ

設定後、通知先メールアドレスが正しいことを確認する。

---

## 20-2. MT5の自動起動を設定する

VPS会社にMT5自動起動機能がある場合は、そちらを優先して使用する。

機能がない場合は、Windowsのスタートアップ登録を検討する。

簡易手順:

1. `Windowsキー + R`
2. `shell:startup`と入力
3. `Enter`
4. 開いたスタートアップフォルダへ`OANDA MT5 LIVE VPS`のショートカットを置く

注意:

スタートアップ登録は、Windowsへログインした後にMT5を起動する仕組みである。

VPS再起動後、誰もWindowsへログインしていない状態で必ず起動するとは限らない。

そのため、VPS再起動後は原則としてリモート接続し、MT5の起動状態を確認する。

---

## 20-3. 再起動テスト

アルゴリズム取引を開始する前に、保有ポジションがない状態で再起動テストを行う。

手順:

1. VPS側のアルゴリズム取引がOFFであることを確認
2. MT5を閉じる
3. VPSを再起動する
4. 再度リモート接続する
5. MT5が起動しているか確認する
6. 実口座へログインしているか確認する
7. Step9.2.2がチャートに残っているか確認する
8. SET値が維持されているか確認する
9. アルゴリズム取引がOFFのままであることを確認する
10. Expertsログを確認する

自動起動されない場合は、VPS会社の監視機能またはスタートアップ設定を見直す。

---

# 21. DELLからVPSへ切り替えるタイミング

最も安全な切替条件:

- DELL側に保有ポジションがない
- 実口座に未決済注文がない
- 当日の同日エントリー済み記録を引き継ぐ必要がない
- 次のエントリー時刻直前ではない
- Time Exit時刻直前ではない
- 重要イベント発表直前ではない
- VPS側の設定確認が完了している
- VPS側のアルゴリズム取引がOFFである

推奨タイミング:

- 週末の市場休場中
- または、全ポジション決済後かつ次のエントリーまで十分な時間がある時
- 可能であれば、新しいJST日付へ切り替わった後
- 本格的な週次複利へ移す場合は月曜日開始

固定0.01ロットのVPS確認段階では、週次基準額は使用しない。

---

# 22. 実際の切替手順

## 22-1. VPS側の最終確認

VPS側で確認する。

- OANDA実口座へログイン済み
- 残高が約50万円で一致
- Step9.2.2が1チャートだけに入っている
- Step9.2.1はチャートへ入っていない
- Fixed Lotが0.01
- Lot Modeが0
- Test Modeがfalse
- Mock JSTがfalse
- ATR Filterがfalse
- Event Filterがtrue
- Event Candidate Cがtrue
- Weekend Guardがtrue
- Emergency Stopがfalse
- EA側のアルゴリズム取引許可がON
- MT5上部のアルゴリズム取引はOFF

---

## 22-2. DELL側を停止する

DELLの実口座用MT5を開く。

1. MT5上部の`アルゴリズム取引`をOFFにする
2. ボタンが停止状態になったことを確認する
3. Expertsログで自動売買停止を確認する
4. 保有ポジションがないことを確認する
5. 未決済注文がないことを確認する

DELL側MT5は削除しない。

緊急時の予備環境として残す。

---

## 22-3. 二重稼働していないことを確認する

切替前状態:

- DELL側: OFF
- VPS側: OFF

この状態を一度作る。

そのうえで、VPS側だけをONにする。

---

## 22-4. VPS側を開始する

VPSへリモート接続する。

1. VPS側の実口座番号を再確認する
2. Step9.2.2の設定を再確認する
3. MT5上部の`アルゴリズム取引`をONにする
4. ボタンがON状態になったことを確認する
5. Expertsログを確認する

切替後状態:

- DELL側: OFF
- VPS側: ON

---

# 23. リモートデスクトップを閉じる方法

VPS上のMT5を稼働させたまま接続を終了する場合は、リモートデスクトップ画面の`×`で接続を閉じるか、`切断`を使用する。

使用しない操作:

- Windowsからサインアウト
- VPSをシャットダウン
- VPSを再起動
- MT5を終了
- OANDA実口座からログアウト

リモートデスクトップを切断しても、通常はVPS上のWindowsとMT5は稼働を続ける。

ただし、サインアウトすると、そのユーザーで起動しているMT5が終了する可能性がある。

日常運用では`サインアウト`ではなく`切断`を使用する。

---

# 24. VPS稼働開始直後の確認

VPS側をONにした直後に確認する。

- Expertsログに異常がない
- 口座残高が正しい
- 通信が正常
- アルゴリズム取引がON
- EAがチャートから外れていない
- Step9.2.2が1つだけ
- DELL側がOFF
- 不要な注文が出ていない
- ロットが0.01
- 証拠金維持率に十分な余裕がある

---

# 25. 初回エントリー時の確認

VPSへ移行後、最初の実注文で次を確認する。

- Strategy名が正しい
- 通貨ペアが正しい
- 売買方向が正しい
- ロットが0.01
- Magic Numberが正しい
- SLが入っている
- 必要なStrategyではTPが入っている
- エントリー時刻が正しい
- 同じStrategyが重複発注していない
- DELL側から注文が出ていない
- Expertsログに成功ログが出ている
- `invalid volume`がない
- `invalid stops`がない
- `not enough money`がない

---

# 26. 初回決済時の確認

初回決済で次を確認する。

- SL決済が正常
- TP決済が正常
- Time Exitが正常
- 対象StrategyとMagic Numberが正しい
- 別Strategyのポジションを誤決済していない
- Expertsログに決済結果が出ている
- 約定履歴がOANDA実口座に反映されている

SL・TPはサーバー側注文として設定されるが、Time ExitはEAがMT5上で稼働している必要がある。

そのため、MT5停止やVPS停止はTime Exitへ影響する可能性がある。

---

# 27. イベントフィルター確認

VPS上でも、実際のイベント日に停止を確認する。

確認対象例:

- 米国雇用統計
- 米国CPI
- FOMC
- BOJ
- BOE
- ECB
- RBA
- 豪州CPI

確認項目:

- 対象Strategyがエントリーしない
- Event Filterログが出る
- イベント対象外Strategyまで誤停止していない
- 日付が最新である
- 発表時刻と停止ウィンドウが正しい

---

# 28. VPS最小ロット確認期間

VPSへ移行後も、すぐに週次複利へ変更しない。

固定0.01ロットのまま、最低限次を確認する。

- 正常なエントリーを1回以上
- SLまたはTP決済を1回以上
- Time Exitを1回以上
- 複数Strategyの同時稼働
- リモート接続を閉じても継続稼働
- VPS再接続後もMT5が稼働
- Windows Update後の復帰
- MT5再起動後の復帰
- イベントフィルター停止
- DELLとの二重発注がない
- 0.01ロットが維持される
- 証拠金不足がない
- 通信切断後に復帰する

推奨確認期間:

- 最低1週間
- 可能であれば2週間
- 実注文と決済を複数回確認する

---

# 29. 日常の確認方法

## 毎日

- VPSへ接続できる
- MT5が起動している
- OANDA実口座へ接続している
- アルゴリズム取引がON
- Step9.2.2がチャートに入っている
- Expertsログに重大エラーがない
- DELL側がOFF
- 不審な重複注文がない

---

## 週1回

- Windows Updateの状態
- VPSの空き容量
- MT5ログの容量
- CPU使用率
- メモリ使用率
- VPS監視通知
- バックアップ状態
- OANDAの取引履歴
- EAコードがGitHub最新版と一致している
- 翌週の重要イベント日程
- EA内イベント日付の更新漏れ

---

## 月1回

- VPS契約・請求状態
- バックアップからの復旧方法
- パスワード管理
- 不要ファイルの整理
- Windowsの再起動
- MT5の再起動
- Expertsログの確認
- OANDA公式メンテナンス情報
- EAイベント日付リスト

---

# 30. VPS障害時の予備運用

VPSに障害が発生した場合は、すぐにDELL側をONにしない。

まず確認する。

1. VPS側MT5が本当に停止しているか
2. VPS側のアルゴリズム取引が停止しているか
3. VPS側から注文が出る可能性がないか
4. 実口座の保有ポジション
5. 未決済注文
6. 当日のエントリー済みStrategy
7. 次のエントリー時刻
8. Time Exit予定時刻

VPS側の停止を確認できた後、必要に応じてDELL側へ切り替える。

緊急切替手順:

1. VPS側の停止を確認
2. OANDA実口座の保有状況を確認
3. DELL実口座用MT5を起動
4. DELL側のSETを確認
5. 同日重複エントリーの可能性を確認
6. 必要なら当日中は新規エントリーを見送る
7. DELL側のアルゴリズム取引をON
8. Expertsログを確認

VPS側の状態が不明なままDELL側をONにしない。

---

# 31. VPSからDELLへ戻す場合

安全な切戻し条件:

- 保有ポジションなし
- 未決済注文なし
- 次のエントリー時刻直前ではない
- VPS側のアルゴリズム取引をOFFにできる
- DELL側の設定が最新
- DELL側EAコードが最新
- DELL側Step9.2.2が再コンパイル済み

切戻し手順:

1. VPS側をOFF
2. VPS側がOFFになったことを確認
3. DELL側を起動
4. 実口座へログイン
5. SETを読み込む
6. 設定を目視確認
7. DELL側だけをON
8. Expertsログを確認

---

# 32. EAコード更新時のルール

EAコードを修正する場合は、VPS上で直接編集しない。

正しい流れ:

1. GitHub管理下のファイルを修正
2. DELLでコンパイル確認
3. GitHubへCommit
4. GitHubへPush
5. VPS側アルゴリズム取引をOFF
6. VPSへ最新版のStep9.2.1とStep9.2.2をコピー
7. VPSでStep9.2.2を再コンパイル
8. 0 errorsを確認
9. SET値を確認
10. 安全なタイミングでVPS側をON

Step9.2.1を変更した場合も、Step9.2.2を再コンパイルする。

---

# 33. 本格運用への移行条件

VPS上で固定0.01ロット運用を継続し、次をすべて確認してから本格運用へ移る。

- エントリー正常
- SL正常
- TP正常
- Time Exit正常
- イベント停止正常
- Weekend Guard正常
- 複数Strategy正常
- Magic Number正常
- 再接続正常
- VPS再起動後の復帰正常
- Windows Update後の復帰正常
- DELLとの二重発注なし
- 重大エラーなし
- 証拠金余力に問題なし

本格運用への変更は、週の途中ではなく月曜日の開始前に行う。

変更予定:

- `InpLotMode = 1`
- `InpWeeklyBaseUseEquity = true`
- `InpRiskPercentPerTrade = 1.00`
- `InpMaxAutoLot = 本格運用の上限値`

本格運用用SETは別名で保存する。

推奨:

`step9_2_2_live_vps_1pct_verified.set`

固定0.01ロット用SETを上書きしない。

---

# 34. VPS移行完了チェックリスト

## VPS環境

- [ ] VPS契約完了
- [ ] リモートデスクトップ接続成功
- [ ] 初期パスワード変更
- [ ] Windows Update完了
- [ ] タイムゾーン確認
- [ ] スリープなし
- [ ] バックアップ設定
- [ ] 障害通知設定
- [ ] MT5監視設定

## OANDA MT5

- [ ] OANDA MT5をVPSへ新規インストール
- [ ] 実口座へログイン
- [ ] 残高一致
- [ ] 通信正常
- [ ] アルゴリズム取引OFFで準備

## EA配置

- [ ] Step9.2.1配置
- [ ] Step9.2.2配置
- [ ] 2ファイルが同じフォルダ
- [ ] ファイル名一致
- [ ] 拡張子`.mq5`
- [ ] RBA日付が20260811
- [ ] Step9.2.2を再コンパイル
- [ ] 0 errors

## チャート

- [ ] チャートは1枚
- [ ] Step9.2.2だけをセット
- [ ] Step9.2.1はセットしていない
- [ ] Step9.2.2の重複なし

## 最小ロット設定

- [ ] `InpFixedLot = 0.01`
- [ ] `InpLotMode = 0`
- [ ] `InpMaxAutoLot = 0.01`
- [ ] `InpTestMode = false`
- [ ] `InpUseTestTimes = false`
- [ ] `InpUseMockJstDateTime = false`
- [ ] `InpEmergencyStop = false`
- [ ] `InpUseGlobalAtrP70Filter = false`
- [ ] `InpUseEventFilter = true`
- [ ] `InpUseEventCandidateC = true`
- [ ] `InpUseWeekendMarketClosedGuard = true`
- [ ] 全StrategyのON/OFF確認
- [ ] VPS用SET保存

## 切替

- [ ] 保有ポジションなし
- [ ] 未決済注文なし
- [ ] DELL側をOFF
- [ ] DELL側OFF確認
- [ ] VPS側をON
- [ ] VPS側ON確認
- [ ] 二重稼働なし
- [ ] Expertsログ正常

## VPS実運用確認

- [ ] 初回エントリー正常
- [ ] ロット0.01
- [ ] SL正常
- [ ] TP正常
- [ ] Time Exit正常
- [ ] イベント停止正常
- [ ] 重複発注なし
- [ ] リモート切断後も稼働
- [ ] VPS再接続後も稼働
- [ ] 再起動後の復帰確認
- [ ] 最低1週間の確認完了

---

# 35. 最終運用構成

## DELL・デモ用MT5

用途:

- フォワード確認
- 新しいEA修正の事前確認
- イベントフィルター確認

状態:

- デモ口座
- 必要に応じてアルゴリズム取引ON

## DELL・実口座用MT5

用途:

- 緊急時の予備
- VPS障害時の切戻し先

通常状態:

- 実口座
- アルゴリズム取引OFF

## VPS・実口座用MT5

用途:

- 実際の24時間運用

通常状態:

- 実口座
- Step9.2.2を1チャート
- アルゴリズム取引ON

---

# 36. 絶対に避けること

- DELLとVPSで同時にEAをONにする
- Step9.2.1とStep9.2.2を両方チャートへセットする
- Step9.2.2を複数チャートへセットする
- テストモードをONのまま実運用する
- Mock JSTをONのまま実運用する
- VPS上で直接EAコードを修正する
- Step9.2.1変更後にStep9.2.2を再コンパイルしない
- 保有ポジションがある状態で安易に切り替える
- リモート接続終了時にWindowsをサインアウトする
- VPSをシャットダウンする
- イベント日付を古いまま放置する
- SETファイルを読み込んだだけで確認せずONにする
- 固定0.01ロットSETを本格運用SETで上書きする
- パスワードや口座番号をGitHubへ保存する

---

# 37. 更新履歴

- 2026-08-06: 初版作成
- 対象: Step9.2.2
- 移行元: DELL・OANDA実口座・固定0.01ロット
- 移行先: Windows VPS・OANDA実口座・固定0.01ロット
