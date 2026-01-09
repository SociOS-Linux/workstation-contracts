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

## Next spec expansions (planned)
- Capability negotiation (runner ↔ adapters)
- Evidence registry (canonical evidence keys)
- Optional SBOM + signature requirements for truth lane images
