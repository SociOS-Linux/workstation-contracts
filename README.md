# workstation-contracts

Linux-first contract runner + backend adapters (pixi first) for reproducible workstation/CI lanes.

Truth lane: linux-amd64-container (pinned digest).

## Topology position

- **Role:** workstation/CI contract and conformance lane.
- **Connects to:**
  - `SociOS-Linux/agentos-spine` — Linux-side integration/workspace spine that orchestrates or routes validated lanes
  - `SourceOS-Linux/sourceos-spec` — canonical typed contracts, JSON-LD contexts, and shared vocabulary
  - `SociOS-Linux/SourceOS` — immutable substrate whose workstation and CI lanes need typed execution contracts
  - `SociOS-Linux/socios` — opt-in automation layer that should only execute well-formed, policy-allowed contracts
  - `SocioProphet/sociosphere` — platform workspace controller that may reuse the same contract posture in broader platform lanes
- **Not this repo:**
  - runner or workspace controller
  - image builder
  - public docs site
  - opt-in automation commons
- **Semantic direction:** this repo should eventually publish a repo-level descriptor that imports the shared SourceOS/SociOS vocabulary from `sourceos-spec` and identifies supported lane types.

## Scope

This repo defines **contracts** and **conformance** for workstation/CI lanes. It is the stable interface between:
- contract authors (humans, CI),
- the runner/orchestrator (execution plane),
- policy enforcement (allow/deny),
- and the artifact supply chain (images, packages).

If you need to *run* a lane, you’re looking for the workspace controller / runner repo, not this one.

## Non-goals

- Implementing the runner/orchestrator (execution belongs elsewhere)
- Hosting container images (this repo only **pins** digests once published)
- Being a monorepo for all workstation tooling (we stay small and auditable)

## How this plugs into the platform

Downstream systems typically do:
1) Load a contract JSON.
2) Validate with `tools/validate_contract.py` (or `make validate`).
3) If allowed by policy, execute lanes via runner/adapters.
4) Emit evidence events/artifacts (digest, deps inventory, OS fingerprint, logs).

The runner/adapters should treat this repo’s schema + validator output as the gate for “well-formed contracts”.
Policy decides whether a well-formed contract is permissible in a given environment.
