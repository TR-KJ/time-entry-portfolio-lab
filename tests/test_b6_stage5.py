"""Stage5 synthetic saved-output audits and packaging; no market input files."""
import copy,csv,hashlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from test_b6_stage4 import point,replay,official,calendar
from b6.stage4_metrics import evaluate_modes,FIXED,FULL
from b6.stage4_config import load_config as prior_config
from b6.stage5_config import load_config
from b6.stage5_input import validate_payload,load_input,strict_json
from b6.stage5_freeze import serialize,sha_bytes,build_candidate_freeze,build_outputs,summary_csv,write_identical_or_new,generate,CANDIDATE_PATH,CONTRACT_PATH
from b6.stage5_validation import contract,assess,dd_limit

def payload():
    c=load_config();c.update(expected_candidate_count=1,expected_variant_count=3,expected_selected_modes=dict(E0=1,E1=0,E2=0));prev=prior_config()
    p=official(point(),replay());data=evaluate_modes(p,replay(),calendar());s=data['selected'];cid=s['CandidateID']
    identity=dict(code_sha=c['stage4_freeze_sha'],config_sha256=c['stage4_config_sha256'],stage3_code_sha=c['stage3_freeze_sha'],selected_settings_sha256=c['stage3_selected_sha256'],stage3_runtime_sha256=prev['stage3_runtime_manifest'],calendar_sha256=prev['calendar_sha256'],calendar_source_commit=prev['calendar_source_commit'],candidate_sha256=prev['candidate_sha256'],scope='FULL_DISCOVERY_STAGE4',runtime=dict(Python='3.13.15',Numpy='2.3.5',Pandas='2.2.3'))
    with (ROOT/'research_inputs/b6/expected_m1_manifest.csv').open() as f:identity['inputs']=[{k:r[k] for k in ('Filename','SHA256')} for r in csv.DictReader(f)]
    summary=dict(State='COMPLETE_STAGE4_ONLY',CandidateCount=1,VariantCount=3,SelectedModeCounts=dict(E0=1,E1=0,E2=0),FilterAdoptionCount=0,E1AdoptionCount=0,E2AdoptionCount=0,SelectedDistributions={k:dict(Count=1,UndefinedCount=0,Min=s[k],Median=s[k],Max=s[k]) for k in ('RetentionRate','RemovedTrades','DeltaTotalR','DeltaAvgR','DeltaMaxDDR')},EventFilterExecuted=True,CandidateFreezeExecuted=False,ValidationExecuted=False,MonitorExecuted=False,PortfolioExecuted=False)
    meta={'identity.json':identity,'effective_config.json':prev,'stage3_input_audit.json':strict_json((ROOT/'results/b6/stage4_freeze/stage3_input_audit.json').read_bytes()),'event_calendar.json':strict_json((ROOT/'research_inputs/b6/stage4_event_calendar.json').read_bytes()),'event_calendar_audit.json':strict_json((ROOT/'results/b6/stage4_freeze/event_calendar_audit.json').read_bytes()),'stage4_summary.json':summary,'progress.json':dict(summary,CompletedJobs=1,ExpectedJobs=1,CompletedConfigurations=3),'stage4_selected_settings.json':[s],'e0_equivalence_audit.json':dict(Status='PASS',Comparison='EXACT_FULL_AND_FOUR_YEARLY_METRICS',Candidates=[dict(CandidateID=cid,FullMetrics='EXACT_PASS',YearlyMetrics='EXACT_PASS')]),'search_space.json':dict(CandidateCount=1,VariantsPerCandidate=3,TheoreticalMax=3,ActualUniqueConfigurations=3,Modes=['E0','E1','E2'],DeduplicateModes=False,NoRetuning=True,NoRefill=True,NoDrop=True)}
    return meta,{cid:data},[p],c

def build_fixture():
    meta,shards,prior,c=payload();selected,_,identity=validate_payload(meta,shards,prior,c)
    audit=dict(FormalInputSHA256=c['stage4_runtime_sha256'],SelectedModeCounts=dict(E0=1,E1=0,E2=0))
    return selected,shards,audit,identity,c

class InputTests(unittest.TestCase):
    def test_valid_saved_outputs(self):self.assertEqual(len(validate_payload(*payload())[0]),1)
    def test_wrong_freeze(self):
        args=payload();args[0]['identity.json']['code_sha']='bad'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_wrong_config_sha(self):
        args=payload();args[0]['identity.json']['config_sha256']='bad'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_incomplete(self):
        args=payload();args[0]['progress.json']['State']='RUNNING'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_later_stage_contamination(self):
        for key in ('CandidateFreezeExecuted','ValidationExecuted','MonitorExecuted','PortfolioExecuted'):
            args=payload();args[0]['stage4_summary.json'][key]=True
            with self.assertRaises(ValueError):validate_payload(*args)
    def test_duplicate_id(self):
        args=payload();args[0]['stage4_selected_settings.json']*=2
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_count_mismatch(self):
        args=payload();args[3]['expected_candidate_count']=2
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_selection_mismatch(self):
        args=payload();s=args[0]['stage4_selected_settings.json'][0];s['SelectedEventMode']='E1'
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_missing_e2(self):
        args=payload();args[1][args[2][0]['CandidateID']]['results'].pop()
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_wrong_delta(self):
        args=payload();args[1][args[2][0]['CandidateID']]['results'][1]['DeltaTotalR']=999
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_wrong_e0_metrics(self):
        args=payload();args[2][0]['TotalR']+=1
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_wrong_selected_yearly(self):
        args=payload();args[0]['stage4_selected_settings.json'][0]['YearlyMetrics'][0]['TotalR']+=1
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_wrong_chat_expected_mode_counts(self):
        args=payload();args[3]['expected_selected_modes']=dict(E0=0,E1=1,E2=0)
        with self.assertRaises(ValueError):validate_payload(*args)
    def test_unavailable_formal_archive_no_reconstruction(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):load_input(Path(d)/'missing','absent')
            (Path(d)/'stage4_review.zip').write_bytes(b'not substitute')
            with self.assertRaises(ValueError):load_input(d,'absent')
    def test_exact_byte_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';p.write_text('{}');c=load_config();c['stage4_runtime_sha256']={'x.json':'0'*64}
            with self.assertRaises(ValueError):load_input(d,'absent',c)

for field in FIXED:
    if field=='CandidateID':continue
    def check(self,field=field):
        args=payload();args[0]['stage4_selected_settings.json'][0][field]='tampered'
        with self.assertRaises(ValueError):validate_payload(*args)
    setattr(InputTests,'test_changed_'+field,check)

class FreezeTests(unittest.TestCase):
    def test_all_selected_fields_and_discovery_raw_values(self):
        selected,shards,audit,identity,c=build_fixture();f=build_candidate_freeze(selected,shards,audit,identity,c);out=f['Candidates'][0];s=selected[0]
        for k in FIXED:self.assertEqual(out[k],s[k])
        for k in ('SelectedEventMode','ApplicableEvents'):self.assertEqual(out[k],s[k])
        self.assertEqual(out['DiscoveryMetrics'],s['SelectedModeMetrics']);self.assertEqual(out['DiscoveryMaxDDR'],s['SelectedModeMetrics']['MaxDDR'])
        for a,b in zip(out['DiscoveryYearlyMetrics'],s['YearlyMetrics']):self.assertTrue(all(a[k]==b[k] for k in a))
        self.assertEqual(out['FixedSpreadPips'],.5);self.assertEqual(out['PipSize'],.01)
    def test_all_fifty_retained_no_reranking(self):
        s,h,a,i,c=build_fixture();selected=[];shards={}
        for n in range(50):
            row=copy.deepcopy(s[0]);row['CandidateID']=f'fixed-order-{49-n:02d}';selected.append(row);shard=copy.deepcopy(next(iter(h.values())));shard['selected']=row;shards[row['CandidateID']]=shard
        c['expected_candidate_count']=50;f=build_candidate_freeze(selected,shards,a,i,c)
        self.assertEqual([r['CandidateID'] for r in f['Candidates']],[r['CandidateID'] for r in selected]);self.assertEqual(len(f['Candidates']),50)
    def test_missing_candidate_rejected(self):
        s,h,a,i,c=build_fixture();c['expected_candidate_count']=2
        with self.assertRaises(ValueError):build_candidate_freeze(s,h,a,i,c)
    def test_e0_is_compared_outcome(self):
        f=build_candidate_freeze(*build_fixture());a=f['Candidates'][0]['Stage4DecisionAudit'];self.assertEqual(a['AllModesCompared'],['E0','E1','E2']);self.assertFalse(a['E1AdoptionPass']);self.assertFalse(a['E2AdoptionPass'])
    def test_deterministic_bytes_sha(self):
        args=build_fixture();a=serialize(build_candidate_freeze(*args));b=serialize(build_candidate_freeze(*copy.deepcopy(args)))
        self.assertEqual(a,b);self.assertEqual(sha_bytes(a),sha_bytes(b));self.assertTrue(a.endswith(b'\n'));self.assertEqual(serialize(dict(b=1,a=2)),serialize(dict(a=2,b=1)))
    def test_raw_dd_not_display_rounding(self):
        args=build_fixture();s=args[0][0];s['SelectedModeMetrics']['MaxDDR']=1.1234567891234567
        f=build_candidate_freeze(*args);self.assertEqual(f['Candidates'][0]['DiscoveryMaxDDR'],1.1234567891234567);self.assertNotEqual(f['Candidates'][0]['DiscoveryMaxDDR'],round(1.1234567891234567,9))
    def test_explicit_inf_undefined_and_reject_nan(self):
        self.assertEqual(strict_json(serialize({'PF':'INF','AvgR':'UNDEFINED'})),{'PF':'INF','AvgR':'UNDEFINED'})
        for bad in (float('nan'),float('inf'),float('-inf')):
            with self.assertRaises(ValueError):serialize({'PF':bad})
        with self.assertRaises(ValueError):strict_json(b'{"PF":NaN}')
    def test_zero_r_kept_neutral(self):
        f=build_candidate_freeze(*build_fixture());m=f['Candidates'][0]['DiscoveryMetrics'];self.assertEqual(m['Trades'],4);self.assertEqual(m['ZeroR'],1);self.assertEqual(m['Wins']+m['Losses']+m['ZeroR'],m['Trades'])
    def test_summary_is_json_view(self):
        f=build_candidate_freeze(*build_fixture());rows=list(csv.DictReader(io.StringIO(summary_csv(f).decode())));p=f['Candidates'][0]
        self.assertEqual(rows[0]['CandidateID'],p['CandidateID']);self.assertEqual(float(rows[0]['MaxDDR']),p['DiscoveryMaxDDR']);self.assertEqual(rows[0]['TPMode'],'TP_NONE');self.assertEqual(rows[0]['TP'],'')
        for y in p['DiscoveryYearlyMetrics']:self.assertEqual(float(rows[0]['TotalR_'+str(y['Year'])]),y['TotalR'])
    def test_no_different_artifact_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.json';write_identical_or_new(p,b'a');write_identical_or_new(p,b'a')
            with self.assertRaises(ValueError):write_identical_or_new(p,b'b')
            self.assertEqual(p.read_bytes(),b'a')
    def test_generation_does_not_call_price_or_research_apis(self):
        s,h,a,i,c=build_fixture()
        with patch('b6.stage5_freeze.load_input',return_value=(s,h,a,i)),patch('b6.stage5_freeze.load_config',return_value=c),patch('b6.stage1_data.audit_inputs',side_effect=AssertionError('M1')),patch('b6.stage1_data.load_discovery',side_effect=AssertionError('prices')),patch('b6.stage4_search.full_sweep',side_effect=AssertionError('research')),patch('b6.stage5_validation.assess',side_effect=AssertionError('validation evaluation')):
            files,report=build_outputs('formal-stage4','stage3-reference')
        self.assertFalse(report['PriceReplayPerformed']);self.assertFalse(report['ValidationExecuted']);self.assertEqual(strict_json(files[CONTRACT_PATH])['CandidateFreezeSHA256'],sha_bytes(files[CANDIDATE_PATH]))
    def test_only_discovery_metric_years(self):
        f=build_candidate_freeze(*build_fixture());self.assertEqual(f['DiscoveryPeriod']['EndExclusive'],'2024-01-01')
        self.assertEqual([r['Year'] for r in f['Candidates'][0]['DiscoveryYearlyMetrics']],[2020,2021,2022,2023])


def validation_fixture():return dict(Trades=30,Losses=5,TotalR=1.,PF=.01,AvgR=-99),dict(Trades=40,Losses=5,TotalR=1.,PF=.01,AvgR=-99),dict(Trades=70,PF=1.10,AvgR=.02,MaxDDR=10.)

class ValidationTests(unittest.TestCase):
    def test_exact_sample_and_pass_boundaries(self):self.assertEqual(assess(*validation_fixture(),5)['ValidationStatus'],'PASS')
    def test_insufficient_is_not_fail_and_does_not_evaluate_performance(self):
        a,b,c=validation_fixture();a['Trades']=29;del a['TotalR'];c.pop('PF');r=assess(a,b,c,5);self.assertEqual(r['ValidationStatus'],'INSUFFICIENT_SAMPLE');self.assertFalse(r['SampleSufficient']);self.assertEqual(r['ValidationFailReasons'],[])
    def test_2025_trades_30_sufficient(self):
        a,b,c=validation_fixture();b['Trades']=30;self.assertTrue(assess(a,b,c,5)['SampleSufficient'])
    def test_no_annual_pf_avg_winrate_extra_gate(self):
        a,b,c=validation_fixture();a.update(WinRate=0,Recovery=-100);b.update(WinRate=0,Recovery=-100);self.assertEqual(assess(a,b,c,5)['ValidationStatus'],'PASS')
    def test_dd_formula_floor_and_scaled(self):self.assertEqual(dd_limit(0),10.);self.assertEqual(dd_limit(5),10.);self.assertEqual(dd_limit(8),12.)
    def test_raw_discovery_dd_used(self):
        d=8.123456789123456;self.assertEqual(dd_limit(d),1.5*d);self.assertNotEqual(dd_limit(d),1.5*round(d,9))
    def test_dd_exact_scaled_pass(self):
        a,b,c=validation_fixture();c['MaxDDR']=12.;self.assertEqual(assess(a,b,c,8)['ValidationStatus'],'PASS')
    def test_required_undefined_fails(self):
        a,b,c=validation_fixture();c['PF']='UNDEFINED';self.assertEqual(assess(a,b,c,5)['ValidationStatus'],'FAIL')
    def test_contract_has_only_five_pass_conditions(self):
        c=contract('a'*64);self.assertEqual(len(c['PassConditions']),5);self.assertEqual(c['Statuses'],['PASS','FAIL','INSUFFICIENT_SAMPLE']);self.assertEqual(c['CandidateFreezeSHA256'],'a'*64)
        self.assertEqual(c['Periods']['Combined'],dict(StartInclusive='2024-01-01',EndExclusive='2026-01-01'));self.assertFalse(c['ValidationExecuted'])

for name,index,key,value in [('2024_trades29',0,'Trades',29),('2024_losses4',0,'Losses',4),('2025_trades29',1,'Trades',29),('2025_losses4',1,'Losses',4),('combined_trades69',2,'Trades',69)]:
    def check(self,index=index,key=key,value=value):
        rows=list(validation_fixture());rows[index][key]=value;out=assess(*rows,5);self.assertEqual(out['ValidationStatus'],'INSUFFICIENT_SAMPLE');self.assertEqual(out['ValidationFailReasons'],[])
    setattr(ValidationTests,'test_'+name,check)
for name,index,key,value in [('2024_zero_total',0,'TotalR',0),('2025_zero_total',1,'TotalR',0),('2024_negative_total',0,'TotalR',-1),('2025_negative_total',1,'TotalR',-1),('pf_below',2,'PF',1.0999999999999999),('avg_below',2,'AvgR',.019999999999999997),('tiny_dd_excess',2,'MaxDDR',10.000000000000002)]:
    def check(self,index=index,key=key,value=value):
        rows=list(validation_fixture());rows[index][key]=value;self.assertEqual(assess(*rows,5)['ValidationStatus'],'FAIL')
    setattr(ValidationTests,'test_'+name,check)
