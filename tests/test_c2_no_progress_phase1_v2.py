import unittest

from test_c2_no_progress_phase1 import fixture, replay
from c2_no_progress_phase1 import paired_summary
from c2_no_progress_phase1_v2 import no_progress, sensitivity_pairs, KEEP_BASELINE


class C2AmendmentTests(unittest.TestCase):
    def test_missing_execution_copies_entire_baseline_both_variants(self):
        for v,start in [('NP50',10),('NP75',15)]:
            a,d=fixture(duration=20)
            d=d.drop(d.index[start:start+5])
            b=replay(a,d,'R0'); c=no_progress(a,d,b,v)
            self.assertEqual(c['Status'],'OK')
            self.assertEqual(c['Assessment'],KEEP_BASELINE)
            self.assertFalse(c['Triggered'])
            for k in ('CloseTime','ClosePrice','ExitReason','Pips','R','ExitDelayMinutes'):
                self.assertEqual(c[k],b[k])
            summary=paired_summary([(a,b,c)])
            self.assertEqual(summary['Trades'],1)
            self.assertEqual(summary['TriggerCount'],0)
            self.assertEqual(summary['DeltaTotalR'],0)
            self.assertEqual(summary['Unchanged'],1)

    def test_valid_checkpoint_and_boundary_unchanged(self):
        a,d=fixture(); b=replay(a,d,'R0')
        self.assertTrue(no_progress(a,d,b,'NP50')['Triggered'])
        d.loc[d.index[1],'High']=100.255
        b=replay(a,d,'R0')
        self.assertEqual(no_progress(a,d,b,'NP50')['Assessment'],'PROGRESS_REACHED')

    def test_sensitivity_removes_pairs_without_mutation(self):
        a,d=fixture(); b=replay(a,d,'R0'); c=no_progress(a,d,b,'NP50')
        second=dict(a,_n=2)
        pairs=[(a,b,c),(second,b,c)]
        kept=sensitivity_pairs(pairs,{(a['_n'],a['EntryTime'])})
        self.assertEqual(len(pairs),2)
        self.assertEqual(len(kept),1)
        self.assertEqual(kept[0][0]['_n'],2)
        self.assertIs(kept[0][1],b)
        self.assertIs(kept[0][2],c)


if __name__=='__main__': unittest.main()
