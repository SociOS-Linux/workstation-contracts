#!/usr/bin/env python3
"""Fog-node conformance checker.

Two lanes:

* ``--check-contract PATH`` (offline, CI-safe): validate the fog-node contract
  document and cross-check that this checker's required paths agree with the
  contract's declared requirements. No host access.
* ``--check-host`` (default): runtime checks of the actual fog node (required
  paths, container host, LVM). Intended to run ON a fog node, not in CI.

Both lanes emit a JSON evidence receipt (``--receipt PATH``) and print it.
Dependency-free (stdlib only).
"""

from __future__ import annotations

import argparse
import datetime
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

RECEIPT_SCHEMA = "fog-node.check-receipt.v0"


# --- host runtime lane ------------------------------------------------------

def check_paths() -> list[str]:
    return [f"missing path: {p}" for p in REQUIRED_PATHS if not Path(p).exists()]


def check_container_host() -> list[str]:
    if shutil.which("podman") is None and shutil.which("docker") is None:
        return ["no container host found (expected podman or docker)"]
    return []


def check_lvm() -> list[str]:
    if shutil.which("vgs") is None:
        return ["LVM tools not found (expected vgs)"]
    try:
        subprocess.run(["vgs"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return ["vgs command failed"]
    return []


def run_host_checks() -> list[str]:
    failures: list[str] = []
    failures.extend(check_paths())
    failures.extend(check_container_host())
    failures.extend(check_lvm())
    return failures


# --- offline contract lane --------------------------------------------------

def run_contract_checks(contract_path: str) -> tuple[list[str], dict]:
    failures: list[str] = []
    p = Path(contract_path)
    if not p.exists():
        return [f"contract not found: {contract_path}"], {}
    try:
        contract = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        return [f"contract is not valid JSON: {exc}"], {}

    if contract.get("kind") != "fog-node":
        failures.append(f"contract kind must be 'fog-node' (got {contract.get('kind')!r})")
    for key in ("contractVersion", "lane", "requirements", "evidence"):
        if key not in contract:
            failures.append(f"contract missing required key: {key}")

    reqs = contract.get("requirements", {})
    contract_paths = reqs.get("paths")
    if not isinstance(contract_paths, list):
        failures.append("requirements.paths must be a list")
    else:
        # the checker and the contract must agree on the required /srv/fog paths
        extra_in_contract = set(contract_paths) - set(REQUIRED_PATHS)
        extra_in_checker = set(REQUIRED_PATHS) - set(contract_paths)
        if extra_in_contract:
            failures.append(f"contract requires paths the checker does not enforce: {sorted(extra_in_contract)}")
        if extra_in_checker:
            failures.append(f"checker enforces paths the contract does not declare: {sorted(extra_in_checker)}")

    for section in ("storage", "runtime"):
        if section not in reqs:
            failures.append(f"requirements.{section} missing")
    return failures, contract


# --- receipt ----------------------------------------------------------------

def build_receipt(mode: str, contract_ref, failures: list[str], offline: bool) -> dict:
    return {
        "schemaVersion": RECEIPT_SCHEMA,
        "contract": "fog-node",
        "contractRef": contract_ref,
        "mode": mode,
        "offline": offline,
        "networkRequired": False,
        "passed": not failures,
        "failures": failures,
        "checkedAt": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "os": {"platform": sys.platform},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="fog-node conformance checker")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check-contract", metavar="PATH",
                   help="offline: validate the contract doc + checker/contract path agreement (CI-safe)")
    g.add_argument("--check-host", action="store_true",
                   help="runtime: check this host's fog-node conformance (run on a fog node)")
    ap.add_argument("--receipt", metavar="PATH", default="evidence/fog-node.check-receipt.json",
                    help="write the JSON evidence receipt here")
    args = ap.parse_args()

    if args.check_contract:
        failures, _ = run_contract_checks(args.check_contract)
        receipt = build_receipt("contract-offline", args.check_contract, failures, offline=True)
    else:
        failures = run_host_checks()
        receipt = build_receipt("host-runtime", None, failures, offline=False)

    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
