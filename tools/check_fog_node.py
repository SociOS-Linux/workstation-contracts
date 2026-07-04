#!/usr/bin/env python3
"""Fog-node conformance checker.

Runnable validate-lane entrypoint for the fog-node contract
(`contracts/fog-node.contract.json`). It performs two tiers of checks:

1. Structural conformance of the contract document itself (hard checks).
   These gate the overall verdict and run fully offline against the JSON
   file, so they are deterministic in CI and on developer workstations.

2. Best-effort host substrate probes (informational checks): canonical
   /srv/fog/* paths, a container host (podman/docker), and LVM (vgs).
   These describe live-host posture and are only *gated* into the verdict
   when run with --require-host (strict mode on an actual fog node). By
   default they are recorded as informational so `make validate` stays
   green on CI runners and workstations that are not provisioned fog nodes.

The checker emits a deterministic, offline evidence receipt (default:
evidence/fog-node.check-receipt.json) recording the contract ref, a
deterministic run id, per-check pass/fail, the overall verdict, and the
fact that it ran offline with no network access.

Usage:
    python3 tools/check_fog_node.py [contracts/fog-node.contract.json]
                                    [--require-host]
                                    [--receipt PATH]
                                    [--no-receipt]

Exits 0 when the gating checks pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_CONTRACT = "contracts/fog-node.contract.json"
DEFAULT_RECEIPT = "evidence/fog-node.check-receipt.json"

# Canonical host paths a provisioned fog node is expected to expose. These
# mirror requirements.paths in the contract but are also used for the
# best-effort host substrate probe.
CANONICAL_FOG_PATHS = [
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


def _check(name: str, tier: str, passed: bool, detail: str = "") -> dict:
    return {"name": name, "tier": tier, "passed": bool(passed), "detail": detail}


# ---------------------------------------------------------------------------
# Tier 1: structural conformance of the contract document (hard / gating)
# ---------------------------------------------------------------------------


def check_contract_structure(contract_path: Path) -> tuple[list[dict], dict | None]:
    """Validate the fog-node contract document structurally, offline.

    Returns (checks, contract_doc_or_None).
    """
    checks: list[dict] = []

    exists = contract_path.is_file()
    checks.append(
        _check(
            "contract.exists",
            "structural",
            exists,
            f"contract file at {contract_path}" if exists else f"missing: {contract_path}",
        )
    )
    if not exists:
        return checks, None

    try:
        doc = json.loads(contract_path.read_text(encoding="utf-8"))
        parsed = True
        parse_detail = "parsed as JSON"
    except Exception as e:  # noqa: BLE001
        doc = None
        parsed = False
        parse_detail = f"parse error: {e}"
    checks.append(_check("contract.parses", "structural", parsed, parse_detail))
    if not parsed:
        return checks, None

    kind_ok = doc.get("kind") == "fog-node"
    checks.append(
        _check("contract.kind", "structural", kind_ok, f"kind={doc.get('kind')!r}")
    )

    version = doc.get("contractVersion")
    checks.append(
        _check(
            "contract.version",
            "structural",
            isinstance(version, str) and bool(version),
            f"contractVersion={version!r}",
        )
    )

    reqs = doc.get("requirements", {})
    paths = reqs.get("paths", [])
    paths_ok = isinstance(paths, list) and set(CANONICAL_FOG_PATHS).issubset(set(paths))
    missing = sorted(set(CANONICAL_FOG_PATHS) - set(paths if isinstance(paths, list) else []))
    checks.append(
        _check(
            "contract.requirements.paths",
            "structural",
            paths_ok,
            "all canonical /srv/fog/* paths declared"
            if paths_ok
            else f"missing canonical paths: {missing}",
        )
    )

    storage_ok = isinstance(reqs.get("storage"), dict)
    checks.append(
        _check("contract.requirements.storage", "structural", storage_ok,
               "storage block present" if storage_ok else "missing requirements.storage")
    )

    runtime_ok = isinstance(reqs.get("runtime"), dict)
    checks.append(
        _check("contract.requirements.runtime", "structural", runtime_ok,
               "runtime block present" if runtime_ok else "missing requirements.runtime")
    )

    evidence_ok = isinstance(doc.get("evidence"), dict)
    checks.append(
        _check("contract.evidence", "structural", evidence_ok,
               "evidence block present" if evidence_ok else "missing evidence block")
    )

    return checks, doc


# ---------------------------------------------------------------------------
# Tier 2: best-effort host substrate probes (informational unless --require-host)
# ---------------------------------------------------------------------------


def probe_host_substrate() -> list[dict]:
    checks: list[dict] = []

    missing_paths = [p for p in CANONICAL_FOG_PATHS if not Path(p).exists()]
    checks.append(
        _check(
            "host.fog_paths",
            "host",
            not missing_paths,
            "all canonical fog paths present"
            if not missing_paths
            else f"missing paths: {missing_paths}",
        )
    )

    has_container_host = shutil.which("podman") is not None or shutil.which("docker") is not None
    checks.append(
        _check(
            "host.container_host",
            "host",
            has_container_host,
            "podman/docker available" if has_container_host
            else "no container host found (expected podman or docker)",
        )
    )

    if shutil.which("vgs") is None:
        checks.append(_check("host.lvm", "host", False, "LVM tools not found (expected vgs)"))
    else:
        try:
            subprocess.run(
                ["vgs"], check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            checks.append(_check("host.lvm", "host", True, "vgs present and returned 0"))
        except subprocess.CalledProcessError:
            checks.append(_check("host.lvm", "host", False, "vgs command failed"))

    return checks


# ---------------------------------------------------------------------------
# Receipt emission (deterministic, offline)
# ---------------------------------------------------------------------------


def build_receipt(
    contract_path: Path,
    contract_doc: dict | None,
    checks: list[dict],
    require_host: bool,
    verdict: bool,
) -> dict:
    contract_ref = str(contract_path)
    contract_version = contract_doc.get("contractVersion") if contract_doc else None

    # Deterministic run id: hash of contract bytes + the gating mode. No
    # timestamps / randomness so repeated offline runs are reproducible.
    hasher = hashlib.sha256()
    if contract_path.is_file():
        hasher.update(contract_path.read_bytes())
    hasher.update(f"require_host={require_host}".encode("utf-8"))
    run_id = "fog-node-" + hasher.hexdigest()[:16]

    return {
        "receiptKind": "fog-node.check-receipt",
        "receiptVersion": "0.1.0",
        "contract": {
            "ref": contract_ref,
            "kind": contract_doc.get("kind") if contract_doc else None,
            "contractVersion": contract_version,
        },
        "runId": run_id,
        "mode": "require-host" if require_host else "structural",
        "checks": checks,
        "verdict": "pass" if verdict else "fail",
        "network": {
            "offline": True,
            "networkAccessed": False,
        },
    }


def write_receipt(receipt: dict, receipt_path: Path) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Fog-node conformance checker")
    parser.add_argument(
        "contract",
        nargs="?",
        default=DEFAULT_CONTRACT,
        help=f"path to fog-node contract (default: {DEFAULT_CONTRACT})",
    )
    parser.add_argument(
        "--require-host",
        action="store_true",
        help="gate the verdict on live host substrate probes (fog-node hosts only)",
    )
    parser.add_argument(
        "--receipt",
        default=DEFAULT_RECEIPT,
        help=f"evidence receipt output path (default: {DEFAULT_RECEIPT})",
    )
    parser.add_argument(
        "--no-receipt",
        action="store_true",
        help="do not write an evidence receipt",
    )
    args = parser.parse_args()

    contract_path = Path(args.contract)

    structural_checks, contract_doc = check_contract_structure(contract_path)
    host_checks = probe_host_substrate()
    checks = structural_checks + host_checks

    # Gating: structural checks always gate. Host checks gate only in
    # --require-host mode; otherwise they are informational.
    structural_ok = all(c["passed"] for c in structural_checks)
    host_ok = all(c["passed"] for c in host_checks)
    verdict = structural_ok and (host_ok if args.require_host else True)

    receipt = build_receipt(contract_path, contract_doc, checks, args.require_host, verdict)

    if not args.no_receipt:
        write_receipt(receipt, Path(args.receipt))

    print(json.dumps(receipt, indent=2, sort_keys=True))

    if not verdict:
        failed = [c["name"] for c in checks if not c["passed"] and (
            c["tier"] != "host" or args.require_host
        )]
        print(f"FAIL fog-node: gating checks failed: {failed}", file=sys.stderr)

    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
