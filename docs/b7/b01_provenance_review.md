# B01 provenance再監査 — 2026-10-05

**現在の判定：CLEAR_WITH_LIMITATION。Stage0：PASS_WITH_PROVENANCE_LIMITATION。DataIntegrity：PASS。BrokerIdentity：HISTORICAL_NOT_FULLY_CERTIFIED。**

今回の基点Freeze：`85a7f71770e5751e37698a11bc8a47552befa772`。ユーザーの研究判断によるB01判定更新のみ。追加の取得証拠やbroker認証を得たという意味ではない。

## 研究判断の更新

既存7pairもhistorical 2015–2025のbroker名が全fileで独立証明されているわけではない。EU/GUだけにより厳しい証明を要求する非対称性を避け、監査済み・SHA256固定済みの72 M1 filesを正式なResearch Data Collectionとして採用する。以前のBLOCKED判定はこの研究判断により置き換える。以下の取得証拠・期間別評価自体は変更しない。

- historical broker名は全9pairについて完全には独立証明されていない。
- 2026 Apr–Sepの8pair RECHECKにはDell Inspiron上のOANDAデモMT5取得を支持する具体的記録がある。
- 別broker混入を示す明示的証拠は確認されていない。
- 結果を見た後のsource差替え・再取得・補完は禁止。72-file manifestおよび元データは固定する。

**Stage1開始はStage1条件Freeze後に可能。現在は条件Freeze未完了のため開始しない。**

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

## 今回の更新範囲と停止位置

必要なB01文書・status・判定artifact・artifact manifestだけを更新。取得証拠の各record、27区分の期間別評価、M1 metadataは変更しない。M1 files、72-file manifest、spread/pip、SL proposal、execution、Stage sequence、ranking philosophy、Validation blind rule、code/tests、EA/SET/VPS/live、B6/mainは変更しない。

Stage1MayStart = true AFTER_STAGE1_CONDITIONS_FREEZE。Stage1条件は未Freezeであり、今回Stage1実装・full sweep・Candidate ranking等は実施しない。既存のStage1未決条件はそのまま維持する。
