from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from recovery_lab.experiment import (
    assess,
    compare_verdict,
    run_case,
    worker_environment,
)
from recovery_lab.prepare import prepare_environments
from recovery_lab.report import html_report, markdown_report, svg_report, write_reports
from recovery_lab.scenario import Options


def stages(*, completed=True, saved=True, calls=1, fingerprint="candidate"):
    runtime = {
        "python": "3.12.4",
        "platform": "test",
        "packages": {"langgraph": "1.2.17"},
        "source_sha256_lf": {"runner": fingerprint},
    }
    return (
        {
            "pid": 10,
            "completed": {"slow": 1} if completed else {},
            "saved_channels": ["__error__", "b"] if saved else ["__error__"],
            "runtime": runtime,
        },
        {
            "pid": 20,
            "state": {"a": 1, "b": 1},
            "calls": {"flaky": 2, "slow": calls},
            "runtime": runtime,
        },
    )


def case(**kwargs):
    first, resumed = stages(**kwargs)
    return {
        "options": {
            "mode": "sync",
            "durability": "exit",
            "async_policy": "finish",
            "delay_ms": 200,
        },
        "assessment": assess(first, resumed),
        "stages": [first, resumed],
        "trace": [],
    }


def report():
    baseline = case(saved=False, calls=2, fingerprint="baseline")
    candidate = case()
    return {
        "generated_at": "2026-10-25T00:00:00+00:00",
        "baseline": [baseline],
        "candidate": [candidate],
        "verdict": compare_verdict([baseline], [candidate]),
    }


class ObservationTests(unittest.TestCase):
    def test_completed_result_missing_is_not_a_successful_recovery(self):
        result = assess(*stages(saved=False, calls=2))
        self.assertEqual(result["observation"], "completed-result-lost")
        self.assertFalse(result["recovery_correct"])

    def test_final_state_alone_does_not_hide_repeated_work(self):
        first, resumed = stages(saved=True, calls=2)
        self.assertEqual(resumed["state"], {"a": 1, "b": 1})
        self.assertFalse(assess(first, resumed)["recovery_correct"])

    def test_unfinished_cancelled_work_should_be_retried(self):
        result = assess(*stages(completed=False, saved=False, calls=2))
        self.assertEqual(result["observation"], "unfinished-node-retried")
        self.assertTrue(result["recovery_correct"])

    def test_success_requires_the_expected_final_state(self):
        first, resumed = stages()
        resumed["state"] = {"a": 1}
        self.assertFalse(assess(first, resumed)["recovery_correct"])

    def test_same_source_cannot_establish_a_fix(self):
        baseline, candidate = case(), case()
        self.assertEqual(
            compare_verdict([baseline], [candidate]), "same-implementation"
        )

    def test_no_baseline_reproduction_is_reported_explicitly(self):
        baseline, candidate = case(fingerprint="baseline"), case()
        self.assertEqual(
            compare_verdict([baseline], [candidate]), "baseline-bug-not-reproduced"
        )

    def test_candidate_failure_is_not_overridden_by_baseline_failure(self):
        baseline = case(saved=False, calls=2, fingerprint="baseline")
        candidate = case(saved=False, calls=2)
        self.assertEqual(
            compare_verdict([baseline], [candidate]), "candidate-check-failed"
        )

    def test_recovery_must_use_a_different_process(self):
        baseline = case(saved=False, calls=2, fingerprint="baseline")
        candidate = case()
        candidate["assessment"]["different_processes"] = False
        self.assertEqual(
            compare_verdict([baseline], [candidate]), "candidate-check-failed"
        )

    def test_distinct_sources_and_correct_candidate_establish_observed_fix(self):
        self.assertEqual(report()["verdict"], "observed-fix")

    def test_a_runtime_change_during_recovery_is_inconclusive(self):
        baseline = case(saved=False, calls=2, fingerprint="baseline")
        candidate = case()
        candidate["stages"][1]["runtime"] = copy.deepcopy(
            candidate["stages"][1]["runtime"]
        )
        candidate["stages"][1]["runtime"]["source_sha256_lf"] = {"runner": "changed"}
        self.assertEqual(compare_verdict([baseline], [candidate]), "runtime-changed")

    def test_mismatched_scenarios_cannot_be_compared(self):
        baseline = case(saved=False, calls=2, fingerprint="baseline")
        candidate = case()
        candidate["options"]["durability"] = "sync"
        with self.assertRaisesRegex(ValueError, "scenarios must match"):
            compare_verdict([baseline], [candidate])

    def test_hosted_tracing_is_disabled_without_mutating_parent_environment(self):
        with patch.dict(
            os.environ,
            {"LANGSMITH_API_KEY": "test-only-secret", "LANGCHAIN_TRACING_V2": "true"},
        ):
            environment = worker_environment()
            self.assertNotIn("LANGSMITH_API_KEY", environment)
            self.assertEqual(environment["LANGCHAIN_TRACING_V2"], "false")
            self.assertEqual(os.environ["LANGCHAIN_TRACING_V2"], "true")

    def test_unmanaged_environment_is_left_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "baseline"
            directory.mkdir()
            sentinel = directory / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unmanaged"):
                prepare_environments(Path(temporary))
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_bounded_injected_delay(self):
        for value in (0, -1, 5001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Options(delay_ms=value)

    def test_timeout_keeps_diagnostic_output(self):
        failure = subprocess.TimeoutExpired(
            ["worker"], 1, output=b"partial output", stderr=b"diagnostic stack"
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "run"
            with patch("recovery_lab.experiment.subprocess.run", side_effect=failure):
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    run_case(Path(sys.executable), directory, Options(), timeout=1)
            self.assertEqual(
                (directory / "fail.stderr.txt").read_text(encoding="utf-8"),
                "diagnostic stack",
            )
            self.assertEqual(
                (directory / "fail.stdout.txt").read_text(encoding="utf-8"),
                "partial output",
            )


class ReportTests(unittest.TestCase):
    def test_html_data_cannot_close_its_script_element(self):
        data = report()
        payload = "</script><script>alert('test')</script>"
        data["candidate"][0]["stages"][0]["runtime"]["packages"]["test"] = payload
        output = html_report(data)
        self.assertNotIn(payload, output)
        self.assertIn("\\u003c/script>", output)

    def test_negative_verdict_is_visible_in_each_report_format(self):
        data = report()
        data["verdict"] = "baseline-bug-not-reproduced"
        self.assertIn("not observed", markdown_report(data))
        self.assertIn("not observed", svg_report(data))
        self.assertIn('"verdict": "baseline-bug-not-reproduced"', html_report(data))

    def test_export_keeps_source_fingerprints_and_observations(self):
        data = report()
        original = copy.deepcopy(data)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            write_reports(directory, data)
            loaded = json.loads(
                (directory / "comparison.json").read_text(encoding="utf-8")
            )
            self.assertEqual(loaded, data)
            self.assertTrue((directory / "index.html").is_file())
            self.assertTrue((directory / "comparison.svg").is_file())
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()
