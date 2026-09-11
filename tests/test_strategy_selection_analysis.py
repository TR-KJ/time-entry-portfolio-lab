from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.research import strategy_selection_analysis as analysis


ROOT = Path(__file__).resolve().parents[1]
MEMBERSHIP_PATH = (
    ROOT
    / "results"
    / "strategy_selection"
    / "strategy_selection_group_membership.csv"
)


def synthetic_is_trades() -> pd.DataFrame:
    rows = []
    for strategy_no in range(1, 29):
        year = analysis.IS_YEARS[(strategy_no - 1) % len(analysis.IS_YEARS)]
        result_r = -0.5 if strategy_no == 1 else strategy_no / 100
        entry = pd.Timestamp(year=year, month=1, day=2, hour=9)
        rows.append(
            {
                "StrategyNo": strategy_no,
                "Strategy": f"strategy_{strategy_no}",
                "Pair": "TEST",
                "Direction": "Long",
                "EntryTime": entry,
                "CloseTime": entry + pd.Timedelta(hours=1),
                "SL": 10.0,
                "TP": 10.0,
                "Pips": result_r * 10.0,
                "R": result_r,
                "ExitReason": "SL" if result_r < 0 else "TP",
                "Period": "IS",
            }
        )
    return pd.DataFrame(rows)


class StrategySelectionAnalysisTest(unittest.TestCase):
    def test_frozen_membership_loads_and_has_all_groups(self) -> None:
        self.assertEqual(
            analysis.file_sha256(MEMBERSHIP_PATH),
            analysis.ACCEPTED_MEMBERSHIP_SHA256,
        )
        membership = analysis.load_membership(MEMBERSHIP_PATH)
        self.assertEqual(len(membership), 28)
        self.assertEqual(membership["StrategyNo"].tolist(), list(range(1, 29)))
        for group in analysis.GROUP_COLUMNS:
            self.assertTrue(membership[group].any())

    def test_performance_metrics_use_close_order_and_jst_periods(self) -> None:
        frame = synthetic_is_trades().iloc[:4].copy()
        frame.loc[:, "R"] = [-1.0, -0.5, 0.25, 1.0]
        frame.loc[:, "Pips"] = frame["R"] * frame["SL"]
        metrics = analysis.performance_metrics(frame)
        self.assertEqual(metrics["Trades"], 4)
        self.assertAlmostEqual(metrics["TotalR"], -0.25)
        self.assertAlmostEqual(metrics["MaxDDR"], 1.5)
        self.assertEqual(metrics["MaxLosingStreak"], 2)
        self.assertEqual(
            metrics["PositiveYears"]
            + metrics["NegativeYears"]
            + metrics["NeutralYears"],
            7,
        )

    def test_leave_one_out_reconciles_total_r(self) -> None:
        trades = synthetic_is_trades()
        health_rows = []
        for strategy_no in range(1, 29):
            part = trades.loc[trades["StrategyNo"].eq(strategy_no)]
            health_rows.append(
                {
                    "StrategyNo": strategy_no,
                    "Strategy": f"strategy_{strategy_no}",
                    **analysis.performance_metrics(part),
                }
            )
        health = pd.DataFrame(health_rows)
        loo = analysis.build_leave_one_out_table(trades, health, "test-run")
        removed_one = loo.loc[loo["RemovedStrategyNo"].eq(1)].iloc[0]
        self.assertAlmostEqual(removed_one["DeltaTotalR"], 0.5)
        self.assertTrue(bool(removed_one["ClearNegativeMarginalCandidate"]))
        self.assertEqual(loo.iloc[0]["RemovedStrategyNo"], 1)

    def test_written_outputs_contain_no_oos_columns(self) -> None:
        frame = pd.DataFrame(
            [{"Segment": "IS_2015_2021", "Value": 1}]
        )
        with tempfile.TemporaryDirectory() as directory:
            paths = analysis.write_outputs(Path(directory), frame, frame, frame)
            self.assertEqual(len(paths), 3)
            for path in paths:
                written = pd.read_csv(path)
                self.assertFalse(
                    any(column.upper().startswith("OOS") for column in written.columns)
                )


if __name__ == "__main__":
    unittest.main()
