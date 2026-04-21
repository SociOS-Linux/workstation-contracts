# Asahi + Fedora Silverblue + Nix workstation lane

## Purpose

This document captures the recommended workstation lane for the current SourceOS/Socios preparation path on Apple Silicon:

- Asahi Linux boot path
- Fedora Silverblue base OS
- Nix as the reproducible tooling and agent/runtime layer
- explicit shared-state staging and rollback boundaries

## Role in the broader repo map

This repository is the correct home for host/operator contracts and workstation lanes.
It is **not** the home for protocol doctrine or local-first runtime implementation.

## Layering model

### L0 — boot and firmware
- Apple firmware and Asahi boot path
- no custom logic here
- reinstallable without redefining workstation semantics

### L1 — immutable base OS
- Fedora Silverblue / rpm-ostree
- minimal host posture
- host remains boring and reproducible

### L2 — persistent shared state
- dedicated shared mount for repos, knowledge bases, model artifacts, and durable user/project state
- designed to survive OS rollback/reinstall

### L3 — Nix tooling layer
- multi-user Nix installed on top of Silverblue
- devshells and agent/runtime flakes live above the host
- no host-level language/toolchain sprawl

### L4 — user/runtime services
- local-first agent runtime (for example OpenClaw)
- workstation services and shells
- rootless/user-scoped where possible

## Default posture

- macOS remains intact
- Linux is dual-booted via Asahi
- Silverblue is the host OS on the Linux side
- Nix provides reproducible tooling and runtime environments
- shared state is explicit and mounted, not scattered

## Proofs

A valid workstation lane should be able to show:
- rpm-ostree status and rollback path
- shared mount presence and policy
- Nix install and flake-based entrypoints
- separation between host state and runtime/tooling state

## Follow-up

1. Encode this lane as a machine-checkable contract in this repo.
2. Add concrete checks for install/update/rollback/shared-state invariants.
3. Attach the OpenClaw and Prophet runtime layers once the lane contract is stable.
