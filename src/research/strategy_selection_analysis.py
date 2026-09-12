"""IS-only Strategy Selection / Portfolio Pruning analysis.

This research-only program reads the accepted frozen Baseline Trade Log. It
never reads M1 prices, recalculates trades, evaluates OOS1/OOS2, or changes EA,
VPS, SET, or live-operation files.
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

try:
    from google.colab import drive
except ImportError:  # permits local validation and unit tests
    drive = None


ANALYSIS_VERSION = "strategy-selection-is-v1.0.0"
PLAN_BRANCH = "research/strategy-selection-validation"
ACCEPTED_BASELINE_SHA256 = (
    "cc32f32e3df57cb03416d111e3cf848fb6b2edc7f193b6da90201a2462420359"
)
ACCEPTED_MEMBERSHIP_SHA256 = (
    "aad041b8cbc03611cbe535060c4887f30f9341c5d0f0010158f1d923e830756d"
)
EXPECTED_TRADE_ROWS = 16_298
EXPECTED_STRATEGY_COUNT = 28
EXPECTED_IS_TRADES = 9_756
EXPECTED_IS_TOTAL_R = 768.488273
IS_START = pd.Timestamp("2015-01-01")
IS_END_EXCLUSIVE = pd.Timestamp("2022-01-01")
IS_YEARS = tuple(range(2015, 2022))
FLOAT_TOLERANCE = 1e-8

BASELINE_CANDIDATES = (
    Path(
        "/content/drive/MyDrive/time-entry-portfolio-lab/daily_stop/"
        "baseline_cc32f32e3df5/daily_stop_baseline_trades.csv"
    ),
    Path("/content/daily_stop_baseline_trades.csv"),
)
MEMBERSHIP_CANDIDATES = (
    Path(
        "/content/drive/MyDrive/time-entry-portfolio-lab/strategy_selection/"
        "strategy_selection_group_membership.csv"
    ),
    Path("/content/strategy_selection_group_membership.csv"),
    Path("results/strategy_selection/strategy_selection_group_membership.csv"),
)
DEFAULT_OUTPUT_DIR = Path("/content")

HEALTH_FILENAME = "strategy_selection_health_is.csv"
LEAVE_ONE_OUT_FILENAME = "strategy_selection_leave_one_out_is.csv"
GROUP_FILENAME = "strategy_selection_group_hypotheses_is.csv"

REQUIRED_BASELINE_COLUMNS = {
    "StrategyNo",
    "Strategy",
    "Pair",
    "Direction",
    "EntryTime",
    "CloseTime",
    "SL",
    "TP",
    "Pips",
    "R",
    "ExitReason",
    "Period",
}
GROUP_COLUMNS = (
    "TP_LT_SL",
    "TP_NONE",
    "JPY_RELATED",
    "AUD_RELATED",
    "LONG",
    "SHORT",
    "OVERNIGHT",
    "CHINA_DEMAND",
)
REQUIRED_MEMBERSHIP_COLUMNS = {
    "StrategyNo",
    "Strategy",
    "Pair",
    "Direction",
    "SL",
    "TP",
    *GROUP_COLUMNS,
    "MembershipBasis",
    "BaselineSHA256",
    "PlanBranch",
    "MembershipFrozenDateJST",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_exact_file(
    explicit: Path | None,
    candidates: tuple[Path, ...],
    expected_sha256: str,
    label: str,
) -> Path:
    choices = (explicit,) if explicit is not None else candidates
    found = [path for path in choices if path is not None and path.is_file()]
    if not found:
        expected_locations = "\n".join(str(path) for path in choices if path)
        raise FileNotFoundError(
            f"{label} was not found. Expected one of:\n{expected_locations}"
        )
    for path in found:
        actual = file_sha256(path)
        if actual != expected_sha256:
            raise RuntimeError(
                f"{label} SHA-256 mismatch: {path}\n"
                f"expected={expected_sha256}\nactual={actual}"
            )
    return found[0]


def _parse_boolean(series: pd.Series, column: str) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    mapping = {"true": True, "false": False}
    unknown = sorted(set(normalized) - set(mapping))
    if unknown:
        raise ValueError(f"Unknown boolean values in {column}: {unknown}")
    return normalized.map(mapping).astype(bool)


def load_membership(path: Path) -> pd.DataFrame:
    if file_sha256(path) != ACCEPTED_MEMBERSHIP_SHA256:
        raise RuntimeError("Group membership hash changed; analysis aborted")
    membership = pd.read_csv(path)
    missing = sorted(REQUIRED_MEMBERSHIP_COLUMNS - set(membership.columns))
    if missing:
        raise ValueError(f"Membership columns missing: {missing}")

    membership["StrategyNo"] = pd.to_numeric(
        membership["StrategyNo"], errors="raise"
    ).astype(int)
    if membership["StrategyNo"].duplicated().any():
        raise AssertionError("Membership has duplicate StrategyNo values")
    if membership["Strategy"].duplicated().any():
        raise AssertionError("Membership has duplicate Strategy values")
    if sorted(membership["StrategyNo"].tolist()) != list(range(1, 29)):
        raise AssertionError("Membership must contain strategy numbers 1..28")

    for column in GROUP_COLUMNS:
        membership[column] = _parse_boolean(membership[column], column)
        if not membership[column].any():
            raise AssertionError(f"Predeclared group {column} has no members")

    expected_hashes = set(membership["BaselineSHA256"].astype(str))
    if expected_hashes != {ACCEPTED_BASELINE_SHA256}:
        raise AssertionError("Membership refers to a different Baseline hash")
    if set(membership["PlanBranch"].astype(str)) != {PLAN_BRANCH}:
        raise AssertionError("Membership refers to a different plan branch")
    return membership.sort_values("StrategyNo", kind="mergesort").reset_index(drop=True)


def load_and_validate_baseline(path: Path) -> pd.DataFrame:
    if file_sha256(path) != ACCEPTED_BASELINE_SHA256:
        raise RuntimeError("Baseline hash changed; analysis aborted")

    trades = pd.read_csv(path)
    missing = sorted(REQUIRED_BASELINE_COLUMNS - set(trades.columns))
    if missing:
        raise ValueError(f"Baseline columns missing: {missing}")
    if len(trades) != EXPECTED_TRADE_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_TRADE_ROWS:,} trades, found {len(trades):,}"
        )

    for column in ("EntryTime", "CloseTime"):
        trades[column] = pd.to_datetime(trades[column], errors="raise")
    for column in ("StrategyNo", "SL", "TP", "Pips", "R"):
        trades[column] = pd.to_numeric(trades[column], errors="raise")
    trades["StrategyNo"] = trades["StrategyNo"].astype("Int64")

    if trades[["StrategyNo", "SL", "Pips", "R"]].isna().any().any():
        raise AssertionError("Required numeric Baseline fields contain NaN")
    if not np.isfinite(trades[["SL", "Pips", "R"]].to_numpy()).all():
        raise AssertionError("Required numeric Baseline fields are non-finite")
    if (trades["CloseTime"] < trades["EntryTime"]).any():
        raise AssertionError("CloseTime precedes EntryTime")
    if trades.duplicated(["StrategyNo", "EntryTime"]).any():
        raise AssertionError("Duplicate StrategyNo + EntryTime rows")
    if sorted(trades["StrategyNo"].astype(int).unique()) != list(range(1, 29)):
        raise AssertionError("Expected exactly strategy numbers 1..28")
    if trades["Strategy"].nunique() != EXPECTED_STRATEGY_COUNT:
        raise AssertionError("Expected exactly 28 unique strategy names")
    if not np.allclose(
        trades["R"], trades["Pips"] / trades["SL"], atol=FLOAT_TOLERANCE
    ):
        raise AssertionError("R != Pips / SL")
    sl_rows = trades["ExitReason"].astype(str).str.upper().eq("SL")
    if not np.allclose(trades.loc[sl_rows, "R"], -1.0, atol=FLOAT_TOLERANCE):
        raise AssertionError("SL rows must equal -1R")

    is_mask = (trades["EntryTime"] >= IS_START) & (
        trades["EntryTime"] < IS_END_EXCLUSIVE
    )
    period_is = trades["Period"].astype(str).eq("IS")
    if not is_mask.equals(period_is):
        raise AssertionError("IS period is not based on EntryTime JST")

    trades["StrategyNo"] = trades["StrategyNo"].astype(int)
    return trades.sort_values(
        ["EntryTime", "StrategyNo", "CloseTime"], kind="mergesort"
    ).reset_index(drop=True)


def select_and_validate_is(
    baseline: pd.DataFrame, membership: pd.DataFrame
) -> pd.DataFrame:
    # This is the only performance slice exposed by this program. OOS rows are
    # neither summarized nor written to output.
    is_trades = baseline.loc[baseline["Period"].astype(str).eq("IS")].copy()
    if len(is_trades) != EXPECTED_IS_TRADES:
        raise AssertionError(
            f"Expected {EXPECTED_IS_TRADES:,} IS trades, found {len(is_trades):,}"
        )
    if not np.isclose(is_trades["R"].sum(), EXPECTED_IS_TOTAL_R, atol=1e-6):
        raise AssertionError("Accepted IS Total R changed")
    if tuple(sorted(is_trades["EntryTime"].dt.year.unique())) != IS_YEARS:
        raise AssertionError("IS years must be exactly 2015..2021")

    baseline_identity = (
        is_trades[["StrategyNo", "Strategy", "Pair", "Direction"]]
        .drop_duplicates()
        .sort_values("StrategyNo", kind="mergesort")
        .reset_index(drop=True)
    )
    membership_identity = membership[
        ["StrategyNo", "Strategy", "Pair", "Direction"]
    ].reset_index(drop=True)
    if not baseline_identity.equals(membership_identity):
        raise AssertionError(
            "Baseline strategy identity differs from frozen membership"
        )
    return is_trades


def _max_losing_streak(values: pd.Series) -> int:
    longest = current = 0
    for value in values.astype(float):
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def performance_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    ordered = frame.sort_values(
        ["CloseTime", "EntryTime", "StrategyNo"], kind="mergesort"
    ).copy()
    values = ordered["R"].astype(float)
    gains = float(values[values > 0].sum())
    losses = float(-values[values < 0].sum())
    equity = np.concatenate(([0.0], values.cumsum().to_numpy()))
    drawdown = np.maximum.accumulate(equity) - equity

    if len(ordered):
        ordered["_CloseDay"] = ordered["CloseTime"].dt.normalize()
        ordered["_CloseWeek"] = ordered["CloseTime"].dt.to_period("W-SUN")
        daily = ordered.groupby("_CloseDay", sort=True)["R"].sum()
        weekly = ordered.groupby("_CloseWeek", sort=True)["R"].sum()
        worst_day = float(daily.min())
        worst_week = float(weekly.min())
    else:
        worst_day = worst_week = 0.0

    yearly = (
        ordered.groupby(ordered["EntryTime"].dt.year, sort=True)["R"]
        .sum()
        .reindex(IS_YEARS, fill_value=0.0)
    )
    exit_reason = ordered["ExitReason"].astype(str).str.upper()
    exit_total = len(exit_reason)
    tp_count = int(exit_reason.eq("TP").sum())
    sl_count = int(exit_reason.eq("SL").sum())
    time_count = int(exit_reason.isin({"TIME", "TIMEEXIT", "TIME_EXIT"}).sum())
    other_count = exit_total - tp_count - sl_count - time_count

    result: dict[str, float | int] = {
        "Trades": int(len(ordered)),
        "TotalR": round(float(values.sum()), 6),
        "PF": round(gains / losses, 6) if losses else np.nan,
        "WinRatePct": round(float((values > 0).mean() * 100), 6)
        if len(values)
        else np.nan,
        "AvgR": round(float(values.mean()), 9) if len(values) else np.nan,
        "AvgWinR": round(float(values[values > 0].mean()), 9)
        if (values > 0).any()
        else np.nan,
        "AvgLossR": round(float(values[values < 0].mean()), 9)
        if (values < 0).any()
        else np.nan,
        "MaxDDR": round(float(drawdown.max()), 6),
        "WorstDayR": round(worst_day, 6),
        "WorstWeekR": round(worst_week, 6),
        "PositiveYears": int((yearly > FLOAT_TOLERANCE).sum()),
        "NegativeYears": int((yearly < -FLOAT_TOLERANCE).sum()),
        "NeutralYears": int((yearly.abs() <= FLOAT_TOLERANCE).sum()),
        "MaxLosingStreak": _max_losing_streak(values),
        "TPExitRatePct": round(tp_count / exit_total * 100, 6)
        if exit_total
        else np.nan,
        "SLExitRatePct": round(sl_count / exit_total * 100, 6)
        if exit_total
        else np.nan,
        "TimeExitRatePct": round(time_count / exit_total * 100, 6)
        if exit_total
        else np.nan,
        "OtherExitRatePct": round(other_count / exit_total * 100, 6)
        if exit_total
        else np.nan,
    }
    for year in IS_YEARS:
        result[f"TotalR_{year}"] = round(float(yearly.loc[year]), 6)
    return result


def provenance(run_jst: str) -> dict[str, str]:
    return {
        "AnalysisVersion": ANALYSIS_VERSION,
        "BaselineSHA256": ACCEPTED_BASELINE_SHA256,
        "MembershipSHA256": ACCEPTED_MEMBERSHIP_SHA256,
        "PlanBranch": PLAN_BRANCH,
        "ValidationRunJST": run_jst,
        "Segment": "IS_2015_2021",
    }


def build_health_table(
    is_trades: pd.DataFrame, membership: pd.DataFrame, run_jst: str
) -> pd.DataFrame:
    metadata_columns = [
        "StrategyNo",
        "Strategy",
        "Pair",
        "Direction",
        "SL",
        "TP",
        *GROUP_COLUMNS,
        "MembershipBasis",
    ]
    metadata = membership.set_index("StrategyNo")
    rows: list[dict] = []
    for strategy_no in range(1, EXPECTED_STRATEGY_COUNT + 1):
        part = is_trades.loc[is_trades["StrategyNo"].eq(strategy_no)]
        row = metadata.loc[strategy_no, metadata_columns[1:]].to_dict()
        rows.append(
            {
                **provenance(run_jst),
                "StrategyNo": strategy_no,
                **row,
                **performance_metrics(part),
            }
        )
    return pd.DataFrame(rows).sort_values("StrategyNo", kind="mergesort")


def _delta(candidate: dict, baseline: dict, metric: str) -> float:
    left, right = candidate[metric], baseline[metric]
    if pd.isna(left) or pd.isna(right):
        return np.nan
    return round(float(left) - float(right), 6)


def build_leave_one_out_table(
    is_trades: pd.DataFrame, health: pd.DataFrame, run_jst: str
) -> pd.DataFrame:
    baseline = performance_metrics(is_trades)
    health_by_no = health.set_index("StrategyNo")
    rows: list[dict] = []
    for strategy_no in range(1, EXPECTED_STRATEGY_COUNT + 1):
        standalone = health_by_no.loc[strategy_no]
        candidate_frame = is_trades.loc[~is_trades["StrategyNo"].eq(strategy_no)]
        candidate = performance_metrics(candidate_frame)
        delta_total_r = _delta(candidate, baseline, "TotalR")
        expected_delta = -float(standalone["TotalR"])
        if not np.isclose(delta_total_r, expected_delta, atol=1e-6):
            raise AssertionError(
                f"LOO Delta Total R identity failed for strategy {strategy_no}"
            )
        clear_negative = (
            float(standalone["TotalR"]) < -FLOAT_TOLERANCE
            and delta_total_r > FLOAT_TOLERANCE
        )
        stable_negative = clear_negative and (
            int(standalone["NegativeYears"]) > int(standalone["PositiveYears"])
        )
        rows.append(
            {
                **provenance(run_jst),
                "RemovedStrategyNo": strategy_no,
                "RemovedStrategy": standalone["Strategy"],
                "RemovedStrategyTotalR": standalone["TotalR"],
                "RemovedStrategyPositiveYears": standalone["PositiveYears"],
                "RemovedStrategyNegativeYears": standalone["NegativeYears"],
                **candidate,
                "DeltaTotalR": delta_total_r,
                "DeltaMaxDDR": _delta(candidate, baseline, "MaxDDR"),
                "DeltaPF": _delta(candidate, baseline, "PF"),
                "DeltaWorstDayR": _delta(candidate, baseline, "WorstDayR"),
                "DeltaWorstWeekR": _delta(candidate, baseline, "WorstWeekR"),
                "ClearNegativeMarginalCandidate": clear_negative,
                "StableNegativeMarginalCandidate": stable_negative,
                "TieBreakRule": "DeltaTotalR_desc_then_StrategyNo_asc",
            }
        )
    result = pd.DataFrame(rows)
    ranked_indices = result.sort_values(
        ["DeltaTotalR", "RemovedStrategyNo"],
        ascending=[False, True],
        kind="mergesort",
    ).index
    rank_by_index = {index: rank for rank, index in enumerate(ranked_indices, 1)}
    result["OverallLOORank"] = result.index.map(rank_by_index)
    candidate_indices = result.loc[result["ClearNegativeMarginalCandidate"]].sort_values(
        ["DeltaTotalR", "RemovedStrategyNo"],
        ascending=[False, True],
        kind="mergesort",
    ).index
    candidate_rank = {
        index: rank for rank, index in enumerate(candidate_indices, start=1)
    }
    result["CandidateRank"] = pd.array(
        [candidate_rank.get(index, pd.NA) for index in result.index], dtype="Int64"
    )
    return result.sort_values(
        ["DeltaTotalR", "RemovedStrategyNo"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def build_group_table(
    is_trades: pd.DataFrame, membership: pd.DataFrame, run_jst: str
) -> pd.DataFrame:
    baseline = performance_metrics(is_trades)
    rows: list[dict] = []
    for group_name in GROUP_COLUMNS:
        member_rows = membership.loc[membership[group_name]]
        member_numbers = member_rows["StrategyNo"].astype(int).tolist()
        member_mask = is_trades["StrategyNo"].isin(member_numbers)
        group_frame = is_trades.loc[member_mask]
        candidate_frame = is_trades.loc[~member_mask]
        group_metrics = performance_metrics(group_frame)
        candidate = performance_metrics(candidate_frame)
        delta_total_r = _delta(candidate, baseline, "TotalR")
        if not np.isclose(
            delta_total_r, -float(group_metrics["TotalR"]), atol=1e-6
        ):
            raise AssertionError(
                f"Group Delta Total R identity failed for {group_name}"
            )
        rows.append(
            {
                **provenance(run_jst),
                "Group": group_name,
                "MemberCount": len(member_numbers),
                "MemberStrategyNos": "|".join(map(str, member_numbers)),
                "MemberStrategies": "|".join(member_rows["Strategy"].astype(str)),
                "GroupTrades": group_metrics["Trades"],
                "GroupTotalR": group_metrics["TotalR"],
                **candidate,
                "DeltaTotalR": delta_total_r,
                "DeltaMaxDDR": _delta(candidate, baseline, "MaxDDR"),
                "DeltaPF": _delta(candidate, baseline, "PF"),
                "DeltaWorstDayR": _delta(candidate, baseline, "WorstDayR"),
                "DeltaWorstWeekR": _delta(candidate, baseline, "WorstWeekR"),
                "ProfitImprovingGroupCandidate": delta_total_r > FLOAT_TOLERANCE,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["DeltaTotalR", "Group"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)


def validate_outputs(
    health: pd.DataFrame, leave_one_out: pd.DataFrame, groups: pd.DataFrame
) -> None:
    if len(health) != EXPECTED_STRATEGY_COUNT:
        raise AssertionError("Health table must contain 28 rows")
    if len(leave_one_out) != EXPECTED_STRATEGY_COUNT:
        raise AssertionError("Leave-One-Out table must contain 28 rows")
    if set(groups["Group"]) != set(GROUP_COLUMNS):
        raise AssertionError("Group table differs from predeclared hypotheses")
    if not np.isclose(health["TotalR"].sum(), EXPECTED_IS_TOTAL_R, atol=5e-5):
        raise AssertionError("Strategy health Total R does not reconcile to IS")
    for frame in (health, leave_one_out, groups):
        if set(frame["Segment"]) != {"IS_2015_2021"}:
            raise AssertionError("An output contains a non-IS segment")
        if any(column.upper().startswith("OOS") for column in frame.columns):
            raise AssertionError("An IS output exposes an OOS column")


def write_outputs(
    output_dir: Path,
    health: pd.DataFrame,
    leave_one_out: pd.DataFrame,
    groups: pd.DataFrame,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = [
        (output_dir / HEALTH_FILENAME, health),
        (output_dir / LEAVE_ONE_OUT_FILENAME, leave_one_out),
        (output_dir / GROUP_FILENAME, groups),
    ]
    for path, frame in outputs:
        frame.to_csv(path, index=False)
    return [path for path, _ in outputs]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run frozen Strategy Selection analysis for IS 2015-2021 only."
    )
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--membership", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--mount-drive",
        action="store_true",
        help="Mount Google Drive in Colab before resolving input files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mount_drive:
        if drive is None:
            raise RuntimeError("--mount-drive is available only in Google Colab")
        drive.mount("/content/drive")

    baseline_path = resolve_exact_file(
        args.baseline,
        BASELINE_CANDIDATES,
        ACCEPTED_BASELINE_SHA256,
        "Accepted Baseline Trade Log",
    )
    membership_path = resolve_exact_file(
        args.membership,
        MEMBERSHIP_CANDIDATES,
        ACCEPTED_MEMBERSHIP_SHA256,
        "Frozen group membership",
    )
    membership = load_membership(membership_path)
    baseline = load_and_validate_baseline(baseline_path)
    is_trades = select_and_validate_is(baseline, membership)

    run_jst = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    health = build_health_table(is_trades, membership, run_jst)
    leave_one_out = build_leave_one_out_table(is_trades, health, run_jst)
    groups = build_group_table(is_trades, membership, run_jst)
    validate_outputs(health, leave_one_out, groups)
    output_paths = write_outputs(args.output_dir, health, leave_one_out, groups)

    print("STRATEGY SELECTION IS ANALYSIS COMPLETE")
    print(f"Baseline SHA-256: {ACCEPTED_BASELINE_SHA256}")
    print(f"Membership SHA-256: {ACCEPTED_MEMBERSHIP_SHA256}")
    print(f"IS trades: {len(is_trades):,}")
    print(f"IS Total R: {is_trades['R'].sum():.6f}")
    print("OOS1/OOS2: NOT CALCULATED")
    print("CSV OUTPUTS")
    for path in output_paths:
        print(path)


if __name__ == "__main__":
    main()
