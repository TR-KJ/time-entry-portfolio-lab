# 100 C6 Portfolio Signal Crowding Phase 1 — Result

**Verdict: NOT_SUPPORTED. Phase2Eligible: False.**

The adjusted 6h slope is positive but its preregistered 95% CI includes zero. Gate B fails; A/C/D/E/F/G/H pass. This does not establish a negative crowding effect or sufficient support for a positive risk layer. Stop C6 without new windows, thresholds or a Phase 2 money simulation.

## Frozen run and inputs

- Branch: `research/c6-portfolio-signal-crowding-phase1`.
- Plan SHA: `24653fa83a652a18ca6d0ed20a113680a73f35a3`; remote verified before code.
- Implementation SHA: `0d64cc740878f867026a9caf35196924e6297219`; remote verified before outcome calculation.
- Result SHA is the commit containing this document, recorded in the final handoff.
- Baseline SHA-256: `cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359`.
- Reused C4 R2 assignment SHA-256: `49f602f6ecb19039c7e7a82b4884f8d82b423fe604c58066df44de2307656021` (3,756,484 bytes).

The original fixed 28-strategy / 16,298-trade baseline was verified. Primary timeline and observations both exclude Strategy22, leaving **27 strategies / 15,837 trades**. Every retained R is unchanged; Total R remains 1,360.253363762. No new signals or trade log were generated. C4 assignment identity/Strategy/Symbol/R/TradeID regression covers all 15,837 rows; 248 active saved trade audit rows and 135 primary Strategy×Q aggregate rows match existing references. R2-unavailable observations: **1,186**, retained as a separate additive FE category. No M1 data or new volatility calculation was required.

Signals are actual fixed baseline entries. The windows are inclusive [t−6h,t] / [t−12h,t], excluding only self. Same-time other signals are included symmetrically. Closed positions, direction and symbol do not affect membership. Features were computed on the entire fixed active timeline before period/LOSO subsetting. 2022–2026 is previously viewed, not a pristine unseen holdout.

## 6h distribution and raw relation

|Trades|Weeks|Min|Max|Mean|Median|P05|P25|P75|P95|P99|Distinct|LargestBucketFraction|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|15837|599|0|7|1.93685673|2|0|1|3|5|7|8|0.248405632|

|SignalCount|Trades|AvgR|TotalR|PF|WinRate|AvgWinR|AvgLossR|
|---|---|---|---|---|---|---|---|
|0|3646|0.0898748749|327.683794|1.38843918|0.532089962|0.60374989|-0.495938267|
|1|3934|0.0934390102|367.589066|1.38791421|0.540671073|0.618332434|-0.525862386|
|2|2987|0.0759983654|227.007117|1.39003124|0.550050218|0.492410239|-0.434345452|
|3|2295|0.0851855437|195.500823|1.47868431|0.561655773|0.46851332|-0.408412847|
|4|1553|0.0556682549|86.4527998|1.32076364|0.540888603|0.423779311|-0.380680539|
|5|1046|0.0849131018|88.8191044|1.46571467|0.569789675|0.469018147|-0.427613702|
|6|193|0.0985274725|19.0158022|1.39288348|0.544041451|0.64206112|-0.550006993|
|7|183|0.26330523|48.1848571|1.85485678|0.595628415|0.959182176|-0.761702703|

Raw 6h OLS slope: **0.000335735884R per additional signal**. Raw count means are not monotonically ordered; monotonicity was not a gate. Every count bucket has positive observed AvgR. These descriptive means do not justify an entry skip or a new threshold.

## Additive adjusted beta and robustness

|Feature|Beta|CILower|CIUpper|ValidBootstrap|EqualWeightSlope|EligibleStrategies|
|---|---|---|---|---|---|---|
|SIGNAL_COUNT_6H|0.0129871407|-8.63588141e-05|0.0259952821|5000|0.0193964422|20|
|SIGNAL_COUNT_12H|0.0051624133|-0.00308364729|0.0131311943|5000|0.00395626379|26|

Model: R = intercept + Strategy FE + R2 category FE + beta×integer signal count. Strategy and R2 are separate main effects. Beta is an observational conditional association in R per additional other signal; it is not a simulated portfolio profit gain or a causal effect.

Primary beta6 = **0.012987140726**, 95%CI **[-0.000086358814, 0.025995282136]**. The lower bound is negative even though close to zero. The registered strict exclusion-of-zero rule is unchanged. No additional seeds, windows or thresholds were searched.

Cluster bootstrap: Monday-start JST entry weeks, 5,000 replicates per feature/period, PCG64 seed 20260913 restarted for each. The additive FE model is refit in every replicate via exact week cross-products. All 5,000 replicates are valid in each of 12 fits. 12h CI exclusion is descriptive only; its adjusted beta has the required positive sign. Strategy equal-weight robustness averages raw within-strategy slopes of eligible strategies, as registered.

## Fixed-period stability

|Period|Trades|Mean|Beta|CILower|CIUpper|EligibleStrategies|Distinct|PeriodEligible|
|---|---|---|---|---|---|---|---|---|
|Historical|9482|1.94452647|0.00544520915|-0.0112441539|0.0214504232|19|8|True|
|Recent A|2688|1.92299107|0.0331760875|-0.000591664691|0.0659691072|16|8|True|
|Recent B|2701|1.92521288|0.0242681699|-0.0119673124|0.0612058555|17|8|True|
|2026 Monitor|966|1.93271222|0.00173025473|-0.0365973469|0.0373577859|10|8|True|
|Recent Combined|6355|1.92541306|0.0244455955|0.00350175983|0.0461007164|18|8|True|
|ALL|15837|1.93685673|0.0129871407|-8.63588141e-05|0.0259952821|20|8|True|

All primary period betas are positive. Recent A/B/2026 are all eligible under fixed sample/variation criteria. Recent Combined alone has a CI excluding zero; it cannot replace ALL as primary.

12h period robustness:

|Period|Trades|Beta|CILower|CIUpper|
|---|---|---|---|---|
|Historical|9482|0.00424559697|-0.00580009708|0.014035088|
|Recent A|2688|0.00463776834|-0.0158466013|0.0236158564|
|Recent B|2701|0.0127834279|-0.0101815314|0.035656401|
|2026 Monitor|966|-0.0016112447|-0.035199131|0.0275775083|
|Recent Combined|6355|0.0065832099|-0.00658113699|0.0198772821|
|ALL|15837|0.0051624133|-0.00308364729|0.0131311943|

## Simultaneous batches and strategy diagnostics

|OtherSimultaneous|Trades|AvgR|TotalR|PF|
|---|---|---|---|---|
|0|12023|0.0794097866|954.743864|1.37906681|
|1|1554|0.132807808|206.383333|1.48653703|
|2|216|0.087534465|18.9074444|1.57119217|
|>=3|2044|0.0881696293|180.218722|1.48618964|

3,814 trades have at least one simultaneous other signal. Batches are descriptive only; no concurrent-only rule is selected.

|StrategyNo|Trades|MeanCount|Distinct|RawSlope|QAdjustedSlope|Eligible|
|---|---|---|---|---|---|---|
|1|852|2.80633803|8|0.00737895615|0.00767147536|True|
|2|1029|1.51797862|5|-0.0131475556|-0.00899066499|True|
|3|1029|2.60932945|5|-0.0292834293|-0.0280796191|True|
|4|956|2.05648536|7|-0.00208390787|-0.00135061627|True|
|5|1252|0.27715655|2|-0.0596604377|-0.0627011943|False|
|6|491|3.38900204|8|0.0541587792|0.0556592397|True|
|7|589|1.72156197|3|0.0876071455|0.0867747238|True|
|8|590|0|1|—|—|False|
|9|340|0|1|—|—|False|
|10|403|2.33995037|6|0.00233520336|0.00204263584|True|
|11|403|0|1|—|—|False|
|12|546|0.580586081|2|0.162638312|0.168033689|False|
|13|223|0.412556054|2|0.090867207|0.0919127884|False|
|14|73|0.890410959|4|0.0137629131|0.0158800903|True|
|15|70|1.15714286|4|0.194700442|0.165796088|True|
|16|60|1.3|4|-0.0467817712|-0.0442217635|True|
|17|351|0.772079772|2|-0.136829665|-0.128119106|False|
|18|953|1.12591815|3|0.00888956567|0.0125164157|True|
|19|703|0.987197724|4|0.0121124252|0.0112730647|True|
|20|770|3.25974026|7|0.025455363|0.0259119608|True|
|21|587|2.879046|6|-0.0339902614|-0.0336582036|True|
|23|434|0.933179724|3|0.0626622838|0.0634462724|True|
|24|434|1.94470046|3|0.0718918811|0.0681472609|True|
|25|1022|3.02935421|6|0.0155057778|0.0159993039|True|
|26|514|4.18287938|4|0.0135697792|0.0121169198|True|
|27|583|4.06861063|4|-0.0225904375|-0.0251856228|True|
|28|580|4.07586207|4|-0.0342243086|-0.0333130084|True|

All 27 strategies are retained. Eligibility for the equal-weight mean requires >=30 trades, >=20 occupied weeks and >=3 distinct counts. Strategy slopes and symbol tables are exploratory diagnostics; no strategy/symbol-specific rule is adopted. Full per-period strategy slopes and distribution tables are in CSVs.

## Leave-one-strategy-out

All 27 omission fits retain a positive beta. Range: **0.007936747545 to 0.016778383378**. Features remain the original full-portfolio counts; only model observations are omitted, as preregistered.

|OmittedStrategy|Beta|Sign|DeltaVsFull|
|---|---|---|---|
|1|0.0140268761|1|0.00103973542|
|2|0.0135890536|1|0.000601912891|
|3|0.0139441188|1|0.000956978117|
|4|0.0167783834|1|0.00379124265|
|5|0.0140035652|1|0.00101642452|
|6|0.00793674754|1|-0.00505039318|
|7|0.0120653743|1|-0.000921766442|
|8|0.0129645581|1|-2.2582591e-05|
|9|0.0129635414|1|-2.35993663e-05|
|10|0.0136359285|1|0.000648787814|
|11|0.0130088305|1|2.16897389e-05|
|12|0.0117986542|1|-0.00118848649|
|13|0.0127757718|1|-0.000211368903|
|14|0.012978891|1|-8.24971564e-06|
|15|0.0121194873|1|-0.000867653385|
|16|0.0132946587|1|0.000307517976|
|17|0.0135297127|1|0.000542571947|
|18|0.0130093903|1|2.22495591e-05|
|19|0.0130602343|1|7.30936023e-05|
|20|0.0111396192|1|-0.00184752154|
|21|0.0133691867|1|0.000382046022|
|23|0.0128836102|1|-0.00010353053|
|24|0.0128641311|1|-0.000123009611|
|25|0.0124498128|1|-0.000537327941|
|26|0.0129877554|1|6.14659244e-07|
|27|0.0137633617|1|0.000776220933|
|28|0.0139633857|1|0.000976244974|

## Formal A–H and decision

|Gate|Pass|Verdict|
|---|---|---|
|A|True|NOT_SUPPORTED|
|B|False|NOT_SUPPORTED|
|C|True|NOT_SUPPORTED|
|D|True|NOT_SUPPORTED|
|E|True|NOT_SUPPORTED|
|F|True|NOT_SUPPORTED|
|G|True|NOT_SUPPORTED|
|H|True|NOT_SUPPORTED|

A raw/adjusted sign agreement; B ALL 6h CI strictly excludes zero; C strategy-equal-weight sign; D Historical/Recent Combined sign; E eligible recent subperiod signs; F 12h sign; G sample/variation/estimability; H every LOSO sign. **Only B fails.** Formal support is therefore NOT_SUPPORTED, with Phase2Eligible=False.

## Verification and publication

Synthetic tests: 5/5 suites passed (inclusive boundaries, ties, self/Strategy22 exclusion, duplicate identity, midnight/weekend, additive FE/unavailable category, identifiability/equal-weight eligibility and row-refit bootstrap equivalence). Independent checks: **88/88 PASS**. Every 6h/12h/simultaneous count was independently recounted. Additive coefficients, raw and equal-weight slopes, all period and 27 LOSO fits agree with separate direct least-squares calculations. Bootstrap verification checked saved CI percentiles and **144 direct row-weighted refits** (first 32 ALL replicates per feature plus first 8 of each other period). Representative low/medium/high, simultaneous and multi-symbol window identities were checked.

Files: `docs/99_c6_portfolio_signal_crowding_phase1_plan.md`; this Result; `src/research/c6_signal_crowding_phase1.py`; `tests/test_c6_signal_crowding_phase1.py`; `tests/verify_c6_signal_crowding_phase1.py`; `notebooks/c6_signal_crowding_phase1.ipynb`; CSVs under `results/c6_signal_crowding_phase1/`. Publication manifest records bytes/SHA-256 for published summaries and local-only trade assignments/bootstrap draws. Notebook contains saved validated snapshots and reproducible Colab cells, outputs `/content`, Drive save OFF.

No Entry Skip, risk adjustment, SL/TP/Time Exit change, money simulation or Phase 2 was performed. Dell Volatility Phase 5 remains Global R2 only. EA / SET / RunId / VPS / Demo / live / Global R2 risk table are unchanged. Previous C1/C2/C3/C4 artifacts remain unchanged.
