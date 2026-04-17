#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    args = ap.parse_args()
    data = json.loads(Path(args.path).read_text())
    required = {"bindingId", "protocol_repo", "protocol_ref", "wire_version"}
    missing = required - set(data)
    if missing:
        raise SystemExit(f"protocol binding missing: {sorted(missing)}")
    if data["protocol_repo"] != "SocioProphet/TriTRPC":
        raise SystemExit("protocol binding must point to canonical TriTRPC repo")
    print(f"protocol binding ok: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
