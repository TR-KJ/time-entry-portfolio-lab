"""Current suite; unchanged historical release assertions use clean snapshots."""
import argparse,subprocess,sys,unittest
from pathlib import Path
from .stage6_config import ROOT

def run(stage2a_snapshot,stage2b_snapshot,stage3_snapshot,stage4_snapshot,stage5_snapshot):
    paths=[Path(p) for p in (stage2a_snapshot,stage2b_snapshot,stage3_snapshot,stage4_snapshot,stage5_snapshot)]
    shas=['50f83f3904acc3bc3abe54204db7a2ab4964b024','686b4b8b479055e3ff43a21f450b1a7182367ebe','a2e689332a229d648ed26418f220df96d8ede196','22a7b5ff8d49455afc730b446c666b1aa3a2a048','e35225782c84a59dd7546e9ff8d3944705c3709a']
    for p,s in zip(paths,shas):
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip()!=s or subprocess.check_output(['git','status','--porcelain'],cwd=p,text=True).strip():raise ValueError('clean historical snapshot SHA required')
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    for name in ('test_b6_release','test_b6_stage2a_release'):sys.modules[name].ROOT=paths[0]
    for name,p in zip(('test_b6_stage2b_release','test_b6_stage3_release','test_b6_stage4_release','test_b6_stage5_release'),paths[1:]):sys.modules[name].ROOT=p
    return unittest.TextTestRunner(verbosity=2).run(suite)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('stage2a-snapshot','stage2b-snapshot','stage3-snapshot','stage4-snapshot','stage5-snapshot'):p.add_argument('--'+n,required=True)
    a=p.parse_args();sys.exit(not run(a.stage2a_snapshot,a.stage2b_snapshot,a.stage3_snapshot,a.stage4_snapshot,a.stage5_snapshot).wasSuccessful())
