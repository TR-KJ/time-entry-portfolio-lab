import copy
import unittest
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src/research'))
from b6.stage9_input import (IDENTITY, AJ, GBP, SCOPE, OUTSIDE, EXPECTED,
    read_json, digest, validate_source, validate_families, audit_archive)


def fixture():
    audit = read_json((ROOT/'results/b6/stage9_freeze/stage8_input_audit.json').read_bytes())
    pool = read_json((ROOT/'research_inputs/b6/stage8_candidate_pool.json').read_bytes())
    evidence = read_json((ROOT/'results/b6/stage9_freeze/stage8_formal_evidence.json').read_bytes())
    return audit['Identity'], audit['Summary'], pool, evidence['CandidatePeriodRows'], evidence['PairRowIdentities']


class InputTests(unittest.TestCase):
    def test_saved_formal_evidence_passes_all_gates(self):
        validate_source(*fixture())

    def reject_identity(self, key, value):
        f = fixture(); f[0][key] = value
        with self.assertRaises(ValueError): validate_source(*f)

    def test_wrong_stage8_code(self): self.reject_identity('code_sha', '0'*40)
    def test_wrong_config_hash(self): self.reject_identity('config_sha256', '0'*64)
    def test_wrong_pool_hash(self): self.reject_identity('candidate_pool_sha256', '0'*64)
    def test_wrong_eligibility_hash(self): self.reject_identity('eligibility_sha256', '0'*64)
    def test_wrong_identity_count(self): self.reject_identity('candidate_count', 8)
    def test_wrong_identity_order(self): self.reject_identity('candidate_ids', list(reversed(fixture()[0]['candidate_ids'])))

    def reject_summary(self, key, value):
        f = fixture(); f[1][key] = value
        with self.assertRaises(ValueError): validate_source(*f)

    def test_incomplete_source(self): self.reject_summary('State', 'RUNNING_STAGE8')
    def test_wrong_nine_count(self): self.reject_summary('DeploymentEligible', 8)
    def test_wrong_pairwise_count(self): self.reject_summary('PairwiseRows', 143)
    def test_wrong_candidate_period_count(self): self.reject_summary('CandidatePeriodRows', 35)
    def test_source_already_consolidated(self): self.reject_summary('FamilyConsolidationExecuted', True)
    def test_source_portfolio_executed(self): self.reject_summary('PortfolioExecuted', True)
    def test_source_live_changed(self): self.reject_summary('LiveChanged', True)
    def test_bool_is_not_integer_count(self): self.reject_summary('EligibleAUDJPY', True)

    def test_every_remaining_summary_gate(self):
        for key, value in EXPECTED.items():
            with self.subTest(key=key):
                self.reject_summary(key, not value if type(value) is bool else (value+1 if type(value) is int else 'wrong'))

    def test_duplicate_candidate_rejected(self):
        f = fixture(); f[2]['Candidates'][-1] = copy.deepcopy(f[2]['Candidates'][0])
        with self.assertRaises(ValueError): validate_source(*f)

    def test_duplicate_metric_row_rejected(self):
        f = fixture(); f[3][-1] = copy.deepcopy(f[3][0])
        with self.assertRaises(ValueError): validate_source(*f)

    def test_missing_metric_row_rejected(self):
        f = fixture(); f[3].pop()
        with self.assertRaises(ValueError): validate_source(*f)

    def test_duplicate_pair_row_rejected(self):
        f = fixture(); f[4][-1] = copy.deepcopy(f[4][0])
        with self.assertRaises(ValueError): validate_source(*f)

    def test_missing_pair_row_rejected(self):
        f = fixture(); f[4].pop()
        with self.assertRaises(ValueError): validate_source(*f)

    def test_family_and_scope_exact(self):
        p = fixture()[2]
        scope = validate_families(p)
        self.assertEqual([c['CandidateID'] for c in scope], list(SCOPE))
        self.assertEqual(len(GBP), 8)
        self.assertEqual([c['CandidateID'] for c in p['Candidates'] if c['Symbol']=='AUDJPY'], [AJ])
        self.assertEqual(set(GBP)-set(SCOPE), set(OUTSIDE))

    def test_wrong_aj_id_rejected(self):
        p = fixture()[2]; p['Candidates'][7]['CandidateID'] = 'B6-AUDJPY-L-W0-E0425-H1315'
        with self.assertRaises(ValueError): validate_families(p)

    def test_wrong_gbp_id_rejected(self):
        p = fixture()[2]; p['Candidates'][0]['CandidateID'] = 'unknown'
        with self.assertRaises(ValueError): validate_families(p)

    def test_scope_uses_actual_entry_not_id(self):
        p = fixture()[2]; p['Candidates'][0]['FinalEntryJST'] = '14:00'
        with self.assertRaises(ValueError): validate_families(p)

    def test_outside_conditions_locked(self):
        for idx, key, val in [(2,'FinalEntryJST','13:00'), (3,'FinalEntryJST','13:59'), (3,'SL',30)]:
            p = fixture()[2]; p['Candidates'][idx][key] = val
            with self.subTest(key=key, idx=idx), self.assertRaises(ValueError): validate_families(p)

    def test_research_status_unchanged(self):
        for key, value in [('FormalValidationStatus','FAIL'), ('MonitorState','PASS'), ('DeploymentReviewEligibility','INELIGIBLE')]:
            p = fixture()[2]; p['Candidates'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): validate_families(p)

    def test_missing_archive_stops(self):
        with self.assertRaises(ValueError): audit_archive(ROOT/'no-such-stage8-archive')

    def test_all_formal_hashes_and_source_evidence_bound(self):
        a = read_json((ROOT/'results/b6/stage9_freeze/stage8_input_audit.json').read_bytes())
        s = read_json((ROOT/'research_inputs/b6/stage9_source_spec.json').read_bytes())
        e = read_json((ROOT/'results/b6/stage9_freeze/stage8_formal_evidence.json').read_bytes())
        self.assertEqual(a['FileSHA256'], s['FileSHA256'])
        self.assertEqual(len(s['FileSHA256']), 45)
        self.assertEqual(e['SourceSHA256'], s['FileSHA256'][e['SourceFile']])
        self.assertFalse(s['ReviewZIPScientificSource'])
        self.assertEqual(sum(n.startswith('matrix_') for n in s['FileSHA256']),20)
        self.assertEqual(sum(n.startswith('shards/') for n in s['FileSHA256']),9)
        for k in ('M1Read','ReplayExecuted','CandidateTradeRecomputed','CorrelationRecomputed'):
            self.assertFalse(a[k])
