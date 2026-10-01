"""Immutable Stage3 config; no runtime input or prices on import."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/'research_inputs/b6/stage3_config.json'
CONFIG_SHA='4c7ca05a7d9ffac826de30ad8f5d3db882b720798e1afddf4bac63ddf2bb279d'
def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError('Stage3 config hash mismatch')
    return json.loads(PATH.read_text())
