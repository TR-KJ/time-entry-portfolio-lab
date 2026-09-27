import sys,unittest,copy,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
from b6.rules import *

def candidate(name,e=60,h=60,score=.1):
    m=dict(N=160,annual_N={y:40 for y in range(2020,2024)},losses=60,PF=1.2,AvgR=score,TotalR=16,MaxDDR=5,annual_TotalR={y:4 for y in range(2020,2024)})
    return dict(id=name,symbol='USDJPY',direction='L',weekday=0,entry=e,hold=h,sl_metrics=[copy.deepcopy(m) for _ in range(5)])

class ProposalRules(unittest.TestCase):
    def test_three_sl_and_all_five_median(self):
        a=candidate('a');b=candidate('b',e=180,score=.09)
        a['sl_metrics'][0]['AvgR']=-1;a['sl_metrics'][1]['AvgR']=-1
        self.assertEqual(shortlist([a,b])[0][0]['id'],'a')
        a['sl_metrics'][2]['AvgR']=-1;self.assertEqual([c['id'] for c in shortlist([a,b])[0]],['b'])
    def test_nontransitive_deterministic_grouping(self):
        a,b,c=[candidate(str(e),e=e) for e in (60,90,120)]
        picked,m=shortlist([c,b,a]);self.assertEqual([x['entry'] for x in picked],[60,120]);self.assertEqual(m['90'],'60')
        self.assertEqual(shortlist([a,b,c]),shortlist([c,b,a]))
    def test_offset_hold_and_clock(self):
        self.assertEqual(circular(1435,5),10)
        self.assertFalse(near(candidate('a',0,30),candidate('b',0,1440)))
        self.assertFalse(near(candidate('a',1380,30),candidate('b',1410,30)))
    def test_pf_zero_loss_and_year_rules(self):
        m=candidate('x')['sl_metrics'][0];m['PF']=float('inf');m['losses']=0;self.assertFalse(single_pass(m))
        m['PF']=1.2;m['losses']=20;m['annual_TotalR'][2020]=0;m['annual_TotalR'][2021]=0;self.assertFalse(single_pass(m))
    def test_finite_grids(self):
        self.assertEqual(tp_grid(10),[None,5,10,15,20,30])
        self.assertEqual(len(local_grid(50,50)),25);self.assertEqual(len(local_grid(50,None)),5)
        self.assertEqual(min(s for s,t in local_grid(10,None)),10)
        self.assertEqual(len(time_grid(600,60)),121)
        self.assertTrue(all(e>=0 and 30<=h<=1440 for e,h in time_grid(0,30)))
    def test_count_and_duplicate(self):
        root=Path(__file__).resolve().parents[1];c=json.loads((root/'research_inputs/b6/proposal.json').read_text())
        self.assertEqual(structure_count(c),5705280)
        with self.assertRaises(ValueError):shortlist([candidate('same'),candidate('same')])

if __name__=='__main__':unittest.main(verbosity=2)
