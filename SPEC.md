# Workstation Contract Spec (v0.1)

This repository defines **lane contracts**: machine-readable declarations of how to build/validate a workstation or CI lane in a reproducible way.

## Core concepts
- **Contract**: a versioned document with one or more lanes.
- **Lane**: an execution environment + ordered steps.
- **Truth lane**: a canonical replay environment; must be pinned by digest.

## Non-goals (for this repo)
- Implementing the runner/orchestrator
- Building/publishing the truth-lane image (a separate repo will do that)

## Invariants
- Container lanes MUST pin images by digest.
- Validators MAY warn on placeholder digests in examples, but real lanes must be real digests.
- Model Plane (T7-19), enforced against the vendored sourceos-spec schemas by `tools/validate_model_plane.py`:
  - **Receipt emission / residency:** an off-device (`sovereign_cluster`/`external_permitted`) `InferenceReceipt` MUST carry an authorizing lease and a non-empty escalation chain (SEAM-011 ledger, SEAM-015 residency).
  - **Unsigned-model refusal:** a `ModelManifest`/`ModelAdapterManifest` MUST carry a signature; an adapter MUST declare its `baseModelDigest` (SEAM-010 analog, SEAM-014/017).
  - **Data-residency enforcement:** an `EscalationDecision` MUST NOT be `permitted` without a lease and a passing T0 sensitivity check (SEAM-015).

## Next spec expansions (planned)
- Capability negotiation (runner ↔ adapters)
- Evidence registry (canonical evidence keys)
- Optional SBOM + signature requirements for truth lane images
