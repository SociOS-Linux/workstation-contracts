#!/usr/bin/env python3
"""Validate the committed LIVE inference-receipt ledger (real completions).

The ledger evidence/model-plane/live-inference-ledger.jsonl holds REAL InferenceReceipts
emitted by tools/inferenced_shim.py from real llama.cpp completions against a real
Apache-2.0 model. This runs in CI (the model isn't needed to validate — only the receipts):
every receipt schema-conforms to the vendored InferenceReceipt schema and the hash-chain
is unbroken. This is the L3 proof: the estate has real receipts, and they check out.

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
LEDGER = ROOT / "evidence" / "model-plane" / "live-inference-ledger.jsonl"


def main() -> int:
    if not LEDGER.exists():
        print(f"ERR: {LEDGER} not found", file=sys.stderr)
        return 2
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)

    ok, msg = verify_ledger(LEDGER, validator)
    if not ok:
        print(f"FAIL live ledger: {msg}", file=sys.stderr)
        return 1

    entries = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    digests = {e["baseModelDigest"] for e in entries}
    print(f"OK live receipts: {msg}")
    print(f"    {len(entries)} real InferenceReceipts, real model digest(s): "
          f"{', '.join(d[:23] + '…' for d in sorted(digests))}")
    print(f"    tasks: {sorted({e['task'] for e in entries})}; "
          f"tiers: {sorted({e['tier'] for e in entries})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
