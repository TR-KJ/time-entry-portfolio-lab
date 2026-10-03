"""Exercise the actual preparation cell in a clean, local release checkout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'research_inputs/b6/stage8_release_manifest.json'

# Only Colab detection and external dependency/transport operations are stubbed.
# Checkout, release hashes, ancestry, input identities and clean guard stay real.
CHILD = r'''
import importlib.util, json, subprocess, sys
from pathlib import Path
from unittest.mock import patch
assert sys.dont_write_bytecode is False
repo = Path(sys.argv[1])
mode = sys.argv[2]
nb = json.loads((repo/'notebooks/b6_stage8_overlap_correlation.ipynb').read_text())
ns = {}
exec(''.join(nb['cells'][1]['source']), ns)
exec(''.join(nb['cells'][2]['source']), ns)
sha = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
ns.update(PREPARE_ENVIRONMENT=True, REPO_ROOT=str(repo), STAGE8_FREEZE_SHA=sha)
source = ''.join(nb['cells'][3]['source'])
if mode == 'original_bug':
    assert source.count('    sys.dont_write_bytecode = True\n') == 1
    source = source.replace('    sys.dont_write_bytecode = True\n', '')
real_run, real_find = subprocess.run, importlib.util.find_spec
calls = []
def run(args, **kwargs):
    if args == [sys.executable,'-m','pip','install','numpy==2.3.5','pandas==2.2.3']:
        calls.append('pip')
        return subprocess.CompletedProcess(args,0)
    if args == ['git','fetch','origin',sha]:
        calls.append('fetch')
        return subprocess.CompletedProcess(args,0)
    return real_run(args, **kwargs)
def find(name, *args, **kwargs):
    return object() if name == 'google.colab' else real_find(name,*args,**kwargs)
with patch('subprocess.run',side_effect=run), patch('importlib.util.find_spec',side_effect=find):
    if mode == 'original_bug':
        try:
            exec(source,ns)
        except ValueError as error:
            assert str(error) == 'clean Stage8 checkout required', str(error)
        else:
            raise AssertionError('original preparation unexpectedly passed')
        assert list(repo.rglob('__pycache__'))
        assert list(repo.rglob('*.pyc'))
    else:
        exec(source,ns)
        exec(source,ns)  # Rerunning preparation also stays clean.
        assert sys.dont_write_bytecode is True
        assert not list(repo.rglob('__pycache__'))
        assert not list(repo.rglob('*.pyc'))
        assert subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True) == ''
        from b6.stage8_search import verify_release
        for path in (repo/'unexpected.txt',repo/'notebooks/b6_stage8_overlap_correlation.ipynb'):
            original = path.read_bytes() if path.exists() else None
            path.write_bytes((original or b'') + b'\n')
            try:
                verify_release(sha)
            except ValueError as error:
                assert str(error) == 'clean Stage8 checkout required', str(error)
            else:
                raise AssertionError('dirty checkout accepted')
            finally:
                if original is None: path.unlink()
                else: path.write_bytes(original)
        assert verify_release(sha) == sha
        assert subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True) == ''
assert 'pip' in calls and 'fetch' in calls
'''


class PreparationTests(unittest.TestCase):
    def exercise(self, mode):
        with tempfile.TemporaryDirectory(prefix='b6-stage8-preparation-') as tmp:
            repo = Path(tmp)/'repo'
            def git(*args, cwd=repo):
                return subprocess.check_output(['git',*args],cwd=cwd,text=True,stderr=subprocess.STDOUT)
            git('clone','--quiet','--no-hardlinks',str(ROOT),str(repo),cwd=tmp)
            # Include the current release under test, even before its publication.
            for name in set(json.loads((ROOT/MANIFEST).read_text())) | {MANIFEST}:
                destination = repo/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,destination)
            git('add','--all')
            git('-c','user.name=Preparation regression','-c','user.email=test@example.invalid',
                'commit','--quiet','--allow-empty','-m','Local preparation test snapshot')
            self.assertEqual(git('status','--porcelain'),'')
            self.assertFalse(list(repo.rglob('__pycache__')))
            env = dict(os.environ)
            for name in ('PYTHONDONTWRITEBYTECODE','PYTHONPYCACHEPREFIX','PYTHONPATH'):
                env.pop(name,None)
            result = subprocess.run([sys.executable,'-c',CHILD,str(repo),mode],
                                    cwd=tmp,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_clean_preparation_no_cache_and_strict_dirty_guard(self):
        self.exercise('fixed')

    def test_regression_detects_original_bytecode_failure(self):
        self.exercise('original_bug')


if __name__ == '__main__':
    unittest.main()
