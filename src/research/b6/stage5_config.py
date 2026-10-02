"""Hash-locked Stage5 source identities. No price inputs."""
import json
from .stage2a_config import ROOT,sha
PATH=ROOT/"research_inputs/b6/stage5_config.json"
CONFIG_SHA='5cde19cc5de4a34252124b9e0aded07948ab9b87cdef4b164e1cca08a2bebb10'
def load_config():
    if sha(PATH)!=CONFIG_SHA:raise ValueError("Stage5 config SHA mismatch")
    return json.loads(PATH.read_text())
