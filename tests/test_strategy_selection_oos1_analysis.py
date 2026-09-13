from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.research import strategy_selection_oos1_analysis as analysis


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = (
    ROOT
    / "results"
    / "strategy_selection"
    / "strategy_selection_candidates_frozen.csv"
)
SOURCE_COMMIT_SHA = "a" * 40


def synthetic_oos1_trades() -> pd.DataFrame:
    rows = []
    for strategy_no in range(1, 29):
        year = analysis.OOS1_YEARS[(strategy_no - 1) % len(analysis.OOS1_YEARS)]
        result_r = -0.5 if strategy_no == 10 else strategy_no / 100
        entry = pd.Timestamp(year=year, month=1, day=3, hour=9)
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
                "Period": "OOS1",
            }
        )
    return pd.DataFrame(rows)


class StrategySelectionOOS1AnalysisTest(unittest.TestCase):
    def test_frozen_candidates_are_exactly_the_predeclared_two(self) -> None:
        self.assertEqual(
            analysis.is_analysis.file_sha256(CANDIDATE_PATH),
            analysis.ACCEPTED_CANDIDATE_SHA256,
        )
        candidates = analysis.load_frozen_candidates(CANDIDATE_PATH)
        self.assertEqual(
            tuple(candidates["CandidateID"]), analysis.EXPECTED_CANDIDATE_IDS
        )
        self.assertEqual(
            str(
                candidates.loc[
                    candidates["CandidateID"].eq("P1_MINUS_TOP1"),
                    "ExcludedStrategyNos",
                ].iloc[0]
            ),
            "10",
        )

    def test_candidate_hash_lock_rejects_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "candidates.csv"
            changed.write_text(
                CANDIDATE_PATH.read_text().replace("10_AJ_SatA", "11_AJ_SatA"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "hash changed"):
                analysis.load_frozen_candidates(changed)

    def test_oos1_results_use_only_frozen_candidates_and_years(self) -> None:
        trades = synthetic_oos1_trades()
        candidates = analysis.load_frozen_candidates(CANDIDATE_PATH)
        results = analysis.build_oos1_results(
            trades, candidates, "test-run", SOURCE_COMMIT_SHA
        )
        self.assertEqual(tuple(results["CandidateID"]), analysis.EXPECTED_CANDIDATE_IDS)
        self.assertEqual(set(results["Segment"]), {"OOS1_2022_2025"})
        self.assertTrue(results["OOS1Viewed"].all())
        self.assertFalse(results["OOS2Viewed"].any())
        self.assertFalse(any(column.endswith("_2026") for column in results.columns))
        top1 = results.loc[results["CandidateID"].eq("P1_MINUS_TOP1")].iloc[0]
        self.assertAlmostEqual(top1["DeltaTotalR"], 0.5)

    def test_one_time_output_refuses_overwrite(self) -> None:
        results = pd.DataFrame([{"Segment": "OOS1_2022_2025"}])
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            first = analysis.write_output(output_dir, results)
            self.assertTrue(first.is_file())
            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                analysis.write_output(output_dir, results)


if __name__ == "__main__":
    unittest.main()
