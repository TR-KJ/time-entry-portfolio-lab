# B7 U09 Supplemental Conditions Freeze

Additional Source of Truth; conditions only. Existing Conditions and U08 Result Freeze and U09 input remain unchanged. No production change. No formal U09 result viewed; U09Executed=false; Validation/Monitor NOT_RUN.

Supplemental prespec: `research_inputs/b7/u09_supplemental_prespec.json`

SHA256: `cefa5aed9fc820c8bbf4dd4a57622263cd2443bc8509f8016f62bb20e76a92f3`

Implementation must pin the Supplemental Freeze commit and this prespec hash. Exact normative decisions and identities follow.

STOP判断は正しいです。

正式U09結果を一切見ていない現時点で、
未定義だった2点を以下の内容で事前Freezeします。

今回はまず、

# B7 U09 Supplemental Conditions Freeze

を作成・commit・pushし、
そのFreezeを新しいU09実装の追加Source of Truthとしてbindしたうえで、
前回依頼した

# B7 U09 Implementation Only
## 1-minute Entry / Exit Fine Tune

を再開してください。

formal U09は絶対に実行しないでください。

---

# 1. 既存Freezeを変更しない

既存：

Conditions Freeze：

5dbac7af2d41aa912308868e6ad1a6dbf7cdd107

U08 Result Freeze：

382f351c169da48e1fe4eadf31fc858bbd57eed0

U09 input SHA256：

8faa886c3d1a72e8020688b8931481d81d1df637d63b0b368e0171b8d1dce2ca

は不変です。

特に、

research_inputs/b7/full_research_prespec.json
docs/b7/full_research_conditions_freeze.md

を内容変更して既存SHAを壊さないでください。

今回の2点は別のSupplemental Freezeとして追加してください。

推奨：

docs/b7/u09_supplemental_conditions_freeze.md

research_inputs/b7/u09_supplemental_prespec.json

合理的な名称変更可。

---

# 2. Supplemental Decision U09-S01
## Neighborhood Median PFpips

U09 ranking第2項：

Neighborhood Median PFpips

は、各center neighborhoodの

**schedule-valid points**

のうち、

PFState == "FINITE"

かつ

PFpips != null

のpointだけをnumeric medianの算出集合とする。

Formal PASS / Formal FAILは問わない。

したがって、

- Formal FAILでもFINITE PFなら含む
- INFは除外
- UNDEFINEDは除外
- PFpips=nullは除外

とする。

禁止：

- INFを巨大数へ置換
- UNDEFINEDを0へ置換
- PFState独自ranking
- INF > FINITE等のstate ordering追加
- Formal PASS pointsだけに限定
- result-dependent rule追加

Medianはunrounded numeric valueで計算。

偶数個の場合は通常のnumeric median、
すなわち中央2値の算術平均。

---

# 3. PF finite-set empty handling

Plateau ranking対象centerはFormal PASS必須なので、
center自身は：

PFState = FINITE
PFpips >= 1.10

であるはずです。

したがって通常、
Neighborhood Median PFpipsのFINITE集合は
最低1件存在します。

もしranking対象centerでFINITE集合が空なら、

fallback値を作らず、

**invariant violationとしてSTOP**

してください。

---

# 4. Supplemental Decision U09-S02
## all-valid Neighborhood Median AvgPips

Frozen Plateau条件：

All-valid Neighborhood Median AvgPips

について、

schedule-valid neighborhood pointは、
Formal PASS / FAILにかかわらず
all-valid集合のmemberです。

---

# 5. AvgPips=null pointのstatus

schedule-validだが、

AvgPips = null

のpointは、

**schedule validのまま**

です。

invalidへ変更しない。

したがって：

- ValidPointCountに含む
- Formal PASS ratio denominatorに含む
- Point Gate上はFAIL

とする。

0 trades等を理由に
schedule-invalid扱いしてはいけない。

---

# 6. Plateau Median Avgのnull semantics

Neighborhoodのschedule-valid pointに

AvgPips = null

が1件でも存在する場合、

**AllValidMedianAvgPips = undefined**

とする。

以下は禁止：

- nullをMedian集合から除外
- nullを0に置換
- nullを極小値に置換
- forward fill
- interpolation

この場合、

そのcenterは：

**PlateauPASS = false**

とする。

理由をartifactへ明示：

UNDEFINED_VALID_NEIGHBOR_AVG

等のdeterministic reasonを保存。

名称は合理的変更可。

---

# 7. Center AvgPips

Center Formal PASSがPlateauの前提なので、
Plateau候補center自身は、

Trades >=150
AvgPips >0

であり、
Center AvgPipsはdefinedである必要があります。

Center Formal PASSなのにAvgPips=nullなら
schema/invariant errorとしてSTOP。

---

# 8. Anchor Neighborhood Median AvgPips

Fine Tune adoptionのbaseline：

Original Five-Minute Anchor Neighborhood Median AvgPips

にも同じall-valid null semanticsを適用。

すなわちAnchor neighborhoodの
schedule-valid pointに
AvgPips=nullが1件でもあれば、

AnchorNeighborhoodMedianAvgPips
=
undefined

とする。

null除外・0置換は禁止。

---

# 9. Anchor baseline undefined時

Anchor baselineがundefinedの場合、

Fine Tune変更に必要な：

BestNeighborhoodMedianAvgPips
-
AnchorNeighborhoodMedianAvgPips

を証明できない。

したがって、

**時刻変更は採用しない。**

Original Five-Minute Anchorを維持する。

Candidate DROPではない。

探索延長しない。

別のranked plateau candidateへfallbackしない。

Calendar / SL / TPへ戻らない。

推奨decision reason：

ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE

名称は合理的変更可。

これは新しいperformance Gateではなく、

「Fine Tune変更にはFrozen improvement条件を満たした証拠が必要」

という保守的な採用判定。

---

# 10. Decision precedence

最終decisionは概念上：

A.
Plateau PASS centerが0
→ ANCHOR_RETAINED_NO_1M_PLATEAU

B.
Plateau PASS centerあり、
Best centerがAnchor 0/0
→ ANCHOR_RETAINED_BEST_IS_ANCHOR

C.
Best centerが非Anchorだが
AnchorNeighborhoodMedianAvgPips undefined
→ ANCHOR_RETAINED_UNDEFINED_ANCHOR_BASELINE

D.
Anchor baseline definedだが
required improvement未達
→ ANCHOR_RETAINED_INSUFFICIENT_IMPROVEMENT

E.
required improvement達成
→ FINE_TUNED

とする。

rank2以下へのfallback禁止。

---

# 11. Anchor neighborhood valid count

Anchor baseline自体について、
新しいMinimumValidPoints=4等のGateは追加しない。

Frozen MinimumValidPoints=4は
Plateau PASS判定の条件。

Anchor baselineは、

schedule-valid neighborhood pointsについて
AvgPipsがすべてdefinedなら
通常のall-valid medianを計算。

1件でもnullなら前項どおりundefined。

---

# 12. Invalid pointとの区別

schedule-invalid point：

Median集合から完全除外。

schedule-valid / AvgPips=null point：

ValidPointCountには含むが、
all-valid Avg medianをundefinedにする。

この違いをtestsで固定。

---

# 13. Supplemental Freeze identity

Supplemental artifactには最低限：

- Original Conditions Freeze SHA
- U08 Result Freeze SHA
- U09 input SHA
- Decision IDs U09-S01 / U09-S02
- No formal U09 result viewed
- U09Executed=false
- Validation/Monitor NOT_RUN

を記録。

Supplemental prespec自体のSHA256も固定。

---

# 14. Supplemental Freeze commit

まず条件だけをcommit / push。

production code変更なし。

正式result生成なし。

推奨commit message：

Freeze B7 U09 supplemental median semantics

commit後、

- Supplemental Freeze SHA
- supplemental prespec SHA256
- remote SHA = local HEAD
- working tree clean

を確認。

---

# 15. その後U09 Implementation Onlyを再開

Supplemental Freeze commitを
U09 Implementationの追加prerequisiteとしてbind。

U09 formal identityは最低限：

- Original Conditions Freeze
- U09 Supplemental Conditions Freeze
- U08 Result Freeze
- U09 input SHA
- M1 manifest
- 72 M1 identities
- ordered54 CandidateIDs
- environment

を固定。

---

# 16. 追加tests — PF Median

最低限：

- all FINITE
- FINITE + INF
- FINITE + UNDEFINED
- FINITE + null
- Formal FAILだがFINITEは含む
- INFをsentinel化しない
- UNDEFINEDをstate順位化しない
- even-number finite median
- unrounded median
- finite set emptyはSTOP

---

# 17. 追加tests — Avg null

最低限：

- valid Avg nullはValidPointCountに含む
- valid Avg nullはFormal PASS ratio denominatorに含む
- invalid pointはdenominatorから除外
- valid Avg nullが1件 → Plateau FAIL
- nullを0置換しない
- nullをMedian集合から除外しない
- Anchor neighborhood null → baseline undefined
- baseline undefined → Anchor retain
- baseline undefined → Candidate DROPしない
- baseline undefined → rank2 fallbackしない
- baseline undefined → search extensionしない

---

# 18. 既存U09 Implementation依頼はその他すべて維持

前回のU09 Implementation Only promptの：

- ±5分
- 1分刻み
- 最大121
- invalid semantics
- Point Gate
- 3×3 Plateau
- 2/3
- 80%
- ranking
- L1
- Anchor retain threshold
- no re-anchor
- Candidate dropなし
- reference / optimized
- Drive checkpoint
- normal resume
- Finalize-Only
- Colab approval guards
- formal U09未実行

等は変更しない。

---

# 19. U09 Implementation Freeze報告

最終的にChatへ：

1. U09 Supplemental Conditions Freeze SHA
2. supplemental prespec SHA256
3. U09 Implementation Freeze SHA
4. Original Conditions Freeze SHA
5. U08 Result Freeze SHA
6. U09 input SHA
7. U09-S01実装内容
8. PF median finite-only確認
9. INF/UNDEFINED/null非numeric処理確認
10. U09-S02実装内容
11. valid-nullのcount semantics
12. Plateau null処理
13. Anchor baseline null処理
14. decision precedence
15. added tests
16. Total tests PASS/FAIL/SKIP
17. bounded actual smoke
18. formal54未実行
19. 正式FineTune結果未閲覧
20. U10以降未実行
21. Validation/Monitor未実行
22. remote SHA = local HEAD
23. working tree clean

を報告。

ここで停止してください。