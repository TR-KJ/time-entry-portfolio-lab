"""Stage2-B immutable configuration; no price or result loading on import."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/'research_inputs/b6/stage2b_config.json'
CONFIG_SHA='60ae03111ed6bf283df47acf62a6713a8ee53459a48d52a84a70553dd9070bf3'

def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError('Stage2-B config hash mismatch')
    return json.loads(PATH.read_text())
