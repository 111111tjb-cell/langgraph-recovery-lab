"""Export a measured pinned-pair report for the repository documentation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recovery_lab.report import svg_report, write_reports  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--name", choices=("default", "matrix"), default="default")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("verdict") != "observed-fix":
        raise ValueError("Export an observed comparison, not a missing reproduction")
    if not all(
        report["source_verification"][label]["matches_expected_source"]
        for label in ("baseline", "candidate")
    ):
        raise ValueError("The example must match both pinned source revisions")
    destination = ROOT / "docs" / "results" / args.name
    destination.mkdir(parents=True, exist_ok=True)
    write_reports(destination, report)
    assets = ROOT / "docs" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    if args.name == "default":
        (assets / "comparison.svg").write_text(svg_report(report), encoding="utf-8")
    print(f"Exported measured report: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
