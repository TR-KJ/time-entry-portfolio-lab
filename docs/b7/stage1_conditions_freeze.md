# B7 Stage1 conditions Freeze — P01/P02/U01–U05

Status: **AGREED/FROZEN**. Base Freeze: `723ac634fdfbea0827d4e397f722df6b1c771b2d`. This is documentation/config only. U06–U12 remain UNDECIDED; no Stage1 implementation or execution is authorized. B01 and Stage0 remain unchanged. The following is the authoritative user-agreed specification, preserved verbatim for sections 1–12. Machine-readable companion: `research_inputs/b7/stage1_prespec.json`.

# 1. P01 — Fixed SL 5本を正式採用

これまでPROVISIONALだったprice-only SL proposalを正式にAGREED/FROZENへ変更してください。

正式SL grid：

| Pair | SL1 | SL2 | SL3 | SL4 | SL5 |
|---|---:|---:|---:|---:|---:|
| USDJPY | 10 | 25 | 40 | 60 | 95 |
| EURJPY | 15 | 30 | 50 | 75 | 115 |
| GBPJPY | 20 | 40 | 65 | 100 | 150 |
| AUDJPY | 10 | 25 | 40 | 65 | 100 |
| AUDUSD | 10 | 20 | 35 | 55 | 85 |
| EURAUD | 20 | 35 | 60 | 95 | 145 |
| GBPAUD | 20 | 40 | 70 | 110 | 160 |
| EURUSD | 10 | 20 | 35 | 60 | 90 |
| GBPUSD | 15 | 30 | 50 | 80 | 120 |

これらは、

- Discovery 2020–2023のみ
- PnL不使用
- B6と同一のprice-only calibration methodology
- JST Tue–Fri eligible dayのDaily High-Low median
- multiplier = 15% / 30% / 50% / 80% / 120%
- 5pips half-up
- min10 / max300
- strictly increasing

で事前算出された値です。

結果を見て変更しないでください。

Stage1ではこの5SLのみ使用予定です。

追加SLを作らないこと。

---

# 2. P02 — 数値・丸め・DD semanticsを正式Freeze

以下を正式採用してください。

## Pips計算

Gate / ranking / PF / DDはすべて、

**内部の丸め前Pips**

で計算してください。

表示用だけ丸めます。

推奨表示：

- Pips系：小数6桁
- 必要な比率/PF：合理的な固定桁

ただし表示丸め値を判定へ使わないこと。

---

## 年帰属

Annual metricsの年は、

**planned Entry JSTの年**

へ帰属。

Exit年ではありません。

---

## PF

PFpips：

`sum(positive pips) / abs(sum(negative pips))`

丸め前Pipsから算出。

---

## MaxDDPips

各tradeのPipsを時系列で累積。

初期累積Pips = 0

初期Peak = 0

各時点：

`DD = PeakCumulativePips - CurrentCumulativePips`

MaxDDPipsは最大DDを正数で保存。

---

## trade chronological ordering

DD等で完全順序が必要な場合は、

1. CloseTime JST
2. EntryTime JST
3. deterministic fixed key

の順で固定。

同順位処理でPythonの偶然の入力順・filesystem順を使わないこと。

---

# 3. U01 — Pure Time Stage1 Gateを正式Freeze

Pure Time：

- SLなし
- TPなし

について、以下をすべて満たした場合のみStage1 Pure Time PASSとしてください。

### Formal Gate

- Total Trades >= **150**
- 各Discovery年 Trades >= **30**
- Total Losses >= **10**
- Overall AvgPips > **0**
- PFpips >= **1.10**
- PositiveYearCount >= **3 / 4**

Positive Year：

`Annual TotalPips > 0`

です。

0pipsの年はPositive扱いしないこと。

---

## MaxDDPips

Stage1 Pure Time Gateでは、

**MaxDDPipsの絶対上限を置かない。**

MaxDDPipsはmetricとして保存し、ranking後段で使用。

pairごとの値幅差があるため、全pair共通のPips DD gateは設けません。

---

# 4. U02 — Fixed 5SL robustness Gateを正式Freeze

Stage1ではPure Timeと同時に、

各正式SL × TP_NONE

を評価予定。

各SL単体のrobustness PASS条件：

- Total Trades >= **150**
- 各Discovery年 Trades >= **30**
- Total Losses >= **10**
- Overall AvgPips > **0**
- PFpips >= **1.05**
- PositiveYearCount >= **3 / 4**

そして5SLのうち、

**3 / 5以上がPASS**

したTime Structureだけ、

`SL_ROBUSTNESS_PASS`

としてください。

---

## 重要な思想

Pure Timeが主評価です。

Fixed SLは、

**Pure Timeで発見した時間edgeが現実的なSLを置いたとき簡単に消えないか**

を見るsurvival / robustness checkです。

したがって、

Pure Time PF >=1.10

に対し、

SL robustness側はPF >=1.05

とします。

SL performanceを主ランキングにしないこと。

Stage1で「一番良いSL」をまだ選ばないこと。

正式SL選択は後段Stageで行います。

---

# 5. U03 — 5分 Plateau / Neighborhood Ruleを正式Freeze

Stage1 Pure Time + SL robustnessを満たした点について、

5分grid上の局所安定性を確認します。

---

## Neighborhood

中心点：

`(EntryTime, ExitTime)`

に対し、

- Entry：-5 / 0 / +5分
- Exit：-5 / 0 / +5分

の最大3×3 = **9点**

をNeighborhoodとします。

中心点自身を含みます。

---

## Valid neighbor

事前仕様上、

- holding 30～1440分内
- 同じsymbol
- 同じdirection
- 同じEntry weekday
- 同じExit day offset規則
- year boundary / schedule等のexecution rule上有効

な点のみvalid neighborとします。

無効なschedule点をFAILとして水増ししないこと。

---

## Plateau PASS条件

すべて必要：

1. Center point自身がStage1 formal PASS
2. Valid Neighborhood point数 >= **4**
3. Valid Neighborhood内のStage1 PASS比率 >= **2 / 3**
4. Neighborhood Median AvgPips >=  
   **Center Point AvgPips × 0.80**

---

## Medianの計算対象

Neighborhood Median AvgPipsは、

**PASS点だけではなく、validな全Neighborhood点**

を使って計算してください。

FAIL点を除外してMedianを良く見せないこと。

---

## 目的

一点だけ突出したsharp peakではなく、

周辺でもedgeが残るPlateauを選ぶ。

Winner's Curse抑制が目的です。

---

# 6. U04 — Time Family / Near-duplicate Suppressionを正式Freeze

Stage1後、似た時間構造でTop8枠を埋めないため、

Time Familyを定義します。

---

## Same Time Family条件

以下をすべて満たす候補をnear-duplicate family候補とします。

- Symbol：同じ
- Direction：同じ
- Entry circular time distance <= **30分**
- Exit circular time distance <= **30分**
- Planned holding difference <= **30分**
- Exit day offset：同じ

### Weekday

**Entry weekdayが異なっていても、同一Time Familyとして抑制可能**

とします。

理由：

後段にWeekday ON/OFF専用Stageがあるため、

Mon/Tue/Wedのほぼ同じ時間edgeでTop8枠を複数消費させないためです。

---

## Representative selection

Stage1正式ranking順に候補を見る。

最初の未抑制候補をFamily Representativeとする。

そのRepresentativeに直接near条件を満たす後続候補を抑制。

---

## Non-transitive

**連鎖mergeは禁止。**

例：

- AとBは近い
- BとCは近い
- AとCは30分条件外

の場合、

A familyへCを自動吸収しない。

Representativeとの直接距離だけで判定。

---

## Weekday情報

曜日違い候補をfamily suppressionしても、

元情報は捨てないでください。

Representative artifactには最低限、

- Anchor weekday
- Supporting weekdays
- 各weekdayの元metric
- 抑制された候補ID

を追跡可能にしてください。

後段のWeekday ON/OFF Stageで利用します。

---

## Pair Top8

Near-duplicate suppression後、

各pair最大 **8 Time Families**

最低保証なし。

不足時のrefillルールは、

ranking順に次の未抑制candidateを採る通常処理のみ。

不合格候補を救済しないこと。

---

# 7. U04 Fixed Keyを正式Freeze

完全同順位や決定論的sortingが必要な場合のfixed keyを以下で固定してください。

1. Symbol
2. Direction  
   - LONG先
   - SHORT後
3. Entry weekday  
   - Monday→Friday
4. Entry minute of day
5. Exit day offset
6. Exit minute of day
7. Planned holding minutes
8. CandidateID

CandidateID自体も上記固定情報から決定論的に生成してください。

filesystem order / DataFrame original order / parallel completion orderをtie-breakに使わないこと。

---

# 8. U05 — PF / INF / UNDEFINED / ZeroPips semanticsを正式Freeze

以下を正式採用してください。

## PF状態

### 通常

positive sum >0  
negative sum <0

の場合：

`PF = positive sum / abs(negative sum)`

---

### INF

positive sum >0  
negative sum =0

の場合：

`PF = INF`

Infinity。

ただしnumeric sentinel、

- 999
- 1e9
- float最大値

などへ置換しないこと。

---

### PF = 0

positive sum =0  
negative sum <0

の場合：

`PF = 0`

---

### UNDEFINED

以下は：

`PF = UNDEFINED`

- positive sum =0 かつ negative sum =0
- Trades =0
- 全tradeがZeroPips

UNDEFINEDを0やINFへ変換しないこと。

---

# 9. U05 — Stage1でのINF扱い

Pure Time / SL robustnessともに、

**Total Losses >=10**

がFormal Gateに含まれるため、

PF=INFのcandidateはFormal PASSできません。

したがって、

INFをランキング最上位の数値として扱わないこと。

Formal PASS candidateでは通常PFが定義される設計です。

---

# 10. ZeroPips

Pips = 0のtradeは、

- Tradesには含める
- Winsには含めない
- Lossesには含めない
- positive pips sumへ含めない
- negative pips sumへ含めない

とします。

---

# 11. Annual metric semantics

各Discovery年について、

Annual TotalPips >0  
→ Positive Year

Annual TotalPips =0  
→ Positive Yearではない

Annual TotalPips <0  
→ Negative Year

---

## Annual sample

各年Trades <30ならStage1 Formal Gate FAIL。

4年すべてが正式Annual sample条件を満たさなければ、

MedianAnnualAvgPipsを正式ranking用として採用しない。

欠けた年を除外して、

「3年だけのMedian」

などを作らないこと。

---

# 12. Stage1 rankingを再確認

Formal eligible candidateのpair内rankingは既合意通り：

1. PositiveYearCount DESC
2. MedianAnnualAvgPips DESC
3. WorstYearAvgPips DESC
4. PFpips DESC
5. Overall AvgPips DESC
6. TotalPips DESC
7. MaxDDPips ASC
8. fixed key

今回U05の定義により、

Formal ranking対象ではPF INF / UNDEFINEDが通常入らない設計にしてください。

---


## Scope and interpretation

Stage1 formal point PASS means Pure Time PASS AND SL_ROBUSTNESS_PASS. Neighborhood PASS counts use this point-level gate; they do not recursively require Plateau PASS. Final ranking eligibility also requires Plateau PASS. All valid neighborhood points, including formal FAIL points, belong in its median; do not drop them to improve the metric.

The fixed key determines order. CandidateID must derive deterministically from the preceding structure fields; concrete artifact serialization remains within the unresolved U12 contract. No new serialization/runtime policy is frozen here.

Original Stage0 proposal CSVs and calibration outputs remain immutable historical calculation artifacts; their PROVISIONAL labels describe their original snapshot. P01 now formally adopts their exact nine grids through this specification and the Decision Register. No recalibration occurred.

P01/P02/U01–U05 are frozen; U06–U12 remain UNDECIDED. U12 runtime/resume/artifact/Colab contract is not frozen, and this request explicitly forbids Stage1 implementation/execution. No new M1 performance results are opened.
