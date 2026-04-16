#!/usr/bin/env python3
"""Validate SourceOS truth-plane example payloads against sourceos-spec schemas.

This repo intentionally does NOT vendor the canonical SourceOS/SociOS schema registry.
Instead, this validator runs against a *local checkout* of SourceOS-Linux/sourceos-spec.

Usage:
  SOURCEOS_SPEC_DIR=~/dev/sourceos-spec \
    python tools/validate_sourceos_truth_plane.py \
      fixtures/sourceos-spec/examples/truth-surface.sample.json \
      fixtures/sourceos-spec/examples/delta-surface.sample.json

If SOURCEOS_SPEC_DIR is unset, we try common checkout paths:
  - ../sourceos-spec
  - ../../sourceos-spec
  - ~/dev/sourceos-spec

Exit code:
  0 on success, non-zero on first failure.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import jsonschema


def _find_sourceos_spec_dir() -> Path:
    candidates = []
    env = os.environ.get("SOURCEOS_SPEC_DIR")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.extend([
        Path("../sourceos-spec"),
        Path("../../sourceos-spec"),
        Path.home() / "dev" / "sourceos-spec",
    ])

    for c in candidates:
        if (c / "schemas").is_dir() and (c / "README.md").is_file():
            return c.resolve()

    raise SystemExit(
        "ERROR: could not locate SourceOS-Linux/sourceos-spec checkout. "
        "Set SOURCEOS_SPEC_DIR to a local clone path (e.g., ~/dev/sourceos-spec)."
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_resolver(spec_dir: Path) -> jsonschema.RefResolver:
    # Allow $ref: './schemas/Foo.json' etc.
    base_uri = (spec_dir.as_uri().rstrip("/") + "/")
    return jsonschema.RefResolver(base_uri=base_uri, referrer={})


def _schema_for_payload(spec_dir: Path, payload: dict) -> Path:
    t = payload.get("type")
    if t == "TruthSurface":
        return spec_dir / "schemas" / "TruthSurface.json"
    if t == "DeltaSurface":
        return spec_dir / "schemas" / "DeltaSurface.json"

    # Control-plane incident samples are named differently and are not yet fully
    # integrated into the v2 EventEnvelope spine in the base specs; we validate
    # them only if the schema exists.
    if payload.get("event_name", "").startswith("incident."):
        p = spec_dir / "schemas" / "control-plane" / "incident-events.schema.json"
        return p

    raise SystemExit(f"ERROR: unsupported payload type; cannot select schema. Keys: {sorted(payload.keys())}")


def validate_payload(spec_dir: Path, payload_path: Path) -> None:
    payload = _load_json(payload_path)
    schema_path = _schema_for_payload(spec_dir, payload)

    if not schema_path.exists():
        raise SystemExit(f"ERROR: schema not found: {schema_path} (did you merge the dependent PRs?)")

    schema = _load_json(schema_path)
    resolver = _make_resolver(spec_dir)

    jsonschema.validate(instance=payload, schema=schema, resolver=resolver)
    print(f"VALID: {payload_path}  (schema: {schema_path.relative_to(spec_dir)})")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        return 2

    spec_dir = _find_sourceos_spec_dir()
    paths = [Path(a) for a in argv[1:]]

    for p in paths:
        p = p.resolve()
        if not p.exists():
            raise SystemExit(f"ERROR: payload file not found: {p}")
        validate_payload(spec_dir, p)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
