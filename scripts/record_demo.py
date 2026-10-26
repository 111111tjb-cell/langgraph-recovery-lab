"""Record real CLI output in asciinema v2 format. Local paths are abbreviated."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cast", type=Path, default=ROOT / "docs/assets/demo.cast")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/recorded-demo")
    args = parser.parse_args()
    if args.cast.exists():
        raise ValueError(
            "Choose a new cast path; existing recordings are not overwritten"
        )
    command = [
        sys.executable,
        "-u",
        "-m",
        "recovery_lab",
        "compare",
        "--output",
        str(args.output),
    ]
    header = {
        "version": 2,
        "width": 110,
        "height": 24,
        "timestamp": int(time.time()),
        "title": "Real LangGraph recovery lab CLI output (local project path abbreviated)",
        "env": {"TERM": "xterm-256color"},
    }
    events = [[0, "o", "$ python -m recovery_lab compare\r\n"]]
    started = time.monotonic()
    with subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    ) as process:
        if process.stdout is None:
            raise RuntimeError("Missing stdout pipe")
        for line in process.stdout:
            line = line.replace(str(ROOT), "<project>")
            events.append(
                [
                    round(time.monotonic() - started, 6),
                    "o",
                    line.rstrip("\r\n") + "\r\n",
                ]
            )
            print(line, end="", flush=True)
        code = process.wait()
    events.append([round(time.monotonic() - started, 6), "o", f"exit_code={code}\r\n"])
    args.cast.parent.mkdir(parents=True, exist_ok=True)
    with args.cast.open("w", encoding="utf-8") as stream:
        for item in [header, *events]:
            stream.write(json.dumps(item, ensure_ascii=True) + "\n")
    print(f"Saved actual CLI recording: {args.cast}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
