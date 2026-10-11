"""Structural/identity/mutation tests only; no Validation performance generation."""
from copy import deepcopy
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
from b7 import candidate_freeze as cf
from b7.stage1_contract import object_hash, digest, ROOT, verify_conditions


class CandidateFreeze(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = cf.load_source()
        cls.outputs = cf.build(cls.source)
        cls.u11 = cls.outputs['u11_validation_selected40_input.json']

    def test_source_file_identity(self):
        self.assertEqual(digest(cf.SOURCE), cf.SOURCE_SHA)
        self.assertEqual(cf.SOURCE.stat().st_size, 254958)
        self.assertEqual(object_hash(self.source), cf.SOURCE_OBJECT_SHA)

    def test_unique_ordered40(self):
        d = self.u11
        self.assertEqual(d['CandidateCount'], 40)
        self.assertEqual(len(set(d['CandidateIDs'])), 40)
        self.assertEqual(d['CandidateIDs'], self.source['CandidateIDs'])
        self.assertEqual(d['CandidateIDs'], [r['CandidateID'] for r in d['Candidates']])

    def test_recursive_exact_candidates(self):
        self.assertTrue(cf.exact(self.u11['Candidates'], self.source['Candidates']))
        self.assertIsNot(self.u11['Candidates'], self.source['Candidates'])
        for a, b in zip(self.u11['Candidates'], self.source['Candidates']):
            self.assertEqual(a.keys(), b.keys())
            self.assertTrue(cf.exact(a, b))

    def test_pair_counts_and_no_replacement(self):
        self.assertIs(self.u11['NoReplacement'], True)
        self.assertEqual(self.u11['PairCounts'], cf.PAIRS)
        self.assertEqual(self.u11['PairCounts']['AUDUSD'], 0)
        self.assertEqual({s: sum(r['Symbol'] == s for r in self.u11['Candidates']) for s in cf.PAIRS}, cf.PAIRS)

    def test_protection_exact_mapping(self):
        self.assertEqual(self.u11['ProtectionModeCounts'], dict(P0=37, P1=2, P2=1, P3=0))
        self.assertEqual({r['CandidateID']: r['FormalProtectionMode'] for r in self.u11['Candidates'] if r['FormalProtectionMode'] != 'P0'}, cf.PROTECTION)

    def test_all_terminal_event_calendar(self):
        for r in self.u11['Candidates']:
            self.assertEqual(r['U10PStatus'], 'PASS_U10P')
            self.assertEqual(r['FormalEventMode'], 'E2')
            self.assertEqual(r['EventCalendarSHA256'], cf.CALENDAR_SHA)
            self.assertEqual(r['CalendarSourceCommit'], cf.CALENDAR_COMMIT)

    def test_baseline_and_stream_retained(self):
        for a, b in zip(self.source['Candidates'], self.u11['Candidates']):
            self.assertTrue(cf.exact(a['SelectedModeDiscoveryMetrics'], b['SelectedModeDiscoveryMetrics']))
            self.assertEqual(a['SelectedModeTradeStreamSHA256'], b['SelectedModeTradeStreamSHA256'])
            self.assertRegex(b['SelectedModeTradeStreamSHA256'], r'^[0-9a-f]{64}$')
            self.assertEqual(set(b['SelectedModeDiscoveryMetrics']['Annual']), {'2020','2021','2022','2023'})

    def test_all_provenance_retained(self):
        for a, b in zip(self.source['Candidates'], self.u11['Candidates']):
            for k in cf.PROVENANCE:
                self.assertTrue(cf.exact(a[k], b[k]), k)
            cf.sha_fields(b)

    def test_frozen_u11_contract_exact(self):
        contract = verify_conditions()['U11']
        self.assertTrue(cf.exact(contract, self.u11['FrozenU11Contract']))
        self.assertTrue(cf.exact(contract, self.outputs['u11_contract.json']))
        self.assertEqual(self.u11['ValidationPeriod'], '[2024-01-01, 2026-01-01) JST')
        self.assertFalse(contract['RetentionGateAdded'])
        self.assertFalse(contract['RescuePASSAllowed'])
        self.assertFalse(contract['PostValidationRetuningAllowed'])

    def test_unexecuted_flags_no_status(self):
        for k in ['ValidationPerformanceEvaluated','MonitorPerformanceEvaluated','RescuePASSAllowed','PostValidationRetuningAllowed']:
            self.assertIs(self.u11[k], False)
        self.assertIs(self.u11['CandidateSetImmutable'], True)
        for r in self.u11['Candidates']:
            self.assertFalse(any(k.startswith(('Validation','Monitor')) for k in r))

    def test_historical_snapshot_separate_completion(self):
        self.assertIs(self.source['CandidateFreezeExecuted'], False)
        self.assertEqual(self.outputs['candidate_freeze_identity.json']['Status'], 'COMPLETE_CANDIDATE_FREEZE')

    def test_fingerprints_and_individual40(self):
        identity = self.outputs['candidate_freeze_identity.json'];fp = identity['Fingerprints'];rs = self.source['Candidates']
        self.assertEqual(fp['CandidateSetSHA256'], object_hash(rs))
        self.assertEqual(fp['ProtectionMappingSHA256'], object_hash({r['CandidateID']:r['FormalProtectionMode'] for r in rs}))
        self.assertEqual(fp['DiscoveryBaselineSHA256'], object_hash({r['CandidateID']:r['SelectedModeDiscoveryMetrics'] for r in rs}))
        self.assertEqual(fp['ScheduleMappingSHA256'], object_hash({r['CandidateID']:{k:r[k] for k in cf.FIXED_FIELDS} for r in rs}))
        inv = self.outputs['candidate_inventory.json']['Candidates'];self.assertEqual(len(inv),40)
        for i,r in zip(inv,rs):
            self.assertEqual(i['CandidateObjectSHA256'],object_hash(r))
            self.assertEqual(i['SelectedModeDiscoveryMaxDDPips'],r['SelectedModeDiscoveryMetrics']['MaxDDPips'])

    def test_artifact_hash_bindings(self):
        identity=self.outputs['candidate_freeze_identity.json']
        self.assertEqual(identity['U11Input']['SHA256'],cf.file_identity(self.u11)['SHA256'])
        for n,e in self.u11['CandidateFreezeArtifacts'].items():self.assertEqual(e,cf.file_identity(self.outputs[n]))

    def test_source_missing_extra_duplicate_order_rejected(self):
        for operation in ('missing','extra','duplicate','reverse'):
            d=deepcopy(self.source)
            if operation=='missing':d['Candidates'].pop()
            elif operation=='extra':d['Candidates'].append(deepcopy(d['Candidates'][0]))
            elif operation=='duplicate':d['Candidates'][1]=deepcopy(d['Candidates'][0])
            else:d['Candidates'].reverse()
            with self.subTest(operation=operation),self.assertRaises(ValueError):cf.validate_source(d)

    def test_every_source_candidate_field_mutation_rejected(self):
        for index in range(40):
            d=deepcopy(self.source);d['Candidates'][index]['FormalEntryMinute']+=1
            with self.subTest(index=index),self.assertRaises(ValueError):cf.validate_source(d)
        for key in self.source['Candidates'][0]:
            d=deepcopy(self.source);d['Candidates'][0].pop(key)
            with self.subTest(key=key),self.assertRaises((ValueError,KeyError)):cf.validate_source(d)

    def test_u11_every_top_level_mutation_rejected(self):
        for key in self.u11:
            d=deepcopy(self.u11);d.pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError):cf.validate_u11(d,self.source)

    def test_u11_candidate_float_type_order_addition_rejected(self):
        for operation in ('float','type','order','add','baseline'):
            d=deepcopy(self.u11);r=d['Candidates'][0]
            if operation=='float':r['SelectedModeDiscoveryMetrics']['MaxDDPips']+=0.0000000001
            elif operation=='type':r['PairRank']=float(r['PairRank'])
            elif operation=='order':d['Candidates'].reverse()
            elif operation=='add':r['ValidationStatus']='PASS'
            else:r['SelectedModeDiscoveryMetrics']=deepcopy(r['DiscoveryE2Metrics']);r['SelectedModeDiscoveryMetrics']['MaxDDPips']+=1
            with self.subTest(operation=operation),self.assertRaises(ValueError):cf.validate_u11(d,self.source)

    def test_sha_format_reject(self):
        for value in ('A'*64,'a'*63,None):
            with self.assertRaises(ValueError):cf.sha_fields({'Nested':{'SelectedModeTradeStreamSHA256':value}})

    def test_pf_and_metric_schema_reject(self):
        for key,value in [('PFState','BAD'),('MaxDDPips',None),('Trades',True)]:
            d=deepcopy(self.source);d['Candidates'][0]['SelectedModeDiscoveryMetrics'][key]=value
            with self.assertRaises(ValueError):cf.validate_source(d)

    def test_source_byte_mutation_reject(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'source.json';p.write_bytes(cf.SOURCE.read_bytes()+b' ')
            with self.assertRaises(ValueError):cf.load_source(p)

    def test_duplicate_json_and_nonfinite_reject(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.json'
            for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
                p.write_text(raw)
                with self.assertRaises(ValueError):cf.read(p)

    def test_source_unchanged_and_deterministic(self):
        before=cf.SOURCE.read_bytes();a=cf.build();b=cf.build()
        self.assertEqual({n:cf.encoded(v) for n,v in a.items()},{n:cf.encoded(v) for n,v in b.items()})
        self.assertEqual(cf.SOURCE.read_bytes(),before)

    def test_no_actual_data_or_performance_access_trap(self):
        code=r'''
import sys,importlib.abc,builtins,io
from pathlib import Path
root=Path(sys.argv[1])
allowed={str(root/p) for p in ['research_inputs/b7/candidate_freeze_selected40_input.json','research_inputs/b7/full_research_prespec.json','docs/b7/full_research_conditions_freeze.md','research_inputs/b7/stage1_prespec.json','docs/b7/stage1_conditions_freeze.md','research_inputs/b7/stage0_protocol.json']}
class ImportTrap(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('b7.') and fullname not in ('b7.candidate_freeze','b7.stage1_contract'):
   raise AssertionError('Performance/loader import forbidden: '+fullname)
sys.meta_path.insert(0,ImportTrap())
opens=[]
def guard(original):
 def wrapped(file,mode='r',*args,**kwargs):
  if isinstance(file,(str,bytes,Path)):
   p=str(Path(file).resolve())
   assert p in allowed, 'Unexpected data read: '+p
   assert not any(x in mode for x in 'wa+'), 'Mutation forbidden'
   opens.append(p)
  return original(file,mode,*args,**kwargs)
 return wrapped
builtins.open=guard(builtins.open);io.open=guard(io.open)
def trace(frame,event,arg):
 if event=='call' and frame.f_globals.get('__name__','').startswith('b7'):
  assert frame.f_globals['__name__'] in ('b7','b7.candidate_freeze','b7.stage1_contract'), 'Performance execution forbidden'
sys.setprofile(trace)
from b7.candidate_freeze import build,validate_u11
out=build();validate_u11(out['u11_validation_selected40_input.json'])
assert opens and all(p.endswith(('.json','.md')) for p in opens)
print('TRAP_PASS: only pinned JSON/docs read; no M1/loader/Engine/event/protection/metrics/Gate/WTL/status execution')
'''
        result=subprocess.run([sys.executable,'-c',code,str(ROOT)],capture_output=True,text=True,env=dict(os.environ,PYTHONPATH=str(ROOT/'src/research'),PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('TRAP_PASS',result.stdout)


if __name__=='__main__':unittest.main()
