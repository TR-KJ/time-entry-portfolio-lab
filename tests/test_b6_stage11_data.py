import unittest,sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/research'))
from b6.stage11_input import load_daily
from b6.stage11_r2 import daily_from_rows,feature_daily,Assigner

class DataTests(unittest.TestCase):
    def parse(self,frame):
        manifest=pd.DataFrame([{'Symbol':'GBPJPY','Filename':'fixture'}]);reader=type('Reader',(),{'read_mt5_file':lambda _,p:frame})()
        with patch('b6.stage0.reference',return_value=reader):return load_daily('GBPJPY',manifest,{'fixture':Path('/synthetic')})
    def frame(self,times):
        return pd.DataFrame({'RawDatetime':pd.to_datetime(times),'Open':[100.]*len(times),'High':[101.]*len(times),'Low':[99.]*len(times),'Close':[100.]*len(times)})
    def test_full_history_timezone_warmup_and_saturday(self):
        d=self.parse(self.frame(['2019-01-04 23:00:00','2019-01-05 00:00:00','2024-07-01 00:00:00']))
        self.assertEqual(d[0]['day'],datetime(2019,1,5));self.assertEqual(d[0]['day'].weekday(),5)
        self.assertEqual(d[0]['last'],datetime(2019,1,5,7));self.assertEqual(d[-1]['last'],datetime(2024,7,1,6));self.assertEqual(len(d),2)
    def test_parser_does_not_sort_bad_source(self):
        with self.assertRaisesRegex(ValueError,'UNSORTED'):self.parse(self.frame(['2020-01-02','2020-01-01']))
    def test_parser_duplicate_reject(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.parse(self.frame(['2020-01-01','2020-01-01']))
    def test_parser_invalid_ohlc_reject(self):
        f=self.frame(['2020-01-01']);f['High']=90.
        with self.assertRaisesRegex(ValueError,'INVALID_OHLC'):self.parse(f)
    def test_parser_nonfinite_reject(self):
        f=self.frame(['2020-01-01']);f['Open']=float('inf')
        with self.assertRaisesRegex(ValueError,'INVALID_OHLC'):self.parse(f)
    def test_m1_alignment_reject(self):
        with self.assertRaisesRegex(ValueError,'ALIGNMENT'):self.parse(self.frame(['2020-01-01 00:00:01']))
    def test_empty_formal_source_reject(self):
        with self.assertRaisesRegex(ValueError,'UNAVAILABLE'):load_daily('GBPJPY',pd.DataFrame(columns=['Symbol','Filename']),{})
