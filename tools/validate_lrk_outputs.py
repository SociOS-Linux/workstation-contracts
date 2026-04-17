#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def require(data, fields, kind):
    missing = set(fields) - set(data)
    if missing:
        raise ValueError(f"{kind} missing fields: {sorted(missing)}")


def validate_b11(data):
    require(data, {"specVersion", "surfaceId", "identity", "projections", "invariants", "attestation"}, "B11Surface")
    inv = data["invariants"]
    for key in ["feature_jaccard", "topic_alignment_cosine", "mixture_js_mean", "mixture_js_p95", "coherence", "stability"]:
        if key in inv and not (0.0 <= inv[key] <= 1.0):
            raise ValueError(f"B11Surface invariant out of bounds: {key}={inv[key]}")


def validate_delta(data):
    require(data, {"specVersion", "deltaId", "from", "to", "metrics", "attestation"}, "DeltaSurface")
    met = data["metrics"]
    for key in ["feature_jaccard", "topic_alignment_cosine", "mixture_js_mean", "mixture_js_p95"]:
        if key in met and not (0.0 <= met[key] <= 1.0):
            raise ValueError(f"DeltaSurface metric out of bounds: {key}={met[key]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--kind", required=True, choices=["b11", "delta"])
    args = ap.parse_args()
    data = json.loads(Path(args.path).read_text())
    if args.kind == "b11":
        validate_b11(data)
    else:
        validate_delta(data)
    print(f"{args.kind} validation passed: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
