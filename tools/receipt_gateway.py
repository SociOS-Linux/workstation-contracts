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
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from inference_receipt_emitter import canonical, emit_receipt  # noqa: E402

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


_CHAT = "/v1/chat/completions"
_EMBED = "/v1/embeddings"
_SUPPORTED = (_CHAT, _EMBED)


def _messages_text(req: dict) -> str:
    return "\n".join(f"{m.get('role')}: {m.get('content', '')}" for m in req.get("messages", []))


def _embed_input_text(req: dict) -> str:
    # /v1/embeddings input may be a string, list[str], or token-ID arrays (list[int] /
    # list[list[int]]); stringify items so hashing never crashes on non-strings.
    inp = req.get("input", "")
    return "\n".join(str(x) for x in inp) if isinstance(inp, list) else str(inp)


def _maybe_emit(path: str, req_body: bytes, resp_bytes: bytes, content_type: str, digest: str) -> None:
    """Emit the right receipt for a real, non-streaming JSON response."""
    if "application/json" not in content_type.lower():
        return  # streaming (SSE) or non-JSON error body — pass through, no receipt
    try:
        body = json.loads(resp_bytes)
        req = json.loads(req_body)
    except (json.JSONDecodeError, ValueError):
        return
    usage = body.get("usage") or {}
    if path == _CHAT:
        output = ((body.get("choices") or [{}])[0].get("message") or {}).get("content")
        if not isinstance(output, str):
            return  # tool-call / null content — nothing to hash as a completion
        emit_receipt(LEDGER, base_model_digest=digest, task="chat.completion",
                     input_text=_messages_text(req), output_text=output,
                     provider_daemon="inferenced", tier="T1", compute_device="cpu",
                     input_token_count=usage.get("prompt_tokens"),
                     output_token_count=usage.get("completion_tokens"))
    elif path == _EMBED:
        vectors = [d.get("embedding") for d in (body.get("data") or [])]
        if not vectors or not all(isinstance(v, list) for v in vectors):
            return
        # hash the real returned vectors; embeddings are a T0 workload with no output tokens
        emit_receipt(LEDGER, base_model_digest=digest, task="embedding",
                     input_text=_embed_input_text(req), output_text=canonical(vectors),
                     provider_daemon="embeddingd", tier="T0", compute_device="cpu",
                     input_token_count=usage.get("prompt_tokens"), output_token_count=None)


def forward_and_receipt(path: str, req_body: bytes, digest: str, headers: dict | None = None
                        ) -> tuple[int, str, bytes]:
    """Forward to the backend path, return its (status, content-type, body); emit on success."""
    fwd = {k: v for k, v in (headers or {}).items() if k.lower() in _FORWARD_HEADERS}
    fwd.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(f"{BACKEND}{path}", data=req_body, headers=fwd, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=300) as resp:
            raw, status = resp.read(), resp.status
            ctype = resp.headers.get("Content-Type", "application/json")
    except urllib.error.HTTPError as e:  # non-2xx: return the backend's real error, no receipt
        return e.code, e.headers.get("Content-Type", "application/json"), e.read()
    _maybe_emit(path, req_body, raw, ctype, digest)
    return status, ctype, raw


# Ollama-native endpoints (e.g. noetica's OLLAMA_HOST) — translated to the OpenAI backend
# so they get receipts too. Non-streaming (stream is forced false to the backend).
_OLLAMA = ("/api/chat", "/api/generate", "/api/embeddings", "/api/embed")


def _ollama_forward(path: str, req_body: bytes, digest: str, headers: dict | None
                    ) -> tuple[int, str, bytes]:
    try:
        req = json.loads(req_body)
    except (json.JSONDecodeError, ValueError):
        return 400, "application/json", b'{"error":"invalid JSON"}'
    model = req.get("model", "")
    if path in ("/api/chat", "/api/generate"):
        msgs = (req.get("messages") if path == "/api/chat"
                else [{"role": "user", "content": req.get("prompt", "")}]) or []
        oai = {"messages": msgs, "stream": False}
        num = (req.get("options") or {}).get("num_predict")
        if num:
            oai["max_tokens"] = num
        status, ctype, raw = forward_and_receipt(_CHAT, json.dumps(oai).encode(), digest, headers)
        if not (200 <= status < 300) or "application/json" not in ctype.lower():
            return status, ctype, raw  # pass backend error through
        try:
            body = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return status, ctype, raw  # backend mislabeled/invalid JSON — pass through, don't crash
        content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content", "")
        usage = body.get("usage") or {}
        out = ({"model": model, "message": {"role": "assistant", "content": content}, "done": True}
               if path == "/api/chat"
               else {"model": model, "response": content, "done": True})
        out["prompt_eval_count"], out["eval_count"] = usage.get("prompt_tokens"), usage.get("completion_tokens")
        return 200, "application/json", json.dumps(out).encode()
    # /api/embeddings (legacy single) or /api/embed (multi)
    inp = req.get("input", req.get("prompt", ""))
    status, ctype, raw = forward_and_receipt(_EMBED, json.dumps({"input": inp}).encode(),
                                             digest, headers)
    if not (200 <= status < 300) or "application/json" not in ctype.lower():
        return status, ctype, raw
    try:
        data = json.loads(raw).get("data") or []
    except (json.JSONDecodeError, ValueError):
        return status, ctype, raw  # backend mislabeled/invalid JSON — pass through
    vectors = [d.get("embedding") for d in data]
    out = ({"embedding": vectors[0] if vectors else []} if path == "/api/embeddings"
           else {"model": model, "embeddings": vectors})
    return 200, "application/json", json.dumps(out).encode()


def _handler(digest: str):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            path = urlsplit(self.path).path.rstrip("/")  # ignore any query string for routing
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            try:
                if path in _SUPPORTED:
                    status, ctype, raw = forward_and_receipt(path, body, digest, dict(self.headers))
                elif path in _OLLAMA:
                    status, ctype, raw = _ollama_forward(path, body, digest, dict(self.headers))
                else:
                    self.send_error(404); return
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
        status, _ctype, _raw = forward_and_receipt(_CHAT, req, digest)
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
