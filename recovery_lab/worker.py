"""Run as a file so each interpreter loads its own LangGraph installation."""

from __future__ import annotations

import argparse
import faulthandler
import json
from pathlib import Path

from scenario import Options, run_stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--stage", choices=("fail", "resume"), required=True)
    parser.add_argument("--mode", choices=("sync", "async"), required=True)
    parser.add_argument(
        "--durability", choices=("exit", "sync", "async"), required=True
    )
    parser.add_argument("--async-policy", choices=("finish", "cancel"), required=True)
    parser.add_argument("--delay-ms", type=int, required=True)
    parser.add_argument("--dump-after", type=float, default=0)
    args = parser.parse_args()
    options = Options(args.mode, args.durability, args.async_policy, args.delay_ms)
    if args.dump_after > 0:
        faulthandler.dump_traceback_later(args.dump_after)
    try:
        print(json.dumps(run_stage(args.directory.resolve(), args.stage, options)))
    finally:
        faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
