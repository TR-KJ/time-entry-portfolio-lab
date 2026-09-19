"""Generate exact-text frozen MQL component include; never edit trading EA."""
from pathlib import Path
import re,hashlib,json,argparse
ROOT=Path(__file__).resolve().parents[1]
SOURCE='src/EA/time_entry_step9_2_4_trade_result_reconcile_27strategies_vol_r2_demo.mq5'
NAMES='ResetPendingEntryReconciliation EnsurePendingEntryReconciliationArray HasPendingEntryReconciliation FindStrategyIndexByMagicAndSymbol ClearPendingEntryReconciliation StartPendingEntryReconciliation TicketToText TradeDirectionText IsNormalTradeSuccessResult IsPlausibleReconciledVolume IsExpectedPositionDirection IsExpectedDealDirection IsMatchingEntryDeal FindMatchingNewPosition FindMatchingNewDeal ReconcileExecutedEntry ConfirmPendingEntryFromDeal ProcessPendingEntryReconciliations ResetPendingExitReconciliation FindPendingExitByPositionTicket HasPendingExitReconciliation AllocatePendingExitReconciliation IsExactReconciledVolume IsMatchingExitDeal FindMatchingExitDeal ReconcileExecutedExit PrintReconciledExitSuccess StartPendingExitReconciliation ConfirmPendingExitFromDeal ProcessPendingExitReconciliations PrintReconciledEntrySuccess OnTradeTransaction OnTick OnTimer'.split()
def extract(s,name,struct=False):
    pattern=(r'\bstruct '+name+r'\s*\{' if struct else r'\b(?:void|bool|int|long|ulong|double|string|datetime) '+name+r'\([^;]*?\)\s*\{')
    m=re.search(pattern,s);assert m,name
    end=m.end();depth=1
    while depth:
        depth+=(s[end]=='{')-(s[end]=='}');end+=1
    if struct:end+=1
    return s[m.start():end]
def generate():
    s=(ROOT/SOURCE).read_text()
    names=['PendingEntryReconciliation','PendingExitReconciliation']+NAMES
    chunks=[extract(s,n,n.startswith('Pending')) for n in names]
    text='// Generated verbatim from frozen dedicated EA; DO NOT HAND EDIT.\n'+'\n\n'.join(chunks[:2])+'\nPendingEntryReconciliation pending_entry_reconciliations[];\nPendingExitReconciliation pending_exit_reconciliations[];\n'+'\n\n'.join(chunks[2:])+'\n'
    manifest={'Source':SOURCE,'ImplementationSHA':'1a69fbfe104ddd41e031273d9318c480a711969c','SourceSHA256':hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest(),'FunctionCount':len(NAMES),'TextHashes':{n:hashlib.sha256(c.encode()).hexdigest() for n,c in zip(names,chunks)}}
    return text,json.dumps(manifest,indent=2)+'\n'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);v=p.parse_args();v.out.mkdir(parents=True,exist_ok=True)
    text,manifest=generate();(v.out/'reconcile_frozen_functions.mqh').write_text(text);(v.out/'reconcile_source_manifest.json').write_text(manifest)
