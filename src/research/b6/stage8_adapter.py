"""Checked period-only AST adapters in private modules; frozen files stay intact.

Only START/END, relative links, the weekday epoch and event date guards change.
No price, eligibility, SL/TP, rounding, fallback or event-overlap expression changes.
"""
import ast,sys,types
from functools import lru_cache
from .stage8_config import ROOT,sha,load_config

def adapted_tree(name,source):
    tree=ast.parse(source);changes=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.ImportFrom) and node.level==1 and node.module in ('execution','stage1_engine','stage2a_engine'):
            node.module='_stage8_'+node.module;changes.append('import')
        if name=='execution' and isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('START','END'):
            key=node.targets[0].id;expected="pd.Timestamp('2020-01-01')" if key=='START' else "pd.Timestamp('2024-01-01')"
            if ast.unparse(node.value)!=expected:raise ValueError('unexpected frozen period AST')
            value='2020-01-01' if key=='START' else '2026-09-10';node.value=ast.parse('pd.Timestamp('+repr(value)+')',mode='eval').body;changes.append(key)
        if name=='stage1_engine' and isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='weekday' for t in node.targets):
            if ast.unparse(node.value)!='(chosen // 1440 + 2) % 7':raise ValueError('unexpected frozen weekday AST')
            node.value=ast.parse('(chosen // 1440 + START.weekday()) % 7',mode='eval').body;changes.append('weekday_epoch')
        if name=='stage4_events' and isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value in ('2020-01-01','2024-01-01'):
            old=node.value;node.value={'2020-01-01':'2020-01-01','2024-01-01':'2026-09-10'}[old];changes.append(old)
    expected={'execution':['START','END'],'stage1_engine':['import','weekday_epoch'],'stage2a_engine':['import','import'],'stage4_events':['import','2020-01-01','2024-01-01']}
    if sorted(changes)!=sorted(expected[name]):raise ValueError('unexpected adapter transformation count: '+name)
    return ast.fix_missing_locations(tree)

@lru_cache(maxsize=1)
def modules():
    c=load_config();result={}
    for name in ('execution','stage1_engine','stage2a_engine','stage4_events'):
        path='src/research/b6/'+name+'.py'
        if sha(ROOT/path)!=c['execution_contract']['FrozenSourceSHA256'][path]:raise ValueError('frozen adapter source SHA mismatch')
        tree=adapted_tree(name,(ROOT/path).read_text());qualified='b6._stage8_'+name
        module=types.ModuleType(qualified);module.__package__='b6';module.__file__=str(ROOT/path);sys.modules[qualified]=module
        exec(compile(tree,str(ROOT/path)+' [Stage8 period adapter]','exec'),module.__dict__);result[name]=module
    return result
