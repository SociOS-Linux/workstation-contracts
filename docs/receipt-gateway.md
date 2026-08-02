# Receipt-emitting inference gateway — how the whole estate gets receipts

`tools/receipt_gateway.py` is the primitive that makes **every** estate inference emit a
receipt without touching each service: a drop-in proxy in front of any OpenAI-compatible
provider (llama-server, vLLM, ollama, an enterprise endpoint). Point a service's
`OPENAI_BASE_URL` at the gateway and every `/v1/chat/completions` it makes is forwarded to
the real backend **and** recorded as a schema-conformant, hash-chained `InferenceReceipt`
(real model digest, real input/output hashes, real token counts).

## Proven live
The gateway was run against a real `llama-server` (Qwen2.5-0.5B-Instruct, Apache-2.0):
it forwarded a real `/v1/chat/completions` (HTTP 200) and emitted a real receipt
(`task: chat.completion`, real weight digest `sha256:74a4da8c…`) to
`evidence/model-plane/gateway-ledger.jsonl`. `tools/validate_live_receipts.py` validates
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
