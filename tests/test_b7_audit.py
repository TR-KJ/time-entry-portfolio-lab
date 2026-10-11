import unittest,sys,tempfile,json,hashlib,ast
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
from b7.stage0_audit import inspect_file,loader,ROOT
from b7.execution import discovery_view,validate
from b7.calibration import calibrate,round5

class B7AuditTests(unittest.TestCase):
    def test_discovery_copy_never_returns_future(self):
        idx=pd.to_datetime(['2019-12-31 23:59','2020-01-01','2023-12-31 23:59','2024-01-01','2026-01-01'],format='mixed')
        full=pd.DataFrame(1.,index=idx,columns=['Open','High','Low','Close']);view=discovery_view(full)
        self.assertEqual(len(view),2);validate(view);view.iloc[0,0]=2;self.assertEqual(full.iloc[1,0],1)
        with self.assertRaises(ValueError):validate(full)
    def test_invalid_data_rejected(self):
        header='<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n'
        for values in ['1\t0.9\t1\t1','NaN\t1\t1\t1','inf\tinf\t1\t1','-1\t-1\t-1\t-1','1.000001\t1.000001\t1.000001\t1.000001']:
            with self.subTest(values=values),tempfile.TemporaryDirectory() as d:
                p=Path(d)/'test.csv';p.write_text(header+'2020.02.04\t03:00:00\t'+values+'\n2020.02.04\t03:01:00\t'+values+'\n')
                with self.assertRaises(ValueError):inspect_file(p,'EURUSD',loader())
    def test_unsorted_raw_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.csv';p.write_text('<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\n2020.02.04\t03:01:00\t1\t1\t1\t1\n2020.02.04\t03:00:00\t1\t1\t1\t1\n')
            with self.assertRaises(ValueError):inspect_file(p,'EURUSD',loader())
    def test_insufficient_calibration_is_not_fabricated(self):
        b=pd.DataFrame(1.,index=pd.date_range('2020-02-04',periods=1440,freq='min'),columns=['Open','High','Low','Close'])
        result,days=calibrate(b,'EURUSD')
        self.assertEqual(result['Status'],'PENDING_INSUFFICIENT_DATA');self.assertEqual(result['SL'],[])
        self.assertEqual(result['EligibleDays'],1)
    def test_half_up_boundaries(self):
        self.assertEqual(round5(12.5),15);self.assertEqual(round5(12.499),10)
    def test_calibration_and_reference_source_identity(self):
        sources=json.loads((ROOT/'results/b7/stage0/source_manifest.json').read_text())
        target=next(x for x in sources if x['Path']=='src/research/b6/execution.py')
        p=ROOT/'src/research/b7/reference/b6_execution.py'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),target['SHA256'])
    def test_protocol_has_no_implicit_stage1_defaults(self):
        c=json.loads((ROOT/'research_inputs/b7/stage0_protocol.json').read_text())
        for k in ['stage1_enabled','validation_enabled','monitor_enabled','money_enabled','live_enabled','formal_stage1_conditions_frozen','candidate_inputs_allowed']:self.assertIs(c[k],False)
        self.assertEqual(c['spread_pips']['GBPUSD'],1.5);self.assertEqual(c['spread_pips']['EURUSD'],1)
        for k in ['gate_values','neighborhood_thresholds','family_distance_rule','fixed_key']:self.assertIsNone(c['stage1_design'][k])
    def test_audit_inventory_and_isolation_evidence(self):
        m=pd.read_csv(ROOT/'research_inputs/b7/expected_m1_manifest.csv');a=pd.read_csv(ROOT/'results/b7/stage0/input_audit.csv')
        self.assertEqual(len(m),72);self.assertTrue((m.groupby('Symbol').size()==8).all());self.assertFalse(m.Filename.duplicated().any())
        selected=a[a.Selected];self.assertEqual(len(selected),72)
        cols=['Symbol','Filename','SHA256','Rows','FirstRaw','LastRaw']
        self.assertTrue(m[cols].sort_values('Filename').reset_index(drop=True).equals(selected[cols].sort_values('Filename').reset_index(drop=True)))
        for r in json.loads((ROOT/'results/b7/stage0/price_statistics.json').read_text()):
            self.assertEqual(set(r['AnnualDays']),{'2020','2021','2022','2023'});self.assertEqual(len(r['SL']),5)
            if r['Symbol'] not in ('EURUSD','GBPUSD'):self.assertTrue(r['B6GridExactMatch'])
    def test_audit_status_does_not_clear_broker(self):
        c=json.loads((ROOT/'results/b7/stage0/run_status.json').read_text())
        self.assertEqual(c['BrokerIdentity'],'HISTORICAL_NOT_FULLY_CERTIFIED');self.assertEqual(c['Stage0'],'PASS_WITH_PROVENANCE_LIMITATION')
        self.assertEqual(c['B01'],'CLEAR_WITH_LIMITATION');self.assertFalse(c['Stage1ExecutionAuthorized'])
        self.assertEqual(c['ValidationPerformance'],'COMPLETE_FROZEN');self.assertTrue(c['U11ResultFrozen'])
        self.assertEqual(c['MonitorPerformance'],'NOT_RUN');self.assertFalse(c['MonitorExecuted'])

if __name__=='__main__':unittest.main()
