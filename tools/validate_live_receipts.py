#!/usr/bin/env python3
"""Validate every committed LIVE inference-receipt ledger (real completions).

Validates each evidence/model-plane/*-ledger.jsonl — REAL InferenceReceipts emitted by
tools/inferenced_shim.py (CLI path) and tools/receipt_gateway.py (OpenAI-compatible proxy
path) from real llama.cpp completions against a real Apache-2.0 model. Runs in CI (no model
needed, only the receipts): every receipt schema-conforms to the vendored InferenceReceipt
schema and each ledger's hash-chain is unbroken. The L3 proof: the estate has real receipts.

exit 0 ok; 1 = conformance/chain failure; 2 = usage error.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import jsonschema
except ImportError:
    print("ERR: jsonschema not installed", file=sys.stderr)
    sys.exit(2)

from inference_receipt_emitter import verify_ledger  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "model-plane" / "InferenceReceipt.schema.json"
LEDGER_DIR = ROOT / "evidence" / "model-plane"


def main() -> int:
    # Every committed real-receipt ledger under evidence/model-plane/ (shim + gateway + …).
    # Match the *-ledger.jsonl convention so unrelated JSONL evidence doesn't get validated.
    ledgers = sorted(LEDGER_DIR.glob("*-ledger.jsonl"))
    if not ledgers:
        print(f"ERR: no *-ledger.jsonl receipt ledgers under {LEDGER_DIR}", file=sys.stderr)
        return 2
    try:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    except (OSError, json.JSONDecodeError, jsonschema.exceptions.SchemaError) as exc:
        print(f"ERR: cannot load InferenceReceipt schema: {exc}", file=sys.stderr)
        return 2
    validator = jsonschema.Draft202012Validator(schema)

    total = 0
    for ledger in ledgers:
        try:
            entries = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERR: cannot read/parse {ledger.name}: {exc}", file=sys.stderr)
            return 2
        if not entries:
            print(f"ERR: {ledger.name} is empty", file=sys.stderr)
            return 2
        ok, msg = verify_ledger(ledger, validator)  # conformance/chain -> exit 1
        if not ok:
            print(f"FAIL {ledger.name}: {msg}", file=sys.stderr)
            return 1
        total += len(entries)
        digests = {e["baseModelDigest"] for e in entries}
        tasks = sorted({e["task"] for e in entries})
        print(f"OK {ledger.name}: {msg}  (tasks {tasks}; digest {sorted(digests)[0][:23]}…)")
    print(f"OK live receipts: {total} real InferenceReceipts across {len(ledgers)} ledger(s), "
          f"all schema-conformant with unbroken chains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
