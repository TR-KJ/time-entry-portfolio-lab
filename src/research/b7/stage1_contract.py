"""Immutable research contract plus deterministic implementation encodings."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
CONDITIONS_SHA = '5dbac7af2d41aa912308868e6ad1a6dbf7cdd107'
FROZEN = {
 'docs/b7/full_research_conditions_freeze.md': 'e4cc4f594ca5b350cdc2fdcace5930d17a856779fa2d7461df31d9e288330823',
 'research_inputs/b7/full_research_prespec.json': 'd096117239ad5acf9fdfbd1092056c9eb625feffbba2cc659ea33f4566537cea',
 'docs/b7/stage1_conditions_freeze.md': 'cdcacd33a47983520188ed9581477996d56ef5d3d7703b74aea0108c7f2176e3',
 'research_inputs/b7/stage1_prespec.json': '1449bfe9e9fc066ce4a59cc156e8247cc67e11522d9cdfb007cafefaf69d05e5',
}

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)

def object_hash(obj): return hashlib.sha256(canonical(obj).encode()).hexdigest()

def verify_conditions(root=ROOT):
    for name, expected in FROZEN.items():
        if digest(root / name) != expected: raise ValueError('Frozen condition identity mismatch: ' + name)
    return json.loads((root / 'research_inputs/b7/full_research_prespec.json').read_text())

PRESPEC = verify_conditions()
SYMBOLS = tuple(sorted(PRESPEC['P01']['SLGridPips']))
SL = PRESPEC['P01']['SLGridPips']
SPREAD = PRESPEC['InheritedEnvironmentAndExecution']['SpreadsPips']
PIPS = PRESPEC['InheritedEnvironmentAndExecution']['PipSize']
WEEKDAYS = ('MON', 'TUE', 'WED', 'THU', 'FRI')
YEARS = (2020, 2021, 2022, 2023)

@dataclass(frozen=True)
class Structure:
    symbol: str
    direction: str
    weekday: int
    entry: int
    holding: int

    def __post_init__(self):
        if self.symbol not in SYMBOLS or self.direction not in ('LONG', 'SHORT'): raise ValueError('symbol/direction')
        if self.weekday not in range(5): raise ValueError('weekday')
        if self.entry not in range(0, 1440, 5) or self.holding not in range(30, 1441, 5): raise ValueError('Stage1 grid')

    @property
    def offset(self): return (self.entry + self.holding) // 1440
    @property
    def exit(self): return (self.entry + self.holding) % 1440
    @property
    def candidate_id(self):
        return f'B7S1:{self.symbol}:{self.direction}:{WEEKDAYS[self.weekday]}:E{self.entry:04d}:D{self.offset}:X{self.exit:04d}:H{self.holding:04d}'
    @property
    def key(self):
        return (self.symbol, int(self.direction == 'SHORT'), self.weekday, self.entry, self.offset, self.exit, self.holding, self.candidate_id)
    def definition(self):
        return dict(CandidateID=self.candidate_id, Symbol=self.symbol, Direction=self.direction, Weekday=self.weekday,
                    EntryMinute=self.entry, ExitMinute=self.exit, ExitDayOffset=self.offset, HoldingMinutes=self.holding, FixedKey=list(self.key))
    @classmethod
    def from_id(cls, cid):
        v = cid.split(':')
        if len(v) != 8 or v[0] != 'B7S1': raise ValueError('CandidateID')
        s = cls(v[1], v[2], WEEKDAYS.index(v[3]), int(v[4][1:]), int(v[7][1:]))
        if s.candidate_id != cid: raise ValueError('noncanonical CandidateID')
        return s
    @classmethod
    def from_record(cls, d): return cls.from_id(d['CandidateID'])

@dataclass(frozen=True)
class Job:
    symbol: str
    direction: str
    weekday: int
    @property
    def job_id(self): return f'{self.symbol}_{self.direction}_{WEEKDAYS[self.weekday]}'
    def structures(self):
        for e in range(0, 1440, 5):
            for h in range(30, 1441, 5): yield Structure(self.symbol, self.direction, self.weekday, e, h)

def jobs(): return tuple(Job(s, d, w) for s in SYMBOLS for d in ('LONG', 'SHORT') for w in range(5))
