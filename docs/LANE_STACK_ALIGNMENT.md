# Lane Stack Alignment

This document records the intended execution/build/content split for Linux-first workstation and CI lanes.

It exists because the lane repo should define **what a valid lane is**, while execution, provisioning, and content promotion remain separate concerns.

---

## Core split

### 1. `workstation-contracts` defines the lane

This repo remains the contract and conformance gate for workstation and CI lanes.

It should define:

- lane descriptors
- conformance expectations
- evidence outputs
- admissibility checks
- artifact and environment pinning requirements
- policy hooks and validation rules

It should **not** become the runner, GitOps controller, or content mirror.

### 2. Argo / Tekton execute or orchestrate validated lanes

Argo and Tekton should be treated as the execution and orchestration layer for validated lanes.

Typical responsibilities:

- GitOps or pipeline-triggered lane execution
- workflow orchestration and dependency ordering
- environment assembly from already-validated lane contracts
- promotion or synchronization orchestration after validation succeeds

### 3. Foreman / Katello manage provisioning and content

Foreman and Katello should be treated as the provisioning, content, repository, and promotion layer.

Typical responsibilities:

- host and node provisioning
- content views and lifecycle environments
- repository mirroring and version promotion
- image/package publication inputs consumed by validated lanes
- build/content distribution for SourceOS and related artifacts

This means Foreman/Katello are not substitutes for Argo/Tekton; they solve a different layer of the stack.

---

## Implications for workstation contracts

Future lane contracts should be able to express, at minimum:

- whether the lane is intended for Argo, Tekton, or another runner profile
- which content sources or promoted views must already exist in Foreman/Katello
- what evidence a successful run must emit
- whether the lane is local-only, CI-only, or promotion-eligible
- what immutable image or digest pins are required

A contract can therefore be valid while still being inadmissible in a specific environment if:

- the required content view is unavailable
- the required provisioned environment is absent
- policy denies the lane
- promotion gates have not been met

---

## UMA Pistis / SourceOS fit

Within the broader SourceOS / SociOS ecosystem, this repo should be read as:

- the stable lane shape and conformance gate
- the place where local-first and shared-mesh execution expectations become testable
- the boundary between typed lane definitions and the tools that actually run them

That means:

- `sourceos-spec` defines the canonical object vocabulary
- `source-os` provides the immutable substrate those lanes target
- `agentos-spine` assembles runtime composition and workspace routing
- `socios` may automate the execution of validated lanes, but only as an opt-in layer

---

## Immediate backlog

1. Add explicit lane metadata for execution profile (`argo`, `tekton`, `local-runner`, `other`).
2. Add content-source requirements for Foreman/Katello lifecycle views or repository channels.
3. Add evidence requirements for provenance, image digest, SBOM, and environment fingerprint.
4. Add promotion-gate metadata so higher-level orchestrators can tell whether a lane is only valid locally or can be promoted to shared execution.
5. Add examples showing the same contract shape executed in different orchestration environments.

---

## Recommended next steps

1. Add schema fields for execution profile and content-source requirements.
2. Add at least one good example lane that references Argo/Tekton execution and Foreman/Katello content prerequisites.
3. Add conformance checks that fail when a lane declares unsupported execution profiles or missing content metadata.
4. Feed the resulting lane metadata into the upstream integration/workspace spine.
