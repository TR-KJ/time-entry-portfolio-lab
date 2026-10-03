import copy
import math
import unittest
from test_b6_stage9_input import fixture
from b6.stage9_input import AJ, SCOPE, OUTSIDE, json_bytes
from b6.stage9_selection import (KEYS, PROXY, BOUNDARY, relative_lot_margin_proxy,
    rank_rows, selection_rows, consolidate, family_policy)


class SelectionTests(unittest.TestCase):
    def synthetic(self):
        return [dict(CandidateID=cid, WorstSegmentMaxDDR=10., RelativeLotMarginProxy=1.,
                     FullAvailableMaxDDR=12., ValidationAvgR=.1, FullAvailableTotalR=100.)
                for cid in ('A','B')]

    def key_wins(self, key, better):
        rows = self.synthetic(); rows[1][key] = better
        self.assertEqual(rank_rows(rows)[0]['CandidateID'], 'B')
        self.assertEqual(rank_rows(rows[::-1])[0]['CandidateID'], 'B')

    def test_key1_worst_dd(self): self.key_wins('WorstSegmentMaxDDR', 9.)
    def test_key2_proxy(self): self.key_wins('RelativeLotMarginProxy', 30/35)
    def test_key3_full_dd(self): self.key_wins('FullAvailableMaxDDR', 11.)
    def test_key4_validation_avg(self): self.key_wins('ValidationAvgR', .2)
    def test_key5_full_total(self): self.key_wins('FullAvailableTotalR', 101.)
    def test_key6_candidate_id(self): self.assertEqual(rank_rows(self.synthetic()[::-1])[0]['CandidateID'], 'A')

    def test_earlier_key_dominates_all_later_keys(self):
        for i in range(5):
            rows=self.synthetic()
            for j, k in enumerate(KEYS[:-1]):
                delta=1 if k['Order']=='ASC' else -1
                if j==i: rows[1][k['Field']] -= delta
                if j>i: rows[1][k['Field']] += delta*1000
            with self.subTest(key=i): self.assertEqual(rank_rows(rows)[0]['CandidateID'],'B')

    def test_no_epsilon_or_rounding(self):
        rows=self.synthetic(); rows[1]['WorstSegmentMaxDDR']=math.nextafter(10.,0.)
        self.assertEqual(rank_rows(rows)[0]['CandidateID'],'B')

    def test_sl30_proxy(self): self.assertEqual(relative_lot_margin_proxy('GBPJPY',30),1.)
    def test_sl35_proxy(self): self.assertEqual(relative_lot_margin_proxy('GBPJPY',35),30/35)
    def test_raw_sl_proxy(self): self.assertEqual(relative_lot_margin_proxy('GBPJPY',30.123456789),30/30.123456789)
    def test_proxy_same_symbol_only(self):
        with self.assertRaises(ValueError): relative_lot_margin_proxy('AUDJPY',30)
    def test_proxy_is_not_actual_margin(self):
        self.assertFalse(PROXY['ActualBrokerMargin']); self.assertFalse(PROXY['LotDecided'])
    def test_invalid_sl_rejected(self):
        for sl in (0,-1,float('nan'),float('inf'),True):
            with self.subTest(sl=sl),self.assertRaises(ValueError): relative_lot_margin_proxy('GBPJPY',sl)
    def test_nonfinite_selection_key_rejected(self):
        for key in KEYS[:-1]:
            rows=self.synthetic(); rows[0][key['Field']]=float('nan')
            with self.subTest(key=key),self.assertRaises(ValueError): rank_rows(rows)

    def result(self, metrics=None):
        f=fixture(); return consolidate(f[2],metrics if metrics is not None else f[3])
    def selected(self, metrics): return self.result(metrics)[0][0]['CandidateID']

    def test_pf_changes_do_not_change_selection(self):
        rows=fixture()[3]; before=self.selected(rows)
        for r in rows: r['PF']='999999' if r['CandidateID']==SCOPE[-1] else '0.01'
        self.assertEqual(self.selected(rows),before)
    def test_monitor_total_changes_do_not_change_selection(self):
        rows=fixture()[3]; before=self.selected(rows)
        for r in rows:
            if r['Period']=='Monitor': r['TotalR']='999999'
        self.assertEqual(self.selected(rows),before)
    def test_correlation_changes_do_not_change_selection(self):
        rows=self.result()[0]
        for r in rows: r.update(PearsonR=-999,SpearmanR=999,TradeJaccard=0)
        self.assertEqual([r['CandidateID'] for r in rank_rows(rows)], [r['CandidateID'] for r in self.result()[0]])
    def test_worst_segment_uses_three_segments_not_full(self):
        f=fixture(); cid=SCOPE[0]
        for r in f[3]:
            if r['CandidateID']==cid: r['MaxDDR']={'Discovery':'2','Validation':'3','Monitor':'4','FullAvailable':'99'}[r['Period']]
        row=next(r for r in selection_rows(f[2],f[3]) if r['CandidateID']==cid)
        self.assertEqual(row['WorstSegmentMaxDDR'],4.);self.assertEqual(row['FullAvailableMaxDDR'],99.)
    def test_source_validation_avg_and_full_total(self):
        f=fixture(); rows=selection_rows(f[2],f[3]); by={(r['CandidateID'],r['Period']):r for r in f[3]}
        for row in rows:
            self.assertEqual(row['ValidationAvgR'],float(by[row['CandidateID'],'Validation']['AvgR']))
            self.assertEqual(row['FullAvailableTotalR'],float(by[row['CandidateID'],'FullAvailable']['TotalR']))
    def test_infinite_pf_kept_as_string(self):
        f=fixture()
        for r in f[3]: r['PF']='INF'
        self.assertTrue(all(r['FullAvailablePF']=='INF' for r in selection_rows(f[2],f[3])))
    def test_formal_selection_exact(self):
        rows,_,_=self.result()
        self.assertEqual(rows[0]['CandidateID'],'B6-GBPJPY-L-W0-E0835-H1415')
        self.assertEqual(sum(r['Selected'] for r in rows),1)
        self.assertEqual([r['LexicographicRank'] for r in rows],list(range(1,7)))
        self.assertEqual(rows[0]['WorstSegmentMaxDDR'],11.07333333333348)
        self.assertTrue(all(rows[0]['WorstSegmentMaxDDR']<r['WorstSegmentMaxDDR'] for r in rows[1:]))
    def test_final_exactly_two_in_family_order(self):
        final=self.result()[2]
        self.assertEqual(final['CandidateCount'],2)
        self.assertEqual([p['Symbol'] for p in final['Candidates']],['AUDJPY','GBPJPY'])
        self.assertEqual(final['Candidates'][0]['CandidateID'],AJ)
        self.assertIn(final['Candidates'][1]['CandidateID'],SCOPE)
    def test_all_conditions_exactly_preserved(self):
        source={p['CandidateID']:p for p in fixture()[2]['Candidates']}
        for p in self.result()[2]['Candidates']:
            extra={'Stage8Eligibility','Stage9Family','Stage9Disposition'}
            self.assertEqual({k:v for k,v in p.items() if k not in extra},source[p['CandidateID']])
    def test_aj_never_competes_with_gbp(self):
        rows=fixture()[3]
        for r in rows:
            if r['CandidateID']==AJ: r.update(MaxDDR='999999',AvgR='-999999',TotalR='-999999')
        final=self.result(rows)[2]
        self.assertEqual(final['Candidates'][0]['CandidateID'],AJ)
        self.assertEqual(final['Candidates'][1]['CandidateID'],self.result()[2]['Candidates'][1]['CandidateID'])
    def test_nine_dispositions_preserve_outside_family(self):
        _,disp,_=self.result(); by={d['CandidateID']:d for d in disp}
        self.assertEqual(len(disp),9)
        for cid in OUTSIDE:
            self.assertEqual(by[cid]['Stage9Disposition'],'NOT_IN_REPRESENTATIVE_SELECTION_SCOPE')
            self.assertEqual(by[cid]['Family'],'GBPJPY_FAMILY')
            self.assertFalse(by[cid]['RepresentativeSelectionScope'])
            self.assertEqual(by[cid]['Stage8Eligibility'],'ELIGIBLE')
        self.assertEqual(sum(d['Stage9Disposition']=='NOT_SELECTED_FAMILY_REDUNDANCY' for d in disp),5)
    def test_no_retuning_numbering_or_portfolio(self):
        f=self.result()[2]
        for key in BOUNDARY: self.assertIs(f[key],False,key)
        self.assertFalse(family_policy()['ClusteringExecuted'])
    def test_stable_bytes_and_no_nan(self):
        self.assertEqual(json_bytes(self.result()[2]),json_bytes(self.result()[2]))
        with self.assertRaises(ValueError): json_bytes({'x':float('nan')})
