# B7 Full Research Conditions Freeze

**P01/P02/U01–U12 + U10-P = AGREED/FROZEN.** Base Freeze: `d625dfb4e360166923b1c390efb94bd1185e1ca6`. Current scope: documentation/config only. Stage1ConditionsFrozen = true; Stage1ImplementationAuthorized = false; Stage1ExecutionAuthorized = false. No implementation, research execution or new performance results opened. B01/Stage0 unchanged.

Machine-readable authoritative companion: `research_inputs/b7/full_research_prespec.json`. Historical `stage1_conditions_freeze.md` and `stage1_prespec.json` retain their original bytes and snapshot status; references and SHA256 are recorded in the full prespec. Their old pending/authorization fields are historical, not current status.

## Previously frozen P01/P02/U01–U05 — unchanged

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



## Newly agreed U06–U12 and U10-P — exact user conditions

# 0. 最重要ルール

今回Freezeする条件は、

**Discovery結果を見る前に固定するB7正式研究ルール**

です。

以下は禁止：

- 結果を見て閾値変更
- Candidateが少ないことを理由に条件緩和
- 0 Candidate pairの救済探索
- SL/TP/曜日/Calendar/Event条件の後付け変更
- Validationを見てDiscoveryへ戻る
- B6既知Candidateへ寄せる

P01/P02/U01〜U05は変更しないでください。

---

# 1. U06 — SL正式選択

Stage1では既にFreeze済みの正式5SLを用いて、

**5SL中3/5以上PASS**

を要求します。

これはU02のままです。

Stage1では最良SLを選びません。

U06で初めて正式SLを1本決定します。

---

## U06-SL Step 1 — PASS Anchor

Stage1の正式5SLのうち、

U02単体GateをPASSしたSLを

`PASS Anchor`

とします。

U02 Gate：

- Total Trades >=150
- 各Discovery年 Trades >=30
- Total Losses >=10
- AvgPips >0
- PFpips >=1.05
- Positive Years >=3/4

---

## U06-SL Step 2 — Local SL scan

各PASS Anchorについて、

**Anchor ±20%**

の範囲を、

**5pips刻み**

で全探索します。

範囲端は5pips単位へ決定論的に丸め、

Anchor自身を必ず含めてください。

例：

Anchor = 65

→ 約52〜78pips

→ local scan：

`50 / 55 / 60 / 65 / 70 / 75 / 80`

---

## 小さいSLの例外

Anchor±20%内に5pips刻みの点が3点未満しか存在しない場合のみ、

最低限、

`Anchor-5 / Anchor / Anchor+5`

の3点まで機械的に拡張してください。

例：

Anchor10 → `5 / 10 / 15`

Anchor15 → `10 / 15 / 20`

結果を見て探索範囲を拡張しないこと。

この拡張ルールは事前固定です。

---

## U06-SL Step 3 — 重複scan統合

複数Anchorのlocal scan範囲が重複した場合、

同一SL値を複数回評価しないでください。

一度だけ評価し、

全local SL点を5pips刻みの一つのSL mapとして統合してください。

---

## U06-SL Step 4 — PASS Zone

local scanの各SL点について、

U02単体Gateを適用します。

そのうえで、

**5pips間隔で3点以上連続してU02 PASSする区間**

をPASS Zone候補とします。

例：

45 PASS  
50 PASS  
55 PASS  
60 PASS  
65 FAIL  
70 PASS  
75 PASS  
80 PASS

なら、

- Zone A = 45/50/55/60
- Zone B = 70/75/80

です。

最大連続区間として抽出してください。

---

## U06-SL Step 5 — Pure Time edge retention

各PASS Zoneについて、

`Zone Median AvgPips >= Pure Time AvgPips × 0.80`

を要求します。

これは、

SL自身80% × 近傍80%

の二重条件にはしません。

**Zone全体の中央値をPure Timeへ直接比較する一本の80%条件**

とします。

これを満たさないZoneは不採用。

---

## U06-SL Step 6 — 複数Zone ranking

正式Zoneが複数ある場合は、

次の固定順で選択してください。

1. Zone Median AvgPips DESC
2. 連続PASS点数 DESC
3. Zone Worst AvgPips DESC
4. Zone Median PFpips DESC
5. Zone中央SL ASC

結果を見て重み付け変更禁止。

---

## U06-SL Step 7 — 最終SL

採用Zoneの中央SLを正式SLとします。

奇数点：

中央1点。

偶数点：

中央2点のうち、

**lower median = 小さい方**

を採用。

例：

50/55/60/65

→ 55pips

です。

したがって最終SLは、元の正式5SL Anchor以外の値になることを許可します。

---

## U06-SL DROP

正式PASS Zoneが一つも存在しない場合、

Candidate DROP。

結果を見て、

- ±30%へ拡張
- 2点連続へ緩和
- 80%を70%へ緩和
- 新SL追加

等は禁止です。

---

# 2. U06 — TP正式探索・決定

正式SLを1本Freezeした後だけTPを探索します。

SLをTP結果から変更しないこと。

---

## U06-TP coarse anchors

正式SLに対して、

- TP_NONE
- 0.5R
- 1.0R
- 1.5R
- 2.0R
- 3.0R

を評価します。

ここで、

`1R = Formal SL pips`

です。

有限TPは、

**5pips half-up**

で固定。

同じpips値へ丸められた重複TPは1回だけ評価してください。

最低有限TPは5pips。

5pips刻みの全面総当たりは禁止。

---

## U06-TP minimum Gate

各有限TP Anchorは、

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.05
- Positive Years >=3/4

を満たす必要があります。

---

## 孤立TP Anchor

有限TP AnchorがPASSしても、

**隣接するcoarse TP Anchorの最低1本もPASS**

していなければ、

そのTPを局所scanへ進めないでください。

例：

1.5RだけPASS  
1.0R FAIL  
2.0R FAIL

→ isolated peakとしてlocal scan対象外。

端：

0.5Rは1.0Rを見る。  
3.0Rは2.0Rを見る。

TP_NONEはlocal TP plateauの隣接Anchorとして扱わない。

---

## U06-TP local scan

局所scan対象となった有限TP Anchorについて、

**Anchor TP pips ±20%**

を5pips刻みで評価します。

SL local scanと同様、

重複TP値は1回だけ評価。

結果を見て探索範囲を追加しないこと。

---

## U06-TP PASS Zone

有限TP local mapから、

U06-TP minimum Gateを満たすTPが

**5pips刻みで連続3点以上**

存在する区間をPASS Zoneとします。

---

## TP Zone ranking

複数Zoneがある場合：

1. Zone Median AvgPips DESC
2. 連続PASS点数 DESC
3. Zone Worst AvgPips DESC
4. Zone Median PFpips DESC
5. Zone中央TP ASC

最終有限TP候補は、

採用Zoneの

**lower median TP**

としてください。

---

# 3. TP_NONEとの正式比較

局所Plateauから有限TP候補が得られても、

自動採用しません。

正式SL + TP_NONEをBaselineとします。

有限TP正式採用には、TP_NONEに対して以下をすべて要求します。

- PositiveYearCount >= TP_NONE
- WorstYearAvgPips >= TP_NONE
- MedianAnnualAvgPips がTP_NONEより

`max(0.10 pips/trade, 5%)`

以上改善

5%はTP_NONE MedianAnnualAvgPipsを基準にします。

最低絶対改善幅は0.10 pips/trade。

条件を満たさなければ、

**TP_NONE採用。**

有限TP側に採用理由を要求します。

MFE/GivebackをTP選択に使用しないでください。

---

# 4. U06完了後

U06で正式にFreezeするもの：

- Formal SL
- Formal TP

以後、

Weekday / DOM / Month / 1m / Event / MFE結果を見て、

SL/TPへ戻らないこと。

---

# 5. U07 — Weekday ON/OFF

U06で固定した

- Pair
- Direction
- Entry
- Exit
- SL
- TP

を全曜日で固定します。

曜日ごとに時間やSL/TPを変更しないこと。

---

## Weekday individual diagnostics

Mon〜Friそれぞれについて、

最低限：

- Trades
- Wins
- Losses
- ZeroPips
- AvgPips
- TotalPips
- PFpips
- MaxDDPips
- annual metrics
- PositiveYearCount
- NegativeYearCount

を保存。

---

## CORE weekday

以下すべて：

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.10
- Positive Years >=3/4

なら

`CORE`

---

## SUPPORT weekday

COREには届かないが、

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.05
- Positive Years >=3/4

なら

`SUPPORT`

---

## NON_SUPPORT

それ以外。

---

# 6. Anchor weekday

U04のTime Family RepresentativeのEntry weekdayを

`Anchor weekday`

とします。

最終SL/TP固定後のU07再評価でも、

Anchor weekdayは

**CORE条件を満たすことを必須**

とします。

AnchorがCOREでなくなった場合、

Candidate DROP。

曜日組み合わせでAnchorの消失を救済しないこと。

---

# 7. Weekday候補Set

31通り総当たりは禁止。

最大4つのnested setのみ作成。

### W0
Anchor weekday only

### W1
全CORE weekdays

### W2
全CORE + SUPPORT weekdays

### W3
Mon〜Fri全5曜日

同一setになる場合は重複除去。

arbitrary subsetは作らない。

---

# 8. Weekday Set Formal Gate

各W set合算で、

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.10
- Positive Years >=3/4

を要求。

PASS setのみ正式比較。

---

# 9. Weekday Set選択

Formal PASSしたsetのうち、

**MedianAnnualAvgPips最大のset**

をBestとします。

そのBestに対し、

`Set MedianAnnualAvgPips >= Best × 0.80`

かつ、

`PositiveYearCount >= Best`

のsetを

`Weekday Performance Plateau`

とします。

そのPlateau内で、

**Active Weekdays数が最も多いset**

を正式採用。

同じ曜日数の重複候補が残る場合は、

W3 → W2 → W1 → W0

の固定優先順で決定してください。

目的：

edgeを大きく薄めない範囲では広い曜日稼働を優先。

一方、本当にAnchor曜日のみが強ければW0を認めます。

---

# 10. U08-A — Day-of-Month 3 bucket

U07までを完全固定した状態で、

- D1 = 1〜10日
- D2 = 11〜20日
- D3 = 21日〜月末

を個別診断。

---

## DOM minimum sample

各bucketについて、

- Candidate全体Tradesの20%以上
- 各年でも、その年Candidate Tradesの20%以上

を最低sample条件とします。

sample不足bucketをOFF候補にしないこと。

---

## DOM OFF候補

minimum sampleを満たし、さらに全部：

- TotalPips <0
- AvgPips <0
- PFpips <1.00
- Negative Years >=3/4

ならOFF候補。

最初の3bucket診断で候補を固定してください。

bucket除外後に新しいOFF候補を追加しないこと。

---

## DOM OFF候補順位

1. NegativeYearCount DESC
2. AvgPips ASC
3. PFpips ASC
4. TotalPips ASC
5. 固定bucket順
   - 1〜10
   - 11〜20
   - 21〜EOM

---

## DOM比較

最大：

### DOM0
全bucket ON

### DOM1
最悪OFF候補1つ停止

### DOM2
上位OFF候補2つ停止

7通り総当たりは禁止。

---

## DOM1採用

DOM0→DOM1で全部：

- AvgPips改善
- PFpips改善
- MedianAnnualAvgPips改善
- PositiveYearCount悪化なし
- MaxDDPips悪化なし

を要求。

---

## DOM2採用

DOM1→DOM2でも同じ条件で、

**さらに改善**

する場合だけDOM2。

改善しなければDOM1。

最大2bucket OFF。

条件を満たせば、最終的に1bucketのみ稼働も許可します。

---

## DOM最終Gate

最終DOM setは、

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.10
- Positive Years >=3/4

を要求。

満たさなければCandidate DROP。

---

# 11. U08-B — Month Seasonality / LOMO

DOM Freeze後。

Jan〜Decを個別診断。

保存：

- Trades
- Wins/Losses
- AvgPips
- TotalPips
- PFpips
- MaxDDPips
- 2020〜2023各年TotalPips
- PositiveYearCount
- NegativeYearCount

---

## Month minimum sample

月停止候補として評価するには、

- Discovery4年合計 Trades >=16
- 各年 Trades >=3

を要求。

---

## Month OFF候補

minimum sampleを満たし、

- 4年合算 TotalPips <0
- PFpips <1.00
- Negative Years >=3/4

をすべて満たす月のみ。

M0状態の12ヶ月診断で候補を固定。

月停止後に新候補を追加しない。

---

# 12. LOMO

12ヶ月それぞれについて、

`Leave One Month Out`

を診断します。

OFF候補月を1ヶ月外した場合に、

- Overall AvgPips改善
- PFpips改善
- MedianAnnualAvgPips改善
- PositiveYearCount悪化なし
- MaxDDPips悪化なし

を要求。

追加の0.10pips等の最低改善幅は設けません。

月自体がすでに、

3/4年マイナス＋PF<1＋Total<0

を満たしていることを前提とします。

---

## Month順位

1. NegativeYearCount DESC
2. AvgPips ASC
3. PFpips ASC
4. TotalPips ASC
5. Month number ASC

---

## Month比較

### M0
月停止なし

### M1
最悪の正式OFF候補1ヶ月停止

### M2
上位正式OFF候補2ヶ月停止

最大2ヶ月停止。

4095通りのmonth ON/OFFは禁止。

M2は、

M1からさらに同じ改善条件を満たした場合のみ採用。

---

# 13. U08完了

U08終了後、

- Weekday
- DOM
- Month stop

を

**Calendar Freeze**

してください。

以後1分Fine TuneやEvent結果を見てCalendarへ戻らない。

---

# 14. U09 — 1-minute Fine Tune

Calendar Freeze後。

固定：

- Pair
- Direction
- SL
- TP
- Weekday
- DOM
- Month stop

5分Anchorに対し、

- Entry = Anchor ±5分
- Exit = Anchor ±5分
- 1分刻み

最大11×11 = 121点。

探索範囲を延長しない。

---

## Invalid shift

1分shiftにより、

- Entry date/weekdayが変わる
- Exit day offsetが変わる
- holdingが30〜1440分外
- execution schedule上無効

となるpointはinvalid。

FAILとして水増しせず、探索対象外。

---

## 1m Point Gate

各1分point：

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.10
- Positive Years >=3/4

---

# 15. 1m Plateau

各centerについて、

Entry ±1分  
Exit ±1分

の最大3×3。

center含む。

条件：

1. Center formal PASS
2. Valid point >=4
3. Formal PASS率 >=2/3
4. 全Valid pointのMedian AvgPips >= Center AvgPips ×0.80

FAIL点をMedianから除外しない。

---

# 16. 1m ranking

Plateau PASS pointを、

1. Neighborhood Median AvgPips DESC
2. Neighborhood Median PFpips DESC
3. Center MedianAnnualAvgPips DESC
4. 5分AnchorからのL1距離 ASC
5. fixed key

で順位付け。

L1距離：

`abs(EntryShiftMinutes) + abs(ExitShiftMinutes)`

---

# 17. Anchor retain rule

1分探索したからといって時刻変更を必須にしません。

正式1分候補へ変更するには、

最良1m candidateのNeighborhood Median AvgPipsが、

5分Anchorを基準としたNeighborhood Median AvgPipsより、

`max(0.05 pips/trade, 2.5%)`

以上改善することを要求。

満たさなければ、

**5分Anchor維持。**

1m Plateauが一つも存在しない場合も、

Candidate DROPではなく、

`ANCHOR_RETAINED_NO_1M_PLATEAU`

として5分Anchor維持。

再anchor・探索延長禁止。

---

# 18. U10 — Event Policy

U10はEvent Filterの最適化Stageではありません。

B7正式Event Modeは、

**結果を見る前にE2を事前採用**

します。

理由：

重要経済イベントによる値動きは、B7で探索した時間edgeとは別の外生的イベントリスクとして扱うため。

---

# 19. Event calendar

B6で監査・Freeze済みのcalendar infrastructureを再利用。

source commit：

`173be2a114dad6bd183a0a1515581528850f0850`

B6 Candidate C strategy-specific matrixは使用しない。

固定Discovery Event：

| Event | Fixed JST | Window |
|---|---:|---:|
| FOMC | 03:00 | ±180m |
| US_NFP | 21:30 | ±120m |
| US_CPI | 21:30 | ±120m |
| BOJ | 12:00 | ±180m |
| BOE | 21:00 | ±120m |
| ECB | 21:15 | ±120m |
| RBA | 13:30 | ±120m |
| AUD_CPI | 10:30 | ±120m |

歴史的発表時刻を今から修正・再構築しないこと。

---

# 20. E0/E1/E2

### E0
Event除外なし

### E1
Pair構成通貨の中央銀行

USD → FOMC  
JPY → BOJ  
EUR → ECB  
GBP → BOE  
AUD → RBA

### E2
E1 +

- US NFP
- US CPI
- AUD pairのみAUD CPI

正式採用は常にE2。

---

# 21. Event overlap

判定区間：

**planned Entry ～ planned Time Exit**

event windowとのoverlapは両端inclusive。

実際にSL/TPで早期決済した場合でも、

planned Time ExitまでをEvent overlap判定に使用。

複数event overlapはtrade除外1回。

---

# 22. E0/E1/E2診断

Discoveryで、

E0/E1/E2をすべて計算し、比較報告してください。

最低限：

- Trades
- RemovedTrades
- Retention
- AvgPips
- TotalPips
- PFpips
- MaxDDPips
- annual metrics

ただし、

**結果をEvent Mode選択に使わない。**

E0が一番良くてもE0へ戻らない。

E1が一番良くてもE1へ変更しない。

正式Event Mode = E2固定。

従来案の

- Retention>=80%
- Removed>=20
- E0からの改善Gate

等は、

採否Gateではなく診断情報としてください。

---

# 23. E2後 Formal Gate

正式戦略はE2適用後の状態です。

E2適用後に、

- Trades >=150
- 各年 Trades >=30
- Losses >=10
- AvgPips >0
- PFpips >=1.10
- Positive Years >=3/4

を要求。

満たさなければCandidate DROP。

成績が悪いからE0/E1へ戻すことは禁止。

---

# 24. U10-P — MFE / Giveback / Profit Protection

U10-PはEvent後、Candidate Freeze前の独立Stage。

ここまでに、

- Pair
- Direction
- Entry/Exit
- SL
- TP
- Weekday
- DOM
- Month
- 1m result
- Event E2

を完全固定。

MFE結果を見て前段条件へ戻らない。

---

# 25. MFE / MAE diagnostics

各正式tradeについて保存：

### MFE
Maximum Favorable Excursion

保有中最大含み益pips。

### MAE
Maximum Adverse Excursion

保有中最大含み損pips。

### FinalPips
正式Exit結果。

### GivebackPips

`MFE - FinalPips`

---

## R normalization

ここでのみ、

`1R = Formal SL pips`

として、

- +0.25R
- +0.50R
- +0.75R
- +1.00R

到達後の最終結果を診断。

RはB7 Candidate rankingには使用しません。

Profit Protection triggerをpair間で共通化するための診断単位のみ。

---

# 26. Winner→Loser

主要Giveback指標：

**MFE >= +0.50Rに到達したのに FinalPips <0**

のtradeを、

`WinnerToLoser`

と定義。

件数・割合・Givebackを保存。

---

# 27. Profit Protection候補

探索自由度を増やさないため、

以下4modeだけ。

### P0
Protectionなし

### P1
+0.50R到達  
→ SLをBreak Evenへ

### P2
+0.75R到達  
→ +0.25RをLock

### P3
+1.00R到達  
→ +0.50RをLock

その他のtrigger/lock値を探索しない。

Trailing幅総当たり禁止。

---

# 28. M1同一bar安全ルール

同一M1 bar内で、

Protection trigger到達と逆行の順序が不明な場合、

楽観的にProtection発動済みと扱わない。

**Protectionはtrigger到達を確認した次のM1 barから有効**

としてください。

M1内High/Low順序を推測しない。

---

# 29. TPとの関係

Freeze済みTPを変更しない。

既存TPがProtection trigger以前に成立するため該当Protectionが意味を持たない場合、

`NOT_APPLICABLE`

としてください。

例：

TP=0.5RでP1 +0.5R BEなど。

MFE結果からTP再最適化禁止。

---

# 30. Profit Protection採用Gate

P1〜P3をP0と比較。

正式採用には全部必要：

- U01相当Gate維持
- TotalPips 悪化なし
- PFpips 悪化なし
- MedianAnnualAvgPips 悪化なし
- PositiveYearCount 悪化なし
- MaxDDPips 悪化なし
- WinnerToLoser件数を **20%以上削減**
- かつ WinnerToLoserを **最低5trade以上削減**

満たさないProtectionは不採用。

---

# 31. 複数Protection PASS時

1. WinnerToLoser削減数 DESC
2. MaxDDPips ASC
3. PFpips DESC
4. TotalPips DESC
5. 単純な方
   - P1
   - P2
   - P3

で固定。

全てFAILなら、

**P0 = Protectionなし**

を正式採用。

---

# 32. Candidate Freeze

U10-P終了後、

以下すべてを完全Freezeしてください。

- Pair
- Direction
- Entry
- Exit
- SL
- TP
- Weekday Set
- DOM Set
- Month stop
- Event = E2
- Profit Protection P0/P1/P2/P3
- spread
- pip size
- execution convention
- data identity
- Discovery metrics
- all config/code/data hashes

このFreeze後にValidationを開きます。

---

# 33. U11 — Validation contract

Validation：

`[2024-01-01, 2026-01-01) JST`

Candidate Freeze条件を一切変更せず実行。

---

## Sample Sufficiency

以下すべて必要：

- 2024 Trades >=30
- 2025 Trades >=30
- Combined Trades >=70
- 2024 Losses >=5
- 2025 Losses >=5

不足：

`INSUFFICIENT_SAMPLE`

FAILとは別status。

---

# 34. Validation Formal PASS

sample十分なCandidateについて、全部必要：

- 2024 TotalPips >0
- 2025 TotalPips >0
- Combined AvgPips >0
- Combined PFpips >=1.10
- Validation MaxDDPips <= Discovery MaxDDPips ×1.50

Discovery AvgPips retention率等をFormal PASS Gateに追加しない。

---

# 35. Validation diagnostics

Formal Gateには使用しないが、

以下は報告可：

- Discovery→Validation AvgPips retention
- PF変化
- TotalPips変化
- MaxDD変化
- WinRate
- annual/monthly metrics
- WinnerToLoser / Giveback
- E2 removed trades
- Protection発動回数
- その他事前定義diagnostics

見た後にValidation Gateを追加しない。

---

# 36. Validation status

### PASS
Sample sufficient + Formal PASS全条件

### FAIL
Sample sufficientだが条件のどれかFAIL

### INSUFFICIENT_SAMPLE
sample不足

準PASS・救済PASS等を作らない。

---

# 37. Validation後の禁止

FAIL Candidateについて、

- Entry/Exit変更
- SL変更
- TP変更
- Weekday変更
- DOM変更
- Month変更
- Event変更
- Protection変更

禁止。

将来別仮説を試す場合は、

B7とは別Research IDとすること。

---

# 38. 2026 Monitor

Formal Validation PASS Candidateのみ。

Monitor：

`[2026-01-01, 2026-09-10)`

statusは、

`OBSERVED_ONLY`

Validation判定を上書きしない。

2026好成績でFAILを救済しない。

2026不調でPASSを取消さない。

---

# 39. U12 — Stage1実装と正式探索の分離

Stage1実装はWork。

正式Stage1 full sweepは、

**Work implementation Freeze → Chat確認 → Google Colab**

の順。

---

## Workで実施可能

- Stage1 code implementation
- tests
- synthetic tests
- bounded actual-data smoke
- notebook作成
- config/manifest/release artifact
- GitHub Freeze

---

## Workで禁止

- Discovery full sweep
- Candidate ranking本結果
- Top8正式選定
- U06以降の正式探索
- Validation
- Monitor
- Money
- Portfolio
- R2

---

# 40. U12正式reference environment

Stage0記録をreferenceとする。

- Python 3.12.14
- NumPy 2.3.5
- pandas 2.2.3

ColabでPython exact version固定が困難な場合：

- 実Python versionを保存
- NumPy/pandasは固定
- tests/reference replay一致必須

環境差を黙って許容しない。

---

# 41. U12 Stage1正式input

正式M1：

**B7 frozen 72-file Research Data Collection**

manifest：

`research_inputs/b7/expected_m1_manifest.csv`

実行開始時に72/72：

- Filename
- SHA256
- Rows
- FirstRaw
- LastRaw

を再監査。

1つでも不一致ならSTOP。

---

# 42. Discovery isolation

Stage1 calculationへ入れるのは、

`[2020-01-01, 2024-01-01) JST`

のみ。

Validation/Monitor rowが同じCSV内に存在しても、

Stage1 calculation arrayへ混入しないことをtestsで保証。

---

# 43. Stage1 formal search space

Freeze済み条件のみ：

- 9 pairs
- Long / Short
- Entry weekday Mon〜Fri個別
- Entry 5分刻み
- holding 30〜1440分、5分刻み
- Pure Time
- Formal Fixed 5SL × TP_NONE

Time Structures：

**7,335,360**

Pure + 5SL evaluations：

**44,012,160**

勝手な時間pruning禁止。

---

# 44. Determinism

並列化は許可。

ただし結果が、

- thread数
- process数
- shard順
- completion順
- filesystem順

で変わらないこと。

trade集計は決定論的順序。

最終sortingはFreeze済みfixed key。

parallel floating-point reduceで判定結果が変わらない設計とする。

---

# 45. Stage1 jobs

基本job単位：

**Pair × Direction × Weekday**

9 × 2 × 5 =

**90 jobs**

各job内：

- Entry 288点
- Hold 283点

---

# 46. Checkpoint / Resume

各job完了後にcheckpoint可能。

ただしResume identity完全一致が必要。

最低限：

- Stage1 implementation commit SHA
- stage1_prespec SHA256
- 72-file manifest SHA256
- official SL grid
- spreads
- pip sizes
- execution convention identity
- Discovery period
- Python/NumPy/pandas versions
- job definition
- U01〜U05 Gate/ranking/family config

不一致checkpointは拒否。

古い結果を自動流用しない。

---

# 47. Stage1 output levels

## Level 1 — Job Summary

90jobs：

- evaluated count
- missing counts
- Pure Time PASS count
- SL robustness PASS count
- errors
- runtime identity

---

## Level 2 — Formal PASS structures

U01 + U02 formal PASSのみ詳細保存。

最低限：

- CandidateID
- structure fields
- overall metrics
- annual metrics
- five-SL metrics
- PF
- AvgPips
- TotalPips
- MaxDDPips

---

## Level 3 — Plateau / Family / Top8

U03/U04後：

- neighborhood diagnostics
- Plateau status
- family suppression
- representative
- supporting weekdays
- suppressed IDs
- pair Top8

を保存。

---

# 48. Raw trade log

全44M variantsのtrade-by-trade logを恒久保存しない。

Top8 families等、後段Candidateについては、

code/config/data hashからtrade logを100%再生成可能にする。

必要になった時点で限定生成。

---

# 49. Work bounded actual-data smoke

Workではperformance探索をしない。

事前固定の少数pair/少数日だけを使い、

- Entry Open
- spread
- Pure Time
- 5SL
- SL hit
- Time Exit
- missing/fallback
- boundary
- deterministic replay

を確認。

正式ranking・Top8・成績表を出さない。

---

# 50. Colab正式本番Barrier

formal full sweep開始前に全部PASS：

1. Repo SHA
2. stage1 config/prespec hash
3. 72-file manifest
4. 72 M1 hashes
5. environment
6. tests
7. bounded reference smoke

1つでもFAILならSTOP。

---

# 51. COMPLETE_STAGE1_ONLY条件

以下すべて完了時のみStage1 COMPLETE：

- 90/90 jobs complete
- 全job identity一致
- missing shardなし
- duplicate jobなし
- expected evaluation count一致
- Formal ranking完了
- Plateau U03完了
- Family suppression U04完了
- pair Top8以下確定
- artifact SHA256 manifest作成

途中結果を正式Candidateとして見ない。

`COMPLETE_STAGE1_ONLY`

まで正式Candidate結果の評価・手動選択をしない。

---

# 52. Colab output

計算：

`/content/b7_stage1`

完了後のみGoogle Driveへ保存。

例：

`/MyDrive/b7_stage1_<date>`

既存folder上書き禁止。

保存：

- effective config
- environment
- input audit
- progress
- 90 job summaries
- formal PASS structures
- plateau diagnostics
- family suppression
- selected Top8/pair
- review JSON
- artifact SHA256 manifest
- archive ZIP

Raw M1は保存しない。

---

# 53. Stage1結果後の禁止

結果を見たあと、

- PF1.10変更
- 3/5変更
- Plateau80%変更
- Family30分変更
- Top8変更
- SL grid変更
- source変更
- spread変更

等は禁止。

pair Candidate 0なら、

**0は0。**

救済探索しない。

---

# 55. Stage sequence更新

正式B7 sequenceを、

1. Stage0 Source/Data/Protocol
2. Stage1 5m Pure Pips + 5SL robustness
3. SL local Plateau / Freeze
4. TP search / Freeze
5. Weekday
6. DOM
7. Month Seasonality / LOMO
8. Calendar Freeze
9. 1m Fine Tune
10. E2 Event Policy + E0/E1/E2 diagnostics
11. MFE/Giveback + Profit Protection
12. Candidate Freeze
13. Validation 2024–2025
14. Monitor 2026
15. B6 structural comparison
16. Money/R/Portfolio/Global R2

へ正式更新してください。

---

# 56. 今回のWorkで実施しないこと

今回は条件Freezeのみ。

禁止：

- Stage1 executor実装
- Stage1 notebook実装
- M1 performance sweep
- Candidate ranking
- Top8
- SL scan実行
- TP scan実行
- Weekday/Calendar実行
- 1m実行
- Event performance実行
- MFE実行
- Validation
- Monitor

新しいperformance結果を開かない。

---

# 58. Status更新

全条件Freezeが完了したら、

- `Stage1ConditionsFrozen = true`

へ更新可能です。

ただし今回のユーザー指示はFreezeのみなので、

- `Stage1ImplementationAuthorized = false`
- `Stage1ExecutionAuthorized = false`

のままとしてください。

Stage1実装は**次の別ユーザー指示**で開始します。

---


## Reproduction and authorization

All previously frozen P01/P02/U01–U05 objects are embedded unchanged in the full prespec. U06–U12 and U10-P contain structured rules and exact user sections. The historical stage1_prespec SHA remains a reference: the future implementation release/effective config must bind the full research prespec as well, not silently run with old pending conditions. No release implementation, Candidate Freeze, Event/MFE result or Stage1 output is created by this documentation Freeze. A separate user instruction is required for implementation; formal sweep follows implementation Freeze → Chat confirmation → Google Colab.
