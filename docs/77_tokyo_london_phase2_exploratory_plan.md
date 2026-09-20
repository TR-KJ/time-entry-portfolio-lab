# Tokyo → London Phase 2 Exploratory — 事前登録Plan
Date: 2026-09-20. Status: Phase 2 assignment/result未計算・未閲覧、実装前。
Branch: research/tokyo-london-market-effect-phase2-exploratory
Base / Phase1 Result SHA: 40183638fe476a1776f6b55bbe69683e7ff558ab
Phase1 Plan SHA: 9a51295b5e5868bb2f7ba909206a8fc0588dafdb
文書番号77 Plan / 78 Result。本Planのみcommit/pushしremote SHA一致後に実装。実装commit/push・remote確認後に実データを計算。

## 研究位置付け・選択の開示
ユーザーがPhase1結果を見た後、UJ・EAを主探索対象、GJを近年の方向転換仮説として選定。
Phase1の6pair NOT_SUPPORTEDを一切変更しない。95%CIを緩めて通過と読み替えない。
「Phase1 SUPPORTEDだけPhase2へ」という元の進行方針を、今回のユーザー指示で探索研究に限り変更した。
Phase1結果に基づくpair/方向/期間選択であり、以下のHolm3検定はこの選択バイアスや過去の全研究を補正しない。
今回の結果は確証的支持・未閲覧OOS・戦略の利益証明ではない。Phase1と同じ履歴の追加利用。
Phase2正式条件PENDINGは本Planのremote固定時に、この探索研究に限り下記条件へ確定する。
従来の確証的なPhase2が成功したとは主張しない。

## 対象・方向・期間
固定順 USDJPY / EURAUD / GBPJPY。AJ/EJ/GAは追加計算しない。
USDJPY: Continuation、主評価ALL（2015-01-01〜2026-09-09のrank評価可能日）。
EURAUD: Reversal、主評価ALL。
GBPJPY: Continuation、主評価RecentCombined（2022-01-01〜2026-09-09）。
GJの2022境界はPhase1で既使用の区切りを採用。変化点を推定・探索しない。
GJ HistoricalはContinuation向きに揃えた対照診断、ALLも参考。HistoricalをReversalへ切り替えて有利な方向を採らない。
「方向転換」は仮説名であり、今回のQ比較のみで構造変化が統計的に証明されたとは言わない。
全pair/methodについてHistorical 2015–2021、RecentA 2022–2023、RecentB 2024–2025、
Monitor2026 2026-01-01〜09-09、RecentCombined 2022〜2026-09-09、ALLを表示。
期間はinclusive。2022〜2026はpristine unseen holdoutではない。

## 入力・保護
Phase1 source manifest（上記Result SHA）中の3pair×8=24本を新規manifestへ凍結コピーする。
全24 source SHA256/行数/始終時刻、重複UTC、不正OHLCをPhase1 loaderで再監査。
Phase1日次CSVの固定SHA256:
d6a243fa93e4ca19af68caeee84e034acb8dc2382a1c15b510c61ce5ff1f1236（36,600行）。
このCSVを読み取り専用で利用し、3pairの再抽出endpointと突合。
Phase1ソースsrc/research/tokyo_london_phase1.pyも固定Git blob
f22231172df6e8c3ad90c46a34bc5fdf6675c9d0と一致を要求。
Phase1 raw loader/時刻仕様/価格/coverageを再利用し、変更しない。
main / Volatility Phase5 / EA / SET / VPS / live / 既存研究ファイル・結果・branchは変更なし。
新規branch、新規Phase2ソース・テスト・Notebook・結果だけ追加。
Entry/Exit、SL/TP、Risk、閾値pips探索、volatility等feature、Money Simulation、Portfolio追加は実施しない。

## X/Yと時刻
Primary X: JST09:00 M1 Open→JST15:00 M1 Open。
Robustness X: JST09:00 M1 Open→London08:00 M1 Open。
Y: London08:00→11:00 M1 Open。
MT5 Europe/Helsinki→UTC→Asia/Tokyo/Europe/London。DSTはIANA。
exact endpointのみ。JPY pip=.01、EA=.0001。欠損補間・fallbackなし。
月〜金、pair×method×date一意。PrimaryとRobustnessのvalid集合はそれぞれ独立。
元の欠損日は欠損のまま保持する。

## 252 valid-day rank / Q assignment（今回初計算）
pair×methodごとに時系列順のPhase1 Valid=true日を使用。
valid dayとは当該methodの必要endpointが全て揃った日（Y endpointも含む）。過去参照日ではLondon終了済み。
各valid日iでM_i=abs(X_i)。参照は自身を含めない直前252 valid days M[i-252:i]。
期間境界でhistoryをresetしない。GJ RecentCombinedにも2021以前の参照を許可。
2015以前のデータを追加しない。最初252 valid日はINSUFFICIENT_RANK_HISTORYとして除外しcoverageに残す。
percentile=(count(ref<M_i)+.5*count(ref==M_i))/252。
実装比較はfloat64、恣意的丸めなし。等値・境界をunit testする。
integer numerator=2*less+equal (0..504)とし Q=min(5, floor(numerator*5/504)+1)。
すなわちQ1 [0,.2), Q2 [.2,.4), Q3 [.4,.6), Q4 [.6,.8), Q5 [.8,1]。
浮動の境界ずれを避ける。固定分布のquintileではなく過去分布からの分類で、各Q件数は等しくなくてよい。
X==0は参照252日に含め、percentile/Qも記録するがAlignedの方向がないので解析から除外（TOKYO_NEUTRAL）。
Y==0はAligned=0として含める。将来の値動き・rank結果による日付除外なし。
列: ReferenceStart/End、ReferenceN、LessCount/EqualCount、Percentile、Q、Eligible、ExclusionReasonを保存。
当日のMはTokyo終了までで既知。過去参照日は当日より前で、Primary/Robustnessの参照に未来データなし。

## AlignedLondonReturnの一意定義
USDJPY/GBPJPY: A_i=sign(X_i)*Y_i（Continuationに整合した動きが正）。
EURAUD: A_i=-sign(X_i)*Y_i（Reversalに整合した動きが正）。
単にYの符号をpair単位で反転するのでなく、各日のTokyo方向にも揃える。
X==0のAはNaN。pips単位、取引PnLではない。spread/commission/slippageは含まない。
Primary/Robustnessはそれぞれ自身のX符号と自身のQを使用。混用しない。

## 統計・主比較・CI
pair×method×period×Q1..Q5にN、観測週数、A mean/median/sample std、A>0/<0/==0率を表示。
主効果Delta=mean(A|Q5)-mean(A|Q1)。
pair×method×periodの分析可能条件:
総解析日>=80、総観測calendar weeks>=20、Q1とQ5それぞれ>=30日かつ>=10観測週。
不足はINSUFFICIENT_SAMPLE、統計は記述表示するが支持判定に使用しない。
calendar-week cluster bootstrap B=5000, seed=20260913, numpy default_rng。
期間開始を含む月曜から終了を含む月曜までの全暦週（空週込み）Kを用い、毎反復K週を復元抽出。
同じ期間では全pair/methodで同じ抽出重み。期間ごとにseedをreset。Q割当は固定し、bootstrap中にrankを再学習しない。
これは観測済みQ割当に条件付けた不確実性で、252日rank推定や長期依存の不確実性を完全には含まない。
Q1/Q5の片方0件の反復はDelta無効。>=4750有効反復を要求、未満BOOTSTRAP_INSUFFICIENT。
Deltaと各Q meanにpercentile 95%CI（2.5/97.5%, linear）。Q meanはそのQ非空>=4750反復時のみ。
DeltaのH0=0に対する両側中心化bootstrap p=(1+count(abs(Delta*-Delta)>=abs(Delta)))/(1+Bvalid)。
片側へ事後変更しない。CIとp値の双対性は仮定しない。
正式な探索主比較はUJ ALL Primary、EA ALL Primary、GJ RecentCombined Primaryの3個のみ。
この3pにHolm alpha=.05。昇順tie固定pair順、p_adj(i)=min(1,max_{j<=i}((3-j+1)*p(j)))。
不足pは補正用1、元pはNaN。全pairを報告し結果後に検定familyから外さない。
他期間/RobustnessのCI/pは補助、別の正式支持主張をしない。

## 探索判定（結果前固定）
各pairについて:
A: 主比較が分析可能で、Delta>0かつDeltaの95%CI lower>0。
B: 主比較Holm adjusted p<=.05。
C: 主評価periodのQ5 Aligned mean>0（「Q1より損失が小さいだけ」の候補を避ける。CI下限>0は要求しない）。
D: 直近安定性。UJ/EAはPrimary RecentCombinedが分析可能かつDelta>0。
   GJはPrimary RecentB（2024–2025）が分析可能かつDelta>0。
   GJの主評価内の一部期間確認であり独立replicationとは呼ばない。2026だけの改善を通過理由にしない。
E: Robustnessの主評価periodが分析可能かつDelta>0。
A〜E全PASS: EXPLORATORY_SUPPORTED（後続の別Planを検討できる探索候補、戦略採用ではない）。
主比較・D・Eは全て分析可能、主Delta>0、C/D/E PASS、ただしAまたはB不通過:
EXPLORATORY_WATCHLIST（方向は揃うが不確実性が大きい。正式支持・自動Phase3進行にはしない）。
必要sample/CI算出条件不足: INSUFFICIENT_SAMPLE（理由を別列）。
その他: NOT_SUPPORTED。
継続観察の区別が今回残す「遊び」。結果後の80/90%CI採用やgate変更はしない。

## 補助形状とUP/DOWN
Q meanが5群全て有限ならQ番号と5群meanのSpearman（tie average rank）を表示。p値は算出しない。
Q2-Q1、Q3-Q2、Q4-Q3、Q5-Q4の差と正の隣接差数、Q4/Q5 meanを表示。単調性はgateにしない。
UP/DOWN非対称性は各pair×method×period×TokyoSign×QのN/mean/median、
side別Q5-Q1の点推定のみ（CI/p/正式検定なし）。sample閾値未満はLOW_SAMPLEと明記。
上昇だけ/下落だけ採用、方向反転、期間変更、Q境界変更は今回しない。
GJはHistoricalとRecentの同じContinuation向きのQ形状を並記する。変化点/構造変化検定は実施しない。
Family平均・3pairのraw pips poolingは行わない。

## Validation / artifacts
既存24 raw hashes、Phase1 assignment hash、固定ソースblob、再抽出X/Y/exact endpoint照合。
timezone/DST・pip・pair uniqueness・future-referenceなし・first252除外・history期間跨ぎ・同値midrank・0/1境界・Q分類・X0/Y0・Aligned符号。
独立Decimal/manual rank spot audit: 3pair×method×Q=30例、各stratumで初eligible日を選び、
過去252日から別ルートcount/rank/Q/Alignedを再計算。加えて2022境界最初日を各pair×methodで確認。
全Q集計/Delta/coverage/方向診断/gatesを独立math.fsum/csvルートで再構築。
bootstrapは各cell最初3反復を実日次行複製で照合、UJ ALL Primary全5000反復CI/p spot-check。
Holm独立loop、synthetic dataでsupported/watchlist/fail/不足分岐。
Phase2入力はread-only。必要な新規ファイル以外を変更しないことをremote treeで検証。
src/research/tokyo_london_phase2.py、tests/test_tokyo_london_phase2.py、tests/verify_tokyo_london_phase2.py、
research_inputs/tokyo_london_phase2_expected_manifest.csv、notebooks/tokyo_london_phase2.ipynb、
docs/77_tokyo_london_phase2_exploratory_plan.md、docs/78_tokyo_london_phase2_exploratory_result.md。
results/tokyo_london_phase2/配下prefix tokyo_london_phase2_:
pair_summary, quintile_summary, period_summary, shape_summary, direction_summary,
coverage, multiple_comparison, input_audit, manual_audit, validation, run_record, publication_manifest。
daily_assignmentはlocal/Colabのみ。GitHubへhash/rowsを公開。
Notebookは3pair主比較/CI/Holm/gates/verdict、Q形状、期間/robustness、UP/DOWN、coverageを表示。
CSV /content保存、Drive save default OFF。実データがない場合はNOT_RUN_INPUT_MISSING、数値捏造なし。
Plan/Implementation/Result SHAを最終報告しremote確認。Phase1正式判定不変、live等無変更を明記。
