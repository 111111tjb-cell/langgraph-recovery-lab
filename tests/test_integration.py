"""Opt in with RECOVERY_LAB_TEST_PYTHON pointing at the candidate environment."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from recovery_lab.experiment import run_case
from recovery_lab.scenario import Options

PYTHON = os.environ.get("RECOVERY_LAB_TEST_PYTHON")


@unittest.skipUnless(
    PYTHON, "Set RECOVERY_LAB_TEST_PYTHON for fresh-process integration tests"
)
class ProcessRecoveryTests(unittest.TestCase):
    def test_completed_sync_node_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_case(Path(PYTHON), Path(temporary) / "run", Options())
        self.assertTrue(result["assessment"]["recovery_correct"])
        self.assertTrue(result["assessment"]["different_processes"])
        self.assertEqual(result["assessment"]["slow_total_calls"], 1)

    def test_cancelled_async_node_is_retried(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_case(
                Path(PYTHON),
                Path(temporary) / "run",
                Options(mode="async", async_policy="cancel"),
            )
        self.assertTrue(result["assessment"]["recovery_correct"])
        self.assertEqual(result["assessment"]["observation"], "unfinished-node-retried")

    def test_existing_result_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "run"
            directory.mkdir()
            sentinel = directory / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                run_case(Path(PYTHON), directory, Options())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
