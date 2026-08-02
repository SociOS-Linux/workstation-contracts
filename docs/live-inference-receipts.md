# Live inference receipts (L3 is real)

This closes the audit's last gap: the estate now has **real `InferenceReceipt`s from real
completions**, not fixtures and not synthetic self-test data.

## What is real
`tools/inferenced_shim.py` runs an actual `llama.cpp` completion against a real,
Apache-2.0-licensed model (Qwen2.5-0.5B-Instruct) and calls `emit_receipt()` with:
- `baseModelDigest` = the **real sha256 of the weights file that ran**,
- `inputHash`/`outputHash` = sha256 of the **real prompt and the real model output**.

The receipts are hash-chained and committed at
`evidence/model-plane/live-inference-ledger.jsonl`. `tools/validate_live_receipts.py`
(wired into `make validate`, so it runs in CI) proves every receipt **schema-conforms** to
the vendored `InferenceReceipt` schema and the **chain is unbroken** — CI needs no model,
only the committed receipts.

## Generate / regenerate (local, needs the model)
```
# provision the Apache-2.0 model once (llama.cpp is already installed):
curl -sL -o /tmp/qwen2.5-0.5b.gguf \
  https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf
python3 tools/inferenced_shim.py --model /tmp/qwen2.5-0.5b.gguf \
  --ledger evidence/model-plane/live-inference-ledger.jsonl -n 40
```
The model weights are **not** committed (large); the receipts are. Regeneration is
append-only — to rebuild from scratch, delete the ledger first.

## Where this sits
- Emitter + hash-chained ledger: `tools/inference_receipt_emitter.py` (#51).
- Live shim + committed real ledger: here.
- The same vendored `InferenceReceipt` schema validates fixtures (T7-19 lane) **and** these
  real receipts — so the conformance lane now checks real emitter output, closing the
  "L2 nominal" gap the reality audit flagged.
