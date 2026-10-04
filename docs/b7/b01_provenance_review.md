# B01 provenance再監査 — 2026-10-05

**最終判定：BLOCKED。Stage0：BLOCKED_PENDING_PROVENANCE。Stage1開始不可。**
基点Stage0 Freeze：`0a5cd78ea6cdcfad81154b6c423413f52a3c470f`。今回の変更はB01の証拠・判定・関連記録だけ。価格の解析、再較正、戦略成績計算、再export・補完・置換なし。

## 判定の変化と理由

新しい具体的証拠「2026-09-09の取得用MT5＝Dell Inspiron上のOANDAデモ口座、同じ流れで8pairのRECHECK取得」を正式に評価した。EU/GUを含む8pairの2026Apr–Sep RECHECKについて、OANDA取得を支持する証拠が得られた。先の「Forex/FXCMかも」という記憶を、今回のBLOCKED根拠には使用しない。

ただし、8pairのこの取得セッションから、別日に作成されたhistorical2015–2025の全export、2026Jan–Mar、またはGAの全セグメントまで同一sourceと遡及推定しない。既存7pairの正式な管理・監査チェーンは強いが、その記録はEU/GUを含まず、歴史的exportのbrokerも明示しない。したがって全9pairの研究source comparabilityを説明するための橋渡し記録がまだ足りない。

CLEAR_WITH_LIMITATIONを採用しなかった理由は「各CSVにbroker欄がない」ことではない。欠けているのは**historical/Q1 EU/GUおよびGAを、そのOANDA取得環境または同一source familyへ結び付ける具体的な取得記録**である。原export記録、当時の一括取得・管理記録、範囲を特定した明確な取得元申告等で十分であり、全fileのbroker metadataや法的証明は要求しない。

## 2026 RECHECKとGA

ユーザー提供の具体的作業記録をE01として保存。元の9月9日Chat原文は今回独立再取得できなかったため、「当時の原文を直接読んだ」とは記載しない。E01自体は今回の正式なprovenance evidenceとして受け入れ、次のexact-file metadataで照合した。

|対象|Drive同期ファイルの更新日時JST|評価|
|---|---|---|
|GA2026Apr–Sep通常版|2026-09-09 12:12:42.622|8pairのRECHECKより前。正常版を保持した可能性と整合|
|UJ RECHECK|2026-09-09 15:31:46.053|8pair連続更新の開始|
|EJ RECHECK|2026-09-09 15:44:22.190|同取得作業の記録と整合|
|GJ RECHECK|2026-09-09 15:45:43.560|同上|
|AJ RECHECK|2026-09-09 15:47:36.963|同上|
|EU RECHECK|2026-09-09 15:48:45.340|明示的OANDA取得記録の対象|
|GU RECHECK|2026-09-09 15:50:01.988|明示的OANDA取得記録の対象|
|EA RECHECK|2026-09-09 15:51:00.213|同取得作業の記録と整合|
|AU RECHECK|2026-09-09 15:56:01.627|8pair連続更新の最後|
|GA2019–2020 RECHECK|2026-09-09 16:00:28.190|直後のhistorical gap再exportと整合|

これは**保存されたmtime順序**であり、認証されたexport操作順序ではない。ファイル名・フォルダ・mtimeだけをbroker証明にはしない。Google Driveのネイティブrevision履歴は取得していない。現在のexact72ファイルはSHA256のみ再照合し、72/72が基点manifestと一致。価格は解析していない。

GAは直接の「2026Apr–Sepの8pair RECHECK」証拠の外にある。一方、初期Daily Stop仕様が**2026-09-09 16:50:23 JST**のcommit `a0d38bf6c0245dadf11a072d99348c48050377f9` に存在し、GAを含む7pairの全期間56file監査、GA2019 gapの再export/M5再現、別brokerで補完しない方針を明記している。GA2019RECHECKの16:00更新→16:50正式監査という履歴は実際に確認できた。ただしこの仕様は取得brokerを名指ししておらず、GAのOANDA帰属までは独立に確定しない。

## Pair・期間別評価

|Pair群|Historical2015–2025|2026Jan–Mar|2026Apr–Sep|
|---|---|---|---|
|EU|B7 exact identity。2/3に6segment更新。取得brokerへの橋渡し未確認|4/18更新。broker橋渡し未確認|具体的8pair取得記録＋mtimeによりOANDA DEMO支持|
|GU|B7 exact identity。2/3に6segment更新。取得brokerへの橋渡し未確認|4/18更新。broker橋渡し未確認|具体的8pair取得記録＋mtimeによりOANDA DEMO支持|
|UJ/EJ/GJ/AJ/AU/EA|既存7pair正式監査・凍結hashの連続性あり。各historical broker未特定|既存監査・hash連続性あり。broker橋渡し未確認|具体的8pair取得記録＋mtimeによりOANDA DEMO支持|
|GA|同じ既存7pair正式監査。2019–2020のみ9/9再export証跡あり。他5segmentは2/1更新。broker未特定|4/22更新、既存監査対象。broker未特定|通常版9/9 12:12を保持。直接の8pair取得記録に含まれずbroker未特定|

Historical更新は2026/1/26〜2/8、Q1更新は4/18・4/22、RECHECKは9/9に分かれる。EU/GU historicalの直後にAU historicalが2/3に更新された点は共通の管理・export習慣を支持する補助証拠として記録したが、取得元の名寄せには使用しない。

## 別broker混入・矛盾・調査限界

- 別brokerの明示的取得記録、historical混在の確定証拠、矛盾する取得記録は、今回の検索範囲では見つからなかった。混入を断定していない。
- 既存7pairの56fileは長期に同一hashで管理された正式研究dataset。これはsource管理の証拠として採用するが、EU/GU historicalを含む同一broker一括取得の記録とは区別する。
- OANDA live/forwardのRepo記録は環境の存在を示す補助情報に留め、historical broker判定には使用しない。価格類似・server timeによるbroker推定も行っていない。
- Repo37branch先端とDaily Stop関連の歴史的commit、Driveの関連metadata・文書/log候補を確認。Chat取得ツールは最近のturnだけを返し、9/9へ進むcursorがなかった。内蔵ブラウザは未ログイン、Chrome閲覧は承認されず、元Chat原文の独立照合は未完了。ただしユーザーが今回提供した具体的記録を無視していない。

## 成果物・不変性・次の停止位置

`provenance_evidence.json` にsource/date/scope/証明すること/証明しないこと/confidence・limitationと27個のpair×period記録を保存。`provenance_file_metadata.csv` は72fileの凍結SHA・今回SHA・mtime・相対保存先。`provenance_status.json`、run status、B01行、Source of Truth・Stage0結果のB01部分、artifact manifestだけを更新した。新規のB01文書・検証記録を追加。

spread/pip、72-file manifest、M1 hash期待値、SL proposal、execution、Stage sequence、ranking、Validation blind rule、全コード・tests、B01以外の数値成果物は不変。検証記録で基点との差分と保護ファイルのhash不変を確認する。B7 branchのみfast-forward公開し、remote=local/cleanを確認する。新Freeze SHAは公開後の引継ぎ報告に記載する。

**Stage1開始不可。今回もStage1実装/sweep・ranking・Top8・Validation・Monitor・Money・R2・B6 Candidate比較・EA/SET/VPS/live変更を行わず、B01再監査で停止。** 他のStage1未決条件もそのままであり、B01判定だけで自動的に研究開始を許可しない。
