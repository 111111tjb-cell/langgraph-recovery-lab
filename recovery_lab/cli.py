from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from recovery_lab import __version__
from recovery_lab.experiment import compare_verdict, run_case, verify_sources
from recovery_lab.prepare import prepare_environments, python_in
from recovery_lab.report import VERDICT_TEXT, write_reports
from recovery_lab.resources import DATA
from recovery_lab.scenario import Options


def _scenario_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=("sync", "async"), default="sync")
    parser.add_argument(
        "--durability", choices=("exit", "sync", "async"), default="exit"
    )
    parser.add_argument(
        "--async-policy", choices=("finish", "cancel"), default="finish"
    )
    parser.add_argument("--delay-ms", type=int, default=200)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Observe LangGraph recovery with SQLite and fresh processes."
    )
    result.add_argument("--version", action="version", version=__version__)
    subcommands = result.add_subparsers(dest="command", required=True)
    prepare = subcommands.add_parser(
        "prepare", help="Install the two pinned environments"
    )
    prepare.add_argument("--venvs", type=Path, default=Path.cwd() / ".venvs")
    compare = subcommands.add_parser(
        "compare", help="Measure baseline and candidate behavior"
    )
    compare.add_argument(
        "--baseline-python",
        type=Path,
        default=python_in(Path.cwd() / ".venvs" / "baseline"),
    )
    compare.add_argument(
        "--candidate-python",
        type=Path,
        default=python_in(Path.cwd() / ".venvs" / "candidate"),
    )
    compare.add_argument("--output", type=Path)
    compare.add_argument("--repeat", type=int, default=1)
    compare.add_argument(
        "--matrix",
        action="store_true",
        help="Both execution modes and all durability modes",
    )
    compare.add_argument(
        "--include-cancelled",
        action="store_true",
        help="Also observe async work that honors cancellation",
    )
    compare.add_argument(
        "--timeout", type=int, default=30, help="Maximum seconds per worker process"
    )
    _scenario_arguments(compare)
    run = subcommands.add_parser("run", help="Observe one installed implementation")
    run.add_argument("--python", type=Path, default=Path(sys.executable))
    run.add_argument("--output", type=Path)
    run.add_argument("--timeout", type=int, default=30)
    _scenario_arguments(run)
    return result


def _options(args) -> Options:
    return Options(args.mode, args.durability, args.async_policy, args.delay_ms)


def _output(args) -> Path:
    directory = args.output or Path.cwd() / "artifacts" / datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%S.%fZ"
    )
    directory = directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError(
            "Use a new or empty output directory; previous results are never overwritten"
        )
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _compare(args) -> int:
    if not 1 <= args.repeat <= 100:
        raise ValueError("repeat must be between 1 and 100")
    if not 1 <= args.timeout <= 300:
        raise ValueError("timeout must be between 1 and 300 seconds")
    options = _options(args)
    scenarios = [options]
    if args.matrix:
        scenarios = [
            Options(mode, durability, "finish", options.delay_ms)
            for mode in ("sync", "async")
            for durability in ("exit", "sync", "async")
        ]
    if args.include_cancelled:
        scenarios.extend(
            Options("async", durability, "cancel", options.delay_ms)
            for durability in (
                ("exit", "sync", "async") if args.matrix else (options.durability,)
            )
        )
    for python in (args.baseline_python, args.candidate_python):
        if not python.is_file():
            raise ValueError(
                f"Python not found: {python}. Run `python -m recovery_lab prepare` first"
            )
    directory = _output(args)
    report = {
        "schema_version": 1,
        "lab_version": __version__,
        "generated_at": datetime.now(UTC).isoformat(),
        "provenance": json.loads(
            (DATA / "provenance.json").read_text(encoding="utf-8")
        ),
        "baseline": [],
        "candidate": [],
    }
    for label, python in (
        ("baseline", args.baseline_python),
        ("candidate", args.candidate_python),
    ):
        for repetition in range(1, args.repeat + 1):
            for index, scenario in enumerate(scenarios, start=1):
                print(
                    f"{label:9} repeat {repetition}/{args.repeat} "
                    f"{scenario.mode}/{scenario.durability}/{scenario.async_policy}",
                    flush=True,
                )
                case = run_case(
                    python.resolve(),
                    directory / label / f"repeat-{repetition:03}-case-{index:02}",
                    scenario,
                    timeout=args.timeout,
                )
                case["repetition"] = repetition
                report[label].append(case)
                assessment = case["assessment"]
                print(
                    f"          B calls={assessment['slow_total_calls']} "
                    f"saved={assessment['slow_result_saved']} "
                    f"{assessment['observation']}",
                    flush=True,
                )
    report["verdict"] = compare_verdict(report["baseline"], report["candidate"])
    report["source_verification"] = verify_sources(report)
    write_reports(directory, report)
    print(f"\n{VERDICT_TEXT[report['verdict']]}")
    print(f"Report: {directory / 'index.html'}")
    return 0 if report["verdict"] == "observed-fix" else 2


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "prepare":
            environments = prepare_environments(args.venvs.resolve())
            print("\nReady. Run: python -m recovery_lab compare")
            for label, python in environments.items():
                print(f"{label}: {python}")
            return 0
        if args.command == "compare":
            return _compare(args)
        if not 1 <= args.timeout <= 300:
            raise ValueError("timeout must be between 1 and 300 seconds")
        directory = _output(args)
        result = run_case(
            args.python.resolve(),
            directory / "run",
            _options(args),
            timeout=args.timeout,
        )
        (directory / "result.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {"options": asdict(_options(args)), **result["assessment"]}, indent=2
            )
        )
        print(f"Result: {directory / 'result.json'}")
        return 0 if result["assessment"]["recovery_correct"] else 1
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"recovery-lab: {error}", file=sys.stderr)
        return 2
