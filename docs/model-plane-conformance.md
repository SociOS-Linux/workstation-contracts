# Model Plane conformance lane (T7-19)

Conformance for the three SourceOS Model Plane concerns, checked against the
**vendored** sourceos-spec schemas (canonical owner: `SourceOS-Linux/sourceos-spec`,
Tranche 7). Schemas live under `schemas/model-plane/*.schema.json` (each `description`
carries a `VENDORED from ...` provenance string); they are loaded from disk so CI is
hermetic.

## What it checks
- **Inference-receipt emission / residency** — an off-device `InferenceReceipt`
  (`sovereign_cluster`/`external_permitted`) without an authorizing `capabilityLeaseRef`
  + non-empty `escalationChain` is rejected (SEAM-011 ledger, SEAM-015 residency).
- **Unsigned-model refusal** — a `ModelManifest`/`ModelAdapterManifest` without a
  `signature`, or an adapter without its `baseModelDigest`, is rejected
  (SEAM-010 unsigned-workflow analog; SEAM-014/017).
- **Data-residency enforcement** — an `EscalationDecision` that is `permitted`
  without a lease + passing T0 sensitivity check is rejected (SEAM-015).

## Layout
- `tools/validate_model_plane.py` — dispatches on the top-level `type` discriminator,
  validates each fixture against its vendored schema; exit 0 iff all conform.
- `conformance/model-plane/good/*.json` — must conform (copied from the canonical
  sourceos-spec examples, plus an on-device receipt).
- `conformance/model-plane/bad/*.json` — must be rejected; each strips exactly one
  teeth-field (off-device receipt without lease; unsigned manifest; adapter without
  base digest; permitted escalation without lease).

## Run
```
make validate-model-plane      # good pass / bad fail
```
Wired into `make validate` (the target CI runs), so it runs on every PR. Note: the
Model Plane seams (SEAM-014..017) are defined in sourceos-spec; this lane references
the existing local analog seams (SEAM-010/011/015) and does not modify the 13-seam
registry.
