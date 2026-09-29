"""Run every test while retaining immutable Stage1/2-A release test semantics.

The two historical release modules use a clean Stage2-A snapshot for their
ROOT-scoped manifest checks. All other tests run on the current Stage2-B tree.
Stage2-B release tests also verify all unchanged frozen files in the new tree.
No historical source/test/manifest needs rewriting to allow evolving docs.
"""
import argparse,subprocess,sys,unittest
from pathlib import Path
from .stage2a_config import ROOT
FREEZE='50f83f3904acc3bc3abe54204db7a2ab4964b024'

def run(snapshot):
    snapshot=Path(snapshot).resolve()
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=snapshot,text=True).strip()!=FREEZE:raise ValueError('Stage2-A snapshot SHA mismatch')
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=snapshot,check=True)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    for name in ('test_b6_release','test_b6_stage2a_release'):sys.modules[name].ROOT=snapshot
    return unittest.TextTestRunner(verbosity=2).run(suite)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage2a-snapshot',required=True);a=p.parse_args();sys.exit(not run(a.stage2a_snapshot).wasSuccessful())
