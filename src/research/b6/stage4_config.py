"""Hash-locked Stage4 configuration; import performs no runtime I/O."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/"research_inputs/b6/stage4_config.json"
CONFIG_SHA='71ed976b935d99d1a6b76a3d8035418b52b15b0c7c99c974b2dfbf74053c53d6'
def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError("Stage4 config SHA mismatch")
    return json.loads(PATH.read_text())
