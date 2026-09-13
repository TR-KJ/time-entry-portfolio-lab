import copy
import inspect
from pathlib import Path
import sys
import tempfile
import unittest
from decimal import Decimal as D
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src/research'))
import edge_decay_sensitivity_analysis as s


def periods():
    return [dict(Trades=n, AvgR=D(a), PF=D(p)) for n,a,p in
            [(100,'.10','1.20'),(30,'.02','1.05'),(30,'.04','1.1'),(60,'.03','1.08')]]

class SensitivityTests(unittest.TestCase):
    def test_settings_exact_oat(self):
        expected = {('1.05','0.50',30,15),('1.00','0.50',30,15),('1.10','0.50',30,15),
                    ('1.05','0.25',30,15),('1.05','0.75',30,15),('1.05','0.50',20,10),('1.05','0.50',40,20)}
        self.assertEqual(len(s.SETTINGS),9)
        self.assertEqual({x[3:] for x in s.SETTINGS},expected)
        self.assertEqual(sum(x[2]=='OFFICIAL' for x in s.SETTINGS),3)
    def test_all_sample_boundaries(self):
        for cmin,abmin in [(20,10),(30,15),(40,20)]:
            v=periods();v[1]['Trades']=v[2]['Trades']=abmin;v[3]['Trades']=cmin
            self.assertEqual(s.classify(*v,combined=cmin,ab=abmin),'EDGE DECAY')
            for i in (1,2,3):
                w=copy.deepcopy(v);w[i]['Trades']-=1
                self.assertEqual(s.classify(*w,combined=cmin,ab=abmin),'INSUFFICIENT SAMPLE')
    def test_pf_strict_and_lost_priority(self):
        for threshold in ('1.00','1.05','1.10'):
            v=periods();v[3].update(AvgR=D('0'),PF=D('1'));v[0]['PF']=D(threshold)
            expected='EDGE DECAY' if D(threshold)>1 else 'STABLE'
            self.assertEqual(s.classify(*v,pf=threshold),expected)
            v[0]['PF']+=D('.000001')
            self.assertEqual(s.classify(*v,pf=threshold),'EDGE LOST')
            v[1]['Trades']=0
            self.assertEqual(s.classify(*v,pf=threshold),'INSUFFICIENT SAMPLE')
    def test_ratio_inclusive(self):
        for ratio in ('0.25','0.50','0.75'):
            v=periods();v[3]['AvgR']=v[0]['AvgR']*D(ratio)
            self.assertEqual(s.classify(*v,ratio=ratio),'EDGE DECAY')
            v[3]['AvgR']+=D('.000000001')
            self.assertEqual(s.classify(*v,ratio=ratio),'STABLE')
    def test_decay_no_extra_historical_gate(self):
        v=periods();v[0]['PF']=D('1.01');v[3]['PF']=D('1.00')
        self.assertEqual(s.classify(*v,pf='1.10'),'EDGE DECAY')
        v[0]['AvgR']=D('-.1');v[1]['AvgR']=v[2]['AvgR']=v[3]['AvgR']=D('-.2')
        self.assertEqual(s.classify(*v),'EDGE DECAY')
    def test_persistence_and_pf_decline(self):
        for i in (1,2):
            v=periods();v[i]['AvgR']=v[0]['AvgR']
            self.assertEqual(s.classify(*v),'STABLE')
        v=periods();v[3]['PF']=v[0]['PF']
        self.assertEqual(s.classify(*v),'STABLE')
    def test_missing_and_infinite(self):
        for i,k in [(0,'AvgR'),(1,'AvgR'),(2,'AvgR'),(3,'AvgR'),(0,'PF'),(3,'PF')]:
            v=periods();v[i][k]=None
            self.assertEqual(s.classify(*v),'STABLE')
        v=periods();v[0]['PF']=D('Infinity')
        self.assertEqual(s.classify(*v),'EDGE DECAY')
    def test_ratio_na(self):
        for h in (None,D(0),D(-1)):
            self.assertEqual(s.avg_ratio(h,D(1)),'NA')
        self.assertEqual(s.avg_ratio(D(2),D(-1)),D('-.5'))
    def test_labels(self):
        for n in range(8):
            self.assertEqual(s.warning_label('EDGE LOST',n),'頑健' if n==7 else '中程度' if n>=5 else '不安定')
            self.assertEqual(s.warning_label('STABLE',n),'NA (non-candidate)')
    def test_monitor_not_input(self):
        self.assertEqual(list(inspect.signature(s.classify).parameters),['h','a','b','c','pf','ratio','combined','ab'])
    def test_bad_hash_stops(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.csv';p.write_text('bad')
            with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):s.load_baseline(p)
            with self.assertRaisesRegex(ValueError,'blob mismatch'):s.read_primary(p)
    def test_primary_changes_stop(self):
        with self.assertRaises(ValueError):s.check_primary([],[])

if __name__=='__main__':unittest.main()
