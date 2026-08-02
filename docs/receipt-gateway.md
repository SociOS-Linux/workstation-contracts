# Receipt-emitting inference gateway — how the whole estate gets receipts

`tools/receipt_gateway.py` is the primitive that makes **every** estate inference emit a
receipt without touching each service: a drop-in transparent proxy in front of an
OpenAI-compatible provider (llama-server, vLLM, ollama). It forwards both
**`/v1/chat/completions`** and **`/v1/embeddings`** to the real backend (preserving client
headers like `Authorization`) and, on a successful non-streaming JSON response, records a
schema-conformant, hash-chained `InferenceReceipt` with the real model digest, real
input/output hashes, and the backend's **real usage token counts**. Chat →
`task: chat.completion, tier: T1`; embeddings → `task: embedding, tier: T0` (output hash =
the real returned vectors). This covers the estate's two real inference shapes — chat and
the ingestion/RAG embedding path (`prophet-platform/apps/embeddings`, the sovereign
`/v1/embeddings` service).

## Ollama-native services (e.g. noetica)
Not everything speaks OpenAI `/v1`. noetica points `OLLAMA_HOST` at an Ollama API. The
gateway also accepts the **Ollama-native** endpoints `/api/chat`, `/api/generate`,
`/api/embeddings`, `/api/embed`: it translates the request to the OpenAI backend, emits the
same receipt, and translates the response back to Ollama shape — so pointing noetica's
`OLLAMA_HOST` at the gateway gives it receipts with no code change. Non-streaming (`stream`
is forced false to the backend). Proven live: `/api/chat` → Ollama `{message,done,…}` and
`/api/embeddings` → Ollama `{embedding:[768]}`, each emitting a real receipt.

Residency: the receipt is `on_device_only` — appropriate for a **local** backend, which is
what this reference proves. An off-device/enterprise backend requires the escalation-grant
path (lease + escalation chain) and is out of scope for this gateway.

## Proven live
The gateway was run against real `llama-server` backends (both Apache-2.0):
- **chat** — Qwen2.5-0.5B-Instruct: forwarded a real `/v1/chat/completions` (200) → real
  `task: chat.completion` receipt (weight digest `sha256:74a4da8c…`);
- **embeddings** — nomic-embed-text-v1.5 (`--embedding`): forwarded a real `/v1/embeddings`
  (200, 768-dim vectors) → real `task: embedding` receipt (weight digest `sha256:d4e38889…`).

Both landed in `evidence/model-plane/gateway-ledger.jsonl` (hash-chained). `tools/validate_live_receipts.py` validates
**all** ledgers under `evidence/model-plane/` (the CLI-shim ledger + this gateway ledger)
in CI — schema conformance + unbroken chain, no model needed.

## Run
```
# backend: any OpenAI-compatible provider, e.g.
llama-server -m model.gguf --port 8899

# gateway in front of it (services point OPENAI_BASE_URL here):
RECEIPT_GATEWAY_BACKEND=http://127.0.0.1:8899 \
RECEIPT_GATEWAY_MODEL_DIGEST=sha256:<weights-digest> \
python3 tools/receipt_gateway.py --serve            # listens on :8898

# or prove one real round-trip:
RECEIPT_GATEWAY_MODEL_PATH=model.gguf python3 tools/receipt_gateway.py --selftest
```

## Why this closes "the whole thing has receipts"
The estate's providers are OpenAI-compatible (`InferenceProvider.endpointMode`), so a
single receipt-emitting gateway in the request path gives **every** routed service receipts
— no per-service change. Each service switched to the gateway is one more component whose
inference is on the ledger. The gateway + the CLI shim (`inferenced_shim.py`) are the two
reference emitters; wiring each real service to route through the gateway is the remaining
rollout.

## Deploy (container + persistent ledger)
The gateway ships as a container so the estate can run it as a service with a **durable
ledger** (SEAM-011 non-local ledger = a mounted volume, not a CI snapshot):

```
podman build -f deploy/receipt-gateway/Dockerfile -t receipt-gateway .
# or: cd deploy/receipt-gateway && docker compose up -d   (set RECEIPT_GATEWAY_MODEL_DIGEST)
```
`deploy/receipt-gateway/compose.yml` runs it with a `receipt-ledger` volume, a `/health`
check, and `RECEIPT_GATEWAY_BACKEND` pointing at the real provider. Proven live: built the
image, ran the container against a real `llama-server`, sent a real `/v1/chat/completions`
through it, and the receipt landed in the mounted volume (`/var/lib/receipt-gateway/ledger.jsonl`).

### Wiring a service (the rollout)
Point the service at the gateway — no code change:
- OpenAI-compatible service: `OPENAI_BASE_URL=http://receipt-gateway:8898/v1`
- Ollama-native service (e.g. noetica): `OLLAMA_HOST=http://receipt-gateway:8898`

and set `RECEIPT_GATEWAY_BACKEND` to the provider the gateway fronts. Every routed call is
then on the ledger.
