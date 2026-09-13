"""One-time OOS1 evaluation for the frozen Strategy Selection candidates.

This research-only program accepts exactly the two candidate portfolios frozen
before OOS was viewed. It verifies the complete Baseline Trade Log by SHA-256,
retains and evaluates only OOS1 rows (2022-2025), and never summarizes or writes
OOS2 results. It does not read M1 prices or change EA, VPS, SET, or live files.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

try:
    from google.colab import drive
except ImportError:  # permits local validation and unit tests
    drive = None

try:
    from src.research import strategy_selection_analysis as is_analysis
except ModuleNotFoundError:  # permits direct execution from the repository root
    import strategy_selection_analysis as is_analysis


ANALYSIS_VERSION = "strategy-selection-oos1-v1.0.0"
PLAN_BRANCH = "research/strategy-selection-validation"
ACCEPTED_BASELINE_SHA256 = is_analysis.ACCEPTED_BASELINE_SHA256
ACCEPTED_CANDIDATE_SHA256 = (
    "ffbed6dd415ca1ec91240b8e4754e71b66ba8a7973c24e8439f9bfaa85d6277c"
)
CANDIDATE_FREEZE_COMMIT_SHA = "1c265a7e4bd156b1abb8a99e84626047d378be63"
EXPECTED_TRADE_ROWS = 16_298
EXPECTED_OOS1_TRADES = 5_547
EXPECTED_OOS1_TOTAL_R = 601.960585
OOS1_START = pd.Timestamp("2022-01-01")
OOS1_END_EXCLUSIVE = pd.Timestamp("2026-01-01")
OOS1_YEARS = tuple(range(2022, 2026))
FLOAT_TOLERANCE = 1e-8

BASELINE_CANDIDATES = is_analysis.BASELINE_CANDIDATES
CANDIDATE_CANDIDATES = (
    Path(
        "/content/drive/MyDrive/time-entry-portfolio-lab/strategy_selection/"
        "strategy_selection_candidates_frozen.csv"
    ),
    Path("/content/strategy_selection_candidates_frozen.csv"),
    Path("results/strategy_selection/strategy_selection_candidates_frozen.csv"),
)
DEFAULT_OUTPUT_DIR = Path("/content")
OUTPUT_FILENAME = "strategy_selection_oos_results.csv"

REQUIRED_BASELINE_COLUMNS = is_analysis.REQUIRED_BASELINE_COLUMNS
REQUIRED_CANDIDATE_COLUMNS = {
    "CandidateFreezeCommitSHA",
    "BaselineSHA256",
    "PlanBranch",
    "Segment",
    "OOSViewed",
    "FrozenForOOS",
    "CandidateID",
    "PortfolioLabel",
    "ExcludedStrategyNos",
    "ExcludedStrategies",
}
EXPECTED_CANDIDATE_IDS = ("P0_BASELINE", "P1_MINUS_TOP1")


def _parse_boolean(series: pd.Series, column: str) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    mapping = {"true": True, "false": False}
    unknown = sorted(set(normalized) - set(mapping))
    if unknown:
        raise ValueError(f"Unknown boolean values in {column}: {unknown}")
    return normalized.map(mapping).astype(bool)


def load_frozen_candidates(path: Path) -> pd.DataFrame:
    if is_analysis.file_sha256(path) != ACCEPTED_CANDIDATE_SHA256:
        raise RuntimeError("Frozen candidate CSV hash changed; OOS1 aborted")

    candidates = pd.read_csv(path, keep_default_na=False)
    missing = sorted(REQUIRED_CANDIDATE_COLUMNS - set(candidates.columns))
    if missing:
        raise ValueError(f"Candidate columns missing: {missing}")
    if tuple(candidates["CandidateID"].astype(str)) != EXPECTED_CANDIDATE_IDS:
        raise AssertionError("OOS1 candidates differ from the frozen two portfolios")
    if set(candidates["CandidateFreezeCommitSHA"].astype(str)) != {
        CANDIDATE_FREEZE_COMMIT_SHA
    }:
        raise AssertionError("Candidate freeze commit changed")
    if set(candidates["BaselineSHA256"].astype(str)) != {
        ACCEPTED_BASELINE_SHA256
    }:
        raise AssertionError("Candidates refer to a different Baseline hash")
    if set(candidates["PlanBranch"].astype(str)) != {PLAN_BRANCH}:
        raise AssertionError("Candidates refer to a different plan branch")
    if set(candidates["Segment"].astype(str)) != {"IS_2015_2021"}:
        raise AssertionError("Candidates were not frozen from the IS segment")

    oos_viewed = _parse_boolean(candidates["OOSViewed"], "OOSViewed")
    frozen = _parse_boolean(candidates["FrozenForOOS"], "FrozenForOOS")
    if oos_viewed.any() or not frozen.all():
        raise AssertionError("Candidate pre-OOS state is not frozen and unopened")

    baseline_row = candidates.loc[candidates["CandidateID"].eq("P0_BASELINE")].iloc[0]
    top1_row = candidates.loc[candidates["CandidateID"].eq("P1_MINUS_TOP1")].iloc[0]
    if str(baseline_row["ExcludedStrategyNos"]).strip():
        raise AssertionError("P0_BASELINE must exclude no strategies")
    if str(baseline_row["ExcludedStrategies"]).strip():
        raise AssertionError("P0_BASELINE must exclude no strategies")
    if str(top1_row["ExcludedStrategyNos"]).strip() != "10":
        raise AssertionError("P1_MINUS_TOP1 must exclude only strategy 10")
    if str(top1_row["ExcludedStrategies"]).strip() != "10_AJ_SatA":
        raise AssertionError("P1_MINUS_TOP1 strategy identity changed")
    return candidates.copy()


def _validate_oos1_frame(trades: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_BASELINE_COLUMNS - set(trades.columns))
    if missing:
        raise ValueError(f"Baseline columns missing: {missing}")

    for column in ("EntryTime", "CloseTime"):
        trades[column] = pd.to_datetime(trades[column], errors="raise")
    for column in ("StrategyNo", "SL", "TP", "Pips", "R"):
        trades[column] = pd.to_numeric(trades[column], errors="raise")
    trades["StrategyNo"] = trades["StrategyNo"].astype(int)

    if len(trades) != EXPECTED_OOS1_TRADES:
        raise AssertionError(
            f"Expected {EXPECTED_OOS1_TRADES:,} OOS1 trades, found {len(trades):,}"
        )
    if not np.isclose(trades["R"].sum(), EXPECTED_OOS1_TOTAL_R, atol=1e-6):
        raise AssertionError("Accepted OOS1 Baseline Total R changed")
    in_range = (trades["EntryTime"] >= OOS1_START) & (
        trades["EntryTime"] < OOS1_END_EXCLUSIVE
    )
    if not in_range.all() or not trades["Period"].astype(str).eq("OOS1").all():
        raise AssertionError("OOS1 selection contains a non-OOS1 row")
    if tuple(sorted(trades["EntryTime"].dt.year.unique())) != OOS1_YEARS:
        raise AssertionError("OOS1 years must be exactly 2022..2025")
    if trades["Strategy"].nunique() != 28:
        raise AssertionError("OOS1 must contain all 28 frozen strategies")
    if sorted(trades["StrategyNo"].unique()) != list(range(1, 29)):
        raise AssertionError("OOS1 strategy numbers must be exactly 1..28")
    if (trades["CloseTime"] < trades["EntryTime"]).any():
        raise AssertionError("CloseTime precedes EntryTime")
    if trades.duplicated(["StrategyNo", "EntryTime"]).any():
        raise AssertionError("Duplicate StrategyNo + EntryTime rows")
    if not np.allclose(
        trades["R"], trades["Pips"] / trades["SL"], atol=FLOAT_TOLERANCE
    ):
        raise AssertionError("R != Pips / SL in OOS1")
    sl_rows = trades["ExitReason"].astype(str).str.upper().eq("SL")
    if not np.allclose(trades.loc[sl_rows, "R"], -1.0, atol=FLOAT_TOLERANCE):
        raise AssertionError("OOS1 SL rows must equal -1R")

    return trades.sort_values(
        ["EntryTime", "StrategyNo", "CloseTime"], kind="mergesort"
    ).reset_index(drop=True)


def load_oos1_only(path: Path, chunksize: int = 4096) -> pd.DataFrame:
    if is_analysis.file_sha256(path) != ACCEPTED_BASELINE_SHA256:
        raise RuntimeError("Baseline hash changed; OOS1 aborted")

    total_rows = 0
    oos1_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        total_rows += len(chunk)
        if "Period" not in chunk.columns:
            raise ValueError("Baseline column missing: Period")
        selected = chunk.loc[chunk["Period"].astype(str).eq("OOS1")].copy()
        if len(selected):
            oos1_parts.append(selected)
    if total_rows != EXPECTED_TRADE_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_TRADE_ROWS:,} full rows, found {total_rows:,}"
        )
    if not oos1_parts:
        raise AssertionError("No OOS1 rows found")
    return _validate_oos1_frame(pd.concat(oos1_parts, ignore_index=True))


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
        .reindex(OOS1_YEARS, fill_value=0.0)
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
    for year in OOS1_YEARS:
        result[f"TotalR_{year}"] = round(float(yearly.loc[year]), 6)
    return result


def _delta(candidate: dict, baseline: dict, metric: str) -> float:
    left, right = candidate[metric], baseline[metric]
    if pd.isna(left) or pd.isna(right):
        return np.nan
    return round(float(left) - float(right), 6)


def _excluded_numbers(value: object) -> list[int]:
    text = str(value).strip()
    if not text:
        return []
    return [int(part) for part in text.split("|")]


def build_oos1_results(
    oos1: pd.DataFrame,
    candidates: pd.DataFrame,
    run_jst: str,
    source_commit_sha: str,
) -> pd.DataFrame:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit_sha):
        raise ValueError("Source implementation commit must be a full 40-char SHA")

    baseline_metrics = performance_metrics(oos1)
    rows: list[dict] = []
    for candidate in candidates.to_dict("records"):
        excluded = _excluded_numbers(candidate["ExcludedStrategyNos"])
        selected = oos1.loc[~oos1["StrategyNo"].isin(excluded)].copy()
        metrics = performance_metrics(selected)
        if excluded:
            excluded_total_r = float(
                oos1.loc[oos1["StrategyNo"].isin(excluded), "R"].sum()
            )
            if not np.isclose(
                float(metrics["TotalR"]) - float(baseline_metrics["TotalR"]),
                -excluded_total_r,
                atol=1e-6,
            ):
                raise AssertionError("Candidate Delta Total R identity failed")

        rows.append(
            {
                "AnalysisVersion": ANALYSIS_VERSION,
                "SourceImplementationCommitSHA": source_commit_sha,
                "CandidateFreezeCommitSHA": CANDIDATE_FREEZE_COMMIT_SHA,
                "CandidateFileSHA256": ACCEPTED_CANDIDATE_SHA256,
                "BaselineSHA256": ACCEPTED_BASELINE_SHA256,
                "PlanBranch": PLAN_BRANCH,
                "ValidationRunJST": run_jst,
                "Segment": "OOS1_2022_2025",
                "OOS1Viewed": True,
                "OOS2Viewed": False,
                "CandidateID": candidate["CandidateID"],
                "PortfolioLabel": candidate["PortfolioLabel"],
                "ExcludedStrategyNos": candidate["ExcludedStrategyNos"],
                "ExcludedStrategies": candidate["ExcludedStrategies"],
                **metrics,
                "DeltaTotalR": _delta(metrics, baseline_metrics, "TotalR"),
                "DeltaMaxDDR": _delta(metrics, baseline_metrics, "MaxDDR"),
                "DeltaPF": _delta(metrics, baseline_metrics, "PF"),
                "DeltaWorstDayR": _delta(metrics, baseline_metrics, "WorstDayR"),
                "DeltaWorstWeekR": _delta(metrics, baseline_metrics, "WorstWeekR"),
            }
        )

    result = pd.DataFrame(rows)
    if tuple(result["CandidateID"]) != EXPECTED_CANDIDATE_IDS:
        raise AssertionError("Output candidate order changed")
    if set(result["Segment"]) != {"OOS1_2022_2025"}:
        raise AssertionError("Output contains a non-OOS1 segment")
    if result["OOS2Viewed"].any():
        raise AssertionError("OOS2 must remain unopened")
    if any(column.endswith("_2026") for column in result.columns):
        raise AssertionError("OOS2 year column must not be written")
    return result


def write_output(output_dir: Path, results: pd.DataFrame) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILENAME
    if output_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite an existing one-time OOS1 result: {output_path}"
        )
    results.to_csv(output_path, index=False)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen Strategy Selection candidates on OOS1 once."
    )
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--candidates", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-commit-sha", required=True)
    parser.add_argument(
        "--confirm-oos1-view",
        action="store_true",
        help="Required acknowledgement that this run opens OOS1 once.",
    )
    parser.add_argument(
        "--mount-drive",
        action="store_true",
        help="Mount Google Drive in Colab before resolving input files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_oos1_view:
        raise RuntimeError("OOS1 remains closed; pass --confirm-oos1-view to open it")
    if args.mount_drive:
        if drive is None:
            raise RuntimeError("--mount-drive is available only in Google Colab")
        drive.mount("/content/drive")

    baseline_path = is_analysis.resolve_exact_file(
        args.baseline,
        BASELINE_CANDIDATES,
        ACCEPTED_BASELINE_SHA256,
        "Accepted Baseline Trade Log",
    )
    candidate_path = is_analysis.resolve_exact_file(
        args.candidates,
        CANDIDATE_CANDIDATES,
        ACCEPTED_CANDIDATE_SHA256,
        "Frozen candidate portfolios",
    )
    candidates = load_frozen_candidates(candidate_path)
    oos1 = load_oos1_only(baseline_path)
    run_jst = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    results = build_oos1_results(oos1, candidates, run_jst, args.source_commit_sha)
    output_path = write_output(args.output_dir, results)

    print("STRATEGY SELECTION OOS1 ANALYSIS COMPLETE")
    print(f"Baseline SHA-256: {ACCEPTED_BASELINE_SHA256}")
    print(f"Candidate file SHA-256: {ACCEPTED_CANDIDATE_SHA256}")
    print(f"OOS1 trades: {len(oos1):,}")
    print(results[["CandidateID", "TotalR", "DeltaTotalR"]].to_string(index=False))
    print("OOS2: NOT CALCULATED OR DISPLAYED")
    print(f"CSV OUTPUT: {output_path}")


if __name__ == "__main__":
    main()
