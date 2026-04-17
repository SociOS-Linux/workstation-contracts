#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()

    data = json.loads(Path(args.path).read_text())
    required = {"bundleId", "artifacts", "manifest", "journal", "witness", "signatures"}
    missing = required - set(data)
    if missing:
        raise SystemExit(f"publication bundle missing: {sorted(missing)}")
    if "manifest_sha256" not in data["manifest"]:
        raise SystemExit("manifest missing manifest_sha256")
    print(f"publication validation passed: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
