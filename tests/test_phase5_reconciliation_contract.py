"""Static fixture provenance/safety checks. These do not execute MQL."""
import unittest,json,re,hashlib
from pathlib import Path
import build_phase5_reconciliation_fixture as b
ROOT=Path(__file__).resolve().parents[1]
FIX=ROOT/'src/EA/phase5_regression'
class ReconciliationFixtureContract(unittest.TestCase):
    def test_generated_exact_source(self):
        text,manifest=b.generate()
        self.assertEqual(text,(FIX/'reconcile_frozen_functions.mqh').read_text())
        self.assertEqual(manifest,(FIX/'reconcile_source_manifest.json').read_text())
        self.assertEqual(len(b.NAMES),34)
    def test_trading_source_not_changed(self):
        m=json.loads((ROOT/'results/volatility_phase5/source_manifest.json').read_text())
        for p,h in m['DedicatedFiles'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h,p)
    def test_no_order_or_terminal_mutation_calls(self):
        s='\n'.join(p.read_text() for p in FIX.glob('*.mq*'))
        for name in ['OrderSend','OrderSendAsync','PositionClose','GlobalVariableSet','GlobalVariableDel','EventSetTimer','EventSetMillisecondTimer']:
            self.assertNotRegex(s,r'\b'+name+r'\s*\(')
        self.assertNotRegex(s,r'\btrade\s*\.\s*(Buy|Sell)\s*\(')
        self.assertNotIn('#include <Trade/',s)
    def test_all_terminal_calls_redirected(self):
        generated=(FIX/'reconcile_frozen_functions.mqh').read_text();adapter=(FIX/'reconcile_test_adapters.mqh').read_text()
        apis=set(re.findall(r'\b((?:History|Position|SymbolInfo|TimeTrade|TimeCurrent|GetTickCount)\w*)\s*\(',generated))
        for api in apis:self.assertRegex(adapter,r'#define '+api+r'\s+R\w+')
        for name in ['OnTick','OnTimer','OnTradeTransaction']:self.assertIn('#define '+name+' R'+name,adapter)
    def test_submission_pending_guards_static_only(self):
        s=(ROOT/b.SOURCE).read_text()
        entry=b.extract(s,'TryEntry');close=b.extract(s,'ClosePositionsByConfig')
        self.assertLess(entry.index('HasPendingEntryReconciliation'),entry.index('SendBuyOrder'))
        self.assertLess(close.index('HasPendingExitReconciliation'),close.index('trade.PositionClose'))
    def test_cases_present_and_honest_label(self):
        s=(FIX/'test_phase5_reconciliation.mq5').read_text()
        for label in ['timeout without evidence','delayed entry DEAL_ADD','duplicate deal not marked twice','disabled callback guard','exit timeout still open','history selection preserves candidate iteration','COMPONENT_ONLY=true']:
            self.assertIn(label,s)
if __name__=='__main__':unittest.main(verbosity=2)
