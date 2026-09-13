"""Colab: generate the frozen 28-strategy baseline trade log (Daily Stop excluded).

This research-only program does not import or modify EA/live-operation code.
It prints notebook summaries and writes equivalent CSV artifacts to /content.
"""

from __future__ import annotations

import ast
import hashlib
import urllib.request
from calendar import monthrange
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from google.colab import drive
except ImportError:  # permits local validation/import without Colab
    drive = None


BASELINE_VERSION = "daily-stop-baseline-v1.0.1"
SOURCE_COMMIT = "173be2a114dad6bd183a0a1515581528850f0850"
CALENDAR_SOURCE_URL = (
    "https://raw.githubusercontent.com/TR-KJ/time-entry-portfolio-lab/"
    f"{SOURCE_COMMIT}/src/portfolio_backtest_v1_2_add_aussie_logic.py"
)
DRIVE_ROOT = Path("/content/drive/MyDrive")
OUTPUT_DIR = Path("/content")
DATA_ROOT_HINT = "ゆうのすけさん2025"
MAX_EXIT_DELAY_MINUTES = 4

PIP_SIZE = {"EJ": 0.01, "GJ": 0.01, "AJ": 0.01, "UJ": 0.01,
            "EA": 0.0001, "GA": 0.0001, "AU": 0.0001}
SPREAD_PIPS = {"EJ": 1.0, "GJ": 2.0, "AJ": 1.5, "UJ": 0.5,
               "EA": 1.5, "GA": 2.0, "AU": 1.5}
SYMBOL_TO_PAIR = {
    "EURJPY": "EJ", "GBPJPY": "GJ", "AUDJPY": "AJ", "USDJPY": "UJ",
    "EURAUD": "EA", "GBPAUD": "GA", "AUDUSD": "AU",
}

# Explicit audited manifest. Recursive lookup is allowed only for these exact names.
MANIFEST_NAMES = {
    "USDJPY": ["USDJPY_M1_201501020900_201612302359.csv", "USDJPY_M1_201701020001_201812282357.csv", "USDJPY_M1_201901020600_202012310000.csv", "USDJPY_M1_202101040002_202212302355.csv", "USDJPY_M1_202301020700_202412310000.csv", "USDJPY_M1_202501010000_202512302358.csv", "USDJPY_M1_202601020001_202603310000.csv", "USDJPY_M1_202604010000_202609090000_RECHECK.csv"],
    "EURJPY": ["EURJPY_M1_201501020900_201612302359.csv", "EURJPY_M1_201701020003_201812282357.csv", "EURJPY_M1_201901020600_202012310000.csv", "EURJPY_M1_202101040002_202212302355.csv", "EURJPY_M1_202301020701_202412310000.csv", "EURJPY_M1_202501010000_202512310000.csv", "EURJPY_M1_202601020000_202603310000.csv", "EURJPY_M1_202604010000_202609090000_RECHECK.csv"],
    "GBPJPY": ["GBPJPY_M1_201501020900_201612302359.csv", "GBPJPY_M1_201701020004_201812282357.csv", "GBPJPY_M1_201901020600_202012310000.csv", "GBPJPY_M1_202101040002_202212302355.csv", "GBPJPY_M1_202301020700_202412302359.csv", "GBPJPY_M1_202501020001_202512310000.csv", "GBPJPY_M1_202601020001_202603310000.csv", "GBPJPY_M1_202604010000_202609090000_RECHECK.csv"],
    "AUDJPY": ["AUDJPY_M1_201501020900_201612302359.csv", "AUDJPY_M1_201701020002_201812282357.csv", "AUDJPY_M1_201901020600_202012310000.csv", "AUDJPY_M1_202101040002_202212302355.csv", "AUDJPY_M1_202301020702_202412310000.csv", "AUDJPY_M1_202501020000_202512310000.csv", "AUDJPY_M1_202601020001_202603310000.csv", "AUDJPY_M1_202604010001_202609090000_RECHECK.csv"],
    "AUDUSD": ["AUDUSD_M1_201501020900_201612302359.csv", "AUDUSD_M1_201701020001_201812282357.csv", "AUDUSD_M1_201901020600_202012310000.csv", "AUDUSD_M1_202101040002_202212302355.csv", "AUDUSD_M1_202301020706_202412310000.csv", "AUDUSD_M1_202501010000_202512310000.csv", "AUDUSD_M1_202601020001_202603310000.csv", "AUDUSD_M1_202604010000_202609090000_RECHECK.csv"],
    "EURAUD": ["EURAUD_M1_201501020900_201612302359.csv", "EURAUD_M1_201701020002_201812282357.csv", "EURAUD_M1_201901020600_202012310000.csv", "EURAUD_M1_202101040002_202212302354.csv", "EURAUD_M1_202301020708_202412310000.csv", "EURAUD_M1_202501010000_202512310000.csv", "EURAUD_M1_202601020000_202603310000.csv", "EURAUD_M1_202604010000_202609090000_RECHECK.csv"],
    "GBPAUD": ["GBPAUD_M1_201501020900_201612302359.csv", "GBPAUD_M1_201701020002_201812282357.csv", "GBPAUD_M1_201901020629_202012310000_RECHECK.csv", "GBPAUD_M1_202101040002_202212302355.csv", "GBPAUD_M1_202301020717_202412310000.csv", "GBPAUD_M1_202501020001_202512310000.csv", "GBPAUD_M1_202601020000_202603310000.csv", "GBPAUD_M1_202604010000_202609090000.csv"],
}

KNOWN_GBPAUD_GAP_CANDIDATES = {
    ("21_GA_B_3", pd.Timestamp("2019-01-07 21:02")),
    ("28_GA_China_Demand", pd.Timestamp("2019-05-09 10:00")),
    ("22_GA_C_2", pd.Timestamp("2019-05-09 16:56")),
}


@dataclass(frozen=True)
class Strategy:
    no: int
    name: str
    pair: str
    long: bool
    weekdays: tuple[int, ...]
    entry: tuple[int, int]
    exit: tuple[int, int]
    exit_day_offset: int
    sl: float
    tp: float | None
    date_rule: str = "weekday"


STRATEGIES = [
    Strategy(1, "1_EJ_Log1", "EJ", True, (0, 2), (13, 55), (4, 55), 1, 70, 250),
    Strategy(2, "2_EJ_NightBlitz_20", "EJ", True, (0, 2), (20, 56), (4, 45), 1, 45, 70),
    Strategy(3, "3_EJ_NightBlitz_21", "EJ", True, (0, 2), (21, 56), (5, 27), 1, 75, 70),
    Strategy(4, "4_GJ_Port_Log1", "GJ", True, (1, 2), (0, 0), (8, 55), 0, 130, 90),
    Strategy(5, "5_GJ_Port_Log2", "GJ", False, (1, 3, 4), (9, 55), (23, 55), 0, 90, None),
    Strategy(6, "6_GJ_Old_Mon", "GJ", True, (0,), (15, 45), (22, 50), 0, 50, 210),
    Strategy(7, "7_GJ_Mon_Blitz", "GJ", True, (0,), (18, 2), (23, 2), 0, 130, 250),
    Strategy(8, "8_AJ_Core1", "AJ", True, (0,), (8, 1), (22, 46), 0, 70, 110),
    Strategy(9, "9_AJ_Core2", "AJ", False, (3,), (17, 14), (1, 14), 1, 30, 80),
    Strategy(10, "10_AJ_SatA", "AJ", False, (4,), (10, 58), (13, 51), 0, 50, 25),
    Strategy(11, "11_AJ_SatB", "AJ", False, (4,), (18, 57), (1, 43), 1, 55, 95),
    Strategy(12, "12_UJ_Short_Core", "UJ", False, (), (9, 55), (14, 56), 0, 20, 50, "uj12"),
    Strategy(13, "13_UJ_Fix_MidWeek", "UJ", True, (), (18, 4), (22, 3), 0, 95, 95, "uj13"),
    Strategy(14, "14_UJ_Sat_3rd", "UJ", False, (), (20, 1), (3, 8), 1, 45, 70, "uj14"),
    Strategy(15, "15_UJ_Sat_Aug", "UJ", False, (), (19, 0), (23, 30), 0, 20, 35, "uj15"),
    Strategy(16, "16_UJ_T10A", "UJ", True, (), (2, 58), (9, 50), 0, 45, 110, "uj16"),
    Strategy(17, "17_EA_1B_Wed_Short", "EA", False, (2,), (9, 59), (20, 58), 0, 70, 175),
    Strategy(18, "18_EA_2_MonWed_Short", "EA", False, (0, 1, 2), (9, 59), (5, 26), 1, 90, 180),
    Strategy(19, "19_EA_3_WedThu_Long", "EA", True, (2, 3), (20, 56), (10, 0), 1, 90, None),
    Strategy(20, "20_EA_1A_MonTue_Short", "EA", False, (0, 1), (10, 1), (16, 0), 0, 50, 125),
    Strategy(21, "21_GA_B_3", "GA", True, (0,), (21, 2), (10, 0), 1, 220, 100),
    Strategy(22, "22_GA_C_2", "GA", True, (3,), (16, 56), (1, 15), 1, 70, 80),
    Strategy(23, "23_GA_F_2", "GA", False, (4,), (19, 42), (22, 45), 0, 90, 200),
    Strategy(24, "24_GA_D_1", "GA", True, (4,), (22, 44), (3, 8), 1, 90, 200),
    Strategy(25, "25_AU_China_Demand", "AU", True, (), (10, 0), (15, 50), 0, 40, 40, "china_au"),
    Strategy(26, "26_AJ_China_Demand", "AJ", True, (), (10, 0), (15, 50), 0, 45, 80, "china_9_15"),
    Strategy(27, "27_EA_China_Demand", "EA", False, (), (10, 0), (15, 50), 0, 60, 60, "china_9_15"),
    Strategy(28, "28_GA_China_Demand", "GA", False, (), (10, 0), (16, 10), 0, 75, 70, "china_9_15"),
]

# Candidate C, followed by the adopted EJ1 overlap correction.
# A=all-day, O=planned-position overlap, S=special date rule, -=not applicable.
EVENTS = ("US_NFP", "US_CPI", "FOMC", "BOJ", "BOE", "ECB", "RBA", "AUD_CPI")
MATRIX_ROWS = {
    1:  ("O", "S", "O", "O", "-", "O", "-", "-"),
    2:  ("A", "A", "O", "A", "-", "A", "-", "-"),
    3:  ("A", "A", "O", "A", "-", "A", "-", "-"),
    4:  ("-", "-", "-", "-", "-", "-", "-", "-"),
    5:  ("A", "A", "O", "A", "O", "-", "-", "-"),
    6:  ("A", "A", "O", "A", "O", "-", "-", "-"),
    7:  ("A", "A", "A", "A", "A", "-", "-", "-"),
    8:  ("A", "A", "O", "A", "-", "-", "O", "O"),
    9:  ("A", "A", "O", "A", "-", "-", "O", "O"),
    10: ("A", "A", "A", "A", "-", "-", "A", "A"),
    11: ("A", "A", "A", "A", "-", "-", "A", "A"),
    12: ("A", "A", "O", "A", "-", "-", "-", "-"),
    13: ("A", "A", "O", "A", "-", "-", "-", "-"),
    14: ("A", "A", "O", "A", "-", "-", "-", "-"),
    15: ("A", "A", "O", "A", "-", "-", "-", "-"),
    16: ("-", "-", "-", "A", "-", "-", "-", "-"),
    17: ("A", "A", "O", "-", "-", "O", "O", "O"),
    18: ("A", "A", "O", "-", "-", "O", "O", "O"),
    19: ("A", "A", "O", "-", "-", "O", "O", "O"),
    20: ("A", "A", "O", "-", "-", "O", "O", "O"),
    21: ("A", "A", "O", "-", "O", "-", "O", "O"),
    22: ("A", "A", "O", "-", "O", "-", "O", "O"),
    23: ("A", "A", "O", "-", "O", "-", "O", "O"),
    24: ("A", "A", "O", "-", "O", "-", "O", "O"),
    25: ("-", "-", "O", "-", "-", "-", "O", "O"),
    26: ("-", "-", "-", "A", "-", "-", "O", "O"),
    27: ("-", "-", "O", "-", "-", "O", "O", "O"),
    28: ("-", "-", "O", "-", "O", "-", "O", "O"),
}
EVENT_POLICY = {n: dict(zip(EVENTS, MATRIX_ROWS[n])) for n in MATRIX_ROWS}
EVENT_CLOCK = {
    "FOMC": (3, 0, 180, 180), "US_NFP": (21, 30, 120, 120),
    "US_CPI": (21, 30, 120, 120), "BOJ": (12, 0, 180, 180),
    "BOE": (21, 0, 120, 120), "ECB": (21, 15, 120, 120),
    "RBA": (13, 30, 120, 120), "AUD_CPI": (10, 30, 120, 120),
}
# The frozen FOMC list is keyed by the US announcement date. Its fixed 03:00
# research timestamp is the following JST calendar day (as documented by the
# 2026-07-29 US date -> 2026-07-30 03:00 JST test case).
EVENT_JST_DAY_OFFSET = {event: (1 if event == "FOMC" else 0) for event in EVENTS}


def load_frozen_event_calendar() -> dict[str, set[pd.Timestamp]]:
    """Extract only literal date lists from the pinned historical Python source."""
    with urllib.request.urlopen(CALENDAR_SOURCE_URL, timeout=60) as response:
        source = response.read().decode("utf-8")
    tree = ast.parse(source)
    wanted = {
        "US_NFP_DATES": "US_NFP", "US_CPI_DATES": "US_CPI", "FOMC_DATES": "FOMC",
        "BOJ_DATES": "BOJ", "BOE_DATES": "BOE", "ECB_DATES": "ECB",
        "RBA_DATES": "RBA", "AUD_CPI_DATES": "AUD_CPI",
    }
    collected: dict[str, list[str]] = {v: [] for v in wanted.values()}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in wanted and isinstance(node.value, ast.List):
            collected[wanted[target.id]].extend(ast.literal_eval(node.value))
        # The pinned source separately defines *_2026_DATES before concatenating.
        if isinstance(target, ast.Name) and target.id.endswith("_2026_DATES") and isinstance(node.value, ast.List):
            base = target.id.replace("_2026_DATES", "_DATES")
            if base in wanted:
                collected[wanted[base]].extend(ast.literal_eval(node.value))
    result = {event: {pd.Timestamp(d).normalize() for d in dates} for event, dates in collected.items()}
    if any(not result[e] for e in EVENTS):
        raise RuntimeError("Frozen event calendar extraction failed")
    return result


def is_year_end(dt: pd.Timestamp) -> bool:
    return (dt.month == 12 and dt.day >= 25) or (dt.month == 1 and dt.day <= 3)


def last_business_days(dt: pd.Timestamp, n: int = 3) -> set[int]:
    days = []
    for day in range(monthrange(dt.year, dt.month)[1], 0, -1):
        if pd.Timestamp(dt.year, dt.month, day).weekday() < 5:
            days.append(day)
        if len(days) == n:
            break
    return set(days)


def is_forward_gotobi(dt: pd.Timestamp) -> bool:
    if dt.weekday() != 4:
        return False
    return any((dt + pd.Timedelta(days=k)).day in (25, 30) for k in (1, 2))


def eligible_date(s: Strategy, dt: pd.Timestamp) -> bool:
    if s.date_rule == "weekday":
        return dt.weekday() in s.weekdays
    if s.date_rule == "uj12":
        return dt.day >= 20 and dt.day not in (21, 22) and dt.month != 8 and dt.weekday() != 2 and not dt.is_month_end
    if s.date_rule == "uj13":
        return dt.day >= 25 and dt.weekday() in (2, 3)
    if s.date_rule == "uj14":
        return dt.day == 3
    if s.date_rule == "uj15":
        return dt.month == 8 and dt.day <= 10
    if s.date_rule == "uj16":
        return dt.day == 10 and dt.weekday() != 2
    if s.date_rule == "china_au":
        return dt.weekday() < 5 and (9 <= dt.day <= 15 or dt.day >= 25)
    if s.date_rule == "china_9_15":
        return dt.weekday() < 5 and 9 <= dt.day <= 15
    raise ValueError(s.date_rule)


def individual_stop(s: Strategy, dt: pd.Timestamp, calendars: dict[str, set[pd.Timestamp]]) -> str | None:
    if is_year_end(dt): return "YEAR_END_STOP"
    if s.no == 1 and (dt.month == 2 or dt.day == 1): return "EJ1_INDIVIDUAL_STOP"
    if s.no == 1:
        cpi_weds = {d - pd.Timedelta(days=d.weekday()) + pd.Timedelta(days=2) for d in calendars["US_CPI"]}
        if dt in cpi_weds: return "US_CPI_WEEK_WED"
    if s.no == 4 and (dt.month == 12 or dt.day in (1, 2, 29, 30, 31)): return "GJ4_INDIVIDUAL_STOP"
    if s.no == 5 and dt.day in (18, 19, 27): return "GJ5_INDIVIDUAL_STOP"
    if s.no == 6 and dt.month in (1, 2): return "GJ6_INDIVIDUAL_STOP"
    if s.no == 9 and (dt.month in (6, 9) or dt.day in (1, 20) or dt.day >= 26): return "AJ9_INDIVIDUAL_STOP"
    if s.no in (17, 20) and dt.month == 8: return "EA_MONTH_STOP"
    if s.no == 18 and dt.month in (1, 8): return "EA_MONTH_STOP"
    if 17 <= s.no <= 20 and (dt.month == 10 or dt.day in last_business_days(dt)): return "EA_REV4_STOP"
    if s.no == 25 and dt.month in (8, 10): return "CHINA_MONTH_STOP"
    if s.no == 26 and dt.month in (2, 8, 10): return "CHINA_MONTH_STOP"
    if s.no in (27, 28) and dt.month in (8, 10): return "CHINA_MONTH_STOP"
    return None


def event_stop(s: Strategy, entry: pd.Timestamp, planned_exit: pd.Timestamp,
               calendars: dict[str, set[pd.Timestamp]]) -> str | None:
    policy = EVENT_POLICY[s.no]
    entry_date = entry.normalize()
    for event in EVENTS:
        mode = policy[event]
        if mode in ("-", "S"):
            continue
        if mode == "A" and entry_date in calendars[event]:
            return f"CANDIDATE_C_DATE_{event}"
        if mode == "O":
            hour, minute, pre, post = EVENT_CLOCK[event]
            # Check every calendar date touched by the planned position plus one day either side.
            dates = pd.date_range(entry_date - pd.Timedelta(days=1), planned_exit.normalize() + pd.Timedelta(days=1), freq="D")
            for event_date in dates:
                if event_date.normalize() not in calendars[event]:
                    continue
                event_time = event_date + pd.Timedelta(
                    days=EVENT_JST_DAY_OFFSET[event], hours=hour, minutes=minute
                )
                window_start = event_time - pd.Timedelta(minutes=pre)
                window_end = event_time + pd.Timedelta(minutes=post)
                if entry <= window_end and planned_exit >= window_start:
                    return f"CANDIDATE_C_OVERLAP_{event}"
    return None


def resolve_manifest() -> tuple[dict[str, list[Path]], pd.DataFrame]:
    rows, resolved = [], {}
    for symbol, names in MANIFEST_NAMES.items():
        resolved[symbol] = []
        for name in names:
            hits = list(DRIVE_ROOT.rglob(name))
            if len(hits) != 1:
                raise RuntimeError(f"{symbol}: expected exactly one {name}, found {len(hits)}")
            path = hits[0]
            resolved[symbol].append(path)
            rows.append({"Symbol": symbol, "Filename": name, "Path": str(path), "Bytes": path.stat().st_size})
    return resolved, pd.DataFrame(rows)


def read_mt5_file(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t")
    normalized = {str(c).strip().strip("<>").upper(): c for c in df.columns}
    needed = ("DATE", "TIME", "OPEN", "HIGH", "LOW", "CLOSE")
    missing = [c for c in needed if c not in normalized]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")
    out = pd.DataFrame({
        "RawDatetime": pd.to_datetime(df[normalized["DATE"]].astype(str).str.strip() + " " + df[normalized["TIME"]].astype(str).str.strip(), errors="coerce"),
        **{c.title(): pd.to_numeric(df[normalized[c]], errors="coerce") for c in ("OPEN", "HIGH", "LOW", "CLOSE")},
    })
    if out.isna().any().any():
        raise ValueError(f"{path.name}: datetime/OHLC parse failure")
    return out


def load_pair(paths: list[Path], symbol: str) -> pd.DataFrame:
    df = pd.concat((read_mt5_file(p) for p in paths), ignore_index=True)
    raw = df["RawDatetime"].dt.tz_localize("Europe/Helsinki", ambiguous="infer", nonexistent="shift_forward")
    df["Datetime"] = raw.dt.tz_convert("Asia/Tokyo").dt.tz_localize(None)
    if df["Datetime"].duplicated().any():
        raise ValueError(f"{symbol}: duplicate JST timestamps")
    if (df["High"] < df[["Open", "Low", "Close"]].max(axis=1)).any():
        raise ValueError(f"{symbol}: invalid High")
    if (df["Low"] > df[["Open", "High", "Close"]].min(axis=1)).any():
        raise ValueError(f"{symbol}: invalid Low")
    df = df.sort_values("Datetime").set_index("Datetime", verify_integrity=True)
    print(f"Loaded {symbol}: {len(df):,} rows | {df.index.min()} -> {df.index.max()} JST")
    return df


def period_label(entry: pd.Timestamp) -> str:
    if entry < pd.Timestamp("2022-01-01"): return "IS"
    if entry < pd.Timestamp("2026-01-01"): return "OOS1"
    return "OOS2"


def run_strategy(s: Strategy, bars: pd.DataFrame, calendars: dict[str, set[pd.Timestamp]], diagnostics: list[dict]) -> list[dict]:
    trades = []
    # Walk every calendar date in the covered range, including dates with no
    # bars at all. This makes complete-day data gaps visible in diagnostics;
    # missing entry bars still generate no trade, preserving baseline behavior.
    dates = pd.date_range(bars.index.min().normalize(), bars.index.max().normalize(), freq="D")
    for dt in dates:
        if not eligible_date(s, dt):
            continue
        entry_h, entry_m = s.entry
        sl, tp, mode = s.sl, s.tp, "STANDARD"
        if s.no == 12:
            goto = dt.day in (20, 25, 30) or is_forward_gotobi(dt)
            if goto:
                entry_h, entry_m, sl, tp, mode = 9, 55, 20, 50, "GOTO"
            else:
                entry_h, entry_m, sl, tp, mode = 8, 4, 50, None, "NORMAL"
        entry = dt + pd.Timedelta(hours=entry_h, minutes=entry_m)
        planned_exit = dt + pd.Timedelta(days=s.exit_day_offset, hours=s.exit[0], minutes=s.exit[1])
        reason = individual_stop(s, dt, calendars) or event_stop(s, entry, planned_exit, calendars)
        if reason:
            diagnostics.append({"Strategy": s.name, "ScheduledEntry": entry, "Type": "FILTERED", "Reason": reason})
            continue
        if entry not in bars.index:
            diagnostics.append({"Strategy": s.name, "ScheduledEntry": entry, "Type": "MISSING_ENTRY", "Reason": "exact M1 entry bar absent"})
            continue
        exit_time = next((planned_exit + pd.Timedelta(minutes=k) for k in range(MAX_EXIT_DELAY_MINUTES + 1)
                          if planned_exit + pd.Timedelta(minutes=k) in bars.index), None)
        if exit_time is None:
            diagnostics.append({"Strategy": s.name, "ScheduledEntry": entry, "Type": "MISSING_EXIT", "Reason": "scheduled through +4m absent"})
            continue
        if entry >= exit_time:
            diagnostics.append({"Strategy": s.name, "ScheduledEntry": entry, "Type": "INVALID_WINDOW", "Reason": "entry >= exit"})
            continue
        pip, spread = PIP_SIZE[s.pair], SPREAD_PIPS[s.pair]
        raw_open = float(bars.at[entry, "Open"])
        entry_price = raw_open + spread * pip if s.long else raw_open - spread * pip
        sl_price = entry_price - sl * pip if s.long else entry_price + sl * pip
        tp_price = None if tp is None else (entry_price + tp * pip if s.long else entry_price - tp * pip)
        close_time, close_price, pips, exit_reason = exit_time, float(bars.at[exit_time, "Open"]), None, "TimeExit"
        # Inclusive entry and exit bars; SL is checked before TP on every bar.
        window = bars.loc[entry:exit_time]
        for ts, row in window.iterrows():
            if (s.long and row["Low"] <= sl_price) or (not s.long and row["High"] >= sl_price):
                close_time, close_price, pips, exit_reason = ts, sl_price, -sl, "SL"
                break
            if tp_price is not None and ((s.long and row["High"] >= tp_price) or (not s.long and row["Low"] <= tp_price)):
                close_time, close_price, pips, exit_reason = ts, tp_price, tp, "TP"
                break
        if pips is None:
            pips = (close_price - entry_price) / pip if s.long else (entry_price - close_price) / pip
        trades.append({
            "StrategyNo": s.no, "Strategy": s.name, "Pair": s.pair,
            "Direction": "Long" if s.long else "Short", "Mode": mode,
            "EntryTime": entry, "ScheduledExitTime": planned_exit, "CloseTime": pd.Timestamp(close_time),
            "ExitDelayMinutes": int((exit_time - planned_exit).total_seconds() / 60),
            "RawEntryOpen": raw_open, "EntryPrice": entry_price, "ClosePrice": close_price,
            "SL": float(sl), "TP": np.nan if tp is None else float(tp), "Pips": round(float(pips), 6),
            "R": round(float(pips / sl), 9), "ExitReason": exit_reason,
            "PipSize": pip, "SpreadPips": spread, "Period": period_label(entry),
        })
    return trades


def summarize(group: pd.DataFrame, label: str) -> dict:
    ordered = group.sort_values(["CloseTime", "EntryTime", "StrategyNo"]).copy()
    equity = ordered["R"].cumsum()
    drawdown = equity.cummax().clip(lower=0) - equity
    gains, losses = ordered.loc[ordered.R > 0, "R"].sum(), -ordered.loc[ordered.R < 0, "R"].sum()
    return {
        "Segment": label, "Trades": len(ordered), "Wins": int((ordered.R > 0).sum()),
        "WinRatePct": round(float((ordered.R > 0).mean() * 100), 3) if len(ordered) else np.nan,
        "TotalR": round(float(ordered.R.sum()), 6),
        "PF": round(float(gains / losses), 6) if losses else np.nan,
        "MaxDDR": round(float(drawdown.max()), 6) if len(drawdown) else 0.0,
        "AvgR": round(float(ordered.R.mean()), 9) if len(ordered) else np.nan,
    }


def canonical_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S").encode("utf-8")


def main() -> None:
    if len(STRATEGIES) != 28 or sorted(s.no for s in STRATEGIES) != list(range(1, 29)):
        raise RuntimeError("Strategy freeze failed: expected exactly strategy numbers 1..28")
    if drive is not None:
        drive.mount("/content/drive")
    calendars = load_frozen_event_calendar()
    manifest, manifest_df = resolve_manifest()
    diagnostics: list[dict] = []
    all_trades: list[dict] = []
    for symbol, paths in manifest.items():
        bars = load_pair(paths, symbol)
        pair = SYMBOL_TO_PAIR[symbol]
        for strategy in (s for s in STRATEGIES if s.pair == pair):
            all_trades.extend(run_strategy(strategy, bars, calendars, diagnostics))
        del bars
    trades = pd.DataFrame(all_trades).sort_values(["EntryTime", "StrategyNo", "CloseTime"]).reset_index(drop=True)
    if trades.empty:
        raise RuntimeError("No baseline trades generated")
    if not np.allclose(trades["R"], trades["Pips"] / trades["SL"], atol=1e-8):
        raise AssertionError("R invariant failed")
    if not np.allclose(trades.loc[trades.ExitReason == "SL", "R"], -1.0, atol=1e-8):
        raise AssertionError("SL must equal -1R")
    summary = pd.DataFrame([summarize(trades, "FULL")] + [summarize(g, p) for p, g in trades.groupby("Period", sort=False)])
    yearly = pd.DataFrame([summarize(g, str(y)) for y, g in trades.groupby(trades.EntryTime.dt.year, sort=True)])
    strategy_summary = pd.DataFrame([summarize(g, name) for name, g in trades.groupby("Strategy", sort=False)])
    diagnostics_df = pd.DataFrame(diagnostics).sort_values(["ScheduledEntry", "Strategy"]).reset_index(drop=True)
    observed_gap_candidates = {
        (row.Strategy, pd.Timestamp(row.ScheduledEntry))
        for row in diagnostics_df.itertuples()
        if row.Type == "MISSING_ENTRY"
    }
    missing_gap_diagnostics = KNOWN_GBPAUD_GAP_CANDIDATES - observed_gap_candidates
    if missing_gap_diagnostics:
        raise AssertionError(
            "Known GBPAUD gap candidates absent from diagnostics: "
            f"{sorted(missing_gap_diagnostics, key=lambda item: item[1])}"
        )
    trade_bytes = canonical_csv_bytes(trades)
    trade_hash = hashlib.sha256(trade_bytes).hexdigest()
    metadata = pd.DataFrame([{
        "BaselineVersion": BASELINE_VERSION, "GeneratedAtUTC": pd.Timestamp.now(tz="UTC").isoformat(),
        "SourceCommit": SOURCE_COMMIT, "CalendarSourceURL": CALENDAR_SOURCE_URL,
        "TradeLogSHA256": trade_hash, "TradeRows": len(trades), "StrategyCount": 28,
        "DailyStopApplied": False, "ATRFilter": False, "EventCandidateC": True,
        "SameBarPolicy": "SL_FIRST", "MaxExitDelayMinutes": MAX_EXIT_DELAY_MINUTES,
        "PeriodBasis": "EntryTime_JST",
        "KnownGBPAUDGapCandidatesObserved": len(KNOWN_GBPAUD_GAP_CANDIDATES),
    }])
    outputs = {
        "daily_stop_baseline_trades.csv": trades,
        "daily_stop_baseline_summary.csv": summary,
        "daily_stop_baseline_yearly_summary.csv": yearly,
        "daily_stop_baseline_strategy_summary.csv": strategy_summary,
        "daily_stop_baseline_diagnostics.csv": diagnostics_df,
        "daily_stop_baseline_manifest.csv": manifest_df,
        "daily_stop_baseline_run_metadata.csv": metadata,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "daily_stop_baseline_trades.csv").write_bytes(trade_bytes)
    for filename, frame in outputs.items():
        if filename != "daily_stop_baseline_trades.csv":
            frame.to_csv(OUTPUT_DIR / filename, index=False)
    print("\n" + "=" * 110)
    print("FROZEN 28-STRATEGY BASELINE (DAILY STOP: OFF)")
    print("=" * 110)
    print(summary.to_string(index=False))
    print("\nYEARLY SUMMARY")
    print(yearly.to_string(index=False))
    print(f"\nTrade log SHA-256: {trade_hash}")
    print("\nCSV OUTPUTS")
    for filename in outputs:
        print(OUTPUT_DIR / filename)


if __name__ == "__main__":
    main()
