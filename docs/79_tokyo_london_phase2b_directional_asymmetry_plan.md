# Tokyo → London Phase 2b Directional Asymmetry Exploratory — 事前登録Plan
状態: Phase 2bの方向別結果を計算・閲覧する前、実装前。2026-09-22 JST。
Branch: research/tokyo-london-phase2b-directional-asymmetry
Base / Phase2 Result SHA: 046be86bffebd28dbd21a11e49fb9eb2e1d507ac
Phase1 Result SHA: 40183638fe476a1776f6b55bbe69683e7ff558ab
新規docs/79 Plan、docs/80 Result。Planのみcommit/push→remote SHA一致確認→実装→実装commit/push→remote SHA一致確認→実データ本計算。

## 位置づけと対象
Phase1の6通貨NOT_SUPPORTED、探索的Phase2のEA/UJ EXPLORATORY_WATCHLIST、GJ NOT_SUPPORTEDを変更しない。
Phase2の方向診断は既に算出・閲覧済み。本研究の対象・仮説・RecentCombined主期間はその結果を受けて選ばれた。
したがって本研究は一度限りの探索であり、独立holdout・確証的検証ではない。
Main=EURAUD(EA), Reversal。Shadow=USDJPY(UJ), Continuation。GJは対象外。
UP/DOWN両方向を同時に全表へ含め、結果後の片側だけの正式採用は禁止。
EAに下記DIRECTIONAL_STRUCTURE_PRESENTがなければTokyo→London研究はいったん終了。
EAに構造がある場合のみ人間がPhase3実施を検討する。Phase3を自動開始しない。
UJ単独結果ではこの終了規則を変更しない。

## 入力・再現性
Phase2の日次assignment CSV固定SHA256 ab12358882adf6a165983710599f4524ce2b37f1409a9f9a04ad967cefdbc21d、18,300行。
Phase2実装src/research/tokyo_london_phase2.py Git blob
9c6f640dff2151f4f03711e0a224c86b47f4a73f、Phase1 loader Git blob
f22231172df6e8c3ad90c46a34bc5fdf6675c9d0。
Phase2既存manifest（blob db064ac3abb9645d7ff7c57e864777204b948e6a）のEA/UJ×8=16本を新規manifestに凍結コピー。
16 source SHA256/行数/raw始終、OHLC、UTC重複を再監査し、Phase2 Q/percentile/Aligned/endpointと照合。
入力はread-only。既存研究成果物・Phase1/Phase2 branch・main/Volatility Phase5/EA/SET/VPS/liveに変更なし。
source不在/hash不一致は中止し、値を捏造しない。

## 不変の時刻・rank・Aligned定義
Primary X=JST09:00 Open→JST15:00 Open。
Robustness X=JST09:00 Open→London08:00 Open。
Y=London08:00→11:00 Open。MT5 Europe/Helsinki→UTC、JST/Londonは同一UTCからIANA時刻変換。
exact M1 Openのみ、補間/fallbackなし。JPY pip=.01、EA pip=.0001。
各pair×methodの直前252 valid trading daysのabs(X)でmidrank percentile。
整数numerator=2*less+equal、Q=min(5,floor(numerator*5/504)+1)、Q5は80–100%。
参照は当日を含まず、期間境界でもresetしない。Q4+Q5や90%ile等へ変更しない。
EA AlignedLondonReturn=−sign(X)×Y。UJ=sign(X)×Y。
各methodは自分のX/Q/Alignedを使用。Tokyo X==0はrank履歴に含めるがAligned解析除外、Y==0は0。
既存Phase2日次assignmentをそのまま使用し、再分類で過去の結果を書き換えない。

## Primary family・期間
Primary期間RecentCombined=2022-01-01〜2026-09-09 inclusive。
固定4セル順: EA Q5 Tokyo UP、EA Q5 Tokyo DOWN、UJ Q5 Tokyo UP、UJ Q5 Tokyo DOWN。
各セルのN、観測calendar weeks、AlignedLondonReturn mean/median/sample std(ddof=1)、
positive/negative/zero rate、Total aligned pips=sum(AlignedLondonReturn)を表示。
Total aligned pipsは単純価格差の和で取引損益・実行可能収益ではない。
補助期間Historical 2015–2021、ALL 2015–2026-09-09、
RecentA 2022–2023、RecentB 2024–2025、Monitor2026 2026-01-01〜09-09。
各periodとPrimary/RobustnessでUP/DOWN Q5の同じ指標を表示。
2022〜2026はpristine unseen holdoutではない。

## Sample rule
各pair×method×period×Tokyo方向×Q5でN>=40かつ観測calendar weeks>=20を評価可能条件。
どちらか不足ならINSUFFICIENT_SAMPLE。mean等は記述表示するが正式cell gateには使わない。
bootstrap有効反復<4750はBOOTSTRAP_INSUFFICIENTで同様にgate不可。
pair全体の方向構造判定には主期間PrimaryのUP/DOWN両セルが評価可能であることを要求。
片側不足ならpairはINSUFFICIENT_SAMPLE。数値が良くても昇格なし。
Historical/Monitor2026が不足の場合はその期間をINSUFFICIENT_SAMPLEで表示し、RecentA/Bの下記安定性条件は変えない。

## 週bootstrap、CI、p、Holm
各period開始週〜終了週の月曜開始calendar weeks（空週含む）をcluster。
NumPy default_rng(20260913)、5000回、元週数Kを復元抽出。同じperiodの全pair/method/方向で同一週draw weights。
週内の日をまとめて再標本化し、Q5 assignmentは固定。空cell反復を無効、>=4750有効反復要求。
各cell meanの95% percentile CI=有効反復の2.5/97.5%、linear補間。
H0 mean=0の両側中心化bootstrap p=(1+count(abs(mean*−mean_hat)>=abs(mean_hat)))/(1+Bvalid)。
one-sidedへ事後変更しない。CIとpの双対性を仮定しない。
Primary4セルのpだけHolm alpha=.05。昇順tieは固定4セル順。
adjusted p_(i)=min(1,max_{j<=i}((4−j+1)*p_(j)))。unadjusted/adjusted両保存。
評価不能pは補正用1、元pはNaNのまま。結果後に比較familyからセルを削除しない。
補助period/Robustnessのpは未調整・記述のみ。多重比較により正式支持は主4セルに限定。

## Directional asymmetry difference
pair×method×periodでD=UP Q5 mean−DOWN Q5 mean（固定符号）。
D>0はUP側が強い、D<0はDOWN側が強い。EA/UJ共通。絶対値のみで方向を隠さない。
同じ週cluster drawからUP/DOWNを再計算しDの95% percentile CIを表示。
Dのp値は計算しない。D/CIは方向偏りの説明用で、4セルHolm familyや構造gateへ追加しない。
DのCIが0を跨いでも片側meanが正になり得る点を区別する。
Q5以外、30/50pips等の閾値、時刻、SL/TPを探索しない。

## 結果前固定のcell gate・pair verdict
「実務上無視できない正の値」の探索基準を両pairともQ5 Aligned mean>=2.0 pipsと事前固定する。
2.0は価格変化の大きさに対する研究上の床で、取引コストを反映した利益の証明ではない。
各主Primary Q5方向cellのSTRONG条件:
A) 評価可能かつmean>=2.0 pips。
B) 同cell meanの95%CI lower>0。
C) 同cellのHolm adjusted p<=.05。
D) 同pair・同方向・Primary RecentAとRecentBの両方が評価可能かつmean>0。
E) 同pair・同方向・Robustness RecentCombinedが評価可能かつmean>0。
A〜E全PASSならCELL_STRONG。A,D,E PASSでBかC不通過ならCELL_WEAK。
その他はCELL_NO_STRUCTURE。評価不能主セルはCELL_INSUFFICIENT_SAMPLE。
RecentA/Bの両方を要求するのは1期間突出を避けるため。2026は補助診断でgateに使わない。
Eは同じ方向・同じ主期間。Robustness CI有意は要求しない。

EA overall: 主Primary UP/DOWN両セルが評価可能で少なくとも一つCELL_STRONGなら
DIRECTIONAL_STRUCTURE_PRESENT（1/2方向または2/2方向を明記）。
STRONGなし、いずれかCELL_WEAKならWEAK_DIRECTIONAL_STRUCTURE。
両方CELL_NO_STRUCTUREならNO_DIRECTIONAL_STRUCTURE。
主2セルの片方不足ならINSUFFICIENT_SAMPLE。
EAの構造がPRESENTの場合だけPHASE3_HUMAN_REVIEW_ELIGIBLE。人間の最終判断まで戦略化しない。
EAがPRESENTでなければ研究をいったん終了と記録。

UJ Shadow: 主2セル両方CELL_STRONG、かつEAがDIRECTIONAL_STRUCTURE_PRESENTの場合だけ
SHADOW_STRUCTURE_PRESENT / PHASE3_HUMAN_REVIEW_ELIGIBLE。
これはEA以上に明確な両方向構造を要求するためで、異なるpairのraw pipsを直接比較しない。
それ以外は、主両セル評価可能で少なくとも一つCELL_WEAKまたはCELL_STRONGなら
SHADOW_WEAK_STRUCTURE、双方NOならSHADOW_NO_STRUCTURE、片方不足ならSHADOW_INSUFFICIENT_SAMPLE。
UJ単独でEAがPRESENTでない場合、研究終了方針を覆さずPhase3候補にしない。
セル/ペア判定は探索的で、Phase1/Phase2の正式支持への昇格ではない。
CI・p閾値・material floor・period/方向・ラベルの後付け変更は禁止。

## Verification・成果物
Plan remote SHA確認後にだけコード作成、Implementation remote SHA確認後にだけPhase2b実データ計算。
16 raw hash/row/date・phase2 daily hash・既存source Git blob・全endpoint/Q/Aligned不変・pair×date×method一意を検証。
Synthetic: DST、pip、X/Y符号、Q5境界、X/Y0、欠損・sample/週境界、bootstrap共有週、Holm4/tie/欠損、cell/pair verdict全分岐。
独立math.fsumで全cell N/mean/std/total/rates、UP−DOWN、coverage、Holm/gates再構築。
各period/methodのbootstrap初3反復を実日次行複製、EA Primary RecentCombined全5000反復CI/p/差CIを独立spot-check。
代表audit: 2pair×UP/DOWN×Primary/Robustness×Historical/RecentCombined初評価可能日=16例。
各例raw Open、時刻、Q5、直前252 valid-day参照、Alignedを独立確認。
run record: 3SHA、入力/出力hash、B/seed、テスト、Phase1/Phase2VerdictChanged=false、LiveChanged=false。
新規 src/research/tokyo_london_phase2b.py、tests/test_tokyo_london_phase2b.py、
tests/verify_tokyo_london_phase2b.py、research_inputs/tokyo_london_phase2b_expected_manifest.csv、
notebooks/tokyo_london_phase2b.ipynb、docs/79/80、results/tokyo_london_phase2b/。
CSV prefix tokyo_london_phase2b_: primary_cells, period_cells, asymmetry_summary,
pair_verdict, coverage, multiple_comparison, input_audit, manual_audit, validation,
run_record, publication_manifest。大きな日次入力はlocal/Colabのみ＋publication hash/rows。
Notebookに4主cell、Holm、安定性、Primary/Robustness、UP−DOWN、coverage、最終label。
CSV /content保存、Drive save cell default OFF。既存research/EA/SET/VPS/liveは変更なし。
