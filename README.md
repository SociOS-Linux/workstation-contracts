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

## Agent Machine and Office Plane conformance

This repo now includes conformance fixtures for SourceOS Agent Machine scoped mounts and Prophet Workspace Office Plane dry-run behavior.

Good fixture:

```text
conformance/good/agent-machine-office-dry-run.json
```

Bad fixtures:

```text
conformance/bad/agent-machine-whole-home-mount.json
conformance/bad/agent-machine-unscoped-downloads.json
conformance/bad/office-raw-apple-app-db.json
```

The semantic validator rejects:

- `$HOME` / `~` as a whole-home Agent Machine mount root;
- unscoped `~/Downloads` browser download mounts;
- raw Apple app database/library access for Notes, Photos, Reminders, or Voice Memos;
- Agent Machine lanes that do not emit `agent-machine.mount.evidence`;
- Office Plane lanes that do not emit `office.artifact.evidence`.

These checks preserve the intended boundary:

```text
sourceosctl agent-machine mounts plan -> scoped mount evidence
sourceosctl office ...                -> OfficeArtifact-compatible dry-run/evidence
agent-term office ...                 -> governance-preserving operator event
AgentPlane                            -> AgentMachineMountEvidence / OfficeArtifactEvidence
```

## IPC v0 reference harness

This repo now includes a small IPC v0 reference harness under:

```text
reference/ipc-v0/
```

The harness exists for conformance and protocol testing only. It demonstrates:

- NDJSON stdin/stdout runner↔adapter transport
- hello/capabilities handshake
- a minimal `text.caps` adapter
- deterministic `ipc-transcript.ndjson`
- deterministic `run-receipt.json`

Run it from `reference/ipc-v0/`:

```bash
python -m src.contract_runner.runner \
  --adapter "python -m src.adapters.caps_adapter" \
  --op text.caps \
  --text "hello"
```

Run its tests:

```bash
reference/ipc-v0/tools/run-tests
```

The production runner/orchestrator remains out of scope for this repo. The reference harness is a runnable conformance fixture for `docs/specs/ipc-v0.md` and `schemas/ipc/v0/envelope.schema.json`.

## Non-goals

- Implementing the production runner/orchestrator (execution belongs elsewhere)
- Hosting container images (this repo only **pins** digests once published)
- Being a monorepo for all workstation tooling (we stay small and auditable)
- Executing Agent Machine mounts or Office generation/conversion directly
- Mounting raw host app databases such as Apple Notes, Photos, Reminders, or Voice Memos

## How this plugs into the platform

Downstream systems typically do:
1) Load a contract JSON.
2) Validate with `tools/validate_contract.py` (or `make validate`).
3) If allowed by policy, execute lanes via runner/adapters.
4) Emit evidence events/artifacts (digest, deps inventory, OS fingerprint, logs).

The runner/adapters should treat this repo’s schema + validator output as the gate for “well-formed contracts”.
Policy decides whether a well-formed contract is permissible in a given environment.
