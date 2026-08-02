#!/usr/bin/env python3
"""Receipt-emitting inference gateway — how the WHOLE estate gets receipts.

A drop-in proxy in front of any OpenAI-compatible provider (llama-server, vLLM, ollama,
etc.): it forwards /v1/chat/completions to the backend and, on the real response, emits a
schema-conformant, hash-chained InferenceReceipt (real model digest, real input/output
hashes, real token counts). Point an estate service's OPENAI_BASE_URL at this gateway and
every one of its completions gets a receipt — no per-service code change.

Modes:
  --serve                 run the proxy (env RECEIPT_GATEWAY_BACKEND, _MODEL_DIGEST, _LEDGER)
  --selftest              forward ONE real request to the backend, emit + validate a receipt
Env: RECEIPT_GATEWAY_BACKEND (default http://127.0.0.1:8899),
     RECEIPT_GATEWAY_MODEL_DIGEST or RECEIPT_GATEWAY_MODEL_PATH (to hash), RECEIPT_GATEWAY_LEDGER.

exit 0 ok; 1 = conformance failure; 2 = usage/infra error.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inference_receipt_emitter import emit_receipt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BACKEND = os.environ.get("RECEIPT_GATEWAY_BACKEND", "http://127.0.0.1:8899").rstrip("/")
LEDGER = Path(os.environ.get("RECEIPT_GATEWAY_LEDGER",
                             ROOT / "evidence" / "model-plane" / "gateway-ledger.jsonl"))


def model_digest() -> str:
    d = os.environ.get("RECEIPT_GATEWAY_MODEL_DIGEST")
    if d:
        return d
    p = os.environ.get("RECEIPT_GATEWAY_MODEL_PATH")
    if p and Path(p).exists():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return "sha256:" + h.hexdigest()
    raise RuntimeError("set RECEIPT_GATEWAY_MODEL_DIGEST or RECEIPT_GATEWAY_MODEL_PATH")


def _messages_text(req: dict) -> str:
    return "\n".join(f"{m.get('role')}: {m.get('content', '')}" for m in req.get("messages", []))


def forward_and_receipt(req_body: bytes, digest: str) -> tuple[int, bytes]:
    """Forward a chat-completions request to the backend, emit a receipt from the response."""
    r = urllib.request.Request(f"{BACKEND}/v1/chat/completions", data=req_body,
                               headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(r, timeout=300) as resp:
        raw = resp.read()
        status = resp.status
    body = json.loads(raw)
    req = json.loads(req_body)
    output = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    emit_receipt(LEDGER, base_model_digest=digest, task="chat.completion",
                 input_text=_messages_text(req), output_text=output,
                 provider_daemon="inferenced", tier="T1", compute_device="cpu")
    return status, raw


def _handler(digest: str):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path.rstrip("/") != "/v1/chat/completions":
                self.send_error(404); return
            n = int(self.headers.get("Content-Length", 0))
            try:
                status, raw = forward_and_receipt(self.rfile.read(n), digest)
            except Exception as exc:  # backend/emit failure
                self.send_error(502, str(exc)); return
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *a):  # quiet
            pass
    return H


def _selftest() -> int:
    try:
        import jsonschema
        from inference_receipt_emitter import verify_ledger
    except ImportError as exc:
        print(f"ERR: {exc}", file=sys.stderr); return 2
    try:
        digest = model_digest()
    except RuntimeError as exc:
        print(f"ERR: {exc}", file=sys.stderr); return 2
    req = json.dumps({"messages": [{"role": "user", "content":
                     "In one sentence, what is a knowledge graph?"}], "max_tokens": 40}).encode()
    try:
        status, _ = forward_and_receipt(req, digest)
    except Exception as exc:
        print(f"ERR: backend forward failed (is a provider at {BACKEND}?): {exc}", file=sys.stderr)
        return 2
    schema = json.loads((ROOT / "schemas" / "model-plane" / "InferenceReceipt.schema.json").read_text())
    ok, msg = verify_ledger(LEDGER, jsonschema.Draft202012Validator(schema))
    if not ok:
        print(f"FAIL gateway: {msg}", file=sys.stderr); return 1
    print(f"OK gateway: forwarded a real /v1/chat/completions (backend {status}) and emitted a receipt")
    print(f"    ledger: {msg}")
    return 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    if "--serve" in argv:
        digest = model_digest()
        port = int(os.environ.get("RECEIPT_GATEWAY_PORT", "8898"))
        print(f"receipt-gateway on :{port} -> {BACKEND} (receipts -> {LEDGER})")
        HTTPServer(("127.0.0.1", port), _handler(digest)).serve_forever()
        return 0
    print("usage: receipt_gateway.py --serve | --selftest", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
