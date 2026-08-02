# InferenceReceipt emitter + hash-chained ledger

`tools/inference_receipt_emitter.py` is the **emitter** side of the Model Plane: when an
inference completes, it appends a schema-conformant, hash-chained `InferenceReceipt` to an
append-only ledger. It is the reference for what a real `inferenced` daemon does on every
completion (SEAM-011: no local-only ledger; the chain makes the ledger tamper-evident).

## What is real vs not
- **Real:** the receipt construction, the SHA-256 input/output hashing, the ledger
  hash-chain (`ledgerPrevHash` binds each entry to the canonical prior entry), schema
  conformance against the vendored `schemas/model-plane/InferenceReceipt.schema.json`, and
  chain verification incl. **tamper-evidence** (mutating any entry breaks the chain).
- **Not real (the audit's L3 gap):** no local model runs — there are no weights on this
  host (ollama blobs empty, no gguf, no ollama CLI). So `--selftest` exercises the emitter
  with clearly-labelled **synthetic completions** (`task: "selftest"`); it proves the
  emitter/ledger machinery, **not** that an LLM completion occurred.

## Making it live (the one unblock)
Provision a runnable, MIT/Apache-licensed model (e.g. a small gguf for `llama.cpp`, which
is already installed), then call `emit_receipt(...)` with the real model's digest and the
real completion's input/output. The emitted receipt is validated by the existing T7-19
conformance lane (`tools/validate_model_plane.py`) — so once wired, the lane checks **real
emitter output**, closing the "L2 nominal" gap.

## Run
```
make validate-inference-emitter   # emit 3 receipts, verify chain + schema + tamper-evidence
```
Wired into `make validate` (CI).
