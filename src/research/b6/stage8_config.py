"""Hash-locked structural analysis specification; no price I/O at import."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/'research_inputs/b6/stage8_config.json'
CONFIG_SHA='addcaab2c618df492bd73d7ae2d83d626d8c9513420c939da5f98625bd4704c7'
def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError('Stage8 config SHA mismatch')
    return json.loads(PATH.read_text())
