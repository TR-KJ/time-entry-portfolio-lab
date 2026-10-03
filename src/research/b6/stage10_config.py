"""Stage10 fixed-risk specification; Global R2 excluded by later user instruction."""
import hashlib
import json
from pathlib import Path
from decimal import Decimal as D
ROOT = Path(__file__).resolve().parents[3]
STAGE9_SHA = 'e66c54b65ca4ee2e6f7f730a1adc69a3357cfdcd'
FINAL_SHA = 'e154b03d92f3af5d0108ec983fe3843ef374cf64a6e5f5d5feb54a3014108562'
BASELINE_SHA = 'cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359'
LEDGER_SHA = 'af0caed1d3002af960042d56e50e290271a3aced5a82ee879997a30d4e418248'
AJ = 'B6-AUDJPY-L-W0-E0950-H1440'
GJ = 'B6-GBPJPY-L-W0-E0835-H1415'
EXCLUDED = '22_GA_C_2'
RISKS = (D('.25'), D('1.0'), D('1.5'), D('2.0'))
CONFIGS = {'P0_CURRENT': (), 'P1_CURRENT_PLUS_AJ': (AJ,),
           'P2_CURRENT_PLUS_GJ': (GJ,), 'P3_CURRENT_PLUS_B6_BOTH': (AJ,GJ)}
PERIODS = {'Discovery': ('2020-01-01','2024-01-01'),
           'Validation': ('2024-01-01','2026-01-01'),
           'Monitor': ('2026-01-01','2026-09-10'),
           'PostDiscovery': ('2024-01-01','2026-09-10'),
           'FullAvailable': ('2020-01-01','2026-09-10')}
MODES = {'CONTINUOUS_2020': ('2020-01-01',tuple(PERIODS)),
         'POSTDISCOVERY_RESET_2024': ('2024-01-01',('Validation','Monitor','PostDiscovery'))}
STATE = 'COMPLETE_STAGE10_INCREMENTAL_PORTFOLIO_ONLY'
INPUT = 'research_inputs/b6/'
OUTPUT = 'results/b6/stage10_freeze/'
IMMUTABLE = {
 INPUT+'stage9_final_candidates.json': FINAL_SHA,
 INPUT+'stage9_config.json': 'b836d2082ed3d432a185d1f496d3499eeff581099d0e85028b193bc4943ef6cd',
 INPUT+'stage9_family_consolidation.json': 'b0e9e3b9aeb64a4ee886054bee702533b835cddf9b880f6ec6ea8fc2649aade5',
 'results/b6/stage9_freeze/stage8_input_audit.json': '14624ffb3243f3f48a107bf8a139da780820d2699e207c37a3432f9a17dd2f47'}


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def load_config():
    c=read(ROOT/INPUT/'stage10_config.json')
    require(c['Risks']==['0.25','1.0','1.5','2.0'] and c['PortfolioConfigs']=={k:list(v) for k,v in CONFIGS.items()},'fixed configurations/risks mismatch')
    require(c['MoneyModes']=={k:{'Start':v[0],'Periods':list(v[1])} for k,v in MODES.items()},'fixed modes mismatch')
    require(c['GlobalR2Applied'] is False and c['RiskPolicy']=='SAME_FIXED_PER_TRADE_RISK_ALL_COMPONENTS','user-fixed risk policy mismatch')
    for name,h in c['InputArtifactSHA256'].items(): require(sha(ROOT/name)==h,'input hash mismatch: '+name)
    return c
