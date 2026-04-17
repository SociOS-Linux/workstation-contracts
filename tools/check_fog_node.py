#!/usr/bin/env python3
"""Minimal fog-node conformance checker scaffold.

This script is intentionally lightweight and dependency-free so it can serve as
an initial lane validator until the full contract runner integration is added.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_PATHS = [
    "/srv/fog/projects",
    "/srv/fog/models",
    "/srv/fog/datasets",
    "/srv/fog/topics",
    "/srv/fog/vector",
    "/srv/fog/cache",
    "/srv/fog/logs",
    "/srv/fog/secrets",
    "/srv/fog/tmp",
]


def check_paths() -> list[str]:
    failures: list[str] = []
    for path in REQUIRED_PATHS:
        if not Path(path).exists():
            failures.append(f"missing path: {path}")
    return failures


def check_container_host() -> list[str]:
    failures: list[str] = []
    if shutil.which("podman") is None and shutil.which("docker") is None:
        failures.append("no container host found (expected podman or docker)")
    return failures


def check_lvm() -> list[str]:
    failures: list[str] = []
    if shutil.which("vgs") is None:
        failures.append("LVM tools not found (expected vgs)")
        return failures
    try:
        subprocess.run(["vgs"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        failures.append("vgs command failed")
    return failures


def main() -> int:
    failures = []
    failures.extend(check_paths())
    failures.extend(check_container_host())
    failures.extend(check_lvm())

    result = {
        "contract": "fog-node",
        "passed": not failures,
        "failures": failures,
        "os": {
            "platform": sys.platform,
            "cwd": os.getcwd(),
        },
    }
    print(json.dumps(result, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
