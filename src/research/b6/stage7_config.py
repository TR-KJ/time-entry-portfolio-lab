"""Hash-locked Monitor specification; import performs no price I/O."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/'research_inputs/b6/stage7_config.json'
CONFIG_SHA='fa42a56ebf23135c4d9c11d973016614c5298c72ecab60a309218a395d58b683'
def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError('Stage7 config SHA mismatch')
    return json.loads(PATH.read_text())
