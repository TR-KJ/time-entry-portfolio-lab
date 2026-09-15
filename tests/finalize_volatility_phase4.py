"""Validate two complete regenerations before recording numerical validation PASS."""
from pathlib import Path
from decimal import Decimal, localcontext
import argparse,csv,json,os,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src/research'))
import volatility_phase4 as p
from verify_volatility_phase4 import verify_decision

def finalize(first,second):
    first,second=Path(first),Path(second)
    files=sorted(first.glob('*.csv'))
    assert {f.name for f in files}=={f.name for f in second.glob('*.csv')}
    for f in files: assert f.read_bytes()==(second/f.name).read_bytes(),f.name
    record=next(csv.DictReader((first/'volatility_phase4_run_record.csv').open()))
    if record['Status']!='MONEY_VERIFIED_AUDIT_AND_FULL_VALIDATION_PENDING':raise ValueError('Real money outputs required')
    assert record['BaselineHash']==p.p3.p1.BASELINE_HASH
    assert record['BaselineTrades']=='16298' and record['ScenarioStrategies']=='27'
    checks=list(csv.DictReader((first/'volatility_phase4_verification.csv').open()))
    money_checks=[r for r in checks if r['Check']=='Independent all trade/metric verification']
    assert len(money_checks)==20 and all(r['Status']=='PASS' for r in money_checks)
    env=dict(os.environ,PYTHONPATH=str(p.ROOT/'src/research')+os.pathsep+str(p.ROOT/'tests'))
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_volatility_phase*.py'],cwd=p.ROOT,env=env,check=True)
    summary=[]
    for name in ['27strategy_money_summary','period_reset_summary']:
        for row in csv.DictReader((first/('volatility_phase4_'+name+'.csv')).open()):
            for key in ['FinalCapital','MaxDDPct','WorstDayPct']:row[key]=Decimal(row[key])
            summary.append(row)
    with localcontext() as ctx:
        ctx.prec=40
        decision=p.decide(summary,validation=True,audit=None)
        verify_decision(summary,decision)
    p.check_sources()
    p.write(first,'decision',[decision])
    checks=[r for r in checks if r['Check']!='Full validation including regeneration and notebook']
    checks.extend([dict(Check='Numerical unit/inherited tests',Status='PASS'),dict(Check='Independent decision signs',Status='PASS'),
                   dict(Check='Complete deterministic CSV regeneration',Status='PASS',Detail=str(len(files))),
                   dict(Check='Notebook execution',Status='EXTERNAL_WORKFLOW_CHECK_REQUIRED')])
    # Heterogeneous records use an explicit common field set.
    fieldnames=sorted(set().union(*(r.keys() for r in checks)))
    with (first/'volatility_phase4_verification.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames);w.writeheader();w.writerows(checks)
    record.update(Status='HISTORICAL_VALIDATED_DEPLOYMENT_AUDIT_PENDING',Validation='PASS_NUMERICAL_AND_REGENERATION',
                  IndependentDecisionVerification='PASS',RegeneratedCSVCount=str(len(files)))
    record['OutputHashes']=json.dumps({f.name:p.p3.p1.sha(f) for f in files if f.name!='volatility_phase4_run_record.csv'},sort_keys=True)
    p.write(first,'run_record',[record])
    print('Historical numerical verification complete; current SET/spec audit remains UNDETERMINED')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--first',required=True);a.add_argument('--second',required=True);v=a.parse_args();finalize(v.first,v.second)
