#!/usr/bin/env python3
"""inferenced shim — run a REAL local completion and emit a REAL InferenceReceipt.

This is the live wiring the audit's gap (b) was missing: it runs an actual llama.cpp
completion against a real model, then emits a schema-conformant, hash-chained
InferenceReceipt whose baseModelDigest is the REAL sha256 of the weights that ran and
whose input/output hashes are of the REAL prompt/completion. No synthetic data.

Local generator (needs the model + llama-cli); the emitted ledger is committed and
validated in CI by verify_ledger / the T7-19 lane. Usage:

    inferenced_shim.py --model <path.gguf> --ledger <ledger.jsonl> [--prompts-file f] [-n N]
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inference_receipt_emitter import emit_receipt  # noqa: E402

DEFAULT_PROMPTS = [
    "In one sentence, what is a knowledge graph?",
    "Name one benefit of content-addressed model storage.",
    "What does an append-only ledger provide?",
]


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def run_completion(model: Path, prompt: str, n: int) -> str:
    cp = subprocess.run(
        ["llama-cli", "-m", str(model), "-p", prompt, "-n", str(n),
         "-no-cnv", "--no-display-prompt", "-st"],
        capture_output=True, text=True, timeout=300,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"llama-cli failed ({cp.returncode}): {cp.stderr[-300:]}")
    return cp.stdout.replace("[end of text]", "").strip()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, type=Path)
    ap.add_argument("--ledger", required=True, type=Path)
    ap.add_argument("--prompts-file", type=Path)
    ap.add_argument("-n", type=int, default=48)
    args = ap.parse_args(argv[1:])

    if not args.model.exists():
        print(f"ERR: model not found: {args.model}", file=sys.stderr)
        return 2
    digest = file_digest(args.model)
    print(f"model {args.model.name}  real digest {digest}")

    prompts = (args.prompts_file.read_text(encoding="utf-8").splitlines()
               if args.prompts_file else DEFAULT_PROMPTS)
    prompts = [p.strip() for p in prompts if p.strip()]

    for p in prompts:
        completion = run_completion(args.model, p, args.n)
        r = emit_receipt(
            args.ledger, base_model_digest=digest, task="completion",
            input_text=p, output_text=completion, provider_daemon="inferenced",
            tier="T1", compute_device="cpu",
        )
        print(f"  seq {r['ledgerSeq']:>2}  in={r['inputHash'][:20]}…  out={r['outputHash'][:20]}…  "
              f"({len(completion)} chars)")
    print(f"OK: {len(prompts)} real receipts appended -> {args.ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
