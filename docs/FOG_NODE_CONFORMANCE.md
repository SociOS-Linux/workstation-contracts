# Fog Node Conformance Lane

This document defines the intended **verification role** of `workstation-contracts` for the Fog layer.

The SourceOS/SociOS fog stack now has:
- canonical object contracts in `SourceOS-Linux/sourceos-spec`
- substrate positioning in `SociOS-Linux/SourceOS`
- first-boot realization guidance in `SociOS-Linux/socios-ignition`

This repo is where those commitments become **checkable assertions** for workstation and CI lanes.

## What this repo should verify

### 1. Host directory contract

A conforming fog-capable node/workstation should expose the canonical host paths:
- `/srv/fog/projects`
- `/srv/fog/models`
- `/srv/fog/datasets`
- `/srv/fog/topics`
- `/srv/fog/vector`
- `/srv/fog/cache`
- `/srv/fog/logs`
- `/srv/fog/secrets`
- `/srv/fog/tmp`

Conformance checks should assert:
- path existence
- expected ownership / permissions
- writeability rules for the appropriate lane

### 2. Local storage substrate readiness

A conforming fog node should be able to demonstrate the expected local storage substrate posture, including where applicable:
- LVM availability
- volume group / thin-pool presence
- mount bindings for fog paths
- enough free capacity for declared lane requirements

### 3. Container-host baseline

The conformance lane should verify that the container execution baseline is present and usable:
- container runtime reachable
- rootless-capable posture where applicable
- fog mounts available to the runtime
- digest-pinned workloads admissible by policy

### 4. Metering / evidence prerequisites

A fog compute node should expose the OS primitives needed to emit trustworthy usage receipts, including best-effort availability of:
- CPU accounting
- memory accounting
- IO accounting
- optional GPU accounting

### 5. Schema alignment

Where this repo validates higher-level artifacts, the contract source of truth remains:
- `SourceOS-Linux/sourceos-spec`

This repo should consume those contracts, not redefine them.

## What should follow this note

Future PRs in this repo should add:
1. a `fog-node` contract profile / lane definition
2. validation tooling that checks substrate and runtime prerequisites
3. CI examples for fog node conformance runs
4. evidence outputs suitable for downstream automation / policy review
