"""All tests, with unchanged historical release assertions at their own freezes."""
import argparse,subprocess,sys,unittest
from pathlib import Path
from .stage5_config import ROOT

def run(stage2a_snapshot,stage2b_snapshot,stage3_snapshot,stage4_snapshot):
    paths=[Path(p) for p in (stage2a_snapshot,stage2b_snapshot,stage3_snapshot,stage4_snapshot)]
    shas=['50f83f3904acc3bc3abe54204db7a2ab4964b024','686b4b8b479055e3ff43a21f450b1a7182367ebe','a2e689332a229d648ed26418f220df96d8ede196','22a7b5ff8d49455afc730b446c666b1aa3a2a048']
    for path,sha in zip(paths,shas):
        if subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()!=sha:raise ValueError('historical snapshot SHA mismatch')
        if subprocess.check_output(['git','status','--porcelain'],cwd=path,text=True).strip():raise ValueError('historical snapshot is not clean')
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_*.py')
    for name in ('test_b6_release','test_b6_stage2a_release'):sys.modules[name].ROOT=paths[0]
    for name,path in zip(('test_b6_stage2b_release','test_b6_stage3_release','test_b6_stage4_release'),paths[1:]):sys.modules[name].ROOT=path
    return unittest.TextTestRunner(verbosity=2).run(suite)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('stage2a-snapshot','stage2b-snapshot','stage3-snapshot','stage4-snapshot'):p.add_argument('--'+n,required=True)
    a=p.parse_args();sys.exit(not run(a.stage2a_snapshot,a.stage2b_snapshot,a.stage3_snapshot,a.stage4_snapshot).wasSuccessful())
