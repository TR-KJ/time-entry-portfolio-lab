"""Frozen R2 overlay, three portfolios and two capital modes only."""
from decimal import Decimal as D
from .stage10_config import ROOT, INPUT, AJ, GJ, MODES, PERIODS, sha, read, require
STAGE10_SHA='0b8a8507b5021baeded4fcfc5fb3f1ce1644cc7d'
PHASE5_SHA='5e93a8834e27d4d9ffdbc2980906511f74ddb27a'
SOURCE_HASHES={'src/EA/phase5_demo/vol_r2_core.mqh':'28fc8fca8f8ac4bab01101f5812dfe40fb4ba7a0d9c0eff7148692fe2e1754bf',
 'src/research/volatility_phase5_audit.py':'68d385daa8bf6239a120c88bd26d151ec91842a212549aa7af9e4f97ebf98702',
 'docs/63_volatility_phase5_plan.md':'37d89f9ec2f63cd499d393360b0a7d78488c90ff19e1524ebbcb4e5a922ec75d'}
MANIFEST_SHA='8a149ea43feecc1e007bb210c96164b868a4cc417d621bac9575b69787f4f78f'
RISK={k:D(v) for k,v in zip(('Q1','Q2','Q3','Q4','Q5','FALLBACK'),('.50','.70','.90','1.10','1.30','.90'))}
CONFIGS={'R0_CURRENT_R2':(), 'R1_CURRENT_R2_PLUS_GJ':(GJ,), 'R2_CURRENT_R2_PLUS_GJ_AJ':(GJ,AJ)}
COMPARISONS={'GJ_INCREMENTAL':(1,0),'AJ_CONDITIONAL_INCREMENTAL':(2,1),'TOTAL_B6_INCREMENTAL':(2,0)}
STATE='COMPLETE_STAGE11_R2_INCREMENTAL_PORTFOLIO_ONLY'
OUTPUT='results/b6/stage11_freeze/'

def load_config():
    c=read(ROOT/INPUT/'stage11_config.json')
    require(c['Stage10CodeSHA']==STAGE10_SHA,'Stage10 identity changed')
    require(c['PortfolioConfigs']=={k:list(v) for k,v in CONFIGS.items()},'three frozen portfolios required')
    require(c['MoneyModes']=={k:dict(Start=v[0],Periods=list(v[1])) for k,v in MODES.items()},'two frozen money modes required')
    require(c['RiskTable']=={k:str(v) for k,v in RISK.items()},'absolute R2 table changed')
    require(c['GlobalR2Applied'] is True and c['R2TradeFilter'] is False,'overlay required')
    for k in ('AJOnlyConfigurationExists','FixedRiskFallbackResearch','LiveEnabled','StrategyNumberingEnabled'):require(c[k] is False,'forbidden scope: '+k)
    for n,h in c['InputArtifactSHA256'].items():require(sha(ROOT/n)==h,'frozen input changed: '+n)
    return c
