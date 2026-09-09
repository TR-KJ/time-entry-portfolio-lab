"""Colab: apply portfolio Daily Stop to the accepted frozen trade log.

This research-only program never reads M1 prices or recalculates baseline trades.
The default IS_SELECTION mode does not calculate or display OOS performance.
"""

from __future__ import annotations

import hashlib
import heapq
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from google.colab import drive
except ImportError:  # permits local import and temporal-rule self-tests
    drive = None


ANALYSIS_VERSION = "daily-stop-analysis-v1.0.0"
ACCEPTED_BASELINE_SHA256 = (
    "cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359"
)
EXPECTED_TRADE_ROWS = 16_298
EXPECTED_STRATEGY_COUNT = 28

# Experimental lock:
# 1. Run IS_SELECTION first and choose a robust zone using 2015-2021 only.
# 2. Commit that choice, then change MODE to FROZEN_REPORT and set one threshold.
# FROZEN_REPORT refuses to run until FROZEN_THRESHOLD_R is explicitly set.
MODE = "IS_SELECTION"  # IS_SELECTION or FROZEN_REPORT
FROZEN_THRESHOLD_R: float | None = None

# Coarse predeclared grid. Do not add a fine-grained value after seeing results.
CANDIDATE_THRESHOLDS_R = (-1.0, -1.5, -2.0, -2.5, -3.0, -4.0)

BASELINE_CANDIDATES = (
    Path(
        "/content/drive/MyDrive/time-entry-portfolio-lab/daily_stop/"
        "baseline_cc32f32e3df5/daily_stop_baseline_trades.csv"
    ),
    Path("/content/daily_stop_baseline_trades.csv"),
)
OUTPUT_DIR = Path("/content")

REQUIRED_COLUMNS = {
    "StrategyNo", "Strategy", "Pair", "EntryTime", "CloseTime",
    "SL", "Pips", "R", "ExitReason", "Period",
}
EXPECTED_BASELINE = {
    "FULL": {"Trades": 16_298, "Wins": 8_887, "TotalR": 1390.267649},
    "IS": {"Trades": 9_756, "Wins": 5_321, "TotalR": 768.488273},
    "OOS1": {"Trades": 5_547, "Wins": 3_054, "TotalR": 601.960585},
    "OOS2": {"Trades": 995, "Wins": 512, "TotalR": 19.818791},
}


def period_label(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2022-01-01"):
        return "IS"
    if ts < pd.Timestamp("2026-01-01"):
        return "OOS1"
    return "OOS2"


def resolve_baseline_path() -> Path:
    found = [path for path in BASELINE_CANDIDATES if path.is_file()]
    if not found:
        choices = "\n".join(str(path) for path in BASELINE_CANDIDATES)
        raise FileNotFoundError(
            "Accepted baseline trade log was not found. Expected one of:\n" + choices
        )
    # Prefer the permanent Drive copy. If both copies exist, both must be exact.
    for path in found:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != ACCEPTED_BASELINE_SHA256:
            raise RuntimeError(
                f"Baseline SHA-256 mismatch: {path}\n"
                f"expected={ACCEPTED_BASELINE_SHA256}\nactual={digest}"
            )
    return found[0]


def load_and_validate_baseline(path: Path) -> pd.DataFrame:
    raw_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if raw_hash != ACCEPTED_BASELINE_SHA256:
        raise RuntimeError("Baseline hash changed; analysis aborted")

    trades = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS - set(trades.columns))
    if missing:
        raise ValueError(f"Baseline columns missing: {missing}")
    if len(trades) != EXPECTED_TRADE_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_TRADE_ROWS:,} trades, found {len(trades):,}"
        )

    for column in ("EntryTime", "CloseTime"):
        trades[column] = pd.to_datetime(trades[column], errors="raise")
    for column in ("StrategyNo", "SL", "Pips", "R"):
        trades[column] = pd.to_numeric(trades[column], errors="raise")

    if trades[["StrategyNo", "SL", "Pips", "R"]].isna().any().any():
        raise AssertionError("Numeric baseline fields contain NaN")
    if not np.isfinite(trades[["SL", "Pips", "R"]].to_numpy()).all():
        raise AssertionError("Numeric baseline fields contain non-finite values")
    if (trades["CloseTime"] < trades["EntryTime"]).any():
        raise AssertionError("CloseTime precedes EntryTime")
    if trades.duplicated(["StrategyNo", "EntryTime"]).any():
        raise AssertionError("Duplicate StrategyNo + EntryTime rows")
    if sorted(trades["StrategyNo"].astype(int).unique()) != list(range(1, 29)):
        raise AssertionError("Expected exactly strategy numbers 1..28")
    if not np.allclose(trades["R"], trades["Pips"] / trades["SL"], atol=1e-8):
        raise AssertionError("R != Pips / SL")
    if not np.allclose(
        trades.loc[trades["ExitReason"] == "SL", "R"], -1.0, atol=1e-8
    ):
        raise AssertionError("SL rows must equal -1R")

    expected_period = trades["EntryTime"].map(period_label)
    if not expected_period.equals(trades["Period"].astype(str)):
        raise AssertionError("Period is not based on EntryTime JST")

    trades["StrategyNo"] = trades["StrategyNo"].astype(int)
    trades = trades.sort_values(
        ["EntryTime", "StrategyNo", "CloseTime"], kind="mergesort"
    ).reset_index(drop=True)
    verify_accepted_baseline_summary(trades)
    return trades


def equity_metrics(frame: pd.DataFrame, r_column: str = "R") -> dict:
    ordered = frame.sort_values(
        ["CloseTime", "EntryTime", "StrategyNo"], kind="mergesort"
    )
    values = ordered[r_column].astype(float)
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    equity = values.cumsum()
    drawdown = equity.cummax().clip(lower=0.0) - equity

    if len(ordered):
        close_day = ordered["CloseTime"].dt.normalize()
        daily = values.groupby(close_day).sum()
        close_week = ordered["CloseTime"].dt.to_period("W-SUN")
        weekly = values.groupby(close_week).sum()
        worst_day = float(daily.min())
        worst_week = float(weekly.min())
    else:
        worst_day = worst_week = 0.0

    return {
        "Trades": int(len(ordered)),
        "Wins": int((values > 0).sum()),
        "WinRatePct": round(float((values > 0).mean() * 100), 3)
        if len(values) else np.nan,
        "TotalR": round(float(values.sum()), 6),
        "PF": round(gains / losses, 6) if losses else np.nan,
        "MaxDDR": round(float(drawdown.max()), 6) if len(drawdown) else 0.0,
        "AvgR": round(float(values.mean()), 9) if len(values) else np.nan,
        "WorstDayR": round(worst_day, 6),
        "WorstWeekR": round(worst_week, 6),
    }


def verify_accepted_baseline_summary(trades: pd.DataFrame) -> None:
    groups = {"FULL": trades}
    groups.update({name: group for name, group in trades.groupby("Period")})
    for label, expected in EXPECTED_BASELINE.items():
        actual = equity_metrics(groups[label])
        if actual["Trades"] != expected["Trades"]:
            raise AssertionError(f"{label} baseline trade count changed")
        if actual["Wins"] != expected["Wins"]:
            raise AssertionError(f"{label} baseline win count changed")
        if not np.isclose(actual["TotalR"], expected["TotalR"], atol=1e-6):
            raise AssertionError(f"{label} baseline TotalR changed")


def simulate_daily_stop(
    trades: pd.DataFrame, threshold_r: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replay entries while recognizing only accepted closes strictly before entry.

    Close events sharing one timestamp are aggregated before threshold evaluation,
    avoiding an unknowable within-minute ordering. Once reached, the stop is
    latched until the next JST date even if later accepted positions recover.
    """
    if threshold_r >= 0:
        raise ValueError("Daily Stop threshold must be negative")

    pending: list[tuple[pd.Timestamp, int, float]] = []
    daily_realized: defaultdict[pd.Timestamp, float] = defaultdict(float)
    stop_time: dict[pd.Timestamp, pd.Timestamp] = {}
    stop_events: list[dict] = []
    decisions: list[dict] = []
    heap_sequence = 0

    def realize_close_groups(before: pd.Timestamp | None = None) -> None:
        nonlocal pending
        while pending and (before is None or pending[0][0] < before):
            close_time = pending[0][0]
            close_total = 0.0
            while pending and pending[0][0] == close_time:
                _, _, result_r = heapq.heappop(pending)
                close_total += result_r
            close_day = close_time.normalize()
            daily_realized[close_day] += close_total
            if (
                close_day not in stop_time
                and daily_realized[close_day] <= threshold_r
            ):
                stop_time[close_day] = close_time
                stop_events.append({
                    "ThresholdR": threshold_r,
                    "StopDate": close_day,
                    "StopTime": close_time,
                    "CumulativeRAtTrigger": round(daily_realized[close_day], 9),
                    "StopDatePeriod": period_label(close_day),
                })

    ordered = trades.sort_values(
        ["EntryTime", "StrategyNo", "CloseTime"], kind="mergesort"
    )
    for decision_order, row in enumerate(ordered.itertuples(index=False), start=1):
        entry_time = pd.Timestamp(row.EntryTime)
        entry_day = entry_time.normalize()
        realize_close_groups(before=entry_time)

        blocked = entry_day in stop_time
        record = row._asdict()
        record.update({
            "ThresholdR": threshold_r,
            "DecisionOrder": decision_order,
            "AccountingDate": entry_day,
            "AvailableRealizedRBeforeEntry": round(daily_realized[entry_day], 9),
            "DailyStopStatus": "BLOCKED" if blocked else "ACCEPTED",
            "StopTriggerTime": stop_time.get(entry_day, pd.NaT),
            "BaselineR": float(row.R),
            "AppliedR": 0.0 if blocked else float(row.R),
        })
        decisions.append(record)

        if not blocked:
            heap_sequence += 1
            heapq.heappush(
                pending,
                (pd.Timestamp(row.CloseTime), heap_sequence, float(row.R)),
            )

    # Finish the accounting ledger, including threshold reaches after the last
    # entry of a day. These cannot change past decisions but remain auditable.
    realize_close_groups(before=None)
    decisions_df = pd.DataFrame(decisions)
    events_df = pd.DataFrame(
        stop_events,
        columns=[
            "ThresholdR", "StopDate", "StopTime",
            "CumulativeRAtTrigger", "StopDatePeriod",
        ],
    )
    return decisions_df, events_df


def validate_simulation(
    baseline: pd.DataFrame,
    decisions: pd.DataFrame,
    events: pd.DataFrame,
    threshold_r: float,
) -> None:
    if len(decisions) != len(baseline):
        raise AssertionError("Daily Stop changed the candidate-trade row count")
    if not decisions["DailyStopStatus"].isin({"ACCEPTED", "BLOCKED"}).all():
        raise AssertionError("Unknown Daily Stop decision")
    accepted = decisions[decisions["DailyStopStatus"] == "ACCEPTED"]
    blocked = decisions[decisions["DailyStopStatus"] == "BLOCKED"]
    if not np.allclose(accepted["AppliedR"], accepted["BaselineR"], atol=1e-12):
        raise AssertionError("Accepted trade R changed")
    if not np.allclose(blocked["AppliedR"], 0.0, atol=1e-12):
        raise AssertionError("Blocked trades must contribute zero R")
    if len(events):
        if events["StopDate"].duplicated().any():
            raise AssertionError("A JST date has more than one stop trigger")
        if not (events["CumulativeRAtTrigger"] <= threshold_r).all():
            raise AssertionError("Stop triggered above its threshold")
        trigger_by_day = events.set_index("StopDate")["StopTime"].to_dict()
    else:
        trigger_by_day = {}

    expected_blocked = decisions.apply(
        lambda row: (
            row["AccountingDate"] in trigger_by_day
            and trigger_by_day[row["AccountingDate"]] < row["EntryTime"]
        ),
        axis=1,
    )
    actual_blocked = decisions["DailyStopStatus"].eq("BLOCKED")
    if not expected_blocked.equals(actual_blocked):
        raise AssertionError("CloseTime < EntryTime / stop-latch invariant failed")

    baseline_total = float(decisions["BaselineR"].sum())
    applied_total = float(decisions["AppliedR"].sum())
    avoided_losses = float(-blocked.loc[blocked["BaselineR"] < 0, "BaselineR"].sum())
    missed_profits = float(blocked.loc[blocked["BaselineR"] > 0, "BaselineR"].sum())
    if not np.isclose(
        applied_total - baseline_total,
        avoided_losses - missed_profits,
        atol=1e-8,
    ):
        raise AssertionError("Blocked-trade P/L decomposition failed")


def make_baseline_decisions(trades: pd.DataFrame) -> pd.DataFrame:
    baseline = trades.copy()
    baseline["ThresholdR"] = np.nan
    baseline["DecisionOrder"] = np.arange(1, len(baseline) + 1)
    baseline["AccountingDate"] = baseline["EntryTime"].dt.normalize()
    baseline["AvailableRealizedRBeforeEntry"] = np.nan
    baseline["DailyStopStatus"] = "ACCEPTED"
    baseline["StopTriggerTime"] = pd.NaT
    baseline["BaselineR"] = baseline["R"].astype(float)
    baseline["AppliedR"] = baseline["R"].astype(float)
    return baseline


def summarize_decisions(
    decisions: pd.DataFrame,
    label: str,
    mode: str,
    threshold_r: float | None,
    stop_events: pd.DataFrame | None = None,
) -> dict:
    accepted = decisions[decisions["DailyStopStatus"] == "ACCEPTED"]
    blocked = decisions[decisions["DailyStopStatus"] == "BLOCKED"]
    performance = equity_metrics(accepted, "AppliedR")
    baseline_total = float(decisions["BaselineR"].sum())
    blocked_losses = float(blocked.loc[blocked["BaselineR"] < 0, "BaselineR"].sum())
    blocked_wins = float(blocked.loc[blocked["BaselineR"] > 0, "BaselineR"].sum())
    reached_days = 0 if stop_events is None else int(stop_events["StopDate"].nunique())
    return {
        "Mode": mode,
        "ThresholdR": np.nan if threshold_r is None else threshold_r,
        "Segment": label,
        "BaselineTrades": int(len(decisions)),
        "ExecutedTrades": performance.pop("Trades"),
        "BlockedTrades": int(len(blocked)),
        "ExecutionRatePct": round(float(len(accepted) / len(decisions) * 100), 3)
        if len(decisions) else np.nan,
        **performance,
        "BaselineTotalR": round(baseline_total, 6),
        "DeltaR": round(float(accepted["AppliedR"].sum()) - baseline_total, 6),
        "AvoidedLossR": round(-blocked_losses, 6),
        "MissedProfitR": round(blocked_wins, 6),
        "ThresholdReachedDays": reached_days,
        "DaysWithBlockedEntries": int(blocked["AccountingDate"].nunique()),
    }


def event_subset(
    events: pd.DataFrame, segment: str | None = None, year: int | None = None
) -> pd.DataFrame:
    if events.empty:
        return events
    if segment is not None:
        return events[events["StopDatePeriod"] == segment]
    if year is not None:
        return events[events["StopDate"].dt.year == year]
    return events


def build_summary_tables(
    baseline: pd.DataFrame,
    simulations: list[tuple[float, pd.DataFrame, pd.DataFrame]],
    segments: tuple[str, ...],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline_decisions = make_baseline_decisions(baseline)
    summary_rows: list[dict] = []
    yearly_rows: list[dict] = []

    for segment in segments:
        base_part = baseline_decisions if segment == "FULL" else baseline_decisions[
            baseline_decisions["Period"] == segment
        ]
        summary_rows.append(
            summarize_decisions(base_part, segment, "NONE", None, None)
        )

    for year, base_part in baseline_decisions.groupby(
        baseline_decisions["EntryTime"].dt.year, sort=True
    ):
        yearly_rows.append(
            summarize_decisions(base_part, str(year), "NONE", None, None)
        )

    for threshold, decisions, events in simulations:
        for segment in segments:
            part = decisions if segment == "FULL" else decisions[
                decisions["Period"] == segment
            ]
            ev = events if segment == "FULL" else event_subset(events, segment=segment)
            summary_rows.append(
                summarize_decisions(part, segment, "DAILY_STOP", threshold, ev)
            )
        for year, part in decisions.groupby(decisions["EntryTime"].dt.year, sort=True):
            yearly_rows.append(
                summarize_decisions(
                    part,
                    str(year),
                    "DAILY_STOP",
                    threshold,
                    event_subset(events, year=int(year)),
                )
            )

    return pd.DataFrame(summary_rows), pd.DataFrame(yearly_rows)


def make_daily_ledger(
    decisions: pd.DataFrame, events: pd.DataFrame, threshold_r: float
) -> pd.DataFrame:
    accepted = decisions[decisions["DailyStopStatus"] == "ACCEPTED"].copy()
    blocked = decisions[decisions["DailyStopStatus"] == "BLOCKED"].copy()

    closed = accepted.assign(CloseDate=accepted["CloseTime"].dt.normalize())
    close_agg = closed.groupby("CloseDate", as_index=True).agg(
        RealizedR=("AppliedR", "sum"),
        AcceptedTradesClosed=("AppliedR", "size"),
    )
    blocked_agg = blocked.groupby("AccountingDate", as_index=True).agg(
        BlockedEntries=("BaselineR", "size"),
        BlockedBaselineR=("BaselineR", "sum"),
    )
    if len(blocked):
        blocked_losses = (
            blocked.assign(Loss=np.where(blocked["BaselineR"] < 0, -blocked["BaselineR"], 0.0))
            .groupby("AccountingDate")["Loss"].sum()
        )
        blocked_wins = (
            blocked.assign(Profit=np.where(blocked["BaselineR"] > 0, blocked["BaselineR"], 0.0))
            .groupby("AccountingDate")["Profit"].sum()
        )
    else:
        blocked_losses = pd.Series(dtype=float)
        blocked_wins = pd.Series(dtype=float)

    event_index = events.set_index("StopDate") if len(events) else pd.DataFrame()
    all_days = close_agg.index.union(blocked_agg.index)
    if len(events):
        all_days = all_days.union(pd.DatetimeIndex(events["StopDate"]))
    ledger = pd.DataFrame(index=all_days.sort_values())
    ledger.index.name = "JSTDate"
    ledger = ledger.join(close_agg).join(blocked_agg)
    ledger["AvoidedLossR"] = blocked_losses.reindex(ledger.index, fill_value=0.0)
    ledger["MissedProfitR"] = blocked_wins.reindex(ledger.index, fill_value=0.0)
    ledger["RealizedR"] = ledger["RealizedR"].fillna(0.0)
    for column in ("AcceptedTradesClosed", "BlockedEntries"):
        ledger[column] = ledger[column].fillna(0).astype(int)
    ledger["BlockedBaselineR"] = ledger["BlockedBaselineR"].fillna(0.0)
    ledger["ThresholdR"] = threshold_r
    ledger["ThresholdReached"] = ledger.index.isin(
        pd.DatetimeIndex(events["StopDate"]) if len(events) else pd.DatetimeIndex([])
    )
    ledger["StopTime"] = (
        event_index["StopTime"].reindex(ledger.index) if len(events) else pd.NaT
    )
    ledger["CumulativeRAtTrigger"] = (
        event_index["CumulativeRAtTrigger"].reindex(ledger.index)
        if len(events) else np.nan
    )
    ledger["DatePeriod"] = [period_label(pd.Timestamp(day)) for day in ledger.index]
    return ledger.reset_index()


def temporal_rule_self_test() -> None:
    # A loss closes at 09:00. The 09:00 entry must not see it, while the 10:00
    # entry must be blocked. A pre-existing +2R closes at 09:30, but the stop
    # remains latched even though available realized R has recovered to +1R.
    rows = [
        (1, "loss", "2020-01-06 08:00", "2020-01-06 09:00", -1.0),
        (2, "recovery", "2020-01-06 08:30", "2020-01-06 09:30", 2.0),
        (3, "same_time", "2020-01-06 09:00", "2020-01-06 09:15", 0.0),
        (4, "later", "2020-01-06 10:00", "2020-01-06 11:00", 1.0),
    ]
    fixture = pd.DataFrame(
        rows, columns=["StrategyNo", "Strategy", "EntryTime", "CloseTime", "R"]
    )
    fixture[["EntryTime", "CloseTime"]] = fixture[["EntryTime", "CloseTime"]].apply(
        pd.to_datetime
    )
    fixture["Period"] = "IS"
    decisions, _ = simulate_daily_stop(fixture, -1.0)
    status = dict(zip(decisions["Strategy"], decisions["DailyStopStatus"]))
    if status != {
        "loss": "ACCEPTED", "recovery": "ACCEPTED",
        "same_time": "ACCEPTED", "later": "BLOCKED",
    }:
        raise AssertionError(f"Same-time/latch self-test failed: {status}")
    later_available = float(
        decisions.loc[decisions["Strategy"] == "later", "AvailableRealizedRBeforeEntry"].iloc[0]
    )
    if not np.isclose(later_available, 1.0):
        raise AssertionError("Recovery self-test failed")

    overnight = pd.DataFrame({
        "StrategyNo": [1, 2],
        "Strategy": ["overnight_loss", "next_day_entry"],
        "EntryTime": pd.to_datetime(["2020-01-06 21:00", "2020-01-07 09:00"]),
        "CloseTime": pd.to_datetime(["2020-01-07 08:00", "2020-01-07 10:00"]),
        "R": [-1.0, 1.0],
        "Period": ["IS", "IS"],
    })
    overnight_decisions, _ = simulate_daily_stop(overnight, -1.0)
    if overnight_decisions.iloc[1]["DailyStopStatus"] != "BLOCKED":
        raise AssertionError("Overnight close-day accounting self-test failed")

    simultaneous_closes = pd.DataFrame({
        "StrategyNo": [1, 2, 3],
        "Strategy": ["same_close_loss", "same_close_win", "later_entry"],
        "EntryTime": pd.to_datetime([
            "2020-01-06 08:00", "2020-01-06 08:30", "2020-01-06 10:00"
        ]),
        "CloseTime": pd.to_datetime([
            "2020-01-06 09:00", "2020-01-06 09:00", "2020-01-06 11:00"
        ]),
        "R": [-1.0, 1.0, 0.5],
        "Period": ["IS", "IS", "IS"],
    })
    simultaneous_decisions, simultaneous_events = simulate_daily_stop(
        simultaneous_closes, -1.0
    )
    if simultaneous_decisions.iloc[2]["DailyStopStatus"] != "ACCEPTED":
        raise AssertionError("Simultaneous-close aggregation self-test failed")
    if len(simultaneous_events):
        raise AssertionError("Simultaneous closes used unknowable within-minute order")


def write_outputs(prefix: str, frames: dict[str, pd.DataFrame]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for suffix, frame in frames.items():
        path = OUTPUT_DIR / f"{prefix}_{suffix}.csv"
        frame.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S")
        paths.append(path)

    manifest_rows = []
    for path in paths:
        manifest_rows.append({
            "Filename": path.name,
            "Rows": len(pd.read_csv(path)),
            "SHA256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    manifest = pd.DataFrame(manifest_rows)
    manifest_path = OUTPUT_DIR / f"{prefix}_output_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    paths.append(manifest_path)
    return paths


def run_is_selection(trades: pd.DataFrame, input_path: Path) -> None:
    is_trades = trades[trades["Period"] == "IS"].copy()
    simulations = []
    ledgers = []
    for threshold in CANDIDATE_THRESHOLDS_R:
        decisions, events = simulate_daily_stop(is_trades, threshold)
        validate_simulation(is_trades, decisions, events, threshold)
        simulations.append((threshold, decisions, events))
        ledgers.append(make_daily_ledger(decisions, events, threshold))

    summary, yearly = build_summary_tables(is_trades, simulations, ("IS",))
    all_decisions = pd.concat([item[1] for item in simulations], ignore_index=True)
    all_events = pd.concat([item[2] for item in simulations], ignore_index=True)
    all_ledgers = pd.concat(ledgers, ignore_index=True)
    accepted = all_decisions[all_decisions["DailyStopStatus"] == "ACCEPTED"].copy()
    blocked = all_decisions[all_decisions["DailyStopStatus"] == "BLOCKED"].copy()
    metadata = pd.DataFrame([{
        "AnalysisVersion": ANALYSIS_VERSION,
        "Mode": MODE,
        "GeneratedAtUTC": pd.Timestamp.now(tz="UTC").isoformat(),
        "InputPath": str(input_path),
        "InputTradeLogSHA256": ACCEPTED_BASELINE_SHA256,
        "InputTradeRows": len(trades),
        "AnalyzedRows": len(is_trades),
        "CandidateThresholdsR": ";".join(str(x) for x in CANDIDATE_THRESHOLDS_R),
        "OOSCalculated": False,
        "StopLatch": True,
        "CloseTimeRule": "CloseTime < EntryTime",
        "ResetTimezone": "Asia/Tokyo",
    }])
    paths = write_outputs("daily_stop_is", {
        "threshold_summary": summary,
        "yearly_summary": yearly,
        "decisions": all_decisions,
        "accepted_trades": accepted,
        "blocked_trades": blocked,
        "daily_ledger": all_ledgers,
        "stop_events": all_events,
        "run_metadata": metadata,
    })

    print("\n" + "=" * 130)
    print("DAILY STOP — IS SELECTION ONLY (2015-2021)")
    print("OOS1/OOS2: NOT CALCULATED")
    print("=" * 130)
    print(summary.to_string(index=False))
    print("\nIS YEARLY SUMMARY")
    print(yearly.to_string(index=False))
    print("\nCSV OUTPUTS")
    for path in paths:
        print(path)


def run_frozen_report(trades: pd.DataFrame, input_path: Path) -> None:
    if FROZEN_THRESHOLD_R is None:
        raise RuntimeError(
            "FROZEN_REPORT requires an IS-selected FROZEN_THRESHOLD_R"
        )
    threshold = float(FROZEN_THRESHOLD_R)
    if threshold not in CANDIDATE_THRESHOLDS_R:
        raise RuntimeError(
            "Frozen threshold must be one of the predeclared IS candidates"
        )

    decisions, events = simulate_daily_stop(trades, threshold)
    validate_simulation(trades, decisions, events, threshold)
    simulations = [(threshold, decisions, events)]
    summary, yearly = build_summary_tables(
        trades, simulations, ("FULL", "IS", "OOS1", "OOS2")
    )
    accepted = decisions[decisions["DailyStopStatus"] == "ACCEPTED"].copy()
    blocked = decisions[decisions["DailyStopStatus"] == "BLOCKED"].copy()
    ledger = make_daily_ledger(decisions, events, threshold)
    metadata = pd.DataFrame([{
        "AnalysisVersion": ANALYSIS_VERSION,
        "Mode": MODE,
        "GeneratedAtUTC": pd.Timestamp.now(tz="UTC").isoformat(),
        "InputPath": str(input_path),
        "InputTradeLogSHA256": ACCEPTED_BASELINE_SHA256,
        "InputTradeRows": len(trades),
        "AnalyzedRows": len(trades),
        "FrozenThresholdR": threshold,
        "OOSCalculated": True,
        "StopLatch": True,
        "CloseTimeRule": "CloseTime < EntryTime",
        "ResetTimezone": "Asia/Tokyo",
    }])
    paths = write_outputs("daily_stop", {
        "threshold_summary": summary,
        "yearly_summary": yearly,
        "decisions": decisions,
        "accepted_trades": accepted,
        "blocked_trades": blocked,
        "daily_ledger": ledger,
        "stop_events": events,
        "run_metadata": metadata,
    })

    print("\n" + "=" * 130)
    print(f"DAILY STOP — FROZEN REPORT ({threshold:g}R)")
    print("=" * 130)
    print(summary.to_string(index=False))
    print("\nYEARLY SUMMARY")
    print(yearly.to_string(index=False))
    print("\nCSV OUTPUTS")
    for path in paths:
        print(path)


def main() -> None:
    if MODE not in {"IS_SELECTION", "FROZEN_REPORT"}:
        raise ValueError(f"Unknown MODE: {MODE}")
    if tuple(CANDIDATE_THRESHOLDS_R) != (-1.0, -1.5, -2.0, -2.5, -3.0, -4.0):
        raise AssertionError("Predeclared threshold grid changed")
    temporal_rule_self_test()
    print("Temporal-rule self-test: OK")

    if drive is not None:
        drive.mount("/content/drive")
    input_path = resolve_baseline_path()
    trades = load_and_validate_baseline(input_path)
    print(f"Accepted baseline: {input_path}")
    print(f"Rows: {len(trades):,}")
    print(f"SHA-256: {ACCEPTED_BASELINE_SHA256}")

    if MODE == "IS_SELECTION":
        run_is_selection(trades, input_path)
    else:
        run_frozen_report(trades, input_path)


if __name__ == "__main__":
    main()
