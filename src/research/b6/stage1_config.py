"""Load one approved, immutable Stage1 configuration; no runtime parameter overrides."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PATH=ROOT/'research_inputs/b6/stage1_config.json'
# Filled from the approved file before release; tests require this exact digest.
CONFIG_SHA='93cc9a92c6473cf770f98b72511de076375411db1c27ae1568f976f96212b37e'

def load_config():
    data=PATH.read_bytes()
    if hashlib.sha256(data).hexdigest()!=CONFIG_SHA:raise ValueError('Stage1 config hash mismatch; not the frozen implementation')
    return json.loads(data)

def search_space(c=None):
    c=load_config() if c is None else c;h=c['holding_minutes']
    structures=len(c['symbols'])*len(c['directions'])*len(c['weekdays'])*len(range(0,1440,c['entry_step_minutes']))*len(range(h['min'],h['max']+1,h['step']))
    return {'time_structures':structures,'SL_settings':structures*5,'entry_minutes':288,'holding_values':283,'TP':'NONE','period':'2020-2023 only','max_stage2_structures':50}
