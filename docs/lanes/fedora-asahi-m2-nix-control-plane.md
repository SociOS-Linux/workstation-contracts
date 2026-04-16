# Fedora Asahi M2 + Nix control-plane lane

This lane describes a workstation substrate that keeps Fedora Asahi as the host baseline while introducing a staged Nix control plane for user-space services, container runtime bindings, and controlled host activation.

## Why this lane exists

The existing workstation contract model covered `pixi` and digest-pinned `container` lanes, but the Fedora Asahi substrate lane needs an explicit `nix` backend so we can describe:

- flake-pinned control-plane inputs,
- staged activation before host switch,
- mount-class discipline,
- multi-layer rollback semantics.

## Canonical dependencies

This lane depends on the following canonical repos:

- `SociOS-Linux/SourceOS` — substrate implementation
- `SourceOS-Linux/sourceos-spec` — typed contracts for boot, storage, and staged deployment
- `SocioProphet/agentplane` — stage execution, evidence, and replay

## Conformance expectations

A conforming lane should prove at least:

1. stage execution occurs before promotion,
2. immutable inputs and mutable state are modeled separately,
3. rollback strategy is explicit,
4. evidence is emitted for stage/promote/rollback transitions,
5. boot-sensitive surfaces are marked as such in prerequisites.

## Current example

See `examples/fedora-asahi-m2-nix-control-plane.contract.json` for the first concrete lane definition.
