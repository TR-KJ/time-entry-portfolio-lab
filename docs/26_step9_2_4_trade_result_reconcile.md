# Step9.2.4 注文結果診断・約定照合

## 1. 目的

VPSのMT5 Build 6116で、`trade.Buy / trade.Sell` 後に実際は約定しているにもかかわらず、EA側だけが `false / ResultRetcode=0 / unknown retcode 0` を返す事象へ対応する。

Step9.2.3の28戦略、売買条件、ロット計算、イベントフィルタ、GA_B3の8月停止は変更しない。時間決済の注文結果判定だけを拡張する。

## 2. 対象ファイル

```text
src/EA/time_entry_step9_2_4_trade_result_reconcile_28strategies.mq5
```

ベース：

```text
src/EA/time_entry_step9_2_3_ga_b3_august_stop_28strategies.mq5
```

## 3. 変更内容

注文送信直後に、以下を1行の診断ログへ出力する。

- `trade.Buy / trade.Sell` の戻り値
- `ResultRetcode`
- `ResultRetcodeDescription`
- `ResultOrder`
- `ResultDeal`
- `GetLastError`
- Symbol / Magic / Direction / RequestedLot

`InpPrintTradeResultDiagnostics=true` が既定値。不要時のみ `false` にできる。

通常の `result=true` かつ成功Retcode（`PLACED / DONE / DONE_PARTIAL`）は、Step9.2.3と同じ成功処理を通る。

それ以外（`result=false`、`ResultRetcode=0`、非成功Retcode等）は、注文直前時刻以降に新しく生成された以下の証拠を照合する。

1. 実ポジション
2. `ResultDeal` または取引履歴内の新しいエントリー約定

照合条件：

- 同一Symbol
- 同一Magic
- 同一方向（BUY / SELL）
- 注文直前時刻以降（時刻精度差として2秒だけ許容）
- 実Lotがブローカーの最小・最大Lot内
- 実Lotが要求Lotを半Lot Stepより大きく超えない
- 約定の場合は `DEAL_ENTRY_IN`

条件に一致するポジションまたは約定を確認できた場合だけ、`entry reconciled success` として `MarkEnteredToday()` を実行する。

注文直後の同期照合で確認できない場合は、即失敗にせず戦略単位の「照合待ち状態」へ移る。既定の待機期限は10秒（`InpTradeReconcileTimeoutSeconds`）で、その間は同じ戦略の再注文を抑止する。

`OnTradeTransaction()` の `TRADE_TRANSACTION_DEAL_ADD` を受信したら、上記条件に加え、`ResultOrder != 0` の場合は `DEAL_ORDER == ResultOrder` も必須として照合する。一致した新規エントリー約定を確認できた場合だけ、`entry reconciled success` として `MarkEnteredToday()` を実行する。

Tick/Timerでもポジション・履歴の補助照合を継続する。期限内に確認できなければ `Reconcile=timeout_no_matching_position_or_deal` の失敗ログを出し、`MarkEnteredToday()` は実行しない。

## 4. ログ例

診断ログ：

```text
[Step9.2.4 Trade Result 1_EJ_Log1] Side=BUY, Returned=false, ResultRetcode=0, ResultRetcodeDescription=unknown retcode 0, ResultOrder=0, ResultDeal=0, GetLastError=0, Symbol=EURJPY, Magic=10001, Direction=1, RequestedLot=0.01
```

実ポジションで救済した場合：

```text
BUY entry reconciled success. Symbol=EURJPY, Magic=10001, RequestedLot=0.01, ActualLot=0.01, Evidence=POSITION, Ticket=...
```

照合待ちへ移行した場合：

```text
BUY entry reconciliation pending. Symbol=EURJPY, Magic=10001, RequestedLot=0.01, ResultOrder=42643435, TimeoutSeconds=10
```

期限切れの場合：

```text
BUY entry failed. Symbol=EURJPY, Retcode=0, unknown retcode 0, Reconcile=timeout_no_matching_position_or_deal, ResultOrder=42643435
```

## 5. Build 6116 実機結果と修正理由

VPS MT5 Build 6116、GBPJPY `4_GJ_Port_Log1`、00:00、固定Lot `0.01` で以下を確認した。

- `CTrade::OrderSend`: `unknown retcode 0`
- 診断: `Returned=false / ResultRetcode=0 / ResultOrder=42643435`
- 直後の同期照合: `Reconcile=no_matching_position_or_deal`
- 操作ログ: `accepted -> placed -> order #42643435 done -> deal #33453748 done`
- 同一時刻: `00:00:00.117`

注文送信直後の同期照合が、Deal/Positionの反映より先に完了した可能性が高い。このため、同じStep9.2.4のまま、実際の取引イベントを根拠に確定する非同期照合へ修正した。

## 6. 修正版の検証手順

1. MetaEditorでStep9.2.4をコンパイルし、`0 errors, 0 warnings` を確認する。
2. デモ口座でBUY・SELL各1回を実行し、診断ログと通常の `entry success` を確認する。
3. 存在しないSymbol、異常Lot、取引禁止時間などの失敗では、照合成功にならないことを確認する。
4. VPS Build 6116の実口座で固定Lot `0.01` を1戦略だけ有効にして試験する。
5. `false / ResultRetcode=0` が再現した場合、まず `entry reconciliation pending` が出て即時失敗にならないことを確認する。
6. `DEAL_ADD` 後に `Evidence=DEAL_ADD` の `entry reconciled success` が出て、Ticket・Symbol・Magic・Lot・方向・ResultOrderが実約定と一致することを確認する。
7. 照合待ち中に同じ戦略の注文が再送されず、救済成功後は同日の再エントリーが `already entered today` で抑止されることを確認する。
8. 無関係な別Symbol・別Magic・逆方向・過大Lot・別OrderのDealでは照合成功にならないことを確認する。
9. 約定証拠がない異常結果は10秒後に `Reconcile=timeout_no_matching_position_or_deal` となることを確認する。
10. 通常の `result=true` + `PLACED / DONE / DONE_PARTIAL` 成功パスをBUY・SELL各1回確認する。
11. GA_B3の8月停止と既存イベントフィルタの代表ケースを再確認する。

実口座試験では、DELLとVPSを同時にアルゴリズム取引ONにしない。

## 7. 現時点の検証範囲

このリポジトリ作業環境にはMetaEditor / MT5がないため、構文の静的確認とStep9.2.3との差分確認までを実施する。最終的な `0 errors, 0 warnings` とBuild 6116での実約定照合は、上記手順でWindows側にて確認する。

## 8. 起動時の未初期化pending修正

最新版EX5をVPSへ再セットした直後、アルゴリズム取引OFF・実注文なしにもかかわらず、次のような照合timeoutログが出る事象を確認した。

```text
[Step6.3 Stops 21_GA_B_3] UNKNOWN entry failed. Symbol=GBPAUD, Retcode=0, , Reconcile=timeout_no_matching_position_or_deal, ResultOrder=2459294974414
```

原因は、`EnsurePendingEntryReconciliationArray()` がstruct配列を `ArrayResize()` するだけで、各要素を明示初期化していなかったことにある。起動直後に `active`、方向、Lot、時刻、Ticket、期限、Retcode、説明文字列などが未初期化値として参照されると、実注文由来ではない偽のpendingを `ProcessPendingEntryReconciliations()` が処理し得る。

修正として `ResetPendingEntryReconciliation(int index)` を追加し、以下の全フィールドを既知の安全値へ戻す。

- `active=false`
- `strategy_index=index`
- `direction=0`
- Lot、時刻、Ticket、期限、Retcodeはすべて0
- `retcode_description=""`

`EnsurePendingEntryReconciliationArray()` は配列サイズが変わった場合だけresizeし、拡張で新しく確保された要素だけを明示初期化する。既存要素は保持するため、実注文に由来する照合待ちを誤って消さない。`ClearPendingEntryReconciliation()` も同じリセット関数を使い、activeだけでなく残存フィールドをすべて消去する。

### 確認項目

1. EA再セット直後、アルゴリズム取引OFF・実注文なしで、`UNKNOWN entry failed` や `Reconcile=timeout_no_matching_position_or_deal` が出ない。
2. 28戦略分の配列作成後、全要素が `active=false` で、各 `strategy_index` が配列indexと一致する。
3. 実際の照合待ちが存在する状態で同サイズの確保処理を呼んでも、そのpendingが保持される。
4. 配列拡張時は既存pendingが保持され、新規要素だけが安全初期化される。
5. 照合成功・timeout後のClearで、全フィールドが安全値へ戻る。
6. `OnTradeTransaction()` の非同期照合、10秒timeout、通常成功パスをBUY・SELLで再確認する。
7. 28戦略、イベントフィルタ、GA_B3の8月停止、ロット計算、および時間決済以外の既存処理に差分がないことを確認する。


## 9. 2026-08-19 08:55 時間決済の実機結果

VPS MT5 Build 6116、GBPJPY `4_GJ_Port_Log1` の時間決済で、新規注文時と同じCTrade結果異常を確認した。

- 対象Position: `#42685687`、GBPJPY Long、0.01 Lot
- EA: `CTrade::OrderSend: market sell 0.01 position #42685687 GBPJPY [unknown retcode 0]`
- EA判定: `Time exit failed ... Retcode=0, unknown retcode 0`
- 操作ログ: `accepted -> placed for execution -> order #42695529 done -> deal #33497312 sell 0.01 GBPJPY done -> failed ... [Done]`
- 実状態: Positionは消失し、時間決済自体は08:55に完了

Build 6116の異常は `trade.Buy / trade.Sell` だけでなく `trade.PositionClose(ticket)` にも発生する。Step9.2.4のバージョン名は変えず、時間決済にも診断と非同期約定照合を追加する。

## 10. 時間決済reconciliation仕様

通常の `PositionClose` 成功（戻り値true、Retcodeが `PLACED / DONE / DONE_PARTIAL`）は従来どおり `Time exit success` とする。

false、Retcode=0、または非成功Retcodeでは、Position ticket/identifier、Symbol、Magic、決済方向、Lot、ResultRetcode/Description、ResultOrder/Deal、GetLastErrorを診断ログへ残す。

送信前に固定した対象Position ticketが消失しているか、対応する決済Dealが存在するかを照合する。Dealは `DEAL_ENTRY_OUT / OUT_BY`、同一Symbol/Magic、元Positionと逆の方向、同一 `DEAL_POSITION_ID / POSITION_IDENTIFIER`、注文直前以降（2秒の精度差を許容）、要求LotとのLot Step内一致を必須とする。`ResultOrder != 0` なら `DEAL_ORDER == ResultOrder` も必須である。このため、別Symbol、別Magic、別Position、逆方向、古いDeal、別Order、部分決済だけのDealは採用しない。

同期照合で確認できなければPosition単位のpendingへ移し、既定10秒の間は同じticketへのClose再送を抑止する。`OnTradeTransaction(DEAL_ADD)` と `OnTick / OnTimer` で継続照合し、Position消失または安全な決済Dealを確認した場合だけ `Time exit reconciled success` とする。期限時に同じticket/Symbol/Magic/identifierのPositionが残る場合だけ `Time exit failed ... Reconcile=timeout_position_still_open` とする。

## 11. 時間決済reconcile検証手順

1. MetaEditorでStep9.2.4をコンパイルし、`0 errors, 0 warnings` を確認する。
2. 通常成功する時間決済で従来どおり `Time exit success` になることを確認する。
3. Build 6116の異常時に、全診断項目が出ることを確認する。
4. Positionが直後に消えた場合、`Evidence=POSITION_GONE` の救済成功になることを確認する。
5. 反映が遅い場合、pending後にDEAL_ADDまたはTick/Timerで10秒以内に成功することを確認する。
6. pending中、同じPosition ticketへCloseが再送されないことを確認する。
7. Symbol、Magic、方向、Position ID、Order、時刻、Lotのいずれかが異なるDealを拾わないことを確認する。
8. 部分決済だけでは成功扱いにならず、対象Positionが残ることを確認する。
9. 10秒後にも同じ対象Positionが残る場合だけ真の失敗になることを確認する。
10. 実機ケースのorder `#42695529`、deal `#33497312`、Position `#42685687` の関連が一致して救済されることを確認する。
11. エントリー側reconciliationとpending初期化修正が従来どおり動くことを確認する。
12. 28戦略、イベント、GA_B3 8月停止、ロット、SL/TP、エントリー条件に差分がないことを確認する。

実口座試験では、DELLとVPSを同時にアルゴリズム取引ONにしない。

## 12. 2026-08-24 WeeklyBase異常の実機確認

2026-08-24、VPS実口座でStep9.2.4をWeekly Compoundモードへ移行し、RiskPercent=0.25で運用確認を開始した。

この際、同一週であるにもかかわらず、戦略ごとにWeeklyBaseが変化する事象を確認した。

確認例：

- 08:01 `8_AJ_Core1`
  - WeeklyBase=501141.00
  - RiskPercent=0.25
  - RiskAmount=1252.85

- 13:55 `1_EJ_Log1`
  - WeeklyBase=501027.00
  - RiskPercent=0.25
  - RiskAmount=1252.57

- 15:45 `6_GJ_Old_Mon`
  - WeeklyBase=501101.00
  - RiskPercent=0.25
  - RiskAmount=1252.75

Weekly Compoundの設計上、同一週では最初に確定したWeeklyBaseをGlobal Variableへ保存し、その週の全戦略で同じ値を再利用する必要がある。

しかし、VPSのF3 Global Variablesでは以下のような異常なWeeklyBaseキーが複数生成されていた。

- `TE_STEP7_WEEKLY_BASE_18`
- `TE_STEP7_WEEKLY_BASE_-1849443664`
- `TE_STEP7_WEEKLY_BASE_140183627`

本来は以下の1個だけが生成されるべきである。

`TE_STEP7_WEEKLY_BASE_20260824`

このため、VPSではWeekKeyが取引ごとに異なる値となり、その都度「今週のWeeklyBaseが未作成」と判定され、その時点のEquityを新しいWeeklyBaseとして保存していた可能性が高いと判断した。

なお、この時点の差額は約100円程度であり、RiskPercent=0.25では実際のRiskAmount差は数十銭程度だったため、ロット面で大きな実害はなかった。

ただしWeekly Compoundの根幹に関わるため、本格運用前に原因確認を行うこととした。


## 13. DELLデモとの比較

同日、DELLデモ口座でも同じStep9.2.4のWeekly Compound動作を確認した。

DELLデモでは正常に、

- `TE_STEP7_WEEKLY_BASE_20260817 = 3054141`
- `TE_STEP7_WEEKLY_BASE_20260824 = 2988220`

が作成されていた。

2026-08-24の取引でも、

- 08:01 AJ
- 13:55 EJ
- 18:02 GJ

のすべてで、

`WeeklyBase=2988220.00`

を維持した。

つまり、

「Weekly Compoundの設計そのものが常に壊れている」

わけではなく、DELL環境では正常に週次固定されていることを確認した。

この時点のBuildは以下。

- DELLデモ：Build 6090
- VPS実口座：Build 6140

VPSは2026-08-22にLiveUpdateでBuild 6140を自動ダウンロードし、MT5再起動時にBuild 6140へ更新されていた。

DELL側もBuild 6140のダウンロードまでは完了していたが、MT5を再起動していなかったためBuild 6090のままだった。

このためBuild差も調査対象としたが、後述のDIAG版検証により、Build 6140そのものが必ずWeeklyBase異常を発生させるわけではないことを確認した。


## 14. WeeklyBase診断版の追加

原因切り分けのため、Step9.2.4にWeeklyBase診断ログを追加した。

追加Input：

`InpPrintWeeklyBaseDiagnostics=true`

診断ログでは以下を出力する。

- JST日時
- DayOfWeek
- WeekStartJST
- Year
- Month
- Day
- 現行ロジックで計算したCurrentWeekKey
- year * 10000 + month * 100 + dayで直接計算したDirectWeekKey
- Global Variable名
- ExistingGV
- ExistingGVValue
- NewBaseAmount

ログ例：

`[Step9.2.4 WeeklyBase Diagnostic] JST=2026.08.26 13:55:10, DayOfWeek=3, WeekStartJST=2026.08.24 00:00:00, Year=2026, Month=8, Day=24, CurrentWeekKey=20260824, DirectWeekKey=20260824, GVName=TE_STEP7_WEEKLY_BASE_20260824, ExistingGV=true, ExistingGVValue=501566.00, NewBaseAmount=N/A`

DELLデモでは2026-08-24 18:02に以下を確認した。

- CurrentWeekKey=20260824
- DirectWeekKey=20260824
- GVName=TE_STEP7_WEEKLY_BASE_20260824
- ExistingGV=true
- ExistingGVValue=2988220.00
- NewBaseAmount=N/A

DELL側の診断版は正常に動作した。


## 15. 同名EX5上書き時の注意

DELLでコンパイルした診断版EX5をVPSへ同じファイル名のまま上書きした。

VPSのExpertsフォルダ上では、

- 更新日時
- ファイルサイズ

ともに新しい診断版EX5へ置き換わっていた。

しかし、既存チャート上のEAプロパティには新規Inputである、

`InpPrintWeeklyBaseDiagnostics`

が表示されなかった。

ナビゲータ更新、EA再初期化を行っても反映されなかった。

そこで、同じEX5を別名として、

`time_entry_step9_2_4_trade_result_reconcile_28strategies_DIAG.ex5`

へ変更し、新規EAとしてVPSに認識させた。

このDIAG版では、

`InpPrintWeeklyBaseDiagnostics`

が正常に表示された。

したがって今回の実機環境では、

「同名EX5を上書きしただけでは、既存EAインスタンスが新しいInput定義を即座に反映しない場合がある」

ことを確認した。

今後のEA更新では、単純な同名EX5上書きだけで更新完了と判断せず、

- 新規Inputの表示確認
- EA再初期化ログ
- 新しい診断ログ
- 必要に応じて別名EAでの認識確認

まで行う。


## 16. VPS Build 6140 DIAG版検証結果

VPS実口座、MT5 Build 6140でDIAG版を別チャートへセットした。

DIAG版はWeeklyBase計算まで進ませるため、

- InpEmergencyStop=false
- InpLotMode=1
- InpWeeklyBaseUseEquity=true
- InpRiskPercentPerTrade=0.25
- InpMaxAutoLot=0.10
- InpAllowMinLotWhenBelowMinimum=false
- InpUseGlobalAtrP70Filter=false
- InpTestMode=false
- InpUseTestTimes=false
- InpUseMockJstDateTime=false
- InpPrintWeeklyBaseDiagnostics=true

とした。

安全のため、DIAG版チャートのEA単位の「アルゴリズム取引を許可」はOFFとした。

本番EA側は、

`InpEmergencyStop=true`

を維持し、新規エントリーを停止した。


### 16.1 2026-08-26 13:55 EJ

`1_EJ_Log1`で以下を確認した。

- CurrentWeekKey=20260824
- DirectWeekKey=20260824
- GVName=TE_STEP7_WEEKLY_BASE_20260824
- WeeklyBase=501566.00
- RiskPercent=0.25
- RiskAmount=1253.91
- RawLot=0.0179
- Lot=0.01

F3 Global Variablesにも、

`TE_STEP7_WEEKLY_BASE_20260824 = 501566.0`

が正常に作成された。

10秒後の再処理でも、

- ExistingGV=true
- ExistingGVValue=501566.00
- NewBaseAmount=N/A

となり、新しいEquityを再取得せず既存WeeklyBaseを再利用した。


### 16.2 2026-08-26 18:04 USDJPY

`13_UJ_Fix_MidWeek`でも以下を確認した。

- CurrentWeekKey=20260824
- DirectWeekKey=20260824
- GVName=TE_STEP7_WEEKLY_BASE_20260824
- ExistingGV=true
- ExistingGVValue=501566.00
- WeeklyBase=501566.00
- RiskAmount=1253.91

異なる通貨・異なるMagicでも同じWeeklyBaseを使用した。


### 16.3 2026-08-26 20:56 同時戦略

以下の2戦略が同時にエントリー判定へ進んだ。

- `19_EA_3_WedThu_Long` EURAUD
- `2_EJ_NightBlitz_20` EURJPY

両方とも、

- CurrentWeekKey=20260824
- DirectWeekKey=20260824
- GVName=TE_STEP7_WEEKLY_BASE_20260824
- ExistingGVValue=501566.00
- WeeklyBase=501566.00
- RiskPercent=0.25
- RiskAmount=1253.91

を使用した。

複数戦略が同時刻にロット計算してもWeeklyBaseは変化しなかった。


### 16.4 2026-08-26 21:56 EJ

`3_EJ_NightBlitz_21`でも同様に、

- CurrentWeekKey=20260824
- DirectWeekKey=20260824
- GVName=TE_STEP7_WEEKLY_BASE_20260824
- ExistingGVValue=501566.00

を継続使用した。

2026-08-26の複数時刻・複数Symbol・複数Magicで、WeeklyBaseが501566.00に固定され続けることを確認した。


## 17. DIAG版でのRetcode=10027について

DIAG版は安全確認のため、EA単位の「アルゴリズム取引を許可」をOFFとしている。

そのためエントリー条件成立後は、

- WeeklyBase Diagnostic
- LOT CALC
- CTrade::OrderSend
- ResultRetcode=10027
- `auto trading disabled by client`
- entry reconciliation pending
- 10秒後 timeout

という流れになる。

これはDIAG版の設定による意図した注文拒否であり、Build 6116で発生した、

`Returned=false / ResultRetcode=0 / unknown retcode 0`

とは別事象である。

DIAG版では注文が成立しないため `MarkEnteredToday()` が実行されず、2分間のEntry Window内ではtimeout後に再度Entry判定へ進む。

このため約10秒間隔で、

- WeeklyBase Diagnostic
- LOT CALC
- Retcode=10027
- reconciliation pending
- timeout

が繰り返される。

これは今回の安全な診断方法に伴う挙動であり、WeeklyBase異常ではない。

実運用で正常約定した場合は `MarkEnteredToday()` が実行されるため、同じ戦略の同日再エントリーは抑止される。


## 18. 現時点のWeeklyBase問題の結論

2026-08-24にVPSで確認した異常なWeeklyBaseキー、

- `TE_STEP7_WEEKLY_BASE_18`
- `TE_STEP7_WEEKLY_BASE_-1849443664`
- `TE_STEP7_WEEKLY_BASE_140183627`

は実在するため、異常そのものは事実である。

一方、同じVPS、同じMT5 Build 6140で、新規ロードしたDIAG版では、

`CurrentWeekKey=20260824`

`DirectWeekKey=20260824`

`GVName=TE_STEP7_WEEKLY_BASE_20260824`

が一貫して正常となった。

したがって、

「MT5 Build 6140そのものが必ずWeekKeyを壊す」

とは判断しない。

また、同名EX5上書き時に新しいInputが既存EAインスタンスへ反映されず、別名DIAG版として新規ロードすると正常に認識された事実がある。

このため現時点では、

- 既存EAインスタンスの保持状態
- 同名EX5差し替え時のMT5側の状態
- 旧EAインスタンスと新EX5の組み合わせ
- その他の一時的ランタイム状態

が関係した可能性を疑う。

ただし原因は完全には特定できていないため、

「古いEAインスタンスが原因だった」

とも断定しない。

重要なのは、現在の最新Step9.2.4 DIAG版では、

- WeekStartJST正常
- CurrentWeekKey正常
- DirectWeekKey正常
- Global Variable名正常
- 同一週のWeeklyBase再利用正常
- 異なる戦略・Symbol・MagicでもWeeklyBase共通
- 同時刻の複数戦略でもWeeklyBase共通

までVPS Build 6140実機で確認できたことである。

このため、現時点ではWeekStartDateKeyのロジックを推測だけで変更せず、正常確認できた最新EAを新規インスタンスとして本番へ載せ直す方向を優先する。


## 19. DIAG専用SET

2026-08-26の診断では、初回に以下の設定ミスがあった。

- ATR FilterがON
- TestModeがON
- TestTimesがON

このため2026-08-26 00:00 `4_GJ_Port_Log1`ではWeeklyBase計算まで到達せず、

`ATR ERROR. Symbol=GBPJPY, Reason=CopyBuffer P70 ATR failed. Copied=-1`

となった。

同じミスを繰り返さないため、正常動作を確認したDIAG版設定を専用SETとして保存した。

ファイル名：

`step9_2_4_diag_weeklybase_vps_verified.set`

DIAG検証時は手入力を避け、原則としてこのSETを読み込んで使用する。

特に以下を必ず確認する。

- InpEmergencyStop=false
- InpLotMode=1
- InpWeeklyBaseUseEquity=true
- InpRiskPercentPerTrade=0.25
- InpMaxAutoLot=0.10
- InpAllowMinLotWhenBelowMinimum=false
- InpUseGlobalAtrP70Filter=false
- InpTestMode=false
- InpUseTestTimes=false
- InpUseMockJstDateTime=false
- InpPrintWeeklyBaseDiagnostics=true

なお、EAプロパティ側の「アルゴリズム取引を許可」はSETだけに依存せず、DIAG使用時に必ず手動でOFFを確認する。

DIAG版を実口座で使用する場合は、

「InpEmergencyStop=false」

かつ

「EA単位のアルゴリズム取引許可OFF」

という組み合わせになるため、売買許可の確認を最重要チェック項目とする。


## 20. 本番復帰前の方針

WeeklyBase診断は十分な実機データを取得できたため、診断フェーズは完了とする。

次の本番復帰では、以前の既存EAインスタンスをそのまま再利用するのではなく、今回正常確認した最新Step9.2.4を新規インスタンスとして読み込む方向で検討する。

本番復帰時には最低限以下を確認する。

1. ポジションがないこと。
2. DELL実口座側のアルゴリズム取引がOFFであること。
3. VPS本番EAを1インスタンスだけ稼働させること。
4. 本番用SETを読み込むこと。
5. InpEmergencyStopの状態を意図どおり設定すること。
6. InpLotMode=1を確認すること。
7. RiskPercent=0.25を確認すること。
8. TestMode=falseを確認すること。
9. UseTestTimes=falseを確認すること。
10. UseMockJstDateTime=falseを確認すること。
11. UseGlobalAtrP70Filter=falseを確認すること。
12. Event Filter設定を本番用SETどおり確認すること。
13. 起動時ログを確認すること。
14. F3 Global Variablesを確認すること。
15. 最初の実エントリーでWeeklyBaseとLot計算を確認すること。
16. 最初の実決済でTrade Result / reconciliationを確認すること。

本番復帰後も、少なくとも0.25%運用確認期間中はWeeklyBase、Lot、Entry、Exit、reconciliation、MT5 Build番号を重点監視する。
