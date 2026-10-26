"""Install the pinned pair without changing the user's active environment."""

from __future__ import annotations

import json
import os
import subprocess
import venv
from pathlib import Path

from recovery_lab.resources import DATA


def python_in(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def prepare_environments(destination: Path) -> dict[str, Path]:
    destination.mkdir(parents=True, exist_ok=True)
    result = {}
    for label in ("baseline", "candidate"):
        directory = destination / label
        marker = directory / ".recovery-lab-env.json"
        if directory.exists() and any(directory.iterdir()) and not marker.is_file():
            raise ValueError(
                f"Refusing to modify an unmanaged environment: {directory}"
            )
        if not python_in(directory).is_file():
            print(f"Creating {label} environment...", flush=True)
            venv.EnvBuilder(with_pip=True).create(directory)
        marker.write_text(
            json.dumps({"owner": "langgraph-recovery-lab", "label": label}) + "\n",
            encoding="utf-8",
        )
        python = python_in(directory).resolve()
        print(f"Installing pinned {label} requirements...", flush=True)
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--progress-bar",
                "off",
                "--quiet",
                "--no-input",
                "-r",
                str(DATA / "requirements" / f"{label}.txt"),
            ],
            check=True,
            cwd=destination,
        )
        subprocess.run([str(python), "-m", "pip", "check"], check=True, cwd=destination)
        result[label] = python
    return result
