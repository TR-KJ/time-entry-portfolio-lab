"""One-time OOS2 final-holdout evaluation for frozen Strategy Selection candidates.

The program locks the accepted Baseline, frozen candidates, and recorded OOS1
result by SHA-256. It evaluates only the same two candidates on OOS2, verifies
that a recomputation of OOS1 still matches the frozen record, and writes OOS1,
OOS2, and combined-OOS rows to a new output file. It never reads M1 prices or
changes EA, VPS, SET, or live-operation files.
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
    from src.research import strategy_selection_oos1_analysis as oos1_analysis
except ModuleNotFoundError:  # permits direct execution from the repository root
    import strategy_selection_oos1_analysis as oos1_analysis


ANALYSIS_VERSION = "strategy-selection-oos2-v1.0.0"
PLAN_BRANCH = oos1_analysis.PLAN_BRANCH
ACCEPTED_BASELINE_SHA256 = oos1_analysis.ACCEPTED_BASELINE_SHA256
ACCEPTED_CANDIDATE_SHA256 = oos1_analysis.ACCEPTED_CANDIDATE_SHA256
ACCEPTED_OOS1_RESULTS_SHA256 = (
    "9042c26a797b0db9ac6a70938b5cad8a645af001ecd878faa0f94174025a6aa2"
)
CANDIDATE_FREEZE_COMMIT_SHA = oos1_analysis.CANDIDATE_FREEZE_COMMIT_SHA
EXPECTED_TRADE_ROWS = 16_298
EXPECTED_OOS2_TRADES = 995
EXPECTED_OOS2_TOTAL_R = 19.818791
OOS2_START = pd.Timestamp("2026-01-01")
OOS2_END_EXCLUSIVE = pd.Timestamp("2026-09-10")
OOS2_YEARS = (2026,)
COMBINED_OOS_YEARS = tuple(range(2022, 2027))
FLOAT_TOLERANCE = 1e-8

BASELINE_CANDIDATES = oos1_analysis.BASELINE_CANDIDATES
CANDIDATE_CANDIDATES = oos1_analysis.CANDIDATE_CANDIDATES
PRIOR_OOS_RESULTS_CANDIDATES = (
    Path(
        "/content/drive/MyDrive/time-entry-portfolio-lab/strategy_selection/"
        "strategy_selection_oos_results.csv"
    ),
    Path("/content/strategy_selection_oos_results.csv"),
    Path("results/strategy_selection/strategy_selection_oos_results.csv"),
)
DEFAULT_OUTPUT_DIR = Path("/content")
OUTPUT_FILENAME = "strategy_selection_oos_results.csv"

EXPECTED_CANDIDATE_IDS = oos1_analysis.EXPECTED_CANDIDATE_IDS
REQUIRED_BASELINE_COLUMNS = oos1_analysis.REQUIRED_BASELINE_COLUMNS
REQUIRED_PRIOR_COLUMNS = {
    "AnalysisVersion",
    "SourceImplementationCommitSHA",
    "CandidateFreezeCommitSHA",
    "CandidateFileSHA256",
    "BaselineSHA256",
    "PlanBranch",
    "ValidationRunJST",
    "Segment",
    "OOS1Viewed",
    "OOS2Viewed",
    "CandidateID",
    "PortfolioLabel",
    "ExcludedStrategyNos",
    "ExcludedStrategies",
    "Trades",
    "TotalR",
    "PF",
    "WinRatePct",
    "AvgR",
    "AvgWinR",
    "AvgLossR",
    "MaxDDR",
    "WorstDayR",
    "WorstWeekR",
    "PositiveYears",
    "NegativeYears",
    "NeutralYears",
    "MaxLosingStreak",
    "TPExitRatePct",
    "SLExitRatePct",
    "TimeExitRatePct",
    "OtherExitRatePct",
    "TotalR_2022",
    "TotalR_2023",
    "TotalR_2024",
    "TotalR_2025",
    "DeltaTotalR",
    "DeltaMaxDDR",
    "DeltaPF",
    "DeltaWorstDayR",
    "DeltaWorstWeekR",
}
METRIC_COLUMNS = [
    "Trades",
    "TotalR",
    "PF",
    "WinRatePct",
    "AvgR",
    "AvgWinR",
    "AvgLossR",
    "MaxDDR",
    "WorstDayR",
    "WorstWeekR",
    "PositiveYears",
    "NegativeYears",
    "NeutralYears",
    "MaxLosingStreak",
    "TPExitRatePct",
    "SLExitRatePct",
    "TimeExitRatePct",
    "OtherExitRatePct",
]
YEAR_COLUMNS = [f"TotalR_{year}" for year in COMBINED_OOS_YEARS]
DELTA_COLUMNS = [
    "DeltaTotalR",
    "DeltaMaxDDR",
    "DeltaPF",
    "DeltaWorstDayR",
    "DeltaWorstWeekR",
]
METADATA_COLUMNS = [
    "AnalysisVersion",
    "SourceImplementationCommitSHA",
    "CandidateFreezeCommitSHA",
    "CandidateFileSHA256",
    "PriorOOS1ResultsSHA256",
    "BaselineSHA256",
    "PlanBranch",
    "ValidationRunJST",
    "Segment",
    "OOS1Viewed",
    "OOS2Viewed",
    "CandidateID",
    "PortfolioLabel",
    "ExcludedStrategyNos",
    "ExcludedStrategies",
]
OUTPUT_COLUMNS = METADATA_COLUMNS + METRIC_COLUMNS + YEAR_COLUMNS + DELTA_COLUMNS


def _parse_boolean(series: pd.Series, column: str) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    mapping = {"true": True, "false": False}
    unknown = sorted(set(normalized) - set(mapping))
    if unknown:
        raise ValueError(f"Unknown boolean values in {column}: {unknown}")
    return normalized.map(mapping).astype(bool)


def load_frozen_oos1_results(path: Path) -> pd.DataFrame:
    if oos1_analysis.is_analysis.file_sha256(path) != ACCEPTED_OOS1_RESULTS_SHA256:
        raise RuntimeError("Frozen OOS1 results hash changed; OOS2 aborted")

    prior = pd.read_csv(path, keep_default_na=False)
    missing = sorted(REQUIRED_PRIOR_COLUMNS - set(prior.columns))
    if missing:
        raise ValueError(f"OOS1 result columns missing: {missing}")
    if len(prior) != 2:
        raise AssertionError("Frozen OOS1 result must contain exactly two rows")
    if tuple(prior["CandidateID"].astype(str)) != EXPECTED_CANDIDATE_IDS:
        raise AssertionError("OOS1 result candidates changed")
    if set(prior["Segment"].astype(str)) != {"OOS1_2022_2025"}:
        raise AssertionError("Prior result is not the frozen OOS1 segment")
    if set(prior["CandidateFreezeCommitSHA"].astype(str)) != {
        CANDIDATE_FREEZE_COMMIT_SHA
    }:
        raise AssertionError("OOS1 result candidate freeze commit changed")
    if set(prior["CandidateFileSHA256"].astype(str)) != {
        ACCEPTED_CANDIDATE_SHA256
    }:
        raise AssertionError("OOS1 result refers to another candidate file")
    if set(prior["BaselineSHA256"].astype(str)) != {
        ACCEPTED_BASELINE_SHA256
    }:
        raise AssertionError("OOS1 result refers to another Baseline")
    if set(prior["PlanBranch"].astype(str)) != {PLAN_BRANCH}:
        raise AssertionError("OOS1 result refers to another plan branch")
    if not _parse_boolean(prior["OOS1Viewed"], "OOS1Viewed").all():
        raise AssertionError("OOS1 result is not marked viewed")
    if _parse_boolean(prior["OOS2Viewed"], "OOS2Viewed").any():
        raise AssertionError("OOS2 is already marked viewed")
    if "TotalR_2026" in prior.columns:
        raise AssertionError("Frozen OOS1 result unexpectedly contains 2026")
    prior["OOS1Viewed"] = True
    prior["OOS2Viewed"] = False
    return prior


def _prepare_numeric_and_time_columns(trades: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_BASELINE_COLUMNS - set(trades.columns))
    if missing:
        raise ValueError(f"Baseline columns missing: {missing}")
    for column in ("EntryTime", "CloseTime"):
        trades[column] = pd.to_datetime(trades[column], errors="raise")
    for column in ("StrategyNo", "SL", "TP", "Pips", "R"):
        trades[column] = pd.to_numeric(trades[column], errors="raise")
    trades["StrategyNo"] = trades["StrategyNo"].astype(int)
    return trades


def _validate_oos2_frame(trades: pd.DataFrame) -> pd.DataFrame:
    trades = _prepare_numeric_and_time_columns(trades)
    if len(trades) != EXPECTED_OOS2_TRADES:
        raise AssertionError(
            f"Expected {EXPECTED_OOS2_TRADES:,} OOS2 trades, found {len(trades):,}"
        )
    if not np.isclose(trades["R"].sum(), EXPECTED_OOS2_TOTAL_R, atol=1e-6):
        raise AssertionError("Accepted OOS2 Baseline Total R changed")
    in_range = (trades["EntryTime"] >= OOS2_START) & (
        trades["EntryTime"] < OOS2_END_EXCLUSIVE
    )
    if not in_range.all() or not trades["Period"].astype(str).eq("OOS2").all():
        raise AssertionError("OOS2 selection contains a non-OOS2 row")
    if tuple(sorted(trades["EntryTime"].dt.year.unique())) != OOS2_YEARS:
        raise AssertionError("OOS2 year must be exactly 2026")
    if trades["Strategy"].nunique() != 28:
        raise AssertionError("OOS2 must contain all 28 frozen strategies")
    if sorted(trades["StrategyNo"].unique()) != list(range(1, 29)):
        raise AssertionError("OOS2 strategy numbers must be exactly 1..28")
    if (trades["CloseTime"] < trades["EntryTime"]).any():
        raise AssertionError("CloseTime precedes EntryTime")
    if trades.duplicated(["StrategyNo", "EntryTime"]).any():
        raise AssertionError("Duplicate StrategyNo + EntryTime rows")
    if not np.allclose(
        trades["R"], trades["Pips"] / trades["SL"], atol=FLOAT_TOLERANCE
    ):
        raise AssertionError("R != Pips / SL in OOS2")
    sl_rows = trades["ExitReason"].astype(str).str.upper().eq("SL")
    if not np.allclose(trades.loc[sl_rows, "R"], -1.0, atol=FLOAT_TOLERANCE):
        raise AssertionError("OOS2 SL rows must equal -1R")
    return trades.sort_values(
        ["EntryTime", "StrategyNo", "CloseTime"], kind="mergesort"
    ).reset_index(drop=True)


def load_final_oos_slices(path: Path, chunksize: int = 4096) -> tuple[pd.DataFrame, pd.DataFrame]:
    if oos1_analysis.is_analysis.file_sha256(path) != ACCEPTED_BASELINE_SHA256:
        raise RuntimeError("Baseline hash changed; OOS2 aborted")

    total_rows = 0
    oos_parts: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        total_rows += len(chunk)
        if "Period" not in chunk.columns:
            raise ValueError("Baseline column missing: Period")
        selected = chunk.loc[
            chunk["Period"].astype(str).isin({"OOS1", "OOS2"})
        ].copy()
        if len(selected):
            oos_parts.append(selected)
    if total_rows != EXPECTED_TRADE_ROWS:
        raise AssertionError(
            f"Expected {EXPECTED_TRADE_ROWS:,} full rows, found {total_rows:,}"
        )
    if not oos_parts:
        raise AssertionError("No OOS rows found")

    oos = pd.concat(oos_parts, ignore_index=True)
    oos1_raw = oos.loc[oos["Period"].astype(str).eq("OOS1")].copy()
    oos2_raw = oos.loc[oos["Period"].astype(str).eq("OOS2")].copy()
    oos1 = oos1_analysis._validate_oos1_frame(oos1_raw)
    oos2 = _validate_oos2_frame(oos2_raw)
    return oos1, oos2


def _max_losing_streak(values: pd.Series) -> int:
    longest = current = 0
    for value in values.astype(float):
        if value < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def performance_metrics(
    frame: pd.DataFrame, years: tuple[int, ...]
) -> dict[str, float | int]:
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
        .reindex(years, fill_value=0.0)
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
    for year in years:
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


def build_segment_results(
    trades: pd.DataFrame,
    candidates: pd.DataFrame,
    segment: str,
    years: tuple[int, ...],
    run_jst: str,
    source_commit_sha: str,
) -> pd.DataFrame:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit_sha):
        raise ValueError("Source implementation commit must be a full 40-char SHA")
    if segment not in {"OOS2_2026_TO_2026_09_09", "OOS_COMBINED_2022_TO_2026_09_09"}:
        raise ValueError("Unexpected final-holdout segment")

    baseline_metrics = performance_metrics(trades, years)
    rows: list[dict] = []
    for candidate in candidates.to_dict("records"):
        excluded = _excluded_numbers(candidate["ExcludedStrategyNos"])
        selected = trades.loc[~trades["StrategyNo"].isin(excluded)].copy()
        metrics = performance_metrics(selected, years)
        if excluded:
            excluded_total_r = float(
                trades.loc[trades["StrategyNo"].isin(excluded), "R"].sum()
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
                "PriorOOS1ResultsSHA256": ACCEPTED_OOS1_RESULTS_SHA256,
                "BaselineSHA256": ACCEPTED_BASELINE_SHA256,
                "PlanBranch": PLAN_BRANCH,
                "ValidationRunJST": run_jst,
                "Segment": segment,
                "OOS1Viewed": True,
                "OOS2Viewed": True,
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
    return result


def verify_recomputed_oos1(
    oos1: pd.DataFrame, candidates: pd.DataFrame, prior: pd.DataFrame
) -> None:
    baseline_metrics = performance_metrics(oos1, oos1_analysis.OOS1_YEARS)
    numeric_columns = METRIC_COLUMNS + [
        "TotalR_2022",
        "TotalR_2023",
        "TotalR_2024",
        "TotalR_2025",
        *DELTA_COLUMNS,
    ]
    recomputed_rows: list[dict] = []
    for candidate in candidates.to_dict("records"):
        excluded = _excluded_numbers(candidate["ExcludedStrategyNos"])
        selected = oos1.loc[~oos1["StrategyNo"].isin(excluded)].copy()
        metrics = performance_metrics(selected, oos1_analysis.OOS1_YEARS)
        recomputed_rows.append(
            {
                "CandidateID": candidate["CandidateID"],
                **metrics,
                "DeltaTotalR": _delta(metrics, baseline_metrics, "TotalR"),
                "DeltaMaxDDR": _delta(metrics, baseline_metrics, "MaxDDR"),
                "DeltaPF": _delta(metrics, baseline_metrics, "PF"),
                "DeltaWorstDayR": _delta(metrics, baseline_metrics, "WorstDayR"),
                "DeltaWorstWeekR": _delta(metrics, baseline_metrics, "WorstWeekR"),
            }
        )
    recomputed = pd.DataFrame(recomputed_rows).set_index("CandidateID")
    recorded = prior.set_index("CandidateID")
    for candidate_id in EXPECTED_CANDIDATE_IDS:
        for column in numeric_columns:
            left = float(recomputed.loc[candidate_id, column])
            right = float(recorded.loc[candidate_id, column])
            if not np.isclose(left, right, atol=1e-9):
                raise AssertionError(
                    f"Frozen OOS1 result changed: {candidate_id} {column}"
                )


def combine_results(
    prior: pd.DataFrame, oos2: pd.DataFrame, combined: pd.DataFrame
) -> pd.DataFrame:
    prior = prior.copy()
    prior["PriorOOS1ResultsSHA256"] = ACCEPTED_OOS1_RESULTS_SHA256
    for column in OUTPUT_COLUMNS:
        if column not in prior.columns:
            prior[column] = pd.NA
    for frame in (oos2, combined):
        for column in OUTPUT_COLUMNS:
            if column not in frame.columns:
                frame[column] = pd.NA

    output = pd.concat(
        [
            prior[OUTPUT_COLUMNS],
            oos2[OUTPUT_COLUMNS],
            combined[OUTPUT_COLUMNS],
        ],
        ignore_index=True,
    )
    expected_segments = (
        "OOS1_2022_2025",
        "OOS1_2022_2025",
        "OOS2_2026_TO_2026_09_09",
        "OOS2_2026_TO_2026_09_09",
        "OOS_COMBINED_2022_TO_2026_09_09",
        "OOS_COMBINED_2022_TO_2026_09_09",
    )
    if tuple(output["Segment"].astype(str)) != expected_segments:
        raise AssertionError("Combined output segment order changed")
    if tuple(output["CandidateID"].astype(str)) != EXPECTED_CANDIDATE_IDS * 3:
        raise AssertionError("Combined output candidate order changed")
    if _parse_boolean(output.iloc[:2]["OOS2Viewed"], "OOS2Viewed").any():
        raise AssertionError("Historical OOS1 rows must retain OOS2Viewed=False")
    if not _parse_boolean(output.iloc[2:]["OOS2Viewed"], "OOS2Viewed").all():
        raise AssertionError("OOS2 and combined rows must record OOS2Viewed=True")
    return output


def write_output(output_dir: Path, results: pd.DataFrame) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILENAME
    if output_path.exists():
        raise FileExistsError(
            f"Refusing to overwrite an existing final OOS output: {output_path}"
        )
    results.to_csv(output_path, index=False)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open the final OOS2 holdout once for frozen candidates."
    )
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--candidates", type=Path, default=None)
    parser.add_argument("--prior-oos-results", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-commit-sha", required=True)
    parser.add_argument(
        "--confirm-oos2-view",
        action="store_true",
        help="Required acknowledgement that this run opens final-holdout OOS2 once.",
    )
    parser.add_argument(
        "--mount-drive",
        action="store_true",
        help="Mount Google Drive in Colab before resolving input files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.confirm_oos2_view:
        raise RuntimeError("OOS2 remains closed; pass --confirm-oos2-view to open it")
    if args.mount_drive:
        if drive is None:
            raise RuntimeError("--mount-drive is available only in Google Colab")
        drive.mount("/content/drive")

    baseline_path = oos1_analysis.is_analysis.resolve_exact_file(
        args.baseline,
        BASELINE_CANDIDATES,
        ACCEPTED_BASELINE_SHA256,
        "Accepted Baseline Trade Log",
    )
    candidate_path = oos1_analysis.is_analysis.resolve_exact_file(
        args.candidates,
        CANDIDATE_CANDIDATES,
        ACCEPTED_CANDIDATE_SHA256,
        "Frozen candidate portfolios",
    )
    prior_path = oos1_analysis.is_analysis.resolve_exact_file(
        args.prior_oos_results,
        PRIOR_OOS_RESULTS_CANDIDATES,
        ACCEPTED_OOS1_RESULTS_SHA256,
        "Frozen OOS1 results",
    )

    candidates = oos1_analysis.load_frozen_candidates(candidate_path)
    prior = load_frozen_oos1_results(prior_path)
    oos1, oos2 = load_final_oos_slices(baseline_path)
    verify_recomputed_oos1(oos1, candidates, prior)

    run_jst = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds")
    oos2_results = build_segment_results(
        oos2,
        candidates,
        "OOS2_2026_TO_2026_09_09",
        OOS2_YEARS,
        run_jst,
        args.source_commit_sha,
    )
    combined_trades = pd.concat([oos1, oos2], ignore_index=True)
    combined_results = build_segment_results(
        combined_trades,
        candidates,
        "OOS_COMBINED_2022_TO_2026_09_09",
        COMBINED_OOS_YEARS,
        run_jst,
        args.source_commit_sha,
    )
    output = combine_results(prior, oos2_results, combined_results)
    output_path = write_output(args.output_dir, output)

    print("STRATEGY SELECTION OOS2 FINAL HOLDOUT COMPLETE")
    print(f"Baseline SHA-256: {ACCEPTED_BASELINE_SHA256}")
    print(f"Candidate file SHA-256: {ACCEPTED_CANDIDATE_SHA256}")
    print(f"Prior OOS1 result SHA-256: {ACCEPTED_OOS1_RESULTS_SHA256}")
    print(f"OOS2 trades: {len(oos2):,}")
    print("OOS2")
    print(oos2_results[["CandidateID", "TotalR", "DeltaTotalR"]].to_string(index=False))
    print("OOS COMBINED")
    print(combined_results[["CandidateID", "TotalR", "DeltaTotalR"]].to_string(index=False))
    print(f"CSV OUTPUT: {output_path}")


if __name__ == "__main__":
    main()
