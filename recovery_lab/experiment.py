from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict
from pathlib import Path

from recovery_lab.scenario import Options

WORKER = Path(__file__).with_name("worker.py")


def worker_environment() -> dict[str, str]:
    environment = dict(os.environ)
    # This lab never needs hosted tracing or model-service credentials.
    for name in list(environment):
        if name.startswith(("LANGSMITH_", "LANGCHAIN_")):
            environment.pop(name)
    environment.update(
        PYTHONUTF8="1",
        PYTHONIOENCODING="utf-8",
        PYTHONDONTWRITEBYTECODE="1",
        LANGSMITH_TRACING="false",
        LANGCHAIN_TRACING_V2="false",
    )
    return environment


def assess(first: dict, resumed: dict) -> dict:
    completed = first["completed"].get("slow", 0) == 1
    saved = "b" in first["saved_channels"]
    calls = resumed["calls"].get("slow", 0)
    state_correct = resumed["state"] == {"a": 1, "b": 1}
    different_processes = first["pid"] != resumed["pid"]
    same_runtime = first["runtime"] == resumed["runtime"]
    expected_calls = 1 if completed else 2
    recovery_correct = (
        state_correct
        and resumed["calls"].get("flaky") == 2
        and calls == expected_calls
        and (not completed or saved)
        and different_processes
        and same_runtime
    )
    if completed and not saved and calls > 1:
        observation = "completed-result-lost"
    elif completed and saved and calls == 1:
        observation = "completed-result-preserved"
    elif not completed and calls == 2:
        observation = "unfinished-node-retried"
    else:
        observation = "unexpected-result"
    return {
        "observation": observation,
        "slow_completed_before_exit": completed,
        "slow_result_saved": saved,
        "slow_total_calls": calls,
        "final_state_correct": state_correct,
        "recovery_correct": recovery_correct,
        "different_processes": different_processes,
        "same_runtime_across_restart": same_runtime,
    }


def run_case(
    python: Path,
    directory: Path,
    options: Options,
    *,
    timeout: int = 30,
) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    reports = []
    trace = []
    for stage in ("fail", "resume"):
        arguments = [
            str(python),
            str(WORKER),
            "--directory",
            str(directory.resolve()),
            "--stage",
            stage,
            "--mode",
            options.mode,
            "--durability",
            options.durability,
            "--async-policy",
            options.async_policy,
            "--delay-ms",
            str(options.delay_ms),
            "--dump-after",
            str(max(0.1, timeout * 0.75)),
        ]
        try:
            process = subprocess.run(
                arguments,
                cwd=directory,
                env=worker_environment(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            for name, output in (("stdout", error.stdout), ("stderr", error.stderr)):
                if isinstance(output, bytes):
                    output = output.decode("utf-8", errors="replace")
                (directory / f"{stage}.{name}.txt").write_text(
                    output or "", encoding="utf-8"
                )
            raise RuntimeError(
                f"{stage} timed out after {timeout}s; inspect {directory}"
            ) from error
        (directory / f"{stage}.stderr.txt").write_text(process.stderr, encoding="utf-8")
        if process.returncode:
            raise RuntimeError(
                f"{stage} exited with {process.returncode}; inspect {directory / (stage + '.stderr.txt')}"
            )
        try:
            report = json.loads(process.stdout)
        except json.JSONDecodeError as error:
            (directory / f"{stage}.stdout.txt").write_text(
                process.stdout, encoding="utf-8"
            )
            raise RuntimeError(f"{stage} did not return a JSON report") from error
        (directory / f"{stage}.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        reports.append(report)
        trace.extend(
            json.loads(line)
            for line in (directory / f"{stage}.trace.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    result = {
        "options": asdict(options),
        "assessment": assess(*reports),
        "stages": reports,
        "trace": trace,
    }
    (directory / "result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def compare_verdict(baseline: list[dict], candidate: list[dict]) -> str:
    if not baseline or len(baseline) != len(candidate):
        raise ValueError(
            "Compare matching nonempty sets of baseline and candidate cases"
        )
    for cases in (baseline, candidate):
        expected = cases[0]["stages"][0]["runtime"]
        if any(
            stage["runtime"] != expected for case in cases for stage in case["stages"]
        ):
            return "runtime-changed"
    if any(
        original["options"] != replacement["options"]
        for original, replacement in zip(baseline, candidate, strict=True)
    ):
        raise ValueError("Baseline and candidate scenarios must match")
    baseline_fingerprint = baseline[0]["stages"][0]["runtime"]["source_sha256_lf"]
    candidate_fingerprint = candidate[0]["stages"][0]["runtime"]["source_sha256_lf"]
    if baseline_fingerprint == candidate_fingerprint:
        return "same-implementation"
    if not all(
        case["assessment"]["recovery_correct"]
        and case["assessment"]["different_processes"]
        for case in candidate
    ):
        return "candidate-check-failed"
    if not any(
        case["assessment"]["observation"] == "completed-result-lost"
        for case in baseline
    ):
        return "baseline-bug-not-reproduced"
    return "observed-fix"


def verify_sources(report: dict) -> dict:
    return {
        label: {
            "matches_expected_source": (
                report[label][0]["stages"][0]["runtime"]["source_sha256_lf"]
                == report["provenance"][label]["source_sha256_lf"]
            ),
            "expected_ref": report["provenance"][label]["source_ref"],
        }
        for label in ("baseline", "candidate")
    }
