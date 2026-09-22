from pathlib import Path
import sys
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import strategy_selective_r2 as a5


def test_membership_source():
    m=a5.membership()
    assert len(m)==28
    assert {x['StrategyNo'] for x in m if x['STRONG']}==a5.STRONG
    assert {x['StrategyNo'] for x in m if x['BROAD']}==a5.BROAD
    assert not next(x for x in m if x['StrategyNo']==22)['Active']


def test_risk_mapping():
    assert [a5.risk('R2_GLOBAL',1,f'Q{i}') for i in range(1,6)]==list(map(D,('.50','.70','.90','1.10','1.30')))
    assert a5.risk('S1_STRONG_ONLY_R2',1,'Q5')==D('1.30')
    assert a5.risk('S1_STRONG_ONLY_R2',2,'Q5')==D('.90')
    assert a5.risk('S2_BROAD_R2',2,'Q5')==D('1.30')
    assert a5.risk('S2_BROAD_R2',28,'Q5')==D('.90')
    assert a5.risk('R2_GLOBAL',1,a5.p3.p1.INS)==D('.90')


def test_decision_profit_first():
    rows=[]
    for method in a5.METHODS:
        for period in a5.PERIODS:
            for variant in a5.VARIANTS:
                wealth=D(600000) if variant=='R2_GLOBAL' else D(500000)
                rows.append(dict(Method=method,Period=period,Variant=variant,FinalCapital=wealth,MaxDDPct=D(10),WorstDayPct=D(-5),MeanNominalRiskPct=D('.9')))
    v=a5.decision(rows,{},True)
    assert all(x['Verdict']=='GLOBAL_R2_REMAINS_PREFERRED' for x in v)
