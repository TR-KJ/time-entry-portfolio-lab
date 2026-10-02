"""Hash-locked Stage6 specification; imports perform no price I/O."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/"research_inputs/b6/stage6_config.json"
CONFIG_SHA='fa68b843ce900a83fa9828a7415cce9256d45982e1fee3de9d21980cbb418e4c'
def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError("Stage6 config SHA mismatch")
    return json.loads(PATH.read_text())
