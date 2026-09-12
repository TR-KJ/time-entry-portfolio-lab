from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.research import strategy_selection_oos2_analysis as analysis


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = (
    ROOT
    / "results"
    / "strategy_selection"
    / "strategy_selection_candidates_frozen.csv"
)
OOS1_RESULT_PATH = (
    ROOT
    / "results"
    / "strategy_selection"
    / "strategy_selection_oos_results.csv"
)
SOURCE_COMMIT_SHA = "b" * 40


def reconstruct_frozen_oos1_result(directory: str) -> Path:
    """Recover the hash-locked OOS1 artifact from its unchanged history rows."""
    expanded = pd.read_csv(OOS1_RESULT_PATH, dtype=str, keep_default_na=False)
    frozen = expanded.iloc[:2].drop(
        columns=["PriorOOS1ResultsSHA256", "TotalR_2026"]
    )
    path = Path(directory) / "strategy_selection_oos1_results_frozen.csv"
    frozen.to_csv(path, index=False, lineterminator="\n")
    return path


def synthetic_trades(years: tuple[int, ...], period: str) -> pd.DataFrame:
    rows = []
    for strategy_no in range(1, 29):
        year = years[(strategy_no - 1) % len(years)]
        result_r = -0.25 if strategy_no == 10 else strategy_no / 100
        entry = pd.Timestamp(year=year, month=2, day=3, hour=9)
        rows.append(
            {
                "StrategyNo": strategy_no,
                "Strategy": "10_AJ_SatA"
                if strategy_no == 10
                else f"strategy_{strategy_no}",
                "Pair": "TEST",
                "Direction": "Long",
                "EntryTime": entry,
                "CloseTime": entry + pd.Timedelta(hours=1),
                "SL": 10.0,
                "TP": 10.0,
                "Pips": result_r * 10.0,
                "R": result_r,
                "ExitReason": "SL" if result_r < 0 else "TP",
                "Period": period,
            }
        )
    return pd.DataFrame(rows)


class StrategySelectionOOS2AnalysisTest(unittest.TestCase):
    def test_prior_oos1_result_is_hash_locked_and_unopened_for_oos2(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frozen_path = reconstruct_frozen_oos1_result(directory)
            self.assertEqual(
                analysis.oos1_analysis.is_analysis.file_sha256(frozen_path),
                analysis.ACCEPTED_OOS1_RESULTS_SHA256,
            )
            prior = analysis.load_frozen_oos1_results(frozen_path)
            self.assertEqual(
                tuple(prior["CandidateID"]), analysis.EXPECTED_CANDIDATE_IDS
            )
            self.assertTrue(prior["OOS1Viewed"].all())
            self.assertFalse(prior["OOS2Viewed"].any())

    def test_prior_oos1_hash_lock_rejects_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            frozen_path = reconstruct_frozen_oos1_result(directory)
            changed = Path(directory) / "oos1.csv"
            changed.write_text(
                frozen_path.read_text().replace("-4.258", "-4.259"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "hash changed"):
                analysis.load_frozen_oos1_results(changed)

    def test_final_holdout_uses_same_two_candidates(self) -> None:
        candidates = analysis.oos1_analysis.load_frozen_candidates(CANDIDATE_PATH)
        oos2_trades = synthetic_trades(analysis.OOS2_YEARS, "OOS2")
        result = analysis.build_segment_results(
            oos2_trades,
            candidates,
            "OOS2_2026_TO_2026_09_09",
            analysis.OOS2_YEARS,
            "test-run",
            SOURCE_COMMIT_SHA,
        )
        self.assertEqual(tuple(result["CandidateID"]), analysis.EXPECTED_CANDIDATE_IDS)
        self.assertTrue(result["OOS2Viewed"].all())
        self.assertEqual(set(result["Segment"]), {"OOS2_2026_TO_2026_09_09"})
        top1 = result.loc[result["CandidateID"].eq("P1_MINUS_TOP1")].iloc[0]
        self.assertAlmostEqual(top1["DeltaTotalR"], 0.25)

    def test_combined_output_preserves_historical_oos1_flags(self) -> None:
        candidates = analysis.oos1_analysis.load_frozen_candidates(CANDIDATE_PATH)
        with tempfile.TemporaryDirectory() as directory:
            frozen_path = reconstruct_frozen_oos1_result(directory)
            prior = analysis.load_frozen_oos1_results(frozen_path)
            oos1_trades = synthetic_trades(
                analysis.oos1_analysis.OOS1_YEARS, "OOS1"
            )
            oos2_trades = synthetic_trades(analysis.OOS2_YEARS, "OOS2")
            oos2_result = analysis.build_segment_results(
                oos2_trades,
                candidates,
                "OOS2_2026_TO_2026_09_09",
                analysis.OOS2_YEARS,
                "test-run",
                SOURCE_COMMIT_SHA,
            )
            combined_result = analysis.build_segment_results(
                pd.concat([oos1_trades, oos2_trades], ignore_index=True),
                candidates,
                "OOS_COMBINED_2022_TO_2026_09_09",
                analysis.COMBINED_OOS_YEARS,
                "test-run",
                SOURCE_COMMIT_SHA,
            )
            output = analysis.combine_results(prior, oos2_result, combined_result)
            self.assertEqual(len(output), 6)
            self.assertFalse(output.iloc[:2]["OOS2Viewed"].any())
            self.assertTrue(output.iloc[2:]["OOS2Viewed"].all())
            self.assertIn("TotalR_2026", output.columns)

    def test_final_output_refuses_overwrite(self) -> None:
        results = pd.DataFrame([{"Segment": "OOS2_2026_TO_2026_09_09"}])
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            first = analysis.write_output(output_dir, results)
            self.assertTrue(first.is_file())
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                analysis.write_output(output_dir, results)


if __name__ == "__main__":
    unittest.main()
