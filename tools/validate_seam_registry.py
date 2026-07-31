#!/usr/bin/env python3
"""Validate the seam registry (T6-3) — 13 architectural seams as SeamDefinition
instances, validated against the vendored SeamDefinition schema (canonical owner:
SourceOS-Linux/sourceos-spec, T0-2).

Asserts: every seam validates; all 13 SEAM-001..013 are present; the SEAM-013
entry references the Claude Desktop telemetry boundary; every seam declares at
least one gate requirement (a seam with no gate is not actionable).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERR: jsonschema not installed", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "seam-definition.schema.json"
REGISTRY = ROOT / "contracts" / "seam-registry.json"
EXPECTED = {f"SEAM-{n:03d}" for n in range(1, 14)}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)

    seams = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(seams, list):
        fail("seam-registry.json must be a JSON array of SeamDefinition objects")

    ids = set()
    for seam in seams:
        errs = sorted(validator.iter_errors(seam), key=lambda e: list(e.path))
        if errs:
            fail(f"{seam.get('seam_id', '?')} schema-invalid: {errs[0].message}")
        if not seam.get("gate_requirements"):
            fail(f"{seam.get('seam_id')} has no gate_requirements (not actionable)")
        ids.add(seam["seam_id"])

    missing = EXPECTED - ids
    if missing:
        fail(f"registry missing seams: {sorted(missing)}")

    seam013 = next((s for s in seams if s["seam_id"] == "SEAM-013"), None)
    if seam013 is None or "telemetry" not in (seam013["attack_vector"] + " " + seam013["name"]).lower():
        fail("SEAM-013 must reference the Claude Desktop telemetry boundary")

    print(f"OK: seam registry — {len(seams)} seams validated (SEAM-001..013 present, SEAM-013 telemetry)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
