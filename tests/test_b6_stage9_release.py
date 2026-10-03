import ast
import json
import tempfile
import unittest
from unittest.mock import patch
from test_b6_stage9_input import ROOT,fixture
from b6.stage9_input import read_json,json_bytes,digest,audit_archive
from b6.stage9_freeze import build,release_manifest,verify_release,INPUT,OUTPUT
from b6.stage9_selection import consolidate,KEYS


class ReleaseTests(unittest.TestCase):
    def test_release_manifest_and_immutable_dependencies(self):
        lock=read_json((ROOT/INPUT/'stage9_release_manifest.json').read_bytes())
        self.assertEqual(lock,release_manifest())
        old=read_json((ROOT/INPUT/'stage8_release_manifest.json').read_bytes())
        for name,sha in old.items():
            if name not in ('docs/b6/research_plan.md','docs/b6/parameter_decision_register.md'):
                self.assertEqual(digest((ROOT/name).read_bytes()),sha,name)

    def test_regenerated_bytes_equal_saved_artifacts(self):
        spec=read_json((ROOT/INPUT/'stage9_source_spec.json').read_bytes())
        audit=read_json((ROOT/OUTPUT/'stage8_input_audit.json').read_bytes())
        evidence=read_json((ROOT/OUTPUT/'stage8_formal_evidence.json').read_bytes())
        with patch('b6.stage9_freeze.audit_archive',return_value=(spec,audit,fixture()[2],evidence)):
            first=build(audit['FormalRoot'],spec); second=build(audit['FormalRoot'],spec)
        self.assertEqual(first,second)
        for path,data in first.items(): self.assertEqual(data,(ROOT/path).read_bytes(),path)

    def test_archive_hash_mismatch_rejected_before_parsing(self):
        spec=read_json((ROOT/INPUT/'stage9_source_spec.json').read_bytes())
        with tempfile.TemporaryDirectory() as name:
            from pathlib import Path
            root=Path(name)
            for filename in spec['RequiredFiles']:
                path=root/filename;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'exact-byte hash mismatch'): audit_archive(root,spec)

    def test_archive_missing_file_is_not_repaired(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(ValueError,'inventory mismatch'): audit_archive(name)

    def test_config_and_final_identity_chain(self):
        config=read_json((ROOT/INPUT/'stage9_config.json').read_bytes())
        for key,name in [('FinalCandidateSHA256',INPUT+'stage9_final_candidates.json'),
                         ('FamilySHA256',INPUT+'stage9_family_consolidation.json'),
                         ('SourceSpecSHA256',INPUT+'stage9_source_spec.json'),
                         ('SourceAuditSHA256',OUTPUT+'stage8_input_audit.json')]:
            self.assertEqual(config[key],digest((ROOT/name).read_bytes()))
        self.assertEqual(config['Stage10RequiredFinalCandidateSHA256'],config['FinalCandidateSHA256'])
        self.assertEqual(config['SelectionKeys'],KEYS)

    def test_release_guard_rejects_wrong_sha_and_dirty(self):
        with self.assertRaises(ValueError): verify_release('')
        with patch('b6.stage9_freeze.subprocess.check_output',return_value='b'*40):
            with self.assertRaises(ValueError): verify_release('a'*40)
        with patch('b6.stage9_freeze.subprocess.check_output',side_effect=['a'*40,'?? unknown.txt']):
            with self.assertRaisesRegex(ValueError,'clean Stage9'): verify_release('a'*40)

    def test_stage9_has_no_price_or_correlation_engine_import(self):
        allowed={'stage9_input','stage9_selection','stage9_freeze'}
        for path in (ROOT/'src/research/b6').glob('stage9*.py'):
            if path.name=='stage9_test_suite.py': continue
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node,ast.ImportFrom) and node.level:
                    self.assertIn(node.module,allowed)
                if isinstance(node,ast.Import):
                    for alias in node.names: self.assertNotIn(alias.name.split('.')[0],{'pandas','numpy'})

    def test_summary_complete_and_boundary(self):
        s=read_json((ROOT/OUTPUT/'stage9_summary.json').read_bytes())
        self.assertEqual(s['State'],'COMPLETE_STAGE9_FINAL_CANDIDATE_FREEZE')
        self.assertTrue(s['FamilyConsolidationExecuted']);self.assertTrue(s['FinalCandidateFreezeExecuted'])
        self.assertEqual(s['FinalCandidateCount'],2)
        for k in ('PortfolioExecuted','LiveChanged','StrategyNumberingAssigned','ReplayExecuted'):self.assertFalse(s[k])

    def test_serialization_is_utf8_sorted_json_final_lf(self):
        for pattern in ('research_inputs/b6/stage9*.json','results/b6/stage9_freeze/*.json'):
            for path in ROOT.glob(pattern):
                data=path.read_bytes();self.assertEqual(json_bytes(read_json(data)),data,path.name)
        for path in ROOT.glob('results/b6/stage9_freeze/*.csv'):
            self.assertTrue(path.read_bytes().endswith(b'\n'));self.assertNotIn(b'\r',path.read_bytes())
