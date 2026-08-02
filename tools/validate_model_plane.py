#!/usr/bin/env python3
"""Validate Model Plane conformance fixtures (T7-19).

Conformance for three SourceOS Model Plane concerns, enforced against the
vendored sourceos-spec schemas (canonical owner: SourceOS-Linux/sourceos-spec,
Tranche 7):

  * inference-receipt emission — an off-device InferenceReceipt without an
    authorizing lease + escalation chain is rejected (SEAM-011 ledger analog,
    SEAM-015 residency);
  * unsigned-model refusal — a ModelManifest/ModelAdapterManifest without a
    signature (or an adapter without its base-model digest) is rejected
    (SEAM-010 unsigned-workflow analog, SEAM-014/017);
  * data-residency enforcement — an EscalationDecision that is `permitted`
    without a lease + passing sensitivity check is rejected (SEAM-015).

Takes fixture paths as argv; exits 0 iff every fixture validates against its
schema (dispatched on the top-level `type` discriminator). A fixture whose type
is unknown is a usage error. Good/bad expectation is decided by the caller
(the Makefile good-pass / bad-fail loops), matching the repo convention.
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
SCHEMA_DIR = ROOT / "schemas" / "model-plane"

# top-level `type` discriminator -> vendored schema file
SCHEMAS = {
    "InferenceReceipt": SCHEMA_DIR / "InferenceReceipt.schema.json",
    "EscalationDecision": SCHEMA_DIR / "EscalationDecision.schema.json",
    "ModelManifest": SCHEMA_DIR / "ModelManifest.schema.json",
    "ModelAdapterManifest": SCHEMA_DIR / "ModelAdapterManifest.schema.json",
}


def _validators() -> dict:
    out = {}
    for kind, path in SCHEMAS.items():
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        out[kind] = jsonschema.Draft202012Validator(schema)
    return out


def validate_file(path: str, validators: dict) -> bool:
    p = Path(path)
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL model-plane.parse: {path}: {exc}", file=sys.stderr)
        return False

    kind = doc.get("type")
    validator = validators.get(kind)
    if validator is None:
        print(
            f"FAIL model-plane.type: {path}: unknown or missing `type` "
            f"(got {kind!r}; expected one of {sorted(SCHEMAS)})",
            file=sys.stderr,
        )
        return False

    errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    if errs:
        e = errs[0]
        loc = "/".join(str(x) for x in e.path) or "<root>"
        print(f"FAIL model-plane.{kind}: {path}: {loc}: {e.message}", file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate_model_plane.py <fixture.json> [<fixture.json> ...]", file=sys.stderr)
        return 2
    validators = _validators()
    ok = True
    for path in argv[1:]:
        if not validate_file(path, validators):
            ok = False
    if ok:
        print(f"OK: model-plane — {len(argv) - 1} fixture(s) conform")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
