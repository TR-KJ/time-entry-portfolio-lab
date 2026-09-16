# Phase 5 — 受入チェックリスト

基準は docs/63 / Plan SHA 9930d2f7fdf903fd60a85ba286592a0cf72a0412 を変更せず適用する。
現在は未開始。以下の未確認欄をPASSで埋めない。

|項目|確認と証拠|開始前状態|
|---|---|---|
|A|同じDell M1から独立再計算したdaily/ATR20/n/percentile/Q/as-ofの一致|PENDING|
|B|固定Q別Risk、fallback=.90、すべての実sizingへの一貫した適用|PENDING|
|C|当該request時点のbase/SL/tick値、丸め/cap/min stopの一致|PENDING|
|D|実Entry〜Exitの注文/deal/history照合、重複・誤magic・意図しないskipなし|PENDING|
|E|週内base再利用、新週最初のsizingによるEquity保存、Monday00週キー|PENDING|
|F|DEMO/allowlist、専用EA/SET、22停止、27有効、VPS変更なし|PENDING|
|G|全candidateとattempt/lifecycle、fallback/stopをログで追跡可能|PENDING|

14日以上、valid featureの重複除外候補10件以上、自然な2Q以上・2通貨以上、実Entry/Exit1組以上、週跨ぎ1回以上と週内再利用が必要。
最初の10件を時刻順に監査表へ表示するが、判定期間内の全candidate/attemptも監査する。
事前にcutoffを固定し、漏れた候補は戦略schedule/稼働ログとの照合で検出する。記録された行だけのチェックではskip不存在を証明しない。
候補がない・Qが偏る・履歴不足等は自然観測を継続。Mock/TestTimesで自然観測件数を作らない。

Python numeric auditor:
`python src/research/volatility_phase5_audit.py --experts <raw Experts log> --evidence <snapshot directory> --out <new audit directory>`
NUMERIC_MATCHはA/B/Cの部分的証拠であり、Phase5 PASSではない。MissingEvidenceはPENDING。
ログのSourceCommit/BinarySHA256/SETSHA256/AccountAliasは同じRunIdの固定start manifestとjoinする。自分自身のbinary hashをEAにハードコードしない。
CSVはevent形式。CANDIDATE/FEATURE/HISTORYはAttemptId=0、SIZING/ORDERは連番。exit/dealは発注元候補に紐付ける。
旧TradeResultログも同時保存し、order/deal/position、symbol/magic、時刻と照合する。遅延reconciliationのpending/timeout詳細は旧ログに保持される。

各A–Gにstatus、証拠path/hash、確認者、確認JSTを記入する。
利益/PF/DDは別の参考欄に保存できるが、採否入力にしない。
判定優先順位: 確認済み不一致→DEMO_FORWARD_FAIL。全条件と最低観測条件を満たす→DEMO_FORWARD_PASS。それ以外→INSUFFICIENT_OBSERVATIONS。
不具合修正後は別runを開始して旧失敗を保持する。Planの基準変更で救済しない。
再起動検証は対象外であり、Eの未達理由にしない。VPS導入前に別途実施する。
