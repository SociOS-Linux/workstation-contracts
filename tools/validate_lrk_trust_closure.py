#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", required=True, choices=["review-grade", "governance-grade"])
    ap.add_argument("path")
    args = ap.parse_args()

    data = json.loads(Path(args.path).read_text())
    required = {"bundleId", "artifacts", "manifest", "journal", "witness", "signatures"}
    missing = required - set(data)
    if missing:
        raise SystemExit(f"publication bundle missing: {sorted(missing)}")
    if args.scope == "governance-grade":
        wit = data.get("witness", {})
        if not wit.get("creator") or not wit.get("twin"):
            raise SystemExit("governance-grade bundle missing witness entries")
    print(f"trust closure validation passed: {args.path} ({args.scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
