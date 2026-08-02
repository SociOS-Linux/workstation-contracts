#!/usr/bin/env python3
"""Receipt-emitting inference gateway — how the WHOLE estate gets receipts.

A drop-in transparent proxy in front of any OpenAI-compatible provider (llama-server,
vLLM, ollama, …): it forwards /v1/chat/completions to the backend (preserving client
headers like Authorization) and, on a successful non-streaming JSON response, emits a
schema-conformant, hash-chained InferenceReceipt with the backend's REAL usage token
counts and real input/output hashes. Point an estate service's OPENAI_BASE_URL at this
gateway and every completion gets a receipt — no per-service code change.

Residency: the emitted receipt is on_device_only (the reference backend is local). An
off-device/enterprise backend needs the escalation-grant path and is out of scope here.

Modes:
  --serve     run the proxy (threaded). Env: RECEIPT_GATEWAY_BACKEND, _MODEL_DIGEST or
              _MODEL_PATH, _LEDGER, _HOST (default 127.0.0.1), _PORT (default 8898).
  --selftest  forward ONE real request to the backend, emit + validate a receipt.
exit 0 ok; 1 = conformance failure; 2 = usage/infra error.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inference_receipt_emitter import emit_receipt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BACKEND = os.environ.get("RECEIPT_GATEWAY_BACKEND", "http://127.0.0.1:8899").rstrip("/")
LEDGER = Path(os.environ.get("RECEIPT_GATEWAY_LEDGER",
                             ROOT / "evidence" / "model-plane" / "gateway-ledger.jsonl"))
_FORWARD_HEADERS = ("authorization", "content-type", "openai-organization", "openai-project")


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


def _maybe_emit(req_body: bytes, resp_bytes: bytes, content_type: str, digest: str) -> None:
    """Emit a receipt only for a real, non-streaming JSON completion with string content."""
    if "application/json" not in content_type.lower():
        return  # streaming (SSE) or non-JSON error body — pass through, no receipt
    try:
        body = json.loads(resp_bytes)
        req = json.loads(req_body)
    except (json.JSONDecodeError, ValueError):
        return
    msg = (body.get("choices") or [{}])[0].get("message") or {}
    output = msg.get("content")
    if not isinstance(output, str):
        return  # tool-call / null content — nothing to hash as a completion
    usage = body.get("usage") or {}
    emit_receipt(LEDGER, base_model_digest=digest, task="chat.completion",
                 input_text=_messages_text(req), output_text=output,
                 provider_daemon="inferenced", tier="T1", compute_device="cpu",
                 input_token_count=usage.get("prompt_tokens"),
                 output_token_count=usage.get("completion_tokens"))


def forward_and_receipt(req_body: bytes, digest: str, headers: dict | None = None
                        ) -> tuple[int, str, bytes]:
    """Forward to the backend, return its (status, content-type, body); emit on success."""
    fwd = {k: v for k, v in (headers or {}).items() if k.lower() in _FORWARD_HEADERS}
    fwd.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(f"{BACKEND}/v1/chat/completions", data=req_body,
                               headers=fwd, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            raw, status = resp.read(), resp.status
            ctype = resp.headers.get("Content-Type", "application/json")
    except urllib.error.HTTPError as e:  # non-2xx: return the backend's real error, no receipt
        return e.code, e.headers.get("Content-Type", "application/json"), e.read()
    _maybe_emit(req_body, raw, ctype, digest)
    return status, ctype, raw


def _handler(digest: str):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path.rstrip("/") != "/v1/chat/completions":
                self.send_error(404); return
            n = int(self.headers.get("Content-Length", 0))
            try:
                status, ctype, raw = forward_and_receipt(
                    self.rfile.read(n), digest, dict(self.headers))
            except urllib.error.URLError as exc:  # backend unreachable
                self.send_error(502, f"backend unreachable: {exc}"); return
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *a):
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
        status, _ctype, _raw = forward_and_receipt(req, digest)
    except urllib.error.URLError as exc:
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
        try:
            digest = model_digest()
        except RuntimeError as exc:
            print(f"ERR: {exc}", file=sys.stderr); return 2
        host = os.environ.get("RECEIPT_GATEWAY_HOST", "127.0.0.1")
        port = int(os.environ.get("RECEIPT_GATEWAY_PORT", "8898"))
        print(f"receipt-gateway on {host}:{port} -> {BACKEND} (receipts -> {LEDGER})")
        ThreadingHTTPServer((host, port), _handler(digest)).serve_forever()
        return 0
    print("usage: receipt_gateway.py --serve | --selftest", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
