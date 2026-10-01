"""All tests; immutable prior releases use their own clean snapshots."""
import argparse,subprocess,sys,unittest
from pathlib import Path
from .stage3_config import ROOT

def run(stage2a_snapshot,stage2b_snapshot):
    snapshots=[(Path(stage2a_snapshot),'50f83f3904acc3bc3abe54204db7a2ab4964b024'),(Path(stage2b_snapshot),'686b4b8b479055e3ff43a21f450b1a7182367ebe')]
    for path,sha in snapshots:
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()!=sha:raise ValueError('historical snapshot SHA mismatch')
        subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=path,check=True)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    for name in ('test_b6_release','test_b6_stage2a_release'):sys.modules[name].ROOT=snapshots[0][0]
    sys.modules['test_b6_stage2b_release'].ROOT=snapshots[1][0]
    return unittest.TextTestRunner(verbosity=2).run(suite)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage2a-snapshot',required=True);p.add_argument('--stage2b-snapshot',required=True);a=p.parse_args();sys.exit(not run(a.stage2a_snapshot,a.stage2b_snapshot).wasSuccessful())
